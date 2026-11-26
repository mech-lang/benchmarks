"""Verify the recorded run and independently recompute its scores."""

from argparse import ArgumentParser
from dataclasses import dataclass
import gzip
from hashlib import sha256
from itertools import permutations
from math import exp, isclose
import json
from pathlib import Path
from re import fullmatch
from runpy import run_path
from statistics import fmean, median
import subprocess
import sys
import tarfile

from campaign_stats import REPLICATES, SEED, balanced_cycles, calibration, nonregression, paired_log, simultaneous
from rebuild import HERE, PARENT, checked, read, sha


POLICY = HERE / "stabilization/closeout-p3/policy.json"
SCOPED_POLICY = HERE / "stabilization/route-memory/policy.json"
SCOPES = ("compiler", "runtime")
SCOPED_BASELINE = "3936f4b1d693aa7a26cd7954ba8cb011ee7cbed7"
STARTING_SOURCE = "146626d6f9bad465efaa2993f49da4a674b993a9"
PREVIOUS_SOURCE = "0bde021f93bd752ebf5e85ba2aaa29f84872caeb"
SCOPED_CONTROLS = ("reviewed", "previous")
BASELINE = "f9eb6c48905ff02e2a5771d1812f6bb42598a57f"
ACTORS = {"reviewed": "R", "closeout": "C", "candidate": "O"}
CONTROLS = ("closeout", "reviewed")
ORDERS = ("forward", "reverse")
STAGE_FILES = {"calibrate": "calibration.json", "qualify": "qualification.json",
               "confirm": "confirmation.json", "assess": "assessment.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def absolute(value):
    path = Path(value)
    require(path.is_absolute(), f"Expected an absolute path: {path}")
    return path


def tool_commit(root):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def scoped_tool_files(root):
    packets = ("mechdeflate-cranelift-v1", "mechdeflate-81-v1", "mechdeflate-phase-routes-v1",
               "mechdeflate-masked-fields-v1", "mechdeflate-silesia-v1")
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", *(str((PARENT / name).relative_to(root)) for name in packets)],
        cwd=root,
    ).decode().split("\0")
    return {name for name in tracked if name.endswith(".py")} | {str(SCOPED_POLICY.relative_to(root))}


def load_campaign(path, record=None, *, scope=None):
    manifest = read(path)
    require(scope is None or scope in SCOPES, "Unknown campaign scope.")
    version = 1 if scope is None else 2
    require(manifest["schema"] == f"mech.native-route-campaign.v{version}", "Campaign schema and scope differ.")
    baseline_commit = BASELINE if scope is None else SCOPED_BASELINE
    require(manifest["baseline_benchmark_commit"] == baseline_commit, "Benchmark baseline pin differs.")
    root = absolute(manifest["bench_root"])
    require(root.resolve() == HERE.parents[2], "Invoke the tooling from the pinned benchmark checkout.")
    require(tool_commit(root) == manifest["tooling_commit"], "Benchmark tooling commit differs.")
    policy_path = POLICY if scope is None else SCOPED_POLICY
    policy = read(policy_path)
    for field in ("sessions", "timing", "bootstrap", "compilation", "boundaries", "comparisons", "reference_targets"):
        require(manifest[field] == policy[field], f"Campaign changes the fixed {field} policy.")
    require(policy["bootstrap"]["seed"] == SEED and policy["bootstrap"]["replicates"] == REPLICATES,
            "Bootstrap algorithm and policy differ.")
    output = absolute(manifest["output_directory"])
    if record is not None:
        require(record.resolve() == output.resolve(), "Campaign record directory differs from the manifest.")
    required_tools = {str((HERE / name).relative_to(root)) for name in
                      ("compare_rebuilt.py", "rebuild.py", "replay.py", "campaign_stats.py", "verify.py")}
    required_tools.add(str(policy_path.relative_to(root)))
    if scope is not None:
        required_tools |= scoped_tool_files(root)
    tool_hashes = manifest["tooling_files_sha256"]
    require(required_tools <= tool_hashes.keys(), "Incomplete tooling hash inventory.")
    if scope is not None:
        require(required_tools == tool_hashes.keys(), "Unexpected scoped tooling paths.")
        status = subprocess.run(["git", "diff", "HEAD", "--quiet", "--", *sorted(required_tools)],
                                cwd=root, check=False)
        require(status.returncode == 0, "Campaign tooling must match its committed version.")
    for name, digest in tool_hashes.items():
        file = (root / name).resolve()
        require(file.is_relative_to(root.resolve()), f"Tooling path escapes the checkout: {name}")
        checked(file, digest)
    absolute(manifest["qualification_root"])
    source_pins = manifest["source_commits"]
    actors = ACTORS
    if scope is None:
        require(set(source_pins) == {"R", "I", "C", "S", "O"} and len(set(source_pins.values())) == 5,
                "Expected distinct R/I/C/S/O source pins.")
    else:
        purpose = manifest["purpose"]
        require(purpose in ("memory-repair", "final-qualification"), "Unknown campaign purpose.")
        require(scope == "compiler" or purpose == "final-qualification", "Runtime is not a memory-repair scope.")
        candidate = "N" if purpose == "memory-repair" else "F"
        pins = {"R", "O", "N"} if candidate == "N" else {"R", "O", "N", "F"}
        require(source_pins.keys() == pins and all(fullmatch("[0-9a-f]{40}", pin) for pin in source_pins.values())
                and len(set(source_pins.values())) == len(pins), "Invalid scoped source pins.")
        require(source_pins["O"] == PREVIOUS_SOURCE, "Previous compiler pin differs.")
        identifier = manifest["campaign_id"]
        require(fullmatch("[A-Za-z0-9][A-Za-z0-9._-]{0,79}", identifier), "Invalid campaign ID.")
        expected_output = SCOPED_POLICY.parent / source_pins[candidate] / identifier
        require(output.resolve() == expected_output.resolve() == path.parent.resolve(),
                "Scoped campaign must use the pinned source and campaign-ID record directory.")
        actors = {"reviewed": "R", "previous": "O", "candidate": candidate}
    expected = read(HERE / "native-first-batch/evidence/configured/recipe.json")
    require(source_pins["R"] == expected["source_commit"], "Reviewed source pin differs.")
    require(manifest["actors"].keys() == actors.keys(), "Incorrect campaign actor roles.")
    for label, pin in actors.items():
        actor = manifest["actors"][label]
        for field in ("source", "build", "recipe"):
            absolute(actor[field])
        path_recipe = Path(actor["recipe"])
        checked(path_recipe, actor["recipe_sha256"])
        recipe = read(path_recipe)
        require(recipe["source_commit"] == source_pins[pin], f"{label} recipe source pin differs.")
        baseline = {**expected, "source_commit": source_pins[pin]}
        driver = baseline["configured_driver"]
        baseline["inputs_sha256"] = {**baseline["inputs_sha256"], driver: recipe["inputs_sha256"][driver]}
        require(recipe == baseline, f"{label} recipe changed fixed inputs.")
    corpus = absolute(manifest["corpus"])
    checked(corpus / "corpus.json", manifest["corpus_manifest_sha256"])
    checked(PARENT / "mechdeflate-silesia-v1/corpus.json", manifest["corpus_manifest_sha256"])
    return manifest, sha(path), output, policy


