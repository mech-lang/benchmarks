#!/usr/bin/env python3
"""Frozen, sequential native output and full Map-update diagnostics; never timings."""
import argparse
from collections import Counter
import fcntl
import gzip
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHARED = ROOT / 'experiments/implementation-audit/remaining-v1'
LOCK = Path('/private/tmp/mech-clbg-timing.lock')
NODE = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
PACKAGES = SHARED / '.build/typescript/node_modules'
PROCESS = ROOT / 'experiments/elixir/rolling-v1/qualification-v1/native_process.py'
WIDTHS = [1, 2, 3, 4, 6, 12, 18]
SOURCES = {'rolling-parent': ROOT / 'experiments/typescript/rolling-map-v1/source/knucleotide.ts',
           **{name: HERE / 'source' / (name + '.ts') for name in
              ['readline-cells', 'buffer-numbers', 'buffer-cells']}}


def module(name, source):
    spec = importlib.util.spec_from_file_location(name, source)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


shared = module('typescript_bounded_reference', SHARED / 'native_bounded.py')
sha, write = shared.sha, shared.write


def cases():
    return dict(shared.nucleotide_cases(), **{
        'bare-cr': b'>ONE\rAAAA\r>THREE desc\rgGtA\r;comment\rct\r>NEXT\rTTTT',
        'header-eof': b'>THREE',
        'empty-target': b'>THREE\r\n>NEXT\r\nACGT',
        'comments-only': b'>THREE\n;ACGT\n;second comment',
        'last-line-eof': b'>THREE\nACGTGGTATTTTAATTTATAGT',
        'empty-lines': b'>THREE\n\nac\n\nGT\n\n',
        'wide-key-collisions': b'>THREE\n' + b'\n'.join([
            b'AAAAAAAAAAAAAAAAAA', b'CAAAAAAAAAAAAAAAAA',
            b'GAAAAAAAAAAAAAAAAA', b'TAAAAAAAAAAAAAAAAA', b'TTTTTTTTTTTTTTTTTT']),
        'ignored-non-ascii': '>ONE \u00e9\nnot DNA\n>THREE \u00e9\nACGT\n;\u00e9 comment\n>LAST\nnot DNA'.encode(),
    })


def bases(raw):
    """Independent line-record oracle, shared specification but no rolling packing."""
    selected = bytearray()
    active = False
    for line in re.split(br'\r\n|\r|\n', raw):
        if line.startswith(b';'):
            continue
        if active:
            if line.startswith(b'>'):
                break
            selected.extend(line.upper())
        elif line == b'>THREE' or line.startswith((b'>THREE ', b'>THREE\t')):
            active = True
    assert all(byte in b'ACGT' for byte in selected)
    return bytes(selected)


def expected_maps(sequence):
    result = []
    for width in WIDTHS:
        counts = Counter()
        events = []
        for start in range(max(0, len(sequence) - width + 1)):
            key = 0
            for byte in sequence[start:start + width]:
                key = key * 4 + b'ACGT'.index(byte)
            previous = counts[key]
            counts[key] += 1
            events.append([key, previous, counts[key]])
        result.append(dict(width=width, entries=sorted(map(list, counts.items())), events=events))
    return result


def check_witness(record, expected, cells):
    assert record['schema'] == 'typescript-complete-map-runtime-witness.v1'
    assert record['quantitative_benchmark'] is False
    assert len(record['maps']) == len(WIDTHS)
    for index, (actual, wanted) in enumerate(zip(record['maps'], expected)):
        assert actual['constructor_arguments'] == 0
        assert actual['entries'] == wanted['entries'], ('histogram', wanted['width'])
        assert actual['events'] == wanted['events'], ('updates', wanted['width'])
        occurrences = len(wanted['events'])
        assert actual['gets'] == occurrences + int(index >= 2)
        expected_sets = len(wanted['entries']) if cells else occurrences
        assert actual['sets'] == expected_sets
        assert actual['cell_updates'] == (occurrences - expected_sets if cells else 0)


