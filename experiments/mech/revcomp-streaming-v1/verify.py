"""Replay frozen source, complete bounded output, timing and closure receipts."""
import hashlib,json,statistics,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    comp=load(HERE/'compiler.json');a=load(HERE/'analysis.json');run=load(HERE/'run-v2/results.json')
    assert sha(ROOT/'data/benchmarks.json')==a['catalog_sha256']
    assert sha(HERE/'run-v2/results.json')==a['timing_report_sha256']
    assert run['status']=='all-35-full-size-outputs-pass' and len(run['samples'])==35
    assert run['official_input_all_five_pass'] and run['mutex_inode']==83858837
    for p,h in comp['snapshot_files'].items():assert sha(HERE/p)==h,p
    baseline=load(HERE/'baseline-build-v1/results.json');candidate=load(HERE/'candidate-build-v1/results.json')
    assert sha(HERE/'compiler-snapshot/runtime-parent.rs')==baseline['runtime_source_sha256']
    assert sha(HERE/'compiler-snapshot/runtime-candidate.rs')==candidate['runtime_source_sha256']
    for n,h in candidate['mech']['unchanged_emitted_inputs'].items():
        for label in ('mech-revcomp-parent','mech-revcomp-candidate'):assert sha(HERE/'compiler-snapshot'/label/n)==h
    assert sha(ROOT/'archive/workloads/revcomp/revcomp.mec')==comp['source_sha256']
    assert sha(ROOT/comp['rust_source'])==candidate['rust']['application_source_sha256']
    # Executables are omitted from the public snapshot; compare their receipt pins.
    binary_hashes={str(HERE/'.build/mech-revcomp-parent'):baseline['binary_sha256'],str(HERE/'.build/mech-revcomp-candidate'):candidate['mech']['binary_sha256'],str(HERE/'.build/rust-revcomp-1'):candidate['rust']['binary_sha256']}
    for name,h in run['pins'].items():
        p=Path(name)
        if name in binary_hashes:
            assert h==binary_hashes[name]
            if p.exists():assert sha(p)==h
        else:
            # Study paths are rebased for a checkout at a different location.
            rel=p.relative_to('/private/tmp/mech-benchmark-publication');assert sha(ROOT/rel)==h
    corpus=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json';q=load(HERE/'qualification-v1/results.json')
    assert sha(corpus)==q['corpus_sha256'] and q['status']=='all-61-parent-candidate-behaviors-identical'
    cases={r['case']:r for r in load(corpus)['cases'] if r['benchmark']=='revcomp'}
    assert len(q['cases'])==len(cases)==61 and not q['new_regressions']
    differences=[]
    for case in q['cases']:
        assert case['parent']==case['candidate']
        for label in ('parent','candidate'):
            d=HERE/'qualification-v1'/f"{label}-{case['case']}";r=load(d/'process.json')
            assert r['exit_status']==case[label]['exit_status'] and not r['quantitative_benchmark']
            assert sha(d/'stdout.bin')==case[label]['stdout_sha256'] and sha(d/'stderr.bin')==case[label]['stderr_sha256']
        expected=cases[case['case']];d=HERE/'qualification-v1'/f"candidate-{case['case']}"
        valid=(case['candidate']['exit_status']==0 and sha(d/'stdout.bin')==expected['expected']['sha256'] and not (d/'stderr.bin').read_bytes()) if expected['expected_exit']==0 else case['candidate']['exit_status']!=0
        assert valid==case['shared_reference_contract_met']
        if not valid:differences.append(case['case'])
    assert differences==q['existing_source_contract_differences'] and len(differences)==11
    expected=(ROOT/'archive/workloads/revcomp/inputs/revcomp-output-1000.txt').read_bytes()
    for label in run['variants']:
        d=HERE/'run-v2'/f'official-{label}';r=load(d/'process.json')
        assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==expected and not (d/'stderr.bin').read_bytes()
    for row in run['samples']:
        d=HERE/'run-v2'/f"{row['round']:02d}-{row['label']}";r=load(d/'process.json');o=load(d/'stdout-omitted.json')
        assert r['quantitative_benchmark'] and r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
        assert r['command']==run['variants'][row['label']]['command'] and r['elapsed_seconds']==row['seconds']
        assert r['maximum_rss_bytes']==row['maximum_rss_bytes'] and row['x_retained_mech_aot']==row['seconds']/run['retained_mech_aot_reference_seconds']
        assert o['verified_complete'] and o['reaped'] and o['group_closed']
        assert o['bytes']==run['expected_output']['bytes']==254166745 and o['sha256']==run['expected_output']['sha256']
    den=run['summary']['candidate4']['median_seconds'];assert a['comparison_denominator']['seconds']==den
    for label,summary in run['summary'].items():
        rows=[r for r in run['samples'] if r['label']==label];times=[r['seconds'] for r in rows]
        assert len(rows)==7 and {r['round'] for r in rows}==set(range(1,8))
        assert summary['median_seconds']==statistics.median(times) and math.isclose(summary['stdev_seconds'],statistics.stdev(times),rel_tol=1e-14)
        assert a['profiles'][label]['x_optimized_mech_aot']==summary['median_seconds']/den
    for pair in a['paired_rounds']:
        rows={r['label']:r['seconds'] for r in run['samples'] if r['round']==pair['round']}
        assert pair['parent4_seconds']==rows['parent4'] and pair['candidate4_seconds']==rows['candidate4']
        assert pair['speedup']==rows['parent4']/rows['candidate4'] and pair['speedup']>1
    closed=0
    for p in HERE.rglob('process.json'):
        r=load(p);assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(p);closed+=1
    first=load(HERE/'run-v1/results.json');assert first['status']=='failed-not-admissible' and not first['samples']
    assert load(HERE/'run-v1/official-rust8/process.json')['exit_status']==126
    assert '8 passed; 0 failed' in (HERE/'tests/sequence-runtime.log').read_text()
    result=dict(status='verified',complete_bounded_comparisons=61,retained_bounded_output_captures=122,official_output_checks=5,full_output_hash_receipts=35,paired_faster_rounds=7,known_extended_source_contract_differences=11,closed_owned_processes=closed,initial_failed_launch_closed_before_timing=True,catalog_unchanged=True)
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
