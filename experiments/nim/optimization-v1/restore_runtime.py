#!/usr/bin/env python3
"""Restore the pinned official Nim distribution; never execute its programs."""
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROPOSAL = ROOT / "archive/languages/nim/20261012/proposals/private-v4.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proposal = json.loads(PROPOSAL.read_text())
    build = HERE / ".build"
    build.mkdir(exist_ok=True)
    archive = build / "nim-2.2.12-macosx_arm64.tar.xz"
    expected = proposal["compiler_archive_sha256"]
    if not archive.exists():
        temporary = archive.with_suffix(archive.suffix + ".download")
        if temporary.exists():
            raise RuntimeError("Previous partial download exists; inspect it before retrying")
        with urllib.request.urlopen(proposal["compiler_archive_url"], timeout=60) as response:
            with temporary.open("xb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
        if sha(temporary) != expected:
            raise RuntimeError("Official distribution archive hash mismatch")
        temporary.rename(archive)
    if sha(archive) != expected:
        raise RuntimeError("Existing archive hash mismatch")
    install = build / "nim"
    distribution = install / "nim-2.2.12"
    if not distribution.exists():
        install.mkdir(exist_ok=True)
        with tarfile.open(archive) as package:
            package.extractall(install, filter="data")
    pins = {}
    for original, value in proposal["pins"].items():
        if "/nim/nim-2.2.12/" in original:
            relative = original.split("/nim/nim-2.2.12/", 1)[1]
            if relative in pins and pins[relative] != value:
                raise RuntimeError("Historical distribution pins conflict")
            pins[relative] = value
    checked, missing, changed = {}, [], []
    for relative, value in pins.items():
        path = distribution / relative
        if not path.is_file():
            missing.append(relative)
        elif sha(path) != value:
            changed.append(relative)
        else:
            checked[relative] = value
    if missing or changed:
        raise RuntimeError(json.dumps(dict(missing=missing, changed=changed)))
    receipt = dict(
        schema="nim-runtime-restoration.v1", status="exact-pinned-distribution-restored-not-executed",
        archive_url=proposal["compiler_archive_url"], archive=str(archive), archive_sha256=sha(archive),
        compiler_source_commit=proposal["compiler_source_commit"], distribution=str(distribution),
        compiler=str(distribution / "bin/nim"), compiler_sha256=sha(distribution / "bin/nim"),
        historical_proposal=str(PROPOSAL.relative_to(ROOT)), historical_proposal_sha256=sha(PROPOSAL),
        checked_distribution_files=len(checked), checked_distribution_pins=checked,
        missing=[], changed=[], native_processes_executed=0, compilation_performed=False,
    )
    output = HERE / "runtime-restoration.json"
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: receipt[k] for k in ("status", "compiler", "compiler_sha256", "checked_distribution_files")}))


if __name__ == "__main__":
    main()
