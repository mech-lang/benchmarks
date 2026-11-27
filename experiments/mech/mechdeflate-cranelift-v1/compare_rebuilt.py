"""Compare two explicitly rebuilt native compilers on the fixed regression corpora."""

from argparse import ArgumentParser
from collections import Counter
import ctypes
from datetime import datetime, timezone
from itertools import permutations
import json
from math import exp, log
from pathlib import Path
import platform
from runpy import run_path
from statistics import mean, median
from subprocess import check_output

from rebuild import (HERE, PARENT, checked, configuration, configuration_sha256,
                     measure_ordinary_compiler, ordinary_compiler_inputs, read, sha, write)
from replay import actor, silesia, suite81


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


def compare81(out, packets, control, candidate, *, retain_warmups=False, orders=ORDERS, cycles=4,
              fixture_stage=None):
    out.mkdir()
    suite81(out, packets, Path(candidate["build_directory"]), Path(control["build_directory"]),
            control["role"], candidate["role"], labels=(control["label"], candidate["label"]),
            retain_warmups=retain_warmups, orders=orders, cycles=cycles, fixture_stage=fixture_stage)
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


def compare_silesia(out, packets, corpus, control, candidate, *, orders=ORDERS):
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
    for direction in orders:
        order = matched if direction == "forward" else matched[::-1]
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


def require_pair(control, candidate, *, calibration):
    if calibration:
        if {key: value for key, value in control.items() if key != "label"} != {
            key: value for key, value in candidate.items() if key != "label"
        }:
            raise ValueError("Calibration roles must bind the same complete control build.")
    elif (control["build_directory"] == candidate["build_directory"]
          or control["source_commit"] == candidate["source_commit"]):
        raise ValueError("Supply separately rebuilt compiler trees at their distinct source pins.")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def campaign_host():
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        raise ValueError("Timing requires Apple Silicon macOS.")

    class Timebase(ctypes.Structure):
        _fields_ = [("numer", ctypes.c_uint32), ("denom", ctypes.c_uint32)]

    timebase = Timebase()
    mach_timebase_info = ctypes.CDLL(None).mach_timebase_info
    mach_timebase_info.argtypes = [ctypes.POINTER(Timebase)]
    mach_timebase_info.restype = ctypes.c_int
    status = mach_timebase_info(ctypes.byref(timebase))
    clock_timebase = {"status": status, "numer": timebase.numer, "denom": timebase.denom}
    if status != 0 or not (timebase.numer and timebase.denom):
        raise ValueError(f"Invalid Mach clock timebase {clock_timebase}.")

    def read_system(*command):
        return check_output(command, text=True).strip()
    chip = read_system("/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string")
    roles = [name for name in ("M1", "M3") if name in chip.split()]
    if len(roles) != 1:
        raise ValueError(f"No qualification policy for {chip}.")
    toolchain = read(PARENT / "mechdeflate-81-v1/recipe.json")["compiler"]["toolchain"]
    return {
        "qualification_host": roles[0], "cpu": chip, "architecture": platform.machine(),
        "model": read_system("/usr/sbin/sysctl", "-n", "hw.model"),
        "machine": platform.node(), "os": platform.system(), "os_version": platform.mac_ver()[0],
        "os_build": read_system("/usr/bin/sw_vers", "-buildVersion"),
        "rustc": read_system("rustc", "+" + toolchain, "-vV"),
        "python": platform.python_version(), "clock_timebase": clock_timebase,
    }


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def compiler_session(folder, slots, compiler_inputs):
    folder.mkdir()
    warmup = {slot: measure_ordinary_compiler(folder / "warmup" / slot, compiler_inputs[actor])
              for slot, actor in slots.items()}
    blocks = []
    for index, sequence in enumerate(permutations(slots), 1):
        results = {slot: measure_ordinary_compiler(folder / f"block-{index}" / slot, compiler_inputs[slots[slot]])
                   for slot in sequence}
        blocks.append({"order": list(sequence), "samples": results})
    write_new(folder / "observations.json", {"slots": slots, "warmup": warmup, "blocks": blocks})


