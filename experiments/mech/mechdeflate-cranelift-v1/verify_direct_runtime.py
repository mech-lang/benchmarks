"""Verify and regenerate the frozen direct M1 comparison from its retained records."""

from argparse import ArgumentParser
import csv
import gzip
import json
from math import expm1, isclose
from pathlib import Path, PurePosixPath
from runpy import run_path
from shutil import copyfileobj
from statistics import fmean, median
import sys
import tarfile

from campaign_stats import balanced_cycles, paired_log
from compare_rebuilt import write_new
from rebuild import PARENT, checked, read, sha
from replay import fixture_campaign_controller
from verify import crossover_pair, crossover_plan, require, verify_inventory, verify_leg_order

SESSION_NAMES = ("session-1", "session-2", "session-3")
ORDERS = ("forward", "reverse")
ROLES = ("O", "F", "libdeflate")
COMPARISONS = {"O/libdeflate": ("O", "libdeflate"), "F/libdeflate": ("F", "libdeflate"), "F/O": ("F", "O")}
FIXTURE_SLOTS = {"control": "mech-control", "candidate": "mech-experiment", "libdeflate": "libdeflate"}
FIXTURE_ORACLE = "pinned-peers/libdeflate-output-oracle.json"
CSV_FIELDS = (
    "suite", "session", "order", "case", "O_ns", "F_ns", "libdeflate_ns",
    "O_vs_libdeflate_pct", "F_vs_libdeflate_pct", "F_vs_O_pct",
)


def check_file(path, pin):
    require(path.is_file() and path.stat().st_size == pin["bytes"], f"Missing or wrong-sized file: {path}")
    checked(path, pin["sha256"])


