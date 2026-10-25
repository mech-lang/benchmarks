"""Qualify one diagnostic copy on the retained prefix before full captures."""
import fcntl
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent
HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
from parse import parse
subject=sys.argv[1]
assert subject in ('aligned','facts','rust')
build=read(STUDY/('build-'+subject+('-v1' if subject=='rust' else '-v2'))/'results.json')
before=source_state();assert not before['status']
binary=Path(build['binary']);assert process.sha(binary)==build['binary_sha256']
inp=HERE/'rust-span-diagnostic-v2/input.fasta';policy=HERE/'full-timing-v1/launch.json'
assert process.sha(inp)=='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
assert process.sha(policy)=='3110571a37e660392e06494f51b5185e53b9df73ce28f7fb2fd0daf57cdb43ec'
out=STUDY/('smoke-'+subject+'-v1');native=STUDY/('smoke-'+subject+'-v1.native.json')
command=[str(binary)]+([] if subject=='rust' else [str(policy),str(native),'--'])
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=process.execute(command,out,build['environment'],lock,stdin=inp,deadline=30,quantitative=False)
    assert result['exit_status']==0
    assert process.sha(out/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
    if subject!='rust':
        n=read(native);assert n['native_hash_table_updates']==n['native_packed_map_updates']==6999961
        assert n['native_parallel_tasks']==7 and 1<=n['native_parallel_peak_workers']<=7
        assert n['policy']=='secured' and n['shutdown']=='completed'
    records=parse(out/'stderr.bin',subject)
    process.save(out/'traces.json',records)
    assert source_state()==before
    process.save(out/'qualification.json',dict(status='prefix-output-and-eight-complete-traces-verified',source_before=before,source_after=before,build_sha256=process.sha(STUDY/('build-'+subject+('-v1' if subject=='rust' else '-v2'))/'results.json'),binary_sha256=process.sha(binary),driver_sha256=process.sha(Path(__file__)),parser_sha256=process.sha(STUDY/'parse.py'),traces_sha256=process.sha(out/'traces.json'),primary_benchmark_samples=0))
    print(subject,'prefix and all seven widths plus main trace verified',flush=True)
