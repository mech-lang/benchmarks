"""Reconcile five completed GNU APL workloads from their retained old schemas.

No producer, interpreter or benchmark is executed. Historical report-only
control44 stays report-only; sample84 keeps its literal kernel exit provenance.
The separate file phase replays inherited pins under the common timing mutex.
"""
from contextlib import contextmanager
from datetime import datetime
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
HIST=Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
COHORT=HIST/'r-apl-uiua-comparison/20261011'
REV=COHORT/'uiua-fann-compact-v5/controller_rev2'
REC=HIST/'continuation/apl-sample84-recovery-v1/full-owner'
OBSERVER=HIST/'continuation/jobs/apl-sample84-kqueue-observer-v1'
PACKET=ROOT/'experiments/apl/retained-native-v1'
INDEX=PACKET/'inputs-v1.json'
INDEX_SHA='efebf6f227e705786619457f150c338cadf97c60469ded31a3d19c3967854963'
LOCK=Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE=79859134
BENCHES={'nbody':50000000,'mandelbrot':16000,'knucleotide':25000000,'fannkuchredux':12,'fasta':25000000}
POWER={'source':'AC Power','low_power_mode':0}
KEY='fannkuchredux:fannkuchredux-apl-compact'
CONTROL='fannkuchredux:mech-control-for-apl'
FASTA='fasta:fasta-apl-affine-hoisted-optimized-v3'
TREE='binarytrees:binarytrees-apl-compact'
REFERENCES={
 'mandelbrot':(32000015,'609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'),
 'knucleotide':(259,'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'),
 'fannkuchredux':(29,'4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'),
 'fasta':(254166745,'3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
 'binarytrees':(455,'341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1')}
LEDGER={'sample','attempt_number','continuation_manifest_sha256'}
SUPERVISOR={'attempt','round','sampler_wait_status','result_path','supervised_native_group',
 'supervisor_remaining_members','qualification_checks','qualified','supervisor_result_path'}
RECOVERY_FIELDS={'sampler_wait_status_origin','native_wait_status_origin','recovered_after_supervisor_exit'}


def require(value,message):
    if not value:raise ValueError(message)


def same(left,right,message):
    require(json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False),message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'Duplicate JSON key');result[key]=value
        return result
    def constant(value):raise ValueError('Nonfinite JSON: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def positive(value):return type(value) in (int,float) and math.isfinite(value) and value>0


def read_ref(ref):
    path=ROOT/ref['path'];require(path.is_relative_to(ROOT) and '..' not in path.parts,'Unsafe retained path')
    raw=path.read_bytes();require(len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'Retained evidence changed: '+ref['path'])
    return raw


def metadata():
    """Small saved JSON/source-only phase; never hashes a runtime closure."""
    raw=INDEX.read_bytes();require(sha(raw)==INDEX_SHA,'Reviewed metadata inventory changed')
    index=strict_json(raw)
    documents={key:strict_json(read_ref(ref)) for key,ref in index['documents'].items()}
    receipts={int(n):{key:strict_json(read_ref(ref)) for key,ref in item.items()} for n,item in index['receipts'].items()}
    sources={key:read_ref(ref) for key,ref in index['sources'].items()}
    return index,documents,receipts,sources


def consumer(index):
    """Only the immutable independent historical consumer is loaded."""
    name='archive/site/explorer/r_apl_uiua_data.py';raw=read_ref(index['artifacts'][name])
    spec=importlib.util.spec_from_file_location('apl_retained_original_fingerprint',ROOT/name)
    module=importlib.util.module_from_spec(spec);exec(compile(raw,str(ROOT/name),'exec'),module.__dict__)
    return module


def twenty_checks(a,row,reference):
    """Independent replay of the exact frozen remaining_owner twenty gates."""
    native=a.get('supervised_native_group');n=21 if row['benchmark']=='binarytrees' else BENCHES[row['benchmark']]
    return dict(sampler_exited_normally=a.get('sampler_wait_status')==0,
      authoritative_native_group_received=native is not None,
      native_inherited_common_mutex=native is not None and native.get('inherited_common_mutex') is True,
      native_exited_normally=a.get('exit_status')==0,no_execution_error=not a.get('error'),
      no_wrapper_integrity_error=not any(a.get(k) for k in ('sampler_failure','sampler_error','registration_error','supervisor_error','supervisor_pin_failure')),
      no_resource_violation=not a.get('resource_violation'),no_resource_monitor_errors=not a.get('resource_monitor_errors'),
      no_compiler_power_monitor_errors=not a.get('monitor_errors'),no_monitor_finish_error=not a.get('monitor_finish_error'),
      no_execute_cleanup_error=not a.get('cleanup_error'),no_remaining_execute_group=not a.get('remaining_group_members'),
      no_supervisor_cleanup=not a.get('supervisor_cleanup'),no_supervisor_remaining_group=not a.get('supervisor_remaining_members'),
      valid_environment=a.get('valid_environment') is True,actual_full_workload=a.get('full_workload') is True and a.get('workload_n')==n,
      exact_command_and_group=native is not None and native['command']==a.get('command')==[v.replace('{n}',str(n)) for v in row['command']],
      complete_output_reference_match=a.get('validation',{}).get('reference_match') is True,
      complete_output_bytes_and_hash=reference is None or (a.get('stdout_bytes'),a.get('stdout_sha256'))==reference,
      pins_unchanged=a.get('pins_unchanged_at_end') is True)


def receipt(a,row,records,fingerprint,failed=False):
    n=a['attempt_number'];bench=row['benchmark'];size=21 if bench=='binarytrees' else BENCHES[bench]
    require(type(n) is int and 44<=n<=87,'Unexpected native attempt')
    for field in ('key','id','benchmark','language','source_sha256','cwd'):
        same(a[field],row[field],'Native identity changed: '+field)
    same(a['runtime_environment'],row.get('runtime_environment',{}),'Recorded runtime overrides differ')
    same(a['execution_fingerprint'],fingerprint(row),'Exact recorded execution fingerprint differs')
    same(a['command'],[v.replace('{n}',str(size)) for v in row['command']],'Executed argv differs')
    require(a['workload_n']==size and a['full_workload'] is True and positive(a['seconds']),'Invalid full workload or elapsed time')
    require(a['timeout_seconds']==14400 and a['maximum_rss_mib']==10240,'Historical bounds differ')
    require(a['power_at_start']==a['power_at_end']==POWER and a['valid_environment'] is True,'Power/environment mismatch')
    require(type(a['exit_status']) is int and a['exit_status']==0 and a['resource_violation'] is None,'Native exit/resource failure')
    for field in ('monitor_errors','resource_monitor_errors','remaining_group_members','competing_compilers','power_changes'):
        same(a[field],[],'Historical monitor/cleanup failure')
    require(not any(a.get(k) for k in ('monitor_finish_error','cleanup_error','supervisor_cleanup','supervisor_error')),'Cleanup/integrity failure')
    require(positive(a['peak_process_group_rss_kib']) or a['peak_process_group_rss_kib']==0,'Invalid sampled RSS')
    require(a['peak_process_group_rss_kib']<=10240*1024,'RSS ceiling exceeded')
    begin,end=map(datetime.fromisoformat,(a['started_at'],a['finished_at']))
    require(begin<end and (end-begin).total_seconds()+0.001>=a['seconds'],'Native elapsed outside recorded interval')
    if n==44:
        require(set(a).isdisjoint(SUPERVISOR|RECOVERY_FIELDS) and n not in records and not failed,'Historical control44 gained invented supervisor fields')
    else:
        pair=records[n];raw,supervised=pair['raw'],pair['supervisor']
        same({k:v for k,v in a.items() if k not in LEDGER},supervised,'Ledger differs from immutable supervisor')
        extras=SUPERVISOR|(RECOVERY_FIELDS if n==84 else set())
        same({k:v for k,v in supervised.items() if k not in extras},raw,'Supervisor changed original sampler fields')
        native=a['supervised_native_group']
        require(type(native['pid']) is type(native['pgid']) is int and native['pid']==native['pgid']>0
            and native['type']=='native-group-started','Missing native PGID registration')
        require(type(a['sampler_wait_status']) is int and a['sampler_wait_status']==0,'Sampler did not exit normally')
        same(a['supervisor_remaining_members'],[],'Supervisor left native members')
        checks=twenty_checks(a,row,REFERENCES.get(bench));same(a['qualification_checks'],checks,'Recorded twenty-gate decision differs')
        require(len(checks)==20 and a['qualified'] is (not failed),'Native qualification disposition changed')
        if not failed:require(all(type(v) is bool and v for v in checks.values()),'Native twenty-gate replay failed')
        else:
            allowed={'no_execution_error','complete_output_reference_match','complete_output_bytes_and_hash'}
            require({k for k,v in checks.items() if not v}==allowed,'Failed attempt has an unrelated integrity failure')
    if failed:
        require(n in (58,75) and a['error_type']=='OutputValidationError' and a['stdout_bytes']==0
            and a['stdout_sha256']==sha(b'') and not a.get('validation'),'Failure changed into successful output')
        if n==75:require('WS FULL' in a['stderr'],'Original tree workspace failure absent')
    else:
        require(not a.get('error') and a['validation']['reference_match'] is True,'Output not accepted')
        same((a['stdout_bytes'],a['stdout_sha256']),(a['validation']['bytes'],a['validation']['sha256']),'Output bytes/hash disagree')
        if bench=='nbody':
            v=a['validation'];require(v['tolerance']==1e-8 and len(v['energies'])==2,'Wrong N-body reference policy')
            require(all(type(x) in (int,float) and math.isfinite(x) and abs(x-y)<=1e-8 for x,y in zip(v['energies'],[-0.169075164,-0.169059907])),'N-body energies differ')
        else:same((a['stdout_bytes'],a['stdout_sha256']),REFERENCES[bench],'Canonical output reference differs')
    return begin,end


def recovered84(d,records):
    old,admission,registered,terminal=d['old_report'],d['admission'],d['registered'],d['observer']
    require(old['status']=='partial' and len(old['attempts'])==83 and d['old_status']['status']=='running','Original interrupted owner state changed')
    active=old['active'];same(registered['saved_active'],active,'Observer registered another active native attempt')
    require(active['attempt']==84 and active['sample']==active['round']==2 and active['key']==KEY
        and active['sampler_pid']==68659 and active['native']['pid']==active['native']['pgid']==68666,'Recovery identities differ')
    require(registered['status']=='both-live-identities-registered' and registered['observer_pid']==terminal['observer_pid']==83359
        and registered['note_exit']==0x80000000 and registered['note_exitstatus']==0x04000000,'Kernel observer registration differs')
    require(terminal['status']=='both-kernel-exit-statuses-captured-awaiting-raw-pin-review'
        and terminal['exit_status_origin']=='Darwin EVFILT_PROC NOTE_EXITSTATUS; not synthetic waitpid','Kernel exit origin differs')
    for item in (registered,terminal):
        require(item['signals_sent']==item['benchmarks_started']==0 and item['debugger_attached'] is item['qualification_granted'] is False
            and not item.get('error') and not item.get('failure_drain_error'),'Observer disturbed the subject or failed')
    require(set(terminal['exit_events'])=={'68659','68666'},'Missing exact two exit events')
    for pid,event_number,birth in [(68666,1,'Tue Oct 13 01:11:27 2026'),(68659,2,'Tue Oct 13 01:11:26 2026')]:
        event=d['exit'+str(pid)];raw=d['event'+str(event_number)]
        same(event,terminal['exit_events'][str(pid)],'Terminal kernel event differs')
        require(registered['identities'][str(pid)].startswith(birth),'Observed process birth differs')
        require(event['raw_event']==str(OBSERVER/f'raw-event-000{event_number}.json'),'Kernel raw event route differs')
        require(type(event['pid']) is type(raw['ident']) is int and event['pid']==raw['ident']==pid,'Kernel event PID differs')
        for field in ('filter','flags','fflags'):
            require(type(event[field]) is type(raw[field]) is int and event[field]==raw[field],'Kernel event flags differ')
        require(event['filter']==-5 and not event['flags']&0x4000 and event['fflags']&0x80000000 and event['fflags']&0x04000000,'Missing literal exit status flags')
        require(type(raw['data']) is type(event['kernel_wait_status']) is int and raw['data']==event['kernel_wait_status']==0
            and event['exited_normally'] is True and event['signalled'] is False and event['exit_code']==0
            and event['signal_number'] is None and event['qualification_granted'] is raw['qualification_granted'] is False,'Kernel exit not normal zero')
    require('apl-after-tree-failure-v1/controller.py' in registered['identities']['68659']
        and 'fannkuchredux.compact.apl -- 12' in registered['identities']['68666'],'Registered process command differs')
    raw=d['raw84'];same(raw,records[84]['raw'],'Original raw84 changed')
    require(raw['seconds']==7797.184570125,'Recovered duration changed')
    expected=copy.deepcopy(raw);native=copy.deepcopy(active['native']);native.pop('identity')
    expected.update(attempt=84,round=2,sampler_wait_status=0,result_path=active['result_path'],supervised_native_group=native,
        supervisor_remaining_members=[],sampler_wait_status_origin='Literal Darwin NOTE_EXITSTATUS kernel event for exact sampler68659; no waitpid call',
        native_wait_status_origin='Literal Darwin NOTE_EXITSTATUS kernel event for exact native68666',recovered_after_supervisor_exit=True)
    expected.update(qualification_checks=twenty_checks(expected,old['programs'][KEY],REFERENCES['fannkuchredux']),qualified=True,
        supervisor_result_path=str(REC/'recovered-084.supervisor.json'))
    same(records[84]['supervisor'],expected,'Recovered supervisor is not the exact additive reconstruction')
    require(admission['status']=='passed-exact-kernel-status-and-original-twenty-gate-replay'
        and admission['already_running_sample_restarted'] is False and admission['old_process_signals_sent']==0
        and admission['fresh_full_processes']==0 and admission['chart_admission'] is False,'Recovery admission changed scope')
    same(admission['literal_kernel_wait_statuses'],{'68659':0,'68666':0},'Recovery statuses differ')
    same(admission['recovered84_checks'],expected['qualification_checks'],'Recovery gate record differs')
    for number in (82,83):same(admission['original82_83_replayed_checks'][str(number)],old['attempts'][number-1]['qualification_checks'],'Prior complete receipt gate differs')
    same(admission['retained_seconds'],[old['attempts'][81]['seconds'],raw['seconds']],'Retained timings changed')
    require(datetime.fromisoformat(active['started_at'])<=datetime.fromisoformat(raw['started_at'])
        <datetime.fromisoformat(registered['registered_at'])
        <datetime.fromisoformat(raw['finished_at'])<=datetime.fromisoformat(d['exit68659']['observed_at']),'Recovery event chronology differs')


def source_work(row,origin,d,inherited,index):
    """Retain the reviewed per-source work and correctness schemas verbatim."""
    for field in ('algorithm','runtime','runtime_sha256','library_support','small_validation',
            'adversarial_validation_status','adversarial_validation','build_status','build_command','execution_mode',
            'adaptations','source_provenance','canonical_constant_correction'):
        same(row.get(field),origin.get(field),'Audited source-work field changed: '+field)
    require(row['algorithm']['strict'] is True and row['algorithm']['native_benchmark_kernel'] is False
        and row['execution_mode']=='interpreted' and row['build_status']=='not-required','Required work delegated or unreviewed')
    command=row['command'];require(command[:2]==[str(COHORT/'run-apl.sh'),'--cc']
        and command[2] in ('1','8') and command[3:5]==['-f',row['source']],'Unreviewed worker ceiling or application invocation')
    runtime=row['runtime'];parallel=runtime['numerical_primitive_parallelism']
    require(parallel['enabled'] is False and parallel['requested_cc_is_ceiling_only'] is True
        and runtime['architecture']=='arm64-apple-darwin','Pinned primitive parallelism scope differs')
    for field in ('proof_source','proof_config'):
        require(inherited.get(parallel[field])==parallel[field+'_sha256'],'Runtime primitive policy evidence omitted')
    small=row['small_validation'];require(small['reference_match'] is True and small.get('passed',True) is True
        and small.get('returncode',0)==0,'Canonical small correctness not accepted')
    adversarial=row['adversarial_validation'];bench=row['benchmark']
    if isinstance(adversarial,list):
        require(row['adversarial_validation_status']=='passed' and len(adversarial)>0
            and all(c['reference_match'] is True and type(c['returncode']) is int and c['returncode']==0 for c in adversarial),
            'Original adversarial source cases not accepted')
    else:
        name='work_'+bench;proof=d[name]
        require(adversarial['passed'] is proof['passed'] is True
            and adversarial['sha256']==index['documents'][name]['sha256']
            and inherited.get(adversarial['report'])==adversarial['sha256'],'Detailed work/correctness report not bound')
        require(all(c['passed'] is True for c in proof['rows']),'Detailed work/correctness case failed')
        if bench=='knucleotide':
            require(row['adversarial_validation_status']=='all-v2-cases-passed'
                and len(proof['rows'])==proof['checks']==48 and proof['benchmark_cases_per_variant']==19
                and proof['generic_map_cases_per_variant']==3 and proof['all_map_cases_per_variant']==2
                and adversarial['scopes']==['benchmark-output','generic-map','all-seven-complete-maps'],
                'Seven-map collision/growth/complete-map proof differs')
        elif bench=='mandelbrot':
            require(len(proof['rows'])==32 and proof['checks']==64 and proof['full_attempts']==0
                and adversarial['per_pixel_work_trace'] is True and adversarial['cases_per_variant']==16
                and all(c['work_trace']['reference_match'] is True for c in proof['rows']),
                'Per-pixel recurrence proof differs')
        elif bench=='fasta':
            require(len(proof['rows'])==adversarial['total_checks']==33 and proof['source_sha256']==row['source_sha256']
                and proof['full_measurements'] is False and proof['planning_only'] is False,
                'Generic affine/cumulative probability proof differs')
        else:raise ValueError('Unexpected detailed work report')
    return dict(qualified=True,qualification_origin='Immutable per-source audited work and retained small/adversarial cases',
        native_benchmark_kernel=False,requested_worker_ceiling=int(command[2]),numerical_primitive_parallelism_enabled=False)


def reconcile(index,d,records,sources):
    """Pure saved-metadata replay; physical closure remains separately required."""
    r,status,manifest,audit,counts=d['report'],d['status'],d['manifest'],d['audit'],d['counts']
    require(r['status']=='partial' and len(r['attempts'])==87 and not r.get('active') and r['sample_count']==3,'Original partial cohort changed')
    require(status['status']=='complete' and status['fresh_full_processes']==status['required_fresh_full_processes']==3
        and status['pins_unchanged_at_end'] is True and status['no_automatic_retry'] is True,'Missing closed recovery terminal')
    require(status['old_sample_signals_sent']==0 and status['original_report_mutated'] is status['original_raw_mutated'] is status['chart_admission'] is False,'Recovery scope changed')
    require(status['manifest_sha256']==index['documents']['manifest']['sha256'] and len(status['retained_input_and_actual_result_pins'])==6388,'Recovery terminal binding differs')
    require(r['source_audit']==str(REV/'apl-argv-v1/full-owner/source-audit-apl-argv.json')
        and r['source_audit_sha256']==index['documents']['audit']['sha256'] and audit['status']=='reviewed','Source audit changed')
    require(r['maximum_rss_mib']==10240 and r['shared_timing_lock']==str(LOCK) and audit['power_required']==POWER,'Original measurement policy differs')
    same(r['protocol'],audit['timing_boundary'],'Timer boundary differs from frozen source audit')
    inherited=status['retained_input_and_actual_result_pins']
    for name in ('manifest','remaining_manifest','argv_manifest','old_manifest','audit'):
        for path,digest in d[name]['pins'].items():
            require(inherited.get(path)==digest,'Inherited native prerequisite omitted or rebound')
    for number,pair in index['receipts'].items():
        a=r['attempts'][int(number)-1]
        for role,field in [('raw','result_path'),('supervisor','supervisor_result_path')]:
            ref=pair[role]
            require(a[field]==ref['recorded_path'] and inherited.get(a[field])==ref['sha256'],'Saved native receipt route or pin differs')
    # Every preceding producer remains immutable; the final report is additive.
    for name,n in [('remaining_before',44),('argv_before',58),('argv_report',75),('tree_before',75),('old_report',83),('before',84)]:
        prior=d[name];require(len(prior['attempts'])==n,'Wrong producer prefix: '+name)
        same(r['attempts'][:n],prior['attempts'],'Prior native ledger changed: '+name)
        same(r['guard_revisions'],prior['guard_revisions'],'Guard migration ancestry changed')
    for key,row in d['old_report']['programs'].items():
        if row['benchmark']!='fannkuchredux':same(r['programs'][key],row,'Recovery changed an unrelated program')
    argv=r['argv_revision']
    extra={'original_report','original_report_sha256','bounded_qualification','bounded_qualification_sha256'}
    same({k:v for k,v in argv.items() if k not in extra},audit['argv_revision'],'Report/audit argv revision disagreement')
    require(argv['original_report_sha256']=='f17725d71bb7886cdee79de7794dd55f399592bbe0695ed7baabcf2a83eb3dd1'
        and argv['bounded_qualification_sha256']==index['documents']['argv_qualification']['sha256'],'Argv revision evidence differs')
    require(argv['key']==FASTA and argv['original_failed_attempt']==58 and argv['sources_changed'] is False
        and argv['original_samples_preserved'] is True,'Wrong command repair scope')
    same(argv['new_command'],argv['old_command']+['--','{n}'],'FASTA repair changed more than missing numeric delivery')
    same(r['programs'][FASTA]['command'],argv['new_command'],'Corrected FASTA command differs')
    require(d['argv_qualification']['status']=='bounded-corrected-command-qualified'
        and len(d['argv_qualification']['attempts'])==11 and d['argv_qualification']['full_performance_runs']==0
        and d['argv_qualification']['sources_changed'] is False,'Corrected argv bounded evidence incomplete')
    recovered84(d,records)
    expected_slots=[dict(sample=2,key=CONTROL),dict(sample=3,key=CONTROL),dict(sample=3,key=KEY)]
    same(manifest['planned_slots'],expected_slots,'Missing-only recovery schedule differs')
    same(d['admission']['missing_slots'],expected_slots,'Recovery admission slot list differs')
    same(status['planned_slots'],expected_slots,'Terminal recovery slot list differs')
    same([dict(sample=a['sample'],key=a['key']) for a in r['attempts'][84:]],expected_slots,'Additional or repeated recovery sample')
    require(r['sample84_recovery']['overall_suite_completion_pending'] is True
        and r['sample84_recovery']['recovered_original_attempt']==84
        and r['sample84_recovery']['fresh_attempts']==3,'Recovery falsely completed the whole suite')
    for name in ('original_report','original_manifest','original_raw84','observer','recovered_supervisor'):
        ref=d['admission'][name]
        require(inherited.get(ref['path'])==ref['sha256'],'Recovery admission dependency omitted')
    for revision in r['guard_revisions']:
        for field in ('prior_report','prior_source_audit'):
            relative='archive/comparisons/'+Path(revision[field]).relative_to(HIST).as_posix()
            require(index['artifacts'][relative]['sha256']==revision[field+'_sha256'],'Guard migration dependency omitted')
    known={row['key']:row for row in audit['programs']+audit['controls']}
    selected=[w for w in d['inventory']['workloads'] if w['language']=='apl']
    require({w['benchmark'] for w in selected}==set(BENCHES),'Changed five-workload inventory')
    expected={row['key']:row for w in selected for role in ('subjects','controls') for row in w[role]}
    require(len(expected)==16 and len(counts['sources'])==9 and len(counts['profiles'])==11
        and counts['canonical_loc_qualified'] is True and counts['formatted_loc_qualified'] is False,'Exact nine-source count admission required')
    owner_counts={row['key']:row for row in counts['profiles']};fingerprint=consumer(index)._execution_fingerprint
    profiles={};used=set();intervals=[]
    for key,wanted in expected.items():
        row=r['programs'][key];origin=known[key]
        for field in ('source','source_sha256','command','binary','binary_sha256','cwd','runtime_environment'):
            same(row.get(field),origin.get(field),'Measured profile differs from source audit')
        same(row.get('timing_alias_of'),wanted['timing_alias_of'],'Alias ownership changed')
        require(row['source_sha256']==wanted['recorded_source_sha256'],'Inventory source identity differs')
        for field in ('source','binary'):
            require(inherited.get(row[field])==row[field+'_sha256'],'Measured source/runtime missing from native closure')
        owner=r['programs'][row.get('timing_alias_of') or key]
        if owner is not row:
            require(not row['attempts'] and not owner.get('timing_alias_of'),'Alias creates native attempts')
            same(fingerprint(row),fingerprint(owner),'Alias execution changed')
            require(row['aliased_sample_source']==owner['key'],'Alias provenance missing')
        indexes=owner['attempts'];observations=[r['attempts'][n-1] for n in indexes]
        require(indexes==[a['attempt_number'] for a in r['attempts'] if a['key']==owner['key']],'Attempt membership differs')
        good=[]
        if owner is row:
            for a in observations:
                number=a['attempt_number'];failed=number==58
                actual=copy.deepcopy(row)
                if failed:actual['command']=argv['old_command']
                intervals.append((number,*receipt(a,actual,records,fingerprint,failed)))
                if not failed:good.append(a);used.add(number)
        else:good=[a for a in observations if not a.get('error')]
        require(len(good)==3 and row['measurement_status']=='measured' and not row.get('full_failure'),'Incomplete selected source/control')
        same(row['samples_seconds'],[a['seconds'] for a in good],'Sample vector differs from native receipts')
        same(row['sample_validation'],[a['validation'] for a in good],'Sample validations differ')
        same(row['full_validation'],good[0]['validation'],'Full output validation differs')
        require(row['median_seconds']==statistics.median(row['samples_seconds'])
            and row['sample_stdev_seconds']==statistics.stdev(row['samples_seconds']),'Statistics differ')
        canonical=None
        work=None
        if row['language']=='apl':
            work=source_work(row,origin,d,inherited,index)
            count=owner_counts[key];canonical=count['canonical_loc'];raw=sources[count['source_identity']]
            require(sha(raw)==row['source_sha256']==count['source']['sha256'] and count['canonical_loc_qualified'] is True
                and count['formatted_loc_qualified'] is False and count['formatted_loc'] is None,'Counted bytes/qualification differ')
            same(count['timing_alias_of'],row.get('timing_alias_of'),'Canonical alias binding differs')
        profiles[key]=dict(benchmark=row['benchmark'],language=row['language'],source=row['source'],source_sha256=row['source_sha256'],
            timing_alias_of=row.get('timing_alias_of'),native_attempts=[] if owner is not row else [a['attempt_number'] for a in good],
            samples_seconds=row['samples_seconds'],median_seconds=row['median_seconds'],sample_stdev_seconds=row['sample_stdev_seconds'],
            canonical_loc=canonical,canonical_loc_qualified=row['language']=='apl',formatted_loc=None,formatted_loc_qualified=False,
            source_work_qualified=row['language']=='apl',source_work_evidence=work,source_profile=copy.deepcopy(row))
    tree=r['programs'][TREE];failure=r['attempts'][74]
    intervals.append((75,*receipt(failure,tree,records,fingerprint,True)))
    require(tree['samples_seconds']==[] and tree['full_failure']['attempt_number']==75 and tree['measurement_status']=='failed','Failed trees were promoted')
    require(r['programs']['binarytrees:binarytrees-apl-optimized']['full_failure']==tree['full_failure']
        and r['programs']['binarytrees:mech-control-for-apl']['samples_seconds']==[],'Tree alias/control disposition changed')
    require(used==set(range(44,88))-{58,75} and set(records)==set(range(45,88)),'Native coverage or receipt inventory differs')
    intervals.sort();require([n for n,_,_ in intervals]==list(range(44,88)),'Duplicate or missing native accounting')
    require(all(left[2]<=right[1] for left,right in zip(intervals,intervals[1:])),'Retained native intervals overlap')
    for a in r['attempts'][44:]:
        n=a['attempt_number'];name='remaining_manifest' if n<=58 else 'argv_manifest' if n<=75 else 'old_manifest' if n<=84 else 'manifest'
        same(a['continuation_manifest_sha256'],index['documents'][name]['sha256'],'Native continuation manifest route differs')
    return dict(schema='apl-retained-five-native-reconciliation-v1',status='saved-ledger-reconciled-awaiting-physical-closure',
        profiles=profiles,accepted_native_observations=42,apl_native_observations=27,matched_control_observations=15,
        selected_source_identities=9,selected_source_labels=11,timing_alias_labels=2,preserved_failed_attempts=[58,75],
        original_report_status=r['status'],recovery_owner_status=status['status'],recovered_original_attempt=84,
        report_only_native_attempts=[44],guarded_native_observations=41,original_prefix_entries=43,
        native_receipt_scope='Historical schemas retain command, PGID registration, normal sampler wait status and cleanup. They do not contain the newer per-attempt kernel birth/parent proof.',
        environment_scope='Recorded row overrides and frozen runner policy; full inherited ambient environment was not captured.',
        timing_scope=r['protocol'],complete_stdout_retained=False,file_integrity_verified=False,full_suite_qualified=False,
        source_work_qualified=True,canonical_loc_qualified=True,source_work_scope='Nine exact retained applications; historical audited work and correctness evidence, not a new native work probe.',
        runtime_dependency_scope='Recorded inherited pin set; no new loaded-image inventory or per-sample library observation.',
        runtime_publication_metadata_qualified=False,chart_admission=False,new_native_processes=0)


class Files:
    def __init__(self):self.pins={}
    def verify(self,path,digest):
        path=Path(path);require(path.is_absolute() and len(digest)==64,'Absolute pinned input required')
        require(str(path) not in self.pins or self.pins[str(path)]==digest,'Conflicting native input pin')
        with path.open('rb') as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==digest,'Physical evidence changed: '+str(path))
        self.pins[str(path)]=digest
    def final(self,original):
        required=dict(original)
        for path,digest in self.pins.items():require(path not in required or required[path]==digest,'Original pin rebound');required[path]=digest
        for path,digest in required.items():self.verify(path,digest)


