"""Compare two explicitly rebuilt native compilers on the fixed regression corpora."""

from argparse import ArgumentParser
from collections import Counter
from itertools import permutations
from math import exp, log
from pathlib import Path
import platform
from runpy import run_path
from statistics import mean, median
from subprocess import check_output

from rebuild import HERE, PARENT, checked, configuration, configuration_sha256, read, sha, write
from replay import actor, suite81


PAIRS = (("frozen", "reconciled"), ("reconciled", "configured"), ("frozen", "configured"))
ORDERS = ("forward", "reverse")


def bind(label, build, recipe_path):
    recipe = read(recipe_path)
    role = recipe["candidate_actor"]
    if role == "standard" or Path(role).name != role or role in (".", ".."):
        raise ValueError(f"{label}: select the actual candidate in a pinned recipe.")
    role_recipe = recipe["roles"][role]
    receipt_path = build / role / "receipt.json"
    receipt = read(receipt_path)
    config = configuration(recipe, role_recipe)
    expected = {
        "source_commit": recipe["source_commit"],
        "recipe_sha256": sha(recipe_path),
        "configuration": config,
        "configuration_sha256": configuration_sha256(config),
        "artifacts": role_recipe["artifacts"],
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"{label}: rebuild receipt does not match the pinned {key}.")
    for filename, digest in expected["artifacts"].items():
        checked(build / role / "bound" / filename, digest)
    for path, digest in config["profiles_sha256"].items():
        checked(HERE / path, digest)
    checked(build / "libmech_gpu_runtime.rlib", receipt["runtime_sha256"])
    checked(build / "silesia-support/libmech_silesia.a", receipt["silesia_runtime_sha256"])
    checked(build / "silesia-support/clock.o", receipt["silesia_clock_sha256"])
    checked(HERE / "support/mimalloc-2.1.7.o", receipt["allocator_sha256"])
    worker = actor(build, role, "bound/mech-worker")
    encoder = actor(build, role, "silesia-encoder")
    return {
        "label": label, "build_directory": str(build), "role": role,
        "recipe": str(recipe_path), "rebuild_receipt": str(receipt_path),
        "rebuild_receipt_sha256": sha(receipt_path),
        "source_commit": receipt["source_commit"], "source_sha256": receipt["source_sha256"],
        "recipe_sha256": receipt["recipe_sha256"], "compiler_sha256": receipt["compiler_sha256"],
        "configuration": config, "configuration_sha256": receipt["configuration_sha256"],
        "artifacts": receipt["artifacts"],
        "81": {
            "path": str(worker), "sha256": receipt["worker_sha256"],
            "runtime_sha256": receipt["runtime_sha256"],
            "boundary": "private heap initialization through closed compression, output acquisition and heap cleanup",
        },
        "silesia": {
            "path": str(encoder), "sha256": receipt["silesia_actor_sha256"],
            "runtime_sha256": receipt["silesia_runtime_sha256"],
            "clock_sha256": receipt["silesia_clock_sha256"],
            "boundary": "one level-12 deploy_encode call with preloaded input",
        },
        "allocator_sha256": receipt["allocator_sha256"],
    }


def compare81(out, packets, control, candidate):
    out.mkdir()
    suite81(out, packets, Path(candidate["build_directory"]), Path(control["build_directory"]),
            control["role"], candidate["role"], labels=(control["label"], candidate["label"]))
    results = out / "cranelift-results.json"
    runs = read(results)["runs"]
    paths = {}
    for run in runs:
        order = run["order"]
        folder = out / f"cranelift-{order}"
        pins = folder / "pins.json"
        bound = read(pins)["actors"]
        reference, = set(bound) - {"mech-control", "mech-experiment", "libdeflate"}
        peers = (("libdeflate", "libdeflate"), ("reference", reference))
        wins = {}
        for name, side in (("mech-control", control), ("mech-experiment", candidate)):
            command = bound[name]["command"]
            if Path(command[0]).resolve() != Path(side["81"]["path"]):
                raise ValueError(f"{name}: timing command did not use the bound executable.")
            checked(Path(command[0]), side["81"]["sha256"])
            wins[side["label"]] = {
                label: sum(row["paired_x_" + peer][name] < 1 for row in run["results"])
                for label, peer in peers
            }
        paths[order] = {
            "actor_pins": str(pins), "actor_pins_sha256": sha(pins),
            "raw": str(folder),
            "reference_comparator_wins": wins,
            # Both terms use the same block means for the shared comparator.
            "cases": [{"case": row["case"],
                       "candidate_x_control": row["paired_x_libdeflate"]["mech-experiment"] /
                       row["paired_x_libdeflate"]["mech-control"]}
                      for row in run["results"]],
        }
    return {"orders": paths, "results": str(results), "results_sha256": sha(results),
            "verification": str(out / "cranelift-verified.json")}


