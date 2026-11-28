from pathlib import Path
from runpy import run_path
from statistics import median
import subprocess
import sys

from campaign_stats import balanced_cycles
from compare_rebuilt import bind, campaign_host, compare81, utc_now, write_new
from rebuild import HERE, PARENT, checked, read, sha, write
from replay import prepare_fixture_stage
from verify import crossover_pair, crossover_plan, inventory, verify_fixture_stage, verify_leg_order

run, prior = (Path(arg).resolve(strict=True) for arg in sys.argv[1:])
repo = PARENT.parent.parent
source = read(prior / "campaign.json")
old_bindings = read(prior / "prepared-bindings.json")
assert sha(prior / "prepared-bindings.json") == source["prepared_bindings_sha256"]
for name, digest in source["tooling_files_sha256"].items():
    checked(repo / name, digest)

bindings = {}
for label, source_role in (("previous", "O"), ("candidate", "F")):
    actor = source["actors"][label]
    actual = bind(label, Path(actor["build"]), Path(actor["recipe"]))
    frozen = old_bindings[label]
    assert actual == {key: value for key, value in frozen.items() if key != "codec_source"}
    assert actual["source_commit"] == source["source_commits"][source_role]
    checked(Path(frozen["codec_source"]), frozen["source_sha256"])
    bindings[label] = actual
assert bindings["previous"]["configuration_sha256"] == bindings["candidate"]["configuration_sha256"]
assert bindings["previous"]["81"]["sha256"] != bindings["candidate"]["81"]["sha256"]
assert bindings["previous"]["silesia"]["sha256"] != bindings["candidate"]["silesia"]["sha256"]

host = campaign_host()
assert host == source["host"] and host["qualification_host"] == "M1"
package = PARENT / "mechdeflate-silesia-v1"
corpus = Path(source["corpus"])
assert checked(corpus / "corpus.json", sha(package / "corpus.json")) == source["corpus_manifest_sha256"]
files = read(corpus / "corpus.json")["files"]
assert len(files) == 12
for name, pin in files.items():
    checked(corpus / name, pin["sha256"])
    assert (corpus / name).stat().st_size == pin["bytes"]
libdeflate_path = package / "actors/libdeflate"
libdeflate_pin = read(package / "binding.json")["actors"]["libdeflate"]["sha256"]
checked(libdeflate_path, libdeflate_pin)
oracle = read(package / "complete.json")["independent_inflation"]
silesia_tools = run_path(str(package / "silesia_compare.py"))
stage_binding = prepare_fixture_stage(run / "fixture-stage", PARENT)
stage = verify_fixture_stage(stage_binding, run)
old_stage = read(Path(source["fixture_stage"]["receipt"]))
relocated = {"fixtures.json", "pinned-peers/pins.json", "prepared.json"}
assert stage["files"].keys() == old_stage["files"].keys()
assert all(stage["files"][name] == old_stage["files"][name] for name in stage["files"].keys() - relocated)
stage_pins = Path(stage["root"]) / "pinned-peers/pins.json"
fixture_peer = read(stage_pins)["actors"]["libdeflate"]
fixture_peer_digest = read(PARENT / "mechdeflate-81-v1/actors/bindings.json")["peers"]["libdeflate"]["binary_sha256"]
assert fixture_peer["binary_sha256"] == fixture_peer_digest
fixture_cycles = source["timing"]["fixtures"]["cycles_per_leg"]
assert fixture_cycles == 2 and source["timing"]["orders"] == ["forward", "reverse"]
planned = {f"session-{n}": list(crossover_plan(("previous",), n, False)) for n in range(1, 4)}

