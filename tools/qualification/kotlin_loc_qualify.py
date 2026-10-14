#!/usr/bin/env python3
"""Qualify reviewed Kotlin source counts from the closed native PSI study.

This command only reads retained evidence. It never starts a compiler or JVM.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/source-units-v1'
PLAN = ROOT/'experiments/kotlin/source-counts-v3/plan-v1.json'
RUN = PLAN.parent/'run-v1'
READER = ROOT/'tools/qualification/kotlin_loc_v3.py'
COUNTER = ROOT/'tools/qualification/kotlin_source_units_v2.py'
REPLAY = PACKET/'replay-v2.json'
REVIEW = PACKET/'review-v2.md'
DURABLE = ROOT/'experiments/kotlin/dispatch-v1/owned-jobs/source-reader-v3/terminal.json'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
LOCK = Path('/tmp/mech-clbg-timing.lock')
PINS = {
    PLAN: '75048092055c76196358805c09acd9e4210b3b32d4ee59697d2a247402cf34e2',
    READER: '7e7bf707e96651559c53ea67909547adce9a6a05d30da07dca266d89d6d4e63f',
    RUN/'report.json': '52a45fc4d96358118dfc6ab5e011b55245ad4caeb5ba07283fcbd6a92a38b1be',
    PYTHON: 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e',
}
BENCHES = {'binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
           'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm'}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def verify(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, 'Pinned bytes changed: '+str(path))


def module(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Reviewed module changed')
    spec = importlib.util.spec_from_file_location('qualified_'+path.stem, path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


def verify_lock(lock):
    held, named = os.fstat(lock.fileno()), LOCK.stat()
    require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
            and held.st_ino == 79859134, 'Common timing mutex changed')


def artifact_closure(terminal, reader):
    errors = []
    paths = reader.inventory_files(RUN, errors)
    artifacts = terminal['available_evidence']
    require(not errors and {str(p.relative_to(RUN)) for p in paths} == set(artifacts)|{'terminal.json'}
            and len(artifacts) == 192, 'Native-reader artifact inventory differs')
    total = 0
    for name, evidence in artifacts.items():
        path = RUN/name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,
                'Unsafe reader artifact path')
        require(path.stat().st_size == evidence['bytes'] and sha(path) == evidence['sha256'],
                'Native-reader artifact bytes differ: '+name)
        total += evidence['bytes']
    require(total == 8847311, 'Native-reader artifact byte total differs')
    return dict(files=len(artifacts), bytes=total)


def reviewed_counts(plan, replay, expected, source_hashes):
    require(set(expected) == BENCHES and all(len(v) == 2 and all(type(n) is int and n > 0 for n in v)
            for v in expected.values()), 'Expected all ten reviewed physical/canonical totals')
    require(replay['status'] == 'candidate-replay-awaiting-owner-review'
            and replay['native_fixture_expectations_passed'] is True
            and len(replay['fixture_checks']) == 14 and all(x['passed'] is True for x in replay['fixture_checks'])
            and replay['formatter_evidence_available'] is False and replay['formatted_loc'] is None,
            'Replay fixtures, status or formatter scope differ')
    inputs = {x['id']: x for x in plan['inputs']}
    require(len(inputs) == len(plan['inputs']) == 54, 'Expected forty sources and fourteen fixtures')
    application = {k: v for k, v in inputs.items() if v['kind'] == 'application'}
    require(len(application) == 40 and len({v['path'] for v in application.values()}) == 40,
            'Expected forty distinct authored inputs')
    require({c['id'] for c in replay['fixture_checks']} == {k for k, v in inputs.items() if v['kind'] == 'fixture'},
            'Fixture identities differ')
    profiles = {p['id']: p for p in plan['profiles']}
    counted = {p['id']: p for p in replay['profiles']}
    wanted = {'kotlin-'+b+'-'+v for b in BENCHES for v in ('compact', 'optimized')}
    require(len(profiles) == len(plan['profiles']) == len(counted) == len(replay['profiles']) == 20
            and set(profiles) == set(counted) == wanted, 'Expected twenty retained forms')
    files, bundles, used = {}, [], []
    for identity, profile in profiles.items():
        bench, variant = profile['benchmark'], profile['variant']
        require(identity == 'kotlin-'+bench+'-'+variant and len(profile['inputs']) == len(set(profile['inputs'])) == 2
                and counted[identity]['inputs'] == profile['inputs'], 'Source bundle membership differs')
        require(all(k in application for k in profile['inputs'])
                and {application[k]['role'] for k in profile['inputs']} == {'application', 'application-helper'},
                'Complete authored source roles required')
        for key in profile['inputs']:
            item, row = application[key], replay['files'][key]
            require(source_hashes[key] == item['sha256'] and row['diagnostics'] == []
                    and all(type(row[k]) is int and row[k] > 0 for k in ('physical_loc', 'normalized_loc')),
                    'Unresolved or invalid source owner: '+key)
            files[key] = dict(source=item['path'], source_sha256=item['sha256'], role=item['role'],
                              original_physical_loc=row['physical_loc'], canonical_loc=row['normalized_loc'])
            used.append(key)
        totals = [sum(files[k][field] for k in profile['inputs'])
                  for field in ('original_physical_loc', 'canonical_loc')]
        require(totals == list(expected[bench]) and counted[identity]['candidate_canonical_loc'] == totals[1],
                'Counts differ from reviewed source totals: '+identity)
        bundles.append(dict(id=identity, benchmark=bench, variant=variant, inputs=profile['inputs'],
            original_physical_loc=totals[0], canonical_loc=totals[1], formatted_loc=None,
            canonical_loc_qualified=True, formatted_loc_qualified=False,
            source_work_qualified=False, full_timings_qualified=False, chart_admission=False))
    require(len(used) == len(set(used)) == 40 and set(used) == set(application), 'Missing or duplicated authored input')
    for bench in BENCHES:
        pairs = [{files[k]['role']: files[k]['source_sha256']
                  for k in profiles['kotlin-'+bench+'-'+v]['inputs']} for v in ('compact', 'optimized')]
        require(pairs[0] == pairs[1], 'Equivalent-source pair differs: '+bench)
    return files, bundles


def validate_process(receipt, kind, folder, plan, controller_pid, supervisor, reader):
    reader.validate_receipt(receipt, kind)
    require(receipt['cwd'] == str(folder) and receipt['identity']['ppid'] == controller_pid,
            'Reader ownership or working directory differs')
    environment = dict(plan['runtime_environment'], HOME=str(folder/'home'),
                       XDG_CONFIG_HOME=str(folder/'config'), TMPDIR=str(folder/'tmp')+os.sep)
    environment['JAVA_OPTS'] = ' '.join(supervisor.kh.FLAGS+
        ['-Duser.home='+str(folder/'home'), '-Djava.io.tmpdir='+str(folder/'tmp')])
    if kind == 'diagnostic-compile':
        command = [plan['javac']]+['-J'+f for f in plan['runtime_flags']]+[
            '-J-Duser.home='+str(folder/'home'), '-J-Djava.io.tmpdir='+str(folder/'tmp'),
            '--release', '17', '-proc:none', '-cp', os.pathsep.join(plan['compiler_jars']),
            '-d', str(RUN/'probe-classes'), str(folder/'SourceReader.java')]
    else:
        command = [plan['java']]+plan['runtime_flags']+[
            '-Duser.home='+str(folder/'home'), '-Djava.io.tmpdir='+str(folder/'tmp'),
            '-cp', os.pathsep.join([str(RUN/'probe-classes')]+plan['compiler_jars']),
            'sourcequalification.SourceReader', str(RUN/'inputs.tsv'), str(folder/'sources')]
    require(receipt['command'] == command and receipt['environment'] == environment,
            'Reader command/environment differs')
    for key, value in (('process_timeout_seconds', supervisor.TIMEOUT),
                      ('cleanup_timeout_seconds', supervisor.CLEANUP_TIMEOUT),
                      ('maximum_process_group_rss_bytes', supervisor.RSS_LIMIT),
                      ('native_file_limit_bytes', supervisor.FILE_LIMIT),
                      ('stdout_capture_limit_bytes', supervisor.FILE_LIMIT+supervisor.PIPE_CHUNK)):
        require(type(receipt[key]) is int and receipt[key] == value, 'Reader resource policy differs')
    require(type(receipt['kernel_monitor_samples']) is int and receipt['kernel_monitor_samples'] > 0
            and type(receipt['observed_peak_process_group_rss_bytes']) is int
            and 0 <= receipt['observed_peak_process_group_rss_bytes'] <= supervisor.RSS_LIMIT,
            'Reader resource observations missing')
    before, after = receipt['identity'], receipt['leader_identity_before_reap']
    require(all(type(before[k]) is int and type(after[k]) is int and before[k] == after[k]
                for k in ('pid', 'ppid', 'pgid', 'birth_seconds', 'birth_microseconds'))
            and before['pid'] == before['pgid'] == receipt['pid'] and after['status'] == 5
            and before['birth_seconds'] > 0 and 0 <= before['birth_microseconds'] < 1000000,
            'Reader birth identity or terminal process state differs')
    require(receipt['benchmark_samples'] == 0 and receipt['source_work_qualified'] is receipt['chart_admission'] is False,
            'Reader receipt grants unrelated qualification')
    request_keys = ('kind', 'command', 'environment', 'cwd', 'started_at', 'process_timeout_seconds',
        'cleanup_timeout_seconds', 'inherited_common_mutex', 'common_mutex_inode', 'stop_signals', 'cleanup_errors',
        'benchmark_samples', 'stdin_bytes', 'stdin_sha256', 'maximum_process_group_rss_bytes',
        'native_file_limit_bytes', 'stdout_capture_limit_bytes', 'stdout_transport', 'stderr_transport',
        'source_work_qualified', 'chart_admission')
    start = dict({k: receipt[k] for k in request_keys}, status='starting', native_process_started=False,
                 observed_peak_process_group_rss_bytes=0, kernel_monitor_samples=0)
    require(read(folder/'start.json') == start and read(folder/'active.json') ==
            dict(start, status='running', native_process_started=True, pid=receipt['pid'],
                 pgid=receipt['pgid'], identity=before), 'Reader start/active/final receipts differ')
    require(receipt['stdin_bytes'] == 0 and receipt['stdin_sha256'] == hashlib.sha256(b'').hexdigest(),
            'Source reader received unexpected stdin')
    for stream in ('stdout', 'stderr'):
        path = folder/(stream+'.bin')
        require(receipt[stream+'_bytes'] == path.stat().st_size == 0
                and receipt[stream+'_sha256'] == sha(path), 'Reader stream receipt differs')


def qualify(args, lock):
    require(not args.output.exists() and args.output.resolve().parent == PACKET, 'Use a fresh source-count output')
    manifest = read(args.review_manifest)
    require(sha(args.review_manifest) == args.review_manifest_sha256
            and manifest['schema'] == 'kotlin-source-owner-review-v1', 'Wrong reviewed ownership manifest')
    pins = dict(PINS)
    for path, digest in manifest['pins'].items():
        path = ROOT/path
        require(path.resolve().is_relative_to(ROOT) and (path not in pins or pins[path] == digest), 'Conflicting review pin')
        pins[path] = digest
    require({COUNTER, REPLAY, REVIEW, DURABLE, RUN/'terminal.json', PACKET/'fixture-contract.json'} <= set(pins),
            'Missing explicit source-owner evidence pins')
    pins[Path(__file__).resolve()] = args.controller_sha256
    pins[args.review_manifest.resolve()] = args.review_manifest_sha256
    verify(pins)
    plan, report, terminal = read(PLAN), read(RUN/'report.json'), read(RUN/'terminal.json')
    require(plan['controller'] == str(READER) and plan['controller_sha256'] == PINS[READER]
            and plan['output'] == str(RUN) and report['plan_sha256'] == PINS[PLAN], 'Reader plan/controller differs')
    for path, digest in report['pins'].items():
        path = Path(path)
        require(path not in pins or pins[path] == digest, 'Conflicting retained input pin')
        pins[path] = digest
    verify(pins)
    require(all(report['pins'].get(p) == d for p, d in plan['pins'].items()), 'Reader omitted prepared pins')
    require(report['status'] == terminal['status'] == 'read-awaiting-canonical-owner-review'
            and terminal['report_sha256'] == PINS[RUN/'report.json'] and report['active'] is None
            and report['reader_evidence_validated'] is terminal['reader_evidence_validated'] is True
            and report['native_launch_requests'] == report['native_processes_started'] == terminal['native_processes_started'] == 2
            and all(terminal[k] == [] for k in ('integrity_errors', 'artifact_errors', 'process_receipt_errors'))
            and report['integrity_errors'] == report['process_receipt_errors'] == []
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
            'Reader did not close cleanly')
    reader, counter = module(READER, PINS[READER]), module(COUNTER, pins[COUNTER])
    supervisor = reader.module()
    closure = artifact_closure(terminal, reader)
    native_dir = RUN/'native-reader'
    options = plan['runtime_flags']+['-Duser.home='+str(native_dir/'home'), '-Djava.io.tmpdir='+str(native_dir/'tmp')]
    native_report = read(native_dir/'sources/report.json')
    reader.validate_reader(native_report, dict(plan, inputs=report['inputs']),
                           native_dir/'sources', RUN/'probe-classes', options)
    durable = read(DURABLE)
    require(durable['exit_code'] == 0 and durable['actual_command_started'] is True and not durable.get('error')
            and durable['stop_signals'] == [], 'Reader durable command did not close cleanly')
    observed = []
    for name, kind in (('diagnostic-compile', 'diagnostic-compile'), ('native-reader', 'native-source-reader')):
        folder = RUN/name
        receipt = read(folder/'process.json')
        validate_process(receipt, kind, folder, plan, durable['command_pid'], supervisor, reader)
        observed.append(dict(kind=kind, pid=receipt['pid'], pgid=receipt['pgid']))
    require(observed == report['native_processes'], 'Reader native process ledger differs')
    compiled = read(reader.COMPILED)
    require({(p['id'], i['role'], i['path'], i['sha256']) for p in compiled['profiles'] for i in p['physical_inputs'] if i['counted']}
            == {(p['id'], i['role'], i['path'], i['sha256']) for p in plan['profiles'] for i in plan['inputs'] if i['id'] in p['inputs']},
            'Reader authored inputs differ from the retained compiled forms')
    replay = read(REPLAY)
    require(counter.replay(PLAN, native_dir/'sources') == replay, 'Saved source-count replay differs')
    files, profiles = reviewed_counts(plan, replay, manifest['expected_totals'],
        {item['id']: item['source_sha256'] for item in native_report['items']})
    for key, row in files.items():
        row['native_artifacts'] = {name: terminal['available_evidence']['native-reader/sources/'+key+'/'+name]
                                  for name in ('source.kt', 'psi-source.kt', 'psi.json')}
    result = dict(schema='kotlin-qualified-source-counts-v1', status='twenty-retained-canonical-source-counts-qualified',
        reviewed_at=datetime.now(timezone.utc).isoformat(), controller=str(Path(__file__).resolve()),
        controller_sha256=args.controller_sha256, review_manifest=str(args.review_manifest.resolve()),
        review_manifest_sha256=args.review_manifest_sha256, verified_closure_pin_count=len(pins),
        source_plan=str(PLAN), source_plan_sha256=PINS[PLAN], native_artifact_closure=closure,
        report=str(RUN/'report.json'), report_sha256=PINS[RUN/'report.json'],
        terminal=str(RUN/'terminal.json'), terminal_sha256=pins[RUN/'terminal.json'],
        replay=str(REPLAY), replay_sha256=pins[REPLAY], counter_sha256=pins[COUNTER],
        rule_version=counter.RULE_VERSION, grammar=counter.GRAMMAR, fixture_checks=replay['fixture_checks'],
        files=files, profiles=profiles, canonical_loc_qualified=True, formatted_loc_qualified=False,
        formatted_loc=None, source_work_qualified=False, full_timings_qualified=False, chart_admission=False,
        native_processes_started=0, subject_recompilations=0, subject_main_invocations=0,
        original_native_processes=2, common_mutex_inode=79859134)
    verify(pins)
    artifact_closure(terminal, reader)
    verify_lock(lock)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output), profiles=len(profiles), canonical_loc_qualified=True)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--review-manifest', type=Path, required=True)
    parser.add_argument('--review-manifest-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site
            and sys.flags.dont_write_bytecode and not sys.flags.optimize, 'Use retained Python with -I -S -B')
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        verify_lock(lock)
        qualify(args, lock)


if __name__ == '__main__':
    main()
