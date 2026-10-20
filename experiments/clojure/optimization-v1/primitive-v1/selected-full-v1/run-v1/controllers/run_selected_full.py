"""Full-only parent/primitive comparison selected before timing from sealed pilot evidence."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PLAN=HERE/'plan.json'
HELPER=BASE/'run_serial.py'
HELPER_SHA='b335d2fc258712b47e859126e3f5d08cd2e69937b720e0331a13aa22a199c1b0'
BASE_PLAN_SHA='cb43a5a01cfafa8c441e0c9ee8a13d1abcfe84cc1b14f3ff247bc74f96c92195'
BOUNDED_SHA='c3f0777f69307134fe9383e4aab8fe1b10e59d9a55d185dd10e785ce9b288d56'
PILOT_SHA='ce91252e209b8c3458e0441e1a15df0200fd4fe961d7dcb14960ae374829b4a8'
POOL=['parent','scalar-updates','primitive-updates']
SELECTED=['parent','primitive-updates']
PILOT_MEDIANS={'parent':3.328331791,'scalar-updates':2.775786959,'primitive-updates':0.274928458}
FULL=b'-0.169075164\n-0.169059907\n'
N=50000000
ROUNDS=3
SEED=20261020


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    path=Path(path).resolve()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),sha256=sha(path))


def helper_module():
    require(sha(HELPER)==HELPER_SHA,'Frozen process helper changed')
    spec=importlib.util.spec_from_file_location('clojure_selected_full_frozen_helper',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    require(helper.NAMES==POOL and helper.ROOT==ROOT and helper.HERE==BASE and helper.PLAN==BASE/'execution-plan.json',
        'Unexpected frozen helper constants; do not mutate them')
    return helper


def verify(plan,helper):
    require(plan['schema']=='clojure-nbody-selected-full-plan.v1' and plan['status']=='PREPARED-NO-EXECUTION'
        and plan['controller']==ref(__file__) and plan['frozen_helper']==ref(HELPER),'Selected-full controller binding differs')
    require(sha(BASE/'execution-plan.json')==BASE_PLAN_SHA and sha(BASE/'bounded-v1/report.json')==BOUNDED_SHA
        and sha(BASE/'pilot-v1/report.json')==PILOT_SHA,'Sealed qualification/pilot changed')
    require(plan['sources']==SELECTED and plan['retained_pilot_pool']==POOL and plan['full_n']==N
        and plan['rounds']==ROUNDS and plan['order_seed']==SEED,'Selected-full schedule differs')
    require(plan['preselection']['pilot_medians_seconds']==PILOT_MEDIANS
        and plan['preselection']['selected_sources']==SELECTED
        and plan['preselection']['omitted_full_source']=='scalar-updates','Predeclared pilot selection differs')
    base=load(BASE/'execution-plan.json')
    require(base==helper.make_plan(),'Frozen three-source execution plan no longer reproduces')
    require(plan['foundation']==ref(BASE/'execution-plan.json') and plan['bounded']==ref(BASE/'bounded-v1/report.json')
        and plan['pilot']==ref(BASE/'pilot-v1/report.json'),'Prerequisite plan references differ')
    require(plan['runtime']==base['runtime'] and plan['builds']==base['builds'] and plan['state_probe']==base['state_probe'],
        'Runtime/build/state selection differs')
    count=load(helper.check_ref(plan['source_count_review']))
    require(count['schema']=='clojure-nbody-retained-source-review.v1' and count['independent_review_approved'] is True
        and count['application_loc']==111 and count['physical_loc']==52
        and count['source']==base['programs']['primitive-updates']['source']
        and count['native_grammar_replay_claimed'] is False,'Exact retained-rule count approval differs')
    require(all(plan['pins'].get(path)==digest for path,digest in base['pins'].items()),'Selected plan omits foundation pins')
    for path,digest in plan['pins'].items():helper.check_ref(dict(path=path,sha256=digest))
    helper.check_prerequisite(BASE/'bounded-v1/report.json','bounded',base)
    helper.check_prerequisite(BASE/'pilot-v1/report.json','pilot',base)
    pilot=load(BASE/'pilot-v1/report.json')
    actual={name:statistics.median([row['elapsed_seconds'] for row in pilot['cases'] if row['source']==name]) for name in POOL}
    require(actual==pilot['medians']==PILOT_MEDIANS and len(pilot['cases'])==3,'Pilot observations/medians differ')
    require(min((name for name in POOL if name!='parent'),key=lambda name:actual[name])=='primitive-updates',
        'Preselected source no longer has the lowest observed candidate pilot time')
    for row in pilot['cases']:
        require(row['source_sha256']==base['programs'][row['source']]['source']['sha256'] and row['n']==1000000,
            'Pilot exact source or workload differs')
    return base


def run(args,plan,helper,base,lock):
    output=args.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(),'Use an exclusive fresh output directory in selected-full-v1')
    helper.competition();output.mkdir(parents=True)
    controllers=output/'controllers';controllers.mkdir()
    shutil.copyfile(__file__,controllers/'run_selected_full.py');shutil.copyfile(HELPER,controllers/'run_serial.py')
    sources=output/'sources';sources.mkdir()
    for name in POOL:shutil.copyfile(ROOT/base['programs'][name]['source']['path'],sources/(name+'.clj'))
    shutil.copyfile(ROOT/base['programs']['parent']['support']['path'],sources/'support.clj')
    evidence=output/'evidence';evidence.mkdir()
    for name,path in [('selected-plan',PLAN),('execution-plan',BASE/'execution-plan.json'),('runtime-build',BASE/'runtime-build.json'),
        ('builds',BASE/'builds.json'),('state-probe-report',BASE/'state-probe-report.json'),('bounded-report',BASE/'bounded-v1/report.json'),
        ('pilot-report',BASE/'pilot-v1/report.json'),('source-count-review',ROOT/plan['source_count_review']['path'])]:shutil.copyfile(path,evidence/(name+'.json'))
    report=dict(schema='clojure-nbody-selected-full-execution.v1',mode='full',status='RUNNING',started_utc=helper.now(),
        plan=ref(PLAN),foundation=plan['foundation'],pins=plan['pins'],controller=ref(__file__),frozen_helper=ref(HELPER),
        runtime=plan['runtime'],builds=plan['builds'],state_probe=plan['state_probe'],bounded=plan['bounded'],pilot=plan['pilot'],
        preselection=plan['preselection'],source_count_review=plan['source_count_review'],sources=SELECTED,retained_pilot_pool=POOL,
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,full_workload=True,diagnostic_profile=False,chart_admission=False,
        timing_boundary=base['timing_boundary'],required_work=base['required_work'],cases=[],orders=[],active=None)
    helper.atom(output/'report.json',report)
    try:
        rng=random.Random(SEED)
        for sample in range(1,ROUNDS+1):
            order=SELECTED.copy();rng.shuffle(order);report['orders'].append(dict(n=N,sample=sample,sources=order))
            for name in order:
                for path,digest in plan['pins'].items():helper.check_ref(dict(path=path,sha256=digest))
                helper.competition();before=helper.power()
                report['active']=dict(source=name,n=N,sample=sample);helper.atom(output/'report.json',report)
                directory=output/('round-'+str(sample)+'-'+name)
                row=helper.one(base['programs'][name]['run_argv']+[str(N)],directory,args.timeout,base['environment'],lock.fileno())
                after=helper.power();raw=(directory/'stdout.bin').read_bytes();stderr=(directory/'stderr.bin').read_bytes()
                valid=(row['exit_code']==0 and not row['timed_out'] and not row['remaining_process_group']
                    and stderr in [b'',helper.EXPECTED_NOTES] and row['stdout']['bytes']==len(FULL)
                    and row['maximum_rss_bytes']<=10*1024**3 and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0
                    and helper.matches(raw,FULL))
                row.update(source=name,n=N,sample=sample,case='full-'+str(sample),output_valid=valid,
                    exact_reference_bytes=raw==FULL,source_sha256=base['programs'][name]['source']['sha256'],
                    power_before=before,power_after=after)
                report['cases'].append(row);report['active']=None;helper.atom(output/'report.json',report)
                print(json.dumps(dict(source=name,n=N,sample=sample,seconds=row['elapsed_seconds'],valid=valid)),flush=True)
                require(valid,'Full output/process check failed; attempt retained, no automatic retry')
                for path,digest in plan['pins'].items():helper.check_ref(dict(path=path,sha256=digest))
        require(sorted((row['source'],row['sample']) for row in report['cases'])==sorted((name,sample) for name in SELECTED for sample in range(1,4)),
            'Full sample inventory incomplete')
        report['samples']={name:[row['elapsed_seconds'] for row in report['cases'] if row['source']==name] for name in SELECTED}
        report['medians']={name:statistics.median(values) for name,values in report['samples'].items()}
        report['sample_sd_seconds']={name:statistics.stdev(values) for name,values in report['samples'].items()}
        report.update(status='PASSED',finished_utc=helper.now(),pins_unchanged=True)
    except BaseException as error:
        report.update(status='FAILED',error=repr(error),finished_utc=helper.now());raise
    finally:helper.atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('--check-only',action='store_true',help='Verify metadata/prerequisites only; starts no subject')
    args=parser.parse_args();require(args.timeout>0,'Positive timeout required');helper=helper_module();plan=load(PLAN)
    with open(helper.LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);base=verify(plan,helper)
        if args.check_only:print(json.dumps(dict(status='PASSED-METADATA-ONLY',plan=ref(PLAN))));return
        require(args.output is not None,'--output required');run(args,plan,helper,base,lock)


if __name__=='__main__':main()
