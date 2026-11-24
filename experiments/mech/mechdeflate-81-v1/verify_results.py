"""Verify the two published 81-case timing records and the preserved partial result."""
from collections import Counter
from itertools import permutations
from pathlib import Path
from statistics import mean, median
from tempfile import TemporaryDirectory
import gzip
import json
import math
import shutil
import sys
import tarfile

PACKET = Path(__file__).resolve().parent
PRIOR = PACKET.parent / "mechdeflate-phase-routes-v1"
EVIDENCE = PACKET / "evidence"
sys.path.insert(0, str(PRIOR))
from run_study import read, sha
from verify_timings import ACTORS, verify as verify_raw

CONTROL, CANDIDATE, INDEPENDENT, LIBRARY = ACTORS
ORDERS = ("forward", "reverse")


def check(condition, message):
    if not condition:
        raise ValueError(message)


def expected_files(role, cases):
    files = {
        "publication/publication.json", "publication/source-replay.json",
        "partial/early-stop.json", "partial/summary.json", "partial/pins.json",
        "partial/prefix-natural-1024/observations.json.gz",
    }
    for run in ("first", "confirmation"):
        files.add(f"{run}/controller.py")
        for suffix in ("results", "current-floor", "verified",
                       "mech-control-score", "mech-experiment-score"):
            files.add(f"{run}/{role}-{suffix}.json")
        for order in ORDERS:
            folder = f"{run}/{role}-{order}"
            for leaf in ("complete.json", "pins.json", "summary.json"):
                files.add(f"{folder}/{leaf}")
            files.update(f"{folder}/{actor}.stderr" for actor in ACTORS)
            files.update(f"{folder}/{case}/observations.json.gz" for case in cases)
    return files


def unpack(destination, manifest, paths):
    archive_path = EVIDENCE / manifest["archive"]
    check(archive_path.stat().st_size == manifest["archive_bytes"] and
          sha(archive_path) == manifest["archive_sha256"], "archive digest or length mismatch")
    remaining = paths.copy()
    check(len(remaining) == manifest["regular_files"], "unexpected file count")
    with tarfile.open(archive_path, "r|gz") as archive:
        for member in archive:
            check(member.isfile() and member.name in remaining, f"unexpected member {member.name!r}")
            remaining.remove(member.name)
            path = destination / member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, path.open("xb") as target:
                shutil.copyfileobj(source, target)
            check(path.stat().st_size == member.size, f"truncated member {member.name!r}")
    check(not remaining, f"missing {len(remaining)} archived files")


def bound_actors(folder, recipe, manifest):
    source = folder / "publication/source-replay.json"
    release = folder / "publication/publication.json"
    checksums = manifest["archived_receipts_sha256"]
    check(sha(source) == checksums["source_replay"] and sha(release) == checksums["publication"],
          "publication receipt digest mismatch")
    publication = read(release)
    replay = read(source)
    role = recipe["role"]
    check(publication["fresh_source_replay_sha256"] == sha(source) and
          publication["parent"] == replay["parent"] and
          publication["commit"] == recipe["source_commit"] and
          publication["verified_review"] == recipe["qualification_review"] and
          publication["object_sha256"] == recipe["artifacts"]["program.o"] and
          publication["worker_sha256"] == recipe["timing_worker_sha256"],
          "recipe does not match the published source, encoder and worker")
    check(recipe["recorded_results_sha256"] == {
        "first": publication["timing_result_sha256"],
        "confirmation": publication["corroborating_result_sha256"],
    }, "timings do not match publication")
    expected = {}
    for actor, name in ((CONTROL, "control"), (CANDIDATE, role)):
        artifacts = replay["roles"][name]["artifacts"]
        directory = PACKET / "actors" / name
        checks = {leaf: sha(directory / leaf) for leaf in ("mech-worker", "metadata.json")}
        check(all(artifacts[k] == v for k, v in checks.items()), f"{name} source-replay mismatch")
        expected[actor] = (checks["mech-worker"], checks["metadata.json"])
        if actor == CANDIDATE:
            check(checks["mech-worker"] == publication["worker_sha256"] and
                  all(artifacts[k] == v for k, v in recipe["artifacts"].items()),
                  "candidate worker or encoder diverges from recipe")
    prior = PACKET.parent / "mechdeflate-masked-fields-v1"
    old = read(prior / "raw-manifest.json")["files"]
    for peer in (INDEPENDENT, LIBRARY):
        metadata = None if peer == LIBRARY else sha(PRIOR / "actors" / f"{peer}-compatible-metadata.json")
        expected[peer] = (old[f"peers/{peer}-worker"]["sha256"], metadata)
    check(old["pinned-peers/libdeflate-output-oracle.json"]["sha256"] == manifest["output_oracle_sha256"],
          "original output oracle mismatch")
    return expected, old["fixtures.json"]["sha256"]


def verify_pins(path, digest, expected, inventory):
    check(sha(path) == digest, "saved worker pins differ")
    pins = read(path)
    observed = {actor: (row["binary_sha256"], row.get("metadata_sha256"))
                for actor, row in pins["actors"].items()}
    check(observed == expected and pins["input_inventory_sha256"] == inventory and pins["level"] == 12,
          "pinned workers, metadata, inventory or compression level differ")