write_new(run / "inputs.json", {
    "purpose": "direct-runtime-comparison",
    "scope": "M1 level-12 O, F, and libdeflate",
    "benchmark_checkout_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
    "benchmark_tooling_commit": source["tooling_commit"],
    "timing_helper_hashes": {
        name: sha(folder / name) for folder, name in (
            (HERE, "compare_rebuilt.py"), (HERE, "replay.py"), (HERE, "verify.py"),
            (package, "silesia_compare.py")
        )
    },
    "driver_sha256": sha(Path(__file__)),
    "binding_source": str(prior / "prepared-bindings.json"),
    "binding_source_sha256": source["prepared_bindings_sha256"],
    "actor_bindings": bindings,
    "libdeflate": {
        "fixtures": {"binary_sha256": fixture_peer_digest, "level": 12, "version": "1.26"},
        "silesia": {"path": str(libdeflate_path), "sha256": libdeflate_pin, "level": 12},
    },
    "host": host,
    "fixture_stage": stage_binding,
    "fixture_cycles_per_leg": fixture_cycles,
    "silesia_cycles_per_leg": 1,
    "silesia_corpus": str(corpus),
    "silesia_corpus_sha256": source["corpus_manifest_sha256"],
    "schedule": planned,
})

def time_silesia(out, slots, direction):
    out.mkdir()
    actors = {**{name: side["silesia"] for name, side in slots.items()},
              "libdeflate": {"path": str(libdeflate_path), "sha256": libdeflate_pin}}
    order = tuple(actors)
    if direction == "reverse":
        order = order[::-1]
    cases = tuple(files) if direction == "forward" else tuple(reversed(files))
    for actor in actors.values():
        checked(Path(actor["path"]), actor["sha256"])
    write_new(out / "binding.json", {"slots": actors, "order": order})
    verified = {}
    for name in cases:
        row = silesia_tools["verify"](corpus / name, files[name], actors, order)
        assert all(result == oracle[name]["libdeflate"] for result in row.values()), (name, row)
        verified[name] = row
    write_new(out / "independent-inflation.json", verified)
    rows = []
    for name in cases:
        blocks, warmups = silesia_tools["balanced_samples"](name, corpus / name, actors, verified[name], order, 1)
        balanced_cycles(blocks, order, 1)
        assert tuple(warmups) == order and all(t > 0 for t in warmups.values())
        rows.append({"case": name, "blocks": blocks, "warmup_ns": warmups,
                     "median_ns": {role: median(block["ns"][role] for block in blocks) for role in order}})
        write(out / f"timings-{direction}.json", rows)
        print(f"Silesia {direction} {name} complete", flush=True)
    write_new(out / "complete.json", {"cases": len(rows), "balanced_blocks_per_case": 6,
                                     "timed_calls": len(rows) * 6 * len(order)})

session_root = run / "sessions"
session_root.mkdir()
for ordinal, (name, steps) in enumerate(planned.items(), 1):
    assert campaign_host() == host
    folder = session_root / name
    folder.mkdir()
    started = {"session": name, "ordinal": ordinal, "start_utc": utc_now(), "inputs_sha256": sha(run / "inputs.json")}
    write_new(folder / "started.json", started)
    print(f"{name} started {started['start_utc']}", flush=True)
    legs = []
    for step in steps:
        direction, leg = step["order"], step["leg"]
        out = folder / f"{direction}-{leg}"
        out.mkdir()
        slots = crossover_pair(bindings, step, False)
        timing = {**step, "start_utc": utc_now()}
        write_new(out / "started.json", timing)
        write_new(out / "bindings.json", slots)
        print(f"{name} {direction}-{leg} {step['slots']} started {timing['start_utc']}", flush=True)
        compare81(out / "suite81", PARENT, slots["control"], slots["candidate"],
                  retain_warmups=True, orders=(direction,), cycles=fixture_cycles, fixture_stage=stage_binding)
        time_silesia(out / "silesia", slots, direction)
        legs.append({**timing, "end_utc": utc_now()})
        write_new(out / "completed.json", legs[-1])
        print(f"{name} {direction}-{leg} complete {legs[-1]['end_utc']}", flush=True)
    end = utc_now()
    verify_leg_order(steps, legs, started["start_utc"], end)
    assert campaign_host() == host
    write_new(folder / "record.json", {**started, "end_utc": end, "legs": legs,
                                       "host": host, "raw_files": inventory(folder)})
    print(f"{name} sealed {end}", flush=True)
print("Three sessions sealed.", flush=True)
