"""Admit one exact, qualified BQN frame candidate without rewriting old observations.

All commands here are offline evidence readers. --prepare writes a reviewable
plan/results/catalog preview; --apply additionally requires both reviewed hashes.
No compiler, interpreter, benchmark, network client or subprocess is launched.
"""
import argparse
import copy
import difflib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[2]
BASE = 'experiments/bqn/optimization-v1/'
ADMISSION = BASE + 'admission-v1/'
PLAN = ADMISSION + 'plan.json'
RESULTS = ADMISSION + 'results.json'
PREPARED = ADMISSION + 'prepared.json'
KEY = 'knucleotide:array-bqn-occurrence-frame'
PARENT = 'knucleotide:array-bqn-faithful'
SOURCE = BASE + 'sources/ordinal-horner-grouped-v5-native-keys-v1.bqn'
SOURCE_SHA = '8443008a54a968cc0dd77bac54cee29fdbc78e2a02a1023b5e7916aa99af4802'
BASELINE_SHA = '84810c4d5567d1554416698e3e83ec5ca7d587d6a21b0be331915c4962326716'
RUNTIME = BASE + '.build/CBQN/BQN'
RUNTIME_SHA = '0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5'
WITNESS_RUNTIME = BASE + '.build/CBQN-witness/BQN'
WITNESS_SHA = 'b2b67734b4b675034e699951e80542560c6caba7b244b7f65f50a94f571cdf10'
WITNESS_SOURCE_SHA = 'ec613c01ced251a396d8b79516dae3c222fc4c7c6078ea8826943f51ea457734'
VALIDATOR_SHA = '620c0433685b7092b194ff73d0470eb3ef2f351bd145a7faf6f1794d2896727e'
PATCH_SHA = 'dded21055879c7405fe8bac52344ab6c8f6ed42a771df9054497bb8248556332'
COMMIT = 'c893d3e7828899a50150df03ad33c9052fa51d3c'
SOURCE_REVISION = 'c8a0184e6fa0be30bda5119f82f9930c96f4255a'
CONTROLLER = 'tools/qualification/bqn_knucleotide_run.py'
CONTROLLER_SHA = '0b435ec95f4bdc71fdd7d7294b5a0b39d6cebb994dff8a20d8771a8b08d858a4'
CORPUS_CONTROLLER = 'tools/qualification/bqn_knucleotide_corpus.py'
CORPUS_CONTROLLER_SHA = 'b063e5d6808592b3f62c49bcb54173d20dd1f4f827ff92399104cfcb9990e91b'
CORPUS = 'experiments/shared/bounded-corpus-v1/cases/manifest.json'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
INPUT = dict(path='experiments/lean4/.build/inputs/n25000000.fasta', bytes=254166745,
             sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa')
OUTPUT = dict(bytes=259, sha256='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7')
WIDTHS = [1, 2, 3, 4, 6, 12, 18]
CASES = {'ties-and-stop', 'one-base', 'empty', 'missing', 'crlf-comment-eof',
         'embedded-header-comment', 'arbitrary-widths', 'header-eof', 'empty-input',
         'exact-token-cr', 'exact-token-controls', 'tail', 'specified-composite-space',
         'specified-composite-tab'}
MATCHED = ['baseline.bqn', Path(SOURCE).name,
           'ordinal-chunk-100000-v4-native-keys-v1.bqn',
           'ordinal-chunk-250000-v4-native-keys-v1.bqn',
           'ordinal-chunk-1000000-v4-native-keys-v1.bqn']
SUPPORT = {
    BASE+'stdlib/standard.bqn': '06d9fac57b6ded281284cee43b949df39e6158432fd14b3937f43fb273944b12',
    BASE+'stdlib/native.c': '3246275bfd0148b9dfa874907bda1f3142612142ab6cf1b17a70da9c19ce4187',
    BASE+'stdlib/khash.h': '4582c7fd4b98f61339ce677bb1daa7a45a53075b112a494a335525c4bda72074',
    BASE+'stdlib/libarray-standard.dylib': '1b893fb84ca47efcc115dcf9c7055610618a4b74a49250b5810104ac037eef1e',
}
REFS = {
    'admission_controller': 'tools/qualification/import_bqn_knucleotide.py',
    'full': BASE+'full-matched-v1/report.json',
    'bounded': BASE+'native-keys-bounded-v1/report.json',
    'delta': BASE+'work-witness/frame-native-keys-source-delta-v1.json',
    'ownership': BASE+'source-ownership-v1/ordinal-horner-grouped-v5-native-keys-v1-counts.json',
    'runtime_build': BASE+'release-build.json',
    'witness_build': BASE+'work-witness/build-v3.json',
    'witness_patch': BASE+'work-witness/instrument-count.patch',
    'validator': BASE+'work-witness/validate_witness.py',
    'corpus': CORPUS, 'controller': CONTROLLER, 'corpus_controller': CORPUS_CONTROLLER,
    'runtime_builder': 'tools/qualification/build_bqn.py',
}
AUTHOR_CONTEXT = dict(tool='OpenAI Codex', model_family='Codex GPT-6', exact_model=None,
                      status='developer-identity-family-only', original_predecessor_authorship='unresolved')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def load(path):
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: '+value)
    return json.loads(Path(path).read_text(), object_pairs_hook=no_duplicates, parse_constant=invalid)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()


def relative(root, value, recorded_root=None):
    if isinstance(value, Path):
        value = str(value)
    require(isinstance(value, str), 'Missing artifact path')
    path = Path(value)
    if path.is_absolute() and recorded_root is not None:
        try:
            # Only the root derived from the exact recorded runtime suffix may
            # be relocated. Never strip an arbitrary absolute artifact prefix.
            candidate = path.relative_to(recorded_root)
        except ValueError:
            raise ValueError('Artifact outside recorded repository: '+value) from None
        require('..' not in candidate.parts, 'Artifact escapes recorded repository')
        return candidate.as_posix()
    path = path if path.is_absolute() else root/path
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise ValueError('Artifact escapes repository: '+value) from None


def execution_root(report, runtime, witness=False):
    rows = report.get('cases', [])
    require(rows and isinstance(rows[0].get('command'), list), 'No recorded execution command')
    command = rows[0]['command']
    offset = 2 if witness else 0
    require(len(command) == offset+2 and isinstance(command[offset], str), 'Wrong recorded command shape')
    executable = command[offset]
    require(Path(executable).is_absolute() and executable.endswith('/'+runtime), 'Wrong recorded runtime suffix')
    prefix = executable[:-len('/'+runtime)]
    require(prefix and '..' not in Path(prefix).parts and Path(prefix).as_posix() == prefix, 'Invalid recorded execution root')
    return prefix


def pin(root, path):
    path = relative(root, path)
    return dict(path=path, sha256=sha(root/path))


class Evidence:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.fingerprints = {}

    def check(self, ref):
        require(isinstance(ref, dict) and re.fullmatch('[0-9a-f]{64}', ref.get('sha256', '')), 'Invalid evidence pin')
        path = relative(self.root, ref['path'])
        if path not in self.fingerprints:
            self.fingerprints[path] = sha(self.root/path)
        require(self.fingerprints[path] == ref['sha256'], 'Changed evidence: '+path)
        if 'bytes' in ref:
            require((self.root/path).stat().st_size == ref['bytes'], 'Changed artifact length: '+path)
        return self.root/path

    def document(self, ref):
        return load(self.check(ref))


def make_plan(root=ROOT):
    """Snapshot evidence identities for independent review; grants no admission."""
    root = Path(root)
    evidence = {name: pin(root, path) for name, path in REFS.items()}
    delta = load(root/REFS['delta'])
    for label in ['full_workload', 'bounded_workload']:
        receipt = delta[label]
        for name in ['report', 'validation']:
            path = receipt[name]
            evidence[label+'_'+name] = pin(root, path)
            require(evidence[label+'_'+name]['sha256'] == receipt[name+'_sha256'], 'Stale source-delta receipt')
    bounded = load(root/REFS['bounded'])
    for case in bounded['reports']:
        evidence['bounded_case_'+case['case']] = pin(root, case['report'])
        require(evidence['bounded_case_'+case['case']]['sha256'] == case['sha256'], 'Stale bounded summary')
    return dict(schema='bqn-knucleotide-admission-plan.v1', key=KEY, parent=PARENT,
                source=pin(root, SOURCE), mode='occurrence', job_plan='frame-pieces', pieces=8,
                chunk_size=None, dna_length=125000000, expected_updates=874999961,
                runtime=dict(path=RUNTIME, sha256=RUNTIME_SHA, commit=COMMIT),
                retained_source_revision=SOURCE_REVISION,
                recorded_execution_root=execution_root(load(root/REFS['full']), RUNTIME),
                input=INPUT, expected=OUTPUT, evidence=evidence,
                author_context=copy.deepcopy(AUTHOR_CONTEXT),
                source_count_policy='retained manual application-loc-v1 BQN extension; draft v2 is not qualified',
                selection='Lowest median among the five retained matched candidates, subject to complete qualification; no global optimality claim.')


def check_power(value):
    require("'AC Power'" in value.get('battery', ''), 'Sample not on AC power')
    modes = [line.split()[-1] for line in value.get('settings', '').splitlines() if 'lowpowermode' in line]
    require(modes and set(modes) == {'0'}, 'Low power mode not verified off')


def check_execution(evidence, ref, sources, runtime, full, samples=1, witness=False,
                    local_artifacts=False, expected_input=None, expected_output=None, recorded_root=None):
    """Check retained raw processes, not just a producer's pass label."""
    root = evidence.root
    report = evidence.document(ref)
    require(report.get('schema') == 'bqn-knucleotide-execution.v1' and report.get('status') == 'PASSED'
            and report.get('active') is None and report.get('finished_utc'), 'Incomplete execution report')
    require(report.get('controller_sha256') == CONTROLLER_SHA, 'Wrong measurement controller')
    actual_root = execution_root(report, runtime, witness)
    require(recorded_root is None or recorded_root == actual_root, 'Execution report changed repository root')
    recorded_root = actual_root
    require(report.get('full_workload') is full and report.get('chart_admission') is False
            and report.get('diagnostic_profile') is False and report.get('diagnostic_work_witness') is witness,
            'Wrong workload or diagnostic boundary')
    source_paths = {name: BASE+'sources/'+name for name in sources}
    wanted_pins = {path: sha(root/path) for path in source_paths.values()}
    wanted_pins.update(SUPPORT)
    wanted_pins[runtime] = WITNESS_SHA if witness else RUNTIME_SHA
    require(report.get('pins') == wanted_pins, 'Execution source/runtime/support pins differ')
    for path, digest in wanted_pins.items():
        # Native binaries need not be distributed with the publication. Their
        # exact digests remain bound to execution/build receipts on replay.
        if local_artifacts or path.endswith(('.bqn', '.c', '.h')):
            evidence.check(dict(path=path, sha256=digest))
    for name, path in source_paths.items():
        evidence.check(dict(path=str(Path(ref['path']).parent/'sources'/name), sha256=wanted_pins[path]))
    input_record = {**report['input'], 'path': relative(root, report['input']['path'], recorded_root)}
    if expected_input is not None:
        require(input_record == expected_input, 'Wrong execution input')
    if expected_output is not None:
        require(report['expected'] == expected_output, 'Wrong expected output')
    if local_artifacts or not full:
        evidence.check(input_record)
    orders = report.get('orders')
    require(isinstance(orders, list) and len(orders) == samples
            and all(len(order) == len(sources) and set(order) == set(sources) for order in orders), 'Missing matched round')
    rows = report.get('cases', [])
    require(len(rows) == samples*len(sources), 'Missing complete-process sample')
    require([(r.get('sample'), r.get('source')) for r in rows]
            == [(i+1, name) for i, order in enumerate(orders) for name in order], 'Sample order/identity mismatch')
    for row in rows:
        command = [str(Path(recorded_root)/runtime), str(Path(recorded_root)/source_paths[row['source']])]
        if witness:
            command = ['/usr/bin/env', 'MECH_BQN_COUNT_WITNESS=1']+command
        require(row.get('command') == command and relative(root, row['stdin'], recorded_root) == input_record['path'], 'Wrong process command/input')
        seconds = row.get('elapsed_seconds')
        require(isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and math.isfinite(seconds)
                and seconds > 0 and row.get('exit_code') == 0 and row.get('timed_out') is False
                and row.get('output_valid') is True, 'Failed/invalid process')
        require(row.get('started_utc') and row.get('finished_utc'), 'Process dates missing')
        for stream in ['stdout', 'stderr']:
            evidence.check({**row[stream], 'path': relative(root, row[stream]['path'], recorded_root)})
        require({k: row['stdout'][k] for k in ['bytes', 'sha256']} == report['expected'], 'Output differs from reference')
        require(witness or row['stderr']['bytes'] == 0, 'Diagnostics in timing sample')
        directory = (root/relative(root, row['stdout']['path'], recorded_root)).parent
        require(relative(root, row['stderr']['path'], recorded_root) == (directory/'stderr.bin').relative_to(root).as_posix(), 'Streams from different processes')
        process = load(directory/'process.json')
        additions = {'source', 'sample', 'output_valid', 'power_before', 'power_after'}
        require(process == {k: v for k, v in row.items() if k not in additions}, 'Raw process receipt differs')
        evidence.check(pin(root, directory/'process.json'))
        check_power(row['power_before']); check_power(row['power_after'])
    medians = {name: statistics.median(r['elapsed_seconds'] for r in rows if r['source'] == name) for name in sources}
    require(report.get('medians') == medians, 'Stale producer medians')
    return report


def check_ownership(evidence, ref):
    receipt = evidence.document(ref)
    require(receipt.get('schema') == 'bqn-source-ownership-review.v1' and receipt.get('source') == SOURCE
            and receipt.get('source_sha256') == SOURCE_SHA, 'Source count is not bound to selected source')
    require(receipt.get('independent_review_approved') is True and receipt.get('application_loc') == 48
            and receipt.get('physical_loc') == 43 and receipt.get('retained_rule_proposed_loc') == 48,
            'Application LOC requires independent exact-source approval')
    lines = (evidence.root/SOURCE).read_text().splitlines()
    ledger = receipt.get('line_ledger', [])
    require(len(ledger) == len(lines) and all(r['line'] == i+1 and r['source_text'] == text
            for i, (r, text) in enumerate(zip(ledger, lines))), 'Source ownership ledger is stale')
    require(sum(r['retained_rule_units'] for r in ledger) == 48
            and sum(bool(r['significant']) for r in ledger) == 43, 'Source ownership sum differs')
    require(all(isinstance(r['retained_rule_units'], int) and r['retained_rule_units'] >= 0
                and len(r['retained_rule_owners']) == r['retained_rule_units'] for r in ledger), 'Invalid owner units')
    for key in ['source', 'saved_audit']:
        policy = receipt['policies']['retained']
        evidence.check(dict(path=policy[key], sha256=policy[key+'_sha256']))
    require(receipt['baseline_comparison']['source_sha256'] == BASELINE_SHA
            and receipt['baseline_comparison']['canonical_retained_loc'] == 39, 'Historical count was changed')
    return receipt


def check_build(evidence, ref, local_artifacts, recorded_root):
    build = evidence.document(ref)
    require(build.get('schema') == 'bqn-runtime-build.v1' and build.get('runtime_use') == 'release-timing'
            and build.get('official_repository') == 'https://github.com/dzaima/CBQN.git'
            and build.get('commit') == COMMIT and build.get('release_source_status') == ''
            and build.get('witness_patch_sha256') is None, 'Release build identity differs')
    require(build.get('flags') and build.get('compiler') and build.get('sdk_resolved')
            and COMMIT in build.get('version', '') and build.get('submodules'), 'Incomplete runtime restoration receipt')
    artifacts = build.get('artifacts', [])
    by_path = {r['path']: r for r in artifacts}
    for path, digest in {RUNTIME: RUNTIME_SHA, **SUPPORT}.items():
        record = by_path.get(str(Path(recorded_root)/path))
        require(record is not None and record['sha256'] == digest, 'Build/measurement artifact differs: '+path)
    require(len(artifacts) == len(by_path) and len(artifacts) >= 8, 'Incomplete dependency artifact pins')
    for row in artifacts:
        require(re.fullmatch('[0-9a-f]{64}', row.get('sha256', '')) and row.get('resolved_path'), 'Unpinned runtime dependency')
        if local_artifacts:
            try:
                restored = evidence.root/Path(row['path']).relative_to(recorded_root)
            except ValueError:
                restored = Path(row['path'])
            require(sha(restored) == row['sha256'], 'Changed runtime/dependency artifact: '+row['path'])
    return build


def reconcile(root=ROOT, local_artifacts=True):
    """Reconcile archived evidence; local mode also checks current native/input bytes."""
    evidence = Evidence(root); root = evidence.root
    plan = load(root/PLAN)
    require(plan == make_plan(root), 'Admission plan is stale or altered')
    require(plan['source'] == dict(path=SOURCE, sha256=SOURCE_SHA), 'Unreviewed selected source')
    for ref in plan['evidence'].values():
        evidence.check(ref)
    require(plan['evidence']['controller']['sha256'] == CONTROLLER_SHA
            and plan['evidence']['corpus_controller']['sha256'] == CORPUS_CONTROLLER_SHA
            and plan['evidence']['corpus']['sha256'] == CORPUS_SHA
            and plan['evidence']['validator']['sha256'] == VALIDATOR_SHA
            and plan['evidence']['witness_patch']['sha256'] == PATCH_SHA, 'Controller/corpus/witness identity differs')
    ownership = check_ownership(evidence, plan['evidence']['ownership'])
    recorded_root = plan['recorded_execution_root']
    build = check_build(evidence, plan['evidence']['runtime_build'], local_artifacts, recorded_root)
    full = check_execution(evidence, plan['evidence']['full'], MATCHED, RUNTIME, True, samples=3,
                           local_artifacts=local_artifacts, expected_input=INPUT, expected_output=OUTPUT, recorded_root=recorded_root)
    require(full['pins'][BASE+'sources/baseline.bqn'] == BASELINE_SHA, 'Historical control source differs')
    require(min(full['medians'], key=lambda name: (full['medians'][name], name)) == Path(SOURCE).name,
            'Selected frame candidate is not the lowest matched median')
    bounded = evidence.document(plan['evidence']['bounded'])
    require(bounded.get('schema') == 'bqn-knucleotide-corpus.v1' and bounded.get('status') == 'PASSED'
            and bounded.get('chart_admission') is False and bounded.get('case_count') == 14
            and bounded.get('controller_sha256') == CORPUS_CONTROLLER_SHA and bounded.get('corpus_sha256') == CORPUS_SHA,
            'Incomplete bounded qualification')
    require(bounded.get('sources') == [Path(SOURCE).name, MATCHED[2]], 'Bounded sources differ')
    require(len(bounded['reports']) == 14 and {r['case'] for r in bounded['reports']} == CASES, 'Missing bounded edge case')
    corpus = evidence.document(plan['evidence']['corpus'])
    corpus_cases = {r['case']: r for r in corpus['cases'] if r['benchmark'] == 'knucleotide'}
    require(set(corpus_cases) == CASES, 'Unexpected reference corpus')
    for row in bounded['reports']:
        case = corpus_cases[row['case']]
        expected_input = {**case['stdin'], 'path': str(Path(CORPUS).parent/case['stdin']['path'])}
        output_path = str(Path(CORPUS).parent/case['expected']['path'])
        evidence.check({**case['expected'], 'path': output_path})
        expected_output = {k: case['expected'][k] for k in ['bytes', 'sha256']}
        check_execution(evidence, dict(path=row['report'], sha256=row['sha256']), bounded['sources'], RUNTIME, False,
                        local_artifacts=local_artifacts, expected_input=expected_input, expected_output=expected_output,
                        recorded_root=recorded_root)
    delta = evidence.document(plan['evidence']['delta'])
    require(delta.get('schema') == 'bqn-frame-witness-source-delta.v1' and delta.get('source') == SOURCE
            and delta.get('source_sha256') == SOURCE_SHA and delta.get('instrumentation_inverse_equals_original_bytes') is True,
            'Witness is not bound to selected source')
    require(delta.get('witness_source_sha256') == WITNESS_SOURCE_SHA, 'Unreviewed diagnostic source')
    original = (root/SOURCE).read_text()
    witness_path = relative(root, delta['witness_source'])
    witness = evidence.check(dict(path=witness_path, sha256=delta['witness_source_sha256'])).read_text()
    require(delta.get('unified_diff') == ''.join(difflib.unified_diff(original.splitlines(True), witness.splitlines(True),
            fromfile=SOURCE, tofile=witness_path)), 'Witness/source delta differs')
    # This frame twin inserts only the reviewed pid/Mark declaration and two
    # marker calls. Removing exactly those lines must recover all source bytes.
    declaration = witness.index('pid ← '); frame = witness.index('Frame ← ', declaration)
    inverse = witness[:declaration]+witness[frame:]
    inverse = inverse.replace(' Mark "begin"‿width‿frame‿piece‿rows\n', '', 1)
    inverse = inverse.replace(' Mark "end"‿width‿frame‿piece‿rows\n', '', 1)
    require(inverse == original, 'Witness instrumentation changes application logic')
    require(delta['validator'] == plan['evidence']['validator'], 'Witness validator receipt differs')
    validator_path = evidence.check(delta['validator'])
    spec = importlib.util.spec_from_file_location('bqn_admission_witness_validator', validator_path)
    validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
    witness_build = evidence.document(plan['evidence']['witness_build'])
    require(witness_build.get('exit_code') == 0 and witness_build.get('admitted_for_timing') is False
            and witness_build.get('runtime_sha256') == WITNESS_SHA
            and witness_build.get('patch_sha256') == plan['evidence']['witness_patch']['sha256'], 'Witness build differs')
    validations = {}
    for label, length, is_full in [('full_workload', 125000000, True), ('bounded_workload', 5042, False)]:
        execution = check_execution(evidence, plan['evidence'][label+'_report'], [Path(witness_path).name],
                                    WITNESS_RUNTIME, is_full, witness=True, local_artifacts=local_artifacts,
                                    expected_input=INPUT if is_full else None, expected_output=OUTPUT if is_full else None,
                                    recorded_root=recorded_root)
        trace = (root/relative(root, execution['cases'][0]['stderr']['path'], recorded_root)).read_text()
        validation = evidence.document(plan['evidence'][label+'_validation'])
        replay = validator.validate(trace, length, widths=WIDTHS, pieces=8, mode='occurrence')
        require(validation == replay and validation.get('status') == 'pass'
                and validation.get('evidence_level') == 'scoped-frame-identity'
                and validation.get('expected_updates') == validation.get('observed_updates')
                == sum(max(0, length-width+1) for width in WIDTHS)
                and validation.get('job_plan') == 'frame-pieces' and validation.get('errors') == [],
                'Work witness does not prove exact required occurrence/hash work')
        validations[label] = validation
    rows = [r for r in full['cases'] if r['source'] == Path(SOURCE).name]
    samples = [r['elapsed_seconds'] for r in rows]
    program = dict(key=KEY, id=KEY.split(':', 1)[1], original_program_key=PARENT, benchmark='knucleotide', language='bqn',
                   source_sha256=SOURCE_SHA, loc=ownership['application_loc'], physical_loc=ownership['physical_loc'],
                   samples_seconds=samples, median_seconds=statistics.median(samples), sample_sd_seconds=statistics.stdev(samples),
                   command=rows[0]['command'], sample_execution_metadata=copy.deepcopy(rows),
                   build_command=build['flags'], build_cwd=BASE+'.build/CBQN', runtime_commit=COMMIT)
    for row in program['sample_execution_metadata']:
        row['producer_report'] = plan['evidence']['full']; row['producer_plan'] = pin(root, PLAN)
    return dict(schema='bqn-knucleotide-admission-results.v1', status='RECONCILED', recorded_at=full['finished_utc'],
                plan=pin(root, PLAN), evidence=plan['evidence'], programs=[program],
                producer_report=plan['evidence']['full'], historical_data_preserved=True, new_observations=3,
                full_workload_n=25000000, selected_dna_length=125000000,
                matched_candidate_medians=full['medians'], matched_control_median_seconds=full['medians']['baseline.bqn'],
                matched_control_speedup=full['medians']['baseline.bqn']/statistics.median(samples),
                selection=plan['selection'], work_validation=validations,
                toolchains=dict(bqn=dict(version=build['version'], commit=COMMIT, path=RUNTIME, sha256=RUNTIME_SHA)),
                runtime_details=build, hardware=full['host'], os=full['host']['os'], input=INPUT,
                timing_boundary=full['timing_boundary'], required_power=dict(source='AC Power', low_power_mode=0),
                support_files=[dict(path=path, sha256=digest) for path, digest in SUPPORT.items()],
                # Runtime/input identities live in their explicit build/input
                # receipts. Offline publication replay must not depend on
                # retaining a 254 MB input or host-specific native binaries.
                artifacts=[dict(path=path, sha256=digest) for path, digest in sorted(evidence.fingerprints.items())
                           if path not in {RUNTIME, WITNESS_RUNTIME, INPUT['path'], BASE+'stdlib/libarray-standard.dylib'}],
                author_context=plan['author_context'], source_count_policy=plan['source_count_policy'],
                recorded_execution_root=recorded_root,
                runtime_restoration=dict(command=['python3', 'tools/qualification/build_bqn.py', '--output',
                    BASE+'release-build-reproduced.json'], cwd='repository root',
                    note='Restoration recipe; the recorded native make command runs in '+BASE+'.build/CBQN.'))


def authorship_record(parent, results, evidence):
    """Current local changes are known; original lineage/model/terms stay open."""
    context = results['author_context']
    return dict(schema='benchmark-authorship.v1', kind='ai-adapted', label='AI adapted · retained local predecessor',
                source_sha256=[SOURCE_SHA]+parent['files'][1:], origin_status='unresolved',
                origin_gaps=copy.deepcopy(parent['authorship'].get('origin_gaps', [])),
                retained_sources=[dict(source_sha256=SOURCE_SHA,
                    url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)]
                    +[copy.deepcopy(ref) for ref in parent['authorship'].get('retained_sources', [])
                      if ref['source_sha256'] in parent['files'][1:]],
                parent_programs=[PARENT], parent_sources=[dict(program_key=PARENT, relationship='local predecessor',
                    **copy.deepcopy(ref)) for ref in parent['authorship'].get('retained_sources', [])],
                sources=copy.deepcopy(parent['authorship'].get('sources', [])), attribution_notices=[],
                ai=dict(tool=context['tool'], models=[], model_family=context['model_family'], exact_model=None,
                        status='family-identified-exact-model-unverified', matched_source_files=[SOURCE_SHA],
                        total_source_files=len(parent['files']), evidence=[evidence['plan'], evidence['results']]),
                license=copy.deepcopy(parent['authorship']['license']),
                local_change_license=dict(status='suite-license', id='Apache-2.0', evidence='LICENSE', scope='New local changes only; inherited terms remain unresolved.'),
                evidence=[evidence['plan']['path'], evidence['results']['path'], evidence['ownership']['path']],
                retained_source_note='Immutable revision identifies this new application; predecessor provenance and inherited terms remain unresolved.')


def bound_authorship(data, profile, root=ROOT):
    """Narrow audit hook: metadata cannot turn another source into a known write."""
    root = Path(root)
    detail = profile.get('source_provenance_record') or {}
    require(profile.get('key') == KEY and detail.get('kind') == 'suite-authored-optimization'
            and detail.get('original_program_key') == PARENT and detail.get('source_sha256') == SOURCE_SHA,
            'Unrecognized local BQN authorship record')
    catalog = {**data.get('program_inventory', {}), **data['programs']}
    parent = catalog[PARENT]
    require(profile['files'] == [SOURCE_SHA]+parent['files'][1:]
            and sha(root/SOURCE) == SOURCE_SHA
            and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest() == SOURCE_SHA,
            'Authorship source identity differs')
    results = load(root/RESULTS)
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    require(detail.get('admission') == evidence['results'] and results.get('schema') == 'bqn-knucleotide-admission-results.v1'
            and results.get('status') == 'RECONCILED' and results['programs'][0]['key'] == KEY
            and results['programs'][0]['source_sha256'] == SOURCE_SHA
            and results['plan'] == evidence['plan'] and detail.get('author_context') == results['author_context']
            and results['author_context'] == AUTHOR_CONTEXT,
            'Authorship admission binding differs')
    Evidence(root).check(evidence['ownership'])
    return authorship_record(parent, results, evidence)


def append_catalog(before, root=ROOT):
    """Pure deterministic extension, also used by historical source-accounting replay."""
    root = Path(root).resolve()
    results = load(root/RESULTS)
    require(results == reconcile(root, local_artifacts=False), 'Stale reconciled results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'], 'Candidate already present')
    data = copy.deepcopy(before); parent = before['programs'][PARENT]
    require(parent['files'][0] == BASELINE_SHA and parent['loc'] == 39 and parent['physical_loc'] == 36,
            'Retained predecessor identity changed')
    r = results['programs'][0]
    bench = next(b for b in data['benchmarks'] if b['key'] == 'knucleotide')
    require(r['median_seconds'] >= bench['baseline_seconds'], 'New global baseline requires separate normalization review')
    evidence = {**results['evidence'], 'plan': pin(root, PLAN), 'results': pin(root, RESULTS)}
    source = dict(name=Path(SOURCE).name, path=SOURCE, sha256=SOURCE_SHA,
                  code=(root/SOURCE).read_text(), archive_path=SOURCE)
    require(SOURCE_SHA not in data['files'], 'Source hash already cataloged')
    data['files'][SOURCE_SHA] = source
    row = copy.deepcopy(parent)
    for name in ['publication_record', 'timing_measurement', 'timing_correction', 'aliased_sample_source',
                 'source_alias_of', 'source_alias_note', 'loc_expansions', 'source_accounting', 'authorship']:
        row.pop(name, None)
    row.update(key=KEY, id=r['id'], receipt_key=r['id'], seconds=r['median_seconds'], samples=r['samples_seconds'],
               timing_sd=r['sample_sd_seconds'], loc=r['loc'], physical_loc=r['physical_loc'],
               files=[SOURCE_SHA]+parent['files'][1:], x=r['loc']/bench['baseline_loc'], y=r['median_seconds']/bench['baseline_seconds'],
               formatted_loc=None, formatted_x=None, formatted_loc_status='pending', formatted_loc_complete=False, formatted_loc_evidence={},
               report=RESULTS, report_sha256=evidence['results']['sha256'], source_report=evidence['ownership']['path'],
               command=r['command'], build_command=r['build_command'], build_cwd=r.get('build_cwd'),
               cwd=results['recorded_execution_root'], execution_mode='interpreter',
               binary_sha256=RUNTIME_SHA, runtime_sha256=RUNTIME_SHA, native_observations=3, timing_alias_of=None,
               sample_execution_metadata=r['sample_execution_metadata'], original_program_key=PARENT,
               local_adaptation=True, distinct_optimization_claimed=True,
               source_provenance='Suite-authored optimization of the retained faithful BQN port; original predecessor authorship remains unresolved.',
               source_provenance_record=dict(kind='suite-authored-optimization', original_program_key=PARENT,
                   source_sha256=SOURCE_SHA, admission=pin(root, RESULTS), origin_status='inherited-unresolved',
                   author_context=results['author_context']),
               retained_source_revision=SOURCE_REVISION,
               runtime_policy='CBQN commit '+COMMIT+'; unmodified release runtime; up to eight process workers per Count call',
               timing_boundary=results['timing_boundary'],
               timing_summary='Three fresh complete-process samples; the historical predecessor observations remain unchanged. Lowest retained matched median, without a global optimality claim.',
               source_accounting=dict(policy='application-loc-v1', application_loc=r['loc'], physical_loc=r['physical_loc'],
                   evidence=evidence['ownership']['path'], review_sha256=evidence['ownership']['sha256'],
                   qualification='Exact-source independently reviewed retained manual BQN extension; draft logical policy v2 unqualified.',
                   files=copy.deepcopy(parent['source_accounting']['files'])),
               full_output_validation=dict(all_three_samples_passed=True, evidence=evidence['full']),
               chart_admission=dict(historical_reports_unchanged=True, **evidence),
               algorithm=dict(strict=True, status='required-work-reviewed', native_benchmark_kernel=False,
                   reason='All seven widths cover all 874,999,961 overlapping occurrences. Vector Horner key construction and native ordinal primitive on boxed storage use normal numeric keys, with one generic hash lookup/write per occurrence, default capacity 64 and doubling; explicit HashMap fallback covers singleton pieces. Untimed scoped runtime witness validates frame identity and work; no diagnostic runtime is timed.',
                   work_evidence=evidence['full_workload_validation']),
               measured_backend=dict(key='bqn', execution='interpreter', label='BQN (CBQN)', verified=True,
                   evidence=dict(verified=True, report=RESULTS, report_sha256=evidence['results']['sha256'], command=r['command'],
                       source_sha256=[SOURCE_SHA]+parent['files'][1:], runtime_receipt=dict(verified=True, report=RESULTS,
                           report_sha256=evidence['results']['sha256'], field='/toolchains/bqn/version',
                           value=results['toolchains']['bqn']['version'], value_encoding='literal-saved-string'))))
    row['authorship'] = authorship_record(parent, results, evidence)
    data['programs'][KEY] = row; data['program_inventory'][KEY] = copy.deepcopy(row)
    group = next(g for g in bench['groups'] if g['language'] == 'bqn')
    candidates = [data['programs'][k] for k in group['programs']+[KEY]]
    group.update(programs=[p['key'] for p in candidates],
                 fast=min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))['key'],
                 small=min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))['key'])
    for section, prefix in [('reference_summary', ''), ('formatted_reference_summary', 'formatted_')]:
        for summary in data[section]:
            if summary['lang'] != 'bqn': continue
            groups = [g for b in data['benchmarks'] for g in b['groups'] if g['language'] == 'bqn']
            for kind in ['fast', 'small']:
                selected = [data['programs'][g[prefix+kind]] for g in groups if g.get(prefix+kind)]
                summary[kind] = dict(x=statistics.geometric_mean(p['formatted_x' if prefix else 'x'] for p in selected),
                                     y=statistics.geometric_mean(p['y'] for p in selected)) if selected else None
    for ref in [*evidence.values(), *results['artifacts'], dict(path=SOURCE, sha256=SOURCE_SHA)]:
        data['archive_paths'][ref['path']] = ref['path']
    data['bqn_knucleotide_audit'] = dict(schema='bqn-knucleotide-catalog-extension.v1', appended_programs=[KEY],
        evidence=evidence, measured_at=results['recorded_at'], new_observations=3, source_files_added=1,
        old_profiles_unchanged=True, old_baselines_unchanged=True)
    for pool in ['programs', 'program_inventory', 'files', 'archive_paths']:
        require(all(data[pool][key] == old for key, old in before[pool].items()), 'Historical '+pool+' changed')
    require([(b['baseline_loc'], b['baseline_seconds']) for b in data['benchmarks']]
            == [(b['baseline_loc'], b['baseline_seconds']) for b in before['benchmarks']], 'Baselines changed')
    return data


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_bytes(encoded(value)); temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Write additive plan/results/prepared preview, never canonical data')
    parser.add_argument('--apply', action='store_true', help='Apply exactly the reviewed preview')
    parser.add_argument('--expected-before-sha256')
    parser.add_argument('--expected-prepared-sha256')
    args = parser.parse_args()
    require(args.prepare != args.apply, 'Choose exactly one of --prepare/--apply')
    catalog = ROOT/'data/benchmarks.json'
    if args.prepare:
        write(ROOT/PLAN, make_plan())
        results = reconcile(); write(ROOT/RESULTS, results)
        write(ROOT/PREPARED, append_catalog(load(catalog)))
        print(json.dumps(dict(before_sha256=sha(catalog), prepared_sha256=sha(ROOT/PREPARED),
                              results_sha256=sha(ROOT/RESULTS), key=KEY, canonical_changed=False)))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256, 'Apply requires both reviewed hashes')
        require(sha(catalog) == args.expected_before_sha256, 'Canonical catalog changed since review')
        require(sha(ROOT/PREPARED) == args.expected_prepared_sha256, 'Prepared catalog changed since review')
        after = append_catalog(load(catalog))
        require(encoded(after) == (ROOT/PREPARED).read_bytes(), 'Prepared catalog no longer reproduces')
        # Check the before identity immediately before replacing the only owned
        # canonical file. Language/source metadata is unchanged by this importer.
        require(sha(catalog) == args.expected_before_sha256, 'Canonical catalog changed during validation')
        write(catalog, after)
        print('Added one qualified BQN frame candidate; all historical profiles and samples retained.')


if __name__ == '__main__':
    main()
