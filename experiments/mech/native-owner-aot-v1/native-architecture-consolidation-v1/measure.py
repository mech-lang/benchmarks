"""The predeclared 192-process F/I/W/R campaign; no warmups or exclusions."""
from collections import Counter
import fcntl,json,statistics,subprocess
from pathlib import Path
from study import HERE,ROOT,process,read,source_state,subjects,inputs,check_native
from campaign import prerequisites

def main():
    plan=read(HERE/'plan.json');targets,pins,f,i=prerequisites(plan);before=source_state()
    assert plan['final_compiler_source']==before['commit'] and plan['subject_pins']==pins
    assert plan['status']=='frozen-before-first-primary-sample'
    gate=read(HERE/'qualification.json')
    assert gate['source']==before and gate['proceed_to_primary']
    assert process.sha(HERE/'qualification.json')==plan['qualification_sha256']
    for path,digest in plan['controller_pins'].items():assert process.sha(ROOT/path)==digest,path
    assert plan['bootstrap_seed']==2026102595 and plan['bootstrap_resamples']==20000
    assert plan['primary_observations']==192 and plan['warmups']==plan['excluded_outliers']==0
    assert plan['acceptance_upper_95_percent']=={'F/I':1.0,'F/W':1.0,'F/R':0.0}
    assert plan['session_2']==list(reversed(plan['session_1']))
    for session in [1,2]:
        orders=plan[f'session_{session}'];assert len(orders)==24
        assert all(len(row)==4 and set(row)==set(targets) for row in orders)
        assert all(Counter(row[p] for row in orders)==dict.fromkeys(targets,6) for p in range(4))
        adjacent=Counter((a,b) for row in orders for a,b in zip(row,row[1:]));assert len(adjacent)==12 and set(adjacent.values())=={6}
    git=lambda *a:subprocess.check_output(['git','-C',str(ROOT),*a],text=True).strip()
    revision=git('rev-parse','HEAD');assert not git('status','--porcelain')
    inp,policy,data=inputs();env=i['environment']
    mutex=Path(plan['common_mutex']);assert mutex.is_file() and mutex.stat().st_ino==83858837
    with mutex.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for session in [1,2]:
            out=HERE/f'primary-session-{session}';out.mkdir(exist_ok=False)
            orders=plan[f'session_{session}']
            report=dict(status='running',source=before,evidence_revision=revision,session=session,orders=orders,pins=pins,plan_sha256=process.sha(HERE/'plan.json'),driver_sha256=process.sha(Path(__file__)),controller_sha256=process.sha(ROOT/'experiments/janet/knucleotide-bytes-v1/process.py'),input_sha256=plan['input_sha256'],policy_sha256=plan['policy_sha256'],canonical_data_sha256=plan['canonical_data_sha256'],source_sha256=plan['source_sha256'],bytecode_sha256=plan['bytecode_sha256'],excluded_warmups=0,excluded_outliers=0,samples=[],scope='Complete secured startup through exit, exact retained controls, fixed balanced serial orders, all observations retained.')
            process.save(out/'results.json',report)
            for index,order in enumerate(orders):
                for position,subject in enumerate(order):
                    assert process.sha(targets[subject])==pins[subject]
                    folder=out/f'{index:02d}-{position}-{subject}';native=out/(folder.name+'.native.json')
                    command=[str(targets[subject])]+([] if subject=='R' else [str(policy),str(native),'--'])
                    receipt=process.execute(command,folder,env,lock,stdin=inp,deadline=30,quantitative=True)
                    assert receipt['exit_status']==0 and process.sha(folder/'stdout.bin')==plan['output_sha256'],(session,index,subject)
                    counters=check_native(native) if subject!='R' else None
                    report['samples'].append(dict(order=index,position=position,subject=subject,seconds=receipt['elapsed_seconds'],maximum_rss_bytes=receipt['maximum_rss_bytes'],process=str((folder/'process.json').relative_to(HERE)),process_sha256=process.sha(folder/'process.json'),stdout_sha256=plan['output_sha256'],native_sha256=process.sha(native) if counters else None,native=counters,verified=True))
                    process.save(out/'results.json',report)
                print('session',session,'order',index+1,'of',len(orders),'verified',flush=True)
            assert source_state()==before and process.sha(data)==plan['canonical_data_sha256'] and git('rev-parse','HEAD')==revision
            for path,digest in plan['controller_pins'].items():assert process.sha(ROOT/path)==digest,path
            report.update(status='all-96-complete-processes-output-counters-pins-and-cleanup-verified',source_after=before,median_seconds={s:statistics.median(x['seconds'] for x in report['samples'] if x['subject']==s) for s in targets},median_peak_rss_bytes={s:statistics.median(x['maximum_rss_bytes'] for x in report['samples'] if x['subject']==s) for s in targets})
            process.save(out/'results.json',report)
            print('session',session,'complete',report['median_seconds'],flush=True)
if __name__=='__main__':main()
