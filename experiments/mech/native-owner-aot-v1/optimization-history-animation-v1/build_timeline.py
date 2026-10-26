#!/usr/bin/env python3
"""Extend the original measured timeline with both qualified Rust-beating cohorts."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    original = ROOT / "optimization-history-hours-v1/analysis.json"
    verification = ROOT / "paired-candidate-loads-v1/verification.json"
    base = json.loads(original.read_text())
    data = copy.deepcopy(base)
    proof = json.loads(verification.read_text())
    commit = "d8d9a7d64944cd3de78fe3f8190284924069c508"
    assert proof["source"]["commit"] == commit
    assert proof["status"] == "paired-candidates-current-source-output-code-profile-counter-and-terminal-receipts-verified"
    assert len(base["records"]) == 118 and base["process_observations"] == 708
    sessions = []
    sources = {str(original.relative_to(ROOT)): sha(original),
               str(verification.relative_to(ROOT)): sha(verification)}
    for number in [1, 2]:
        receipt = ROOT / f"full-paired-candidate-loads-v{number}/results.json"
        result = json.loads(receipt.read_text())
        assert result["source"] == result["source_after"] == proof["source"]
        assert result["input_sha256"] == base["records"][0]["input_sha256"]
        assert result["status"] == "all-direct-transform-six-subject-full-outputs-updates-and-source-pins-verified"
        assert result["excluded_warmups"] == 0 and result["excluded_outliers"] == 0
        sources[str(receipt.relative_to(ROOT))] = sha(receipt)
        observations = {}
        for subject in ["candidate", "rust"]:
            observations[subject] = []
            for sample in [s for s in result["samples"] if s["subject"] == subject]:
                path = ROOT / sample["process"]
                assert sha(path) == sample["process_sha256"]
                process = json.loads(path.read_text())
                assert process["exit_status"] == 0 and process["reaped"] and process["group_closed"]
                assert not process["cleanup_errors"]
                assert process["elapsed_seconds"] == sample["seconds"]
                birth = process["birth_identity"]
                timestamp = birth["birth_seconds"] + birth["birth_microseconds"] / 1e6
                observations[subject].append({"seconds": sample["seconds"], "timestamp": timestamp,
                    "time_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                    "process": sample["process"], "process_sha256": sample["process_sha256"]})
            assert len(observations[subject]) == 12
        seconds = statistics.median(o["seconds"] for o in observations["candidate"])
        rust = statistics.median(o["seconds"] for o in observations["rust"])
        assert seconds == result["median_seconds"]["candidate"]
        assert rust == result["median_seconds"]["rust"]
        ratio = seconds / rust
        assert ratio == result["x_rust"]["candidate"] and ratio < 1
        assert result["paired_comparisons"]["rust"]["interval_95"][1] < 0
        timestamp = statistics.median(o["timestamp"] for o in observations["candidate"])
        hours = (timestamp - base["t0_timestamp"]) / 3600
        assert hours > base["final_cohort_hours"]
        row = {"key": "paired-candidate-loads", "label": "Paired key/count loads · Mech beats Rust",
            "commit": commit, "session": number, "timestamp": timestamp, "hours": hours,
            "time_utc": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            "time_basis": "Median of exact candidate process birth timestamps",
            "seconds": seconds, "rust_seconds": rust, "x_rust": ratio,
            "n": 12, "observations": observations["candidate"],
            "samples": [o["seconds"] for o in observations["candidate"]],
            "receipt": str(receipt.relative_to(ROOT)), "receipt_sha256": sha(receipt),
            "bases": 125000000, "input_sha256": result["input_sha256"],
            "parent_seconds": result["median_seconds"]["parent"],
            "parent_x_rust": result["x_rust"]["parent"],
            "paired_rust_interval_95": result["paired_comparisons"]["rust"]["interval_95"],
            "single_run": False, "trial": False}
        data["records"].append(row)
        sessions.append({k: row[k] for k in ["session", "hours", "seconds", "rust_seconds", "x_rust", "parent_seconds", "parent_x_rust", "paired_rust_interval_95"]})
    assert data["records"][:118] == base["records"]
    data.update(schema="mech.optimization-animation-timeline.v2", cohorts=120,
        stages=base["stages"] + 1, process_observations=732, unique_processes=732,
        final_cohort_hours=data["records"][-1]["hours"], final_sessions=sessions,
        original_final_cohort_hours=base["final_cohort_hours"],
        source_hashes=sources, builder_sha256=sha(Path(__file__)))
    first = data["records"][-2]
    data["discontinuities"].append({"number": 10, "key": "paired-candidate-loads",
        "label": "Paired key/count loads · ahead of Rust", "hours": first["hours"],
        "seconds": first["seconds"], "x_rust": first["x_rust"],
        "label_hours": 32.0, "label_ratio": 0.67, "n": 12,
        "parent_seconds": first["parent_seconds"], "parent_x_rust": first["parent_x_rust"],
        "receipt": first["receipt"],
        "basis": "Qualified candidate against its contemporaneous parent and unchanged Rust controls; replicated in both balanced sessions."})
    data["notes"].append("Two later paired-load candidate cohorts are appended at their recovered median process births. Parent/anchor controls remain controls, rather than additional implementation changes.")
    (HERE / "timeline.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"cohorts": 120, "observations": 732, "final_sessions": sessions}, indent=2))


if __name__ == "__main__":
    build()
