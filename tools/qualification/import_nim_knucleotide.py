"""Offline, additive admission of the exact qualified Nim preencoded candidate."""
import argparse
import copy
import difflib
import hashlib
import math
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from qualification import import_bqn_knucleotide as shared
BASE = 'experiments/nim/optimization-v1/'
ADMISSION = BASE+'admission-v1/'
PLAN, RESULTS, PREPARED = [ADMISSION+name+'.json' for name in ['plan', 'results', 'prepared']]
KEY = 'knucleotide:nim-knucleotide-preencoded-v1'
PARENT = 'knucleotide:nim-knucleotide-optimized'
SOURCE = BASE+'sources/knucleotide-preencoded.nim'
SOURCE_SHA = 'b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b'
PARENT_SHA = '9b5a250702745e4ade2bd0488444aa6a4c393c198da57be7fedd7bd8b04732a8'
MGET_SHA = '7ece7878152461f837d85045c8e5a91c7dcfa2d0adc5bd912abd1168fecee60d'
SOURCE_REVISION = 'd20bb396f396b46e0c0f40e2ecbd658e4bbae86e'
COMPILER_SHA = '5f09b756aaaa46af99ae72e66f54ed5d4e41343e8440df07046712a506857a1f'
COMPILER_COMMIT = '8e8fbf60693418dc95bb0d762fd660231d08a583'
COMPILER_ARCHIVE_SHA = '130a43eff76c1c3cc78b89329a7efd892c1f65839dbc6d8e53651f3f77516fe5'
CONTROLLER_SHA = '86b749e25164574fb5b0119e2411b6510dcaf0714f229e4c67f601a0dfa6980d'
OLD_CONTROLLER_SHA = '54174d3524eef00c0bb53b37f2a98853176f6eae6590ae8dd3963ad51338c1af'
PROCESS_SHA = '313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
CORPUS = shared.CORPUS
IDENTITIES = ['parent', 'mgetorput', 'parent-native', 'mgetorput-native', 'preencoded', 'preencoded-native']
HASHES = dict(parent=PARENT_SHA, mgetorput=MGET_SHA, preencoded=SOURCE_SHA)
BINARY_HASHES = dict(parent='d093b5ba4a32d7934a4214bb3fe03ac1973700d8d381b356c3cca27443449f61',
    mgetorput='8ff7a32b9e6fb7eccd20267461c5917d9f89d25339d0c138dc9cb8b01c84317d',
    preencoded='3acabfc9faaaeccfb568ca1394c85051e8caef5ff81fd0b7deb8115c8aeef4e6')
NATIVE_DEPENDENCIES = {
    '/opt/homebrew/Cellar/llvm@22/22.1.8/bin/clang-22': '012b35304481c5d5db6b57f20e144fb78f198ca9db14aa0b8db72cd2e493e12d',
    '/opt/homebrew/Cellar/pcre/8.45/lib/libpcre.1.dylib': 'fa6189ca7f9be97b18a9868806c8dfa5ff655c61f8985f6810f25bb6ae9acd10',
    '/opt/homebrew/Cellar/gmp/6.3.0/lib/libgmp.10.dylib': '571ffb9eb5b5110cda32f62197c1f039e5627d66524ba47bb0774eca184532b9',
}
PACKETS = {'full': ('additional-full-v1', IDENTITIES, True),
           'bounded': ('additional-bounded-v1', IDENTITIES[2:], False),
           'control_full': ('full-matched-v1', IDENTITIES[:2], True),
           'control_bounded': ('bounded-v1', IDENTITIES[:2], False)}
REFS = dict(importer='tools/qualification/import_nim_knucleotide.py',
    shared_helpers='tools/qualification/import_bqn_knucleotide.py',
    restoration=BASE+'runtime-restoration.json', original_plan=BASE+'plan.json',
    matched_build=BASE+'matched-build-plan.json', additional_build=BASE+'additional-build-plan.json',
    ownership=BASE+'source-ownership-v1/knucleotide-preencoded-counts.json',
    corpus=CORPUS, builder=BASE+'build_matched.py', additional_builder=BASE+'build_additional.py',
    restore_tool=BASE+'restore_runtime.py')
REFS.update(runtime_version=BASE+'runtime-version.json', target_equivalence=BASE+'target-binary-equivalence.json')
REFS.update({key: BASE+folder+'/report.json' for key, (folder, _, _) in PACKETS.items()})
sha, pin, load, encoded, require, relative = shared.sha, shared.pin, shared.load, shared.encoded, shared.require, shared.relative


def variant_base(identity):
    return identity.removesuffix('-native')


