"""Recompute balanced ratios and correctness from the saved timing blocks."""
from argparse import ArgumentParser
from collections import Counter
import gzip
from itertools import permutations
import json
import math
from pathlib import Path
from statistics import mean, median

from run_study import read, sha, write

ACTORS = ("mech-control", "mech-experiment", "roc", "libdeflate")
CLEANUP = {
    "mech-control": "private_payload_bytes=0 live_owner_records=0",
    "mech-experiment": "private_payload_bytes=0 live_owner_records=0",
    "roc": "reference_input_and_output_roots_released=1",
    "libdeflate": "libdeflate_compressor_and_output_released=1",
}


def verify(directory, results, name, oracle):
    manifest = read(results)
    assert manifest["complete"] and [row["order"] for row in manifest["runs"]] == ["forward", "reverse"]
    blocks_expected = manifest["blocks_per_case"]
    total_rows = 0
    previous_pins = None
    for order in manifest["runs"]:
        folder = directory / (name + "-" + order["order"])
        assert sha(folder / "summary.json") == order["summary_sha256"]
        assert read(folder / "summary.json") == order["results"]
        assert sha(directory / "controller.py") == manifest["controller_sha256"]
        completion = read(folder / "complete.json")
        assert completion["balanced_blocks_per_case"] == blocks_expected
        assert completion["cases"] == len(order["results"])
        assert all(completion[key] for key in (
            "fresh_compression_all_cases", "all_outputs_independently_inflated",
            "all_input_and_output_aliases_preserved",
        ))
        pins = read(folder / "pins.json")
        assert pins["level"] == 12 and set(pins["actors"]) == set(ACTORS)
        if previous_pins is not None:
            assert pins == previous_pins
        previous_pins = pins
        for actor, suffix in CLEANUP.items():
            assert (folder / f"{actor}.stderr").read_text().endswith(f"CLEANUP {suffix}\n")
        count = 0
        for row in order["results"]:
            case = row["case"]
            samples = {actor: [] for actor in ACTORS}
            with gzip.open(folder / case / "observations.json.gz", "rt") as stream:
                blocks = json.load(stream)
            assert Counter(tuple(block["order"]) for block in blocks) == Counter({
                sequence: blocks_expected // 24 for sequence in permutations(ACTORS)
            })
            block_size, leftover = divmod(row["timed_calls"], blocks_expected * len(ACTORS))
            assert block_size > 0 and not leftover
            for block in blocks:
                assert set(block["observations"]) == set(ACTORS)
                for actor, values in block["observations"].items():
                    assert len(values) == block_size
                    for value in values:
                        assert value["case"] == case and value["input_bytes"] == row["input_bytes"]
                        assert not value["profile"] and not value["warmup"]
                        assert all(value[key] for key in ("independent_inflation", "input_alias_unchanged",
                                                          "borrowed_output_alias_unchanged"))
                        if actor == "libdeflate":
                            assert value["version"] == "1.26" and value["level"] == 12
                            for key in ("output_sha256", "raw_bytes", "capacity", "matches_reference_bytes"):
                                assert value[key] == oracle[case][key]
                        else:
                            assert value["exact_reference"] and value["raw_bytes"] == row["reference_raw_bytes"]
                            assert value["capacity"] == row["reference_capacity"]
                        assert math.isfinite(value["seconds"]) and value["seconds"] >= 0
                    seconds = [value["seconds"] for value in values]
                    average = mean(seconds)
                    assert average > 0 and average == block["means"][actor]
                    samples[actor].extend(seconds)
            for actor, values in samples.items():
                assert median(values) == row["median_seconds"][actor]
                for peer in ("roc", "libdeflate"):
                    paired = math.exp(mean(math.log(block["means"][actor] / block["means"][peer])
                                           for block in blocks))
                    assert math.isclose(paired, row["paired_x_" + peer][actor], rel_tol=1e-12)
            assert sum(map(len, samples.values())) == row["timed_calls"]
            count += row["timed_calls"]
        assert count == completion["timed_calls"]
        total_rows += count
    return {"role": name, "runtime_observations_recomputed": total_rows,
            "orders": len(manifest["runs"]), "blocks_per_case": blocks_expected,
            "cases": len(manifest["runs"][0]["results"]), "result_sha256": sha(results)}


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("name")
    parser.add_argument("oracle", type=Path)
    args = parser.parse_args()
    oracle = {row["case"]: row for row in read(args.oracle)}
    result = verify(args.directory, args.directory / (args.name + "-results.json"), args.name, oracle)
    write(args.directory / (args.name + "-verified.json"), result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
