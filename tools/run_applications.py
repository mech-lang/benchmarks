#!/usr/bin/env python3
"""Run full-size applications and pinned controls; never substitute smoke inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
from application_tasks import (FASTA_N, NBODY_STEPS, deflate_cases, validate_deflate, nbody_output, validate_nbody)
from benchmark_suite import (ROOT, SCHEMA, archive_evidence, campaign_lock, digest, environment, execute,
    file_digest, invoke, load_catalog, preserve_worker, save, seal_evidence, summarize, worker_provenance)


def required_command(command, directory, timeout, **kwargs):
    response=execute([str(x) for x in command],directory,timeout,**kwargs)
    if response['outcome']!='ok':raise ValueError(f'command failed; inspect {directory}')
    return response


def raw(directory):
    return (directory/'stdout.txt').read_bytes()


def java_home(path):
    path=Path(path).resolve()
    if not (path/'java').is_file() or not (path/'javac').is_file():raise ValueError('supply the real JDK bin directory, not an OS launcher stub')
    return path


def run(args):
    output=args.output.resolve()
    if output.exists():raise ValueError('choose a new campaign directory')
    worker=worker_provenance(args.worker);apps=worker_provenance(args.application_worker)
    for name,value in apps.get('applications',{}).items():
        if file_digest(value['binary'])!=value['binary_sha256']:raise ValueError('application binary changed: '+name)
    if worker['revision']!=apps['revision']:raise ValueError('application and canonical workers must pin the same compiler')
    controls=json.loads(args.controls.read_text())
    if controls.get('schema')!='mech.compression-controls.v1':raise ValueError('invalid controls receipt')
    for name in ('roc','libdeflate'):
        if file_digest(controls[name]['binary'])!=controls[name]['binary_sha256']:raise ValueError('control binary changed: '+name)
    if file_digest(controls['wrapper'])!=controls['wrapper_sha256']:raise ValueError('control wrapper changed')
    jdk=java_home(args.java)
    cases=[c for c in load_catalog()['cases'] if set(c['backends']) & {'source-native','fused-native','jvm','program-jit','program-jit-bytecode','roc','libdeflate'}]
    host=environment()
    campaign={'schema':SCHEMA,'id':output.name,'started_at':datetime.now(timezone.utc).isoformat(),'profile':'full-applications',
        'sampling':{'forks':args.forks,'deflate_warmup_calls':1,'application_warmup':'fresh processes; no discarded full runs'},
        'environment':host,'environment_hash':digest(host),'workers':{'candidate':worker,'applications':apps},
        'controls':controls,'harness_sha256':{n:file_digest(ROOT/'tools'/n) for n in ['run_applications.py','application_tasks.py','benchmark_suite.py']},
        'catalog_sha256':file_digest(ROOT/'suite/catalog.json'),'performance_gate':False,'results':[],'order':[],'comparisons':[],'complete':False}
    records={}
    with campaign_lock(ROOT/'.local'):
        output.mkdir(parents=True);preserve_worker(worker,output/'workers/candidate');preserve_worker(apps,output/'workers/applications')
        save(output/'controls.json',controls)
        for case in cases:
            save(output/'fixtures'/(case['id']+'.json'),case)
            for backend in case['backends']:
                if backend == 'program-linked':
                    continue  # Its separate public-link qualification has no accepted executable timing.
                measurement={**case['measurement'],'backend':backend}
                if backend in ('program-jit','program-jit-bytecode'):measurement.update(warmup_calls=1,artifact_form='decoded bytecode' if backend.endswith('bytecode') else 'source',program_case_group=12,compiler_policy=json.loads((ROOT/'suite/applications/deflate-compiler-policy.json').read_text()),launch_policy=json.loads((ROOT/'suite/applications/deflate-launch-policy.json').read_text()))
                if backend=='source-native':measurement.update(threads=4,source_native_policy={'partitions':4,'simd':True,'standard_map':True,'narrow_histogram':True},input_transport='complete inherited stdin file; read during process')
                if backend=='fused-native':measurement['native_numeric_options']='jit-simd; all optional numerical transformation flags disabled'
                if backend=='jvm':measurement['thread_policy']='one application thread; ActiveProcessorCount=1, SerialGC; HotSpot JIT threads remain part of process'
                if backend in ('roc','libdeflate'):measurement.update(primary_metric='control_call_seconds',boundary='complete_compressor_call',allocator='system malloc',output_reservation='exact prefix + input + 5 * max(1,ceil(input/5000))',setup='File loading and held-alias/output reservation excluded from call; whole process separately recorded',destruction='Compressor scratch destruction included; previous and returned output destruction outside call')
                source=(ROOT/case['source']).read_text()
                revision=worker['revision']
                if backend=='roc':source=controls['roc']['app_source'];revision=controls['roc']['compiler_revision']
                if backend=='libdeflate':source=(ROOT/'suite/controls/deflate_control.c').read_text();revision=controls['libdeflate']['source_revision']
                record={'case_id':case['id'],'title':case['title'],'family':case['family'],'backend':backend,'lane':'candidate','revision':revision,
                    'progress':'implemented','capability':'unknown','outcome':'pending','task':case['task'],'measurement':measurement,'task_hash':digest(case['task']),
                    'measurement_hash':digest(measurement),'source':source,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'environment_hash':digest(host),
                    'feature_profile':{'profile':worker['feature_profile'] if backend in ('program-jit','program-jit-bytecode') else backend,'native_generation':backend in ('program-jit','program-jit-bytecode')},'samples':[]}
                records[case['id'],backend]=record;campaign['results'].append(record)
        save(output/'campaign.json',campaign)
        def persist():save(output/'campaign.json',campaign)
        def accept(record, fork, directory, metrics, observed, provenance=None):
            receipt={'outcome':'ok','metrics':metrics,'final_output':observed,**(provenance or {})};save(directory/'supervised.json',receipt)
            relative=directory.relative_to(output).as_posix()
            if fork is None:
                record.update(progress='verified',capability='supported',outcome='ok',verification={'outcome':'ok','reason':'Complete full-size task and required ownership/stream checks passed.','outputs':[observed],'raw':relative})
            else:
                record['samples'].append({'fork':fork,'raw':relative,'metrics':metrics,'final_output':observed})
                campaign['order'].append({'case_id':record['case_id'],'backend':record['backend'],'fork':fork,'lane':'candidate'})
            persist()
        # Build the independent Java implementation before any application timings.
        directory=output/'raw/prepare/java';directory.mkdir(parents=True)
        shutil.copyfile(ROOT/'suite/applications/nbody.java',directory/'nbody.java')
        required_command([jdk/'javac','-d',directory,directory/'nbody.java'],output/'raw/prepare/javac',args.timeout)
        required_command([jdk/'java','-version'],output/'raw/prepare/java-version',args.timeout)
        java_command=[str(jdk/'java'),'-XX:ActiveProcessorCount=1','-XX:+UseSerialGC','-Xms64m','-Xmx64m','-cp',str(directory),'nbody',str(NBODY_STEPS)]
        campaign['java']={'runtime_binary_sha256':file_digest(jdk/'java'),'compiler_binary_sha256':file_digest(jdk/'javac'),
            'class_files_sha256':{p.name:file_digest(p) for p in sorted(directory.glob('*.class'))},'command':java_command,
            'version':(output/'raw/prepare/java-version/stderr.txt').read_text()}
        records['jvm','jvm']['revision']=campaign['java']['version'].splitlines()[0]
        # Full independent FASTA verification lives in its own process, outside Mech's memory high-water mark.
        if args.fasta.stat().st_size!=254_166_745:raise ValueError('FASTA input must be the complete N=25,000,000 fixture')
        required_command(['clang','-O3',ROOT/'suite/controls/knucleotide_oracle.c','-o',output/'raw/prepare/knucleotide-oracle'],output/'raw/prepare/knucleotide-oracle-build',args.timeout)
        required_command([output/'raw/prepare/knucleotide-oracle'],output/'raw/prepare/knucleotide-oracle-run',args.timeout,stdin_path=args.fasta)
        expected_kn=(ROOT/'suite/applications/knucleotide-25000000.expected').read_bytes()
        if raw(output/'raw/prepare/knucleotide-oracle-run')!=expected_kn:raise ValueError('full FASTA differs from the independent/historical output contract')
        campaign['fasta']={'n':FASTA_N,'bytes':args.fasta.stat().st_size,'sha256':file_digest(args.fasta),'generator_source_sha256':file_digest(ROOT/'suite/applications/fasta.c')}
        # Java is both an independent numerical oracle and a separately labelled cross-runtime control.
        required_command(java_command,output/'raw/oracle/nbody-full',args.timeout)
        expected_nbody=nbody_output(raw(output/'raw/oracle/nbody-full'))
        if not math.isclose(expected_nbody[0],-0.169075164,abs_tol=1e-9) or not math.isclose(expected_nbody[1],-0.169059907,abs_tol=1e-8):raise ValueError('independent full N-body result differs from preserved energies')
        persist()
        env=dict(os.environ,MECH_SEQUENCE_PARTITIONS='4',MECH_SEQUENCE_STD_MAP='1',MECH_SEQUENCE_NARROW='1',MECH_SEQUENCE_ASYNC='0')
        jobs=[('knucleotide','source-native',[apps['applications']['mech-application']['binary'],str(ROOT/'suite/applications/knucleotide.mec'),'jit'],args.fasta,env),
              ('nbody','fused-native',[apps['applications']['mech-numerical-application']['binary'],str(NBODY_STEPS),str(ROOT/'suite/applications/nbody.mec'),'jit-simd'],None,None),
              ('jvm','jvm',java_command,None,None)]
        for id,backend,command,stdin,environment_ in jobs:
            record=records[id,backend]
            for fork in [None,*range(args.forks)]:
                label='verify' if fork is None else f'fork-{fork+1}'
                print(f'{id} / {backend} / {label} / full workload',flush=True)
                d=output/'raw'/id/backend/label
                result=required_command(command,d,args.timeout,stdin_path=stdin,env=environment_)
                observed=raw(d)
                if id=='knucleotide':
                    if observed!=expected_kn:raise ValueError('full Mech K-nucleotide output differs from independent oracle')
                    endpoint={'kind':'text','value':observed.decode()}
                else:endpoint=validate_nbody(observed,expected_nbody)
                accept(record,fork,d,{'native_process_seconds':result['seconds']},endpoint)
        # Build corpus inputs and independent expected streams with pinned controls.
        fixtures=[]
        for case in deflate_cases(args.corpus):
            d=output/'raw/deflate-inputs'/case['name'];d.mkdir(parents=True)
            for name in ('input','prefix'):(d/name).write_bytes(case[name])
            capacity=len(case['prefix'])+len(case['input'])+5*max(1,(len(case['input'])+4999)//5000)
            expected=case['expected']
            for backend in ('roc','libdeflate'):
                id='deflate' if case['name']=='full-reymont' else 'deflate-'+case['name'];record=records[id,backend]
                command=[controls[backend]['binary'],str(d/'input'),str(d/'prefix'),str(capacity)]
                for fork in [None,*range(args.forks)]:
                    label='verify' if fork is None else f'fork-{fork+1}'
                    out=output/'raw'/id/backend/label
                    print(f'{id} / {backend} / {label}',flush=True)
                    response=required_command(command,out,args.timeout)
                    compressed=raw(out)
                    validation=validate_deflate(compressed,case['input'],case['prefix'],expected if backend=='roc' else None)
                    detail=json.loads((out/'stderr.txt').read_text().splitlines()[-1])
                    if detail.get('aliases_preserved') is not True:raise ValueError('control failed held-alias obligations')
                    if backend=='roc' and expected is None:expected=compressed
                    endpoint={'kind':'deflate','sha256':hashlib.sha256(compressed).hexdigest(),**validation}
                    accept(record,fork,out,{'control_call_seconds':detail['control_call_seconds'],'native_process_seconds':response['seconds'],'input_bytes':len(case['input']),'output_bytes':len(compressed)},endpoint)
            (d/'expected').write_bytes(expected)
            fixtures.append({'name':case['name'],'input':str(d/'input'),'prefix':str(d/'prefix'),'expected':str(d/'expected')})
        save(output/'fixtures/deflate-inputs.json',[{**f,**{k+'_sha256':file_digest(f[k]) for k in ('input','prefix','expected')}} for f in fixtures])
        # One source compilation per independent worker fork, covering every complete input.
        # The timed boundary is one stateless checked call; compilation and import stay outside it.
        for form in ('source','bytecode'):
            for fork in [None,*range(args.forks)]:
                label='verify' if fork is None else f'fork-{fork+1}'
                print(f'Deflate complete corpus / {form} / {label}',flush=True)
                d=output/'raw/deflate-jit'/form/label
                request={'protocol':1,'action':'application_jit','backend':form,'source':(ROOT/'suite/applications/deflate.mec').read_text(),
                    'schedule':[[]],'output':'result','application_cases':fixtures,'warmup':0 if fork is None else 1,
                    'compile_limits':json.loads((ROOT/'suite/applications/deflate-compiler-policy.json').read_text()),
                    'launch_policy':json.loads((ROOT/'suite/applications/deflate-launch-policy.json').read_text())}
                response=invoke([worker['binary']],request,d,args.timeout)
                if response.get('outcome')!='ok':raise ValueError(f'Deflate JIT failed: {response.get("error")}')
                if [r['name'] for r in response['application_results']]!=[f['name'] for f in fixtures]:raise ValueError('worker omitted or reordered corpus inputs')
                for f,result in zip(fixtures,response['application_results']):
                    id='deflate' if f['name']=='full-reymont' else 'deflate-'+f['name']
                    backend='program-jit' if form=='source' else 'program-jit-bytecode'
                    record=records[id,backend]
                    compressed=bytes.fromhex(result['raw_hex'])
                    validation=validate_deflate(compressed,Path(f['input']).read_bytes(),Path(f['prefix']).read_bytes(),Path(f['expected']).read_bytes())
                    if result.get('aliases_preserved') is not True or result['metrics']['managed_after_drop_bytes']!=0:raise ValueError('native program ownership obligations failed')
                    metrics={**result['metrics'],**response['metrics']}
                    endpoint={'kind':'deflate','sha256':hashlib.sha256(compressed).hexdigest(),**validation}
                    detail=d/'cases'/f['name'];detail.mkdir(parents=True)
                    accept(record,fork,detail,metrics,endpoint,{'parent_observation':{'path':(d/'stdout.json').relative_to(output).as_posix(),'sha256':file_digest(d/'stdout.json'),'case':f['name']}})
        for record in campaign['results']:
            if record['outcome']=='ok' and len(record['samples'])==args.forks:record.update(progress='measured',summary=summarize(record['samples']))
            else:record['summary']={}
        campaign.update(complete=True,outcome='ok' if all(r['progress']=='measured' for r in campaign['results']) else 'failed',finished_at=datetime.now(timezone.utc).isoformat())
        persist()
        lines=['# Full application campaign','',f'Outcome: {campaign["outcome"]}. Independent process forks: {args.forks}.',
            '', 'K-nucleotide consumes FASTA N=25,000,000. N-body and the JVM control each execute 50,000,000 steps. Deflate covers every maintained small stream, both boundary inputs and the entire 6,627,202-byte corpus in source and decoded forms.',
            '', 'Deflate calls preserve held input/prefix snapshots, publish a separately owned complete stream, and release all managed storage. Python zlib checks exact decompression, EOF and absence of trailing data. Mech and Roc match the pinned level-12 stream; libdeflate has its own valid stream.',
            '', 'Each Deflate fork compiles the complete program once, then invokes all corpus inputs. Compilation, input snapshot import, warmup and returned-output destruction are excluded from the call timer. The complete fork process is retained separately in raw supervision. Roc/libdeflate have different transport and allocation contracts; these observations do not establish an automatic cross-runtime speed ratio.',
            '', '| Case | Backend | Median primary seconds |','| --- | --- | ---: |']
        for r in campaign['results']:
            m=r.get('summary',{}).get(r['measurement']['primary_metric'],{}).get('median')
            lines.append(f'| {r["case_id"]} | {r["backend"]} | {m if m is not None else r["outcome"]} |')
        (output/'report.md').write_text('\n'.join(lines)+'\n');seal_evidence(output);archive_evidence(output)
        print(output/'report.md',flush=True)
    return 0 if campaign['outcome']=='ok' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('worker','application-worker','controls','java','fasta','corpus','output'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--forks',type=int,default=3);p.add_argument('--timeout',type=float,default=1800)
    args=p.parse_args()
    if args.forks<1 or args.timeout<=0:p.error('positive forks and deadline required')
    try:sys.exit(run(args))
    except (OSError,ValueError) as error:
        # Failed qualifications retain all completed samples and raw failures, with no partial summary accepted.
        path=args.output.resolve()/'campaign.json'
        if path.exists():
            campaign=json.loads(path.read_text())
            if not campaign.get('complete'):
                for record in campaign['results']:
                    if record.get('outcome')=='ok' and len(record['samples'])==args.forks:
                        record.update(progress='measured',summary=summarize(record['samples']))
                    else:
                        record.update(outcome='error',reason=str(error),summary={})
                campaign.update(complete=True,outcome='failed',error=str(error),finished_at=datetime.now(timezone.utc).isoformat())
                save(path,campaign)
                (path.parent/'report.md').write_text('# Full application qualification failed\n\n'+str(error)+'\n')
                seal_evidence(path.parent);archive_evidence(path.parent)
        p.exit(1,f'Application campaign error: {error}\n')
