"""Offline additive intake for the exact SWI eight-row-block spectral source.

The final six-process report and exact-source count review are pinned.
No native process, compilation, browser or network path exists in this module.
Earlier intake utilities are imported unchanged; no constants are reassigned.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from qualification import import_bqn_knucleotide as shared

BASE='experiments/prolog/optimization-v1/'
QUAL=BASE+'qualification-v1/'
PILOT=BASE+'pilot-700-v1/'
FULL_DIR=BASE+'full-selected-v1/'
ADMISSION=BASE+'admission-v1/'
PLAN,RESULTS,PREPARED=[ADMISSION+name+'.json' for name in ['plan','results','prepared']]
KEY='spectralnorm:prolog-spectralnorm-blocks8-v1'
PARENT='spectralnorm:prolog-spectralnorm-compact'
SOURCE=BASE+'source-v1/sources/spectralnorm/blocks8-specialized.pl'
SOURCE_SHA='bc2223d1fa22aed05a7ea4da9904a88a701c6d0972749ced5f0e106fc9685ba5'
PARENT_SOURCE='archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-spectralnorm-compact/input/sources/spectralnorm/compact.pl'
PARENT_SHA='1d868f9e772820b1b2e7a3c68e82f142b6704357f6fa1249ef3e828e78c02fda'
SUPPORT=BASE+'source-v1/support/clbg_io.pl'
SUPPORT_SHA='bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3'
SOURCE_REVISION='612fb31e030be207779c03cddb00a16af56f0173'
SOURCES={'parent':PARENT_SHA,'serial-specialized':'cdd1303c005ba0743ae60778f4ac4004b12f5acb9c727535e870c184345c5fef','blocks8-specialized':SOURCE_SHA}
MODULES=dict(zip(SOURCES,['clbg_spectralnorm','clbg_spectralnorm_serial','clbg_spectralnorm_blocks8']))
SELECTED=['parent','blocks8-specialized']
RUNTIME_STAGE=BASE+'.build/runtime-attempt-v2'
APP=RUNTIME_STAGE+'/arm64-app/SWI-Prolog.app'
RUNTIME=APP+'/Contents/MacOS/swipl'
RUNTIME_HOME=APP+'/Contents/Resources/swipl'
RUNTIME_SHA='554814b1da7c0c30595adafb758145e42a6134c696b47c8870d359008246443e'
DMG_SHA='bf775f0b8d7880f4908dee513316013ef42a73793be392814fde2a0a8e9ddc5d'
DMG_URL='https://www.swi-prolog.org/download/stable/bin/swipl-10.0.2-1.fat.dmg'
HISTORICAL_CONFIG='archive/languages/prolog/20261013/runtime-qualified/success-halt-v1/runtime-config.json'
PREPARE='archive/languages/prolog/20261013/revisions/prepare-success-halt-v1/tools/prepare_qlf.pl'
READER='archive/validation/loc-normalization/20261013/prolog-proposal-v5/scan_source.pl'
COUNTER='archive/validation/loc-normalization/20261013/prolog-proposal-v5/foreign_prolog.py'
FLAGS=['-q','-O','-f','none','--stack-limit=8g']
FULL=dict(n=5500,bytes=12,sha256='f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb')
FULL_BYTES=b'1.274224153\n'
PILOT_SECONDS={'parent':2.963027875,'blocks8-specialized':0.666657,'serial-specialized':2.727397041}
FINAL_FULL_SHA='6817f95f1e6a6c0aa2cc93e4746f4d6e9f79449f851e65a80ea5ab4ecbe3f87d'  # Completed six-process cohort, pinned after the quiet window.
SHARED_SHA='5e79b71fc96822ece4604f4075bae444f25ecaf2b65bd3af07d9cea66c6f1843'
PINNED={
 'producer_plan':'4a31caf0bd6d106d01329baf4f5aff3ca7d314235ac398e491f87eb9c8c2d4de',
 'controller':'df1d7c3f64b3f72dc4c50bf7c181c1ffd426d4e44b473d615bf759309dd8bf34',
 'process':'34e7b16fa6853af99e35faedb893c4eb21425c1a09df62dd4d65ca6526a1130e',
 'pilot_plan':'c9d368e2a1db0aecd190fd238cf17d101b044eae485872756a676a5ee89c7bc4',
 'pilot_controller':'8f554f3278e49dd27665e3f03b821783f19b99cebd099e02d42e39ee5e8df3b5',
 'pilot':'b01458f60a0b5bee4c6bccb47278f7b1062367a701ecde18052e9f50b00ed9c9',
 'foundation':'bf3de3c515794adb0a35440385bad385eb56f32d8326460699bb3a0ad47aa669',
 'builds':'c4536958d8302ae2a89b8af5f269a73c6515e0ac6380a11d724155ecb459113a',
 'bounded':'2814b60bf5ac6326ec758175e492ca0a8d3ec4e00b5be9bfa2eca2b1f7207b01',
 'ownership':'55d933c57612f5c46cbd42e0ad74aeb83b2c44896e2a032d84dac931087c0e1f',
 'shared_helpers':SHARED_SHA,
}
REFS=dict(importer='tools/qualification/import_prolog_spectral.py',shared_helpers='tools/qualification/import_bqn_knucleotide.py',
 producer_plan=FULL_DIR+'plan.json',controller=FULL_DIR+'run_full.py',process=FULL_DIR+'process.py',
 pilot_plan=PILOT+'plan.json',pilot_controller=PILOT+'run_pilot.py',pilot=PILOT+'pilot-v1/report.json',
 foundation=QUAL+'execution-plan-v3.json',builds=QUAL+'build-native-v3/report.json',bounded=QUAL+'completed-v2/report.json',
 ownership=BASE+'source-ownership-extension-v1/approved.json',ownership_proposal=BASE+'source-ownership-extension-v1/proposal.json',
 runtime=QUAL+'runtime-v3/restoration-report.json',runtime_artifacts=QUAL+'runtime-v3/artifacts.json',
 corpus='experiments/shared/bounded-corpus-v1/cases/manifest.json',full=FULL_DIR+'full-v1/report.json',
 source_review=QUAL+'README.md')
AUTHOR_CONTEXT=copy.deepcopy(shared.AUTHOR_CONTEXT)
sha,pin,load,encoded,require=shared.sha,shared.pin,shared.load,shared.encoded,shared.require


def safe_relative(value):
    require(isinstance(value,str) and value and not Path(value).is_absolute() and '..' not in Path(value).parts
        and Path(value).as_posix()==value and value!='.','Unsafe relative evidence path')
    return value


def recorded_root(report):
    rows=report.get('cases',[]);command=rows[0].get('command') if rows else None;suffix='/'+RUNTIME
    require(isinstance(command,list) and len(command)==14 and isinstance(command[0],str) and command[0].endswith(suffix),'Wrong recorded SWI command')
    value=command[0][:-len(suffix)]
    require(Path(value).is_absolute() and '..' not in Path(value).parts and Path(value).as_posix()==value,'Unsafe recorded execution root')
    return value


class Evidence(shared.Evidence):
    def __init__(self,root,recorded):
        super().__init__(root);self.recorded=recorded
    def relative(self,value):
        if Path(value).is_absolute():
            result=shared.relative(self.root,value,self.recorded)
        else:result=safe_relative(value)
        return safe_relative(result)
    def check(self,ref):
        require(isinstance(ref,dict),'Missing evidence reference')
        return super().check({**ref,'path':self.relative(ref.get('path',''))})
    def path(self,value):return self.root/self.relative(value)
    def document(self,ref):return load(self.check(ref))
    def pin(self,value):return pin(self.root,self.relative(value))


def require_final_pin():
    require(isinstance(FINAL_FULL_SHA,str) and re.fullmatch('[0-9a-f]{64}',FINAL_FULL_SHA),'Full cohort pending final immutable pin')


def make_plan(root=ROOT):
    require_final_pin();root=Path(root)
    evidence={name:pin(root,path) for name,path in REFS.items()}
    require(all(evidence[name]['sha256']==digest for name,digest in PINNED.items()) and evidence['full']['sha256']==FINAL_FULL_SHA,'Frozen source/cohort/ownership pin differs')
    full=load(root/REFS['full'])
    return dict(schema='prolog-spectral-admission-plan.v1',key=KEY,parent=PARENT,source=dict(path=SOURCE,sha256=SOURCE_SHA),
        support=dict(path=SUPPORT,sha256=SUPPORT_SHA),source_revision=SOURCE_REVISION,recorded_execution_root=recorded_root(full),
        evidence=evidence,author_context=AUTHOR_CONTEXT,selected='blocks8-specialized',
        selection='Preselected lowest N700 candidate; retain serial pilot and all six matched full observations. No global optimality or full-size ranking of omitted serial source.',
        chart_admission=False,historical_observations_unchanged=True)


def check_refs(evidence,plan):
    require(plan.get('schema')=='prolog-spectral-admission-plan.v1' and plan.get('key')==KEY and plan.get('parent')==PARENT
        and plan.get('source')==dict(path=SOURCE,sha256=SOURCE_SHA) and plan.get('source_revision')==SOURCE_REVISION,'Admission source/parent identity differs')
    for name,ref in plan['evidence'].items():
        require(ref['path']==REFS[name],'Admission evidence path differs');evidence.check(ref)
    require(set(plan['evidence'])==set(REFS) and all(plan['evidence'][name]['sha256']==digest for name,digest in PINNED.items())
        and plan['evidence']['full']['sha256']==FINAL_FULL_SHA,'Unreviewed frozen evidence')


def check_pins(evidence,pins,local_artifacts):
    require(isinstance(pins,dict) and pins,'Missing producer pin closure')
    for path,digest in pins.items():
        path=evidence.relative(path)
        require(re.fullmatch('[0-9a-f]{64}',digest) is not None,'Malformed artifact hash')
        if '/.build/' in path:
            require(path.startswith(BASE+'.build/'),'Unexpected ignored binary root')
            if local_artifacts:evidence.check(dict(path=path,sha256=digest))
        else:evidence.check(dict(path=path,sha256=digest))


def environment(recorded):
    return dict(PATH='/usr/bin:/bin',LC_ALL='C',LANG='C',TZ='UTC',SWI_HOME_DIR=recorded+'/'+RUNTIME_HOME)


def source_path(name):return BASE+'source-v1/sources/spectralnorm/'+name+'.pl'


def qlf_path(name,support=False):
    prefix=QUAL+'build-v3/'+name+'/input/'
    return prefix+'support/clbg_io.qlf' if support else prefix+'sources/spectralnorm/'+name+'.qlf'


def run_command(recorded,name,n):
    return [recorded+'/'+RUNTIME]+FLAGS+['-l',recorded+'/'+qlf_path(name,True),'-s',recorded+'/'+qlf_path(name),'-g','clbg_io:run('+MODULES[name]+':main)','--',str(n)]


def check_programs(evidence,programs):
    require(set(programs)==set(SOURCES),'Wrong exact-source build inventory')
    for name,digest in SOURCES.items():
        p=programs[name]
        require(p['source']==dict(path=source_path(name),sha256=digest) and p['module']==MODULES[name]
            and p['run_argv']==run_command(evidence.recorded,name,0)[:-1],'Unreviewed source/module/QLF invocation')
        require(evidence.relative(p['source_qlf'])==qlf_path(name) and evidence.relative(p['support_qlf'])==qlf_path(name,True),'Wrong QLF path')
        source=evidence.check(p['source']).read_bytes();compiled=evidence.check(p['compiled_source']).read_bytes()
        require(source==compiled and hashlib.sha256(source).hexdigest()==digest,'Compiled input differs from original source')
        require(evidence.check(p['support']).read_bytes()==evidence.check(dict(path=SUPPORT,sha256=SUPPORT_SHA)).read_bytes(),'Generic support copy differs')
        if 'source_qlf_pin' in p:
            require(p['source_qlf_pin']['path']==qlf_path(name) and p['support_qlf_pin']['path']==qlf_path(name,True),'QLF pin path differs')
            evidence.check(p['source_qlf_pin']);evidence.check(p['support_qlf_pin'])


def check_runtime(evidence,ref,artifact_ref,local_artifacts):
    runtime=evidence.document(ref);artifacts=evidence.document(artifact_ref)
    require(runtime['schema']=='prolog-spectral-runtime-restoration.v1' and runtime['status']=='PASSED'
        and runtime['whole_tree_exact'] is True and runtime['historical_file_count']==2799 and runtime['owned_mount_detached'] is True,'Incomplete SWI restoration')
    require(runtime['binary']==dict(path=RUNTIME,sha256=RUNTIME_SHA) and runtime['home']==evidence.recorded+'/'+RUNTIME_HOME
        and runtime['environment']==environment(evidence.recorded),'Restored runtime identity/path differs')
    historical=evidence.document(runtime['historical_config'])
    expected={APP+'/'+path.split('/arm64-app/SWI-Prolog.app/',1)[1]:digest for path,digest in historical['pins'].items() if '/arm64-app/SWI-Prolog.app/' in path}
    require(len(expected)==2799 and runtime['pins']==expected and expected[RUNTIME]==RUNTIME_SHA,'Historical 2799-file runtime map differs')
    require(historical['binary_sha256']==RUNTIME_SHA and historical['version_components']==[10,0,2] and historical['architecture']=='arm64'
        and historical['default_gc_observed'] is True and historical['bounded_observed'] is False,'Wrong historical SWI backend')
    archive=runtime['archive']
    require(archive['url']==DMG_URL and archive['sha256']==DMG_SHA and archive['bytes']==34301763,'Wrong official archive')
    if local_artifacts:
        for path,digest in expected.items():evidence.check(dict(path=path,sha256=digest))
        evidence.check(archive)
    require(artifacts['schema']=='prolog-spectral-restoration-artifacts.v1' and artifacts['report']==ref
        and evidence.relative(artifacts['original_recorded_report'])==RUNTIME_STAGE+'/report.json','Durable restoration bridge differs')
    mapping=artifacts['durable_exact_copies']
    for original,target in mapping.items():
        relative=evidence.relative(original);prefix=RUNTIME_STAGE+'/commands/'
        require(relative.startswith(prefix) and target['path']==QUAL+'runtime-v3/commands/'+relative[len(prefix):],'Wrong copied restoration artifact')
        evidence.check(target)
    for row in runtime['attempts']:
        directory=str(Path(row['stdout']['path']).parent)
        raw=evidence.document(mapping[directory+'/process.json'])
        # The mutable environment object in the completed restoration summary
        # added SWI_HOME_DIR to early attach/plutil/slice rows after raw capture.
        # Accept only this exact transparent summary addition; raw is authoritative.
        require({k:v for k,v in row.items() if k!='environment'}=={k:v for k,v in raw.items() if k!='environment'},'Raw restoration process differs')
        require(row['environment']==raw['environment'] or (row['environment']=={**raw['environment'],'SWI_HOME_DIR':evidence.recorded+'/'+RUNTIME_HOME}
            and raw['command'][0] in ['/usr/bin/hdiutil','/usr/bin/plutil','/usr/bin/lipo']),'Unreviewed restoration environment difference')
        require(raw['exit_code']==0 and raw['timed_out'] is False and raw['remaining_process_group'] is False,'Failed restoration process')
        for stream in ['stdout','stderr']:
            target=mapping[raw[stream]['path']];require(target['sha256']==raw[stream]['sha256'],'Restoration stream bridge differs');evidence.check({**target,'bytes':raw[stream]['bytes']})
    version=next(row for row in runtime['attempts'] if row['command']==[evidence.recorded+'/'+RUNTIME,'--version'])
    require(version['stdout']['sha256']=='17f679c59f5980232090f30158ce6caef61e950a0e5946d48d53e4f8887ec4be' and version['stderr']['bytes']==0,'Exact SWI version stream differs')
    return runtime


def check_raw_process(evidence,row,directory,*,quantitative,source=None,n=None,sample=None,expected=None,summary_extras=()):
    require(evidence.relative(row['stdout']['path'])==directory+'/stdout.bin' and evidence.relative(row['stderr']['path'])==directory+'/stderr.bin','Wrong process stream path')
    raw=evidence.document(evidence.pin(directory+'/process.json'))
    additions={'source','n','sample','output_valid','source_sha256','power_before','power_after','competing_processes_before',*summary_extras}
    require(raw=={k:v for k,v in row.items() if k not in additions},'Raw process receipt differs')
    seconds=row.get('elapsed_seconds')
    require(row.get('exit_code')==0 and row.get('timed_out') is False and row.get('remaining_process_group') is False
        and row.get('quantitative_benchmark') is quantitative and type(row.get('pid')) is int and row['pid']>0
        and type(seconds) in (int,float) and math.isfinite(seconds) and seconds>0 and row.get('started_utc') and row.get('finished_utc')
        and row.get('stdin')=='/dev/null' and row.get('cwd')==evidence.recorded,'Failed/nonfinite/incomplete process')
    require(row['environment']==environment(evidence.recorded),'Wrong process environment')
    for stream in ['stdout','stderr']:evidence.check({**row[stream],'path':directory+'/'+stream+'.bin'})
    require(row['stderr']['bytes']==0,'Unexpected subject/probe stderr')
    if source is not None:
        require(row['source']==source and row['n']==n and row['command']==run_command(evidence.recorded,source,n)
            and row.get('source_sha256')==SOURCES[source] and row.get('output_valid') is True,'Wrong exact process source/workload/command')
        if sample is not None:require(row['sample']==sample,'Wrong sample identity')
    if expected is not None:require((evidence.root/directory/'stdout.bin').read_bytes()==expected,'Complete output differs')
    if quantitative:
        shared.check_power(row['power_before']);shared.check_power(row['power_after'])
        require(row['competing_processes_before']==[] and row['maximum_rss_bytes']<=10*1024**3,'Invalid process/resource controls')
    return raw


def check_builds(evidence,ref,foundation,runtime):
    builds=evidence.document(ref)
    require(builds['schema']=='prolog-spectral-native-builds.v1' and builds['status']=='PASSED' and builds['active'] is None
        and builds['plan']==dict(path=REFS['foundation'],sha256=PINNED['foundation']),'Wrong or incomplete source build')
    check_programs(evidence,builds['programs'])
    require(foundation['programs'].keys()==builds['programs'].keys(),'Build/foundation inventory differs')
    for row in builds['attempts']:
        directory=str(Path(evidence.relative(row['stdout']['path'])).parent)
        raw=evidence.document(evidence.pin(directory+'/process.json'))
        require(raw=={k:v for k,v in row.items() if k!='stderr_classification'},'Raw compiler/loader process differs')
        require(raw['exit_code']==0 and raw['timed_out'] is False and raw['remaining_process_group'] is False
            and raw['quantitative_benchmark'] is False and raw['cwd']==evidence.recorded,'Failed compilation/inspection process')
        for stream in ['stdout','stderr']:evidence.check({**raw[stream],'path':directory+'/'+stream+'.bin'})
        is_loader=directory==QUAL+'build-native-v3/runtime-probe'
        env=environment(evidence.recorded)
        if is_loader:env['DYLD_PRINT_LIBRARIES']='1'
        require(raw['environment']==env,'Compiler/loader environment differs')
        if not is_loader:
            stderr=(evidence.root/directory/'stderr.bin').read_bytes()
            module=next((MODULES[name] for name in SOURCES if '/'+name+'/' in directory),None)
            expected=('Warning: [Thread main] Local definition of clbg_prepare:main/0 overrides weak import from '+str(module)+'\n').encode()
            require(stderr in [b'',expected],'Unreviewed compiler diagnostic')
    require(len(builds['attempts'])==10,'Compiler/inspect attempt inventory differs')
    identity=builds['runtime_identity']
    require(identity['version']==[10,0,2] and identity['gc'] is True and identity['bounded'] is False and identity['threads'] is True
        and identity['stack_limit']==8589934592 and identity['home']==evidence.recorded+'/'+RUNTIME_HOME,'Actual compiler runtime differs')
    require(identity['concurrent']['module']=='thread' and identity['concurrent']['name']=='concurrent'
        and identity['concurrent']['arity']==3 and identity['concurrent']['meta_predicate']=='concurrent(+,:,+)'
        and evidence.relative(identity['concurrent']['file'])==RUNTIME_HOME+'/library/thread.pl'
        and identity['append']['meta_predicate']=='none' and identity['univ']['meta_predicate']=='none','Actual library metadata differs')
    for name,p in builds['programs'].items():
        root=QUAL+'build-v3/'+name+'/input'
        require(len(p['compilations'])==2,'Missing support/application compilation')
        for label,record,source in [('support',p['compilations'][0],root+'/support/clbg_io.pl'),
            ('application',p['compilations'][1],root+'/sources/spectralnorm/'+name+'.pl')]:
            process=evidence.document(record['process']);metadata=evidence.document(record['metadata']);evidence.check(record['wam'])
            expected=[evidence.recorded+'/'+RUNTIME]+FLAGS+['-l',evidence.recorded+'/'+PREPARE,'-g','clbg_prepare:main','--','compile',
                evidence.recorded+'/'+source,evidence.recorded+'/'+record['metadata']['path'],evidence.recorded+'/'+record['wam']['path'],evidence.recorded+'/'+root]
            require(process['command']==expected and metadata['mode']=='compile' and metadata['target']==evidence.recorded+'/'+source,'Wrong compiler target/flags')
            rt=metadata['runtime']
            require(rt['version_components']==[10,0,2] and rt['gc'] is True and rt['bounded'] is False
                and rt['home']==evidence.recorded+'/'+RUNTIME_HOME and rt['stack_limit']==8589934592,'Compiler runtime flag mismatch')
            for path in metadata['loaded_sources']:
                relative=evidence.relative(path)
                require(relative.startswith(APP+'/') or relative.startswith(root+'/') or relative==PREPARE,'Unreviewed compiled source root')
        inspect=p['inspect'];process=evidence.document(inspect['process']);metadata=evidence.document(inspect['metadata'])
        wam=evidence.check(inspect['wam']).read_text()
        require(process['command']==[evidence.recorded+'/'+RUNTIME]+FLAGS+['-l',evidence.recorded+'/'+PREPARE,'-g','clbg_prepare:main','--','inspect',
            evidence.recorded+'/'+qlf_path(name),evidence.recorded+'/'+inspect['metadata']['path'],evidence.recorded+'/'+inspect['wam']['path'],evidence.recorded+'/'+root]
            and metadata['mode']=='inspect' and metadata['target']==evidence.recorded+'/'+qlf_path(name),'Wrong production QLF inspection')
        for predicate in ['coefficient/3','apply/3','apply_transpose/3','apply_ata/3']:
            require(MODULES[name]+':'+predicate in wam,'Required separately compiled predicate missing')
    return builds


def check_ownership(evidence,ref):
    receipt=evidence.document(ref);source=evidence.check(dict(path=SOURCE,sha256=SOURCE_SHA)).read_text()
    require(ref['sha256']==PINNED['ownership'] and receipt['schema']=='prolog-spectral-exact-source-owner-extension-review.v1'
        and receipt['status']=='independently-reviewed-exact-source-retained-policy-extension'
        and receipt['source']==SOURCE and receipt['source_sha256']==SOURCE_SHA and receipt['source_revision']==SOURCE_REVISION
        and receipt['application_loc']==receipt['retained_rule_proposed_loc']==128 and receipt['physical_loc']==87
        and receipt['independent_review_approved'] is True and receipt['native_grammar_qualification_claimed'] is False
        and receipt['current_native_v5_normalized_loc'] is None,'Exact 128/87 manual source approval differs')
    require(receipt['independent_review']['decision']=='approve-exact-128-87-ledger','Missing independent source review')
    proposal=evidence.document(receipt['proposal'])
    require(proposal['line_ledger']==receipt['line_ledger'] and proposal['independent_review_approved'] is False
        and proposal['application_loc'] is None,'Unapproved proposal/history changed')
    ledger=receipt['line_ledger'];lines=source.splitlines()
    require(len(ledger)==len(lines),'Stale written source ledger')
    for index,(row,text) in enumerate(zip(ledger,lines),1):
        significant=bool(text.strip()) and not text.lstrip().startswith('%')
        require(row['line']==index and row['source_text']==text and row['significant'] is significant
            and type(row['retained_rule_units']) is int and row['retained_rule_units']>=0
            and sum(owner['units'] for owner in row['retained_rule_owners'])==row['retained_rule_units'],'Wrong source owner/span/units')
    require(sum(row['retained_rule_units'] for row in ledger)==128 and sum(row['significant'] for row in ledger)==87,'Source owners do not reconcile')
    for value in receipt['evidence'].values():evidence.check(value)
    projection=evidence.document(receipt['evidence']['current_v5_projection'])
    require(projection['normalized_loc'] is None and projection['physical_loc']==87
        and projection['diagnostics'] and any('Unselected vendor library' in row.get('detail','') for row in projection['diagnostics']),'Unchanged V5 null was rewritten')
    for name,item in receipt['native_library_metadata'].items():
        path=item['source_path'];require(path in load(evidence.root/REFS['foundation'])['pins'],'Unbound standard library source')
        require(load(evidence.root/REFS['foundation'])['pins'][path]==item['source_sha256'],'Standard library hash differs')
    require(receipt['native_library_metadata']['thread']['source_sha256']=='bf007d4752f446205dfda66ffc3638d5a8c977fdb802a58073836e3a1167a217','Wrong pinned concurrent implementation')
    return receipt


def check_bounded(evidence,ref,builds):
    complete=evidence.document(ref)
    require(complete['schema']=='prolog-spectral-completed-bounded-qualification.v1' and complete['status']=='PASSED'
        and complete['complete_output_cases']==39 and complete['vector_comparisons']==144 and complete['geometry_cases']==12 and complete['work_cases']==6
        and complete['source_runtime_qlf_pins_unchanged'] is True and complete['parallel_source_count_certified'] is False
        and complete['quantitative_benchmark'] is False and complete['chart_admission'] is False,'Incomplete native bounded qualification')
    attempt=evidence.document(complete['complete_output_attempt'])
    require(attempt['status']=='FAILED' and attempt['error']=="ValueError('State probe warning retained')" and attempt['builds']==dict(path=REFS['builds'],sha256=PINNED['builds']),
        'Diagnostic-bearing original attempt was relabeled')
    corpus=evidence.document(evidence.pin(REFS['corpus']));cases=sorted((row for row in corpus['cases'] if row['benchmark']=='spectralnorm'),key=lambda row:row['n'])
    require([row['n'] for row in cases]==[1,2,3,5,9,10,100],'Shared bounded inventory differs')
    expected={}
    for row in cases:
        for field in ['stdin','expected']:
            item={**row[field],'path':str(Path(REFS['corpus']).parent/row[field]['path'])};evidence.check(item)
        expected[row['n']]=evidence.path(str(Path(REFS['corpus']).parent/row['expected']['path'])).read_bytes()
    identities=[(n,name) for n in [0,1,2,3,5,7,8,9,10,15,16,17,100] for name in SOURCES]
    require([(row['n'],row['source']) for row in attempt['cases']]==identities,'Missing/duplicated complete-output case')
    for item in attempt['cases']:
        name,n=item['source'],item['n'];row=item['process'];directory=QUAL+'bounded-v3/n-'+str(n)+'-'+name
        require(item['exact_output_valid'] is True and item['shared_reference'] is (n in [1,2,3,5,9,10,100]),'Wrong bounded decision')
        check_raw_process(evidence,row,directory,quantitative=False)
        require(row['command']==run_command(evidence.recorded,name,n),'Bounded command/argument differs')
        raw=(evidence.root/directory/'stdout.bin').read_bytes()
        if name=='parent':expected.setdefault(n,raw)
        require(raw==expected[n] and re.fullmatch(rb'[0-9]+\.[0-9]{9}\n',raw) is not None,'Bounded reference/parent output differs')
    states={};ns=[1,2,3,5,7,8,9,10,15,16,17,31]
    require(len(complete['attempts'])==3 and set(complete['state_work'])==set(SOURCES),'Clean native capture inventory differs')
    for row,name in zip(complete['attempts'],SOURCES):
        directory=QUAL+'completed-v2/state-work-'+name
        check_raw_process(evidence,row,directory,quantitative=False)
        require(row['command']==[evidence.recorded+'/'+RUNTIME]+FLAGS+['-l',evidence.recorded+'/'+QUAL+'state_probe_v3.pl','-g','prolog_spectral_state_probe:main','--',
            evidence.recorded+'/'+qlf_path(name),MODULES[name]],'Clean state capture command differs')
        require(complete['state_work'][name]==evidence.pin(directory+'/stdout.bin'),'State stream binding differs')
        state=evidence.document(complete['state_work'][name]);states[name]=state
        require(state['schema']=='prolog-spectral-single-qlf-state-work-capture.v1' and state['status']=='CAPTURED' and state['module']==MODULES[name]
            and state['version']==[10,0,2] and state['gc'] is True and state['bounded'] is False
            and state['home']==evidence.recorded+'/'+RUNTIME_HOME,'State/runtime identity differs')
        require([(v['n'],v['pattern'],v['operation']) for v in state['vectors']]==[(n,p,o) for n in ns for p in ['positive','signed'] for o in ['apply','apply_transpose','apply_ata']],
            'Missing vector/orientation/input pattern')
        for vector in state['vectors']:
            require(len(vector['components'])==vector['n'] and all(isinstance(x,str) and math.isfinite(float(x)) for x in vector['components']),'Malformed exact component data')
        require(state['worker_outcomes']==dict(failure_propagated=True,exception_propagated=True,workers_joined=True),'Worker lifecycle checks differ')
        require([w['n'] for w in state['work']]==[3,8],'Missing bounded work case')
        for work in state['work']:
            require(work==dict(module=MODULES[name],n=work['n'],coefficient_calls=40*work['n']**2,forward_products=20,transpose_products=20,ata_applications=20,
                library_wrapper=True,quantitative_benchmark=False),'Per-key coefficient/product work omitted')
    require(states['parent']['vectors']==states['serial-specialized']['vectors']==states['blocks8-specialized']['vectors'],'Exact intermediate vectors differ')
    require(states['parent']['geometry']==states['serial-specialized']['geometry']==[],'Unexpected nonparallel geometry evidence')
    geometry=states['blocks8-specialized']['geometry'];require([row['n'] for row in geometry]==ns,'Missing block boundary case')
    for row in geometry:
        n=row['n'];ranges=[dict(block=b,first=b*n//8,end=(b+1)*n//8,rows=(b+1)*n//8-b*n//8) for b in range(8)]
        require(row['ranges']==ranges and row['result_lengths']==[r['rows'] for r in ranges] and row['rows']==n
            and all(row[field] is True for field in ['workers_joined','exactly_eight_goals','ground_inputs','independent_results','ordered_results']),'Wrong parallel ranges/results/lifetime')
    count=evidence.document(complete['source_counts'])
    require(count['schema']=='prolog-spectral-native-source-counts.v1' and count['status']=='PARTIAL-RETAINED-POLICY-REPLAY'
        and count['independent_review_approved'] is False and count['parallel_certified'] is False,'Native count scope differs')
    packets={}
    for name in [*SOURCES,'support']:
        item=count['rows'][name];directory=QUAL+'completed-v2/reader-'+name
        raw=evidence.document(item['process']);check_raw_process(evidence,raw,directory,quantitative=False)
        source=SUPPORT if name=='support' else source_path(name)
        require(raw['command']==[evidence.recorded+'/'+RUNTIME,'-q','-f','none','-l',evidence.recorded+'/'+READER,'-g','prolog_source_scan_v1:main','--',evidence.recorded+'/'+source],'Original source reader command differs')
        packet=evidence.document(evidence.pin(directory+'/stdout.bin'));packets[name]=packet
        require(packet['source']==evidence.recorded+'/'+source and packet['source_text']==evidence.check(item['source']).read_text()
            and packet['version']==[10,0,2],'Native reader source/bytes differ')
    import importlib.util
    counter_ref=dict(path=COUNTER,sha256='6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8')
    spec=importlib.util.spec_from_file_location('prolog_spectral_frozen_owner_replay',evidence.check(counter_ref))
    counter=importlib.util.module_from_spec(spec);spec.loader.exec_module(counter)
    for name,loc,physical in [('parent',96,67),('serial-specialized',114,78),('blocks8-specialized',None,87)]:
        item=count['rows'][name];context=counter.BundleContext([packets[name],packets['support']])
        projection=counter.count_prolog(evidence.path(source_path(name)).read_bytes(),packets[name],language='prolog',context=context)
        projection=json.loads(encoded(projection))
        require(projection==evidence.document(item['projection']) and item['normalized_loc']==loc and item['physical_loc']==physical,'Native source-owner replay differs')
    return complete


def check_producer(evidence,ref,foundation,builds,local_artifacts):
    producer=evidence.document(ref)
    require(ref['sha256']==PINNED['producer_plan'] and producer['schema']=='prolog-spectral-selected-full-plan.v1'
        and producer['status']=='PREPARED-NO-EXECUTION' and producer['source_revision']==SOURCE_REVISION
        and producer['sources']==SELECTED and producer['retained_pilot_pool']==list(SOURCES)
        and producer['n']==5500 and producer['rounds']==3 and producer['order_seed']==20261020
        and producer['chart_admission'] is False and producer['new_observations']==0,'Wrong full-size producer plan')
    require(producer['controller']==dict(path=REFS['controller'],sha256=PINNED['controller'])
        and producer['process_helper']==dict(path=REFS['process'],sha256=PINNED['process'])
        and producer['programs']==builds['programs'] and producer['flags']==FLAGS
        and producer['binary']==dict(path=RUNTIME,sha256=RUNTIME_SHA)
        and producer['environment']==environment(evidence.recorded),'Producer runtime/source/observer differs')
    require(producer['foundation']==dict(path=REFS['foundation'],sha256=PINNED['foundation'])
        and producer['builds']==dict(path=REFS['builds'],sha256=PINNED['builds'])
        and producer['bounded']==dict(path=REFS['bounded'],sha256=PINNED['bounded'])
        and producer['pilot']==dict(path=REFS['pilot'],sha256=PINNED['pilot'])
        and producer['pilot_plan']==dict(path=REFS['pilot_plan'],sha256=PINNED['pilot_plan']),'Producer prerequisite binding differs')
    require(producer['required_work']==dict(power_iterations=10,ata_applications=20,matrix_vector_products=40,
        coefficient_calls_per_process=1210000000,coefficient_calls_formula='40*5500*5500',matrix_cache=False,parallel_worker_limit=8,
        evidence='Exact production sources/QLFs plus existing bounded native work wrappers; full processes contain no wrappers/instrumentation.'),'Full required work changed')
    rng=random.Random(20261020);orders=[]
    for sample in [1,2,3]:
        order=SELECTED.copy();rng.shuffle(order);orders.append(dict(sample=sample,n=5500,sources=order))
    require(producer['orders']==orders and producer['preselection']['pilot_seconds']==PILOT_SECONDS
        and producer['preselection']['selected_sources']==SELECTED and producer['preselection']['omitted_full_source']=='serial-specialized','Changed preselection/schedule')
    require(producer['retained_source_counts']['blocks8-specialized']['normalized_loc'] is None
        and producer['retained_source_counts']['blocks8-specialized']['candidate_independent_count_approved'] is False,
        'Historical measured-plan count status changed')
    reference=producer['expected'];require(reference['bytes']==12 and reference['sha256']==FULL['sha256']
        and reference['path']==evidence.pin(FULL_DIR+'expected.stdout') and evidence.check(reference['path']).read_bytes()==FULL_BYTES,'Full reference bytes differ')
    owner=evidence.check(reference['established_reference_source']);tree=ast.parse(owner.read_text())
    values=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='FULL' for t in node.targets))
    require(values['spectralnorm']==(5500,12,FULL['sha256']),'Established shared full reference differs')
    require(all(producer['pins'].get(path)==digest for path,digest in foundation['pins'].items()),'Full plan omits native foundation closure')
    check_pins(evidence,producer['pins'],local_artifacts)
    return producer


def check_pilot(evidence,ref,producer):
    report=evidence.document(ref);plan=evidence.document(dict(path=REFS['pilot_plan'],sha256=PINNED['pilot_plan']))
    require(report['schema']=='prolog-spectral-pilot700-execution.v1' and report['status']=='PASSED' and report['active'] is None
        and report['plan']==dict(path=REFS['pilot_plan'],sha256=PINNED['pilot_plan']) and report['pins']==plan['pins']
        and report['n']==700 and report['rounds']==1 and report['new_observations']==3 and report['seconds']==PILOT_SECONDS
        and report['exact_parent_output_match'] is True and report['pins_unchanged'] is True
        and report['full_workload'] is False and report['diagnostic_profile'] is True and report['chart_admission'] is False,'Incomplete or changed pilot')
    require(plan['programs']==producer['programs'] and plan['controller']==dict(path=REFS['pilot_controller'],sha256=PINNED['pilot_controller'])
        and plan['sources']==list(SOURCES) and plan['n']==700 and plan['rounds']==1 and plan['full_mode_available'] is False,'Pilot source/runtime selection differs')
    expected_ref=report['independent_reference'];expected=evidence.check(expected_ref['stdout']).read_bytes()
    require(expected_ref['function']=='spectralnorm(700)' and expected_ref['source']['sha256']=='6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3'
        and expected_ref['bytes']==len(expected)==12,'Independent pilot reference differs');evidence.check(expected_ref['source'])
    require([row['source'] for row in report['cases']]==plan['order']==['parent','blocks8-specialized','serial-specialized'],'Pilot inventory/order differs')
    for row in report['cases']:
        name=row['source'];check_raw_process(evidence,row,PILOT+'pilot-v1/'+name,quantitative=True,source=name,n=700,sample=1,expected=expected)
        require(row['elapsed_seconds']==PILOT_SECONDS[name],'Pilot time changed')
    return report


def check_full(evidence,ref,producer):
    require_final_pin();require(ref['sha256']==FINAL_FULL_SHA,'Unreviewed final full cohort')
    report=evidence.document(ref)
    require(report['schema']=='prolog-spectral-selected-full-execution.v1' and report['mode']=='full' and report['status']=='PASSED'
        and report['active'] is None and report['full_workload'] is True and report['diagnostic_profile'] is False and report['chart_admission'] is False
        and report['new_observations']==6 and report['rounds']==3 and report['n']==5500 and report['sources']==SELECTED
        and report['retained_pilot_pool']==list(SOURCES) and report['source_revision']==SOURCE_REVISION
        and report['pins_unchanged'] is True and report['exact_reference_and_parent_outputs'] is True,'Incomplete/diagnostic full-size cohort')
    require(report['plan']==dict(path=REFS['producer_plan'],sha256=PINNED['producer_plan'])
        and report['controller']==dict(path=REFS['controller'],sha256=PINNED['controller']) and report['pins']==producer['pins']
        and report['orders']==producer['orders'] and report['preselection']==producer['preselection']
        and report['required_work']==producer['required_work'] and report['timing_boundary']==producer['timing_boundary']
        and report['runtime']==producer['runtime'] and report['binary']==producer['binary'],'Full source/controller/runtime/work binding differs')
    require(type(report['common_mutex_inode']) is int and report['common_mutex_inode']>0 and report['started_utc'] and report['finished_utc'],'Missing full mutex/time record')
    wanted=[(order['sample'],name) for order in producer['orders'] for name in order['sources']]
    require([(row['sample'],row['source']) for row in report['cases']]==wanted,'Missing/duplicated/out-of-order full observation')
    pids=[]
    for row in report['cases']:
        name,sample=row['source'],row['sample'];directory=FULL_DIR+'full-v1/round-'+str(sample)+'-'+name
        check_raw_process(evidence,row,directory,quantitative=True,source=name,n=5500,sample=sample,expected=FULL_BYTES)
        require(row['stdout']['bytes']==12 and row['stdout']['sha256']==FULL['sha256'],'Wrong full output length/hash');pids.append(row['pid'])
    require(len(set(pids))==6,'Reused process identity in full cohort')
    samples={name:[row['elapsed_seconds'] for row in report['cases'] if row['source']==name] for name in SELECTED}
    require(report['samples']==samples and report['medians']=={n:statistics.median(v) for n,v in samples.items()},'Stale full sample aggregation')
    require(set(report['sample_sd_seconds'])==set(samples) and all(type(report['sample_sd_seconds'][n]) in (int,float)
        and math.isfinite(report['sample_sd_seconds'][n]) and report['sample_sd_seconds'][n]>=0
        and math.isclose(report['sample_sd_seconds'][n],statistics.stdev(v),rel_tol=1e-14,abs_tol=0) for n,v in samples.items()),'Stale full sample dispersion')
    for name in SOURCES:evidence.check(dict(path=FULL_DIR+'full-v1/sources/'+name+'.pl',sha256=SOURCES[name]))
    evidence.check(dict(path=FULL_DIR+'full-v1/controllers/run_full.py',sha256=PINNED['controller']))
    evidence.check(dict(path=FULL_DIR+'full-v1/controllers/process.py',sha256=PINNED['process']))
    require(evidence.check(evidence.pin(FULL_DIR+'full-v1/expected.stdout')).read_bytes()==FULL_BYTES,'Saved full reference snapshot differs')
    return report


def reconcile(root=ROOT,local_artifacts=True):
    require_final_pin();root=Path(root).resolve();plan=load(root/PLAN)
    require(plan==make_plan(root),'Stale/changed Prolog admission plan')
    evidence=Evidence(root,plan['recorded_execution_root']);check_refs(evidence,plan)
    foundation=evidence.document(plan['evidence']['foundation'])
    require(foundation['schema']=='prolog-spectral-bounded-execution-plan.v1' and foundation['status']=='PREPARED-NO-EXECUTION'
        and foundation['binary']==dict(path=RUNTIME,sha256=RUNTIME_SHA) and foundation['flags']==FLAGS,'Wrong native foundation')
    check_programs(evidence,foundation['programs'])
    runtime=check_runtime(evidence,plan['evidence']['runtime'],plan['evidence']['runtime_artifacts'],local_artifacts)
    builds=check_builds(evidence,plan['evidence']['builds'],foundation,runtime)
    ownership=check_ownership(evidence,plan['evidence']['ownership'])
    bounded=check_bounded(evidence,plan['evidence']['bounded'],builds)
    producer=check_producer(evidence,plan['evidence']['producer_plan'],foundation,builds,local_artifacts)
    pilot=check_pilot(evidence,plan['evidence']['pilot'],producer)
    full=check_full(evidence,plan['evidence']['full'],producer)
    require(recorded_root(full)==evidence.recorded and {runtime['common_mutex_inode'],builds['common_mutex_inode'],bounded['common_mutex_inode'],pilot['common_mutex_inode'],full['common_mutex_inode']}=={full['common_mutex_inode']},'Execution root/common mutex differs')
    # The frozen full producer pins every failed and successful small artifact;
    # require the known diagnostic attempts remain failed instead of relabeling.
    for path in [QUAL+'build-native-v1/report.json',QUAL+'build-native-v2/report.json',QUAL+'bounded-v3/report.json',QUAL+'completed-v1/report.json']:
        require(evidence.document(evidence.pin(path))['status']=='FAILED','A retained failed attempt was relabeled')
    require(evidence.check(dict(path=PARENT_SOURCE,sha256=PARENT_SHA)).read_bytes()==evidence.check(dict(path=source_path('parent'),sha256=PARENT_SHA)).read_bytes(),'Retained parent snapshot changed')
    selected=[]
    for row in full['cases']:
        if row['source']=='blocks8-specialized':
            item=copy.deepcopy(row);item.update(producer_report=plan['evidence']['full'],producer_plan=plan['evidence']['producer_plan']);selected.append(item)
    samples=[row['elapsed_seconds'] for row in selected]
    program=dict(key=KEY,id=KEY.split(':',1)[1],original_program_key=PARENT,source_sha256=SOURCE_SHA,files=[SOURCE_SHA,SUPPORT_SHA],
        loc=128,physical_loc=87,samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=full['sample_sd_seconds']['blocks8-specialized'],
        command=selected[0]['command'],sample_execution_metadata=selected,build_command=evidence.document(builds['programs']['blocks8-specialized']['compilations'][1]['process'])['command'],
        build_cwd=evidence.recorded)
    artifacts=[dict(path=path,sha256=digest) for path,digest in sorted(evidence.fingerprints.items()) if '/.build/' not in path]
    return dict(schema='prolog-spectral-admission-results.v1',status='RECONCILED',plan=pin(root,PLAN),evidence=plan['evidence'],
        programs=[program],recorded_execution_root=evidence.recorded,recorded_at=full['finished_utc'],author_context=AUTHOR_CONTEXT,
        new_observations=3,matched_evidence_observations=6,matched_controls=[copy.deepcopy(row) for row in full['cases'] if row['source']=='parent'],
        matched_candidate_medians=full['medians'],matched_control_speedup=full['medians']['parent']/program['median_seconds'],
        source_count_review=ownership,native_v5_normalized_loc=None,full_workload_n=5500,required_work=producer['required_work'],
        runtime_environment=environment(evidence.recorded),runtime_details=dict(version='SWI-Prolog version 10.0.2 for arm64-darwin',
            executable_sha256=RUNTIME_SHA,backend='swi-native-bytecode-vm',restoration=plan['evidence']['runtime'],
            restored_application_file_count=2799,official_archive_url=DMG_URL,official_archive_sha256=DMG_SHA,
            archived_limitation='Ignored official DMG/runtime 2799-file bytes are not required or freshly rehashed by archived replay; exact historical manifests and durable native receipts remain bound. Production QLFs and all small raw streams are mandatory archived evidence.',
            restoration_summary_note='Early attach/plutil/slice summary environments gained SWI_HOME_DIR after raw capture; only that exact documented addition is permitted and raw process receipts are authoritative.'),
        toolchains=dict(prolog=dict(version='SWI-Prolog 10.0.2',sha256=RUNTIME_SHA)),timing_boundary=producer['timing_boundary'],
        historical_observations_unchanged=True,selection=plan['selection'],artifacts=artifacts)


def authorship_record(parent,results,evidence):
    result=copy.deepcopy(parent['authorship'])
    result.update(kind='ai-adapted',label='AI adapted · retained Prolog predecessor',origin_status='unresolved',source_sha256=[SOURCE_SHA,SUPPORT_SHA],
        parent_programs=[PARENT],parent_sources=[{**copy.deepcopy(ref),'program_key':PARENT,'relationship':'local predecessor'} for ref in parent['authorship'].get('retained_sources',[])],
        retained_sources=[dict(source_sha256=SOURCE_SHA,url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)]
            +[copy.deepcopy(ref) for ref in parent['authorship'].get('retained_sources',[]) if ref['source_sha256']==SUPPORT_SHA],
        ai=dict(tool=AUTHOR_CONTEXT['tool'],models=[],model_family=AUTHOR_CONTEXT['model_family'],exact_model=None,
            status='family-identified-exact-model-unverified',matched_source_files=[SOURCE_SHA],total_source_files=2,evidence=[evidence['plan'],evidence['results']]),
        local_change_license=dict(status='suite-license',id='Apache-2.0',evidence='LICENSE',scope='New local changes only; inherited terms remain unresolved.'),
        evidence=[evidence['plan']['path'],evidence['results']['path'],evidence['ownership']['path']])
    return result


def bound_authorship(data,profile,root=ROOT):
    root=Path(root);results=load(root/RESULTS);detail=profile.get('source_provenance_record') or {}
    evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    require(profile.get('key')==KEY and profile.get('files')==[SOURCE_SHA,SUPPORT_SHA] and detail.get('kind')=='suite-authored-optimization'
        and detail.get('source_sha256')==SOURCE_SHA and detail.get('original_program_key')==PARENT
        and detail.get('admission')==evidence['results'] and detail.get('author_context')==AUTHOR_CONTEXT
        and results['schema']=='prolog-spectral-admission-results.v1' and results['status']=='RECONCILED'
        and results['plan']==evidence['plan'] and results['programs'][0]['source_sha256']==SOURCE_SHA
        and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest()==SOURCE_SHA
        and hashlib.sha256(data['files'][SUPPORT_SHA]['code'].encode()).hexdigest()==SUPPORT_SHA,'Unbound Prolog source/authorship')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT],results,evidence)


def append_catalog(before,root=ROOT):
    root=Path(root).resolve();results=load(root/RESULTS)
    require(results==reconcile(root,local_artifacts=False),'Stale reconciled Prolog results')
    require(KEY not in before['programs'] and KEY not in before.get('program_inventory',{}) and 'prolog_spectral_audit' not in before,'Prolog candidate already admitted')
    parent=before['programs'][PARENT]
    require(parent['files']==[PARENT_SHA,SUPPORT_SHA] and parent['loc']==96 and parent['physical_loc']==67
        and parent['seconds']==179.423098959,'Historical Prolog parent/count/median changed')
    for digest in [PARENT_SHA,SUPPORT_SHA]:
        require(before['files'][digest]['sha256']==digest and hashlib.sha256(before['files'][digest]['code'].encode()).hexdigest()==digest,'Historical parent/helper source differs')
    require(SOURCE_SHA not in before['files'],'Candidate source already cataloged')
    data=copy.deepcopy(before);r=results['programs'][0];bench=next(b for b in data['benchmarks'] if b['key']=='spectralnorm')
    require(r['loc']>=bench['baseline_loc'] and r['median_seconds']>=bench['baseline_seconds'],'New global baseline needs separate normalization review')
    evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    data['files'][SOURCE_SHA]=dict(name='blocks8-specialized.pl',path=SOURCE,archive_path=SOURCE,sha256=SOURCE_SHA,code=(root/SOURCE).read_text())
    row=dict(key=KEY,id=r['id'],receipt_key=r['id'],benchmark='spectralnorm',language='prolog',files=[SOURCE_SHA,SUPPORT_SHA],
        loc=128,physical_loc=87,loc_metric='assignment-normalized',seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],
        x=128/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],formatted_loc=None,formatted_x=None,
        formatted_loc_status='pending',formatted_loc_complete=False,formatted_loc_evidence={},
        report=RESULTS,report_sha256=evidence['results']['sha256'],source_report=evidence['ownership']['path'],loc_report=evidence['ownership']['path'],
        command=r['command'],runtime_arguments=['5500'],build_command=r['build_command'],build_cwd=r['build_cwd'],cwd=results['recorded_execution_root'],
        execution_mode='interpreter',binary_sha256=RUNTIME_SHA,runtime_sha256=RUNTIME_SHA,native_observations=3,timing_alias_of=None,
        sample_execution_metadata=r['sample_execution_metadata'],original_program_key=PARENT,retained_source_revision=SOURCE_REVISION,
        local_adaptation=True,distinct_optimization_claimed=True,eligible_for_chart=True,
        source_provenance='Suite-authored eight-block specialization of the retained derived Prolog spectral source; inherited predecessor origin and terms remain unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization',original_program_key=PARENT,source_sha256=SOURCE_SHA,
            admission=evidence['results'],origin_status='inherited-unresolved',author_context=AUTHOR_CONTEXT),
        runtime_policy='Exact retained SWI-Prolog 10.0.2 ARM64 bytecode VM; -q -O -f none --stack-limit=8g; default GC/unbounded integers; ordinary concurrent(8,Goals,[])',
        runtime_support='Pinned unmodified SWI thread/lists libraries and unchanged generic CLI support. All coefficient, row, block and goal-construction helpers are application source.',
        runtime_environment=results['runtime_environment'],timing_boundary=results['timing_boundary'],
        timing_summary='Three matched fresh complete-process observations; all six parent/candidate rows and serial pilot retained. Historical parent 179.423s observation is unchanged and is not used as the matched control.',
        required_work_validated=True,algorithm=dict(strict=True,status='required-work-reviewed',native_benchmark_kernel=False,
            reason='Separate coefficient/apply/apply_transpose/apply_ata predicates retain twenty AtA applications and all forty dense products; eight independent contiguous row blocks return ordered results through standard concurrent/3. No matrix cache or native benchmark executor.',
            full_work=dict(n=5500,power_applications=20,matrix_vector_products=40,coefficient_evaluations=1210000000),evidence=evidence['bounded']),
        source_accounting=dict(policy='application-loc-v1',application_loc=128,physical_loc=87,evidence=evidence['ownership']['path'],review_sha256=evidence['ownership']['sha256'],
            qualification='Independently approved exact-source manual retained-policy extension 128/87. Unchanged V5 normalized count remains null; no native grammar qualification.',files=[]),
        file_roles={SOURCE_SHA:dict(role='application',included_in_application_loc=True,normalized_loc=128,physical_loc=87),
            SUPPORT_SHA:dict(role='runtime-support',included_in_application_loc=False,normalized_loc=39,physical_loc=24)},
        full_output_validation=dict(all_three_samples_passed=True,evidence=evidence['full']),chart_admission=dict(historical_reports_unchanged=True,**evidence),
        measured_backend=dict(key='prolog',execution='interpreter',label='Prolog (SWI10.0.2)',verified=True,
            evidence=dict(verified=True,report=RESULTS,report_sha256=evidence['results']['sha256'],command=r['command'],source_sha256=[SOURCE_SHA,SUPPORT_SHA],
                runtime_receipt=dict(verified=True,report=RESULTS,report_sha256=evidence['results']['sha256'],field='/toolchains/prolog/version',
                    value=results['toolchains']['prolog']['version'],value_encoding='literal-saved-string'))))
    row['authorship']=authorship_record(parent,results,evidence)
    data['programs'][KEY]=row;data.setdefault('program_inventory',{})[KEY]=copy.deepcopy(row)
    group=next(g for g in bench['groups'] if g['language']=='prolog');group['programs'].append(KEY)
    candidates=[data['programs'][key] for key in group['programs'] if data['programs'][key].get('eligible_for_chart') is not False]
    group['fast']=min(candidates,key=lambda p:(p['seconds'],p['loc'],p['key']))['key'];group['small']=min(candidates,key=lambda p:(p['loc'],p['seconds'],p['key']))['key']
    for summary in data.get('reference_summary',[]):
        if summary['lang']!='prolog':continue
        groups=[g for b in data['benchmarks'] for g in b['groups'] if g['language']=='prolog']
        for kind in ['fast','small']:
            selected=[data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind]=dict(x=statistics.geometric_mean(p['x'] for p in selected),y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*evidence.values(),*results['artifacts'],dict(path=SOURCE,sha256=SOURCE_SHA)]:data['archive_paths'][ref['path']]=ref['path']
    data['prolog_spectral_audit']=dict(schema='prolog-spectral-catalog-extension.v1',appended_programs=[KEY],evidence=evidence,
        measured_at=results['recorded_at'],new_observations=3,matched_evidence_observations=6,source_files_added=1,old_profiles_unchanged=True,old_baselines_unchanged=True)
    for pool in ['programs','program_inventory','files','archive_paths']:
        require(all(data[pool][key]==old for key,old in before.get(pool,{}).items()),'Historical '+pool+' changed')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--apply',action='store_true')
    parser.add_argument('--expected-before-sha256');parser.add_argument('--expected-prepared-sha256');args=parser.parse_args()
    require(args.prepare!=args.apply,'Choose exactly one of --prepare/--apply');require_final_pin()
    catalog=ROOT/'data/benchmarks.json'
    if args.prepare:
        raw=catalog.read_bytes();before=json.loads(raw,object_pairs_hook=shared.no_duplicates,parse_constant=lambda value:require(False,'Nonfinite JSON: '+value))
        before_sha=hashlib.sha256(raw).hexdigest();shared.write(ROOT/PLAN,make_plan());shared.write(ROOT/RESULTS,reconcile())
        shared.write(ROOT/PREPARED,append_catalog(before));require(sha(catalog)==before_sha,'Canonical changed during preview preparation')
        print(dict(before_sha256=before_sha,prepared_sha256=sha(ROOT/PREPARED),results_sha256=sha(ROOT/RESULTS),canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256,'Apply requires reviewed before/preview hashes')
        require(sha(catalog)==args.expected_before_sha256 and sha(ROOT/PREPARED)==args.expected_prepared_sha256,'Reviewed before/preview identity differs')
        after=append_catalog(load(catalog));require(encoded(after)==(ROOT/PREPARED).read_bytes(),'Prepared overlay does not reproduce')
        require(sha(catalog)==args.expected_before_sha256,'Canonical changed during reconciliation');shared.write(catalog,after)
        print('Added exact Prolog eight-block profile; historical 96/67 source and observations retained.')


if __name__=='__main__':main()
