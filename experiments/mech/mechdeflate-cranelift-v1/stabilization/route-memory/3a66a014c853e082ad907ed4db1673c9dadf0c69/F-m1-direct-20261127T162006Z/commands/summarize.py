from math import expm1, isclose
from pathlib import Path
from statistics import fmean, median
import csv
import sys

from campaign_stats import balanced_cycles, paired_log
from compare_rebuilt import bind, write_new
from rebuild import PARENT, checked, read, sha
from verify import crossover_pair, crossover_plan, fixture_inputs, verify_fixture_stage, verify_inventory, verify_leg_order

run = Path(sys.argv[1]).resolve(strict=True)
inputs = read(run / "inputs.json")
stage = verify_fixture_stage(inputs["fixture_stage"], run)
corpus = Path(inputs["silesia_corpus"])
checked(corpus / "corpus.json", inputs["silesia_corpus_sha256"])
silesia_files = tuple(read(corpus / "corpus.json")["files"])
fixture_names = tuple(row["name"] for row in read(Path(stage["root"]) / "fixtures.json"))
silesia_reference = inputs["libdeflate"]["silesia"]
checked(Path(silesia_reference["path"]), silesia_reference["sha256"])
oracle = read(PARENT / "mechdeflate-silesia-v1/complete.json")["independent_inflation"]
pinned = inputs["actor_bindings"]
for role, actor in pinned.items():
    assert actor == bind(role, Path(actor["build_directory"]), Path(actor["recipe"]))

roles = ("O", "F", "libdeflate")
comparisons = {"O/libdeflate": ("O", "libdeflate"), "F/libdeflate": ("F", "libdeflate"), "F/O": ("F", "O")}
orders = ("forward", "reverse")
suites = {"fixtures": fixture_names, "silesia": silesia_files}
fixture_calls = silesia_calls = 0

def roles_for_slots(leg):
    known = {"previous": "O", "candidate": "F"}
    actual = {known[pinned_role]: slot for slot, pinned_role in leg["slots"].items()}
    return actual | {"libdeflate": "libdeflate"}

def fixture_rows(directory, slots, actual, order):
    global fixture_calls
    groups, references, durations = fixture_inputs(directory, slots, orders=(order,),
                                                  cycles=inputs["fixture_cycles_per_leg"], fixture_stage=stage)
    key = f"fixtures/{order}"
    pins = read(directory / f"cranelift-{order}" / "pins.json")["actors"]
    assert pins["libdeflate"]["binary_sha256"] == inputs["libdeflate"]["fixtures"]["binary_sha256"]
    completed = read(directory / f"cranelift-{order}" / "complete.json")
    assert completed["cases"] == len(fixture_names) and completed["timed_calls"] == 491328
    fixture_calls += completed["timed_calls"]

    actor = {"control": "mech-control", "candidate": "mech-experiment", "libdeflate": "libdeflate"}
    for case in fixture_names:
        before = references[key][actual["O"]]["libdeflate"][case]
        after = references[key][actual["F"]]["libdeflate"][case]
        change = fmean(cycle[f"{key}/{case}"] for cycle in groups[key])
        if actual["F"] == "control":
            change = -change
        assert isclose(change, after - before, rel_tol=1e-10, abs_tol=1e-13)
        yield case, {
            "log_ratios": {"O/libdeflate": before, "F/libdeflate": after, "F/O": change},
            "absolute_ns": {role: durations[key][case][actor[actual[role]]] for role in roles},
        }

def silesia_rows(directory, slots, actual, direction):
    global silesia_calls
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
    cycles = inputs["silesia_cycles_per_leg"]
    assert cycles == 1
    assert completed == {"cases": len(silesia_files), "balanced_blocks_per_case": 6,
                         "timed_calls": len(silesia_files) * 6 * len(roles)}
    silesia_calls += completed["timed_calls"]
    for row in rows:
        case = row["case"]
        assert verified[case] == dict.fromkeys(order, oracle[case]["libdeflate"])
        assert tuple(row["warmup_ns"]) == order and all(t > 0 for t in row["warmup_ns"].values())
        blocks, = balanced_cycles(row["blocks"], order, cycles)
        assert all(tuple(block["ns"]) == tuple(block["order"])
                   and all(t > 0 for t in block["ns"].values()) for block in blocks)
        assert row["median_ns"] == {role: median(block["ns"][role] for block in blocks) for role in order}
        yield case, {
            "log_ratios": {key: fmean(paired_log(block["ns"][actual[left]], block["ns"][actual[right]])
                                     for block in blocks) for key, (left, right) in comparisons.items()},
            "absolute_ns": {role: row["median_ns"][actual[role]] for role in roles},
        }

