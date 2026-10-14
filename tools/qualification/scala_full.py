"""Prepare and own the first sixty full-size Scala/control timing slots.

Exactly one retained Scala source and one matched Mech control per workload,
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
HERE = ROOT/'experiments/scala/full60-v1'
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


helpers=cold(HELPERS,HELPERS_SHA,'scala_full_shared_policy')
r=cold(RECEIPTS,RECEIPTS_SHA,'scala_full_independent_receipts')
shared=helpers.shared
merge,new_json,verify=shared.merge,shared.new_json,shared.verify
isolated_failure=shared.isolated_failure
refresh_attempt_accounting=shared.refresh_attempt_accounting
preserve_wrapper_failure=shared.preserve_wrapper_failure
LOCK,PYTHON,PYTHON_SHA,BENCHES=helpers.LOCK,helpers.PYTHON,helpers.PYTHON_SHA,helpers.BENCHES
SUPERVISOR,SUPERVISOR_SHA=helpers.SUPERVISOR,helpers.SUPERVISOR_SHA
FULL,SAMPLER_PINS=helpers.FULL,helpers.SAMPLER_PINS
verify_lock,common_lock,held_lock=helpers.verify_lock,helpers.common_lock,helpers.held_lock
FLAGS=['-XX:ActiveProcessorCount=8','-Xms64m','-Xmx8g','-XX:+UseG1GC']
INJECTION_ENV=('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','LD_PRELOAD',
               'DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH')
REFS={
    'work':('experiments/scala/single-entry-work-v1/actual-instruction-review-v1.json','32540d68a39aaeac3676ea5573cb48d7df2dbcdaea80e865ab30e7ef7c6c0cfc'),
    'tree_peer':('experiments/scala/single-entry-work-v1/tree-peer-review-v1.json','8f554b4cf43c801daacc790779948f67bdbc00f07487f873e61733d7d0a974e3'),
    'pi_peer':('experiments/scala/single-entry-work-v1/pi-peer-review-v1.json','2a32bc0a078f204657daea99afbb0b89ae9a40efbb483a9308cfeda5398b5c98'),
    'static':('experiments/scala/compiled-applications-v1/required-work-review-v1.json','c71af7c1070e2c17df3e5c00148edc550bddfefba4a0d27b76084367e6574510'),
    'compiled_report':('experiments/scala/compiled-applications-v1/run-v1/report.json','55e266372bf64595430fc83aeb47dd68149075ff53d9d0d8b9627bf21c14f782'),
    'compiled_terminal':('experiments/scala/compiled-applications-v1/run-v1/terminal.json','ccd911b9e313c085e86466ff9cd6bdf5e7c5a1fdf4617b54efc0a21edb3f2522'),
    'compiled_review':('experiments/scala/compiled-applications-v1/independent-compilation-plan-review-v1.json','4688c8180e3149515ef0cdfdcc3f6b0373c7cf8f717001e075708d735b2108c3'),
    'bounded_plan':('experiments/scala/bounded-v1/plan-v1.json','8dcc5342826524ef290ee0ed55e3d77fec89d50642fb82f51ece405ba67bacbc'),
    'bounded_report':('experiments/scala/bounded-v1/run-v1/report.json','a5d794e06c554f2d89fe4430f55eefc9ebfa03e3a35f55c512ff5816d7c774b8'),
    'bounded_terminal':('experiments/scala/bounded-v1/run-v1/terminal.json','e85b8306e290deb148f41a02ae6ad4e3ed516ba0d364d249720406b8ac807161'),
    'bounded_review':('experiments/scala/bounded-v1/independent-closed-artifact-review-v1.json','feef20e589c177bab59999e94539d2283ce3ba49d52837b69f6175b3130585f8'),
    'capture_plan':('experiments/scala/single-entry-work-v1/plan-v1.json','f508fb2a0aef9a06a69219e322847a152142b0a8f5ea4b9a2fe3c8abc96dd1a2'),
    'capture_report':('experiments/scala/single-entry-work-v1/run-v1/report.json','0fc2ed6759ee95bb2ff375e83ffe6be57b1fce745cb83cd3d212ae6a09d3507a'),
    'capture_terminal':('experiments/scala/single-entry-work-v1/run-v1/terminal.json','06aed95539f79eae8d3188494820268526d34612325b5fed43849b22a52da1c6'),
    'loc':('experiments/scala/source-counts-v1/canonical-owner-review-v1/qualified-source-counts-v1.json','f5c706f72cdae4bf31cc5f19ff7fec2ea0ddeba2f05ec16571868c343028c0d0'),
    'projection_review':('experiments/scala/source-counts-v1/canonical-owner-review-v1/results-v1/review.json','25fde663cc9a774fd0d6668434919c1014a8984478c180b3a9bed00f42c69869'),
    'parser_report':('experiments/scala/source-counts-v1/native-token-capture-v2/report.json','a2b5a96c833d7c16e73c6a070e863d832d051048b4d87611543b4dbc17c97287'),
    'parser_terminal':('experiments/scala/source-counts-v1/native-token-capture-v2/terminal.json','7b336f1138cffe20047cd438f84621f4635904c19fec3d68d1a12b25f12f6b4f'),
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


def keyed(rows):
    result={row['id']:row for row in rows}
    require(len(rows)==len(result)==10 and set(result)=={'scala-'+b+'-jvm-v1' for b in BENCHES},
            'Exactly ten distinct retained Scala implementations required')
    return result


def bound_ref(actual,name):
    expected=reference(name);path=Path(actual['path'])
    require(str(path if path.is_absolute() else ROOT/path)==expected['path']
            and actual['sha256']==expected['sha256'],'Qualification references another artifact: '+name)


def validate_evidence(d):
    """Validate only saved small metadata; no native work or runtime-file reads."""
    work,loc,cp,bp=d['work'],d['loc'],d['capture_plan'],d['bounded_plan']
    require(work['schema']=='scala-actual-required-work-review-v1'
            and work['status']=='tree-allocation-and-lifetime-reviewed-pi-peer-reviewed'
            and work['source_work_qualified'] is True and work['full_timings_qualified'] is work['chart_admission'] is False
            and work['producer_artifacts_unchanged'] is work['closed_artifact_inventory_exact'] is True
            and work['benchmark_samples']==work['native_executions_by_review']==0
            and sorted(work['qualified_profiles'])==sorted(keyed(d['compiled_report']['profiles'])),
            'Independent ten-profile required-work admission missing')
    for field,name in [('producer_plan','capture_plan'),('producer_report','capture_report'),
            ('producer_terminal','capture_terminal'),('pidigits_peer_review','pi_peer'),
            ('prior_static_required_work_review','static'),('prior_149_case_closed_artifact_review','bounded_review')]:
        bound_ref(work[field],name)
    require(d['pi_peer']['both_division_calls_dominate_comparison'] is True
            and d['pi_peer']['complete_hotspot_log'] is True and d['pi_peer']['caller_execution_path']=='interpreted-main'
            and d['tree_peer']['status']=='no-concrete-tree-evidence-blocker','Independent tree/pi work decisions differ')
    bound_ref(d['tree_peer']['review'],'work')
    require(loc['schema']=='scala-qualified-source-counts-v1'
            and loc['status']=='ten-retained-canonical-source-counts-qualified'
            and loc['canonical_loc_qualified'] is loc['canonical_LOC_admitted'] is loc['manual_owner_review_replayed'] is True
            and loc['formatted_loc_qualified'] is False and loc['formatted_loc'] is None
            and loc['full_timings_qualified'] is loc['chart_admission'] is False,'Canonical source admission missing')
    require(cp['schema']=='scala-two-single-entry-plan-v1' and cp['runtime_flags']==FLAGS
            and cp['native_processes']==2 and cp['compiler_invocations']==cp['automatic_retries']==0,
            'Native execution-path policy changed')
    require(cp['compiled']==bp['compiled'],'Bounded and diagnostic classes/runtime differ')
    require(cp['bounded_prerequisite']['cases_replayed']==149 and cp['bounded_prerequisite']['successful_cases']==142
            and cp['bounded_prerequisite']['rejected_cases']==7,'Incomplete bounded prerequisite')
    for kind in ('plan','report','terminal'):
        bound_ref(dict(path=cp['bounded_prerequisite'][kind],sha256=cp['bounded_prerequisite'][kind+'_sha256']),'bounded_'+kind)
    compiled=cp['compiled'];original=keyed(compiled['profiles']);counted=keyed(loc['profiles'])
    actual=keyed(d['compiled_report']['profiles']);static=keyed(d['static']['profiles'])
    require(d['compiled_report']['status']==d['compiled_terminal']['status']=='ten-applications-compiled-and-inspected-awaiting-native-conformance'
            and d['compiled_report']['active'] is None and d['compiled_report']['integrity_errors']==[]
            and d['compiled_report']['native_processes_started']==20
            and d['compiled_report']['compiler_processes_started']==d['compiled_report']['bytecode_reader_processes_started']==10,
            'Original compilation did not close')
    for kind in ('report','terminal'):
        bound_ref(dict(path=compiled[kind],sha256=compiled[kind+'_sha256']),'compiled_'+kind)
    for name,count,status in [('compiled',20,'ten-applications-compiled-and-inspected-awaiting-native-conformance'),
            ('bounded',149,'all149-bounded-output-contracts-passed-awaiting-required-work-review'),
            ('capture',2,'two-native-captures-complete-awaiting-instruction-review'),
            ('parser',2,'revised-eighty-source-transports-retained-awaiting-independent-review')]:
        report,terminal=d[name+'_report'],d[name+'_terminal']
        require(report['status']==terminal['status']==status and report['active'] is None
                and report['integrity_errors']==[] and report['native_processes_started']==terminal['native_processes_started']==count
                and terminal['report_sha256']==reference(name+'_report')['sha256'],'Unclosed prerequisite: '+name)
        require(report['chart_admission'] is False and report['benchmark_samples']==0,'Producer scope changed')
        if name in ('bounded','capture'):
            require(terminal['common_mutex_held'] is True and terminal['common_mutex_inode']==79859134
                    and terminal['integrity_errors']==[],'Prerequisite integrity/mutex error')
            bound_ref(dict(path=report['plan'],sha256=report['plan_sha256']),name+'_plan')
    br=d['bounded_review']
    require(br['status']=='all149-outputs-and-lifecycles-replayed' and br['cases_verified']==149
            and br['successful_outputs_verified']==142 and br['expected_rejections_verified']==7
            and all(br[k] is True for k in ('exact_case_order_preserved','serial_lifetimes_verified',
                'all_original_process_receipts_preserved','all_native_children_reaped','all_process_groups_closed','all_output_bytes_rechecked')),
            'Independent bounded output/lifecycle replay missing')
    for kind in ('plan','report','terminal'):bound_ref(br['bounded_'+kind],'bounded_'+kind)
    require(d['bounded_report']['qualified_cases']==149 and d['bounded_report']['successful_cases']==142
            and d['bounded_report']['rejected_cases']==7 and d['bounded_report']['process_receipt_errors']==[],
            'Bounded case coverage differs')
    for identity,row in original.items():
        counted_row,measured,reviewed=counted[identity],actual[identity],static[identity]
        require(row['benchmark']==counted_row['benchmark']==measured['benchmark']==reviewed['benchmark']
                and row['source_sha256']==counted_row['source_sha256']==measured['source_sha256']==reviewed['source']['sha256']
                and row['source']==counted_row['source']==str(ROOT/reviewed['source']['path'])
                and row['compiled_source']==measured['source']==str(ROOT/reviewed['compiled_source']['path'])
                and row['artifacts']==measured['artifacts'] and row['main_owner']==measured['main_owner']=='Main'
                and row['runtime_classpath']==measured['runtime_classpath']
                and reviewed['static_workload_contracts_passed'] is True
                and all(c['static_result']=='passed' for c in reviewed['contracts']),'Source/class/work/count identity differs')
        require({a['path']:a['sha256'] for a in row['artifacts']}==
                {str(ROOT/a['path']):a['sha256'] for a in reviewed['class_artifacts']},'Reviewed classes differ')
    require(len(d['capture_report']['profiles'])==2
            and {r['benchmark'] for r in cp['profiles']}=={'binarytrees','pidigits'},'Targeted work captures differ')
    for row in cp['profiles']:require(row==original[row['id']],'Capture used another implementation')
    return original,counted,compiled


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
    pins={};d={name:read_ref(reference(name),pins) for name in REFS}
    original,counted,compiled=validate_evidence(d);closures=[]
    for name in ('compiled_report','bounded_plan','bounded_report','capture_plan','capture_report','parser_report'):
        pins.update(merge(pins,d[name]['pins']))
    pins.update(merge(pins,d['loc']['evidence_pins']))
    for name in ('compiled','bounded','capture','parser'):
        report,terminal=d[name+'_report'],d[name+'_terminal'];directory=Path(reference(name+'_report')['path']).parent
        artifacts=terminal['available_evidence'] if name in ('bounded','capture') else report['artifacts']
        closure(directory,artifacts,[(reference(name+'_'+k)['path'],reference(name+'_'+k)['sha256']) for k in ('report','terminal')],pins,closures)
    projection=d['projection_review'];directory=Path(reference('projection_review')['path']).parent
    require(projection['input_replay']['report_sha256']==reference('parser_report')['sha256']
            and projection['input_replay']['native_pairs']==80 and len(projection['artifacts'])==51,'Source projection closure differs')
    closure(directory,projection['artifacts'],[(reference('projection_review')['path'],reference('projection_review')['sha256'])],pins,closures)
    for row in counted.values():
        require(pins.get(row['projection'])==row['projection_sha256'],'Canonical projection unbound')
    for row in original.values():
        require(pins.get(row['source'])==pins.get(row['compiled_source'])==row['source_sha256']
                and all(pins.get(a['path'])==a['sha256'] for a in row['artifacts']),'Authored/class input missing from closure')
    return original,counted,compiled,pins,closures


def candidate(original,counted,runtime,pins):
    identity,bench=original['id'],original['benchmark'];java=runtime['java']
    require(identity==counted['id']=='scala-'+bench+'-jvm-v1','Scala profile identity differs')
    require(counted['canonical_loc_qualified'] is True and counted['formatted_loc_qualified'] is False
            and counted['formatted_loc'] is None and type(counted['canonical_loc']) is type(counted['physical_loc']) is int
            and min(counted['canonical_loc'],counted['physical_loc'])>0,'Canonical-only count policy differs')
    classes=Path(original['classes']);directory=classes.parent
    artifacts=original['artifacts']
    require(original['source']==counted['source'] and original['source_sha256']==counted['source_sha256']
            and pins.get(original['source'])==pins.get(original['compiled_source'])==original['source_sha256']
            and artifacts and len({a['relative_path'] for a in artifacts})==len(artifacts),
            'Counted authored input or generated class inventory differs')
    for artifact in artifacts:
        part=Path(artifact['relative_path'])
        require(not part.is_absolute() and '..' not in part.parts and artifact['path']==str(classes/part)
                and pins.get(artifact['path'])==artifact['sha256'],'Generated class is not pinned in its classpath')
    libraries=runtime['runtime_libraries']
    require(len(libraries)==2 and [Path(p).name for p in libraries]==['scala3-library_3-3.10.0.jar','scala-library-3.10.0.jar']
            and original['runtime_classpath']==os.pathsep.join([str(classes),*libraries])
            and all(p in pins for p in [java,*libraries]),'Only pinned retained runtime jars are allowed')
    environment=dict(PATH='/usr/bin:/bin',HOME=str(directory/'home'),TMPDIR=str(directory/'tmp')+'/',
                     JAVA_HOME=str(Path(java).parent.parent),LC_ALL='C',LANG='C',TZ='UTC',CLASSPATH='')
    command=[java,*FLAGS,'-Duser.home='+environment['HOME'],'-Djava.io.tmpdir='+environment['TMPDIR'],
             '-cp',original['runtime_classpath'],'Main']
    if bench not in ('regexredux','revcomp','knucleotide'):command.append('{n}')
    return dict(id=identity,key=identity,benchmark=bench,variant='jvm-v1',language='scala',
        source=original['source'],source_sha256=original['source_sha256'],compiled_source=original['compiled_source'],
        binary=java,binary_sha256=pins[java],command=command,cwd=str(directory),runtime_environment=environment,
        maximum_workers=8,classes=str(classes),class_artifacts=copy.deepcopy(original['artifacts']),
        runtime_libraries=copy.deepcopy(libraries),main_owner='Main',source_alias_of=None,optimization_claim=False,
        source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,
        loc=counted['canonical_loc'],canonical_loc=counted['canonical_loc'],formatted_loc=None,physical_loc=counted['physical_loc'],
        physical_inputs=[dict(path=original['source'],sha256=original['source_sha256'],role='application',counted=True)],
        source_count_projection=dict(path=counted['projection'],sha256=counted['projection_sha256']),
        memory_policy='Retained -Xms64m -Xmx8g G1; ActiveProcessorCount=8; default tiered compilation',
        diagnostic_flags=[],runtime_policy_changes=[],chart_admission=False)


def controls(pins):
    rows=helpers.controls(pins)
    for bench,row in rows.items():row['key']=bench+':scala-full-study:mech-control'
    return rows


def orders_for(bench):
    ids=['scala-'+bench+'-jvm-v1','mech-aot-control'];offset=BENCHES.index(bench)%2
    return [dict(round=i+1,profiles=ids[(i+offset)%2:]+ids[:(i+offset)%2]) for i in range(3)]


def schedule_for(manifests):
    require(set(manifests)==set(BENCHES),'Exactly ten workload manifests required')
    slots=[]
    for bench in BENCHES:
        manifest=manifests[bench];rows=manifest['profiles'];ids=['scala-'+bench+'-jvm-v1','mech-aot-control']
        require([r['id'] for r in rows]==ids and [r['language'] for r in rows]==['scala','mech']
                and all(r['benchmark']==bench for r in rows),'One real Scala source and matched control required')
        require(type(manifest['samples']) is int and manifest['samples']==3 and manifest['orders']==orders_for(bench),
                'Exactly three alternating rounds required')
        keys={r['id']:r['key'] for r in rows}
        slots.extend((bench,o['round'],identity,keys[identity]) for o in manifest['orders'] for identity in o['profiles'])
    require(len(slots)==len(set(slots))==60 and len({s[3] for s in slots})==20,'Full60 schedule differs')
    return slots


def build_draft(output):
    original,counted,runtime,pins,closures=prerequisites();control_rows=controls(pins);manifests={}
    for bench in BENCHES:
        identity='scala-'+bench+'-jvm-v1';size,count,digest=FULL[bench]
        rows=[candidate(original[identity],counted[identity],runtime,pins),control_rows[bench]]
        manifests[bench]=dict(benchmark=bench,profiles=rows,samples=3,size=size,canonical_full_workload=True,
            orders=orders_for(bench),timeout_seconds=21600,supervisor_timeout_seconds=22200,maximum_rss_mib=10240,
            full_output_reference=None if bench=='nbody' else dict(bytes=count,sha256=digest),shared_timing_lock=str(LOCK),
            no_automatic_retry=True,chart_admission=False,retained_subject_compilation_outside_timer=True,
            runtime_and_class_loading_inside_timer=True,runtime_JIT_inside_timer=True,direct_main_invocations_per_sample=1)
    pins=merge(pins,SAMPLER_PINS,{str(HELPERS):HELPERS_SHA,str(helpers.SHARED):helpers.SHARED_SHA,
        str(SUPERVISOR):SUPERVISOR_SHA,str(RECEIPTS):RECEIPTS_SHA,str(r.HELPER):r.HELPER_SHA,
        str(PYTHON.resolve()):PYTHON_SHA,str(Path(__file__).resolve()):sha(__file__),
        str(HERE/'README.md'):sha(HERE/'README.md')})
    return dict(schema='scala-qualified-retained-full60-v1',status='draft-metadata-only-not-executable',pins_verified=False,
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),repository=str(ROOT),output=str(Path(output).resolve()),
        qualified_work=reference('work'),qualified_source_counts=reference('loc'),source_work_profiles=10,canonical_loc_profiles=10,
        formatted_loc_profiles=0,formatted_loc_qualified=False,retained_bounded_cases=149,compiler_invocations=0,
        fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,new_native_probes=0,original_files_mutated=False,
        samples=3,scala_samples=30,matched_mech_samples=30,full_processes=60,schedule=[list(s) for s in schedule_for(manifests)],
        manifests=manifests,pins=pins,prerequisite_artifact_closures=closures,shared_timing_lock=str(LOCK),common_mutex_inode=79859134,
        continuous_common_mutex=True,no_automatic_retry=True,full_timings_qualified=False,chart_admission=False,
        timing_policy='Fresh direct JVM process including startup, retained class loading, tiered JIT, full input, '
            'all work, complete output and shutdown; subject compilation, pin hashing and output validation excluded')


def validate_plan(plan,prepared=False):
    expected=build_draft(plan['output'])
    if prepared:expected.update(status='prepared-awaiting-independent-review',pins_verified=True)
    require(plan==expected,'Plan differs from exact qualification, cohort, closure, schedule or timing policy')


def checked_runtime():
    helpers.checked_runtime()
    require(not any(k in os.environ for k in INJECTION_ENV),'Ambient JVM/native injection variables must be absent')


def qualified_sample(attempt,manifest,row,fingerprint):
    shared.qualified_sample(attempt,manifest,row,fingerprint)
    require(attempt.get('stderr')=='','Qualified full sample requires empty native stderr')


def load_measurement():
    guard,harness=helpers.load_measurement()
    require(not any(k in harness.compact.ENV for k in INJECTION_ENV),'Sampler inherited an unqualified JVM environment')
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
            if row['language']!='scala':continue
            directory=Path(row['classes']);paths=list(directory.rglob('*'))
            require(directory.is_dir() and not directory.is_symlink() and not any(p.is_symlink() for p in paths)
                    and {str(p.relative_to(directory)):p.stat().st_size for p in paths if p.is_file()}==
                    {a['relative_path']:a['bytes'] for a in row['class_artifacts']},'Retained executable class inventory changed')
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
    new_json(guard.OUT/'terminal.json',dict(schema='scala-full60-terminal-v1',status=report['status'],
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
    lease_path = ROOT / 'experiments/scala/scala-full60.owner.lock'
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with held_lock(live_lock) as lock:
            verify(plan['pins'])
            guard,harness = load_measurement()
            check_execution_inputs(plan, harness)
            supervisor = cold(SUPERVISOR, SUPERVISOR_SHA, 'scala_full60_independent_supervisor')
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
            report = dict(schema='scala-full60-results-v1',status='running',started_at=guard.now(),supervisor=guard.identity(os.getpid()),
                plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,programs=rows,attempts=[],active=None,
                benchmark_order=BENCHES,completed_benchmarks=[],sample_count=3,full_performance_runs=0,
                skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=str(LOCK),
                source_work_profiles=10,canonical_loc_profiles=10,formatted_loc_profiles=0,
                planned_scala_samples=30,planned_matched_mech_samples=30,full_timings_qualified=False,
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
                    print('SCALA FULL',bench,round_index,identifier,manifest['size'],flush=True)
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
