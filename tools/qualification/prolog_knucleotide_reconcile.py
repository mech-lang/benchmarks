"""Independently reconcile 36 new Prolog slots and 54 preserved observations.

Only independent receipt validators are imported. All three stopped producers
retain their original failures, physical pins and sample identities. Successful
file replay holds six existing leases through any downstream publication.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import sys

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/prolog/full36-knucleotide-v1'
SOURCE=ROOT/'experiments/prolog/knucleotide-linear-v1'
STOP=SOURCE/'stop-v1'
PREVIOUS=ROOT/'experiments/prolog/full50-remaining-v1'
PREVIOUS_PLAN=PREVIOUS/'plan-v1.json'
PREVIOUS_PLAN_SHA='fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195'
PREVIOUS_JOB=ROOT/'experiments/prolog/full90-v1/owned-jobs/linear-remaining50-v1'
CLOSURE_SHA='0649952532e5a1c8a1bd27d805e087f950ea0c50bb82e6246c1ecd1c230536b6'
QUALIFICATION=SOURCE/'qualification/qualified-source-work-counts-v2.json'
QUALIFICATION_SHA='4fe44e66ff923d914c1f7c6a368457ab014ded14df9153c61216713eaa5eef68'
PLAN=PACKET/'plan-v1.json'
PLAN_SHA='f9953cbdc051cf2d536fab8b5e74f342e6d1a4ebd41783d7ad8e8e27f2d3f75c'
CONTROLLER=ROOT/'tools/qualification/prolog_knucleotide_remaining.py'
CONTROLLER_SHA='abd025be6c894cc01a5e4b416a8312e7e4ffdac63a722db350d7b42a16e05f32'
HELPER=Path(__file__).with_name('prolog_remaining_reconcile.py')
HELPER_SHA='74a6b1cdaeffa370619cd8099b57e7127d98ae38a6cf0ccecaeb1901f416621e'
raw=HELPER.read_bytes()
if hashlib.sha256(raw).hexdigest()!=HELPER_SHA:raise ValueError('Frozen independent reconciler changed')
spec=importlib.util.spec_from_file_location('knucleotide36_independent_receipts',HELPER)
q=importlib.util.module_from_spec(spec);exec(compile(raw,str(HELPER),'exec'),q.__dict__)
l,r,p,require,same=q.l,q.r,q.p,q.require,q.same
OLD,OLD_REFS,PRIOR,PRIOR_PLAN,PRIOR_PLAN_SHA=q.OLD,q.OLD_REFS,q.PRIOR,q.PRIOR_PLAN,q.PRIOR_PLAN_SHA
JOB=OLD/'owned-jobs/knucleotide-remaining36-v1'
SCHEMA='prolog-knucleotide-independent36-plus54-reconciliation-v1'
PRODUCER_SCHEMA='prolog-knucleotide-remaining36-plus54-v1'
AGGREGATE=q.AGGREGATE
merge,attempt_paths,fingerprint_pins,summarize=q.merge,q.attempt_paths,q.fingerprint_pins,q.summarize
sample_origin=q.sample_origin
SOURCE_SHA='b3f524485ccfc29204efecc2f0da47b91b7a63041f4591512ecb2af844ade1e6'
SOURCES={str(SOURCE/'sources/knucleotide'/name):SOURCE_SHA for name in ('compact.pl','optimized.pl')}
SOURCES.update({str(SOURCE/'support/clbg_io.pl'):'bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3',
               str(SOURCE/'support/clbg_records.pl'):'efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19'})


def seed_rows(plan):
    rows={row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],
        retained_attempts=[],measurement_status='pending') for manifest in plan['manifests'].values() for row in manifest['profiles']}
    for sample in plan['retained']['reused_samples']:
        row=rows[sample['slot'][3]];row['samples_seconds'].append(sample['seconds'])
        row['sample_validation'].append(copy.deepcopy(sample['validation']))
        row['retained_attempts'].append(dict(cohort=sample['cohort'],attempt=sample['original_attempt'],
            report=sample['original_report'],report_sha256=sample['original_report_sha256']))
        row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
    completed=[bench for bench in r.BENCHES if summarize(rows,plan['manifests'][bench])]
    same(completed,plan['retained']['completed_benchmarks'],'Retained workload completeness differs')
    return rows

def stopped_durable(durable, request, closure):
    command = [p.PYTHON, '-I', '-S', '-B', str(ROOT/'tools/qualification/prolog_remaining_full.py'),
               'run', '--plan', str(PREVIOUS/'plan-v1.json'), '--plan-sha256', PREVIOUS_PLAN_SHA]
    for name in ('request', 'launch', 'worker-started', 'command-started'):
        same(durable[name]['command'], command, 'Stopped durable command changed')
        require(durable[name]['cwd'] == str(ROOT), 'Stopped durable cwd changed')
    first, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    require(p.integer(first['schema_version'], 1) and first['common_mutex_owned_by_target_command'] is True,
            'Stopped durable request changed')
    for value in (first, launch, ended):
        require(value['automatic_retry'] is value['qualification_granted'] is False, 'Stopped scope changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Stopped worker lost ownership')
    require(ended['status'] == 'command-failed' and p.integer(ended['exit_code'], -2)
            and ended['stop_signals'] == [15] and ended['actual_command_started'] is True
            and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False,
            'Deliberate interruption was normalized')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Durable cleanup failed')
    same(p.process_identity(started['command_identity']), p.process_identity(ended['command_identity']),
         'Controller identity changed')
    for value in (launch, ended):
        same(p.process_identity(value['worker_identity']), p.process_identity(worker['worker_identity']),
             'Worker identity changed')
    require(started['command_pid'] == ended['command_pid'] == 2953 and worker['worker_identity']['pid'] == 2948
            and p.process_identity(started['command_identity'])[2] == ' '.join(command)
            and started['command_identity']['listing'].split(None, 2)[1] == '2948', 'Stopped owner differs')
    same(request['worker'], ended['worker_identity']['listing'], 'Stop worker differs')
    same(request['controller'], ended['command_identity']['listing'], 'Stop controller differs')
    require(p.timestamp(first['created_at']) <= p.timestamp(worker['started_at']) <= p.timestamp(started['started_at'])
            <= p.timestamp(request['created_at']) <= p.timestamp(ended['finished_at'])
            <= p.timestamp(closure['verified_at']), 'Stop chronology changed')


def cancelled_attempt(attempt, raw, wrapper, outer, request, closure):
    """Cancellation is preserved as an ownership event, never a timing sample."""
    same(attempt, wrapper, 'Report interrupted attempt differs from wrapper')
    fields = {'wrapper_native_registration', 'attempt', 'round', 'qualified', 'wrapper_supervisor_failure',
              'wrapper_error', 'wrapper_error_type', 'chart_admission'}
    same({k: v for k, v in wrapper.items() if k not in fields}, raw, 'Wrapper changed interrupted raw result')
    require(attempt['attempt'] == 15 and attempt['round'] == 1 and attempt['id'] == 'prolog-knucleotide-compact'
            and attempt['key'] == 'knucleotide:prolog-knucleotide-compact' and attempt['benchmark'] == 'knucleotide'
            and attempt['qualified'] is attempt['chart_admission'] is False
            and attempt['wrapper_supervisor_failure'] is True, 'Interrupted attempt was admitted')
    for prefix in ('', 'wrapper_'):
        require(attempt[prefix+'error_type'] == 'KeyboardInterrupt'
                and attempt[prefix+'error'] == 'Benchmark harness received signal 15', 'Stop is not a deadline')
    require(attempt['pins_unchanged_at_end'] is True and attempt['valid_environment'] is True
            and p.integer(attempt['exit_status'], -9) and not attempt.get('resource_violation'),
            'Interrupted environment or cleanup changed')
    for field in ('monitor_errors', 'resource_monitor_errors', 'competing_compilers', 'power_changes'):
        same(attempt[field], [], 'Interrupted monitor failure')
    require(not any(attempt.get(k) for k in ('cleanup_error', 'remaining_group_members', 'monitor_finish_error')),
            'Interrupted native group was not cleaned')
    active = request['active_before_signal']
    same(attempt['wrapper_native_registration'], active['native'], 'Cancelled native registration differs')
    native = {k: v for k, v in active['native'].items() if k != 'identity'}
    same(outer['native_registrations'], [native], 'Outer native registration differs')
    require(outer['status'] == 'failed' and outer['error_type'] == 'KeyboardInterrupt'
            and outer['error'] == attempt['error'] and outer['deadline_expired'] is False
            and outer['common_mutex_held_through_cleanup'] is True
            and outer['native_execute_unchanged'] is outer['native_validation_unchanged'] is True
            and p.integer(outer['deadline_seconds'], 22200) and p.integer(outer['native_timeout_seconds'], 21600)
            and p.integer(outer['common_mutex_fd']) and outer['common_mutex_fd'] >= 0,
            'Outer cancellation policy changed')
    same(outer['cleanup_errors'], [], 'Outer cleanup failure')
    same(outer['owned_sampler_children'], {'15240': dict(identity=active['sampler_identity'], reaped=True)},
         'Owned sampler was not reaped')
    same(outer['owned_groups'], {'15240': active['sampler_identity'], '15261': active['native']['identity']},
         'Recorded owned groups changed')
    same(outer['signals'], [dict(kind='direct-child', pid=15240, signal=15)], 'Unexpected cancellation signals')
    for pid, parent in ((15240, 2953), (15261, 15240)):
        identity = outer['owned_groups'][str(pid)]
        r.kernel_identity(identity, pid)
        require(identity['ppid'] == parent, 'Unowned cancellation child')
        recorded = request['identities'][str(pid)]
        same({k: identity[k] for k in ('pid', 'ppid', 'birth_seconds', 'birth_microseconds')},
             {k: recorded[k] for k in ('pid', 'ppid', 'birth_seconds', 'birth_microseconds')},
             'Process birth differs from the stop observation')
    same(closure['owned_processes_absent'], [2948, 2953, 15240, 15261], 'Closed process inventory differs')
    same(closure['owned_groups_empty'], [2948, 15240, 15261], 'Closed group inventory differs')


def stopped_prefix(plan, before, report, terminal, durable, request, closure, artifacts):
    """Pure boundary/receipt replay; the original forty remain separately sealed."""
    same(plan['remaining_slots'],plan['schedule'][40:],'Stopped schedule partition differs')
    stopped_durable(durable, request, closure)
    require(closure['schema'] == 'prolog-knucleotide-quadratic-stop-closure-v1'
            and closure['status'] == 'closed-deliberately-stopped-unqualified'
            and closure['deadline_expired'] is closure['interrupted_attempt_qualified'] is False
            and closure['automatic_retry'] is closure['chart_admission'] is False
            and closure['remaining_cohort_reconciliation_performed'] is False
            and closure['integrity_errors'] == [], 'Wrong deliberately closed boundary')
    for field, value in (('qualified_samples_preserved', 54), ('original_retained_samples', 40),
                         ('new_completed_samples_preserved', 14), ('interrupted_attempt', 15),
                         ('repeated_completed_samples', 0), ('signal_target', 2948)):
        require(p.integer(closure[field], value), 'Changed stop count: '+field)
    require(request['signal'] == 15 and request['signal_target'] == 2948
            and request['native_signal_sent_directly'] is request['timeout_claim'] is False
            and request['automatic_retry'] is request['qualification_granted'] is False
            and request['qualified_samples_before_signal'] == 54 and request['retained_qualified_samples'] == 40
            and request['new_qualified_samples'] == 14 and request['preserved_completed_attempts'] == list(range(1, 15)),
            'Wrong stop request')
    same(before['active'], request['active_before_signal'], 'Saved active checkpoint differs')
    require(before['status'] == 'running' and before['qualified_samples'] == 54, 'Wrong pre-stop checkpoint')
    same(before['attempts'], report['attempts'][:14], 'Completed attempts changed after stop')
    require(report['schema'] == q.PRODUCER_SCHEMA and terminal['schema'] == 'prolog-linear-remaining50-terminal-v1'
            and report['status'] == terminal['status'] == 'stopped-unqualified' and report['active'] is None
            and report['error_type'] == 'KeyboardInterrupt' and report['error'] == 'Benchmark harness received signal 15'
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors'] == []
            and not report.get('terminal_integrity_errors'), 'Stopped producer closure failed')
    require(report['plan'] == str(PREVIOUS/'plan-v1.json') and report['plan_sha256'] == PREVIOUS_PLAN_SHA
            and terminal['report'] == str(PREVIOUS/'run-v1/report.json')
            and terminal['report_sha256'] == closure['controller_report_sha256'], 'Stopped report binding differs')
    same(terminal['prerequisite_pins'], merge(plan['pins'], {str(PREVIOUS/'plan-v1.json'): PREVIOUS_PLAN_SHA}),
         'Stopped prerequisite closure differs')
    require(closure['prerequisite_pins_verified'] == len(terminal['prerequisite_pins'])
            and closure['terminal_artifacts_verified'] == len(terminal['available_evidence_pins']),
            'Closed inventory count differs')
    require(terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134
            and terminal['original_files_mutated'] is False and terminal['new_qualified_samples'] == 14,
            'Stopped mutex/new-sample policy differs')
    for value in (report, terminal):
        for field, expected in (('qualified_samples', 54), ('retained_qualified_samples', 40),
                                ('saved_attempts', 15), ('full_performance_runs', 15)):
            require(p.integer(value[field], expected), 'Stopped native ledger differs')
        require(value['common_mutex_held_continuously'] is True
                and value['full_timings_qualified'] is value['chart_admission'] is False,
                'Stopped measurement scope differs')
        same(value['registered_native_attempts'], list(range(1, 16)), 'Missing registered native attempt')
        same(value['native_launch_unconfirmed_attempts'], [], 'Unconfirmed native launch')
        same(value['skipped_failed_profile_slots'], [], 'Unexplained skipped slot')
    require(report['isolated_failed_profiles'] == [] and report['no_automatic_retry'] is True
            and report['repeated_completed_samples'] == 0, 'Cancellation was an isolated benchmark failure')
    same(report['completed_benchmarks'], list(r.BENCHES)[:6], 'Stopped workload boundary differs')
    same(report['reused_samples'], plan['retained']['reused_samples'], 'Original forty observations changed')
    require(len(report['attempts']) == len(report['independent_supervisors']) == 15, 'Stopped receipt count differs')
    rows = seed_rows(plan)
    reused = copy.deepcopy(plan['retained']['reused_samples'])
    provenance, gaps, snapshots, last = [], [], {}, None
    pins = fingerprint_pins(plan, terminal['prerequisite_pins'])
    for index, (slot, attempt) in enumerate(zip(plan['remaining_slots'][:14], report['attempts'][:14]), 1):
        require(attempt['attempt'] == index and attempt['qualified'] is True, 'Stopped prefix contains a failed sample')
        paths = attempt_paths(PREVIOUS/'run-v1', attempt)
        require(attempt['result_path'] == str(paths[0]) and attempt['supervisor_result_path'] == str(paths[1]),
                'Stopped receipt path changed')
        row = rows[slot[3]]; manifest = plan['manifests'][slot[0]]
        begin, end = r.check_attempt(attempt, artifacts[str(paths[0])], artifacts[str(paths[1])],
                                    slot, row, manifest, pins, provenance)
        require(last is None or last <= begin, 'Stopped samples overlap'); last = end
        gaps.extend(r.check_outer(artifacts[str(paths[2])], attempt, 2953))
        for path in paths:
            snapshots[str(path)] = terminal['available_evidence_pins'][str(path)]
        same(report['independent_supervisors'][index-1],
             dict(path=str(paths[2]), sha256=snapshots[str(paths[2])], status='returned'), 'Outer receipt reference differs')
        row['attempts'].append(index); row['samples_seconds'].append(attempt['seconds'])
        row['sample_validation'].append(attempt['validation'])
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        reused.append(dict(slot=slot, original_attempt=index, cohort='linear-remaining50',
            original_report=str(PREVIOUS/'run-v1/report.json'), original_report_sha256=closure['controller_report_sha256'],
            raw=str(paths[0]), raw_sha256=snapshots[str(paths[0])], supervised=str(paths[1]),
            supervised_sha256=snapshots[str(paths[1])], outer=str(paths[2]), outer_sha256=snapshots[str(paths[2])],
            seconds=attempt['seconds'], validation=attempt['validation']))
    for manifest in plan['manifests'].values(): summarize(rows, manifest)
    cancelled = report['attempts'][14]; key = cancelled['key']
    rows[key]['attempts'].append(15); rows[key]['measurement_status'] = 'stopped-unqualified'
    q.same_summary(report['programs'], rows)
    same(snapshots, closure['completed_artifacts_unchanged'], 'Completed checkpoint hashes differ')
    same(snapshots, report['validated_attempt_artifacts'], 'Stopped validated snapshots differ')
    same(provenance, report['descriptive_provenance'], 'Stopped descriptive evidence differs')
    same(gaps, report['kernel_identity_observation_gaps'], 'Stopped identity observations differ')
    raw, _, outer = attempt_paths(PREVIOUS/'run-v1', cancelled)
    wrapper = raw.with_suffix('.wrapper.json')
    cancelled_attempt(cancelled, artifacts[str(raw)], artifacts[str(wrapper)], artifacts[str(outer)], request, closure)
    same(report['independent_supervisors'][-1], dict(path=str(outer),
         sha256=terminal['available_evidence_pins'][str(outer)], status='failed'), 'Interrupted outer binding differs')
    expected = set(snapshots) | {str(raw), str(wrapper), str(outer)}
    require(set(artifacts) == expected, 'Extra/missing stopped process receipt')
    require(set(terminal['available_evidence_pins']) == expected | {str(PREVIOUS/'run-v1/report.json'),
         str(PREVIOUS/'run-v1/error.log')}, 'Unregistered stopped artifact')
    require(p.timestamp(report['started_at']) <= p.timestamp(report['attempts'][0]['started_at'])
            <= last <= p.timestamp(cancelled['started_at']) <= p.timestamp(request['created_at'])
            <= p.timestamp(cancelled['finished_at']) <= p.timestamp(report['finished_at'])
            <= p.timestamp(durable['terminal']['finished_at']), 'Stopped process chronology differs')
    return dict(reused_samples=reused, completed_benchmarks=list(r.BENCHES)[:6], reused_native_processes=54,
        excluded_attempts=[dict(report=str(PREVIOUS/'run-v1/report.json'), attempt=15,
                               disposition='deliberately-stopped-unqualified')],
        stopped_report=dict(path=str(PREVIOUS/'run-v1/report.json'), sha256=closure['controller_report_sha256']),
        stop_review=dict(path=str(STOP/'closure.json'), sha256=CLOSURE_SHA),
        descriptive_provenance=provenance, kernel_identity_observation_gaps=gaps)


REPLACED = frozenset(('source', 'source_sha256', 'measured_source', 'source_bundle', 'command', 'cwd',
    'compiled_artifact', 'compiler_bound_input_inventory', 'required_work_review', 'source_count_review',
    'canonical_source_projection', 'loc', 'canonical_loc', 'physical_loc', 'formatted_loc',
    'source_alias_of', 'optimization_claim'))


def packet_path(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(SOURCE),
            'Replacement evidence outside its packet')
    return path


def qualification_checks(value, old_profiles):
    require(value['schema'] == 'prolog-knucleotide-linear-qualified-v1'
            and value['status'] == 'qualified-source-work-and-canonical-counts-awaiting-full-timing',
            'Actual independently qualified replacement is required')
    for flag in ('bounded_outputs_qualified', 'compiled_inputs_qualified', 'source_work_qualified', 'canonical_LOC_admitted'):
        require(value[flag] is True, 'Pending replacement qualification: '+flag)
    require(value['full_timings_qualified'] is value['chart_admission'] is False, 'Replacement claims unmeasured timings')
    pins = value['pins']
    require(type(pins) is dict and all(Path(k).is_absolute() and p.digest(v) for k, v in pins.items()),
            'Replacement pins are malformed')
    require(all(pins.get(path) == digest for path, digest in SOURCES.items()), 'Missing exact authored source pins')
    require(set(value['evidence']) == {'compilation', 'bounded', 'source_counts', 'required_work'},
            'Missing independent replacement evidence')
    for ref in value['evidence'].values():
        packet_path(ref['path']); require(pins.get(ref['path']) == ref['sha256'], 'Unpinned qualification evidence')
    require(type(value['artifact_inventories']) is dict and bool(value['artifact_inventories']),
            'Closed native artifact inventories required')
    for directory, inventory in value['artifact_inventories'].items():
        packet_path(directory)
        require(type(inventory) is dict and bool(inventory), 'Empty artifact closure')
        for relative, digest in inventory.items():
            path = Path(relative)
            require(not path.is_absolute() and '..' not in path.parts and path.parts and p.digest(digest)
                    and pins.get(str(Path(directory)/path)) == digest, 'Unpinned/escaped native artifact')
    profiles = value['profiles']
    require(type(profiles) is list and len(profiles) == 2, 'Exactly two existing source aliases required')
    for index, (row, old) in enumerate(zip(profiles, old_profiles)):
        same({k: v for k, v in row.items() if k not in REPLACED},
             {k: v for k, v in old.items() if k not in REPLACED}, 'Replacement changed unrelated profile policy')
        require(row['source_sha256'] == SOURCE_SHA and row['source'] in SOURCES
                and SOURCES[row['source']] == SOURCE_SHA and row.get('formatted_loc') is None,
                'Replacement main identity/formatted count differs')
        require(pins.get(row['binary']) == row['binary_sha256'], 'Replacement runtime unpinned')
        bundle = row['source_bundle']
        require(len(bundle) == 3 and len({v['path'] for v in bundle}) == 3
                and {v['origin'] for v in bundle} == {row['source'], str(SOURCE/'support/clbg_io.pl'),
                                                       str(SOURCE/'support/clbg_records.pl')}, 'Incomplete three-file bundle')
        for entry in bundle:
            packet_path(entry['path'])
            require(pins.get(entry['path']) == SOURCES[entry['origin']] == entry['sha256']
                    and p.integer(entry['normalized_loc']) and entry['normalized_loc'] > 0
                    and p.integer(entry['physical_loc']) and entry['physical_loc'] > 0, 'Unqualified source/count binding')
        primary = next(e for e in bundle if e['origin'] == row['source'])
        require(row['measured_source'] == primary['path'] and row['loc'] == row['canonical_loc']
                == sum(e['normalized_loc'] for e in bundle)
                and row['physical_loc'] == sum(e['physical_loc'] for e in bundle), 'Bundle count/primary mismatch')
        by_name = {Path(e['origin']).name: Path(e['path']).with_suffix('.qlf') for e in bundle}
        qlf = Path(primary['path']).with_suffix('.qlf')
        require(row['compiled_artifact']['path'] == str(qlf)
                and row['compiled_artifact']['sha256'] == pins.get(str(qlf))
                and p.integer(row['compiled_artifact']['bytes']) and row['compiled_artifact']['bytes'] > 0,
                'Unbound compiled main')
        require(all(p.digest(pins.get(str(path))) for path in by_name.values()), 'Unpinned helper QLF')
        same(row['command'], [old['binary'], '-q', '-O', '-f', 'none', '--stack-limit=8g', '-l',
             str(by_name['clbg_io.pl']), '-l', str(by_name['clbg_records.pl']), '-s', str(qlf),
             '-g', 'clbg_io:run(clbg_knucleotide:main)'], 'Changed direct runtime invocation')
        packet_path(row['cwd'])
        require(row['cwd'] == str(Path(primary['path']).parents[2])
                and by_name['clbg_io.pl'] == Path(row['cwd'])/'support/clbg_io.qlf'
                and by_name['clbg_records.pl'] == Path(row['cwd'])/'support/clbg_records.qlf',
                'Compiled input root/helper layout differs')
        for name in ('compiler_bound_input_inventory', 'required_work_review', 'source_count_review', 'canonical_source_projection'):
            ref = row[name]; packet_path(ref['path'])
            require(pins.get(ref['path']) == ref['sha256'], 'Unpinned profile proof: '+name)
        for profile_field, evidence_field in (('required_work_review', 'required_work'), ('source_count_review', 'source_counts')):
            same({k: row[profile_field][k] for k in ('path', 'sha256')}, value['evidence'][evidence_field],
                 'Independent profile qualification differs')
        require(row['required_work_review']['status'] == 'passed'
                and row['compiler_bound_input_inventory']['status'] == 'qualified-exact-authored-compiler-inputs',
                'Compiled input/work disposition missing')
        require(row['source_alias_of'] == (old_profiles[0]['id'] if index else None), 'Alias identity differs')
    require(profiles[1]['optimization_claim'] == 'explicit equivalent-source alias; no distinct optimization admitted',
            'Identical sources presented as distinct optimization')
    for field in ('binary', 'binary_sha256', 'runtime_environment', 'canonical_loc', 'physical_loc'):
        same(profiles[0][field], profiles[1][field], 'Alias execution differs: '+field)


def durable_checks(durable, plan):
    request,launch,worker,started,ended = [durable[k] for k in ('request','launch','worker-started','command-started','terminal')]
    command = [p.PYTHON,'-I','-S','-B',str(CONTROLLER),'run','--plan',str(PLAN),'--plan-sha256',PLAN_SHA]
    for item in (request,launch,worker,started):
        same(item['command'],command,'Durable command must have exact reviewed argv, without -u')
        require(item['cwd']==str(ROOT),'Durable working directory differs')
    require(p.integer(request['schema_version'],1) and request['common_mutex_owned_by_target_command'] is True,
            'Durable ownership request differs')
    for item in (request,launch,ended):
        require(item['automatic_retry'] is item['qualification_granted'] is False,'Durable scope changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Durable worker ownership incomplete')
    require(ended['status']=='command-exited-zero-awaiting-report-review' and p.integer(ended['exit_code'],0)
            and ended['actual_command_started'] is True and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False and ended['stop_signals']==[],
            'Durable controller is not closed successfully')
    require(not any(ended.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure')),
            'Durable owner has failure evidence')
    same(p.process_identity(ended['command_identity']),p.process_identity(started['command_identity']),
         'Controller identity changed')
    same(p.process_identity(ended['worker_identity']),p.process_identity(worker['worker_identity']),'Worker identity changed')
    same(p.process_identity(launch['worker_identity']),p.process_identity(worker['worker_identity']),'Launch worker changed')
    pid = started['command_pid']
    require(p.integer(pid) and pid>0 and p.integer(ended['command_pid'],pid)
            and started['command_identity']['pid']==pid
            and p.process_identity(started['command_identity'])[2]==' '.join(command), 'Unbound observed controller')
    require(p.timestamp(request['created_at']) <= p.timestamp(worker['started_at']) <= p.timestamp(started['started_at'])
            <= p.timestamp(ended['finished_at']),'Durable timestamps inverted')
    return pid


def schedule(plan, previous, prior, original):
    slots,old_profiles,original_profiles=q.schedule(previous,prior,original)
    require(plan['schema']==PRODUCER_SCHEMA and plan['status']=='prepared-awaiting-independent-review'
        and plan['controller']==str(CONTROLLER) and plan['controller_sha256']==CONTROLLER_SHA
        and plan['repository']==str(ROOT) and plan['output']==str(PACKET/'run-v1'),'Wrong remaining36 identity')
    for field,count in (('samples',3),('full_processes',36),('combined_sample_slots',90),
        ('retained_qualified_samples',54),('new_prolog_processes',24),('new_mech_processes',12),
        ('source_work_profiles',20),('canonical_loc_profiles',20),('compiler_invocations',0),
        ('fixture_reexecutions',0),('bounded_reexecutions',0),('count_replays',0),('repeated_completed_samples',0)):
        require(p.integer(plan[field],count),'Remaining36 plan count differs: '+field)
    require(plan['common_mutex_held_continuously'] is plan['no_automatic_retry'] is True
        and plan['original_files_mutated'] is plan['full_timings_qualified'] is plan['chart_admission'] is False
        and plan['shared_timing_lock']==str(r.LOCK),'Remaining36 execution policy differs')
    for field in ('historical_pins','linear_qualification','timing_policy'):
        same(plan[field],previous[field],'Preserved execution policy changed: '+field)
    same(plan['qualification'],dict(path=str(QUALIFICATION),sha256=QUALIFICATION_SHA),'Wrong replacement disposition')
    replacement=plan['knucleotide_qualification'];qualification_checks(replacement,previous['manifests']['knucleotide']['profiles'][:2])
    manifests=copy.deepcopy(previous['manifests']);manifests['knucleotide']['profiles'][:2]=copy.deepcopy(replacement['profiles'])
    same(plan['manifests'],manifests,'Unqualified manifest changes')
    same(plan['schedule'],slots,'Original90 rotation changed')
    same(plan['retained_slots'],slots[:54],'Retained54 partition differs')
    same(plan['remaining_slots'],slots[54:],'Remaining36 partition differs')
    same([s['slot'] for s in plan['retained']['reused_samples']],slots[:54],'Retained sample order differs')
    required=merge(previous['pins'],replacement['pins'],{str(PREVIOUS_PLAN):PREVIOUS_PLAN_SHA,
        str(CONTROLLER):CONTROLLER_SHA,str(QUALIFICATION):QUALIFICATION_SHA,str(STOP/'closure.json'):CLOSURE_SHA})
    require(all(plan['pins'].get(path)==digest for path,digest in required.items()),'Inherited/replacement pin missing')
    profiles={row['key']:row for manifest in manifests.values() for row in manifest['profiles']}
    require(len(profiles)==30,'Profile inventory differs')
    return slots,profiles,original_profiles


def retained_context(plan,stopped,prior,original,old_raw,old_supervised,old_outer,prior_artifacts,stopped_artifacts):
    slots,profiles,_=schedule(plan,stopped['plan'],prior['plan'],original['plan'])
    _,_,grouped,provenance,gaps,last=q.retained_context(stopped['plan'],prior,original,
        old_raw,old_supervised,old_outer,prior_artifacts)
    preserved=stopped_prefix(stopped['plan'],stopped['before'],stopped['report'],stopped['terminal'],
        stopped['durable'],stopped['request'],stopped['closure'],stopped_artifacts)
    same(plan['retained'],preserved,'Remaining36 changed retained54 observations')
    require(last<=p.timestamp(stopped['report']['started_at']),'Stopped14 overlap prior31')
    for attempt in stopped['report']['attempts'][:14]:grouped.setdefault(attempt['key'],[]).append(attempt)
    provenance+=preserved['descriptive_provenance'];gaps+=preserved['kernel_identity_observation_gaps']
    require(not any(a['benchmark']=='knucleotide' for values in grouped.values() for a in values),
        'Old knucleotide observation cannot enter corrected profile')
    return slots,profiles,grouped,provenance,gaps,p.timestamp(stopped['report']['finished_at'])


def reconcile(plan,stopped,prior,original,report,terminal,durable,raw,supervised,outer,
              old_raw,old_supervised,old_outer,prior_artifacts,stopped_artifacts):
    """Pure four-cohort accounting; file/inventory verification is a separate gate."""
    slots,profiles,grouped,provenance,gaps,last_prior=retained_context(plan,stopped,prior,original,
        old_raw,old_supervised,old_outer,prior_artifacts,stopped_artifacts)
    parent=durable_checks(durable,plan)
    worker=p.process_identity(durable['worker-started']['worker_identity'])[0]
    require(all(durable[k]['command_identity']['listing'].split(None,7)[1]==str(worker)
                for k in ('command-started','terminal')),'New controller parent differs from durable worker')
    require(report['schema']==PRODUCER_SCHEMA and terminal['schema']=='prolog-knucleotide-remaining36-terminal-v1'
            and report['status'] in ('complete','complete-with-unqualified-profiles')
            and report['status']==terminal['status'] and report['active'] is None,
            'Remaining36 producer has not completed')
    require(report['plan']==str(PLAN) and report['plan_sha256']==PLAN_SHA
            and terminal['report']==plan['output']+'/report.json','New plan/report binding differs')
    require(not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors'))
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors']==[],
            'Remaining36 integrity failure')
    require(terminal['common_mutex_held'] is True and p.integer(terminal['common_mutex_inode'],79859134),
            'Terminal common mutex differs')
    for value in (report,terminal):
        require(value['common_mutex_held_continuously'] is True and value['full_timings_qualified'] is False
                and value['chart_admission'] is False and value['native_launch_unconfirmed_attempts']==[],
                'New producer scope or ownership differs')
    require(report['shared_timing_lock']==str(r.LOCK) and report['no_automatic_retry'] is True
            and all(p.integer(report[k],v) for k,v in (('sample_count',3),('source_work_profiles',20),
                ('canonical_loc_profiles',20),('retained_qualified_samples',54),('repeated_completed_samples',0))),
            'Remaining36 report policy differs')
    for field in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','count_replays','repeated_completed_samples'):
        require(p.integer(terminal[field],0),'Unexpected repeated or preparatory execution')
    require(terminal['original_files_mutated'] is False and p.integer(terminal['retained_qualified_samples'],54),
            'Changed original evidence or retained count')
    expected_pins=merge(plan['pins'],{str(PLAN):PLAN_SHA})
    same(terminal['prerequisite_pins'],expected_pins,'New terminal prerequisite closure differs')
    same(report['reused_samples'],plan['retained']['reused_samples'],'New report changed preserved observations')
    same(report['benchmark_order'],list(r.BENCHES),'Benchmark order changed')
    same(report['completed_benchmarks'],list(r.BENCHES),'Incomplete combined workload accounting')
    require(report['supervisor']['pid']==parent,'Report names another controller')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+report['supervisor']['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']),'New controller birth/command differs')
    require(set(report['programs'])==set(profiles),'Profile inventory differs')
    all_pins=fingerprint_pins(plan,expected_pins)
    attempts=report['attempts'];failed={};skipped=[];index=0;previous_end=None;used=set();new_provenance=[];new_gaps=[]
    require(len(report['independent_supervisors'])==len(attempts),'New outer receipt count differs')
    for slot in slots[54:]:
        bench,round_,identifier,key=slot
        if key in failed:
            skipped.append(dict(benchmark=bench,round=round_,id=identifier,key=key));continue
        require(index<len(attempts),'Missing remaining36 attempt');attempt=attempts[index];index+=1
        require(p.integer(attempt['attempt'],index),'Repeated or missing new attempt index')
        paths=attempt_paths(Path(plan['output']),attempt);out=str(paths[2])
        require(attempt['result_path']==str(paths[0]) and attempt['supervisor_result_path']==str(paths[1]),
                'New sample artifact path differs')
        ref=report['independent_supervisors'][index-1]
        require(ref['path']==out and ref['status']=='returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'][out]==ref['sha256'],'New outer receipt binding differs')
        begin,end=r.check_attempt(attempt,raw[str(paths[0])],supervised[str(paths[1])],slot,
            profiles[key],plan['manifests'][bench],all_pins,new_provenance)
        require(previous_end is None or previous_end<=begin,'Remaining36 native intervals overlap');previous_end=end
        new_gaps.extend(r.check_outer(outer[out],attempt,parent));used.update(map(str,paths))
        grouped.setdefault(key,[]).append(attempt)
        if not attempt['qualified']:failed[key]=attempt
    require(index==len(attempts) and index+len(skipped)==36,'Unaccounted new attempts or schedule slots')
    require(set(raw)|set(supervised)|set(outer)==used and len(raw)==len(supervised)==len(outer)==index,
            'Unexpected, duplicate or missing new receipt')
    require(set(terminal['available_evidence_pins'])==used|{plan['output']+'/report.json'},
            'Unregistered terminal artifact')
    same(report['validated_attempt_artifacts'],{path:terminal['available_evidence_pins'][path] for path in used},
         'Terminal digests differ from validated receipt snapshots')
    same(report['descriptive_provenance'],new_provenance,'New provenance observations differ')
    same(report['kernel_identity_observation_gaps'],new_gaps,'New kernel observations differ')
    same(report['isolated_failed_profiles'],list(failed),'Failed-profile inventory differs')
    same(report['skipped_failed_profile_slots'],skipped,'Unexplained skipped new slots')
    same(terminal['skipped_failed_profile_slots'],skipped,'Terminal skipped slots differ')
    require(report['status']==('complete-with-unqualified-profiles' if failed else 'complete'),'Final status hides failure')
    good_new=sum(a['qualified'] for a in attempts)
    for value in (report,terminal):
        for field,count in (('saved_attempts',index),('full_performance_runs',index),('qualified_samples',54+good_new)):
            require(p.integer(value[field],count),'Wrong new/retained process count: '+field)
        same(value['registered_native_attempts'],list(range(1,index+1)),'New native registration ledger differs')
    require(p.integer(terminal['new_qualified_samples'],good_new),'Wrong new qualified sample count')
    origins={}
    for cohort,output,observations in (
        ('original-full90',str(OLD/'results'),original['report']['attempts'][:9]),
        ('linear-full81',str(PRIOR/'run-v1'),prior['report']['attempts']),
        ('linear-remaining50',str(PREVIOUS/'run-v1'),stopped['report']['attempts'][:14]),
        ('knucleotide-remaining36',plan['output'],attempts)):
        for attempt in observations:
            origins[attempt['result_path']]=sample_origin(attempt,cohort,output)
    summaries={}
    for key,original_row in profiles.items():
        row=report['programs'][key];observations=grouped.get(key,[])
        same({k:v for k,v in row.items() if k not in AGGREGATE},original_row,'Measured profile/source metadata changed')
        new=[a for a in attempts if a['key']==key]
        retained=[s for s in plan['retained']['reused_samples'] if s['slot'][3]==key]
        same(row['attempts'],[a['attempt'] for a in new],'New profile membership differs')
        expected_retained=[dict(cohort=s['cohort'],attempt=s['original_attempt'],report=s['original_report'],
            report_sha256=s['original_report_sha256']) for s in retained]
        same(row['retained_attempts'],expected_retained,'Retained profile provenance differs')
        good=[a for a in observations if a['qualified']];values=[a['seconds'] for a in good]
        same(row['samples_seconds'],values,'Profile samples differ across the four actual cohorts')
        same(row['sample_validation'],[a['validation'] for a in good],'Profile validation membership differs')
        if key in failed:
            require(row['measurement_status']=='failed-full-workload' and len(values)<3
                    and row.get('median_seconds') is None and row.get('sample_stdev_seconds') is None
                    and row['time_x_mech'] is None,'Partial failed profile promoted to a summary')
            same(row['full_failure'],failed[key],'Failure differs from actual new attempt');median=sd=None
        else:
            require(row['measurement_status']=='measured' and not row.get('full_failure'),'Incomplete measured profile')
            median,sd=p.three_statistics(values)
            require(p.finite(row['median_seconds'],True) and row['median_seconds']==median
                    and p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds']>=0
                    and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Profile statistics differ')
        summaries[key]=dict(key=key,id=row['id'],language=row['language'],benchmark=row['benchmark'],source=row['source'],
            source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],attempts=[a['attempt'] for a in new],
            retained_attempts=expected_retained,samples_seconds=values,median_seconds=median,sample_stdev_seconds=sd,
            full_workload_qualified=key not in failed,failed_attempt=failed.get(key,{}).get('attempt'),
            failed_cohort='knucleotide-remaining36' if key in failed else None,
            sample_evidence=[origins[a['result_path']] for a in observations])
    for key,row in report['programs'].items():
        control_key=row['benchmark']+':prolog-full-study:mech-control';control=summaries[control_key]
        require(row['matched_mech_control']==control_key and row['matched_mech_source_sha256']==profiles[control_key]['source_sha256'],
                'Matched control identity differs')
        ratio=summaries[key]['median_seconds']/control['median_seconds'] if key not in failed and control_key not in failed else None
        same(row['time_x_mech'],ratio,'Matched-control ratio differs');summaries[key]['time_x_mech']=ratio
    require(last_prior<=p.timestamp(report['started_at'])<=p.timestamp(attempts[0]['started_at'])
            and previous_end<=p.timestamp(report['finished_at']),'Remaining36 overlaps preserved cohort or excludes a sample')
    require(p.timestamp(durable['command-started']['started_at'])<=p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at'])<=p.timestamp(durable['terminal']['finished_at']),
            'Remaining36 exceeds durable lifetime')
    return dict(schema=SCHEMA,status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        new_full_native_processes=index,reused_qualified_samples=54,original_regex_samples=9,retained_linear_samples=31,retained_remaining_samples=14,
        actual_full_native_processes=index+54,total_native_processes_including_cancelled=index+56,
        excluded_original_attempt=10,excluded_remaining50_attempt=15,qualified_samples=54+good_new,new_qualified_samples=good_new,
        skipped_slots=skipped,failed_profiles=list(failed),profiles=summaries,repeated_completed_samples=0,
        original_files_mutated=False,prior_producer_statuses={'original-full90':'stopped-unqualified','linear-full81':'stopped-unqualified','linear-remaining50':'stopped-unqualified'},
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance+new_provenance})],
        kernel_identity_observation_gaps=gaps+new_gaps,file_integrity_verified=False,chart_admission=False,
        runtime_publication_metadata_qualified=False,full_timings_qualified=False,complete_stdout_retained=False,
        full_output_evidence='sampler byte counts/hashes and frozen complete-output validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        cohort_policy='Nine original regex,31 linear-continuation,14 stopped-prefix observations and36 remaining slots retain their original reports and attempt indices.',
        source_evidence=dict(original_plan=dict(path=str(l.OLD_REFS['plan'][0]),sha256=l.OLD_REFS['plan'][1]),
            original_source_outcome=original['plan']['sealed_source_outcome'],linear_qualification=plan['linear_qualification'],knucleotide_qualification=plan['qualification']),
        admission_requirements=['recorded runtime metadata for all20 forms including linear QLF',
            'publication preserving all four actual cohort identities and excluding failed forms','catalog and website validation'])


def cohort_refs(stopped,report,terminal,terminal_sha):
    refs=q.cohort_refs(stopped['report'],stopped['terminal'],stopped['closure']['controller_terminal_sha256'])
    refs['linear-remaining50'].update(status='stopped-unqualified',preserved_qualified_samples=14,
        excluded_attempts=[15],interrupted_native_attempts=1,
        stop_review=dict(path=str(STOP/'closure.json'),sha256=CLOSURE_SHA))
    refs['knucleotide-remaining36']=dict(plan=dict(path=str(PLAN),sha256=PLAN_SHA),
        report=dict(path=terminal['report'],sha256=terminal['report_sha256']),
        terminal=dict(path=str(PACKET/'run-v1/terminal.json'),sha256=terminal_sha),
        status=report['status'],actual_native_processes=len(report['attempts']),
        qualified_samples=terminal['new_qualified_samples'])
    return refs


def verify_leases(leases):
    for path,handle,device,inode in leases:
        held,named=os.fstat(handle.fileno()),Path(path).lstat()
        require(stat.S_ISREG(held.st_mode) and stat.S_ISREG(named.st_mode)
            and (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==(device,inode),
            'Completed-job lease identity changed')


@contextmanager
def review_context(*,on_exit_failure=None,final_consumer_check=None):
    """Replay four actual cohorts under the common, suite and four owner leases."""
    with ExitStack() as stack:
        leases=[]
        for path,expected_inode in ((JOB/'owner.lock',None),(PREVIOUS_JOB/'owner.lock',82087540),
                (q.PRIOR_JOB/'owner.lock',82039660),(OLD/'owned-jobs/full90/owner.lock',81764070),
                (ROOT/'experiments/prolog/prolog-full90.owner.lock',81764078),(r.LOCK,79859134)):
            require(stat.S_ISREG(path.lstat().st_mode),'Regular retained lease required')
            handle=stack.enter_context(path.open('rb'));fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held,named=os.fstat(handle.fileno()),path.lstat()
            require(stat.S_ISREG(named.st_mode) and (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)
                and (expected_inode is None or held.st_ino==expected_inode),'Completed-job lease replaced')
            leases.append((path,handle,held.st_dev,held.st_ino))
        files=r.Files();files.verify(p.PYTHON,l.PYTHON_SHA)
        plan=files.document(str(PLAN),PLAN_SHA)
        for path,digest in plan['pins'].items():files.verify(path,digest)
        for path,digest in ((Path(__file__).resolve(),hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                (HELPER,HELPER_SHA),(q.HELPER,q.HELPER_SHA),(l.RECONCILER,l.RECONCILER_SHA),(r.HELPER,r.HELPER_SHA)):
            files.verify(str(path),digest)
        qualification=files.document(str(QUALIFICATION),QUALIFICATION_SHA)
        same(plan['knucleotide_qualification'],qualification,'Plan changed independent replacement disposition')
        original={key:files.document(str(path),digest) for key,(path,digest) in OLD_REFS.items()}
        prior=dict(plan=files.document(str(PRIOR_PLAN),PRIOR_PLAN_SHA),
            report=files.document(str(PRIOR/'run-v1/report.json'),q.PRIOR_REPORT_SHA),
            terminal=files.document(str(PRIOR/'run-v1/terminal.json'),q.FIXED[PRIOR/'run-v1/terminal.json']),
            request=files.document(str(PRIOR/'priority-interpreter-stop-v1/request.json'),q.FIXED[PRIOR/'priority-interpreter-stop-v1/request.json']),
            closure=files.document(str(PRIOR/'priority-interpreter-stop-v1/closure.json'),q.FIXED[PRIOR/'priority-interpreter-stop-v1/closure.json']),
            durable={name:files.document(str(q.PRIOR_JOB/(name+'.json')),q.FIXED[q.PRIOR_JOB/(name+'.json')])
                for name in ('request','launch','worker-started','command-started','terminal')})
        closure=files.document(str(STOP/'closure.json'),CLOSURE_SHA)
        def pinned(path,digest=None):
            path=str(path);return files.document(path,digest if digest is not None else plan['pins'][path])
        stopped=dict(plan=pinned(PREVIOUS_PLAN,PREVIOUS_PLAN_SHA),closure=closure,
            report=pinned(PREVIOUS/'run-v1/report.json',closure['controller_report_sha256']),
            terminal=pinned(PREVIOUS/'run-v1/terminal.json',closure['controller_terminal_sha256']),
            before=pinned(STOP/'before-report.json',closure['before_report_sha256']),
            request=pinned(STOP/'request.json',closure['request_sha256']),
            durable={name:pinned(PREVIOUS_JOB/(name+'.json'),closure['durable_terminal_sha256'] if name=='terminal' else None)
                for name in ('request','launch','worker-started','command-started','terminal')})
        sent=pinned(STOP/'signal-sent.json',closure['signal_sent_sha256'])
        require(sent['signal']==15 and sent['target']==2948 and sent['automatic_retry'] is False
            and sent['request_sha256']==closure['request_sha256'],'Actual deliberate stop signal differs')
        durable={name:files.document(str(JOB/(name+'.json')),hashlib.sha256((JOB/(name+'.json')).read_bytes()).hexdigest())
            for name in ('request','launch','worker-started','command-started','terminal')}
        require((JOB/'command.stderr').read_bytes()==b'','New durable controller emitted errors')
        inventories=[]
        for directory in (JOB,PREVIOUS_JOB,q.PRIOR_JOB,OLD/'owned-jobs/full90'):
            expected={str(directory/name) for name in ('request.json','launch.json','worker-started.json',
                'command-started.json','terminal.json','command.stdout','command.stderr','worker.log','owner.lock')}
            require(r.inventory(directory)==expected,'Durable artifact inventory differs')
            for path in expected:
                if path in files.verified:continue
                files.verify(path,hashlib.sha256(Path(path).read_bytes()).hexdigest())
            inventories.append((directory,expected))
        output=Path(plan['output']);terminal_path=output/'terminal.json'
        terminal_sha=hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal=files.document(str(terminal_path),terminal_sha)
        require(terminal['report']==str(output/'report.json'),'New report escaped output')
        report=files.document(terminal['report'],terminal['report_sha256'])
        retained_inventories={}
        for directory,closed in ((output,terminal),(PREVIOUS/'run-v1',stopped['terminal']),
                (PRIOR/'run-v1',prior['terminal']),(OLD/'results',original['terminal'])):
            expected=set(closed['available_evidence_pins'])|{str(directory/'terminal.json')}
            require(r.inventory(directory)==expected,'Closed native artifact inventory differs')
            for path,digest in closed['available_evidence_pins'].items():
                require(Path(path).is_relative_to(directory),'Artifact escapes closed cohort');files.verify(path,digest)
            inventories.append((directory,expected))
            if directory!=output:
                retained_inventories[str(directory)]=dict(closed['available_evidence_pins'],
                    **{str(directory/'terminal.json'):files.verified[str(directory/'terminal.json')]})
        same(plan['retained_artifact_inventories'],retained_inventories,'Plan changed retained complete inventories')
        for directory,relative in qualification['artifact_inventories'].items():
            expected={str(Path(directory)/name) for name in relative}
            require(r.inventory(Path(directory))==expected,'Qualified replacement artifact membership differs')
            for name,digest in relative.items():files.verify(str(Path(directory)/name),digest)
            inventories.append((Path(directory),expected))
        def documents(paths):return {path:files.document(path,files.verified[path]) for path in paths}
        old=original['report']['attempts'][:9]
        stopped_paths={path for path in stopped['terminal']['available_evidence_pins']
            if '/attempts/' in path or '/outer-supervisor/' in path}
        result=reconcile(plan,stopped,prior,original,report,terminal,durable,
            documents(a['result_path'] for a in report['attempts']),
            documents(a['supervisor_result_path'] for a in report['attempts']),
            documents(a['path'] for a in report['independent_supervisors']),
            documents(a['result_path'] for a in old),documents(a['supervisor_result_path'] for a in old),
            documents(str(attempt_paths(OLD/'results',a)[2]) for a in old),
            documents(prior['report']['validated_attempt_artifacts']),documents(stopped_paths))
        verified=tuple(files.verified.items())
        def recheck():
            for path,digest in verified:files.verify(path,digest)
            for directory,expected in inventories:require(r.inventory(directory)==expected,'Closed inventory changed during review')
            verify_leases(leases)
        result.update(status='full36-plus-retained54-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=dict(path=str(PLAN),sha256=PLAN_SHA),report=dict(path=terminal['report'],sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path),sha256=terminal_sha),durable_directory=str(JOB),
            cohorts=cohort_refs(stopped,report,terminal,terminal_sha),verified_file_pins=dict(verified))
        with q._yield_verified(result,recheck,on_exit_failure,final_consumer_check) as reviewed:yield reviewed


def review_files():
    with review_context() as result:return result


def write_review(path):
    owned={}
    def cleanup():
        if not owned:return
        current=path.lstat()
        raw=path.read_bytes() if stat.S_ISREG(current.st_mode) else None
        require(stat.S_ISREG(current.st_mode) and (current.st_dev,current.st_ino)==owned['identity']
            and (raw==owned['raw'] if owned['complete'] else owned['raw'].startswith(raw)),
            'Result changed; preserving external bytes')
        path.unlink();owned.clear()
    def verify_owned():
        current=path.lstat()
        require(stat.S_ISREG(current.st_mode) and (current.st_dev,current.st_ino)==owned['identity']
            and path.read_bytes()==owned['raw'],'Result bytes/identity changed during final closure')
        require((path.lstat().st_dev,path.lstat().st_ino)==owned['identity'],'Result replaced during final read')
    try:
        with review_context(on_exit_failure=cleanup,final_consumer_check=verify_owned) as result:
            raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode()
            with path.open('xb') as stream:
                opened=os.fstat(stream.fileno());owned.update(identity=(opened.st_dev,opened.st_ino),raw=raw,complete=False)
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
                owned['complete']=True
        return result,hashlib.sha256(raw).hexdigest()
    except BaseException as error:
        try:cleanup()
        except BaseException as restoration:raise BaseExceptionGroup('Review and owned-output restoration failed',[error,restoration])
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
        and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B')
    path=args.output.resolve()
    require(path.is_relative_to(PACKET) and not path.is_relative_to(PACKET/'run-v1')
        and not os.path.lexists(path) and path.parent.is_dir(),'Fresh reconciliation output required')
    result,digest=write_review(path)
    print(json.dumps(dict(status=result['status'],sha256=digest,qualified_samples=result['qualified_samples'])),flush=True)


if __name__=='__main__':main()
