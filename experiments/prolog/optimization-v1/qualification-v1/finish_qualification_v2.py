"""Additive clean-loader state/read-owner continuation; preserve all prior attempts."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
from native_process import atom,now,sha,success

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SHARED=HERE/'run_qualification_v3.py'
SHARED_SHA='853c134795269319d42616ea3cf94d101ffb65d104c2feccfa11fb85626245c6'
BASE_PLAN=HERE/'execution-plan-v3.json'
BUILD=HERE/'build-native-v3/report.json'
BOUNDED=HERE/'bounded-v3/report.json'
PLAN=HERE/'completion-plan-v2.json'
PROBE=HERE/'state_probe_v3.pl'
LOCK='/tmp/mech-clbg-timing.lock'


def require(condition,message):
    if not condition:raise ValueError(message)


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def shared_module():
    require(sha(SHARED)==SHARED_SHA,'Frozen helper changed')
    spec=importlib.util.spec_from_file_location('prolog_spectral_completion_frozen_v3',SHARED)
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    require(shared.ROOT==ROOT and shared.HERE==HERE and shared.PLAN==BASE_PLAN,'Frozen helper roots differ');return shared


def prerequisites(shared):
    base=shared.verify(load(BASE_PLAN));build=load(BUILD);bounded=load(BOUNDED)
    require(build['status']=='PASSED' and build['plan']==ref(BASE_PLAN) and build['active'] is None,'Complete build required')
    for program in build['programs'].values():
        shared.check_ref(program['source_qlf_pin']);shared.check_ref(program['support_qlf_pin'])
    require(bounded['schema']=='prolog-spectral-bounded-qualification.v1' and bounded['status']=='FAILED'
        and bounded['error']=="ValueError('State probe warning retained')" and bounded['builds']==ref(BUILD)
        and len(bounded['cases'])==39,'Exact stopped bounded attempt required')
    expected_ns=[0,1,2,3,5,7,8,9,10,15,16,17,100]
    require([(row['n'],row['source']) for row in bounded['cases']]==[(n,name) for n in expected_ns for name in shared.NAMES], 'Bounded case inventory differs')
    expected={case['n']:(shared.CORPUS/case['expected']['path']).read_bytes() for case in base['bounded']}
    for row in bounded['cases']:
        process=row['process'];success(process);require(row['exact_output_valid'] is True and process['stderr']['bytes']==0,'Failed bounded row')
        directory=Path(process['stdout']['path']).parent;raw=load(directory/'process.json')
        require(raw==process and process['command']==base['programs'][row['source']]['run_argv']+[str(row['n'])],'Raw bounded command/process differs')
        for stream in ['stdout','stderr']:
            path=Path(process[stream]['path']);require(path.stat().st_size==process[stream]['bytes'] and sha(path)==process[stream]['sha256'],'Raw bounded stream differs')
        output=Path(process['stdout']['path']).read_bytes()
        if row['source']=='parent':expected.setdefault(row['n'],output)
        require(output==expected[row['n']],'Replayed bounded bytes differ')
    return base,build,bounded


def prepare(shared):
    require(not PLAN.exists(),'Fresh completion plan required');prerequisites(shared)
    files=[Path(__file__),SHARED,BASE_PLAN,BUILD,BOUNDED,PROBE,HERE/'run_bounded_v1.py',HERE/'bounded-plan-v1.json']
    files.extend([HERE/'finish_qualification_v1.py',HERE/'completion-plan-v1.json',HERE/'state_probe_v2.pl'])
    files.extend(p for p in (HERE/'completed-v1').rglob('*') if p.is_file())
    files.extend(p for p in (HERE/'build-native-v3').rglob('*') if p.is_file())
    files.extend(p for p in (HERE/'bounded-v3').rglob('*') if p.is_file())
    plan=dict(schema='prolog-spectral-qualification-completion-plan.v1',status='PREPARED-NO-EXECUTION',controller=ref(__file__),
        frozen_helper=ref(SHARED),foundation=ref(BASE_PLAN),builds=ref(BUILD),complete_output_attempt=ref(BOUNDED),
        state_probe=ref(PROBE),pins={str(p.relative_to(ROOT)):sha(p) for p in files},
        correction='Each production QLF is loaded alone in a fresh native process. Exact17-digit component captures are compared against parent offline; this avoids importing multiple same-name generic support copies. Previous diagnostic-bearing loader attempts remain failed evidence.',
        quantitative_benchmark=False,chart_admission=False)
    atom(PLAN,plan);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN))))


def verify(shared):
    base,build,bounded=prerequisites(shared);plan=load(PLAN)
    require(plan['controller']==ref(__file__) and plan['foundation']==ref(BASE_PLAN) and plan['builds']==ref(BUILD)
        and plan['complete_output_attempt']==ref(BOUNDED) and plan['state_probe']==ref(PROBE),'Completion bindings differ')
    for path,digest in plan['pins'].items():shared.check_ref(dict(path=path,sha256=digest))
    return base,build,bounded,plan


def run(shared,lock):
    base,build,bounded,plan=verify(shared)
    output=HERE/'completed-v2';require(not output.exists(),'Fresh completion attempt required');output.mkdir()
    report=dict(schema='prolog-spectral-completed-bounded-qualification.v1',status='RUNNING',plan=ref(PLAN),foundation=ref(BASE_PLAN),
        builds=ref(BUILD),complete_output_attempt=ref(BOUNDED),started_utc=now(),common_mutex_inode=os.fstat(lock.fileno()).st_ino,
        quantitative_benchmark=False,chart_admission=False,attempts=[])
    atom(output/'report.json',report)
    try:
        states={}
        for name in shared.NAMES:
            program=base['programs'][name];directory=output/('state-work-'+name)
            command=[str(ROOT/base['binary']['path'])]+shared.FLAGS+['-l',str(PROBE),'-g','prolog_spectral_state_probe:main','--',program['source_qlf'],program['module']]
            row=shared.native(base,command,directory,lock,timeout=180);report['attempts'].append(row);atom(output/'report.json',report)
            success(row);require(row['stderr']['bytes']==0,'Single-QLF state probe stderr retained; stopped')
            state=load(directory/'stdout.bin')
            require(state['schema']=='prolog-spectral-single-qlf-state-work-capture.v1' and state['status']=='CAPTURED'
                and state['module']==program['module'] and len(state['vectors'])==72 and len(state['work'])==2
                and len(state['geometry'])==(12 if name=='blocks8-specialized' else 0),'State/work inventory differs')
            require(state['version']==[10,0,2] and state['gc'] is True and state['bounded'] is False,'State runtime differs')
            states[name]=state
        for name in ['serial-specialized','blocks8-specialized']:
            require(states[name]['vectors']==states['parent']['vectors'],'Exact17-digit component parent comparison failed: '+name)
        report['state_work']={name:ref(output/('state-work-'+name)/'stdout.bin') for name in shared.NAMES}
        report['vector_validation']='Exact equality of72 full component lists per candidate against parent,17 significant decimal digits per component; includes signed zero text and no tolerance.'
        counts=shared.count_sources(base,output,lock);atom(output/'source-counts.json',counts);report['source_counts']=ref(output/'source-counts.json')
        verify(shared);report.update(status='PASSED',finished_utc=now(),complete_output_cases=39,vector_comparisons=144,geometry_cases=12,work_cases=6,
            source_runtime_qlf_pins_unchanged=True,parallel_source_count_certified=counts['parallel_certified'])
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)
    print(json.dumps(dict(status=report['status'],report=ref(output/'report.json'))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');args=parser.parse_args();shared=shared_module()
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.prepare:prepare(shared)
        else:run(shared,lock)


if __name__=='__main__':main()
