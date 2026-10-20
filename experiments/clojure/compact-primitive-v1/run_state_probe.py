"""Untimed state qualification against the four exact compiled applications."""
import argparse
import fcntl
import os
from pathlib import Path

import run_serial as run
from build_candidates import check


def execute(output):
    run.require(output.is_relative_to(run.HERE) and not output.exists() and not (run.HERE/'state-probe-report.json').exists(),'Use fresh state-probe output')
    with open(run.LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run.competition();output.mkdir(parents=True)
        runtime=run.load(run.HERE/'runtime-build.json');builds=run.load(run.HERE/'builds.json')
        run.require(runtime['status']==builds['status']=='PASSED' and builds['runtime']==run.ref(run.HERE/'runtime-build.json'),'Completed exact builds required')
        pins=dict(runtime['pins'])
        for program in builds['programs'].values():pins.update(program['class_pins'])
        probe=run.HERE/'state_probe.clj';pins[run.ref(probe)['path']]=run.sha(probe)
        for path,digest in pins.items():run.check_ref(dict(path=path,sha256=digest))
        classpath=':'.join([builds['programs'][name]['classes'] for name in run.NAMES]+[str(run.ROOT/row['path']) for row in runtime['jars']])
        command=[str(run.ROOT/runtime['java']['path']),*run.FLAGS,'-cp',classpath,'clojure.main',str(probe)]
        record=run.one(command,output/'process',60,runtime['environment'],lock.fileno());check(record)
        raw=Path(record['stdout']['path']).read_text()
        run.require(':status :pass' in raw and ':advance-function-invocations 464' in raw and ':inner-pair-store-counters :not-instrumented-source-proof-only' in raw,'Unexpected full-state probe receipt')
        for path,digest in pins.items():run.check_ref(dict(path=path,sha256=digest))
        report=dict(schema='clojure-nbody-state-probe.v1',status='PASSED',mode='untimed-qualified-state',
            controller=run.ref(__file__),script=run.ref(probe),runtime=run.ref(run.HERE/'runtime-build.json'),builds=run.ref(run.HERE/'builds.json'),
            pins=pins,process=record,cases=[0,1,2,3,10,100],implementations=4,raw_bit_state_slots=35,
            advance_function_invocations=464,inner_pair_store_counters='not-instrumented-source-proof-only',
            chart_admission=False,timing_sample=False,common_mutex_inode=os.fstat(lock.fileno()).st_ino)
        run.atom(output/'report.json',report);run.atom(run.HERE/'state-probe-report.json',report)
        print(':status :pass;464 actual advance calls;35 state slots and energy compared by raw bits')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();execute(args.output.resolve())
