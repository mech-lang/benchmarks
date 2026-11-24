"""Replay the published Silesia timing matrix with hash-pinned arm64 actors."""
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
import platform
import sys

from silesia_compare import digest, read, save


parser = ArgumentParser(__doc__)
parser.add_argument("--corpus", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
assert platform.system() == "Darwin" and platform.machine() == "arm64"
here = Path(__file__).resolve().parent
assert read(args.corpus / "corpus.json") == read(here / "corpus.json")
binding = read(here / "binding.json")
for name, row in binding["actors"].items():
    path = here / "actors" / name
    assert digest(path) == row["sha256"]
    row["path"] = str(path)
args.output.mkdir(parents=True)
save(args.output / "binding.json", binding)
run([sys.executable, str(here / "silesia_compare.py"), "time", "--corpus", str(args.corpus),
     "--builds", str(here), "--output", str(args.output)], check=True)