def stage(identity):
    return BASE+'.build/'+('matched-v1' if identity in IDENTITIES[:2] else 'additional-v1')+'/'+identity


def recorded_root(report):
    rows = report.get('cases', [])
    require(rows and rows[0].get('source') in IDENTITIES, 'No recorded Nim command')
    row = rows[0]; suffix = '/'+stage(row['source'])+'/knucleotide'
    command = row.get('command')
    require(isinstance(command, list) and len(command) == 1 and isinstance(command[0], str)
            and Path(command[0]).is_absolute() and command[0].endswith(suffix), 'Wrong native executable suffix')
    prefix = command[0][:-len(suffix)]
    require(prefix and '..' not in Path(prefix).parts and Path(prefix).as_posix() == prefix, 'Unsafe recorded repository root')
    return prefix


def make_plan(root=ROOT):
    root = Path(root)
    evidence = {name: pin(root, path) for name, path in REFS.items()}
    for label, (folder, identities, _) in PACKETS.items():
        for identity in identities:
            evidence[label+'_build_'+identity] = pin(root, BASE+folder+'/builds/'+identity+'/build.json')
        if label in ['full', 'bounded']:
            for name in ['controller.py', 'process_controller.py', 'build-plan.json']:
                evidence[label+'_'+name] = pin(root, BASE+folder+'/'+name)
    return dict(schema='nim-knucleotide-admission-plan.v1', key=KEY, parent=PARENT,
        source=pin(root, SOURCE), retained_source_revision=SOURCE_REVISION,
        selected_configuration='preencoded', recorded_execution_root=recorded_root(load(root/REFS['full'])),
        input=shared.INPUT, expected=shared.OUTPUT, evidence=evidence,
        author_context=copy.deepcopy(shared.AUTHOR_CONTEXT),
        selection='Lowest retained three-sample median among six matched configurations. Generic/native pairs have identical executable digests; no CPU-target speedup or global optimality is claimed.')


def check_restoration(evidence, ref, recorded, local_artifacts):
    receipt = evidence.document(ref); root = evidence.root
    require(receipt.get('schema') == 'nim-runtime-restoration.v1'
        and receipt.get('compiler_source_commit') == COMPILER_COMMIT and receipt.get('compiler_sha256') == COMPILER_SHA
        and receipt.get('archive_sha256') == COMPILER_ARCHIVE_SHA and receipt.get('checked_distribution_files') == 6770
        and receipt.get('missing') == [] and receipt.get('changed') == [], 'Restored Nim identity differs')
    proposal = evidence.document(dict(path=receipt['historical_proposal'], sha256=receipt['historical_proposal_sha256']))
    require(proposal['compiler_archive_sha256'] == COMPILER_ARCHIVE_SHA
            and proposal['compiler_source_commit'] == COMPILER_COMMIT and proposal['compiler_archive_url'] == receipt['archive_url'],
            'Historical compiler distribution differs')
    expected = {}
    for path, digest in proposal['pins'].items():
        if '/nim/nim-2.2.12/' in path:
            suffix = path.split('/nim/nim-2.2.12/', 1)[1]
            require(suffix not in expected or expected[suffix] == digest, 'Conflicting historical distribution pins')
            expected[suffix] = digest
    require(receipt.get('checked_distribution_pins') == expected and len(expected) == 6770
            and expected['bin/nim'] == COMPILER_SHA, 'Distribution pin set incomplete')
    distribution = relative(root, receipt['distribution'], recorded)
    require(distribution == BASE+'.build/nim/nim-2.2.12'
            and relative(root, receipt['compiler'], recorded) == distribution+'/bin/nim', 'Wrong restored distribution path')
    if local_artifacts:
        for path, digest in expected.items():
            require(sha(root/distribution/path) == digest, 'Changed local compiler/distribution file: '+path)
        require(sha(root/relative(root, receipt['archive'], recorded)) == COMPILER_ARCHIVE_SHA, 'Changed distribution archive')
    return receipt, proposal


