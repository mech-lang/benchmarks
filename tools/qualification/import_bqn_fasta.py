"""Offline additive admission of the measured BQN FASTA floating-Bins source.

Prepare writes an overlay only. Apply needs separately reviewed before/preview
hashes. Full stdout is local verification data, excluded from durable proof;
archival replay verifies its complete recorded digest/length and raw receipt.
"""
import argparse
import copy
import difflib
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from qualification import import_bqn_knucleotide as shared

BASE='experiments/bqn/fasta-bins-v1/'
ADMISSION=BASE+'admission-v1/'
PLAN,RESULTS,PREPARED=[ADMISSION+name+'.json' for name in ['plan','results','prepared']]
KEY,PARENT='fasta:array-bqn-bins','fasta:array-bqn-faithful'
SOURCE=BASE+'sources/bins-empty-safe.bqn'
SOURCE_SHA='62c9f888a5869da3655fc530478a590ad7472f5c0ccf337dfb4e088dfef8edc5'
PARENT_SOURCE='archive/comparisons/array-comparison/all-20261009/sources/fasta.bqn'
PARENT_SHA='531d039ae5f9aa34f9db35e4df9efc723dc64098e3b1828c7b4fba972e35085e'
SOURCE_REVISION='e8c5182fe380402c042e312730a0703e47f1f3ee'
SOURCES=dict(zip(['parent-faithful','bins-only','bins-empty-safe'],[PARENT_SHA,
    'ca20f70bee8b85d0ab78bb20edba0ef9c30d55dcac4d37995377a220779914c2',SOURCE_SHA]))
FULL_SOURCES=['parent-faithful','bins-empty-safe']
NS=[0,1,2,19,20,21,29,30,31,59,60,61,287,574,1000,20000]
FULL=dict(n=25000000,bytes=254166745,sha256='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa')
CONTROLLER_SHA='ece6a617df537f09ce566d08e49f583bca035c5e5ebd0b4194fac52cf4e3e4d6'
PROCESS_SHA='313418c88aae0de3c86a98566c6138bbaeeb697830da99c9cc1ad5c7be0737ec'
SHARED_SHA='5e79b71fc96822ece4604f4075bae444f25ecaf2b65bd3af07d9cea66c6f1843'
EXECUTION_PLAN_SHA='67e357fa37949ae635c5f81e5571edff0632c89b35c7ed1d3792fab39400390f'
PROPOSAL_SHA='80e55c9904d3f227c4fcecf7fe65b462c28336b536e403f1338a2319075d9f60'
LOOKUP_SHA='e03cca27d7ac020614f83e9c8c6cf0f256f0de7b700ae1d9495f8675d92943ce'
LOOKUP_OUTPUT=dict(bytes=81,sha256='4b7a751165a398be00d059162a294c02767a58a7934eea8c45a57ddb006fec6b')
FFI=dict(path='/opt/homebrew/opt/libffi/lib/libffi.8.dylib',resolved_path='/opt/homebrew/Cellar/libffi/3.8.0/lib/libffi.8.dylib',
    sha256='e400b27537b9c7ff08e4e1d89fafc83e233020fcfb425a3ad25cb8c35029e1e1')
WORK=dict(naive_lcg_updates_full=200000000,floating_division=True,cumulative_probabilities_unchanged=True,
    native_lookup='ordinary f64 binary search',cached_random_period=False,integer_threshold_scaling=False,new_native_helper_or_ffi=False,application_imports=[])
TIMING_BOUNDARY='Fresh BQN process through exit, including startup, argv parsing, all naive LCG updates, floating probability searches, complete formatting/output and shutdown; excludes hashing, qualification and power checks.'
AUTHOR_CONTEXT=copy.deepcopy(shared.AUTHOR_CONTEXT)
REFS=dict(importer='tools/qualification/import_bqn_fasta.py',shared_helpers='tools/qualification/import_bqn_knucleotide.py',
    producer_plan=BASE+'execution-plan.json',source_proposal=BASE+'plan.json',controller=BASE+'run_serial.py',process_controller='tools/qualification/lean_run.py',
    frozen_review=BASE+'REVIEW.md',instructions=BASE+'RUNNER.md',ownership=BASE+'source-ownership-v1/bins-empty-safe-counts.json',
    lookup=BASE+'tests/lookup-equivalence.bqn',corpus=shared.CORPUS,runtime_build=shared.REFS['runtime_build'],
    bounded=BASE+'bounded-v1/report.json',full=BASE+'full-matched-v1/report.json')
