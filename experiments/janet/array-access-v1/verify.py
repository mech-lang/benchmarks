"""Replay complete outputs, full bounded work and source identity; no benchmark run."""
import hashlib
import json
import math
from pathlib import Path
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success
from qualify import permutation_stream

CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'

def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    report=json.loads((HERE/'qualification-v1/results.json').read_bytes());assert report['status']=='all-bounded-output-and-full-work-witnesses-pass'
    for label,digest in report['source_sha256'].items():assert process.sha(SOURCES[label][1])==digest
    for label,digest in report['projection_sha256'].items():assert process.sha(HERE/'qualification-v1'/(label+'-witness.janet'))==digest
    corpus_path=ROOT/PLAN['corpus'];corpus=json.loads(corpus_path.read_bytes())
    cases={(row['benchmark'],row['case']):corpus['cases'][row['corpus_index']] for row in PLAN['schedule'] if row['benchmark'] in ('binarytrees','fannkuchredux')}
    for row in report['outputs']:
        case=cases[row['benchmark'],row['case']];d=HERE/'qualification-v1'/f"{row['label']}-{row['case']}"
        r=json.loads((d/'process.json').read_bytes())
        validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],(corpus_path.parent/case['expected']['path']).read_bytes())
    for row in report['work_witnesses']:
        d=HERE/'qualification-v1'/f"{row['label']}-witness-{row['case']}";case=cases[row['benchmark'],row['case']]
        r=json.loads((d/'process.json').read_bytes())
        validate_success(case,(d/'stdout.bin').read_bytes(),b'',r['exit_status'],(corpus_path.parent/case['expected']['path']).read_bytes())
        if row['benchmark']=='binarytrees':
            depth=max(6,row['n']);count=(2**(depth+2)-1)+(2**(depth+1)-1)+sum(2**(4+depth-level)*(2**(level+1)-1) for level in range(4,depth+1,2))
            assert row['allocations']==row['node_check_visits']==row['distinct_mutable_nodes']==count
            assert (d/'stderr.bin').read_bytes()==f'W {count} {count} {count}\n'.encode()
        else:
            reference=b''.join(permutation_stream(row['n']))
            assert (d/'stderr.bin').read_bytes()==reference
            assert hashlib.sha256(reference).hexdigest()==row['complete_permutation_and_flip_stream_sha256']
            assert row['all_permutations']==(math.factorial(row['n']) if row['n'] else 0)
    metrics=json.loads((HERE/'source-measures.json').read_bytes())
    for label,row in metrics['profiles'].items():
        assert row['sha256']==process.sha(SOURCES[label][1]) and isinstance(row['language_lexical_tokens'],int)
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    manifest=json.loads((HERE/'source-manifest.json').read_bytes())
    for row in manifest['sources']:assert process.sha(ROOT/row['path'])==row['sha256']
    owned=0
    for path in HERE.rglob('process.json'):
        row=json.loads(path.read_bytes());assert row['exit_status']==0 and row['reaped'] and row['group_closed'] and not row['cleanup_errors'],path
        assert row['controller_sha256'] in {process.sha(HERE.parent/'knucleotide-bytes-v1/process.py'),process.sha(HERE.parent/'native-v1/run.py')}
        assert not row['quantitative_benchmark'];owned+=1
    assert len(report['outputs'])==35 and len(report['work_witnesses'])==35
    result=dict(status='verified',bounded_outputs=len(report['outputs']),complete_work_witnesses=len(report['work_witnesses']),closed_owned_processes=owned,benchmark_samples=0,canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
