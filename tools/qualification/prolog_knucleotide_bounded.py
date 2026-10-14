"""Prepare and execute the corrected k-nucleotide qualification, serially.

Reuses the frozen QLF preparer, bounded observer/receipt checks and owner grammar.
Successful native evidence still awaits independent WAM and source-owner review.
No full benchmark timing or publication is performed by this controller.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/prolog/knucleotide-linear-v1'
Q=PACKET/'qualification'
BOUNDED_SHA='642e0f761aa873023eb24e8a66e9a6837d57f1eb9568e80fe1478a263e95bda9'
PLAN=ROOT/'experiments/prolog/full90-v1/plan.json'
PLAN_SHA='55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a'
SOURCE_SHA='b3f524485ccfc29204efecc2f0da47b91b7a63041f4591512ecb2af844ade1e6'
SOURCE_FILES={'sources/knucleotide/compact.pl':SOURCE_SHA,'sources/knucleotide/optimized.pl':SOURCE_SHA,
    'support/clbg_io.pl':'bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3',
    'support/clbg_records.pl':'efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19'}
STOP_SHA='0649952532e5a1c8a1bd27d805e087f950ea0c50bb82e6246c1ecd1c230536b6'
LEGACY=ROOT/'archive/validation/loc-normalization/20261013/prolog-proposal-v5/jobs/reader31-v1'
LEGACY_REPORT_SHA='1f3f96d2888ffac3180d75ec7652a762fb3be0fa09278e3e6e3a410354c02700'
LEGACY_TERMINAL_SHA='c4e2d74e97d514d2dc1d9fd29e50fe152d88e857c7dd0bfa9f553fcfb2d5f089'
COMPLETE='native-evidence-complete-awaiting-independent-work-and-owner-review'
KINDS='prolog-revcomp-bounded'  # Immutable legacy validator's exact observer tag.


def require(value,message):
    if not value:raise AssertionError(message)


def load(path,digest,name):
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'Pinned executable source changed: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),result.__dict__);return result


# Definitions only. No original plan, native process, or full closure is read here.
b=load(ROOT/'tools/qualification/prolog_revcomp_bounded.py',BOUNDED_SHA,'knucleotide_frozen_bounded')
kb=b.kb
sha,save,bind=b.sha,b.save,b.bind


def source_tools(pins):
    # The reviewed prepare plan freezes these current source bytes; run also
    # verifies every input before importing either definition-only helper.
    return (load(Q/'fixtures.py',pins[str(Q/'fixtures.py')],'knucleotide_fixture_oracle'),
            load(ROOT/'tools/qualification/prolog_knucleotide_source_units.py',
                 pins[str(ROOT/'tools/qualification/prolog_knucleotide_source_units.py')],'knucleotide_units'))


def own_pins():
    result={str(PACKET/name):digest for name,digest in SOURCE_FILES.items()}
    result.update({str(PLAN):PLAN_SHA,str(PACKET/'stop-v1/closure.json'):STOP_SHA,
        str(b.PREPARER):b.PREPARER_SHA,str(ROOT/'tools/qualification/prolog_revcomp_bounded.py'):BOUNDED_SHA,
        str(ROOT/'tools/qualification/kotlin_bounded_v2.py'):b.OBSERVER_SHA,
        str(ROOT/'tools/qualification/kotlin_helpers.py'):kb.HELPER_CONTROLLER_SHA,
        str(ROOT/'tools/qualification/elixir_bounded.py'):kb.REFERENCE_CONTROLLER_SHA,
        str(kb.kh.PYTHON):kb.kh.PYTHON_SHA,
        str(LEGACY/'fixture-receipt.json'):LEGACY_REPORT_SHA,
        str(LEGACY/'terminal-pin.json'):LEGACY_TERMINAL_SHA})
    for path in (Path(__file__),Q/'fixtures.py',Q/'inspect_maps.pl',Q/'inspect_targets.pl',
                 ROOT/'tools/qualification/prolog_knucleotide_source_units.py'):
        result[str(path.resolve())]=sha(path)
    grammar=LEGACY.parents[1]
    result[str(grammar/'foreign_prolog.py')]='6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8'
    result[str(grammar/'scan_source.pl')]='b48e07039914d448e4f313235f347f4604269d0a9802896f0d019ed3e7c52021'
    return result


def legacy_reader(pins):
    report=json.loads(Path(bind(pins,LEGACY/'fixture-receipt.json',LEGACY_REPORT_SHA)).read_bytes())
    terminal=json.loads(Path(bind(pins,LEGACY/'terminal-pin.json',LEGACY_TERMINAL_SHA)).read_bytes())
    require(report['status']==terminal['status']=='passed-awaiting-original-source-review' and
            terminal['receipt_sha256']==LEGACY_REPORT_SHA and report['tests_run']==31 and
            len(report['expected_ids'])==len(set(report['expected_ids']))==31 and
            set(report['expected_ids'])==set(report['started_ids'])==set(report['discovered_ids']),
            'Existing source-reader fixture cohort differs')
    require(all(report[key]==0 for key in ('failures','errors','skipped','expected_failures','unexpected_successes')) and
            report['pin_reconciliation_passed'] is True and report['terminal_artifact_errors']==[] and
            terminal['integrity_errors']==[] and report['shared_timing_mutex_held'] is True and
            report['mutex_inode']==kb.LOCK_INODE,'Existing source reader is not qualified')
    grammar={Path(path).name:digest for path,digest in report['input_pins'].items()
             if '/prolog-proposal-v5/' in path}
    require(grammar['foreign_prolog.py']==pins[str(LEGACY.parents[1]/'foreign_prolog.py')] and
            grammar['scan_source.pl']==pins[str(LEGACY.parents[1]/'scan_source.pl')],
            'Existing native fixtures exercised another owner grammar')


def command(binary,compiled_root,variant):
    require(variant in ('compact','optimized'),'Unknown source alias')
    return [binary]+b.FLAGS+['-l',str(compiled_root/'support/clbg_io.qlf'),
        '-l',str(compiled_root/'support/clbg_records.qlf'),'-s',
        str(compiled_root/('sources/knucleotide/'+variant+'.qlf')),
        '-g','clbg_io:run(clbg_knucleotide:main)']


def prepare_command(binary,mode,target,directory,authored,preloads=()):
    require(mode in ('compile','inspect'),'Unknown compiler mode')
    prefix=[binary]+b.FLAGS
    for path in preloads:prefix+=['-l',str(path)]
    return prefix+['-l',str(b.PREPARER),'-g','clbg_prepare:main','--',mode,str(target),
                   str(directory/'loaded-inputs.json'),str(directory/'candidate.wam'),str(authored)]


def schedule(manifest,units):
    require(manifest['schema']=='prolog-knucleotide-linear-fixtures-v1' and len(manifest['cases'])==31 and
            len({c['id'] for c in manifest['cases']})==31 and
            sum(c['expected_status']=='success' for c in manifest['cases'])==26 and
            sum(c['expected_status']=='invalid-acgt' for c in manifest['cases'])==5,
            'Wrong complete-output fixture cohort')
    rows=[]
    for name in ('clbg_io','clbg_records','compact','optimized'):
        rows.append(dict(id='compile-'+name,kind='compile',name=name))
    for variant in ('compact','optimized'):
        rows.append(dict(id='inspect-'+variant,kind='inspect',variant=variant))
        rows.extend(dict(id=variant+'-'+c['id'],kind='case',variant=variant,case=c) for c in manifest['cases'])
        require(manifest['complete_map_cases']==['empty','all-four-base-words','query-overlaps','lowercase-long-line'],
                'Complete-map fixture scope changed')
        rows.extend(dict(id='maps-'+variant+'-'+name,kind='maps',variant=variant,case_id=name)
                    for name in manifest['complete_map_cases'])
    rows.append(dict(id='builtin-metadata',kind='metadata'))
    rows.extend(dict(id='reader-fixture-'+r['id'],kind='reader-fixture',fixture=r) for r in units.fixtures())
    rows.extend(dict(id='reader-'+Path(name).stem,kind='reader',source=name) for name in SOURCE_FILES)
    require(len(rows)==len({r['id'] for r in rows})==88,'Incomplete or duplicate native schedule')
    return rows


def runtime_profiles(manifest_rows):
    require([r['id'] for r in manifest_rows]==['prolog-knucleotide-compact','prolog-knucleotide-optimized','mech-aot-control'] and
            [r['language'] for r in manifest_rows]==['prolog','prolog','mech'] and
            manifest_rows[2]['key']=='knucleotide:prolog-full-study:mech-control','Original manifest/control differs')
    rows=manifest_rows[:2]
    require(all(r['binary']==rows[0]['binary'] and r['runtime_environment']==rows[0]['runtime_environment'] for r in rows),
            'Original aliases/runtime differ')
    return rows


def prepare(args):
    plan_path,output,fixtures=(p.resolve() for p in (args.plan,args.output,args.fixtures))
    require(all(p.is_relative_to(Q) and not p.exists() for p in (plan_path,output,fixtures)) and
            not plan_path.is_relative_to(output) and not fixtures.is_relative_to(output) and
            not output.is_relative_to(fixtures) and plan_path!=fixtures,'Fresh separate qualification paths required')
    require(sha(PLAN)==PLAN_SHA,'Original runtime plan changed')
    retained=json.loads(PLAN.read_bytes());pins=dict(retained['pins'])
    for path,digest in own_pins().items():bind(pins,path,digest)
    require(not b.verify_pins(pins),'Existing physical runtime/input closure changed')
    legacy_reader(pins)
    rows=runtime_profiles(retained['manifests']['knucleotide']['profiles'])
    oracle,units=source_tools(pins)
    # Exact retained corpus uses the unchanged existing evidence resolver. No
    # source/runtime process or old producer is executed to recover these bytes.
    evidence=kb.eb.Evidence();cases=kb.eb.reference_cases(evidence)['knucleotide']
    for path,digest in evidence.pins.items():bind(pins,path,digest)
    known=[(r['case'],Path(r['stdin']['path']).read_bytes(),Path(r['expected']['path']).read_bytes()) for r in cases]
    manifest=oracle.write(fixtures,known,sha(Q/'fixtures.py'))
    source_fixtures=fixtures/'source';source_fixtures.mkdir()
    for row in units.fixtures():(source_fixtures/(row['id']+'.pl')).write_text(row['source_text'])
    for path in sorted(fixtures.rglob('*')):
        if path.is_file():bind(pins,path)
    value=dict(schema='prolog-knucleotide-linear-qualification-plan-v1',status='prepared-awaiting-native-execution',
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),pins=pins,
        binary=rows[0]['binary'],environment=rows[0]['runtime_environment'],fixtures=str(fixtures),
        output=str(output),schedule=schedule(manifest,units),planned_native_processes=88,
        process_timeout_seconds=kb.TIMEOUT,cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=kb.FILE_LIMIT,
        maximum_live_subject_processes=1,automatic_retries=0,benchmark_samples=0,
        source_work_qualified=False,canonical_LOC_admitted=False,full_timings_qualified=False,chart_admission=False)
    require(not b.verify_pins(pins),'Inputs changed during preparation')
    plan_path.parent.mkdir(parents=True,exist_ok=True);require(not plan_path.exists(),'Plan appeared')
    save(plan_path,value)
    print(json.dumps(dict(plan=str(plan_path),sha256=sha(plan_path),native_executions=0,planned_native_processes=88)))


def validate_plan(plan):
    expected=dict(schema='prolog-knucleotide-linear-qualification-plan-v1',status='prepared-awaiting-native-execution',
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),planned_native_processes=88,
        process_timeout_seconds=kb.TIMEOUT,cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=kb.FILE_LIMIT,
        maximum_live_subject_processes=1,automatic_retries=0,benchmark_samples=0,
        source_work_qualified=False,canonical_LOC_admitted=False,full_timings_qualified=False,chart_admission=False)
    for key,value in expected.items():
        require(type(plan.get(key)) is type(value) and plan.get(key)==value,'Qualification plan policy differs: '+key)
    require(all(plan['pins'].get(path)==digest for path,digest in own_pins().items()),'Required source pin omitted/changed')
    retained=json.loads(PLAN.read_bytes());profile=runtime_profiles(retained['manifests']['knucleotide']['profiles'])[0]
    require(plan['binary']==profile['binary'] and plan['environment']==profile['runtime_environment'] and
            all(plan['pins'].get(path)==digest for path,digest in retained['pins'].items()),'Retained runtime closure differs')
    for key in ('output','fixtures'):
        path=Path(plan[key]);require(path.is_absolute() and path.resolve()==path and path.is_relative_to(Q),'Unsafe '+key)
    oracle,units=source_tools(plan['pins']);fixtures=Path(plan['fixtures'])
    manifest=json.loads((fixtures/'manifest.json').read_bytes())
    require(manifest['generator_sha256']==sha(Q/'fixtures.py') and schedule(manifest,units)==plan['schedule'],
            'Fixture/schedule changed')
    for path in sorted(fixtures.rglob('*')):
        require(not path.is_symlink(),'Symlink in fixture tree')
        if path.is_file():require(plan['pins'].get(str(path))==sha(path),'Unpinned fixture artifact')
    return oracle,units,manifest


def compiler_metadata(directory,mode,target,authored,loaded,plan):
    data=json.loads((directory/'loaded-inputs.json').read_bytes());runtime=data['runtime']
    require(data['mode']==mode and data['target']==str(target) and data['wam']==str(directory/'candidate.wam'),
            'Compiler target/VM listing differs')
    require(runtime==dict(version_components=[10,0,2],version_data='swi(10,0,2,[])',architecture='arm64-darwin',
        home=plan['environment']['SWI_HOME_DIR'],bounded=False,gc=True,stack_limit=8*1024**3),'Runtime policy differs')
    expected={str(authored/name) for name in loaded}
    actual={path for path in data['loaded_sources'] if Path(path).is_relative_to(authored)}
    require(actual==expected,'Compiler-bound authored inventory differs')
    for path in data['loaded_sources']:
        require(path in expected or path in plan['pins'],'Unpinned loaded source: '+path)
    for library in data['foreign_libraries']:
        require(library['resolved_path'] in plan['pins'],'Unpinned native library')
    return data


def check_output(case,stdout,stderr):
    if case['expected_status']=='success':
        require(not stderr and len(stdout)==case['output_bytes'] and
                hashlib.sha256(stdout).hexdigest()==case['output_sha256'],'Complete output mismatch')
        return
    require(case['expected_status']=='invalid-acgt','Unplanned outcome')
    expected=b"ERROR: [Thread main] Domain error: `acgt_nucleotide' expected, found `"+str(case['expected_invalid_code']).encode()+b"'\n"
    require(stdout==b'' and stderr==expected,'Invalid-base outcome differs')


def finish(report,plan,pins,output,snapshots,lock):
    errors=[]
    for name,expected in snapshots.items():
        try:require(b.inventory(output/name)==expected,'Completed artifact inventory changed')
        except BaseException as error:errors.append(dict(path=name,error=str(error) or type(error).__name__))
    if report['status']==COMPLETE:
        if not ([r['id'] for r in report['commands']]==[r['id'] for r in plan['schedule']] and
                report['native_processes_started']==88 and report['active'] is None and
                len(report['projections'])==2 and len({r['pid'] for r in report['commands']})==88):
            errors.append(dict(error='Incomplete successful qualification ledger'))
    integrity=b.verify_pins(pins)
    if errors or integrity:report['status']='failed-integrity'
    report.update(integrity_errors=integrity,artifact_errors=errors,finished_at=datetime.now(timezone.utc).isoformat())
    kb.kh.verify_lock(lock)
    report_path=output/'report.json'
    expected_report=(json.dumps(report,indent=2)+'\n').encode()
    expected_report_sha=hashlib.sha256(expected_report).hexdigest()
    save(report_path,report)
    artifacts={}
    try:
        require(report_path.read_bytes()==expected_report,'Serialized report changed before snapshot')
        artifacts=b.inventory(output)
        require(artifacts['report.json']==dict(bytes=len(expected_report),sha256=expected_report_sha),
                'Output inventory adopted another report')
        for name,expected in snapshots.items():
            require(b.inventory(output/name)==expected,'Command artifacts changed during closure inventory')
        late_integrity=b.verify_pins(pins)
        require(not late_integrity,'Input pins changed during closure inventory: '+str(late_integrity))
        require(b.inventory(output)==artifacts,'Output inventory changed during closure')
        require(report_path.read_bytes()==expected_report,'Serialized report changed during closure')
        kb.kh.verify_lock(lock)
    except BaseException as error:
        errors.append(dict(error=str(error) or type(error).__name__))
        report['status']='failed-integrity'
        report['artifact_errors']=errors
        # Retain externally changed bytes; never adopt them as a successful
        # producer report. A still-owned report can safely record the failure.
        if report_path.read_bytes()==expected_report:
            expected_report=(json.dumps(report,indent=2)+'\n').encode()
            expected_report_sha=hashlib.sha256(expected_report).hexdigest()
            save(report_path,report)
        artifacts=b.inventory(output)
    require(not (output/'terminal.json').exists(),'Terminal appeared')
    kb.kh.verify_lock(lock)
    terminal=dict(schema='prolog-knucleotide-linear-qualification-terminal-v1',
        status=report['status'],report_sha256=sha(report_path),expected_report_sha256=expected_report_sha,available_evidence=artifacts,
        integrity_errors=integrity,artifact_errors=errors,native_processes_started=report['native_processes_started'],
        common_mutex_held=True,common_mutex_inode=kb.LOCK_INODE,
        source_work_qualified=False,canonical_LOC_admitted=False,full_timings_qualified=False,chart_admission=False)
    save(output/'terminal.json',terminal)
    require((output/'terminal.json').read_bytes()==(json.dumps(terminal,indent=2)+'\n').encode(),
            'Serialized terminal changed')
    kb.kh.verify_lock(lock)
    require(not integrity and not errors,'Qualification closure failed')


def run(args,lock):
    require(sha(args.plan)==args.plan_sha256,'Prepared plan changed')
    plan=json.loads(args.plan.read_bytes());pins=dict(plan['pins']);bind(pins,args.plan,args.plan_sha256)
    require(not b.verify_pins(pins),'Prepared physical inputs changed')
    oracle,units,manifest=validate_plan(plan);legacy_reader(pins)
    output=Path(plan['output']);output.mkdir(parents=True,exist_ok=False)
    report=dict(schema='prolog-knucleotide-linear-qualification-report-v1',status='running',
        plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,pins=pins,started_at=datetime.now(timezone.utc).isoformat(),
        commands=[],active=None,native_processes_started=0,projections={},compiled_artifacts={},
        bounded_cases=0,complete_map_cases=0,source_work_qualified=False,canonical_LOC_admitted=False,
        full_timings_qualified=False,benchmark_samples=0,chart_admission=False)
    snapshots={};packets={};metadata=None;authored=output/'input';fixtures=Path(plan['fixtures'])
    save(output/'report.json',report)

    def execute(row,argv,payload=b'',warning=False,rejection=False):
        kb.kh.verify_lock(lock);directory=output/row['id'];directory.mkdir()
        entry=dict(row,argv=argv,pid=None,status='starting',stdin_bytes=len(payload),
                   stdin_sha256=hashlib.sha256(payload).hexdigest())
        report['commands'].append(entry);report['active']=row['id'];save(output/'report.json',report)
        def launched(pid):
            entry['pid']=pid;report['native_processes_started']+=1;save(output/'report.json',report)
        try:kb.observe(argv,plan['environment'],directory,payload,lock,launched,kind=KINDS)
        except AssertionError as error:
            expected='Native command exited unsuccessfully' if rejection else 'Unexpected stderr; raw bytes retained' if warning else None
            if str(error)!=expected:raise
        b.check_receipt(directory,argv,plan['environment'],payload,entry['pid'],rejection,warning)
        if warning:
            require((directory/'stderr.bin').read_bytes()==b'Warning: [Thread main] Local definition of clbg_prepare:main/0 overrides weak import from clbg_knucleotide\n',
                    'Unfamiliar compiler diagnostic')
        entry.update(status='native-lifetime-verified',process_sha256=sha(directory/'process.json'))
        report['active']=None;save(output/'report.json',report)
        return directory

    try:
        for relative,digest in SOURCE_FILES.items():
            path=authored/relative;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write((PACKET/relative).read_bytes())
            bind(pins,path,digest)
        for row in plan['schedule']:
            kind=row['kind'];name=row['id']
            if kind in ('compile','inspect'):
                relative=('support/'+row['name']+'.pl' if row.get('name','').startswith('clbg_') else
                          'sources/knucleotide/'+row.get('name',row.get('variant'))+'.pl')
                target=authored/relative
                loaded=[relative] if relative.startswith('support/') else [relative,'support/clbg_io.pl','support/clbg_records.pl']
                preloads=[]
                if kind=='inspect':
                    target=target.with_suffix('.qlf');preloads=[authored/'support/clbg_io.qlf',authored/'support/clbg_records.qlf']
                argv=prepare_command(plan['binary'],kind,target,output/name,authored,preloads)
                directory=execute(row,argv,warning=relative.startswith('sources/'))
                require((directory/'stdout.bin').read_bytes()==b'','Unexpected compiler stdout')
                compiler_metadata(directory,kind,target,authored,loaded,plan)
                artifact=(authored/relative).with_suffix('.qlf')
                require(artifact.is_file() and artifact.stat().st_size>0,'Missing QLF')
                if kind=='compile':
                    report['compiled_artifacts'][relative]=dict(path=str(artifact),sha256=sha(artifact))
                    bind(pins,artifact,report['compiled_artifacts'][relative]['sha256'])
            elif kind in ('case','maps'):
                for artifact in report['compiled_artifacts'].values():
                    require(sha(artifact['path'])==artifact['sha256'],'QLF changed before use')
                if kind=='case':
                    case=row['case'];payload=(fixtures/case['stdin']).read_bytes()
                    directory=execute(row,command(plan['binary'],authored,row['variant']),payload,
                                      rejection=case['expected_status']=='invalid-acgt')
                    check_output(case,(directory/'stdout.bin').read_bytes(),(directory/'stderr.bin').read_bytes())
                    report['bounded_cases']+=1
                else:
                    case=next(c for c in manifest['cases'] if c['id']==row['case_id']);payload=(fixtures/case['stdin']).read_bytes()
                    argv=[plan['binary']]+b.FLAGS+['-l',str(authored/'support/clbg_io.qlf'),'-l',str(authored/'support/clbg_records.qlf'),
                        '-l',str(Q/'inspect_maps.pl'),'-g','knucleotide_map_inspection:main','--',
                        str(authored/('sources/knucleotide/'+row['variant']+'.qlf'))]
                    directory=execute(row,argv,payload)
                    require(json.loads((directory/'stdout.bin').read_bytes())==oracle.complete_maps(payload),'Complete seven-map contents differ')
                    report['complete_map_cases']+=1
            elif kind=='metadata':
                argv=[plan['binary'],'-q','-f','none','-l',str(Q/'inspect_targets.pl'),'-g','knucleotide_loc_targets:main','--']
                directory=execute(row,argv);metadata=json.loads((directory/'stdout.bin').read_bytes())
                units.validate_metadata(metadata,plan['environment']['SWI_HOME_DIR'])
            else:
                source=fixtures/'source'/(row['fixture']['id']+'.pl') if kind=='reader-fixture' else PACKET/row['source']
                argv=[plan['binary'],'-q','-f','none','-l',str(units.GRAMMAR/'scan_source.pl'),'-g','prolog_source_scan_v1:main','--',str(source)]
                directory=execute(row,argv);packet=json.loads((directory/'stdout.bin').read_bytes())
                require(packet['source']==str(source) and packet['source_text'].encode()==source.read_bytes(),'Reader source differs')
                if kind=='reader-fixture':
                    projection=units.project_fixture(packet,metadata,plan['environment']['SWI_HOME_DIR'],row['fixture'])
                    save(directory/'projection.json',projection)
                else:packets[row['source']]=packet
            report['commands'][-1]['status']='validated'
            snapshots[name]=b.inventory(directory);save(output/'report.json',report)
        for variant in ('compact','optimized'):
            names=['sources/knucleotide/'+variant+'.pl','support/clbg_io.pl','support/clbg_records.pl']
            projection=units.project_bundle([packets[n] for n in names],[(PACKET/n).read_bytes() for n in names],
                [(authored/n).read_bytes() for n in names],metadata,plan['environment']['SWI_HOME_DIR'],
                (output/('inspect-'+variant)/'candidate.wam').read_text())
            save(output/('source-projection-'+variant+'.json'),projection)
            report['projections'][variant]=dict(path=str(output/('source-projection-'+variant+'.json')),
                sha256=sha(output/('source-projection-'+variant+'.json')),canonical_loc=projection['canonical_loc'],
                physical_loc=projection['physical_loc'])
            bind(pins,output/('source-projection-'+variant+'.json'),report['projections'][variant]['sha256'])
        require(report['bounded_cases']==62 and report['complete_map_cases']==8,'Incomplete correctness coverage')
        report['status']=COMPLETE
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__);raise
    finally:
        with kb.atomic():finish(report,plan,pins,output,snapshots,lock)
    print(json.dumps(dict(status=report['status'],native_processes_started=report['native_processes_started'])))


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare')
    for name in ('plan','fixtures','output'):p.add_argument('--'+name,type=Path,required=True)
    p=sub.add_parser('run');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    require(Path(sys.executable).resolve()==kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use retained Python with -I -S -B')
    def interrupted(signum,frame):raise KeyboardInterrupt('Qualification interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock)
        prepare(args) if args.action=='prepare' else run(args,lock)


if __name__=='__main__':main()
