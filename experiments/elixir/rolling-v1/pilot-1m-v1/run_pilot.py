"""One shuffled fresh-process observation per Elixir source on1m selected bases.

Pilot only. Prefix extraction and independent direct-window reference generation
occur before all measured processes; there is no full-size mode or admission.
"""
import argparse
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

from process import atom,now,one,sha,success
import input_reference

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
QUAL=HERE.parent/'qualification-v1'
PLAN=HERE/'plan.json'
QUALIFICATION=QUAL/'qualification.json'
BUILD=QUAL/'bounded-v2/report.json'
RUNTIME_PLAN=QUAL/'runtime-plan-v2.json'
FULL_INPUT=ROOT/'experiments/lean4/.build/inputs/n25000000.fasta'
FULL_INPUT_SHA='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
FULL_INPUT_BYTES=254166745
PYTHON='/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12'
LOCK=Path('/tmp/mech-clbg-timing.lock')
NAMES=['parent','serial','parallel']
N=1000000
SEED=20261020


def require(value,message):
    if not value:raise ValueError(message)


def load(path):return json.loads(Path(path).read_bytes())


def ref(path):
    p=Path(path);return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),sha256=sha(p))


def prepare():
    require(not PLAN.exists(),'Fresh pilot plan required')
    q=load(QUALIFICATION);build=load(BUILD);runtime=load(RUNTIME_PLAN)
    require(q['status']=='QUALIFIED-BOUNDED-NOT-TIMED' and q['work_witness']['observations']==117
        and q['work_witness']['whole_histograms']==819 and q['work_witness']['actual_map_update_calls']==222597
        and q['parallel_failure_cleanup']['passed'] is True and build['status']=='PASSED','Incomplete qualification')
    pins=dict(q['pins'])
    for path in [Path(__file__),HERE/'process.py',HERE/'input_reference.py',QUALIFICATION,BUILD,RUNTIME_PLAN]:
        p=ref(path);pins[p['path']]=p['sha256']
    order=NAMES.copy();random.Random(SEED).shuffle(order)
    plan=dict(schema='elixir-rolling-pilot1m-plan.v1',status='PREPARED-NO-EXECUTION',controller=ref(__file__),
        process_helper=ref(HERE/'process.py'),observer_parent=ref(QUAL/'native_process.py'),
        observer_delta='Only module description and quantitative_benchmark metadata true; input/process/start/exit/group/watchdog/RSS capture unchanged.',
        qualification=ref(QUALIFICATION),builds=ref(BUILD),sources=NAMES,programs=build['programs'],environment=runtime['environment'],
        pins=pins,runtime_files={**load(QUAL/'runtime-v2/report.json')['elixir_files'],**load(QUAL/'runtime-v2/report.json')['otp_files']},
        python=dict(path=PYTHON,sha256=sha(PYTHON)),n=N,n_scope='Selected DNA bases, not FASTA generator parameter.',
        shared_full_input=dict(path=str(FULL_INPUT.relative_to(ROOT)),sha256=FULL_INPUT_SHA,bytes=FULL_INPUT_BYTES),
        input_derivation=dict(source=ref(HERE/'input_reference.py'),function='prefix(shared_full_input,1000000)',
            scope='Prefix of THREE record only; earlier records omitted, original header/base bytes retained with60-column lines. Diagnostic selected-record input, not the full input boundary.'),
        independent_reference=dict(source=ref(HERE/'input_reference.py'),function='reference(dna)',
            method='Direct overlapping byte slices and Counter for every complete histogram; independent of rolling packed-key recurrence.',
            generated='Once under common lock, before any measured subject and outside every reported process timer.'),
        order_seed=SEED,order=order,rounds=1,common_mutex=str(LOCK),full_mode_available=False,
        required_work=dict(widths=input_reference.WIDTHS,dna_length=N,standard_map_occurrence_updates=7*N-39,
            complete_histograms=7,default_empty_standard_maps=True,query_only_shortcut=False,maximum_application_counting_workers=7),
        timing_boundary='Fresh elixir/OTP process launch and pinned BEAM loading; prefix stdin reading, selected-record parsing/encoding, all seven complete maps and occurrence updates, ordered results, complete stdout/flush and exit. Excludes input/reference generation, compression, hashing, power/competition checks.',
        output_rule='Exit0, no timeout/group survivor/stderr; complete stdout equals independent reference and parent stdout byte for byte.',
        source_count=None,source_formatting=None,chart_admission=False,full_workload=False,diagnostic_profile=True,new_observations=0,
        inference_limit='One observation per exact source on1m selected bases is for later full-size preselection. No precision, full-size speedup, source-size approval or global optimality claim.')
    atom(PLAN,plan);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN),order=order,pins=len(pins),full_mode_available=False)))


def verify():
    plan=load(PLAN)
    require(plan['schema']=='elixir-rolling-pilot1m-plan.v1' and plan['status']=='PREPARED-NO-EXECUTION'
        and plan['controller']==ref(__file__) and plan['process_helper']==ref(HERE/'process.py')
        and plan['qualification']==ref(QUALIFICATION) and plan['builds']==ref(BUILD),'Pilot protocol binding differs')
    order=NAMES.copy();random.Random(SEED).shuffle(order)
    require(plan['n']==N and plan['sources']==NAMES and plan['rounds']==1 and plan['order']==order and plan['full_mode_available'] is False
        and plan['source_count'] is None and plan['source_formatting'] is None,'Pilot selection/workload/count differs')
    require(Path(sys.executable).resolve()==Path(PYTHON).resolve() and plan['python']==dict(path=PYTHON,sha256=sha(PYTHON)),'Use exact bundled Python3.12')
    for path,digest in {**plan['pins'],**plan['runtime_files']}.items():require(sha(ROOT/path if not Path(path).is_absolute() else path)==digest,'Changed pilot qualification/runtime pin: '+path)
    require(FULL_INPUT.stat().st_size==FULL_INPUT_BYTES and sha(FULL_INPUT)==FULL_INPUT_SHA,'Shared full input differs')
    require(plan['programs']==load(BUILD)['programs'] and plan['environment']==load(RUNTIME_PLAN)['environment'],'Source/BEAM/runtime environment differs')
    return plan


