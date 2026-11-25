"""Compare pinned level-12 builds on the exact full files from Feldman's benchmark."""
from argparse import ArgumentParser
from contextlib import ExitStack
from hashlib import file_digest, sha256
from itertools import permutations
from math import exp, log
from pathlib import Path
from statistics import mean, median
from subprocess import PIPE, Popen, check_output, run
import json
import zlib

ORDER = ("mech-candidate", "roc", "libdeflate")
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    with path.open("rb") as data:
        return file_digest(data, "sha256").hexdigest()


def bind(builds, output):
    builds_plan = read(builds / "plan.json")
    measurements = read(builds / "comparison.json")
    assert digest(builds / "plan.json") == measurements["plan_sha256"]
    compilers = output / "actors"
    compilers.mkdir()
    main = compilers / "clock.o"
    cc = ["/usr/bin/clang", "-arch", "arm64", "-mmacosx-version-min=15.0"]
    compile_main = [*cc, "-O2", "-std=c17", "-Wall", "-Wextra", "-Werror",
                    "-c", str(HERE / "timed_deployment.c"), "-o", str(main)]
    run(compile_main, check=True)
    actors = {}
    for name in ORDER:
        meta = builds_plan["actors"][name]
        for file, checksum in meta["host_inputs_sha256"].items():
            assert digest(Path(file)) == checksum
        trial = builds / "warmup" / name
        rel = "frontend/program.o" if name.startswith("mech-") else Path(meta["reference_object"]).name
        encoder = trial / rel
        assert digest(encoder) == measurements["warmup"][name]["encoder_sha256"]
        link = meta["link"].copy()
        main_at, = [i for i, arg in enumerate(link) if Path(arg).name == "main.o"]
        link[main_at] = str(main)
        link[link.index(meta["reference_object"])] = str(encoder)
        executable = compilers / name
        link[link.index("-o") + 1] = str(executable)
        run(link, check=True)
        actors[name] = {"path": str(executable), "command": link, "sha256": digest(executable),
                        "encoder_sha256": digest(encoder)}
    save(output / "binding.json", {"common_host_command": compile_main, "actors": actors,
                                  "common_host_source_sha256": digest(HERE / "timed_deployment.c"),
                                  "original_build_plan_sha256": digest(builds / "plan.json")})


def verify(input_path, pin, actors, order=ORDER):
    raw = input_path.read_bytes()
    assert len(raw) == pin["bytes"] and sha256(raw).hexdigest() == pin["sha256"]
    results = {}
    for name in order:
        compressed = check_output([actors[name]["path"], input_path, "--verify"])
        assert zlib.decompress(compressed, -15) == raw
        results[name] = {"bytes": len(compressed), "sha256": sha256(compressed).hexdigest()}
    return results


def balanced_samples(case, input_path, actors, verified, order, cycles):
    with ExitStack() as resources:
        workers = {name: resources.enter_context(Popen([actors[name]["path"], input_path],
                                                       stdin=PIPE, stdout=PIPE))
                   for name in order}
        for worker in workers.values():
            assert worker.stdout.readline() == b"READY\n"

        def sample(name):
            worker = workers[name]
            worker.stdin.write(b"N")
            worker.stdin.flush()
            ns, size = map(int, worker.stdout.readline().split())
            assert ns > 0 and size == verified[name]["bytes"], (case, name)
            return ns

        warmup = {name: sample(name) for name in order}
        blocks = []
        for pairing in list(permutations(order)) * cycles:
            blocks.append({"order": pairing, "ns": {name: sample(name) for name in pairing}})
        for worker in workers.values():
            worker.stdin.write(b"Q")
            worker.stdin.flush()
            assert worker.wait() == 0
    return blocks, warmup


def measure_case(case, input_path, actors, verified, order, cycles):
    blocks, warmup = balanced_samples(case, input_path, actors, verified, order, cycles)
    medians = {name: median(row["ns"][name] for row in blocks) for name in order}
    paired = {peer: exp(mean(log(row["ns"]["mech-candidate"] / row["ns"][peer])
                            for row in blocks)) for peer in ("roc", "libdeflate")}
    roc_c = exp(mean(log(row["ns"]["roc"] / row["ns"]["libdeflate"]) for row in blocks))
    return {"case": case, "median_ns": medians, "mech_paired_x_peer": paired,
            "roc_paired_x_libdeflate": roc_c, "blocks": blocks, "warmup_ns": warmup}


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("mode", choices=("bind", "time"))
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--builds", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=1)
    args = parser.parse_args()
    out = args.output
    if args.mode == "bind":
        out.mkdir()
        bind(args.builds, out)
        return
    assert args.cycles >= 1
    corpus = read(args.corpus / "corpus.json")
    actors = read(out / "binding.json")["actors"]
    assert all(digest(Path(row["path"])) == row["sha256"] for row in actors.values())
    cases = list(corpus["files"])
    verified = {}
    observations = {}
    for direction in ("forward", "reverse"):
        rows = observations[direction] = []
        for case in (cases if direction == "forward" else reversed(cases)):
            input_path = args.corpus / case
            if direction == "forward":
                verified[case] = verify(input_path, corpus["files"][case], actors)
            order = ORDER if direction == "forward" else ORDER[::-1]
            result = measure_case(case, input_path, actors, verified[case], order, args.cycles)
            rows.append(result)
            save(out / ("timings-" + direction + ".json"), rows)
            print(direction, case, {n: round(v, 6) for n, v in result["mech_paired_x_peer"].items()},
                  "roc/C", round(result["roc_paired_x_libdeflate"], 6), flush=True)
    for direction, rows in observations.items():
        assert len(rows) == 12 and len(verified) == 12
        assert all(len(row["blocks"]) == len(list(permutations(ORDER))) * args.cycles for row in rows)
    save(out / "complete.json", {"corpus_sha256": digest(args.corpus / "corpus.json"),
                                 "binding_sha256": digest(out / "binding.json"),
                                 "independent_inflation": verified, "cases": len(cases),
                                 "balanced_blocks_per_order_and_case": 6 * args.cycles})


if __name__ == "__main__":
    main()
