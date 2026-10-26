"""Normalize generated SVG line endings and refresh artifact hashes."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    folder = parser.parse_args().media
    manifest_path = folder / "animation.json"
    manifest = json.loads(manifest_path.read_text())
    for name in ["mech-compiler-optimization.svg", "mech-compiler-optimization-frame.svg"]:
        path = folder / name
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        manifest["artifacts"][name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                       "bytes": path.stat().st_size}
    manifest["svg_normalization_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
