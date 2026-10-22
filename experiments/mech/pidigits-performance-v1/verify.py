"""Replay complete output, actual GMP work and closed process receipts."""
import hashlib
import json
from pathlib import Path
import statistics
from run import HERE,ROOT,PLAN,COMMANDS,process,reference
CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'
def load(p):return json.loads(p.read_bytes())
def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    builds=load(HERE/'build-v1/results.json');assert builds['status']=='all-four-subjects-built'
    for name,row in builds['subjects'].items():
        assert process.sha(Path(COMMANDS[name][0]))==row['executable_sha256']
        src=HERE/'sources'/(name.removeprefix('mech-')+'.mec') if name.startswith('mech-') else ROOT/'archive/workloads/pidigits/upstream/pidigits-rust-3.rs'
        assert process.sha(src)==row['source_sha256']
        r=load(HERE/'build-v1'/name/'process.json');assert r['command']==row['command'] and r['exit_status']==0
        if name.startswith('mech-'):
            assert (HERE/'build-v1'/name/'object/source.mec').read_bytes()==src.read_bytes()
            assert process.sha(HERE/'build-v1'/name/'object/mech-control.o')==row['object_sha256']
    outputs=0
    for folder,size in [('qualification-v1',85),('run-v1',35)]:
        x=load(HERE/folder/'results.json');assert x['status']=='all-complete-outputs-pass' and len(x['samples'])==size
        assert all(process.sha(Path(p))==h for p,h in x['pins'].items())
        for row in x['samples']:
            d=HERE/folder/f"{row['round']:02d}-{row['label']}-n{row['n']}";r=load(d/'process.json')
            assert r['command']==COMMANDS[row['label']]+[str(row['n'])]
            assert (d/'stdout.bin').read_bytes()==reference(row['n'])[0] and not (d/'stderr.bin').read_bytes()
            assert row['stdout_sha256']==process.sha(d/'stdout.bin') and row['seconds']==r['elapsed_seconds']
            assert r['quantitative_benchmark']==(folder=='run-v1');outputs+=1
        if folder=='run-v1':
            for label,s in x['summary'].items():
                rows=[r['seconds'] for r in x['samples'] if r['label']==label]
                assert len(rows)==7 and s['median_seconds']==statistics.median(rows) and s['stdev_seconds']==statistics.stdev(rows)
                assert {r['round'] for r in x['samples'] if r['label']==label}==set(range(1,8))
    work=load(HERE/'work-v2/results.json');assert work['status']=='all-real-quotient-traces-and-full-size-division-counts-pass' and len(work['outputs'])==45
    assert work['counter_source_sha256']==process.sha(HERE/'gmp-work-counter.c')
    for row in work['outputs']:
        d=HERE/'work-v2'/f"{row['label']}-n{row['n']}";assert (d/'stdout.bin').read_bytes()==reference(row['n'])[0]
        assert row['stdout_sha256']==process.sha(d/'stdout.bin') and row['stderr_sha256']==process.sha(d/'stderr.bin')
        if row['n']==10000:assert row['counts']['tdiv']==44908 and row['counts']['fdiv']==0
        else:assert (d/'stderr.bin').read_bytes().split(b'WORK ')[0]==(HERE/'work-v2'/f"expected-n{row['n']}.trace").read_bytes()
    full={r['label']:r['counts'] for r in work['outputs'] if r['n']==10000}
    assert full['mech-parent']['mul_ui']-full['mech-compact-shared']['mul_ui']==22454
    assert full['mech-shared-numerator']==full['mech-compact-shared']
    lib=load(HERE/'library-v1/results.json');assert lib['status']=='all-five-executables-load-pinned-gmp' and len(lib['subjects'])==5
    assert process.sha(Path(lib['gmp_path']))==lib['gmp_sha256']
    for name,row in lib['subjects'].items():
        d=HERE/'library-v1'/name;assert process.sha(d/'stderr.bin')==row['loader_sha256'] and lib['gmp_path'] in (d/'stderr.bin').read_text()
    analysis=load(HERE/'analysis.json');run=load(HERE/'run-v1/results.json');assert analysis['timing_report_sha256']==process.sha(HERE/'run-v1/results.json')
    den=run['summary']['mech-compact-shared']['median_seconds'];assert analysis['comparison_denominator']['seconds']==den
    for name,row in analysis['profiles'].items():assert row['x_optimized_mech_aot']==run['summary'][name]['median_seconds']/den
    closed=0;failures=[]
    for p in HERE.rglob('process.json'):
        r=load(p);assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(p)
        if r['exit_status']!=0:failures.append(str(p.relative_to(HERE)));assert r['exit_status']==-9 and r['error']=='Owned process deadline'
        closed+=1
    assert failures==['work-v1/mech-parent-n1/process.json']
    result=dict(status='verified',complete_uninstrumented_outputs=outputs,full_size_quantitative_samples=35,real_gmp_work_witnesses=45,bounded_exact_quotient_traces=40,accepted_loader_captures=5,closed_owned_processes=closed,initial_failed_diagnostic_closed=True,canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))
if __name__=='__main__':main()
