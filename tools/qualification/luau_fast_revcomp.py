"""Qualify and time the guarded-error Luau reverse-complement candidate."""
import argparse
import fcntl
import json
import re
from pathlib import Path
import subprocess

from lean_run import one,sha,now,FULL,CORPUS,atom
from luau_run import ROOT,HERE,BUILD


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('bounded','full'),required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--bounded-report',type=Path)
    args=parser.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    source=HERE/'source-fast-v1/revcomp.luau';host=BUILD/'luau-host'
    base=(HERE/'source-v1/revcomp.luau').read_text()
    assert base.count('        assert(mapped, "Invalid IUPAC byte: " .. original)\n')==1
    assert source.read_text()==base.replace('        assert(mapped, "Invalid IUPAC byte: " .. original)\n',
        '        if not mapped then\n            error("Invalid IUPAC byte: " .. original)\n        end\n')
    pins={str(p.relative_to(ROOT)):sha(p) for p in (source,HERE/'source-v1/Host.cpp')}
    record=dict(schema='luau-guarded-revcomp-execution.v1',mode=args.mode,status='RUNNING',sources=pins,
        binary_sha256=sha(host),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        cases=[],active=None,started_utc=now(),benchmark_samples=0,controller_sha256=sha(__file__),chart_admission=False)
    if args.mode=='bounded':cases=[c for c in json.loads((CORPUS/'manifest.json').read_text())['cases'] if c['benchmark']=='revcomp']
    else:
        bounded=json.loads(args.bounded_report.read_text());assert bounded['status']=='PASSED' and len(bounded['cases'])==122 and bounded['sources']==pins and bounded['binary_sha256']==sha(host)
        record['bounded_prerequisite']=dict(path=str(args.bounded_report.relative_to(ROOT)) if args.bounded_report.is_absolute() else str(args.bounded_report),sha256=sha(args.bounded_report))
        stdin=ROOT/'experiments/lean4/.build/inputs/n25000000.fasta'
        record['input']=dict(path=str(stdin),bytes=stdin.stat().st_size,sha256=sha(stdin))
        cases=[dict(case=f'full-{i}',expected_exit=0) for i in range(1,4)]
    def save():atom(args.output/'report.json',record)
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for case in cases:
            for mode in ('vm','jit'):
                assert sha(host)==record['binary_sha256'] and all(sha(ROOT/p)==s for p,s in pins.items())
                power={}
                if args.mode=='bounded':
                    stdin=CORPUS/case['stdin']['path'];assert sha(stdin)==case['stdin']['sha256']
                else:
                    assert sha(stdin)==record['input']['sha256']
                    power['before']=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
                    power['settings']=subprocess.check_output(['/usr/bin/pmset','-g','custom'],text=True)
                    assert 'AC Power' in power['before'] and re.search(r'lowpowermode\s+0',power['settings'])
                    rows=subprocess.check_output(['/bin/ps','-axo','pid,comm'],text=True).splitlines()[1:]
                    forbidden={'cargo','rustc','clang','clang++','cc','cc1','lean','leanc','lake','julia','hyperfine','luau-host','luau-regex','luau-bigint'}
                    power['competitors']=[r for r in rows if len(r.split(maxsplit=1))==2 and Path(r.split(maxsplit=1)[1]).name in forbidden]
                    assert not power['competitors']
                record['active']=dict(case=case['case'],execution_mode=mode);save()
                directory=args.output/f'{len(record["cases"])+1:03d}-{case["case"]}-{mode}'
                r=one([str(host),'--'+mode,str(source)],stdin,directory,180 if args.mode=='bounded' else 21600)
                if case['expected_exit']=='nonzero':
                    valid=r['exit_code']==1 and (directory/'stdout.bin').read_bytes()==b'>r\n' and f'Invalid IUPAC byte: {case["expected_invalid_byte"]}'.encode() in (directory/'stderr.bin').read_bytes()
                elif args.mode=='bounded':
                    expected=CORPUS/case['expected']['path'];assert sha(expected)==case['expected']['sha256']
                    valid=r['exit_code']==0 and r['stderr']['bytes']==0 and (directory/'stdout.bin').read_bytes()==expected.read_bytes()
                else:
                    valid=r['exit_code']==0 and r['stderr']['bytes']==0 and r['stdout']['bytes']==FULL['revcomp'][1] and r['stdout']['sha256']==FULL['revcomp'][2]
                    power['after']=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True);valid=valid and 'AC Power' in power['after']
                r.update(case=case['case'],benchmark='revcomp',execution_mode=mode,valid=valid,power=power)
                atom(directory/'process.json',r);record['cases'].append(r);record['active']=None
                if valid and args.mode=='full':record['benchmark_samples']+=1
                save();print(f'{len(record["cases"])} guarded revcomp {case["case"]} {mode}: {"PASS" if valid else "FAIL"} ({r["elapsed_seconds"]:.3f}s)',flush=True)
                if not valid:record['status']='FAILED';save();raise SystemExit(1)
        record.update(status='PASSED',finished_utc=now());save()
    if args.mode=='bounded':
        counts=json.loads(subprocess.check_output([BUILD/'luau-source-reader',source],text=True))
        baseline=json.loads((HERE/'source-counts-v1/qualified-v1/qualified-counts.json').read_text())
        old=baseline['units']['revcomp.luau']
        assert counts['canonical_loc']==old['canonical_loc']+2
        assert counts['physical_loc']==old['physical_loc']+2
        counts.update(path=str(source.relative_to(ROOT)),sha256=sha(source),source_language='Luau')
        counts['expansions']=[dict(line=o['line'],extra_units=o['units']-1,reason='Packed native AST/closing owners') for o in counts['owners'] if o['units']>1]
        qualified=dict(schema='luau-guarded-revcomp-counts.v1',status='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES',
            units={'revcomp.luau':counts,'Host.cpp':baseline['units']['Host.cpp']},
            canonical_loc=counts['canonical_loc']+baseline['units']['Host.cpp']['canonical_loc'],
            physical_loc=counts['physical_loc']+baseline['units']['Host.cpp']['physical_loc'],
            reader_sha256=sha(BUILD/'luau-source-reader'),source_change='One eager assert becomes an if/error/end: two additional normalized source units.',benchmark_samples=0)
        (args.output/'qualified-counts.json').write_text(json.dumps(qualified,indent=2)+'\n')
    else:
        import statistics
        base_results=json.loads((HERE/'results-v1.json').read_text())
        summary={}
        for language,mode in [('luau','vm'),('luau-jit','jit')]:
            rows=[r for r in record['cases'] if r['execution_mode']==mode];assert len(rows)==3
            for r in rows:
                for stream in ('stdout','stderr'):
                    p=Path(r[stream]['path']);assert p.stat().st_size==r[stream]['bytes'] and sha(p)==r[stream]['sha256']
                assert json.loads((Path(r['stdout']['path']).parent/'process.json').read_text())==r
            samples=[r['elapsed_seconds'] for r in rows]
            summary[language]=dict(samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=statistics.stdev(samples))
        output=dict(schema='luau-guarded-revcomp-results.v1',status='SIX_FULL_SIZE_SAMPLES_RECONCILED',benchmark_samples=6,
            timing_processes_serial=True,all_full_outputs_validated=True,all_saved_stream_hashes_recomputed=True,
            source_commit=record['source_commit'],results=summary,
            report=dict(path=str((args.output/'report.json').relative_to(ROOT)),sha256=sha(args.output/'report.json')),
            timing_boundary=base_results['timing_boundary'],hardware=base_results['hardware'],os=base_results['os'],
            toolchains=base_results['toolchains'],inputs=record['input'],library_pins=base_results['library_pins'],
            libraries=base_results['libraries'],support_files=base_results['support_files'],all_process_records_reconciled=True,chart_admission=False)
        (HERE/'results-guarded-revcomp-v1.json').write_text(json.dumps(output,indent=2)+'\n')
        print(json.dumps({'status':output['status'],'results':summary}),flush=True)


if __name__=='__main__':main()
