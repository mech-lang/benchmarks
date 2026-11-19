#!/usr/bin/env python3
"""Strong scaling of a fixed Mech workload across independent, supervised processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from benchmark_suite import (ROOT,SCHEMA,archive_evidence,campaign_lock,digest,environment,equal,file_digest,invoke,
    load_catalog,preserve_worker,save,seal_evidence,summarize,verify_response,measurement_response,worker_provenance)
from suite_oracle import outputs


def group(worker, case, directory, verify, timeout):
    workers=case['measurement']['workers'];schedule=case['measurement']['schedule']
    total=case['measurement']['total_turns']
    if total%workers or (total//workers)%len(schedule):raise ValueError('partitions must preserve complete schedule cycles')
    count=len(schedule)*2 if verify else total//workers
    request={'protocol':1,'action':'verify' if verify else 'measure','source':(ROOT/case['source']).read_text(),
        'backend':'source','output':'result','schedule':schedule,'warmup':case['measurement']['warmup'],
        'iterations':count,'retain_snapshots':False,'abort_before_accept':False}
    expected=outputs(case,len(schedule)*2)
    if file_digest(worker['binary'])!=worker['binary_sha256']:raise ValueError('worker binary changed')
    # Fixed total work, including process startup and destruction. Supervising threads only wait on owned processes.
    started=time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(invoke,[worker['binary']],request,directory/f'worker-{i}',timeout) for i in range(workers)]
        responses=[future.result() for future in futures]
    seconds=time.perf_counter()-started
    if file_digest(worker['binary'])!=worker['binary_sha256']:raise ValueError('worker binary changed during group')
    for response in responses:
        status,reason=verify_response(response,expected,case) if verify else measurement_response(response,expected[-1],{**case,'measurement':{**case['measurement'],'primary_metric':'resident_turn_seconds'}},count)
        if status!='ok':raise ValueError(f'worker group failed: {reason}')
    metrics={'worker_group_process_seconds':seconds,'total_turns':count*workers,
        'accepted_turns_per_second':count*workers/seconds,
        'sum_worker_execution_block_seconds':sum(r['metrics']['execution_block_seconds'] for r in responses),
        'execution_allocations':sum(r['metrics']['execution_allocations'] for r in responses),
        'managed_after_drop_bytes':sum(r['metrics']['managed_after_drop_bytes'] for r in responses)}
    receipt={'outcome':'ok','metrics':metrics,'outputs':[r['final_output'] for r in responses],
        'worker_iterations':[r['iterations'] for r in responses],'workers':workers,
        'verification_schedule_cycles':2 if verify else None,
        'worker_observations':[{'path':f'worker-{i}/supervised.json','sha256':file_digest(directory/f'worker-{i}/supervised.json')} for i in range(workers)]}
    save(directory/'supervised.json',receipt)
    return receipt


def run(args):
    worker=worker_provenance(args.worker);output=args.output.resolve()
    if output.exists():raise ValueError('choose a new campaign directory')
    host=environment();cases=[c for c in load_catalog()['cases'] if c['family']=='concurrency']
    campaign={'schema':SCHEMA,'id':output.name,'started_at':datetime.now(timezone.utc).isoformat(),'profile':'strong-scaling',
        'sampling':{'forks':args.forks},'environment':host,'environment_hash':digest(host),'workers':{'candidate':worker},
        'performance_gate':False,'results':[],'order':[],'comparisons':[],'complete':False,
        'harness_sha256':{n:file_digest(ROOT/'tools'/n) for n in ('run_concurrent.py','suite_oracle.py','extended_oracles.py','benchmark_suite.py')}}
    with campaign_lock(ROOT/'.local'):
        output.mkdir(parents=True);preserve_worker(worker,output/'workers/candidate')
        for case in cases:
            source=(ROOT/case['source']).read_text()
            record={'case_id':case['id'],'title':case['title'],'family':case['family'],'backend':'process-workers','lane':'candidate',
                'revision':worker['revision'],'progress':'implemented','capability':'unknown','outcome':'pending',
                'feature_profile':{'profile':worker['feature_profile'],'native_generation':worker.get('native_generation',False)},
                'task':case['task'],'measurement':case['measurement'],'source':source,'source_sha256':file_digest(ROOT/case['source']),
                'task_hash':digest(case['task']),'measurement_hash':digest(case['measurement']),'environment_hash':digest(host),'samples':[]}
            campaign['results'].append(record);save(output/'campaign.json',campaign);save(output/'fixtures'/(case['id']+'.json'),case)
            print('Verify '+case['title'],flush=True)
            verified=group(worker,case,output/'raw'/case['id']/'verify',True,args.timeout)
            record.update(progress='verified',capability='supported',outcome='ok',verification={'outcome':'ok','reason':'Every independent worker verified all distinct pure inputs and the no-execution control. Measured partitions preserve complete schedule cycles; every accepted turn count and endpoint is checked.','outputs':verified['outputs'],'raw':f'raw/{case["id"]}/verify'})
        # Rotate group order across forks, rather than always giving the same worker count first place.
        for fork in range(args.forks):
            for case in cases[fork%len(cases):]+cases[:fork%len(cases)]:
                print(f'Measure {case["title"]} / fork {fork+1}',flush=True)
                record=next(r for r in campaign['results'] if r['case_id']==case['id'])
                relative=f'raw/{case["id"]}/fork-{fork+1}'
                result=group(worker,case,output/relative,False,args.timeout)
                record['samples'].append({'fork':fork,'raw':relative,'metrics':result['metrics'],'final_output':result['outputs']})
                campaign['order'].append({'case_id':case['id'],'backend':'process-workers','lane':'candidate','fork':fork})
                save(output/'campaign.json',campaign)
        for record in campaign['results']:record.update(progress='measured',summary=summarize(record['samples']))
        campaign.update(complete=True,outcome='ok',finished_at=datetime.now(timezone.utc).isoformat());save(output/'campaign.json',campaign)
        lines=['# Mech worker scaling','', 'Fixed total work: 196,608 accepted pure numerical turns, split evenly across 1, 2 and 4 independent Mech processes. Each application worker uses one execution thread. The group timer includes supervisor startup, source compilation, activation, warmup, accepted turns, output observation and complete child-process teardown. It is a process-scaling result; it makes no shared-state or parallel-kernel claim.', '', '| Workers | Median complete group seconds | Accepted turns/s |','| ---: | ---: | ---: |']
        for r in campaign['results']:lines.append(f'| {r["measurement"]["workers"]} | {r["summary"]["worker_group_process_seconds"]["median"]:.6f} | {r["summary"]["accepted_turns_per_second"]["median"]:.1f} |')
        (output/'report.md').write_text('\n'.join(lines)+'\n');seal_evidence(output);archive_evidence(output)
        print(output/'report.md',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--forks',type=int,default=3);p.add_argument('--timeout',type=float,default=300)
    args=p.parse_args()
    if args.forks<1 or args.timeout<=0:p.error('positive forks and deadline required')
    try:run(args)
    except (OSError,ValueError) as error:p.exit(1,f'Worker scaling failed: {error}\n')
