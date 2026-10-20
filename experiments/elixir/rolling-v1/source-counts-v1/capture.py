"""Exact retained Elixir frontend capture; source data are never evaluated.

New host entrypoint validates the current mutex without patching frozen reader
or counter constants. All retained reader function bytes remain identical.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path

from native_process import atom,now,one,sha,success

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PLAN=HERE/'plan-v1.json'
OUTPUT=HERE/'run-v1'
STAGED=HERE/'retained-reader-host-v1.exs'
FRONTEND=ROOT/'experiments/elixir/source-counts-v1/read_sources.exs'
FRONTEND_SHA='b2f2102e16ed2213eaf012704952c5bda9da116fb7af736363664eda321e0b3b'
COUNTER=ROOT/'tools/qualification/elixir_source_units.py'
COUNTER_SHA='d1070e8f38fdebdfe2523c918bfb4367958667f34bf3c77efb6d6725544dc07f'
OLD_PLAN=ROOT/'experiments/elixir/source-counts-v1/plan-v1.json'
OLD_REPLAY=ROOT/'experiments/elixir/source-units-v1/replay-v2.json'
QUALIFIED=ROOT/'experiments/elixir/source-units-v1/qualified-source-counts.json'
CONTRACT=ROOT/'experiments/elixir/source-units-v1/fixture-contract.json'
QUAL=HERE.parent/'qualification-v1'
PARENT=ROOT/'programs/elixir/knucleotide/elixir-knucleotide-optimized'
RUNTIME=HERE.parent/'.build/runtime-v2/elixir'
LOCK=Path('/tmp/mech-clbg-timing.lock')
ENTRY=b'\nSourceCountReader.main(System.argv())\n'


def require(value,message):
    if not value:raise ValueError(message)


def ref(path):
    p=Path(path);return dict(path=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),sha256=sha(p))


def staged_bytes():
    require(sha(FRONTEND)==FRONTEND_SHA and sha(COUNTER)==COUNTER_SHA,'Qualified frontend/counter changed')
    raw=FRONTEND.read_bytes();require(raw.endswith(ENTRY) and raw.count(ENTRY)==1,'Ambiguous retained reader entrypoint')
    return raw[:-len(ENTRY)]+b'\n'+(HERE/'reader_host.exs').read_bytes()


def make_plan(create=False):
    expected=staged_bytes()
    if create:require(not STAGED.exists(),'Fresh staged host required');STAGED.write_bytes(expected)
    require(STAGED.read_bytes()==expected,'Staged native parser functions differ')
    old=json.loads(OLD_PLAN.read_bytes());restore=json.loads((QUAL/'runtime-v2/report.json').read_bytes())
    runtime=json.loads((QUAL/'runtime-plan-v2.json').read_bytes())
    require(restore['status']=='PASSED' and len(restore['elixir_files'])==723 and len(restore['otp_files'])==4243,'Exact restored runtime required')
    inputs=[]
    for identity,path,role in [('parent-main',PARENT/'main.ex','application'),
        ('serial-main',HERE.parent/'sources/serial.ex','application'),('parallel-main',HERE.parent/'sources/parallel.ex','application'),
        ('support',PARENT/'support.ex','runtime-support'),('runner',PARENT/'runner.exs','runtime-support')]:
        inputs.append(dict(id=identity,path=str(path),sha256=sha(path),kind='application',role=role,expected_parse='ok'))
    inputs.extend(copy.deepcopy(row) for row in old['inputs'] if row['kind']=='fixture')
    require(len(inputs)==19,'Expected5sources+14retained fixtures')
    for row in inputs:
        if row['kind']=='fixture':require(hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256'],'Retained fixture differs')
    static=[Path(__file__),HERE/'native_process.py',HERE/'reader_host.exs',STAGED,FRONTEND,COUNTER,OLD_PLAN,OLD_REPLAY,QUALIFIED,CONTRACT,
        ROOT/'experiments/elixir/source-units-v1/review.md',ROOT/'docs/methodology.md',ROOT/'docs/source-metrics.md',ROOT/'docs/source-size-correction.md',
        ROOT/'data/source-size-review.json',ROOT/'experiments/source-size-correction/v1/receipt.json',PARENT/'program.json',
        QUAL/'runtime-v2/report.json',QUAL/'runtime-plan-v2.json']
    oldreader=ROOT/'experiments/elixir/source-counts-v1/run-v1/reader'
    for role in ['application','application-helper','application-launcher']:
        folder=oldreader/('elixir-knucleotide-optimized--'+role)
        static.extend(folder/name for name in ['source.exs','ast.json','ast.etf','formatted.exs','formatted-ast.json'])
    pins={ref(path)['path']:sha(path) for path in static}
    for row in inputs:
        if row['kind']=='application':pins[ref(row['path'])['path']]=row['sha256']
    env={k:v for k,v in runtime['environment'].items() if k!='ERL_COMPILER_OPTIONS'}
    # Independent count-capture home/config/tmp; immutable runtime paths/flags.
    stage=HERE.parent/'.build/source-counts-v1'
    env.update(HOME=str(stage/'home'),XDG_CONFIG_HOME=str(stage/'config'),TMPDIR=str(stage/'tmp')+'/',ERL_CRASH_DUMP=str(stage/'erl-crash.dump'))
    return dict(schema='elixir-source-reader-plan-v1',status='PREPARED-NO-APPLICATION-EXECUTION',inputs=inputs,
        profiles=[dict(id=name,inputs=[name+'-main','support','runner']) for name in ['parent','serial','parallel']],
        controller=ref(__file__),frontend=ref(FRONTEND),counter=ref(COUNTER),staged_host=ref(STAGED),host_delta=ref(HERE/'reader_host.exs'),
        host_derivation='Exact original module byte prefix; only the final SourceCountReader.main invocation is replaced by the appended host. Historical inode assertion remains unchanged in the unused original main. All parser/formatter/inspection function bytes and Python counter constants are unchanged.',
        pins=pins,runtime_files={**restore['elixir_files'],**restore['otp_files']},environment=env,runtime=str(RUNTIME/'bin/elixir'),
        common_mutex=str(LOCK),common_mutex_inode=LOCK.stat().st_ino,output=str(OUTPUT),
        retained_rule_version='canonical-source-units-20261012-approved-rule-v2',retained_grammar='elixir-native-position-owners-v1',
        current_application_policy='application-loc-v1',uniform_logical_axis_qualified=False,
        source_evaluations=0,subject_recompilations=0,subject_main_invocations=0,
        application_loc=None,formatted_loc=None,independent_review_approved=False,chart_admission=False)


def verify(plan):
    require(plan==make_plan(),'Capture plan/host changed')
    for path,digest in {**plan['pins'],**plan['runtime_files']}.items():require(sha(ROOT/path if not Path(path).is_absolute() else path)==digest,'Changed source/count/runtime pin: '+path)


def run():
    plan=json.loads(PLAN.read_bytes());require(not OUTPUT.exists(),'Fresh native capture required')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require(os.fstat(lock.fileno()).st_ino==plan['common_mutex_inode']==LOCK.stat().st_ino,'Common mutex changed')
        verify(plan);OUTPUT.mkdir()
        for variable in ['HOME','XDG_CONFIG_HOME','TMPDIR']:Path(plan['environment'][variable]).mkdir(parents=True,exist_ok=True)
        report=dict(schema='elixir-rolling-retained-source-capture.v1',status='RUNNING',plan=ref(PLAN),started_utc=now(),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,source_evaluations=0,subject_recompilations=0,subject_main_invocations=0,
            application_loc=None,formatted_loc=None,chart_admission=False)
        atom(OUTPUT/'report.json',report)
        try:
            row=one([plan['runtime'],str(STAGED),str(PLAN),str(OUTPUT/'reader'),str(lock.fileno())],OUTPUT/'native-process',plan['environment'],ROOT,lock.fileno(),timeout=120)
            report['process']=row;success(row)
            require(Path(row['stdout']['path']).read_bytes()==Path(row['stderr']['path']).read_bytes()==b'','Unexpected reader diagnostic retained')
            native=json.loads((OUTPUT/'reader/report.json').read_bytes())
            require(native['application_files']==5 and native['fixture_files']==14 and len(native['items'])==19
                and all(native[k]==0 for k in ['source_evaluations','subject_recompilations','subject_main_invocations']),'Native source-only contract differs')
            verify(plan);report.update(status='PASSED-NATIVE-READER-AWAITING-OWNER-REVIEW',finished_utc=now(),pins_unchanged=True,
                artifacts={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted((OUTPUT/'reader').rglob('*')) if p.is_file()})
        except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:atom(OUTPUT/'report.json',report)
    print(report['status'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.run,'Choose one mode')
    if args.prepare:require(not PLAN.exists(),'Fresh plan required');atom(PLAN,make_plan(create=True))
    else:run()
