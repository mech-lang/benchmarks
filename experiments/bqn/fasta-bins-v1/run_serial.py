"""Source-pinned FASTA qualification/matched runner; --prepare starts no native code."""
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
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT/'experiments/bqn/fasta-bins-v1'
PLAN = HERE/'execution-plan.json'
SOURCE_PROPOSAL = HERE/'plan.json'
RUNTIME = ROOT/'experiments/bqn/optimization-v1/.build/CBQN/BQN'
RUNTIME_SHA = '0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5'
COMMIT = 'c893d3e7828899a50150df03ad33c9052fa51d3c'
BUILD = ROOT/'experiments/bqn/optimization-v1/release-build.json'
HELPER = ROOT/'tools/qualification/lean_run.py'
HELPER_SHA = '313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases'
CORPUS_SHA = '92767a167dafd97745361221cd5a9fe04a2388ba6be7f591756f6153ab3895f1'
PARENT = ROOT/'archive/comparisons/array-comparison/all-20261009/sources/fasta.bqn'
SOURCES = dict(zip(['parent-faithful','bins-only','bins-empty-safe'],[
    '531d039ae5f9aa34f9db35e4df9efc723dc64098e3b1828c7b4fba972e35085e',
    'ca20f70bee8b85d0ab78bb20edba0ef9c30d55dcac4d37995377a220779914c2',
    '62c9f888a5869da3655fc530478a590ad7472f5c0ccf337dfb4e088dfef8edc5']))
FULL_SOURCES = ['parent-faithful','bins-empty-safe']
NS = [0,1,2,19,20,21,29,30,31,59,60,61,287,574,1000,20000]
FULL = dict(n=25000000,bytes=254166745,sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa')
LOOKUP_SOURCE = HERE/'tests/lookup-equivalence.bqn'
LOOKUP_OUTPUT = b'PASS: finite FASTA sample domain, threshold equality, duplicates and empty input\n'
CONTROL_ZERO_OUTPUT = b'>ONE Homo sapiens alu\n>TWO IUB ambiguity codes\n'
SEED = 20261020
TIMING_BOUNDARY = 'Fresh BQN process through exit, including startup, argv parsing, all naive LCG updates, floating probability searches, complete formatting/output and shutdown; excludes hashing, qualification and power checks.'


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def digest(data):return hashlib.sha256(data).hexdigest()


def ref(path):
    path=Path(path)
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),sha256=sha(path))


def load(path):return json.loads(Path(path).read_text())


