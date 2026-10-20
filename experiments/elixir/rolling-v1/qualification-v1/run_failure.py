"""Source-bound callback failure twin and native descendant cleanup, untimed."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil

from native_process import atom,now,one,sha,success
import run_bounded_v2 as bounded

ROOT,HERE,RUNTIME,LOCK=bounded.ROOT,bounded.HERE,bounded.RUNTIME,bounded.LOCK
PLAN=HERE/'failure-plan-v1.json'
OUTPUT=HERE/'failure-v1'
TWIN=HERE/'failure-twin-v1.ex'
SOURCE=HERE.parent/'sources/parallel.ex'
REPLACE='fn width -> result(dna, width) end'
INJECT='''fn width ->
        if width == 3 do
          Process.sleep(100)
          raise "injected width3 failure"
        else
          Process.sleep(10_000)
          result(dna, width)
        end
      end'''
require,ref=bounded.require,bounded.ref


def make_plan(create=False):
    require(sha(SOURCE)==bounded.SOURCE_SHA['parallel'],'Production parallel source differs')
    source=SOURCE.read_text();require(source.count(REPLACE)==1,'Failure callback delta ambiguous');expected=source.replace(REPLACE,INJECT)
    if create:require(not TWIN.exists(),'Fresh twin required');TWIN.write_text(expected)
    require(TWIN.read_text()==expected,'Failure twin contains any extra change')
    bp=json.loads(bounded.PLAN.read_bytes())
    pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'native_process.py',HERE/'failure_probe.exs',TWIN,SOURCE,bounded.PLAN,
        bounded.PARENT/'support.ex',HERE/'bounded-v1/compile-parent/stderr.bin']}
    stdin=ROOT/bp['cases'][0]['stdin']['path'];pins[str(stdin.relative_to(ROOT))]=sha(stdin)
    return dict(schema='elixir-rolling-failure-plan.v1',status='PREPARED',source=ref(SOURCE),twin=ref(TWIN),
        exact_delta=dict(find=REPLACE,replace=INJECT),pins=pins,environment={k:v for k,v in bp['environment'].items() if k!='ERL_COMPILER_OPTIONS'},
        runtime_files=bp['runtime_files'],stdin=ref(stdin),common_mutex=str(LOCK),
        scope='Only a separately compiled callback twin raises in width3 after100ms and holds other workers for10s, allowing failure propagation and monitor cleanup to be observed. Production source/BEAM and timed source remain unchanged.',
        quantitative_benchmark=False,chart_admission=False,source_count=None)


def run():
    plan=json.loads(PLAN.read_bytes());require(plan==make_plan(),'Failure plan/controller changed');require(not OUTPUT.exists(),'Fresh failure attempt required')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);require(os.fstat(lock.fileno()).st_ino==LOCK.stat().st_ino,'Common lock changed')
        bounded.unchanged(plan);OUTPUT.mkdir();inp=OUTPUT/'input';inp.mkdir();ebin=OUTPUT/'ebin';ebin.mkdir()
        shutil.copyfile(TWIN,inp/'main.ex');shutil.copyfile(bounded.PARENT/'support.ex',inp/'support.ex')
        report=dict(schema='elixir-rolling-failure-execution.v1',status='RUNNING',plan=ref(PLAN),started_utc=now(),attempts=[],
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,quantitative_benchmark=False,chart_admission=False)
        atom(OUTPUT/'report.json',report)
        try:
            compilation=one([str(RUNTIME/'bin/elixirc'),'-o',str(ebin),str(inp/'support.ex'),str(inp/'main.ex')],OUTPUT/'compile',plan['environment'],ROOT,lock.fileno())
            report['attempts'].append(compilation);success(compilation)
            template=(HERE/'bounded-v1/compile-parent/stderr.bin').read_bytes().replace(
                b'experiments/elixir/rolling-v1/qualification-v1/bounded-v1/builds/parent/input/support.ex',str((inp/'support.ex').relative_to(ROOT)).encode())
            require(Path(compilation['stderr']['path']).read_bytes()==template,'Unexpected failure-twin compiler diagnostic')
            beam=ebin/'Elixir.Clbg.Main.beam';result=OUTPUT/'result.json'
            spec=dict(lock_fd=str(lock.fileno()),lock_inode=os.fstat(lock.fileno()).st_ino,result=str(result),main_beam_sha256=sha(beam));atom(OUTPUT/'spec.json',spec)
            raw=one([str(RUNTIME/'bin/elixir'),'-pa',str(ebin),str(HERE/'failure_probe.exs'),str(OUTPUT/'spec.json')],OUTPUT/'process',plan['environment'],ROOT,lock.fileno(),timeout=30,stdin=ROOT/plan['stdin']['path'])
            report['attempts'].append(raw);success(raw);w=json.loads(result.read_bytes())
            require(w['status']=='PASSED' and w['all_application_descendants_dead'] is True and w['failure_propagated'] is True,'Failure cleanup incomplete')
            # Logger output is expected only for this intentionally failing twin;
            # exact raw streams are retained and must contain the injected label.
            combined=Path(raw['stdout']['path']).read_bytes()+Path(raw['stderr']['path']).read_bytes()
            require(b'injected width3 failure' in combined,'Expected native task failure diagnostic missing')
            bounded.unchanged(plan);report.update(status='PASSED',finished_utc=now(),result=ref(result),beam=ref(beam),pins_unchanged=True)
        except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:atom(OUTPUT/'report.json',report)
    print(report['status'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.run,'Choose one mode')
    if args.prepare:require(not PLAN.exists(),'Fresh plan required');atom(PLAN,make_plan(create=True))
    else:run()
