"""Matched complete-process timings and separate hardware counters."""
import fcntl
import re
import statistics
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import (PLAN, process, read, source_state, check_native,
                     INPUT_SHA, OUTPUT_SHA, POLICY_SHA)


def main():
    assert len(sys.argv) == 2 and sys.argv[1] in ('timings', 'counters')
    mode = sys.argv[1]
    plan = read(STUDY / 'plan.json')
    before = source_state()
    assert before['commit'] == plan['source_commit'] and not before['status']
    timing = read(HERE / 'full-prepared-refill-v1/results.json')
    env = read(HERE / plan['compiler'] / 'results.json')['environment']
    targets = dict(mech=HERE / '.build' / plan['baseline_binary'],
                   rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
    pins = dict(mech=timing['pins']['candidate'], rust=timing['pins']['rust'])
    for subject, binary in targets.items():
        assert process.sha(binary) == pins[subject]
    inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
    policy = HERE / 'full-disjoint-state-v1/launch.json'
    assert process.sha(inp) == INPUT_SHA and process.sha(policy) == POLICY_SHA
    out = STUDY / mode
    out.mkdir(exist_ok=False)
    report = dict(status='collecting', mode=mode, source=before, pins=pins,
                  driver_sha256=process.sha(Path(__file__)), plan_sha256=process.sha(STUDY / 'plan.json'),
                  input_sha256=INPUT_SHA, policy_sha256=POLICY_SHA, samples=[],
                  excluded_warmups=0, excluded_outliers=0,
                  benchmark_samples=12 if mode == 'timings' else 0,
                  scope='Serial complete-process timings including startup and secured shutdown.' if mode == 'timings'
                  else 'Separate diagnostic /usr/bin/time -l processes. Rounded elapsed values are not primary timings.')
    process.save(out / 'results.json', report)
    orders = plan['timing_orders'] if mode == 'timings' else [[s] for s in plan['diagnostic_order']]
    with Path(PLAN['common_mutex']).open('a+') as lock:
        assert Path(PLAN['common_mutex']).stat().st_ino == plan['mutex_inode']
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for index, order in enumerate(orders):
            for position, subject in enumerate(order):
                folder = out / f'{index}-{position}-{subject}'
                native_path = out / (folder.name + '.native.json')
                command = [str(targets[subject])]
                if subject == 'mech':
                    command += [str(policy), str(native_path), '--']
                if mode == 'counters':
                    command = ['/usr/bin/time', '-l'] + command
                receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30,
                                          quantitative=mode == 'timings')
                assert receipt['exit_status'] == 0 and process.sha(folder / 'stdout.bin') == OUTPUT_SHA
                native = check_native(native_path) if subject == 'mech' else None
                row = dict(subject=subject, order=index, position=position, process=receipt,
                           seconds=receipt['elapsed_seconds'], maximum_rss_bytes=receipt['maximum_rss_bytes'],
                           native=native, stdout_sha256=OUTPUT_SHA,
                           native_sha256=process.sha(native_path) if native else None)
                if mode == 'counters':
                    text = (folder / 'stderr.bin').read_text()
                    def counter(name):
                        values = re.findall(r'^\s*(\d+)\s+' + re.escape(name) + r'\s*$', text, re.M)
                        assert len(values) == 1
                        return int(values[0])
                    times = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', text)
                    assert times
                    row.update(instructions=counter('instructions retired'), cycles=counter('cycles elapsed'),
                               involuntary_context_switches=counter('involuntary context switches'),
                               real_seconds=float(times[1]), user_seconds=float(times[2]), system_seconds=float(times[3]),
                               stderr_sha256=process.sha(folder / 'stderr.bin'))
                report['samples'].append(row)
                process.save(out / 'results.json', report)
            print(mode, index + 1, 'of', len(orders), 'verified', flush=True)
    assert source_state() == before
    keys = ['seconds', 'maximum_rss_bytes'] if mode == 'timings' else [
        'instructions', 'cycles', 'involuntary_context_switches', 'user_seconds', 'system_seconds', 'real_seconds']
    report['medians'] = {s: {k: statistics.median(r[k] for r in report['samples'] if r['subject'] == s)
                            for k in keys} for s in targets}
    if mode == 'timings':
        report['x_rust'] = {s: report['medians'][s]['seconds'] / report['medians']['rust']['seconds'] for s in targets}
        report['stdev_seconds'] = {s: statistics.stdev(r['seconds'] for r in report['samples'] if r['subject'] == s) for s in targets}
    report.update(status='all-complete-process-outputs-and-update-counts-verified', source_after=before)
    process.save(out / 'results.json', report)
    print(report['medians'], flush=True)


if __name__ == '__main__':
    main()
