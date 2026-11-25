"""Retime both pinned corpora against the original level-12 peers."""

from argparse import ArgumentParser
from pathlib import Path
from runpy import run_path
import subprocess
import sys

from rebuild import HERE, PARENT, checked, read, sha, write


def actor(build, role, filename):
    path = build / role / filename
    receipt = read(build / role / "receipt.json")
    key = "worker_sha256" if filename == "bound/mech-worker" else "silesia_actor_sha256"
    checked(path, receipt[key])
    if filename == "bound/mech-worker":
        checked(path.parent / "metadata.json", receipt["artifacts"]["metadata.json"])
    return path


def capture_fixture_warmups(program):
    patches = (
        ("        for actor in warmup_order:",
         "        warmups = {}\n        for actor in warmup_order:"),
        ("            assert valid(json.loads(worker.line()),case,actor)['warmup']",
         "            observation = valid(json.loads(worker.line()),case,actor)\n"
         "            assert observation['warmup']\n"
         "            warmups[actor] = dict(calls=int(calls), seconds=float(seconds), "
         "observation=observation)"),
        ("        persist(lambda:(folder/'observations.json.gz').write_bytes(compressed))",
         "        persist(lambda:(folder/'observations.json.gz').write_bytes(compressed))\n"
         "        persist(lambda:(folder/'warmups.json').write_text(json.dumps(warmups)+'\\n'))"),
    )
    for old, new in patches:
        if program.count(old) != 1:
            raise ValueError("Pinned fixture warmup recording anchor changed.")
        program = program.replace(old, new)
    return program


def suite81(out, packets, build, control_build, control, candidate, labels=None, *, retain_warmups=False):
    previous = packets / "mechdeflate-81-v1"
    routes = packets / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    helpers = run_path(str(routes / "replay_timings.py"))
    reference = run_path(str(previous / "replay_timings.py"))["prepare"](out, helpers)
    controller = out / "controller.py"
    if retain_warmups:
        controller.write_text(capture_fixture_warmups(controller.read_text()))
    bindings = [actor(control_build, control, "bound/mech-worker").parent,
                actor(build, candidate, "bound/mech-worker").parent]
    runs = []
    role = "cranelift"
    for order in ("forward", "reverse"):
        folder = out / f"{role}-{order}"
        command = [sys.executable, "-B", controller, folder, *bindings]
        if order == "reverse":
            command.append(order)
        subprocess.run(command, check=True)
        complete = read(folder / "complete.json")
        assert (complete["cases"], complete["balanced_blocks_per_case"], complete["timed_calls"]) == (81, 96, 982656)
        summary = read(folder / "summary.json")
        runs.append({"order": order, "summary_sha256": sha(folder / "summary.json"), "results": summary})
    write(out / f"{role}-results.json", {
        "complete": True, "blocks_per_case": 96, "controller_sha256": sha(controller), "runs": runs,
    })
    subprocess.run([sys.executable, "-B", routes / "verify_timings.py", out, role,
                    out / "pinned-peers/libdeflate-output-oracle.json"], check=True)
    for run in runs:
        control_label, candidate_label = labels or (control, candidate)
        for label, measured in ((control_label, "mech-control"), (candidate_label, "mech-experiment")):
            wins = {
                peer_label: sum(row["paired_x_" + peer][measured] < 1 for row in run["results"])
                for peer_label, peer in (("reference", reference), ("libdeflate", "libdeflate"))
            }
            print(run["order"], label, wins, flush=True)


def silesia(out, packets, build, corpus, candidate):
    package = packets / "mechdeflate-silesia-v1"
    out.mkdir()
    checked(corpus / "corpus.json", sha(package / "corpus.json"))
    binding = read(package / "binding.json")
    candidate_binding = read(build / candidate / "receipt.json")
    for name, record in binding["actors"].items():
        if name == "mech-candidate":
            path = actor(build, candidate, "silesia-encoder")
            record.clear()
            record.update(sha256=candidate_binding["silesia_actor_sha256"],
                          encoder_sha256=candidate_binding["artifacts"]["program.o"])
        else:
            path = package / "actors" / name
            checked(path, record["sha256"])
        record["path"] = str(path)
    write(out / "binding.json", binding)
    subprocess.run([sys.executable, "-B", package / "silesia_compare.py", "time",
                    "--corpus", corpus, "--builds", package, "--output", out, "--cycles", "1"], check=True)
    complete = read(out / "complete.json")
    assert complete["independent_inflation"] == read(package / "complete.json")["independent_inflation"]
    with (out / "score.log").open("w") as stream:
        subprocess.run([sys.executable, "-B", package / "score_silesia.py", out, corpus / "corpus.json"],
                       stdout=stream, check=True)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--build", type=Path, default=HERE / "actors",
                        help="Use a directory from rebuild.py in place of the timed executables")
    parser.add_argument("--control-build", type=Path,
                        help="Existing build directory for the pinned control worker")
    parser.add_argument("--corpus", type=Path, help="Pinned Silesia corpus and corpus.json")
    parser.add_argument("--suite", choices=("all", "81", "silesia"), default="all")
    parser.add_argument("--bench-root", type=Path, help="Override the benchmark repository location")
    parser.add_argument("--recipe", type=Path, default=HERE / "recipe.json",
                        help="Use a different pinned source and candidate recipe")
    args = parser.parse_args()
    if args.suite in ("all", "silesia") and args.corpus is None:
        parser.error("Provide the full pinned corpus for Silesia.")
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    build = args.build.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True)
    recipe = read(args.recipe.resolve(strict=True))
    candidate, control = recipe["candidate_actor"], recipe["control_actor"]
    if args.suite in ("all", "81"):
        directory = output / "suite81"
        directory.mkdir()
        control_build = args.control_build.resolve(strict=True) if args.control_build else build
        suite81(directory, packets, build, control_build, control, candidate)
    if args.suite in ("all", "silesia"):
        silesia(output / "silesia", packets, build, args.corpus.resolve(strict=True), candidate)


if __name__ == "__main__":
    main()