REPORT_HASHES=dict(bounded='bb46a9f8a3532b36937670759c7e832d49d78d00c77c221bfdb9d8c1b35cb826',
    full='928491b6b871e270b37272f7d51be5403e4f92727676c4e3c5431eb63dd94ffd')
sha,pin,load,encoded,require,relative=shared.sha,shared.pin,shared.load,shared.encoded,shared.require,shared.relative


def recorded_root(report):
    rows=report.get('cases',[]);command=rows[0].get('command') if rows else None;suffix='/'+shared.RUNTIME
    require(isinstance(command,list) and len(command)==3 and isinstance(command[0],str)
        and Path(command[0]).is_absolute() and command[0].endswith(suffix),'Wrong recorded runtime command')
    prefix=command[0][:-len(suffix)]
    require(prefix and '..' not in Path(prefix).parts and Path(prefix).as_posix()==prefix,'Unsafe recorded repository root')
    return prefix


def make_plan(root=ROOT):
    root=Path(root)
    return dict(schema='bqn-fasta-admission-plan.v1',source=dict(path=SOURCE,sha256=SOURCE_SHA),selected='bins-empty-safe',
        parent_program=PARENT,source_revision=SOURCE_REVISION,recorded_execution_root=recorded_root(load(root/REFS['full'])),
        evidence={name:pin(root,path) for name,path in REFS.items()},author_context=AUTHOR_CONTEXT,
        selection='Admit the complete empty-safe floating-Bins source with all three observations; a modest matched improvement, without a major or global optimality claim.',
        full_stdout_archive_policy='Six large full stdout files are local-only, not required in the durable repository. Archived replay checks pinned raw native process hash/length records, not absent full bytes.',
        chart_admission=False,historical_observations_unchanged=True)


def check_sources(evidence):
    old=evidence.check(dict(path=PARENT_SOURCE,sha256=PARENT_SHA)).read_bytes()
    needle='  indices ← +´˘⍉ cumulative ≤⌜ r÷139968\n'.encode();require(old.count(needle)==1,'Parent lookup inventory differs')
    bins=old.replace(needle,'  indices ← cumulative ⍋ r÷139968\n'.encode())
    needle='  seed ↩ ¯1⊑r\n'.encode();require(bins.count(needle)==1,'Parent seed update differs')
    safe=bins.replace(needle,'  seed ↩ {0<≠𝕩? ¯1⊑𝕩; seed} r\n'.encode())
    for (name,digest),content in zip(SOURCES.items(),[old,bins,safe]):
        require(evidence.check(dict(path=BASE+'sources/'+name+'.bqn',sha256=digest)).read_bytes()==content,'Unreviewed source change')
    return old.decode(),safe.decode()


def check_ownership(evidence,ref):
    receipt=evidence.document(ref)
    require(receipt.get('schema')=='bqn-fasta-source-ownership-review.v1' and receipt.get('source')==SOURCE
        and receipt.get('source_sha256')==SOURCE_SHA and receipt.get('independent_review_approved') is True
        and receipt.get('application_loc')==24 and receipt.get('physical_loc')==24 and receipt.get('retained_rule_proposed_loc')==24,
        'Exact-source24/24 approval missing')
    require(receipt.get('policy')=='application-loc-v1 / retained BQN physical-plus-packed-statements','Wrong retained count policy')
    old,new=check_sources(evidence);lines=new.splitlines();ledger=receipt['line_ledger']
    require(len(ledger)==len(lines) and all(row['line']==i+1 and row['source_text']==text for i,(row,text) in enumerate(zip(ledger,lines))),'Stale owner ledger')
    for row,line in zip(ledger,lines):
        significant=bool(line.strip()) and not line.lstrip().startswith('#')
        require(row['significant'] is significant and type(row['retained_rule_units']) is int
            and row['retained_rule_units']==int(significant) and len(row['retained_rule_owners'])==int(significant),'Owner units differ')
    require(sum(row['retained_rule_units'] for row in ledger)==24,'Source owner sum differs')
    policy=receipt['policies']['retained']
    for key in ['source','saved_audit']:evidence.check(dict(path=policy[key],sha256=policy[key+'_sha256']))
    parent=next(row for row in load(evidence.root/policy['saved_audit'])['rows'] if row['file']=='fasta.bqn')
    require(parent['sha256']==PARENT_SHA and parent['physical_loc']==parent['normalized_loc']==24 and parent['expansions']==[]
        and receipt['baseline_comparison']==dict(source=PARENT_SOURCE,source_sha256=PARENT_SHA,canonical_retained_loc=24,physical_loc=24,retained_expansions=[]),'Historical count differs')
    require(receipt['source_delta']['unified_diff']==''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=PARENT_SOURCE,tofile=SOURCE)),'Reviewed source delta differs')
    require(receipt['required_work']==dict(status='static-review-only-not-executed',naive_lcg_updates_full=200000000,full_n=25000000,
        original_floating_probabilities_and_division=True,unscaled_f64_binary_search=True,cached_random_period=False,new_native_helper=False,empty_input_seed_preserved=True),'Required-work source review differs')
    return receipt


