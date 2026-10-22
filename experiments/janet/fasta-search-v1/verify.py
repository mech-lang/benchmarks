"""Replay FASTA evidence checks without starting a compiler or benchmark."""
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SHA='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
BYTES=254166745

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert sha(ROOT/'data/benchmarks.json')=='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'
    seal=json.loads((HERE/'preparation-seal.json').read_bytes())
    for path,digest in seal['files'].items():assert sha(ROOT/path)==digest,path
    q=json.loads((HERE/'qualification-v1/results.json').read_bytes())
    assert q['status']=='48-bounded-outputs-48-draw-witnesses-and-279951-search-checks-pass'
    assert len(q['outputs'])==len(q['witnesses'])==48 and q['search_equivalence_checks']==279951
    c=json.loads((HERE/'compact-qualification-v1/results.json').read_bytes())
    assert c['status']=='16-compact-bounded-outputs-and-16-draw-witnesses-pass'
    assert len(c['outputs'])==len(c['witnesses'])==16
    samples=0
    for name,status,labels in [('run-v1','nine-full-size-complete-process-outputs-pass',{'parent','linear','binary'}),('compact-run-v1','three-compact-full-size-complete-process-outputs-pass',{'compact'})]:
        folder=HERE/name;r=json.loads((folder/'results.json').read_bytes())
        assert r['status']==status and r['active'] is None and r['n']==25000000
        assert set(r['summary'])==labels and r['benchmark_samples']==3*len(labels)
        assert r['denominator']['seconds']==0.541193292 and r['denominator']['n']==25000000
        assert r['expected']==dict(bytes=BYTES,sha256=SHA)
        for path,digest in r['pins'].items():assert sha(Path(path))==digest,path
        for sample in r['samples']:
            assert sample['output_valid'] and sample['full_stdout_retained'] is False
            assert sample['x_mech_aot']==sample['seconds']/r['denominator']['seconds']
            directory=folder/f"{sample['sample']:02d}-{sample['label']}"
            process=json.loads((directory/'process.json').read_bytes())
            assert process['elapsed_seconds']==sample['seconds'] and process['exit_status']==0
            assert not (directory/'stderr.bin').read_bytes() and not (directory/'stdout.bin').exists()
            marker=json.loads((directory/'stdout-omitted.json').read_bytes())
            assert marker['bytes']==BYTES and marker['sha256']==SHA and marker['complete_output_verified_before_removal'] and not marker['retained']
        for label in labels:
            values=[x['seconds'] for x in r['samples'] if x['label']==label]
            assert len(values)==3 and statistics.median(values)==r['summary'][label]['median_seconds']
            assert statistics.stdev(values)==r['summary'][label]['stdev_seconds']
        for snapshot in r['telemetry']:
            assert "'AC Power'" in snapshot['battery']
            modes=[line.split()[-1] for line in snapshot['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
        samples+=len(r['samples'])
    records=0
    for path in HERE.rglob('process.json'):
        row=json.loads(path.read_bytes())
        assert row['reaped'] and row['group_closed'] and not row['cleanup_errors'],str(path)
        records+=1
    metrics=json.loads((HERE/'source-measures.json').read_bytes())
    for label,row in metrics['profiles'].items():
        assert sha(ROOT/row['source'])==row['sha256']
        raw=(HERE/'metrics-native-v1'/label/'stdout.bin').read_bytes()
        assert raw==f"{row['language_lexical_tokens']}\n".encode()
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    assert (HERE/'host-cpu.txt').read_text().strip()=='Apple M3'
    assert '26.2' in (HERE/'host-os.txt').read_text() and '25C56' in (HERE/'host-os.txt').read_text()
    print(json.dumps(dict(status='verified',full_samples=samples,bounded_outputs=64,draw_witnesses=64,owned_process_receipts=records,canonical_catalog_unchanged=True)))

if __name__=='__main__':main()
