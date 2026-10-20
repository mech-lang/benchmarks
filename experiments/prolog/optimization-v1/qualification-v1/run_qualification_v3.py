"""Pinned SWI spectral source compilation and bounded qualification; no timing mode."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
from native_process import atom,now,one,sha,success

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PACKET=HERE.parent
PLAN=HERE/'execution-plan-v3.json'
LOCK='/tmp/mech-clbg-timing.lock'
CORPUS=ROOT/'experiments/shared/bounded-corpus-v1/cases'
CONFIG=ROOT/'archive/languages/prolog/20261013/runtime-qualified/success-halt-v1/runtime-config.json'
PREPARE=ROOT/'archive/languages/prolog/20261013/revisions/prepare-success-halt-v1/tools/prepare_qlf.pl'
READER=ROOT/'archive/validation/loc-normalization/20261013/prolog-proposal-v5/scan_source.pl'
COUNTER=READER.with_name('foreign_prolog.py')
FLAGS=['-q','-O','-f','none','--stack-limit=8g']
NAMES=['parent','serial-specialized','blocks8-specialized']
MODULES=['clbg_spectralnorm','clbg_spectralnorm_serial','clbg_spectralnorm_blocks8']
SOURCE_HASHES=['1d868f9e772820b1b2e7a3c68e82f142b6704357f6fa1249ef3e828e78c02fda','cdd1303c005ba0743ae60778f4ac4004b12f5acb9c727535e870c184345c5fef','bc2223d1fa22aed05a7ea4da9904a88a701c6d0972749ced5f0e106fc9685ba5']
SUPPORT=PACKET/'source-v1/support/clbg_io.pl'
SUPPORT_SHA='bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3'


def require(condition,message):
    if not condition:raise ValueError(message)


def load(path):return json.loads(Path(path).read_text())


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def check_ref(value):
    p=ROOT/value['path'];require(p.is_file() and sha(p)==value['sha256'],'Changed pinned file: '+value['path']);return p


def verify(plan):
    require(plan['schema']=='prolog-spectral-bounded-execution-plan.v1' and plan['status']=='PREPARED-NO-EXECUTION','Unexpected plan')
    require(plan['controller']==ref(__file__) and plan['process_helper']==ref(HERE/'native_process.py'),'Qualification controller changed')
    for path,digest in plan['pins'].items():check_ref(dict(path=path,sha256=digest))
    return plan


def prepare(runtime_path):
    require(not PLAN.exists() and not (HERE/'build-v3').exists() and not (HERE/'runtime-v3').exists(),'Fresh qualification packet required')
    runtime_path=runtime_path.resolve();runtime=load(runtime_path)
    require(runtime['schema']=='prolog-spectral-runtime-restoration.v1' and runtime['status']=='PASSED'
        and runtime['whole_tree_exact'] is True and runtime['historical_file_count']==2799
        and runtime['owned_mount_detached'] is True,'Exact closed restoration required')
    require(runtime['binary']['sha256']=='554814b1da7c0c30595adafb758145e42a6134c696b47c8870d359008246443e','Wrong runtime')
    require(runtime['historical_config']==ref(CONFIG),'Historical configuration changed')
    for path,digest in runtime['pins'].items():check_ref(dict(path=path,sha256=digest))
    durable=HERE/'runtime-v3';durable.mkdir()
    shutil.copyfile(runtime_path,durable/'restoration-report.json')
    shutil.copytree(runtime_path.parent/'commands',durable/'commands')
    relocations={}
    for path in sorted((durable/'commands').rglob('*')):
        if path.is_file():relocations[str(runtime_path.parent/'commands'/path.relative_to(durable/'commands'))]=ref(path)
    manifest=dict(schema='prolog-spectral-restoration-artifacts.v1',report=ref(durable/'restoration-report.json'),
        original_recorded_report=str(runtime_path),durable_exact_copies=relocations,
        runtime_binaries='Local ignored restoration;2799 pins and official archive recipe retained, not falsely claimed archived bytes.')
    atom(durable/'artifacts.json',manifest)
    pins=dict(runtime['pins'])
    static=[Path(__file__),HERE/'native_process.py',HERE/'state_probe.pl',HERE/'runtime_probe.pl',
        HERE/'restore_runtime.py',HERE/'restore_runtime_v2.py',HERE/'restore-launch-v1.json',PREPARE,READER,COUNTER,
        CONFIG,PACKET/'plan.json',PACKET/'source-ownership-proposed.json',CORPUS/'manifest.json',durable/'restoration-report.json',durable/'artifacts.json']
    static.extend(p for p in (durable/'commands').rglob('*') if p.is_file())
    static.extend([HERE/'run_qualification_v2.py',HERE/'execution-plan-v2.json',HERE/'build-native-v2/report.json'])
    static.extend(p for p in (HERE/'build-native-v2').rglob('*') if p.is_file())
    static.extend([HERE/'run_qualification.py',HERE/'execution-plan.json',HERE/'build-native-v1/report.json'])
    static.extend(p for p in (HERE/'build-native-v1/runtime-probe').iterdir() if p.is_file())
    require(sha(READER)=='b48e07039914d448e4f313235f347f4604269d0a9802896f0d019ed3e7c52021'
        and sha(COUNTER)=='6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8','Retained reader/counter changed')
    corpus=load(CORPUS/'manifest.json');cases=sorted([x for x in corpus['cases'] if x['benchmark']=='spectralnorm'],key=lambda x:x['n'])
    require([x['n'] for x in cases]==[1,2,3,5,9,10,100],'Shared case inventory differs')
    for case in cases:
        for field in ['stdin','expected']:
            value=case[field];p=CORPUS/value['path'];require(sha(p)==value['sha256'] and p.stat().st_size==value['bytes'],'Corpus bytes differ');static.append(p)
    programs={}
    for name,module,expected_sha in zip(NAMES,MODULES,SOURCE_HASHES):
        original=PACKET/'source-v1/sources/spectralnorm'/(name+'.pl')
        require(sha(original)==expected_sha and sha(SUPPORT)==SUPPORT_SHA,'Exact proposed source differs')
        build=HERE/'build-v3'/name;source=build/'input/sources/spectralnorm'/(name+'.pl');source.parent.mkdir(parents=True)
        support=build/'input/support/clbg_io.pl';support.parent.mkdir(parents=True)
        shutil.copyfile(original,source);shutil.copyfile(SUPPORT,support)
        for p in [original,source,SUPPORT,support]:static.append(p)
        command=[str(ROOT/runtime['binary']['path'])]+FLAGS
        programs[name]=dict(source=ref(original),compiled_source=ref(source),support=ref(support),module=module,
            source_qlf=str(source.with_suffix('.qlf')),support_qlf=str(support.with_suffix('.qlf')),
            run_argv=command+['-l',str(support.with_suffix('.qlf')),'-s',str(source.with_suffix('.qlf')),'-g','clbg_io:run('+module+':main)','--'])
    for p in static:pins[str(p.relative_to(ROOT))]=sha(p)
    plan=dict(schema='prolog-spectral-bounded-execution-plan.v1',status='PREPARED-NO-EXECUTION',
        controller=ref(__file__),process_helper=ref(HERE/'native_process.py'),runtime=ref(durable/'restoration-report.json'),
        restoration_artifacts=ref(durable/'artifacts.json'),binary=runtime['binary'],environment=runtime['environment'],
        flags=FLAGS,pins=pins,programs=programs,bounded=cases,additional_n=[0,7,8,15,16,17],
        expected_state_vector_comparisons=144,expected_geometry_cases=12,expected_work_cases=6,
        required_work=load(PACKET/'plan.json')['required_work'],common_mutex=LOCK,
        quantitative_benchmarks_authorized=False,chart_admission=False,
        native_count_policy='Unchanged retained V5 counter only; unresolved library/goal-list ownership leaves normalized count null. No guessed certified count.')
    atom(PLAN,plan);print(json.dumps(dict(status='PREPARED',plan=ref(PLAN),pin_count=len(pins))))


def native(plan,command,directory,lock,environment=None,timeout=120):
    return one(command,directory,environment or plan['environment'],ROOT,lock.fileno(),timeout)


def compiler_stderr(row,module):
    raw=Path(row['stderr']['path']).read_bytes()
    expected=('Warning: [Thread main] Local definition of clbg_prepare:main/0 overrides weak import from '+module+'\n').encode()
    require(raw in (b'',expected),'Unexpected compiler stderr retained; qualification stopped')
    row['stderr_classification']='empty' if not raw else 'retained-helper-main-export-warning-exact'


def runtime_ok(metadata,plan):
    runtime=metadata['runtime'];require(runtime['version_components']==[10,0,2] and runtime['gc'] is True and runtime['bounded'] is False
        and runtime['home']==plan['environment']['SWI_HOME_DIR'] and runtime['stack_limit']==8589934592,'Compiler runtime flags differ')


def build(plan,lock):
    output=HERE/'build-native-v3';require(not output.exists(),'Fresh build attempt required');output.mkdir()
    report=dict(schema='prolog-spectral-native-builds.v1',status='RUNNING',plan=ref(PLAN),controller=ref(__file__),
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,started_utc=now(),programs={},attempts=[],active=None,quantitative_benchmark=False)
    atom(output/'report.json',report)
    try:
        binary=str(ROOT/plan['binary']['path']);base=[binary]+FLAGS
        env=dict(plan['environment'],DYLD_PRINT_LIBRARIES='1')
        row=native(plan,base+['-l',str(HERE/'runtime_probe.pl'),'-g','prolog_spectral_runtime_probe:main','--'],output/'runtime-probe',lock,env)
        report['attempts'].append(row);success(row)
        identity=load(output/'runtime-probe/stdout.bin')
        require(identity['version']==[10,0,2] and identity['gc'] is True and identity['bounded'] is False
            and identity['threads'] is True and identity['stack_limit']==8589934592 and identity['home']==plan['environment']['SWI_HOME_DIR'],'Runtime identity differs')
        dyld=(output/'runtime-probe/stderr.bin').read_text()
        images=[match.group(1) for line in dyld.splitlines() if (match:=re.match(r'^dyld\[\d+\]: <[A-F0-9-]+> (/.+)$',line))]
        app=(ROOT/plan['binary']['path']).parents[2]
        require(images and all(p.startswith(('/usr/lib/','/System/Library/',str(app)+'/')) for p in images),'Unresolved nonprivate loaded image')
        report['runtime_identity']=identity;report['loaded_native_images']=images
        for name in NAMES:
            verify(plan);p=plan['programs'][name];build_root=HERE/'build-v3'/name;records=[]
            for label,source in [('support',ROOT/p['support']['path']),('application',ROOT/p['compiled_source']['path'])]:
                receipt=output/name/(label+'-compile.json');wam=receipt.with_suffix('.wam');receipt.parent.mkdir(parents=True,exist_ok=True)
                report['active']=dict(program=name,phase=label);atom(output/'report.json',report)
                row=native(plan,base+['-l',str(PREPARE),'-g','clbg_prepare:main','--','compile',str(source),str(receipt),str(wam),str(build_root/'input')],output/name/(label+'-process'),lock)
                report['attempts'].append(row);success(row);compiler_stderr(row,p['module'])
                metadata=load(receipt);runtime_ok(metadata,plan)
                for loaded in metadata['loaded_sources']:
                    q=Path(loaded);require(q.is_relative_to(app) or q.is_relative_to(build_root/'input') or q==PREPARE,'Unexpected compiler source root: '+loaded)
                records.append(dict(process=ref(output/name/(label+'-process/process.json')),metadata=ref(receipt),wam=ref(wam)))
            receipt=output/name/'inspect.json';wam=output/name/'inspect.wam'
            row=native(plan,base+['-l',str(PREPARE),'-g','clbg_prepare:main','--','inspect',p['source_qlf'],str(receipt),str(wam),str(build_root/'input')],output/name/'inspect-process',lock)
            report['attempts'].append(row);success(row);compiler_stderr(row,p['module']);runtime_ok(load(receipt),plan)
            require(sha(ROOT/p['source']['path'])==sha(ROOT/p['compiled_source']['path']),'Compiled original byte identity differs')
            report['programs'][name]=dict(**p,source_qlf_pin=ref(p['source_qlf']),support_qlf_pin=ref(p['support_qlf']),compilations=records,
                inspect=dict(process=ref(output/name/'inspect-process/process.json'),metadata=ref(receipt),wam=ref(wam)))
            report['active']=None;atom(output/'report.json',report)
        verify(plan);report.update(status='PASSED',finished_utc=now())
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)
    print(json.dumps(dict(status='PASSED-BUILD',report=ref(output/'report.json'))))


def count_sources(plan,output,lock):
    spec=importlib.util.spec_from_file_location('retained_prolog_v5',COUNTER);counter=importlib.util.module_from_spec(spec);spec.loader.exec_module(counter)
    paths={name:ROOT/plan['programs'][name]['source']['path'] for name in NAMES};paths['support']=SUPPORT
    packets={};rows={};binary=str(ROOT/plan['binary']['path'])
    for name,path in paths.items():
        directory=output/('reader-'+name)
        row=native(plan,[binary,'-q','-f','none','-l',str(READER),'-g','prolog_source_scan_v1:main','--',str(path)],directory,lock)
        success(row);require(row['stderr']['bytes']==0,'Reader warning retained');packet=load(directory/'stdout.bin')
        require(packet['source']==str(path) and packet['source_text']==path.read_text() and packet['version']==[10,0,2],'Native reader source binding differs')
        packets[name]=packet;rows[name]=dict(process=ref(directory/'process.json'),source=ref(path))
    for name in NAMES:
        context=counter.BundleContext([packets[name],packets['support']])
        projection=counter.count_prolog(paths[name].read_bytes(),packets[name],language='prolog',context=context)
        atom(output/('owners-'+name+'.json'),projection)
        rows[name].update(projection=ref(output/('owners-'+name+'.json')),normalized_loc=projection['normalized_loc'],physical_loc=projection['physical_loc'],diagnostics=projection['diagnostics'])
    require(rows['parent']['normalized_loc']==96 and rows['serial-specialized']['normalized_loc']==114,'Parent/serial native owner replay differs')
    # The unchanged counter is intentionally not extended to guess library/constructed goal-flow ownership.
    return dict(schema='prolog-spectral-native-source-counts.v1',status='PARTIAL-RETAINED-POLICY-REPLAY',rows=rows,
        independent_review_approved=False,parallel_certified=rows['blocks8-specialized']['normalized_loc'] is not None)


def bounded(plan,lock):
    builds=load(HERE/'build-native-v1/report.json');require(builds['status']=='PASSED' and builds['plan']==ref(PLAN),'Matching complete builds required')
    for p in builds['programs'].values():check_ref(p['source_qlf_pin']);check_ref(p['support_qlf_pin'])
    output=HERE/'bounded-v3';require(not output.exists(),'Fresh bounded attempt required');output.mkdir()
    report=dict(schema='prolog-spectral-bounded-qualification.v1',status='RUNNING',plan=ref(PLAN),builds=ref(HERE/'build-native-v1/report.json'),
        common_mutex_inode=os.fstat(lock.fileno()).st_ino,started_utc=now(),cases=[],active=None,quantitative_benchmark=False,chart_admission=False)
    atom(output/'report.json',report)
    try:
        expectations={case['n']:(CORPUS/case['expected']['path']).read_bytes() for case in plan['bounded']}
        for n in sorted(set(expectations)|set(plan['additional_n'])):
            parent_bytes=None
            for name in NAMES:
                p=plan['programs'][name];report['active']=dict(source=name,n=n);atom(output/'report.json',report)
                directory=output/('n-'+str(n)+'-'+name);row=native(plan,p['run_argv']+[str(n)],directory,lock)
                report['cases'].append(dict(source=name,n=n,process=row));atom(output/'report.json',report);success(row)
                raw=(directory/'stdout.bin').read_bytes();require(row['stderr']['bytes']==0,'Bounded stderr retained; qualification stopped')
                if name=='parent':parent_bytes=raw
                expected=expectations.get(n,parent_bytes)
                require(raw==expected,'Bounded complete output differs: '+name+' N='+str(n))
                require(re.fullmatch(rb'[0-9]+\.[0-9]{9}\n',raw) is not None,'Malformed norm output')
                report['cases'][-1]['exact_output_valid']=True;report['cases'][-1]['shared_reference']=n in expectations
                print(json.dumps(dict(source=name,n=n,status='PASS')),flush=True)
        qlfs=[plan['programs'][name]['source_qlf'] for name in NAMES]
        directory=output/'state-work-probe';row=native(plan,[str(ROOT/plan['binary']['path'])]+FLAGS+['-l',str(HERE/'state_probe.pl'),'-g','prolog_spectral_state_probe:main','--']+qlfs,directory,lock,timeout=180)
        report['state_work_process']=row;atom(output/'report.json',report);success(row);require(row['stderr']['bytes']==0,'State probe warning retained')
        state=load(directory/'stdout.bin')
        require(state['status']=='PASSED' and len(state['vectors'])==144 and len(state['geometry'])==12 and len(state['work'])==6,'State probe inventory differs')
        report['state_work']=ref(directory/'stdout.bin')
        counts=count_sources(plan,output,lock);atom(output/'source-counts.json',counts);report['source_counts']=ref(output/'source-counts.json')
        verify(plan)
        for p in builds['programs'].values():check_ref(p['source_qlf_pin']);check_ref(p['support_qlf_pin'])
        report.update(status='PASSED',active=None,finished_utc=now(),source_runtime_qlf_pins_unchanged=True)
    except BaseException as error:report.update(status='FAILED',error=repr(error),finished_utc=now());raise
    finally:atom(output/'report.json',report)
    print(json.dumps(dict(status='PASSED-BOUNDED',report=ref(output/'report.json'),cases=len(report['cases']))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=['prepare','build','bounded'],required=True)
    parser.add_argument('--runtime-report',type=Path);args=parser.parse_args()
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.mode=='prepare':require(args.runtime_report is not None,'--runtime-report required');prepare(args.runtime_report)
        else:
            plan=verify(load(PLAN))
            if args.mode=='build':build(plan,lock)
            else:bounded(plan,lock)


if __name__=='__main__':main()