def check_producer_plan(evidence,ref):
    require(ref['sha256']==EXECUTION_PLAN_SHA,'Unreviewed execution plan');plan=evidence.document(ref)
    require(plan.get('schema')=='bqn-fasta-bins-execution-plan.v1' and plan.get('status')=='PREPARED-NO-EXECUTION'
        and plan.get('full')==FULL and plan.get('full_sources')==FULL_SOURCES and plan.get('bounded_sources')==list(SOURCES)
        and plan.get('samples')==3 and plan.get('order_seed')==20261020 and plan.get('required_work')==WORK
        and plan.get('timing_boundary')==TIMING_BOUNDARY and plan.get('common_mutex')=='/tmp/mech-clbg-timing.lock'
        and plan.get('runtime_dependencies')==[FFI] and plan.get('chart_admission') is False,'Wrong execution plan/work')
    require(plan['parent']==dict(path=PARENT_SOURCE,sha256=PARENT_SHA) and plan['runtime']==dict(path=shared.RUNTIME,sha256=shared.RUNTIME_SHA)
        and plan['runtime_commit']==shared.COMMIT and plan['controller']==dict(path=REFS['controller'],sha256=CONTROLLER_SHA)
        and plan['process_controller']==dict(path=REFS['process_controller'],sha256=PROCESS_SHA)
        and plan['source_proposal']==dict(path=REFS['source_proposal'],sha256=PROPOSAL_SHA)
        and plan['sources']=={name:dict(path=BASE+'sources/'+name+'.bqn',sha256=digest) for name,digest in SOURCES.items()},'Execution source/runtime pins differ')
    lookup=plan['exhaustive_lookup']
    require(lookup['source']==dict(path=REFS['lookup'],sha256=LOOKUP_SHA) and lookup['normalized_states']==139968
        and lookup['probability_vectors']==2 and lookup['expected']==LOOKUP_OUTPUT and lookup['timing_admissible'] is False,'Missing exhaustive lookup domain')
    corpus=evidence.document(dict(path=shared.CORPUS,sha256=shared.CORPUS_SHA))
    cases=sorted((row for row in corpus['cases'] if row['benchmark']=='fasta'),key=lambda row:row['n'])
    require([row['n'] for row in cases]==NS and cases==plan['bounded_cases'],'Incomplete independent cases')
    refs=[]
    for case in cases:
        require(case['expected_exit']==0 and case['validation']=='exact-complete-bytes','Wrong corpus validation')
        for key in ['stdin','expected']:
            record={**case[key],'path':str(Path(shared.CORPUS).parent/case[key]['path'])};evidence.check(record)
            refs.append({key:record[key] for key in ['path','sha256']})
    require(refs==plan['reference_files'],'Changed reference inventory')
    return plan


def expected_pins(plan):
    refs=[plan[key] for key in ['source_proposal','controller','process_controller','review','instructions','parent','runtime','runtime_build','corpus']]
    refs += [dict(path=REFS['producer_plan'],sha256=EXECUTION_PLAN_SHA),plan['exhaustive_lookup']['source']]+list(plan['sources'].values())+plan['reference_files']+plan['runtime_dependencies']
    return {row['path']:row['sha256'] for row in refs}


