#!/usr/bin/env python3
"""Import saved V executions without measuring or modifying historical evidence."""
import argparse
import ast
import copy
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import sys
from types import SimpleNamespace

BASE = 'v-report-only/20261012'
SUITE = BASE + '/reconciliation/all-ten-full-samples-v4.json'
LOC_REPORT = BASE + '/source-counts/recovery-20261014.json'
POWER = {'source': 'AC Power', 'low_power_mode': 0}
# Exact source forms reviewed for scope/ownership after the generic V normalizer
# conservatively flagged grammar. Never discard diagnostics for other sources.
REVIEWS = {
 'cc4f4f773be41fe75b604a5d4f191eac42227f2b3abf2d8f5145ed721d7b349c': {
  'vlang-conditional-expression-review': 'The if after position++ is an imperative CRLF handling block. Its header, body increment and close are each counted.',
  'vlang-constructor-in-control-header-review': 'The final tokens are masked rune literals in comparisons. These are ordinary if/for conditions, not constructors. Each header and explicit close is counted; packed close/else headers count twice.'},
 '667d02fb557bc2fb1c19edb589f3ce2c2a45abee2ffab4c8ee2fd0c94a364aa3': {
  'vlang-conditional-expression-review': 'The if after printed++ is an imperative output-padding condition, with counted loop, writes and explicit closes.'},
 'c9c78dc4f4daa1140d5d04008132c1557274910efbd593388a3f04346d9e7d8c': {
  'vlang-imperative-block-review': 'defer and its nested unsafe block each have a counted header and explicit close; sb.free() is a counted statement. Both output branches and all builder calls are included.'},
 'bd0422be6166adb33dc99ed3c117362b2d5fafc3ae323bcde7204dd0e8437202': {
  'vlang-conditional-expression-review': 'The if after position++ is an imperative wraparound condition. Header, position assignment and explicit close are independently counted.'},
 'ce86ea460b32ab963d1c302468d3bd0df2653fb9e9d76e7effbeeeee2883f700': {
  'vlang-imperative-block-review': 'return match owns the nucleotide decoding expression. Each single-value rune arm is one written expression; the else arm has a counted header, panic call and close. The surrounding match close is counted. No packed independent statements are hidden in the arms.'},
 'b109deea791eb821cd1b38183b68f03a1ce4d210cce5484e5ba9b19276db652f': {
  'vlang-conditional-expression-review': 'The if after digits[width - 1]++ is an imperative break condition. Header, break and explicit close are independently counted.'},
}
STDLIB = {'os', 'io', 'regex', 'strconv', 'math', 'math.big', 'strings'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-dir', type=Path, default=Path('/tmp/mech-benchmark-recovery'))
    args = parser.parse_args()
    clbg = args.repo.resolve() / 'benchmarks/clbg'
    args.audit_dir.mkdir(parents=True, exist_ok=True)
    checked = {}
    recovered = []

    def relative(name):
        name = str(name)
        return name.split('/benchmarks/clbg/', 1)[1] if '/benchmarks/clbg/' in name else name

    def resolve(name):
        candidate = clbg / relative(name)
        if candidate.is_file():
            return candidate
        original = Path(name)
        if original.is_absolute() and original.is_file():
            return original
        raise FileNotFoundError(name)

    def check(name, digest):
        path = resolve(name)
        actual = sha(path)
        assert actual == digest, (str(path), actual, digest)
        checked[relative(name)] = {'sha256': digest, 'read_from': str(path)}
        return path

    suite_path = clbg / SUITE
    suite = json.loads(suite_path.read_text())
    pins = suite['pins']
    assert suite['status'] == 'all-ten-workloads-independently-reconciled'
    assert suite['canonical_full_native_processes'] == 90 and suite['candidate_sources'] == 20
    assert suite['actual_samples_per_source'] == 3
    assert suite['report_only'] and suite['never_chart_eligible'] and not suite['chart_admission']
    assert not suite['original_reports_mutated']

    # Reuse only the existing pure receipt validator via AST; importing any
    # study module could initialize launch/build code with historical paths.
    validator_path = clbg / BASE / 'reconcile_full_v2.py'
    pinned_validator = next(name for name in pins if name.endswith('/' + BASE + '/reconcile_full_v2.py'))
    check(pinned_validator, pins[pinned_validator])
    tree = ast.parse(validator_path.read_text())
    nodes = [node for node in tree.body if (
        isinstance(node, ast.FunctionDef) and node.name in {'require', 'validate_data'}
        or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {'POWER', 'EMPTY', 'FATAL'} for t in node.targets))]
    namespace = dict(json=json, math=math, statistics=statistics, deepcopy=copy.deepcopy)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(validator_path), 'exec'), namespace)

    def support_pins(value):
        result = {}
        if isinstance(value, dict):
            if value.get('path') and isinstance(value.get('sha256'), str):
                result[value['path']] = value['sha256']
            for name, child in value.items():
                if name in {'pins', 'libraries', 'pin_files', 'support_pins'} and isinstance(child, dict):
                    for filename, digest in child.items():
                        if isinstance(digest, str) and len(digest) == 64:
                            result[str(Path(filename).absolute())] = digest
                            result[str(Path(filename).resolve())] = digest
                if isinstance(child, (dict, list)):
                    result.update(support_pins(child))
        elif isinstance(value, list):
            for child in value:
                result.update(support_pins(child))
        return result

    def fingerprint(row):
        return json.dumps(dict(source_sha256=row['source_sha256'], binary_sha256=row.get('binary_sha256'),
            command=[x.replace(row['source'], '{source}') for x in row['command']], cwd=row['cwd'],
            environment=row.get('runtime_environment', {}), support=support_pins(row)), sort_keys=True)

    compact_tree = ast.parse((clbg / 'compact/run.py').read_text())
    constants = {}
    for node in compact_tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'WORK', 'HASHES'}:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    work = constants['WORK'] | {'regexredux': (30, 5000000), 'pidigits': (30, 10000)}
    harness = SimpleNamespace(WORK=work, LOCK=Path('/tmp/mech-clbg-timing.lock'), execution_fingerprint=fingerprint)
    assert set(suite['benchmarks']) == set(work)

    # Verify the frozen tested normalizer, then recount every actual source.
    fixture = clbg / 'loc-normalization/20261012/jobs/vlang-fixtures-02/receipt.json'
    fixture_doc = json.loads(fixture.read_text())
    assert fixture_doc['status'] == 'passed' and fixture_doc['tests_run'] == 17
    for name, digest in fixture_doc['frozen_module_pins'].items():
        check(name, digest)
    check(fixture_doc['pygments_module'], fixture_doc['pygments_module_sha256'])
    snapshot = resolve(next(n for n in fixture_doc['frozen_module_pins'] if n.endswith('/vlang.py'))).parent
    sys.path[:0] = [str(snapshot), str(Path(fixture_doc['pygments_module']).parent.parent)]
    sys.dont_write_bytecode = True
    from vlang import normalize_vlang

    data = json.loads(args.input.read_text())
    assert not any(lang['key'] == 'v' for lang in data['languages']), 'V already imported'
    originals = copy.deepcopy(data['programs'])
    original_bases = {b['key']: (b['baseline_loc'], b['baseline_seconds']) for b in data['benchmarks']}
    loc_audit = dict(status='exact-sources-reviewed', method='Frozen generic V canonical normalizer plus exact-source grammar review; application closures and every non-unit expansion reviewed. No source or timing changes.',
        fixture_receipt=relative(fixture), fixture_receipt_sha256=sha(fixture), tests_run=17, profiles=[])
    benches = {b['key']: b for b in data['benchmarks']}
    program_rows = []
    endpoints = {}
    dates = []
    raw_count = 0
    for benchmark, entry in suite['benchmarks'].items():
        manifest_path = check(entry['manifest'], entry['manifest_sha256'])
        report_path = check(entry['report'], entry['report_sha256'])
        manifest = json.loads(manifest_path.read_text())
        report = json.loads(report_path.read_text())
        if benchmark == 'binarytrees':
            assert report['retained_attempt_count'] == 1 and report['fresh_attempt_count'] == 8
            assert report['original_report_mutated'] is False
        if benchmark == 'nbody':
            reference = dict(energies=[-0.169075164, -0.169059907], tolerance=1e-8)
        elif benchmark in {'pidigits', 'regexredux'}:
            reference_file = clbg / benchmark / 'inputs/output-full.txt'
            reference = dict(bytes=reference_file.stat().st_size, sha256=sha(reference_file))
        elif benchmark in {'spectralnorm', 'fannkuchredux'}:
            body = {'spectralnorm': b'1.274224153\n', 'fannkuchredux': b'3968050\nPfannkuchen(12) = 65\n'}[benchmark]
            reference = dict(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        else:
            size, digest = constants['HASHES'][benchmark][1]
            reference = dict(bytes=size, sha256=digest)

        def read_raw(name):
            nonlocal raw_count
            assert name in pins, name
            raw_count += 1
            return json.loads(check(name, pins[name]).read_text())

        rows, exclusions = namespace['validate_data'](manifest, report, entry['manifest_sha256'], harness, reference, read_raw)
        for identity, row in rows.items():
            for field in ['language', 'variant', 'source_sha256', 'samples_seconds', 'median_seconds', 'loc']:
                assert row[field] == entry['profiles'][identity][field], (identity, field)
        assert exclusions == entry['environment_exclusions']
        control = next(v for v in entry['profiles'].values() if v['language'] == 'mech')
        candidates = []
        for profile in manifest['profiles']:
            if profile['language'] != 'v':
                continue
            identity = profile['id']
            row = rows[identity]
            source_path = check(profile['source'], profile['source_sha256'])
            check(profile['original_source'], profile['source_sha256'])
            code = source_path.read_text()
            imports = re.findall(r'^\s*import\s+([\w.]+)', code, re.M)
            assert imports and set(imports) <= STDLIB, (identity, imports)
            actual_sources = sorted(p.name for p in source_path.parent.glob('*.v'))
            assert actual_sources == ['program.v'], (identity, actual_sources)
            assert profile['required_work_review']['status'] == 'passed'
            assert profile['required_work_review']['source_sha256'] == profile['source_sha256']
            assert profile['small_validation']['reference_match']
            assert profile.get('native_benchmark_kernel') is False
            assert profile['maximum_compute_workers'] <= 8
            assert profile['runtime']['version'] == 'V 0.5.2 7647ce1'
            # Hash saved executable/compiler bytes for identity only: no runs.
            check(profile['binary'], profile['binary_sha256'])
            check(profile['runtime']['path'], profile['runtime']['sha256'])
            for evidence in [profile['required_work_review'].get('qualification')]:
                if evidence:
                    assert evidence in pins
                    check(evidence, pins[evidence])
            normalized = normalize_vlang(code, 'vlang')
            diagnostic_reviews = []
            for diagnostic in normalized['diagnostics']:
                resolution = REVIEWS.get(profile['source_sha256'], {}).get(diagnostic['kind'])
                assert resolution, (identity, diagnostic)
                diagnostic_reviews.append(dict(diagnostic, line=code.count('\n', 0, diagnostic['offset']) + 1, resolution=resolution))
            # All non-unit expansions of these formatted exact sources are
            # imperative error handlers (4 units) or close+else (2 units).
            for expansion in normalized['expansions']:
                units = expansion['normalized_units']
                if units != 1:
                    assert (units == 4 and 'or { panic(err) }' in expansion['original']) or (units == 2 and '} else' in expansion['original']), (identity, expansion)
            count = dict(id=identity, benchmark=benchmark, variant=profile['variant'], source=relative(profile['source']),
                source_sha256=profile['source_sha256'], physical_loc=normalized['physical_loc'], normalized_loc=normalized['normalized_loc'],
                rule_version=normalized['rule_version'], expansions=normalized['expansions'], diagnostics=normalized['diagnostics'],
                diagnostic_reviews=diagnostic_reviews, review_status='source-grammar-reviewed', imports=imports,
                authored_source_files=[relative(profile['source'])], additional_authored_helpers=[],
                standard_library_policy='Unmodified V standard library supplies I/O, strings, math, regex and pure-V arbitrary precision; no custom domain kernel or omitted application helper.')
            loc_audit['profiles'].append(count)
            filekey = profile['source_sha256']
            data['files'][filekey] = dict(name=source_path.name, path=relative(profile['source']), sha256=filekey, code=code)
            samples = row['samples_seconds']
            attempts = [copy.deepcopy(a) for a in report['attempts'] if a['id'] == identity and a['qualified']]
            dates.extend(a['started_at'] for a in attempts)
            key = benchmark + ':' + identity
            program = dict(key=key, id=identity, benchmark=benchmark, language='v', loc=count['normalized_loc'],
                physical_loc=count['physical_loc'], loc_metric='statement-normalized', loc_report=LOC_REPORT, source_report=LOC_REPORT,
                loc_expansions=count['expansions'], seconds=row['median_seconds'], samples=samples, timing_sd=statistics.stdev(samples),
                files=[filekey], file_roles={filekey: dict(role='application', loc_note='Complete actual V application source; all authored code counted.',
                    normalized_loc=count['normalized_loc'], physical_loc=count['physical_loc'])},
                report=relative(entry['report']), measurement_status='measured', binary_sha256=profile['binary_sha256'],
                required_work_validated=True, full_output_validation=[a['validation'] for a in attempts], sample_execution_metadata=attempts,
                runtime_arguments=profile['command'], execution_mode='aot', runtime_policy='V 0.5.2 7647ce1; C backend, Clang 22, native macOS ARM64',
                memory_policy='Default V memory management; exact recorded compiler flags retained.', runtime_support=profile.get('library'),
                timing_boundary=manifest['timing_boundary'], timing_summary='Median of three saved full fresh-process runs; startup, full input, computation, complete output and teardown included; compilation and validation excluded.',
                source_url=profile.get('provenance', {}).get('upstream_repository', 'https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/' + benchmark + '.html'),
                source_link_label='Source provenance', local_adaptation=True, source_provenance=('Complete V ' + profile['variant'] + ' application source, ' + profile['provenance']['kind'] + '. Original upstream and revision provenance are retained in the source evidence; every authored statement is counted.'), source_provenance_record=profile['provenance'],
                matched_mech_control=control, time_ratio_to_matched_mech=row['median_seconds'] / control['median_seconds'],
                measured_backend=dict(key='native-aot', execution='aot', label='V 0.5.2 / Clang 22, native macOS ARM64', verified=True,
                    evidence=dict(verified=True, report=relative(entry['report']), report_sha256=entry['report_sha256'], command=profile['command'],
                        source_sha256=[filekey], runtime_receipt=dict(verified=True, report=relative(entry['manifest']), report_sha256=entry['manifest_sha256'],
                            field='/profiles/' + str(manifest['profiles'].index(profile)) + '/runtime/version', value=profile['runtime']['version'], value_encoding='literal-saved-string'))),
                formatted_loc=None, formatted_loc_status='pending', formatted_loc_complete=False, formatted_loc_evidence={}, formatted_x=None,
                original_admission_policy=dict(report_only=True, never_chart_eligible=True, chart_admission=False),
                chart_admission=dict(historical_reports_unchanged=True),
                build_command=profile['build_command'])
            baseline_loc, baseline_seconds = original_bases[benchmark]
            assert program['loc'] >= baseline_loc and program['seconds'] >= baseline_seconds, 'V changes baseline; update all existing ratios explicitly'
            program.update(x=program['loc'] / baseline_loc, y=program['seconds'] / baseline_seconds)
            data['program_inventory'][key] = program
            candidates.append(program)
            program_rows.append(program)
        fast = min(candidates, key=lambda p: (p['seconds'], p['loc'], p['key']))
        small = min(candidates, key=lambda p: (p['loc'], p['seconds'], p['key']))
        selected = list(dict.fromkeys([fast['key'], small['key']]))
        for key in selected:
            data['programs'][key] = data['program_inventory'][key]
        benches[benchmark]['groups'].append(dict(language='v', label='V', programs=selected, fast=fast['key'], small=small['key'], formatted_fast=None, formatted_small=None))
        endpoints[benchmark] = dict(fast=fast['key'], small=small['key'], measured_forms=len(candidates))

    assert len(program_rows) == 20 and raw_count == 90
    assert all(data['programs'][key] == value for key, value in originals.items())
    assert original_bases == {b['key']: (b['baseline_loc'], b['baseline_seconds']) for b in data['benchmarks']}
    benchmark_keys = list(benches)
    data['languages'].append(dict(key='v', label='V', color='#4f87c4', release_year=2019, release_name='V',
        release_source='https://github.com/vlang/v/blob/master/CHANGELOG.md', release_note='Public V releases in 2019; official changelog documents the June 2019 series.',
        timed_benchmarks=benchmark_keys, source_benchmarks=benchmark_keys, formatted_timed_benchmarks=[], formatted_source_benchmarks=[]))
    reference = dict(lang='v', label='V')
    for form in ['fast', 'small']:
        selected = [data['programs'][endpoints[b][form]] for b in benchmark_keys]
        reference[form] = {axis: statistics.geometric_mean(p[axis] for p in selected) for axis in ['x', 'y']}
    data['reference_summary'].append(reference)
    data['protocol']['v'] = ('V 0.5.2 7647ce1, native C backend with Clang 22 and -prod -O3 -march=native -ffp-contract=off. '
        'Twenty complete authored source forms across all ten full workloads; three saved fresh-process samples per form and thirty matched Mech controls. '
        'Actual output checks, process/environment receipts, runtime/compiler identity, complete source and canonical LOC are retained.')
    if isinstance(data['protocol'].get('native_ready_languages'), str):
        data['protocol']['native_ready_languages'] = data['protocol']['native_ready_languages'].replace('V is report-only and Red is excluded.', 'V is now included from its separately audited saved cohort; Red is excluded.')
    for audit_key in ['native_language_audit', 'native_ready_publication_audit']:
        if audit_key in data:
            data[audit_key]['V_visualization_entries'] = sum(p['language'] == 'v' for p in data['programs'].values())
    audit = dict(status='saved-cohort-imported', suite=SUITE, suite_sha256=sha(suite_path), canonical_loc=LOC_REPORT,
        candidate_sources=20, samples_per_source=3, v_samples=60, matched_mech_samples=30, actual_full_native_processes=90,
        earliest_sample=min(dates), latest_sample=max(dates), source_or_timing_mutations=0, historical_reports_mutated=False,
        endpoints=endpoints, baseline_changed=False, checked_artifacts=checked)
    data['v_audit'] = audit
    loc_audit['normalizer_pins'] = fixture_doc['frozen_module_pins']
    write_json(args.audit_dir / 'v-loc-audit.json', loc_audit)
    write_json(args.output, data)
    original_vroot = Path(next(iter(suite['benchmarks']['nbody']['profiles'].values()))['source']).parents[4]
    assert original_vroot.name == '20261012'
    for source in sorted(original_vroot.rglob('*.v')):
        rel = source.relative_to(original_vroot)
        if rel.parts[0].startswith('.'):
            continue
        destination = args.audit_dir / 'v-sources' / BASE / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        recovered.append(dict(original=str(source), original_relative='benchmarks/clbg/' + BASE + '/' + str(rel),
            staged=str(destination), sha256=sha(source), bytes=source.stat().st_size))
    write_json(args.audit_dir / 'v-source-map.json', recovered)
    write_json(args.audit_dir / 'v-import-result.json', dict(audit, output=str(args.output), imported_program_inventory=20,
        imported_endpoint_programs=sum(p['language'] == 'v' for p in data['programs'].values()), recovered_source_files=len(recovered),
        recovered_source_bytes=sum(r['bytes'] for r in recovered), loc_audit=str(args.audit_dir / 'v-loc-audit.json'),
        source_map=str(args.audit_dir / 'v-source-map.json'), reference_summary=reference,
        notes=['No compiler, benchmark or runtime was executed.', 'All original benchmark ratios and baselines retained because V sets no new minimum.']))
    print(json.dumps(dict(output=str(args.output), v_forms=20, v_samples=60, controls=30, endpoints=len([p for p in data['programs'].values() if p['language']=='v']), recovered_sources=len(recovered), canonical_loc_review='complete')))


if __name__ == '__main__':
    with Path('/tmp/mech-clbg-timing.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        main()
