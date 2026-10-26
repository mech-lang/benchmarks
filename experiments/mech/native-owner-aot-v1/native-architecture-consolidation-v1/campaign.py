"""Evidence checks for this one predeclared complete-process campaign."""
import hashlib
import math
import subprocess
from pathlib import Path
from study import HERE, ROOT, process, read, source_state, subjects, inputs, check_native

COMPLETE = 'all-96-complete-processes-output-counters-pins-and-cleanup-verified'
CONTROLLER = 'experiments/janet/knucleotide-bytes-v1/process.py'
CORRECTNESS = {
    'none-check', 'none-tree', 'scalar-runtime-check', 'scalar-runtime-tree',
    'program-runtime-check', 'program-runtime-tree', 'host-runtime-check',
    'host-runtime-tree', 'scalar-compiler-check', 'program-compiler-check',
    'native-unit', 'native-facts', 'native-lines', 'worker-credit', 'native-catalog',
    'scalar-integration', 'program-integration', 'scalar-unit', 'native-source-lowering',
    'source-contracts', 'source-applications', 'source-assignment', 'benchmark-policy-unit',
    'format', 'unsafe', 'unsafe-contract', 'runtime-factory-safety',
    'build-analysis-layout', 'warning-policy', 'module-layout', 'planning-quarantine',
    'workflow-contracts', 'process-contracts',
}
PROCESS_TESTS = {
    'canonical-cli-unit-contracts', 'canonical-cli-public-qualification',
    'canonical-hosted-contracts', 'canonical-hosted-linked', 'canonical-policy-kernel',
    'canonical-policy-contracts', 'canonical-policy-linked',
}


def contained(path):
    candidate = (HERE / path).resolve()
    assert candidate.is_relative_to(HERE.resolve()), path
    return candidate


def evidence(ref):
    path = contained(ref['path'])
    assert process.sha(path) == ref['sha256'], path
    return read(path)


def stages(rows, head, required):
    assert len({row['stage'] for row in rows}) == len(rows)
    assert required <= {row['stage'] for row in rows}
    for row in rows:
        assert row['head'] == head and row['exit_code'] == 0, row['stage']
        if row['counts']:
            assert sum(int(count[0]) for count in row['counts']) > 0, row['stage']
            assert all(int(count[1]) == 0 for count in row['counts']), row['stage']
    return {row['stage']: row for row in rows}


def prerequisites(plan):
    assert plan['status'] == 'frozen-before-first-primary-sample'
    targets, pins, f, i = subjects()
    assert source_state() == f['source'] and not f['source']['status']
    assert plan['final_compiler_source'] == f['source']['commit']
    assert plan['implementation_base'] == i['source']['commit'] and not i['source']['status']
    assert source_state(Path(i['workspace'])) == i['source']
    assert plan['subject_pins'] == pins
    assert plan['bootstrap_seed'] == 2026102595 and plan['bootstrap_resamples'] == 20000
    assert plan['primary_observations'] == 192 and plan['warmups'] == plan['excluded_outliers'] == 0
    assert plan['acceptance_upper_95_percent'] == {'F/I': 1.0, 'F/W': 1.0, 'F/R': 0.0}
    block = [['F','I','R','W'], ['I','W','F','R'], ['W','R','I','F'], ['R','F','W','I']]
    assert plan['session_1'] == block * 6 and plan['session_2'] == list(reversed(block * 6))
    inputs()
    for name in ['measure.py', 'analyze.py', 'qualify.py', 'campaign.py', 'study.py']:
        assert str((HERE / name).relative_to(ROOT)) in plan['controller_pins']
    assert CONTROLLER in plan['controller_pins']
    for path, digest in plan['controller_pins'].items():
        assert process.sha(ROOT / path) == digest, path
    gate = read(HERE / 'qualification.json')
    assert process.sha(HERE / 'qualification.json') == plan['qualification_sha256']
    assert gate['source'] == f['source'] and gate['baseline_source'] == i['source']
    assert gate['proceed_to_primary'] is True
    checks = gate['checks']
    rows = stages(evidence(checks['correctness']), f['source']['commit'], CORRECTNESS)
    for name in ['native-unit','native-facts','native-lines','worker-credit','native-catalog',
                 'scalar-integration','program-integration','scalar-unit','native-source-lowering',
                 'source-contracts','source-applications','source-assignment','benchmark-policy-unit']:
        assert rows[name]['counts'], name
    rows = stages(evidence(checks['generated_processes']), f['source']['commit'], PROCESS_TESTS)
    assert all(rows[name]['counts'] for name in PROCESS_TESTS)
    baseline = stages(evidence(checks['baseline_correctness']), i['source']['commit'],
                      {'native-unit', 'native-facts', 'native-lines', 'worker-credit', 'native-catalog'})
    assert all(row['counts'] for row in baseline.values())
    changed = evidence(checks['changed_inputs'])
    assert changed['status'] == 'seven-independent-oracles-and-fourteen-pinned-AOT-executions-verified'
    assert changed['source'] == changed['source_after'] == f['source']
    assert changed['pins'] == {s: pins[s] for s in ('F','I')}
    assert len(changed['cases']) == 7 and all(len(c['executions']) == 2 for c in changed['cases'])
    assert {c['name'] for c in changed['cases']} == {
        'one-key-short', 'query-boundaries', 'random-single-row', 'random-short-rows',
        'random-ordinary-rows', 'growth-and-partial-credit', 'repeated-wide-key'}
    assert all({e['subject'] for e in c['executions']} == {'F','I'} for c in changed['cases'])
    code = evidence(checks['guest_code'])
    assert code['F_source'] == f['source'] and code['I_source'] == i['source']
    assert len(code['files']) == 6 and all(row['equal'] and row['F'] == row['I'] for row in code['files'])
    files = {row['file']: row for row in code['files']}
    assert set(files) == {'program.o','program.mecb','native-descriptor.json','native-descriptor.bin','object-identity.bin','native-resources.json'}
    assert files['program.o']['F'] == f['object_sha256'] == i['object_sha256'] == read(HERE / 'retained-controls.json')['W']['object_sha256']
    for subject, receipt in [('F',f), ('I',i)]:
        project = Path(receipt['executable'] + '.project')
        assert all(process.sha(project / name) == row[subject] for name, row in files.items())
    representatives = evidence(checks['representative_objects'])
    assert representatives['F_source'] == f['source'] and representatives['I_source'] == i['source']
    assert len(representatives['files']) == 32 and all(row['equal'] and row['F'] == row['I'] for row in representatives['files'])
    expected = {f'{fixture}-{variant}.{suffix}' for fixture in ['aggregate','owner','owner-words','scalar']
                for variant in ['source','decoded'] for suffix in ['o','mecb','metadata.json','descriptor.json']}
    assert {row['path'] for row in representatives['files']} == expected
    return targets, pins, f, i