def inventory(folder, exclude=()):
    result = {}
    for item in sorted(folder.rglob("*")):
        name = item.relative_to(folder).as_posix()
        require(not item.is_symlink(), f"Unexpected symbolic link in record: {item}")
        if item.is_file() and name not in exclude:
            result[name] = {"bytes": item.stat().st_size, "sha256": sha(item)}
    return result


def verify_inventory(folder, expected, exclude=()):
    names = {item.relative_to(folder).as_posix() for item in folder.rglob("*") if item.is_file()} - set(exclude)
    require(names == expected.keys(), f"Missing or unexpected raw files in {folder}.")
    for name, entry in expected.items():
        file = folder / name
        require(not file.is_symlink() and file.stat().st_size == entry["bytes"],
                f"Raw evidence changed: {file}")
        checked(file, entry["sha256"])


def verify_session(folder, manifest_hash, stage, calibration_hash, host=None, *, scope_fields=None):
    path = folder / "record.json"
    require(path.is_file(), f"Incomplete session retained at {folder}.")
    info = read(path)
    require(info["manifest_sha256"] == manifest_hash and info["stage"] == stage
            and info["calibration_sha256"] == calibration_hash and info["session"] == folder.name,
            f"Session binding differs: {folder}")
    if scope_fields is not None:
        require(all(info[key] == value for key, value in scope_fields.items()),
                f"Scoped session identity differs: {folder}")
    require(info["start_utc"] <= info["end_utc"], f"Invalid timestamps: {folder}")
    if host is not None:
        require(info["host"] == host, f"Host or toolchain identity differs: {folder}")
        started = read(folder / "started.json")
        fields = {"manifest_sha256", "calibration_sha256", "stage", "session", "start_utc"}
        require(started == {key: info[key] for key in started}
                and set(started) == fields | (scope_fields or {}).keys(),
                f"Session start marker differs: {folder}")
    verify_inventory(folder, info["raw_files"], {"record.json"})
    return info


def session_names(policy, stage):
    if stage == "calibrate":
        count = policy["sessions"]["calibrate_per_control"]
        return tuple(f"{control}-{i + 1}" for control in CONTROLS for i in range(count))
    return tuple(f"session-{i + 1}" for i in range(policy["sessions"][stage]))


def sessions_for(output, policy, stage, manifest_hash, calibration_hash, host):
    base = output / stage
    names = session_names(policy, stage)
    require(base.is_dir() and set(names) == {item.name for item in base.iterdir()},
            f"Incomplete session inventory for {stage}.")
    return [(base / name, verify_session(base / name, manifest_hash, stage, calibration_hash, host))
            for name in names]


def pinned_bindings(manifest):
    from compare_rebuilt import bind
    bindings = {}
    for label, actor in manifest["actors"].items():
        row = bind(label, Path(actor["build"]), Path(actor["recipe"]))
        require(tool_commit(Path(actor["source"])) == row["source_commit"],
                f"Source checkout changed for {label}.")
        checked(Path(actor["build"]) / "compile_profile", row["compiler_sha256"])
        codec = read(PARENT / "mechdeflate-81-v1/recipe.json")["codec_source"]
        source = Path(actor["source"]) / codec
        checked(source, row["source_sha256"])
        bindings[label] = {**row, "codec_source": str(source)}
    return bindings


def expected_pair(bindings, control, stage):
    from compare_rebuilt import require_pair
    aa = stage == "calibrate"
    left = {**bindings[control], "label": "control"} if aa else bindings[control]
    right = {**bindings[control], "label": "candidate"} if aa else bindings["candidate"]
    require_pair(left, right, calibration=aa)
    return {"kind": "calibration" if aa else "comparison", "control": left, "candidate": right}


def validate_fixture_actor_pins(folder, pair):
    pins = read(folder / "pins.json")
    names = ("mech-control", "mech-experiment")
    peers = tuple(sorted(set(pins["actors"]) - set(names)))
    require(len(peers) == 2 and "libdeflate" in peers, "Unexpected fixture reference actors.")
    for label, side in zip(names, ("control", "candidate"), strict=True):
        binding, pin = pair[side], pins["actors"][label]
        require(pin["command"][0] == binding["81"]["path"]
                and pin["binary_sha256"] == binding["81"]["sha256"]
                and pin["metadata_sha256"] == binding["artifacts"]["metadata.json"],
                f"Timed fixture actor differs in {folder}.")
        checked(Path(pin["command"][0]), pin["binary_sha256"])
        checked(Path(pin["command"][1]), pin["metadata_sha256"])
    expected = read(PARENT / "mechdeflate-81-v1/actors/bindings.json")["peers"]
    for peer in peers:
        recorded = pins["actors"][peer]
        label = peer if peer == "libdeflate" else "reference"
        for key, digest in expected[label].items():
            require(recorded[key] == digest, f"Fixture reference identity changed: {peer}.")
        checked(Path(recorded["command"][0]), recorded["binary_sha256"])
        if "metadata_sha256" in recorded:
            checked(Path(recorded["command"][1]), recorded["metadata_sha256"])
    return names, peers


