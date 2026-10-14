"""Reconcile retained Prolog evidence and seal reviewed work/LOC; no native runs.

Historical JSON is immutable. Paths are resolved through the migration index;
gzip stores exact original JSON bytes. Explicit editorial-only Markdown changes
are separate evidence, never silent replacements of executable/source hashes.
"""
import argparse
import ast
from copy import deepcopy
import csv
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import traceback

LEGACY = '/Users/cim310/mech-lang/benchmarks/benchmarks/clbg/'
OLD = '/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/'
REPLAY = LEGACY + 'prolog-comparison/20261013/source-counts/original22-replay-v1/replay.json'
REPLAY_SHA = '06ce8419f7bb8c3e6549627a4668c2297bf122f402b3e108349a734f3d464c2f'
REPLAY_BODY_SHA = '1f59886cf17ea7ffc2d8ef900a37c7dd4ff2f77dd27a85a34a7cbe809b523091'
REPLAY_DURABLE_SHA = 'cfacff5314fe89ef71a422aa66358221205af649ddbf9743ab9fbba6a0a56f44'
OWNER = LEGACY + 'continuation/owned-jobs/prolog-original22-owner-replay-v1/'
BENCHMARKS = ('binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
              'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def noneditorial_digest(raw, kind):
    if kind == 'json-next-step':
        value = json.loads(raw)
        assert type(value['next_step']) is str
        del value['next_step']
        return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
    if kind == 'python-migration-policy':
        tree = ast.parse(raw)
        selected = [node for node in ast.walk(tree) if isinstance(node, ast.keyword)
                    and node.arg == 'migration_policy']
        assert len(selected) == 1 and isinstance(selected[0].value, ast.Constant)
        assert type(selected[0].value.value) is str
        selected[0].value = ast.Constant(value=None)
        return digest(ast.dump(tree, include_attributes=False).encode())
    raise AssertionError(('Unreviewed editorial field', kind))


def save(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class Evidence:
    def __init__(self, root, overrides):
        self.root = root.resolve()
        with (root / 'migration/reorganization-paths.tsv').open() as stream:
            self.mapping = {row['original_path']: row['current_path']
                            for row in csv.DictReader(stream, delimiter='\t')}
        self.overrides = {(r['current_path'], r['historical_sha256']): r
                          for r in overrides['substitutions']}
        self.verified = {}
        self.stats = {}

    def path(self, historical):
        raw = str(historical)
        relative = ('benchmarks/clbg/' + raw.split('/benchmarks/clbg/', 1)[1]
                    if '/benchmarks/clbg/' in raw else raw)
        candidates = []
        if relative in self.mapping:
            candidates.append(self.root / self.mapping[relative])
        # New retained evidence may have been archived after the migration table.
        if relative.startswith('benchmarks/clbg/prolog-comparison/'):
            candidates.append(self.root / relative.replace('benchmarks/clbg/prolog-comparison/',
                                                           'archive/languages/prolog/', 1))
        if relative.startswith('benchmarks/clbg/continuation/owned-jobs/prolog-'):
            candidates.append(self.root / relative.replace('benchmarks/clbg/continuation/owned-jobs/',
                                                           'archive/qualification/prolog/executions/', 1))
        candidates.append(Path(raw))
        for path in candidates:
            if path.is_file():
                return path
            compressed = Path(str(path) + '.gz')
            if compressed.is_file():
                return compressed
        raise FileNotFoundError(raw)

    def read_bytes(self, historical, expected=None):
        path = self.path(historical)
        stat = path.stat()
        state = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        key = (str(historical), expected)
        if key in self.verified:
            assert self.stats[str(path)] == state, ('Changed evidence after verification', path)
        added_compression = path.suffix == '.gz' and not str(historical).endswith('.gz')
        raw = gzip.decompress(path.read_bytes()) if added_compression else path.read_bytes()
        actual = digest(raw)
        editorial = None
        if expected and actual != expected:
            relative = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path)
            editorial = self.overrides.get((relative, expected))
            assert (editorial and editorial['current_sha256'] == actual and
                    editorial['technical_content_preserved'] is True), ('Changed evidence', path, expected, actual)
            if path.suffix != '.md':
                assert path.suffix in ('.json', '.py')
                assert noneditorial_digest(raw, editorial['field_rule']) == editorial['noneditorial_sha256']
        self.verified[key] = dict(historical_path=str(historical), resolved_path=str(path),
            expected_sha256=expected, actual_content_sha256=actual,
            storage_encoding='gzip' if added_compression else 'identity', editorial_substitution=editorial)
        self.stats[str(path)] = state
        return raw

    def read(self, historical, expected=None):
        return json.loads(self.read_bytes(historical, expected))

    def pins(self, pins):
        for path, expected in pins.items():
            key = (path, expected)
            if key not in self.verified:
                self.read_bytes(path, expected)

    def unchanged(self):
        for path, expected in self.stats.items():
            s = Path(path).stat()
            assert (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns) == expected, ('Changed during seal', path)


def bare(node):
    while node['kind'] == 'group':
        node = node['children'][0]
    return node


def signature(node):
    node = bare(node)
    return (node['name'], len(node['children'])) if node['kind'] == 'term' else (node.get('value'), 0)


def inspect_ast(node, source, parent=None):
    assert node['kind'] in {'term', 'group', 'list', 'atom', 'number', 'string', 'variable'}
    start, end = node['start'], node['end']
    assert type(start) is type(end) is int and 0 <= start < end <= len(source)
    if parent:
        assert parent['start'] <= start < end <= parent['end']
    if node['kind'] == 'group':
        assert source[start] == '(' and source[end-1] == ')'
    if node['kind'] == 'term':
        a, b = node['functor_start'], node['functor_end']
        assert start <= a < b <= end
        assert source[a:b] == node['name'], ('Functor spelling', source[a:b], node['name'])
    children = list(node.get('children', []))
    if node.get('tail'):
        children.append(node['tail'])
    cursor = start
    for child in children:
        assert child['start'] >= cursor
        inspect_ast(child, source, node)
        cursor = child['end']


def review_owners(e, replay, review):
    """Check every saved owner span and compiler bridge against reviewed bytes."""
    assert replay['unresolved'] == [] and len(replay['sources']) == 22
    assert set(replay['profiles']) == {f'prolog-{b}-{v}' for b in BENCHMARKS for v in ('compact', 'optimized')}
    source_reviews, profiles, wams = {}, {}, {}
    for origin, source_entry in replay['sources'].items():
        raw = e.read_bytes(source_entry['retained_source'], source_entry['source_sha256'])
        assert raw == e.read_bytes(origin, source_entry['source_sha256'])
        source = raw.decode('utf8')
        packet = source_entry['original_reader_packet']
        assert packet == e.read(source_entry['scanner_stdout'], source_entry['scanner_stdout_sha256'])
        assert packet['source'] == origin and packet['source_text'] == source
        assert packet['schema'] == 'prolog-source-reader-v1' and packet['version'] == [10, 0, 2]
        assert packet['operators_before'] and packet['operators_before'] == packet['operators_after']
        assert packet['eof_char_count'] == len(source) and packet['comments'] == []
        cursor, definitions = 0, set()
        for form in packet['forms']:
            node = form['node']
            inspect_ast(node, source)
            assert form['quasi_quotation_count'] == 0
            assert not source[cursor:node['start']].strip()
            assert form['read_start'] <= node['start'] < node['end'] < form['read_end']
            assert source[node['end']:form['read_end']].strip() == '.'
            cursor = form['read_end']
            term = bare(node)
            sig = signature(term)
            if sig == (':-', 2):
                head = signature(term['children'][0])
                definitions.add(f'{head[0]}/{head[1]}')
            elif sig != (':-', 1):
                definitions.add(f'{sig[0]}/{sig[1]}')
        assert not source[cursor:].strip()
        expected = review['source_fingerprints'][source_entry['source_sha256']]
        accepted = None
        for identifier, reference in source_entry['profile_projections'].items():
            record = e.read(reference['path'], reference['sha256'])
            metric = record['original_projection']
            assert metric['diagnostics'] == [] and metric['language'] == 'prolog'
            assert metric['normalized_loc'] == expected['canonical_loc']
            assert metric['physical_loc'] == expected['physical_loc']
            assert metric['physical_loc'] == sum(bool(line.strip()) for line in source.splitlines())
            assert metric['normalized_loc'] == sum(item['units'] for item in metric['canonical_events'])
            assert len(metric['canonical_events']) == len(record['full_owner_expansions'])
            previous = 0
            for event, expansion in zip(metric['canonical_events'], record['full_owner_expansions']):
                assert event['units'] in (0, 1)
                a, b = event['start'], event['end']
                c, d = event['full_owner_start'], event['full_owner_end']
                assert 0 <= c <= a < b <= d <= len(source) and a >= previous
                previous = b
                assert event['byte_start'] == len(source[:a].encode('utf8'))
                assert event['byte_end'] == len(source[:b].encode('utf8'))
                assert event['line'] == source.count('\n', 0, a)+1
                assert expansion == dict(event, original_source=source[c:d])
                if event['kind'].endswith('-close'):
                    assert source[a:b] in (')', '.')
                if event['units'] == 0:
                    assert (event.get('merged_with_containing_control_header') or
                            event.get('merged_with_directive_header') or
                            event['kind'] in ('formal-meta-reference', 'named-closure-reference'))
            value = dict(source_sha256=source_entry['source_sha256'], normalized_loc=metric['normalized_loc'],
                         physical_loc=metric['physical_loc'], canonical_events=metric['canonical_events'],
                         full_owner_expansions=record['full_owner_expansions'], definitions=sorted(definitions))
            assert accepted is None or accepted == value, ('Shared helper context changed', origin)
            accepted = value
        assert accepted is not None
        source_reviews[origin] = accepted
    for identifier, row in replay['profiles'].items():
        original = row['original_scored_profile']
        files = row['source_bundle']
        expected_helpers = ['clbg_io.pl'] + (['clbg_records.pl'] if row['benchmark'] in ('knucleotide', 'revcomp') else [])
        assert [Path(f['origin']).name for f in files[1:]] == expected_helpers
        assert row['source'] == files[0]['path'] and row['source_sha256'] == files[0]['sha256']
        assert row['canonical_loc'] == sum(f['normalized_loc'] for f in files)
        assert row['physical_loc'] == sum(f['physical_loc'] for f in files)
        assert row['canonical_loc'] == review['bundle_totals'][row['benchmark']]['canonical_loc']
        assert row['physical_loc'] == review['bundle_totals'][row['benchmark']]['physical_loc']
        assert {f['origin']: (f['path'], f['sha256']) for f in files} == {
            f['original_path']: (f['path'], f['sha256']) for f in original['source_bundle']}
        for f in files:
            assert e.read_bytes(f['path'], f['sha256']) == e.read_bytes(f['origin'], f['sha256'])
            record = e.read(f['count_receipt']['path'], f['count_receipt']['sha256'])
            assert record['compiled_source'] == f['path'] and record['original_source'] == f['origin']
            assert record['compiled_source_sha256'] == record['original_source_sha256'] == f['sha256']
            assert record['exact_original_and_compiled_bytes_equal'] is True
            assert f['unresolved_diagnostics'] == []
        inv = original['compiler_bound_input_inventory']
        wam = e.read_bytes(inv['original_scored_wam'], inv['original_scored_wam_sha256']).decode()
        expected_defs = {'clbg_'+row['benchmark']+':'+d for d in source_reviews[row['source_origin']]['definitions']}
        expected_defs |= {'clbg_io:'+d for k,v in source_reviews.items() if k.endswith('/clbg_io.pl') for d in v['definitions']}
        if expected_helpers[-1] == 'clbg_records.pl':
            expected_defs |= {'clbg_records:'+d for k,v in source_reviews.items() if k.endswith('/clbg_records.pl') for d in v['definitions']}
        actual_defs = set(re.findall(r'^(clbg_\w+:\w+/\d+)$', wam, re.M))
        assert actual_defs == expected_defs, ('WAM predicate inventory', identifier, actual_defs ^ expected_defs)
        for witness in review['work_review'][row['benchmark']]['wam_required_fragments']:
            assert witness in wam, (identifier, witness)
        normalized = re.sub(r'^source .*\n', '', wam, flags=re.M)
        normalized = re.sub(r'0x[0-9a-fA-F]+', '<address>', normalized)
        prior = wams.get(row['benchmark'])
        assert prior is None or prior == normalized, ('Alias WAM differs beyond source paths/addresses', identifier)
        wams[row['benchmark']] = normalized
        profiles[identifier] = {k: row[k] for k in ('source', 'source_sha256', 'canonical_loc', 'physical_loc')}
        profiles[identifier]['source_bundle'] = [{k: f[k] for k in
            ('path', 'origin', 'sha256', 'role', 'normalized_loc', 'physical_loc')} for f in files]
    assert len(profiles) == 20 and sum(len(p['source_bundle']) for p in profiles.values()) == 44
    return dict(status='accepted-exact-Prolog22-source-owners-and20-whole-bundles',
        review_identity=review['review_identity'], reviewed_replay=dict(path=REPLAY, sha256=REPLAY_SHA),
        scored_source_WAM_review=replay['scored_source_WAM_review'],
        all_original_AST_and_owner_spans_reviewed=True, all22_original_sources_reviewed=True,
        all44_compiled_copy_bridges_reviewed=True, all20_complete_bundles_and_totals_reviewed=True,
        all20_scored_source_work_reviewed=True, unresolved=[], sources=source_reviews, profiles=profiles)


def durable(e, owner, pins, expected_command=None):
    done = e.read(owner+'terminal.json', pins[owner+'terminal.json'])
    request, start, worker = [e.read(owner+n, pins[owner+n])
                             for n in ('request.json','command-started.json','worker-started.json')]
    assert request['command'] == start['command'] == worker['command']
    if expected_command:
        assert request['command'] == expected_command
    assert request['cwd'] == start['cwd'] == worker['cwd']
    assert request['common_mutex_owned_by_target_command'] is True
    assert request['qualification_granted'] is request['automatic_retry'] is False
    assert done['status'] == 'command-exited-zero-awaiting-report-review'
    assert type(done['exit_code']) is int and done['exit_code'] == 0
    assert done['stop_signals'] == [] and done['actual_command_started'] is True
    assert done['command_identity_observation_missing'] is False
    assert start['command_identity'] == done['command_identity'] and start['command_pid'] == done['command_pid']
    assert worker['worker_identity'] == done['worker_identity']
    listing = done['command_identity']['listing'].split(None, 7)
    assert listing[:2] == [str(done['command_pid']), str(done['worker_identity']['pid'])]
    assert listing[7].split() == request['command']
    assert done['qualification_granted'] is done['automatic_retry'] is False
    assert not any(done.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure'))
    return done


def seal(e, replay, meaning, review, output):
    assert replay['scanner_commands'] == 22 and replay['compiled_copy_reconciliations'] == 44
    assert replay['original_subject_executions'] == replay['original_QLF_rebuilds'] == replay['original_WAM_reexecutions'] == 0
    assert replay['source_work_qualified'] is replay['canonical_LOC_admitted'] is replay['chart_admission'] is False
    closure_pins = review['original_replay_closure_pins']
    assert closure_pins[REPLAY.replace('replay.json','terminal.json')] == REPLAY_BODY_SHA
    assert closure_pins[OWNER+'terminal.json'] == REPLAY_DURABLE_SHA
    e.pins(closure_pins)
    body = e.read(REPLAY.replace('replay.json','terminal.json'), REPLAY_BODY_SHA)
    assert body['replay_sha256'] == REPLAY_SHA and body['status'] == replay['status']
    assert body['input_pins'] == replay['pins'] and body['artifact_pins'] == replay['artifact_pins']
    assert body['integrity_errors'] == [] and replay['terminal_evidence_complete'] is True
    e.pins(replay['pins'])
    e.pins(replay['artifact_pins'])
    source_root = LEGACY+'prolog-comparison/20261013/revisions/original-source-admission-v1/'
    expected = ['/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12',
                '-I','-S','-B','-u',source_root+'replay.py',
                '--worker-sha256',replay['pins'][source_root+'replay.py'],
                '--evidence-sha256',replay['pins'][source_root+'evidence.py'],
                '--review-sha256',replay['pins'][source_root+'REVIEW.md'],
                '--scored-review-sha256',replay['scored_source_WAM_review']['sha256']]
    durable(e, OWNER, closure_pins, expected)
    gates = {}
    counts = {'six': 14652, 'reader': 15888, 'work': 15048}
    for key, reference in replay['retained_gate_reviews'].items():
        root = e.read(reference['path'], reference['sha256'])
        assert root['error'] is None and root['input_pin_mismatches'] == [] and root['verified_pins'] == counts[key]
        assert root['actual_durable_exit_status'] == 0 and root['original_preparation_reexecutions'] == 0
        owner_pins = {path:record['sha256'] for path,record in root['copies'].items()}
        assert owner_pins[root['owner']+'/terminal.json'] == root['durable_terminal_sha256']
        durable(e, root['owner']+'/', owner_pins, root['command'])
        report_path = root['original_output'] + ('/fixture-receipt.json' if key == 'reader' else '/report.json')
        report = e.read(report_path, root['report_sha256'])
        e.read(root['original_output']+'/terminal-pin.json', root['body_terminal_sha256'])
        gates[key] = (root, report, reference)
    reader = gates['reader'][1]
    assert reader['tests_run'] == 31 and set(reader['started_ids']) == set(reader['discovered_ids']) == set(reader['expected_ids'])
    assert all(reader[k] == 0 for k in ('failures','errors','skipped','expected_failures','unexpected_successes'))
    six = gates['six'][1]['work_fixture_receipt']
    assert six['tests_run'] == six['discovered_tests'] == 6
    assert set(six['actual_test_ids']) == set(six['discovered_test_ids']) == set(six['expected_test_ids'])
    assert all(six[k] == [] for k in ('failures','errors','skips','expected_failures','unexpected_successes'))
    observed = gates['work'][1]
    assert observed['work_probe_processes'] == len(observed['case_results']) == len(observed['attempts']) == 30
    assert observed['new_native_commands'] == 56 and len(observed['instrumented_profiles']) == 6
    assert observed['actual_tree_map_pi_observations_reconciled'] is True
    prep = e.read(replay['actual_preparation']['path'], replay['actual_preparation']['sha256'])
    assert prep['all20_bounded_outputs_qualified'] is prep['terminal_evidence_complete'] is True
    assert prep['total_bounded_cases'] == 156 and prep['retained_contract_fixture_count'] == 6
    assert prep['retained_ownership_fixture_count'] == 11 and len(prep['profiles']) == 20
    runtime = e.read(prep['runtime_config'], prep['runtime_config_sha256'])
    assert runtime['status'] == 'qualified-runtime-discovery'
    assert runtime['version_components'] == [10, 0, 2]
    assert runtime['architecture'] == 'arm64' and runtime['runtime_backend'] == 'swi-native-bytecode-vm'
    assert runtime['default_gc_observed'] is True and runtime['bounded_observed'] is False
    assert runtime['prior_failures_relabelled'] is False
    factories = []
    for name, expected in [('pl-prims.c','28a235fd7c83b22af965e59b559c2c491361c943f6161fcc9b064bffabea9ecd'),
                           ('pl-fli.c','888cf810185db5443e7967aa47367c6e4851f0b638a8b4a13ae7c5eabc812797')]:
        prefix = OLD+'prolog-comparison/20261013/.build/'
        original = prefix+'swi-runtime-private-v2/official-source/swipl-10.0.2/src/'+name
        reviewed = prefix+'swi-runtime-directory-v1/official-source/swipl-10.0.2/src/'+name
        assert replay['pins'][original] == expected
        assert e.read_bytes(original, expected) == e.read_bytes(reviewed, expected)
        factories.append(dict(path=reviewed, sha256=expected, qualified_original_source=original,
            exact_qualified_source_copy=True, role='generic-SWI-native-factory-not-counted-application'))
    table_path = runtime['home']+'/library/hashtable.pl'
    table_reference = dict(path=table_path, sha256=replay['pins'][table_path])
    e.read_bytes(table_path, table_reference['sha256'])
    profiles, inventories, work_profiles = {}, {}, {}
    for identifier, row in replay['profiles'].items():
        original = row['original_scored_profile']
        assert original == prep['profiles'][identifier]
        files = deepcopy(row['source_bundle'])
        for item in files:
            item['ownership_review'] = dict(status='passed', review_identity=meaning['review_identity'],
                evidence_path=str(output/'meaning.json'), evidence_sha256=digest((output/'meaning.json').read_bytes()))
        profiles[identifier] = dict(source=row['source'], source_origin=row['source_origin'],
            source_sha256=row['source_sha256'], benchmark=row['benchmark'], variant=row['variant'],
            canonical_loc=row['canonical_loc'], physical_loc=row['physical_loc'], source_bundle=files,
            source_alias_of=row['source_alias_of'], semantic_review=files[0]['ownership_review'])
        inventory = deepcopy(replay['compiler_bound_input_inventory'][identifier])
        assert inventory['independently_retained_compiler_input_evidence'] == original
        assert inventory['original_compiler_input_evidence'] == original['compiler_bound_input_inventory']
        inventory.update(status='qualified-exact-authored-compiler-inputs', files=files)
        path = output/(identifier+'-compiled-inputs.json')
        save(path, inventory)
        inventories[identifier] = dict(inventory, evidence_path=str(path), evidence_sha256=digest(path.read_bytes()))
        item = dict(status='passed', source_sha256=original['source_sha256'], binary_sha256=original['binary_sha256'],
            application_artifact_pins=original['application_artifact_pins'],
            compiler_bound_input_inventory=original['compiler_bound_input_inventory'],
            source_review=dict(status='passed', evidence_path=str(output/'meaning.json'),
                evidence_sha256=digest((output/'meaning.json').read_bytes()), historical_scored_review=replay['scored_source_WAM_review']),
            original_scored_wam={k: original['compiler_bound_input_inventory'][v] for k,v in
                [('path','original_scored_wam'),('sha256','original_scored_wam_sha256')]})
        cases = [c for c in observed['case_results'] if c['id'] == identifier]
        benchmark = row['benchmark']
        if benchmark in ('binarytrees','knucleotide','pidigits'):
            assert len(cases) == (7 if benchmark == 'pidigits' else 4)
            key = {'binarytrees':'allocation_retention_witness','knucleotide':'seven_map_capacity_windows_witness',
                   'pidigits':'both_actual_divisions_witness'}[benchmark]
            item[key] = dict(status='passed', actual_cases=cases, closed_review=gates['work'][2])
            if benchmark == 'binarytrees':
                item['original_scored_vm_allocation_review'] = dict(status='passed',
                    evidence_path=str(output/'meaning.json'), actual_original_scored_wam=item['original_scored_wam'],
                    qualified_native_factory_sources=factories,
                    factory_source_review='functor/3 -> PL_unify_functor: allocate 1+arity cells including leaves')
            elif benchmark == 'knucleotide':
                item[key].update(per_window_trace_recorded=False, original_source_loop_review=item['source_review'],
                                 qualified_generic_table_source=table_reference)
        else:
            assert not cases
        work_profiles[identifier] = item
    work = dict(status='qualified-required-source-work', language='prolog', profiles=work_profiles,
        original_bounded_preparation=replay['actual_preparation'], actual_work30_closed_review=gates['work'][2],
        scored_source_WAM_review=replay['scored_source_WAM_review'], pins=replay['pins'], chart_admission=False,
        portable_pin_resolution='evidence-resolution.json')
    save(output/'qualified-work20.json', work)
    overlay = dict(status='qualified-exact-source-LOC', language='prolog', profile_count=20,
        profiles=profiles, compiler_bound_input_inventory=inventories, canonical_LOC_admitted=True,
        complete_authored_source_bundles=True, unresolved=[], chart_admission=False,
        fixture_receipt=dict(status='passed', **replay['reader_fixture_receipt']),
        replay_receipts=[dict(path=REPLAY, sha256=REPLAY_SHA)],
        actual_required_work=dict(path=str(output/'qualified-work20.json'), sha256=digest((output/'qualified-work20.json').read_bytes())),
        exact_owner_meaning_review=dict(path=str(output/'meaning.json'), sha256=digest((output/'meaning.json').read_bytes())),
        grammar_snapshot_pins={p:h for p,h in replay['pins'].items() if p.startswith(LEGACY+'loc-normalization/20261013/prolog-proposal-v5/')
            and Path(p).name in ('foreign_prolog.py','test_prolog.py','scan_source.pl','run_fixtures.py','REVIEW.md')},
        pins=replay['pins'], portable_pin_resolution='evidence-resolution.json')
    save(output/'qualified-loc-overlay.json', overlay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lock', type=Path, default=Path('/tmp/mech-clbg-timing.lock'))
    parser.add_argument('--review-only', action='store_true', help='Only the small saved source/AST/WAM checks; no whole dependency closure')
    args = parser.parse_args()
    review_path = args.root/'experiments/prolog/owner-review-spec.json'
    overrides_path = args.root/'experiments/prolog/editorial-substitutions.json'
    with args.lock.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        held, named = os.fstat(lock.fileno()), args.lock.stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
        args.output.mkdir(parents=True, exist_ok=False)
        e = Evidence(args.root, json.loads(overrides_path.read_text()))
        result = dict(status='failed', native_commands=0, benchmark_executions=0, chart_admission=False)
        try:
            review = e.read(str(review_path))
            e.read_bytes(str(Path(__file__).resolve()))
            e.read_bytes(str(overrides_path))
            replay = e.read(REPLAY, REPLAY_SHA)
            meaning = review_owners(e, replay, review)
            save(args.output/'meaning.json', meaning)
            if not args.review_only:
                seal(e, replay, meaning, review, args.output)
            e.unchanged()
            result.update(status='source-meaning-reviewed-awaiting-dependency-reconciliation' if args.review_only else
                'qualified-original-Prolog20-work-and-LOC-awaiting-full90',
                source_work_qualified=not args.review_only, canonical_LOC_admitted=not args.review_only,
                original_sources=22, compiled_copy_reconciliations=44, profiles=20)
        except BaseException as error:
            result.update(error=str(error), error_type=type(error).__name__)
            (args.output/'error.log').write_text(traceback.format_exc())
            raise
        finally:
            save(args.output/'evidence-resolution.json', dict(schema='portable-evidence-resolution-v1',
                records=list(e.verified.values()), historical_receipts_unchanged=True))
            result['outputs'] = {p.name:digest(p.read_bytes()) for p in args.output.iterdir() if p.is_file()}
            save(args.output/'outcome.json', result)
            print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
