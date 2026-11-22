#!/usr/bin/env python3
"""Verify the original PR 992 blobs and pinned reconstruction inputs."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    records = manifest["records"]
    assert len(records) == manifest["file_count"] == 14
    assert sum(record["bytes"] for record in records) == manifest["total_bytes"]
    assert sum(record["changed_from_base"] for record in records) == 5
    assert manifest["changed_file_count"] == 5
    destinations = set()
    for record in records:
        path = (ROOT / record["destination"]).resolve()
        path.relative_to(HERE / "source")
        assert path not in destinations, f"duplicate destination: {path}"
        destinations.add(path)
        data = path.read_bytes()
        assert len(data) == record["bytes"], f"byte count differs: {path}"
        assert hashlib.sha256(data).hexdigest() == record["sha256"], path
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        assert hashlib.sha1(blob).hexdigest() == record["git_blob"], path
        if path.suffix == ".py":
            compile(data, str(path), "exec")
    assert destinations == {path.resolve() for path in (HERE / "source").rglob("*")
                            if path.is_file()}, "archive file inventory differs"
    recipe_dir = HERE / "source/benchmarks/mech-deflate/native-profile/compact-size"
    recipe = json.loads((recipe_dir / "recipe.json").read_text())
    for name, expected in recipe["fixture_sha256"].items():
        path = recipe_dir / "fixtures" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    assert recipe["fixture_sha256"]["metadata.json"] == recipe["exact_metadata_sha256"]
    print(f"Verified {len(records)} original Git blobs and all pinned recipe inputs.")


if __name__ == "__main__":
    main()
