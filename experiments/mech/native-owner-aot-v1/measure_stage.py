"""Build a source-preserving stage and compare it with its parent and upstream Rust."""
import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument('--compiler', required=True)
parser.add_argument('--parent-receipt', required=True)
parser.add_argument('--parent-binary', required=True)
parser.add_argument('--binary', required=True)
parser.add_argument('--package', required=True)
parser.add_argument('--work-policy', required=True, type=int)
parser.add_argument('--receipt', required=True)
parser.add_argument('--minimum-closed-map-regions', type=int, default=0)
parser.add_argument('--allow-equal-admissions', action='store_true',
                    help='For improvements inside an already selected closed loop; still reject more admissions')
parser.add_argument('--require-packed-map', action='store_true',
                    help='Require every candidate execution to select packed storage for all regions and updates')
args = parser.parse_args()
out = HERE / args.receipt
out.mkdir(exist_ok=False)
prepared = json.loads((HERE / args.compiler / 'results.json').read_text())
parent = json.loads((HERE / args.parent_receipt / 'results.json').read_text())
assert prepared['status'] == 'compiler-built'
assert parent['status'] == 'all-outputs-and-update-counts-verified'
assert subprocess.check_output(['git', '-C', str(WORKSPACE), 'rev-parse', 'HEAD'], text=True).strip() == prepared['source_commit']
assert not subprocess.check_output(['git', '-C', str(WORKSPACE), 'status', '--porcelain'])
env = prepared['environment']
cli = HERE / '.build/mech-canonical'
assert process.sha(cli) == prepared['compiler_sha256']
source = HERE / 'knucleotide-source-map.mec'
assert process.sha(source) == parent['source_sha256'] == 'ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
targets = dict(candidate=HERE / '.build' / args.binary,
               baseline=HERE / '.build' / args.parent_binary,
               rust=HERE.parent / 'native-hashmap-work-v1/.build/knucleotide-rust-7')
assert not targets['candidate'].exists()
assert process.sha(targets['baseline']) == parent['candidate_sha256']
assert process.sha(targets['rust']) == parent['rust_sha256'] == 'f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
inp = HERE / 'rust-span-diagnostic-v2/input.fasta'
assert process.sha(inp) == 'e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
policy = HERE / 'full-timing-v1/launch.json'
assert process.sha(policy) == '3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
expected = (HERE / 'rust-span-diagnostic-v2/expected.txt').read_bytes()
report = dict(status='building', source_commit=prepared['source_commit'],
              baseline_source_commit=parent['source_commit'],
              source_sha256=process.sha(source), input_sha256=process.sha(inp),
              launch_sha256=process.sha(policy), baseline_sha256=process.sha(targets['baseline']),
              rust_sha256=process.sha(targets['rust']), input_bases=1000000,
              expected_table_updates=6999961, samples=[], configuration=vars(args),
              require_packed_map=args.require_packed_map, native_executions=[],
              scope='One-million-base standard THREE prefix; complete fresh processes; secured Mech AOT; diagnostic only')
process.save(out / 'results.json', report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    command = [str(cli), '--no-config', 'build', str(source), '--backend', 'cranelift',
               '--profile', 'release', '--keep-project', '--offline', '--workspace-root',
               str(WORKSPACE), '--name', args.package, '-o', str(targets['candidate'])]
    result = process.execute(command, out / 'build', env, lock, deadline=1800)
    assert result['exit_status'] == 0, (out / 'build/stderr.bin').read_text()[-5000:]
    report['candidate_sha256'] = process.sha(targets['candidate'])
    project = Path(str(targets['candidate']) + '.project')
    assert process.sha(project / 'program.mecb') == process.sha(Path(str(targets['baseline']) + '.project/program.mecb'))
    manifest = json.loads((project / 'linked-manifest.json').read_text())
    assert manifest['object']['work_policy_version'] == args.work_policy
    report['native_admission_groups'] = manifest['object']['retained_map_scalar_admission_groups']
    descriptor = json.loads((project / 'native-descriptor.json').read_text())['descriptor']
    report['closed_map_regions'] = sum(region.get('map') is not None
                                      for region in descriptor['closed_tails']['regions'])
    assert report['closed_map_regions'] >= args.minimum_closed_map_regions
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
            packed = dict(packed_map_regions=native.get('native_packed_map_regions'),
                          packed_map_updates=native.get('native_packed_map_updates'))
            if label == 'candidate' and args.require_packed_map:
                assert packed['packed_map_regions'] == 7, 'Candidate fell back from packed map regions'
                assert packed['packed_map_updates'] == 6999961, 'Candidate did not complete every update in packed storage'
            report['native_executions'].append(dict(label=label, round=round_number,
                                                     timed=timed, **packed))
            process.save(out / 'results.json', report)
        if timed:
            row = dict(label=label, seconds=result['elapsed_seconds'], maximum_rss_bytes=result['maximum_rss_bytes'])
            report['samples'].append(row)
            process.save(out / 'results.json', report)
            print(json.dumps(row), flush=True)

    for label in targets:
        run(label, 'warmup', False)
    if args.minimum_closed_map_regions:
        candidate = json.loads((out / 'warmup-candidate.report.json').read_text())
        baseline = json.loads((out / 'warmup-baseline.report.json').read_text())
        if args.allow_equal_admissions:
            assert candidate['native_visits'] <= baseline['native_visits'], 'The candidate added runtime admissions'
        else:
            assert candidate['native_visits'] < baseline['native_visits'], 'The new path did not reduce runtime admissions'
        report['warmup_native_visits'] = {label: native['native_visits']
                                         for label, native in [('candidate', candidate), ('baseline', baseline)]}
    for index, order in enumerate([['candidate', 'baseline', 'rust'], ['rust', 'baseline', 'candidate'], ['baseline', 'candidate', 'rust']]):
        for label in order:
            run(label, index, True)
report['median_seconds'] = {label: statistics.median(row['seconds'] for row in report['samples'] if row['label'] == label) for label in targets}
report['x_rust'] = {label: seconds / report['median_seconds']['rust'] for label, seconds in report['median_seconds'].items()}
report['denominator'] = 'Unmodified upstream Rust #7 on the same one-million-base input and machine'
report['status'] = 'all-outputs-and-update-counts-verified'
process.save(out / 'results.json', report)
print(json.dumps(report), flush=True)
