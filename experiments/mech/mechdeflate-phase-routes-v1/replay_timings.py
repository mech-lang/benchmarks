"""Replay balanced runtime timings using the published, content-pinned arm64 actors."""
from argparse import ArgumentParser
from collections import defaultdict
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

from run_study import exec_script, read, sha, write

HERE = Path(__file__).resolve().parent
PARENT_PACKET = HERE.parent / "mechdeflate-masked-fields-v1"


def extract_previous(packet, out):
    manifest = read(packet / "raw-manifest.json")
    archive_plan = read(packet / "archive.json")
    assert sha(packet / "raw-manifest.json") == archive_plan["manifest_sha256"]
    paths = [packet / part["file"] for part in archive_plan["parts"]]
    digest = sha256()
    for path, part in zip(paths, archive_plan["parts"], strict=True):
        assert path.stat().st_size == part["bytes"]
        with path.open("rb") as stream:
            checksum = sha256()
            while data := stream.read(1 << 20):
                checksum.update(data)
                digest.update(data)
        assert checksum.hexdigest() == part["sha256"]
    assert digest.hexdigest() == archive_plan["archive_sha256"]
    required = {
        "compare-library.py", "fixtures.json", "pinned-peers/pins.json",
        "pinned-peers/libdeflate-output-oracle.json", "peers/roc-worker", "peers/libdeflate-worker",
        "actors/control/bound/mech-worker", "actors/control/bound/metadata.json",
        *(f"fixtures/{index}/{field}" for index in range(81) for field in ("input", "prefix", "expected")),
    }
    paths_by_digest = defaultdict(list)
    for name in sorted(required):
        pin = manifest["files"][name]
        paths_by_digest[pin["sha256"]].append((name, pin["bytes"]))
    with subprocess.Popen(["/bin/cat", *map(str, paths)], stdout=subprocess.PIPE) as child:
        with tarfile.open(fileobj=child.stdout, mode="r|gz") as archive:
            for member in archive:
                checksum = member.name.removeprefix("blobs/")
                if checksum not in paths_by_digest:
                    continue
                assert member.isfile()
                names = paths_by_digest.pop(checksum)
                data = archive.extractfile(member).read()
                assert sha256(data).hexdigest() == checksum
                for name, size in names:
                    assert len(data) == size
                    destination = out / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
        assert child.wait(timeout=30) == 0
    assert not paths_by_digest


def bind(out):
    inventory_path = out / "fixtures.json"
    fixtures = read(inventory_path)
    assert len(fixtures) == 81
    pins_path = out / "pinned-peers/pins.json"
    pins = read(pins_path)
    assert sha(inventory_path) == pins["input_inventory_sha256"]
    for index, fixture in enumerate(fixtures):
        for field in ("input", "prefix", "expected"):
            path = out / f"fixtures/{index}/{field}"
            fixture[field] = str(path)
            if field in {"input", "expected"}:
                assert sha(path) == fixture[field + "_sha256"]
            else:
                assert path.stat().st_size == fixture["prefix_bytes"]
    write(inventory_path, fixtures)
    roc = out / "peers/roc-worker"
    libdeflate = out / "peers/libdeflate-worker"
    metadata = HERE / "actors/roc-compatible-metadata.json"
    assert sha(metadata) == pins["actors"]["roc"]["metadata_sha256"]
    for peer, worker, arguments in (("roc", roc, [metadata]), ("libdeflate", libdeflate, [])):
        assert sha(worker) == pins["actors"][peer]["binary_sha256"]
        worker.chmod(0o755)
        pins["actors"][peer]["command"] = list(map(str, [worker, *arguments, inventory_path]))
    pins["original_input_inventory_sha256"] = pins["input_inventory_sha256"]
    pins["input_inventory_sha256"] = sha(inventory_path)
    write(pins_path, pins)


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--blocks", type=int, choices=(24, 48, 72, 96), default=96)
    args = parser.parse_args()
    assert os.uname().machine == "arm64" and os.uname().sysname == "Darwin"
    out = args.output.resolve()
    out.mkdir(parents=True)
    extract_previous(PARENT_PACKET, out)
    bind(out)
    control = out / "actors/control/bound"
    (control / "mech-worker").chmod(0o755)
    candidate = out / "actors" / args.role
    candidate.mkdir(parents=True)
    role = read(HERE / "roles.json")[args.role]
    for name, expected in (("mech-worker", role["worker_sha256"]),
                           ("metadata.json", role["artifacts"]["metadata.json"])):
        path = HERE / "actors" / args.role / name
        assert sha(path) == expected
        shutil.copyfile(path, candidate / name)
    (candidate / "mech-worker").chmod(0o755)
    timer = out / "compare-library.py"
    program = timer.read_text()
    needle = "orders = list(permutations(commands))"
    assert program.count(needle) == 1
    program = program.replace(needle, needle + f" * {args.blocks // 24}")
    (out / "controller.py").write_text(program)
    runs = []
    for order in ("forward", "reverse"):
        directory = out / f"{args.role}-{order}"
        exec_script(timer, program, [directory, control, candidate, *([order] if order == "reverse" else [])])
        completion = read(directory / "complete.json")
        assert completion["cases"] == 81 and completion["balanced_blocks_per_case"] == args.blocks
        runs.append({"order": order, "summary_sha256": sha(directory / "summary.json"),
                     "results": read(directory / "summary.json")})
    write(out / f"{args.role}-results.json", {"complete": True, "runs": runs,
                                            "blocks_per_case": args.blocks,
                                            "controller_sha256": sha(out / "controller.py")})


if __name__ == "__main__":
    main()
