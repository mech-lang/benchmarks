"""Measure the unchanged compact Fannkuch source with first-call YJIT."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

from lean_run import FULL, atom, now, sha

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'experiments/ruby-jit'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'first-call-v1')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();args.output=args.output.resolve()
    plan=json.loads((HERE/'plan-v1.json').read_text())
    archive=HERE/'controller-v1.py';assert sha(archive)==plan['controller_sha256']
    spec=importlib.util.spec_from_file_location('ruby_measurement_v1',archive)
    recorder=importlib.util.module_from_spec(spec);spec.loader.exec_module(recorder)
    profile=next(p for p in plan['profiles'] if p['id']=='fannkuchredux-ruby-8')
    policy_path=HERE/'engine-policy-v1/diagnostics/report.json'
    policy=json.loads(policy_path.read_text());assert policy['status']=='PASSED'
    check=next(c for c in policy['cases'] if c['jit']=='yjit' and c['policy']=='first-call')
    default=next(c for c in policy['cases'] if c['jit']=='yjit' and c['policy']=='default')
    assert check['valid'] and check['elapsed_seconds'] < default['elapsed_seconds']*.8
    assert 'fannkuch@' in (ROOT/check['compilation_log']['path']).read_text()
    command=recorder.command(profile,'yjit',12)
    command.insert(2,'--yjit-call-threshold=1')
    path=args.output/'report.json'
    if args.resume:
        report=json.loads(path.read_text())
        assert report['controller_sha256']==sha(__file__) and report['command']==command
    else:
        args.output.mkdir(parents=True,exist_ok=False)
        report=dict(schema='ruby-yjit-first-call-full.v1',status='RUNNING',started_utc=now(),
            controller_sha256=sha(__file__),source_sha256=profile['source_sha256'],
            original_program_key=profile['key'],runtime_sha256=plan['runtime']['sha256'],
            command=command,environment=profile['environment'],n=12,cases=[],active=None,
            policy_diagnostic=dict(path=str(policy_path.relative_to(ROOT)),sha256=sha(policy_path)),
            timing_boundary=plan['timing_boundary'],chart_admission=False,
            source_unchanged=True,logging_and_inspection_disabled_in_measured_processes=True)
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['common_mutex_inode']=os.fstat(lock.fileno()).st_ino
        assert json.loads((HERE/'full-v1/report.json').read_text())['status']=='PASSED'
        for sample in range(len(report['cases'])+1,4):
            assert sha(__file__)==report['controller_sha256']
            assert sha(ROOT/profile['source_path'])==profile['source_sha256']
            assert sha(plan['runtime']['path'])==plan['runtime']['sha256']
            power=dict(before=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True),
                       settings=subprocess.check_output(['/usr/bin/pmset','-g','custom'],text=True))
            assert 'AC Power' in power['before'] and re.search(r'lowpowermode\s+0',power['settings'])
            rows=subprocess.check_output(['/bin/ps','-axo','pid,comm'],text=True).splitlines()[1:]
            forbidden={'ruby','cargo','rustc','clang','clang++','lean','leanc','lake','julia','hyperfine','luau-host'}
            competitors=[r for r in rows if len(r.split(maxsplit=1))==2 and Path(r.split(maxsplit=1)[1]).name in forbidden]
            assert not competitors,competitors
            power['competing_processes_before']=competitors
            report['active']=dict(sample=sample,started_utc=now());atom(path,report)
            directory=args.output/f'{sample:03d}-fannkuchredux-yjit-first-call'
            record=recorder.execute(command,profile['environment'],Path('/dev/null'),directory,3600)
            valid=(record['exit_code']==0 and not record['timed_out'] and record['stderr']['bytes']==0 and
                   record['stdout']['bytes']==FULL['fannkuchredux'][1] and record['stdout']['sha256']==FULL['fannkuchredux'][2])
            power['after']=subprocess.check_output(['/usr/bin/pmset','-g','batt'],text=True)
            valid=valid and 'AC Power' in power['after']
            record.update(key=profile['key'],benchmark='fannkuchredux',jit='yjit',policy='first-call',sample=sample,n=12,
                source_sha256=profile['source_sha256'],runtime_sha256=plan['runtime']['sha256'],valid=valid,power=power)
            atom(directory/'process.json',record);report['cases'].append(record);report['active']=None;atom(path,report)
            print(f'{sample} YJIT first-call full: {"PASS" if valid else "FAIL"} {record["elapsed_seconds"]:.3f}s',flush=True)
            if not valid:
                report['status']='FAILED';atom(path,report);raise SystemExit(1)
        report.update(status='PASSED',finished_utc=now());atom(path,report)


if __name__=='__main__':main()
