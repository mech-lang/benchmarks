"""Run the retained encoder correctness and complete-build gates for one role."""
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
from runpy import run_path
from statistics import median
import json
import os
import re
import shutil
import subprocess
import sys
import zlib

from run_study import BLOCK_LAYOUT, CLEAN_ENV, MATCHER, REGISTER_WEIGHTS, exec_script, read, sha, write


def run(command, log, env=CLEAN_ENV):
    command = list(map(str, command))
    with log.open("w") as stream:
        subprocess.run(command, env=env, stdout=stream, stderr=stream, check=True)
    return {"command": command, "log_sha256": sha(log)}


def gate_artifacts(args):
    role = args.role
    receipt = read(role / "receipt.json")
    for mode, extra in (
        ("checked", {"MECH_COMPACT_PAIR_REGISTER_SPILLS": "checked"}),
        ("inspect", {"MECH_INSPECT_FP_SPILL_CACHE": str(args.output / "spill-plans")}),
    ):
        frontend = args.output / mode
        command = receipt["command"].copy()
        command[2] = frontend
        run(command, args.output / (mode + ".log"), CLEAN_ENV | receipt["flags"] | extra)
        assert {name: sha(frontend / name) for name in receipt["artifacts"]} == receipt["artifacts"]


def linked_gates(args):
    role = args.role
    archived = args.archived_packet
    q = args.lab.parents[1]
    template = args.lab / "fp-spill-keep-pairs-study/census/keep-pairs2-gates/recovery-packet"
    fixture_file = q / "fixtures.json"
    fixtures = read(fixture_file)
    check = run_path(str(archived / "rebuild_checks.py"))
    actor = role / "bound"
    runtime = read(actor / "runtime.json")
    control = role.parent / "control/bound"
    assert read(actor / "metadata.json")["origins"] == read(control / "metadata.json")["origins"]
    rows = {}
    for name, folder in (("control", control), ("candidate", actor)):
        rows[name] = check["check_successes"](folder / "mech-worker", folder / "metadata.json",
                                             fixture_file, fixtures, args.output / (name + "-smokes.log"),
                                             CLEAN_ENV)
        for row in rows[name]:
            del row["seconds"]
        write(args.output / (name + "-smokes.json"), rows[name])
    assert rows["control"] == rows["candidate"]

    fault = args.output / "recovery"
    fault.mkdir()
    fault_packet = fault / "packet"
    fault_packet.mkdir()
    for name in ("worker.rs", "pinned_allocator.rs", "qualification-policy-v3.json"):
        shutil.copyfile(template / name, fault_packet / name)
    command = runtime["link"].copy()
    worker = next(Path(item) for item in command if item.endswith("/mech-worker.rs"))
    assert sha(worker) == sha(fault_packet / "worker.rs")
    command[command.index(str(worker))] = fault_packet / "worker.rs"
    recovery = check["check_faults"](fault_packet, fault, command, actor / "metadata.json",
                                      fixture_file, fixtures, CLEAN_ENV, run)
    assert recovery["cases"] == 6 and recovery["exact_recoveries"] == 12

    support = args.output / "stack"
    support.mkdir()
    stack_probe = q / "consolidation-995/preserved-registers/linked-current-preserved/linked-proofs/stack-support/stack.o"
    assert sha(stack_probe) == "47629aa045ac454421a6f8412b9a50fd52eebc76cb4a19191aee9f4c6d7aec22"
    source = worker.read_text()
    for old, new in (
        ("mech_compact_closed_v2(", "mech_probe_native_stack("),
        ("        output: *mut u64,", "        output: *mut u64,\n        sample: u64,\n        depth: *mut usize,"),
        ("        let status = unsafe {", "        let mut depth = 0;\n        let status = unsafe {"),
        ("                output.as_mut_ptr(),", "                output.as_mut_ptr(),\n                sample as u64,\n                &mut depth,"),
        ("        let returned = if status.status == 0 {",
         '        eprintln!("STACK {} {sample} {depth}", case.name);\n        let returned = if status.status == 0 {'),
    ):
        assert source.count(old) >= 1
        source = source.replace(old, new)
    source_path = support / "stack-worker.rs"
    source_path.write_text(source)
    shutil.copyfile(worker.with_name("pinned_allocator.rs"), support / "pinned_allocator.rs")
    command = runtime["link"].copy()
    command[command.index(str(worker))] = str(source_path)
    executable = support / "stack-worker"
    command[command.index("-o") + 1] = executable
    stack_link = run([*command, "-C", f"link-arg={stack_probe}"], support / "link.log")
    check["check_successes"](executable, actor / "metadata.json", fixture_file, fixtures,
                             support / "observations.log", CLEAN_ENV)
    depths = {}
    for name, sample, value in re.findall(r"^STACK (\S+) ([01]) (\d+)$",
                                          (support / "observations.log").read_text(), re.M):
        depths.setdefault(name, {})[sample] = int(value)
    assert len(depths) == 81 and all(len(visits) == 2 for visits in depths.values())
    peak = max(value for case in depths.values() for value in case.values())
    assert peak <= 5_280
    write(args.output / "qualification.json", {
        "worker_sha256": sha(actor / "mech-worker"), "object_sha256": sha(actor / "program.o"),
        "metadata_sha256": sha(actor / "metadata.json"), "bytecode_sha256": sha(actor / "program.mecb"),
        "exact_success_observations": len(rows["candidate"]), "recovery": recovery,
        "stack_probe_sha256": sha(stack_probe), "stack_link": stack_link, "stack_bytes": peak,
        "stack_observations": depths, "checked_and_inspected_emissions": "exact",
    })
    print("GATES", role.name, len(rows["candidate"]), recovery["cases"], recovery["exact_recoveries"], peak, flush=True)