def record_session(folder, manifest, policy, stage, digest, calibration_hash, bindings, compiler_inputs):
    from verify import CONTROLS, expected_pair, inventory, require, session_metrics
    actual_host = campaign_host()
    require(actual_host == manifest["host"], "Campaign host or toolchain changed.")
    folder.mkdir()
    start = utc_now()
    write_new(folder / "started.json", {"manifest_sha256": digest, "calibration_sha256": calibration_hash,
                                       "stage": stage, "session": folder.name, "start_utc": start})
    aa = stage == "calibrate"
    controls = (folder.name.rsplit("-", 1)[0],) if aa else CONTROLS
    compilation = policy["compilation"]
    slots = (dict.fromkeys(compilation["calibration_slots"], controls[0]) if aa
             else {name: name for name in compilation["performance_slots"]})
    compiler_session(folder / "compiler", slots, compiler_inputs)
    paired = folder / "pairs"
    paired.mkdir()
    corpus = Path(manifest["corpus"])
    pairs, reference_replay = {}, {}
    for control in controls:
        pair = expected_pair(bindings, control, stage)
        left, right = pair["control"], pair["candidate"]
        pairs[control] = pair
        reference_replay[control] = {"control": control, "candidate": control if aa else "candidate"}
        pair_folder = paired / control
        pair_folder.mkdir()
        compare81(pair_folder / "suite81", PARENT, left, right, retain_warmups=True)
        compare_silesia(pair_folder / "silesia", PARENT, corpus, left, right)
    reference_dir = folder / "references"
    reference_dir.mkdir()
    for label in dict.fromkeys(slots.values()):
        bound = bindings[label]
        silesia(reference_dir / label, PARENT, Path(bound["build_directory"]), corpus, bound["role"])

    require(campaign_host() == actual_host, "Campaign host changed during the session.")
    record = {
        "manifest_sha256": digest, "calibration_sha256": calibration_hash, "stage": stage,
        "session": folder.name, "start_utc": start, "end_utc": utc_now(), "host": actual_host,
        "pair_bindings": pairs, "reference_replay": reference_replay,
        "raw_files": inventory(folder),
    }
    session_metrics(folder, record, bindings, policy)
    write_new(folder / "record.json", record)


def run_campaign(path, stage, calibration_path):
    from verify import (STAGE_FILES, calculate_assessment, calculate_calibration, load_campaign,
                        pinned_bindings, require, session_names, stage_summary, verify_session)
    manifest, digest, output, policy = load_campaign(path)
    bindings = pinned_bindings(manifest)
    target = output / STAGE_FILES[stage]
    require(not target.exists(), f"Completed stage is retained at {target}.")
    seal = None
    calibration_hash = None
    if stage != "calibrate":
        expected = output / STAGE_FILES["calibrate"]
        require(calibration_path is not None and calibration_path.resolve() == expected.resolve(),
                "Use this campaign's sealed calibration.")
        calibration_hash = sha(expected)
        seal = read(expected)
        actual = stage_summary(output, policy, "calibrate", digest, None, manifest["host"])
        require(seal["stage"] == "calibrate" and seal["manifest_sha256"] == digest
                and seal["sessions"] == actual["sessions"], "Calibration inputs differ.")
        require(all(set(families) == {"compiler", "runtime"} for families in seal["controls"].values()),
                "Calibration envelope is incomplete.")
    if stage in ("confirm", "assess"):
        check = stage_summary(output, policy, "qualify", digest, calibration_hash, manifest["host"])
        require(check == read(output / STAGE_FILES["qualify"]), "Qualification seal differs.")
    if stage != "calibrate":
        require(seal == calculate_calibration(output, policy, digest, bindings, manifest["host"]),
                "Sealed calibration does not reproduce.")
    if stage == "assess":
        result = calculate_assessment(output, policy, digest, bindings, seal, calibration_hash,
                                      manifest["host"])
    else:
        require(campaign_host() == manifest["host"], "Expected the pinned qualification machine.")
        ordinary = {label: ordinary_compiler_inputs(Path(actor["source"]), Path(actor["build"]),
                                                     Path(actor["recipe"]), PARENT)
                    for label, actor in manifest["actors"].items()}
        (output / stage).mkdir(parents=True, exist_ok=True)
        for name in session_names(policy, stage):
            folder = output / stage / name
            if folder.exists():
                verify_session(folder, digest, stage, calibration_hash, manifest["host"])
                continue
            record_session(folder, manifest, policy, stage, digest, calibration_hash, bindings, ordinary)
        if stage == "calibrate":
            result = calculate_calibration(output, policy, digest, bindings, manifest["host"])
        else:
            result = stage_summary(output, policy, stage, digest, calibration_hash, manifest["host"])
    write_new(target, result)
    print(target, result.get("decision", "sealed"), flush=True)


