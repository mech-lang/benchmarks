#!/usr/bin/env python3
"""Qualify and measure source-to-linked-scalar native builds and full program lifecycles."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import sys
import time

from benchmark_suite import (ROOT, SCHEMA, campaign_lock, digest, environment, equal, execute,
    file_digest, invoke, load_catalog, save, summarize, worker_provenance, preserve_worker, seal_evidence, archive_evidence)


def parse_sections(output, system):
    if system!='Darwin':
        return {name:int(size) for name,size in re.findall(r'^\s*(\.\S+)\s+(\d+)\s+',output,re.M)} or None
    result={}
    segment=''
    for line in output.splitlines():
        heading=re.match(r'Segment\s+(.*?):\s*\d+',line)
        if heading:segment=heading[1]
        explicit=re.search(r'Section\s+\(([^,]+),\s*([^)]+)\):\s*(\d+)',line)
        simple=re.search(r'Section\s+(\S+):\s*(\d+)',line)
        if explicit:result[explicit[1]+'/'+explicit[2]]=int(explicit[3])
        elif simple:result[segment+'/'+simple[1]]=int(simple[2])
    return result or None


def sections(path, directory, timeout):
    command = ['size', '-m' if sys.platform == 'darwin' else '-A', str(path)]
    result = execute(command, directory, timeout)
    if result['outcome'] != 'ok':
        return None
    output = (directory / 'stdout.txt').read_text()
    return parse_sections(output,platform.system())


def text_size(section_sizes):
    if not section_sizes:
        return None
    names = [key for key in section_sizes if key.rsplit('/',1)[-1] in ('__text','.text') or key.startswith('.text.')]
    return sum(section_sizes[key] for key in names) if names else None


def build_and_run(worker, case, directory, target, timeout):
    directory.mkdir(parents=True)
    source = (ROOT / case['source']).read_text()
    started = time.perf_counter()
    generated = invoke([worker['binary']], {'protocol':1,'action':'native_generate','source':source,
        'workspace':worker['source_checkout'],'schedule':case['measurement']['schedule'],
        'native_directory':str(directory/'project')}, directory/'generate', timeout)
    if generated.get('outcome') != 'ok':
        return {'outcome':generated.get('outcome','error'),'reason':generated.get('error','native generation failed')}
    project = directory/'project'
    env = dict(os.environ, RUSTC_BOOTSTRAP='1')
    lock = execute(['cargo','generate-lockfile','--offline','--manifest-path',str(project/'Cargo.toml')],
                   directory/'lock',timeout,env)
    if lock['outcome'] != 'ok':
        return {'outcome':lock['outcome'],'reason':'generated-project dependency resolution failed'}
    built = execute(['cargo','build','--release','--offline','--locked','--message-format=json',
                     '--features','mech-engine/pure_text',
                     '--manifest-path',str(project/'Cargo.toml'),'--target-dir',str(target)],
                    directory/'build',timeout,env)
    source_to_executable = time.perf_counter()-started
    if built['outcome'] != 'ok':
        return {'outcome':built['outcome'],'reason':'native support build/link failed; inspect build/stderr.txt'}
    messages = []
    for line in (directory/'build/stdout.txt').read_text().splitlines():
        try:
            message=json.loads(line)
        except ValueError:
            continue
        if message.get('reason')=='compiler-artifact' and message.get('executable'):
            messages.append(message)
    if len(messages)!=1:
        return {'outcome':'error','reason':'build did not identify exactly one executable'}
    binary=Path(messages[0]['executable'])
    names=generated['output_names']
    if names!=['result']:
        return {'outcome':'incorrect','reason':'native result output identity ambiguous'}
    result_index=names.index('result')
    oracle=invoke([sys.executable,str(ROOT/'tools/suite_oracle.py')],{'case':case,'count':len(case['measurement']['schedule'])},directory/'oracle',timeout)
    if oracle.get('outcome')!='ok':
        return {'outcome':'error','reason':'independent native oracle failed'}
    process_times=[]
    observations=[]
    for index,frame in enumerate(case['measurement']['schedule']):
        if len(frame)!=1:
            return {'outcome':'error','reason':'scalar native recipe requires one f64 input'}
        argument='f64:'+struct.pack('>d',frame[0]).hex()
        run=execute([str(binary),'--budget=17179869184','--',argument],directory/f'program-{index+1}',timeout)
        if run['outcome']!='ok':
            return {'outcome':run['outcome'],'reason':'linked native program failed'}
        lines=(directory/f'program-{index+1}'/'stdout.txt').read_text().splitlines()
        try:
            # Validate every output, including the exact declared result position.
            if len(lines)!=len(names) or any(not re.fullmatch(r'f64:[0-9a-f]{16}',line) for line in lines):
                raise ValueError('unexpected native output type/count')
            values=[struct.unpack('>d',bytes.fromhex(line[4:]))[0] for line in lines]
        except (ValueError,struct.error) as error:
            return {'outcome':'incorrect','reason':str(error)}
        observed={'kind':'scalar','value':values[result_index]}
        if not equal(observed,oracle['outputs'][index],case['task']):
            return {'outcome':'incorrect','reason':'linked program disagrees with independent oracle'}
        process_times.append(run['seconds'])
        observations.append(observed)
    objects=list(project.glob('*.o'))
    if len(objects)!=1:
        return {'outcome':'error','reason':'expected exactly one emitted object'}
    obj=objects[0]
    object_sections=sections(obj,directory/'object-sections',timeout)
    linked_sections=sections(binary,directory/'linked-sections',timeout)
    metrics={'source_to_executable_seconds':source_to_executable,
             'source_to_artifact_seconds':generated['source_to_artifact_seconds'],
             'native_generation_seconds':generated['native_generation_seconds'],
             'support_build_link_seconds':built['seconds'],'native_process_seconds':sum(process_times)/len(process_times),
             'object_bytes':obj.stat().st_size,'executable_bytes':binary.stat().st_size}
    for name,value in [('object_text_bytes',text_size(object_sections)),('linked_text_bytes',text_size(linked_sections))]:
        if value is not None:metrics[name]=value
    receipt={'outcome':'ok','metrics':metrics,'outputs':observations,'process_samples':process_times,
        'object_sha256':file_digest(obj),'executable_sha256':file_digest(binary),'lock_sha256':file_digest(project/'Cargo.lock'),
        'object_sections':object_sections,'linked_sections':linked_sections,'generator_metadata':generated['metadata'],
        'stripping_policy':'generated canonical application release profile: strip=symbols',
        'native_boundary':'public checked scalar linked application; startup, metadata admission, invocation, output, shutdown',
        'build_memory':'not measured; no compiler-tree RSS claim'}
    save(directory/'receipt.json',receipt)
    return receipt


def run(args):
    worker=worker_provenance(args.worker)
    if not worker.get('native_generation'):
        raise ValueError('worker must be built with --native')
    catalog=load_catalog()
    case=next(c for c in catalog['cases'] if c['id']=='native-build')
    output=args.output.resolve()
    if output.exists():raise ValueError('choose a new output directory; existing evidence is immutable')
    host=environment()
    measurement={**case['measurement'],'cache':'runtime/support dependencies warmed by untimed qualification; new generated project per fork',
                 'stripping_policy':'generated release profile strip=symbols','native_route':'checked scalar linked application',
                 'memory_budget_bytes':1 << 34,'native_limits':'checked scalar launcher defaults',
                 'support_features':['mech-engine/pure_text'],
                 'support_feature_reason':'pinned engine native scalar metadata requires program_image_proofs, exposed through pure_text',
                 'support_build_environment':{key:os.environ[key] for key in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS') if key in os.environ},
                 'timing':'source compiler worker start through dependency resolution, support build and link; separately complete native process for every input'}
    record={'case_id':case['id'],'title':case['title'],'family':case['family'],'backend':'native','lane':'candidate',
            'revision':worker['revision'],'progress':'implemented','capability':'unknown','outcome':'pending',
            'feature_profile':{'profile':worker['feature_profile'],'native_generation':True},
            'task':case['task'],'measurement':measurement,'task_hash':digest(case['task']),
            'measurement_hash':digest(measurement),'source_sha256':file_digest(ROOT/case['source']),
            'source':(ROOT/case['source']).read_text(),'environment_hash':digest(host),'samples':[]}
    campaign={'schema':SCHEMA,'id':output.name,'started_at':datetime.now(timezone.utc).isoformat(),'profile':'native',
              'environment':host,'environment_hash':digest(host),'workers':{'candidate':worker},
              'performance_gate':False,'results':[record],'order':[],'comparisons':[],'complete':False,
              'harness_sha256':file_digest(__file__),'experiment':args.experiment}
    target=ROOT/'.local/native-target'/worker['revision']
    with campaign_lock(ROOT/'.local'):
        output.mkdir(parents=True)
        preserve_worker(worker,output/'workers/candidate')
        save(output/'campaign.json',campaign)
        print('Qualify native object, linked executable and complete output trajectory',flush=True)
        verified=build_and_run(worker,case,output/'raw/verify',target,args.timeout)
        save(output/'raw/verify/supervised.json',verified)
        record['verification']={'outcome':verified['outcome'],'reason':verified.get('reason'),
                                'outputs':verified.get('outputs'),'raw':'raw/verify'}
        if verified['outcome']=='ok':
            record.update(progress='verified',capability='supported',outcome='ok')
            for fork in range(args.forks):
                print(f'Native build and complete-process observations / fork {fork+1}',flush=True)
                if file_digest(worker['binary'])!=worker['binary_sha256']:raise ValueError('worker binary changed')
                raw=f'raw/fork-{fork+1}'
                result=build_and_run(worker,case,output/raw,target,args.timeout)
                save(output/raw/'supervised.json',result)
                if result['outcome']!='ok':
                    record.update(outcome=result['outcome'],reason=result.get('reason'),failed_observation=raw)
                    break
                record['samples'].append({'fork':fork,'raw':raw,'metrics':result['metrics'],
                    'object_sha256':result['object_sha256'],'executable_sha256':result['executable_sha256'],
                    'lock_sha256':result['lock_sha256'],'process_samples':result['process_samples']})
                campaign['order'].append({'case_id':case['id'],'backend':'native','lane':'candidate','fork':fork})
                save(output/'campaign.json',campaign)
            if record['outcome']=='ok':
                record.update(progress='measured',summary=summarize(record['samples']))
        else:record.update(outcome=verified['outcome'],reason=verified.get('reason'),summary={})
        if record['outcome']!='ok':record['summary']={}
        campaign.update(complete=True,outcome='ok' if record['outcome']=='ok' else 'failed',finished_at=datetime.now(timezone.utc).isoformat())
        save(output/'campaign.json',campaign)
        lines=['# Mech native build and footprint campaign','',
            'Ordinary source → canonical ProgramArtifact → checked scalar Cranelift object → linked application. '
            'All scheduled inputs and the explicitly named result are checked against an independent Python oracle.','',
            'Runtime/support dependencies are warmed by the separate qualification build. Each measured fork creates a new project. '
            'Source-to-executable includes worker startup, source compilation, lowering/codegen, dependency lock resolution, support generation/build and final link. '
            'Complete-process time includes startup, admission, invocation, complete output and shutdown.','',
            f"Outcome: {record['outcome']}. Experiment: {args.experiment}.",'',
            '| Measurement | Median |','| --- | ---: |']
        for name,summary in record.get('summary',{}).items():lines.append(f"| {name} | {summary['median']:.9g} |")
        lines+=['','Release stripping policy: symbols stripped by the generated application profile. '
                'Exact object/executable hashes, code-section reports, compiler logs, generated input pins and raw process samples are retained. '
                'Compiler-process-tree memory is not measured. These scalar measurements make no general hosted-application or resident-turn claim.','']
        (output/'report.md').write_text('\n'.join(lines))
        seal_evidence(output)
        archive_evidence(output)
        print(f"Native campaign {campaign['outcome']}: {output/'report.md'}",flush=True)
    return 0 if campaign['outcome']=='ok' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--forks',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=1200)
    parser.add_argument('--experiment',choices=('compiler_acceleration','code_generation'),default='code_generation')
    args=parser.parse_args()
    if args.forks<1 or args.timeout<=0:parser.error('forks and timeout must be positive')
    try:sys.exit(run(args))
    except (ValueError,OSError) as error:parser.exit(2,f'Native campaign error: {error}\n')
