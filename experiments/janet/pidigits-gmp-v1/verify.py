"""Replay full integer traces, dual extraction work, loaders and all fresh-process samples."""
import hashlib
import json
from pathlib import Path
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,reference

SOURCES={**SOURCES,**{name:HERE/'sources'/(name+'.janet') for name in ('positive-division','compact','compact-positive')}}
CATALOG_SHA='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'
WARNING=b"otool: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead\n"

def load(path):return json.loads(path.read_bytes())
def main():
    assert process.sha(ROOT/'data/benchmarks.json')==CATALOG_SHA
    gmp=Path(PLAN['environment']['MECH_GMP_LIBRARY']);assert process.sha(gmp)==PLAN['gmp_resolution']['sha256']
    outputs=0;witnesses=0
    for folder in ('qualification-v2','refined-qualification-v1','composed-qualification-v1'):
        report=load(HERE/folder/'results.json');assert report['status']=='all-complete-outputs-and-unbounded-integer-state-traces-pass'
        assert report['reference_sha256']==process.sha(HERE/'common.py')
        for label,digest in report['source_sha256'].items():assert process.sha(SOURCES[label])==digest
        for label,digest in report['projection_sha256'].items():assert process.sha(HERE/folder/(label+'-witness.janet'))==digest
        for row in report['outputs']:
            d=HERE/folder/f"{row['label']}-n{row['n']}"
            assert (d/'stdout.bin').read_bytes()==reference(row['n'])[0] and not (d/'stderr.bin').read_bytes()
            assert row['stdout_sha256']==process.sha(d/'stdout.bin');outputs+=1
        for row in report['work_witnesses']:
            want,trace,counts=reference(row['n'],True);d=HERE/folder/f"{row['label']}-witness-n{row['n']}"
            assert (d/'stdout.bin').read_bytes()==want and (d/'stderr.bin').read_bytes()==trace
            assert row['complete_trace_sha256']==hashlib.sha256(trace).hexdigest()
            assert all(row[name]==value for name,value in counts.items()) and row['mpz_initializations']==row['mpz_clears']==6
            witnesses+=1
    assert outputs==witnesses==96
    expected,_,counts=reference(10000)
    assert len(expected)==16893 and hashlib.sha256(expected).hexdigest()=='bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'
    assert counts==dict(advance_steps=33209,extract3_calls=22454,extract4_calls=22454,emitted_digits=10000,removal_steps=9999)
    work_profiles=0
    for folder,status in [('full-work-v1','five-full-size-outputs-and-dual-extraction-work-counts-pass'),('refined-full-work-v1','two-new-full-size-outputs-and-dual-extraction-work-counts-pass'),('composed-full-work-v1','one-composed-full-size-output-and-dual-extraction-work-counts-pass')]:
        report=load(HERE/folder/'results.json');assert report['status']==status and report['reference_counts']==counts
        assert (HERE/folder/'expected.stdout').read_bytes()==expected
        assert report['reference_sha256']==process.sha(HERE/'common.py')
        historical=report['historical_output_reference'];assert process.sha(ROOT/historical['path'])==historical['sha256']
        for label,row in report['profiles'].items():
            assert process.sha(SOURCES[label])==row['source_sha256'] and process.sha(HERE/folder/(label+'-witness.janet'))==row['projection_sha256']
            d=HERE/folder/label;assert (d/'stdout.bin').read_bytes()==expected and (d/'stderr.bin').read_bytes()==b'C 33209 22454 22454 10000 9999 6 6\n'
            assert all(row[name]==value for name,value in counts.items());work_profiles+=1
    assert work_profiles==8
    libraries=0
    for folder in ('library-v2','refined-library-v1','composed-library-v1'):
        report=load(HERE/folder/'results.json')
        assert report['status'] in ('both-applications-load-pinned-gmp; loader-and-link-metadata-retained','composed-application-loads-pinned-gmp; loader-and-link-metadata-retained')
        for label,row in report['profiles'].items():
            d=HERE/folder/label;assert row['source_sha256']==process.sha(SOURCES[label]) and row['gmp_sha256']==process.sha(gmp)
            assert (d/'stdout.bin').read_bytes()==reference(30)[0] and row['complete_loader_capture_sha256']==process.sha(d/'stderr.bin')
            lines=(d/'stderr.bin').read_text().splitlines();assert lines and all(line.startswith('dyld[') for line in lines) and any(str(gmp) in line for line in lines)
            libraries+=1
        for name,row in report['metadata'].items():
            d=HERE/folder/name;assert row['stdout_sha256']==process.sha(d/'stdout.bin') and row['stderr_sha256']==process.sha(d/'stderr.bin')
            stderr=(d/'stderr.bin').read_bytes();assert not stderr or (name.endswith('links') and stderr==WARNING)
    assert libraries==5
    full=0
    for folder,status,number in [('run-v1','35-full-size-complete-process-outputs-pass',35),('refined-run-v1','49-full-size-complete-process-outputs-pass',49),('final-run-v1','56-full-size-complete-process-outputs-pass',56)]:
        report=load(HERE/folder/'results.json');assert report['status']==status and report['active'] is None and len(report['samples'])==number
        assert report['n']==10000 and report['rounds']==7 and report['required_work']==counts
        assert report['denominator']['program']=='pidigits:mech-pi-final-advance-signed' and report['denominator']['seconds']==.300272042
        for name,digest in report['pins'].items():assert process.sha(Path(name))==digest,name
        for row in report['samples']:
            d=HERE/folder/f"{row['sample']:02d}-{row['label']}";receipt=load(d/'process.json')
            assert receipt['quantitative_benchmark'] and (d/'stdout.bin').read_bytes()==expected and not (d/'stderr.bin').read_bytes()
            assert row['seconds']==receipt['elapsed_seconds'] and row['maximum_rss_bytes']==receipt['maximum_rss_bytes']
            assert row['x_mech_aot']==row['seconds']/.300272042;full+=1
        for label,summary in report['summary'].items():
            rows=[r for r in report['samples'] if r['label']==label];assert len(rows)==7
            assert summary['median_seconds']==statistics.median(r['seconds'] for r in rows)
            assert summary['stdev_seconds']==statistics.stdev(r['seconds'] for r in rows)
            assert summary['maximum_rss_bytes']==max(r['maximum_rss_bytes'] for r in rows) and summary['x_mech_aot']==summary['median_seconds']/.300272042
        for snap in report['telemetry']:
            assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line];assert modes and set(modes)=={'0'}
    assert full==140
    final=load(HERE/'final-run-v1/results.json');analysis=load(HERE/'analysis.json')
    assert analysis['status']=='verified-final-eight-way-cohort-only' and analysis['final_report_sha256']==process.sha(HERE/'final-run-v1/results.json')
    parents={r['sample']:r for r in final['samples'] if r['label']=='parent'}
    for label,row in analysis['profiles'].items():
        ratios=[parents[r['sample']]['seconds']/r['seconds'] for r in final['samples'] if r['label']==label]
        assert row['paired_parent_speedups']==ratios and row['median_paired_parent_speedup']==statistics.median(ratios)
        assert row['rounds_faster_than_parent']==sum(value>1 for value in ratios)
    measures=load(HERE/'source-measures.json')
    for label,row in measures['profiles'].items():
        assert row['sha256']==process.sha(SOURCES[label]) and isinstance(row['language_lexical_tokens'],int)
        assert row['normalized_logical_loc'] is None and row['canonical_formatted_loc'] is None
    manifest=load(HERE/'source-manifest.json')
    for row in manifest['sources']:assert process.sha(ROOT/row['path'])==row['sha256']
    release=load(HERE/'gmp-release-source-v1/manifest.json')
    for name,row in release['files'].items():assert process.sha(HERE/'gmp-release-source-v1'/name)==row['sha256']
    assert b'mpz_tdiv_qr (quot, rem, dividend, divisor)' in (HERE/'gmp-release-source-v1/mpz/fdiv_q.c').read_bytes()
    assert b'mpn_div_q (qp, np, nl, dp, dl, tp)' in (HERE/'gmp-release-source-v1/mpz/tdiv_q.c').read_bytes()
    owned=0
    for p in HERE.rglob('process.json'):
        r=load(p);assert r['group_closed'] and r['reaped'] and not r['cleanup_errors'],p
        allowed=1 if p==HERE/'qualification-v1/parent-witness-n0/process.json' else 0
        assert r['exit_status']==allowed,p
        assert r['controller_sha256'] in {process.sha(HERE.parent/'knucleotide-bytes-v1/process.py'),process.sha(HERE.parent/'native-v1/run.py')};owned+=1
    result=dict(status='verified',bounded_outputs=outputs,exact_unbounded_state_traces=witnesses,full_size_actual_work_witnesses=work_profiles,accepted_loader_captures=libraries,full_size_quantitative_samples=full,final_cohort_samples=56,closed_owned_processes=owned,canonical_catalog_unchanged=True)
    process.save(HERE/'verification.json',result);print(json.dumps(result))

if __name__=='__main__':main()
