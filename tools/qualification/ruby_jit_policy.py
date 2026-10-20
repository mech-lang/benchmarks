"""Inspect cold-method compilation, serially after the full Ruby cohort.

These N=10 runs are diagnostics, never chart timings or full-size estimates.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path

from lean_run import atom, now, sha

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'experiments/ruby-jit'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output=args.output.resolve()
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        # A waiting diagnostic process consumes no benchmark resources and
        # cannot overlap the full cohort which owns the same lock.
        fcntl.flock(lock,fcntl.LOCK_EX)
        full=HERE/'full-v1/report.json'
        assert json.loads(full.read_text())['status']=='PASSED'
        args.output.mkdir(parents=True,exist_ok=False)
        plan=json.loads((HERE/'plan-v1.json').read_text())
        archive=HERE/'controller-v1.py'
        assert sha(archive)==plan['controller_sha256']
        spec=importlib.util.spec_from_file_location('ruby_measurement_v1',archive)
        recorder=importlib.util.module_from_spec(spec);spec.loader.exec_module(recorder)
        profile=next(p for p in plan['profiles'] if p['id']=='fannkuchredux-ruby-8')
        assert sha(ROOT/profile['source_path'])==profile['source_sha256']
        probe=HERE/'engine-policy-v1/inspect.rb'
        report=dict(schema='ruby-jit-cold-method-diagnostic.v1',status='RUNNING',started_utc=now(),
            full_prerequisite=dict(path=str(full.relative_to(ROOT)),sha256=sha(full)),
            source_sha256=profile['source_sha256'],recorder_sha256=sha(archive),probe_sha256=sha(probe),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,cases=[],chart_admission=False,
            scope='N=10 compilation diagnostics. Diagnostic times are not full-size estimates or chart observations.')
        expected=None
        for mode in ['yjit','zjit']:
            for policy in ['default','first-call']:
                directory=args.output/(mode+'-'+policy)
                flags=[]
                if policy=='first-call':
                    flags=['--'+mode+'-call-threshold=1']
                    if mode=='zjit':flags.append('--zjit-num-profiles=0')
                log=directory/'compilation.log'
                logging='--yjit-log='+str(log) if mode=='yjit' else '--zjit-log-compiled-iseqs='+str(log)
                original=recorder.command(profile,mode,10)
                command=[original[0],*flags,logging,'-r',str(probe),*original[1:]]
                environment=dict(profile['environment'],RUBY_POLICY_KERNEL='fannkuch',RUBY_POLICY_REPORT=str(directory/'engine.json'))
                record=recorder.execute(command,environment,Path('/dev/null'),directory,180)
                valid=record['exit_code']==0 and not record['timed_out']
                if valid:
                    output=(directory/'stdout.bin').read_bytes()
                    if expected is None:expected=output
                    valid=output==expected
                record.update(jit=mode,policy=policy,n=10,valid=valid)
                if (directory/'engine.json').exists():record['engine']=json.loads((directory/'engine.json').read_text())
                if log.exists():record['compilation_log']=dict(path=str(log.relative_to(ROOT)),sha256=sha(log))
                atom(directory/'process.json',record)
                report['cases'].append(record);atom(args.output/'report.json',report)
                print(f'{mode} {policy}: {"PASS" if valid else "FAIL"} diagnostic {record["elapsed_seconds"]:.3f}s',flush=True)
                if not valid:
                    report['status']='FAILED';atom(args.output/'report.json',report);raise SystemExit(1)
        report.update(status='PASSED',finished_utc=now());atom(args.output/'report.json',report)


if __name__=='__main__':main()
