"""Prepare one hash-verified shared full FASTA fixture, outside timing."""
import fcntl
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('janet_input_owned',HERE.parent/'native-v1/run.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
EXPECTED='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
BYTES=254166745

def main():
    plan=json.loads((HERE.parent/'bounded-v1/plan-v1.json').read_bytes())
    target=HERE.parent/'.build/inputs/fasta-n25000000.stdin'
    if target.exists():
        assert target.stat().st_size==BYTES and process.sha(target)==EXPECTED
        print('Existing complete input identity verified');return
    source=HERE.parent/'fasta-search-v1/sources/linear.janet'
    evidence=json.loads((HERE.parent/'fasta-search-v1/run-v1/results.json').read_bytes())
    assert evidence['status']=='nine-full-size-complete-process-outputs-pass'
    assert process.sha(source)==evidence['pins'][str(source)]
    assert process.sha(Path(plan['runtime']))==plan['runtime_sha256']
    directory=HERE/'input-generation-v1'
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        command=[plan['runtime'],'-R','-n',str(source),'25000000']
        result=process.execute(command,directory,plan['environment'],lock,deadline=180)
        output=directory/'stdout.bin'
        assert result['exit_status']==0 and not (directory/'stderr.bin').read_bytes()
        assert output.stat().st_size==BYTES and process.sha(output)==EXPECTED
        target.parent.mkdir(parents=True,exist_ok=True);output.rename(target)
        process.save(directory/'input.json',dict(path=str(target),bytes=BYTES,sha256=EXPECTED,
            generator=str(source.relative_to(ROOT)),generator_sha256=process.sha(source),
            runtime_sha256=process.sha(Path(plan['runtime'])),preparation_only=True,
            benchmark_samples=0,full_payload_relocated_after_closed_process=True))
    print('Full input generated and verified; retained for subsequent stdin workloads')

if __name__=='__main__':main()