def atom(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def make_plan():
    require(sha(PARENT)==SOURCES['parent-faithful'],'Retained parent changed')
    original=PARENT.read_bytes()
    old='  indices ← +´˘⍉ cumulative ≤⌜ r÷139968\n'.encode()
    require(original.count(old)==1,'Parent lookup inventory changed')
    bins=original.replace(old,'  indices ← cumulative ⍋ r÷139968\n'.encode())
    old='  seed ↩ ¯1⊑r\n'.encode();require(bins.count(old)==1,'Parent seed update changed')
    safe=bins.replace(old,'  seed ↩ {0<≠𝕩? ¯1⊑𝕩; seed} r\n'.encode())
    for (name,expected_sha),content in zip(SOURCES.items(),[original,bins,safe]):
        path=HERE/'sources'/(name+'.bqn')
        require(path.read_bytes()==content and sha(path)==expected_sha,'Unreviewed candidate source change')
    require(sha(RUNTIME)==RUNTIME_SHA and sha(HELPER)==HELPER_SHA,'Wrong release runtime/process helper')
    require(sha(CORPUS/'manifest.json')==CORPUS_SHA,'Changed independent corpus')
    build=load(BUILD)
    require(build['schema']=='bqn-runtime-build.v1' and build['runtime_use']=='release-timing'
        and build['commit']==COMMIT and build['release_source_status']=='' and build['witness_patch_sha256'] is None,
        'Wrong release receipt')
    require(any(row['path'].endswith('/.build/CBQN/BQN') and row['sha256']==RUNTIME_SHA for row in build['artifacts']),
        'Runtime not bound to release receipt')
    ffi=next(row for row in build['artifacts'] if row['path']=='/opt/homebrew/opt/libffi/lib/libffi.8.dylib')
    require(sha(ffi['path'])==ffi['sha256'],'Changed linked runtime dependency')
    cases=sorted((row for row in load(CORPUS/'manifest.json')['cases'] if row['benchmark']=='fasta'),key=lambda row:row['n'])
    require([row['n'] for row in cases]==NS,'Need all sixteen shared FASTA cases')
    references=[]
    for case in cases:
        require(case['expected_exit']==0 and case['validation']=='exact-complete-bytes','Wrong reference policy')
        for key in ['stdin','expected']:
            path=CORPUS/case[key]['path']
            require(sha(path)==case[key]['sha256'] and path.stat().st_size==case[key]['bytes'],'Changed independent reference')
            references.append(ref(path))
    proposal=load(SOURCE_PROPOSAL)
    require(proposal['sources']=={name:ref(HERE/'sources'/(name+'.bqn')) for name in SOURCES}
        and proposal['lookup_test']==ref(LOOKUP_SOURCE) and proposal['review']==ref(HERE/'REVIEW.md')
        and proposal['controller_created'] is True and proposal['controller']==ref(__file__)
        and proposal['execution_instructions']==ref(HERE/'RUNNER.md'),
        'Source proposal is stale')
    return dict(schema='bqn-fasta-bins-execution-plan.v1',status='PREPARED-NO-EXECUTION',
        source_proposal=ref(SOURCE_PROPOSAL),controller=ref(__file__),process_controller=ref(HELPER),review=ref(HERE/'REVIEW.md'),instructions=ref(HERE/'RUNNER.md'),
        parent=ref(PARENT),sources={name:ref(HERE/'sources'/(name+'.bqn')) for name in SOURCES},
        runtime=ref(RUNTIME),runtime_commit=COMMIT,runtime_build=ref(BUILD),runtime_dependencies=[ffi],
        corpus=ref(CORPUS/'manifest.json'),bounded_cases=cases,reference_files=references,
        exhaustive_lookup=dict(source=ref(LOOKUP_SOURCE),normalized_states=139968,probability_vectors=2,
            additional_cases=['exact thresholds','duplicate thresholds','empty right argument'],
            expected=dict(bytes=len(LOOKUP_OUTPUT),sha256=digest(LOOKUP_OUTPUT)),timing_admissible=False),
        bounded_sources=list(SOURCES),full_sources=FULL_SOURCES,full=FULL,samples=3,order_seed=SEED,
        known_control_zero_failure=dict(sources=['parent-faithful','bins-only'],n=0,expected_exit=1,
            expected_partial_stdout=dict(bytes=len(CONTROL_ZERO_OUTPUT),sha256=digest(CONTROL_ZERO_OUTPUT)),
            reason='Retained original last-state pick on empty vector; diagnosed separately, never accepted as a candidate output pass.'),
        required_work=dict(naive_lcg_updates_full=200000000,floating_division=True,cumulative_probabilities_unchanged=True,
            native_lookup='ordinary f64 binary search',cached_random_period=False,integer_threshold_scaling=False,
            new_native_helper_or_ffi=False,application_imports=[]),common_mutex='/tmp/mech-clbg-timing.lock',
        timing_boundary=TIMING_BOUNDARY,source_counts_approved=False,chart_admission=False)


def pins_from(plan):
    refs=[plan[key] for key in ['source_proposal','controller','process_controller','review','instructions','parent','runtime','runtime_build','corpus']]
    refs += [ref(PLAN),plan['exhaustive_lookup']['source']]+list(plan['sources'].values())+plan['reference_files']+plan['runtime_dependencies']
    return {row['path']:row['sha256'] for row in refs}


def check_pins(pins):require(all(sha(ROOT/path)==value for path,value in pins.items()),'A source/runtime/support/reference pin changed')


def power():
    battery=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
    settings=subprocess.check_output(['/usr/bin/pmset','-g','custom'],text=True)
    low=[line.split()[-1] for line in settings.splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in battery and low and all(value=='0' for value in low),'AC power with low-power mode off required')
    return dict(battery=battery,settings=settings)


def valid_record(record,expected,known_failure=False):
    output_match=record['stdout']['bytes']==expected['bytes'] and record['stdout']['sha256']==expected['sha256']
    seconds=record.get('elapsed_seconds')
    common=(record.get('timed_out') is False and type(seconds) in (int,float) and math.isfinite(seconds) and seconds>0
        and type(record.get('pid')) is int and record['pid']>0 and record.get('started_utc') and record.get('finished_utc'))
    return bool(common and output_match and (record['exit_code']==1 and record['stderr']['bytes']>0 if known_failure
        else record['exit_code']==0 and record['stderr']['bytes']==0)
    )


def check_power_receipt(value):
    low=[line.split()[-1] for line in value['settings'].splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in value['battery'] and low and all(item=='0' for item in low),'Invalid saved power evidence')


def expected_case(plan,name,n):
    known=n==0 and name in plan['known_control_zero_failure']['sources']
    expected=plan['known_control_zero_failure']['expected_partial_stdout'] if known else next(case['expected'] for case in plan['bounded_cases'] if case['n']==n)
    return expected,known


def check_saved_record(row,additions):
    directory=Path(row['stdout']['path']).parent
    require(directory.is_relative_to(HERE) and Path(row['stderr']['path'])==directory/'stderr.bin','Wrong saved stream directory')
    require(load(directory/'process.json')=={key:value for key,value in row.items() if key not in additions},'Changed raw process receipt')
    for stream in ['stdout','stderr']:
        path=Path(row[stream]['path'])
        require(sha(path)==row[stream]['sha256'] and path.stat().st_size==row[stream]['bytes'],'Changed saved process stream')


def check_bounded(path,plan):
    report=load(path)
    require(report['schema']=='bqn-fasta-bins-execution.v1' and report['mode']=='bounded' and report['status']=='PASSED'
        and report['active'] is None and report['plan']==ref(PLAN) and report['pins']==pins_from(plan)
        and report['controller_sha256']==sha(__file__) and report['process_controller_sha256']==HELPER_SHA
        and report['runtime_sha256']==RUNTIME_SHA and report['chart_admission'] is False
        and report['complete_candidate_all_16_passed'] is True and report['pins_unchanged'] is True,
        'Need matching complete bounded qualification')
    lookup=report['lookup_qualification']
    require(lookup['command']==[str(RUNTIME),str(LOOKUP_SOURCE)] and lookup['stdin']=='/dev/null'
        and lookup['qualification_valid'] is True and lookup['timing_admissible'] is False
        and valid_record(lookup,plan['exhaustive_lookup']['expected']),
        'Exhaustive floating lookup equivalence did not pass')
    check_saved_record(lookup,{'qualification_valid','output_valid','timing_admissible','power_before','power_after','qualification'})
    check_power_receipt(lookup['power_before']);check_power_receipt(lookup['power_after'])
    rows=report['cases'];require(len(rows)==len(NS)*len(SOURCES),'Incomplete bounded source/case coverage')
    require(sorted((row['source'],row['n']) for row in rows)==sorted((name,n) for name in SOURCES for n in NS),'Repeated or missing bounded case')
    for row in rows:
        expected,known=expected_case(plan,row['source'],row['n'])
        require(row['command']==[str(RUNTIME),str(HERE/'sources'/(row['source']+'.bqn')),str(row['n'])]
            and row['source_sha256']==SOURCES[row['source']] and row['runtime_sha256']==RUNTIME_SHA
            and row['qualification_valid'] is True and row['known_control_failure'] is known
            and row['output_valid'] is (not known) and valid_record(row,expected,known), 'Failed/stale bounded case')
        case=next(case for case in plan['bounded_cases'] if case['n']==row['n'])
        require(row['stdin']==str(CORPUS/case['stdin']['path']),'Wrong bounded input')
        check_saved_record(row,{'source','n','sample','case','output_valid','qualification_valid','known_control_failure',
            'source_sha256','runtime_sha256','power_before','power_after'})
        check_power_receipt(row['power_before']);check_power_receipt(row['power_after'])
    return ref(path)


def execute(args,plan):
    require(args.output is not None and args.timeout>0,'Need output directory and positive timeout')
    output=args.output.resolve();require(output.is_relative_to(HERE) and not output.exists(),'Use a fresh directory inside this experiment')
    prerequisite=check_bounded(args.bounded_report.resolve(),plan) if args.mode=='full' else None
    spec=importlib.util.spec_from_file_location('fasta_saved_process',HELPER)
    process=importlib.util.module_from_spec(spec);sys.modules[spec.name]=process;spec.loader.exec_module(process)
    pins=pins_from(plan)
    with open(plan['common_mutex'],'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);check_pins(pins)
        output.mkdir(parents=True);(output/'sources').mkdir();(output/'controllers').mkdir();(output/'tests').mkdir()
        for name in SOURCES:shutil.copyfile(HERE/'sources'/(name+'.bqn'),output/'sources'/(name+'.bqn'))
        shutil.copyfile(__file__,output/'controllers/run_serial.py');shutil.copyfile(HELPER,output/'controllers/lean_run.py')
        shutil.copyfile(LOOKUP_SOURCE,output/'tests/lookup-equivalence.bqn');shutil.copyfile(PLAN,output/'execution-plan.json')
        report=dict(schema='bqn-fasta-bins-execution.v1',mode=args.mode,status='RUNNING',started_utc=process.now(),
            plan=ref(PLAN),pins=pins,controller_sha256=sha(__file__),process_controller_sha256=sha(HELPER),runtime_sha256=RUNTIME_SHA,
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,bounded_prerequisite=prerequisite,full_workload=args.mode=='full',
            chart_admission=False,diagnostic_profile=False,timing_boundary=TIMING_BOUNDARY,required_work=plan['required_work'],
            qualification_scope='Complete empty-safe candidate all16 cases; original/minimal controls retain explicit expected n0 failure; exhaustive lookup separate and untimed.',
            lookup_qualification=None,cases=[],orders=[],active=None,
            host=dict(cpu=subprocess.check_output(['/usr/sbin/sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
                os=subprocess.check_output(['/usr/bin/sw_vers'],text=True)))
        if args.mode=='bounded':
            before=power();report['active']=dict(qualification='exhaustive-lookup');atom(output/'report.json',report)
            row=process.one([str(RUNTIME),str(LOOKUP_SOURCE)],Path('/dev/null'),output/'exhaustive-lookup',args.timeout)
            after=power();valid=valid_record(row,plan['exhaustive_lookup']['expected'])
            row.update(qualification='exhaustive-lookup',qualification_valid=valid,output_valid=valid,timing_admissible=False,power_before=before,power_after=after)
            report['lookup_qualification']=row;report['active']=None
            if not valid:report['status']='FAILED'
            atom(output/'report.json',report);require(valid,'Exhaustive lookup failed; retain attempt without automatic retry');check_pins(pins)
        rng=random.Random(SEED)
        schedule=[(case['n'],1,case['case'],case['stdin'],case['expected']) for case in plan['bounded_cases']] if args.mode=='bounded' else [
            (FULL['n'],sample,'full-'+str(sample),None,FULL) for sample in [1,2,3]]
        for n,sample,case,stdin_ref,reference in schedule:
            names=list(SOURCES) if args.mode=='bounded' else FULL_SOURCES.copy();rng.shuffle(names)
            report['orders'].append(dict(n=n,sample=sample,sources=names))
            for name in names:
                check_pins(pins);before=power();report['active']=dict(source=name,n=n,sample=sample,case=case);atom(output/'report.json',report)
                command=[str(RUNTIME),str(HERE/'sources'/(name+'.bqn')),str(n)]
                row=process.one(command,CORPUS/stdin_ref['path'] if stdin_ref else Path('/dev/null'),output/(case+'-'+name),args.timeout)
                after=power();expected,known=expected_case(plan,name,n) if args.mode=='bounded' else (reference,False)
                valid=valid_record(row,expected,known)
                row.update(source=name,n=n,sample=sample,case=case,qualification_valid=valid,output_valid=valid and not known,
                    known_control_failure=known,source_sha256=SOURCES[name],runtime_sha256=RUNTIME_SHA,power_before=before,power_after=after)
                report['cases'].append(row);report['active']=None
                if not valid:report['status']='FAILED'
                atom(output/'report.json',report)
                print(json.dumps(dict(source=name,n=n,sample=sample,seconds=row['elapsed_seconds'],qualified=valid,known_control_failure=known)),flush=True)
                require(valid,'Unexpected native result; retain attempt without automatic retry');check_pins(pins)
        report.update(status='PASSED',finished_utc=process.now(),pins_unchanged=True)
        if args.mode=='bounded':
            report['complete_candidate_all_16_passed']=all(row['output_valid'] for row in report['cases'] if row['source']=='bins-empty-safe')
            report['known_control_failures']=[dict(source=row['source'],n=row['n'],exit_code=row['exit_code']) for row in report['cases'] if row['known_control_failure']]
        else:
            samples={name:[row['elapsed_seconds'] for row in report['cases'] if row['source']==name] for name in FULL_SOURCES}
            report.update(samples=samples,medians={name:statistics.median(values) for name,values in samples.items()},
                sample_sd_seconds={name:statistics.stdev(values) for name,values in samples.items()})
        atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--mode',choices=['bounded','full']);parser.add_argument('--output',type=Path)
    parser.add_argument('--bounded-report',type=Path);parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args();require(args.prepare!=(args.mode is not None),'Choose --prepare or --mode')
    plan=make_plan()
    if args.prepare:
        require(args.output is None and args.bounded_report is None,'Preparation has no execution paths')
        atom(PLAN,plan);print(json.dumps(dict(status=plan['status'],plan=ref(PLAN),native_processes_started=0)));return
    require(load(PLAN)==plan,'Absent/stale execution plan; prepare and review first')
    require((args.bounded_report is not None)==(args.mode=='full'),'Full execution alone needs bounded report')
    execute(args,plan)


if __name__=='__main__':main()