assert (run / "commands/exit.txt").read_text().strip() == "0"
raw = {}
records = {}
expected_sessions = tuple(f"session-{n}" for n in range(1, 4))
assert set(inputs["schedule"]) == {p.name for p in (run / "sessions").iterdir()} == set(expected_sessions)
previous_end = ""
for ordinal, name in enumerate(expected_sessions, 1):
    folder = run / "sessions" / name
    record = read(folder / "record.json")
    assert (record["session"], record["ordinal"]) == (name, ordinal)
    assert record["inputs_sha256"] == sha(run / "inputs.json") and record["host"] == inputs["host"]
    assert previous_end <= record["start_utc"]
    started = read(folder / "started.json")
    assert started == {key: record[key] for key in ("session", "ordinal", "start_utc", "inputs_sha256")}
    verify_inventory(folder, record["raw_files"], {"record.json"})
    steps = list(crossover_plan(("previous",), ordinal, False))
    assert steps == inputs["schedule"][name]
    verify_leg_order(steps, record["legs"], record["start_utc"], record["end_utc"])
    for step, leg in zip(steps, record["legs"], strict=True):
        order, label = leg["order"], leg["leg"]
        directory = folder / f"{order}-{label}"
        assert read(directory / "completed.json") == leg
        assert read(directory / "started.json") == {key: value for key, value in leg.items() if key != "end_utc"}
        slots = crossover_pair(pinned, step, False)
        assert read(directory / "bindings.json") == slots
        actual = roles_for_slots(leg)
        raw[name, order, label] = {
            "fixtures": dict(fixture_rows(directory / "suite81", slots, actual, order)),
            "silesia": dict(silesia_rows(directory / "silesia", slots, actual, order)),
        }
    previous_end = record["end_utc"]
    records[name] = {key: record[key] for key in ("start_utc", "end_utc")} | {"record_sha256": sha(folder / "record.json")}
    print(f"Verified {name}.", flush=True)
assert len(raw) == 12 and fixture_calls == 5895936 and silesia_calls == 2592

def count_and_margin(data, comparison):
    observations = [row["log_ratios"][comparison] for row in data.values()]
    return {
        "wins": sum(x < 0 for x in observations),
        "losses": sum(x > 0 for x in observations),
        "ties": sum(x == 0 for x in observations),
        "geomean_change_percent": 100 * expm1(fmean(observations)),
        "median_case_change_percent": median(100 * expm1(x) for x in observations),
    }

def aggregate(sessions, directions, suite):
    sets = [raw[session, direction, leg][suite]
            for session in sessions for direction in directions for leg in ("A", "B")]
    return {case: {
        "log_ratios": {key: fmean(rows[case]["log_ratios"][key] for rows in sets) for key in comparisons},
        "absolute_ns": {role: median(rows[case]["absolute_ns"][role] for rows in sets) for role in roles},
    } for case in suites[suite]}

labels = (*expected_sessions, "pooled")
directions = (*orders, "both")
by_case = {}
summary = {}
for suite in suites:
    summary[suite] = {}
    for label in labels:
        summary[suite][label] = {}
        for direction in directions:
            case_rows = aggregate(expected_sessions if label == "pooled" else (label,),
                                  orders if direction == "both" else (direction,), suite)
            by_case[suite, label, direction] = case_rows
            summary[suite][label][direction] = {
                "cases": len(case_rows),
                "comparisons": {key: count_and_margin(case_rows, key) for key in comparisons},
                "sum_of_case_medians_ns": {role: sum(row["absolute_ns"][role] for row in case_rows.values())
                                          for role in roles},
            }

flagged = {}
for suite in suites:
    flagged[suite] = {}
    for comparison in comparisons:
        flagged[suite][comparison] = []
        pooled = by_case[suite, "pooled", "both"]
        for case in suites[suite]:
            delta = 100 * expm1(pooled[case]["log_ratios"][comparison])
            values = [100 * expm1(by_case[suite, session, order][case]["log_ratios"][comparison])
                      for session in expected_sessions for order in orders]
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

with (run / "cases.csv").open("x", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["suite", "session", "order", "case", "O_ns", "F_ns", "libdeflate_ns",
                     "O_vs_libdeflate_pct", "F_vs_libdeflate_pct", "F_vs_O_pct"])
    for (suite, session, order), rows in by_case.items():
        for case, row in rows.items():
            writer.writerow([suite, session, order, case, *(row["absolute_ns"][role] for role in roles),
                             *(100 * expm1(row["log_ratios"][key]) for key in comparisons)])

write_new(run / "summary.json", {
    "purpose": inputs["purpose"], "inputs_sha256": sha(run / "inputs.json"),
    "cases_csv_sha256": sha(run / "cases.csv"),
    "sessions": records, "fixture_legs": len(raw), "fixture_timed_calls": fixture_calls,
    "silesia_legs": len(raw), "silesia_timed_calls": silesia_calls,
    "results": summary, "close_inconsistent_and_losing_cases": flagged,
    "individual_leg_losses_and_ties_vs_libdeflate": leg_losses,
})

def counts(entry):
    values = (entry["wins"], entry["losses"], entry["ties"])
    return f"{values[0]}/{values[1]}/{values[2]} ({entry['geomean_change_percent']:+.3f}%)"

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
    "[Input identities and schedule](inputs.json) · [Raw evidence receipt](archive-receipt.json)",
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
            absolute = " / ".join(f"{entry['sum_of_case_medians_ns'][role] / scale:.6f}" for role in roles)
            cells = " | ".join(counts(entry["comparisons"][key]) for key in comparisons)
            lines.append(f"| {label} | {order} | {cells} | {absolute} |")
    if suite == "silesia":
        lines.extend([
            "",
            "| File | O (s) | F (s) | libdeflate (s) | O / libdeflate | F / libdeflate | F / O |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for case, row in by_case[suite, "pooled", "both"].items():
            cells = [*(f"{row['absolute_ns'][role] / 1e9:.6f}" for role in roles),
                     *(f"{100 * expm1(row['log_ratios'][key]):+.3f}%" for key in comparisons)]
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
for suite, comparison in ((suite, key) for suite in suites for key in comparisons):
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
with (run / "report.md").open("x") as stream:
    stream.write("\n".join(lines) + "\n")
