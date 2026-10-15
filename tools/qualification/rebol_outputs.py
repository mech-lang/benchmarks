"""Pure Rebol stream checks for the pinned 149-case shared corpus.

Success contracts match scala_typescript_outputs.py without assigning Rebol
another language's identity. The caller independently pins the corpus, inputs,
subject/runtime and native receipt; this module reads no files and starts no
processes. A passing output check does not qualify source work or publication.
"""
import hashlib
import math
import re

CORPUS_SHA256 = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
SUCCESS_CASES = 142
REJECTION_CASES = 7
NEGATIVE_EXIT_STATUS = 1
NEGATIVE_STDERR = b'\n** User error: Unsupported revcomp sequence byte\n\n'
ENERGIES = re.compile(rb'-?\d+\.\d{9}\n-?\d+\.\d{9}\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rejection(case, stdout, stderr, exit_status, expected):
    """Check the source-derived direct ``runtime -q -s main.reb`` error.

    Retained revcomp/main.reb:14 calls clbg_io.reb:6's ``do make error!``;
    its only stdout write is main.reb:41, after all buffered records succeed.
    In sdk-generation-v1/work-v1/source/src, core/t-object.c:364-367 calls
    Make_Error_Object (core/c-error.c:376,411-415), which clones boot/sysobj.reb's
    blank near/where template and sets RE_USER/arg1/type. It does not call the
    separate Make_Error trap path that adds a backtrace. core/n-control.c:681-683
    calls Throw_Error; core/c-do.c:2358-2374 prints this error and returns -1.
    core/s-mold.c:1144-1201 and boot/strings.reb:130-133 supply the exact envelope,
    boot/errors.reb:234 supplies User, and core/d-print.c:794-817 adds the final
    newline. os/posix/dev-stdio.c:639-643 sends error text to stderr;
    os/host-main.c:363-374 exits 1 and -q suppresses the separate closing print.

    This is a proposed native acceptance contract supported by retained source,
    not an observed rejection or proof of source/runtime equivalence. Actual
    differing captures must fail. The invalid-byte oracle identifies the corpus
    input; this Rebol message does not emit that byte's numeric value.
    """
    require(case['benchmark'] == 'revcomp' and expected is None and
            'expected' not in case and case['expected_exit'] == 'nonzero',
            'Malformed rejection contract')
    code = case['expected_invalid_byte']
    require(type(code) is int and 0 <= code <= 255, 'Invalid expected IUPAC byte')
    require(exit_status == NEGATIVE_EXIT_STATUS,
            'Rebol rejection requires normal exit 1, not success or a signal')
    require(stdout == b'', 'Rebol rejection must precede the buffered stdout write')
    require(stderr == NEGATIVE_STDERR, 'Rebol user-error diagnostic differs')
    return dict(expected_invalid_byte=code, invalid_byte_emitted=False,
                rejection_policy='rebol-user-error-before-buffered-output',
                rejection_policy_basis='retained-source', native_rejection_prequalified=False)


def validate(case, stdout, stderr, exit_status, expected):
    """Check complete captured bytes using a case from the pinned corpus.

    ``expected`` is the pinned expected.stdout bytes for a success, or None for
    a rejection. The corpus digest above is an authority identifier, not a claim
    that this pure function has opened or verified the manifest or native files.
    """
    require(isinstance(stdout, bytes) and isinstance(stderr, bytes), 'Byte streams required')
    require(type(exit_status) is int, 'Exact native integer exit status required')
    method = case['validation']
    record = dict(language='rebol', benchmark=case['benchmark'], case=case['case'],
                  exit_status=exit_status, stdout_bytes=len(stdout), stdout_sha256=sha(stdout),
                  stderr_bytes=len(stderr), stderr_sha256=sha(stderr), method=method,
                  native_process_verified=False, source_work_qualified=False,
                  chart_admission=False)
    if method == 'language-specific-invalid-iupac':
        record.update(rejection(case, stdout, stderr, exit_status, expected))
    else:
        require(type(case['expected_exit']) is int and case['expected_exit'] == 0 and
                exit_status == 0 and stderr == b'',
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
            # Nine fractional digits make the printed signed integer comparison
            # exact, including negative values at the retained 1e-8 boundary.
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
