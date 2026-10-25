"""Verify actual-path diagnostics against raw owned executions and boundaries."""
import hashlib,importlib.util,statistics,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state,check_native,INPUT_SHA,OUTPUT_SHA,POLICY_SHA,DATA_SHA,SOURCE_SHA

def parser(name):
    spec=importlib.util.spec_from_file_location(name,STUDY/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.parse
worker_parse=parser('worker-parse');phase_parse=parser('phase-parse')
plan=read(STUDY/'plan.json');before=source_state();assert before['commit']==plan['diagnostic_source'] and not before['status']
build=read(STUDY/'build-candidate-v1/results.json');spec=read(STUDY/'build-candidate.json')
assert build['source_before']==build['source_after']==before and build['status']=='diagnostic-host-built'
assert build['spec_sha256']==process.sha(STUDY/'build-candidate.json')
assert build['driver_sha256']==process.sha(STUDY/'build.py')
assert build['probe_sha256']==spec['phase_probe_sha256']==process.sha(STUDY/'phase_probe.rs')
assert build['worker_probe_sha256']==spec['worker_probe_sha256']==process.sha(STUDY/'worker_probe.rs')
assert process.sha(Path(build['binary']))==build['binary_sha256']
production=read(HERE/'compact-ascii-map-v1/verification.json')
assert process.sha(HERE/'compact-ascii-map-v1/verification.json')==plan['production_verification_sha256']
assert production['source']['commit']==plan['production_source']
assert production['object_sha256']==build['guest_object_sha256']
project=HERE/'.build'/(spec['output']+'.project');parent=HERE/'.build'/(spec['parent_binary']+'.project')
for name in ['program.o','program.mecb','native-resources.json']:
    assert process.sha(project/name)==process.sha(parent/name)
assert process.sha(project/'program.o')==production['object_sha256']
pins=read(STUDY/'build-candidate-v1/pin-update.json')
assert pins['checks_removed']==0 and {k for k in pins['before'] if pins['before'][k]!=pins['after'][k]}=={'src/main.rs','build.rs'}
for name,expected in pins['after'].items():assert process.sha(project/name)==expected
compat=read(STUDY/'probe-compatibility.json')
assert process.sha(STUDY/'probe-compatibility.json')==plan['probe_compatibility_sha256']
assert compat['candidate_phase_probe_sha256']==build['probe_sha256'] and compat['worker_probe_sha256']==build['worker_probe_sha256']
assert compat['control_phase_probe_sha256']==process.sha(STUDY/'phase-probe-parent.rs')
assert compat['clock_ids']==[16,6] and compat['fixed_marks']==16
for name,pin in plan['retained_builds'].items():
    path=HERE/pin['path'];assert process.sha(path)==pin['sha256']
    r=read(path);assert process.sha(Path(r['binary']))==pin['binary_sha256']==r['binary_sha256']
    if name!='rust':assert r['worker_probe_sha256']==build['worker_probe_sha256'] and r['probe_sha256']==compat['direct_parent_phase_probe_sha256' if name=='parent' else 'control_phase_probe_sha256']
    else:assert r['probe_sha256']==build['worker_probe_sha256']
capture=read(STUDY/'capture-v1/results.json')
assert capture['status']=='all-thirty-two-full-boundaries-phases-outputs-and-updates-verified'
assert capture['source_before']==capture['source_after']==before
assert capture['plan_sha256']==process.sha(STUDY/'plan.json') and capture['driver_sha256']==process.sha(STUDY/'capture-v2.py')
assert capture['phase_parser_sha256']==process.sha(STUDY/'phase-parse.py') and capture['worker_parser_sha256']==process.sha(STUDY/'worker-parse.py')
assert len(capture['prefix'])==4 and len(capture['samples'])==32 and capture['primary_benchmark_samples']==capture['excluded_runs']==0
assert [r['subject'] for r in capture['prefix']]==['candidate','parent','ordinary','rust']
for order,subjects in enumerate(plan['orders']):
    assert [r['subject'] for r in capture['samples'] if r['order']==order]==subjects
for subject in ['candidate','parent','ordinary','rust']:
    assert len([r for r in capture['samples'] if r['subject']==subject])==8
    assert all(len([r for r in capture['samples'] if r['subject']==subject and r['position']==p])==2 for p in range(4))
for full,rows in [(False,capture['prefix']),(True,capture['samples'])]:
    for row in rows:
        folder=STUDY/row['folder'];subject=row['subject']
        assert process.sha(folder/'process.json')==row['process_sha256']
        assert process.sha(folder/'stdout.bin')==row['output_sha256']==(OUTPUT_SHA if full else 'f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa')
        assert process.sha(folder/'workers.json')==row['workers_sha256']
        assert worker_parse(folder/'stderr.bin',subject)==read(folder/'workers.json')
        if subject!='rust':
            assert process.sha(folder/'phases.json')==row['phases_sha256']
            assert phase_parse(folder/'stderr.bin',subject)==read(folder/'phases.json')
            native=folder.with_name(folder.name+'.native.json');assert process.sha(native)==row['native_sha256']
            n=read(native);assert n['native_hash_table_updates']==n['native_packed_map_updates']==(874999961 if full else 6999961)
            assert n['native_parallel_tasks']==7 and n['policy']=='secured' and n['shutdown']=='completed'
            if full:check_native(native);assert n['native_worker_credit_batches']==854497
            else:assert n['native_worker_credit_batches']>0
            assert n.get('native_fused_string_map_bytes',0)==((125000000 if full else 1000000) if subject in ['candidate','parent'] else 0)
analysis=read(STUDY/'analysis.json')
assert analysis['status']=='complete-boundaries-analyzed' and analysis['source']==analysis['source_after']==before
assert analysis['analysis_sha256']==process.sha(STUDY/'analyze.py') and analysis['capture_sha256']==process.sha(STUDY/'capture-v1/results.json')
assert len(analysis['worker_samples'])==224 and len(analysis['root_samples'])==32 and len(analysis['workers'])==28
for row in capture['samples']:
    traces=read(STUDY/row['folder']/'workers.json');origin=traces['main'][0]['wall_ns']
    for trace in traces['workers']:
        marks={r['label']:r for r in trace};width=trace[0]['width']
        derived=next(r for r in analysis['worker_samples'] if r['subject']==row['subject'] and r['order']==row['order'] and r['width']==width)
        assert derived['count']['cpu_seconds']==(marks['count_complete']['cpu_ns']-marks['count_begin']['cpu_ns'])/1e9
        assert derived['body_complete_after_main_seconds']==(marks['body_complete']['wall_ns']-origin)/1e9
for summary in analysis['workers']:
    selected=[r for r in analysis['worker_samples'] if r['subject']==summary['subject'] and r['width']==summary['width']]
    assert len(selected)==summary['samples']==8
    assert summary['count']['cpu_seconds']==statistics.median(r['count']['cpu_seconds'] for r in selected)
    rust=next(r for r in analysis['workers'] if r['subject']=='rust' and r['width']==summary['width'])
    assert summary['count_cpu_x_rust']==summary['count']['cpu_seconds']/rust['count']['cpu_seconds']
for subject in ['candidate','parent','ordinary']:
    phases=[read(STUDY/r['folder']/'phases.json') for r in capture['samples'] if r['subject']==subject]
    for name,value in analysis['preparation_phase_median_cpu_seconds'][subject].items():
        assert value==statistics.median(p['phases'][name]['cpu_ns']/1e9 for p in phases)
paths=list((STUDY/'build-candidate-v1').rglob('process.json'))+list((STUDY/'capture-v1').rglob('process.json'))
assert len(paths)==37
for path in paths:
    p=read(path);assert p['exit_status']==0 and p['inherited_common_mutex'] and p['reaped'] and p['group_closed'] and not p['signals'] and not p['cleanup_errors']
assert process.sha(HERE.parents[2]/'data/benchmarks.json')==DATA_SHA and process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
assert process.sha(HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin')==INPUT_SHA
assert process.sha(HERE/'full-disjoint-state-v1/launch.json')==POLICY_SHA and source_state()==before
result=dict(status='all-four-subject-actual-path-phases-widths-outputs-work-and-terminal-receipts-verified',source=before,production_source=plan['production_source'],primary_benchmark_samples=0,diagnostic_full_processes=32,qualifying_prefix_processes=4,worker_intervals=224,terminal_owned_receipts=len(paths),guest_object_sha256=build['guest_object_sha256'],candidate_binary_sha256=build['binary_sha256'],verifier_sha256=process.sha(Path(__file__)),analysis_sha256=process.sha(STUDY/'analysis.json'),scope='Instrumented preparation and per-width observations; no primary elapsed or parity claim.')
process.save(STUDY/'verification.json',result);print(result)