def extract_archive(archive, inventory, destination):
    """Use only ordinary members named in the frozen inventory."""
    files, directories = inventory["files"], inventory["directories"]
    require(not files.keys() & directories.keys(), "An archive member is both file and directory.")
    unseen = files.keys() | directories.keys()
    destination.mkdir()
    with tarfile.open(archive, "r|gz") as stream:
        for member in stream:
            name = member.name
            relative = PurePosixPath(name)
            require(name in unseen, f"Unexpected or duplicate archive member: {name}")
            require(relative.as_posix() == name and not relative.is_absolute() and ".." not in relative.parts
                    and relative.parts, f"Noncanonical archive member: {name}")
            unseen.remove(name)
            target = destination.joinpath(*relative.parts)
            mode = f"{member.mode & 0o7777:04o}"
            if name in directories:
                require(member.isdir() and mode == directories[name]["mode"], f"Directory differs: {name}")
                target.mkdir(parents=True, exist_ok=True)
            else:
                pin = files[name]
                require(member.isfile() and mode == pin["mode"] and member.size == pin["bytes"],
                        f"File type, mode or size differs: {name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with stream.extractfile(member) as source, target.open("xb") as output:
                    copyfileobj(source, output)
                check_file(target, pin)
    require(not unseen, f"Missing archive members: {sorted(unseen)}")


def open_record(record, output, inputs):
    receipt = read(record / "archive-receipt.json")
    published = receipt["published_files"]
    for name in published.values():
        require(Path(name).name == name and name not in {"", ".", ".."}, f"Invalid published filename: {name}")
    archive, inventory_file = (record / published[key] for key in ("archive", "inventory"))
    check_file(archive, receipt)
    check_file(inventory_file, receipt["verified_inventory"])
    inventory = read(inventory_file)
    require(len(inventory["files"]) == receipt["content_files_verified"]
            and len(inventory["directories"]) == receipt["content_directories_verified"],
            "Archive inventory counts differ from the receipt.")
    destination = output / "archive"
    extract_archive(archive, inventory, destination)

    recorded_run = PurePosixPath(inputs["fixture_stage"]["root"]).parent
    matches = [PurePosixPath(name).parent for name in inventory["files"]
               if name.endswith(f"/{recorded_run.name}/inputs.json")]
    require(len(matches) == 1, "Expected one recorded run in the archive.")
    archived_run, = matches
    require(recorded_run.is_absolute() and recorded_run.parts[-len(archived_run.parts):] == archived_run.parts,
            "The archived run does not match its recorded path suffix.")
    recorded_root = PurePosixPath(*recorded_run.parts[:-len(archived_run.parts)])
    require(recorded_root.is_absolute(), "Expected an absolute recorded archive root.")

    def locate(recorded):
        original = PurePosixPath(recorded)
        require(original.is_relative_to(recorded_root) and original.as_posix() == recorded
                and ".." not in original.parts, f"Path escapes the recorded archive: {recorded}")
        name = original.relative_to(recorded_root).as_posix()
        require(name in inventory["files"] or name in inventory["directories"], f"Missing archived path: {recorded}")
        return destination / name

    run = locate(str(recorded_run))
    for name in ("inputs.json", "cases.csv", "summary.json", "report.md", "commands/measure.py",
                 "commands/summarize.py", "commands/verification.log"):
        checked(run / name, sha(record / name))
    checked(run / "commands/measure.py", inputs["driver_sha256"])
    return run, recorded_root, recorded_run, locate


def verify_stage(binding, recorded_run, locate):
    stage_name = str(recorded_run / "fixture-stage")
    receipt_name = str(recorded_run / "fixture-stage.json")
    require(binding["root"] == stage_name and binding["receipt"] == receipt_name, "Fixture stage paths differ.")
    receipt = locate(receipt_name)
    checked(receipt, binding["receipt_sha256"])
    stage = read(receipt)
    stage_root = locate(stage_name)
    verify_inventory(stage_root, stage["files"])
    require(stage["root"] == stage_name and stage["active_controller"] == "campaign-controller.py"
            and stage["cases"] == 81 and stage["cycles_per_leg"] == 2 and stage["permutations"] == 24,
            "Fixture stage does not match the collection protocol.")

    pinned = read(PARENT / "mechdeflate-81-v1/actors/bindings.json")
    checked(stage_root / "controller.py", pinned["controller_sha256"])
    checked(stage_root / FIXTURE_ORACLE, pinned["oracle_sha256"])
    controller = fixture_campaign_controller((stage_root / "controller.py").read_text(), 2)
    require(controller == (stage_root / stage["active_controller"]).read_text(), "Fixture controller differs.")

    fixture_names = []
    manifest = stage_root / "fixtures.json"
    for index, row in enumerate(read(manifest)):
        for field in ("input", "prefix", "expected"):
            path = stage_root / "fixtures" / str(index) / field
            require(locate(row[field]) == path, f"Fixture payload path differs: {row['name']}/{field}")
        checked(locate(row["input"]), row["input_sha256"])
        checked(locate(row["expected"]), row["expected_sha256"])
        require(locate(row["prefix"]).stat().st_size == row["prefix_bytes"], "Fixture prefix length differs.")
        fixture_names.append(row["name"])
    require(len(fixture_names) == len(set(fixture_names)) == 81, "Fixture case inventory differs.")

    peers = read(stage_root / "pinned-peers/pins.json")
    require(peers["input_inventory_sha256"] == sha(manifest), "Fixture input manifest hash differs.")
    stage["peers"] = peers["actors"]
    require(stage["peers"].keys() == {"libdeflate", stage["reference_actor"]}, "Fixture peer inventory differs.")
    for name, pin in stage["peers"].items():
        expected = pinned["peers"]["libdeflate" if name == "libdeflate" else "reference"]
        require(all(pin[key] == digest for key, digest in expected.items()), f"Fixture peer pin differs: {name}")
        require(pin["command"][-1] == f"{stage_name}/fixtures.json", f"Fixture peer input path differs: {name}")
        require(all(locate(path).is_relative_to(stage_root) for path in pin["command"]),
                f"Fixture peer uses a file outside the stage: {name}")
        checked(locate(pin["command"][0]), expected["binary_sha256"])
        if "metadata_sha256" in expected:
            checked(locate(pin["command"][1]), expected["metadata_sha256"])
    return stage, tuple(fixture_names)


def fixture_worker(actor):
    binary = PurePosixPath(actor["81"]["path"])
    return str(binary), str(binary.with_name("metadata.json"))


def verify_actor(actor, locate):
    binary, metadata = fixture_worker(actor)
    checked(locate(binary), actor["81"]["sha256"])
    checked(locate(metadata), actor["artifacts"]["metadata.json"])
    checked(locate(actor["silesia"]["path"]), actor["silesia"]["sha256"])


def roles_for_slots(leg):
    known = {"previous": "O", "candidate": "F"}
    actual = {known[pinned_role]: slot for slot, pinned_role in leg["slots"].items()}
    return actual | {"libdeflate": "libdeflate"}


def fixture_rows(directory, slots, actual, order, stage, names, root, locate, receipt_hash, verify_timings, libdeflate):
    direction = f"cranelift-{order}"
    leg = directory / direction
    pins = read(leg / "pins.json")
    fixtures = f"{stage['root']}/fixtures.json"
    actors = dict(stage["peers"])
    for slot in ("control", "candidate"):
        actor = slots[slot]
        actors[FIXTURE_SLOTS[slot]] = {
            "command": [*fixture_worker(actor), fixtures],
            "binary_sha256": actor["81"]["sha256"],
            "metadata_sha256": actor["artifacts"]["metadata.json"],
        }
    require(pins["actors"] == actors and pins["input_inventory_sha256"] == stage["files"]["fixtures.json"]["sha256"],
            f"Fixture actor commands or inputs differ: {leg}")
    require(actors["libdeflate"]["binary_sha256"] == libdeflate["binary_sha256"]
            and pins["level"] == libdeflate["level"] and pins["libdeflate_source"]["version"] == libdeflate["version"],
            f"Fixture libdeflate identity differs: {leg}")
    execution = read(directory / "fixture-execution.json")
    controller = f"{stage['root']}/{stage['active_controller']}"
    cwd = PurePosixPath(stage["root"]).relative_to(root).parts[0]
    prefix = execution["output_prefix"]
    require(locate(prefix) == leg, f"Fixture output prefix differs: {leg}")
    command = execution["command"]
    worker_roots = [str(PurePosixPath(fixture_worker(slots[name])[0]).parent) for name in ("control", "candidate")]
    require(execution == {"fixture_stage_receipt_sha256": receipt_hash,
                          "controller": controller,
                          "controller_sha256": stage["files"][stage["active_controller"]]["sha256"],
                          "command": command, "output_prefix": prefix, "cwd": str(root / cwd)}
            and PurePosixPath(command[0]).is_absolute()
            and command[1:] == ["-B", controller, prefix, *worker_roots, *(("reverse",) if order == "reverse" else ())],
            f"Fixture execution receipt differs: {leg}")
    for local, staged in (("controller.py", stage["active_controller"]), ("compare-library.py", "compare-library.py"),
                          ("fixtures.json", "fixtures.json"), (FIXTURE_ORACLE, FIXTURE_ORACLE)):
        checked(directory / local, stage["files"][staged]["sha256"])

    oracle = {row["case"]: row for row in read(directory / FIXTURE_ORACLE)}
    receipt = verify_timings(directory, directory / "cranelift-results.json", "cranelift", oracle, orders=(order,))
    require(receipt == read(directory / "cranelift-verified.json")
            and (receipt["cases"], receipt["blocks_per_case"], receipt["runtime_observations_recomputed"])
            == (81, 48, 491328), f"Fixture verification receipt differs: {leg}")
    actor_names = tuple(actors)
    startup = tuple(read(leg / "worker-startup.json"))
    forward_startup = ("mech-control", "mech-experiment", stage["reference_actor"], "libdeflate")
    require(startup == (forward_startup if order == "forward" else forward_startup[::-1]),
            f"Fixture startup order differs: {leg}")
    rows = read(leg / "summary.json")
    require(tuple(row["case"] for row in rows) == (names if order == "forward" else names[::-1]),
            f"Fixture case order differs: {leg}")

    actor = {role: FIXTURE_SLOTS[actual[role]] for role in ROLES}
    result = {}
    for row in rows:
        case = row["case"]
        folder = leg / case
        warmups = read(folder / "warmups.json")
        require(warmups.keys() == actors.keys() and all(
            item["calls"] > 0 and item["seconds"] >= 0.2 and item["observation"]["warmup"]
            and item["observation"]["case"] == case for item in warmups.values()
        ), f"Fixture warmups differ: {case}")
        with gzip.open(folder / "observations.json.gz", "rt") as stream:
            blocks = json.load(stream)
        cycles = balanced_cycles(blocks, actor_names, 2)
        ratios = {role: fmean(paired_log(block["means"][actor[role]], block["means"]["libdeflate"])
                             for block in blocks) for role in ("O", "F")}
        change = fmean(fmean(paired_log(block["means"]["mech-experiment"], block["means"]["mech-control"])
                             for block in cycle) for cycle in cycles)
        if actual["F"] == "control":
            change = -change
        require(isclose(change, ratios["F"] - ratios["O"], rel_tol=1e-12, abs_tol=1e-12),
                f"Paired fixture ratios disagree: {case}")
        result[case] = {
            "log_ratios": {"O/libdeflate": ratios["O"], "F/libdeflate": ratios["F"], "F/O": change},
            "absolute_ns": {role: row["median_seconds"][actor[role]] * 1e9 for role in ROLES},
        }
    return result, receipt["runtime_observations_recomputed"]


def fixture_verifier():
    routes = PARENT / "mechdeflate-phase-routes-v1"
    sys.path.insert(0, str(routes))
    try:
        return run_path(str(routes / "verify_timings.py"))["verify"]
    finally:
        sys.path.pop(0)


def silesia_rows(directory, slots, actual, direction, silesia_files, oracle, silesia_reference):
    described = read(directory / "binding.json")
    names = ("control", "candidate", "libdeflate")
    order = names if direction == "forward" else names[::-1]
    assert described == {"slots": {**{role: slots[role]["silesia"] for role in slots},
                                  "libdeflate": {key: silesia_reference[key] for key in ("path", "sha256")}},
                         "order": list(order)}
    rows = read(directory / f"timings-{direction}.json")
    names_in_order = silesia_files if direction == "forward" else silesia_files[::-1]
    assert tuple(row["case"] for row in rows) == names_in_order
    verified = read(directory / "independent-inflation.json")
    assert set(verified) == set(silesia_files)
    completed = read(directory / "complete.json")
    assert completed == {"cases": len(silesia_files), "balanced_blocks_per_case": 6,
                         "timed_calls": len(silesia_files) * 6 * len(ROLES)}
    for row in rows:
        case = row["case"]
        assert verified[case] == dict.fromkeys(order, oracle[case]["libdeflate"])
        assert tuple(row["warmup_ns"]) == order and all(t > 0 for t in row["warmup_ns"].values())
        blocks, = balanced_cycles(row["blocks"], order, 1)
        assert all(tuple(block["ns"]) == tuple(block["order"])
                   and all(t > 0 for t in block["ns"].values()) for block in blocks)
        assert row["median_ns"] == {role: median(block["ns"][role] for block in blocks) for role in order}
        yield case, {
            "log_ratios": {key: fmean(paired_log(block["ns"][actual[left]], block["ns"][actual[right]])
                                     for block in blocks) for key, (left, right) in COMPARISONS.items()},
            "absolute_ns": {role: row["median_ns"][actual[role]] for role in ROLES},
        }

def count_and_margin(data, comparison):
    observations = [row["log_ratios"][comparison] for row in data.values()]
    return {
        "wins": sum(x < 0 for x in observations),
        "losses": sum(x > 0 for x in observations),
        "ties": sum(x == 0 for x in observations),
        "geomean_change_percent": 100 * expm1(fmean(observations)),
        "median_case_change_percent": median(100 * expm1(x) for x in observations),
    }

def aggregate(raw, suites, sessions, directions, suite):
    sets = [raw[session, direction, leg][suite]
            for session in sessions for direction in directions for leg in ("A", "B")]
    return {case: {
        "log_ratios": {key: fmean(rows[case]["log_ratios"][key] for rows in sets) for key in COMPARISONS},
        "absolute_ns": {role: median(rows[case]["absolute_ns"][role] for rows in sets) for role in ROLES},
    } for case in suites[suite]}

def summarize(output, run, raw, records, suites, fixture_calls, silesia_calls, inputs):
    labels = (*SESSION_NAMES, "pooled")
    directions = (*ORDERS, "both")
    by_case = {}
    summary = {}
    for suite in suites:
        summary[suite] = {}
        for label in labels:
            summary[suite][label] = {}
            for direction in directions:
                case_rows = aggregate(raw, suites, SESSION_NAMES if label == "pooled" else (label,),
                                      ORDERS if direction == "both" else (direction,), suite)
                by_case[suite, label, direction] = case_rows
                summary[suite][label][direction] = {
                    "cases": len(case_rows),
                    "comparisons": {key: count_and_margin(case_rows, key) for key in COMPARISONS},
                    "sum_of_case_medians_ns": {role: sum(row["absolute_ns"][role] for row in case_rows.values())
                                              for role in ROLES},
                }

    flagged = {}
    for suite in suites:
        flagged[suite] = {}
        for comparison in COMPARISONS:
            flagged[suite][comparison] = []
            pooled = by_case[suite, "pooled", "both"]
            for case in suites[suite]:
                delta = 100 * expm1(pooled[case]["log_ratios"][comparison])
                values = [100 * expm1(by_case[suite, session, order][case]["log_ratios"][comparison])
                          for session in SESSION_NAMES for order in ORDERS]
                minimum, maximum = min(values), max(values)
                near, changed_sign, loss_or_tie = abs(delta) <= 1, minimum < 0 < maximum, delta >= 0
                if near or changed_sign or loss_or_tie:
                    flagged[suite][comparison].append({
                        "case": case, "pooled_percent": delta, "min_session_order_percent": minimum,
                        "max_session_order_percent": maximum, "near_parity": near,
                        "changed_sign": changed_sign, "pooled_loss_or_tie": loss_or_tie,
                    })
            flagged[suite][comparison].sort(key=lambda row: -row["pooled_percent"])

    leg_losses = []
    for (session, direction, leg), leg_data in raw.items():
        for suite, cases in leg_data.items():
            for case, row in cases.items():
                for role in ("O", "F"):
                    change = row["log_ratios"][f"{role}/libdeflate"]
                    if change >= 0:
                        leg_losses.append({"session": session, "order": direction, "leg": leg, "suite": suite,
                                           "case": case, "role": role, "percent": 100 * expm1(change),
                                           "actor_ns": row["absolute_ns"][role],
                                           "libdeflate_ns": row["absolute_ns"]["libdeflate"]})

    with (output / "cases.csv").open("x", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(CSV_FIELDS)
        for (suite, session, order), rows in by_case.items():
            for case, row in rows.items():
                writer.writerow([suite, session, order, case, *(row["absolute_ns"][role] for role in ROLES),
                                 *(100 * expm1(row["log_ratios"][key]) for key in COMPARISONS)])

    summary = {
        "purpose": inputs["purpose"], "inputs_sha256": sha(run / "inputs.json"),
        "cases_csv_sha256": sha(output / "cases.csv"),
        "sessions": records, "fixture_legs": len(raw), "fixture_timed_calls": fixture_calls,
        "silesia_legs": len(raw), "silesia_timed_calls": silesia_calls,
        "results": summary, "close_inconsistent_and_losing_cases": flagged,
        "individual_leg_losses_and_ties_vs_libdeflate": leg_losses,
    }
    write_new(output / "summary.json", summary)
    return summary, by_case


def counts(entry):
    values = (entry["wins"], entry["losses"], entry["ties"])
    return f"{values[0]}/{values[1]}/{values[2]} ({entry['geomean_change_percent']:+.3f}%)"

def render_report(output, record, pinned, summary, by_case, suites):
    fixture_calls = summary["fixture_timed_calls"]
    silesia_calls = summary["silesia_timed_calls"]
    records = summary["sessions"]
    flagged = summary["close_inconsistent_and_losing_cases"]
    leg_losses = summary["individual_leg_losses_and_ties_vs_libdeflate"]
    labels = (*SESSION_NAMES, "pooled")
    directions = (*ORDERS, "both")
    summary = summary["results"]
    titles = {"fixtures": "81 fixtures", "silesia": "12 Silesia files"}
    lines = [
        "# M1 direct runtime comparison",
        "",
        f"Before is O (`{pinned['previous']['source_commit']}`). After is F "
        f"(`{pinned['candidate']['source_commit']}`). Both used their frozen executables and the pinned libdeflate level-12 peers.",
        "Three complete sessions ran on the Apple M1. Each session used both case orders and both O/F slot mappings. "
        "Each fixture leg retained two full permutation cycles with the existing four workers. "
        "Each Silesia leg included O, F and libdeflate together in all six permutations. "
        "Every timing block includes both Mech builds and libdeflate.",
        "",
        "The existing correctness checks verified the fixture output and independently inflated every Silesia file. "
        "All Silesia streams matched the pinned output size and digest. "
        "The fixture timer measures closed compression through output acquisition and heap cleanup. "
        "The Silesia timer measures one level-12 encode with preloaded input. "
        f"The record contains {fixture_calls:,} timed fixture calls and {silesia_calls:,} timed Silesia calls, plus warmups. "
        "These direct results are separate from the sealed qualification campaigns. "
        f"[Input identities and schedule]({record / 'inputs.json'}) · "
        f"[Raw evidence receipt]({record / 'archive-receipt.json'})",
        "",
        "Counts are wins/losses/ties. A negative percentage means the first actor took less time. "
        "Percentages use the geometric mean of paired time ratios across cases. "
        "The summaries weight each included session, order and slot mapping equally. "
        "Absolute times are medians of the selected leg medians per case. The absolute suite column sums those case medians.",
    ]
    for suite, cases in suites.items():
        unit, scale = ("ms", 1e6) if suite == "fixtures" else ("s", 1e9)
        lines.extend([
            "",
            f"## {titles[suite]}",
            "",
            f"| Session | Order | O / libdeflate | F / libdeflate | F / O | O / F / libdeflate ({unit}) |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ])
        for label in labels:
            for order in directions:
                entry = summary[suite][label][order]
                absolute = " / ".join(f"{entry['sum_of_case_medians_ns'][role] / scale:.6f}" for role in ROLES)
                cells = " | ".join(counts(entry["comparisons"][key]) for key in COMPARISONS)
                lines.append(f"| {label} | {order} | {cells} | {absolute} |")
        if suite == "silesia":
            lines.extend([
                "",
                "| File | O (s) | F (s) | libdeflate (s) | O / libdeflate | F / libdeflate | F / O |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ])
            for case, row in by_case[suite, "pooled", "both"].items():
                cells = [*(f"{row['absolute_ns'][role] / 1e9:.6f}" for role in ROLES),
                         *(f"{100 * expm1(row['log_ratios'][key]):+.3f}%" for key in COMPARISONS)]
                lines.append(f"| {case} | {' | '.join(cells)} |")
    lines.extend([
        "",
        "## Close, inconsistent and losing cases",
        "",
        "Close means within 1% of parity after pooling both orders. A sign change means at least one win and one loss across "
        "the six session-by-order estimates. The observed range covers those six estimates. "
        "Every pooled loss or tie is included.",
        "",
        "| Suite and comparison | Case | Pooled time change | Observed range | Finding |",
        "| --- | --- | ---: | ---: | --- |",
    ])
    for suite, comparison in ((suite, key) for suite in suites for key in COMPARISONS):
        for row in flagged[suite][comparison]:
            flags = []
            if row["near_parity"]:
                flags.append("close")
            if row["changed_sign"]:
                flags.append("sign change")
            if row["pooled_loss_or_tie"]:
                flags.append("loss" if row["pooled_percent"] > 0 else "tie")
            lines.append(f"| {suite}, {comparison} | `{row['case']}` | {row['pooled_percent']:+.3f}% | "
                         f"{row['min_session_order_percent']:+.3f}% to {row['max_session_order_percent']:+.3f}% | "
                         f"{', '.join(flags)} |")
    lines.extend(["", "### Individual leg losses and ties against libdeflate", ""])
    if leg_losses:
        lines.extend([
            "| Session | Order and slot mapping | Suite | Case | Actor | Time change | Actor / libdeflate (ns) |",
            "| --- | --- | --- | --- | --- | ---: | ---: |",
        ])
        for row in leg_losses:
            lines.append(f"| {row['session']} | {row['order']}-{row['leg']} | {row['suite']} | `{row['case']}` | "
                         f"{row['role']} | {row['percent']:+.3f}% | {row['actor_ns']:.3f} / {row['libdeflate_ns']:.3f} |")
    else:
        lines.append("Both builds won every case against libdeflate in every leg.")
    lines.extend([
        "",
        "[All case results by session and order](cases.csv) · [Machine-readable summary](summary.json)",
        "",
        "## Collection records",
        "",
        "| Session | Start UTC | End UTC | SHA-256 of record |",
        "| --- | --- | --- | --- |",
    ])
    for session, metadata in records.items():
        lines.append(f"| {session} | `{metadata['start_utc']}` | `{metadata['end_utc']}` | `{metadata['record_sha256']}` |")
    with (output / "report.md").open("x") as stream:
        stream.write("\n".join(lines) + "\n")


def verify_cases(original, regenerated):
    with original.open(newline="") as source, regenerated.open(newline="") as output:
        recorded, replay = csv.reader(source), csv.reader(output)
        require(tuple(next(recorded)) == tuple(next(replay)) == CSV_FIELDS, "Case columns differ.")
        count = 0
        for count, (expected, actual) in enumerate(zip(recorded, replay, strict=True), 1):
            require(len(actual) == len(expected) == len(CSV_FIELDS) and actual[:4] == expected[:4],
                    f"Case identity or order differs at row {count}.")
            for name, first, second in zip(CSV_FIELDS[4:], actual[4:], expected[4:], strict=True):
                require(isclose(float(first), float(second), rel_tol=1e-12, abs_tol=1e-12),
                        f"Case row {count} differs for {name}: {first} versus {second}")
    require(count == 1116, f"Expected 1116 case rows, found {count}.")
    return count


def verify_summary(actual, expected, key="summary"):
    require(type(actual) is type(expected), f"Summary type differs: {key}")
    if isinstance(expected, dict):
        require(tuple(actual) == tuple(expected), f"Summary fields or order differ: {key}")
        for name, value in expected.items():
            verify_summary(actual[name], value, f"{key}/{name}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"Summary list length differs: {key}")
        for index, (first, second) in enumerate(zip(actual, expected, strict=True)):
            verify_summary(first, second, f"{key}/{index}")
    elif isinstance(expected, float):
        require(isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12),
                f"Summary number differs: {key}: {actual} versus {expected}")
    else:
        require(actual == expected, f"Summary value differs: {key}")


def verify_direct_runtime(record, output):
    require(__debug__, "Run with Python assertions enabled.")
    require(record.is_absolute() and output.is_absolute(), "Record and output must be absolute paths.")
    record = record.resolve(strict=True)
    output.mkdir()
    inputs = read(record / "inputs.json")
    require(inputs["purpose"] == "direct-runtime-comparison"
            and inputs["host"]["qualification_host"] == "M1"
            and (inputs["fixture_cycles_per_leg"], inputs["silesia_cycles_per_leg"]) == (2, 1),
            "Expected the frozen direct M1 comparison.")
    run, root, recorded_run, locate = open_record(record, output, inputs)
    stage, fixture_names = verify_stage(inputs["fixture_stage"], recorded_run, locate)
    require((run / "commands/exit.txt").read_text().strip() == "0", "Timing did not complete.")

    package = PARENT / "mechdeflate-silesia-v1"
    corpus_manifest = package / "corpus.json"
    checked(corpus_manifest, inputs["silesia_corpus_sha256"])
    silesia_files = tuple(read(corpus_manifest)["files"])
    require(len(silesia_files) == 12, "Silesia corpus inventory differs.")
    oracle = read(package / "complete.json")["independent_inflation"]
    silesia_reference = inputs["libdeflate"]["silesia"]
    require(silesia_reference["sha256"] == read(package / "binding.json")["actors"]["libdeflate"]["sha256"]
            and silesia_reference["level"] == 12, "Silesia libdeflate identity differs.")
    checked(locate(silesia_reference["path"]), silesia_reference["sha256"])
    pinned = inputs["actor_bindings"]
    require(pinned.keys() == {"previous", "candidate"}, "Mech actor inventory differs.")
    for actor in pinned.values():
        verify_actor(actor, locate)

    verify_timings = fixture_verifier()
    raw, records = {}, {}
    fixture_calls = silesia_calls = 0
    sessions = run / "sessions"
    require(set(inputs["schedule"]) == {folder.name for folder in sessions.iterdir()} == set(SESSION_NAMES),
            "Direct session inventory differs.")
    previous_end = ""
    for ordinal, name in enumerate(SESSION_NAMES, 1):
        folder = sessions / name
        current = read(folder / "record.json")
        started_keys = ("session", "ordinal", "start_utc", "inputs_sha256")
        require((current["session"], current["ordinal"]) == (name, ordinal)
                and current["inputs_sha256"] == sha(run / "inputs.json")
                and current["host"] == inputs["host"] and previous_end <= current["start_utc"]
                and read(folder / "started.json") == {key: current[key] for key in started_keys},
                f"Direct session binding or start order differs: {name}")
        verify_inventory(folder, current["raw_files"], {"record.json"})
        steps = list(crossover_plan(("previous",), ordinal, False))
        require(steps == inputs["schedule"][name], f"Crossover schedule differs: {name}")
        verify_leg_order(steps, current["legs"], current["start_utc"], current["end_utc"])
        for step, leg in zip(steps, current["legs"], strict=True):
            order, label = leg["order"], leg["leg"]
            directory = folder / f"{order}-{label}"
            require(read(directory / "completed.json") == leg
                    and read(directory / "started.json") == {key: value for key, value in leg.items() if key != "end_utc"},
                    f"Crossover leg receipt differs: {directory}")
            slots = crossover_pair(pinned, step, False)
            require(read(directory / "bindings.json") == slots, f"Crossover leg actor binding differs: {directory}")
            actual = roles_for_slots(leg)
            fixtures, calls = fixture_rows(directory / "suite81", slots, actual, order, stage, fixture_names,
                                          root, locate, inputs["fixture_stage"]["receipt_sha256"], verify_timings,
                                          inputs["libdeflate"]["fixtures"])
            fixture_calls += calls
            silesia = dict(silesia_rows(directory / "silesia", slots, actual, order, silesia_files,
                                        oracle, silesia_reference))
            silesia_calls += read(directory / "silesia/complete.json")["timed_calls"]
            raw[name, order, label] = {"fixtures": fixtures, "silesia": silesia}
        previous_end = current["end_utc"]
        records[name] = {key: current[key] for key in ("start_utc", "end_utc")} | {
            "record_sha256": sha(folder / "record.json")
        }
    require((len(raw), fixture_calls, silesia_calls) == (12, 5895936, 2592), "Direct collection totals differ.")

    suites = {"fixtures": fixture_names, "silesia": silesia_files}
    regenerated, by_case = summarize(output, run, raw, records, suites, fixture_calls, silesia_calls, inputs)
    expected = read(record / "summary.json")
    original_csv = checked(record / "cases.csv", expected["cases_csv_sha256"])
    row_count = verify_cases(record / "cases.csv", output / "cases.csv")
    verify_summary(regenerated, expected | {"cases_csv_sha256": regenerated["cases_csv_sha256"]})
    render_report(output, record, pinned, regenerated, by_case, suites)
    result = {
        "fixture_cases": len(fixture_names),
        "silesia_cases": len(silesia_files),
        "sessions": len(records),
        "fixture_legs": len(raw),
        "silesia_legs": len(raw),
        "fixture_calls": fixture_calls,
        "silesia_calls": silesia_calls,
        "case_rows": row_count,
        "individual_leg_exceptions": len(regenerated["individual_leg_losses_and_ties_vs_libdeflate"]),
        "original_cases_csv_sha256": original_csv,
        "regenerated_cases_csv_sha256": regenerated["cases_csv_sha256"],
        "original_summary_sha256": sha(record / "summary.json"),
        "regenerated_summary_sha256": sha(output / "summary.json"),
    }
    write_new(output / "replay-verification.json", result)
    return result


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True, help="Absolute path to the frozen benchmark record")
    parser.add_argument("--output", type=Path, required=True, help="Absolute path to a new scratch directory")
    args = parser.parse_args()
    print(json.dumps(verify_direct_runtime(args.record, args.output), indent=2))


if __name__ == "__main__":
    main()