def record_crossover(folder, campaign, stage, ordinal, controls):
    from verify import crossover_pair, crossover_plan, scoped_slots

    paired = folder / "pairs"
    paired.mkdir()
    corpus = Path(campaign.manifest["corpus"])
    cycles = campaign.policy["timing"]["fixtures"]["cycles_per_leg"]
    legs = []
    for step in crossover_plan(controls, ordinal, stage == "calibrate"):
        order = step["order"]
        path = paired / step["comparison"] / f"{order}-{step['leg']}"
        path.mkdir(parents=True)
        bindings = crossover_pair(campaign.bindings, step, stage == "calibrate")
        write_new(path / "bindings.json", bindings)
        started = {**step, "start_utc": utc_now()}
        write_new(path / "started.json", started)
        print(f"Session {ordinal} {step['comparison']} {order} leg {step['leg']} {step['slots']}", flush=True)
        left, right = bindings["control"], bindings["candidate"]
        compare81(path / "suite81", PARENT, left, right, retain_warmups=True, orders=(order,), cycles=cycles,
                  fixture_stage=campaign.manifest["fixture_stage"])
        compare_silesia(path / "silesia", PARENT, corpus, left, right, orders=(order,))
        legs.append({**started, "end_utc": utc_now()})
    references = folder / "references"
    references.mkdir()
    for label in dict.fromkeys(scoped_slots(campaign.policy, stage, controls).values()):
        bound = campaign.bindings[label]
        silesia(references / label, PARENT, Path(bound["build_directory"]), corpus, bound["role"])
    return legs


def record_scoped_session(campaign, folder, stage, calibration_hash, ordinal, controls, compiler_inputs):
    from verify import inventory, require, scoped_compiler_slots, scoped_metrics, verify_fixture_stage

    actual_host = campaign_host()
    require(actual_host == campaign.manifest["host"], "Campaign host or toolchain changed.")
    folder.mkdir()
    started = {**campaign.identity(stage, calibration_hash), "session": folder.name, "start_utc": utc_now()}
    write_new(folder / "started.json", started)
    print(campaign.scope, stage, folder.name, flush=True)
    metadata = {}
    if campaign.scope == "compiler":
        slots = scoped_compiler_slots(campaign.policy, stage, controls, ordinal)
        compiler_session(folder / "processes", slots, compiler_inputs)
    else:
        stage_binding = campaign.manifest["fixture_stage"]
        verify_fixture_stage(stage_binding, campaign.output.parent)
        metadata["legs"] = record_crossover(folder, campaign, stage, ordinal, controls)
        verify_fixture_stage(stage_binding, campaign.output.parent)
    require(campaign_host() == actual_host, "Campaign host changed during the session.")
    record = {**started, "end_utc": utc_now(), "host": actual_host, "ordinal": ordinal,
              "controls": list(controls), **metadata, "raw_files": inventory(folder)}
    scoped_metrics(folder, record, campaign)
    write_new(folder / "record.json", record)