def pins():
    files = [Path(__file__), HERE / 'map-witness.cjs', HERE / 'proposal.json', PROCESS, NODE,
             SHARED / 'native_bounded.py', ROOT / 'experiments/typescript/source-v1/tsconfig.json',
             *SOURCES.values()]
    files += [file for file in PACKAGES.rglob('*') if file.is_file() and not file.is_symlink()]
    return {str(file): sha(file) for file in sorted(set(files))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    plan_path = HERE / 'native-plan-v1.json'
    corpus = cases()
    rejected = {name: b'>THREE\nAC' + value + b'GT\n' for name, value in
                [('invalid-base', b'N'), ('invalid-space', b' '), ('invalid-utf8', b'\xff')]}
    if args.prepare:
        write(plan_path, dict(schema='typescript-input-map-native-plan.v1', pins=pins(),
            mutex_inode=LOCK.stat().st_ino, quantitative_benchmark=False,
            cases={name: __import__('hashlib').sha256(raw).hexdigest() for name, raw in corpus.items()},
            rejection_cases={name: __import__('hashlib').sha256(raw).hexdigest() for name, raw in rejected.items()},
            complete_work='Every ordered update and every final entry for all seven ordinary Maps.',
            diagnostic_boundary='Map subclass and cell proxies observe unchanged emitted JavaScript in separate untimed processes.',
            limits='120-second command deadline; sequential fresh processes; no quantitative timings or source-count approval.'))
        print(sha(plan_path), flush=True)
        return
    assert args.run and sha(plan_path) == args.plan_sha256
    plan = json.loads(plan_path.read_bytes())
    assert plan['pins'] == pins()
    output = HERE / 'native-v1'
    build = HERE / '.build/native-v1'
    output.mkdir(exist_ok=False)
    build.mkdir(parents=True, exist_ok=False)
    process = module('typescript_native_process', PROCESS)
    report = dict(schema='typescript-input-map-native-results.v1', status='running',
        plan_sha256=sha(plan_path), quantitative_benchmark=False,
        compilations=[], cases=[], rejections=[])
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
        env = dict(PATH='/opt/homebrew/bin:/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC', TMPDIR=str(build) + '/')

        def one(command, name, stdin=None, witness=None, allow_failure=False):
            assert os.fstat(lock.fileno()).st_ino == LOCK.stat().st_ino == plan['mutex_inode']
            environment = dict(env)
            if witness:
                environment['MECH_MAP_WITNESS'] = str(witness)
            row = process.one(list(map(str, command)), output / name, environment, build,
                              lock.fileno(), timeout=120, stdin=stdin)
            if not allow_failure:
                process.success(row)
                assert not (output / name / 'stderr.bin').read_bytes(), name
            return row

        try:
            one([NODE, '--version'], 'node-version')
            assert (output / 'node-version/stdout.bin').read_bytes() == b'v24.19.0\n'
            compiler = PACKAGES / '@typescript/typescript-darwin-arm64/lib/tsc'
            one([compiler, '--version'], 'typescript-version')
            assert (output / 'typescript-version/stdout.bin').read_bytes() == b'Version 7.0.2\n'
            config = json.loads((ROOT / 'experiments/typescript/source-v1/tsconfig.json').read_bytes())
            emitted = {}
            for label, source in SOURCES.items():
                project = build / label
                project.mkdir()
                shutil.copyfile(source, project / 'knucleotide.ts')
                write(project / 'tsconfig.json', dict(config, files=['knucleotide.ts']))
                one([compiler, '--project', project / 'tsconfig.json', '--typeRoots', PACKAGES / '@types',
                     '--pretty', 'false', '--listFiles', '--listEmittedFiles', '--incremental', 'false'], 'compile-' + label)
                emitted[label] = project / 'emitted/knucleotide.js'
                shutil.copyfile(emitted[label], output / (label + '.js'))
                report['compilations'].append(dict(label=label, source_sha256=sha(source),
                    emitted_sha256=sha(emitted[label]), config_sha256=sha(project / 'tsconfig.json')))
            for name, raw in corpus.items():
                inp = output / (name + '.stdin')
                expected = output / (name + '.expected')
                inp.write_bytes(raw)
                expected.write_bytes(shared.nucleotide_reference(raw))
                maps = expected_maps(bases(raw))
                for label, javascript in emitted.items():
                    for diagnostic in [False, True]:
                        capture = label + '-' + name + ('-work' if diagnostic else '-plain')
                        witness = output / (capture + '.maps.json.gz') if diagnostic else None
                        command = [NODE] + (['--require', HERE / 'map-witness.cjs'] if diagnostic else []) + [javascript]
                        one(command, capture, stdin=inp, witness=witness)
                        actual = output / capture / 'stdout.bin'
                        assert actual.read_bytes() == expected.read_bytes(), capture
                        if diagnostic:
                            check_witness(json.loads(gzip.decompress(witness.read_bytes())), maps, 'cells' in label)
                        report['cases'].append(dict(label=label, case=name, diagnostic=diagnostic,
                            complete_output_matches=True, complete_work_matches=True if diagnostic else None,
                            output_sha256=sha(actual), witness_sha256=sha(witness) if diagnostic else None,
                            map_count=7 if diagnostic else None,
                            total_updates=sum(len(row['events']) for row in maps) if diagnostic else None))
                print(json.dumps(dict(case=name, variants=4, output_checks=8, complete_map_checks=4)), flush=True)
            for name, raw in rejected.items():
                inp = output / (name + '.stdin')
                inp.write_bytes(raw)
                for label, javascript in emitted.items():
                    capture = label + '-' + name
                    row = one([NODE, javascript], capture, stdin=inp, allow_failure=True)
                    assert row['exit_code'] != 0 and not row['timed_out'] and not row['remaining_process_group']
                    assert b'Invalid nucleotide in THREE record' in (output / capture / 'stderr.bin').read_bytes()
                    assert not (output / capture / 'stdout.bin').read_bytes()
                    report['rejections'].append(dict(label=label, case=name, rejected=True))
            assert plan['pins'] == pins(), 'Pinned inputs changed during qualification'
            report.update(status='passed', output_checks=len(report['cases']),
                          complete_work_checks=sum(row['diagnostic'] for row in report['cases']),
                          rejection_checks=len(report['rejections']), source_counts_qualified=False,
                          chart_admission=False, timing_admission=False)
        except BaseException as error:
            report.update(status='failed', error=repr(error))
            raise
        finally:
            write(output / 'results.json', report)
    print(json.dumps({key: value for key, value in report.items() if key not in ['cases', 'compilations', 'rejections']}), flush=True)


if __name__ == '__main__':
    main()
