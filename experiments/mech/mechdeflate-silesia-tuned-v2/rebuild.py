"""Reproduce the level-12 Silesia-tuned encoder object from the pinned source."""
from argparse import ArgumentParser
import json
import os
from pathlib import Path
from runpy import run_path
import shutil
import subprocess
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "mechdeflate-81-v1"
base = run_path(str(BASE / "rebuild.py"))
digest, require_hash = base["digest"], base["require_hash"]



def link_timing_actor(out, encoder, candidate):
    support = json.loads((BASE / "host-support.json").read_text())
    bundle = BASE / "host-support.tar.gz"
    linker = run_path(str(BASE / "link_deployment.py"))
    linker["verify"](bundle, support["archive"])
    harness = HERE.parent / "mechdeflate-silesia-v1/timed_deployment.c"
    require_hash(harness, candidate["timing_harness_source_sha256"])
    clang = ["/usr/bin/clang", "-arch", "arm64", "-mmacosx-version-min=15.0"]

    with tempfile.TemporaryDirectory(prefix=".silesia-link-", dir=out) as temporary:
        work = Path(temporary)
        runtime_path = Path(support["runtime_debug_name_relative_to_virtual_root"])
        if runtime_path.is_absolute() or ".." in runtime_path.parts or runtime_path.name != "libmech_deploy.a":
            raise ValueError("Invalid relative runtime path in the host manifest.")
        runtime = work / runtime_path
        allocator = work / "mimalloc.o"
        runtime.parent.mkdir(parents=True)
        with tarfile.open(bundle, "r:gz") as archive:
            for file in (runtime, allocator):
                pin = support["members"][file.name]
                entry = archive.getmember(file.name)
                if not entry.isfile() or entry.size != pin["bytes"]:
                    raise ValueError(f"Unexpected host archive member {file.name}.")
                with archive.extractfile(entry) as data, file.open("wb") as destination:
                    shutil.copyfileobj(data, destination)
                linker["verify"](file, pin)

        clock = work / "clock.o"
        program = work / "encoder"
        with (out / "timing-actor-link.log").open("w") as log:
            subprocess.run([*clang, "-O2", "-std=c17", "-Wall", "-Wextra", "-Werror",
                            "-c", harness, "-o", clock], stdout=log, stderr=log, check=True)
            subprocess.run([*clang, "-Wl,-dead_strip", "-Xlinker", "-oso_prefix", "-Xlinker", work,
                            clock, runtime, encoder, allocator, "-o", program],
                           stdout=log, stderr=log, check=True)
        actor_hash = require_hash(program, candidate["timing_actor_sha256"])
        os.replace(program, out / "encoder")
    return actor_hash


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--mech-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compiler", type=Path)
    args = parser.parse_args()
    source_root, out = args.mech_root.resolve(), args.output.resolve()
    candidate = json.loads((HERE / "recipe.json").read_text())
    base_file = BASE / "recipe.json"
    require_hash(base_file, candidate["base_recipe_sha256"])
    original = json.loads(base_file.read_text())
    original["source_commit"] = candidate["source_commit"]
    source = base["check_checkout"](source_root, original)
    flags = base["load_flags"](original)
    for key, value in candidate["settings_delta"].items():
        if value is None:
            del flags[key]
        else:
            flags[key] = value
    host = os.uname()
    if (host.sysname, host.machine) != ("Darwin", "arm64"):
        parser.error("The recorded encoder targets Apple Silicon macOS.")
    toolchain = original["compiler"]
    packet = (BASE / toolchain["driver_packet"]).resolve()
    for relative, expected in toolchain["inputs_sha256"].items():
        require_hash(packet / relative, expected)
    builder = run_path(str(packet / "reproduce.py"))
    base["remove_build_overrides"]()
    out.mkdir(parents=True)
    if args.compiler:
        compiler = args.compiler.resolve(strict=True)
    else:
        rustc = subprocess.check_output(["rustc", "+" + toolchain["toolchain"], "-vV"], text=True)
        if ("commit-hash: " + toolchain["rustc_commit"] not in rustc or
                "host: " + toolchain["target"] not in rustc):
            raise ValueError("Install the pinned Apple Silicon Rust toolchain.")
        compiler = builder["build_compiler"](source_root, out, out / "target")
    frontend = out / "frontend"
    command = [compiler, source, frontend, original["encoder_mode"]]
    with (out / "encoder-build.log").open("w") as log:
        subprocess.run(command, cwd=source_root, env=builder["clean_environment"]() | flags,
                       stdout=log, stderr=log, check=True)
    artifacts = {name: require_hash(frontend / name, expected) for name, expected in candidate["artifacts"].items()}
    actor_hash = link_timing_actor(out, frontend / "program.o", candidate)
    (out / "reproduction.json").write_text(json.dumps({
        "source_commit": candidate["source_commit"], "compiler_sha256": digest(compiler),
        "artifacts": artifacts, "timing_actor_sha256": actor_hash,
        "settings_delta": candidate["settings_delta"],
    }, indent=2) + "\n")
    print("Encoder object, bytecode, metadata and timed executable match the Silesia recipe.")


if __name__ == "__main__":
    main()