def complete_builds(args):
    study = args.lab / "matcher-bit-fields-tied-study"
    previous = read(study / "matched-builds-v1/plan.json")
    timer = study / "complete-build-timer.py"
    assert sha(timer) == previous["timer_sha256"]
    measure = run_path(str(timer), run_name="complete_timer")["compile_and_link"]
    roles = {"mech-control": args.role.parent / "control", "mech-candidate": args.role,
             "roc": None, "libdeflate": None}
    actors = {}
    for actor, folder in roles.items():
        if folder is None:
            actors[actor] = previous["actors"][actor]
            continue
        receipt = read(folder / "receipt.json")
        prior = previous["actors"]["mech-control-reference"]
        obj = str(folder / "frontend/program.o")
        link = [obj if token == prior["reference_object"] else token for token in prior["link"]]
        assert link.count(obj) == 1
        actors[actor] = {
            "compile": receipt["command"], "link": link, "flags": receipt["flags"], "reference_object": obj,
            "compiler_sha256": receipt["compiler_sha256"], "host_inputs_sha256": prior["host_inputs_sha256"],
            "codec_source_inputs_sha256": {receipt["command"][1]: receipt["source_sha256"]},
            "artifact_sha256": {key: receipt["artifacts"][file] for key, file in
                                (("encoder", "program.o"), ("bytecode", "program.mecb"), ("metadata", "metadata.json"))},
        }
    for job in actors.values():
        assert sha(job["compile"][0]) == job["compiler_sha256"]
        for path, checksum in (job["host_inputs_sha256"] | job["codec_source_inputs_sha256"]).items():
            assert sha(path) == checksum
        job["profile_inputs_sha256"] = {}
        for key in (REGISTER_WEIGHTS, BLOCK_LAYOUT):
            for entry in job["flags"].get(key, "").split(";"):
                if entry:
                    path = entry.split("@", 1)[1]
                    job["profile_inputs_sha256"][path] = sha(path)
    names = list(actors)
    pattern = (0, 1, 3, 2)
    orders = [[names[(offset + item) % len(names)] for item in pattern]
              for offset in range(len(names))] * 2
    assert len(set(Counter(pair for order in orders for pair in zip(order, order[1:])).values())) == 1
    plan = {"actors": actors, "orders": orders, "host": previous["host"],
            "timer_sha256": sha(timer), "load_before": os.getloadavg(),
            "scope": "Original source through final executable link with prebuilt compilers and fixed host support."}
    write(args.output / "plan.json", plan)

    def trial(actor, label):
        job = actors[actor]
        return measure(actor, args.output / label / actor, job["compile"], job["link"],
                       job["reference_object"], job["flags"], job["artifact_sha256"])

    warmup = {name: trial(name, "warmup") for name in names}
    trials = [{actor: trial(actor, f"order-{index}") for actor in order}
              for index, order in enumerate(orders, 1)]
    for actor, first in warmup.items():
        assert all(batch[actor]["stripped_executable"] == first["stripped_executable"] for batch in trials)
    medians = {name: {key: median(batch[name]["seconds"][key] for batch in trials)
                      for key in first["seconds"]}
               for name, first in warmup.items()}
    record = {"medians_seconds": medians, "observations": trials, "warmup": warmup,
              "plan_sha256": sha(args.output / "plan.json")}
    write(args.output / "comparison.json", record)
    print("BUILD", json.dumps(medians), flush=True)

    fixtures = read(args.lab.parents[1] / "fixtures.json")
    records = []
    streams = args.output / "raw-streams"
    streams.mkdir()
    for name in names:
        executable = args.output / "warmup" / name / "compressor"
        for fixture in fixtures:
            raw = subprocess.check_output([str(executable), fixture["input"]])
            expected = Path(fixture["expected"]).read_bytes()[fixture["prefix_bytes"]:]
            assert zlib.decompress(raw, -15) == Path(fixture["input"]).read_bytes()
            assert raw == expected or name == "libdeflate"
            from hashlib import sha256
            checksum = sha256(raw).hexdigest()
            path = streams / (checksum + ".deflate")
            if not path.exists():
                path.write_bytes(raw)
            else:
                assert path.read_bytes() == raw
            records.append({"actor": name, "case": fixture["name"], "raw_sha256": checksum,
                            "raw_bytes": len(raw), "exact": raw == expected, "independent_inflation": True})
    assert len(records) == len(names) * 81
    write(args.output / "deployment-smokes.json", records)


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument("mode", choices=("native", "build"))
    for field in ("role", "lab", "archived-packet", "output"):
        parser.add_argument("--" + field, required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    if args.mode == "native":
        gate_artifacts(args)
        linked_gates(args)
    else:
        complete_builds(args)


if __name__ == "__main__":
    main()