def check_build_plans(evidence, plan, restoration, local_artifacts):
    matched = evidence.document(plan['evidence']['matched_build'])
    additional = evidence.document(plan['evidence']['additional_build'])
    require(matched.get('schema') == 'nim-matched-build-plan.v1'
            and additional.get('schema') == 'nim-additional-build-plan.v1', 'Wrong build plan schema')
    require([r['id'] for r in matched['commands']] == IDENTITIES[:2]
            and [r['id'] for r in additional['commands']] == IDENTITIES[2:], 'Wrong prepared build cohort')
    historical = evidence.document(dict(path=matched['historical_build'], sha256=matched['historical_build_sha256']))
    recorded = plan['recorded_execution_root']
    distribution = str(Path(recorded)/(BASE+'.build/nim/nim-2.2.12'))
    builds = {}
    for document in [matched, additional]:
        require(document['compiler_sha256'] == COMPILER_SHA and document['runtime_restoration'] == REFS['restoration']
                and document['runtime_restoration_sha256'] == plan['evidence']['restoration']['sha256'], 'Build/compiler receipt differs')
        require(document['historical_build'] == matched['historical_build']
                and document['historical_build_sha256'] == matched['historical_build_sha256']
                and document['pinned_native_build_dependencies'] == matched['pinned_native_build_dependencies'], 'Matched build dependencies differ')
        for row in document['commands']:
            identity = row['id']; folder = str(Path(recorded)/stage(identity))
            require(row['source_sha256'] == HASHES[variant_base(identity)]
                    and row['source'] == folder+'/knucleotide.nim' and row['binary'] == folder+'/knucleotide', 'Source/build identity differs')
            wanted = list(historical['command']); wanted[0] = distribution+'/bin/nim'; wanted[-1] = row['source']
            for i, arg in enumerate(wanted):
                if arg.startswith('--lib:'): wanted[i] = '--lib:'+distribution+'/lib'
                elif arg.startswith('--nimcache:'): wanted[i] = '--nimcache:'+folder+'/nimcache'
                elif arg.startswith('--out:'): wanted[i] = '--out:'+row['binary']
            if identity.endswith('-native'): wanted.insert(-1, '--passC:-mcpu=apple-m3')
            require(row['command'] == wanted, 'Unreviewed compiler flag or path change')
            builds[identity] = row
    require(additional['parent_build_plan_sha256'] == plan['evidence']['matched_build']['sha256']
            and additional['build_tool_sha256'] == plan['evidence']['additional_builder']['sha256'], 'Stale additional build recipe')
    dependencies = matched['pinned_native_build_dependencies']
    require(dependencies == NATIVE_DEPENDENCIES, 'Native dependency identity differs')
    if local_artifacts:
        for path, digest in dependencies.items(): require(sha(path) == digest, 'Changed native build dependency: '+path)
    return builds


def check_build_snapshot(evidence, ref, recipe, identity, packet, recorded, local_artifacts):
    receipt = evidence.document(ref); root = evidence.root
    require(receipt.get('schema') == ('nim-matched-compilation.v1' if identity in IDENTITIES[:2] else 'nim-additional-compilation.v1')
            and receipt.get('id') == identity and receipt.get('source_sha256') == recipe['source_sha256']
            and receipt.get('compiler_sha256') == COMPILER_SHA and receipt.get('command') == recipe['command']
            and receipt.get('exit_status') == 0 and receipt.get('build_only') is True
            and receipt.get('benchmark_processes') == 0, 'Incomplete or mismatched compilation')
    artifacts = receipt.get('artifacts', {})
    required = {'knucleotide', 'knucleotide.nim', 'build.stdout', 'build.stderr',
                'nimcache/@mknucleotide.nim.c', 'nimcache/@ptables.nim.c'}
    require(required <= set(artifacts) and artifacts['knucleotide'] == BINARY_HASHES[variant_base(identity)]
            and artifacts['knucleotide.nim'] == recipe['source_sha256'], 'Incomplete compiled artifact pins')
    for path, digest in artifacts.items():
        require(not Path(path).is_absolute() and '..' not in Path(path).parts
                and re.fullmatch('[0-9a-f]{64}', digest), 'Unsafe or invalid compiled artifact pin')
        if path in ['knucleotide.nim', 'build.stdout', 'build.stderr']:
            evidence.check(dict(path=BASE+packet+'/builds/'+identity+'/'+path, sha256=digest))
        if local_artifacts:
            require(sha(root/stage(identity)/path) == digest, 'Changed local build artifact: '+identity+'/'+path)
    # Loaded standard code is identified in the generated-C manifest. Historical
    # unused package search paths are not counted as application dependencies.
    require(not any('bigints' in name.lower() or 'gmp' in name.lower() for name in artifacts), 'Unexpected nonstandard Nim module')
    return receipt


