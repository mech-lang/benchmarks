"""Build and verify the qualified level-12 encoder from the pinned Mech source."""
import argparse
from hashlib import file_digest
import json
import os
from pathlib import Path
from runpy import run_path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PATH_SETTINGS = ("MECH_COMPACT_PHASE_BLOCK_LAYOUT", "MECH_COMPACT_PHASE_REGISTER_WEIGHTS")


def digest(path):
    with path.open("rb") as data:
        return file_digest(data, "sha256").hexdigest()


def require_hash(path, expected):
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"{path}: expected SHA-256 {expected}, got {actual}")
    return actual


def load_flags(recipe):
    flags = recipe["flags"].copy()
    inputs = recipe["profile_inputs_sha256"]
    used = set()
    for option in PATH_SETTINGS:
        entries = []
        for entry in flags[option].split(";"):
            symbol, relative = entry.split("@", 1)
            path = HERE / relative
            require_hash(path, inputs[relative])
            entries.append(f"{symbol}@{path}")
            used.add(relative)
        flags[option] = ";".join(entries)
    if used != inputs.keys():
        raise ValueError("The recipe and profile manifest describe different files.")
    return flags


def remove_build_overrides():
    names = {
        "RUSTC", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER",
        "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_BUILD_TARGET",
        "CARGO_BUILD_RUSTFLAGS", "CARGO_BUILD_RUSTC", "CARGO_BUILD_RUSTC_WRAPPER",
        "CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER",
    }
    for key in tuple(os.environ):
        if key in names or key.startswith(("CARGO_PROFILE_", "MECH_")):
            os.environ.pop(key)


def check_checkout(root, recipe):
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True,
    ).strip()
    if commit != recipe["source_commit"]:
        raise ValueError(f"Check out {recipe['source_commit']} in {root}. Found {commit}.")
    tracked = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=root)
    if tracked.returncode:
        raise ValueError(f"Use a clean checkout of the pinned Mech revision in {root}.")
    source = root / recipe["codec_source"]
    require_hash(source, recipe["codec_source_sha256"])
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="A fresh directory for the build.")
    parser.add_argument("--target-dir", type=Path, help="Reuse a Cargo target directory.")
    parser.add_argument("--compiler", type=Path, help="Use an existing compile_profile executable.")
    parser.add_argument("--encoder-only", action="store_true", help="Stop after verifying the emitted artifacts.")
    args = parser.parse_args()

    root, output = args.mech_root.resolve(), args.output.resolve()
    recipe = json.loads((HERE / "recipe.json").read_text())
    source = check_checkout(root, recipe)
    flags = load_flags(recipe)
    toolchain = recipe["compiler"]
    packet = HERE / toolchain["driver_packet"]
    for relative, expected in toolchain["inputs_sha256"].items():
        require_hash(packet / relative, expected)

    host = os.uname()
    if (host.sysname, host.machine) != ("Darwin", "arm64"):
        parser.error("The recorded encoder targets Apple Silicon macOS.")
    assembler = run_path(str(packet / "reproduce.py"))
    remove_build_overrides()
    output.mkdir(parents=True)
    if args.compiler:
        compiler = args.compiler.resolve(strict=True)
    else:
        rustc = subprocess.check_output(
            ["rustc", "+" + toolchain["toolchain"], "-vV"], text=True
        )
        if ("commit-hash: " + toolchain["rustc_commit"] not in rustc or
                "host: " + toolchain["target"] not in rustc):
            raise ValueError("Install the pinned Apple Silicon Rust toolchain.")
        target = args.target_dir.resolve() if args.target_dir else output / "target"
        compiler = assembler["build_compiler"](root, output, target)
        record = json.loads((output / "compiler-build.json").read_text())
        if record["environment"] != toolchain["cargo_environment"]:
            raise ValueError("The rebuilt compiler used different Cargo settings.")

    frontend = output / "frontend"
    command = [str(compiler), str(source), str(frontend), recipe["encoder_mode"]]
    with (output / "encoder-build.log").open("w") as log:
        subprocess.run(command, cwd=root, env=assembler["clean_environment"]() | flags,
                       stdout=log, stderr=log, check=True)
    artifacts = {
        name: require_hash(frontend / name, expected)
        for name, expected in recipe["artifacts"].items()
    }
    witness = {
        "source_commit": recipe["source_commit"],
        "role": recipe["role"],
        "compiler_sha256": digest(compiler),
        "command": command,
        "profile_inputs_sha256": recipe["profile_inputs_sha256"],
        "artifacts": artifacts,
        "recipe_sha256": digest(HERE / "recipe.json"),
    }
    if not args.encoder_only:
        executable = output / "compressor"
        subprocess.run(
            [sys.executable, str(HERE / "link_deployment.py"),
             "--encoder", str(frontend / "program.o"), "--output", str(executable),
             "--receipt", str(output / "deployment-link.json")],
            check=True,
        )
        witness["deployment_sha256"] = require_hash(executable, recipe["deployment_stripped_executable_sha256"])
    (output / "reproduction.json").write_text(json.dumps(witness, indent=2) + "\n")
    print("Encoder object, canonical bytecode and metadata match all three recorded hashes.")


if __name__ == "__main__":
    main()
