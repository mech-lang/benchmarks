"""Verify the recorded run and independently recompute its scores."""

from argparse import ArgumentParser
import json
from pathlib import Path
from runpy import run_path
import subprocess
import sys
import tarfile

from rebuild import HERE, PARENT, checked, read


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New extraction directory")
    parser.add_argument("--record", type=Path, default=HERE, help="Directory with archived observations")
    parser.add_argument("--bench-root", type=Path, help="Override the benchmark repository location")
    args = parser.parse_args()
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    record = args.record.resolve(strict=True)
    archive = record / "observations.tar.gz"
    manifest = read(record / "observations.json")
    checked(archive, manifest["archive_sha256"])
    root = args.output.resolve()
    root.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as data:
        files = data.getmembers()
        assert len(files) == len(manifest["files"])
        assert all(item.isfile() and manifest["files"][item.name]["bytes"] == item.size for item in files)
        data.extractall(root, filter="data")
    for name, pin in manifest["files"].items():
        checked(root / name, pin["sha256"])

    suite = root / "suite81"
    routes = packets / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    verifier = run_path(str(routes / "verify_timings.py"))["verify"]
    oracle = {row["case"]: row for row in read(suite / "pinned-peers/libdeflate-output-oracle.json")}
    result = verifier(suite, suite / "cranelift-results.json", "cranelift", oracle)
    print(json.dumps(result, indent=2))

    silesia = root / "silesia"
    if "silesia/complete.json" not in manifest["files"]:
        return
    package = packets / "mechdeflate-silesia-v1"
    assert read(silesia / "complete.json")["independent_inflation"] == read(
        package / "complete.json"
    )["independent_inflation"]
    original_score = read(silesia / "scores.json")
    subprocess.run(
        [sys.executable, "-B", package / "score_silesia.py", silesia, package / "corpus.json"],
        check=True, stdout=subprocess.DEVNULL,
    )
    assert original_score == read(silesia / "scores.json")
    print("Verified both Silesia orders, all 12 streams and all paired ratios.")


if __name__ == "__main__":
    main()
