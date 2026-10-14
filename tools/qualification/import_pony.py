#!/usr/bin/env python3
"""Prepare Pony publication from independently closed, explicitly pinned evidence.

No compiler, runtime, sampler, replay, or historical controller is imported or
executed. Run only after the timing lane is idle: all evidence pins are rehashed
under the existing nonblocking common mutex. The default writes a fresh candidate
tree; --apply additionally replaces the three current publication files after
all checks, retaining their exact original bytes in that private candidate tree.
Historical receipts and their admission flags are never changed.
"""
import argparse
import copy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import statistics
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
TARGETS = ('data/benchmarks.json', 'data/languages.json', 'site/src/languages.mjs')
BENCHES = frozenset(('regexredux', 'revcomp', 'pidigits', 'spectralnorm', 'mandelbrot',
                    'fasta', 'knucleotide', 'binarytrees', 'nbody', 'fannkuchredux'))
PLAN_SHA = '710530db6445292bd6506c97a9e6c91fd7aeba4523f077cf72be25cbebf7a3ee'
LOC_SHA = '5831dd9675da58865a39edab9f86ecbdb36377a470052814aeb06a981fbbe182'
LOC_ROOT_SHA = '4c0d830178406cd4ab4bd800eabfe6493a68816e363c52eeb2e6f20dfc0e72de'
WORK_SHA = 'aa7786b7cd16565a5ef21cb0bb56e8e0b7ccf77ddf5e98cbcfd1710b6b6aa421'
OWNER_SHA = '2696c89a2a4f0c50ea418452e62b791a39850704691e9cd931dbd0e0a80a05db'
ALLOCATION_SHA = '354f4eab47aef151f1f5cf29824c2b7b4f45f582b307b2373ca0ec316434d346'
META_FIELDS = ('platform', 'runtime', 'execution', 'typing', 'style', 'memory', 'note', 'sources')


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def same(left, right, message):
    require(canonical(left) == canonical(right), message)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: '+key)
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError('Nonfinite JSON number: '+value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def is_sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def checked_bytes(path, expected):
    require(is_sha(expected), 'Explicit SHA-256 required: '+str(path))
    raw = Path(path).read_bytes()
    require(sha_bytes(raw) == expected, 'Input bytes changed: '+str(path))
    return raw


def module_object(raw):
    text = raw.decode('utf-8')
    match = re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)', text, re.S)
    require(match is not None, 'Unexpected language module syntax')
    return match.group(1), strict_json(match.group(2)), match.group(3)


class Evidence:
    """Explicit plan relocations for verification; migration map for public paths.

    Historical hashes are never silently substituted with sanitized hashes.
    Reconciliation pins contain the exact active bytes it actually verified.
    """
    def __init__(self, root, plan, pins):
        self.root, self.plan, self.pins = root, plan, {}
        self.checked = {}
        for mapping in pins:
            for name, digest in mapping.items():
                require(is_sha(digest), 'Malformed evidence pin: '+name)
                require(name not in self.pins or self.pins[name] == digest, 'Conflicting input pins: '+name)
                self.pins[name] = digest
        self.migration_path = root/'migration/reorganization-paths.tsv'
        self.migration_raw = self.migration_path.read_bytes()
        self.archive = {}
        for row in csv.DictReader(io.StringIO(self.migration_raw.decode('utf-8')), delimiter='\t'):
            old, current = row['original_path'], row['current_path']
            require(old not in self.archive or self.archive[old] == current, 'Ambiguous migration path')
            require(not Path(current).is_absolute() and '..' not in Path(current).parts, 'Unsafe archive path')
            self.archive[old] = current

    def path(self, logical):
        p = Path(logical)
        require(p.is_absolute() and '..' not in p.parts, 'Unsafe evidence path: '+str(p))
        record = self.plan['path_reconciliation'].get(str(p))
        if record:
            p = Path(record['path'])
        # The saved plan records its checkout. Rebase only that exact prefix.
        old_root = Path(self.plan['repository'])
        if p.is_relative_to(old_root):
            p = self.root/p.relative_to(old_root)
        return p

    def expected(self, logical):
        actual = str(self.path(logical))
        candidates = {self.pins[n] for n in (str(logical), actual) if n in self.pins}
        # In another checkout the verified pin still names the saved root.
        if Path(actual).is_relative_to(self.root):
            old = str(Path(self.plan['repository'])/Path(actual).relative_to(self.root))
            if old in self.pins:
                candidates.add(self.pins[old])
        require(len(candidates) == 1, 'Missing or conflicting verified pin: '+str(logical))
        return candidates.pop()

    def bind(self, logical, expected=None):
        digest = self.expected(logical)
        if expected is not None:
            require(digest == expected, 'Expected identity differs: '+str(logical))
        path = self.path(logical)
        with path.open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == digest, 'Evidence changed: '+str(path))
        self.checked[str(path)] = digest
        return path

    def read(self, logical, expected=None):
        path = self.bind(logical, expected)
        return strict_json(checked_bytes(path, self.expected(logical)))

    def public(self, logical, digest=None):
        """Require a real exact-byte repository artifact for every public link."""
        path = self.path(logical)
        if path.is_relative_to(self.root):
            relative = str(path.relative_to(self.root))
        else:
            marker = '/benchmarks/clbg/'
            require(marker in str(logical), 'Evidence has no public archive path: '+str(logical))
            key = 'benchmarks/clbg/'+str(logical).split(marker, 1)[1]
            require(key in self.archive, 'Evidence is absent from migration map: '+key)
            relative = self.archive[key]
        actual = self.root/relative
        require(actual.is_file() and actual.resolve().is_relative_to(self.root), 'Missing public evidence: '+relative)
        expected = digest or self.expected(logical)
        checked_bytes(actual, expected)
        self.checked[str(actual)] = expected
        return relative

    def ref(self, logical, digest=None):
        expected = digest or self.expected(logical)
        return dict(path=self.public(logical, expected), sha256=expected)


