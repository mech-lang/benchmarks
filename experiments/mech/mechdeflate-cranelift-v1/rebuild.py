"""Rebuild the Cranelift encoder, runtime tests and native timing executables."""

from argparse import ArgumentParser
from hashlib import file_digest, sha256
import json
import os
from pathlib import Path
import re
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


def configuration(recipe, role):
    return {
        "architecture": recipe["architecture"],
        "native_backend": recipe["native_backend"],
        "base_recipe_sha256": recipe["base_recipe_sha256"],
        "settings_delta": role["settings_delta"],
        "profiles_sha256": role.get("profile_inputs_sha256", {}),
        "inline_owner_records": recipe["inline_owner_records"],
    }


def configuration_sha256(config):
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    return sha256(canonical).hexdigest()


def run(command, log, env, cwd):
    with log.open("w") as stream:
        subprocess.run(command, stdout=stream, stderr=stream, check=True, env=env, cwd=cwd)


def write_source(path, template, root):
    text = template.read_text()
    # The substituted path appears inside existing Rust and TOML strings.
    path.write_text(text.replace("@MECH_ROOT@", json.dumps(str(root), ensure_ascii=False)[1:-1]))


def configure_driver(driver, recipe):
    module = recipe.get("configured_driver")
    if module is None:
        return
    checked(HERE / module, recipe["inputs_sha256"][module])
    shutil.copyfile(HERE / module, driver / "configured_profile.rs")
    source = driver / "compile_profile.rs"
    contents = source.read_text()
    patches = [
        ("use mech_engine::CanonicalSourceFrontend;",
         "mod configured_profile;\nuse mech_engine::CanonicalSourceFrontend;"),
        ("NativeCompileLimits, emit_compact_closed_object_for_diagnostic, emit_program_object_with_limits,",
         "NativeCompileLimits, emit_program_object_with_limits,"),
        ("args.len() == 4,", 'args.len() == 4 || (args.len() == 5 && args[3] == "compact" && args[4] == "--host-report"),'),
        ('"compact" => emit_compact_closed_object_for_diagnostic(&artifact, &catalog).unwrap(),',
         '"compact" => configured_profile::compile(&artifact, &catalog, &out, args.len() == 5),'),
        ('    println!("{receipt}");',
         '    if args.len() == 5 { configured_profile::finish(&out, &receipt); }\n    println!("{receipt}");'),
    ]
    for old, new in patches:
        if contents.count(old) != 1:
            raise ValueError(f"{source}: configured driver anchor changed: {old}")
        contents = contents.replace(old, new)
    source.write_text(contents)


def host_report(emit, root, env, variant, recipe, role, compiler):
    output = variant / "host-report"
    log = variant / "host-report-process.log"
    command = [*emit, "--host-report"]
    command[2] = output
    run(["/usr/bin/time", "-l", *command], log, env, root)
    for file, expected in role["artifacts"].items():
        checked(output / file, expected)
    path = output / "host-report.json"
    report = read(path)
    if report["object_sha256"] != role["artifacts"]["program.o"]:
        raise ValueError("Host reporting changed the emitted object.")
    rss = re.search(r"(?m)^\s*(\d+)\s+maximum resident set size\s*$", log.read_text())
    if rss:
        report["peak_process_rss"] = {
            "available": True, "bytes": int(rss[1]), "scope": "compiler subprocess lifetime on macOS",
        }
    report["compiler_sha256"] = sha(compiler)
    report["source_commit"] = recipe["source_commit"]
    report["recipe_configuration_sha256"] = configuration_sha256(configuration(recipe, role))
    report["raw_evidence"]["process_measurement"] = str(log)
    write(path, report)
    return {"path": str(path), "sha256": sha(path)}


def effective_settings(flags, role, path_settings):
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
        elif key in path_settings:
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
        raise ValueError("The role and profile manifest describe different files.")
    return selected


def ordinary_compiler_inputs(root, build, recipe_path, packets):
    """Bind the fixed source, ordinary compiler and effective recipe settings."""
    recipe = read(recipe_path)
    base = packets / "mechdeflate-81-v1"
    checked(base / "recipe.json", recipe["base_recipe_sha256"])
    original = read(base / "recipe.json")
    original["source_commit"] = recipe["source_commit"]
    helpers = run_path(str(base / "rebuild.py"))
    source = helpers["check_checkout"](root, original)
    role = recipe["roles"][recipe["candidate_actor"]]
    flags = effective_settings(helpers["load_flags"](original), role, helpers["PATH_SETTINGS"])
    receipt = read(build / recipe["candidate_actor"] / "receipt.json")
    compiler = build / "compile_profile"
    checked(compiler, receipt["compiler_sha256"])
    checked(recipe_path, receipt["recipe_sha256"])
    if receipt["source_commit"] != recipe["source_commit"]:
        raise ValueError("Ordinary compiler inputs do not match the bound source.")
    for path, digest in recipe["inputs_sha256"].items():
        checked(HERE / path, digest)
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("MECH_")}
    return root, [compiler, source, original["encoder_mode"]], environment | flags, receipt