def cycles_for_cases(rows, prefix, cycles, measure):
    coordinates = [dict() for _ in range(cycles)]
    for row in rows:
        estimates = measure(row)
        for output, estimate in zip(coordinates, estimates, strict=True):
            output[f"{prefix}/{row['case']}"] = estimate
    for output in coordinates:
        output[f"{prefix}/suite-geomean"] = fmean(output.values())
    return coordinates


def fixture_inputs(folder, pair, *, orders=ORDERS, cycles=4):
    from replay import fixture_campaign_controller
    archived = read(PARENT / "mechdeflate-81-v1/actors/bindings.json")
    order_names = [row["name"] for row in read(folder / "fixtures.json")]
    names = sorted(order_names)
    require(len(names) == len(set(names)) == 81, "Incomplete fixture inventory.")
    original = (folder / "compare-library.py").read_text()
    timer = original.replace("orders = list(permutations(commands))", "orders = list(permutations(commands)) * 4")
    timer = timer.replace("selected = {case['name'] for case in cases}", f"selected = set({names!r})")
    require(sha256(timer.encode()).hexdigest() == archived["controller_sha256"],
            "Original fixture controller identity differs.")
    require((folder / "controller.py").read_text() == fixture_campaign_controller(timer, cycles),
            "Campaign fixture controller does not match the declared cycle and recording policy.")
    routes = PARENT / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    try:
        oracle_path = folder / "pinned-peers/libdeflate-output-oracle.json"
        checked(oracle_path, archived["oracle_sha256"])
        oracle = {row["case"]: row for row in read(oracle_path)}
        fixture_tools = run_path(str(routes / "verify_timings.py"))
        result = fixture_tools["verify"](folder, folder / "cranelift-results.json", "cranelift", oracle, orders=orders)
        require(result["blocks_per_case"] == cycles * 24, "Fixture cycle count differs.")
    finally:
        sys.path.pop(0)
    groups, references, absolute_ns = {}, {}, {}
    runs = read(folder / "cranelift-results.json")["runs"]
    require(tuple(run["order"] for run in runs) == orders, "Missing fixture order.")
    for run in runs:
        order = run["order"]
        path = folder / f"cranelift-{order}"
        labels, peers = validate_fixture_actor_pins(path, pair)
        if cycles == 2:
            startup = fixture_tools["ACTORS"]
            expected_startup = startup if order == "forward" else startup[::-1]
            require(read(path / "worker-startup.json") == list(expected_startup),
                    f"Unexpected fixture worker startup order in {path}.")
        rows = run["results"]
        observed_names = [row["case"] for row in rows]
        require(observed_names == (order_names if order == "forward" else order_names[::-1]),
                "Fixture case inventory or order differs.")
        peers_by_label = {peer if peer == "libdeflate" else "reference": peer for peer in peers}
        reference = {side: {name: {} for name in peers_by_label} for side in ("control", "candidate")}
        durations = {}
        def measured(row):
            case = row["case"]
            with gzip.open(path / case / "observations.json.gz", "rt") as stream:
                blocks = json.load(stream)
            warmups = read(path / case / "warmups.json")
            require(warmups.keys() == set((*labels, *peers)) and all(
                value["calls"] > 0 and value["seconds"] >= 0.2 and value["observation"]["warmup"]
                and value["observation"]["case"] == case for value in warmups.values()),
                f"Invalid warmup inventory for {case}.")
            units = balanced_cycles(blocks, (*labels, *peers), cycles)
            for side, actor in zip(reference, labels, strict=True):
                for name, peer in peers_by_label.items():
                    reference[side][name][case] = fmean(paired_log(block["means"][actor], block["means"][peer])
                                                       for block in blocks)
            durations[case] = {actor: value * 1e9 for actor, value in row["median_seconds"].items()}
            return [fmean(paired_log(block["means"][labels[1]], block["means"][labels[0]]) for block in cycle)
                    for cycle in units]
        key = f"fixtures/{order}"
        groups[key] = cycles_for_cases(rows, key, cycles, measured)
        references[key] = reference
        absolute_ns[key] = durations
    return groups, references, absolute_ns


def silesia_pair_inputs(folder, pair, *, orders=ORDERS):
    package = PARENT / "mechdeflate-silesia-v1"
    names = list(read(package / "corpus.json")["files"])
    verified = read(folder / "independent-inflation.json")
    labels = tuple(pair[side]["label"] for side in ("control", "candidate"))
    oracle = read(package / "complete.json")["independent_inflation"]
    require(set(verified) == set(names) and all(
        set(verified[case]) == set(labels) and
        all(value == oracle[case]["mech-candidate"] for value in verified[case].values())
        for case in names), "Paired Silesia compression or inflation evidence differs.")
    groups, absolute_ns = {}, {}
    for direction in orders:
        inventory_names = names if direction == "forward" else names[::-1]
        rows = read(folder / f"timings-{direction}.json")
        require([row["case"] for row in rows] == inventory_names, "Incomplete paired Silesia cases.")
        def measured(row):
            blocks = row["blocks"]
            require(row["warmup_ns"].keys() == set(labels) and min(row["warmup_ns"].values()) > 0,
                    "Missing Silesia warmup.")
            if len(orders) == 1:
                startup = labels if direction == "forward" else labels[::-1]
                require(tuple(row["warmup_ns"]) == startup, "Unexpected Silesia worker startup order.")
            require(all(set(block["ns"]) == set(labels) and min(block["ns"].values()) > 0
                        for block in blocks), "Incomplete Silesia timing block.")
            for label in labels:
                require(row["median_ns"][label] == median(block["ns"][label] for block in blocks),
                        "Paired Silesia median cannot be reproduced.")
            require(isclose(row["candidate_x_control"],
                            exp(fmean(paired_log(block["ns"][labels[1]], block["ns"][labels[0]])
                                      for block in blocks)), rel_tol=1e-12),
                    "Paired Silesia ratio cannot be reproduced.")
            return [fmean(paired_log(block["ns"][labels[1]], block["ns"][labels[0]]) for block in cycle)
                    for cycle in balanced_cycles(blocks, labels, 3)]
        key = f"silesia/{direction}"
        groups[key] = cycles_for_cases(rows, key, 3, measured)
        absolute_ns[key] = {row["case"]: row["median_ns"] for row in rows}
    return groups, absolute_ns