def check_execution(evidence, plan, label, builds, local_artifacts=False):
    folder, identities, full = PACKETS[label]; root = evidence.root
    report = evidence.document(plan['evidence'][label]); recorded = plan['recorded_execution_root']
    require(report.get('schema') == 'nim-knucleotide-execution.v1' and report.get('status') == 'PASSED'
            and report.get('full_workload') is full and report.get('chart_admission') is False
            and 'active' not in report, 'Incomplete Nim execution report')
    require(recorded_root(report) == recorded and report.get('shared_process_controller_sha256') == PROCESS_SHA
            and report.get('controller_sha256') == (CONTROLLER_SHA if label in ['full', 'bounded'] else OLD_CONTROLLER_SHA), 'Wrong producer/controller identity')
    if label in ['full', 'bounded']:
        require(plan['evidence'][label+'_controller.py']['sha256'] == CONTROLLER_SHA
                and plan['evidence'][label+'_process_controller.py']['sha256'] == PROCESS_SHA
                and plan['evidence'][label+'_build-plan.json']['sha256'] == plan['evidence']['additional_build']['sha256'], 'Producer snapshot differs')
        require({**report['build_plan'], 'path': relative(root, report['build_plan']['path'], recorded)}
                == plan['evidence']['additional_build'] and report['included_controls'] is (label == 'full'), 'Wrong producer build plan')
    else:
        require(report['matched_build_plan_sha256'] == plan['evidence']['matched_build']['sha256'], 'Wrong control build plan')
    wanted_pins = {}
    for identity in identities:
        recipe = builds[identity]
        wanted_pins[stage(identity)+'/knucleotide.nim'] = recipe['source_sha256']
        wanted_pins[stage(identity)+'/knucleotide'] = BINARY_HASHES[variant_base(identity)]
        check_build_snapshot(evidence, plan['evidence'][label+'_build_'+identity], recipe, identity, folder, recorded, local_artifacts)
    require(report.get('pins') == wanted_pins, 'Sample executable/source pins differ')
    corpus = evidence.document(plan['evidence']['corpus'])
    cases = [r for r in corpus['cases'] if r['benchmark'] == 'knucleotide']
    require({r['case'] for r in cases} == shared.CASES and len(cases) == 14, 'Wrong bounded corpus')
    if full:
        cases = [dict(case='n25000000', stdin=dict(path=str(Path(recorded)/shared.INPUT['path']), sha256=shared.INPUT['sha256']), expected=shared.OUTPUT)]
    rounds = 3 if full else 1
    orders = report.get('orders', [])
    require(len(orders) == len(cases)*rounds, 'Missing matched execution round')
    require([(r.get('case'), r.get('sample')) for r in orders]
            == [(case['case'], sample) for case in cases for sample in range(1, rounds+1)]
            and all(len(r['order']) == len(identities) and set(r['order']) == set(identities) for r in orders), 'Matched cohort/order differs')
    rows = report.get('cases', [])
    require(len(rows) == len(cases)*rounds*len(identities)
            and [(r.get('case'), r.get('sample'), r.get('source')) for r in rows]
            == [(o['case'], o['sample'], identity) for o in orders for identity in o['order']], 'Missing complete process')
    by_case = {c['case']: c for c in cases}
    for row in rows:
        identity = row['source']; case = by_case[row['case']]
        require(row.get('command') == [builds[identity]['binary']] and row.get('input') == case['stdin']
                and row.get('expected') == case['expected'], 'Process input/command/reference differs')
        input_path = shared.INPUT['path'] if full else str(Path(CORPUS).parent/case['stdin']['path'])
        require(relative(root, row['stdin'], recorded) == input_path, 'Mixed or wrong recorded input root')
        if local_artifacts or not full:
            evidence.check(dict(path=input_path, sha256=case['stdin']['sha256']))
        if not full:
            evidence.check({**case['expected'], 'path': str(Path(CORPUS).parent/case['expected']['path'])})
        seconds = row.get('elapsed_seconds')
        require(isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and math.isfinite(seconds)
                and seconds > 0 and row.get('exit_code') == 0 and row.get('timed_out') is False
                and row.get('output_valid') is True, 'Failed or invalid complete process')
        require(row.get('started_utc') and row.get('finished_utc'), 'Missing process dates')
        for stream in ['stdout', 'stderr']:
            evidence.check({**row[stream], 'path': relative(root, row[stream]['path'], recorded)})
        require(row['stderr']['bytes'] == 0 and all(row['stdout'][field] == case['expected'][field]
                for field in ['bytes', 'sha256']), 'Complete output mismatch or diagnostic timing')
        directory = (root/relative(root, row['stdout']['path'], recorded)).parent
        require(relative(root, row['stderr']['path'], recorded) == str((directory/'stderr.bin').relative_to(root)), 'Mixed process streams')
        additions = {'source', 'case', 'sample', 'output_valid', 'input', 'expected', 'power_before', 'power_after'}
        raw = evidence.document(pin(root, directory/'process.json'))
        require(raw == {k: v for k, v in row.items() if k not in additions}, 'Raw process receipt differs')
        shared.check_power(row['power_before']); shared.check_power(row['power_after'])
    if full:
        require(report.get('medians') == {identity: statistics.median(r['elapsed_seconds'] for r in rows if r['source'] == identity)
                for identity in identities}, 'Stale producer medians')
    return report


