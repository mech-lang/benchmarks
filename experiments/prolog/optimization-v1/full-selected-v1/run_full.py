"""Three matched complete-process rounds atN5500 for the preselected parent/eight-block pair."""
import argparse
import ast
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import sys
from process import atom,now,one,sha

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PILOT=HERE.parent/'pilot-700-v1'
HELPER=PILOT/'run_pilot.py'
HELPER_SHA='8f554f3278e49dd27665e3f03b821783f19b99cebd099e02d42e39ee5e8df3b5'
PILOT_PLAN=PILOT/'plan.json'
PILOT_PLAN_SHA='c9d368e2a1db0aecd190fd238cf17d101b044eae485872756a676a5ee89c7bc4'
PILOT_REPORT=PILOT/'pilot-v1/report.json'
PILOT_SHA='b01458f60a0b5bee4c6bccb47278f7b1062367a701ecde18052e9f50b00ed9c9'
SHARED_REFERENCE=ROOT/'tools/qualification/lean_run.py'
SHARED_REFERENCE_SHA='313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
PLAN=HERE/'plan.json'
EXPECTED=HERE/'expected.stdout'
EXPECTED_BYTES=b'1.274224153\n'
EXPECTED_SHA='f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'
SOURCE_REVISION='612fb31e030be207779c03cddb00a16af56f0173'
SELECTED=['parent','blocks8-specialized']
POOL=['parent','serial-specialized','blocks8-specialized']
PILOT_SECONDS={'parent':2.963027875,'blocks8-specialized':0.666657,'serial-specialized':2.727397041}
N=5500
ROUNDS=3
SEED=20261020
LOCK='/tmp/mech-clbg-timing.lock'
PYTHON='/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'


def require(condition,message):
    if not condition:raise ValueError(message)


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def helper_module():
    require(sha(HELPER)==HELPER_SHA and sha(PILOT_PLAN)==PILOT_PLAN_SHA,'Frozen pilot controller/plan differs')
    require(sha(HERE/'process.py')==sha(PILOT/'process.py'),'Complete-process observer differs')
    spec=importlib.util.spec_from_file_location('prolog_full_frozen_pilot',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    require(helper.ROOT==ROOT and helper.HERE==PILOT and helper.NAMES==POOL and helper.N==700,'Frozen helper constants differ')
    return helper


def check_pilot(base):
    require(sha(PILOT_REPORT)==PILOT_SHA,'Sealed pilot report differs')
    report=load(PILOT_REPORT)
    require(report['schema']=='prolog-spectral-pilot700-execution.v1' and report['status']=='PASSED' and report['plan']==ref(PILOT_PLAN)
        and report['n']==700 and report['rounds']==1 and report['seconds']==PILOT_SECONDS
        and report['exact_parent_output_match'] is True and report['pins_unchanged'] is True
        and len(report['cases'])==3 and report['new_observations']==3,'Exact successful pilot inventory differs')
    require(sorted(row['source'] for row in report['cases'])==sorted(POOL),'Pilot source pool differs')
    for row in report['cases']:
        program=base['programs'][row['source']]
        require(row['output_valid'] is True and row['n']==700 and row['sample']==1 and row['exit_code']==0
            and not row['timed_out'] and not row['remaining_process_group'] and row['stderr']['bytes']==0
            and row['command']==program['run_argv']+['700'] and row['source_sha256']==program['source']['sha256'],'Pilot row differs')
        path=Path(row['stdout']['path']).with_name('process.json');raw=load(path)
        require(all(row.get(key)==value for key,value in raw.items()),'Pilot raw process differs')
        for stream in ['stdout','stderr']:
            path=Path(row[stream]['path']);require(path.stat().st_size==row[stream]['bytes'] and sha(path)==row[stream]['sha256'],'Pilot stream differs')
    return report


def reference_check():
    require(sha(SHARED_REFERENCE)==SHARED_REFERENCE_SHA,'Established full-reference source changed')
    module=ast.parse(SHARED_REFERENCE.read_text())
    full=next(ast.literal_eval(node.value) for node in module.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=='FULL' for target in node.targets))
    require(full['spectralnorm']==(N,12,EXPECTED_SHA),'Established full reference tuple differs')
    require(EXPECTED.read_bytes()==EXPECTED_BYTES and sha(EXPECTED)==EXPECTED_SHA,'Complete full reference bytes differ')