def silesia_reference_inputs(folder, binding):
    package = PARENT / "mechdeflate-silesia-v1"
    names = list(read(package / "corpus.json")["files"])
    original = read(package / "binding.json")
    actual = read(folder / "binding.json")
    actors = actual["actors"]
    measured = "mech-candidate"
    peers = tuple(sorted(set(actors) - {measured}))
    require(actors.keys() == original["actors"].keys(), "Silesia standalone actor inventory changed.")
    require(actors[measured]["path"] == binding["silesia"]["path"]
            and actors[measured]["sha256"] == binding["silesia"]["sha256"]
            and actors[measured]["encoder_sha256"] == binding["artifacts"]["program.o"],
            "Standalone Silesia actor differs from its rebuilt binding.")
    for peer in peers:
        pin = {**actors[peer]}
        checked(Path(pin.pop("path")), pin["sha256"])
        expected = {key: value for key, value in original["actors"][peer].items() if key != "path"}
        require(pin == expected, f"Standalone Silesia reference identity changed: {peer}.")
    completion = read(folder / "complete.json")
    require(completion["binding_sha256"] == sha(folder / "binding.json")
            and completion["corpus_sha256"] == sha(package / "corpus.json")
            and completion["independent_inflation"] == read(package / "complete.json")["independent_inflation"],
            "Standalone Silesia independent output evidence differs.")
    references, sums = {}, {}
    for order, inventory_names in zip(ORDERS, (names, names[::-1]), strict=True):
        rows = read(folder / f"timings-{order}.json")
        require([row["case"] for row in rows] == inventory_names, "Incomplete standalone Silesia cases.")
        reference = {peer if peer == "libdeflate" else "reference": {} for peer in peers}
        for row in rows:
            require(row["warmup_ns"].keys() == actors.keys() and min(row["warmup_ns"].values()) > 0,
                    "Missing standalone Silesia warmup.")
            blocks = row["blocks"]
            balanced_cycles(blocks, tuple(actors), 1)
            require(all(block["ns"].keys() == actors.keys() for block in blocks),
                    "Incomplete standalone Silesia block.")
            for actor in actors:
                require(row["median_ns"][actor] == median(block["ns"][actor] for block in blocks),
                        "Standalone Silesia median cannot be reproduced.")
            for peer in peers:
                name = peer if peer == "libdeflate" else "reference"
                estimate = fmean(paired_log(block["ns"][measured], block["ns"][peer]) for block in blocks)
                require(isclose(exp(estimate), row["mech_paired_x_peer"][peer], rel_tol=1e-12),
                        "Standalone Silesia ratio cannot be reproduced.")
                reference[name][row["case"]] = estimate
        key = f"silesia/{order}"
        references[key] = reference
        sums[key] = {actor: sum(row["median_ns"][actor] for row in rows) for actor in actors}
    return references, sums


def compilation_inputs(folder, slots, bindings, numerator, denominator, *, ordered=False):
    from re import findall
    raw = read(folder / "observations.json")
    require(raw["slots"] == slots and raw["warmup"].keys() == slots.keys(),
            "Compiler process slots differ from the fixed policy.")
    blocks, = balanced_cycles(raw["blocks"], tuple(slots), 1)
    if ordered:
        require(tuple(raw["warmup"]) == tuple(slots)
                and tuple(tuple(block["order"]) for block in blocks) == tuple(permutations(slots))
                and all(tuple(block["samples"]) == tuple(block["order"]) for block in blocks),
                "Compiler process launch order differs from the session schedule.")

    def checked_sample(path, slot, sample):
        binding = bindings[slots[slot]]
        require(sample["elapsed_ns"] > 0 and sample["maximum_resident_bytes"] > 0
                and sample["compiler_sha256"] == binding["compiler_sha256"]
                and sample["configuration_sha256"] == binding["configuration_sha256"]
                and sample["artifacts"] == binding["artifacts"], "Ordinary compiler sample binding differs.")
        require(sample["command"][:3] == ["/usr/bin/time", "-l", str(Path(binding["build_directory"]) / "compile_profile")]
                and sample["command"][3:] == [binding["codec_source"], str(path / "frontend"), "compact"],
                "Ordinary compiler command differs or enables diagnostic instrumentation.")
        rss, = findall(r"(?m)^\s*(\d+)\s+maximum resident set size\s*$", (path / "process.log").read_text())
        require(int(rss) == sample["maximum_resident_bytes"], "Compiler RSS differs from its raw log.")
        for name, digest in binding["artifacts"].items():
            checked(path / "frontend" / name, digest)
    for slot, sample in raw["warmup"].items():
        checked_sample(folder / "warmup" / slot, slot, sample)
    for index, block in enumerate(blocks):
        require(block["samples"].keys() == slots.keys(), "Missing compiler sample in a complete block.")
        for slot, sample in block["samples"].items():
            checked_sample(folder / f"block-{index + 1}" / slot, slot, sample)
    coordinates = {key: fmean(paired_log(block["samples"][numerator][key],
                                         block["samples"][denominator][key]) for block in blocks)
                   for key in ("elapsed_ns", "maximum_resident_bytes")}
    return [coordinates]


def session_metrics(folder, row, bindings, policy):
    stage = row["stage"]
    aa = stage == "calibrate"
    controls = (folder.name.rsplit("-", 1)[0],) if aa else CONTROLS
    compilation = policy["compilation"]
    if aa:
        slots = dict.fromkeys(compilation["calibration_slots"], controls[0])
        reference_labels = {controls[0]}
    else:
        slots = {name: name for name in compilation["performance_slots"]}
        reference_labels = set(slots)
    require(row["pair_bindings"].keys() == set(controls), "Unexpected session pair inventory.")
    require({directory.name for directory in (folder / "pairs").iterdir()} == set(controls)
            and {directory.name for directory in (folder / "references").iterdir()} == reference_labels,
            "Unexpected paired or standalone measurement directories.")
    standalone = {label: silesia_reference_inputs(folder / "references" / label, bindings[label])
                  for label in sorted(reference_labels)}
    metrics = {}
    for control in controls:
        measured = control if aa else "candidate"
        pair = expected_pair(bindings, control, stage)
        require(pair == row["pair_bindings"][control], f"Actor binding changed for {control}.")
        require(row["reference_replay"][control] == {"control": control, "candidate": measured},
                "Standalone reuse binding differs.")
        path = folder / "pairs" / control
        groups, references, duration = fixture_inputs(path / "suite81", pair)
        silesia_groups, silesia_ns = silesia_pair_inputs(path / "silesia", pair)
        for key in ("silesia/forward", "silesia/reverse"):
            references[key] = {"control": standalone[control][0][key],
                               "candidate": standalone[measured][0][key]}
        compiler = compilation_inputs(
            folder / "compiler", slots, bindings,
            compilation["calibration_numerator"] if aa else "candidate",
            compilation["calibration_denominator"] if aa else control,
        )
        metrics[control] = {
            "runtime": groups | silesia_groups,
            "compiler": {"ordinary-process": compiler},
            "references": references,
            "absolute_case_median_ns": duration | silesia_ns,
            "sums_of_standalone_file_medians_ns": {"control": standalone[control][1],
                                                  "candidate": standalone[measured][1]},
        }
    return metrics


