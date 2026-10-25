"""Profile full and cold-start executions, then collect separate resource data."""
import fcntl
import re
import subprocess
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent


def run(label, arguments):
    with (STUDY / (label + '.controller.stdout')).open('wb') as stdout, (STUDY / (label + '.controller.stderr')).open('wb') as stderr:
        result = subprocess.run([sys.executable, *arguments], cwd=HERE, stdout=stdout, stderr=stderr)
    print(label, 'exit', result.returncode, flush=True)
    if result.returncode:
        sys.exit(result.returncode)


run('profile-build', ['build_profile.py', '--receipt', 'profile-sized-schedule-build-v1', '--source', 'counting-sized-schedule',
    '--output', 'counting-sized-schedule-profile', '--package', 'owner-counting-sized-schedule', '--compiler', 'compiler-v71'])
for mode in ('full', 'prefix'):
    for index in (1, 2, 3):
        folder = f'{mode}-profile-sized-schedule-v{index}'
        arguments = ['profile_full.py', folder, 'profile-sized-schedule-build-v1',
            '--input-mode', mode, '--launch', 'full-disjoint-state-v1/launch.json' if mode == 'full' else 'full-timing-v1/launch.json',
            '--interval', '0.001', '--sample-count', '1', '--sample-duration', '1',
            '--require-completion', '--require-packed-map', '--require-packed-ssa']
        if mode == 'full':
            arguments += ['--require-parallel']
        run(mode + '-profile-' + str(index), arguments)
        run(mode + '-analysis-' + str(index), ['analyze_profile.py', '--timing', 'sized-schedule-timing-v1',
            '--profile-build', 'profile-sized-schedule-build-v1', '--samples', folder, '--binary', 'counting-sized-schedule'])
    run(mode + '-partition', ['profile_hotspots.py', '--mech', *[f'{mode}-profile-sized-schedule-v{i}' for i in (1, 2, 3)],
        '--rust', 'rust-full-profile-v17', '--receipt', f'sized-schedule-{mode}-remaining-profile-v1'])
run('threads', ['sized-schedule-v1/thread-driver.py', 'sized-schedule-thread-lifetimes-v1'])
run('diagnostics', ['sized-schedule-v1/diagnostics.py'])

# The prefix counter cohort is diagnostic only. It measures the fixed cold
# costs on the identical qualified prefix, without reusing timing observations.
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
plan = read(STUDY / 'plan.json')
before = source_state()
assert before['commit'] == plan['source_commit'] and not before['status']
timing = read(HERE / 'full-sized-schedule-v1/results.json')
out = HERE / 'sized-schedule-prefix-counters-v1'
out.mkdir(exist_ok=False)
targets = dict(candidate=HERE / '.build' / plan['binary'], parent=HERE / '.build' / plan['parent_binary'],
    rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
inp, policy = HERE / 'rust-span-diagnostic-v2/input.fasta', HERE / 'full-timing-v1/launch.json'
env = read(HERE / plan['compiler'] / 'results.json')['environment']
report = dict(status='collecting', source=before, driver_sha256=process.sha(Path(__file__)),
    input_sha256=process.sha(inp), policy_sha256=process.sha(policy), observations=[], benchmark_samples=0,
    scope='Nine separate instrumented counter processes on the one-million-base prefix, three per subject. time -l elapsed values are centisecond-rounded and not primary timings. No counter process is pooled with either full-input timing session or the prefix timing cohort.')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    for index, order in enumerate(plan['orders'][:3]):
        for subject in order:
            assert process.sha(targets[subject]) == timing['pins'][subject]
            folder = out / f'{index}-{subject}'
            native_path = out / (folder.name + '.native.json')
            command = ['/usr/bin/time', '-l', str(targets[subject])]
            if subject != 'rust':
                command += [str(policy), str(native_path), '--']
            receipt = process.execute(command, folder, env, lock, stdin=inp, deadline=30, quantitative=False)
            assert receipt['exit_status'] == 0
            assert process.sha(folder / 'stdout.bin') == 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
            if subject != 'rust':
                native = read(native_path)
                assert native['native_hash_table_updates'] == native['native_packed_map_updates'] == 6999961
                assert native['native_parallel_tasks'] == 7 and native['shutdown'] == 'completed'
            raw = (folder / 'stderr.bin').read_text()
            def counter(name):
                matches = re.findall(r'^\s*(\d+)\s+' + re.escape(name) + r'\s*$', raw, re.M)
                assert len(matches) == 1
                return int(matches[0])
            times = re.search(r'([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys', raw)
            assert times
            report['observations'].append(dict(subject=subject, order=index, process=receipt,
                instructions=counter('instructions retired'), cycles=counter('cycles elapsed'),
                user_seconds=float(times[2]), system_seconds=float(times[3]),
                maximum_rss_bytes=counter('maximum resident set size'), stderr_sha256=process.sha(folder / 'stderr.bin')))
            process.save(out / 'results.json', report)
assert source_state() == before
report['source_after'] = before
report['status'] = 'all-prefix-counter-outputs-and-physical-updates-verified'
process.save(out / 'results.json', report)