def verify_partial(folder, manifest, oracle):
    info = manifest["partial"]
    case = info["case"]
    summary, path = folder / "summary.json", folder / case / "observations.json.gz"
    check(sha(summary) == info["summary_sha256"] and sha(path) == info["observation_sha256"],
          "partial evidence digest mismatch")
    rows, stop = read(summary), read(folder / "early-stop.json")
    check(stop["complete"] is False and
          len(set(x["case"] for x in rows)) == len(rows) == stop["finished_forward_rows"] == info["finished_forward_rows"],
          "partial record size or status mismatch")
    row = next(x for x in rows if x["case"] == case)
    oracle_row = oracle[case]
    with gzip.open(path, "rt") as stream:
        blocks = json.load(stream)
    check(Counter(tuple(b["order"]) for b in blocks) == Counter({p: 4 for p in permutations(ACTORS)}),
          "partial actor order imbalance")
    samples = {actor: [] for actor in ACTORS}
    size = 64
    for block in blocks:
        check(set(block["observations"]) == set(ACTORS), "partial actor inventory mismatch")
        for actor, values in block["observations"].items():
            check(len(values) == size, "partial block size mismatch")
            for v in values:
                check(v["case"] == case and v["input_bytes"] == row["input_bytes"] and
                      not v["profile"] and not v["warmup"] and all(v[k] for k in
                      ("independent_inflation", "input_alias_unchanged", "borrowed_output_alias_unchanged")),
                      "partial sample validation mismatch")
                if actor == LIBRARY:
                    check(v["level"] == 12 and v["version"] == "1.26" and all(v[k] == oracle_row[k] for k in
                          ("output_sha256", "raw_bytes", "capacity", "matches_reference_bytes")),
                          "partial output differs from oracle")
                else:
                    check(v["exact_reference"] and v["raw_bytes"] == row["reference_raw_bytes"] and
                          v["capacity"] == row["reference_capacity"], "partial output differs from original")
            seconds = [v["seconds"] for v in values]
            check(all(v >= 0 and math.isfinite(v) for v in seconds) and
                  mean(seconds) == block["means"][actor] > 0, "partial timing values differ")
            samples[actor].extend(seconds)
    for actor, seconds in samples.items():
        check(median(seconds) == row["median_seconds"][actor], "partial median differs")
        for peer in (INDEPENDENT, LIBRARY):
            ratio = math.exp(mean(math.log(b["means"][actor] / b["means"][peer]) for b in blocks))
            check(math.isclose(ratio, row["paired_x_" + peer][actor], rel_tol=1e-12),
                  "partial paired ratio differs from saved result")
    paired = row["paired_x_" + LIBRARY]
    check(row["timed_calls"] == sum(map(len, samples.values())) and
          stop["failed_rows"] == {case: paired} and paired[CANDIDATE] > 1, "partial stop result differs")
    return paired[CANDIDATE]


def main():
    check(__debug__, "run Python without -O so the original verifier retains its checks")
    recipe, manifest = read(PACKET / "recipe.json"), read(EVIDENCE / "manifest.json")
    oracle_path = PRIOR / "libdeflate-output-oracle.json"
    check(sha(oracle_path) == manifest["output_oracle_sha256"] and
          sha(PRIOR / "verify_timings.py") == manifest["original_verifier_sha256"],
          "original oracle or raw verifier differs")
    oracle = {row["case"]: row for row in read(oracle_path)}
    check(len(oracle) == 81, "incorrect original inventory size")
    role = recipe["role"]
    with TemporaryDirectory(prefix="mechdeflate-results-") as scratch:
        folder = Path(scratch)
        unpack(folder, manifest, expected_files(role, oracle))
        actors, inventory = bound_actors(folder, recipe, manifest)
        for name in ("first", "confirmation"):
            panel = folder / name
            path = panel / f"{role}-results.json"
            check(sha(path) == recipe["recorded_results_sha256"][name] and
                  sha(panel / "controller.py") == manifest["source_controller_sha256"],
                  f"{name} result or controller differs")
            results = read(path)
            check(results["blocks_per_case"] == recipe["blocks_per_case_per_order"] == 96,
                  f"{name} block count differs")
            for order in results["runs"]:
                verify_pins(panel / f"{role}-{order['order']}" / "pins.json",
                            manifest["archived_pins_sha256"][name], actors, inventory)
                rows = order["results"]
                check(len(rows) == len(oracle) and {r["case"] for r in rows} == set(oracle),
                      f"{name} inventory differs")
                for row in rows:
                    for peer in (LIBRARY, INDEPENDENT):
                        check(row["paired_x_" + peer][CANDIDATE] < 1,
                              f"{name} {order['order']} lost {row['case']}")
            verified = verify_raw(panel, path, role, oracle)
            check(verified == read(panel / f"{role}-verified.json"), f"{name} verification receipt differs")
            print(f"{name} verified {verified['runtime_observations_recomputed']:,} observations and "
                  "81/81 strict wins against both comparisons in each order.", flush=True)
        partial = folder / "partial"
        verify_pins(partial / "pins.json", manifest["archived_pins_sha256"]["partial"], actors, inventory)
        ratio = verify_partial(partial, manifest, oracle)
        print(f"Separate partial run retained {manifest['partial']['finished_forward_rows']} forward rows. "
              f"The preserved 96-block row has candidate/library ratio {ratio:.9f}.")


if __name__ == "__main__":
    main()
