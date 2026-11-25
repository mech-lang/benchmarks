"""Download the twelve pinned full Silesia inputs."""
from argparse import ArgumentParser
from hashlib import file_digest
from pathlib import Path
from shutil import copyfileobj
from subprocess import run
from zipfile import ZipFile
import json
import re


MIRROR = "https://raw.githubusercontent.com/MiloszKrajewski/SilesiaCorpus/3f3fa2cdbbb3795c903b74e774acb309e1360337"


def digest(path):
    with path.open("rb") as content:
        return file_digest(content, "sha256").hexdigest()


parser = ArgumentParser(description=__doc__)
parser.add_argument("pins", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--manifest", action="store_true", help="Use the published corpus.json as the input pins")
args = parser.parse_args()

pin_bytes = args.pins.read_bytes()
manifest = json.loads(pin_bytes) if args.manifest else None
if manifest is None:
    content = pin_bytes.decode()
    mirror, = re.findall(r'^mirror = "([^"]+)"', content, re.M)
    pins = re.findall(r'{ name: "([a-z-]+)", sha: "([0-9a-f]{64})" }', content)
else:
    mirror = MIRROR
    pins = [(name, row["zip_sha256"]) for name, row in manifest["files"].items()]
    assert all(re.fullmatch(r"[a-z-]+", name) and re.fullmatch(r"[0-9a-f]{64}", sha)
               for name, sha in pins)
assert len(pins) == len(dict(pins)) == 12
output = args.output
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
    if manifest is not None:
        assert records[name] == manifest["files"][name], name
    zipped.unlink()
    print(name, entry.file_size, records[name]["sha256"], flush=True)
assert sum(row["bytes"] for row in records.values()) == 211_938_580
if manifest is None:
    (output / "corpus.json").write_text(
        json.dumps({"pins_sha256": digest(args.pins), "files": records}, indent=2) + "\n")
else:
    (output / "corpus.json").write_bytes(pin_bytes)
