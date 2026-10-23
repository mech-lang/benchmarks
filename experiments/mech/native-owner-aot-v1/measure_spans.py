"""Build and measure selected String keys against the unchanged cache-total baseline."""
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

out = HERE / 'key-span-timing-v1'
out.mkdir(exist_ok=False)
prepared = json.loads((HERE / 'compiler-v4/results.json').read_text())
assert prepared['status'] == 'compiler-built'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == prepared['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
env = prepared['environment']
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == prepared['compiler_sha256']
source = HERE / 'knucleotide-source-map.mec'
assert process.sha(source) == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
candidate = HERE / '.build/counting-spans'
baseline = HERE / '.build/counting-cache'
assert process.sha(baseline) == '06096c15be008b5495a9458e16a5e47e1f024fc34adbca690f473ce03b099f11'
input_path = HERE / 'cache-scale-v1/input.fasta'
assert process.sha(input_path) == '9d6141d3b346a237e13de00ac1fce3a999119b34968d37aaa123bc2ebc4dcfaf'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
expected = (HERE / 'cache-scale-v1/expected.txt').read_bytes()
report = dict(status='building', source_commit=prepared['source_commit'],
              baseline_source_commit='f6ee09e631048fb831d2032e8013a56d876efc63',
              source_sha256=process.sha(source), input_sha256=process.sha(input_path),
              launch_sha256=process.sha(policy), baseline_sha256=process.sha(baseline),
              input_bases=100000, expected_table_updates=699961,
              scope='100000-base standard THREE prefix; complete secured processes, diagnostic only',
              samples=[])
process.save(out / 'results.json', report)

with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = [str(cli), '--no-config', 'build', str(source), '--backend', 'cranelift',
               '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
               str(WORKSPACE), '--name', 'owner-spans', '-o', str(candidate)]
    result = process.execute(command, out / 'build', env, lock, deadline=1800)
    assert result['exit_status'] == 0, (out / 'build/stderr.bin').read_text()[-5000:]
    report['candidate_sha256'] = process.sha(candidate)
    assert process.sha(Path(str(candidate) + '.project/program.mecb')) == process.sha(Path(str(baseline) + '.project/program.mecb'))
    manifest = json.loads(Path(str(candidate) + '.project/linked-manifest.json').read_text())
    assert manifest['object']['work_policy_version'] == 49

    def run(label, round_number, timed):
        binary = candidate if label == 'candidate' else baseline
        name = f'{round_number}-{label}'
        command = [str(binary), str(policy), str(out / (name + '.report.json')), '--']
        result = process.execute(command, out / name, env, lock, stdin=input_path,
                                 deadline=120, quantitative=timed)
        assert result['exit_status'] == 0, (out / name / 'stderr.bin').read_text()[-4000:]
        assert (out / name / 'stdout.bin').read_bytes() == expected
        native = json.loads((out / (name + '.report.json')).read_text())
        assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation']
        assert native['shutdown'] == 'completed'
        if label == 'candidate':
            assert native['native_hash_table_regions'] == 7
            assert native['native_hash_table_updates'] == 699961
        if timed:
            row = dict(label=label, seconds=result['elapsed_seconds'],
                       maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in ['candidate', 'baseline']:
        run(label, 'warmup', False)
    for index, order in enumerate([['candidate', 'baseline'], ['baseline', 'candidate'], ['candidate', 'baseline']]):
        for label in order:
            run(label, index, True)

report['median_seconds'] = {label: statistics.median(row['seconds'] for row in report['samples'] if row['label'] == label) for label in ['candidate', 'baseline']}
report['x_mech_aot'] = {label: seconds / report['median_seconds']['candidate'] for label, seconds in report['median_seconds'].items()}
report['denominator'] = 'Current source-map Mech AOT on the same 100000-base input'
report['status'] = 'all-outputs-and-update-counts-verified'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
