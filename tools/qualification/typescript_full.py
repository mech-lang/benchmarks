"""Prepare and own the first sixty full-size TypeScript/control timing slots.

Exactly one retained TypeScript source and one matched Mech control per workload,
three fresh process samples each. Saved qualification is reused without native
diagnostics, compilation, warmup, automatic retries or source aliases.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'experiments/typescript/full60-v1'
HELPERS = ROOT/'tools/qualification/elixir_full.py'
HELPERS_SHA = '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'
RECEIPTS = ROOT/'tools/qualification/prolog_reconcile.py'
RECEIPTS_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'


def require(condition, message):
    if not condition: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def cold(path, expected, name):
    raw=Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected,'Frozen helper source changed')
    require(name not in sys.modules,'Unexpected cached helper module')
    module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


helpers=cold(HELPERS,HELPERS_SHA,'typescript_full_shared_policy')
r=cold(RECEIPTS,RECEIPTS_SHA,'typescript_full_independent_receipts')
shared=helpers.shared
merge,new_json,verify=shared.merge,shared.new_json,shared.verify
isolated_failure=shared.isolated_failure
refresh_attempt_accounting=shared.refresh_attempt_accounting
preserve_wrapper_failure=shared.preserve_wrapper_failure
LOCK,PYTHON,PYTHON_SHA,BENCHES=helpers.LOCK,helpers.PYTHON,helpers.PYTHON_SHA,helpers.BENCHES
SUPERVISOR,SUPERVISOR_SHA=helpers.SUPERVISOR,helpers.SUPERVISOR_SHA
FULL,SAMPLER_PINS=helpers.FULL,helpers.SAMPLER_PINS
verify_lock,common_lock,held_lock=helpers.verify_lock,helpers.common_lock,helpers.held_lock
# The native loop/receipt/finalizer below is copied from reviewed scala_full.py
# b9462a71eddd6fbc6ae5eb7a7098995f2184c54178ebc176c187cd9e49d10d13;
# only family labels and TypeScript prerequisite/command routing differ.
CAPTURE = ROOT/'tools/qualification/typescript_single_entry_remaining.py'
CAPTURE_SHA = 'd99f7c994f1e27bcfa7bd8cf75bf08c4fbe237eaf481b97d558df6233796e000'
capture=cold(CAPTURE,CAPTURE_SHA,'typescript_full_saved_capture')
INJECTION_ENV=('NODE_OPTIONS','NODE_PATH','NODE_COMPILE_CACHE','NODE_ICU_DATA','NODE_EXTRA_CA_CERTS',
               'LD_PRELOAD','DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH')
REFS={
 'work':('experiments/typescript/required-work-v1/qualified-work-v1.json','b4c48ede5c375e3f2f1ab37fe4975199ba539bcd06fc4ab3dd93677525ec02f2'),
 'runtime':('experiments/typescript/runtime-metadata-v1/qualified-runtime-metadata-v1.json','4678a7e7ce8cf63834f5e224b5b488a6b914c374f31d87917cd36dcaa4695aa2'),
 'loc':('experiments/typescript/source-units-v1/qualified-source-counts-v1.json','c8e3461eebdfd73f6052debad012345e4ef4206bdaa2f1e916b8cfbb0d00ebef'),
 'pi_plan':('experiments/typescript/single-entry-work-v1/plan-pi-v1.json','96a0ce9449982d5039ca0ac8ec48379339cb7e5a53db67adb3b3a7ac95d7fb87'),
 'pi_report':('experiments/typescript/single-entry-work-v1/run-pi-v1/report.json','fd8f59f43a65a7d2e04b8bff9d9a39b3f3b38ec02f81b237714f4c1558015d73'),
 'pi_terminal':('experiments/typescript/single-entry-work-v1/run-pi-v1/terminal.json','4a5e138b0725c91e759300438a9e150c7827becf345481ea5951bfb1bba02c4a'),
}


def reference(name):
    path,digest=REFS[name];return dict(path=str(ROOT/path),sha256=digest)


def read_ref(ref,pins):
    require(set(ref)=={'path','sha256'} and Path(ref['path']).is_absolute()
            and '..' not in Path(ref['path']).parts,'Exact absolute metadata reference required')
    raw=Path(ref['path']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'Saved metadata changed: '+ref['path'])
    pins.update(merge(pins,{ref['path']:ref['sha256']}))
    return json.loads(raw)


def file_ref(value):
    path=Path(value['path']);path=path if path.is_absolute() else ROOT/path
    require(path.resolve()==path,'Physical referenced file required')
    return dict(path=str(path),sha256=value['sha256'])


def bind_records(value,pins):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            ref=file_ref(value);pins.update(merge(pins,{ref['path']:ref['sha256']}))
        for item in value.values():bind_records(item,pins)
    elif isinstance(value,list):
        for item in value:bind_records(item,pins)


def keyed(rows):
    result={row['id']:row for row in rows}
    require(len(result)==len(rows)==10 and set(result)=={'typescript-'+b+'-v1' for b in BENCHES},
        'Exactly ten distinct retained TypeScript implementations required')
    return result


def validate_evidence(d,compiled):
    work,runtime,loc=d['work'],d['runtime'],d['loc']
    original,counted,reviewed=keyed(compiled['profiles']),keyed(loc['profiles']),keyed(work['profiles'])
    require(work['schema']=='typescript-qualified-required-work-v1'
        and work['status']=='ten-retained-required-work-contracts-qualified'
        and work['source_work_qualified'] is work['required_work_qualified'] is True
        and work['qualified_contracts']==27 and set(work['qualified_profiles'])==set(original)
        and work['bounded_total_cases']==149 and work['bounded_successful_cases']==142 and work['bounded_expected_rejections']==7
        and work['required_work_diagnostic_subject_invocations']==2 and work['capability_listing_invocations']==1
        and work['original_producer_receipts_unchanged'] is work['original_three_command_stage_preserved_failed'] is True
        and work['first_tree_capture_reused_without_rerun'] is work['missing_pi_captured_once'] is True
        and work['old_producer_flags_preserved'] is True,'Complete required-work admission missing')
    require(file_ref(work['evidence']['runtime'])==reference('runtime') and file_ref(work['evidence']['source_counts'])==reference('loc'),
        'Combined admission runtime/count linkage differs')
    require(runtime['schema']=='typescript-runtime-metadata-qualification-v1'
        and runtime['status']=='exact-retained-node-and-declared-system-dependencies-reviewed'
        and runtime['runtime_publication_metadata_qualified'] is runtime['runtime_dependency_closure_qualified'] is True
        and runtime['declared_runtime_dependency_closure_qualified'] is True
        and runtime['actual_loaded_image_inventory_observed'] is runtime['observed_in_each_timed_process'] is False
        and runtime['node']['path']==compiled['node'] and runtime['node']['expected_full_sha256']==capture.b.c.NODE_SHA,
        'Exact runtime or honest dependency scope missing')
    require(runtime['default_runtime_policy']['external_runtime_packages']==[]
        and runtime['default_runtime_policy']['node_options_or_preloads'] is False
        and runtime['default_runtime_policy']['forced_optimization'] is False
        and runtime['default_runtime_policy']['custom_heap_or_gc_flags'] is False,'Qualified runtime policy differs')
    require(loc['schema']=='typescript-canonical-source-owner-review-v1'
        and loc['status']=='ten-authored-source-canonical-counts-qualified'
        and loc['canonical_loc_qualified'] is loc['fixture_expectations_all_passed'] is True
        and loc['formatted_loc_qualified'] is False and loc['formatted_loc'] is None,
        'Typed canonical-only source admission missing')
    for doc in (work,runtime,loc):
        require(doc['full_timings_qualified'] is doc['chart_admission'] is False and doc['benchmark_samples']==0,
            'Pre-timing evidence changed scope')
    for identity,row in original.items():
        owner,proof=counted[identity],reviewed[identity]
        require(row['benchmark']==owner['workload']==proof['benchmark']
            and row['source']==file_ref(owner['source'])['path']==file_ref(proof['source'])['path']
            and row['source_sha256']==owner['source']['sha256']==proof['source']['sha256']==proof['staged_source']['sha256']
            and row['compiled_source']==file_ref(proof['staged_source'])['path']
            and row['javascript']==file_ref(proof['emitted_javascript']) and row['source_map']==file_ref(proof['source_map'])
            and owner['native_ast']==proof['native_ast']
            and owner['complete_nonoverlapping_source_owner_coverage'] is owner['manual_expectation_matches'] is True
            and proof['required_work_qualified'] is proof['source_work_qualified'] is True
            and all(c['qualified'] is True for c in proof['contracts']), 'Typed/source/emitted/count/work binding differs')
    require(sum(len(p['contracts']) for p in reviewed.values())==27,'Required-work coverage changed')
    return original,counted,runtime


def closure(directory,artifacts,extras,pins,closures):
    require(type(artifacts) is dict and artifacts,'Missing prerequisite inventory')
    inventory=copy.deepcopy(artifacts)
    for path,digest in extras:
        path=Path(path);require(path.parent==directory,'Wrong inventory metadata path')
        record=dict(bytes=path.stat().st_size,sha256=digest)
        require(path.name not in inventory or inventory[path.name]==record,'Conflicting metadata inventory')
        inventory[path.name]=record
    pins.update(merge(pins,helpers.artifact_pins(directory,inventory)))
    closures.append(dict(directory=str(directory),artifacts=inventory))


def prerequisites():
    pins={};compiled=capture.s.prerequisites(pins);prior=capture.closed_prior(pins)
    d={name:read_ref(reference(name),pins) for name in REFS}
    original,counted,runtime=validate_evidence(d,compiled);closures=[]
    for name in ('work','runtime','loc'):bind_records(d[name],pins)
    for item in d['work']['evidence'].values():
        # Read the small, exact review documents and bind their underlying files.
        doc=read_ref(file_ref(item),pins);bind_records(doc,pins)
        if 'evidence' in doc and isinstance(doc['evidence'],dict):
            for path,record in doc['evidence'].items():
                if isinstance(record,dict) and 'sha256' in record and 'path' not in record:
                    ref=file_ref(dict(path=path,sha256=record['sha256']));pins.update(merge(pins,{ref['path']:ref['sha256']}))
    pp,report,terminal=d['pi_plan'],d['pi_report'],d['pi_terminal']
    require(pp['controller_sha256']==CAPTURE_SHA and pp['compiled']==compiled and pp['prior_capture']==prior
        and pp['schedule']==[capture.SLOT] and pp['native_processes']==1,
        'Missing-only pi plan differs')
    require(report['status']==terminal['status']==capture.SUCCESS and report['plan_sha256']==reference('pi_plan')['sha256']
        and terminal['report_sha256']==reference('pi_report')['sha256']
        and report['active'] is None and report['integrity_errors']==terminal['integrity_errors']==[]
        and report['native_processes_started']==terminal['native_processes_started']==terminal['capture_count']==1
        and report['registered_commands']==[dict(directory='00-pidigits',pid=2755)]
        and terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==79859134,
        'Closed pi raw capture missing')
    directory=Path(reference('pi_report')['path']).parent
    result=capture.checked_capture(pp,directory/'00-pidigits',2741)
    require(report['captures']==[result] and report['validated_artifacts']['00-pidigits']==capture.s.inventory(directory/'00-pidigits'),
        'Actual pi raw snapshot differs')
    actual=capture.s.inventory(directory,('terminal.json',))
    require(actual==terminal['available_evidence'] and {n:v for n,v in actual.items() if n!='report.json'}==report['artifacts'],
        'Closed pi inventory differs')
    pins.update(merge(pins,pp['pins']))
    for run in [capture.s.PRIOR/'run-v1',capture.b.c.HERE/'run-v1',capture.PACKET/'run-v1',directory]:
        # Exact schemas differ, but each terminal inventories the report and all native files.
        t=json.loads((run/'terminal.json').read_bytes())
        items=t['available_evidence']
        closure(run,items,[(run/'terminal.json',sha(run/'terminal.json'))],pins,closures)
    loc=d['loc'];pins.update(merge(pins,loc['native_prerequisite_pins']))
    replay=read_ref(file_ref(loc['replay']),pins);replay_dir=Path(file_ref(loc['replay'])['path']).parent
    require(len(replay['result_files'])==40 and replay['native_reader_artifact_files']==160,
        'Canonical projection coverage differs')
    pins.update(merge(pins,replay['prerequisite_pins']))
    closure(replay_dir,replay['result_files'],[(file_ref(loc['replay'])['path'],loc['replay']['sha256'])],pins,closures)
    for row in original.values():
        require(pins.get(row['source'])==pins.get(row['compiled_source'])==row['source_sha256']
            and all(pins.get(row[k]['path'])==row[k]['sha256'] for k in ('javascript','source_map')),
            'Typed source, JavaScript or map missing from closure')
    require(pins.get(compiled['node'])==runtime['node']['expected_full_sha256'],'Node binary is not bound')
    pins.update(merge(pins,{str(CAPTURE):CAPTURE_SHA}))
    return original,counted,dict(compiled=compiled,metadata=runtime),pins,closures


def candidate(original,counted,runtime,pins):
    identity,bench=original['id'],original['benchmark'];node=runtime['compiled']['node']
    require(identity==counted['id']=='typescript-'+bench+'-v1','TypeScript profile identity differs')
    require(counted['canonical_loc_qualified'] is True and counted['formatted_loc_qualified'] is False
        and counted['formatted_loc'] is None and type(counted['canonical_loc']) is type(counted['physical_loc']) is int
        and min(counted['canonical_loc'],counted['physical_loc'])>0,'Canonical-only count policy differs')
    require(original['source']==file_ref(counted['source'])['path'] and original['source_sha256']==counted['source']['sha256']
        and pins.get(original['source'])==pins.get(original['compiled_source'])==original['source_sha256']
        and all(pins.get(original[k]['path'])==original[k]['sha256'] for k in ('javascript','source_map'))
        and pins.get(node)==capture.b.c.NODE_SHA,'Retained executable or authored input is unpinned')
    project=Path(original['compiled_source']).parent;native_directory=project.parent
    environment=dict(PATH='/usr/bin:/bin',HOME=str(native_directory/'home'),TMPDIR=str(native_directory/'tmp'),
        LC_ALL='C',LANG='C',TZ='UTC',UV_THREADPOOL_SIZE='8')
    command=[node,original['javascript']['path']]
    if bench not in ('regexredux','revcomp','knucleotide'):command.append('{n}')
    return dict(id=identity,key=identity,benchmark=bench,variant='v1',language='typescript',
        source=original['source'],source_sha256=original['source_sha256'],compiled_source=original['compiled_source'],
        javascript=copy.deepcopy(original['javascript']),source_map=copy.deepcopy(original['source_map']),
        binary=node,binary_sha256=pins[node],command=command,cwd=str(project),runtime_environment=environment,
        maximum_workers=8,source_alias_of=None,optimization_claim=False,
        source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,
        loc=counted['canonical_loc'],canonical_loc=counted['canonical_loc'],formatted_loc=None,physical_loc=counted['physical_loc'],
        physical_inputs=[dict(path=original['source'],sha256=original['source_sha256'],role='application',counted=True)],
        source_count_projection=file_ref(counted['projection']),
        memory_policy='Retained Node/V8 defaults; no custom heap or collector; UV_THREADPOOL_SIZE=8',
        runtime_dependency_scope=runtime['metadata']['qualification_scope'],
        diagnostic_flags=[],runtime_policy_changes=[],chart_admission=False)


def controls(pins):
    rows=helpers.controls(pins)
    for bench,row in rows.items():row['key']=bench+':typescript-full-study:mech-control'
    return rows


def orders_for(bench):
    ids=['typescript-'+bench+'-v1','mech-aot-control'];offset=BENCHES.index(bench)%2
    return [dict(round=i+1,profiles=ids[(i+offset)%2:]+ids[:(i+offset)%2]) for i in range(3)]


def schedule_for(manifests):
    require(set(manifests)==set(BENCHES),'Exactly ten workload manifests required')
    slots=[]
    for bench in BENCHES:
        manifest=manifests[bench];rows=manifest['profiles'];ids=['typescript-'+bench+'-v1','mech-aot-control']
        require([r['id'] for r in rows]==ids and [r['language'] for r in rows]==['typescript','mech']
                and all(r['benchmark']==bench for r in rows),'One real TypeScript source and matched control required')
        require(type(manifest['samples']) is int and manifest['samples']==3 and manifest['orders']==orders_for(bench),
                'Exactly three alternating rounds required')
        keys={r['id']:r['key'] for r in rows}
        slots.extend((bench,o['round'],identity,keys[identity]) for o in manifest['orders'] for identity in o['profiles'])
    require(len(slots)==len(set(slots))==60 and len({s[3] for s in slots})==20,'Full60 schedule differs')
    return slots


def build_draft(output):
    original,counted,runtime,pins,closures=prerequisites();control_rows=controls(pins);manifests={}
    for bench in BENCHES:
        identity='typescript-'+bench+'-v1';size,count,digest=FULL[bench]
        rows=[candidate(original[identity],counted[identity],runtime,pins),control_rows[bench]]
        manifests[bench]=dict(benchmark=bench,profiles=rows,samples=3,size=size,canonical_full_workload=True,
            orders=orders_for(bench),timeout_seconds=21600,supervisor_timeout_seconds=22200,maximum_rss_mib=10240,
            full_output_reference=None if bench=='nbody' else dict(bytes=count,sha256=digest),shared_timing_lock=str(LOCK),
            no_automatic_retry=True,chart_admission=False,retained_subject_compilation_outside_timer=True,
            runtime_and_script_loading_inside_timer=True,runtime_JIT_inside_timer=True,direct_main_invocations_per_sample=1)
    pins=merge(pins,SAMPLER_PINS,{str(HELPERS):HELPERS_SHA,str(helpers.SHARED):helpers.SHARED_SHA,
        str(SUPERVISOR):SUPERVISOR_SHA,str(RECEIPTS):RECEIPTS_SHA,str(r.HELPER):r.HELPER_SHA,
        str(PYTHON.resolve()):PYTHON_SHA,str(Path(__file__).resolve()):sha(__file__),
        str(HERE/'README.md'):sha(HERE/'README.md')})
    return dict(schema='typescript-qualified-retained-full60-v1',status='draft-metadata-only-not-executable',pins_verified=False,
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),repository=str(ROOT),output=str(Path(output).resolve()),
        qualified_work=reference('work'),qualified_source_counts=reference('loc'),qualified_runtime=reference('runtime'),
        runtime_dependency_scope=runtime['metadata']['qualification_scope'],source_work_profiles=10,canonical_loc_profiles=10,
        formatted_loc_profiles=0,formatted_loc_qualified=False,retained_bounded_cases=149,compiler_invocations=0,
        fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,new_native_probes=0,original_files_mutated=False,
        samples=3,typescript_samples=30,matched_mech_samples=30,full_processes=60,schedule=[list(s) for s in schedule_for(manifests)],
        manifests=manifests,pins=pins,prerequisite_artifact_closures=closures,shared_timing_lock=str(LOCK),common_mutex_inode=79859134,
        continuous_common_mutex=True,no_automatic_retry=True,full_timings_qualified=False,chart_admission=False,
        timing_policy='Fresh direct Node process including startup, retained JavaScript loading, tiered JIT, full input, '
            'all work, complete output and shutdown; subject compilation, pin hashing and output validation excluded')


def validate_plan(plan,prepared=False):
    expected=build_draft(plan['output'])
    if prepared:expected.update(status='prepared-awaiting-independent-review',pins_verified=True)
    require(plan==expected,'Plan differs from exact qualification, cohort, closure, schedule or timing policy')


def checked_runtime():
    helpers.checked_runtime()
    require(not any(k in os.environ for k in INJECTION_ENV) and not any(k.startswith('NODE_') for k in os.environ),'Ambient Node/native injection variables must be absent')


def qualified_sample(attempt,manifest,row,fingerprint):
    shared.qualified_sample(attempt,manifest,row,fingerprint)
    require(attempt.get('stderr')=='','Qualified full sample requires empty native stderr')


def load_measurement():
    guard,harness=helpers.load_measurement()
    require(not any(k in harness.compact.ENV for k in INJECTION_ENV) and not any(k.startswith('NODE_') for k in harness.compact.ENV),'Sampler inherited an unqualified Node environment')
    return guard,harness


def verify_artifact_inventories(closures):
    for item in closures:
        directory=Path(item['directory']);paths=list(directory.rglob('*'))
        require(directory.is_dir() and not directory.is_symlink()
                and all(not p.is_symlink() and (p.is_file() or p.is_dir()) for p in paths),'Invalid prerequisite artifact')
        actual={str(p.relative_to(directory)):p.stat().st_size for p in paths if p.is_file()}
        require(actual=={name:r['bytes'] for name,r in item['artifacts'].items()},'Prerequisite artifact inventory changed')


def check_execution_inputs(plan,harness):
    helpers.check_execution_inputs(plan,harness);verify_artifact_inventories(plan['prerequisite_artifact_closures'])
    for manifest in plan['manifests'].values():
        for row in manifest['profiles']:
            if row['language']!='typescript':continue
            require(row['command']==[row['binary'],row['javascript']['path']]+([] if row['benchmark'] in ('regexredux','revcomp','knucleotide') else ['{n}']),
                'Direct retained JavaScript main command changed')
            require(all(Path(row['runtime_environment'][k]).is_dir() for k in ('HOME','TMPDIR')),'Retained working directory missing')


def draft(args):
    require(not args.plan.exists() and not args.output.exists(),'Fresh draft and native output paths required')
    require(not args.plan.resolve().is_relative_to(args.output.resolve()),'Plan cannot lie inside native output')
    plan=build_draft(args.output);new_json(args.plan,plan)
    print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_executions=0,pins_verified=False)),flush=True)


def prepare(args):
    require(not args.plan.exists(),'Prepared plan must be new')
    with common_lock() as lock:
        checked_runtime();pins={}
        plan=read_ref(dict(path=str(args.draft.resolve()),sha256=args.draft_sha256),pins);validate_plan(plan)
        require(not Path(plan['output']).exists() and not args.plan.resolve().is_relative_to(Path(plan['output'])),
                'Fresh native output must remain absent and separate from plan')
        verify(plan['pins']);_,harness=load_measurement();check_execution_inputs(plan,harness)
        plan.update(status='prepared-awaiting-independent-review',pins_verified=True);verify_lock(lock);new_json(args.plan,plan)
        print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),full_processes=60,native_executions=0)),flush=True)


def initial_rows(plan):
    return {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],measurement_status='pending')
            for manifest in plan['manifests'].values() for row in manifest['profiles']}


def summarize(rows,manifest):
    group=[rows[row['key']] for row in manifest['profiles']]
    if not all(len(row['samples_seconds'])==3 or row.get('full_failure') for row in group):return False
    control=next(row for row in group if row['language']=='mech')
    for row in group:
        if not row.get('full_failure'):
            row.update(median_seconds=statistics.median(row['samples_seconds']),sample_stdev_seconds=statistics.stdev(row['samples_seconds']))
    for row in group:
        row['time_x_mech']=(row['median_seconds']/control['median_seconds']
            if not row.get('full_failure') and not control.get('full_failure') else None)
        row['matched_mech_control']=control['key'];row['matched_mech_source_sha256']=control['source_sha256']
    return True


def attempt_paths(output,attempt):
    stem=f'{attempt["attempt"]:03d}-{attempt["id"]}'
    return (output/'attempts'/(stem+'.json'),output/'attempts'/(stem+'.supervisor.json'),output/'outer-supervisor'/(stem+'.json'))


def check_attempt(output,attempt,slot,row,manifest,pins,parent):
    paths=attempt_paths(output,attempt)
    require([attempt['result_path'],attempt['supervisor_result_path']]==[str(p) for p in paths[:2]],'Receipt escaped native output')
    raw_bytes=[path.read_bytes() for path in paths]
    raw,supervised,outer=[r.p.strict_json(value) for value in raw_bytes]
    provenance=[];r.check_attempt(attempt,raw,supervised,list(slot),row,manifest,pins,provenance)
    gaps=r.check_outer(outer,attempt,parent)
    # Hash the actual bytes decoded above, then require they remain current.
    snapshot={str(path):hashlib.sha256(value).hexdigest() for path,value in zip(paths,raw_bytes)}
    require(all(sha(path)==digest for path,digest in snapshot.items()),'Receipt changed during independent validation')
    return snapshot,provenance,gaps


def record_attempt(supervisor,guard,harness,report,row,manifest,slot,pins,snapshots,attempt):
    """Persist the returned native result and derived state as one masked transfer."""
    with supervisor.lifecycle_atomic():
        report['attempts'].append(attempt);report['active']=None;row['attempts'].append(attempt['attempt'])
        refresh_attempt_accounting(report);guard.save(guard.REPORT,report)
        original=next(value for value in manifest['profiles'] if value['key']==row['key'])
        captured,provenance,gaps=check_attempt(guard.OUT,attempt,slot,original,manifest,pins,os.getpid())
        snapshots.update(merge(snapshots,captured))
        report['descriptive_provenance'].extend(provenance);report['kernel_identity_observation_gaps'].extend(gaps)
        if attempt['qualified']:
            qualified_sample(attempt,manifest,row,harness.execution_fingerprint(row))
            row['samples_seconds'].append(attempt['seconds']);row['sample_validation'].append(attempt['validation'])
            row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
        elif isolated_failure(guard,attempt):
            row['measurement_status']='failed-full-workload';row['full_failure']=dict(attempt)
            report['isolated_failed_profiles'].append(row['key'])
        else:row['measurement_status']='stopped-unqualified'
        if summarize(report['programs'],manifest) and row['benchmark'] not in report['completed_benchmarks']:
            report['completed_benchmarks'].append(row['benchmark'])
        report['validated_attempt_artifacts']=dict(snapshots)
        refresh_attempt_accounting(report);guard.save(guard.REPORT,report)
        require(attempt['qualified'] or row.get('full_failure'),'Integrity/environment/ownership failure; no retry')


def check_success_ledger(plan,report):
    slots=schedule_for(plan['manifests']);rows=initial_rows(plan);failed=[];index=0;skips=[]
    for bench,round_index,identity,key in slots:
        row=rows[key]
        if row.get('full_failure'):
            skips.append(dict(benchmark=bench,round=round_index,id=identity,key=key));continue
        require(index<len(report['attempts']),'Missing native slot')
        attempt=report['attempts'][index];index+=1
        require(attempt['attempt']==index and [attempt[k] for k in ('benchmark','round','id','key')]==
                [bench,round_index,identity,key],'Missing, duplicated or reordered native slot')
        row['attempts'].append(index)
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']);row['sample_validation'].append(attempt['validation'])
            row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
        else:row.update(full_failure=attempt,measurement_status='failed-full-workload');failed.append(key)
    require(index==len(report['attempts']) and skips==report['skipped_failed_profile_slots'],'Extra attempt or invalid skip')
    require(all(summarize(rows,manifest) for manifest in plan['manifests'].values()),'Incomplete workload group')
    require(rows==report['programs'] and failed==report['isolated_failed_profiles'],'Sample summaries do not replay exact ledger')
    require(report['active'] is None and report['completed_benchmarks']==BENCHES
            and report['native_launch_unconfirmed_attempts']==[] and report['full_performance_runs']==index
            and report['qualified_samples']==sum(len(row['samples_seconds']) for row in rows.values()),'Native/sample accounting differs')


def finish(plan,report,pins,snapshots,guard,harness,lock):
    """Called with interrupt signals blocked and the original mutex still held."""
    errors=[]
    def problem(error,path=None):
        errors.append(dict(path=path,error=str(error) or type(error).__name__,error_type=type(error).__name__))
    for path,digest in merge(pins,snapshots).items():
        try:require(sha(path)==digest,'Pinned or validated artifact changed')
        except BaseException as error:problem(error,path)
    refresh_attempt_accounting(report)
    try:
        check_execution_inputs(plan,harness);verify_lock(lock)
        require(report['active'] is None,'Supervisor cleanup left active native state')
        if report['status'] in ('complete','complete-with-unqualified-profiles'):check_success_ledger(plan,report)
        expected=set();previous=None
        for attempt in report['attempts']:
            if attempt.get('wrapper_supervisor_failure'):
                require(report['status']=='stopped-unqualified','Wrapper failure in completed cohort');continue
            slot=[attempt[k] for k in ('benchmark','round','id','key')]
            require(tuple(slot) in schedule_for(plan['manifests']),'Attempt outside reviewed full60 schedule')
            manifest=plan['manifests'][attempt['benchmark']];row=next(v for v in manifest['profiles'] if v['key']==attempt['key'])
            captured,_,_=check_attempt(guard.OUT,attempt,slot,row,manifest,pins,os.getpid())
            require(all(snapshots.get(path)==digest for path,digest in captured.items()),'Missing or changed validated snapshot')
            begin,end=r.p.timestamp(attempt['started_at']),r.p.timestamp(attempt['finished_at'])
            require(previous is None or previous<=begin,'Native intervals overlap');previous=end;expected.update(captured)
        require(set(snapshots)==expected,'Unowned validated artifact')
        if report['status'] in ('complete','complete-with-unqualified-profiles'):
            require(r.inventory(guard.OUT)==expected|{str(guard.REPORT)},'Unexpected or missing completed-run artifact')
            outer_refs=[dict(path=str(attempt_paths(guard.OUT,a)[2]),sha256=snapshots[str(attempt_paths(guard.OUT,a)[2])],status='returned')
                        for a in report['attempts']]
            require(report['independent_supervisors']==outer_refs,'Independent supervisor inventory differs')
    except BaseException as error:problem(error)
    report['pins_unchanged_at_end']=not errors;report['validated_attempt_artifacts']=dict(snapshots)
    if errors:report.update(status_before_terminal_integrity_failure=report['status'],status='failed-terminal-integrity',terminal_integrity_errors=errors)
    guard.save(guard.REPORT,report)
    try:available={path:sha(path) for path in r.inventory(guard.OUT)}
    except BaseException as error:problem(error);available={str(guard.REPORT):sha(guard.REPORT)}
    for path,digest in merge(pins,snapshots).items():
        try:
            require(sha(path)==digest,'Prerequisite or snapshot changed during terminal inventory')
            if path in snapshots:require(available.get(path)==digest,'Snapshot changed during terminal inventory')
        except BaseException as error:problem(error,path)
    try:
        require(r.inventory(guard.OUT)==set(available),'Run inventory changed before terminal')
        require(available.get(str(guard.REPORT))==sha(guard.REPORT),'Report changed during terminal inventory')
        check_execution_inputs(plan,harness);verify_lock(lock)
    except BaseException as error:problem(error)
    if errors:
        report.update(status='failed-terminal-integrity',terminal_integrity_errors=errors,pins_unchanged_at_end=False)
        guard.save(guard.REPORT,report);available[str(guard.REPORT)]=sha(guard.REPORT)
    new_json(guard.OUT/'terminal.json',dict(schema='typescript-full60-terminal-v1',status=report['status'],
        report=str(guard.REPORT),report_sha256=sha(guard.REPORT),prerequisite_pins=pins,available_evidence_pins=available,
        validated_attempt_artifacts=dict(snapshots),integrity_errors=errors,common_mutex_held=True,common_mutex_inode=79859134,
        common_mutex_held_continuously=True,full_performance_runs=report['full_performance_runs'],saved_attempts=len(report['attempts']),
        registered_native_attempts=report['registered_native_attempts'],native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
        qualified_samples=report['qualified_samples'],skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,
        original_files_mutated=False,full_timings_qualified=False,chart_admission=False))
    verify_lock(lock);require(not errors,'Terminal integrity failed; actual samples preserved')


def run_locked(args, live_lock):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan, prepared=True)
    output = Path(plan['output'])
    require(not output.exists(), 'No overwrite, implicit resume, or repeated sample')
    output.parent.mkdir(parents=True,exist_ok=True)
    # The suite lease also excludes another cohort using a different output.
    lease_path = ROOT / 'experiments/typescript/typescript-full60.owner.lock'
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with held_lock(live_lock) as lock:
            verify(plan['pins'])
            guard,harness = load_measurement()
            check_execution_inputs(plan, harness)
            supervisor = cold(SUPERVISOR, SUPERVISOR_SHA, 'typescript_full60_independent_supervisor')
            verify_lock(lock)
            schedule = schedule_for(plan['manifests'])
            require([list(slot) for slot in schedule] == plan['schedule'], 'Reviewed schedule changed')
            pins = merge(plan['pins'],{str(args.plan.resolve()):args.plan_sha256})
            manifests = {bench:dict(manifest,pins=pins) for bench,manifest in plan['manifests'].items()}
            for bench,manifest in manifests.items():
                require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                        and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                        and manifest['maximum_rss_mib'] == 10240,
                        'Workload or resource policy changed')
            output.mkdir()
            guard.OUT,guard.REPORT = output,output/'report.json'
            harness.install_interrupt_handlers()
            rows = initial_rows(plan)
            snapshots = {}
            require(len(rows) == 20,'Full cohort changed')
            report = dict(schema='typescript-full60-results-v1',status='running',started_at=guard.now(),supervisor=guard.identity(os.getpid()),
                plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,programs=rows,attempts=[],active=None,
                benchmark_order=BENCHES,completed_benchmarks=[],sample_count=3,full_performance_runs=0,
                skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=str(LOCK),
                source_work_profiles=10,canonical_loc_profiles=10,formatted_loc_profiles=0,
                planned_typescript_samples=30,planned_matched_mech_samples=30,full_timings_qualified=False,
                chart_admission=False,no_automatic_retry=True,validated_attempt_artifacts={},
                descriptive_provenance=[],kernel_identity_observation_gaps=[])
            refresh_attempt_accounting(report)
            guard.save(guard.REPORT,report)
        try:
            for bench,round_index,identifier,key in schedule:
                row,manifest = rows[key],manifests[bench]
                if row.get('full_failure'):
                    with supervisor.lifecycle_atomic():
                        report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                        guard.save(guard.REPORT,report)
                    continue
                with held_lock(live_lock) as lock:
                    verify(pins)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    check_execution_inputs(plan, harness)
                    verify_lock(lock)
                    print('TYPESCRIPT FULL',bench,round_index,identifier,manifest['size'],flush=True)
                    before=len(report['attempts'])
                    try:
                        attempt=supervisor.one_attempt(guard,harness,row,manifest,report,round_index,lock.fileno())
                        record_attempt(supervisor,guard,harness,report,row,manifest,
                                       (bench,round_index,identifier,key),pins,snapshots,attempt)
                    except BaseException as error:
                        with supervisor.lifecycle_atomic():
                            if len(report['attempts'])==before:
                                preserve_wrapper_failure(guard,report,row,round_index,error)
                        raise
                    verify_lock(lock)
            require(len(report['attempts'])+len(report['skipped_failed_profile_slots']) == 60
                    and len(report['completed_benchmarks']) == 10,'Incomplete full60 accounting')
            require(report['full_performance_runs'] == len(report['attempts']),'Native attempt accounting mismatch')
            check_success_ledger(plan,report)
            with supervisor.lifecycle_atomic():
                report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                              finished_at=guard.now())
        except BaseException as error:
            with supervisor.lifecycle_atomic():
                report.update(status='stopped-unqualified',finished_at=guard.now(),error=str(error) or type(error).__name__,
                              error_type=type(error).__name__)
                (output/'error.log').write_text(traceback.format_exc())
                guard.save(guard.REPORT,report)
            raise
        finally:
            with supervisor.lifecycle_atomic():
                with held_lock(live_lock) as lock:
                    finish(plan,report,pins,snapshots,guard,harness,lock)


def run(args):
    # A single inherited descriptor remains locked through environment waits,
    # all 60 slots, every cleanup and the final evidence/terminal write.
    with common_lock() as lock:
        run_locked(args, lock)




def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_subparsers(dest='mode',required=True)
    draft_parser=modes.add_parser('draft',help='Read saved metadata only; no native execution or full runtime hashing')
    draft_parser.add_argument('--plan',type=Path,required=True)
    draft_parser.add_argument('--output',type=Path,required=True)
    prep=modes.add_parser('prepare',help='Verify the reviewed draft and flat closure under the timing mutex')
    prep.add_argument('--draft',type=Path,required=True)
    prep.add_argument('--draft-sha256',required=True)
    prep.add_argument('--plan',type=Path,required=True)
    execute=modes.add_parser('run',help='Execute exactly the independently reviewed prepared plan')
    execute.add_argument('--plan',type=Path,required=True)
    execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==PYTHON.resolve(),'Use retained Python -I -S -B')
    {'draft':draft,'prepare':prepare,'run':run}[args.mode](args)


if __name__=='__main__':main()