def check_process(evidence,row,directory,expected,recorded,additions,known=False,archive_full=False,local_artifacts=False):
    seconds=row.get('elapsed_seconds')
    require(type(seconds) in (int,float) and math.isfinite(seconds) and seconds>0 and type(row.get('pid')) is int and row['pid']>0
        and row.get('timed_out') is False and row.get('started_utc') and row.get('finished_utc')
        and row.get('qualification_valid') is True and row.get('output_valid') is (not known),'Failed/nonfinite process')
    require(row['exit_code']==(1 if known else 0) and (row['stderr']['bytes']>0 if known else row['stderr']['bytes']==0),'Unexpected exit/diagnostics')
    require(row['stdout']['bytes']==expected['bytes'] and row['stdout']['sha256']==expected['sha256'],'Wrong complete output record')
    for stream in ['stdout','stderr']:
        require(relative(evidence.root,row[stream]['path'],recorded)==directory+'/'+stream+'.bin','Wrong recorded stream path')
        record={**row[stream],'path':directory+'/'+stream+'.bin'}
        if stream=='stdout' and archive_full:
            if local_artifacts:evidence.check(record)
        else:evidence.check(record)
    raw=evidence.document(pin(evidence.root,directory+'/process.json'))
    require(raw=={key:value for key,value in row.items() if key not in additions},'Raw process receipt differs')
    shared.check_power(row['power_before']);shared.check_power(row['power_after'])


