"""Emit, profile and time private AArch64 phase choices against the pinned control."""
from argparse import ArgumentParser
import ast
from hashlib import file_digest
import json
import os
from pathlib import Path
from runpy import run_path
import shutil
import subprocess
import sys

MATCHER = "mech_compact_numeric_475_vector"
REGISTER_WEIGHTS = "MECH_COMPACT_PHASE_REGISTER_WEIGHTS"
BLOCK_LAYOUT = "MECH_COMPACT_PHASE_BLOCK_LAYOUT"
CHOICES = {
    "reprofiled": {},
    "forward": {"MECH_COMPACT_FORWARD_PHASE_ROUTES": MATCHER},
    "zero": {"MECH_COMPACT_PHASE_BRANCH_ON_ZERO": MATCHER},
    "combined": {"MECH_COMPACT_FORWARD_PHASE_ROUTES": MATCHER,
                 "MECH_COMPACT_PHASE_BRANCH_ON_ZERO": MATCHER},
}
CHOICES["shared-bases"] = CHOICES["combined"] | {"MECH_ARM64_REUSE_PREFETCH_BASES": "1"}
CHOICES["refined"] = CHOICES["combined"] | {"MECH_COMPACT_REFINE_PHASE_PREDICATES": MATCHER}
CHOICES["shared-refined"] = CHOICES["shared-bases"] | CHOICES["refined"]
CLEAN_ENV = {key: value for key, value in os.environ.items() if not key.startswith("MECH_")}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha(path):
    with Path(path).open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def exec_script(path, program, argv, **scope):
    original = sys.argv
    try:
        sys.argv = [str(path), *map(str, argv)]
        exec(compile(program, str(path), "exec"), {"__file__": str(path), "__name__": "__main__", **scope})
    finally:
        sys.argv = original


def bind_recipe(packet):
    recipe = read(packet / "recipes.json")
    flags = recipe["roles"]["control"]["flags"].copy()
    for key in (REGISTER_WEIGHTS, BLOCK_LAYOUT):
        entries = []
        for entry in flags[key].split(";"):
            symbol, relative = entry.split("@", 1)
            profile = packet / relative
            assert sha(profile) == profile.stem
            entries.append(f"{symbol}@{profile}")
        flags[key] = ";".join(entries)
    return recipe, flags


def drop_matcher(flags):
    return flags | {
        key: ";".join(entry for entry in flags[key].split(";") if not entry.startswith(MATCHER + "@"))
        for key in (REGISTER_WEIGHTS, BLOCK_LAYOUT)
    }


def add_profile(flags, key, profile):
    return flags | {key: ";".join((flags[key], f"{MATCHER}@{profile}"))}


def emit(output, flags, args, recipe, driver, template, *, capture=False, expected=None):
    output.mkdir(parents=True)
    source = args.mech_root / recipe["codec_source"]
    assert sha(source) == recipe["codec_source_sha256"]
    inspect = {"MECH_INSPECT_OPTIMIZED_PHASE_CLIF": str(output / (MATCHER + ".clif"))}
    if capture:
        inspect["MECH_INSPECT_PHASE_REGISTER_PROFILE"] = str(output / (MATCHER + ".vcode"))
    command = [str(args.compiler), str(source), str(output / "frontend"), "compact"]
    with (output / "compile.log").open("w") as log:
        subprocess.run(command, cwd=args.mech_root, env=CLEAN_ENV | flags | inspect,
                       stdout=log, stderr=log, check=True)
    artifacts = {name: sha(output / "frontend" / name) for name in recipe["roles"]["control"]["artifacts"]}
    assert artifacts["program.mecb"] == recipe["roles"]["control"]["artifacts"]["program.mecb"]
    if expected:
        assert artifacts == expected
    layout = driver.symbols(output / "frontend/program.o")
    record = {
        "role": output.name, "command": command, "flags": flags, "artifacts": artifacts, "layout": layout,
        "object_sha256": artifacts["program.o"], "source_sha256": sha(source), "compiler_sha256": sha(args.compiler), "text_bytes": layout["text_bytes"],
    }
    write(output / "receipt.json", record)
    driver.link.link_worker(template / "bound", output / "frontend", output / "bound")
    runtime = read(output / "bound/runtime.json")
    write(output / "bound/runtime.json", runtime | {"encoder_text_bytes": layout["text_bytes"]})
    print("EMITTED", output.name, layout["text_bytes"], flush=True)


