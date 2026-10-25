"""Balanced diagnostic-only complete-process runs, with exact boundary counters."""
import fcntl
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent
HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state, check_native, INPUT_SHA, OUTPUT_SHA, POLICY_SHA, DATA_SHA, SOURCE_SHA
from parse import parse
plan_path=STUDY/'capture-plan.json'
plan=read(plan_path)
before=source_state(); assert before==plan['source'] and not before['status']
subjects=['aligned','facts','rust']
assert len(plan['orders'])==6 and len({tuple(row) for row in plan['orders']})==6
assert all(sorted(row)==subjects for row in plan['orders'])
canonical=HERE.parents[2]/'data/benchmarks.json'
inp=HERE.parents[2]/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
policy=HERE/'full-disjoint-state-v1/launch.json'
assert process.sha(canonical)==DATA_SHA and process.sha(inp)==INPUT_SHA and process.sha(policy)==POLICY_SHA
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
assert process.sha(STUDY/'parse.py')==plan['parser_sha256']
for subject in subjects:
    pin=plan['subjects'][subject]
    assert process.sha(Path(pin['binary']))==pin['binary_sha256']
    assert process.sha(STUDY/pin['build_receipt'])==pin['build_receipt_sha256']
out=STUDY/'full-capture-v1'; out.mkdir(exist_ok=False)
report=dict(status='running',source_before=before,plan_sha256=process.sha(plan_path),driver_sha256=process.sha(Path(__file__)),primary_benchmark_samples=0,excluded_runs=0,samples=[])
process.save(out/'results.json',report)
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for index,order in enumerate(plan['orders']):
        for position,subject in enumerate(order):
            pin=plan['subjects'][subject]; binary=Path(pin['binary'])
            assert process.sha(binary)==pin['binary_sha256']
            folder=out/f'{index:02d}-{position}-{subject}'
            native=out/(folder.name+'.native.json')
            command=[str(binary)]+([] if subject=='rust' else [str(policy),str(native),'--'])
            receipt=process.execute(command,folder,plan['environment'],lock,stdin=inp,deadline=30,quantitative=False)
            assert receipt['exit_status']==0 and process.sha(folder/'stdout.bin')==OUTPUT_SHA
            n=check_native(native) if subject!='rust' else None
            traces=parse(folder/'stderr.bin',subject)
            process.save(folder/'traces.json',traces)
            report['samples'].append(dict(order=index,position=position,subject=subject,process=str((folder/'process.json').relative_to(STUDY)),process_sha256=process.sha(folder/'process.json'),traces=str((folder/'traces.json').relative_to(STUDY)),traces_sha256=process.sha(folder/'traces.json'),stdout_sha256=OUTPUT_SHA,native=n,native_sha256=process.sha(native) if n else None))
            process.save(out/'results.json',report)
        print('diagnostic order',index+1,'of 6 verified',flush=True)
    assert source_state()==before and process.sha(canonical)==DATA_SHA
report.update(status='all-eighteen-diagnostic-outputs-widths-and-updates-verified',source_after=source_state())
process.save(out/'results.json',report)
