"""Verify profiling code identity and summarize the retained macOS stack samples."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_section(path):
    data = path.read_bytes()
    header = struct.unpack_from("<8I", data)
    assert header[0] == 0xFEEDFACF, "Expected a little-endian 64-bit Mach-O"
    position = 32
    for _ in range(header[4]):
        command, size = struct.unpack_from("<II", data, position)
        assert size >= 8 and position + size <= len(data)
        if command == 0x19:  # LC_SEGMENT_64
            sections = struct.unpack_from("<I", data, position + 64)[0]
            assert 72 + sections * 80 <= size
            for index in range(sections):
                section = position + 72 + index * 80
                name, segment, _, length, offset = struct.unpack_from(
                    "<16s16sQQI", data, section
                )
                if (segment.rstrip(b"\0"), name.rstrip(b"\0")) == (b"__TEXT", b"__text"):
                    assert offset + length <= len(data)
                    return data[offset:offset + length]
        position += size
    raise AssertionError("Missing machine-code section")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timing', default='cache-timing-v2')
    parser.add_argument('--profile-build', default='profile-cache-build-v2')
    parser.add_argument('--samples', default='full-profile-cache-v1')
    parser.add_argument('--binary', default='counting-cache')
    args = parser.parse_args()
    timing = json.loads((HERE / args.timing / 'results.json').read_text())
    profile = json.loads((HERE / args.profile_build / 'results.json').read_text())
    timed_binary = HERE / '.build' / args.binary
    profile_binary = Path(profile["binary"])
    assert sha(timed_binary.read_bytes()) == timing["candidate_sha256"]
    assert sha(profile_binary.read_bytes()) == profile["binary_sha256"]
    timed_code = text_section(timed_binary)
    profile_code = text_section(profile_binary)
    assert timed_code == profile_code

    patterns = {
        "ordinary_library_invocation": "CallCacheLane6invoke",
        "caller_cache_metadata_total": "CallCacheLane21caller_retained_nodes",
        "changed_cache_metadata_demand": "retained_metadata_demand",
        "range_snapshot": "range_snapshot",
        "canonical_string_selection": "canonical_string_selection",
        "retained_map_helper": "retained_map_helper",
        "closed_map_storage_binding": "10map_owners6closed",
        "private_map_read": "11native_read",
        "private_map_insert": "13native_insert",
        "library_work_scope": "16with_call_limits",
        "library_scope_guard": "ControlWorkScopeGuard",
        "library_account_scope": "10with_scope",
        "map_publication": "owned_string_map11publication",
        "selected_key_projection": "State11project_key",
        "selected_range_cardinality": "selected_u64_range_cardinality",
        "selected_range_shape_reuse": "selected_u64_string_span_selector_reusing_shape",
        "selected_range_endpoint_count": "selected_u64_range_count",
        "selected_range_shape_validation": "validate_selected_u64_range_shape",
        "generated_block_admission": "program_runtime5admit",
        "runtime_boundary_validation": "7Context5visit",
        "iteration_transition_validation": "10visit_from",
        "native_work_debit": "NativeWorkMeter6charge",
        "library_work_debit": "NativeLibraryWorkBudget6charge",
    }
    summaries = []
    for path in sorted((HERE / args.samples).glob("sample-*/stacks.txt")):
        content = path.read_text()
        graph = content.split("Call graph:\n", 1)[1].split("Total number in stack", 1)[0]
        counts = {label: 0 for label in patterns}
        total = None
        entry_samples = None
        ancestors = []
        for line in graph.splitlines():
            match = re.match(r"^[\s+!:|]*(\d+) (\S+)", line)
            if not match:
                continue
            count, symbol = int(match[1]), match[2]
            depth = match.start(1)
            while ancestors and ancestors[-1][0] >= depth:
                ancestors.pop()
            if symbol.startswith("Thread_") and "com.apple.main-thread" in line:
                assert total is None
                total = count
            if symbol == "start":
                assert entry_samples is None
                entry_samples = count
            active = set().union(*(labels for _, labels in ancestors))
            matched = set()
            for label, pattern in patterns.items():
                if pattern in symbol:
                    # A generic Rust symbol can contain its parent closure's
                    # name. Count the union of matching subtrees, so the same
                    # observed stack never counts twice within a category.
                    if label not in active:
                        counts[label] += count
                    matched.add(label)
            ancestors.append((depth, matched))
        assert total and all(count <= total for count in counts.values())
        summaries.append({
            "stacks": str(path.relative_to(HERE)),
            "stacks_sha256": sha(path.read_bytes()),
            "main_thread_samples": total,
            "samples_unwound_to_start": entry_samples,
            "inclusive_samples": counts,
            "inclusive_percent": {key: 100 * value / total for key, value in counts.items()},
        })
    assert len(summaries) == 3
    result = {
        "status": "machine-code-identity-verified",
        "scope": "Current candidate only; samples are inclusive, overlap, and are not benchmark timings or a matched baseline profile",
        "source_commit": timing["source_commit"],
        "timed_binary_sha256": timing["candidate_sha256"],
        "profiling_binary_sha256": profile["binary_sha256"],
        "machine_code_section": "__TEXT,__text",
        "machine_code_bytes": len(timed_code),
        "machine_code_sha256": sha(timed_code),
        "machine_code_identical": True,
        "symbol_patterns": patterns,
        "aggregation": "Union of matching subtrees within each category; categories overlap; denominator includes all main-thread samples, including partial unwinds",
        "samples": summaries,
    }
    output = HERE / args.samples / 'analysis.json'
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
