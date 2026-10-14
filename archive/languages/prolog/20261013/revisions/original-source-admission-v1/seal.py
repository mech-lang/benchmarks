"""Admit actual reviewed original Prolog owners and existing whole20 work."""
import argparse
from contextlib import ExitStack
from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import traceback

P = Path(__file__).resolve().parent
H = P.parents[1]
LOCK = Path('/tmp/mech-clbg-timing.lock')


def main():
    parser = argparse.ArgumentParser()
    for name in ('worker-sha256', 'evidence-sha256', 'review-sha256', 'scored-review-sha256',
                 'replay-sha256', 'replay-terminal-sha256', 'replay-durable-sha256', 'meaning-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('replay-owner', 'meaning'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    assert sys.dont_write_bytecode
    assert all(len(value) == 64 and set(value) <= set('0123456789abcdef')
        for key, value in vars(args).items() if key.endswith('_sha256'))
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Prolog original-source seal interrupted: ' + str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
        signal.signal(signum, interrupted)
    print('WAIT common mutex: reviewed whole20 Prolog source/work/LOC seal', flush=True)
    with LOCK.open('r+') as lock, ExitStack() as dependencies:
        fcntl.flock(lock, fcntl.LOCK_EX)
        held, named = os.fstat(lock.fileno()), LOCK.stat()
        assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134
        output = H / 'source-counts/qualified-original22-v1'
        output.mkdir(parents=True, exist_ok=False)
        pins, failure, e = {}, None, None
        outcome = dict(status='failed-Prolog-original-source-admission', native_commands=0,
            preparation_or_fixture_reexecutions=0, chart_admission=False, canonical_LOC_admitted=False,
            source_work_qualified=False)
        signal.alarm(1200)
        try:
            path = P / 'evidence.py'
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == args.evidence_sha256 and not path.stat().st_mode & 0o222
            spec = importlib.util.spec_from_file_location('prolog_original22_seal_evidence_v1', path)
            e = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = e
            exec(compile(raw, str(path), 'exec'), e.__dict__)
            for path, digest in ((P / 'seal.py', args.worker_sha256), (P / 'evidence.py', args.evidence_sha256),
                                 (P / 'SEAL_REVIEW.md', args.review_sha256)):
                assert not path.stat().st_mode & 0o222
                e.bind(path, digest, pins)
            authority, modules, gates = e.load(pins, dependencies, args.scored_review_sha256)
            assert Path(sys.executable).resolve() == Path(e.PYTHON).resolve()
            replay_path = H / 'source-counts/original22-replay-v1/replay.json'
            replay = e.read(replay_path, args.replay_sha256, pins)
            terminal = e.read(replay_path.with_name('terminal.json'), args.replay_terminal_sha256, pins)
            assert terminal['status'] == replay['status'] == 'original22-Prolog-owner-replay-awaiting-exact-meaning-review'
            assert terminal['replay'] == str(replay_path) and terminal['replay_sha256'] == args.replay_sha256
            assert terminal['input_pins'] == replay['pins'] and terminal['artifact_pins'] == replay['artifact_pins']
            assert terminal['integrity_errors'] == [] and terminal['exclusive_common_mutex_held'] is True
            assert replay['terminal_evidence_complete'] is replay['exclusive_common_mutex_held'] is True
            assert replay['unresolved'] == [] and replay['original_source_count'] == replay['scanner_commands'] == 22
            assert replay['profile_count'] == len(replay['profiles']) == 20 and replay['compiled_copy_reconciliations'] == 44
            assert replay['preparation_or_fixture_reexecutions'] == replay['original_subject_executions'] == 0
            assert replay['source_work_qualified'] is replay['canonical_LOC_admitted'] is replay['chart_admission'] is False
            for mapping in (replay['pins'], replay['artifact_pins']):
                for path, digest in mapping.items(): e.bind(path, digest, pins)
            owner = args.replay_owner.resolve(strict=True)
            assert owner.parent == e.NEW / 'continuation/owned-jobs'
            e.lease(owner / 'owner.lock', dependencies)
            done = e.read(owner / 'terminal.json', args.replay_durable_sha256, pins)
            request, start, worker = [e.read(owner / name, e.sha(owner / name), pins)
                for name in ('request.json', 'command-started.json', 'worker-started.json')]
            expected = [e.PYTHON, '-I', '-S', '-B', '-u', str(P / 'replay.py'),
                '--worker-sha256', replay['pins'][str(P / 'replay.py')],
                '--evidence-sha256', replay['pins'][str(P / 'evidence.py')],
                '--review-sha256', replay['pins'][str(P / 'REVIEW.md')],
                '--scored-review-sha256', args.scored_review_sha256]
            assert request['command'] == start['command'] == worker['command'] == expected
            assert request['cwd'] == start['cwd'] == worker['cwd'] == str(e.NEW.parents[1])
            assert request['common_mutex_owned_by_target_command'] is True
            assert request['qualification_granted'] is request['automatic_retry'] is False
            assert done['status'] == 'command-exited-zero-awaiting-report-review' and type(done['exit_code']) is int and done['exit_code'] == 0
            assert done['stop_signals'] == [] and done['actual_command_started'] is True
            assert done['command_identity_observation_missing'] is False
            assert not any(done.get(key) for key in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure'))
            assert done['qualification_granted'] is done['automatic_retry'] is False
            assert start['command_identity'] == done['command_identity'] and start['command_pid'] == done['command_pid']
            assert worker['worker_identity'] == done['worker_identity']
            listing = done['command_identity']['listing'].split(None, 7)
            assert listing[:2] == [str(done['command_pid']), str(done['worker_identity']['pid'])] and listing[7].split() == expected
            assert not args.meaning.stat().st_mode & 0o222
            meaning = e.read(args.meaning, args.meaning_sha256, pins)
            assert meaning['status'] == 'accepted-exact-Prolog22-source-owners-and20-whole-bundles'
            assert meaning['review_identity'] and meaning['review_identity'] != 'Prolog replay author'
            assert meaning['reviewed_replay'] == dict(path=str(replay_path), sha256=args.replay_sha256)
            assert meaning['scored_source_WAM_review'] == replay['scored_source_WAM_review'] == dict(path=str(e.SCORING), sha256=args.scored_review_sha256)
            assert all(meaning[key] is True for key in ('all_original_AST_and_owner_spans_reviewed',
                'all22_original_sources_reviewed', 'all44_compiled_copy_bridges_reviewed',
                'all20_complete_bundles_and_totals_reviewed', 'all20_scored_source_work_reviewed'))
            assert meaning['unresolved'] == [] and set(meaning['sources']) == set(replay['sources'])
            assert set(meaning['profiles']) == set(replay['profiles']) == set(modules['report']['profiles'])
            profiles, inventories = {}, {}
            for identifier, proposed in replay['profiles'].items():
                original = modules['report']['profiles'][identifier]
                assert proposed['original_scored_profile'] == original
                accepted = meaning['profiles'][identifier]
                assert accepted['source'] == proposed['source'] and accepted['source_sha256'] == proposed['source_sha256']
                assert accepted['canonical_loc'] == proposed['canonical_loc'] and accepted['physical_loc'] == proposed['physical_loc']
                files = []
                for item in proposed['source_bundle']:
                    record = e.read(item['count_receipt']['path'], item['count_receipt']['sha256'], pins)
                    metric = record['original_projection']
                    source = e.bind(item['origin'], item['sha256'], pins).read_bytes()
                    assert source == e.bind(item['path'], item['sha256'], pins).read_bytes()
                    accepted_source = meaning['sources'][item['origin']]
                    assert accepted_source['source_sha256'] == item['sha256']
                    assert accepted_source['canonical_events'] == metric['canonical_events']
                    assert accepted_source['full_owner_expansions'] == record['full_owner_expansions']
                    assert accepted_source['normalized_loc'] == metric['normalized_loc'] == item['normalized_loc']
                    assert accepted_source['physical_loc'] == metric['physical_loc'] == item['physical_loc']
                    assert metric['diagnostics'] == item['unresolved_diagnostics'] == []
                    assert type(item['normalized_loc']) is type(item['physical_loc']) is int
                    assert item['normalized_loc'] > 0 and item['physical_loc'] > 0
                    assert sum(event['units'] for event in metric['canonical_events']) == item['normalized_loc']
                    assert record['compiled_source'] == item['path'] and record['original_source'] == item['origin']
                    assert record['compiled_source_sha256'] == record['original_source_sha256'] == item['sha256']
                    assert record['exact_original_and_compiled_bytes_equal'] is True
                    e.bind(replay['sources'][item['origin']]['scanner_stdout'],
                        replay['sources'][item['origin']]['scanner_stdout_sha256'], pins)
                    files.append(dict(item, ownership_review=dict(status='passed', review_identity=meaning['review_identity'],
                        evidence_path=str(args.meaning), evidence_sha256=args.meaning_sha256)))
                assert accepted['source_bundle'] == [{key: item[key] for key in
                    ('path', 'origin', 'sha256', 'role', 'normalized_loc', 'physical_loc')} for item in proposed['source_bundle']]
                assert sum(item['normalized_loc'] for item in files) == proposed['canonical_loc']
                assert sum(item['physical_loc'] for item in files) == proposed['physical_loc']
                files_by_origin = {item['origin']: item for item in files}
                assert set(files_by_origin) == {item['original_path'] for item in original['source_bundle']}
                for entry in original['source_bundle']:
                    assert files_by_origin[entry['original_path']]['path'] == entry['path']
                    assert files_by_origin[entry['original_path']]['sha256'] == entry['sha256']
                profiles[identifier] = dict(source=proposed['source'], source_origin=proposed['source_origin'],
                    source_sha256=proposed['source_sha256'], benchmark=proposed['benchmark'], variant=proposed['variant'],
                    canonical_loc=proposed['canonical_loc'], physical_loc=proposed['physical_loc'], source_bundle=files,
                    source_alias_of=proposed['source_alias_of'], semantic_review=dict(status='passed',
                        review_identity=meaning['review_identity'], evidence_path=str(args.meaning), evidence_sha256=args.meaning_sha256))
                inventory = deepcopy(replay['compiler_bound_input_inventory'][identifier])
                assert inventory['independently_retained_compiler_input_evidence'] == original
                assert inventory['original_compiler_input_evidence'] == original['compiler_bound_input_inventory']
                inventory.update(status='qualified-exact-authored-compiler-inputs', files=deepcopy(files))
                inventory_path = output / (identifier + '-compiled-inputs.json')
                e.save(inventory_path, inventory)
                e.bind(inventory_path, e.sha(inventory_path), pins)
                inventories[identifier] = dict(inventory, evidence_path=str(inventory_path), evidence_sha256=e.sha(inventory_path))
            assert len(profiles) == len(inventories) == 20 and sum(len(profile['source_bundle']) for profile in profiles.values()) == 44
            factory_sources = []
            runtime_root = e.OLD / 'prolog-comparison/20261013/.build'
            for name, digest in (
                ('pl-prims.c', '28a235fd7c83b22af965e59b559c2c491361c943f6161fcc9b064bffabea9ecd'),
                ('pl-fli.c', '888cf810185db5443e7967aa47367c6e4851f0b638a8b4a13ae7c5eabc812797')):
                qualified = runtime_root / 'swi-runtime-private-v2/official-source/swipl-10.0.2/src' / name
                reviewed = runtime_root / 'swi-runtime-directory-v1/official-source/swipl-10.0.2/src' / name
                assert pins[str(qualified)] == digest
                assert e.bind(qualified, digest, pins).read_bytes() == e.bind(reviewed, digest, pins).read_bytes()
                factory_sources.append(dict(path=str(reviewed), sha256=digest,
                    qualified_original_source=str(qualified), exact_qualified_source_copy=True,
                    role='generic-SWI-native-factory-not-counted-application'))
            table_source = Path(modules['home']) / 'library/hashtable.pl'
            table_digest = pins[str(table_source)]
            e.bind(table_source, table_digest, pins)
            work_profiles = {}
            work_case_results = gates['work']['report']['case_results']
            for identifier, row in modules['report']['profiles'].items():
                entry = dict(status='passed', source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
                    application_artifact_pins=deepcopy(row['application_artifact_pins']),
                    compiler_bound_input_inventory=deepcopy(row['compiler_bound_input_inventory']),
                    source_review=dict(status='passed', evidence_path=str(e.SCORING), evidence_sha256=args.scored_review_sha256,
                        owner_meaning_review=dict(path=str(args.meaning), sha256=args.meaning_sha256)),
                    original_scored_wam=dict(path=row['compiler_bound_input_inventory']['original_scored_wam'],
                        sha256=row['compiler_bound_input_inventory']['original_scored_wam_sha256']))
                cases = [deepcopy(case) for case in work_case_results if case['id'] == identifier]
                if row['benchmark'] == 'binarytrees':
                    assert len(cases) == 4
                    entry['allocation_retention_witness'] = dict(status='passed', actual_cases=cases,
                        closed_review=dict(path=gates['work']['root_path'], sha256=gates['work']['root_sha256']))
                    entry['original_scored_vm_allocation_review'] = dict(status='passed', evidence_path=str(e.SCORING),
                        evidence_sha256=args.scored_review_sha256, actual_original_scored_wam=entry['original_scored_wam'],
                        qualified_native_factory_sources=deepcopy(factory_sources))
                elif row['benchmark'] == 'knucleotide':
                    assert len(cases) == 4
                    entry['seven_map_capacity_windows_witness'] = dict(status='passed', actual_cases=cases,
                        per_window_trace_recorded=False, original_source_loop_review=entry['source_review'],
                        qualified_generic_table_source=dict(path=str(table_source), sha256=table_digest))
                elif row['benchmark'] == 'pidigits':
                    assert len(cases) == 7
                    entry['both_actual_divisions_witness'] = dict(status='passed', actual_cases=cases,
                        original_scored_WAM_review=entry['source_review'])
                else:
                    assert cases == []
                work_profiles[identifier] = entry
            work = dict(status='qualified-required-source-work', language='prolog', profiles=work_profiles,
                original_bounded_preparation=deepcopy(replay['actual_preparation']),
                actual_work30_closed_review=dict(path=gates['work']['root_path'], sha256=gates['work']['root_sha256']),
                scored_source_WAM_review=deepcopy(replay['scored_source_WAM_review']), pins=dict(pins), chart_admission=False)
            modules['contracts'].full_work_receipt(work, list(modules['report']['profiles'].values()), e.verify)
            work_path = output / 'qualified-work20.json'
            e.save(work_path, work)
            e.bind(work_path, e.sha(work_path), pins)
            grammar = {str(e.READER / name): pins[str(e.READER / name)]
                for name in ('foreign_prolog.py', 'test_prolog.py', 'scan_source.pl', 'run_fixtures.py', 'REVIEW.md')}
            overlay = dict(status='qualified-exact-source-LOC', language='prolog', profile_count=20,
                profiles=profiles, compiler_bound_input_inventory=inventories, canonical_LOC_admitted=True,
                complete_authored_source_bundles=True, unresolved=[], chart_admission=False,
                fixture_receipt=dict(status='passed', path=gates['reader']['report_path'], sha256=gates['reader']['report_sha256']),
                grammar_snapshot_pins=grammar, replay_receipts=[dict(path=str(replay_path), sha256=args.replay_sha256)],
                actual_required_work=dict(path=str(work_path), sha256=e.sha(work_path)),
                exact_owner_meaning_review=dict(path=str(args.meaning), sha256=args.meaning_sha256), pins=dict(pins))
            e.save(output / 'qualified-loc-overlay.json', overlay)
            outcome.update(status='qualified-original-Prolog20-work-and-LOC-awaiting-full90',
                canonical_LOC_admitted=True, source_work_qualified=True, profiles=20, original_sources=22,
                compiled_copy_reconciliations=44, qualified_work_path=str(work_path), qualified_work_sha256=e.sha(work_path),
                qualified_loc_path=str(output / 'qualified-loc-overlay.json'), qualified_loc_sha256=e.sha(output / 'qualified-loc-overlay.json'))
        except BaseException as error:
            failure = error
            outcome.update(error=str(error), error_type=type(error).__name__)
            (output / 'error.log').write_text(traceback.format_exc())
        finally:
            signal.alarm(0)
            available, errors = {}, []
            if e is not None:
                for path, digest in pins.items():
                    try:
                        assert e.sha(path) == digest
                    except BaseException as error:
                        errors.append(dict(path=path, error=str(error)))
                for path in output.rglob('*'):
                    if path.is_file():
                        try: available[str(path)] = e.sha(path)
                        except BaseException as error: errors.append(dict(path=str(path), error=str(error)))
            outcome.update(prerequisite_pins=pins, artifact_pins=available, integrity_errors=errors,
                exclusive_common_mutex_held=True, common_mutex_inode=79859134)
            if errors: outcome['status'] = 'failed-terminal-integrity'
            with (output / 'outcome.json').open('x') as stream:
                json.dump(outcome, stream, indent=2)
                stream.write('\n')
            if failure is not None: raise failure
            assert not errors
            print(json.dumps({key: outcome[key] for key in ('status', 'qualified_work_sha256', 'qualified_loc_sha256',
                'profiles', 'original_sources', 'compiled_copy_reconciliations')}), flush=True)


if __name__ == '__main__':
    main()