@contextmanager
def review_context(tool_sha256,on_exit_failure=None,final_consumer_check=None):
    """Deferred physical replay; no native invocation and no automatic retry."""
    require(LOCK.is_file() and LOCK.stat().st_ino==LOCK_INODE,'Original common mutex replaced')
    with LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        identity=(os.fstat(lock.fileno()).st_dev,os.fstat(lock.fileno()).st_ino);files=Files();original=()
        def verify_lease():
            held=os.fstat(lock.fileno());named=LOCK.stat()
            require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==identity
                and named.st_ino==LOCK_INODE,'Timing lease identity changed')
        def finish():
            verify_lease()
            files.final(original)
            verify_lease()
            if final_consumer_check is not None:final_consumer_check()
        try:
            verify_lease()
            files.verify(Path(__file__).resolve(),tool_sha256);files.verify(INDEX,INDEX_SHA)
            index,d,records,sources=metadata()
            for collection in ('documents','sources','artifacts'):
                for ref in index[collection].values():files.verify(ROOT/ref['path'],ref['sha256'])
            for pair in index['receipts'].values():
                for ref in pair.values():files.verify(ROOT/ref['path'],ref['sha256']);files.verify(ref['recorded_path'],ref['sha256'])
            inherited=d['status']['retained_input_and_actual_result_pins']
            for name in ('manifest','remaining_manifest','argv_manifest','old_manifest','audit'):
                for path,digest in d[name]['pins'].items():
                    require(inherited.get(path)==digest,'Inherited native prerequisite omitted or rebound')
            for path,digest in inherited.items():files.verify(path,digest)
            for revision in d['report']['guard_revisions']:
                for field in ('prior_report','prior_source_audit'):files.verify(revision[field],revision[field+'_sha256'])
            result=reconcile(index,d,records,sources)
            result.update(status='five-completed-workloads-reconciled-awaiting-publication-review',file_integrity_verified=True,
                common_mutex_held=True,common_mutex_inode=LOCK_INODE,verified_file_pins=dict(files.pins))
            original=tuple(files.pins.items());yield result,files
        except BaseException:
            if on_exit_failure is not None:on_exit_failure()
            raise
        finally:
            try:finish()
            except BaseException:
                if on_exit_failure is not None:on_exit_failure()
                raise