def family(sessions, kind):
    groups = sessions[0][kind]
    return {group: [session[kind][group] for session in sessions] for group in groups}


def calculate_calibration(output, policy, manifest_hash, bindings, host):
    selected = {control: [] for control in CONTROLS}
    sessions = {}
    for folder, record in sessions_for(output, policy, "calibrate", manifest_hash, None, host):
        sessions[folder.name] = sha(folder / "record.json")
        for control, metrics in session_metrics(folder, record, bindings, policy).items():
            selected[control].append(metrics)
    return {
        "manifest_sha256": manifest_hash,
        "stage": "calibrate",
        "sessions": sessions,
        "controls": {control: {kind: calibration(simultaneous(family(rows, kind)))
                               for kind in ("runtime", "compiler")} for control, rows in selected.items()},
    }


def stage_summary(output, policy, stage, manifest_hash, calibration_hash, host):
    return {
        "manifest_sha256": manifest_hash, "calibration_sha256": calibration_hash, "stage": stage,
        "sessions": {folder.name: sha(folder / "record.json")
                     for folder, _ in sessions_for(output, policy, stage, manifest_hash, calibration_hash, host)},
    }


def point_wins(sessions, chip, policy):
    def counts(rows):
        return {group: {side: {peer: sum(value < 0 for value in ratios.values())
                              for peer, ratios in peers.items()} for side, peers in actors.items()}
                for group, actors in rows.items()}
    raw = [session["references"] for session in sessions]
    pooled = {group: {side: {peer: {
        case: fmean(row[group][side][peer][case] for row in raw) for case in cases
    } for peer, cases in peers.items()} for side, peers in actors.items()}
        for group, actors in raw[0].items()}
    pooled_counts = counts(pooled)
    gates = {}
    for group, actors in pooled.items():
        suite, _ = group.split("/")
        gates[group] = {}
        for peer, control in actors["control"].items():
            candidate = actors["candidate"][peer]
            if chip == "M1":
                target = policy["reference_targets"][chip][suite]
                if pooled_counts[group]["control"][peer] != target:
                    decision = "unresolved"
                elif pooled_counts[group]["candidate"][peer] != target:
                    decision = "fail"
                else:
                    decision = "pass"
            else:
                lost = {case for case, ratio in control.items() if ratio < 0 <= candidate[case]}
                decision = "fail" if lost else "pass"
            gates[group][peer] = decision
    return {"decisions": gates, "pooled_log_ratios": pooled, "pooled_wins": pooled_counts,
            "session_wins": [counts(row) for row in raw]}


def calculate_assessment(output, policy, manifest_hash, bindings, seal, calibration_hash, host):
    sessions = {control: [] for control in CONTROLS}
    records = {}
    for stage in ("qualify", "confirm"):
        summary = stage_summary(output, policy, stage, manifest_hash, calibration_hash, host)
        require(summary == read(output / STAGE_FILES[stage]), f"{stage} seal differs.")
        records[stage] = summary["sessions"]
        for folder, record in sessions_for(output, policy, stage, manifest_hash, calibration_hash, host):
            for control, values in session_metrics(folder, record, bindings, policy).items():
                sessions[control].append(values)
    comparisons, decisions = {}, []
    for control, rows in sessions.items():
        runtime = nonregression(simultaneous(family(rows, "runtime")), seal["controls"][control]["runtime"])
        compiler = nonregression(simultaneous(family(rows, "compiler")), seal["controls"][control]["compiler"])
        refs = point_wins(rows, host["qualification_host"], policy)
        decisions.extend((runtime["decision"], compiler["decision"]))
        decisions.extend(result for group in refs["decisions"].values() for result in group.values())
        comparisons[control] = {
            "runtime": runtime, "compiler": compiler, "references": refs,
            "elapsed_time_faster": compiler["intervals"]["coordinates"]["elapsed_ns"]["interval95"][1] < 0,
            "compiler_session_log_ratios": [row["compiler"]["ordinary-process"][0] for row in rows],
            "absolute_case_median_ns": [row["absolute_case_median_ns"] for row in rows],
            "sums_of_standalone_file_medians_ns": [row["sums_of_standalone_file_medians_ns"] for row in rows],
        }
    decision = "fail" if "fail" in decisions else "unresolved" if "unresolved" in decisions else "pass"
    return {"manifest_sha256": manifest_hash, "calibration_sha256": calibration_hash,
            "stage": "assess", "decision": decision, "sessions": records, "comparisons": comparisons}


@dataclass(frozen=True)
class ScopedCampaign:
    manifest: dict
    digest: str
    output: Path
    policy: dict
    scope: str
    bindings: dict
    compiler_assessment: str | None = None

    def identity(self, stage, calibration_hash):
        return {"manifest_sha256": self.digest, "calibration_sha256": calibration_hash,
                "stage": stage, "scope": self.scope, "compiler_assessment_sha256": self.compiler_assessment}

    def session(self, folder, stage, calibration_hash, ordinal, controls):
        row = verify_session(folder, self.digest, stage, calibration_hash, self.manifest["host"],
                             scope_fields={"scope": self.scope, "compiler_assessment_sha256": self.compiler_assessment})
        require(row["ordinal"] == ordinal and row["controls"] == list(controls),
                f"Scheduled session identity differs: {folder}")
        return row