def compare_silesia(out, packets, corpus, control, candidate):
    out.mkdir()
    package = packets / "mechdeflate-silesia-v1"
    checks = run_path(str(package / "silesia_compare.py"))
    inventory = corpus / "corpus.json"
    corpus_sha256 = checked(inventory, sha(package / "corpus.json"))
    inputs = read(inventory)["files"]
    assert len(inputs) == 12
    actors = {side["label"]: side["silesia"] for side in (control, candidate)}
    matched = tuple(actors)
    verified = {case: checks["verify"](corpus / case, pin, actors, matched) for case, pin in inputs.items()}
    assert all(row[matched[0]] == row[matched[1]] for row in verified.values())
    verification = out / "independent-inflation.json"
    write(verification, verified)
    observations = {}
    for direction, order in zip(ORDERS, (matched, matched[::-1]), strict=True):
        rows = []
        raw = out / f"timings-{direction}.json"
        for case in (inputs if direction == "forward" else reversed(inputs)):
            blocks, warmup = checks["balanced_samples"](case, corpus / case, actors, verified[case], order, 3)
            assert Counter(tuple(block["order"]) for block in blocks) == Counter({
                permutation: 3 for permutation in permutations(matched)
            })
            ratio = exp(mean(log(block["ns"][matched[1]] / block["ns"][matched[0]]) for block in blocks))
            rows.append({"case": case, "candidate_x_control": ratio, "blocks": blocks, "warmup_ns": warmup,
                         "median_ns": {name: median(block["ns"][name] for block in blocks) for name in order}})
            write(raw, rows)
            print(direction, case, f"{ratio:.6f}", flush=True)
        observations[direction] = {"raw": str(raw), "raw_sha256": sha(raw),
                                   "cases": [{"case": row["case"], "candidate_x_control": row["candidate_x_control"]}
                                             for row in rows]}
    return {"corpus_sha256": corpus_sha256, "orders": observations, "blocks_per_order_and_case": 6,
            "verification": str(verification), "verification_sha256": sha(verification)}


def main():
    parser = ArgumentParser(description=__doc__)
    for side in ("control", "candidate"):
        parser.add_argument(f"--{side}", required=True, choices=("frozen", "reconciled", "configured"))
        parser.add_argument(f"--{side}-build", required=True, type=Path)
        parser.add_argument(f"--{side}-recipe", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bench-root", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--suite", choices=("81", "silesia", "all"), default="all")
    parser.add_argument("--prepare-only", action="store_true", help="Verify the rebuilt actors and write bindings")
    args = parser.parse_args()
    if not __debug__:
        parser.error("Use Python with assertions enabled.")
    if (args.control, args.candidate) not in PAIRS:
        parser.error("Choose reconciled versus frozen, configured versus reconciled or configured versus frozen.")
    if args.suite != "81" and not args.prepare_only and args.corpus is None:
        parser.error("Supply the pinned full Silesia corpus.")
    if not args.prepare_only and (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        parser.error("Timing requires Apple Silicon macOS.")
    control = bind(args.control, args.control_build.resolve(strict=True), args.control_recipe.resolve(strict=True))
    candidate = bind(args.candidate, args.candidate_build.resolve(strict=True), args.candidate_recipe.resolve(strict=True))
    if control["build_directory"] == candidate["build_directory"] or control["source_commit"] == candidate["source_commit"]:
        parser.error("Supply separately rebuilt compiler trees at their distinct source pins.")
    out = args.output.resolve()
    out.mkdir(parents=True)
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    host = {
        "os": platform.system(), "os_version": platform.mac_ver()[0], "architecture": platform.machine(),
    }
    if host["os"] == "Darwin":
        host["cpu"] = check_output(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    binding = {"control": control, "candidate": candidate, "host": host}
    write(out / "binding.json", binding)
    if args.prepare_only:
        return
    measurements = {}
    if args.suite in ("81", "all"):
        measurements["81"] = compare81(out / "suite81", packets, control, candidate)
    if args.suite in ("silesia", "all"):
        measurements["silesia"] = compare_silesia(out / "silesia", packets, args.corpus.resolve(strict=True),
                                                 control, candidate)
    for side in (control, candidate):
        for suite in ("81", "silesia"):
            checked(Path(side[suite]["path"]), side[suite]["sha256"])
    write(out / "comparison.json", {"binding_sha256": sha(out / "binding.json"), "measurements": measurements})


if __name__ == "__main__":
    main()
