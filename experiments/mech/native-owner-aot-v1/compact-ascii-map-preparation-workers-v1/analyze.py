"""Summarize exact task boundaries separately from primary benchmark timings."""
import json
from pathlib import Path
import statistics
STUDY=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
report=load(STUDY/'capture-v1/results.json')
assert report['status']=='all-thirty-two-full-boundaries-phases-outputs-and-updates-verified'
rows=[]; roots=[]
def span(a,b):
    delta={k:b[k]-a[k] for k in ('wall_ns','cpu_ns','p_instructions','e_instructions','p_cycles','e_cycles','p_user_mach','p_system_mach','e_user_mach','e_system_mach')}
    delta['wall_seconds']=delta['wall_ns']/1e9;delta['cpu_seconds']=delta['cpu_ns']/1e9
    delta['instructions']=delta['p_instructions']+delta['e_instructions']
    delta['cycles']=delta['p_cycles']+delta['e_cycles']
    for core in ('p','e'):
        delta[core+'_cpu_seconds']=(delta[core+'_user_mach']+delta[core+'_system_mach'])*125/3/1e9
    return delta
for sample in report['samples']:
    traces=load(STUDY/sample['folder']/'workers.json');main=traces['main'];subject=sample['subject']
    by={r['label']:r for r in main}; origin=main[0]['wall_ns']
    root=dict(subject=subject,order=sample['order'],total=span(main[0],main[-1]))
    if subject=='rust':
        root['input']=span(main[0],by['input_ready'])
        root['after_input_before_spawn']=span(by['input_ready'],by['spawn_begin'])
    else:
        root['before_capture']=span(main[0],by['capture_setup_begin'])
        root['input']=span(by['capture_setup_begin'],by['capture_eof'])
        root['after_input_before_spawn']=span(by['capture_eof'],by['spawn_begin'])
    root['spawn']=span(by['spawn_begin'],by['spawn_complete'])
    roots.append(root)
    for trace in traces['workers']:
        m={r['label']:r for r in trace}
        row=dict(subject=subject,order=sample['order'],width=trace[0]['width'],thread_id=trace[0]['thread_id'],total=span(trace[0],trace[-1]),count=span(m['count_begin'],m['count_complete']))
        for label in ('worker_begin','count_begin','count_complete','body_complete'):
            row[label+'_after_main_seconds']=(m[label]['wall_ns']-origin)/1e9
        if subject!='rust':
            for label,a,b in [('setup','worker_begin','worker_setup_ready'),('prepare_count','worker_setup_ready','count_begin'),('publication','count_complete','map_publication_complete'),('post_publication','map_publication_complete','generated_body_complete'),('retire_storage','generated_body_complete','worker_storage_retired')]:
                row[label]=span(m[a],m[b])
        rows.append(row)
median=lambda seq:statistics.median(seq)
worker_summary=[]
for subject in ['candidate','parent','ordinary','rust']:
    for width in [1,2,3,4,6,12,18]:
        selected=[r for r in rows if r['subject']==subject and r['width']==width];assert len(selected)==8
        row=dict(subject=subject,width=width,samples=8)
        for label in ['total','count','setup','prepare_count','publication','post_publication','retire_storage']:
            if label not in selected[0]:continue
            row[label]={k:median([r[label][k] for r in selected]) for k in ['cpu_seconds','wall_seconds','instructions','cycles','p_cpu_seconds','e_cpu_seconds']}
        for label in ('worker_begin','count_begin','count_complete','body_complete'):
            key=label+'_after_main_seconds';row[key]=median([r[key] for r in selected])
        worker_summary.append(row)
for row in worker_summary:
    rust=next(r for r in worker_summary if r['subject']=='rust' and r['width']==row['width'])
    row['count_cpu_x_rust']=row['count']['cpu_seconds']/rust['count']['cpu_seconds']
root_summary={}
for subject in ['candidate','parent','ordinary','rust']:
    selected=[r for r in roots if r['subject']==subject];assert len(selected)==8
    root_summary[subject]={label:{k:median([r[label][k] for r in selected]) for k in ['cpu_seconds','wall_seconds','instructions','cycles']} for label in selected[0] if isinstance(selected[0][label],dict)}
result=dict(status='complete-boundaries-analyzed',primary_benchmark_samples=0,worker_samples=rows,root_samples=roots,workers=worker_summary,main=root_summary,limitations=['Instrumented diagnostic hosts are separate from primary timing binaries; no elapsed speedup is inferred from this cohort.','Count completion is an in-task boundary; body completion is before OS thread-wrapper exit.','Rust workers return maps and format/drop them in main; Mech workers include publication and generated body work.','Per-core counters are read-only and cumulative. Performance/Efficiency names and 125/3 ns Mach timebase were verified on this runner.'])
result['preparation_phase_median_cpu_seconds']={}
result['preparation_milestone_median_cpu_seconds']={}
for subject in ['candidate','parent','ordinary']:
    phase_rows=[load(STUDY/r['folder']/'phases.json') for r in report['samples'] if r['subject']==subject]
    assert len(phase_rows)==8
    result['preparation_phase_median_cpu_seconds'][subject]={name:median([r['phases'][name]['cpu_ns']/1e9 for r in phase_rows]) for name in phase_rows[0]['phases']}
    result['preparation_milestone_median_cpu_seconds'][subject]={m['name']:median([next(x['cpu_ns'] for x in r['marks'] if x['name']==m['name'])/1e9 for r in phase_rows]) for m in phase_rows[0]['marks']}
result['limitations'].append('Preparation spans are nested and instrumented; do not add them or substitute them for primary elapsed samples. Worker and preparation roots use separate clock origins.')
result['source']=report['source_before']
result['source_after']=report['source_after']
result['preparation_phase_calls']={}
for subject in ['candidate','parent','ordinary']:
    phase_rows=[load(STUDY/r['folder']/'phases.json') for r in report['samples'] if r['subject']==subject]
    result['preparation_phase_calls'][subject]={name:sorted(set(r['phases'][name]['calls'] for r in phase_rows)) for name in phase_rows[0]['phases']}
result['phase_semantics']=load(STUDY/'plan.json')['phase_semantics']
result['limitations'].append('Candidate and immediate parent use identical ten-slot phase probes and chunk boundaries; the ordinary control retains its seven-slot probe. Source-loan, combined transform/copy and chunk-receipt spans replace the unused legacy copy/map spans. Their scopes and clock counts differ, and no clock-overhead subtraction is made.')
import hashlib
result['analysis_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
result['capture_sha256']=hashlib.sha256((STUDY/'capture-v1/results.json').read_bytes()).hexdigest()
(STUDY/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for subject in root_summary:
    print(subject,'main', {k:{m:round(v,6) for m,v in d.items() if m.endswith('seconds')} for k,d in root_summary[subject].items()})
print('subject width countCPU countWall xRustCPU startAfterMain finishAfterMain Pcpu Ecpu')
for r in worker_summary:
    print(r['subject'],r['width'],*[round(v,6) for v in [r['count']['cpu_seconds'],r['count']['wall_seconds'],r['count_cpu_x_rust'],r['worker_begin_after_main_seconds'],r['body_complete_after_main_seconds'],r['count']['p_cpu_seconds'],r['count']['e_cpu_seconds']]])
