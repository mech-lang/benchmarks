#!/usr/bin/env python3
"""Verify and archive completed published-head correctness/process receipts."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

BENCHMARKS = Path('/private/tmp/benchmarks-native-consolidation')
CODE = BENCHMARKS / 'experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1'
DRIVERS = {
    'correctness': (Path('/private/tmp/native-final-correctness-driver-v1.py'), 'ca8743be72315fca351bf36419443c7138afc429697dd8f66bc0ed1d59264bf1'),
    'processes': (Path('/private/tmp/native-final-process-driver-v1.py'), '0474b9621ee4af8d9da23b28520de3e1ec41d4c618cdfedea6d24c2049c161d0'),
}
CACHES = {'target', 'cargo-target', 'maintained-hosted-runner-target'}
MACHO = {bytes.fromhex(value) for value in ['cffaedfe', 'cefaedfe', 'feedfacf', 'feedface', 'cafebabe', 'bebafeca']}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def source_state(workspace):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(workspace), *args], text=True).strip()
    return dict(commit=git('rev-parse', 'HEAD'), tree=git('rev-parse', 'HEAD^{tree}'), status=git('status', '--porcelain=v1', '--untracked-files=all'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=tuple(DRIVERS))
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    original, expected_driver = DRIVERS[args.mode]
    assert sha(original) == expected_driver
    src, dst = args.evidence.resolve(), args.destination.resolve()
    assert dst.is_relative_to(CODE.parent) and not dst.exists() and not src.is_relative_to(dst)
    context, complete, rows = (read(src / name) for name in ('context.json', 'complete.json', 'results.json'))
    source = source_state(args.workspace)
    assert source == context['source'] == complete['source'] and source['commit'] == args.head and not source['status']
    assert complete['head'] == args.head and complete['results_sha256'] == sha(src / 'results.json')
    assert context['driver_sha256'] == expected_driver and context['reuse_of_old_results'] is False
    assert complete['primary_timing_samples'] == context['primary_timing_samples'] == 0
    assert complete['stages'] == len(rows) == len({row['stage'] for row in rows})
    stage_owner = args.workspace / 'scripts/run-native-plan-stage.py'
    assert sha(stage_owner) == context['stage_owner_sha256']
    spec = importlib.util.spec_from_file_location('qualification_driver', original)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    substantive = rows
    if args.mode == 'correctness':
        assert complete['status'] == 'correctness-passed' and len(rows) == 51
        specs = driver.stage_specs(src)
        assert specs == context['stages']
    else:
        assert complete['status'] == 'all-sixteen-generated-process-scopes-qualified'
        substantive = read(src / 'process-results.json')
        assert complete['process_results_sha256'] == sha(src / 'process-results.json')
        assert len(substantive) == complete['substantive_stages'] == 16
        assert {row['stage'] for row in substantive} == set(driver.PROCESS_TESTS)
        assert substantive == [row for row in rows if row['stage'] in driver.PROCESS_TESTS]
    for i, row in enumerate(rows):
        name = row['stage']
        assert row['head'] == args.head and row['exit_code'] == row['wrapper_exit_code'] == 0
        assert row['source_before'] == row['source_after'] == source
        log, summary_path = src / (name + '.log'), src / (name + '.summary.json')
        assert sha(log) == row['log_sha256'] and sha(summary_path) == row['summary_sha256']
        summary = read(summary_path)
        assert summary['stage'] == name and summary['reason'] == 'exit'
        assert summary['command_exit_status'] == 0 and summary['owned_group_cleanup'] == 'complete'
        assert summary['timeout_seconds'] == int(row['wrapper'][row['wrapper'].index('--timeout-secs') + 1])
        counts = [list(map(int, match)) for match in re.findall(r'^test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored;', log.read_text(errors='replace'), re.M)]
        assert counts == row['counts']
        if args.mode == 'correctness':
            expected = specs[i]
            assert row['stage'] == expected['stage'] and row['command'] == expected['command']
            driver.validate_stage(expected, log.read_text(errors='replace'), summary, 0, source, source)
        elif name in driver.PROCESS_TESTS:
            assert sum(row[0] for row in counts) >= {'canonical-cli-unit-contracts': 5, 'canonical-cli-public-qualification': 3, 'canonical-policy-kernel': 13}.get(name, 1)
            assert all(row[0] > 0 and row[1] == 0 for row in counts)
            if name in driver.LINKED_PROCESS_TESTS:
                cmd = row['command']
                assert cmd.count('--exact') == cmd.count('--ignored') == 1 and '--list' not in cmd and '--no-run' not in cmd
                assert cmd[cmd.index('--exact') + 1] == driver.LINKED_PROCESS_TESTS[name] and counts == [[1, 0, 0]]
        if row.get('harness_pin'):
            pin = row['harness_pin']
            assert pin['source_commit'] == args.head and sha(pin['executable']) == pin['sha256']
    dst.mkdir(parents=True)
    preserved = CODE / '.build' / ('qualified-' + args.mode + '-' + args.head[:7])
    preserved.mkdir(exist_ok=False)
    binaries, records, excluded = {}, [], []

    def retain_binary(path):
        digest = sha(path)
        if digest not in binaries:
            target = preserved / digest
            shutil.copy2(path, target)
            assert sha(target) == digest
            binaries[digest] = dict(path=str(target), sha256=digest, bytes=target.stat().st_size, originals=[])
        binaries[digest]['originals'].append(str(path))

    def archive(original, relative):
        data = original.read_bytes()
        if relative != 'archive-driver.py' and not (relative.endswith('.o') or relative.endswith('.mecb')) and (data[:4] in MACHO or data.startswith(b'\x7fELF') or data.startswith(b'!<arch>')):
            retain_binary(original)
            return
        compress = relative.endswith('.log') or relative.endswith('.bin') and original.name in ('stdout.bin', 'stderr.bin') and len(data) > 65536
        name = relative + '.gz' if compress else relative
        target = dst / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(gzip.compress(data, mtime=0) if compress else data)
        assert (gzip.decompress(target.read_bytes()) if compress else target.read_bytes()) == data
        records.append(dict(original=str(original), source_relative=relative, archive_relative=name,
                            encoding='gzip' if compress else 'identity', raw_sha256=hashlib.sha256(data).hexdigest(),
                            archive_sha256=sha(target), raw_bytes=len(data), archive_bytes=target.stat().st_size))

    for current, dirs, names in os.walk(src):
        for name in list(dirs):
            path = Path(current) / name
            if name in CACHES or name.endswith('-target') or path.is_symlink():
                excluded.append(str(path))
                dirs.remove(name)
        for name in sorted(names):
            path = Path(current) / name
            assert not path.is_symlink()
            archive(path, str(path.relative_to(src)))
    archive(original, 'executed-driver.py')
    archive(stage_owner, 'bounded-stage-owner.py')
    archive(Path(__file__), 'archive-driver.py')
    for row in rows:
        if row.get('harness_pin'):
            retain_binary(Path(row['harness_pin']['executable']))
    save(dst / 'local-binary-preservation.json', dict(scope='Exact qualification harnesses/generated binaries retained outside rebuildable Cargo caches; these are not primary timing subjects', binaries=list(binaries.values())))
    assert source_state(args.workspace) == source
    manifest = dict(schema='mech.published-qualification-archive.v1', mode=args.mode, status='passed', source=source,
                    original_evidence=str(src), stages=len(rows), substantive_stages=len(substantive),
                    executed_driver_sha256=expected_driver, archive_driver_sha256=sha(__file__),
                    tests=dict(passed=sum(int(c[0]) for row in substantive for c in row['counts']),
                               failed=sum(int(c[1]) for row in substantive for c in row['counts']),
                               ignored=sum(int(c[2]) for row in substantive for c in row['counts'])),
                    files=records, excluded_rebuildable_cache_directories=excluded,
                    preserved_local_binaries=len(binaries), primary_timing_samples=0, performance_qualified=False)
    save(dst / 'archive-manifest.json', manifest)
    print(json.dumps({key:manifest[key] for key in ['status','mode','source','stages','substantive_stages','tests','preserved_local_binaries']},indent=2))


if __name__ == '__main__':
    main()
