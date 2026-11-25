"""Pure paired-cycle statistics for native route qualification."""

from collections import Counter
from itertools import permutations
from math import ceil, isfinite, log
from random import Random
from statistics import fmean, stdev


SEED = 0x4D454348
REPLICATES = 20_000


def balanced_cycles(blocks, actors, count):
    """Return consecutive complete permutation cycles in recorded order."""
    inventory = Counter(permutations(actors))
    width = len(inventory)
    if len(blocks) != count * width:
        raise ValueError("wrong balanced-block inventory")
    cycles = tuple(tuple(blocks[i:i + width]) for i in range(0, len(blocks), width))
    if any(Counter(tuple(row["order"]) for row in cycle) != inventory for cycle in cycles):
        raise ValueError("each cycle must contain every actor permutation exactly once")
    return cycles


def paired_log(candidate, control):
    if min(candidate, control) <= 0 or not all(map(isfinite, (candidate, control))):
        raise ValueError("paired duration or memory observation must be finite and positive")
    return log(candidate / control)


def nearest_rank(sorted_samples, probability):
    return sorted_samples[ceil(probability * len(sorted_samples)) - 1]


def simultaneous(groups, *, replicates=REPLICATES, seed=SEED):
    """Groups map names to sessions of cycles of coordinate-to-log-ratio rows.

    All groups share session draws. Cycles are drawn within the selected
    session and shared across every coordinate in their group.
    """
    if replicates < 2 or not groups:
        raise ValueError("simultaneous intervals require samples and at least two replicates")
    rng = Random(seed)
    owners, coordinates, observed = [], [], []
    all_names = set()
    session_count = len(next(iter(groups.values())))
    if not session_count:
        raise ValueError("no sessions")
    for group, sessions in sorted(groups.items()):
        if len(sessions) != session_count or not sessions[0]:
            raise ValueError("incomplete session inventory")
        cycle_count = len(sessions[0])
        keys = tuple(sorted(sessions[0][0]))
        if not keys or all_names.intersection(keys):
            raise ValueError("empty or duplicate interval coordinates")
        all_names.update(keys)
        if any(len(session) != cycle_count for session in sessions):
            raise ValueError("incomplete cycle inventory")
        if any(row.keys() != set(keys) for session in sessions for row in session):
            raise ValueError("incomplete coordinate inventory")
        rows = tuple(tuple(tuple(row[key] for key in keys) for row in session)
                     for session in sessions)
        columns = tuple(zip(*(row for session in rows for row in session)))
        if any(not isfinite(value) for column in columns for value in column):
            raise ValueError("nonfinite paired log ratio")
        coordinates.extend(keys)
        observed.extend(column[0] if min(column) == max(column) else fmean(column)
                        for column in columns)
        owners.append((group, rows, cycle_count, tuple(min(col) == max(col) for col in columns)))

    samples = [[] for _ in coordinates]
    for _ in range(replicates):
        selected_sessions = rng.choices(range(session_count), k=session_count)
        offset = 0
        for _, rows, cycle_count, constant in owners:
            drawn = [rows[session][cycle]
                     for session in selected_sessions
                     for cycle in rng.choices(range(cycle_count), k=cycle_count)]
            for index, values in enumerate(zip(*drawn), start=offset):
                estimate = observed[index] if constant[index - offset] else fmean(values)
                samples[index].append(estimate)
            offset += len(constant)

    deviations = tuple(stdev(sample) for sample in samples)
    maxima = [0.0] * replicates
    for center, sd, estimates in zip(observed, deviations, samples, strict=True):
        if sd:
            maxima = [max(previous, abs(value - center) / sd)
                      for previous, value in zip(maxima, estimates, strict=True)]
    maxima.sort()
    q95, q99 = (nearest_rank(maxima, p) for p in (0.95, 0.99))
    return {
        "algorithm": "paired log ratios, equal sessions and cycles, simultaneous bootstrap max statistic",
        "seed": seed,
        "replicates": replicates,
        "session_count": session_count,
        "cycles_per_session": {group: count for group, _, count, _ in owners},
        "q95": q95,
        "q99": q99,
        "coordinates": {
            name: {"log_ratio": center, "sd": sd,
                   "interval95": [center - q95 * sd, center + q95 * sd],
                   "interval99": [center - q99 * sd, center + q99 * sd]}
            for name, center, sd in zip(coordinates, observed, deviations, strict=True)
        },
    }


def calibration(intervals):
    coordinates = intervals["coordinates"]
    excludes_zero = [name for name, values in coordinates.items()
                     if not values["interval95"][0] <= 0 <= values["interval95"][1]]
    return {
        "decision": "unresolved" if excludes_zero else "pass",
        "excludes_zero": excludes_zero,
        "epsilon": {name: abs(values["log_ratio"]) + intervals["q99"] * values["sd"]
                    for name, values in coordinates.items()},
        "intervals": intervals,
    }


def nonregression(intervals, seal):
    coordinates = intervals["coordinates"]
    epsilon = seal["epsilon"]
    if coordinates.keys() != epsilon.keys():
        raise ValueError("coordinate mismatch between calibration and comparison")
    rows = {name: {**values, "epsilon": epsilon[name]}
            for name, values in coordinates.items()}
    if seal["decision"] != "pass":
        decision = "unresolved"
    elif any(row["interval95"][0] > row["epsilon"] for row in rows.values()):
        decision = "fail"
    elif all(row["interval95"][1] <= row["epsilon"] for row in rows.values()):
        decision = "pass"
    else:
        decision = "unresolved"
    return {"decision": decision, "intervals": {**intervals, "coordinates": rows}}
