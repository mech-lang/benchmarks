#!/usr/bin/env python3
"""Measure both scalar entry interfaces against one clean pinned Mech candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BENCHMARKS = HERE.parents[1]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    mech = args.mech.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision) or git(mech, "rev-parse", "HEAD") != args.revision:
        parser.error("Mech must be checked out at the supplied full immutable revision")
    if git(mech, "status", "--porcelain"):
        parser.error("use a clean disposable Mech checkout")
    if git(BENCHMARKS, "status", "--porcelain", "--", "tools/scalar-native-probe"):
        parser.error("commit the benchmark probe before measurement")
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    source = (HERE / "probe.rs").read_bytes()
    target = mech / "hosts/gpu/tests/pre911_scalar_probe.rs"
    if target.exists():
        parser.error("probe target already exists; nothing overwritten")
    command = ["cargo", "+nightly-2026-03-03", "test", "--release", "--locked", "--offline",
               "-p", "mech-gpu", "--features", "canonical-native-program-host",
               "--test", "pre911_scalar_probe", "scalar_entry_latency_and_allocations",
               "--", "--ignored", "--exact", "--nocapture", "--test-threads=1"]
    receipt = {"schema": "mech.scalar-entry-comparison.v1", "ok": False,
               "candidate_mech_revision": args.revision, "runner_revision": git(BENCHMARKS, "rev-parse", "HEAD"),
               "probe_sha256": hashlib.sha256(source).hexdigest(),
               "lockfile_sha256": hashlib.sha256((mech / "Cargo.lock").read_bytes()).hexdigest(),
               "command": command, "platform": platform.platform(), "architecture": platform.machine(),
               "rustc": subprocess.check_output(["rustc", "+nightly-2026-03-03", "-vV"], text=True),
               "profile": "release", "host_idle_verified": False,
               "scope": "warm synchronous invocation incl setup/publication/release; excludes parsing and JIT compilation; batch means with in-loop correctness assertions; independent scalar and managed-Value interfaces"}
    result_path = evidence / "result.json"
    result_path.write_text(json.dumps(receipt, indent=2) + "\n")
    created = False
    try:
        with target.open("xb") as stream:
            stream.write(source)
        created = True
        with (evidence / "execution.log").open("wb") as stream:
            completed = subprocess.run(command, cwd=mech, stdout=stream, stderr=subprocess.STDOUT)
    finally:
        if created:
            target.unlink()
    log = (evidence / "execution.log").read_text(errors="replace")
    rows = [{"operations": int(n), "variant": int(v), "round": int(r), "path": p,
             "ns_per_call": int(t), "allocations_per_call": int(a)}
            for n, v, r, p, t, a in re.findall(
                r"SCALAR_PROBE operations=(\d+) variant=(\d+) round=(\d+) path=(\w+) ns_per_call=(\d+) allocations_per_call=(\d+)", log)]
    expected = {(n, v, r, p) for n in (1, 32, 256) for v in (0, 1) for r in range(5) for p in ("program", "scalar")}
    actual = {(row["operations"], row["variant"], row["round"], row["path"]) for row in rows}
    receipt.update(exit_code=completed.returncode, samples=rows,
                   ok=completed.returncode == 0 and len(rows) == len(expected) and actual == expected
                   and "1 passed; 0 failed;" in log and not git(mech, "status", "--porcelain"))
    summaries = []
    if receipt["ok"]:
        for n in (1, 32, 256):
            for v in (0, 1):
                summary = {"operations": n, "variant": v}
                for p in ("program", "scalar"):
                    selected = [row for row in rows if (row["operations"], row["variant"], row["path"]) == (n, v, p)]
                    summary[p] = {"median_batch_ns_per_call": statistics.median(row["ns_per_call"] for row in selected),
                                  "allocations_per_call": sorted({row["allocations_per_call"] for row in selected})}
                summaries.append(summary)
    receipt["summary"] = summaries
    receipt["replacement_qualified"] = False
    receipt["qualification_note"] = "This comparison records evidence, not permission to replace the primary scalar entry; require correctness and controlled performance validation."
    result_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(result_path)
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
