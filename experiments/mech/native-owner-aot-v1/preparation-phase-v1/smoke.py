"""Qualify phase boundaries and complete prefix semantics before full captures."""
import fcntl
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state
from parse import parse
build=read(STUDY/'build-offsets-v2/results.json');spec=read(STUDY/'build-offsets.json')
before=source_state();assert before['commit']==spec['source_commit'] and not before['status']
binary=Path(build['binary']);assert process.sha(binary)==build['binary_sha256']
inp=HERE/'rust-span-diagnostic-v2/input.fasta';policy=HERE/'full-timing-v1/launch.json'
assert process.sha(inp)=='e9a7a743b0cda5b46863eaec0483370c3eb2cdb20c6a0f24c2bfac776abfe4bb'
out=STUDY/'smoke-v1';native=STUDY/'smoke-v1.native.json'
with Path(PLAN['common_mutex']).open('a+') as lock:
 assert Path(PLAN['common_mutex']).stat().st_ino==83858837
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=process.execute([str(binary),str(policy),str(native),'--'],out,build['environment'],lock,stdin=inp,deadline=30,quantitative=False)
 assert r['exit_status']==0 and process.sha(out/'stdout.bin')=='f14defab6d0218adf873d1b3c9ecde472b9c8c7141da7be51ea0c9877a6cebfa'
 n=read(native);assert n['native_hash_table_updates']==n['native_packed_map_updates']==6999961 and n['native_parallel_tasks']==7 and n['policy']=='secured' and n['shutdown']=='completed'
 records=parse(out/'stderr.bin');process.save(out/'phases.json',records)
 assert records['rows']['direct_rows']==inp.read_bytes().count(b'\n')
 assert source_state()==before
 process.save(out/'qualification.json',dict(status='prefix-output-rows-phases-and-original-updates-verified',source_before=before,source_after=before,binary_sha256=process.sha(binary),driver_sha256=process.sha(Path(__file__)),parser_sha256=process.sha(STUDY/'parse.py'),primary_benchmark_samples=0))
 print('Diagnostic prefix output, row coverage and phase order verified',flush=True)
