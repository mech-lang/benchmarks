"""Separate counters and exact file sizes for shared immutable String facts."""
import fcntl
import os
import re
import signal
import statistics
import sys
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from memory import process, read, source_state, check_native, OUTPUT_SHA, PLAN
from memory import discover, sample, guarded, same_birth
from binary import macho


def main():
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    timing = read(HERE / 'full-shared-string-facts-v1/results.json')
    targets = dict(candidate=HERE / '.build' / plan['binary'], parent=HERE / '.build' / plan['parent_binary'],
                   rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    policy = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == timing['input_sha256'] and process.sha(policy) == timing['policy_sha256']
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    out = STUDY / 'counters'
    out.mkdir(exist_ok=False)
    report = dict(status='collecting', source=before, driver_sha256=process.sha(Path(__file__)),
                  memory_helper_sha256=process.sha(HERE / 'preparation-interactions-v1/memory.py'),
                  binary_helper_sha256=process.sha(HERE / 'preparation-interactions-v1/binary.py'),
                  snapshots=[], counters=[], binary={}, benchmark_samples=0,
                  scope='Nine separate full-input counter executions, not primary timings. Exact timed files supply disk sizes. Inline immutable String facts are covered by concrete snapshot-owner admission; primary processes retain actual peak RSS.')
    for subject, binary in targets.items():
        parsed = macho(binary)[0]
        assert parsed['sha256'] == timing['pins'][subject]
        report['binary'][subject] = parsed
    process.save(out / 'results.json', report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, order in enumerate(plan['orders'][:3]):
            for subject in order:
                native_path = out / f'counter-{index}-{subject}.native.json'
                command = ['/usr/bin/time', '-l', str(targets[subject])]
                if subject != 'rust':
                    command += [str(policy), str(native_path), '--']
                folder = out / f'counter-{index}-{subject}'
                receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30, quantitative=False)
                assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                if subject != 'rust':
                    check_native(native_path)
                text = (folder / 'stderr.bin').read_text()
                def counter(name):
                    values = re.findall(r'^\s*(\d+)\s+' + re.escape(name) + r'\s*$', text, re.M)
                    assert len(values) == 1
                    return int(values[0])
                times = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', text)
                assert times
                report['counters'].append(dict(subject=subject, order=index, process=receipt,
                    instructions=counter('instructions retired'), cycles=counter('cycles elapsed'),
                    involuntary_context_switches=counter('involuntary context switches'),
                    real_seconds=float(times[1]), user_seconds=float(times[2]), system_seconds=float(times[3]),
                    stderr_sha256=process.sha(folder / 'stderr.bin')))
                process.save(out / 'results.json', report)
    assert source_state() == before
    report['counter_medians'] = {s: {k: statistics.median(r[k] for r in report['counters'] if r['subject'] == s)
        for k in ['instructions', 'cycles', 'involuntary_context_switches', 'real_seconds', 'user_seconds', 'system_seconds']}
        for s in targets}
    report['source_after'] = before
    report['status'] = 'all-shared-string-fact-diagnostic-outputs-and-exact-sizes-verified'
    process.save(out / 'results.json', report)
    print('Live blocks', {r['subject']: r['live_allocations'] for r in report['snapshots']}, flush=True)
    print('Counter medians', report['counter_medians'], flush=True)


if __name__ == '__main__':
    main()
