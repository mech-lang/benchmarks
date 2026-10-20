"""One complete-process N700 spectral pilot per exact source; no full mode."""
import argparse
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from process import atom,now,one,sha,success

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
QUAL=HERE.parent/'qualification-v1'
PLAN=HERE/'plan.json'
BASE_PLAN=QUAL/'execution-plan-v3.json'
BUILD=QUAL/'build-native-v3/report.json'
COMPLETED=QUAL/'completed-v2/report.json'
REFERENCE=ROOT/'archive/languages/c3/20261012/revisions/private-v1/references.py'
REFERENCE_SHA='6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3'
SOURCE_REVISION='612fb31e030be207779c03cddb00a16af56f0173'
PYTHON='/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
LOCK='/tmp/mech-clbg-timing.lock'
N=700
NAMES=['parent','serial-specialized','blocks8-specialized']
SEED=20261020


def require(condition,message):
    if not condition:raise ValueError(message)


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def check_ref(value):
    p=ROOT/value['path'];require(p.is_file() and sha(p)==value['sha256'],'Changed pinned artifact: '+str(p));return p


def count_review():
    counts=load(QUAL/'completed-v2/source-counts.json')
    return {name:dict(normalized_loc=counts['rows'][name]['normalized_loc'],physical_loc=counts['rows'][name]['physical_loc'],
        candidate_independent_count_approved=False if name!='parent' else True) for name in NAMES}


def prepare():
    require(not PLAN.exists(),'Exclusive pilot plan required')
    base=load(BASE_PLAN);build=load(BUILD);complete=load(COMPLETED)
    require(base['status']=='PREPARED-NO-EXECUTION' and build['status']=='PASSED'
        and build['plan']==ref(BASE_PLAN) and complete['status']=='PASSED'
        and complete['builds']==ref(BUILD) and complete['foundation']==ref(BASE_PLAN),'Matching native qualification required')
    require(complete['complete_output_cases']==39 and complete['vector_comparisons']==144 and complete['geometry_cases']==12
        and complete['work_cases']==6 and complete['parallel_source_count_certified'] is False,'Bounded qualification inventory differs')
    require(sha(REFERENCE)==REFERENCE_SHA,'Independent reference source differs')
    pins=dict(base['pins'])
    # Seal durable small artifacts now; actual runtime/QLF pins are verified by --check-only and before every measured process.
    files=[Path(__file__),HERE/'process.py',BASE_PLAN,BUILD,COMPLETED,REFERENCE]
    files.extend(p for p in QUAL.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp'))
    for path in files:pins[str(path.relative_to(ROOT))]=sha(path)
    for program in build['programs'].values():
        for field in ['source_qlf_pin','support_qlf_pin']:
            item=program[field];pins[item['path']]=item['sha256']
    order=NAMES.copy();random.Random(SEED).shuffle(order)
    plan=dict(schema='prolog-spectral-pilot700-plan.v1',status='PREPARED-NO-EXECUTION',controller=ref(__file__),
        process_helper=ref(HERE/'process.py'),observer_parent=ref(QUAL/'native_process.py'),
        observer_delta='Only module description and quantitative_benchmark metadata true; process/start/exit/group/watchdog/RSS capture unchanged.',
        foundation=ref(BASE_PLAN),builds=ref(BUILD),bounded=ref(COMPLETED),source_revision=SOURCE_REVISION,
        runtime=base['runtime'],binary=base['binary'],environment=base['environment'],flags=base['flags'],programs=build['programs'],pins=pins,
        python=dict(path=PYTHON,sha256=sha(PYTHON)),sources=NAMES,n=N,rounds=1,order_seed=SEED,order=order,
        independent_reference=dict(source=ref(REFERENCE),function='spectralnorm(700)',
            generation='At the beginning of the locked pilot, before any measured subject process. Save complete expected stdout and its hash; do not treat oracle generation as a measurement.'),
        output_rule='Exit0, no timeout/group survivor/stderr, complete12byte stdout exactly equals independently generated reference and parent stdout; no numeric tolerance.',
        required_work=dict(power_iterations=10,ata_applications=20,matrix_vector_products=40,coefficient_calls=19600000,
            coefficient_calls_formula='40*700*700',matrix_cache=False,parallel_worker_limit=8,
            evidence='Exact sources plus bounded native work wrappers; pilot itself has no instrumentation.'),
        retained_source_counts=count_review(),common_mutex=LOCK,full_mode_available=False,
        timing_boundary='Fresh SWI process launch, runtime/QLF loading and worker setup, all40products, final dots, complete output/flush and process exit; excludes reference generation, hashing and power/competition checks.',
        inference_limit='One diagnostic observation per source atN700 selects later full-size candidates; no full-size speedup, statistical precision or global optimality claim.',
        new_observations=0,chart_admission=False)
    atom(PLAN,plan);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN),pins=len(pins),order=order)))


