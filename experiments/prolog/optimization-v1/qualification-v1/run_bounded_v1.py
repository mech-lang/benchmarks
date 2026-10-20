"""Bounded continuation of the successful frozen SWI source/QLF build packet."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
from native_process import atom,now,sha,success

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SHARED=HERE/'run_qualification_v3.py'
SHARED_SHA='853c134795269319d42616ea3cf94d101ffb65d104c2feccfa11fb85626245c6'
BASE_PLAN=HERE/'execution-plan-v3.json'
BUILDS=HERE/'build-native-v3/report.json'
PLAN=HERE/'bounded-plan-v1.json'
LOCK='/tmp/mech-clbg-timing.lock'


def require(condition,message):
    if not condition:raise ValueError(message)


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def shared_module():
    require(sha(SHARED)==SHARED_SHA,'Frozen build/reader helper changed')
    spec=importlib.util.spec_from_file_location('prolog_spectral_frozen_qualification_v3',SHARED)
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    require(shared.ROOT==ROOT and shared.HERE==HERE and shared.PLAN==BASE_PLAN,'Frozen helper roots changed')
    return shared


def verify(shared):
    base=shared.verify(load(BASE_PLAN));builds=load(BUILDS)
    require(builds['status']=='PASSED' and builds['plan']==ref(BASE_PLAN) and builds['active'] is None,'Matching successful builds required')
    for program in builds['programs'].values():
        shared.check_ref(program['source_qlf_pin']);shared.check_ref(program['support_qlf_pin'])
    packet=load(PLAN)
    require(packet['schema']=='prolog-spectral-bounded-continuation-plan.v1' and packet['controller']==ref(__file__)
        and packet['frozen_helper']==ref(SHARED) and packet['foundation']==ref(BASE_PLAN) and packet['builds']==ref(BUILDS),'Bounded plan binding differs')
    for path,digest in packet['pins'].items():shared.check_ref(dict(path=path,sha256=digest))
    return base,builds,packet


def prepare(shared):
    require(not PLAN.exists(),'Exclusive bounded plan required')
    shared.verify(load(BASE_PLAN));builds=load(BUILDS)
    require(builds['status']=='PASSED' and builds['plan']==ref(BASE_PLAN),'Complete successful builds required')
    files=[Path(__file__),SHARED,BASE_PLAN,BUILDS]
    files.extend(p for p in (HERE/'build-native-v3').rglob('*') if p.is_file())
    for program in builds['programs'].values():
        for field in ['source_qlf_pin','support_qlf_pin']:files.append(shared.check_ref(program[field]))
    packet=dict(schema='prolog-spectral-bounded-continuation-plan.v1',status='PREPARED-NO-EXECUTION',controller=ref(__file__),
        frozen_helper=ref(SHARED),foundation=ref(BASE_PLAN),builds=ref(BUILDS),pins={str(p.relative_to(ROOT)):sha(p) for p in files},
        correction='Build controller v3 bounded-entry literal referenced the first stopped build. This separate additive entry binds the actual successful v3 build; all previous controllers/plans/attempts remain unchanged.',
        quantitative_benchmark=False,chart_admission=False)
    atom(PLAN,packet);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN))))


def execute(shared,lock):
    base,builds,packet=verify(shared)
    output=HERE/'bounded-v3';require(not output.exists(),'Fresh bounded attempt required');output.mkdir()
    report=dict(schema='prolog-spectral-bounded-qualification.v1',status='RUNNING',plan=ref(PLAN),foundation=ref(BASE_PLAN),builds=ref(BUILDS),
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,started_utc=now(),cases=[],active=None,quantitative_benchmark=False,chart_admission=False)
    atom(output/'report.json',report)
    try:
        expectations={case['n']:(shared.CORPUS/case['expected']['path']).read_bytes() for case in base['bounded']}
        for n in sorted(set(expectations)|set(base['additional_n'])):
            parent_bytes=None
            for name in shared.NAMES:
                program=base['programs'][name];report['active']=dict(source=name,n=n);atom(output/'report.json',report)
                directory=output/('n-'+str(n)+'-'+name)
                row=shared.native(base,program['run_argv']+[str(n)],directory,lock)
                report['cases'].append(dict(source=name,n=n,process=row));atom(output/'report.json',report);success(row)
                raw=(directory/'stdout.bin').read_bytes();require(row['stderr']['bytes']==0,'Bounded stderr retained; qualification stopped')
                if name=='parent':parent_bytes=raw
                expected=expectations.get(n,parent_bytes)
                require(raw==expected,'Bounded complete output differs: '+name+' N='+str(n))
                require(re.fullmatch(rb'[0-9]+\.[0-9]{9}\n',raw) is not None,'Malformed norm output')
                report['cases'][-1].update(exact_output_valid=True,shared_reference=n in expectations)
                print(json.dumps(dict(source=name,n=n,status='PASS')),flush=True)
        qlfs=[base['programs'][name]['source_qlf'] for name in shared.NAMES]
        directory=output/'state-work-probe'
        row=shared.native(base,[str(ROOT/base['binary']['path'])]+shared.FLAGS+['-l',str(HERE/'state_probe.pl'),'-g','prolog_spectral_state_probe:main','--']+qlfs,directory,lock,timeout=180)
        report['state_work_process']=row;atom(output/'report.json',report);success(row)
        require(row['stderr']['bytes']==0,'State probe warning retained')
        state=load(directory/'stdout.bin')
        require(state['status']=='PASSED' and len(state['vectors'])==144 and len(state['geometry'])==12 and len(state['work'])==6,'State probe inventory differs')
        report['state_work']=ref(directory/'stdout.bin')
        counts=shared.count_sources(base,output,lock);atom(output/'source-counts.json',counts);report['source_counts']=ref(output/'source-counts.json')
        verify(shared);report.update(status='PASSED',active=None,finished_utc=now(),source_runtime_qlf_pins_unchanged=True)
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)
    print(json.dumps(dict(status='PASSED-BOUNDED',report=ref(output/'report.json'),cases=len(report['cases']))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    shared=shared_module()
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.prepare:prepare(shared)
        else:execute(shared,lock)


if __name__=='__main__':main()