def scoped_schedule(policy, stage):
    counts = policy["sessions"]
    if stage == "calibrate":
        return [(f"{control}-{ordinal}", ordinal, (control,))
                for ordinal in range(1, counts["calibrate_per_control"] + 1)
                for control in SCOPED_CONTROLS]
    first = 1 if stage == "qualify" else counts["qualify"] + 1
    return [(f"session-{ordinal}", ordinal, SCOPED_CONTROLS if ordinal % 2 else SCOPED_CONTROLS[::-1])
            for ordinal in range(first, first + counts[stage])]


def scoped_slots(policy, stage, controls):
    compilation = policy["compilation"]
    if stage == "calibrate":
        return dict.fromkeys(compilation["calibration_slots"], controls[0])
    return {name: name for name in compilation["performance_slots"]}


def scoped_compiler_slots(policy, stage, controls, ordinal):
    roles = scoped_slots(policy, stage, controls)
    keys = tuple(roles)
    offset = (ordinal - 1) % len(keys)
    return {key: roles[key] for key in keys[offset:] + keys[:offset]}


def crossover_plan(controls, ordinal, calibrating):
    """Each step assigns real builds to the same two worker slot names."""
    for control in controls:
        candidate = control if calibrating else "candidate"
        for order in ORDERS:
            first = "A" if (ordinal % 2 == 1) == (order == "forward") else "B"
            for leg in (first, "B" if first == "A" else "A"):
                pair = (control, candidate) if leg == "A" else (candidate, control)
                yield {"comparison": control, "order": order, "leg": leg,
                       "slots": dict(zip(("control", "candidate"), pair, strict=True))}


def crossover_pair(bindings, step, calibrating):
    from compare_rebuilt import require_pair

    slots = {slot: {**bindings[label], "label": slot} for slot, label in step["slots"].items()}
    require_pair(slots["control"], slots["candidate"], calibration=calibrating)
    return slots


def crossed_units(first, swapped, count):
    require(len(first) == len(swapped) == count, "Missing or duplicate crossover cycles.")
    crossed = []
    for original, reversed_slots in zip(first, swapped, strict=True):
        require(original.keys() == reversed_slots.keys(), "Crossover coordinate inventory differs.")
        crossed.append({case: (log_ratio - reversed_slots[case]) / 2 for case, log_ratio in original.items()})
    return crossed


def verify_leg_order(expected, observed, start, end):
    require(len(observed) == len(expected), "Missing or duplicate crossover legs.")
    previous = start
    for step, leg in zip(expected, observed, strict=True):
        require(leg == {**step, "start_utc": leg.get("start_utc"), "end_utc": leg.get("end_utc")},
                "Crossover leg startup order or actor mapping differs.")
        require(previous <= leg["start_utc"] <= leg["end_utc"] <= end, "Crossover leg timestamps differ.")
        previous = leg["end_utc"]


def scoped_compiler_metrics(folder, row, campaign):
    controls = row["controls"]
    stage = row["stage"]
    slots = scoped_compiler_slots(campaign.policy, stage, controls, row["ordinal"])
    names = campaign.policy["compilation"]
    results = {}
    for control in controls:
        if stage == "calibrate":
            numerator, denominator = names["calibration_numerator"], names["calibration_denominator"]
        else:
            numerator, denominator = "candidate", control
        cycle = compilation_inputs(folder / "processes", slots, campaign.bindings, numerator, denominator,
                                   ordered=True)
        results[control] = {"compiler": {"ordinary-process": cycle}}
    return results


def scoped_runtime_metrics(folder, row, campaign):
    calibrating = row["stage"] == "calibrate"
    controls = row["controls"]
    plan = list(crossover_plan(controls, row["ordinal"], calibrating))
    verify_leg_order(plan, row["legs"], row["start_utc"], row["end_utc"])
    pair_root = folder / "pairs"
    for leg in row["legs"]:
        raw = pair_root / leg["comparison"] / f"{leg['order']}-{leg['leg']}" / "started.json"
        require(read(raw) == {key: value for key, value in leg.items() if key != "end_utc"},
                "Crossover leg startup marker differs.")
    require({p.name for p in pair_root.iterdir()} == set(controls), "Wrong crossover comparisons.")
    reference_labels = set(scoped_slots(campaign.policy, row["stage"], controls).values())
    require({p.name for p in (folder / "references").iterdir()} == reference_labels,
            "Standalone reference actor inventory differs.")
    standalone = {label: silesia_reference_inputs(folder / "references" / label, campaign.bindings[label])
                  for label in sorted(reference_labels)}
    fixtures = campaign.policy["timing"]["fixtures"]["cycles_per_leg"]
    silesia = campaign.policy["timing"]["silesia_pair"]["cycles_per_leg"]

    results = {}
    for control in controls:
        path = pair_root / control
        require({p.name for p in path.iterdir()} == {f"{order}-{leg}" for order in ORDERS for leg in ("A", "B")},
                "Crossover leg directory inventory differs.")
        groups, references, durations = {}, {}, {}
        for order in ORDERS:
            fixture_key, silesia_key = f"fixtures/{order}", f"silesia/{order}"
            legs, fixture_refs, absolute = {}, {}, {}
            for step in (step for step in plan if (step["comparison"], step["order"]) == (control, order)):
                leg = step["leg"]
                directory = path / f"{order}-{leg}"
                bindings = crossover_pair(campaign.bindings, step, calibrating)
                require(read(directory / "bindings.json") == bindings, "Crossover leg binary bindings differ.")
                fixture, refs, fixture_ns = fixture_inputs(directory / "suite81", bindings, orders=(order,), cycles=fixtures)
                paired, silesia_ns = silesia_pair_inputs(directory / "silesia", bindings, orders=(order,))
                legs[leg] = fixture | paired
                fixture_refs[leg] = refs[fixture_key]
                absolute[leg] = fixture_ns | silesia_ns

            for key, count in ((fixture_key, fixtures), (silesia_key, silesia)):
                groups[key] = crossed_units(legs["A"][key], legs["B"][key], count)
                durations[key] = {leg: values[key] for leg, values in absolute.items()}
            references[fixture_key] = {
                role: {peer: {case: fmean((ratio, fixture_refs["B"][swapped][peer][case]))
                              for case, ratio in cases.items()}
                       for peer, cases in fixture_refs["A"][role].items()}
                for role, swapped in (("control", "candidate"), ("candidate", "control"))
            }
            measured = control if calibrating else "candidate"
            references[silesia_key] = {"control": standalone[control][0][silesia_key],
                                       "candidate": standalone[measured][0][silesia_key]}
        results[control] = {"runtime": groups, "references": references, "absolute_case_median_ns": durations,
                            "sums_of_standalone_file_medians_ns": {"control": standalone[control][1],
                                                                  "candidate": standalone[measured][1]}}
    return results