def check_ownership(evidence, ref):
    receipt = evidence.document(ref)
    require(receipt.get('schema') == 'nim-source-ownership-review.v1' and receipt.get('source') == SOURCE
            and receipt.get('source_sha256') == SOURCE_SHA and receipt.get('independent_review_approved') is True,
            'Nim source count needs independent exact-source approval')
    require(receipt.get('application_loc') == 72 and receipt.get('physical_loc') == 64
            and receipt.get('retained_rule_proposed_loc') == 72
            and receipt.get('policy') == 'canonical-source-units-20261012-approved-rule-v2', 'Unapproved normalized LOC')
    lines = (evidence.root/SOURCE).read_text().splitlines(); ledger = receipt.get('line_ledger', [])
    require(len(ledger) == len(lines) and all(r['line'] == i+1 and r['source_text'] == text for i, (r, text) in enumerate(zip(ledger, lines))), 'Stale source line ledger')
    require(sum(r['retained_rule_units'] for r in ledger) == receipt['application_loc']
            and sum(bool(r['significant']) for r in ledger) == receipt['physical_loc']
            and all(isinstance(r['retained_rule_units'], int) and r['retained_rule_units'] >= 0
                    and len(r['retained_rule_owners']) == r['retained_rule_units'] for r in ledger), 'Owner count does not reconcile')
    work = receipt.get('required_work', {})
    require(work.get('status') == 'source-reviewed' and work.get('widths') == shared.WIDTHS
            and work.get('dna_length') == 125000000 and work.get('expected_updates') == 874999961,
            'Required hash-work source review incomplete')
    require(work.get('real_default_growing_tables') == 7 and work.get('default_initial_size_argument') == 32
            and work.get('actual_initial_bucket_slots') == 64, 'Default standard Table work review differs')
    parent = receipt['baseline_comparison']
    require(parent['source_sha256'] == PARENT_SHA and parent['canonical_retained_loc'] == 72 and parent['physical_loc'] == 64,
            'Historical Nim count changed')
    evidence.check(dict(path=parent['source'], sha256=PARENT_SHA))
    old = (evidence.root/parent['source']).read_text(); new = (evidence.root/SOURCE).read_text()
    require(receipt['source_delta']['unified_diff'] == ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile=parent['source'], tofile=SOURCE)), 'Reviewed application source delta differs')
    for ref in receipt['policy_evidence']: evidence.check(ref)
    restoration = evidence.document(receipt['runtime_restoration'])
    require(restoration['compiler_sha256'] == COMPILER_SHA and receipt['vendor_runtime_commit'] == COMPILER_COMMIT,
            'Vendor/compiler review binding differs')
    require(len(receipt['vendor_snapshot']) == 7, 'Incomplete reviewed vendor boundary')
    for ref in receipt['vendor_snapshot']:
        evidence.check(ref)
        require(ref['sha256'] == restoration['checked_distribution_pins'][ref['original_distribution_relative_path']]
                and ref['included_in_application_loc'] is False, 'Vendor snapshot is not the pinned distribution')
    generated = receipt['generated_source_evidence']
    require(generated['parent_build_source_sha256'] == SOURCE_SHA and generated['parent_build_compiler_sha256'] == COMPILER_SHA,
            'Generated source work review differs')
    refs = generated['artifacts']; require(len(refs) == 3, 'Incomplete generated source evidence')
    build_ref = next(r for r in refs if r['path'].endswith('/build.json'))
    compiled = evidence.document(build_ref)
    require(compiled['source_sha256'] == SOURCE_SHA and compiled['compiler_sha256'] == COMPILER_SHA
            and compiled['exit_status'] == 0, 'Generated evidence compiled another source')
    for ref in refs:
        evidence.check(ref)
        prefix = stage('preencoded-native')+'/'
        require(ref['original_generated_artifact'].startswith(prefix) and ref['included_in_application_loc'] is False,
                'Generated evidence is outside sampled build')
        suffix = ref['original_generated_artifact'][len(prefix):]
        if suffix != 'build.json': require(compiled['artifacts'][suffix] == ref['sha256'], 'Generated C/source build hash differs')
    return receipt


