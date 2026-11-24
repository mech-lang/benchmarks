"""Recompute paired Silesia results from the raw block observations."""
from argparse import ArgumentParser
from math import exp, fsum, log
from pathlib import Path
from statistics import mean, median
import json


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("timings", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    timing = json.loads(args.timings.read_text())
    directions = timing["record"]
    actors = list(timing["actors_sha256"])
    records = {}
    for direction, rows in directions.items():
        for row in rows:
            case = row["case"]
            blocks = row["blocks"]
            assert all(set(b["ns"]) == set(actors) for b in blocks)
            medians = {actor: median(block["ns"][actor] for block in blocks) for actor in actors}
            assert medians == row["median_ns"]
            recomputed = {
                role: {
                    peer: exp(mean(log(b["ns"][role] / b["ns"][peer]) for b in blocks))
                    for peer in ("baseline", "libdeflate")
                }
                for role in actors if role != "libdeflate"
            }
            assert recomputed == row["paired_ratio"]
            records.setdefault(case, {})[direction] = (recomputed, medians)
    matched = {case: values for case, values in records.items() if set(values) == set(directions)}
    answer = {"directions": list(directions), "fully_measured_cases": len(matched), "actors": {}}
    for actor in actors:
        if actor == "libdeflate":
            continue
        total = {role: fsum(mean(block[1][role] for block in case.values()) / 1e9
                            for case in matched.values()) for role in (actor, "baseline", "libdeflate")}
        cases = {
            case: {
                "relative_libdeflate": {direction: values[0][actor]["libdeflate"]
                                        for direction, values in row.items()},
                "relative_baseline": {direction: values[0][actor]["baseline"]
                                        for direction, values in row.items()},
                "median_s": {role: mean(values[1][role] for values in row.values()) / 1e9
                             for role in (actor, "baseline", "libdeflate")},
            }
            for case, row in matched.items()
        }
        report = {
            "total_s_from_case_medians": total,
            "corpus_reduction_pct_vs_libdeflate": (1 - total[actor] / total["libdeflate"]) * 100,
            "corpus_reduction_pct_vs_baseline": (1 - total[actor] / total["baseline"]) * 100,
            "wins_vs_libdeflate_by_order": {
                direction: sum(row["relative_libdeflate"][direction] < 1 for row in cases.values())
                for direction in directions
            },
            "wins_vs_libdeflate_in_all_orders": sum(
                max(row["relative_libdeflate"].values()) < 1 for row in cases.values()),
            "cases": cases,
        }
        answer["actors"][actor] = report
        print(actor, len(matched), f"{total[actor]:.3f}s / {total['libdeflate']:.3f}s",
              f"{report['corpus_reduction_pct_vs_libdeflate']:.3f}% less time than libdeflate,",
              f"{report['corpus_reduction_pct_vs_baseline']:.3f}% less time than baseline,",
              report["wins_vs_libdeflate_by_order"])
    if args.output:
        args.output.write_text(json.dumps(answer, indent=2) + "\n")


if __name__ == "__main__":
    main()
