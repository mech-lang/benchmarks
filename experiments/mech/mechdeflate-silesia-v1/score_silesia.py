"""Verify raw balanced Silesia observations and report head-to-head results."""
from collections import Counter
from itertools import permutations
from math import exp, isclose, log, sqrt
from pathlib import Path
from statistics import mean, median
import json
import sys

from silesia_compare import ORDER, digest, read, save

folder, inventory = map(Path, sys.argv[1:])
complete = read(folder / "complete.json")
assert digest(inventory) == complete["corpus_sha256"]
assert digest(folder / "binding.json") == complete["binding_sha256"]
assert complete["cases"] == 12
names = list(read(inventory)["files"])
cycles, remainder = divmod(complete["balanced_blocks_per_order_and_case"], 6)
assert cycles > 0 and not remainder
directions = [read(folder / ("timings-" + direction + ".json")) for direction in ("forward", "reverse")]
assert [row["case"] for row in directions[0]] == names
assert [row["case"] for row in directions[1]] == names[::-1]
timings = {row["case"]: [row] for row in directions[0]}
for row in directions[1]:
    timings[row["case"]].append(row)
for rows in directions:
    for row in rows:
        blocks = row["blocks"]
        assert Counter(tuple(block["order"]) for block in blocks) == Counter({p: cycles for p in permutations(ORDER)})
        assert all(set(block["ns"]) == set(ORDER) and min(block["ns"].values()) > 0 for block in blocks)
        for actor in ORDER:
            assert row["median_ns"][actor] == median(block["ns"][actor] for block in blocks)
        for peer, stored in row["mech_paired_x_peer"].items():
            check = exp(mean(log(block["ns"]["mech-candidate"] / block["ns"][peer]) for block in blocks))
            assert isclose(check, stored, rel_tol=1e-12)
        roc_c = exp(mean(log(block["ns"]["roc"] / block["ns"]["libdeflate"]) for block in blocks))
        assert isclose(roc_c, row["roc_paired_x_libdeflate"], rel_tol=1e-12)

paired_rows = {}
for name, (forward, reverse) in timings.items():
    paired = {peer: sqrt(forward["mech_paired_x_peer"][peer] * reverse["mech_paired_x_peer"][peer])
              for peer in ("libdeflate", "roc")}
    paired_rows[name] = {"mech_x_peer": paired,
                         "roc_x_libdeflate": sqrt(forward["roc_paired_x_libdeflate"] * reverse["roc_paired_x_libdeflate"]),
                         "bytes": complete["independent_inflation"][name]}
    print(name, {k: round(v, 6) for k, v in paired.items()},
          "Roc / C", round(paired_rows[name]["roc_x_libdeflate"], 6))
stats = {
    "mech_median_x_peer": {peer: median(row["mech_x_peer"][peer] for row in paired_rows.values())
                           for peer in ("libdeflate", "roc")},
    "roc_median_x_libdeflate": median(row["roc_x_libdeflate"] for row in paired_rows.values()),
    "mech_paired_wins": {peer: sum(row["mech_x_peer"][peer] < 1 for row in paired_rows.values())
                         for peer in ("libdeflate", "roc")},
    "mech_wins_in_both_orders": {peer: sum(all(row["mech_paired_x_peer"][peer] < 1 for row in rows)
                                            for rows in timings.values()) for peer in ("libdeflate", "roc")},
    "roc_paired_wins_against_libdeflate": sum(row["roc_x_libdeflate"] < 1 for row in paired_rows.values()),
    "identical_all_three_streams": sum(len({actor["sha256"] for actor in row["bytes"].values()}) == 1
                                      for row in paired_rows.values()),
    "results": paired_rows,
}
save(folder / "scores.json", stats)
print(json.dumps({key: val for key, val in stats.items() if key != "results"}, indent=2))
