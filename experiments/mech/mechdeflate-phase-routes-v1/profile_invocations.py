"""Sample complete encoder calls and capture exact diagnostic block visits."""
from argparse import ArgumentParser
from hashlib import file_digest
import json
from pathlib import Path
import subprocess


def digest(path):
    with Path(path).open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def line(worker):
    result = worker.stdout.readline()
    if not result:
        raise RuntimeError(f"Worker exited with {worker.poll()}")
    return result.rstrip("\n")


def send(worker, command):
    worker.stdin.write(command)
    worker.stdin.flush()


def collect(command, fixtures, selected, output, actor, seconds):
    records = {}
    output.mkdir()
    with (output / "worker.stderr").open("w") as errors:
        with subprocess.Popen(list(map(str, command)), stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=errors, text=True) as worker:
            assert line(worker) == "SESSION_READY"
            try:
                for index, case in enumerate(fixtures):
                    name = case["name"]
                    if name not in selected:
                        continue
                    send(worker, f"C\t{index}\t0\n")
                    assert line(worker) == f"CASE_READY\t{name}"
                    sample_path = output / (name + ".sample.txt")
                    if seconds:
                        with (output / (name + ".sample.stderr")).open("w") as detail:
                            with subprocess.Popen(["/usr/bin/sample", str(worker.pid),
                                                   str(seconds), "1", "-file", str(sample_path)],
                                                  stdout=detail, stderr=detail) as sampler:
                                while sampler.poll() is None:
                                    send(worker, "W")
                                    assert line(worker).startswith(f"WARMUP_DONE\t{name}\t")
                                if sampler.returncode:
                                    raise RuntimeError(f"Sampling failed for {actor}/{name}: {detail.name}")
                    send(worker, "NN")
                    observations = [json.loads(line(worker)), json.loads(line(worker))]
                    assert all(row["case"] == name for row in observations)
                    assert observations[0]["warmup"] and observations[1]["profile"]
                    for row in observations:
                        for key in ("independent_inflation", "input_alias_unchanged",
                                    "borrowed_output_alias_unchanged"):
                            assert row[key], (actor, name, key)
                    if "block_counts" in observations[0]:
                        assert observations[0]["block_counts"] == observations[1]["block_counts"]
                    assert line(worker) == f"CASE_DONE\t{name}"
                    records[name] = observations
                    print(actor, name, flush=True)
            finally:
                send(worker, "Q\n")
                assert worker.wait() == 0
    assert set(records) == selected
    (output / "observations.json").write_text(json.dumps({
        "command": list(map(str, command)), "worker_sha256": digest(command[0]),
        "input_inventory_sha256": digest(command[-1]), "records": records,
    }, indent=2) + "\n")


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("--pinned-root", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sampling-seconds", type=int, default=2)
    parser.add_argument("--actor", action="append", required=True)
    arguments = parser.parse_args()
    fixture_file = arguments.pinned_root / "fixtures.json"
    fixtures = json.loads(fixture_file.read_text())
    pins = json.loads((arguments.pinned_root / "pinned-peers/pins.json").read_text())
    assert digest(fixture_file) == pins["input_inventory_sha256"]
    selected = {case["case"] for case in json.loads(arguments.baseline.read_text())["cohort"]}
    arguments.output.mkdir()
    for actor in arguments.actor:
        seconds = arguments.sampling_seconds
        if actor == "mech":
            command = [arguments.control / "bound/mech-worker",
                       arguments.control / "bound/metadata.json", fixture_file]
        elif actor in {"roc", "libdeflate"}:
            command = pins["actors"][actor]["command"]
            assert digest(command[0]) == pins["actors"][actor]["binary_sha256"]
        else:
            command = [arguments.control / f"counts-word-reuse-v1-{actor}/mech-worker",
                       arguments.control / "canonical-counter-input/bound/metadata.json", fixture_file]
            seconds = 0
        collect(command, fixtures, selected, arguments.output / actor, actor, seconds)


if __name__ == "__main__":
    main()