def scoped_metrics(folder, row, campaign):
    if campaign.scope == "compiler":
        require(not (folder / "pairs").exists() and not (folder / "references").exists(),
                "Compiler scope cannot include runtime observations.")
        return scoped_compiler_metrics(folder, row, campaign)
    require(not (folder / "processes").exists(), "Runtime scope cannot include compiler observations.")
    return scoped_runtime_metrics(folder, row, campaign)


def scoped_sessions(campaign, stage, calibration_hash):
    base = campaign.output / stage
    schedule = scoped_schedule(campaign.policy, stage)
    require(base.is_dir() and {name for name, _, _ in schedule} == {p.name for p in base.iterdir()},
            f"Incomplete {campaign.scope} {stage} session inventory.")
    previous = ""
    for name, ordinal, controls in schedule:
        folder = base / name
        row = campaign.session(folder, stage, calibration_hash, ordinal, controls)
        require(previous <= row["start_utc"], "Session startup order differs.")
        previous = row["end_utc"]
        yield folder, row


def scoped_summary(campaign, stage, calibration_hash):
    return {**campaign.identity(stage, calibration_hash),
            "sessions": {folder.name: sha(folder / "record.json")
                         for folder, _ in scoped_sessions(campaign, stage, calibration_hash)}}


def gate_status(decisions):
    if "fail" in decisions:
        return "fail"
    return "unresolved" if "unresolved" in decisions else "pass"


def scoped_calibration(campaign):
    selected = {control: [] for control in SCOPED_CONTROLS}
    sessions = {}
    for folder, row in scoped_sessions(campaign, "calibrate", None):
        sessions[folder.name] = sha(folder / "record.json")
        for control, metrics in scoped_metrics(folder, row, campaign).items():
            selected[control].append(metrics)
    controls = {control: calibration(simultaneous(family(rows, campaign.scope))) for control, rows in selected.items()}
    return {**campaign.identity("calibrate", None), "sessions": sessions, "controls": controls,
            "decision": gate_status([row["decision"] for row in controls.values()])}


def compiler_gates(intervals, seal, control):
    """The previous compiler's RSS requires strict improvement."""
    calibrated = nonregression(intervals, seal)
    coordinates = calibrated["intervals"]["coordinates"]

    def decide(name, strict=False):
        if seal["decision"] != "pass":
            return "unresolved"
        row = coordinates[name]
        low, high = row["interval95"]
        if strict:
            return "pass" if high < 0 else "fail" if low >= 0 else "unresolved"
        return "pass" if high <= row["epsilon"] else "fail" if low > row["epsilon"] else "unresolved"

    gates = {"elapsed_ns": decide("elapsed_ns"),
             "maximum_resident_bytes": decide("maximum_resident_bytes", strict=control == "previous")}
    return {"decision": gate_status(list(gates.values())), "gates": gates, "intervals": calibrated["intervals"],
            "elapsed_time_faster": coordinates["elapsed_ns"]["interval95"][1] < 0}


def scoped_calibration_seal(campaign, path):
    expected = campaign.output / STAGE_FILES["calibrate"]
    require(path is not None and path.resolve() == expected.resolve(), "Use this scope's sealed calibration.")
    stored = read(expected)
    require(stored == scoped_calibration(campaign), "Scoped calibration does not reproduce.")
    return stored, sha(expected)


def scoped_stage_seal(campaign, stage, calibration_hash):
    expected = scoped_summary(campaign, stage, calibration_hash)
    require(expected == read(campaign.output / STAGE_FILES[stage]), f"Scoped {stage} seal differs.")
    return expected


def scoped_assessment(campaign, seal, calibration_hash):
    selected = {control: [] for control in SCOPED_CONTROLS}
    sessions = {}
    for stage in ("qualify", "confirm"):
        sessions[stage] = scoped_stage_seal(campaign, stage, calibration_hash)["sessions"]
        for folder, row in scoped_sessions(campaign, stage, calibration_hash):
            for control, metrics in scoped_metrics(folder, row, campaign).items():
                selected[control].append(metrics)
    comparisons, decisions = {}, [seal["decision"]]
    for control, rows in selected.items():
        intervals = simultaneous(family(rows, campaign.scope))
        if campaign.scope == "compiler":
            result = compiler_gates(intervals, seal["controls"][control], control)
            result["compiler_session_log_ratios"] = [row["compiler"]["ordinary-process"][0] for row in rows]
        else:
            result = nonregression(intervals, seal["controls"][control])
            refs = point_wins(rows, campaign.manifest["host"]["qualification_host"], campaign.policy)
            decisions.extend(result for group in refs["decisions"].values() for result in group.values())
            result["references"] = refs
            for key in ("absolute_case_median_ns", "sums_of_standalone_file_medians_ns"):
                result[key] = [row[key] for row in rows]
        decisions.append(result["decision"])
        comparisons[control] = result
    return {**campaign.identity("assess", calibration_hash), "sessions": sessions,
            "decision": gate_status(decisions), "comparisons": comparisons}


def verify_scoped_assessment(campaign):
    seal, calibration_hash = scoped_calibration_seal(campaign, campaign.output / STAGE_FILES["calibrate"])
    path = campaign.output / STAGE_FILES["assess"]
    if campaign.scope == "runtime" and seal["decision"] != "pass":
        require(not path.exists() and all(
            not (campaign.output / name).exists()
            for stage in ("qualify", "confirm") for name in (stage, STAGE_FILES[stage])
        ), "Invalid runtime calibration forbids candidate comparisons.")
        return None
    if not path.exists():
        for stage in ("qualify", "confirm"):
            if (campaign.output / STAGE_FILES[stage]).exists():
                scoped_stage_seal(campaign, stage, calibration_hash)
        return None
    computed = scoped_assessment(campaign, seal, calibration_hash)
    require(computed == read(path), "Scoped assessment does not reproduce.")
    return computed