def committed_before_sampling(revision, plan):
    files = ['plan.json', 'qualification.json', plan['baseline_receipt'], plan['candidate_receipt']]
    files += [ref['path'] for ref in read(HERE / 'qualification.json')['checks'].values()]
    paths = [str((HERE / name).relative_to(ROOT)) for name in files] + list(plan['controller_pins'])
    for path in paths:
        blob = subprocess.check_output(['git','-C',str(ROOT),'show',revision + ':' + path])
        assert hashlib.sha256(blob).hexdigest() == process.sha(ROOT / path), path


def observation(sample, session, plan, targets, identities, policy):
    order, position, subject = sample['order'], sample['position'], sample['subject']
    assert subject == plan[f'session_{session}'][order][position]
    expected = f'primary-session-{session}/{order:02d}-{position}-{subject}/process.json'
    assert sample['process'] == expected
    path = contained(expected)
    assert process.sha(path) == sample['process_sha256']
    raw = read(path)
    assert raw['exit_status'] == 0 and raw['quantitative_benchmark'] is True
    assert raw['inherited_common_mutex'] is True and raw['deadline_seconds'] == 30
    assert raw['cleanup_errors'] == [] and raw['group_closed'] is True and raw['reaped'] is True
    assert raw['signals'] == [] and 'error' not in raw and not raw.get('observer_still_waiting')
    assert raw['controller_sha256'] == plan['controller_pins'][CONTROLLER]
    assert math.isfinite(raw['elapsed_seconds']) and raw['elapsed_seconds'] > 0
    assert sample['seconds'] == raw['elapsed_seconds']
    assert sample['maximum_rss_bytes'] == raw['maximum_rss_bytes'] > 0
    identity = raw['birth_identity']
    birth = (identity['pid'], identity['birth_seconds'], identity['birth_microseconds'])
    assert birth not in identities
    identities.add(birth)
    assert process.sha(path.parent / 'stdout.bin') == sample['stdout_sha256'] == plan['output_sha256']
    assert (path.parent / 'stderr.bin').is_file()
    native = path.parent.parent / (path.parent.name + '.native.json')
    command = [str(targets[subject])]
    if subject != 'R':
        command += [str(policy), str(native), '--']
        assert process.sha(native) == sample['native_sha256']
        assert check_native(native) == sample['native']
    else:
        assert sample['native_sha256'] is None and sample['native'] is None
    assert raw['command'] == command and sample['verified'] is True


def validate_reports(reports, plan):
    targets, pins, f, _ = prerequisites(plan)
    assert [r['session'] for r in reports] == [1, 2]
    assert len({r['evidence_revision'] for r in reports}) == 1
    committed_before_sampling(reports[0]['evidence_revision'], plan)
    _, policy, _ = inputs()
    identities = set()
    for report in reports:
        session = report['session']
        assert report['status'] == COMPLETE and len(report['samples']) == 96
        assert report['source'] == report['source_after'] == f['source']
        assert report['pins'] == pins and report['orders'] == plan[f'session_{session}']
        assert report['excluded_warmups'] == report['excluded_outliers'] == 0
        assert report['plan_sha256'] == process.sha(HERE / 'plan.json')
        assert report['driver_sha256'] == process.sha(HERE / 'measure.py')
        assert report['controller_sha256'] == plan['controller_pins'][CONTROLLER]
        for key in ['input_sha256','policy_sha256','canonical_data_sha256','source_sha256','bytecode_sha256']:
            assert report[key] == plan[key]
        assert [(r['order'], r['position']) for r in report['samples']] == [(o, p) for o in range(24) for p in range(4)]
        for sample in report['samples']:
            observation(sample, session, plan, targets, identities, policy)
    assert len(identities) == 192