def orders():
    rng=random.Random(SEED);result=[]
    for sample in range(1,ROUNDS+1):
        order=SELECTED.copy();rng.shuffle(order);result.append(dict(sample=sample,n=N,sources=order))
    return result


def prepare(helper):
    require(not PLAN.exists() and not EXPECTED.exists(),'Exclusive new full plan required')
    base=load(PILOT_PLAN);pilot=check_pilot(base)
    require(min((name for name in POOL if name!='parent'),key=lambda name:PILOT_SECONDS[name])=='blocks8-specialized','Preselected source differs')
    EXPECTED.write_bytes(EXPECTED_BYTES);reference_check()
    pins=dict(base['pins'])
    files=[Path(__file__),HERE/'process.py',HELPER,PILOT_PLAN,PILOT_REPORT,SHARED_REFERENCE,EXPECTED]
    files.extend(p for p in (PILOT/'pilot-v1').rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp'))
    for path in files:pins[str(path.relative_to(ROOT))]=sha(path)
    plan=dict(schema='prolog-spectral-selected-full-plan.v1',status='PREPARED-NO-EXECUTION',controller=ref(__file__),
        process_helper=ref(HERE/'process.py'),frozen_pilot_helper=ref(HELPER),pilot=ref(PILOT_REPORT),pilot_plan=ref(PILOT_PLAN),
        foundation=base['foundation'],builds=base['builds'],bounded=base['bounded'],runtime=base['runtime'],binary=base['binary'],
        environment=base['environment'],flags=base['flags'],programs=base['programs'],pins=pins,python=base['python'],source_revision=SOURCE_REVISION,
        sources=SELECTED,retained_pilot_pool=POOL,n=N,rounds=ROUNDS,order_seed=SEED,orders=orders(),
        preselection=dict(status='declared-before-full-execution',basis='All three preserved one-observationN700 pilots',
            pilot_seconds=PILOT_SECONDS,selected_sources=SELECTED,omitted_full_source='serial-specialized',
            rationale='Retain unchanged parent as matched control and the lowest observed candidate pilot time.',
            limit='Pilot does not establish full-size ranking of the omitted source or global optimality; all full comparison claims require these six observations.'),
        expected=dict(path=ref(EXPECTED),bytes=12,sha256=EXPECTED_SHA,established_reference_source=ref(SHARED_REFERENCE)),
        required_work=dict(power_iterations=10,ata_applications=20,matrix_vector_products=40,coefficient_calls_per_process=1210000000,
            coefficient_calls_formula='40*5500*5500',matrix_cache=False,parallel_worker_limit=8,
            evidence='Exact production sources/QLFs plus existing bounded native work wrappers; full processes contain no wrappers/instrumentation.'),
        retained_source_counts=base['retained_source_counts'],common_mutex=LOCK,new_observations=0,chart_admission=False,
        output_rule='Exit0, no timeout/process-group survivor/stderr, complete12bytes exactly equal established full reference; exact parent equality retained for all rounds.',
        timing_boundary=base['timing_boundary'],inference_limit='Three matched full observations per source, all retained; report medians/dispersion without claiming global optimality.')
    atom(PLAN,plan);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN),pins=len(pins),orders=plan['orders'])))


def verify(helper):
    base=helper.verify();check_pilot(base);reference_check();plan=load(PLAN)
    require(plan['schema']=='prolog-spectral-selected-full-plan.v1' and plan['status']=='PREPARED-NO-EXECUTION'
        and plan['controller']==ref(__file__) and plan['process_helper']==ref(HERE/'process.py')
        and plan['frozen_pilot_helper']==ref(HELPER) and plan['pilot']==ref(PILOT_REPORT)
        and plan['pilot_plan']==ref(PILOT_PLAN),'Full plan binding differs')
    require(plan['n']==N and plan['rounds']==ROUNDS and plan['sources']==SELECTED and plan['retained_pilot_pool']==POOL
        and plan['orders']==orders() and plan['source_revision']==SOURCE_REVISION,'Full schedule/source differs')
    require(plan['programs']==base['programs'] and plan['binary']==base['binary'] and plan['environment']==base['environment']
        and plan['flags']==base['flags'] and plan['retained_source_counts']==base['retained_source_counts'],'Full runtime/build/count differs')
    require(plan['preselection']['pilot_seconds']==PILOT_SECONDS and plan['preselection']['selected_sources']==SELECTED
        and plan['preselection']['omitted_full_source']=='serial-specialized','Pilot selection differs')
    for path,digest in plan['pins'].items():helper.check_ref(dict(path=path,sha256=digest))
    return plan


