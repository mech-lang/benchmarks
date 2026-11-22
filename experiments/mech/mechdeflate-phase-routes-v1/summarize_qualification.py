"""Report the fixed-cohort results, qualification gates and matched build times."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess

from run_study import read, write


def sizes(role, executable, stack):
    image = role / "frontend" / "program.o"
    output = subprocess.check_output(["/usr/bin/otool", "-l", str(image)], text=True)
    sections = [block.splitlines() for block in output.split("\nSection\n")[1:]]
    const_size, = [int(line.split()[1], 16) for block in sections
                   if "sectname __const" in block[0]
                   for line in block if line.strip().startswith("size ")]
    metadata = read(image.with_name("metadata.json"))
    lookup_bytes, = [phase["composed_variant"]["admission"]["immutable_code_bytes"]
                     for phase in metadata["numeric_phases"] if "composed_variant" in phase]
    return {"encoder_text_bytes": read(role / "receipt.json")["text_bytes"],
            "lookup_bytes": lookup_bytes, "whole_const_bytes": const_size,
            "stripped_executable_bytes": executable["bytes"], "stack_bytes": stack,
            "stripped_sha256": executable["sha256"]}


def main():
    parser = ArgumentParser(__doc__)
    for key in ("role", "timings", "native", "builds", "output", "baseline"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    name = args.role.name
    reference = read(args.baseline)
    actors = ("mech-control", "mech-experiment")
    scores = {actor: read(args.timings / f"{name}-{actor}-score.json") for actor in actors}
    runtime = read(args.timings / f"{name}-results.json")
    verification = read(args.timings / f"{name}-verified.json")
    assert verification["blocks_per_case"] == 96 and verification["orders"] == 2
    assert verification["cases"] == 81
    indexed = {run["order"]: {row["case"]: row for row in run["results"]} for run in runtime["runs"]}
    native = read(args.native / "qualification.json")
    builds = read(args.builds / "comparison.json")
    deployment = read(args.builds / "deployment-smokes.json")
    assert len(deployment) == 324 and all(row["independent_inflation"] for row in deployment)
    cases = []
    for c in scores["mech-experiment"]["cases"]:
        case = c["case"]
        control = next(row for row in scores["mech-control"]["cases"] if row["case"] == case)
        cases.append({"case": case, "control_paired_x_C": control["paired_x_C"],
                      "candidate_paired_x_C": c["paired_x_C"],
                      "control_contribution_pp": control["contribution_pp"],
                      "candidate_contribution_pp": c["contribution_pp"],
                      "improvement_pp": control["contribution_pp"] - c["contribution_pp"],
                      "orders": {order: {key: rows[case][key] for key in
                                         ("median_seconds", "paired_x_libdeflate", "paired_x_roc")}
                                 for order, rows in indexed.items()}})
    sizes_by_actor = {
        "mech-control": sizes(args.role.parent / "control", builds["warmup"]["mech-control"]["stripped_executable"], 4832),
        "mech-experiment": sizes(args.role, builds["warmup"]["mech-candidate"]["stripped_executable"], native["stack_bytes"]),
    }
    new_wins = sorted({case for case in reference["inventory"]
                       if all(rows[case]["paired_x_libdeflate"]["mech-experiment"] < 1
                              for rows in indexed.values())} - set(reference["protected_wins"]["libdeflate"]))
    assert len(new_wins) == scores["mech-experiment"]["cohort_wins_in_both_orders"]
    write(args.output / "case-margins.json", cases)
    write(args.output / "qualification.json", {
        "role": name, "runtime_verification": verification, "scores": scores, "new_libdeflate_wins": new_wins,
        "sizes": sizes_by_actor, "stack_cap_bytes": 5280, "native": native,
        "source_through_final_link_seconds": {actor: row["source_through_link"] for actor, row in builds["medians_seconds"].items()},
        "balanced_timed_builds": sum(map(len, builds["observations"])), "correct_deployment_outputs": len(deployment),
        "artifact_sha256": read(args.role / "receipt.json")["artifacts"],
    })


if __name__ == "__main__":
    main()
