#!/usr/bin/env python3
"""Link the qualified arm64 macOS file compressor from its verified encoder object."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


HERE = Path(__file__).resolve().parent
HOST_MEMBERS = ("main.o", "libmech_deploy.a", "mimalloc.o")


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def verify(path, expected):
    actual = fingerprint(path)
    if actual["sha256"] != expected["sha256"] or actual["bytes"] != expected["bytes"]:
        raise ValueError(f"{path.name}: expected {expected['bytes']} bytes and SHA-256 "
                         f"{expected['sha256']}, got {actual['bytes']} and {actual['sha256']}")
    return actual


def link(encoder, output, receipt):
    manifest_path = HERE / "host-support.json"
    manifest = json.loads(manifest_path.read_text())
    archive = HERE / "host-support.tar.gz"
    protected = {encoder, archive, manifest_path, Path(__file__).resolve()}
    if output in protected or (receipt and receipt in protected | {output}):
        raise ValueError("Use separate paths for the inputs, executable, and receipt.")
    verify(archive, manifest["archive"])
    encoder_info = verify(encoder, manifest["encoder"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".mech-link-", dir=output.parent) as scratch:
        work = Path(scratch)
        virtual_name = Path(manifest["runtime_debug_name_relative_to_virtual_root"])
        if virtual_name.is_absolute() or ".." in virtual_name.parts or virtual_name.name != "libmech_deploy.a":
            raise ValueError("Invalid runtime archive debug-map name in the manifest.")
        inputs = {name: work / name for name in HOST_MEMBERS}
        inputs["libmech_deploy.a"] = work / virtual_name
        with tarfile.open(archive, "r:gz") as bundle:
            for name, destination in inputs.items():
                member = bundle.getmember(name)
                expected = manifest["members"][name]
                if not member.isfile() or member.size != expected["bytes"]:
                    raise ValueError(f"Invalid host-support archive entry {name}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
                verify(destination, expected)

        # Apple ld embeds the archive's debug path before deriving the executable UUID.
        # Strip only the temporary root from that path. Keep the signed output name fixed.
        executable = work / "compressor"
        subprocess.run([
            "/usr/bin/clang", "-arch", "arm64", "-mmacosx-version-min=15.0",
            "-Wl,-dead_strip", "-Xlinker", "-oso_prefix", "-Xlinker", str(work),
            str(inputs["main.o"]), str(inputs["libmech_deploy.a"]), str(encoder),
            str(inputs["mimalloc.o"]), "-o", str(executable),
        ], check=True)
        unstripped_info = fingerprint(executable)
        subprocess.run(["/usr/bin/strip", "-S", "-x", str(executable)], check=True)
        stripped_info = verify(executable, manifest["qualified_stripped_executable"])
        os.replace(executable, output)

    report = {
        "encoder": encoder_info,
        "host_archive": manifest["archive"],
        "linked_before_strip": unstripped_info,
        "qualified_stripped_executable": stripped_info,
    }
    if receipt:
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{output}  {stripped_info['bytes']} bytes  SHA-256 {stripped_info['sha256']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoder", type=Path, required=True, help="qualified program.o from rebuild.py")
    parser.add_argument("--output", type=Path, required=True, help="destination executable")
    parser.add_argument("--receipt", type=Path, help="optional output JSON with hashes before and after stripping")
    args = parser.parse_args()
    try:
        link(args.encoder.resolve(), args.output.resolve(), args.receipt.resolve() if args.receipt else None)
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        sys.exit(f"Deployment link failed: {error}")


if __name__ == "__main__":
    main()