def reconcile(root=ROOT, local_artifacts=True):
    evidence = shared.Evidence(root); root = evidence.root; plan = load(root/PLAN)
    require(plan == make_plan(root) and plan['source'] == dict(path=SOURCE, sha256=SOURCE_SHA), 'Stale or changed admission plan')
    evidence.check(plan['source'])
    for ref in plan['evidence'].values(): evidence.check(ref)
    require(plan['evidence']['corpus']['sha256'] == shared.CORPUS_SHA, 'Changed reference corpus')
    restoration, proposal = check_restoration(evidence, plan['evidence']['restoration'], plan['recorded_execution_root'], local_artifacts)
    ownership = check_ownership(evidence, plan['evidence']['ownership'])
    builds = check_build_plans(evidence, plan, restoration, local_artifacts)
    reports = {label: check_execution(evidence, plan, label, builds, local_artifacts) for label in PACKETS}
    version = evidence.document(plan['evidence']['runtime_version'])
    require(version.get('schema') == 'nim-runtime-version.v1' and version.get('exit_status') == 0
            and version.get('compiler_sha256') == COMPILER_SHA and version.get('timed_benchmark') is False
            and version.get('stderr') == '' and version.get('command') == [str(Path(plan['recorded_execution_root'])/(BASE+'.build/nim/nim-2.2.12/bin/nim')), '--version']
            and 'Version 2.2.12' in version.get('stdout', '') and COMPILER_COMMIT in version['stdout'], 'Runtime version receipt differs')
    equivalence = evidence.document(plan['evidence']['target_equivalence'])
    require(equivalence.get('schema') == 'nim-target-binary-equivalence.v1'
            and equivalence.get('status') == 'identical-executable-bytes-for-each-source'
            and equivalence.get('plan_sha256') == plan['evidence']['additional_build']['sha256']
            and equivalence.get('binaries') == {name: BINARY_HASHES[variant_base(name)] for name in IDENTITIES},
            'CPU-target equivalence receipt differs')
    generated_build = next(r for r in ownership['generated_source_evidence']['artifacts'] if r['path'].endswith('/build.json'))
    require(generated_build['sha256'] == plan['evidence']['full_build_preencoded-native']['sha256'], 'Work review is not bound to sampled compiled artifact')
    full = reports['full']; selected = 'preencoded'
    require(min(full['medians'], key=lambda k: (full['medians'][k], k)) == selected, 'Selected configuration is not the lowest retained median')
    rows = [r for r in full['cases'] if r['source'] == selected]; samples = [r['elapsed_seconds'] for r in rows]
    meta = copy.deepcopy(rows)
    for row in meta: row.update(producer_report=plan['evidence']['full'], producer_plan=pin(root, PLAN))
    program = dict(key=KEY, id=KEY.split(':', 1)[1], original_program_key=PARENT, benchmark='knucleotide', language='nim',
        source_sha256=SOURCE_SHA, loc=ownership['application_loc'], physical_loc=ownership['physical_loc'],
        samples_seconds=samples, median_seconds=statistics.median(samples), sample_sd_seconds=statistics.stdev(samples),
        command=rows[0]['command'], build_command=builds[selected]['command'], build_cwd=str(Path(plan['recorded_execution_root'])/stage(selected)),
        binary_sha256=BINARY_HASHES[selected], sample_execution_metadata=meta)
    artifacts = [dict(path=path, sha256=digest) for path, digest in sorted(evidence.fingerprints.items())
                 if path != shared.INPUT['path'] and '/.build/' not in path]
    return dict(schema='nim-knucleotide-admission-results.v1', status='RECONCILED', plan=pin(root, PLAN), evidence=plan['evidence'],
        programs=[program], recorded_at=max(r['finished_utc'] for r in full['cases']), recorded_execution_root=plan['recorded_execution_root'],
        producer_report=plan['evidence']['full'], historical_data_preserved=True, new_observations=3,
        full_workload_n=25000000, selected_dna_length=125000000, input=shared.INPUT,
        matched_candidate_medians=full['medians'], matched_control_speedup=full['medians']['parent']/program['median_seconds'],
        identical_executable_pairs=[dict(generic=name, native=name+'-native', sha256=BINARY_HASHES[name]) for name in HASHES],
        selection=plan['selection'], author_context=plan['author_context'], source_count_review=ownership,
        toolchains=dict(nim=dict(version=version['stdout'], sha256=COMPILER_SHA, version_evidence=plan['evidence']['runtime_version'])),
        runtime_details=dict(restoration=plan['evidence']['restoration'], source_commit=COMPILER_COMMIT,
            archive_url=restoration['archive_url'], archive_sha256=COMPILER_ARCHIVE_SHA, checked_distribution_files=6770,
            recorded_sdk_path=proposal.get('sdk'), native_dependencies=load(root/REFS['matched_build'])['pinned_native_build_dependencies'],
            missing_old_controller_source='The first two-profile control cohort predates controller snapshots; its declared digest and raw processes remain retained. The admitted candidate uses exact snapshotted controllers.'),
        timing_boundary=full['timing_boundary'], runtime_environment=dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC'),
        required_power=dict(source='AC Power', low_power_mode=0), artifacts=artifacts)


