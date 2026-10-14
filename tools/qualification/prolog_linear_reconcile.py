"""Independent reconciliation of 81 new Prolog slots and nine preserved samples.

Reads closed evidence only. No producer, sampler, runtime or compiler is imported.
File verification runs under the existing durable/suite/common leases and emits
an additive review, never a chart publication or an edit to native evidence.
"""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/prolog/full81-linear-v1'
OLD = ROOT/'experiments/prolog/full90-v1'
LINEAR = ROOT/'experiments/prolog/revcomp-linear-v1'
PLAN = PACKET/'plan-v1.json'
PLAN_SHA = 'ad39e6e8ccc4b4497b0462014bd1c1d7ee14e4837900adc409634deff0bb5aab'
CONTROLLER = ROOT/'tools/qualification/prolog_linear_full.py'
CONTROLLER_SHA = '27c50f640396d80bea2e505fb985ae7ef6ab354f6e7c0245d8609f68e1fc0e01'
JOB = OLD/'owned-jobs/linear-full81-v1'
RECONCILER = Path(__file__).with_name('prolog_reconcile.py')
RECONCILER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
SOURCE_SHA = 'bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322'
QLF_SHA = 'c4526a2d463d5c9c570e88b5ab68237ecf61244d104825ab1e4fbb66b13c1f9e'
COUNT_SHA = '808f8d4f98d2826925a27b34f4116e5a84d454cc7cb0d55935c0af7a9b4e9677'
WORK_SHA = '2225c08c30bf3e5aa518c57d96d6e6ffd9596c50e7858abfde96dab03ca7c1ae'
SCHEMA = 'prolog-linear-independent-81-plus9-reconciliation-v1'
OLD_REFS = {
    'plan': (OLD/'plan.json', '55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a'),
    'report': (OLD/'results/report.json', '88e9dad8e6ed707f8794c62ba081c10a0ffc75f2b2d7208db58489abe2f657b0'),
    'terminal': (OLD/'results/terminal.json', 'afc0be094e361a5240b8ccf23f1f5f1ab8e82db219aa7a8684091c567c863908'),
    'durable': (OLD/'owned-jobs/full90/terminal.json', '82241a16edf0874e80dad2aadb37c6d3e5b67e37e50a48ac37d070e883d4c229'),
    'cancellation': (OLD/'cancellation-v1.json', 'bd60e5b703fde262392e039780c93ba1bc4ad3ee20fb49356ce2182f6aa4dd0a'),
    'closure': (OLD/'cancellation-review-v1.json', 'd1ada9b81eaeba324fed6a20e2eacde7bfe755b1f845c56fff3b36cd05ffd2c9'),
}
raw = RECONCILER.read_bytes()
if hashlib.sha256(raw).hexdigest() != RECONCILER_SHA:
    raise ValueError('Frozen independent receipt validator changed')