def run_scoped_campaign(path, stage, calibration_path, scope):
    from verify import (STAGE_FILES, open_scope, require, scoped_assessment, scoped_calibration,
                        scoped_calibration_seal, scoped_metrics, scoped_schedule, scoped_stage_seal, scoped_summary)

    campaign = open_scope(path, scope)
    target = campaign.output / STAGE_FILES[stage]
    require(not target.exists(), f"Completed stage is retained at {target}.")
    calibration_hash = None
    if stage == "calibrate":
        require(calibration_path is None, "Calibration creates its own seal.")
    else:
        seal, calibration_hash = scoped_calibration_seal(campaign, calibration_path)
        if scope == "runtime":
            require(seal["decision"] == "pass", "Invalid runtime calibration forbids candidate timing.")
    if stage == "assess":
        result = scoped_assessment(campaign, seal, calibration_hash)
    else:
        if stage == "confirm":
            scoped_stage_seal(campaign, "qualify", calibration_hash)
        require(campaign_host() == campaign.manifest["host"], "Expected the pinned qualification machine.")
        compiler_inputs = {}
        if scope == "compiler":
            compiler_inputs = {
                name: ordinary_compiler_inputs(Path(actor["source"]), Path(actor["build"]),
                                               Path(actor["recipe"]), PARENT)
                for name, actor in campaign.manifest["actors"].items()
            }
        base = campaign.output / stage
        base.mkdir(parents=True, exist_ok=True)
        schedule = scoped_schedule(campaign.policy, stage)
        existing = {folder.name for folder in base.iterdir()}
        require(existing == {name for name, _, _ in schedule[:len(existing)]},
                "Existing sessions do not form a prefix of the scheduled stage.")
        previous = ""
        for name, ordinal, controls in schedule[:len(existing)]:
            record = campaign.session(base / name, stage, calibration_hash, ordinal, controls)
            require(previous <= record["start_utc"], "Existing sessions have invalid startup order.")
            if scope == "runtime":
                scoped_metrics(base / name, record, campaign)
            previous = record["end_utc"]
        for name, ordinal, controls in schedule[len(existing):]:
            record_scoped_session(campaign, base / name, stage, calibration_hash, ordinal, controls, compiler_inputs)
        if stage == "calibrate":
            result = scoped_calibration(campaign)
        else:
            result = scoped_summary(campaign, stage, calibration_hash)
    write_new(target, result)
    print(target, result.get("decision", "sealed"), flush=True)


def main():
    parser = ArgumentParser(description=__doc__)
    for side in ("control", "candidate"):
        parser.add_argument(f"--{side}", choices=("frozen", "reconciled", "configured"))
        parser.add_argument(f"--{side}-build", type=Path)
        parser.add_argument(f"--{side}-recipe", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bench-root", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--suite", choices=("81", "silesia", "all"), default="all")
    parser.add_argument("--prepare-only", action="store_true", help="Verify the rebuilt actors and write bindings")
    parser.add_argument("--campaign", type=Path, help="Immutable native route campaign manifest")
    parser.add_argument("--stage", choices=("calibrate", "qualify", "confirm", "assess"))
    parser.add_argument("--calibration", type=Path, help="The sealed calibration for this campaign")
    parser.add_argument("--scope", choices=("compiler", "runtime"))
    args = parser.parse_args()
    if not __debug__:
        parser.error("Use Python with assertions enabled.")
    if args.campaign is not None:
        if args.stage is None:
            parser.error("--campaign requires --stage.")
        path = args.campaign.resolve()
        if args.scope is None:
            run_campaign(path, args.stage, args.calibration)
        else:
            run_scoped_campaign(path, args.stage, args.calibration, args.scope)
        return
    if args.stage is not None or args.calibration is not None or args.scope is not None:
        parser.error("--stage, --calibration and --scope require --campaign.")
    for name in ("output", "control", "control_build", "control_recipe",
                 "candidate", "candidate_build", "candidate_recipe"):
        if getattr(args, name) is None:
            parser.error(f"--{name.replace('_', '-')} is required for a legacy comparison.")
    if (args.control, args.candidate) not in PAIRS:
        parser.error("Choose reconciled versus frozen, configured versus reconciled or configured versus frozen.")
    if args.suite != "81" and not args.prepare_only and args.corpus is None:
        parser.error("Supply the pinned full Silesia corpus.")
    if not args.prepare_only and (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        parser.error("Timing requires Apple Silicon macOS.")
    control = bind(args.control, args.control_build.resolve(strict=True), args.control_recipe.resolve(strict=True))
    candidate = bind(args.candidate, args.candidate_build.resolve(strict=True), args.candidate_recipe.resolve(strict=True))
    require_pair(control, candidate, calibration=False)
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