def check_execution(evidence,ref,mode,producer,recorded,local_artifacts=False):
    report=evidence.document(ref)
    require(report.get('schema')=='bqn-fasta-bins-execution.v1' and report.get('mode')==mode and report.get('status')=='PASSED'
        and report.get('active') is None and report.get('pins_unchanged') is True and report.get('chart_admission') is False
        and report.get('diagnostic_profile') is False and report.get('full_workload') is (mode=='full'),'Incomplete/diagnostic cohort')
    require(report.get('pins')==expected_pins(producer) and report.get('controller_sha256')==CONTROLLER_SHA
        and report.get('process_controller_sha256')==PROCESS_SHA and report.get('runtime_sha256')==shared.RUNTIME_SHA
        and report.get('plan')==dict(path=REFS['producer_plan'],sha256=EXECUTION_PLAN_SHA)
        and report.get('source_commit')==SOURCE_REVISION and recorded_root(report)==recorded
        and report.get('required_work')==WORK and report.get('timing_boundary')==TIMING_BOUNDARY,'Cohort source/runtime/work differs')
    require(type(report.get('common_mutex_inode')) is int and report['common_mutex_inode']>0 and report.get('started_utc') and report.get('finished_utc'),'Missing common lock/dates')
    require(report.get('bounded_prerequisite')==(pin(evidence.root,REFS['bounded']) if mode=='full' else None),'Wrong bounded prerequisite')
    directory=str(Path(ref['path']).parent)
    for name,digest in SOURCES.items():evidence.check(dict(path=directory+'/sources/'+name+'.bqn',sha256=digest))
    for path,digest in [('controllers/run_serial.py',CONTROLLER_SHA),('controllers/lean_run.py',PROCESS_SHA),('tests/lookup-equivalence.bqn',LOOKUP_SHA),('execution-plan.json',EXECUTION_PLAN_SHA)]:
        evidence.check(dict(path=directory+'/'+path,sha256=digest))
    for path,digest in report['pins'].items():
        if path==shared.RUNTIME or Path(path).is_absolute():
            if local_artifacts:require(sha(evidence.root/path)==digest,'Changed local runtime/dependency')
        else:evidence.check(dict(path=path,sha256=digest))
    if mode=='bounded':
        lookup=report.get('lookup_qualification');require(isinstance(lookup,dict) and lookup.get('timing_admissible') is False
            and lookup.get('qualification')=='exhaustive-lookup' and lookup['command']==[str(Path(recorded)/shared.RUNTIME),str(Path(recorded)/REFS['lookup'])]
            and lookup['stdin']=='/dev/null','Missing/non-exhaustive lookup qualification')
        check_process(evidence,lookup,directory+'/exhaustive-lookup',LOOKUP_OUTPUT,recorded,
            {'qualification','qualification_valid','output_valid','timing_admissible','power_before','power_after'})
    else:require(report.get('lookup_qualification') is None,'Qualification mixed into full timing')
    schedule=[(n,1,'n-'+str(n)) for n in NS] if mode=='bounded' else [(25000000,sample,'full-'+str(sample)) for sample in [1,2,3]]
    rng=random.Random(20261020);orders=[]
    for n,sample,_ in schedule:
        names=list(SOURCES) if mode=='bounded' else FULL_SOURCES.copy();rng.shuffle(names);orders.append(dict(n=n,sample=sample,sources=names))
    require(report.get('orders')==orders,'Shuffled round order differs')
    identities=[(n,sample,case,name) for (n,sample,case),order in zip(schedule,orders) for name in order['sources']]
    rows=report.get('cases',[])
    require([(row.get('n'),row.get('sample'),row.get('case'),row.get('source')) for row in rows]==identities,'Missing/duplicated case or round')
    additions={'source','n','sample','case','qualification_valid','output_valid','known_control_failure','source_sha256','runtime_sha256','power_before','power_after'}
    failures=[]
    for row in rows:
        n,name=row['n'],row['source'];known=mode=='bounded' and n==0 and name in ['parent-faithful','bins-only']
        require(row['command']==[str(Path(recorded)/shared.RUNTIME),str(Path(recorded)/(BASE+'sources/'+name+'.bqn')),str(n)]
            and row['source_sha256']==SOURCES[name] and row['runtime_sha256']==shared.RUNTIME_SHA
            and row['known_control_failure'] is known,'Wrong process command/source/control identity')
        if mode=='full':expected=FULL;require(row['stdin']=='/dev/null','Wrong full stdin')
        else:
            case=next(case for case in producer['bounded_cases'] if case['n']==n)
            require(relative(evidence.root,row['stdin'],recorded)==str(Path(shared.CORPUS).parent/case['stdin']['path']),'Wrong recorded bounded input')
            expected=producer['known_control_zero_failure']['expected_partial_stdout'] if known else case['expected']
        check_process(evidence,row,directory+'/'+row['case']+'-'+name,expected,recorded,additions,known,mode=='full',local_artifacts)
        if known:failures.append(dict(source=name,n=0,exit_code=1))
    if mode=='bounded':require(report.get('complete_candidate_all_16_passed') is True and report.get('known_control_failures')==failures,'Control failure/candidate coverage differs')
    else:
        samples={name:[row['elapsed_seconds'] for row in rows if row['source']==name] for name in FULL_SOURCES}
        require(report.get('samples')==samples and report.get('medians')=={name:statistics.median(values) for name,values in samples.items()}
            and report.get('sample_sd_seconds')=={name:statistics.stdev(values) for name,values in samples.items()},'Stale sample aggregation')
    return report


