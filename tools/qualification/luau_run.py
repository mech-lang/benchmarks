"""Qualify Luau VM/JIT outputs and record serial complete-process samples."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess

from lean_run import FULL, CORPUS, energy_output, one, sha, now, atom

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/luau'
SOURCE = HERE / 'source-v1'
BUILD = HERE / '.build/native-v1'
STDIN = {'regexredux', 'knucleotide', 'revcomp'}


def source_pins():
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(SOURCE.iterdir()) if p.suffix in ('.cpp','.luau')}


def host(benchmark):
    return BUILD / ('luau-regex' if benchmark=='regexredux' else 'luau-bigint' if benchmark=='pidigits' else 'luau-host')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('bounded','full'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bounded-report',type=Path)
    parser.add_argument('--work-review',type=Path)
    parser.add_argument('--benchmarks',nargs='+',default=list(FULL))
    parser.add_argument('--modes',nargs='+',choices=('vm','jit'),default=['vm','jit'])
    parser.add_argument('--samples',type=int,default=3)
    parser.add_argument('--input-large',type=Path,default=ROOT/'experiments/lean4/.build/inputs/n25000000.fasta')
    parser.add_argument('--input-regex',type=Path,default=ROOT/'experiments/lean4/.build/inputs/n5000000.fasta')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    pins=source_pins()
    binaries={b:sha(host(b)) for b in args.benchmarks}
    report=dict(schema='luau-serial-execution.v1',status='RUNNING',mode=args.mode,started_utc=now(),
                toolchain=dict(language='Luau',version='0.743',revision='9d7748a4f324213a18cb8283fa2a77c330225fa0',
                               source_optimization_level=2,type_info_level=1),
                sources=pins,binaries=binaries,controller_sha256=sha(__file__),cases=[],active=None,
                benchmark_samples=0,chart_admission=False,timing_processes_serial=True,
                timing_boundary='Fresh process: host and VM startup, source read and -O2 bytecode compilation, optional native JIT, arguments/input, all work/output, flushing and shutdown. Runtime builds and output comparisons excluded.')
    report['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report['process_recorder']=dict(path='tools/qualification/lean_run.py',sha256=sha(ROOT/'tools/qualification/lean_run.py'))
    report['build_evidence']=dict(path='experiments/luau/build-v2/report.json',sha256=sha(HERE/'build-v2/report.json'))
    manifest=json.loads((CORPUS/'manifest.json').read_text())
    if args.mode=='full':
        bounded=json.loads(args.bounded_report.read_text())
        assert bounded['status']=='PASSED' and len(bounded['cases'])==298
        assert bounded['sources']==pins
        assert all(bounded['binaries'][b]==binaries[b] for b in args.benchmarks)
        review=json.loads(args.work_review.read_text())
        assert review['status']=='PASSED' and review['sources']==pins
        report['bounded_prerequisite']=dict(path=str(args.bounded_report),sha256=sha(args.bounded_report))
        report['required_work']=dict(path=str(args.work_review),sha256=sha(args.work_review))
        report['input_pins']={str(p):dict(bytes=p.stat().st_size,sha256=sha(p),mtime_ns=p.stat().st_mtime_ns)
                              for p in (args.input_large,args.input_regex)}
        cases=[dict(benchmark=b,case=f'full-{i}',n=FULL[b][0],expected_exit=0)
               for b in args.benchmarks for i in range(1,args.samples+1)]
    else:
        cases=[c for c in manifest['cases'] if c['benchmark'] in args.benchmarks]
        report['corpus_sha256']=sha(CORPUS/'manifest.json')
    def save():
        atom(args.output/'report.json',report)
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['common_mutex_inode']=os.fstat(lock.fileno()).st_ino
        save()
        for case in cases:
            b=case['benchmark']
            for mode in args.modes:
                assert source_pins()==pins and sha(host(b))==binaries[b]
                if args.mode=='bounded':
                    stdin=CORPUS/case['stdin']['path']
                    assert sha(stdin)==case['stdin']['sha256']
                else:
                    stdin=(args.input_regex if b=='regexredux' else args.input_large) if b in STDIN else Path('/dev/null')
                    if b in STDIN:
                        pin=report['input_pins'][str(stdin)]
                        assert stdin.stat().st_size==pin['bytes'] and sha(stdin)==pin['sha256']
                command=[str(host(b)),'--'+mode,str(SOURCE/(b+'.luau'))]
                if b not in STDIN:command.append(str(case['n']))
                power={}
                if args.mode=='full':
                    for label,options in [('before',['-g','batt']),('settings',['-g','custom'])]:
                        power[label]=subprocess.check_output(['/usr/bin/pmset',*options],text=True)
                    assert 'AC Power' in power['before'] and re.search(r'lowpowermode\s+0',power['settings'])
                    rows=subprocess.check_output(['/bin/ps','-axo','pid,comm'],text=True).splitlines()[1:]
                    forbidden={'cargo','rustc','rustdoc','clang','clang++','cc','cc1','lean','leanc','lake','julia','hyperfine','luau-host','luau-regex','luau-bigint'}
                    competitors=[r for r in rows if len(r.split(maxsplit=1))==2 and Path(r.split(maxsplit=1)[1]).name in forbidden]
                    assert not competitors,competitors
                    power['competing_processes_before']=competitors
                report['active']=dict(benchmark=b,case=case['case'],execution_mode=mode)
                save()
                directory=args.output/f'{len(report["cases"])+1:03d}-{b}-{case["case"]}-{mode}'
                record=one(command,stdin,directory,180 if args.mode=='bounded' else 21600)
                raw=(directory/'stdout.bin').read_bytes() if args.mode=='bounded' or b=='nbody' else None
                if case['expected_exit']=='nonzero':
                    valid=record['exit_code']==1 and raw==b'>r\n' and f'Invalid IUPAC byte: {case["expected_invalid_byte"]}'.encode() in (directory/'stderr.bin').read_bytes()
                elif args.mode=='bounded':
                    expected=CORPUS/case['expected']['path']
                    assert sha(expected)==case['expected']['sha256']
                    valid=record['exit_code']==0 and record['stderr']['bytes']==0 and (energy_output(raw,expected.read_bytes()) if b=='nbody' else raw==expected.read_bytes())
                elif b=='nbody':
                    valid=record['exit_code']==0 and record['stderr']['bytes']==0 and energy_output(raw,b'-0.169075164\n-0.169059907\n')
                else:
                    valid=record['exit_code']==0 and record['stderr']['bytes']==0 and record['stdout']['bytes']==FULL[b][1] and record['stdout']['sha256']==FULL[b][2]
                if args.mode=='full':
                    power['after']=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
                    valid=valid and 'AC Power' in power['after']
                record.update(benchmark=b,case=case['case'],execution_mode=mode,valid=valid,power=power)
                atom(directory/'process.json',record)
                report['cases'].append(record)
                report['active']=None
                if valid and args.mode=='full':report['benchmark_samples']+=1
                save()
                print(f'{len(report["cases"])} {b} {case["case"]} {mode}: {"PASS" if valid else "FAIL"} ({record["elapsed_seconds"]:.3f}s)',flush=True)
                if not valid:
                    report['status']='FAILED';save();raise SystemExit(1)
        report.update(status='PASSED',finished_utc=now(),sources_unchanged=source_pins()==pins)
        save()


if __name__=='__main__':
    main()
