"""Pure N27 instrumented-call review; no native ownership or work admission."""

import hashlib
import re


N = 27
MAX_TRACE_BYTES = 1024 * 1024
U64_MAX = (1 << 64) - 1
EXPECTED_BYTES = 45
EXPECTED_SHA256 = "ab4264eca722a55e8a6458574e6e607450b978c5f95aedc426ae0615c48cbbba"
HEADER = (
    b"rebol-pi-floor-observation-v1\t27\n"
    b"pair\tsource-line\tq\tr\tt\tk\temitted\tnumerator\tdenominator\tquotient\n"
)
DECIMAL = re.compile(rb"(?:0|-?[1-9][0-9]*)")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def parse(trace):
    require(type(trace) is bytes, "Trace must be complete bytes")
    require(len(trace) <= MAX_TRACE_BYTES, "Trace exceeds bounded byte limit")
    require(trace.startswith(HEADER), "Unexpected trace header")
    require(trace.endswith(b"\n"), "Truncated final trace row")
    body = trace[len(HEADER):]
    require(body, "No facade calls recorded")
    rows = []
    for line in body[:-1].split(b"\n"):
        fields = line.split(b"\t")
        require(len(fields) == 10, "Trace row must have exactly ten fields")
        require(all(DECIMAL.fullmatch(field) for field in fields),
                "Noncanonical decimal trace field")
        # Conversion retains the full integer or fails; no float/truncation path.
        try:
            rows.append(tuple(int(field) for field in fields))
        except ValueError as exc:
            raise AssertionError("Decimal field cannot be represented by this parser") from exc
    require(len(rows) % 2 == 0, "Incomplete facade call pair")
    return rows


def check_quotient(numerator, denominator, observed):
    require(denominator > 0, "Nonpositive denominator")
    require(observed == numerator // denominator, "Floor quotient mismatch")


def formatted_output(digits):
    lines = []
    for start in range(0, len(digits), 10):
        row = "".join(str(digit) for digit in digits[start:start + 10])
        lines.append(row.ljust(10) + "\t:" + str(min(start + 10, len(digits))) + "\n")
    return "".join(lines).encode("ascii")


def validate(stdout, stderr, exit_status, trace, expected):
    """Validate full bytes and recurrence; caller separately proves their origin.

    The supplied reference must be the retained N27 corpus bytes. Trace labels
    identify source order, not native stack frames or machine instructions.
    No filesystem access, evidence imports or subprocesses occur here.
    """
    require(type(stdout) is bytes and type(stderr) is bytes and type(expected) is bytes,
            "Outputs and reference must be complete bytes")
    require(type(exit_status) is int and exit_status == 0, "Diagnostic did not exit normally at zero")
    require(stderr == b"", "Unexpected diagnostic stderr")
    require(len(expected) == EXPECTED_BYTES
            and hashlib.sha256(expected).hexdigest() == EXPECTED_SHA256,
            "Reference is not the retained N27 output")
    rows = parse(trace)
    q, r, t, k, emitted = 1, 0, 1, 1, 0
    digits = []
    refinements = 0
    witness = None
    for offset in range(0, len(rows), 2):
        require(emitted < N, "Extra pair after final emitted digit")
        pair = offset // 2 + 1
        first, second = rows[offset:offset + 2]
        state = (q, r, t, k, emitted)
        for row, site, multiplier in ((first, 15, 3), (second, 16, 4)):
            require(row[:2] == (pair, site), "Missing, duplicate or out-of-order call/site")
            require(row[2:7] == state, "Observed state differs from recurrence")
            require(row[7] == multiplier * q + r, "Numerator equation mismatch")
            require(row[8] == t, "Denominator differs from current t")
            check_quotient(row[7], row[8], row[9])
        if witness is None and all(max(abs(row[7]), abs(row[8])) > U64_MAX
                                   for row in (first, second)):
            witness = {
                "pair": pair,
                "calls": [{
                    "source_line": row[1],
                    "numerator": str(row[7]),
                    "denominator": str(row[8]),
                    "quotient": str(row[9]),
                    "beyond_u64_operands": [name for name, value in
                                            (("numerator", row[7]), ("denominator", row[8]))
                                            if abs(value) > U64_MAX],
                } for row in (first, second)],
            }
        if first[9] == second[9]:
            digit = first[9]
            require(0 <= digit <= 9, "Equal quotient is not a decimal digit")
            digits.append(digit)
            q, r = 10 * q, 10 * (r - digit * t)
            emitted += 1
        else:
            factor = 2 * k + 1
            q, r, t, k = q * k, (2 * q + r) * factor, t * factor, k + 1
            refinements += 1
    require(emitted == N, "Trace ends before 27 emitted digits")
    require(witness is not None, "No pair demonstrates beyond-u64 operands in both calls")
    reconstructed = formatted_output(digits)
    require(reconstructed == expected, "Replayed digits differ from complete reference")
    require(stdout == expected, "Complete diagnostic stdout differs from reference")
    return {
        "schema": "rebol-pi-instrumented-integer-review-v1",
        "status": "instrumented-recurrence-and-output-validated",
        "argument": N,
        "trace_bytes": len(trace),
        "trace_sha256": hashlib.sha256(trace).hexdigest(),
        "stdout_bytes": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "reference_sha256": EXPECTED_SHA256,
        "call_pairs": len(rows) // 2,
        "facade_calls": len(rows),
        "emitted_digits": emitted,
        "equal_branches": emitted,
        "unequal_branches": refinements,
        "beyond_u64_pair": witness,
        "final_state": {"q": str(q), "r": str(r), "t": str(t), "k": k, "emitted": emitted},
        "source_labels_are_native_stack_observations": False,
        "machine_division_count_established": False,
        "native_process_verified": False,
        "source_work_qualified": False,
        "runtime_source_equivalence_proven": False,
        "canonical_source_count_qualified": False,
        "full_timing_qualified": False,
        "chart_admission": False,
    }
