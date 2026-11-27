"""Retime both pinned corpora against the original level-12 peers."""

from argparse import ArgumentParser
from pathlib import Path
from runpy import run_path
from shutil import copyfile
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


def fixture_campaign_controller(program, cycles):
    if cycles == 2:
        permutations = "orders = list(permutations(commands)) * 4"
        startup = "        workers[actor] = Worker(actor,out)\n"
        for anchor in (permutations, startup):
            if program.count(anchor) != 1:
                raise ValueError("Pinned fixture crossover anchor changed.")
        program = program.replace(permutations, permutations.removesuffix("4") + "2")
        program = program.replace(
            startup, startup + "    persist(lambda:(out/'worker-startup.json').write_text(json.dumps(list(workers))))\n"
        )
    elif cycles != 4:
        raise ValueError("Expected two cycles per crossover leg or four for the historical run.")
    return capture_fixture_warmups(program)


def prepare_fixture_inputs(out, packets):
    previous = packets / "mechdeflate-81-v1"
    routes = packets / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    try:
        helpers = run_path(str(routes / "replay_timings.py"))
        return run_path(str(previous / "replay_timings.py"))["prepare"](out, helpers)
    finally:
        sys.path.pop(0)


def prepare_fixture_stage(stage_root, packets):
    from compare_rebuilt import write_new
    from verify import FIXTURE_STAGING, fixture_stage_inventory, require

    require(stage_root.is_absolute() and stage_root == stage_root.resolve()
            and stage_root.name == FIXTURE_STAGING["root_basename"], "Expected the canonical campaign stage path.")
    require(packets.is_absolute() and packets == packets.resolve(strict=True),
            "Expected the canonical benchmark packet directory.")
    receipt = stage_root.parent / FIXTURE_STAGING["receipt_basename"]
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError(receipt)
    stage_root.mkdir()
    reference = prepare_fixture_inputs(stage_root, packets)
    active = FIXTURE_STAGING["active_controller"]
    program = fixture_campaign_controller((stage_root / "controller.py").read_text(), 2)
    with (stage_root / active).open("x") as controller:
        controller.write(program)
    files = fixture_stage_inventory(stage_root)
    for name in files:
        item = stage_root / name
        item.chmod(0o555 if item.stat().st_mode & 0o111 else 0o444)
    for directory in stage_root.rglob("*"):
        if directory.is_dir():
            directory.chmod(0o555)
    stage_root.chmod(0o555)
    write_new(receipt, {
        "schema": "mech.native-route-fixture-stage.v1",
        "root": str(stage_root),
        "active_controller": active,
        "reference_actor": reference,
        "cases": 81,
        "cycles_per_leg": 2,
        "permutations": 24,
        "files": files,
    })
    return {"root": str(stage_root), "receipt": str(receipt), "receipt_sha256": sha(receipt)}


def fixture_command(controller, prefix, bindings, order):
    command = [sys.executable, "-B", str(controller), str(prefix), *map(str, bindings)]
    if order == "reverse":
        command.append(order)
    return command


def suite81(out, packets, build, control_build, control, candidate, labels=None, *,
            retain_warmups=False, orders=("forward", "reverse"), cycles=4, fixture_stage=None):
    routes = packets / "mechdeflate-phase-routes-v1"
    if fixture_stage is None:
        reference = prepare_fixture_inputs(out, packets)
        controller = out / "controller.py"
        if retain_warmups:
            controller.write_text(fixture_campaign_controller(controller.read_text(), cycles))
    else:
        from compare_rebuilt import write_new
        from verify import FIXTURE_WITNESSES, require, verify_fixture_stage

        stage_root = Path(fixture_stage["root"])
        stage = verify_fixture_stage(fixture_stage, stage_root.parent)
        require(retain_warmups and len(orders) == 1 and cycles == stage["cycles_per_leg"],
                "The shared stage supplies one complete crossover leg.")
        require(out.is_absolute() and out == out.resolve(strict=True) and not out.is_relative_to(stage_root),
                "Fixture results must use a canonical directory outside the shared stage.")
        reference = stage["reference_actor"]
        controller = stage_root / stage["active_controller"]
        for local, staged in FIXTURE_WITNESSES.items():
            witness = out / local
            witness.parent.mkdir(parents=True, exist_ok=True)
            copyfile(stage_root / staged, witness)
    blocks = cycles * 24
    bindings = [actor(control_build, control, "bound/mech-worker").parent,
                actor(build, candidate, "bound/mech-worker").parent]
    runs = []
    role = "cranelift"
    for order in orders:
        folder = out / f"{role}-{order}"
        command = fixture_command(controller, folder, bindings, order)
        if fixture_stage is not None:
            require(folder == folder.resolve() and not folder.is_relative_to(stage_root),
                    "Fixture output prefix must be outside the shared stage.")
            write_new(out / "fixture-execution.json", {
                "fixture_stage_receipt_sha256": fixture_stage["receipt_sha256"],
                "controller": str(controller),
                "controller_sha256": stage["files"][stage["active_controller"]]["sha256"],
                "command": command,
                "output_prefix": str(folder),
                "cwd": str(Path.cwd()),
            })
        subprocess.run(command, check=True)
        complete = read(folder / "complete.json")
        assert (complete["cases"], complete["balanced_blocks_per_case"], complete["timed_calls"]) == (
            81, blocks, 982656 * cycles // 4
        )
        summary = read(folder / "summary.json")
        runs.append({"order": order, "summary_sha256": sha(folder / "summary.json"), "results": summary})
    write(out / f"{role}-results.json", {
        "complete": True, "blocks_per_case": blocks, "controller_sha256": sha(controller), "runs": runs,
    })
    command = [sys.executable, "-B", routes / "verify_timings.py", out, role,
               out / "pinned-peers/libdeflate-output-oracle.json"]
    if len(orders) == 1:
        command.extend(("--order", orders[0]))
    subprocess.run(command, check=True)
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
