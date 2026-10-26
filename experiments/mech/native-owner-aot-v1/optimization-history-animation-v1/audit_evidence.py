"""Independently recompute plotted timings and timestamps from process receipts."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT_SHA = "3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((HERE / "timeline.json").read_text())
    cache = {}
    checked = {}

    def read(path):
        if path not in cache:
            cache[path] = json.loads(path.read_text())
        return cache[path]

    def check_hash(path, expected):
        if path not in checked:
            checked[path] = digest(path)
        assert checked[path] == expected, str(path)

    pool_cache = {}

    def process_pool(receipt):
        if receipt in pool_cache:
            return pool_cache[receipt]
        data = read(receipt)
        paths = set(receipt.parent.glob("*/process.json"))
        for sample in data.get("samples", []):
            if isinstance(sample, dict) and sample.get("process"):
                path = ROOT / sample["process"]
                check_hash(path, sample["process_sha256"])
                paths.add(path)
        for evidence in data.get("evidence", []):
            if isinstance(evidence, dict) and evidence.get("path", "").endswith("/results.json"):
                child = ROOT / evidence["path"]
                check_hash(child, evidence["sha256"])
                paths.update(process_pool(child))
        pool_cache[receipt] = paths
        return paths

    def valid_process(path, seconds):
        data = read(path)
        assert data["elapsed_seconds"] == seconds, str(path)
        assert data["quantitative_benchmark"] is True, str(path)
        assert data["exit_status"] == 0 and data["reaped"] and data["group_closed"], str(path)
        assert not data.get("cleanup_errors"), str(path)
        return data["birth_identity"]["birth_seconds"] + data["birth_identity"]["birth_microseconds"] / 1e6

    for relative, expected in timeline["source_hashes"].items():
        check_hash(ROOT / relative, expected)
    candidates, rust_processes = set(), set()
    records = []
    for row in timeline["records"]:
        receipt = ROOT / row["receipt"]
        check_hash(receipt, row["receipt_sha256"])
        raw = read(receipt)
        assert raw["input_sha256"] == row["input_sha256"] == INPUT_SHA
        assert row["bases"] == 125000000
        for key in ["excluded_warmups", "excluded_outliers"]:
            if key in raw:
                assert raw[key] == 0
        values, births = [], []
        for observation in row["observations"]:
            path = ROOT / observation["process"]
            check_hash(path, observation["process_sha256"])
            birth = valid_process(path, observation["seconds"])
            assert abs(birth - observation["timestamp"]) <= 1e-6
            values.append(read(path)["elapsed_seconds"])
            births.append(birth)
            candidates.add(path)
        rust = raw.get("samples_seconds", {}).get("rust")
        if rust is None:
            rust = [sample["seconds"] for sample in raw.get("samples", [])
                    if sample.get("subject", sample.get("label")) == "rust"]
        assert rust, row["receipt"]
        pool = process_pool(receipt)
        for seconds in rust:
            matches = [path for path in pool if read(path).get("quantitative_benchmark")
                       and read(path).get("elapsed_seconds") == seconds]
            assert len(matches) == 1, (row["receipt"], seconds, len(matches))
            valid_process(matches[0], seconds)
            rust_processes.add(matches[0])
        candidate_median, rust_median = statistics.median(values), statistics.median(rust)
        timestamp = statistics.median(births)
        hours = (timestamp - timeline["t0_timestamp"]) / 3600
        assert len(values) == row["n"]
        assert math.isclose(candidate_median, row["seconds"], abs_tol=1e-10, rel_tol=0)
        assert math.isclose(rust_median, row["rust_seconds"], abs_tol=1e-10, rel_tol=0)
        assert math.isclose(candidate_median / rust_median, row["x_rust"], abs_tol=1e-10, rel_tol=0)
        assert math.isclose(timestamp, row["timestamp"], abs_tol=1e-6, rel_tol=0)
        assert math.isclose(hours, row["hours"], abs_tol=1e-9, rel_tol=0)
        records.append({"receipt": row["receipt"], "n": len(values), "rust_n": len(rust),
                        "candidate_seconds": candidate_median, "rust_seconds": rust_median,
                        "x_rust": candidate_median / rust_median, "hours": hours})
    assert len(candidates) == 732 and len(records) == 120
    first, last = records[0], records[-1]
    report = {"status": "passed", "cohorts": len(records), "unique_candidate_processes": len(candidates),
              "unique_rust_processes": len(rust_processes), "hashed_evidence_files": len(checked),
              "full_input_bases": 125000000, "input_sha256": INPUT_SHA,
              "single_process_cohorts": sum(r["n"] == 1 for r in records),
              "raw_runtime_speedup": first["candidate_seconds"] / last["candidate_seconds"],
              "raw_runtime_reduction_percent": 100 * (1 - last["candidate_seconds"] / first["candidate_seconds"]),
              "final_speed_advantage_percent": 100 * (last["rust_seconds"] / last["candidate_seconds"] - 1),
              "normalized_ratio_drop": first["x_rust"] / last["x_rust"],
              "timestamp_basis": "Median process launch, not commit time or completion time",
              "timeline_sha256": digest(HERE / "timeline.json"),
              "auditor_sha256": digest(Path(__file__)), "records": records}
    (output / "receipt-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
