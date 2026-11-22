#!/usr/bin/env python3
"""Verify the relocated PR 973 records without compiling or measuring anything."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def verify(path, record):
    data = path.read_bytes()
    if len(data) != record["bytes"]:
        raise ValueError(f"byte count differs: {path}")
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"SHA-256 differs: {path}")
    if "git_blob" in record:
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        if hashlib.sha1(blob).hexdigest() != record["git_blob"]:
            raise ValueError(f"original Git blob differs: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true",
                        help="download any missing pinned release assets")
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    assets = {entry["name"]: entry for entry in manifest["assets"]}
    if len(assets) != len(manifest["assets"]):
        raise ValueError("duplicate release asset")
    args.asset_dir.mkdir(parents=True, exist_ok=True)
    for name, asset in assets.items():
        if Path(name).name != name:
            raise ValueError(f"invalid asset name: {name}")
        path = args.asset_dir / name
        if not path.exists() and args.download:
            temporary = path.with_suffix(path.suffix + ".partial")
            subprocess.run(["curl", "--fail", "--location", "--silent",
                            "--show-error", asset["url"], "--output", str(temporary)],
                           check=True)
            verify(temporary, asset)
            temporary.replace(path)
        verify(path, asset)
    seen = set()
    for record in manifest["files"]:
        original = record["source_path"]
        if original in seen:
            raise ValueError(f"duplicate source path: {original}")
        seen.add(original)
        if "destination_path" in record:
            path = (ROOT / record["destination_path"]).resolve()
            if not path.is_relative_to(HERE / "source"):
                raise ValueError(f"destination escapes snapshot: {original}")
        else:
            name = record["release_asset"]
            if name not in assets:
                raise ValueError(f"missing asset mapping: {original}")
            path = args.asset_dir / name
        verify(path, record)
    summary = manifest["summary"]
    if len(seen) != summary["files"]:
        raise ValueError("source inventory count differs")
    print(f"Verified {len(seen):,} original files, "
          f"{summary['source_bytes']:,} bytes, and {len(assets)} release assets.")


if __name__ == "__main__":
    main()
