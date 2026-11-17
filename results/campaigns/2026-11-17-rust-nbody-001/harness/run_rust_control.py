#!/usr/bin/env python3
"""Measure the full N-body task against the retained Rust source in randomized pairs."""
import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import random
import shutil

from application_tasks import NBODY_STEPS, validate_nbody
from benchmark_suite import (ROOT, SCHEMA, archive_evidence, campaign_lock, digest, environment,
    execute, file_digest, load_catalog, preserve_worker, save, seal_evidence, summarize, validate_campaign, worker_provenance)


def run(args):
    directory=args.output.resolve()
    if directory.exists():raise ValueError('choose a new campaign directory')
    worker=worker_provenance(args.application_worker)
    app=worker['applications']['mech-numerical-application']
    if file_digest(app['binary'])!=app['binary_sha256']:raise ValueError('application binary changed')
    case=next(c for c in load_catalog()['cases'] if c['id']=='nbody')
    host=environment()
    contract={'task':'Five-body ordered f64 N-body; 50,000,000 steps; initial and final energy within 1e-8',
              'boundary':'Fresh process launch through complete output and exit; compilation excluded; startup JIT included for Mech',
              'arithmetic':'No requested fast math, reassociation or reciprocal approximation',
              'threads':'One application thread; independent implementation/vectorization permitted'}
    rng=random.Random(args.seed)
    orders=[rng.sample(['fused-native','rust'],2) for _ in range(args.forks)]
    campaign={'schema':SCHEMA,'id':directory.name,'started_at':datetime.now(timezone.utc).isoformat(),
              'profile':'rust-task-control','environment':host,'environment_hash':digest(host),
              'workers':{'candidate':worker,'applications':worker},'complete':False,'results':[],
              'sampling':{'forks':args.forks,'seed':args.seed,'order':orders,'warmup':'None; no discarded full runs'},
              'comparison_contract':contract,'performance_gate':False,'comparisons':[]}
    with campaign_lock(ROOT/'.local'):
        directory.mkdir(parents=True);save(directory/'campaign.json',campaign)
        preserve_worker(worker,directory/'workers/applications')
        source=ROOT/'programs/rust/nbody/rust-3/nbody-rust-3.rs'
        build=directory/'raw/build'
        source_copy=directory/'rust/nbody.rs';source_copy.parent.mkdir();shutil.copyfile(source,source_copy)
        shutil.copyfile(source.with_name('program.json'),source_copy.with_name('program.json'))
        binary=directory/'nbody-rust'
        command=['rustc','+nightly-2026-03-03',str(source_copy),'-C','opt-level=3','-C','target-cpu=native','-C','codegen-units=1','-o',str(binary)]
        if execute(command,build,args.timeout)['outcome']!='ok':raise ValueError('Rust build failed')
        execute(['rustc','+nightly-2026-03-03','-Vv'],directory/'raw/rust-version',args.timeout)
        version=(directory/'raw/rust-version/stdout.txt').read_text()
        rust={'binary_sha256':file_digest(binary),'adapter_sha256':file_digest(source_copy),'rustc':version,'build_command':command}
        records={}
        for backend in ['fused-native','rust']:
            text=source_copy.read_text() if backend=='rust' else (ROOT/case['source']).read_text()
            measurement={**case['measurement'],'backend':backend,'comparison_note':'Same full task and complete process boundary, same machine and randomized cohort. Algorithms and vectorization may differ; median change is informational.'}
            record={'case_id':'nbody','title':'Rust · Benchmarks Game #3' if backend=='rust' else case['title'],'family':case['family'],
                    'backend':backend,'lane':'control' if backend=='rust' else 'candidate','revision':file_digest(source_copy) if backend=='rust' else worker['revision'],
                    'task':case['task'],'task_hash':digest(case['task']),'measurement':measurement,'measurement_hash':digest(measurement),
                    'source':text,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'environment_hash':digest(host),'feature_profile':{'profile':backend},'control_contract':digest(contract),
                    'progress':'implemented','outcome':'pending','capability':'unknown','samples':[]}
            if backend=='rust':record['implementation']=rust
            records[backend]=record;campaign['results'].append(record)
        save(directory/'campaign.json',campaign)
        for fork,order in enumerate(orders):
            for backend in order:
                command=[str(binary),str(NBODY_STEPS)] if backend=='rust' else [app['binary'],str(NBODY_STEPS),str(ROOT/case['source']),'jit-simd']
                out=directory/f'raw/{backend}/fork-{fork+1}'
                print(f'N-body full task / {backend} / fork {fork+1}',flush=True)
                response=execute(command,out,args.timeout)
                record=records[backend]
                if response['outcome']!='ok':raise ValueError('application failed; all raw evidence retained')
                endpoint=validate_nbody((out/'stdout.txt').read_bytes(),[-.169075164,-.169059907])
                metrics={'native_process_seconds':response['seconds']}
                save(out/'supervised.json',{**response,'metrics':metrics,'final_output':endpoint,'validation':'Independent preserved full-step energies; exact output arity and finite values checked.'})
                relative=out.relative_to(directory).as_posix()
                record['samples'].append({'fork':fork,'raw':relative,'metrics':metrics,'final_output':endpoint})
                record['verification']={'outcome':'ok','raw':relative,'outputs':[endpoint],
                    'reason':'Every measured fresh process executes all 50,000,000 steps and matches the independently preserved initial and final energy, within 1e-8.'}
                save(directory/'campaign.json',campaign)
        if file_digest(binary)!=rust['binary_sha256'] or file_digest(app['binary'])!=app['binary_sha256']:raise ValueError('measured binary changed')
        for record in records.values():record.update(summary=summarize(record['samples']),progress='measured',outcome='ok',capability='supported')
        campaign.update(complete=True,outcome='ok',finished_at=datetime.now(timezone.utc).isoformat())
        save(directory/'campaign.json',campaign)
        (directory/'report.md').write_text(f'# Full N-body Rust control\n\n{args.forks} randomized pairs, all 50,000,000 steps per process. Complete launch through exit. '
            'Rust uses the unchanged retained Benchmarks Game #3 source; source authorship, build flags, compiler and binary hashes are retained. '
            'No warmup samples or adverse observations are removed. This exploratory cohort does not promote a new Mech control.\n\n'+
            '\n'.join(f"- {backend}: {record['summary']['native_process_seconds']['median']:.9f} s" for backend,record in records.items())+'\n')
        binary.unlink()  # Immutable hash/build receipt retained; executable is a local build product.
        seal_evidence(directory);archive_evidence(directory);validate_campaign(directory,campaign)
        return campaign


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--application-worker',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--forks',type=int,default=5)
    p.add_argument('--seed',type=int,default=202611171);p.add_argument('--timeout',type=float,default=120)
    a=p.parse_args()
    if a.forks<3:p.error('at least three independent forks required')
    run(a)
