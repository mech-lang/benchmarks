#!/usr/bin/env python3
"""Secondary prefix diagnostic after both maintained primary campaigns complete."""
import fcntl
import hashlib
import math
import statistics
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from study import (HERE, ROOT, STUDY_ID, STUDY_IDS, process, read, read_plan,
                   source_state, inputs, runtime_environment, build_receipt_path)
from campaign import prerequisites

BLOCK = [['F', 'I', 'R', 'W'], ['I', 'W', 'F', 'R'],
         ['W', 'R', 'I', 'F'], ['R', 'F', 'W', 'I']]


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def native_counters(path, protocol, policy):
    report = read(path)
    for key, expected in protocol['native_checks']['required_flags'].items():
        require(type(report[key]) is type(expected) and report[key] == expected, key)
    for key, expected in protocol['native_checks']['exact_counters'].items():
        require(type(report[key]) is int and report[key] == expected, key)
    for key, cap in [('native_work', policy['work']),
                     ('native_comparison_work', policy['library']['comparison_work'])]:
        require(type(report[key]) is int and 0 < report[key] <= cap, key)
    require(type(report['native_parallel_peak_workers']) is int and
            1 <= report['native_parallel_peak_workers'] <= 7, 'Peak workers')
    claims = report['native_worker_credit_claims']
    require(type(claims) is int and claims > 0 and
            type(report['native_worker_credit_reclaims']) is int and
            claims == report['native_worker_credit_reclaims'], 'Credit reconciliation')
    return report


