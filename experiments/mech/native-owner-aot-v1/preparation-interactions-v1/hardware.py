"""Collect separate whole-process counters for all five factorial subjects."""
import fcntl
import json
import re
import statistics
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(STUDY))
from measure import PLAN, process, read, source_state, check_native

plan = read(STUDY / 'plan.json')
timing = read(HERE / 'full-preparation-interactions-v1/results.json')
assert timing['status'] == 'all-factorial-outputs-updates-and-source-pins-verified'
before = source_state()
assert not before['status'] and before['commit'] == plan['source_commit']
targets = {s: HERE / '.build' / pin['binary'] for s, pin in timing['pins'].items() if s != 'rust'}
targets['rust'] = HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7'
for subject, binary in targets.items():
    assert process.sha(binary) == timing['pins'][subject]['binary_sha256']
inp = HERE.parents[2] / 'experiments/janet/.build/inputs/fasta-n25000000.stdin'
policy = HERE / 'full-disjoint-state-v1/launch.json'
assert process.sha(inp) == timing['input_sha256'] and process.sha(policy) == timing['policy_sha256']
compiler = read(HERE / plan['compiler'] / 'results.json')
assert compiler['source_commit'] == before['commit']
out = HERE / 'preparation-interactions-hardware-v1'
out.mkdir(exist_ok=False)
report = dict(status='running', source=before, plan_sha256=process.sha(STUDY / 'plan.json'),
              driver_sha256=process.sha(Path(__file__)), observations=[], benchmark_samples=0,
              input_sha256=timing['input_sha256'], policy_sha256=timing['policy_sha256'],
              scope='Fifteen separate diagnostic executions, three per factorial subject, serial under the common lock. time -l reports whole-process counters across native threads, with centisecond elapsed rounding. These are not primary benchmark timing observations or an interaction significance test.')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index, order in enumerate([plan['orders'][i] for i in (0, 7, 14)]):
        for subject in order:
            native_path = out / f'{index}-{subject}.native.json'
            command = ['/usr/bin/time', '-l', str(targets[subject])]
            if subject != 'rust':
                command += [str(policy), str(native_path), '--']
            folder = out / f'{index}-{subject}'
            receipt = process.execute(command, folder, compiler['environment'], lock,
                                      stdin=inp, deadline=30, quantitative=False)
            assert receipt['exit_status'] == 0
            assert process.sha(folder / 'stdout.bin') == 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
            if subject != 'rust':
                check_native(native_path)
            raw = (folder / 'stderr.bin').read_text()
            def counter(name):
                rows = re.findall(r'^\s*(\d+)\s+' + re.escape(name) + r'\s*$', raw, re.M)
                assert len(rows) == 1
                return int(rows[0])
            times = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', raw)
            assert times
            report['observations'].append(dict(subject=subject, order=index,
                instructions=counter('instructions retired'), cycles=counter('cycles elapsed'),
                real_seconds=float(times[1]), user_seconds=float(times[2]), system_seconds=float(times[3]),
                involuntary_context_switches=counter('involuntary context switches'),
                maximum_rss_bytes=counter('maximum resident set size'),
                process_sha256=process.sha(folder / 'process.json'), stderr_sha256=process.sha(folder / 'stderr.bin')))
            process.save(out / 'results.json', report)
    assert source_state() == before
report['medians'] = {s: {key: statistics.median(r[key] for r in report['observations'] if r['subject'] == s)
                        for key in ['instructions', 'cycles', 'real_seconds', 'user_seconds', 'system_seconds', 'involuntary_context_switches']}
                     for s in plan['subjects']}
report['status'] = 'all-five-subject-counter-outputs-and-updates-verified'
process.save(out / 'results.json', report)
print(json.dumps(report['medians'], indent=2))
