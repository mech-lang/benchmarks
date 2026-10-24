"""Trace live allocation callers in separate stack-logging diagnostic processes."""
import fcntl
import os
import signal
import sys
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(STUDY))
from memory import process, read, source_state, check_native, OUTPUT_SHA, PLAN
from memory import discover, sample, guarded, same_birth


def main():
    out = HERE / 'preparation-interactions-allocation-callers-v1'
    out.mkdir(exist_ok=False)
    timing = read(HERE / 'full-preparation-interactions-v1/results.json')
    plan = read(STUDY / 'plan.json')
    targets = dict(combined=HERE / '.build/counting-preparation-combined',
                   rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    policy = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == timing['input_sha256'] and process.sha(policy) == timing['policy_sha256']
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    base_env = read(HERE / plan['compiler'] / 'results.json')['environment']
    env = dict(base_env, MallocStackLogging='1')
    report = dict(status='collecting', source=before, driver_sha256=process.sha(Path(__file__)),
                  memory_helper_sha256=process.sha(STUDY / 'memory.py'),
                  input_sha256=timing['input_sha256'], policy_sha256=timing['policy_sha256'],
                  environment_delta=dict(MallocStackLogging='1'), observations=[], benchmark_samples=0,
                  scope='Two separate, allocation-instrumented diagnostic executions. Exact timed binaries with MallocStackLogging=1; content-free snapshots approximately 100 ms after seven workers are first observed. The owned process alone is stopped and always resumed. Live allocation stacks and sizes are not allocation churn, peak attribution, primary timing samples or a causal speedup measurement.')
    process.save(out / 'results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for subject, binary in targets.items():
            assert process.sha(binary) == timing['pins'][subject]['binary_sha256']
            identity, first_workers, snapshots, captures = None, None, [], []
            captured = False
            origin = time.monotonic_ns()
            def monitor():
                nonlocal identity, first_workers, captured
                if identity is None:
                    identity = discover(binary)
                if identity is None:
                    return
                observation = sample(identity, binary)
                if observation is None:
                    return
                now = time.monotonic()
                snapshots.append(dict(seconds=(time.monotonic_ns() - origin) / 1e9, **observation))
                if first_workers is None and observation['threads'] >= 8:
                    first_workers = now
                if captured or first_workers is None or now - first_workers < .100:
                    return
                captured = True
                assert guarded(identity, binary)
                os.kill(identity['pid'], signal.SIGSTOP)
                try:
                    for tool, args in [('vmmap', ['-summary', '-wide']),
                                       ('heap', ['--noContent', '--sortBySize', '--showSizes']),
                                       ('malloc_history', ['-callTree', '-invert', '-ignoreThreads',
                                                           '-consolidateAllBySymbol', '-noContent', '-q'])]:
                        assert guarded(identity, binary)
                        command = ['/usr/bin/' + tool, str(identity['pid']), *args] if tool == 'malloc_history' else ['/usr/bin/' + tool, *args, str(identity['pid'])]
                        folder = out / (subject + '-' + tool)
                        receipt = process.execute(command, folder, base_env, lock, deadline=20, quantitative=False)
                        captures.append(dict(tool=tool, process=receipt,
                            stdout_sha256=process.sha(folder / 'stdout.bin'), stderr_sha256=process.sha(folder / 'stderr.bin')))
                finally:
                    if guarded(identity, binary):
                        os.kill(identity['pid'], signal.SIGCONT)
            native_path = out / (subject + '.native.json')
            command = [str(binary)]
            if subject != 'rust':
                command += [str(policy), str(native_path), '--']
            folder = out / subject
            receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=60,
                                      monitor=monitor, monitor_interval=.001, quantitative=False)
            assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
            assert identity and same_birth(identity, receipt['birth_identity']) and captured and len(captures) == 3
            if subject != 'rust':
                check_native(native_path)
            process.save(folder / 'allocation-observations.json', dict(identity=identity, snapshots=snapshots, captures=captures))
            report['observations'].append(dict(subject=subject, process=receipt,
                capture_sample=snapshots[next(i for i, s in enumerate(snapshots) if i + 1 < len(snapshots) and snapshots[i + 1]['seconds'] - s['seconds'] > .25)],
                captures=[dict(tool=c['tool'], exit_status=c['process']['exit_status']) for c in captures],
                raw_sha256=process.sha(folder / 'allocation-observations.json')))
            process.save(out / 'results.json', report)
            print(subject, 'allocation caller snapshots completed; output verified', flush=True)
    assert source_state() == before
    report['source_after'] = before
    report['status'] = 'all-owned-allocation-diagnostics-and-outputs-verified'
    process.save(out / 'results.json', report)


if __name__ == '__main__':
    main()
