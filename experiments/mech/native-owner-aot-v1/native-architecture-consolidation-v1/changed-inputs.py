"""Same-final-binary F/I changed-input checks with the retained direct oracle."""
from collections import Counter
import argparse
import fcntl
import uuid
from pathlib import Path
from study import HERE,WORKSPACE,process,read,source_state,subjects,inputs

def random_bases(n,seed):
    state=seed;result=[]
    for _ in range(n):
        state ^= state << 13;state &= (1<<64)-1
        state ^= state >> 7;state ^= state << 17;state &= (1<<64)-1
        result.append('ACGT'[state&3])
    return ''.join(result)


def expected(seq):
    # Direct string windows and Python counters; no packed keys, generated
    # hash layout, source graph or optimized compiler helper is reused.
    seq=seq.upper();parts=[]
    for width in (1,2):
        counts=Counter(seq[i:i+width] for i in range(len(seq)-width+1))
        total=sum(counts.values())
        parts.append('\n'.join(f'{key} {100*count/total:.3f}' for key,count in sorted(counts.items(),key=lambda p:(-p[1],p[0])))+'\n\n')
    for query in ['GGT','GGTA','GGTATT','GGTATTTTAATT','GGTATTTTAATTTATAGT']:
        width=len(query)
        parts.append(f'{sum(seq[i:i+width]==query for i in range(len(seq)-width+1))}\t{query}\n')
    return ''.join(parts).encode()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',default=uuid.uuid4().hex)
    args=parser.parse_args()
    assert args.run_id and all(c.isalnum() or c in '-_' for c in args.run_id)
    all_targets,pins,f,i=subjects();targets={s:all_targets[s] for s in ['F','I']}
    before=source_state();plan=read(HERE/'plan.json');_,policy,_=inputs()
    motif='GGTATTTTAATTTATAGT';rng=random_bases(8193,0x75d5b70ad086419f)
    cases=[('one-key-short','a'*31,7),('query-boundaries',motif*59+'ACGTT',11),('random-single-row',rng,8193),('random-short-rows',rng,1),('random-ordinary-rows',rng,60),('growth-and-partial-credit',random_bases(65541,0xb797f4f25f1c90ed),131),('repeated-wide-key',(motif*4000)[:65539],59)]
    out=HERE/('changed-inputs-'+args.run_id);out.mkdir(exist_ok=False)
    env=i['environment']
    report=dict(status='checking',source=before,driver_sha256=process.sha(Path(__file__)),pins={s:pins[s] for s in targets},cases=[],benchmark_samples=0,scope='Fourteen exact F/I AOT processes, seven changed FASTA inputs, direct Python string-window oracle; correctness only.')
    process.save(out/'results.json',report)
    mutex=Path(plan['common_mutex']);assert mutex.is_file() and mutex.stat().st_ino==83858837
    with mutex.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,seq,width in cases:
            folder=out/name;folder.mkdir();seq=''.join(c.lower() if k%3==0 else c for k,c in enumerate(seq))
            payload='>ONE ignored\nACGT\n>THREEX decoy\nTTTT\n>THREE changed input\n'+'\n'.join(seq[k:k+width] for k in range(0,len(seq),width))+'\n'
            inp=folder/'input.fasta';inp.write_text(payload);want=folder/'expected.stdout';want.write_bytes(expected(seq))
            updates=sum(max(0,len(seq)-w+1) for w in [1,2,3,4,6,12,18])
            row=dict(name=name,bases=len(seq),row_width=width,input_sha256=process.sha(inp),expected_stdout_sha256=process.sha(want),expected_updates=updates,executions=[])
            for subject,binary in targets.items():
                assert process.sha(binary)==pins[subject]
                native=folder/(subject+'.native.json');receipt=process.execute([str(binary),str(policy),str(native),'--'],folder/subject,env,lock,stdin=inp,deadline=30,quantitative=False)
                assert receipt['exit_status']==0,(name,subject,receipt)
                assert (folder/subject/'stdout.bin').read_bytes()==want.read_bytes(),(name,subject)
                n=read(native);assert n['native_aot'] and not n['jit'] and n['policy']=='secured' and n['shutdown']=='completed'
                assert n['native_hash_table_updates']==n['native_packed_map_updates']==updates
                assert n['native_parallel_tasks']==7 and n['native_fused_string_map_bytes']==len(seq)
                row['executions'].append(dict(subject=subject,process_sha256=process.sha(folder/subject/'process.json'),native_sha256=process.sha(native),stdout_sha256=process.sha(folder/subject/'stdout.bin'),updates=updates))
            report['cases'].append(row);process.save(out/'results.json',report);print(name,'F/I oracle and',updates,'updates verified',flush=True)
    assert source_state()==before
    report.update(source_after=before,status='seven-independent-oracles-and-fourteen-pinned-AOT-executions-verified');process.save(out/'results.json',report)
if __name__=='__main__':main()
