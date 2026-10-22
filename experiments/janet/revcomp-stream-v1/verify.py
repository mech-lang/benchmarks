"""Replay exact corpus contracts, closed ownership, source pins and measured summaries."""
import hashlib
import json
from pathlib import Path
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,validate,oracle

ALL_SOURCES={**SOURCES,'block-rows':HERE/'sources/block-rows.janet'}
CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'

def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    expected=json.loads((HERE/'reference-v1/expected.json').read_bytes())
    assert expected['bytes']==254166745 and expected['sha256']=='e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'
    assert expected['reference_sha256']==process.sha(HERE/'reference.py')
    outputs=0;witnesses=0;rejections=0;corruptions=0
    for directory in ('qualification-v3','block-qualification-v1'):
        report=json.loads((HERE/directory/'results.json').read_bytes())
        assert report['status']=='all-complete-output-rejection-and-visit-contracts-pass'
        for label,pin in report['sources'].items():assert process.sha(ROOT/pin['path'])==pin['sha256']
        for row in report['outputs']:
            source=ALL_SOURCES[row['label']];raw=(ROOT/row['stdin']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['stdin_sha256']
            d=HERE/directory/f"{row['label']}-{row['case']}";receipt=json.loads((d/'process.json').read_bytes())
            stdout=(d/'stdout.bin').read_bytes();stderr=(d/'stderr.bin').read_bytes()
            validate(stdout,stderr,receipt['exit_status'],raw,source)
            assert process.sha(d/'stdout.bin')==row['stdout_sha256']
            outputs+=1
            if row['invalid']:
                rejections+=1
                changes=[(stdout+b'X',stderr,1),(stdout,stderr,0),(stdout,stderr,2),
                         (stdout,stderr.replace(b'Invalid IUPAC',b'Unrelated error',1),1),
                         (stdout,stderr.replace(b' at record offset ',b' at wrong offset ',1),1),
                         (stdout,b'',1),(stdout,stderr.replace(b'in write-record',b'in other-frame',1),1)]
                for a,b,c in changes:
                    try:validate(a,b,c,raw,source)
                    except AssertionError:corruptions+=1
                    else:raise AssertionError('Corrupted rejection accepted')
        by_case={r['case']:ROOT/r['stdin'] for r in report['outputs']}
        for row in report['work_witnesses']:
            raw=by_case[row['case']].read_bytes();want,error,work=oracle(raw);assert error is None
            d=HERE/directory/f"{row['label']}-witness-{row['case']}"
            assert (d/'stdout.bin').read_bytes()==want
            assert (d/'stderr.bin').read_bytes()==''.join(f'W {n} {v}\n' for n,v in work).encode()
            assert row['records']==len(work) and row['base_visits']==sum(n for n,_ in work)
            witnesses+=1
    full=0
    for directory,status in [('run-v2','nine-full-size-complete-process-outputs-pass'),('block-run-v1','three-full-size-complete-process-outputs-pass')]:
        report=json.loads((HERE/directory/'results.json').read_bytes())
        assert report['status']==status and report['active'] is None
        assert report['denominator']['program']=='revcomp:mech-revcomp-optimized'
        assert report['denominator']['seconds']==.149272625
        for name,digest in report['pins'].items():assert process.sha(Path(name))==digest,name
        for row in report['samples']:
            d=HERE/directory/f"{row['sample']:02d}-{row['label']}"
            receipt=json.loads((d/'process.json').read_bytes());omitted=json.loads((d/'stdout-omitted.json').read_bytes())
            assert receipt['quantitative_benchmark'] and receipt['exit_status']==0
            assert receipt['elapsed_seconds']==row['seconds'] and receipt['maximum_rss_bytes']==row['maximum_rss_bytes']
            assert row['output_valid'] and row['x_mech_aot']==row['seconds']/.149272625
            assert omitted['bytes']==expected['bytes'] and omitted['sha256']==expected['sha256'] and omitted['verified_complete']
            assert omitted['group_closed'] and omitted['reaped'] and not (d/'stdout.bin').exists() and not (d/'stderr.bin').read_bytes()
            full+=1
        for label,summary in report['summary'].items():
            rows=[r for r in report['samples'] if r['label']==label];assert len(rows)==3
            assert summary['median_seconds']==statistics.median(r['seconds'] for r in rows)
            assert summary['stdev_seconds']==statistics.stdev(r['seconds'] for r in rows)
            assert summary['x_mech_aot']==summary['median_seconds']/.149272625
            assert summary['maximum_rss_bytes']==max(r['maximum_rss_bytes'] for r in rows)
        for snap in report['telemetry']:
            assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
    owned=0
    for p in HERE.rglob('process.json'):
        r=json.loads(p.read_bytes())
        assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],p
        assert r['controller_sha256'] in {process.sha(HERE.parent/'knucleotide-bytes-v1/process.py'),process.sha(HERE.parent/'native-v1/run.py')},p
        owned+=1
    manifest=json.loads((HERE/'source-manifest.json').read_bytes())
    assert manifest['active_parent']['sha256']==process.sha(ALL_SOURCES['parent'])
    for row in manifest['candidates']:assert process.sha(ROOT/row['path'])==row['sha256']
    assert manifest['source_overlay_manifest_sha256']==process.sha(HERE.parent/'source-overlays-v1.json')
    metrics=json.loads((HERE/'source-measures.json').read_bytes())
    for label,row in metrics['profiles'].items():
        assert row['sha256']==process.sha(ALL_SOURCES[label])
        assert isinstance(row['language_lexical_tokens'],int)
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    assert outputs==272 and witnesses==232 and full==12 and rejections==40 and corruptions==280
    result=dict(status='verified',bounded_outputs=outputs,record_visit_witnesses=witnesses,rejections=rejections,rejection_corruptions_rejected=corruptions,full_samples=full,closed_owned_processes=owned,canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
