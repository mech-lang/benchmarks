#!/usr/bin/env python3
"""Verify frozen bytes and Git blob identities, optionally against pinned Mech."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def verify(mech=None):
    manifest = json.loads((HERE / "manifest.json").read_text())
    seen = set()
    for row in manifest["files"]:
        relative = Path(row["archive_path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        path = ROOT / relative
        assert path.is_relative_to(HERE / "source")
        assert relative not in seen, f"duplicate archive path: {relative}"
        seen.add(relative)
        data = path.read_bytes()
        assert len(data) == row["byte_size"], relative
        assert hashlib.sha256(data).hexdigest() == row["sha256"], relative
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        assert blob == row["git_blob"], relative
        assert row["source_commit"] == manifest["source_commit"]
        assert row["original_repository"] == "https://github.com/mech-lang/mech"
        original = row["original_path"].removeprefix("mech-lang/mech/")
        assert original != row["original_path"]
        if mech:
            expected = subprocess.check_output(
                ["git", "show", f'{row["source_commit"]}:{original}'], cwd=mech
            )
            assert data == expected, relative
    actual = {p.relative_to(ROOT) for p in (HERE / "source").rglob("*") if p.is_file()}
    assert actual == seen, "manifest does not cover the exact archived source set"
    receipts = [r for r in manifest["files"] if r["classification"] == "historical-receipt"]
    assert len(receipts) == 78
    return len(seen)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", type=Path)
    args = parser.parse_args()
    print(f"Verified {verify(args.mech)} archived files, including all 78 receipts")
