"""Compile only an instrumented copy with the protected Rust toolchain/flags."""
import fcntl
from pathlib import Path
import sys
STUDY=Path(__file__).resolve().parent
HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
before=source_state();assert not before['status']
reference=read(HERE.parent/'native-hashmap-work-v1/rust-comparison-v2/results.json')
for library in reference['rust_libraries'].values():assert process.sha(Path(library['path']))==library['sha256']
assert reference['environment']['RUSTUP_TOOLCHAIN']=='nightly-2026-03-03'
original=Path(reference['rust_compile_command'][-3])
assert process.sha(original)=='47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
assert process.sha(HERE.parent/'native-hashmap-work-v1/.build/knucleotide-rust-7')=='f084777c37420ac822b4cfc1be72fa6b9bc8438d833f1647856d13b40d1ee763'
source=STUDY/'rust-instrumented.rs';binary=HERE/'.build/worker-cpu-rust'
command=reference['rust_compile_command'][:-3]+[str(source),'-o',str(binary)]
env=reference['environment'];out=STUDY/'build-rust-v1';out.mkdir(exist_ok=False)
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=process.execute(command,out/'build',env,lock,deadline=300,quantitative=False)
    row=dict(status='diagnostic-rust-built' if result['exit_status']==0 else 'failed',source_before=before,source_after=source_state(),environment=env,binary=str(binary),source_sha256=process.sha(source),probe_sha256=process.sha(STUDY/'worker_probe.rs'),driver_sha256=process.sha(Path(__file__)),primary_benchmark_samples=0)
    if result['exit_status']==0:row['binary_sha256']=process.sha(binary)
    process.save(out/'results.json',row)
    assert source_state()==before and result['exit_status']==0
    print('Instrumented Rust copy built; protected source and binary unchanged',flush=True)
