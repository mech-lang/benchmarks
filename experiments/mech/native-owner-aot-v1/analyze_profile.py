"""Verify profiling code identity and summarize the retained macOS stack samples."""
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
    timing = json.loads((HERE / "cache-timing-v2/results.json").read_text())
    profile = json.loads((HERE / "profile-cache-build-v2/results.json").read_text())
    timed_binary = HERE / ".build/counting-cache"
    profile_binary = Path(profile["binary"])
    assert sha(timed_binary.read_bytes()) == timing["candidate_sha256"]
    assert sha(profile_binary.read_bytes()) == profile["binary_sha256"]
    timed_code = text_section(timed_binary)
    profile_code = text_section(profile_binary)
    assert timed_code == profile_code

    patterns = {
        "ordinary_library_invocation": "CallCacheLane6invoke",
        "caller_cache_metadata_total": "caller_retained_nodes",
        "changed_cache_metadata_demand": "retained_metadata_demand",
        "range_snapshot": "range_snapshot",
        "canonical_string_selection": "canonical_string_selection",
        "retained_map_helper": "retained_map_helper",
    }
    summaries = []
    for path in sorted((HERE / "full-profile-cache-v1").glob("sample-*/stacks.txt")):
        content = path.read_text()
        graph = content.split("Call graph:\n", 1)[1].split("Total number in stack", 1)[0]
        counts = {label: 0 for label in patterns}
        total = None
        for line in graph.splitlines():
            match = re.match(r"^[\s+!:|]*(\d+) (\S+)", line)
            if not match:
                continue
            count, symbol = int(match[1]), match[2]
            if symbol == "start":
                assert total is None
                total = count
            for label, pattern in patterns.items():
                if pattern in symbol:
                    counts[label] += count
        assert total and all(count <= total for count in counts.values())
        summaries.append({
            "stacks": str(path.relative_to(HERE)),
            "stacks_sha256": sha(path.read_bytes()),
            "main_entry_samples": total,
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
        "samples": summaries,
    }
    output = HERE / "full-profile-cache-v1/analysis.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
