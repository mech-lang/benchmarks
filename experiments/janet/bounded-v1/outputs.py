"""Pure success-output contracts for the pinned shared corpus, without Janet.

The byte and exact-decimal policies match the retained Scala/TypeScript checker.
Janet's language-specific rejection adapter remains unqualified. Process closure,
input identity, runtime dependencies and required work need separate evidence.
"""
import hashlib
import re

ENERGIES = re.compile(rb'-?\d+\.\d{9}\n-?\d+\.\d{9}\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def validate_success(case, stdout, stderr, exit_status, expected):
    """Check whole streams; a match does not itself qualify a native process."""
    require(type(case['expected_exit']) is int and case['expected_exit'] == 0,
            'Janet rejection contracts require separate native review')
    require(type(exit_status) is int and exit_status == 0 and stderr == b'',
            'Normal exit zero and empty stderr required')
    require(type(stdout) is bytes and type(stderr) is bytes and type(expected) is bytes,
            'Complete byte streams required')
    pin = case['expected']
    require(type(pin['bytes']) is int and len(expected) == pin['bytes'] and
            digest(expected) == pin['sha256'], 'Expected output pin differs')
    method = case['validation']
    detail = {}
    if method == 'finite-two-energy-lines-within-1e-8':
        require(case['benchmark'] == 'nbody' and ENERGIES.fullmatch(stdout) is not None
                and ENERGIES.fullmatch(expected) is not None,
                'Two complete finite nine-decimal energy lines required')
        actual = [int(line.replace(b'.', b'')) for line in stdout.splitlines()]
        reference = [int(line.replace(b'.', b'')) for line in expected.splitlines()]
        differences = [abs(a - b) for a, b in zip(actual, reference)]
        require(all(difference <= 10 for difference in differences),
                'N-body energy exceeds retained decimal tolerance')
        detail = dict(comparison='signed-integer-nanounits',
                      differences_nanounits=differences, maximum_difference_nanounits=10)
    else:
        require(method == 'exact-complete-bytes' and case['benchmark'] != 'nbody',
                'Unsupported or mismatched output method')
        require(stdout == expected, 'Complete output differs from independent reference')
    return dict(language='janet', benchmark=case['benchmark'], case=case['case'],
                method=method, exit_status=exit_status, stdout_bytes=len(stdout),
                stdout_sha256=digest(stdout), stderr_bytes=0, stderr_sha256=digest(stderr),
                expected_bytes=len(expected), expected_sha256=digest(expected),
                output_contract_satisfied=True, native_process_verified=False,
                source_work_qualified=False, chart_admission=False, **detail)
