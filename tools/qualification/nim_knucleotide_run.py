"""Serial exact-output checks and matched whole-process Nim nucleotide timings."""
import argparse
import fcntl
import json
from pathlib import Path
import random
import shutil
import statistics
from bqn_knucleotide_run import ROOT,power,sha,atom,process

HERE=ROOT/'experiments/nim/optimization-v1'
CORPUS=ROOT/'experiments/shared/bounded-corpus-v1/cases'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--full',action='store_true')
    p.add_argument('--samples',type=int,default=1)
    args=p.parse_args()
    assert args.samples>0 and not args.output.exists()
    plan=json.loads((HERE/'matched-build-plan.json').read_text())
    builds={r['id']:r for r in plan['commands']}
    pins={}
    args.output.mkdir(parents=True)
    for name,row in builds.items():
        source,binary=Path(row['source']),Path(row['binary'])
        receipt=json.loads((source.parent/'build.json').read_text())
        assert receipt['exit_status']==0 and receipt['source_sha256']==sha(source)==row['source_sha256']
        assert receipt['artifacts']['knucleotide']==sha(binary)
        pins[str(source.relative_to(ROOT))]=sha(source)
        pins[str(binary.relative_to(ROOT))]=sha(binary)
        dest=args.output/'builds'/name;dest.mkdir(parents=True)
        for file in ['build.json','build.stdout','build.stderr','knucleotide.nim']:
            shutil.copyfile(source.parent/file,dest/file)
    cases=[c for c in json.loads((CORPUS/'manifest.json').read_text())['cases'] if c['benchmark']=='knucleotide']
    if args.full:
        cases=[dict(case='n25000000',stdin=dict(path=str(ROOT/'experiments/lean4/.build/inputs/n25000000.fasta'),
            sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
            expected=dict(bytes=259,sha256=process.FULL['knucleotide'][2]))]
    report=dict(schema='nim-knucleotide-execution.v1',status='RUNNING',chart_admission=False,full_workload=args.full,
        source_commit=__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
        controller_sha256=sha(__file__),shared_process_controller_sha256=sha(ROOT/'tools/qualification/lean_run.py'),
        matched_build_plan_sha256=sha(HERE/'matched-build-plan.json'),pins=pins,
        timing_boundary='Fresh executable process through exit, all startup/input/worker threads/output included; no compilation or validation in timer.',
        orders=[],cases=[])
    rng=random.Random(20261020)
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['common_mutex_inode']=__import__('os').fstat(lock.fileno()).st_ino
        for case in cases:
            inp=CORPUS/case['stdin']['path'];assert sha(inp)==case['stdin']['sha256']
            for sample in range(1,args.samples+1):
                order=list(builds);rng.shuffle(order);report['orders'].append(dict(case=case['case'],sample=sample,order=order))
                for name in order:
                    assert all(sha(ROOT/path)==digest for path,digest in pins.items())
                    before=power();folder=args.output/case['case']/f'{sample:02d}-{name}'
                    record=process.one([builds[name]['binary']],inp,folder,300)
                    after=power()
                    valid=record['exit_code']==0 and record['stderr']['bytes']==0 and all(record['stdout'][f]==case['expected'][f] for f in ['bytes','sha256'])
                    record.update(source=name,case=case['case'],sample=sample,output_valid=valid,input=case['stdin'],expected=case['expected'],power_before=before,power_after=after)
                    report['cases'].append(record);atom(args.output/'report.json',report)
                    print(json.dumps(dict(source=name,case=case['case'],sample=sample,seconds=record['elapsed_seconds'],valid=valid)),flush=True)
                    if not valid:
                        report['status']='FAILED';atom(args.output/'report.json',report);raise SystemExit(1)
                    assert all(sha(ROOT/path)==digest for path,digest in pins.items())
        report['status']='PASSED'
        if args.full:report['medians']={name:statistics.median(r['elapsed_seconds'] for r in report['cases'] if r['source']==name) for name in builds}
        atom(args.output/'report.json',report)

if __name__=='__main__':main()