def execute(args,plan,helper,lock):
    output=args.output.resolve();require(output.is_relative_to(HERE) and not output.exists(),'Exclusive fresh full output directory required')
    helper.competition();helper.power();output.mkdir(parents=True)
    controllers=output/'controllers';controllers.mkdir()
    for path in [Path(__file__),HERE/'process.py',HELPER]:shutil.copyfile(path,controllers/path.name)
    sources=output/'sources';sources.mkdir()
    for name in POOL:shutil.copyfile(ROOT/plan['programs'][name]['source']['path'],sources/(name+'.pl'))
    shutil.copyfile(EXPECTED,output/'expected.stdout')
    report=dict(schema='prolog-spectral-selected-full-execution.v1',mode='full',status='RUNNING',started_utc=now(),plan=ref(PLAN),
        controller=ref(__file__),pins=plan['pins'],source_revision=SOURCE_REVISION,runtime=plan['runtime'],binary=plan['binary'],
        foundation=plan['foundation'],builds=plan['builds'],bounded=plan['bounded'],pilot=plan['pilot'],preselection=plan['preselection'],
        n=N,rounds=ROUNDS,sources=SELECTED,retained_pilot_pool=POOL,orders=plan['orders'],required_work=plan['required_work'],
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,timing_boundary=plan['timing_boundary'],
        full_workload=True,diagnostic_profile=False,chart_admission=False,cases=[],active=None,new_observations=0)
    atom(output/'report.json',report)
    try:
        raw_outputs={}
        for schedule in plan['orders']:
            sample=schedule['sample']
            for name in schedule['sources']:
                verify(helper);helper.competition();before=helper.power()
                report['active']=dict(source=name,n=N,sample=sample);atom(output/'report.json',report)
                directory=output/('round-'+str(sample)+'-'+name)
                row=one(plan['programs'][name]['run_argv']+[str(N)],directory,plan['environment'],ROOT,lock.fileno(),args.timeout)
                after=helper.power();raw=(directory/'stdout.bin').read_bytes()
                valid=(row['exit_code']==0 and not row['timed_out'] and not row['remaining_process_group'] and row['stderr']['bytes']==0
                    and raw==EXPECTED_BYTES and row['stdout']['bytes']==12 and row['stdout']['sha256']==EXPECTED_SHA
                    and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0 and row['maximum_rss_bytes']<=10*1024**3)
                row.update(source=name,n=N,sample=sample,output_valid=valid,source_sha256=plan['programs'][name]['source']['sha256'],
                    power_before=before,power_after=after,competing_processes_before=[])
                report['cases'].append(row);report['new_observations']+=1;report['active']=None;atom(output/'report.json',report)
                print(json.dumps(dict(source=name,n=N,sample=sample,seconds=row['elapsed_seconds'],valid=valid)),flush=True)
                require(valid,'Full process/output failed; raw attempt retained, no automatic retry')
                raw_outputs[(name,sample)]=raw;verify(helper)
        wanted={(name,sample) for name in SELECTED for sample in range(1,ROUNDS+1)}
        require(set(raw_outputs)==wanted and len(report['cases'])==6 and report['new_observations']==6,'Full sample inventory incomplete')
        require(all(raw_outputs[name,sample]==raw_outputs['parent',sample] for name,sample in wanted),'Exact matched parent output differs')
        samples={name:[row['elapsed_seconds'] for row in report['cases'] if row['source']==name] for name in SELECTED}
        report.update(status='PASSED',finished_utc=now(),samples=samples,
            medians={name:statistics.median(values) for name,values in samples.items()},
            sample_sd_seconds={name:statistics.stdev(values) for name,values in samples.items()},
            exact_reference_and_parent_outputs=True,pins_unchanged=True)
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--prepare',action='store_true');group.add_argument('--check-only',action='store_true')
    parser.add_argument('--output',type=Path);parser.add_argument('--timeout',type=int,default=1200);args=parser.parse_args()
    require(args.timeout>0,'Positive timeout required');helper=helper_module()
    require(Path(sys.executable).resolve()==Path(PYTHON).resolve(),'Use bundled Python3.12')
    if args.prepare:prepare(helper);return
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan=verify(helper)
        if args.check_only:print(json.dumps(dict(status='PASSED-METADATA-ONLY',plan=ref(PLAN))));return
        require(args.output is not None,'--output required');execute(args,plan,helper,lock)


if __name__=='__main__':main()
