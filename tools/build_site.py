#!/usr/bin/env python3
"""Build the static explorer from its editable source and recorded dataset."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build():
    source = ROOT / 'site/src'
    output = ROOT / 'site/public'
    dataset = ROOT / 'data/benchmarks.json'
    inputs = sorted(source.iterdir()) + [dataset]
    digest = hashlib.sha256()
    for path in inputs:
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    version = digest.hexdigest()[:16]
    output.mkdir(parents=True, exist_ok=True)
    for path in source.iterdir():
        if not path.is_file():
            continue
        if path.suffix in {'.html', '.mjs'}:
            text = path.read_text()
            text = re.sub(r"(\./[A-Za-z0-9_.-]+\.(?:mjs|css))(?:\?v=[A-Za-z0-9_.-]+)?", lambda m: m[1] + '?v=' + version, text)
            (output / path.name).write_text(text)
        else:
            shutil.copyfile(path, output / path.name)
    for path in (ROOT / 'site/reports').iterdir():
        if path.is_file():
            shutil.copyfile(path, output / path.name)
    shutil.copyfile(dataset, output / 'data.json')
    manifest = {'version': version, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.iterdir()) if p.is_file() and p.name != 'build.json'}}
    (output / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Built site/public ({len(manifest["files"])} files, {version})')
    return output


if __name__ == '__main__':
    build()