def validate_reviews(review, metadata, plan, evidence):
    require(review['schema'] == 'pony-independent-full90-reconciliation-v1'
            and review['status'] == 'full90-reconciled-awaiting-runtime-and-publication-review'
            and review['file_integrity_verified'] is True and review['common_mutex_held'] is True
            and type(review['common_mutex_inode']) is int and review['common_mutex_inode'] == LOCK_INODE,
            'Independent completed file-bound reconciliation required')
    for key, value in dict(source_forms=20, pony_samples=60, matched_mech_samples=30,
                           actual_full_native_processes=90, retained_samples=54, added_samples=36,
                           repeated_completed_samples=0).items():
        require(type(review[key]) is int and review[key] == value, 'Incomplete full90 accounting: '+key)
    require(review['runtime_publication_metadata_qualified'] is False and review['chart_admission'] is False,
            'Reconciliation producer policy changed')
    require(review['verified_file_pins'].get(review['reconciler']['path']) == review['reconciler']['sha256'],
            'Independent reconciler source is not file-bound')
    evidence.bind(review['reconciler']['path'], review['reconciler']['sha256'])
    require(metadata['schema'] == 'pony-production-runtime-metadata-v1'
            and metadata['status'] == 'qualified-recorded-runtime-metadata'
            and metadata['runtime_publication_metadata_qualified'] is True
            and metadata['chart_admission'] is False, 'Verified runtime metadata required')
    require(metadata['runtime_gc_configuration_observed'] is False and metadata['gc_numeric_defaults_claimed'] is False,
            'Unexpected runtime observation claim')
    for key in ('compiler_invocations', 'native_probes', 'benchmark_samples'):
        require(type(metadata[key]) is int and metadata[key] == 0, 'Metadata review executed native work')
    require(review['plan']['sha256'] == metadata['plan_sha256'] == PLAN_SHA
            and review['plan']['path'] == metadata['plan'], 'Reviews bind different execution plans')
    same(review['source_evidence'], plan['source_evidence'], 'Source prerequisite summary differs')
    source = review['source_evidence']
    same({k: source[k] for k in ('source_work_profiles', 'bounded_cases_reused', 'canonical_loc_profiles',
                               'new_native_probes', 'new_source_count_replays')},
         dict(source_work_profiles=20, bounded_cases_reused=155, canonical_loc_profiles=20,
              new_native_probes=0, new_source_count_replays=0), 'Source qualification incomplete')
    require(source['tree_allocation']['unchanged_scored_binary_allocation_verified'] is True
            and source['tree_allocation']['allocation_review_sha256'] == ALLOCATION_SHA, 'Tree allocation unqualified')
    evidence.bind(metadata['review_tool']['path'], metadata['review_tool']['sha256'])
    require(set(plan['manifests']) == BENCHES, 'Ten workload manifests required')
    profiles = {r['key']: r for m in plan['manifests'].values() for r in m['profiles']}
    require(len(profiles) == 30 and set(profiles) == set(review['profiles']), 'Reconciled profile inventory differs')
    runtime = {r['key']: r for r in metadata['profiles']}
    pony = {k for k, r in profiles.items() if r['language'] == 'pony'}
    require(len(metadata['profiles']) == len(runtime) == len(pony) == 20 and set(runtime) == pony,
            'Exactly twenty matching runtime profiles required')
    require(set(review['matched_mech_controls']) == BENCHES, 'Ten matched Mech controls required')
    return profiles, runtime