def compiler_prerequisite(campaign):
    path = campaign.output / STAGE_FILES["assess"]
    require(path.is_file(), "Runtime requires this campaign's passing compiler assessment.")
    assessment = verify_scoped_assessment(campaign)
    require(assessment is not None and assessment["decision"] == "pass",
            "Runtime requires this campaign's passing compiler assessment.")
    return sha(path)


def open_scope(path, scope, record=None):
    manifest, digest, output, policy = load_campaign(path, record, scope=scope)
    bindings_file = output / "prepared-bindings.json"
    checked(bindings_file, manifest["prepared_bindings_sha256"])
    bindings = pinned_bindings(manifest)
    require(read(bindings_file) == bindings, "Prepared binaries or compiler bindings changed.")
    require(len({row["build_directory"] for row in bindings.values()}) == 3
            and len({row["configuration_sha256"] for row in bindings.values()}) == 1,
            "Scoped actors need separate builds of the same configuration.")
    pins = manifest["source_commits"]
    candidate = pins["F"] if "F" in pins else pins["N"]
    parent = pins["N"] if "F" in pins else STARTING_SOURCE
    candidate_source = manifest["actors"]["candidate"]["source"]
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", parent, candidate],
                              cwd=candidate_source, check=False)
    require(parent != candidate and ancestry.returncode == 0, "Candidate is not descended from its pinned starting source.")
    compiler = ScopedCampaign(manifest, digest, output / "compiler", policy, "compiler", bindings)
    if scope == "compiler":
        return compiler
    return ScopedCampaign(manifest, digest, output / "runtime", policy, scope, bindings,
                          compiler_prerequisite(compiler))


def verify_scoped_campaign(path, record, scope):
    campaign = open_scope(path, scope, record)
    result = verify_scoped_assessment(campaign)
    decision = "incomplete" if result is None else result["decision"]
    # A final campaign is only decided after its separately gated runtime scope.
    overall = decision
    if campaign.manifest["purpose"] == "final-qualification" and scope == "compiler" and decision == "pass":
        overall = "runtime required"
    return {"manifest_sha256": campaign.digest, "scope": scope,
            "scope_assessment": decision, "assessment": overall}


def verify_campaign(path, record):
    manifest, digest, output, policy = load_campaign(path, record)
    bindings = pinned_bindings(manifest)
    calibration_path = output / STAGE_FILES["calibrate"]
    calibration_hash = sha(calibration_path)
    seal = calculate_calibration(output, policy, digest, bindings, manifest["host"])
    require(seal == read(calibration_path), "Calibration does not reproduce from raw sessions.")
    assessment_path = output / STAGE_FILES["assess"]
    if not assessment_path.exists():
        for stage in ("qualify", "confirm"):
            checkpoint = output / STAGE_FILES[stage]
            if checkpoint.exists():
                require(stage_summary(output, policy, stage, digest, calibration_hash, manifest["host"]) == read(checkpoint),
                        f"{stage} seal differs.")
        return {"manifest_sha256": digest, "calibration_sha256": calibration_hash, "assessment": "incomplete"}
    computed = calculate_assessment(output, policy, digest, bindings, seal, calibration_hash,
                                    manifest["host"])
    require(computed == read(assessment_path), "Assessment does not reproduce from raw sessions.")
    return {"manifest_sha256": digest, "calibration_sha256": calibration_hash, "assessment": computed["decision"]}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New extraction directory")
    parser.add_argument("--record", type=Path, default=HERE, help="Directory with archived observations")
    parser.add_argument("--bench-root", type=Path, help="Override the benchmark repository location")
    parser.add_argument("--campaign-record", type=Path, help="Verify a sealed route campaign without timing")
    parser.add_argument("--campaign", type=Path, help="Immutable campaign manifest")
    parser.add_argument("--scope", choices=SCOPES)
    args = parser.parse_args()
    if not __debug__:
        parser.error("Use Python with assertions enabled.")
    if args.campaign is not None or args.campaign_record is not None or args.scope is not None:
        if args.campaign is None or args.campaign_record is None:
            parser.error("Campaign verification requires both --campaign and --campaign-record.")
        path = args.campaign.resolve()
        result = (verify_campaign(path, args.campaign_record) if args.scope is None
                  else verify_scoped_campaign(path, args.campaign_record, args.scope))
        print(json.dumps(result, indent=2))
        return
    if args.output is None:
        parser.error("Historical archive verification requires --output.")
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    record = args.record.resolve(strict=True)
    archive = record / "observations.tar.gz"
    manifest = read(record / "observations.json")
    checked(archive, manifest["archive_sha256"])
    root = args.output.resolve()
    root.mkdir(parents=True)
    with tarfile.open(archive, "r:gz") as data:
        files = data.getmembers()
        assert len(files) == len(manifest["files"])
        assert all(item.isfile() and manifest["files"][item.name]["bytes"] == item.size for item in files)
        data.extractall(root, filter="data")
    for name, pin in manifest["files"].items():
        checked(root / name, pin["sha256"])

    suite = root / "suite81"
    routes = packets / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    verifier = run_path(str(routes / "verify_timings.py"))["verify"]
    oracle = {row["case"]: row for row in read(suite / "pinned-peers/libdeflate-output-oracle.json")}
    result = verifier(suite, suite / "cranelift-results.json", "cranelift", oracle)
    print(json.dumps(result, indent=2))

    silesia = root / "silesia"
    if "silesia/complete.json" not in manifest["files"]:
        return
    package = packets / "mechdeflate-silesia-v1"
    assert read(silesia / "complete.json")["independent_inflation"] == read(
        package / "complete.json"
    )["independent_inflation"]
    original_score = read(silesia / "scores.json")
    subprocess.run(
        [sys.executable, "-B", package / "score_silesia.py", silesia, package / "corpus.json"],
        check=True, stdout=subprocess.DEVNULL,
    )
    assert original_score == read(silesia / "scores.json")
    print("Verified both Silesia orders, all 12 streams and all paired ratios.")


if __name__ == "__main__":
    main()
