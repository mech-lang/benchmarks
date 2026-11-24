"""Download only the full Silesia inputs pinned by Feldman's benchmark."""
from hashlib import file_digest
from pathlib import Path
from shutil import copyfileobj
from subprocess import run
from zipfile import ZipFile
import json
import re
import sys


def digest(path):
    with path.open("rb") as content:
        return file_digest(content, "sha256").hexdigest()


pin_source, output = map(Path, sys.argv[1:])
text = pin_source.read_text()
mirror, = re.findall(r'^mirror = "([^"]+)"', text, re.M)
pins = re.findall(r'{ name: "([a-z-]+)", sha: "([0-9a-f]{64})" }', text)
assert len(pins) == len(dict(pins)) == 12
output.mkdir(exist_ok=True)
records = {}
for name, checksum in pins:
    zipped = output / (name + ".zip")
    command = ["curl", "-fsSL", "--retry", "3", "--connect-timeout", "10", "--max-time", "90",
               "--output", str(zipped), mirror + "/" + name + ".zip"]
    run(command, check=True)
    assert digest(zipped) == checksum, name
    path = output / name
    with ZipFile(zipped) as archive:
        entry, = [info for info in archive.infolist() if info.filename == name]
        with archive.open(entry) as source, path.open("wb") as target:
            copyfileobj(source, target, 1 << 20)
        assert path.stat().st_size == entry.file_size
    records[name] = {"bytes": entry.file_size, "sha256": digest(path), "zip_sha256": checksum}
    zipped.unlink()
    print(name, entry.file_size, records[name]["sha256"], flush=True)
assert sum(row["bytes"] for row in records.values()) == 211_938_580
(output / "corpus.json").write_text(json.dumps({"pins_sha256": digest(pin_source), "files": records}, indent=2) + "\n")
