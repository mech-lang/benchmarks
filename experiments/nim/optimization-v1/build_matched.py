#!/usr/bin/env python3
"""Prepare a pinned matched build; compilation requires explicit --execute."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HISTORICAL = ROOT / "archive/languages/nim/20261012/qualification/private-v4/builds/nim-knucleotide-optimized/build.json"
LOCK = Path("/tmp/mech-clbg-timing.lock")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def prepare():
    recipe = json.loads((HERE / "plan.json").read_text())
    restored = json.loads((HERE / "runtime-restoration.json").read_text())
    compiler = Path(restored["compiler"])
    distribution = Path(restored["distribution"])
    if sha(compiler) != restored["compiler_sha256"]:
        raise RuntimeError("Restored compiler changed")
    for relative, expected in restored["checked_distribution_pins"].items():
        if sha(distribution / relative) != expected:
            raise RuntimeError("Restored distribution changed: " + relative)
    historical = json.loads(HISTORICAL.read_text())
    commands = []
    staging = HERE / ".build/matched-v1"
    staging.mkdir(exist_ok=False)
    for identity, original, expected in (
        ("parent", ROOT / recipe["parent_source"]["path"], recipe["parent_source"]["sha256"]),
        ("mgetorput", ROOT / recipe["candidate"]["path"], recipe["candidate"]["sha256"]),
    ):
        if sha(original) != expected:
            raise RuntimeError("Application source changed")
        folder = staging / identity
        folder.mkdir()
        source = folder / "knucleotide.nim"
        shutil.copyfile(original, source)
        binary, cache = folder / "knucleotide", folder / "nimcache"
        command = list(historical["command"])
        command[0], command[-1] = str(compiler), str(source)
        for index, argument in enumerate(command):
            if argument.startswith("--lib:"):
                command[index] = "--lib:" + str(distribution / "lib")
            elif argument.startswith("--nimcache:"):
                command[index] = "--nimcache:" + str(cache)
            elif argument.startswith("--out:"):
                command[index] = "--out:" + str(binary)
        commands.append(dict(id=identity, source=str(source), original_source=str(original),
                             source_sha256=expected, binary=str(binary), nimcache=str(cache), command=command))
    dependencies = {}
    proposal = json.loads((ROOT / "archive/languages/nim/20261012/proposals/private-v4.json").read_text())
    for path in (commands[0]["command"][commands[0]["command"].index("--cc:clang") + 1].split(":", 1)[1],
                 "/opt/homebrew/Cellar/pcre/8.45/lib/libpcre.1.dylib", "/opt/homebrew/Cellar/gmp/6.3.0/lib/libgmp.10.dylib"):
        actual = sha(Path(path))
        if actual != proposal["pins"][path]:
            raise RuntimeError("Pinned compiler/link dependency changed: " + path)
        dependencies[path] = actual
    plan = dict(
        schema="nim-matched-build-plan.v1", status="prepared-not-compiled", commands=commands,
        historical_build=str(HISTORICAL.relative_to(ROOT)), historical_build_sha256=sha(HISTORICAL),
        runtime_restoration=str((HERE / "runtime-restoration.json").relative_to(ROOT)),
        runtime_restoration_sha256=sha(HERE / "runtime-restoration.json"), compiler_sha256=sha(compiler),
        pinned_native_build_dependencies=dependencies,
        compile_flags_policy="Exact saved flags retained; only compiler, stdlib, source, nimcache and output locations relocate. Both source copies have identical module basename.",
        unused_historical_package_search_paths=[dict(argument=arg, exists=Path(arg.split(":", 1)[1]).exists())
                                                for arg in commands[0]["command"] if arg.startswith("--path:")],
        unused_search_path_note="The two historical --path arguments remain verbatim for flag parity. k-nucleotide imports only pinned standard modules and uses neither BigInts nor nim-gmp. Their old directories are absent; no content at those paths was read during preparation. Verify compiler-loaded modules in the eventual nimcache/log before admission.",
        sdk_note="Recorded MacOSX14.4 SDK path is retained and exists. Preparation did not invoke Clang to establish header/library compatibility. If a relocation is required, prepare a new matched recipe for both sources and record it explicitly.",
        shared_timing_lock=str(LOCK), compilation_performed=False, benchmark_processes=0,
        no_samples_reused=True, canonical_catalog_changed=False,
    )
    write_new(HERE / "matched-build-plan.json", plan)
    return plan


def execute(reviewed_sha):
    path = HERE / "matched-build-plan.json"
    if sha(path) != reviewed_sha:
        raise RuntimeError("Reviewed plan digest differs")
    plan = json.loads(path.read_text())
    restored = json.loads((HERE / "runtime-restoration.json").read_text())
    with LOCK.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        inherited = fcntl.fcntl(lock.fileno(), fcntl.F_DUPFD, 64)
        try:
            for row in plan["commands"]:
                source = Path(row["source"])
                if sha(source) != row["source_sha256"]:
                    raise RuntimeError("Prepared source changed")
                if sha(Path(row["command"][0])) != plan["compiler_sha256"]:
                    raise RuntimeError("Compiler changed")
                for relative, expected in restored["checked_distribution_pins"].items():
                    if sha(Path(restored["distribution"]) / relative) != expected:
                        raise RuntimeError("Compiler distribution changed")
                folder = source.parent
                receipt_path = folder / "build.json"
                if receipt_path.exists() or Path(row["binary"]).exists():
                    raise RuntimeError("Existing build result; do not retry/overwrite")
                started = time.monotonic()
                with (folder / "build.stdout").open("x") as stdout, (folder / "build.stderr").open("x") as stderr:
                    process = subprocess.Popen(row["command"], cwd=folder, stdout=stdout, stderr=stderr,
                                               start_new_session=True, pass_fds=(inherited,))
                    try:
                        status = process.wait(timeout=180)
                    except BaseException:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        raise
                receipt = dict(schema="nim-matched-compilation.v1", id=row["id"], command=row["command"],
                               cwd=str(folder), source_sha256=sha(source), compiler_sha256=plan["compiler_sha256"],
                               reviewed_plan_sha256=reviewed_sha, exit_status=status,
                               elapsed_build_seconds=time.monotonic() - started, compiler_pid=process.pid,
                               compiler_pgid=process.pid, inherited_common_mutex_descriptor=inherited,
                               build_only=True, benchmark_processes=0, never_chart_eligible=True,
                               artifacts={str(p.relative_to(folder)): sha(p) for p in folder.rglob("*") if p.is_file()})
                write_new(receipt_path, receipt)
                if status != 0:
                    raise RuntimeError("Matched build failed; inspect its receipt before proceeding")
        finally:
            os.close(inherited)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--reviewed-plan-sha256")
    args = parser.parse_args()
    if args.execute:
        if not args.reviewed_plan_sha256:
            parser.error("--execute requires --reviewed-plan-sha256")
        execute(args.reviewed_plan_sha256)
    else:
        plan = prepare()
        print(json.dumps(dict(status=plan["status"], plan=str(HERE / "matched-build-plan.json"),
                              plan_sha256=sha(HERE / "matched-build-plan.json"), compilation_performed=False)))