def authorship_record(parent, results, evidence):
    result = copy.deepcopy(parent['authorship'])
    result.update(kind='ai-adapted', label='AI adapted · retained local predecessor', source_sha256=[SOURCE_SHA],
        origin_status='unresolved', parent_programs=[PARENT],
        retained_sources=[dict(source_sha256=SOURCE_SHA, url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)],
        parent_sources=[dict(program_key=PARENT, relationship='local predecessor', **ref) for ref in parent['authorship'].get('retained_sources', [])],
        ai=dict(tool='OpenAI Codex', models=[], model_family='Codex GPT-6', exact_model=None,
            status='family-identified-exact-model-unverified', matched_source_files=[SOURCE_SHA], total_source_files=1,
            evidence=[evidence['plan'], evidence['results']]),
        evidence=[evidence['plan']['path'], evidence['results']['path'], evidence['ownership']['path']])
    return result


def bound_authorship(data, profile, root=ROOT):
    root = Path(root); detail = profile.get('source_provenance_record') or {}
    require(profile.get('key') == KEY and profile.get('files') == [SOURCE_SHA]
            and detail.get('kind') == 'suite-authored-optimization' and detail.get('source_sha256') == SOURCE_SHA
            and detail.get('original_program_key') == PARENT and sha(root/SOURCE) == SOURCE_SHA
            and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest() == SOURCE_SHA, 'Unbound Nim authorship source')
    results = load(root/RESULTS); evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    require(results.get('schema') == 'nim-knucleotide-admission-results.v1' and results.get('status') == 'RECONCILED'
            and results['plan'] == evidence['plan'] and detail.get('admission') == evidence['results']
            and results['programs'][0]['key'] == KEY and results['programs'][0]['source_sha256'] == SOURCE_SHA
            and results['author_context'] == shared.AUTHOR_CONTEXT and detail.get('author_context') == results['author_context'], 'Nim authorship admission differs')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT], results, evidence)


