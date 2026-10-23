"""Measure compiled admission groups against the previous AOT and upstream Rust."""
import fcntl
import json
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0, str(HERE.parent / 'revcomp-streaming-v1'))
from build_baseline import PLAN, process

out = HERE / 'map-admission-timing-v1'
out.mkdir(exist_ok=False)
prepared = json.loads((HERE / 'compiler-v5/results.json').read_text())
assert prepared['status'] == 'compiler-built'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == prepared['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
env = prepared['environment']
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == prepared['compiler_sha256']
source = HERE / 'knucleotide-source-map.mec'
assert process.sha(source) == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
targets = dict(candidate=HERE / '.build/counting-groups', baseline=HERE / '.build/counting-spans',
               rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
assert process.sha(targets['baseline']) == '6dbb7b58332bd8cf6b156f0861e55597440e107c4b940b8bd102c703149b9d8a'
assert process.sha(targets['rust']) == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
expected = (HERE / 'rust-span-diagnostic-v2/expected.txt').read_bytes()
report = dict(status='building', source_commit=prepared['source_commit'],
              baseline_source_commit='7aa1bea1b5565113cd07ddeaeea2bed30ed84a54',
              source_sha256=process.sha(source), input_sha256=process.sha(inp),
              launch_sha256=process.sha(policy), baseline_sha256=process.sha(targets['baseline']),
              rust_sha256=process.sha(targets['rust']), input_bases=1000000,
              expected_table_updates=6999961, samples=[],
              scope='One-million-base standard THREE prefix; complete fresh processes; secured Mech AOT; diagnostic only')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = [str(cli), '--no-config', 'build', str(source), '--backend', 'cranelift',
               '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
               str(WORKSPACE), '--name', 'owner-groups', '-o', str(targets['candidate'])]
    result = process.execute(command, out / 'build', env, lock, deadline=1800)
    assert result['exit_status'] == 0, (out / 'build/stderr.bin').read_text()[-5000:]
    report['candidate_sha256'] = process.sha(targets['candidate'])
    project = Path(str(targets['candidate']) + '.project')
    assert process.sha(project / 'program.mecb') == process.sha(Path(str(targets['baseline']) + '.project/program.mecb'))
    manifest = json.loads((project / 'linked-manifest.json').read_text())
    assert manifest['object']['work_policy_version'] == 50
    assert manifest['object']['retained_map_scalar_admission_groups'] > 0
    report['native_admission_groups'] = manifest['object']['retained_map_scalar_admission_groups']
    process.save(out / 'results.json', report)

    def run(label, round_number, timed):
        name = f'{round_number}-{label}'
        command = [str(targets[label])]
        if label != 'rust':
            command += [str(policy), str(out / (name + '.report.json')), '--']
        result = process.execute(command, out / name, env, lock, stdin=inp, deadline=120, quantitative=timed)
        assert result['exit_status'] == 0, (out / name / 'stderr.bin').read_text()[-4000:]
        assert (out / name / 'stdout.bin').read_bytes() == expected
        if label != 'rust':
            native = json.loads((out / (name + '.report.json')).read_text())
            assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
            assert native['shutdown'] == 'completed'
            assert native['native_hash_table_regions'] == 7 and native['native_hash_table_updates'] == 6999961
        if timed:
            row = dict(label=label, seconds=result['elapsed_seconds'], maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in targets:
        run(label, 'warmup', False)
    for index, order in enumerate([['candidate', 'baseline', 'rust'], ['rust', 'baseline', 'candidate'], ['baseline', 'candidate', 'rust']]):
        for label in order:
            run(label, index, True)
report['median_seconds'] = {label: statistics.median(row['seconds'] for row in report['samples'] if row['label'] == label) for label in targets}
report['x_rust'] = {label: seconds / report['median_seconds']['rust'] for label, seconds in report['median_seconds'].items()}
report['denominator'] = 'Unmodified upstream Rust #7 on the same one-million-base input and machine'
report['status'] = 'all-outputs-and-update-counts-verified'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