def reconcile(root=ROOT,local_artifacts=True):
    evidence=shared.Evidence(root);root=evidence.root;plan=load(root/PLAN)
    require(plan==make_plan(root) and plan['source']==dict(path=SOURCE,sha256=SOURCE_SHA),'Stale admission plan')
    for ref in plan['evidence'].values():evidence.check(ref)
    require(plan['evidence']['shared_helpers']['sha256']==SHARED_SHA and all(plan['evidence'][label]['sha256']==digest for label,digest in REPORT_HASHES.items()),'Changed frozen helper/report')
    producer=check_producer_plan(evidence,plan['evidence']['producer_plan']);ownership=check_ownership(evidence,plan['evidence']['ownership'])
    require(producer['runtime_build']==plan['evidence']['runtime_build'],'Changed runtime receipt')
    build=shared.check_build(evidence,plan['evidence']['runtime_build'],local_artifacts,plan['recorded_execution_root'])
    bounded=check_execution(evidence,plan['evidence']['bounded'],'bounded',producer,plan['recorded_execution_root'],local_artifacts)
    full=check_execution(evidence,plan['evidence']['full'],'full',producer,plan['recorded_execution_root'],local_artifacts)
    require(bounded['common_mutex_inode']==full['common_mutex_inode'],'Different common lock identities')
    selected=[copy.deepcopy(row) for row in full['cases'] if row['source']=='bins-empty-safe'];samples=[row['elapsed_seconds'] for row in selected]
    require(statistics.median(samples)<full['medians']['parent-faithful'],'Selected candidate is not the lower retained matched median')
    for row in selected:row.update(producer_report=plan['evidence']['full'],producer_plan=plan['evidence']['producer_plan'])
    program=dict(key=KEY,id=KEY.split(':')[1],original_program_key=PARENT,source_sha256=SOURCE_SHA,loc=24,physical_loc=24,
        samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=statistics.stdev(samples),
        command=selected[0]['command'],sample_execution_metadata=selected,build_command=build['flags'],build_cwd=shared.BASE+'.build/CBQN')
    large=[dict(path=relative(root,row['stdout']['path'],plan['recorded_execution_root']),bytes=row['stdout']['bytes'],sha256=row['stdout']['sha256']) for row in full['cases']]
    excluded={row['path'] for row in large}
    artifacts=[dict(path=path,sha256=digest) for path,digest in sorted(evidence.fingerprints.items()) if '/.build/' not in path and path not in excluded]
    return dict(schema='bqn-fasta-admission-results.v1',status='RECONCILED',plan=pin(root,PLAN),evidence=plan['evidence'],programs=[program],
        recorded_at=full['finished_utc'],recorded_execution_root=plan['recorded_execution_root'],new_observations=3,historical_data_preserved=True,
        full_workload_n=25000000,matched_candidate_medians=full['medians'],matched_control_speedup=full['medians']['parent-faithful']/program['median_seconds'],
        selection=plan['selection'],source_count_review=ownership,required_work=dict(status='source-reviewed-with-exhaustive-lookup-bounded-and-full-output',**WORK),
        full_stdout_archive=dict(retained_in_durable_repository=False,files=large,
            verification='Original native attempts validated complete bytes/hash. Local prepare rehashes present full stdout; durable archived replay checks pinned raw process records and does not claim to rehash unavailable full bytes.'),
        bounded_validation=dict(candidate_cases=16,all_three_sources_cases=48,exhaustive_normalized_states=139968,probability_vectors=2,
            known_original_zero_failures_preserved=True,bounded_streams_rehashed=True),author_context=AUTHOR_CONTEXT,
        toolchains=dict(bqn=dict(version=build['version'],commit=shared.COMMIT,sha256=shared.RUNTIME_SHA)),
        runtime_details=dict(build=plan['evidence']['runtime_build'],restoration_limitation=build['restoration_limitation'],application_imports=[],linked_runtime_dependencies=[FFI]),
        runtime_environment=dict(PATH='/usr/bin:/bin',LC_ALL='C',LANG='C',TZ='UTC'),timing_boundary=TIMING_BOUNDARY,artifacts=artifacts)


def authorship_record(parent,results,evidence):
    result=copy.deepcopy(parent['authorship'])
    result.update(kind='ai-adapted',label='AI adapted · retained faithful predecessor',source_sha256=[SOURCE_SHA],origin_status='unresolved',
        parent_programs=[PARENT],parent_sources=[dict(program_key=PARENT,relationship='local predecessor',**ref) for ref in parent['authorship'].get('retained_sources',[])],
        retained_sources=[dict(source_sha256=SOURCE_SHA,url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)],
        ai=dict(tool=AUTHOR_CONTEXT['tool'],models=[],model_family=AUTHOR_CONTEXT['model_family'],exact_model=None,status='family-identified-exact-model-unverified',
            matched_source_files=[SOURCE_SHA],total_source_files=1,evidence=[evidence['plan'],evidence['results']]),
        local_change_license=dict(status='suite-license',id='Apache-2.0',evidence='LICENSE',scope='New local changes only; inherited terms remain unresolved.'),
        evidence=[evidence['plan']['path'],evidence['results']['path'],evidence['ownership']['path']])
    return result


