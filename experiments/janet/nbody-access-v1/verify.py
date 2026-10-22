"""Replay source-bound n-body output, work, state, resource and timing evidence."""
import hashlib
import json
from pathlib import Path
import statistics
import struct
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success
from qualify_perturbed import CASES
from reference import integrate

CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'

def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    q=json.loads((HERE/'qualification-v1/results.json').read_bytes())
    assert q['status']=='all-energy-work-and-complete-state-contracts-pass'
    for label,digest in q['source_sha256'].items():assert process.sha(SOURCES[label])==digest
    for label,digest in q['projection_sha256'].items():assert process.sha(HERE/'qualification-v1'/(label+'-witness.janet'))==digest
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    contract={row['case']:corpus['cases'][row['corpus_index']] for row in PLAN['schedule'] if row['benchmark']=='nbody'}
    for row in q['outputs']:
        case=contract[row['case']];d=HERE/'qualification-v1'/f"{row['label']}-{row['case']}"
        receipt=json.loads((d/'process.json').read_bytes())
        validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),receipt['exit_status'],(corpus_path.parent/case['expected']['path']).read_bytes())
    states={}
    for row in q['work_witnesses']:
        d=HERE/'qualification-v1'/f"{row['label']}-witness-{row['case']}";case=contract[row['case']]
        receipt=json.loads((d/'process.json').read_bytes());assert receipt['exit_status']==0
        validate_success(case,(d/'stdout.bin').read_bytes(),b'',0,(corpus_path.parent/case['expected']['path']).read_bytes())
        lines=(d/'stderr.bin').read_bytes().splitlines();assert len(lines)==36
        assert lines[0]==f"W {10*row['n']} {15*row['n']}".encode()
        state=b''.join(struct.pack('>d',float(v)) for v in lines[1:]);assert hashlib.sha256(state).hexdigest()==row['state_sha256']
        assert row['pair_interactions']==10*row['n'] and row['position_updates']==15*row['n']
        if row['label']=='parent':states[row['case']]=state
        else:assert states[row['case']]==state
    p=json.loads((HERE/'perturbed-v1/results.json').read_bytes());assert p['status']=='all-perturbed-state-bits-match-independent-reference'
    assert p['reference_sha256']==process.sha(HERE/'reference.py')
    for label,digest in p['source_sha256'].items():assert process.sha(SOURCES[label])==digest
    for label,digest in p['projection_sha256'].items():assert process.sha(HERE/'perturbed-v1'/(label+'.janet'))==digest
    for row in p['cases']:
        seed,n,dt=CASES[row['slot']];assert (seed,n,dt)==(row['seed'],row['n'],row['dt'])
        wanted=b''.join(struct.pack('>d',v) for body in integrate(seed,n,dt) for v in body)
        d=HERE/'perturbed-v1'/f"{row['slot']:02d}-{row['label']}";raw=(d/'stdout.bin').read_bytes().splitlines()
        assert len(raw)==35 and b''.join(struct.pack('>d',float(v)) for v in raw)==wanted
        assert hashlib.sha256(wanted).hexdigest()==row['state_sha256'] and not (d/'stderr.bin').read_bytes()
    r=json.loads((HERE/'run-v1/results.json').read_bytes())
    assert r['status']=='twelve-full-size-complete-process-outputs-pass' and r['active'] is None
    assert r['n']==50000000 and r['denominator']['seconds']==1.039486459 and r['denominator']['program']=='nbody:pairwise-mass-tails'
    assert r['required_work']['pair_interactions']==500000000 and r['required_work']['position_components']==750000000
    for name,digest in r['pins'].items():assert process.sha(Path(name))==digest,name
    for row in r['samples']:
        d=HERE/'run-v1'/f"{row['sample']:02d}-{row['label']}";receipt=json.loads((d/'process.json').read_bytes())
        validate_success(r['output_contract'],(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),receipt['exit_status'],r['expected_stdout'].encode())
        assert receipt['quantitative_benchmark'] and row['seconds']==receipt['elapsed_seconds']
        assert row['maximum_rss_bytes']==receipt['maximum_rss_bytes'] and row['x_mech_aot']==row['seconds']/1.039486459
    for label,summary in r['summary'].items():
        rows=[x for x in r['samples'] if x['label']==label];assert len(rows)==3
        assert summary['median_seconds']==statistics.median(x['seconds'] for x in rows)
        assert summary['stdev_seconds']==statistics.stdev(x['seconds'] for x in rows)
        assert summary['x_mech_aot']==summary['median_seconds']/1.039486459
        assert summary['maximum_rss_bytes']==max(x['maximum_rss_bytes'] for x in rows)
    for snap in r['telemetry']:
        assert "'AC Power'" in snap['battery']
        modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line]
        assert modes and set(modes)=={'0'}
    bytecode=json.loads((HERE/'bytecode-v1/results.json').read_bytes());assert bytecode['status']=='four-source-bound-native-disassemblies-captured'
    for label,row in bytecode['profiles'].items():
        assert row['source_sha256']==process.sha(SOURCES[label])
        assert row['projection_sha256']==process.sha(HERE/'bytecode-v1'/(label+'.janet'))
        assert row['bytecode_sha256']==process.sha(HERE/'bytecode-v1'/label/'stdout.bin')
    metrics=json.loads((HERE/'source-measures.json').read_bytes())
    for label,row in metrics['profiles'].items():
        assert row['sha256']==process.sha(SOURCES[label]) and isinstance(row['language_lexical_tokens'],int)
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    analysis=json.loads((HERE/'bytecode-review.json').read_bytes())
    assert analysis['status']=='verified-source-bound-static-instruction-findings'
    assert analysis['profiles']['scalar-registers']['single_time_step_loop']['aggregate_state_reads_or_writes']==0
    for label,row in analysis['profiles'].items():assert row['bytecode_sha256']==process.sha(HERE/'bytecode-v1'/label/'stdout.bin')
    review=json.loads((HERE.parent/'measurement-boundary-review-v1.json').read_bytes())
    assert not review['elapsed_samples_changed'] and not review['source_controller_changed'] and not review['prior_sealed_artifacts_changed']
    assert sum(x['subjects_with_strictly_inside_live_snapshot'] for x in review['reports'])==24
    for packet in review['reports']:
        assert packet['report_sha256']==process.sha(ROOT/packet['report'])
        for example in packet['examples']:
            assert example['subject_sha256']==process.sha(ROOT/example['subject'])
            assert example['snapshot_sha256']==process.sha(ROOT/example['snapshot'])
            subject=json.loads((ROOT/example['subject']).read_bytes());snapshot=json.loads((ROOT/example['snapshot']).read_bytes())
            a=subject['birth_identity'];b=snapshot['birth_identity']
            start=a['birth_seconds']+a['birth_microseconds']/1e6;when=b['birth_seconds']+b['birth_microseconds']/1e6
            assert start+1<when<start+subject['elapsed_seconds']-1
    manifest=json.loads((HERE/'source-manifest.json').read_bytes())
    for row in manifest['sources']:assert process.sha(ROOT/row['path'])==row['sha256']
    owned=0
    for path in HERE.rglob('process.json'):
        row=json.loads(path.read_bytes());assert row['reaped'] and row['group_closed'] and not row['cleanup_errors'] and row['exit_status']==0,path
        assert row['controller_sha256'] in {process.sha(HERE.parent/'knucleotide-bytes-v1/process.py'),process.sha(HERE.parent/'native-v1/run.py')}
        owned+=1
    assert len(q['outputs'])==24 and len(q['work_witnesses'])==24 and len(p['cases'])==24 and len(r['samples'])==12
    result=dict(status='verified',bounded_energy_outputs=24,canonical_complete_state_work_witnesses=24,independent_perturbed_state_cases=24,full_size_samples=12,native_disassemblies=4,closed_owned_processes=owned,canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