def main():
    require(len(sys.argv) == 1, 'Only shared --study is accepted')
    plan = read_plan()
    targets, pins, final, initial = prerequisites(plan)
    protocol_path = HERE / 'secondary-prefix-protocol.json'
    protocol = read(protocol_path)
    require(protocol['study_id'] == STUDY_ID and protocol['orders'] == BLOCK,
            'Unexpected diagnostic schedule')
    require(protocol['observations'] == 16 and protocol['warmups'] == 0 and
            protocol['excluded_outliers'] == 0 and protocol['replacement_samples'] == 0,
            'Unexpected diagnostic observation policy')
    require(protocol['subject_pins'] == pins, 'Diagnostic and primary binaries differ')
    require(protocol['performance_qualified'] is False, 'Diagnostic cannot qualify performance')
    require(protocol['deadline_seconds'] == 30, 'Diagnostic process deadline changed')
    git = lambda *a: subprocess.check_output(['git', '-C', str(ROOT), *a], text=True).strip()
    revision = git('rev-parse', 'HEAD')
    require(not git('status', '--porcelain'), 'Evidence repository must be committed')
    paths = [protocol_path, Path(__file__).resolve()]
    for path in paths:
        require(path.is_relative_to(ROOT), 'Adopt the diagnostic in the evidence repository first')
        blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + str(path.relative_to(ROOT))])
        require(hashlib.sha256(blob).hexdigest() == process.sha(path), 'Uncommitted diagnostic input')
    # Reuse the primary evidence validator in a fresh, explicitly selected module
    # context for each study. This checks all raw observations, not just a summary.
    validation = ('from study import HERE,read,read_plan;from campaign import validate_reports;'
                  'validate_reports([read(HERE/f"primary-session-{n}/results.json") for n in (1,2)],read_plan())')
    validations, primary_pins = [], {}
    for study_id in STUDY_IDS:
        command = [sys.executable, '-c', validation, '--study', study_id]
        completed = subprocess.run(command, cwd=CODE, check=True, text=True, capture_output=True)
        validations.append(dict(study_id=study_id, command=command, exit_status=completed.returncode,
                                stdout=completed.stdout, stderr=completed.stderr))
        for session in (1, 2):
            for path in sorted((CODE.parent / study_id / f'primary-session-{session}').rglob('*')):
                if path.is_file():
                    require(not path.is_symlink(), 'Primary evidence cannot be a symbolic link')
                    primary_pins[str(path.relative_to(ROOT))] = process.sha(path)
    inp = Path(protocol['input']['path'])
    expected = Path(protocol['expected_output']['path'])
    _, policy_path, _ = inputs()
    for key, path in [('input', inp), ('expected_output', expected), ('policy', policy_path)]:
        require(process.sha(path) == protocol[key]['sha256'], key + ' pin differs')
    require(inp.stat().st_size == protocol['input']['bytes'], 'Prefix size differs')
    env = runtime_environment(plan)
    policy = read(policy_path)
    source_before = {label: source_state(Path(receipt['workspace']))
                     for label, receipt in [('F', final), ('I', initial)]}
    receipts = [build_receipt_path(plan['candidate_receipt']),
                build_receipt_path(plan['baseline_receipt'], shared=True),
                build_receipt_path(plan['runtime_environment_receipt'], shared=True)]
    held = {str(p): process.sha(p) for p in [*paths, *receipts, HERE / 'plan.json',
            HERE / 'retained-controls.json', inp, expected, policy_path,
            ROOT / 'tools/qualification/prolog_supervisor.py']}
    held.update({str(ROOT / name): digest for name, digest in plan['controller_pins'].items()})
    mutex = Path(plan['common_mutex'])
    require(mutex.is_file() and mutex.stat().st_ino == 83858837, 'Shared mutex changed')
    out = HERE / 'secondary-prefix-v1'
    out.mkdir(exist_ok=False)
    report = dict(status='prepared', study_id=STUDY_ID, evidence_revision=revision,
                  source=source_before, pins=pins, protocol_sha256=process.sha(protocol_path),
                  runtime_environment=env, input_pins=held, primary_validations=validations,
                  primary_evidence_sha256=primary_pins,
                  scope='Descriptive prefix observations; separate from primary acceptance.',
                  performance_qualified=False, primary_samples=0, samples=[],
                  executable_size_bytes={s: p.stat().st_size for s, p in targets.items()})
    process.save(out / 'results.json', report)
    identities = set()
    try:
        with mutex.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            for order, subjects in enumerate(BLOCK):
                for position, subject in enumerate(subjects):
                    require(all(process.sha(targets[s]) == pins[s] for s in targets), 'Executable drift')
                    require(all(process.sha(Path(p)) == h for p, h in held.items()), 'Diagnostic protocol drift')
                    folder = out / f'{order:02d}-{position}-{subject}'
                    native = out / (folder.name + '.native.json')
                    command = [str(targets[subject])] + ([] if subject == 'R' else [str(policy_path), str(native), '--'])
                    receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30, quantitative=True)
                    require(receipt['exit_status'] == 0 and not receipt.get('error') and
                            not receipt.get('observer_still_waiting') and receipt['signals'] == [] and
                            receipt['cleanup_errors'] == [] and receipt['group_closed'] and receipt['reaped'],
                            'Diagnostic process failed')
                    require(receipt['inherited_common_mutex'] and receipt['quantitative_benchmark'] and
                            receipt['deadline_seconds'] == 30 and receipt['command'] == command and
                            receipt['controller_sha256'] == plan['controller_pins']['experiments/janet/knucleotide-bytes-v1/process.py'],
                            'Diagnostic process boundary changed')
                    require(process.sha(folder / 'stdout.bin') == protocol['expected_output']['sha256'], 'Prefix output differs')
                    birth = receipt['birth_identity']
                    identity = (birth['pid'], birth['birth_seconds'], birth['birth_microseconds'])
                    require(identity not in identities, 'Repeated process birth identity')
                    identities.add(identity)
                    seconds, rss = receipt['elapsed_seconds'], receipt['maximum_rss_bytes']
                    require(math.isfinite(seconds) and seconds > 0 and type(rss) is int and rss > 0,
                            'Invalid observation')
                    counters = native_counters(native, protocol, policy) if subject != 'R' else None
                    report['samples'].append(dict(order=order, position=position, subject=subject,
                        seconds=seconds, maximum_rss_bytes=rss, process=str((folder / 'process.json').relative_to(HERE)),
                        process_sha256=process.sha(folder / 'process.json'), native=counters,
                        native_sha256=process.sha(native) if counters else None, verified=True))
                    process.save(out / 'results.json', report)
            require(len(identities) == 16, 'Incomplete diagnostic observations')
            require(all(process.sha(Path(p)) == h for p, h in held.items()), 'Diagnostic protocol drift')
            require(all(process.sha(targets[s]) == pins[s] for s in targets), 'Executable drift')
            require(source_before == {label: source_state(Path(receipt['workspace']))
                    for label, receipt in [('F', final), ('I', initial)]}, 'Source drift')
            require(git('rev-parse', 'HEAD') == revision, 'Evidence revision drift')
            require(all(process.sha(ROOT / p) == h for p, h in primary_pins.items()), 'Primary evidence drift')
            report.update(status='all-16-secondary-observations-verified', source_after=source_before,
                median_seconds={s: statistics.median(r['seconds'] for r in report['samples'] if r['subject'] == s) for s in targets},
                median_peak_rss_bytes={s: statistics.median(r['maximum_rss_bytes'] for r in report['samples'] if r['subject'] == s) for s in targets})
    except BaseException as error:
        report.update(status='failed', error=repr(error))
        raise
    finally:
        process.save(out / 'results.json', report)


if __name__ == '__main__':
    main()
