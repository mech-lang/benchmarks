#!/usr/bin/env python3
"""Prepare or archive the unchanged public wide-slot runner at published heads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path('/private/tmp/benchmarks-native-consolidation')
CODE = ROOT / 'experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1'
OLD = Path('/private/tmp/native-wide-slot-supplement-v1')
PREP = Path('/private/tmp/native-wide-slot-published-protocol-v1')
RAW = Path('/private/tmp/native-wide-slot-published-heads-v1')
ARCHIVE = CODE / 'supplemental-wide-slot-published-v1'
SUBJECTS = {
    'I': ('a093aea452340a70c1e72a1f58bd831f1edef70f',
          '/private/tmp/mech-native-base-ci-repair-next', CODE / 'baseline-builds/published-a093aea-v1/public-aot.json'),
    'A': ('7543c56d5efc4df30d0b60961922024d74caa9d7',
          '/private/tmp/mech-native-consolidation-final', CODE / 'candidate-builds/published-7543c56-v1/public-aot.json'),
    'C': ('a68fb2e60d7afbc59bc146f8878b17181e275645',
          '/private/tmp/mech-post-native-authority-cleanup-v2',
          CODE.parent / 'post-native-architecture-cleanup-v1/candidate-builds/published-a68fb2e-v1/public-aot.json'),
}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(workspace):
    def git(*args):
        return subprocess.check_output(['git', '-C', workspace, *args], text=True).strip()
    return dict(commit=git('rev-parse', 'HEAD'), tree=git('rev-parse', 'HEAD^{tree}'),
                status=git('status', '--porcelain=v1'))


def prepare():
    complete = read(Path('/private/tmp/native-published-public-builds-v1/complete.json'))
    assert complete['status'] == 'three-published-head-public-builds-validated-six-guest-artifacts-identical'
    assert complete['primary_timing_samples'] == 0
    assert not PREP.exists()
    protocol = read(OLD / 'protocol.json')
    assert sha(OLD / 'run.py') == protocol['runner_sha256']
    assert sha(OLD / 'wide-packed-slots.mec') == protocol['fixture']['sha256']
    for name, (head, workspace, path) in SUBJECTS.items():
        receipt = read(path)
        validation = read(path.parent / 'adoption-validation.json')
        assert receipt['source'] == state(workspace) and receipt['source']['commit'] == head
        assert not receipt['source']['status'] and receipt['workspace'] == workspace
        assert validation['source'] == receipt['source']
        assert validation['receipt_sha256'] == sha(path)
        assert validation['guest_artifacts'] == complete['guest_artifacts']
        subject = protocol['subjects'][name]
        subject.update(commit=head, workspace=workspace, receipt=str(path.relative_to(ROOT)),
                       receipt_sha256=sha(path), compiler_sha256=receipt['compiler_sha256'])
        subject['source_contract_pins'] = {name: sha(Path(workspace) / name)
                                           for name in subject['source_contract_pins']}
    protocol.update(prepared_utc=datetime.now(timezone.utc).isoformat(), status='ready',
                    destination_recommendation=str(ARCHIVE.relative_to(ROOT)),
                    previous_protocol_sha256=sha(OLD / 'protocol.json'))
    protocol['readiness'] = dict(public_builds_independently_validated=True,
                                 public_target_released_by_owner=True,
                                 shared_mutex_released_by_owner=True,
                                 runner='Unchanged reviewed runner; only published source/build pins adopted.')
    PREP.mkdir()
    for name in ('run.py', 'wide-packed-slots.mec'):
        shutil.copyfile(OLD / name, PREP / name)
    (PREP / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    shutil.copyfile(__file__, PREP / 'preparation-driver.py')
    print(json.dumps(dict(protocol=str(PREP / 'protocol.json'), sha256=sha(PREP / 'protocol.json'),
                          runner_sha256=sha(PREP / 'run.py'), primary_timing_samples=0), indent=2))


def archive():
    report = read(RAW / 'result.json')
    assert report['status'] == 'passed-six-public-builds-wide-guest-artifacts-identical'
    assert [(r['subject'], r['route']) for r in report['builds']] == [
        (name, route) for name in 'IAC' for route in ('source', 'decoded')]
    assert not ARCHIVE.exists()
    ARCHIVE.mkdir()
    files = []

    def copy(source, relative):
        destination = ARCHIVE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert source.is_file() and not source.is_symlink()
        shutil.copyfile(source, destination)
        assert sha(source) == sha(destination)
        files.append(dict(original=str(source), path=str(relative), sha256=sha(source)))

    for name in ('result.json', 'prospective-protocol.json', 'executed-runner.py', 'fixture.mec'):
        copy(RAW / name, Path(name))
    for row in report['builds']:
        subject, route = row['subject'], row['route']
        raw = RAW / subject / route
        binary = raw / 'native-wide-slot-evidence'
        assert row['command'][-1] == str(binary)
        for name, digest in row['guest_artifacts'].items():
            source = Path(str(binary) + '.project') / name
            assert sha(source) == digest
            copy(source, Path('artifacts') / subject / route / name)
        copy(raw / 'aot-build/process.json', Path('processes') / subject / route / 'aot.json')
        for name in ('process.json', 'stdout.bin', 'stderr.bin'):
            copy(raw / 'disassembly' / name, Path('processes') / subject / route / 'disassembly' / name)
    for subject in 'IAC':
        copy(RAW / subject / 'cache-provenance.json', Path('cache') / subject / 'provenance.json')
        for stage in ('metadata', 'clean'):
            for name in ('process.json', 'stdout.bin', 'stderr.bin'):
                copy(RAW / subject / stage / name, Path('cache') / subject / stage / name)
    copy(Path(__file__), Path('archive-driver.py'))
    (ARCHIVE / 'archive-manifest.json').write_text(json.dumps(dict(
        files=files, raw_result_sha256=sha(RAW / 'result.json'),
        performance_qualified=False, primary_timing_samples=0), indent=2) + '\n')
    sys.path.insert(0, str(CODE))
    old_argv = sys.argv
    sys.argv = [__file__]
    import wide_slot
    sys.argv = old_argv
    ref = dict(study_id=CODE.name, path=str((ARCHIVE / 'result.json').relative_to(CODE)),
               sha256=sha(ARCHIVE / 'result.json'))
    assert wide_slot.check(ref, read(SUBJECTS['A'][2]), read(SUBJECTS['I'][2]))
    print(json.dumps(dict(reference=ref, archived_files=len(files), primary_timing_samples=0), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'archive'))
    args = parser.parse_args()
    (prepare if args.mode == 'prepare' else archive)()
