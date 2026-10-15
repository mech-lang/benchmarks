"""Independent full60 Rebol ledger and held physical-evidence review.

No timing producer or sampler is imported. The existing prerequisite consumer
replays the actual extension, fixture, bounded-output, work and count evidence;
frozen independent primitives check every fresh native timing receipt.
"""
from contextlib import ExitStack, contextmanager
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/full60-v1'
CONTROLLER = ROOT/'tools/qualification/rebol_full60.py'
QUALIFIER = ROOT/'tools/qualification/rebol_qualification_final.py'
ORIGINAL = ROOT/'tools/qualification/rebol_full.py'
ORIGINAL_SHA = '62617612fee2c4047e23dd704f1da826349b68fcef270b9919d693238631bca6'
HELPER = ROOT/'tools/qualification/prolog_reconcile.py'
HELPER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
raw_helper = HELPER.read_bytes()
if hashlib.sha256(raw_helper).hexdigest() != HELPER_SHA:
    raise ValueError('Independent receipt helper changed')
spec = importlib.util.spec_from_file_location('rebol_independent_receipts', HELPER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw_helper, str(HELPER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
BENCHES, SIZES, LOCK, POWER = r.BENCHES, r.SIZES, r.LOCK, r.POWER
AGGREGATE, check_attempt, check_outer = r.AGGREGATE, r.check_attempt, r.check_outer
SCHEMA = 'rebol-independent-full60-reconciliation-v1'
JOB = ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-full60-v1'
SUITE = PACKET/'rebol-full60.owner.lock'
CLBG = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
CONTROL_REFS = {
    'audit': dict(path=str(CLBG/'r-apl-uiua-comparison/20261011/source-audit-r.json'),
        sha256='d76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'),
    'mandelbrot': dict(path=str(CLBG/'mandelbrot/experiments/20261011-array-state/source-modes-study/full-study/manifest.json'),
        sha256='fbffba7b5674e889ac9e5088bbb2e2d8499df41f5d9b4c677be38d831091680f'),
}
FULL_REFERENCES = {
    'regexredux': (298,'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'),
    'revcomp': (254166745,'e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'),
    'pidigits': (16893,'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
    'spectralnorm': (12,'f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'),
    'mandelbrot': (32000015,'609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'),
    'fasta': (254166745,'3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
    'knucleotide': (259,'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'),
    'binarytrees': (455,'341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'nbody': None,
    'fannkuchredux': (29,'4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'),
}
TIMING_POLICY = ('Fresh direct Rebol process including runtime startup, authored source/facade evaluation, '
    'extension loading, full input, all work, complete output and shutdown; extension compilation, '
    'harness file setup, pin hashing, environment waits and output validation excluded')
EXECUTION_FIELDS = ('id','key','benchmark','language','source','source_sha256','binary',
                    'binary_sha256','command','cwd','runtime_environment')


def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return json.dumps(value,sort_keys=True,allow_nan=False).encode()


def expected_subject(base, form, admission, output, pins):
    require(form=='compact', 'Only the canonical compact subject is admitted')
    bench = base['benchmark']; main = base['main']; runtime = admission['runtime']['binary']
    image = admission['extension_image']; inputs = base['physical_inputs']
    fixed = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C',
                 OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
    env = dict(fixed, HOME=output+'/home', REBOL_HOME=output+'/home', TMPDIR=output+'/tmp',
               MECH_CLBG_REBOL_PRIMITIVES=image['path'])
    require(base['language']=='rebol3' and base['original_profile_id']==f'rebol-{bench}-baseline-v1'
            and p.integer(base['maximum_workers'],1) and base['cwd']==str(ROOT)
            and base['formatted_loc'] is None, 'Qualified source identity differs')
    same(base['command_prefix'],[runtime['path'],'-q','-s',main['path']], 'Direct runtime command differs')
    stdin = bench in ('regexredux','revcomp','knucleotide')
    require(base['input_kind']==('stdin' if stdin else 'integer-argument'), 'Input policy differs')
    same(base['runtime_environment_policy'],dict(fixed=fixed,
        fresh_directories=dict(HOME='home',REBOL_HOME='home',TMPDIR='tmp'),
        extension_variable='MECH_CLBG_REBOL_PRIMITIVES',ambient_loader_overrides=False,diagnostic_flags=[]),
        'Default runtime environment differs')
    same(base['alias_policy'],dict(authored_source_forms=1,publication_forms=['compact'],
        distinct_optimization_claim=False,copied_timing_allowed=False), 'Source alias scope differs')
    require(len(inputs)==(5 if bench in ('pidigits','regexredux') else 4)
            and len({v['path'] for v in inputs})==len(inputs), 'Source bundle membership differs')
    roles = {}
    for item in inputs:
        require(item['counted'] is True and pins.get(item['path'])==item['sha256']
                and p.digest(item['sha256']) and all(p.integer(item[k]) and item[k]>0
                for k in ('canonical_loc','physical_loc')), 'Uncounted or unpinned source')
        roles.setdefault(item['role'],[]).append(item)
    require(set(roles)=={'application','application-helper','application-launcher','general-library-helper'}
            and all(len(roles[k])==1 for k in ('application','application-launcher','general-library-helper')),
            'Counted owner roles differ')
    same({k:roles['application'][0][k] for k in ('path','sha256')},main,'Main owner differs')
    require(Path(roles['application-launcher'][0]['path']).name=='clbg_primitives.reb'
            and Path(roles['general-library-helper'][0]['path']).name=='clbg_primitives.c'
            and {Path(v['path']).name for v in roles['application-helper']}==
            ({'clbg_io.reb','clbg_big.reb'} if bench=='pidigits' else
             {'clbg_io.reb','clbg_regex.reb'} if bench=='regexredux' else {'clbg_io.reb'}),
            'General helpers or corrected C omitted')
    require(all(p.integer(base[k]) and base[k]==sum(v[k] for v in inputs)
                for k in ('canonical_loc','physical_loc')), 'Count totals differ')
    for item in (main,runtime,image):
        require(p.digest(item['sha256']) and pins.get(item['path'])==item['sha256'], 'Unbound source/runtime/image')
    identity=f'rebol-{bench}-{form}'
    return dict(id=identity,key=identity,benchmark=bench,variant=form,language='rebol3',
        source=main['path'],source_sha256=main['sha256'],binary=runtime['path'],binary_sha256=runtime['sha256'],
        command=base['command_prefix']+([] if stdin else ['{n}']),cwd=str(ROOT),runtime_environment=env,
        maximum_workers=1,physical_inputs=inputs,support=dict(extension_image=image,counted_authored_inputs=inputs),
        original_profile_id=base['original_profile_id'],corrections=base['corrections'],alias_policy=base['alias_policy'],
        source_alias_group=base['original_profile_id'],separate_fresh_samples_required=True,optimization_claim=False,
        source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,
        loc=base['canonical_loc'],canonical_loc=base['canonical_loc'],physical_loc=base['physical_loc'],formatted_loc=None,
        runtime_policy_changes=[],diagnostic_flags=[],runtime_source_equivalence_proven=False,chart_admission=False)


def schedule(plan):
    require(plan['schema']=='rebol-qualified-full60-v1' and plan['status']=='prepared-awaiting-independent-review'
            and plan['pins_verified'] is True and plan['repository']==str(ROOT)
            and plan['controller']==str(CONTROLLER) and p.digest(plan['controller_sha256'])
            and plan['pins'].get(str(CONTROLLER))==plan['controller_sha256'], 'Wrong prepared producer')
    require(Path(plan['output']).is_relative_to(PACKET) and Path(plan['output'])!=PACKET
            and '..' not in Path(plan['output']).parts, 'Output escapes full60 packet')
    counts=dict(source_work_profiles=10,canonical_loc_profiles=10,formatted_loc_profiles=0,
        distinct_subject_bundles=10,counted_physical_sources=15,retained_bounded_cases=149,retained_primitive_cases=18,
        samples=3,rebol_samples=30,matched_mech_samples=30,full_processes=60,new_native_probes=0,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0)
    require(all(p.integer(plan[k],v) for k,v in counts.items()), 'Preparation or sample accounting differs')
    require(all(plan[k] is False for k in ('original_files_mutated','chart_admission','full_timings_qualified',
                'runtime_source_equivalence_proven')) and plan['no_automatic_retry'] is True
            and plan['continuous_common_mutex'] is True and plan['shared_timing_lock']==str(LOCK)
            and p.integer(plan['common_mutex_inode'],p.LOCK_INODE) and plan['timing_policy']==TIMING_POLICY,
            'Timer, admission or ownership policy differs')
    require(set(plan['pins'])==set(plan['resolutions']) and all(p.digest(v) for v in plan['pins'].values()),
            'Named prerequisite closure differs')
    for name in ('qualification_manifest','source_review','original_profiles','cohort_policy_file'):
        ref=plan[name];require(set(ref)=={'path','sha256'} and plan['pins'].get(ref['path'])==ref['sha256'],
                               'Unbound plan evidence')
    same(plan['cohort_policy_file']['path'],str(PACKET/'POLICY.md'),'Canonical cohort policy path differs')
    same(plan['subject_policy'],dict(authored_source_forms_per_workload=1,publication_forms=['compact'],
        duplicate_program_records=0,distinct_optimization_claim=False),'Canonical subject policy differs')
    admission=plan['qualification'];scope=admission['scope']
    require(admission['schema']=='rebol-pre-timing-admission-v1' and admission['manifest']==plan['qualification_manifest']
            and all(scope[k] is True for k in ('required_work_qualified','canonical_source_count_qualified',
                'bounded_output_qualified','extension_abi_qualified','full_primitive_fixtures_qualified'))
            and all(scope[k] is False for k in ('runtime_source_equivalence_proven','full_timing_qualified','chart_admission')),
            'Actual prerequisite approval differs')
    bases=admission['bases'];require(len(bases)==10 and {v['benchmark'] for v in bases}==set(BENCHES), 'Ten bases required')
    require(len({v['path'] for b in bases for v in b['physical_inputs']})==15, 'Fifteen physical sources required')
    require(set(plan['manifests'])==set(BENCHES), 'Ten manifests required')
    slots,profiles=[],{}
    for bench in BENCHES:
        m=plan['manifests'][bench];rows=m['profiles'];base=next(v for v in bases if v['benchmark']==bench)
        require(m['benchmark']==bench and all(p.integer(m[k],v) for k,v in dict(size=SIZES[bench],samples=3,
            timeout_seconds=21600,supervisor_timeout_seconds=22200,maximum_rss_mib=10240).items()), 'Workload or bounds differ')
        require(m['canonical_full_workload'] is m['compilation_outside_timer'] is
                m['runtime_source_helpers_extension_loading_inside_timer'] is m['no_automatic_retry'] is True
                and m['chart_admission'] is False and m['shared_timing_lock']==str(LOCK), 'Manifest policy differs')
        ref=FULL_REFERENCES[bench]
        same(m['full_output_reference'],None if ref is None else dict(bytes=ref[0],sha256=ref[1]),'Full output reference differs')
        require(len(rows)==2, 'One canonical subject plus control required')
        for i,form in enumerate(('compact',)):
            same(rows[i],expected_subject(base,form,admission,plan['output'],plan['pins']), 'Subject differs from qualification')
        c=rows[1];require(c['id']=='mech-aot-control' and c['language']=='mech' and c['benchmark']==bench
            and c['key']==bench+':rebol-full-study:mech-control' and p.integer(c['maximum_workers'],8)
            and c['chart_admission'] is False and c['loc'] is None, 'Control identity differs')
        for row in rows:
            require('timing_alias_of' not in row and row['key'] not in profiles, 'Copied or duplicate timing row')
            require(all(plan['pins'].get(row[k])==row[k+'_sha256'] and p.digest(row[k+'_sha256'])
                        for k in ('source','binary')), 'Unpinned measured source/runtime')
            profiles[row['key']]=row
        ids=[v['id'] for v in rows];orders=[dict(round=i+1,profiles=ids[i % 2:]+ids[:i % 2]) for i in range(3)]
        same(m['orders'],orders,'Rotation differs')
        keys={v['id']:v['key'] for v in rows}
        slots.extend([bench,o['round'],identity,keys[identity]] for o in orders for identity in o['profiles'])
    require(len(slots)==len({tuple(v) for v in slots})==60 and len(profiles)==20, 'Incomplete full60 schedule')
    same(plan['schedule'],slots,'Saved schedule differs')
    return slots,profiles


def check_controls(plan, documents):
    require(documents['audit']['status']=='reviewed' and
            {v['benchmark'] for v in documents['audit']['controls']}==set(BENCHES), 'Control audit differs')
    for bench in BENCHES:
        ref=CONTROL_REFS['mandelbrot' if bench=='mandelbrot' else 'audit']
        origin=(next(v for v in documents['mandelbrot']['profiles'] if v['id']=='row16-aot-control')
                if bench=='mandelbrot' else next(v for v in documents['audit']['controls'] if v['benchmark']==bench))
        expected={k:copy.deepcopy(origin[k]) for k in EXECUTION_FIELDS}
        expected.update(id='mech-aot-control',key=bench+':rebol-full-study:mech-control',maximum_workers=8,
            loc=None,role='Fresh unchanged matched Mech AOT control',chart_admission=False,
            control_provenance=dict(ref,original_id=origin['id']))
        same(plan['manifests'][bench]['profiles'][1],expected,'Matched control differs from retained source audit')


def check_durable(durable, plan_path, plan_sha, plan):
    request,launch,worker,started,ended=[durable[k] for k in ('request','launch','worker-started','command-started','terminal')]
    command=[p.PYTHON,'-I','-S','-B',plan['controller'],'run','--plan',plan_path,'--plan-sha256',plan_sha]
    for item in (request,launch,worker,started):
        same(item['command'],command,'Durable command differs');require(item['cwd']==str(ROOT),'Durable cwd differs')
    require(p.integer(request['schema_version'],1) and request['common_mutex_owned_by_target_command'] is True
            and worker['inherited_private_lease'] is worker['detached_session'] is
                worker['common_mutex_owned_by_target_command'] is True, 'Durable ownership differs')
    require(all(v['qualification_granted'] is False for v in (request,launch,worker,ended))
            and all(v['automatic_retry'] is False for v in (request,launch,ended)), 'Durable admission/retry differs')
    require(ended['status']=='command-exited-zero-awaiting-report-review' and p.integer(ended['exit_code'],0)
            and ended['actual_command_started'] is True and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False and ended['stop_signals']==[], 'Durable execution failed')
    require(not any(ended.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure')), 'Durable cleanup failed')
    first=p.process_identity(started['command_identity']);last=p.process_identity(ended['command_identity'])
    same(first,last,'Controller identity changed');same(first[2],' '.join(command),'Observed controller argv differs')
    require(p.integer(started['command_pid']) and started['command_pid']>0
            and p.integer(ended['command_pid'],started['command_pid']) and first[0]==started['command_pid'], 'Controller PID differs')
    owner=p.process_identity(worker['worker_identity'])
    for item in (launch,ended):same(p.process_identity(item['worker_identity']),owner,'Worker identity changed')
    require(all(v['command_identity']['listing'].split(None,7)[1]==str(owner[0]) for v in (started,ended)), 'Controller parent differs')
    require(p.timestamp(request['created_at'])<=p.timestamp(worker['started_at'])<=p.timestamp(started['started_at'])
            <=p.timestamp(ended['finished_at']), 'Durable times differ')


def reconcile(plan, report, terminal, raw, supervised, outer, durable, plan_path, plan_sha):
    """Pure ledger. This alone grants no file, runtime or publication approval."""
    require(p.digest(plan_sha),'Exact plan SHA required');slots,originals=schedule(plan)
    check_durable(durable,plan_path,plan_sha,plan);parent=durable['command-started']['command_pid']
    identity=report['supervisor'];require(p.integer(identity['pid'],parent),'Report controller differs')
    same(p.process_identity(dict(pid=parent,listing=str(parent)+' 0 '+identity['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']),'Report controller birth/argv differs')
    require(report['schema']=='rebol-full60-results-v1' and terminal['schema']=='rebol-full60-terminal-v1'
            and report['status'] in ('complete','complete-with-unqualified-profiles')
            and terminal['status']==report['status'] and report['active'] is None, 'Not a completed full60 ledger')
    require(not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors'))
            and terminal['integrity_errors']==[] and report['pins_unchanged_at_end'] is True,
            'Terminal integrity failure')
    require(report['plan']==plan_path and report['plan_sha256']==plan_sha
            and report['qualification_manifest']==plan['qualification_manifest'], 'Report plan binding differs')
    pins=dict(plan['pins']);pins[plan_path]=plan_sha
    resolutions=dict(plan['resolutions']);resolutions[plan_path]=plan_path
    same(terminal['prerequisite_pins'],pins,'Terminal input closure differs')
    same(terminal['prerequisite_resolutions'],resolutions,'Terminal named input resolutions differ')
    require(terminal['common_mutex_held'] is terminal['common_mutex_held_continuously'] is True
            and p.integer(terminal['common_mutex_inode'],p.LOCK_INODE), 'Timing lock boundary differs')
    for item in (report,terminal):
        require(all(item[k] is False for k in ('chart_admission','full_timings_qualified','runtime_source_equivalence_proven')),
                'Measurement grants unsupported admission')
        same(item['native_launch_unconfirmed_attempts'],[],'Unconfirmed native launch')
    require(terminal['original_files_mutated'] is False and all(p.integer(terminal[k],0) for k in
        ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','repeated_completed_samples')), 'Unexpected preparation/retry')
    require(report['no_automatic_retry'] is True and report['shared_timing_lock']==str(LOCK)
            and all(p.integer(report[k],v) for k,v in dict(sample_count=3,source_work_profiles=10,
                canonical_loc_profiles=10,formatted_loc_profiles=0,planned_rebol_samples=30,planned_matched_mech_samples=30).items()),
            'Report policy differs')
    same(report['benchmark_order'],list(BENCHES),'Benchmark order differs')
    same(report['completed_benchmarks'],list(BENCHES),'Incomplete workload accounting')
    require(set(report['programs'])==set(originals),'Profile inventory differs')
    attempts=report['attempts'];failed={};skipped=[];provenance=[];gaps=[];grouped={k:[] for k in originals}
    index=0;previous_end=None;used_raw=set();used_supervised=set();used_outer=set()
    require(len(report['independent_supervisors'])==len(attempts),'Outer receipt count differs')
    for slot in slots:
        bench,round_number,identifier,key=slot
        if key in failed:
            skipped.append(dict(benchmark=bench,round=round_number,id=identifier,key=key));continue
        require(index<len(attempts),'Missing scheduled attempt');a=attempts[index];index+=1
        require(p.integer(a['attempt'],index),'Repeated or missing attempt')
        base=plan['output']+'/attempts/'+f'{index:03d}-{identifier}'
        require(a['result_path']==base+'.json' and a['supervisor_result_path']==base+'.supervisor.json','Receipt path differs')
        path=plan['output']+'/outer-supervisor/'+f'{index:03d}-{identifier}.json';ref=report['independent_supervisors'][index-1]
        require(ref['path']==path and ref['status']=='returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'].get(path)==ref['sha256'],'Outer receipt binding differs')
        begin,end=check_attempt(a,raw[a['result_path']],supervised[a['supervisor_result_path']],slot,
                               originals[key],plan['manifests'][bench],pins,provenance)
        require(previous_end is None or previous_end<=begin,'Native timing intervals overlap');previous_end=end
        gaps.extend(check_outer(outer[path],a,parent));grouped[key].append(a)
        used_raw.add(a['result_path']);used_supervised.add(a['supervisor_result_path']);used_outer.add(path)
        if not a['qualified']:failed[key]=a
    require(index==len(attempts) and index+len(skipped)==60,'Unaccounted execution or skip')
    require(set(raw)==used_raw and set(supervised)==used_supervised and set(outer)==used_outer,'Receipt membership differs')
    available=terminal['available_evidence_pins'];report_path=plan['output']+'/report.json'
    require(set(available)==used_raw|used_supervised|used_outer|{report_path}
            and all(p.digest(v) for v in available.values()) and terminal['report']==report_path
            and available[report_path]==terminal['report_sha256'],'Closed full60 inventory differs')
    snapshots={k:available[k] for k in sorted(used_raw|used_supervised|used_outer)}
    same(report['validated_attempt_artifacts'],snapshots,'Report snapshots differ')
    same(terminal['validated_attempt_artifacts'],snapshots,'Terminal snapshots differ')
    same(report['descriptive_provenance'],provenance,'Report descriptive provenance differs')
    same(report['kernel_identity_observation_gaps'],gaps,'Report identity observation gaps differ')
    same(report['isolated_failed_profiles'],list(failed),'Failure inventory differs')
    for item in (report,terminal):same(item['skipped_failed_profile_slots'],skipped,'Unexplained skipped slots')
    require(report['status']==('complete-with-unqualified-profiles' if failed else 'complete'),'Status hides failure')
    qualified=sum(a['qualified'] for a in attempts)
    for item in (report,terminal):
        require(all(p.integer(item[k],v) for k,v in dict(saved_attempts=index,full_performance_runs=index,
                qualified_samples=qualified).items()),'Execution totals differ')
        same(item['registered_native_attempts'],list(range(1,index+1)),'Registration ledger differs')
    summaries={}
    for key,original in originals.items():
        row=report['programs'][key];observations=grouped[key];good=[a for a in observations if a['qualified']]
        same({k:v for k,v in row.items() if k not in AGGREGATE},original,'Measured profile metadata differs')
        same(row['attempts'],[a['attempt'] for a in observations],'Profile attempt membership differs')
        values=[a['seconds'] for a in good];same(row['samples_seconds'],values,'Sample values differ')
        same(row['sample_validation'],[a['validation'] for a in good],'Sample validations differ')
        if key in failed:
            require(row['measurement_status']=='failed-full-workload' and len(values)<3
                and row.get('median_seconds') is row.get('sample_stdev_seconds') is row['time_x_mech'] is None,
                'Partial failure promoted to median');same(row['full_failure'],failed[key],'Failure differs');median=sd=None
        else:
            require(row['measurement_status']=='measured' and not row.get('full_failure'),'Incomplete measured profile')
            median,sd=p.three_statistics(values)
            require(p.finite(row['median_seconds'],True) and row['median_seconds']==median
                and p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds']>=0
                and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Median or sample SD differs')
        evidence=[]
        for a in observations:
            outer_path=plan['output']+'/outer-supervisor/'+f'{a["attempt"]:03d}-{a["id"]}.json'
            evidence.append(dict(attempt=a['attempt'],round=a['round'],qualified=a['qualified'],seconds=a.get('seconds'),
                raw=dict(path=a['result_path'],sha256=available[a['result_path']]),
                supervisor=dict(path=a['supervisor_result_path'],sha256=available[a['supervisor_result_path']]),
                outer=dict(path=outer_path,sha256=available[outer_path]),stdout_bytes=a.get('stdout_bytes'),
                stdout_sha256=a.get('stdout_sha256'),validation=copy.deepcopy(a.get('validation'))))
        summaries[key]=dict(key=key,id=row['id'],language=row['language'],benchmark=row['benchmark'],
            source=row['source'],source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
            original_profile=copy.deepcopy(original),attempts=list(row['attempts']),samples_seconds=values,
            median_seconds=median,sample_stdev_seconds=sd,full_workload_qualified=key not in failed,
            failed_attempt=failed.get(key,{}).get('attempt'),sample_evidence=evidence,
            sample_execution_metadata=[copy.deepcopy(a) for a in observations],
            full_output_validation=[copy.deepcopy(a['validation']) for a in good])
    for key,row in report['programs'].items():
        control_key=row['benchmark']+':rebol-full-study:mech-control';control=summaries[control_key]
        require(row['matched_mech_control']==control_key and
                row['matched_mech_source_sha256']==originals[control_key]['source_sha256'],'Matched control differs')
        eligible=key not in failed and control_key not in failed
        ratio=summaries[key]['median_seconds']/control['median_seconds'] if eligible else None
        same(row['time_x_mech'],ratio,'Matched ratio differs')
        summaries[key].update(time_x_mech=ratio,matched_mech_control=control_key,
                             matched_control_qualified=control_key not in failed,endpoint_eligible=eligible)
    require(attempts and p.timestamp(report['started_at'])<=p.timestamp(attempts[0]['started_at'])
            and previous_end<=p.timestamp(report['finished_at']) and
            p.timestamp(durable['command-started']['started_at'])<=p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at'])<=p.timestamp(durable['terminal']['finished_at']),'Timing lifetime differs')
    return dict(schema=SCHEMA,status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        actual_full_native_processes=index,qualified_samples=qualified,skipped_slots=skipped,failed_profiles=list(failed),
        profiles=summaries,repeated_completed_samples=0,planned_rebol_samples=30,planned_matched_mech_samples=30,
        actual_rebol_processes=sum(a['language']=='rebol3' for a in attempts),
        actual_matched_mech_processes=sum(a['language']=='mech' for a in attempts),
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance})],
        kernel_identity_observation_gaps=gaps,qualification=copy.deepcopy(plan['qualification']),
        file_integrity_verified=False,chart_admission=False,runtime_publication_metadata_qualified=False,
        full_timings_qualified=False,runtime_source_equivalence_proven=False,complete_stdout_retained=False,
        full_output_evidence='sampler byte counts/hashes and frozen validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum')


def read_regular(path, limit=64*1024**2):
    path=Path(path);require(path.is_absolute() and path.resolve(strict=True)==path,'Physical evidence path required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Regular evidence file required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd);require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Evidence replaced before read')
        raw=stream.read(limit+1);after=path.lstat()
        require(len(raw)<=limit and stat.S_ISREG(after.st_mode) and
                (held.st_dev,held.st_ino)==(after.st_dev,after.st_ino),'Evidence changed or exceeds bound')
    return raw


def verify_leases(leases):
    for path,stream,identity in leases:
        held=os.fstat(stream.fileno());named=path.lstat()
        require(stat.S_ISREG(named.st_mode) and path.resolve(strict=True)==path and
            (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==identity,'Review lease replaced')


@contextmanager
def regular_lease(path):
    require(path.resolve(strict=True)==path,'Physical original lease required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Regular original lease required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd)
        require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Lease replaced before open')
        yield stream


def source_review(plan, document):
    files={str(v.relative_to(ROOT)) for v in (CONTROLLER,CONTROLLER.with_name('test_rebol_full60.py'),PACKET/'README.md',PACKET/'POLICY.md')}
    dependencies={str(v.relative_to(ROOT)) for v in (QUALIFIER,ROOT/'tools/qualification/elixir_full.py',HELPER,ORIGINAL)}
    require(document['schema']=='rebol-full60-source-review-v1'
        and document['status']=='independent-source-review-complete-native-timing-pending'
        and document['independent_review'] is True and document['full_timing_qualified'] is document['chart_admission'] is False
        and set(document['files'])==files and set(document['dependencies'])==dependencies,'Producer source review differs')
    for name,sha in {**document['files'],**document['dependencies']}.items():
        require(p.digest(sha) and plan['pins'].get(str(ROOT/name))==sha,'Reviewed producer dependency differs')
    require(document['dependencies']['tools/qualification/elixir_full.py']==
            '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'
            and document['dependencies']['tools/qualification/prolog_reconcile.py']==HELPER_SHA
            and document['dependencies']['tools/qualification/rebol_full.py']==ORIGINAL_SHA,'Frozen support differs')


def immutable_final_check(pins, resolutions, result, replay, consumer_check=None):
    fixed_pins=dict(pins);fixed_resolutions=dict(resolutions);fixed_result=encoded(result)
    def unchanged():
        require(all(pins.get(k)==v for k,v in fixed_pins.items()) and
                all(resolutions.get(k)==v for k,v in fixed_resolutions.items()),'Review-owned pin removed or rebound')
        require(encoded(result)==fixed_result,'Yielded reconciliation changed')
    def check():
        unchanged();replay(fixed_pins,fixed_resolutions);unchanged()
        if consumer_check is not None:consumer_check()
        unchanged()
    return check


def load_qualification(plan):
    """Execute only verified entry bytes, then request its exact approved loader."""
    expected=plan['pins'][str(QUALIFIER)]
    qraw=read_regular(QUALIFIER)
    require(p.digest(expected) and digest(qraw)==expected,'Qualification consumer changed')
    entry=types.ModuleType('rebol_full60_qualification_entry');entry.__file__=str(QUALIFIER)
    exec(compile(qraw,str(QUALIFIER),'exec'),entry.__dict__)
    q=entry.load_controller(expected)
    require(q.ROOT==ROOT,'Qualification root differs')
    return q


@contextmanager
def review_context(plan_path, expected_sha, durable_directory, consumer_sha,
                   *, on_exit_failure=None, final_consumer_check=None):
    """Reproduce qualification and ledger while all original leases remain held.

    Inputs are future actual references, never placeholder receipt identities.
    Cleanup handles body, final replay and inherited-helper exit failures. A
    consumer must not claim that a late cleanup still holds a closed mutex.
    """
    plan_path=Path(plan_path);job=Path(durable_directory)
    require(p.digest(expected_sha) and p.digest(consumer_sha) and job==JOB
        and plan_path.is_relative_to(PACKET) and plan_path!=PACKET,'Exact original full60 paths required')
    initial=read_regular(plan_path);require(digest(initial)==expected_sha,'Plan changed')
    plan=p.strict_json(initial);schedule(plan)
    require(digest(read_regular(Path(__file__).resolve()))==consumer_sha,'Reviewed independent consumer changed')
    q=load_qualification(plan)
    cleaned=False;final=lambda:None
    def cleanup():
        nonlocal cleaned
        if not cleaned:
            cleaned=True
            if on_exit_failure is not None:on_exit_failure()
    def finish():final()
    try:
        with ExitStack() as stack:
            leases=[]
            for path in (job/'owner.lock',SUITE):
                stream=stack.enter_context(regular_lease(path))
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                held=os.fstat(stream.fileno());leases.append((path,stream,(held.st_dev,held.st_ino)))
            verify_leases(leases)
            with q.review_context(Path(plan['qualification_manifest']['path']),plan['qualification_manifest']['sha256'],
                    on_exit_failure=cleanup,final_consumer_check=finish) as (admission,held):
                e=held.evidence;same(admission,plan['qualification'],'Actual prerequisite replay differs')
                pins,resolutions=held.pins,held.resolutions
                for name,sha in plan['pins'].items():
                    e.pin(pins,resolutions,name,sha)
                    require(resolutions[name]==plan['resolutions'][name],'Prepared named input resolution differs')
                e.pin(pins,resolutions,plan_path,expected_sha)
                require(e.read_bytes(plan_path)==initial,'Plan changed after locking')
                for path,sha in ((Path(__file__).resolve(),consumer_sha),(HELPER,HELPER_SHA),(r.HELPER,r.HELPER_SHA)):
                    e.pin(pins,resolutions,path,sha)
                document=e.document(plan['source_review'],pins,resolutions);source_review(plan,document)
                controls={key:e.document(ref,pins,resolutions) for key,ref in CONTROL_REFS.items()};check_controls(plan,controls)
                job_inventory=e.inventory(job)[0]
                require(set(job_inventory)=={'owner.lock','request.json','launch.json','worker-started.json',
                    'command-started.json','terminal.json','command.stdout','command.stderr','worker.log'},'Durable artifact membership differs')
                for name,item in job_inventory.items():e.pin(pins,resolutions,job/name,item['sha256'])
                durable={name:e.document(dict(path=str(job/(name+'.json')),
                    sha256=job_inventory[name+'.json']['sha256']),pins,resolutions) for name in
                    ('request','launch','worker-started','command-started','terminal')}
                require(e.read_bytes(job/'command.stderr')==b'','Durable command emitted stderr')
                output=Path(plan['output']);closed=e.inventory(output)[0]
                terminal_path=output/'terminal.json';terminal_sha=closed['terminal.json']['sha256']
                terminal=e.document(dict(path=str(terminal_path),sha256=terminal_sha),pins,resolutions)
                require(terminal['report']==str(output/'report.json'),'Report escaped measured output')
                report=e.document(dict(path=terminal['report'],sha256=terminal['report_sha256']),pins,resolutions)
                available=terminal['available_evidence_pins']
                require({str(output/name) for name in closed}==set(available)|{str(terminal_path)},'Closed output inventory differs')
                for name,sha in available.items():
                    require(Path(name).is_relative_to(output) and '..' not in Path(name).parts,'Artifact escaped output')
                    e.pin(pins,resolutions,name,sha)
                def documents(paths):return {name:e.document(dict(path=name,sha256=available[name]),pins,resolutions)
                                             for name in paths}
                result=reconcile(plan,report,terminal,documents(a['result_path'] for a in report['attempts']),
                    documents(a['supervisor_result_path'] for a in report['attempts']),
                    documents(a['path'] for a in report['independent_supervisors']),durable,str(plan_path),expected_sha)
                fixed_pins=dict(pins);fixed_resolutions=dict(resolutions)
                refs=dict(plan=dict(path=str(plan_path),sha256=expected_sha),
                    report=dict(path=terminal['report'],sha256=terminal['report_sha256']),
                    terminal=dict(path=str(terminal_path),sha256=terminal_sha),
                    durable=dict(path=str(job/'terminal.json'),sha256=job_inventory['terminal.json']['sha256']))
                result.update(status='full60-reconciled-awaiting-runtime-and-publication-review',file_integrity_verified=True,
                    common_mutex_held=True,common_mutex_inode=p.LOCK_INODE,references=refs,**refs,
                    verified_file_pins=dict(sorted(fixed_pins.items())),verified_input_resolutions=dict(sorted(fixed_resolutions.items())),
                    source_evidence=dict(qualification=plan['qualification_manifest'],counts=admission['references']['count_review'],
                        work=admission['references']['work_review'],stages=admission['references']['stages']),
                    runtime_evidence=copy.deepcopy(admission['runtime']))
                def replay(original_pins,original_resolutions):
                    e.verify(original_pins,original_resolutions)
                    same(e.inventory(output)[0],closed,'Closed full60 artifacts changed')
                    same(e.inventory(job)[0],job_inventory,'Durable artifacts changed')
                    verify_leases(leases);e.check_leases(held.leases)
                final=immutable_final_check(pins,resolutions,result,replay,final_consumer_check)
                immutable_final_check(pins,resolutions,result,replay)()
                yield result
            verify_leases(leases)
    except BaseException as error:
        try:cleanup()
        except BaseException as restore_error:
            raise BaseExceptionGroup('Reconciliation and consumer restoration failed',[error,restore_error])
        raise


review_files = review_context
