"""Pure output checks for the Scala/TypeScript shared bounded corpus.

The caller must independently verify the native process, runtime, limits,
source/artifact pins and exact input. Passing these checks establishes only
that the supplied streams and exit code satisfy a bounded output contract.
"""
import hashlib
import math
import re

LANGUAGES = {'scala', 'typescript'}
ENERGIES = re.compile(rb'-?\d+\.\d{9}\n-?\d+\.\d{9}\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(case, language, stdout, stderr, exit_status, expected):
    """Validate complete captured bytes, without reading files or running code.

    `case` must come from the independently pinned corpus manifest. `expected`
    is its expected.stdout bytes for success cases and None for rejections.
    Language-specific rejection rules are proposed from the exact source
    drafts; native acceptance remains pending until supervised execution.
    """
    require(language in LANGUAGES, 'Unsupported language adapter')
    require(isinstance(stdout, bytes) and isinstance(stderr, bytes), 'Byte streams required')
    require(type(exit_status) is int, 'Exact native integer exit status required')
    method = case['validation']
    record = dict(language=language, benchmark=case['benchmark'], case=case['case'],
                  exit_status=exit_status, stdout_bytes=len(stdout), stdout_sha256=sha(stdout),
                  stderr_bytes=len(stderr), stderr_sha256=sha(stderr), method=method,
                  native_process_verified=False, source_work_qualified=False,
                  chart_admission=False)
    if method == 'language-specific-invalid-iupac':
        require(case['benchmark'] == 'revcomp' and expected is None and
                'expected' not in case and case['expected_exit'] == 'nonzero',
                'Malformed rejection contract')
        code = case['expected_invalid_byte']
        require(type(code) is int and 0 <= code <= 255, 'Invalid expected IUPAC byte')
        require(exit_status == 1, 'Rejection requires normal exit 1, not success or a signal')
        diagnostic = b'Invalid IUPAC byte: ' + str(code).encode('ascii')
        if language == 'typescript':
            require(stdout == b'>r\n', 'TypeScript rejection partial output differs')
            require(stderr == diagnostic + b'\n', 'TypeScript rejection diagnostic differs')
        else:
            # The direct java Main entry leaves its local BufferedOutputStream
            # unflushed when require throws. All seven fixtures are below its
            # capacity, so no sequence or header bytes should reach stdout.
            require(stdout == b'', 'Scala rejection partial output differs')
            prefix = (b'Exception in thread "main" java.lang.IllegalArgumentException: '
                      b'requirement failed: ' + diagnostic + b'\n')
            require(stderr.startswith(prefix) and stderr.endswith(b'\n'),
                    'Scala rejection exception differs')
            suffix = stderr[len(prefix):]
            frames = suffix[:-1].split(b'\n')
            require(b'\r' not in suffix and frames and
                    all(frame.startswith(b'\tat ') and
                        all(32 <= byte < 127 for byte in frame[4:]) for frame in frames),
                    'Unexpected Scala diagnostic suffix')
            require(any(frame.startswith(b'\tat Main$.') for frame in frames) and
                    any(frame.startswith(b'\tat Main.main(') for frame in frames),
                    'Scala rejection lacks the direct subject main stack')
        record.update(expected_invalid_byte=code,
                      rejection_policy='typed-error-and-source-defined-partial-output')
    else:
        require(case['expected_exit'] == 0 and exit_status == 0 and stderr == b'',
                'Successful output requires normal exit zero and empty stderr')
        require(isinstance(expected, bytes), 'Complete expected bytes required')
        pinned = case['expected']
        require(type(pinned['bytes']) is int and len(expected) == pinned['bytes'] and
                sha(expected) == pinned['sha256'], 'Expected output does not match corpus pin')
        if method == 'finite-two-energy-lines-within-1e-8':
            require(case['benchmark'] == 'nbody' and ENERGIES.fullmatch(stdout) is not None and
                    ENERGIES.fullmatch(expected) is not None, 'Malformed complete N-body output')
            actual_values = [float(line) for line in stdout.splitlines()]
            reference_values = [float(line) for line in expected.splitlines()]
            require(all(math.isfinite(value) for value in actual_values + reference_values),
                    'Nonfinite N-body energy')
            # Both lines have exactly nine fractional digits. Compare their
            # printed decimal values exactly: binary floating subtraction can
            # round a valid difference of 1e-8 slightly above that threshold.
            actual_units = [int(line.replace(b'.', b'')) for line in stdout.splitlines()]
            reference_units = [int(line.replace(b'.', b'')) for line in expected.splitlines()]
            differences = [abs(actual - reference)
                           for actual, reference in zip(actual_units, reference_units)]
            require(all(difference <= 10 for difference in differences),
                    'N-body energy differs beyond the retained tolerance')
            record.update(energies=actual_values, expected_energies=reference_values,
                          tolerance=1e-8, comparison='signed-integer-nanounits',
                          differences_nanounits=differences, maximum_difference_nanounits=10)
        else:
            require(method == 'exact-complete-bytes' and case['benchmark'] != 'nbody',
                    'Unsupported or mismatched output-validation method')
            require(stdout == expected, 'Complete output differs from independent reference')
        record.update(expected_bytes=len(expected), expected_sha256=sha(expected))
    record['output_contract_satisfied'] = True
    return record