def measure_ordinary_compiler(folder, inputs):
    """Measure one fresh subprocess from source entry through artifact emission."""
    root, (compiler, source, mode), environment, receipt = inputs
    folder.mkdir(parents=True)
    output = folder / "frontend"
    log = folder / "process.log"
    command = ["/usr/bin/time", "-l", compiler, source, output, mode]
    with log.open("x") as stream:
        start = time.perf_counter_ns()
        subprocess.run(command, cwd=root, env=environment, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
        elapsed = time.perf_counter_ns() - start
    for name, digest in receipt["artifacts"].items():
        checked(output / name, digest)
    rss, = re.findall(r"(?m)^\s*(\d+)\s+maximum resident set size\s*$", log.read_text())
    return {
        "command": list(map(str, command)),
        "elapsed_ns": elapsed,
        "maximum_resident_bytes": int(rss),
        "compiler_sha256": receipt["compiler_sha256"],
        "configuration_sha256": receipt["configuration_sha256"],
        "artifacts": receipt["artifacts"],
    }


QUALIFIED_ENCODER_TEST = (
    "native_artifact::program::compilation_report::tests::"
    "qualified_encoder_profile_resolution_and_retry"
)


def qualify_encoder(root, recipe_path, bench_root, output, target=None):
    """Run and record the maintained ignored test as an exact selection."""
    output.mkdir(parents=True)
    recipe = read(recipe_path)
    rust = read(bench_root / "experiments/mech/mechdeflate-81-v1/recipe.json")["compiler"]["toolchain"]
    command = ["cargo", "+" + rust, "test", "--locked", "--offline", "-p", "mech-gpu",
               "--no-default-features", "--features", "canonical-native-program", "--lib"]
    if target is not None:
        command += ["--target-dir", str(target)]
    selection = ["--ignored", "--exact", QUALIFIED_ENCODER_TEST]
    list_command = command + ["--", "--list", *selection]
    test_command = command + ["--", *selection, "--test-threads=1"]
    qualification_env = {"NATIVE_COMPILER_QUALIFICATION_RECIPE": str(recipe_path),
                         "NATIVE_COMPILER_BENCH_ROOT": str(bench_root)}
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("MECH_")}
    environment.update(qualification_env)
    pin = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if pin != recipe["source_commit"]:
        raise ValueError("Qualification test source does not match the recipe.")
    receipt = {
        "source_commit": pin, "recipe_sha256": sha(recipe_path), "toolchain": rust,
        "selection": QUALIFIED_ENCODER_TEST, "list_command": list_command,
        "test_command": test_command, "inputs": qualification_env,
        "selected": 0, "passed": 0,
    }
    try:
        line = QUALIFIED_ENCODER_TEST + ": test"
        listed = output / "selected.log"
        run(list_command, listed, environment, root)
        receipt["selected"] = listed.read_text().splitlines().count(line)
        if receipt["selected"] != 1:
            raise ValueError("Expected exactly one selected ignored encoder test.")
        log = output / "test.log"
        run(test_command, log, environment, root)
        receipt["passed"] = int("test result: ok. 1 passed; 0 failed" in log.read_text())
        if receipt["passed"] != 1:
            raise ValueError("The exact ignored encoder test did not pass.")
    finally:
        write(output / "qualification-receipt.json", receipt)
    return receipt


def build(args):
    root, output = args.mech_root.resolve(strict=True), args.output.resolve()
    packets = args.bench_root.resolve() / "experiments/mech" if args.bench_root else PARENT
    recipe_bytes = args.recipe.read_bytes()
    recipe = json.loads(recipe_bytes)
    if args.with_host_report and "configured_driver" not in recipe:
        raise ValueError("Host reporting requires a pinned configured compiler driver.")
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
    configure_driver(driver, recipe)
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
    compiler = output / "compile_profile"
    shutil.copy2(target / "release/compile_profile", compiler)

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
        selected = effective_settings(flags, role, helpers["PATH_SETTINGS"])
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
        config = configuration(recipe, role)
        receipt = {
            "source_commit": recipe["source_commit"], "compiler_sha256": sha(compiler),
            "source_sha256": sha(source),
            "recipe_sha256": sha256(recipe_bytes).hexdigest(),
            "configuration": config, "configuration_sha256": configuration_sha256(config),
            "runtime_sha256": sha(runtime_lib), "artifacts": role["artifacts"],
            "silesia_runtime_sha256": sha(whole_lib),
            "silesia_clock_sha256": sha(clock), "allocator_sha256": sha(allocator),
            "worker_sha256": sha(worker), "silesia_actor_sha256": sha(whole_actor),
            "measurements": measurements,
            "encoder_command": list(map(str, emit)), "worker_command": list(map(str, link)),
        }
        if args.with_host_report:
            receipt["host_report"] = host_report(emit, root, env | selected, variant, recipe, role, compiler)
        write(variant / "receipt.json", receipt)
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
    parser.add_argument("--with-host-report", action="store_true",
                        help="Run a separately measured host report and verify identical artifacts")
    parser.add_argument("--qualify-encoder", type=Path, metavar="EVIDENCE",
                        help="Also run the exact maintained ignored encoder test")
    args = parser.parse_args()
    if args.build_repeats < 1:
        parser.error("Choose at least one build repetition.")
    build(args)
    if args.qualify_encoder is not None:
        qualify_encoder(args.mech_root.resolve(), args.recipe.resolve(),
                        args.bench_root.resolve() if args.bench_root else HERE.parents[2],
                        args.qualify_encoder.resolve(), args.target_dir)
