#!/usr/bin/env python3
"""Draft only: hash-bound Ruby generic-support partitions; never edit inputs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/source-normalization/ruby-support-v1/review.json"
# Inclusive original-source rows. These are reviewed identities, not a detector.
CANDIDATES = {
    "c7bd5e001454bf9f9966c9e9adb95ca2a8d0251db07ed9aa22b89fa44de841cf": (12, 103, "binarytrees:binarytrees-ruby-5", "MiniParallel"),
    "b8bbe0b852722800ff89f6c5ee92a90cec8d0b7755fa855af891c2056d6e9adb": (14, 105, "mandelbrot:mandelbrot-ruby-5", "MiniParallel"),
    "45d77609445db3378a7aba02d855a4e89b0cec9c6f85b4b09b182d88785db328": (10, 101, "fannkuchredux:fannkuchredux-ruby-2-cpu4", "MiniParallel"),
    "01d3079dc51dba4defb49d74574dceea591d7642c24fa23014286c9b3c55eb44": (5, 74, "spectralnorm:spectralnorm-ruby-5", "Worker.map"),
    "affb193beb99fee220ef23a08581d99d901f9c2722b26ef7b1351aacf2d0f5af": (44, 62, "knucleotide:knucleotide-ruby-1", "Worker"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stable(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def reviewed_segments(start, api):
    if api == "MiniParallel":
        definitions = [
            (1, 15, "Worker pipe abstraction: initialize arbitrary handles, close them, serialize an index and load an arbitrary result."),
            (17, 23, "Generic array/block map entry point and worker-count cap; no workload partition logic."),
            (25, 27, "Generic cached CPU-count discovery; runtime shim policy is unchanged."),
            (31, 53, "Generic process-map queue: mutex-protected index dispatch, ordered results, thread/process joins."),
            (55, 61, "Construct an arbitrary requested number of generic workers."),
            (63, 83, "Generic pipe/fork lifecycle and dispatch of the caller-provided block; no benchmark callback is hardcoded."),
            (85, 90, "Generic job server: deserialize an index and serialize caller block(array[index]) result."),
        ]
        return [(start + a, start + b, reason) for a, b, reason in definitions]
    if api == "Worker.map":
        return [(7, 7, "Expose a generic reader handle."),
                (9, 23, "Retain arbitrary enumeration/worker index and fork its caller-provided block over generic pipe handles."),
                (25, 33, "Partition enumeration indices across workers and return indexed arbitrary callback results; no dense-product formula."),
                (35, 37, "Serialize an arbitrary message to the parent."),
                (39, 63, "Gather arbitrary indexed results from selectable pipes, handle EOF and wait for children."),
                (65, 73, "Generic enumeration/block map entry point with a default worker count.")]
    return [(45, 54, "Generic arbitrary-block fork, byte-output pipe and descriptor lifecycle; no sequence/frequency method is named."),
            (56, 61, "Read the arbitrary worker output, close the descriptor and wait for that child.")]


def build_review(raw):
    data = json.loads(raw)
    catalog = {**data.get("program_inventory", {}), **data["programs"]}
    ruby = {k: p for k, p in catalog.items() if p["language"] in {"ruby", "ruby-zjit"}}
    if len(ruby) != 42:
        raise ValueError("Ruby cohort changed; re-review expected profile coverage")
    sources = {h for p in ruby.values() for h in p["files"]}
    if len(sources) != 19:
        raise ValueError("Ruby source cohort changed")
    for h in sources:
        if sha(data["files"][h]["code"].encode()) != h:
            raise ValueError("Ruby original source digest mismatch")
    reviews = []
    for h, (start, end, owner, api) in CANDIDATES.items():
        f = data["files"][h]
        rows = f["code"].splitlines(keepends=True)
        if not (rows[start - 1].strip() in {"module MiniParallel", "class Worker"} and rows[end - 1].strip() == "end"):
            raise ValueError("Reviewed helper boundary mismatch")
        profiles = sorted(k for k, p in ruby.items() if h in p["files"])
        if profiles != sorted([owner, owner + "-zjit"]):
            raise ValueError("Ruby source alias coverage changed")
        support = "".join(rows[start - 1:end]).encode()
        application = "".join(rows[:start - 1] + rows[end:]).encode()
        segments = reviewed_segments(start, api)
        reviews.append({
            "source_sha256": h, "name": f["name"], "path": f["path"],
            "expected_profiles": profiles, "generic_api": api,
            "support_line_ranges": [[start, end]],
            "application_line_ranges": [[1, start - 1], [end + 1, len(rows)]],
            "submitted": {"utf8_bytes": len(f["code"].encode()), "sha256": h},
            "candidate_application": {"utf8_bytes": len(application), "sha256": sha(application)},
            "candidate_excluded_support": {"utf8_bytes": len(support), "sha256": sha(support)},
            "review_segments": [{"start": a, "end": b, "reason": reason} for a, b, reason in segments],
            "per_line_review": [{"line": n, "line_sha256": sha(rows[n - 1].encode()),
                                 "role": "candidate-reusable-support",
                                 "reason": next((reason for a, b, reason in segments if a <= n <= b), "Enclosing generic class/module syntax, visibility marker or separator within the reviewed API definition.")}
                                for n in range(start, end + 1)],
            "normalized_loc": None,
            "normalized_loc_status": "unavailable-pending-Ruby-native-owner-qualification",
        })
    return {
        "schema": "ruby-embedded-support-review.v1", "status": "candidate-not-applied",
        "catalog_sha256": sha(raw), "tool_sha256": sha(Path(__file__).read_bytes()),
        "policy": "Only exact reviewed generic worker definitions are proposed support. Imports, arguments, workload partition construction, workload callbacks, merging, formatting and top-level dispatch remain application.",
        "source_policy": "Protected unchanged Game source remains byte-identical; this proposal changes neither admission nor runtime code. Canonical application/LOC/source metrics remain unchanged.",
        "native_processes_run": 0, "candidate_source_files": len(reviews),
        "candidate_profiles": sum(len(r["expected_profiles"]) for r in reviews),
        "protected_ruby_profiles": len(ruby), "protected_source_files": len(sources),
        "protected_profile_sha256": {k: sha(stable(p)) for k, p in sorted(ruby.items())},
        "protected_source_sha256": sorted(sources),
        "reviews": reviews,
        "deferred": [
            {"source_name": "revcomp-ruby-4.rb", "line_ranges": [[31, 60]], "reason": "forking_worker calls the fixed original_process_segment callback; keep this benchmark-coupled bridge and record dispatch counted until a narrower review."},
            {"source_name": "regexredux-ruby-3.rb", "line_ranges": [[53, 65]], "reason": "forked_pattern_count calls the fixed original_pattern_count callback; keep the wrapper and nine-pattern orchestration counted."},
        ],
        "limits": ["No Ruby parser/native ownership count is qualified here; do not subtract physical rows from retained LOC.", "Proposed raw scopes include original comments and whitespace and concatenate kept complete rows without synthetic separators.", "gzip/BPE/formatted metrics require separate regeneration only after boundary approval; current report is not changed."],
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build_review((ROOT / "data/benchmarks.json").read_bytes())
    encoded = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode()
    if args.check:
        if OUTPUT.read_bytes() != encoded:
            raise SystemExit("Ruby support proposal is stale")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(encoded)
    print("Ruby support candidate: 5 files, 10 affected profiles, 42 protected profiles; not applied")


if __name__ == "__main__":
    main()
