"""Replay complete tree outputs, allocation/visit identity, partitions and full timings."""
import hashlib
import json
from pathlib import Path
import re
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,expected,work

SOURCES={**SOURCES,**{name:HERE/'sources'/(name+'.janet') for name in ('unrolled','threaded-unrolled')}}
CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'

def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    outputs=0;witnesses=0
    for folder in ('qualification-v1','unrolled-qualification-v1'):
        report=json.loads((HERE/folder/'results.json').read_bytes());assert report['status']=='all-bounded-outputs-and-distinct-node-partitions-pass'
        for label,pin in report['sources'].items():assert process.sha(ROOT/pin['path'])==pin['sha256']==process.sha(SOURCES[label])
        for label,digest in report['projection_sha256'].items():assert process.sha(HERE/folder/(label+'-witness.janet'))==digest
        for row in report['outputs']:
            d=HERE/folder/f"{row['label']}-n{row['n']}-w{row['workers']}"
            assert (d/'stdout.bin').read_bytes()==expected(row['n']) and not (d/'stderr.bin').read_bytes()
            assert row['stdout_sha256']==process.sha(d/'stdout.bin');outputs+=1
        for row in report['work_witnesses']:
            n=row['n'];workers=row['workers'];depth=max(6,n);main_nodes,short=work(n)
            d=HERE/folder/f"{row['label']}-n{n}-w{workers}-witness"
            assert (d/'stdout.bin').read_bytes()==expected(n)
            if row['label'].startswith('threaded-'):
                trace=f'M {main_nodes} {main_nodes} {main_nodes}\n';summed=0
                for id in range(workers):
                    nodes=sum(((2**(4+depth-level)*(id+1)//workers)-(2**(4+depth-level)*id//workers))*(2**(level+1)-1) for level in range(4,depth+1,2));summed+=nodes
                    trace+=f'W {id} {nodes} {nodes} {nodes}\n'
                assert summed==short
            else:trace=f'M {main_nodes+short} {main_nodes+short} {main_nodes+short}\n'
            assert (d/'stderr.bin').read_bytes()==trace.encode()
            assert row['total_distinct_nodes']==row['total_check_visits']==main_nodes+short;witnesses+=1
    assert outputs==66 and witnesses==66
    partition=json.loads((HERE/'partition-domain-v1/results.json').read_bytes());assert partition['status']=='all-native-bounds-match-exact-integer-partitions' and partition['partitions']==2464
    want=[]
    for depth in range(6,22):
        for workers in range(1,8):
            for level in range(4,depth+1,2):
                count=2**(4+depth-level);last=0
                for id in range(workers):
                    start=count*id//workers;end=count*(id+1)//workers;assert start==last;last=end
                    want.append(f'{depth} {workers} {level} {id} {start} {end}\n')
                assert last==count
    assert (HERE/'partition-domain-v1/capture/stdout.bin').read_bytes()==''.join(want).encode()
    assert partition['source_sha256']==process.sha(SOURCES['threaded-cached']) and partition['projection_sha256']==process.sha(HERE/'partition-domain-v1/bounds.janet')
    failure=json.loads((HERE/'failure-v1/results.json').read_bytes());assert failure['status']=='owned-worker-error-propagates-without-depth-summaries'
    assert failure['source_sha256']==process.sha(SOURCES['threaded-cached']) and failure['projection_sha256']==process.sha(HERE/'failure-v1/owned-failure.janet')
    d=HERE/'failure-v1/capture';assert (d/'stdout.bin').read_bytes()==expected(9).splitlines(keepends=True)[0]
    assert (d/'stderr.bin').read_bytes().startswith(b'error: Tree worker failed: owned-tree-worker-probe\n')
    report=json.loads((HERE/'run-v1/results.json').read_bytes());assert report['status']=='fifteen-full-size-complete-process-outputs-pass' and report['active'] is None
    assert report['n']==21 and report['required_work']['nodes_constructed']==report['required_work']['nodes_walked']==613766494
    assert report['denominator']['seconds']==.394411208 and report['denominator']['program']=='binarytrees:mech-binarytrees-parallel'
    assert report['denominator']['allocation_policy']=='General core library pool; distinct 16-byte node slots; per-tree frame release.'
    for name,digest in report['pins'].items():assert process.sha(Path(name))==digest,name
    for row in report['samples']:
        d=HERE/'run-v1'/f"{row['sample']:02d}-{row['label']}";receipt=json.loads((d/'process.json').read_bytes())
        assert receipt['quantitative_benchmark'] and (d/'stdout.bin').read_bytes()==expected(21) and not (d/'stderr.bin').read_bytes()
        assert row['seconds']==receipt['elapsed_seconds'] and row['maximum_rss_bytes']==receipt['maximum_rss_bytes']
        assert row['x_mech_aot']==row['seconds']/.394411208
    assert len(report['samples'])==15
    for label,summary in report['summary'].items():
        rows=[r for r in report['samples'] if r['label']==label];assert len(rows)==3
        assert summary['median_seconds']==statistics.median(r['seconds'] for r in rows) and summary['stdev_seconds']==statistics.stdev(r['seconds'] for r in rows)
        assert summary['maximum_rss_bytes']==max(r['maximum_rss_bytes'] for r in rows) and summary['x_mech_aot']==summary['median_seconds']/.394411208
    swap=[]
    for snap in report['telemetry']:
        assert "'AC Power'" in snap['battery']
        modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line];assert modes and set(modes)=={'0'}
        assert 'Mach Virtual Memory Statistics' in snap['memory']
        value=re.search(r'used\s*=\s*([0-9.]+)M',snap['swap']);assert value;swap.append(float(value.group(1)))
    measures=json.loads((HERE/'source-measures.json').read_bytes())
    for label,row in measures['profiles'].items():
        assert row['sha256']==process.sha(SOURCES[label]) and isinstance(row['language_lexical_tokens'],int)
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    manifest=json.loads((HERE/'source-manifest.json').read_bytes())
    for row in manifest['sources']:assert process.sha(ROOT/row['path'])==row['sha256']
    runtime=json.loads((HERE/'runtime-review.json').read_bytes())
    for row in runtime['files']:assert process.sha(ROOT/row['path'])==row['sha256']
    owned=0
    for p in HERE.rglob('process.json'):
        r=json.loads(p.read_bytes());assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],p
        assert r['exit_status']==(1 if p==HERE/'failure-v1/capture/process.json' else 0),p
        assert r['controller_sha256'] in {process.sha(HERE.parent/'knucleotide-bytes-v1/process.py'),process.sha(HERE.parent/'native-v1/run.py')}
        owned+=1
    result=dict(status='verified',bounded_outputs=outputs,distinct_node_visit_partition_witnesses=witnesses,native_partition_bounds=2464,owned_worker_failure_verified=True,full_samples=15,closed_owned_processes=owned,maximum_swap_MiB_in_recorded_host_snapshots=max(swap),canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
