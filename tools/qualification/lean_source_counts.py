"""Native lexical source counts and packed statement expansion for Lean bundles."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/lean4/source-counts-v1'
SOURCE = ROOT / 'experiments/lean4/source-v1'
TOOLCHAIN = Path('/private/tmp/mech-lean4-toolchain/lean-4.35.0-darwin_aarch64')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    build = ROOT / 'experiments/lean4/.build/source-counts'
    build.mkdir(exist_ok=True)
    sdk = subprocess.check_output(['/usr/bin/xcrun', '--show-sdk-path'], text=True).strip()
    commands = []

    def run(command, name, cwd=ROOT):
        command = [str(x) for x in command]
        result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=180)
        (args.output / (name + '.stdout')).write_bytes(result.stdout)
        (args.output / (name + '.stderr')).write_bytes(result.stderr)
        commands.append(dict(command=command, cwd=str(cwd), exit_code=result.returncode))
        (args.output / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            print(result.stdout.decode(errors='replace'))
            print(result.stderr.decode(errors='replace')[-6000:])
            raise SystemExit(result.returncode)
        return result

    run([TOOLCHAIN / 'bin/lean', '-j1', '-o', build / 'Reader.olean', '-c', build / 'Reader.c', 'Reader.lean'], 'reader-lean', HERE)
    run([TOOLCHAIN / 'bin/leanc', '-O3', '-mmacosx-version-min=14.4', '-isysroot', sdk,
         '-isystem', sdk + '/usr/include', '-o', build / 'reader', build / 'Reader.c'], 'reader-native')
    fixtures = {
        'strings-comments': ('import Std\n-- ignored\ndef value : String :=\n  "a; -- b /- c -/"\n/- block\nignored -/\n', 3),
        'packed-lets': ('import Std\ndef action : IO Unit := do\n  let x := 1; let y := 2\n  IO.println (x+y)\n', 5),
        'inline-for': ('import Std\ndef action : IO Unit := do\n  for i in [:2] do IO.println i\n', 4),
        'utf8-packed': ('import Std\ndef action : IO Unit := do\n  IO.println "λ--"; IO.println "漢/-"\n', 4),
        'multiline-for': ('import Std\ndef action : IO Unit := do\n  for i in [:2] do\n    IO.println i\n', 4),
        'block-comment': ('import Std\n/- a block\nignored -/\ndef n := 1 -- suffix\n', 2),
    }
    fixture_dir = args.output / 'fixtures'
    fixture_dir.mkdir()
    for name, (text, _) in fixtures.items():
        (fixture_dir / (name + '.lean')).write_text(text)
    files = sorted(SOURCE.glob('*.lean')) + sorted(fixture_dir.glob('*.lean'))
    result = run([build / 'reader', TOOLCHAIN, *files], 'native-reader')
    parsed = [json.loads(line) for line in result.stdout.decode().splitlines()]
    assert len(parsed) == len(files) and {p['source'] for p in parsed} == {str(p) for p in files}

    def count_lean(record):
        path = Path(record['source'])
        raw = path.read_bytes()
        lines = set()
        for token in record['tokens']:
            start, end = token['start'], token['end']
            if start is None or end is None or start == end:
                continue
            assert isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(raw)
            lines.update(range(raw.count(b'\n', 0, start) + 1, raw.count(b'\n', 0, end - 1) + 2))
        owners = collections.Counter(raw.count(b'\n', 0, s['start']) + 1 for s in record['do_statements'])
        expansions = [dict(line=line, extra_units=count - 1, reason='Independent do statements sharing a physical line')
                      for line, count in sorted(owners.items()) if count > 1]
        return dict(path=str(path), sha256=sha(path), physical_loc=len(lines),
                    canonical_loc=len(lines) + sum(e['extra_units'] for e in expansions),
                    token_lines=sorted(lines), expansions=expansions,
                    native_tokens=len(record['tokens']), native_do_statements=len(record['do_statements']))

    counted = {Path(row['source']).name: count_lean(row) for row in parsed}
    for name, (_, expected) in fixtures.items():
        actual = counted[name + '.lean']['canonical_loc']
        assert actual == expected, (name, expected, actual, counted[name + '.lean'])
    for name in ['Format.c', 'Regex.c']:
        path = SOURCE / name
        result = run([TOOLCHAIN / 'bin/clang', '-fsyntax-only', '-Xclang', '-dump-tokens',
                      '-isysroot', sdk, '-isystem', sdk + '/usr/include', '-isystem', TOOLCHAIN / 'include/clang',
                      '-I' + str(TOOLCHAIN / 'include'), '-I/opt/homebrew/opt/pcre2/include', path], name + '-tokens')
        byline = collections.defaultdict(list)
        for line in result.stderr.decode().splitlines():
            match = re.match(r"(\w+) .*Loc=<" + re.escape(str(path)) + r':(\d+):(\d+)', line)
            if match and match[1] != 'eof':
                byline[int(match[2])].append(match[1])
        text = path.read_text().splitlines()
        lines = set(byline) | {i + 1 for i, line in enumerate(text) if line.lstrip().startswith('#')}
        assert lines
        expansions = [dict(line=line, extra_units=1, reason='Native if token and its same-line body statement')
                      for line, tokens in sorted(byline.items()) if 'if' in tokens and 'semi' in tokens]
        counted[name] = dict(path=str(path), sha256=sha(path), physical_loc=len(lines),
                             canonical_loc=len(lines) + len(expansions), token_lines=sorted(lines), expansions=expansions)
    source_units = {name: value for name, value in counted.items() if (SOURCE / name).is_file()}
    profiles = {}
    for path in sorted(SOURCE.glob('*.lean')):
        if path.name == 'Common.lean':
            continue
        units = [path.name, 'Common.lean', 'Format.c'] + (['Regex.c'] if path.stem == 'regexredux' else [])
        profiles[path.stem] = dict(files=units, canonical_loc=sum(source_units[n]['canonical_loc'] for n in units),
                                   physical_loc=sum(source_units[n]['physical_loc'] for n in units), formatted_loc=None)
    report = dict(schema='lean-canonical-source-counts.v1', status='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES',
                  policy='Count source lines owning native lexical tokens, excluding comments and blanks; expand packed independent do statements and same-line C control bodies. Count every authored helper compilation unit in each retained bundle.',
                  reader_sha256=sha(HERE / 'Reader.lean'), controller_sha256=sha(__file__),
                  fixtures_verified=len(fixtures), units=source_units, profiles=profiles,
                  formatted_loc_qualified=False, benchmark_measurements=0,
                  helper_scope='Common.lean and Format.c are authored inputs to all ten builds and counted in full; Regex.c is additionally counted for regex-redux. General Lean/PCRE2 libraries and compiler-generated C are excluded.')
    assert len(profiles) == 10
    (args.output / 'qualified-counts.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(profiles, indent=2))


if __name__ == '__main__':
    main()