def count_tools(args, training):
    """Reuse the retained counter instrumentation and its canonical address checks."""
    helper = args.lab / "matcher-word-qualification-v1/counter-bootstrap.py"
    ns = run_path(str(helper))["ns"]
    ns["shapes"]["OUT"] = args.output
    ns["training"] = training
    script = args.lab / "prepare-forwarded-register-study.py"
    content = script.read_text()
    node = next(node for node in ast.parse(content).body if isinstance(node, ast.FunctionDef) and node.name == "count")
    body = ast.get_source_segment(content, node)
    assert body.count("folder=raw/('counts-'+symbol.split('_')[3])") == 1
    body = body.replace("folder=raw/('counts-'+symbol.split('_')[3])",
                        "folder=raw/('counts-word-reuse-v1-'+symbol.split('_')[3])")
    old = "program=original.read_text()"
    assert body.count(old) == 1
    # Reuse the retained proof for NOP alignment before a literal pool.
    patch_script = args.lab / "matcher-bit-fields-tied-study/count.py"
    patch_text = patch_script.read_text()
    patch_node = next(node for node in ast.parse(patch_text).body
                      if isinstance(node, ast.FunctionDef) and node.name == "patch_counter")
    scope = {"ns": ns, "driver": ns["driver"], "Q": args.lab.parents[1],
             "Path": Path, "shutil": shutil, "read": read, "sha": sha, "json": json}
    exec(compile(ast.Module(body=[patch_node], type_ignores=[]),
                 str(patch_script), "exec"), scope)
    exec(compile(body.replace(old, "program=patch_counter(original.read_text())"), str(script), "exec"), scope)
    def count(output, symbol):
        directory = output / ("counts-word-reuse-v1-" + symbol.split("_")[3])
        shape_file = directory / "native-shape.json"
        if shape_file.is_file():
            shape = read(shape_file)
        elif (directory / "counts.json").is_file():
            shape = ns["shapes"]["shape"](str(output), symbol)
            write(shape_file, shape)
        else:
            directory, shape = scope["count"](output, symbol)
            write(shape_file, shape)
        assert shape["object_sha256"] == sha(output / "frontend/program.o")
        return directory, shape

    return ns["driver"], count


def prepare(args):
    baseline = read(args.packet.parent / "mechdeflate-average-margin-v1/baseline.json")
    recipe, control = bind_recipe(args.packet)
    training = {row["case"] for row in baseline["cohort"]} | {
        "prefix-natural-4096", "prefix-natural-8192", "320-overlap",
    }
    fixtures = read(args.lab.parents[1] / "fixtures.json")
    ordered_training = [row["name"] for row in fixtures if row["name"] in training]
    assert len(ordered_training) == 21
    driver, count = count_tools(args, ordered_training)
    template = args.lab / "fp-spill-keep-pairs-study/census/keep-pairs2"
    derive_registers = run_path(str(args.lab / "matcher-bit-fields-tied-study/derive-registers.py"))["derive"]
    derive_layout = run_path(str(args.lab / "derive-coalesced-layout.py"))["derive"]
    if not (args.output / "control").exists():
        emit(args.output / "control", control, args, recipe, driver, template,
             expected=recipe["roles"]["control"]["artifacts"])
        assert sha(args.output / "control/bound/mech-worker") == sha(template / "bound/mech-worker")
    for choice in args.choice:
        unweighted = args.output / (choice + "-unweighted")
        flags = drop_matcher(control) | CHOICES[choice]
        if not (unweighted / "receipt.json").is_file():
            emit(unweighted, flags, args, recipe, driver, template, capture=True)
        else:
            receipt = read(unweighted / "receipt.json")
            assert receipt["flags"] == flags and receipt["compiler_sha256"] == sha(args.compiler)
        count(unweighted, MATCHER)
        weights, proof = derive_registers(unweighted, MATCHER)
        write(unweighted / "weight-proof.json", proof)
        for mode in args.weight:
            weighted = args.output / (choice + "-" + mode + "-unlaid")
            register_file = unweighted / (mode + ".json")
            write(register_file, weights[mode])
            weighted_flags = add_profile(flags, REGISTER_WEIGHTS, register_file)
            emit(weighted, weighted_flags, args, recipe, driver, template)
            visits, shape = count(weighted, MATCHER)
            profile, layout_proof = derive_layout(shape, read(visits / "counts.json"))
            layout_file = weighted / "matcher-layout.json"
            write(layout_file, profile)
            write(weighted / "layout-proof.json", layout_proof)
            final = args.output / (choice + "-" + mode)
            emit(final, add_profile(weighted_flags, BLOCK_LAYOUT, layout_file), args, recipe, driver, template)
            print("PREPARED", final.name, flush=True)