spec = importlib.util.spec_from_file_location('linear_independent_receipts', RECONCILER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw, str(RECONCILER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
AGGREGATE = r.AGGREGATE | {'retained_attempts'}


def schedule(plan, previous):
    old_slots, old_profiles = r.schedule(previous)
    require(plan['schema'] == 'prolog-linear-continuation81-v1'
            and plan['status'] == 'prepared-awaiting-independent-review'
            and plan['controller'] == str(CONTROLLER) and plan['controller_sha256'] == CONTROLLER_SHA
            and plan['repository'] == str(ROOT) and plan['output'] == str(PACKET/'run-v1'), 'Wrong continuation identity')
    for name, value in (('samples',3),('full_processes',81),('combined_sample_slots',90),
            ('retained_qualified_samples',9),('new_prolog_processes',54),('new_mech_processes',27),
            ('source_work_profiles',20),('canonical_loc_profiles',20),('compiler_invocations',0),
            ('fixture_reexecutions',0),('bounded_reexecutions',0),('count_replays',0),('repeated_completed_samples',0)):
        require(p.integer(plan[name],value), 'Changed plan count: '+name)
    require(plan['shared_timing_lock'] == str(r.LOCK) and plan['common_mutex_held_continuously'] is True
            and plan['no_automatic_retry'] is True and plan['original_files_mutated'] is False
            and plan['full_timings_qualified'] is plan['chart_admission'] is False, 'Continuation policy changed')
    same(plan['historical_pins'], previous['historical_pins'], 'Original historical evidence aliases changed')
    require(all(plan['pins'].get(path) == digest for path,digest in previous['pins'].items()), 'Original pin omitted')
    for path,digest in [(CONTROLLER,CONTROLLER_SHA),(LINEAR/'candidate.pl',SOURCE_SHA),
            (LINEAR/'bounded-run-v1/authored/candidate.pl',SOURCE_SHA),
            (LINEAR/'bounded-run-v1/authored/candidate.qlf',QLF_SHA),
            (LINEAR/'compiled-work-review.md',WORK_SHA),
            (LINEAR/'source-counts-v1/source-count-review.json',COUNT_SHA),*OLD_REFS.values()]:
        require(plan['pins'].get(str(path)) == digest, 'Required continuation evidence pin missing')
    require(set(plan['manifests']) == set(r.BENCHES), 'Wrong workload inventory')
    slots, profiles = [], {}
    for bench in r.BENCHES:
        manifest, old = plan['manifests'][bench], previous['manifests'][bench]
        if bench != 'revcomp': same(manifest,old,'Unchanged workload manifest differs')
        else:
            same({k:v for k,v in manifest.items() if k not in ('profiles','orders')},
                 {k:v for k,v in old.items() if k not in ('profiles','orders')}, 'Reverse-complement workload policy differs')
            same(manifest['profiles'][2],old['profiles'][2],'Reverse-complement matched control changed')
        prefix = 'prolog-revcomp-linear' if bench == 'revcomp' else 'prolog-'+bench
        ids = [prefix+'-compact',prefix+'-optimized','mech-aot-control']
        rows = manifest['profiles']
        same([row['id'] for row in rows],ids,'Profile inventory changed')
        same([row['language'] for row in rows],['prolog','prolog','mech'],'Language inventory changed')
        orders = [dict(round=i+1,profiles=ids[i:]+ids[:i]) for i in range(3)]
        same(manifest['orders'],orders,'Three-sample rotation differs')
        for row in rows:
            key = bench+':'+row['id'] if row['language']=='prolog' else bench+':prolog-full-study:mech-control'
            require(row['key'] == key and row['benchmark'] == bench and key not in profiles, 'Duplicate or changed key')
            profiles[key] = row
        keys = {row['id']:row['key'] for row in rows}
        slots.extend([bench,order['round'],name,keys[name]] for order in orders for name in order['profiles'])
    pair = plan['manifests']['revcomp']['profiles'][:2]
    original = previous['manifests']['revcomp']['profiles'][0]
    for row in pair:
        require(row['source'] == str(LINEAR/'candidate.pl') and row['source_sha256'] == SOURCE_SHA
                and row['measured_source'] == str(LINEAR/'bounded-run-v1/authored/candidate.pl')
                and row['compiled_artifact'] == dict(path=str(LINEAR/'bounded-run-v1/authored/candidate.qlf'),
                    sha256=QLF_SHA,bytes=3352), 'Linear source/compiler artifact differs')
        same(row['command'],[original['binary'],'-q','-O','-f','none','--stack-limit=8g','-s',
            row['compiled_artifact']['path'],'-g','clbg_revcomp_linear:run'],'Linear production command differs')
        for name in ('binary','binary_sha256','runtime_environment','memory_policy','execution_mode','maximum_workers'):
            same(row[name],original[name],'Retained runtime policy differs: '+name)
        require(row['cwd'] == str(LINEAR/'bounded-run-v1/authored') and p.integer(row['loc'],242)
                and p.integer(row['canonical_loc'],242) and p.integer(row['physical_loc'],146)
                and row['eligible_for_chart'] is row['chart_admission'] is False,'Linear LOC or admission differs')
        same(row['source_bundle'],[dict(path=row['measured_source'],origin=row['source'],sha256=SOURCE_SHA,
            normalized_loc=242,physical_loc=146)],'Linear authored-source bundle differs')
        same(row['required_work_review'],dict(path=str(LINEAR/'compiled-work-review.md'),sha256=WORK_SHA,status='passed'),
             'Linear work review differs')
        same(row['source_count_review'],dict(path=str(LINEAR/'source-counts-v1/source-count-review.json'),sha256=COUNT_SHA),
             'Linear canonical review differs')
    same({k:v for k,v in pair[0].items() if k not in ('id','key','variant','source_alias_of','optimization_claim')},
         {k:v for k,v in pair[1].items() if k not in ('id','key','variant','source_alias_of','optimization_claim')},
         'Linear aliases do not execute the same source/artifact')
    require(pair[0]['variant']=='compact' and pair[0]['source_alias_of'] is None
            and pair[1]['variant']=='optimized' and pair[1]['source_alias_of']==pair[0]['id']
            and pair[1]['optimization_claim']=='explicit equivalent-source alias; no distinct optimization admitted',
            'Linear alias presented as a distinct optimization')
    same(plan['schedule'],slots,'Combined schedule differs')
    same(plan['retained_slots'],old_slots[:9],'Retained regex slots differ')
    same(plan['retained_slots'],slots[:9],'New schedule changes retained regex')
    same(plan['remaining_slots'],slots[9:],'Wrong 81 new slots')
    require(len(slots)==len({tuple(s) for s in slots})==90,'Incomplete unique schedule')
    return slots,profiles,old_profiles


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


def retained_checks(plan, previous, profiles, raw, supervised, outer):
    report,terminal,cancel,closure = [previous[k] for k in ('report','terminal','cancellation','closure')]
    require(report['status']==terminal['status']=='stopped-unqualified' and report['active'] is None
            and len(report['attempts'])==10 and report['qualified_samples']==9
            and report['completed_benchmarks']==['regexredux'] and report['pins_unchanged_at_end'] is True
            and report['supervisor']['pid']==83209 and terminal['integrity_errors']==[]
            and terminal['report_sha256']==OLD_REFS['report'][1], 'Old cancellation boundary differs')
    require(previous['durable']['status']=='command-failed' and previous['durable']['exit_code']==-2
            and previous['durable']['command_pid']==83209 and previous['durable']['actual_command_started'] is True,
            'Old durable controller boundary differs')
    require(closure['status']=='owned-cancellation-closed-no-measurement-admission'
            and closure['preserved_completed_attempt_files']==27 and closure['preserved_completed_samples']==9
            and closure['owned_sampler_reaped'] is True and closure['cleanup_errors']==[]
            and closure['remaining_owned_processes_or_groups']==[] and closure['deadline_expired'] is False,
            'Deliberate cancellation cleanup unverified')
    require(cancel['cancellation_is_timeout'] is cancel['cancellation_is_timing'] is False
            and cancel['attempt']==10 and report['attempts'][9]['qualified'] is False,
            'Cancelled attempt was admitted or relabeled as timeout')
    all_pins = dict(previous['plan']['historical_pins']);all_pins.update(terminal['prerequisite_pins'])
    reused,provenance,gaps,paths,grouped = [],[],[],{},{}
    previous_end = None
    for index,(slot,a) in enumerate(zip(plan['retained_slots'],report['attempts'][:9]),1):
        require(p.integer(a['attempt'],index) and a['qualified'] is True,'Retained sample missing or unqualified')
        base=str(OLD/'results/attempts')+'/'+f'{index:03d}-{slot[2]}'
        out=str(OLD/'results/outer-supervisor'/f'{index:03d}-{slot[2]}.json')
        require(a['result_path']==base+'.json' and a['supervisor_result_path']==base+'.supervisor.json',
                'Retained receipt path differs')
        begin,end=r.check_attempt(a,raw[a['result_path']],supervised[a['supervisor_result_path']],slot,
            profiles[slot[3]],previous['plan']['manifests'][slot[0]],all_pins,provenance)
        require(previous_end is None or previous_end<=begin,'Retained sample intervals overlap');previous_end=end
        gaps.extend(r.check_outer(outer[out],a,83209))
        for path in (a['result_path'],a['supervisor_result_path'],out):
            paths[str(Path(path).relative_to(OLD))]=terminal['available_evidence_pins'][path]
        grouped.setdefault(slot[3],[]).append(a)
        reused.append(dict(slot=slot,original_attempt=index,raw=a['result_path'],raw_sha256=paths[str(Path(a['result_path']).relative_to(OLD))],
            supervised=a['supervisor_result_path'],supervised_sha256=paths[str(Path(a['supervisor_result_path']).relative_to(OLD))],
            outer=out,outer_sha256=paths[str(Path(out).relative_to(OLD))],seconds=a['seconds'],validation=a['validation']))
    require(set(raw)=={a['result_path'] for a in report['attempts'][:9]}
            and set(supervised)=={a['supervisor_result_path'] for a in report['attempts'][:9]}
            and set(outer)=={item['outer'] for item in reused},'Retained sample artifact inventory differs')
    same(paths,cancel['preserved_completed_attempt_files'],'The 27 preserved receipt digests differ')
    same({key:[a['seconds'] for a in values] for key,values in grouped.items()},cancel['preserved_completed_samples'],
         'Preserved sample values differ')
    expected=dict(plan=str(OLD_REFS['plan'][0]),plan_sha256=OLD_REFS['plan'][1],
        report=str(OLD_REFS['report'][0]),report_sha256=OLD_REFS['report'][1],
        cancellation_review=str(OLD_REFS['closure'][0]),cancellation_review_sha256=OLD_REFS['closure'][1],
        reused_samples=reused,excluded_original_attempt=10,reused_native_processes=9,
        descriptive_provenance=provenance,kernel_identity_observation_gaps=gaps)
    same(plan['retained'],expected,'Plan does not preserve exactly the reviewed nine receipts')
    return grouped,provenance,gaps,previous_end


def reconcile(plan,previous,report,terminal,durable,raw,supervised,outer,old_raw,old_supervised,old_outer):
    slots,originals,old_profiles=schedule(plan,previous['plan'])
    grouped,provenance,gaps,last_old=retained_checks(plan,previous,old_profiles,old_raw,old_supervised,old_outer)
    parent=durable_checks(durable,plan)
    require(report['schema']=='prolog-linear-continuation81-v1' and terminal['schema']=='prolog-linear-continuation-terminal-v1'
            and report['status'] in ('complete','complete-with-unqualified-profiles') and report['status']==terminal['status']
            and report['active'] is None,'Continuation is not complete')
    require(report['plan']==str(PLAN) and report['plan_sha256']==PLAN_SHA and terminal['report']==plan['output']+'/report.json',
            'Report/terminal plan linkage differs')
    require(not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors'))
            and report['pins_unchanged_at_end'] is True and terminal['integrity_errors']==[], 'Continuation integrity failure')
    for value in (report,terminal):
        require(value['common_mutex_held_continuously'] is True and value['full_timings_qualified'] is value['chart_admission'] is False
                and value['native_launch_unconfirmed_attempts']==[],'Continuation scope or ownership differs')
    require(terminal['common_mutex_held'] is True and p.integer(terminal['common_mutex_inode'],79859134),
            'Terminal common mutex differs')
    same(report['reused_samples'],plan['retained']['reused_samples'],'Report changed reused samples')
    same(report['benchmark_order'],list(r.BENCHES),'Workload order differs')
    same(report['completed_benchmarks'],list(r.BENCHES),'Incomplete workloads')
    require(report['shared_timing_lock']==str(r.LOCK) and report['no_automatic_retry'] is True
            and all(p.integer(report[k],v) for k,v in (('sample_count',3),('source_work_profiles',20),
                ('canonical_loc_profiles',20),('retained_qualified_samples',9),('repeated_completed_samples',0))),
            'Report policy changed')
    for name in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','count_replays','repeated_completed_samples'):
        require(p.integer(terminal[name],0),'Unexpected repeated/preparation work')
    require(terminal['original_files_mutated'] is False and p.integer(terminal['retained_qualified_samples'],9),
            'Original evidence mutation or wrong retained count')
    expected_pins=dict(plan['pins']);expected_pins[str(PLAN)]=PLAN_SHA
    same(terminal['prerequisite_pins'],expected_pins,'Terminal prerequisite pins differ')
    require(report['supervisor']['pid']==parent,'Report supervisor differs from durable controller')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+report['supervisor']['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']),'Controller birth/command differs')
    require(set(report['programs'])==set(originals),'Profile membership differs')
    all_pins=dict(plan['historical_pins']);all_pins.update(expected_pins)
    attempts=report['attempts'];failed={};skipped=[];index=0;previous_end=None;used=set();new_provenance=[];new_gaps=[]
    require(len(report['independent_supervisors'])==len(attempts),'Outer supervisor count differs')
    for slot in slots[9:]:
        bench,round_,identifier,key=slot
        if key in failed:
            skipped.append(dict(benchmark=bench,round=round_,id=identifier,key=key));continue
        require(index<len(attempts),'Missing scheduled attempt');a=attempts[index];index+=1
        require(p.integer(a['attempt'],index),'New attempt index omitted or repeated')
        base=plan['output']+'/attempts/'+f'{index:03d}-{identifier}';out=plan['output']+'/outer-supervisor/'+f'{index:03d}-{identifier}.json'
        require(a['result_path']==base+'.json' and a['supervisor_result_path']==base+'.supervisor.json','New receipt path differs')
        ref=report['independent_supervisors'][index-1]
        require(ref['path']==out and ref['status']=='returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'][out]==ref['sha256'],'Outer receipt binding differs')
        begin,end=r.check_attempt(a,raw[a['result_path']],supervised[a['supervisor_result_path']],slot,
            originals[key],plan['manifests'][bench],all_pins,new_provenance)
        require(previous_end is None or previous_end<=begin,'New native timing intervals overlap');previous_end=end
        new_gaps.extend(r.check_outer(outer[out],a,parent))
        used.update((a['result_path'],a['supervisor_result_path'],out));grouped.setdefault(key,[]).append(a)
        if not a['qualified']:failed[key]=a
    require(index==len(attempts) and index+len(skipped)==81,'Unaccounted new attempts or skipped slots')
    require(set(raw)|set(supervised)|set(outer)==used,'Unexpected or missing native receipt')
    require(len(raw)==len(supervised)==len(outer)==index,'Native receipt classes overlap or duplicate')
    require(set(terminal['available_evidence_pins'])==used|{plan['output']+'/report.json'},'Unregistered terminal artifact')
    same(report['validated_attempt_artifacts'],{path:terminal['available_evidence_pins'][path] for path in used},
         'Terminal artifact inventory differs from validated snapshots')
    same(report['descriptive_provenance'],new_provenance,'Recorded provenance observations differ')
    same(report['kernel_identity_observation_gaps'],new_gaps,'Recorded kernel identity gaps differ')
    same(report['isolated_failed_profiles'],list(failed),'Failed-profile ledger differs')
    same(report['skipped_failed_profile_slots'],skipped,'Unexplained skipped slots')
    same(terminal['skipped_failed_profile_slots'],skipped,'Terminal skipped slots differ')
    require(report['status']==('complete-with-unqualified-profiles' if failed else 'complete'),'Status hides failures')
    good_new=sum(a['qualified'] for a in attempts)
    for value in (report,terminal):
        for key,expected in (('saved_attempts',index),('full_performance_runs',index),('qualified_samples',good_new+9)):
            require(p.integer(value[key],expected),'Wrong process/sample count: '+key)
        same(value['registered_native_attempts'],list(range(1,index+1)),'New native registration ledger differs')
    require(p.integer(terminal['new_qualified_samples'],good_new),'Terminal new sample count differs')
    summaries={}
    for key,original in originals.items():
        row=report['programs'][key];observations=grouped.get(key,[]);retained=original['benchmark']=='regexredux'
        same({k:v for k,v in row.items() if k not in AGGREGATE},original,'Profile execution/source metadata changed')
        same(row['attempts'],[] if retained else [a['attempt'] for a in observations],'New profile membership differs')
        same(row['retained_attempts'],[a['attempt'] for a in observations] if retained else [],'Retained membership differs')
        good=[a for a in observations if a['qualified']];values=[a['seconds'] for a in good]
        same(row['samples_seconds'],values,'Profile sample values differ')
        same(row['sample_validation'],[a['validation'] for a in good],'Profile validation membership differs')
        if key in failed:
            require(row['measurement_status']=='failed-full-workload' and len(values)<3 and row.get('median_seconds') is None
                    and row.get('sample_stdev_seconds') is None and row['time_x_mech'] is None,'Partial failed timings promoted')
            same(row['full_failure'],failed[key],'Failure differs from actual attempt');median=sd=None
        else:
            require(row['measurement_status']=='measured' and not row.get('full_failure'),'Incomplete profile')
            median,sd=p.three_statistics(values)
            require(p.finite(row['median_seconds'],True) and row['median_seconds']==median
                    and p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds']>=0
                    and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Median or SD differs')
        summaries[key]=dict(key=key,id=row['id'],language=row['language'],benchmark=row['benchmark'],source=row['source'],
            source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],attempts=[a['attempt'] for a in observations],
            attempt_cohort='preserved-full90' if retained else 'linear-full81',samples_seconds=values,median_seconds=median,
            sample_stdev_seconds=sd,full_workload_qualified=key not in failed,failed_attempt=failed.get(key,{}).get('attempt'),
            sample_evidence=[dict(attempt=a['attempt'],round=a['round'],raw=a['result_path'],supervisor=a['supervisor_result_path'],
                stdout_bytes=a['stdout_bytes'],stdout_sha256=a['stdout_sha256'],validation=a['validation']) for a in good])
    for key,row in report['programs'].items():
        control_key=row['benchmark']+':prolog-full-study:mech-control';control=summaries[control_key]
        require(row['matched_mech_control']==control_key and row['matched_mech_source_sha256']==originals[control_key]['source_sha256'],
                'Matched control source differs')
        ratio=summaries[key]['median_seconds']/control['median_seconds'] if key not in failed and control_key not in failed else None
        same(row['time_x_mech'],ratio,'Matched Mech ratio differs');summaries[key]['time_x_mech']=ratio
    require(last_old<=p.timestamp(report['started_at'])<=p.timestamp(attempts[0]['started_at'])
            and previous_end<=p.timestamp(report['finished_at']),'New study interval excludes samples or overlaps retained cohort')
    require(p.timestamp(durable['command-started']['started_at'])<=p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at'])<=p.timestamp(durable['terminal']['finished_at']),'Samples exceed durable lifetime')
    return dict(schema=SCHEMA,status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        new_full_native_processes=index,reused_qualified_samples=9,actual_full_native_processes=index+9,
        total_native_processes_including_cancelled=index+10,excluded_original_attempt=10,
        qualified_samples=good_new+9,new_qualified_samples=good_new,skipped_slots=skipped,failed_profiles=list(failed),
        profiles=summaries,repeated_completed_samples=0,original_files_mutated=False,
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance+new_provenance})],
        kernel_identity_observation_gaps=gaps+new_gaps,file_integrity_verified=False,chart_admission=False,
        runtime_publication_metadata_qualified=False,full_timings_qualified=False,complete_stdout_retained=False,
        full_output_evidence='sampler byte counts/hashes and frozen complete-output validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        cohort_policy='Nine original regex samples with their original matched control; 81 new slots for nine other workloads.',
        source_evidence=dict(original_plan=dict(path=str(OLD_REFS['plan'][0]),sha256=OLD_REFS['plan'][1]),
            original_source_outcome=previous['plan']['sealed_source_outcome'],linear_qualification=plan['linear_qualification']),
        admission_requirements=['recorded runtime metadata review for all20 forms including linear QLF',
            'explicit publication excluding failed profiles and preserving source aliases', 'catalog and website validation'])