def append_catalog(before, root=ROOT):
    root = Path(root).resolve(); results = load(root/RESULTS)
    require(results == reconcile(root, local_artifacts=False), 'Stale Nim reconciled results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'], 'Nim candidate already admitted')
    data = copy.deepcopy(before); parent = before['programs'][PARENT]; r = results['programs'][0]
    require(parent['files'] == [PARENT_SHA] and parent['loc'] == 72 and parent['physical_loc'] == 64, 'Retained Nim parent changed')
    bench = next(b for b in data['benchmarks'] if b['key'] == 'knucleotide')
    require(r['median_seconds'] >= bench['baseline_seconds'] and r['loc'] >= bench['baseline_loc'], 'New global minima need separate normalization review')
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    row = {k: copy.deepcopy(parent[k]) for k in ['benchmark', 'language', 'measurement_status', 'source_url', 'source_link_label', 'memory_policy', 'runtime_support'] if k in parent}
    row.update(key=KEY, id=r['id'], receipt_key=r['id'], files=[SOURCE_SHA], loc=r['loc'], physical_loc=r['physical_loc'],
        loc_metric='statement-normalized', loc_report=evidence['ownership']['path'], source_report=evidence['ownership']['path'],
        file_roles={SOURCE_SHA: dict(role='application', included_in_application_loc=True, normalized_loc=r['loc'], physical_loc=r['physical_loc'])},
        seconds=r['median_seconds'], samples=r['samples_seconds'], timing_sd=r['sample_sd_seconds'],
        x=r['loc']/bench['baseline_loc'], y=r['median_seconds']/bench['baseline_seconds'],
        formatted_loc=None, formatted_x=None, formatted_loc_status='pending', formatted_loc_complete=False, formatted_loc_evidence={},
        report=RESULTS, report_sha256=evidence['results']['sha256'], original_program_key=PARENT, local_adaptation=True,
        source_provenance='Suite-authored optimization of retained Nim source; one-time byte encoding and ordinary Table mutable-value API. Predecessor origin remains unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization', original_program_key=PARENT, source_sha256=SOURCE_SHA,
            admission=evidence['results'], author_context=results['author_context'], origin_status='inherited-unresolved'),
        retained_source_revision=SOURCE_REVISION, command=r['command'], build_command=r['build_command'], build_cwd=r['build_cwd'],
        cwd=results['recorded_execution_root'], binary_sha256=r['binary_sha256'], execution_mode='aot', native_observations=3,
        timing_alias_of=None, runtime_arguments=[], runtime_policy='Nim 2.2.12; ORC; seven private standard Table worker threads; generic CPU build',
        runtime_environment=results['runtime_environment'], sample_execution_metadata=r['sample_execution_metadata'],
        timing_boundary=results['timing_boundary'], timing_summary='Three fresh matched full-process observations; lowest retained candidate median. Generic/native pairs produce identical executable bytes. Historical measurements remain exact.',
        required_work_validated=dict(status='source-reviewed-with-bounded-and-full-output', evidence=evidence['ownership'], expected_updates=874999961),
        algorithm=dict(strict=True, status='required-work-reviewed', native_benchmark_kernel=False,
            reason='One standard uint8 mapping pass; seven independent standard Tables. Every overlapping window performs mgetOrPut plus increment, retaining default initialization and growth; no query-specific scan or precomputed answer.'),
        source_accounting=dict(policy='application-loc-v1', application_loc=r['loc'], physical_loc=r['physical_loc'],
            evidence=evidence['ownership']['path'], review_sha256=evidence['ownership']['sha256'], files=[]),
        full_output_validation=dict(all_three_samples_passed=True, evidence=evidence['full']), chart_admission=dict(historical_reports_unchanged=True, **evidence),
        measured_backend=dict(key='nim', execution='aot', label='Nim', verified=True, evidence=dict(verified=True, report=RESULTS,
            report_sha256=evidence['results']['sha256'], command=r['command'], source_sha256=[SOURCE_SHA],
            runtime_receipt=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'],
                field='/toolchains/nim/version', value=results['toolchains']['nim']['version'], value_encoding='literal-saved-string'))))
    row['authorship'] = authorship_record(parent, results, evidence)
    require(SOURCE_SHA not in data['files'], 'Selected source already present')
    data['files'][SOURCE_SHA] = dict(name=Path(SOURCE).name, path=SOURCE, sha256=SOURCE_SHA, code=(root/SOURCE).read_text(), archive_path=SOURCE)
    data['programs'][KEY] = row; data['program_inventory'][KEY] = copy.deepcopy(row)
    group = next(g for g in bench['groups'] if g['language'] == 'nim'); group['programs'].append(KEY)
    candidates = [data['programs'][key] for key in group['programs']]
    group['fast'] = min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))['key']
    group['small'] = min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))['key']
    for section, prefix in [('reference_summary', ''), ('formatted_reference_summary', 'formatted_')]:
        for summary in data[section]:
            if summary['lang'] != 'nim': continue
            groups = [g for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'nim']
            for kind in ['fast', 'small']:
                selected = [data['programs'][g[prefix+kind]] for g in groups if g.get(prefix+kind)]
                summary[kind] = dict(x=statistics.geometric_mean(p['formatted_x' if prefix else 'x'] for p in selected),
                    y=statistics.geometric_mean(p['y'] for p in selected)) if selected else None
    for ref in [*evidence.values(), *results['artifacts'], dict(path=SOURCE, sha256=SOURCE_SHA)]: data['archive_paths'][ref['path']] = ref['path']
    data['nim_knucleotide_audit'] = dict(schema='nim-knucleotide-catalog-extension.v1', appended_programs=[KEY], evidence=evidence,
        measured_at=results['recorded_at'], new_observations=3, source_files_added=1, old_profiles_unchanged=True, old_baselines_unchanged=True)
    for pool in ['programs', 'program_inventory', 'files', 'archive_paths']:
        require(all(data[pool][key] == old for key, old in before[pool].items()), 'Historical '+pool+' changed')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expected-before-sha256'); parser.add_argument('--expected-prepared-sha256')
    args = parser.parse_args(); require(args.prepare != args.apply, 'Choose exactly one of --prepare/--apply')
    catalog = ROOT/'data/benchmarks.json'
    if args.prepare:
        shared.write(ROOT/PLAN, make_plan()); shared.write(ROOT/RESULTS, reconcile())
        shared.write(ROOT/PREPARED, append_catalog(load(catalog)))
        print(dict(before_sha256=sha(catalog), prepared_sha256=sha(ROOT/PREPARED), results_sha256=sha(ROOT/RESULTS), canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256, 'Apply requires reviewed hashes')
        require(sha(catalog) == args.expected_before_sha256 and sha(ROOT/PREPARED) == args.expected_prepared_sha256, 'Reviewed before/preview identity differs')
        after = append_catalog(load(catalog)); require(encoded(after) == (ROOT/PREPARED).read_bytes(), 'Prepared result no longer reproduces')
        require(sha(catalog) == args.expected_before_sha256, 'Canonical changed during reconciliation')
        shared.write(catalog, after)
        print('Added one qualified Nim preencoded candidate; all historical records retained.')


if __name__ == '__main__': main()