def time_roles(args):
    root = args.lab.parents[1]
    baseline_receiver = args.packet.parent / "mechdeflate-average-margin-v1"
    baseline = read(baseline_receiver / "baseline.json")
    selected = set(baseline["inventory"])
    if args.blocks < 96:
        selected = {row["case"] for row in baseline["cohort"]} | {
            "prefix-natural-4096", "prefix-natural-8192", "320-overlap", "prefix-natural-65535",
            "prefix-natural-65536", "prefix-natural-65537", "heldout-window-32767"
        }
    timer = root / "compare-library.py"
    program = timer.read_text()
    assert program.count("orders = list(permutations(commands))") == 1
    program = program.replace("orders = list(permutations(commands))",
                              f"orders = list(permutations(commands)) * {args.blocks // 24}")
    assert program.count("selected = {case['name'] for case in cases}") == 1
    program = program.replace("selected = {case['name'] for case in cases}",
                              f"selected = set({sorted(selected)!r})")
    output = args.output / ("timings-" + args.tag)
    output.mkdir()
    (output / "controller.py").write_text(program)
    control = args.output / "control/bound"
    for role in args.choice:
        candidate = args.output / role / "bound"
        runs = []
        for order in ("forward", "reverse"):
            directory = output / f"{role}-{order}"
            exec_script(timer, program, [directory, control, candidate, *([order] if order == "reverse" else [])])
            complete = read(directory / "complete.json")
            assert complete["balanced_blocks_per_case"] == args.blocks
            assert complete["cases"] == len(selected)
            runs.append({"order": order, "summary_sha256": sha(directory / "summary.json"),
                         "results": read(directory / "summary.json")})
        results = output / (role + "-results.json")
        write(results, {"complete": True, "runs": runs, "blocks_per_case": args.blocks,
                        "controller_sha256": sha(output / "controller.py")})
        for actor in ("mech-control", "mech-experiment"):
            with (output / f"{role}-{actor}-score.json").open("w") as stream:
                subprocess.run([sys.executable, baseline_receiver / "score.py", "--results", results,
                                "--actor", actor, *(["--discovery"] if args.blocks < 96 else [])],
                               check=True, stdout=stream)
        score = read(output / f"{role}-mech-experiment-score.json")
        print("SCORE", role, score["average_improvement_pp_vs_matched_control"],
              score["cohort_wins_in_both_orders"],
              [(row["order"], row["wins"], row["protected_missing"]) for row in score["scores"]], flush=True)


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("mode", choices=("prepare", "time"))
    for path in ("mech-root", "packet", "lab", "compiler", "output"):
        parser.add_argument("--" + path, type=Path, required=True)
    parser.add_argument("--choice", action="append", required=True)
    parser.add_argument("--weight", action="append")
    parser.add_argument("--blocks", type=int, choices=(24, 48, 72, 96), default=24)
    parser.add_argument("--tag", default="discovery")
    args = parser.parse_args()
    args.weight = args.weight or ["linear-4096"]
    args.output.mkdir(exist_ok=True)
    (prepare if args.mode == "prepare" else time_roles)(args)


if __name__ == "__main__":
    main()