def review_files():
    files=r.Files()
    with ExitStack() as stack:
        leases=[]
        for path,expected_inode in ((JOB/'owner.lock',None),(OLD/'owned-jobs/full90/owner.lock',81764070),
                (ROOT/'experiments/prolog/prolog-full90.owner.lock',81764078),(r.LOCK,79859134)):
            handle=stack.enter_context(path.open('rb'));fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held,named=os.fstat(handle.fileno()),path.stat()
            require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)
                    and (expected_inode is None or held.st_ino==expected_inode),'Existing lease was replaced')
            leases.append((path,handle,held.st_dev,held.st_ino))
        files.verify(p.PYTHON,PYTHON_SHA)
        plan=files.document(str(PLAN),PLAN_SHA)
        previous={key:files.document(str(path),digest) for key,(path,digest) in OLD_REFS.items()}
        for path in (Path(__file__).resolve(),RECONCILER,r.HELPER):
            files.verify(str(path),hashlib.sha256(path.read_bytes()).hexdigest())
        for path,digest in plan['pins'].items():files.verify(path,digest)
        durable={name:files.document(str(JOB/(name+'.json')),hashlib.sha256((JOB/(name+'.json')).read_bytes()).hexdigest())
                 for name in ('request','launch','worker-started','command-started','terminal')}
        require((JOB/'command.stderr').read_bytes()==b'','Durable command stderr is not empty')
        job_inventory=r.inventory(JOB)
        require(job_inventory=={str(JOB/name) for name in ('request.json','launch.json','worker-started.json',
            'command-started.json','terminal.json','command.stdout','command.stderr','worker.log','owner.lock')},
            'Durable file inventory differs')
        for path in job_inventory:
            with Path(path).open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            files.verify(path,digest)
        output=Path(plan['output']);terminal_path=output/'terminal.json'
        terminal_sha=hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal=files.document(str(terminal_path),terminal_sha)
        require(terminal['report']==str(output/'report.json'),'Terminal report escaped its run')
        report=files.document(terminal['report'],terminal['report_sha256'])
        inventories=[]
        for directory,closed,path in ((output,terminal,terminal_path),(OLD/'results',previous['terminal'],OLD_REFS['terminal'][0])):
            expected=set(closed['available_evidence_pins'])|{str(path)}
            require(r.inventory(directory)==expected,'Closed native artifact inventory differs')
            for name,digest in closed['available_evidence_pins'].items():
                require(Path(name).is_relative_to(directory),'Native artifact escapes its run');files.verify(name,digest)
            inventories.append((directory,expected))
        def docs(names,available):return {name:files.document(name,available[name]) for name in names}
        available=terminal['available_evidence_pins'];old_available=previous['terminal']['available_evidence_pins']
        retained=previous['report']['attempts'][:9]
        result=reconcile(plan,previous,report,terminal,durable,
            docs((a['result_path'] for a in report['attempts']),available),
            docs((a['supervisor_result_path'] for a in report['attempts']),available),
            docs((a['path'] for a in report['independent_supervisors']),available),
            docs((a['result_path'] for a in retained),old_available),
            docs((a['supervisor_result_path'] for a in retained),old_available),
            docs((str(OLD/'results/outer-supervisor'/f'{a["attempt"]:03d}-{a["id"]}.json') for a in retained),old_available))
        for path,digest in list(files.verified.items()):files.verify(path,digest)
        for directory,expected in inventories:require(r.inventory(directory)==expected,'Native artifact inventory changed during review')
        require(r.inventory(JOB)==job_inventory,'Durable inventory changed during review')
        for path,handle,device,inode in leases:
            held,named=os.fstat(handle.fileno()),path.stat()
            require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==(device,inode),'Lease identity changed')
        result.update(status='full81-plus-retained9-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=dict(path=str(PLAN),sha256=PLAN_SHA),report=dict(path=terminal['report'],sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path),sha256=terminal_sha),durable_directory=str(JOB),verified_file_pins=files.verified)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B without -O')
    output=args.output.resolve()
    require(output.is_relative_to(PACKET) and not output.is_relative_to(PACKET/'run-v1')
            and not output.exists() and output.parent.is_dir(),'Fresh additive review outside native output required')
    result=None
    try:result=review_files()
    except BaseException as error:
        result=dict(schema=SCHEMA,status='reconciliation-failed',error_type=type(error).__name__,error=str(error),
            file_integrity_verified=False,full_timings_qualified=False,runtime_publication_metadata_qualified=False,chart_admission=False)
        raise
    finally:
        if result is not None:
            with output.open('x') as stream:
                p.json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


if __name__=='__main__':main()