def read_sources(plan, evidence):
    first = next(iter(plan['manifests'].values()))
    loc_ref, closed_ref = first['canonical_source_evidence'], first['canonical_source_closed_review']
    require(loc_ref['sha256'] == LOC_SHA and closed_ref['sha256'] == LOC_ROOT_SHA
            and first['source_work_qualification_sha256'] == WORK_SHA, 'Source proof identity changed')
    for manifest in plan['manifests'].values():
        for field in ('canonical_source_evidence', 'canonical_source_closed_review',
                      'source_work_qualification', 'source_work_qualification_sha256'):
            same(manifest[field], first[field], 'Workloads bind different source proofs')
    loc = evidence.read(loc_ref['path'], LOC_SHA)
    closed = evidence.read(closed_ref['path'], LOC_ROOT_SHA)
    work = evidence.read(first['source_work_qualification'], WORK_SHA)
    require(loc['status'] == 'qualified-exact-source-LOC' and loc['canonical_LOC_admitted'] is True
            and loc['chart_admission'] is False and loc['complete_authored_source_bundles'] is True
            and loc['profile_count'] == 20 and loc['unresolved'] == [], 'Incomplete canonical LOC closure')
    require(closed['status'] == 'closed-qualified-Pony20-canonical-LOC'
            and closed['overlay_sha256'] == LOC_SHA and closed['semantic_review_sha256'] == OWNER_SHA
            and closed['count_override'] is False and closed['chart_admission'] is False
            and (closed['profiles'], closed['unique_authored_sources'], closed['bundle_entries']) == (20, 21, 22),
            'Independent source ownership closure is missing')
    require(work['source_work_profiles'] == 20 and work['chart_admission'] is False,
            'Twenty source-work qualifications required')
    reviewed = {r['id']: r for r in work['reviewed_sources']}
    require(len(reviewed) == 20 and set(reviewed) == set(loc['profiles'])
            == set(loc['compiler_bound_input_inventory']), 'Work/LOC source cohorts differ')
    return loc, reviewed, evidence.ref(loc_ref['path'], LOC_SHA), evidence.ref(closed_ref['path'], LOC_ROOT_SHA), evidence.ref(first['source_work_qualification'], WORK_SHA)


def validate_three(row):
    samples = row['samples_seconds']
    require(type(samples) is list and len(samples) == 3 and all(positive(x) for x in samples),
            'Three finite positive actual samples required')
    require(row['median_seconds'] == sorted(samples)[1], 'Incorrect sample median')
    sd = statistics.stdev(samples)
    require(all(type(row[k]) in (int, float) and math.isfinite(row[k])
                and math.isclose(row[k], sd, rel_tol=1e-12, abs_tol=1e-12)
                for k in ('sample_stdev_seconds', 'independently_calculated_sample_stdev_seconds')),
            'Incorrect sample standard deviation')
    require(len(row['sample_evidence']) == len(row['attempts']) == 3
            and len(set(row['attempts'])) == 3, 'Missing sample evidence')
    return samples, sd


