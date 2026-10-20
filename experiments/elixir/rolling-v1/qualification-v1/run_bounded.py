"""Pinned fresh-process Elixir compilation and bounded complete-output checks.

No pilot/full mode or source-count assignment. Frozen source proposals are copied
byte for byte; support.ex and runner.exs retain their original counted roles.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil

from native_process import atom,now,one,sha,success

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PACKET=HERE.parent
RUNTIME=PACKET/'.build/runtime-v2/elixir'
RESTORE=HERE/'runtime-v2/report.json'
RUNTIME_PLAN=HERE/'runtime-plan-v2.json'
PROPOSAL=PACKET/'plan.json'
CORPUS=ROOT/'experiments/shared/bounded-corpus-v1/cases'
PARENT=ROOT/'programs/elixir/knucleotide/elixir-knucleotide-optimized'
PLAN=HERE/'bounded-plan-v1.json'
OUTPUT=HERE/'bounded-v1'
LOCK=Path('/tmp/mech-clbg-timing.lock')
NAMES=['parent','serial','parallel']
SOURCE_SHA={'parent':'325d3d1992f3fcd2128973802904dd842659c34d20d48ff8ffa73a21620f863c',
 'serial':'c42abaa7c1e04edfea27e2965e70e8d40a1a79294dd1fbc23e74f9b26e62968f',
 'parallel':'b5e24735c6f0494c0d61fca1ec713011b9a689b3c7dc70c23d4adca4441adddb'}
SUPPORT_SHA='c9fbb60888c46fb50195245761a411716f1256145af367e03a23f70aea270e89'
RUNNER_SHA='bdad2389d437fd4c69122e5d25b3065412b4bca0c272631667283273392ba8ff'


def require(value,message):
    if not value:raise ValueError(message)


def ref(path):
    path=Path(path);return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),sha256=sha(path))


def make_plan():
    restore=json.loads(RESTORE.read_bytes());runtime=json.loads(RUNTIME_PLAN.read_bytes())
    require(restore['status']=='PASSED' and restore['plan']==ref(RUNTIME_PLAN),'Restoration not qualified')
    proposal=json.loads(PROPOSAL.read_bytes())
    for p,d in proposal['pins'].items():require(sha(ROOT/p)==d,'Frozen proposal changed')
    pins={}
    def bind(path):
        r=ref(path);pins[r['path']]=r['sha256'];return r
    static=[__file__,HERE/'native_process.py',HERE/'inspect_beam.exs',PROPOSAL,RESTORE,RUNTIME_PLAN,CORPUS/'manifest.json']
    for path in static:bind(path)
    programs={}
    for name in NAMES:
        source=PARENT/'main.ex' if name=='parent' else PACKET/'sources'/(name+'.ex')
        require(sha(source)==SOURCE_SHA[name] and sha(PARENT/'support.ex')==SUPPORT_SHA and sha(PARENT/'runner.exs')==RUNNER_SHA,'Wrong exact source bundle')
        programs[name]=dict(source=bind(source),support=bind(PARENT/'support.ex'),runner=bind(PARENT/'runner.exs'),
            input=str(OUTPUT/'builds'/name/'input'),ebin=str(OUTPUT/'builds'/name/'ebin'))
    manifest=json.loads((CORPUS/'manifest.json').read_bytes());cases=[]
    for row in manifest['cases']:
        if row['benchmark']!='knucleotide':continue
        require(row['expected_exit']==0 and row['validation']=='exact-complete-bytes','Unexpected shared case')
        item=dict(case=row['case'],n=row['n'],stdin=bind(CORPUS/row['stdin']['path']),expected=bind(CORPUS/row['expected']['path']))
        require(item['stdin']['sha256']==row['stdin']['sha256'] and item['expected']['sha256']==row['expected']['sha256'],'Shared corpus changed')
        cases.append(item)
    require(len(cases)==14,'Expected all fourteen shared k-nucleotide cases')
    return dict(schema='elixir-rolling-bounded-plan.v1',status='PREPARED',controller=ref(__file__),process_helper=ref(HERE/'native_process.py'),
        restored_runtime=ref(RESTORE),programs=programs,cases=cases,pins=pins,environment=runtime['environment'],
        runtime_files={**restore['elixir_files'],**restore['otp_files']},common_mutex=str(LOCK),
        output=str(OUTPUT),quantitative_benchmark=False,chart_admission=False,source_count=None,
        source_scope='Main, unchanged general formatting/I/O helper and runner remain application source; no new support exclusion is claimed.')


def unchanged(plan):
    for p,d in {**plan['pins'],**plan['runtime_files']}.items():require(sha(ROOT/p if not Path(p).is_absolute() else p)==d,'Changed qualification/runtime pin: '+p)


def run():
    plan=json.loads(PLAN.read_bytes());require(plan==make_plan(),'Qualification plan/controller changed')
    require(not OUTPUT.exists(),'Fresh bounded attempt required')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require(os.fstat(lock.fileno()).st_ino==LOCK.stat().st_ino,'Common lock changed')
        unchanged(plan);OUTPUT.mkdir()
        report=dict(schema='elixir-rolling-bounded-execution.v1',status='RUNNING',started_utc=now(),plan=ref(PLAN),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,programs={},cases=[],active=None,quantitative_benchmark=False,chart_admission=False)
        def command(label,argv,stdin=None):
            report['active']=label;atom(OUTPUT/'report.json',report)
            row=one(argv,OUTPUT/label,plan['environment'],ROOT,lock.fileno(),timeout=90,stdin=stdin)
            success(row);require(Path(row['stderr']['path']).read_bytes()==b'','Unexpected native diagnostic retained: '+label);return row
        try:
            for name in NAMES:
                p=plan['programs'][name];inp=Path(p['input']);ebin=Path(p['ebin']);inp.mkdir(parents=True);ebin.mkdir()
                for key,dest in [('source','main.ex'),('support','support.ex'),('runner','runner.exs')]:shutil.copyfile(ROOT/p[key]['path'],inp/dest)
                compilation=command('compile-'+name,[str(RUNTIME/'bin/elixirc'),'-o',str(ebin),str(inp/'support.ex'),str(inp/'main.ex')])
                beams={str(f.relative_to(ROOT)):sha(f) for f in ebin.glob('*.beam')}
                require(len(beams)==2,'Unexpected compiled module set')
                inspect_dir=OUTPUT/('inspect-'+name);inspect_dir.mkdir()
                inspection=command('inspect-command-'+name,[str(RUNTIME/'bin/elixir'),'-pa',str(ebin),str(HERE/'inspect_beam.exs'),str(inspect_dir),
                    str(inp/'main.ex'),str(inp/'support.ex'),str(lock.fileno()),str(os.fstat(lock.fileno()).st_ino)])
                report['programs'][name]=dict(**p,source_snapshot=ref(inp/'main.ex'),support_snapshot=ref(inp/'support.ex'),runner_snapshot=ref(inp/'runner.exs'),
                    compiler_command=compilation,inspection=inspection,beams=beams,run_argv=[str(RUNTIME/'bin/elixir'),'-pa',str(ebin),str(inp/'runner.exs')])
                atom(OUTPUT/'report.json',report)
            for case in plan['cases']:
                expected=(ROOT/case['expected']['path']).read_bytes();outputs=[]
                for name in NAMES:
                    row=command('case-'+case['case']+'/'+name,report['programs'][name]['run_argv']+[str(case['n'])],ROOT/case['stdin']['path'])
                    report['cases'].append(dict(source=name,case=case['case'],n=case['n'],expected=case['expected'],stdin=case['stdin'],process=row,
                        exact_reference_bytes=Path(row['stdout']['path']).read_bytes()==expected));atom(OUTPUT/'report.json',report)
                    require(report['cases'][-1]['exact_reference_bytes'],'Bounded complete output differs: '+case['case']+'/'+name)
                    outputs.append(Path(row['stdout']['path']).read_bytes())
                require(outputs[0]==outputs[1]==outputs[2],'Bounded exact parent output differs')
            unchanged(plan);report.update(status='PASSED',active=None,finished_utc=now(),pins_unchanged=True,
                compiled_sources=3,complete_output_observations=42,required_work_witness_status='pending-separate-production-BEAM-tracing',source_count=None)
        except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:atom(OUTPUT/'report.json',report)
    print(report['status'],len(report['programs']),len(report['cases']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.run,'Choose one mode')
    if args.prepare:require(not PLAN.exists(),'Fresh plan required');atom(PLAN,make_plan())
    else:run()