def power():
    battery=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
    settings=subprocess.check_output(['/usr/bin/pmset','-g','custom'],text=True)
    modes=[line.split()[-1] for line in settings.splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in battery and modes and set(modes)=={'0'},'AC power and low-power off required')
    return dict(battery=battery,settings=settings)


def competition():
    listing=subprocess.check_output(['/bin/ps','-axo','pid=,comm='],text=True)
    forbidden={'beam.smp','erl','erlexec','elixir','elixirc','swipl','java','javac','javap','BQN','nim','nimpretty','cargo','rustc','rustdoc','clang','clang++','cc','gcc','julia','futhark','hyperfine','lean','leanc','lake','node'}
    rows=[line.strip() for line in listing.splitlines() if len(line.split(None,1))==2 and Path(line.split(None,1)[1]).name in forbidden]
    require(not rows,'Competing native subject/compiler process: '+repr(rows));return rows


def execute(output,plan,lock):
    output=output.resolve();require(output.is_relative_to(HERE) and not output.exists(),'Exclusive fresh pilot output inside pilot1m packet required')
    competition();power();output.mkdir()
    report=dict(schema='elixir-rolling-pilot1m-execution.v1',status='RUNNING',started_utc=now(),plan=ref(PLAN),controller=ref(__file__),
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,pins=plan['pins'],runtime_files=plan['runtime_files'],n=N,order=plan['order'],
        diagnostic_profile=True,full_workload=False,chart_admission=False,timing_boundary=plan['timing_boundary'],required_work=plan['required_work'],
        source_count=None,source_formatting=None,cases=[],active='untimed-input-and-independent-reference')
    atom(output/'report.json',report)
    try:
        fixture,dna,derivation=input_reference.prefix(FULL_INPUT,N)
        expected,histograms=input_reference.reference(dna)
        require(sum(r['updates'] for r in histograms)==plan['required_work']['standard_map_occurrence_updates'],'Reference occurrence work differs')
        inp=output/'stdin.fasta';inp.write_bytes(fixture);(output/'expected.stdout').write_bytes(expected)
        with (output/'stdin.fasta.gz').open('xb') as stream:
            with gzip.GzipFile(filename='',fileobj=stream,mode='wb',mtime=0) as zipped:zipped.write(fixture)
        report['input']=dict(**ref(inp),bytes=len(fixture),gzip=ref(output/'stdin.fasta.gz'),shared_source=plan['shared_full_input'],derivation=derivation)
        report['independent_reference']=dict(**ref(output/'expected.stdout'),bytes=len(expected),source=plan['independent_reference']['source'],histograms=histograms)
        snapshots=output/'sources';snapshots.mkdir();controllers=output/'controllers';controllers.mkdir()
        for source in [Path(__file__),HERE/'process.py',HERE/'input_reference.py']:shutil.copyfile(source,controllers/source.name)
        for name,p in plan['programs'].items():
            dest=snapshots/name;dest.mkdir()
            for field in ['source_snapshot','support_snapshot','runner_snapshot']:shutil.copyfile(ROOT/p[field]['path'],dest/Path(p[field]['path']).name)
        outputs={}
        for name in plan['order']:
            verify();require(sha(inp)==report['input']['sha256'],'Pilot fixture changed');competition();before=power()
            report['active']=name;atom(output/'report.json',report)
            row=one(plan['programs'][name]['run_argv']+['0'],output/name,plan['environment'],ROOT,lock.fileno(),timeout=600,stdin=inp)
            after=power();competition();raw=Path(row['stdout']['path']).read_bytes()
            valid=(row['exit_code']==0 and not row['timed_out'] and not row['remaining_process_group'] and row['stderr']['bytes']==0 and raw==expected
                and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0 and row['maximum_rss_bytes']<=10*1024**3)
            row.update(source=name,sample=1,n=N,source_sha256=plan['programs'][name]['source']['sha256'],power_before=before,power_after=after,
                exact_independent_output=raw==expected,output_valid=valid,competing_processes_before=[],competing_processes_after=[])
            report['cases'].append(row);report['active']=None;atom(output/'report.json',report)
            print(json.dumps(dict(source=name,n=N,seconds=row['elapsed_seconds'],valid=valid)),flush=True)
            require(valid,'Pilot process/output failure; no automatic retry');outputs[name]=raw;verify()
        require(all(outputs[name]==outputs['parent'] for name in NAMES),'Exact parent output differs')
        require(len(report['cases'])==3 and sorted(r['source'] for r in report['cases'])==sorted(NAMES),'Pilot observation inventory differs')
        report.update(status='PASSED',finished_utc=now(),exact_parent_output_match=True,pins_unchanged=True,new_observations=3,
            seconds={r['source']:r['elapsed_seconds'] for r in report['cases']})
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);modes=parser.add_mutually_exclusive_group();modes.add_argument('--prepare',action='store_true');modes.add_argument('--check-only',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.prepare:prepare()
    else:
        with LOCK.open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require(os.fstat(lock.fileno()).st_ino==LOCK.stat().st_ino,'Common mutex changed');plan=verify()
            if args.check_only:print(json.dumps(dict(status='PASSED-METADATA-ONLY',plan=ref(PLAN),full_mode_available=False)))
            else:require(args.output is not None,'Fresh --output required');execute(args.output,plan,lock)