def bound_authorship(data,profile,root=ROOT):
    root=Path(root);detail=profile.get('source_provenance_record') or {};results=load(root/RESULTS)
    evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    require(profile.get('key')==KEY and profile.get('files')==[SOURCE_SHA] and detail.get('kind')=='suite-authored-optimization'
        and detail.get('source_sha256')==SOURCE_SHA and detail.get('original_program_key')==PARENT and detail.get('admission')==evidence['results']
        and detail.get('author_context')==AUTHOR_CONTEXT and results.get('schema')=='bqn-fasta-admission-results.v1' and results.get('status')=='RECONCILED'
        and results.get('plan')==evidence['plan'] and results.get('author_context')==AUTHOR_CONTEXT
        and results['programs'][0]['key']==KEY and results['programs'][0]['source_sha256']==SOURCE_SHA and sha(root/SOURCE)==SOURCE_SHA
        and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest()==SOURCE_SHA,'Unbound FASTA source/authorship admission')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT],results,evidence)


def append_catalog(before,root=ROOT):
    root=Path(root).resolve();results=load(root/RESULTS)
    require(results==reconcile(root,local_artifacts=False),'Stale reconciled FASTA results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'] and 'bqn_fasta_audit' not in before,'FASTA candidate already admitted')
    data=copy.deepcopy(before);parent=before['programs'][PARENT];r=results['programs'][0]
    require(parent['files']==[PARENT_SHA] and parent['loc']==parent['physical_loc']==24,'Historical FASTA parent changed')
    bench=next(b for b in data['benchmarks'] if b['key']=='fasta')
    require(r['loc']>=bench['baseline_loc'] and r['median_seconds']>=bench['baseline_seconds'],'New global baseline needs separate normalization review')
    require(SOURCE_SHA not in data['files'],'Source already cataloged');evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    data['files'][SOURCE_SHA]=dict(name='bins-empty-safe.bqn',path=SOURCE,archive_path=SOURCE,sha256=SOURCE_SHA,code=(root/SOURCE).read_text())
    row=copy.deepcopy(parent)
    for field in ['publication_record','timing_measurement','timing_correction','aliased_sample_source','source_alias_of','source_alias_note','loc_expansions','source_accounting','authorship','source_metrics']:row.pop(field,None)
    row.update(key=KEY,id=r['id'],receipt_key=r['id'],files=[SOURCE_SHA],loc=24,physical_loc=24,loc_metric='assignment-normalized',
        seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],x=24/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],
        formatted_loc=None,formatted_x=None,formatted_loc_status='pending',formatted_loc_complete=False,formatted_loc_evidence={},
        report=RESULTS,report_sha256=evidence['results']['sha256'],source_report=evidence['ownership']['path'],loc_report=evidence['ownership']['path'],
        command=r['command'],runtime_arguments=['25000000'],build_command=r['build_command'],build_cwd=str(Path(results['recorded_execution_root'])/r['build_cwd']),
        cwd=results['recorded_execution_root'],execution_mode='interpreter',binary_sha256=shared.RUNTIME_SHA,runtime_sha256=shared.RUNTIME_SHA,
        native_observations=3,timing_alias_of=None,sample_execution_metadata=r['sample_execution_metadata'],original_program_key=PARENT,
        retained_source_revision=SOURCE_REVISION,local_adaptation=True,distinct_optimization_claimed=True,
        source_provenance='Suite-authored floating-Bins/empty-record adaptation of retained faithful BQN FASTA; predecessor origin and inherited terms remain unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization',original_program_key=PARENT,source_sha256=SOURCE_SHA,admission=evidence['results'],origin_status='inherited-unresolved',author_context=AUTHOR_CONTEXT),
        runtime_policy='CBQN commit '+shared.COMMIT+'; exact uninstrumented rebuilt release; single-process source; ordinary f64 Bins primitive',
        runtime_support='Existing CBQN runtime only; no application imports, FFI helper or benchmark executor.',runtime_environment=results['runtime_environment'],timing_boundary=TIMING_BOUNDARY,
        timing_summary='Three matched whole-process observations; modest approximately4% gain in this cohort. All samples retained; no major or global optimality claim. Large full stdout is local-only; archived proof uses native raw hash/length records.',
        algorithm=dict(strict=True,status='required-work-reviewed',native_benchmark_kernel=False,
            reason='Every one of200,000,000 naive LCG updates and original floating division/probability value remains. Bins performs native floating binary search; no scaling, integer cutoff, cached period or state-to-letter table. Empty records preserve the seed.',
            full_work=dict(n=25000000,random_nucleotides=200000000,lcg_updates=200000000),evidence=evidence['ownership']),
        source_accounting=dict(policy='application-loc-v1',application_loc=24,physical_loc=24,evidence=evidence['ownership']['path'],review_sha256=evidence['ownership']['sha256'],
            qualification='Root-approved exact-source24/24 extension of retained BQN physical-plus-packed-statements rule; no native parser certificate.',files=[]),
        file_roles={SOURCE_SHA:dict(role='application',included_in_application_loc=True,normalized_loc=24,physical_loc=24)},
        full_output_validation=dict(all_three_samples_passed=True,evidence=evidence['full'],archive_scope='Recorded complete native hash/length; full stdout bytes are not durable artifacts.'),
        chart_admission=dict(historical_reports_unchanged=True,**evidence),
        measured_backend=dict(key='bqn',execution='interpreter',label='BQN (CBQN)',verified=True,evidence=dict(verified=True,report=RESULTS,
            report_sha256=evidence['results']['sha256'],command=r['command'],source_sha256=[SOURCE_SHA],runtime_receipt=dict(verified=True,report=RESULTS,
                report_sha256=evidence['results']['sha256'],field='/toolchains/bqn/version',value=results['toolchains']['bqn']['version'],value_encoding='literal-saved-string'))))
    row['authorship']=authorship_record(parent,results,evidence);data['programs'][KEY]=row;data['program_inventory'][KEY]=copy.deepcopy(row)
    group=next(g for g in bench['groups'] if g['language']=='bqn');group['programs'].append(KEY)
    candidates=[data['programs'][key] for key in group['programs']]
    group['fast']=min(candidates,key=lambda p:(p['seconds'],p['loc'],p['key']))['key'];group['small']=min(candidates,key=lambda p:(p['loc'],p['seconds'],p['key']))['key']
    for summary in data['reference_summary']:
        if summary['lang']!='bqn':continue
        groups=[g for b in data['benchmarks'] for g in b['groups'] if g['language']=='bqn']
        for kind in ['fast','small']:
            selected=[data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind]=dict(x=statistics.geometric_mean(p['x'] for p in selected),y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*evidence.values(),*results['artifacts'],dict(path=SOURCE,sha256=SOURCE_SHA)]:data['archive_paths'][ref['path']]=ref['path']
    data['bqn_fasta_audit']=dict(schema='bqn-fasta-catalog-extension.v1',appended_programs=[KEY],evidence=evidence,measured_at=results['recorded_at'],
        new_observations=3,source_files_added=1,old_profiles_unchanged=True,old_baselines_unchanged=True)
    for pool in ['programs','program_inventory','files','archive_paths']:require(all(data[pool][key]==old for key,old in before[pool].items()),'Historical '+pool+' changed')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--apply',action='store_true')
    parser.add_argument('--expected-before-sha256');parser.add_argument('--expected-prepared-sha256');args=parser.parse_args()
    require(args.prepare!=args.apply,'Choose exactly one of --prepare/--apply');catalog=ROOT/'data/benchmarks.json'
    if args.prepare:
        before_bytes=catalog.read_bytes();before=json.loads(before_bytes,object_pairs_hook=shared.no_duplicates,parse_constant=lambda value:require(False,'Nonfinite JSON:'+value))
        before_sha=hashlib.sha256(before_bytes).hexdigest();shared.write(ROOT/PLAN,make_plan());shared.write(ROOT/RESULTS,reconcile())
        shared.write(ROOT/PREPARED,append_catalog(before));require(sha(catalog)==before_sha,'Canonical changed during preview preparation')
        print(dict(before_sha256=before_sha,prepared_sha256=sha(ROOT/PREPARED),results_sha256=sha(ROOT/RESULTS),canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256,'Apply needs reviewed hashes')
        require(sha(catalog)==args.expected_before_sha256 and sha(ROOT/PREPARED)==args.expected_prepared_sha256,'Reviewed before/preview identity differs')
        after=append_catalog(load(catalog));require(encoded(after)==(ROOT/PREPARED).read_bytes(),'Preview does not reproduce')
        require(sha(catalog)==args.expected_before_sha256,'Canonical changed during reconciliation');shared.write(catalog,after)
        print('Added one qualified BQN FASTA Bins source; historical records retained.')


if __name__=='__main__':main()
