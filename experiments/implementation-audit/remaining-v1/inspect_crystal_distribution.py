#!/usr/bin/env python3
"""Inventory the checksum-verified extraction, retaining platform symlink loops."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
target = HERE / ".build/crystal"
distribution = target / "distribution"
archive = target / "crystal-1.21.1-1-darwin-universal.tar.gz"
expected = "ba34fa7fb8bc8b951f12d17e12f69c9d7ccce38900caa4b8a17f1b4f29d37605"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
prior = HERE / "crystal-restore.json"
assert json.loads(prior.read_bytes())["status"] == "failed"
files = {}
for path in sorted(distribution.rglob("*")):
    key = str(path.relative_to(distribution))
    if path.is_symlink():
        link = str(path.readlink())
        lexical_target = Path(os.path.normpath(path.parent / link))
        assert not os.path.isabs(link) and lexical_target.is_relative_to(distribution)
        files[key] = {"symlink": link, "followed": False}
    elif path.is_file():
        files[key] = {"bytes": path.stat().st_size,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
result = {
    "schema": "crystal-retained-distribution-inventory.v2",
    "status": "restored-no-native-execution",
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "archive_sha256": expected,
    "prior_failed_receipt": {"path": prior.name, "sha256": hashlib.sha256(prior.read_bytes()).hexdigest()},
    "inventory_method": "Regular files hashed; symlink text retained without resolving platform-specific loops.",
    "extractor_boundary": "Original Python tarfile data filter; exact official release archive checksum verified again.",
    "native_processes_started": 0,
    "files": files,
}
output = HERE / "crystal-restore-v2.json"
with output.open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps({k: v for k, v in result.items() if k != "files"}))
