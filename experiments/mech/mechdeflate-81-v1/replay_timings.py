"""Replay both 96-block orders for the published 81-case arm64 workers."""

from argparse import ArgumentParser
from pathlib import Path
from runpy import run_path
import platform
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "mechdeflate-phase-routes-v1"
CANDIDATE = "short-prefix-copy"


def prepare(out, helpers):
    read, sha, write = (helpers[key] for key in ("read", "sha", "write"))
    binding = read(HERE / "actors/bindings.json")
    helpers["extract_previous"](helpers["PARENT_PACKET"], out)
    assert sha(out / "fixtures.json") == binding["inventory_sha256"]
    oracle = out / "pinned-peers/libdeflate-output-oracle.json"
    assert sha(oracle) == binding["oracle_sha256"]
    helpers["bind"](out)
    fixtures = read(out / "fixtures.json")
    names = sorted(row["name"] for row in fixtures)
    assert len(names) == len(set(names)) == 81
    assert sorted(row["case"] for row in read(oracle)) == names

    pins_file = out / "pinned-peers/pins.json"
    pins = read(pins_file)
    assert pins["level"] == 12 and pins["libdeflate_source"]["version"] == "1.26"
    reference, = set(pins["actors"]) - {"libdeflate"}
    for label, peer in (("reference", reference), ("libdeflate", "libdeflate")):
        observed = pins["actors"][peer]
        for key, digest in binding["peers"][label].items():
            assert observed[key] == digest, (label, key)
        command = observed["command"]
        assert sha(command[0]) == observed["binary_sha256"]
        if "metadata_sha256" in observed:
            metadata = out / "peers/reference-metadata.json"
            shutil.copyfile(command[1], metadata)
            assert sha(metadata) == observed["metadata_sha256"]
            command[1] = str(metadata)
        assert Path(command[-1]) == out / "fixtures.json"
    write(pins_file, pins)

    for role, files in binding["mech"].items():
        destination = out / "actors" / role / "bound"
        destination.mkdir(parents=True, exist_ok=True)
        for name, key in (("mech-worker", "binary_sha256"), ("metadata.json", "metadata_sha256")):
            source = HERE / "actors" / role / name
            assert sha(source) == files[key], (role, name)
            shutil.copyfile(source, destination / name)
            assert sha(destination / name) == files[key]
        (destination / "mech-worker").chmod(0o755)

    timer = (out / "compare-library.py").read_text()
    orders = "orders = list(permutations(commands))"
    selected = "selected = {case['name'] for case in cases}"
    assert timer.count(orders) == 1 and timer.count(selected) == 1
    controller = out / "controller.py"
    controller.write_text(timer.replace(orders, orders + " * 4").replace(selected, f"selected = set({names!r})"))
    assert sha(controller) == binding["controller_sha256"]
    write(out / "prepared.json", {
        "blocks_per_case": 96, "cases": len(names),
        "controller_sha256": sha(controller), "oracle_sha256": sha(oracle),
        "original_inventory_sha256": binding["inventory_sha256"],
        "relocated_inventory_sha256": sha(out / "fixtures.json"),
        "mech": binding["mech"], "peers": binding["peers"],
    })
    return reference


def run_timings(out, helpers, reference):
    read, sha, write = (helpers[key] for key in ("read", "sha", "write"))
    controller = out / "controller.py"
    actors = out / "actors"
    runs = []
    for order in ("forward", "reverse"):
        directory = out / f"{CANDIDATE}-{order}"
        command = [sys.executable, controller, directory, actors / "control/bound", actors / CANDIDATE / "bound"]
        if order == "reverse":
            command.append("reverse")
        subprocess.run(command, check=True)
        completed = read(directory / "complete.json")
        assert completed["cases"] == 81 and completed["balanced_blocks_per_case"] == 96
        assert completed["timed_calls"] == 982656
        runs.append({"order": order, "summary_sha256": sha(directory / "summary.json"),
                     "results": read(directory / "summary.json")})

    write(out / f"{CANDIDATE}-results.json", {
        "complete": True, "blocks_per_case": 96, "controller_sha256": sha(controller), "runs": runs,
    })
    subprocess.run([sys.executable, PREVIOUS / "verify_timings.py", out, CANDIDATE,
                    out / "pinned-peers/libdeflate-output-oracle.json"], check=True)
    wins = {}
    for run in runs:
        wins[run["order"]] = {
            label: sum(row["paired_x_" + peer]["mech-experiment"] < 1 for row in run["results"])
            for label, peer in (("reference", reference), ("libdeflate", "libdeflate"))
        }
    write(out / "runtime-wins.json", wins)
    for order, peers in wins.items():
        print(f"{order}: reference {peers['reference']}/81, libdeflate {peers['libdeflate']}/81")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New or empty output directory")
    parser.add_argument("--prepare-only", action="store_true", help="Verify and stage all runtime inputs, then exit")
    args = parser.parse_args()
    if not __debug__:
        parser.error("Use the default Python assertion setting for the archived verifier")
    if not args.prepare_only and (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        parser.error("Full timing requires Apple Silicon macOS")
    out = args.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Choose a new or empty output directory")
    out.mkdir(parents=True, exist_ok=True)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(PREVIOUS))
    helpers = run_path(str(PREVIOUS / "replay_timings.py"))
    reference = prepare(out, helpers)
    print(f"Prepared all four actors, 81 fixtures and the qualified controller in {out}", flush=True)
    if not args.prepare_only:
        run_timings(out, helpers, reference)


if __name__ == "__main__":
    main()
