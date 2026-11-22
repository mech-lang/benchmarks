"""Summarize stack samples and exact phase-entry counts from the diagnostic runs."""
from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import re

FRAME = re.compile(r"^([ +!|:;]*)(\d+) (\S+?)(?=  \(in |\s|$)")


def sample_leaves(path):
    graph = path.read_text().split("Call graph:\n", 1)[1].split("\n\n", 1)[0]
    stack = []
    for line in graph.splitlines():
        match = FRAME.match(line)
        assert match, line
        prefix, count, symbol = match.groups()
        depth = len(prefix)
        count = int(count)
        while stack and stack[-1][0] >= depth:
            _, remaining, parent = stack.pop()
            assert remaining >= 0
            if remaining:
                yield [entry[2] for entry in stack] + [parent], remaining
        if stack:
            parent_depth, parent_remaining, parent_symbol = stack[-1]
            stack[-1] = (parent_depth, parent_remaining - count, parent_symbol)
        stack.append((depth, count, symbol))
    while stack:
        _, remaining, symbol = stack.pop()
        assert remaining >= 0
        if remaining:
            yield [entry[2] for entry in stack] + [symbol], remaining


def classify_mech(stack):
    if "mech_compact_closed_v2" not in stack:
        return "worker_preparation_validation_or_wait"
    names = " ".join(stack)
    for prefix, category in (
        ("mech_compact_numeric_475", "matcher"),
        ("mech_compact_numeric_3009", "scorer"),
        ("mech_compact_numeric_3956", "huffman"),
        ("mech_compact_numeric_2821", "literal_histograms"),
        ("mech_compact_numeric_3447", "literal_histograms"),
        ("__bzero", "scratch_clearing"),
        ("mech_compact_allocate", "scratch_allocation"),
        ("mech_compact_free", "cleanup"),
        ("mech_compact_release", "cleanup"),
        ("mech_compact_reserve", "output_reserve"),
        ("mech_compact_append", "output_append"),
    ):
        if prefix in names:
            return category
    return "unresolved_native_controller_or_helper"


def classify_c(stack):
    names = " ".join(stack)
    if "libdeflate_alloc_compressor" in names:
        return "allocation_and_initialization"
    if "libdeflate_free_compressor" in names:
        return "cleanup"
    if "libdeflate_deflate_compress" not in names:
        return "worker_preparation_validation_or_wait"
    for prefix, category in (
        ("deflate_find_min_cost_path", "scorer"),
        ("deflate_make_huffman_code", "huffman"),
        ("deflate_optimize_and_flush_block", "block_output"),
        ("__bzero", "scratch_clearing"),
        ("deflate_compress_near_optimal", "inlined_matcher_and_controller"),
    ):
        if prefix in names:
            return category
    return "other_libdeflate"


def read(path):
    return json.loads(path.read_text())


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixtures = {item["name"]: item for item in read(args.fixtures)}
    records = {actor: read(args.profile / actor / "observations.json")
               for actor in ("mech", "libdeflate", "475", "3009", "3956")}
    cases = list(records["mech"]["records"])
    assert all(set(record["records"]) == set(cases) for record in records.values())
    rows = {}
    for case in cases:
        row = {"input_sha256": fixtures[case]["input_sha256"],
               "input_bytes": fixtures[case]["input_bytes"]}
        for actor, classify in [("mech", classify_mech), ("libdeflate", classify_c)]:
            counts = Counter()
            native_leaves = Counter()
            path = args.profile / actor / (case + ".sample.txt")
            for stack, visits in sample_leaves(path):
                category = classify(stack)
                counts[category] += visits
                if category in {"unresolved_native_controller_or_helper", "other_libdeflate"}:
                    native_leaves[stack[-1]] += visits
            native = sum(counts.values()) - counts["worker_preparation_validation_or_wait"]
            row[actor] = {"native_samples": native, "samples": counts,
                          "other_native_symbols": native_leaves}
        representative = records["mech"]["records"][case][1]
        row["mech_resources"] = {key: representative[key] for key in (
            "payload_allocation_requests", "zeroed_bytes", "initialized_bytes_copied",
            "requested_payload_bytes", "peak_private_payload_bytes",
        )}
        row["mech_diagnostic_calls"] = {
            name: records[phase]["records"][case][1]["block_counts"][0]
            for name, phase in (("matcher", "475"), ("scorer", "3009"), ("huffman", "3956"))
        }
        rows[case] = row
    args.output.write_text(json.dumps({
        "scope": "2 s macOS sample at a 1 ms nominal interval per named case and original worker. "
                 "Leaf stacks are partitioned by visible symbols. Inlined controller operations remain unresolved. "
                 "Phase entries come from separate diagnostic images.",
        "worker_sha256": {actor: record["worker_sha256"] for actor, record in records.items()},
        "cases": rows,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
