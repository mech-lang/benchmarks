"""Rebuild the Cranelift encoder, runtime tests and native timing executables."""

from argparse import ArgumentParser
from hashlib import file_digest
import json
import os
from pathlib import Path
from runpy import run_path
import shutil
import subprocess
import time


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def checked(path, expected):
    actual = sha(path)
    if actual != expected:
        raise ValueError(f"{path}: expected {expected}, got {actual}")
    return actual


def run(command, log, env, cwd):
    with log.open("w") as stream:
        subprocess.run(command, stdout=stream, stderr=stream, check=True, env=env, cwd=cwd)


def write_source(path, template, root):
    text = template.read_text()
    # The substituted path appears inside existing Rust and TOML strings.
    path.write_text(text.replace("@MECH_ROOT@", json.dumps(str(root), ensure_ascii=False)[1:-1]))


def build(args):
    root, output = args.mech_root.resolve(strict=True), args.output.resolve()
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    recipe = read(args.recipe.resolve(strict=True))
    base = packets / "mechdeflate-81-v1"
    manifest = base / "recipe.json"
    checked(manifest, recipe["base_recipe_sha256"])
    original = read(manifest)
    original["source_commit"] = recipe["source_commit"]
    helpers = run_path(str(base / "rebuild.py"))
    source = helpers["check_checkout"](root, original)
    flags = helpers["load_flags"](original)
    if (os.uname().sysname, os.uname().machine) != ("Darwin", "arm64"):
        raise ValueError("The pinned timing workers target Apple Silicon macOS.")

    tools = original["compiler"]
    rust = tools["toolchain"]
    version = subprocess.check_output(["rustc", "+" + rust, "-vV"], text=True)
    if f"commit-hash: {tools['rustc_commit']}" not in version:
        raise ValueError("Install the Rust toolchain pinned by the base recipe.")
    for path, expected in recipe["inputs_sha256"].items():
        checked(HERE / path, expected)
    helpers["remove_build_overrides"]()
    env = dict(os.environ)
    output.mkdir(parents=True)
    target = args.target_dir.resolve() if args.target_dir else output / "target"

    driver = output / "compiler-driver"
    driver.mkdir()
    for name in ("Cargo.toml", "compile_profile.rs"):
        write_source(driver / name, HERE / "compiler-driver" / (name + ".in"), root)
    shutil.copyfile(HERE / "compiler-driver/Cargo.lock", driver / "Cargo.lock")
    cargo = ["cargo", "+" + rust, "build", *tools["cargo_options"],
             "--message-format=json-render-diagnostics",
             "--manifest-path", str(driver / "Cargo.toml"), "--target-dir", str(target)]
    events = output / "compiler-artifacts.jsonl"
    with events.open("w") as stdout, (output / "compiler-build.log").open("w") as stderr:
        subprocess.run(cargo, stdout=stdout, stderr=stderr, cwd=root, check=True,
                       env=env | tools["cargo_environment"])
    libraries = {}
    for line in events.read_text().splitlines():
        event = json.loads(line)
        if event.get("reason") == "compiler-artifact":
            name = event["target"]["name"]
            if name in ("mech_engine", "serde", "serde_json", "miniz_oxide"):
                paths = [path for path in event["filenames"] if path.endswith(".rlib")]
                assert len(paths) == 1 and name not in libraries
                libraries[name] = paths[0]
    assert len(libraries) == 4
    compiler = target / "release/compile_profile"

    support = HERE / "support"
    allocator = support / "mimalloc-2.1.7.o"
    runtime = output / "runtime.rs"
    module = root / "hosts/gpu/src/native_artifact/compact_runtime/mod.rs"
    runtime.write_text(
        'pub mod native_artifact {\n #[path = ' + json.dumps(str(module)) + ']\n'
        ' pub mod compact_runtime;\n}\n'
    )
    rustc = ["rustc", "+" + rust, "--edition=2024", "-C", "opt-level=3", "-D", "warnings"]
    runtime_env = env | {"MECH_INLINE_OWNER_RECORDS": str(recipe["inline_owner_records"])}
    tests = output / "runtime-tests"
    run([*rustc, str(runtime), "--test", "-o", str(tests)], output / "runtime-test-link.log", runtime_env, root)
    run([tests], output / "runtime-tests.log", runtime_env, root)
    runtime_lib = output / "libmech_gpu_runtime.rlib"
    run([*rustc, str(runtime), "--crate-type", "rlib", "--crate-name", "mech_gpu", "-o", str(runtime_lib)],
        output / "runtime-link.log", runtime_env, root)

    whole = output / "silesia-support"
    whole.mkdir()
    wrapper = whole / "deploy_wrapper.rs"
    write_source(wrapper, support / "deploy_wrapper.rs.in", root)
    shutil.copyfile(support / "pinned_allocator.rs", whole / "pinned_allocator.rs")
    whole_lib = whole / "libmech_silesia.a"
    run(["rustc", "+" + rust, "--edition", "2024", "--crate-name", "mech_silesia",
         "--crate-type", "staticlib", "-C", "panic=abort", "-C", "opt-level=3", wrapper, "-o", whole_lib],
        whole / "runtime-build.log", runtime_env, root)
    clock = whole / "clock.o"
    cc = ["/usr/bin/clang", "-arch", "arm64", "-mmacosx-version-min=15.0"]
    c = packets / "mechdeflate-silesia-v1/timed_deployment.c"
    checked(c, recipe["silesia_clock_source_sha256"])
    run([*cc, "-O2", "-std=c17", "-Wall", "-Wextra", "-Werror", "-c", c, "-o", clock],
        whole / "clock-build.log", env, root)

    for name, role in recipe["roles"].items():
        variant = output / name
        variant.mkdir()
        selected = flags.copy()
        profiles = role.get("profile_inputs_sha256", {})
        used_profiles = set()
        for key, value in role["settings_delta"].items():
            if value is None:
                del selected[key]
            elif key == "MECH_COMPACT_ROOT_TAIL_PROFILE":
                path = HERE / value
                checked(path, profiles[value])
                used_profiles.add(value)
                selected[key] = str(path)
            elif key in helpers["PATH_SETTINGS"]:
                entries = []
                for entry in value.split(";"):
                    symbol, relative = entry.split("@", 1)
                    path = HERE / relative
                    checked(path, profiles[relative])
                    used_profiles.add(relative)
                    entries.append(f"{symbol}@{path}")
                selected[key] = ";".join(entries)
            else:
                selected[key] = value
        if used_profiles != profiles.keys():
            raise ValueError(f"{name}: the role and profile manifest describe different files.")
        bound = variant / "bound"
        bound.mkdir()
        for file in ("mech-worker.rs", "pinned_allocator.rs"):
            shutil.copyfile(support / file, bound / file)
        worker = bound / "mech-worker"
        frontend = variant / "frontend"
        emit = [compiler, source, frontend, original["encoder_mode"]]
        link = [*rustc, "-L", "dependency=" + str(target / "release/deps"),
                bound / "mech-worker.rs", "-o", worker, "-C", "link-arg=" + str(allocator),
                "-C", "link-arg=" + str(bound / "program.o")]
        for crate in recipe["worker_extern_order"]:
            library = runtime_lib if crate == "mech_gpu" else libraries[crate]
            link.extend(["--extern", crate + "=" + str(library)])
        measurements = []
        for index in range(args.build_repeats):
            start = time.perf_counter()
            run(emit, variant / f"encoder-build-{index}.log", env | selected, root)
            emitted = time.perf_counter()
            for file in role["artifacts"]:
                shutil.copyfile(frontend / file, bound / file)
            run(link, variant / f"worker-link-{index}.log", env, root)
            complete = time.perf_counter()
            measurements.append({
                "source_through_executable_seconds": complete - start,
                "source_through_object_seconds": emitted - start,
                "worker_link_seconds": complete - emitted,
            })
            for file, expected in role["artifacts"].items():
                checked(bound / file, expected)
        whole_actor = variant / "silesia-encoder"
        run([*cc, "-Wl,-dead_strip", clock, whole_lib, bound / "program.o", allocator, "-o", whole_actor],
            variant / "silesia-encoder-link.log", env, root)
        write(variant / "receipt.json", {
            "source_commit": recipe["source_commit"], "compiler_sha256": sha(compiler),
            "runtime_sha256": sha(runtime_lib), "artifacts": role["artifacts"],
            "worker_sha256": sha(worker), "silesia_actor_sha256": sha(whole_actor),
            "measurements": measurements,
            "encoder_command": list(map(str, emit)), "worker_command": list(map(str, link)),
        })
        print(f"{name}: all encoder artifact hashes match.", flush=True)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--mech-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New output directory")
    parser.add_argument("--target-dir", type=Path, help="Reuse existing Cargo build dependencies")
    parser.add_argument("--bench-root", type=Path, help="Override the benchmark repository location")
    parser.add_argument("--recipe", type=Path, default=HERE / "recipe.json",
                        help="Use a different pinned source and candidate recipe")
    parser.add_argument("--build-repeats", type=int, default=1)
    args = parser.parse_args()
    if args.build_repeats < 1:
        parser.error("Choose at least one build repetition.")
    build(args)
