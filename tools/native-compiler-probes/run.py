#!/usr/bin/env python3
"""Run archived compiler diagnostics against an exact Mech commit in a disposable clone."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTROLLER = ROOT / "experiments/janet/knucleotide-bytes-v1/process.py"
SUPERVISOR = ROOT / "tools/qualification/prolog_supervisor.py"
MANIFEST = HERE / "probes.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_pin(path):
    return {"path": str(path), "sha256": digest(path.read_bytes())}


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def git(workspace, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(workspace), *arguments], stderr=subprocess.PIPE
    )


def source_state(workspace):
    return {
        "commit": git(workspace, "rev-parse", "HEAD").decode().strip(),
        "tree": git(workspace, "rev-parse", "HEAD^{tree}").decode().strip(),
        "status": git(workspace, "status", "--porcelain", "--untracked-files=all").decode(),
        "diff_sha256": digest(git(workspace, "diff", "--binary", "HEAD")),
    }


def install_probe(checkout, name, spec):
    source = HERE / "probes" / (name + ".rs")
    raw = source.read_bytes()
    require(digest(raw) == spec["source_sha256"], f"Archive hash changed: {name}")
    target = checkout / spec["target_file"]
    require(target.resolve().is_relative_to(checkout.resolve()), "Probe target escapes checkout")
    require(target.is_file() and not target.is_symlink(), f"Missing regular test support: {target}")
    original = target.read_bytes()
    marker = ("fn " + spec["function"] + "(").encode()
    if marker in original:
        require(original.count(marker) == 1 and raw in original,
                f"Existing {name} differs from the archived diagnostic")
        mode = "existing-identical"
    else:
        # The archived functions previously used their test module's imports.
        # Local imports keep the overlay independent of that incidental scaffolding.
        installed = raw
        if name in ("window-kernel", "histogram-kernel"):
            declaration = ("fn " + spec["function"] + "() {\n").encode()
            require(raw.count(declaration) == 1, "Unexpected probe declaration")
            installed = raw.replace(declaration, declaration +
                                    b"    use std::{hint::black_box, time::Instant};\n", 1)
        target.write_bytes(original.rstrip() + b"\n\n" + installed)
        mode = "test-overlay"
    return {
        "probe": name, "mode": mode, "target_file": spec["target_file"],
        "archived_source": file_pin(source), "before_sha256": digest(original),
        "after_sha256": digest(target.read_bytes()), "test": spec["test"],
    }


def selected_executable(output, target):
    expected_name = "mech_gpu" if target == "lib" else target
    expected_kind = "lib" if target == "lib" else "test"
    paths = set()
    for line in output.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (message.get("reason") == "compiler-artifact"
                and message.get("profile", {}).get("test") is True
                and message.get("target", {}).get("name") == expected_name
                and expected_kind in message["target"].get("kind", [])
                and message.get("executable")):
            paths.add(message["executable"])
    require(len(paths) == 1, f"Expected one Cargo test executable for {target}, got {paths}")
    executable = Path(paths.pop())
    require(executable.is_absolute() and executable.is_file(), "Cargo executable is not a file")
    return executable


def validate_selection(output, test):
    require(output.strip().splitlines() == [test + ": test"],
            f"The ignored exact test selection was not unique: {output!r}")


def validate_result(output, test):
    counts = re.findall(r"^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;", output, re.M)
    require(counts == [("1", "0", "0")], f"The probe did not pass exactly one test: {counts}")
    require(re.search(r"^test " + re.escape(test) + r" \.\.\. ok$", output, re.M),
            "The completed test name did not match the selected probe")


def environment(args, evidence):
    if args.environment:
        env = json.loads(args.environment.read_text())
        require(isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str)
                for k, v in env.items()), "Environment JSON must map names to strings")
    else:
        allowed = ("PATH", "HOME", "CARGO_HOME", "RUSTUP_HOME", "RUSTFLAGS",
                   "C_INCLUDE_PATH", "LIBRARY_PATH", "MECH_GMP_LIBRARY", "SDKROOT")
        env = {key: os.environ[key] for key in allowed if key in os.environ}
    # Never allow an ambient diagnostic input to select an unrecorded fixture.
    env = {key: value for key, value in env.items() if not key.startswith("MECH_WINDOW_KERNEL_")
           and not key.startswith("MECH_HISTOGRAM_KERNEL_")}
    env.update(LC_ALL="C", LANG="C", TZ="UTC", NO_COLOR="1", CARGO_INCREMENTAL="0",
               CARGO_BUILD_JOBS="1", CARGO_PROFILE_TEST_DEBUG="0", CARGO_PROFILE_DEV_DEBUG="0",
               CARGO_TARGET_DIR=str(evidence / "target"), TMPDIR=str(evidence / "tmp"))
    (evidence / "tmp").mkdir()
    return env


def execute_stage(process, command, stage, env, lock, checkout, deadline):
    # The shared controller owns the child group and inherited mutex. Its cwd is
    # the benchmarks root, so exec a tiny argv-based chdir wrapper for this clone.
    wrapper = "import os,sys;os.chdir(sys.argv[1]);os.execve(sys.argv[2],sys.argv[2:],os.environ)"
    receipt = process.execute([sys.executable, "-c", wrapper, str(checkout), *command],
                              stage, env, lock, deadline=deadline, quantitative=False)
    require(receipt["exit_status"] == 0, f"{stage.name} failed; see {stage / 'stderr.bin'}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path, help="Clean local Mech Git repository")
    parser.add_argument("--commit", required=True, help="Full 40-character immutable Git commit")
    parser.add_argument("--probe", choices=["all", "window-kernel", "histogram-kernel", "window-region"], default="all")
    parser.add_argument("--evidence", required=True, type=Path, help="New directory outside both repositories")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-only", action="store_true", help="Verify and install overlays without compiling")
    mode.add_argument("--compile-only", action="store_true", help="Compile and verify exact ignored selections")
    parser.add_argument("--input", type=Path, help="FASTA fixture with exactly 10,000,000 bases in >THREE")
    parser.add_argument("--oracle", type=Path, help="Exact k-nucleotide oracle for window-kernel")
    parser.add_argument("--environment", type=Path, help="Optional JSON map of build environment strings")
    parser.add_argument("--cargo", default=shutil.which("cargo"), help="Cargo executable (default: PATH)")
    parser.add_argument("--toolchain", default="nightly-2026-03-03")
    parser.add_argument("--mutex", type=Path, default=Path("/private/tmp/mech-clbg-timing.lock"),
                        help="Existing common timing mutex; never created or replaced")
    args = parser.parse_args()
    workspace, evidence = args.workspace.resolve(), args.evidence.resolve()
    require(re.fullmatch(r"[0-9a-f]{40}", args.commit), "--commit must be a full lowercase Git SHA")
    require(not evidence.is_relative_to(workspace) and not evidence.is_relative_to(ROOT),
            "Evidence must be outside the source and benchmarks repositories")
    before = source_state(workspace)
    require(not before["status"], "Source workspace must be clean")
    require(git(workspace, "rev-parse", args.commit + "^{commit}").decode().strip() == args.commit,
            "Commit is unavailable in source workspace")
    manifest = json.loads(MANIFEST.read_text())
    probes = manifest["probes"]
    names = list(probes) if args.probe == "all" else [args.probe]
    run_probes = not args.prepare_only and not args.compile_only
    if run_probes:
        require(args.input is not None or not any(probes[n]["required_environment"] for n in names),
                "Selected kernel probes require --input")
        require(args.oracle is not None or "window-kernel" not in names,
                "window-kernel requires --oracle")
    inputs = {key: file_pin(path.resolve()) for key, path in
              (("input", args.input), ("oracle", args.oracle)) if path is not None}
    evidence.mkdir(parents=True, exist_ok=False)
    checkout = evidence / "checkout"
    report = {"schema": "mech.native-compiler-probe-run.v1", "status": "started",
              "scope": "compiler/kernel diagnostics", "performance_qualified": False,
              "primary_timing_samples": 0, "source_workspace": str(workspace),
              "source_before": before, "requested_commit": args.commit, "probes": names,
              "runner": file_pin(Path(__file__)), "manifest": file_pin(MANIFEST),
              "controller": file_pin(CONTROLLER), "supervisor": file_pin(SUPERVISOR), "inputs": inputs}
    try:
        with (evidence / "checkout.log").open("wb") as log:
            subprocess.run(["git", "clone", "--no-hardlinks", "--no-checkout", "--",
                            str(workspace), str(checkout)], stdout=log, stderr=log, check=True)
            subprocess.run(["git", "-C", str(checkout), "checkout", "--detach", args.commit],
                           stdout=log, stderr=log, check=True)
        report["checkout_before"] = source_state(checkout)
        require(report["checkout_before"]["commit"] == args.commit
                and not report["checkout_before"]["status"], "Checkout is not exact and clean")
        report["overlays"] = [install_probe(checkout, n, probes[n]) for n in names]
        (evidence / "test-overlay.patch").write_bytes(git(checkout, "diff", "--binary", "HEAD"))
        report["checkout_overlay"] = source_state(checkout)
        report["status"] = "prepared"
        save(evidence / "result.json", report)
        if args.prepare_only:
            return
        require(sys.platform == "darwin", "The shared resource receipt controller currently requires macOS")
        require(args.cargo is not None, "Cargo executable not found")
        cargo = Path(args.cargo).absolute()
        require(cargo.is_file(), "Cargo executable is not a file")
        env = environment(args, evidence)
        if args.input:
            env.update(MECH_WINDOW_KERNEL_INPUT=inputs["input"]["path"],
                       MECH_HISTOGRAM_KERNEL_INPUT=inputs["input"]["path"])
        if args.oracle:
            env["MECH_WINDOW_KERNEL_ORACLE"] = inputs["oracle"]["path"]
        report["environment"] = env
        targets = sorted({probes[name]["target"] for name in names})
        command = [str(cargo), "+" + args.toolchain, "test", "--locked", "--offline", "-j1",
                   "-p", "mech-gpu", "--no-default-features", "--features", "canonical-native-program",
                   "--no-run", "--message-format=json"]
        for target in targets:
            command += ["--lib"] if target == "lib" else ["--test", target]
        report["compile_command"] = command
        module = importlib.util.spec_from_file_location("native_probe_process", CONTROLLER)
        process = importlib.util.module_from_spec(module)
        module.loader.exec_module(process)
        # r+ preserves the shared lock inode; contention fails before compilation.
        with args.mutex.resolve().open("r+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            report["mutex"] = {"path": str(args.mutex.resolve()), "inode": os.fstat(lock.fileno()).st_ino}
            execute_stage(process, command, evidence / "compile", env, lock, checkout, 1800)
            output = (evidence / "compile/stdout.bin").read_text()
            binaries = {target: selected_executable(output, target) for target in targets}
            report["executables"] = {target: file_pin(path) for target, path in binaries.items()}
            for name in names:
                test = probes[name]["test"]
                binary = str(binaries[probes[name]["target"]])
                execute_stage(process, [binary, test, "--exact", "--ignored", "--list", "--format=terse"],
                              evidence / (name + "-selection"), env, lock, checkout, 30)
                validate_selection((evidence / (name + "-selection/stdout.bin")).read_text(), test)
                if run_probes:
                    execute_stage(process, [binary, test, "--exact", "--ignored", "--test-threads=1", "--nocapture"],
                                  evidence / (name + "-run"), env, lock, checkout, 120)
                    validate_result((evidence / (name + "-run/stdout.bin")).read_text(), test)
            report["status"] = "diagnostics-passed" if run_probes else "compiled-and-selected"
    except BaseException as error:
        report["status"] = "failed"
        report["error"] = repr(error)
        raise
    finally:
        try:
            report["source_after"] = source_state(workspace)
            require(report["source_after"] == before, "Source workspace changed during probe run")
            if "checkout_overlay" in report:
                report["checkout_after"] = source_state(checkout)
                require(report["checkout_after"] == report["checkout_overlay"], "Checkout changed after overlay")
            pins = [report[key] for key in ("runner", "manifest", "controller", "supervisor")]
            pins += list(inputs.values()) + list(report.get("executables", {}).values())
            pins += [overlay["archived_source"] for overlay in report.get("overlays", [])]
            for pin in pins:
                require(file_pin(Path(pin["path"])) == pin, f"Pinned file changed during probe run: {pin['path']}")
        except BaseException as error:
            report["status"] = "failed"
            report["integrity_error"] = repr(error)
            raise
        finally:
            report["process_evidence"] = {
                receipt.parent.name: {name: file_pin(receipt.parent / name)
                                      for name in ("process.json", "stdout.bin", "stderr.bin")}
                for receipt in evidence.glob("*/process.json")
            }
            save(evidence / "result.json", report)
            print(json.dumps({"status": report["status"], "evidence": str(evidence),
                              "performance_qualified": False}))


if __name__ == "__main__":
    main()
