"""Qualify normalized source counts for the exact native candidate bundles."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN = Path('/private/tmp/mech-lean4-toolchain/lean-4.35.0-darwin_aarch64')
READER = ROOT / 'experiments/lean4/source-counts-v1/Reader.lean'
BASELINE = ROOT / 'experiments/lean4/source-counts-v1/qualification-v4'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def lean_count(record):
    source = Path(record['source'])
    raw = source.read_bytes()
    lines = set()
    for token in record['tokens']:
        start, end = token['start'], token['end']
        if start is None or end is None or start == end:
            continue
        assert isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(raw)
        lines.update(range(raw.count(b'\n', 0, start) + 1, raw.count(b'\n', 0, end - 1) + 2))
    owners = Counter(raw.count(b'\n', 0, item['start']) + 1 for item in record['do_statements'])
    expansions = [dict(line=line, extra_units=count - 1,
                       reason='Independent do statements sharing a physical line')
                  for line, count in sorted(owners.items()) if count > 1]
    return dict(path=str(source), sha256=sha(source), physical_loc=len(lines),
                canonical_loc=len(lines) + sum(item['extra_units'] for item in expansions),
                token_lines=sorted(lines), expansions=expansions,
                native_tokens=len(record['tokens']), native_do_statements=len(record['do_statements']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build_report.read_text())
    assert build['status'] == 'COMPILED_AWAITING_CONFORMANCE'
    assert all(sha(ROOT / name) == digest for name, digest in build['sources'].items())
    args.output.mkdir(parents=True, exist_ok=False)
    native = ROOT / 'experiments/lean4/.build/optimization-v1' / args.output.name
    native.mkdir(parents=True, exist_ok=False)
    source = Path(build['source_directory'])
    reference = json.loads((BASELINE / 'qualified-counts.json').read_text())
    assert sha(READER) == reference['reader_sha256']
    reader_source = args.output / 'reader'
    reader_source.mkdir()
    shutil.copyfile(READER, reader_source / 'Reader.lean')
    fixtures = args.output / 'fixtures'
    shutil.copytree(BASELINE / 'fixtures', fixtures)
    sdk = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip()
    commands = []

    def run(command, label, cwd):
        command = [str(value) for value in command]
        result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=300)
        (args.output / (label + '.stdout')).write_bytes(result.stdout)
        (args.output / (label + '.stderr')).write_bytes(result.stderr)
        commands.append(dict(command=command, cwd=str(cwd), exit_code=result.returncode))
        (args.output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            print(result.stdout.decode(errors='replace'))
            print(result.stderr.decode(errors='replace'))
            raise SystemExit(result.returncode)
        return result

    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run([TOOLCHAIN / 'bin/lean', '-j1', '-c', native / 'Reader.c', 'Reader.lean'], 'reader-lean', reader_source)
        run([TOOLCHAIN / 'bin/leanc', '-O3', '-mmacosx-version-min=14.4', '-isysroot', sdk,
             '-isystem', sdk + '/usr/include', '-o', native / 'reader', native / 'Reader.c'], 'reader-native', ROOT)
        inputs = sorted(source.glob('*.lean')) + sorted(fixtures.glob('*.lean'))
        result = run([native / 'reader', TOOLCHAIN, *[p.resolve() for p in inputs]], 'native-reader', ROOT)
        parsed = [json.loads(line) for line in result.stdout.decode().splitlines()]
        assert len(parsed) == len(inputs)
        counted = {Path(record['source']).name: lean_count(record) for record in parsed}
        expected = {'strings-comments': 3, 'packed-lets': 5, 'inline-for': 4,
                    'utf8-packed': 4, 'multiline-for': 4, 'block-comment': 2}
        for name, count in expected.items():
            assert counted[name + '.lean']['canonical_loc'] == count
        units = {name: row for name, row in counted.items() if (source / name).is_file()}
        for file in source.glob('*.c'):
            prior = reference['units'][file.name]
            assert sha(file) == prior['sha256'] == sha(prior['path'])
            units[file.name] = dict(prior, path=str(file),
                identical_source_count_evidence=dict(
                    report=str(BASELINE / 'qualified-counts.json'),
                    report_sha256=sha(BASELINE / 'qualified-counts.json'),
                    original_source=prior['path'], source_sha256=prior['sha256']))
        profiles = {}
        for benchmark, profile in build['profiles'].items():
            names = profile['files']
            assert set(names) <= set(units)
            assert set(profile['linked_native_helpers']) == {str(source / name) for name in names if name.endswith('.c')}
            profiles[benchmark] = dict(files=names,
                canonical_loc=sum(units[name]['canonical_loc'] for name in names),
                physical_loc=sum(units[name]['physical_loc'] for name in names), formatted_loc=None)
        report = dict(schema='lean-variant-normalized-source-counts.v1',
            status='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES', variant=build['variant'],
            build_report=str(args.build_report), build_report_sha256=sha(args.build_report),
            sources=build['sources'], controller_sha256=sha(__file__),
            reader_sha256=sha(READER), reader_binary_sha256=sha(native / 'reader'),
            fixtures_verified=6, units=units, profiles=profiles, benchmark_measurements=0,
            policy='Native lexical token ownership with independent do-statement expansion; every authored input compiled into each executable is counted. Byte-identical C helpers reuse their retained native Clang evidence. Standard Lean libraries and generated C are excluded.',
            formatted_loc_qualified=False)
        assert all(sha(ROOT / name) == digest for name, digest in build['sources'].items())
        (args.output / 'qualified-counts.json').write_text(json.dumps(report, indent=2) + '\n')
        shutil.copyfile(__file__, args.output / 'producer.py')
        print(json.dumps(profiles, indent=2))


if __name__ == '__main__':
    main()