def build_publication(originals, review, metadata, plan, evidence, refs):
    data, languages = strict_json(originals[TARGETS[0]]), strict_json(originals[TARGETS[1]])
    prefix, module, suffix = module_object(originals[TARGETS[2]])
    before_data, before_languages, before_module = copy.deepcopy(data), copy.deepcopy(languages), copy.deepcopy(module)
    require('pony' not in {r['key'] for r in data['languages']}
            and 'pony' not in languages['languages'] and 'pony' not in module, 'Pony already published')
    require(not any(r['language'] == 'pony' for r in data['program_inventory'].values())
            and not any(r['language'] == 'pony' for r in data['programs'].values()), 'Pony programs already exist')
    require(set(b['key'] for b in data['benchmarks']) == BENCHES, 'Unexpected dataset workloads')
    profiles, runtime = validate_reviews(review, metadata, plan, evidence)
    loc, work, loc_ref, closed_ref, work_ref = read_sources(plan, evidence)
    report_ref = evidence.ref(review['report']['path'], review['report']['sha256'])
    report = evidence.read(review['report']['path'], review['report']['sha256'])
    def archive_link(original, current):
        require(original not in data['archive_paths'] or data['archive_paths'][original] == current,
                'Existing archive mapping conflicts: '+original)
        data['archive_paths'][original] = current

    for ref in (report_ref, loc_ref, closed_ref, work_ref, *refs.values()):
        archive_link(ref['path'], ref['path'])
    attempts = {a['attempt']: a for a in report['attempts']}
    require(len(report['attempts']) == len(attempts) == 90, 'Full report has a missing/repeated attempt')
    endpoints, dates, candidate_keys = {}, [], []
    for bench in data['benchmarks']:
        name = bench['key']
        control = review['matched_mech_controls'][name]
        same(control, review['profiles'][control['key']], 'Matched control differs from reconciled profile')
        require(control['language'] == 'mech' and control['benchmark'] == name, 'Wrong matched Mech control')
        validate_three(control)
        control_public = copy.deepcopy(control)
        control_public['source_evidence'] = evidence.ref(control['source'], control['source_sha256'])
        for sample in control_public['sample_evidence']:
            sample['raw_evidence'] = evidence.ref(sample['raw'])
            sample['supervisor_evidence'] = evidence.ref(sample['supervisor'])
        candidates = []
        cohort = [r for r in profiles.values() if r['language'] == 'pony' and r['benchmark'] == name]
        require(len(cohort) == 2 and {r['variant'] for r in cohort} == {'compact', 'optimized'}, 'Wrong two source forms')
        for row in cohort:
            key, identity = row['key'], row['id']
            require(key == name+':'+identity and key not in data['program_inventory'], 'Duplicate program identity')
            measured, native, counted = review['profiles'][key], runtime[key], loc['profiles'][identity]
            for field in ('id', 'benchmark', 'source', 'source_sha256', 'binary_sha256', 'loc', 'physical_loc',
                          'source_bundle', 'compiler_bound_input_inventory', 'command', 'cwd', 'runtime_environment'):
                same(measured[field], row[field], 'Reconciled profile differs: '+field)
            for field in ('key', 'id', 'benchmark', 'binary_sha256', 'command', 'runtime_environment',
                          'runtime_arguments', 'maximum_compute_actors'):
                same(native[field], row[field], 'Runtime profile differs: '+field)
            require(native['execution_mode'] == 'native-aot' and native['native_architecture'] == 'arm64'
                    and native['binary'] == row['command'][0]
                    and measured['matched_mech_control_key'] == control['key'], 'Runtime/control binding differs')
            same(native['sources'], [{k: s[k] for k in ('path', 'sha256', 'role')} for s in row['source_bundle']],
                 'Runtime and counted source bundles differ')
            same(row['source_bundle'], counted['source_bundle'], 'Canonical counted bundle differs')
            same(row['compiler_bound_input_inventory'], loc['compiler_bound_input_inventory'][identity],
                 'Compiler-bound authored inventory differs')
            require(work[identity]['source'] == row['source'] and work[identity]['source_sha256'] == row['source_sha256']
                    and counted['source_sha256'] == row['source_sha256']
                    and counted['canonical_loc'] == row['loc'] and counted['physical_loc'] == row['physical_loc'],
                    'Work/source/LOC identities differ')
            bundle = row['source_bundle']
            require(all(type(s[k]) is int and s[k] > 0 for s in bundle for k in ('physical_loc', 'normalized_loc'))
                    and row['loc'] == sum(s['normalized_loc'] for s in bundle)
                    and row['physical_loc'] == sum(s['physical_loc'] for s in bundle), 'Invalid source totals')
            files, roles = [], {}
            for source in bundle:
                require(source['role'] in {'application', 'application-helper'}
                        and source['unresolved_diagnostics'] == []
                        and source['ownership_review']['status'] == 'passed'
                        and source['ownership_review']['evidence_sha256'] == OWNER_SHA, 'Unresolved source role/LOC')
                sha = source['sha256']
                require(sha not in files, 'Duplicate content within a counted source bundle')
                path = evidence.public(source['path'], sha)
                code = checked_bytes(evidence.root/path, sha).decode('utf-8')
                original_path = source['path'].split('/benchmarks/clbg/', 1)[1]
                archive_link(original_path, path)
                file = dict(name=Path(path).name, path=original_path, archive_path=path, sha256=sha, code=code)
                if sha in data['files']:
                    require(data['files'][sha]['code'] == code and data['files'][sha]['sha256'] == sha,
                            'Existing source content conflicts')
                else:
                    data['files'][sha] = file
                files.append(sha)
                roles[sha] = dict(role=source['role'], normalized_loc=source['normalized_loc'],
                    physical_loc=source['physical_loc'], source_path=path,
                    loc_note='Exact authored compiler input; application and authored helpers included in canonical LOC.',
                    count_receipt=evidence.ref(source['count_receipt']['path'], source['count_receipt']['sha256']),
                    ownership_review=evidence.ref(source['ownership_review']['evidence_path'], OWNER_SHA))
            samples, sd = validate_three(measured)
            actual = [attempts[i] for i in measured['attempts']]
            same(samples, [a['seconds'] for a in actual], 'Sample values differ from actual report attempts')
            require(all(a['key'] == key and a['qualified'] is True for a in actual), 'Wrong or unqualified actual sample')
            sample_refs = []
            for a, item in zip(actual, measured['sample_evidence']):
                require(a['attempt'] == item['attempt'] and a['validation']['reference_match'] is True,
                        'Sample identity/output check differs')
                sample_refs.append(dict(item, raw_evidence=evidence.ref(item['raw']),
                                        supervisor_evidence=evidence.ref(item['supervisor'])))
                dates.extend((a['started_at'], a['finished_at']))
            provenance = dict(source_evidence=evidence.ref(row['source'], row['source_sha256']),
                qualification_origin=row['qualification_origin'], source_profile=row['source_profile'],
                source_bundle=copy.deepcopy(bundle), compiler_bound_input_inventory=copy.deepcopy(row['compiler_bound_input_inventory']),
                canonical_source_evidence=loc_ref, closed_source_review=closed_ref, required_work_evidence=work_ref,
                production_build=evidence.ref(native['build_receipt']), general_library_support=row['general_library_support'])
            program = dict(key=key, id=identity, benchmark=name, language='pony',
                loc=row['loc'], physical_loc=row['physical_loc'], loc_metric='statement-normalized',
                loc_report=loc_ref['path'], source_report=loc_ref['path'], loc_expansions=counted['expansions'],
                files=files, file_roles=roles, seconds=measured['median_seconds'], samples=samples, timing_sd=sd,
                binary_sha256=row['binary_sha256'], measurement_status='measured',
                report=report_ref['path'], report_sha256=report_ref['sha256'], required_work_validated=True,
                full_output_validation=[a['validation'] for a in actual], sample_execution_metadata=sample_refs,
                command=row['command'], runtime_arguments=native['runtime_arguments'], runtime_environment=row['runtime_environment'],
                execution_mode='aot', runtime_policy=metadata['runtime_policy'], memory_policy=metadata['memory_policy'],
                runtime_support='Pony standard library/runtime'+('; '+', '.join(row['general_library_support'])
                    if row['general_library_support'] else ''),
                vendor_libraries=copy.deepcopy(native['vendor_libraries']), runtime_evidence=copy.deepcopy(native),
                runtime_evidence_scope=metadata['evidence_scope'], runtime_gc_configuration_observed=False,
                gc_numeric_defaults_claimed=False, build_command=native['build_command'],
                timing_boundary=plan['manifests'][name]['timing_boundary'],
                timing_summary='Median of three actual full fresh-process runs; runtime startup, input, required work, complete output and shutdown included. Compilation, source review, validation and hashing excluded.',
                source_provenance='Exact retained Pony application and authored helper sources bound to the scored production binary; work, compiler input ownership and canonical LOC independently qualified.',
                source_provenance_record=provenance,
                source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(provenance['source_evidence']['path']),
                source_link_label='Exact retained source', local_adaptation=True,
                matched_mech_control=control_public, time_ratio_to_matched_mech=measured['median_seconds']/control['median_seconds'],
                measured_backend=dict(key='native-aot', execution='aot', label=metadata['runtime_policy'], verified=True,
                    evidence=dict(verified=True, report=report_ref['path'], report_sha256=report_ref['sha256'],
                        command=row['command'], source_sha256=files,
                        runtime_receipt=dict(verified=True, report=refs['runtime']['path'], report_sha256=refs['runtime']['sha256'],
                            field='/profiles/'+str(metadata['profiles'].index(native))+'/execution_mode',
                            value='native-aot', value_encoding='literal-saved-string'))),
                formatted_loc=None, formatted_loc_status='unavailable', formatted_loc_complete=False,
                formatted_loc_evidence={}, formatted_x=None,
                original_admission_policy=dict(eligible_for_chart=row['eligible_for_chart'],
                    manifest_chart_admission=plan['manifests'][name]['chart_admission'],
                    reconciliation_chart_admission=review['chart_admission'], runtime_chart_admission=metadata['chart_admission']),
                chart_admission=dict(historical_reports_unchanged=True, reconciliation=refs['reconciliation'],
                                     runtime_metadata=refs['runtime'], canonical_source_evidence=loc_ref),
                x=row['loc']/bench['baseline_loc'], y=measured['median_seconds']/bench['baseline_seconds'])
            data['program_inventory'][key] = program
            candidates.append(program); candidate_keys.append(key)
        fast = min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))
        small = min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))
        selected = list(dict.fromkeys((fast['key'], small['key'])))
        for key in selected:
            require(key not in data['programs'], 'Endpoint key already exists')
            data['programs'][key] = data['program_inventory'][key]
        bench['groups'].append(dict(language='pony', label='Pony', programs=selected, fast=fast['key'], small=small['key'],
                                    formatted_fast=None, formatted_small=None))
        endpoints[name] = dict(fast=fast['key'], small=small['key'], measured_forms=2)
    require(len(candidate_keys) == len(set(candidate_keys)) == 20, 'Not all twenty forms retained')
    bundles = [s for key in candidate_keys for s in profiles[key]['source_bundle']]
    require(len(bundles) == 22 and len({(s['path'], s['sha256']) for s in bundles}) == 21,
            'Exact authored-source closure changed')
    language = copy.deepcopy(metadata['language'])
    require(language['key'] == language['family'] == 'pony' and language['label'] == 'Pony', 'Wrong language classification')
    module['pony'] = {k: copy.deepcopy(language[k]) for k in META_FIELDS}
    benchmark_keys = [b['key'] for b in data['benchmarks']]
    data['languages'].append(dict(key='pony', label='Pony', color='#c680b6', family='pony',
        release_year=language['release_year'], release_name='Pony', release_source=language['sources'][0],
        release_note=language['release_note'], timed_benchmarks=benchmark_keys, source_benchmarks=benchmark_keys,
        formatted_timed_benchmarks=[], formatted_source_benchmarks=[], runtime_family=language['platform'],
        runtime=language['runtime'], execution_modes=language['execution'], typing=language['typing'],
        execution='AOT', line_style='solid', runtime_policy=metadata['runtime_policy'],
        paradigms=language['style'], memory_models=language['memory'], classification_note=language['note']))
    displayed = sum(p['language'] == 'pony' for p in data['programs'].values())
    languages['languages']['pony'] = dict(language, measurement_basis=[dict(report_ref, status='independently-reconciled-full90'),
        dict(refs['runtime'], status='verified-recorded-runtime-metadata')], runtime_policy=metadata['runtime_policy'],
        displayed_program_count=displayed, evidence_scope=metadata['evidence_scope'], runtime_gc_configuration_observed=False)
    languages['audited_on'] = datetime.now(timezone.utc).date().isoformat()
    languages['scope'] = (str(len(data['languages']))+' measured variants; all classifications explicit. '
        'Static typing is never inferred merely from absence in a dynamic-language list.')
    reference = dict(lang='pony', label='Pony')
    for form in ('fast', 'small'):
        selected = [data['program_inventory'][endpoints[b][form]] for b in benchmark_keys]
        reference[form] = {axis: statistics.geometric_mean(p[axis] for p in selected) for axis in ('x', 'y')}
    data['reference_summary'].append(reference)
    data['protocol']['pony'] = (metadata['runtime_policy']+'. Twenty exact authored source forms, sixty qualified Pony samples '
        'and thirty matched Mech controls. Complete bundle canonical LOC is available; formatted LOC is unavailable. '
        'Static build/link receipts establish implementation identity; actual loaded images and GC configuration were not observed.')
    for group in data['language_groups']:
        include = (group['key'] in language['execution'] or group['key'] in language['style']
                   or group['key'] == language['typing'])
        if include:
            require('pony' not in group['languages'], 'Duplicate language group member')
            group['languages'].append('pony')
    audit = dict(schema='pony-publication-import-v1', status='qualified-saved-cohort-prepared',
        reconciliation=refs['reconciliation'], runtime_metadata=refs['runtime'], full_report=report_ref,
        canonical_loc=loc_ref, closed_source_review=closed_ref, required_work=work_ref,
        candidate_sources=20, pony_samples=60, matched_mech_samples=30, actual_full_native_processes=90,
        imported_program_inventory=20, imported_endpoint_programs=displayed, endpoints=endpoints,
        earliest_sample=min(dates), latest_sample=max(dates), baseline_changed=False,
        historical_reports_mutated=False, source_or_timing_mutations=0, formatted_loc_available=False,
        runtime_gc_configuration_observed=False, native_commands=0, benchmark_runs=0,
        original_producer_chart_flags_preserved=True)
    data['pony_audit'] = audit
    # Preservation contract: every pre-existing row, source, endpoint, baseline,
    # exclusion, reference and unrelated top-level value remains type-identical.
    for field in ('programs', 'program_inventory', 'files', 'archive_paths'):
        same({k: data[field][k] for k in before_data[field]}, before_data[field], 'Existing '+field+' changed')
    for old, new in zip(before_data['benchmarks'], data['benchmarks']):
        same(dict(new, groups=new['groups'][:-1]), old, 'Existing benchmark or fixed baseline changed')
    same(data['languages'][:-1], before_data['languages'], 'Existing language rows changed')
    same(data['reference_summary'][:-1], before_data['reference_summary'], 'Existing aggregate references changed')
    same({k: v for k, v in data['protocol'].items() if k != 'pony'}, before_data['protocol'], 'Existing protocol changed')
    for old, new in zip(before_data['language_groups'], data['language_groups']):
        same(dict(new, languages=[k for k in new['languages'] if k != 'pony']), old, 'Existing language group changed')
    allowed = {'programs', 'program_inventory', 'files', 'archive_paths', 'benchmarks', 'languages', 'reference_summary', 'protocol', 'language_groups'}
    for key in set(before_data)-allowed:
        same(data[key], before_data[key], 'Unrelated dataset value changed: '+key)
    same({k: v for k, v in languages['languages'].items() if k != 'pony'}, before_languages['languages'], 'Existing audited language changed')
    for key in set(before_languages)-{'languages', 'scope', 'audited_on'}:
        same(languages[key], before_languages[key], 'Unrelated taxonomy value changed')
    same({k: v for k, v in module.items() if k != 'pony'}, before_module, 'Existing filter metadata changed')
    require(set(module) == set(languages['languages']) == {r['key'] for r in data['languages']}, 'Catalog keys differ')
    encoded = {TARGETS[0]: (json.dumps(data, indent=2, allow_nan=False)+'\n').encode(),
               TARGETS[1]: (json.dumps(languages, indent=2, allow_nan=False)+'\n').encode(),
               TARGETS[2]: (prefix+json.dumps(module, indent=2, allow_nan=False)+suffix).encode()}
    return encoded, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--reconciliation', type=Path, required=True)
    parser.add_argument('--reconciliation-sha256', required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--runtime-sha256', required=True)
    parser.add_argument('--benchmarks-sha256', required=True)
    parser.add_argument('--languages-sha256', required=True)
    parser.add_argument('--module-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True, help='Fresh private candidate directory; contains original byte backups')
    parser.add_argument('--apply', action='store_true', help='Also replace the three publication files after all verification')
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    require(not output.exists() and not output.is_relative_to(root), 'Fresh candidate output must be outside the repository')
    pins = dict(zip(TARGETS, (args.benchmarks_sha256, args.languages_sha256, args.module_sha256)))
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held, named = os.fstat(lock.fileno()), LOCK.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == LOCK_INODE,
                'Common timing mutex changed')
        originals = {name: checked_bytes(root/name, sha) for name, sha in pins.items()}
        review_raw = checked_bytes(args.reconciliation, args.reconciliation_sha256)
        metadata_raw = checked_bytes(args.runtime, args.runtime_sha256)
        review, metadata = strict_json(review_raw), strict_json(metadata_raw)
        plan_path = Path(review['plan']['path'])
        if not plan_path.is_file():
            plan_path = root/'experiments/pony/migration-resume-v1/plan.json'
        plan = strict_json(checked_bytes(plan_path, PLAN_SHA))
        evidence = Evidence(root, plan, [review['verified_file_pins'], review['durable_evidence_pins'],
            metadata['pins'], {str(plan_path): PLAN_SHA, metadata['review_tool']['path']: metadata['review_tool']['sha256']}])
        refs = {}
        for key, path, sha in (('reconciliation', args.reconciliation, args.reconciliation_sha256),
                               ('runtime', args.runtime, args.runtime_sha256)):
            path = path.resolve()
            require(path.is_relative_to(root), 'Publication review must be retained in the repository')
            refs[key] = dict(path=str(path.relative_to(root)), sha256=sha)
        for logical in evidence.pins:
            evidence.bind(logical)
        prepared, audit = build_publication(originals, review, metadata, plan, evidence, refs)
        # Final evidence/input recheck occurs before the first output write.
        for path, sha in list(evidence.checked.items()):
            with Path(path).open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == sha, 'Evidence changed during import: '+path)
        for name, sha in pins.items():
            checked_bytes(root/name, sha)
        checked_bytes(args.reconciliation, args.reconciliation_sha256)
        checked_bytes(args.runtime, args.runtime_sha256)
        require(evidence.migration_path.read_bytes() == evidence.migration_raw, 'Migration map changed during import')
        held_after, named_after = os.fstat(lock.fileno()), LOCK.stat()
        require((held_after.st_dev, held_after.st_ino) == (named_after.st_dev, named_after.st_ino)
                == (held.st_dev, held.st_ino), 'Mutex changed during import')
        output.mkdir(parents=True)
        for name, raw in prepared.items():
            target, backup = output/name, output/'originals'/name
            target.parent.mkdir(parents=True, exist_ok=True); backup.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw); backup.write_bytes(originals[name])
        receipt = dict(audit, generated_at=datetime.now(timezone.utc).isoformat(), applied=False,
            inputs=pins, outputs={name: sha_bytes(raw) for name, raw in prepared.items()},
            import_tool=dict(path=str(Path(__file__).resolve()), sha256=sha_bytes(Path(__file__).read_bytes())),
            checked_artifacts=evidence.checked, migration_map_sha256=sha_bytes(evidence.migration_raw),
            evidence_scope=metadata['evidence_scope'])
        if args.apply:
            replaced = []
            try:
                for name, raw in prepared.items():
                    checked_bytes(root/name, pins[name])
                    temporary = root/(name+'.pony-import.tmp')
                    with temporary.open('xb') as stream:
                        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                    temporary.replace(root/name); replaced.append(name)
            except BaseException:
                for name in reversed(replaced):
                    (root/name).write_bytes(originals[name])
                raise
            receipt['applied'] = True
            receipt['status'] = 'qualified-saved-cohort-imported'
        (output/'import-receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        print(json.dumps({k: receipt[k] for k in ('status', 'applied', 'imported_program_inventory',
            'imported_endpoint_programs', 'pony_samples', 'matched_mech_samples', 'baseline_changed')}))


if __name__ == '__main__':
    main()