def verify():
    plan=load(PLAN)
    require(plan['schema']=='prolog-spectral-pilot700-plan.v1' and plan['status']=='PREPARED-NO-EXECUTION'
        and plan['controller']==ref(__file__) and plan['process_helper']==ref(HERE/'process.py')
        and plan['foundation']==ref(BASE_PLAN) and plan['builds']==ref(BUILD) and plan['bounded']==ref(COMPLETED),'Pilot binding differs')
    require(plan['n']==N and plan['sources']==NAMES and plan['rounds']==1 and plan['order_seed']==SEED
        and plan['source_revision']==SOURCE_REVISION and plan['full_mode_available'] is False,'Pilot workload differs')
    order=NAMES.copy();random.Random(SEED).shuffle(order);require(plan['order']==order,'Pilot order differs')
    require(plan['python']['path']==PYTHON and sha(PYTHON)==plan['python']['sha256'] and Path(sys.executable).resolve()==Path(PYTHON).resolve(),'Use the pinned bundled Python3.12')
    for path,digest in plan['pins'].items():check_ref(dict(path=path,sha256=digest))
    base=load(BASE_PLAN);build=load(BUILD);complete=load(COMPLETED)
    require(build['status']=='PASSED' and complete['status']=='PASSED' and complete['source_runtime_qlf_pins_unchanged'] is True,'Native qualification no longer complete')
    require(plan['programs']==build['programs'] and plan['binary']==base['binary'] and plan['environment']==base['environment']
        and plan['flags']==base['flags'] and plan['retained_source_counts']==count_review(),'Exact runtime/build/count selection differs')
    require(sha(REFERENCE)==REFERENCE_SHA,'Independent reference changed')
    return plan


def competition():
    listing=subprocess.check_output(['/bin/ps','-axo','pid=,comm='],text=True)
    names={'swipl','java','javac','javap','BQN','nim','nimpretty','cargo','rustc','rustdoc','clang','clang++','cc','gcc','julia','futhark','hyperfine','lean','leanc','lake'}
    rows=[line.strip() for line in listing.splitlines() if len(line.split(None,1))==2 and Path(line.split(None,1)[1]).name in names]
    require(not rows,'Competing subject/compiler processes: '+repr(rows));return rows


def power():
    battery=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
    settings=subprocess.check_output(['/usr/bin/pmset','-g','custom'],text=True)
    modes=[line.split()[-1] for line in settings.splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in battery and modes and set(modes)=={'0'},'AC power with low-power mode disabled required')
    return dict(battery=battery,settings=settings)


def oracle():
    require(sha(REFERENCE)==REFERENCE_SHA,'Independent reference changed')
    spec=importlib.util.spec_from_file_location('prolog_pilot_independent_reference',REFERENCE)
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    expected=reference.spectralnorm(N);require(type(expected) is bytes and len(expected)==12,'Malformed independent reference');return expected


def execute(args,plan,lock):
    output=args.output.resolve();require(output.is_relative_to(HERE) and not output.exists(),'Exclusive fresh output inside pilot-700-v1 required')
    competition();power();output.mkdir(parents=True)
    controllers=output/'controllers';controllers.mkdir()
    for source in [Path(__file__),HERE/'process.py',REFERENCE]:shutil.copyfile(source,controllers/source.name)
    sources=output/'sources';sources.mkdir()
    for name in NAMES:shutil.copyfile(ROOT/plan['programs'][name]['source']['path'],sources/(name+'.pl'))
    report=dict(schema='prolog-spectral-pilot700-execution.v1',status='RUNNING',started_utc=now(),plan=ref(PLAN),
        controller=ref(__file__),pins=plan['pins'],source_revision=SOURCE_REVISION,common_mutex_inode=os.fstat(lock.fileno()).st_ino,
        n=N,rounds=1,order=plan['order'],required_work=plan['required_work'],timing_boundary=plan['timing_boundary'],
        chart_admission=False,full_workload=False,diagnostic_profile=True,new_observations=0,cases=[],active='independent-reference')
    atom(output/'report.json',report)
    try:
        expected=oracle();(output/'expected.stdout').write_bytes(expected)
        report['independent_reference']=dict(source=ref(REFERENCE),function='spectralnorm(700)',stdout=ref(output/'expected.stdout'),bytes=len(expected))
        raw_outputs={}
        for name in plan['order']:
            verify();competition();before=power();report['active']=dict(source=name,n=N);atom(output/'report.json',report)
            directory=output/name
            row=one(plan['programs'][name]['run_argv']+[str(N)],directory,plan['environment'],ROOT,lock.fileno(),args.timeout)
            after=power();raw=(directory/'stdout.bin').read_bytes()
            valid=(row['exit_code']==0 and not row['timed_out'] and not row['remaining_process_group'] and row['stderr']['bytes']==0
                and raw==expected and row['stdout']['bytes']==12 and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0
                and row['maximum_rss_bytes']<=10*1024**3)
            row.update(source=name,n=N,sample=1,output_valid=valid,source_sha256=plan['programs'][name]['source']['sha256'],
                power_before=before,power_after=after,competing_processes_before=[])
            report['cases'].append(row);report['new_observations']+=1;report['active']=None;atom(output/'report.json',report)
            print(json.dumps(dict(source=name,n=N,seconds=row['elapsed_seconds'],valid=valid)),flush=True)
            require(valid,'Pilot output/process check failed; no automatic retry');raw_outputs[name]=raw;verify()
        require(all(raw_outputs[name]==raw_outputs['parent'] for name in NAMES),'Exact parent output differs')
        require(sorted(row['source'] for row in report['cases'])==sorted(NAMES),'Pilot case inventory incomplete')
        report.update(status='PASSED',finished_utc=now(),exact_parent_output_match=True,pins_unchanged=True,
            seconds={row['source']:row['elapsed_seconds'] for row in report['cases']})
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group()
    group.add_argument('--prepare',action='store_true');group.add_argument('--check-only',action='store_true')
    parser.add_argument('--output',type=Path);parser.add_argument('--timeout',type=int,default=600);args=parser.parse_args()
    require(args.timeout>0,'Positive timeout required')
    if args.prepare:prepare();return
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan=verify()
        if args.check_only:print(json.dumps(dict(status='PASSED-METADATA-ONLY',plan=ref(PLAN))));return
        require(args.output is not None,'--output required');execute(args,plan,lock)


if __name__=='__main__':main()
