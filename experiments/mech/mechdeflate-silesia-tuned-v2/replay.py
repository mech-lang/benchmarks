"""Replay the balanced level-12 Silesia comparison on Apple Silicon."""
from argparse import ArgumentParser
from contextlib import ExitStack
from hashlib import file_digest, sha256
from math import exp, log
from pathlib import Path
from statistics import mean, median
import json
import platform
import subprocess
import zlib

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open("rb") as file:
        return file_digest(file, "sha256").hexdigest()


def verify(input_path, input_pin, stream_pin, actors):
    raw = input_path.read_bytes()
    assert len(raw) == input_pin["bytes"] and sha256(raw).hexdigest() == input_pin["sha256"]
    for name, actor in actors.items():
        stream = subprocess.check_output([actor, input_path, "--verify"])
        assert zlib.decompress(stream, -15) == raw, (input_path.name, name, "inflation")
        assert len(stream) == stream_pin["bytes"] and sha256(stream).hexdigest() == stream_pin["sha256"], (
            input_path.name, name, "stream bytes"
        )
    return stream_pin["bytes"]


def measure(path, actors, actor_order, expected_size, cycles):
    with ExitStack() as resources:
        workers = {}
        for name in actors:
            worker = resources.enter_context(subprocess.Popen([actors[name], path], stdin=subprocess.PIPE,
                                                               stdout=subprocess.PIPE))
            resources.callback(worker.stdin.close)
            assert worker.stdout.readline() == b"READY\n", name
            workers[name] = worker

        def encode(name):
            worker = workers[name]
            worker.stdin.write(b"N")
            worker.stdin.flush()
            ns, size = map(int, worker.stdout.readline().split())
            assert ns > 0 and size == expected_size, (path.name, name, ns, size)
            return ns

        warmup = {name: encode(name) for name in actors}
        rotations = [actor_order[i:] + actor_order[:i] for i in range(len(actor_order))]
        blocks = [{"order": order, "ns": {name: encode(name) for name in order}}
                  for order in rotations * cycles]
        for name, worker in workers.items():
            worker.stdin.write(b"Q")
            worker.stdin.flush()
            assert worker.wait() == 0, name

    medians = {name: median(row["ns"][name] for row in blocks) for name in actors}
    ratios = {
        name: {
            peer: exp(mean(log(row["ns"][name] / row["ns"][peer]) for row in blocks))
            for peer in ("baseline", "libdeflate")
        }
        for name in actors if name != "libdeflate"
    }
    return {"case": path.name, "warmup_ns": warmup, "median_ns": medians,
            "paired_ratio": ratios, "blocks": blocks}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=1)
    args = parser.parse_args()
    if not __debug__ or (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        parser.error("Use the default Python assertion setting on Apple Silicon macOS.")
    if args.cycles < 1 or args.output.exists():
        parser.error("Supply a fresh output path and one or more cycles")
    binding = read(HERE / "binding.json")
    corpus = args.corpus.resolve()
    actors = {name: (HERE / record["path"]).resolve() for name, record in binding["actors"].items()}
    hashes = {name: binding["actors"][name]["sha256"] for name in actors}
    assert all(digest(path) == hashes[name] for name, path in actors.items())
    assert digest(corpus / "corpus.json") == binding["corpus_sha256"]
    inputs = read(corpus / "corpus.json")["files"]
    assert len(inputs) == len(binding["streams"]) == 12 and inputs.keys() == binding["streams"].keys()
    inventory = list(inputs)
    output = {"actors_sha256": hashes, "corpus_sha256": binding["corpus_sha256"],
              "record": {"forward": [], "reverse": []}}
    sizes = {}
    for direction in output["record"]:
        names = list(actors)
        cases, order = (inventory, names) if direction == "forward" else (inventory[::-1], names[::-1])
        for case in cases:
            path = corpus / case
            if case not in sizes:
                sizes[case] = verify(path, inputs[case], binding["streams"][case], actors)
            row = measure(path, actors, order, sizes[case], args.cycles)
            output["record"][direction].append(row)
            args.output.write_text(json.dumps(output, indent=2) + "\n")
            print(direction, case, row["paired_ratio"], flush=True)


if __name__ == "__main__":
    main()
