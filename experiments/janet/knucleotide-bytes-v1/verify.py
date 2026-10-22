"""Replay source/output/resource evidence without executing a benchmark."""
import hashlib
import json
from pathlib import Path
import statistics
import qualify as reference

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXPECTED='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert sha(ROOT/'data/benchmarks.json')=='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'
    jobs=[('run-v1','nine-full-size-complete-process-outputs-pass',{'parent','byte-buffer','line-reader'}),
          ('modulo-run-v1','six-modulo-full-size-complete-process-outputs-pass',{'byte-modulo','line-modulo'}),
          ('threaded-run-v1','three-threaded-full-size-complete-process-outputs-pass',{'threaded-modulo'})]
    total=0
    for folder,status,labels in jobs:
        directory=HERE/folder;r=json.loads((directory/'results.json').read_bytes())
        assert r['status']==status and r['active'] is None and r['benchmark_samples']==len(r['samples'])==3*len(labels)
        assert set(r['summary'])==labels and r['three_sequence_length']==125000000 and r['full_histogram_updates']==874999961
        assert r['denominator']['seconds']==0.51382825 and r['denominator']['n']==25000000
        assert r['expected']==dict(bytes=259,sha256=EXPECTED)
        for path,digest in r['pins'].items():assert sha(Path(path))==digest,path
        for row in r['samples']:
            case=directory/f"{row['sample']:02d}-{row['label']}"
            process=json.loads((case/'process.json').read_bytes())
            assert process['exit_status']==0 and process['quantitative_benchmark'] is True
            assert process['elapsed_seconds']==row['seconds'] and process['maximum_rss_bytes']==row['maximum_rss_bytes']
            assert row['x_mech_aot']==row['seconds']/r['denominator']['seconds'] and row['output_valid']
            assert (case/'stdout.bin').stat().st_size==259 and sha(case/'stdout.bin')==EXPECTED and not (case/'stderr.bin').read_bytes()
        for label in labels:
            rows=[x for x in r['samples'] if x['label']==label];values=[x['seconds'] for x in rows]
            assert len(values)==3 and statistics.median(values)==r['summary'][label]['median_seconds']
            assert statistics.stdev(values)==r['summary'][label]['stdev_seconds']
            assert max(x['maximum_rss_bytes'] for x in rows)==r['summary'][label]['maximum_rss_bytes']
        for snapshot in r['telemetry']:
            assert "'AC Power'" in snapshot['battery']
            modes=[line.split()[-1] for line in snapshot['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
        total+=len(r['samples'])
    counts=[]
    for folder,status,count in [('qualification-v1','42-complete-outputs-and-294-full-histograms-pass',42),('modulo-qualification-v1','28-complete-outputs-and-196-full-histograms-pass',28),('threaded-qualification-v1','14-threaded-outputs-98-full-histograms-and-worker-failure-pass',14)]:
        r=json.loads((HERE/folder/'results.json').read_bytes())
        assert r['status']==status and len(r['outputs'])==len(r['work_witnesses'])==count
        counts.append(count)
        plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
        corpus_path=ROOT/plan['corpus'];corpus=json.loads(corpus_path.read_bytes())
        for row in plan['schedule']:
            if row['benchmark']!='knucleotide':continue
            case=corpus['cases'][row['corpus_index']]
            stdin=(ROOT/row['stdin']).read_bytes()
            expected=(corpus_path.parent/case['expected']['path']).read_bytes()
            trace=reference.witness(reference.sequence(stdin))
            labels=['threaded'] if folder=='threaded-qualification-v1' else list(r['sources'])
            for label in labels:
                normal=HERE/folder/(f"normal-{row['case']}" if label=='threaded' else f"{label}-{row['case']}")
                witness=HERE/folder/(f"witness-{row['case']}" if label=='threaded' else f"{label}-witness-{row['case']}")
                nr=json.loads((normal/'process.json').read_bytes());wr=json.loads((witness/'process.json').read_bytes())
                reference.validate_success(case,(normal/'stdout.bin').read_bytes(),(normal/'stderr.bin').read_bytes(),nr['exit_status'],expected)
                reference.validate_success(case,(witness/'stdout.bin').read_bytes(),b'',wr['exit_status'],expected)
                assert (witness/'stderr.bin').read_bytes()==trace

    domain=json.loads((HERE/'native-domain-v1/result.json').read_bytes())
    assert domain['status']=='72360-native-domain-checks-pass' and sha(HERE/'modulo-domain.janet')==domain['source_sha256']
    records=0
    for path in HERE.rglob('process.json'):
        r=json.loads(path.read_bytes());assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(path)
        records+=1
    a=json.loads((HERE/'source-measures.json').read_bytes());b=json.loads((HERE/'source-measures-v2.json').read_bytes())
    assert b['base_sha256']==sha(HERE/'source-measures.json') and len(b['profiles'])==6
    for label,row in a['profiles'].items():assert b['profiles'][label]==row
    for label,row in b['profiles'].items():assert sha(ROOT/row['source'])==row['sha256']
    print(json.dumps(dict(status='verified',full_samples=total,bounded_outputs=sum(counts),full_histograms=sum(counts)*7,
                         native_domain_checks=72360,owned_process_receipts=records,canonical_catalog_unchanged=True)))

if __name__=='__main__':main()
