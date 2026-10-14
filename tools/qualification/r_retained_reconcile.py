"""Reconcile the 27 saved R tree, N-body and fannkuch observations.

The first 21 observations use the repaired report-only runner. The last six
also have separate sampler and supervisor receipts. No missing fields are
invented, no measured source is changed and no native program is launched.
"""
from contextlib import contextmanager, ExitStack
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
COHORT = 'r-apl-uiua-comparison/20261011'
BASE = ROOT/'archive/comparisons'/COHORT
CONTINUATION = 'uiua-fann-compact-v5/controller_rev2/remaining-owner'
PACKET = ROOT/'experiments/r/retained-native-v1'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
REPORT_SHA = 'ce37df0204cd7880033206f3afb2f91296d4b757090c5026947a414c224f1c6e'
AUDIT_SHA = 'd76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'
MANIFEST_SHA = 'affba5b243da43d1a15c28e5364741828e4f684bb1b43d15d81ad720b28ef39f'
BEFORE_SHA = '44a20749c5ee485392af2c220ef074d3846323e04c613243a73d3c6f9da49b0a'
RUNNER_SHA = '5b2a038cfae4112e9e2eee79c3cd57ccc6a1521812828c47bf28986d6a8e139b'
SAMPLER_SHA = '55581d56609803243b3be264e6a2e37229be06789c22788bbf8cdb6ff6828544'
COUNTS = ROOT/'experiments/r/retained-source-counts-v1/qualified-source-counts-v1.json'
COUNTS_SHA = '835ded7cc27df684f6628048b90f4ec06ef249ba8f58ed207016a669dcacb0cf'
POLICIES = {
    'consumer': ('archive/site/explorer/r_apl_uiua_data.py', 'bdbfdb4ec2db65e25f8fe05ec546ac027495dfb7a8ed33004ca2a5a399d3ab93'),
    'owners': ('tools/qualification/r_retained_source_units.py', '1da6c798290d28a8fa0785fe7ec9bc1937248c0710a17a6003f0d31c68fd417c'),
    'files': ('tools/qualification/uiua_fann_reconcile.py', 'bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd'),
}
BENCHES = {'binarytrees': (21,67), 'nbody': (50000000,76), 'fannkuchredux': (12,85)}
OUTPUTS = {
    'binarytrees': (455,'341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'fannkuchredux': (29,'4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'),
}
CHECKS = set(('sampler_exited_normally authoritative_native_group_received native_inherited_common_mutex '
    'native_exited_normally no_execution_error no_wrapper_integrity_error no_resource_violation '
    'no_resource_monitor_errors no_compiler_power_monitor_errors no_monitor_finish_error '
    'no_execute_cleanup_error no_remaining_execute_group no_supervisor_cleanup '
    'no_supervisor_remaining_group valid_environment actual_full_workload exact_command_and_group '
    'complete_output_reference_match complete_output_bytes_and_hash pins_unchanged').split())
SUPERVISOR_FIELDS = set(('attempt qualification_checks qualified result_path round sampler_wait_status '
    'supervised_native_group supervisor_remaining_members supervisor_result_path').split())
REPORT_FIELDS = {'attempt_number','continuation_manifest_sha256','sample'}


def require(condition, message):
    if not condition: raise ValueError(message)


def same(left, right, message):
    require(json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False),message)


def load_policy(name):
    relative,digest = POLICIES[name]
    path = ROOT/relative
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'Reviewed policy changed: '+relative)
    spec = importlib.util.spec_from_file_location('r_retained_'+name,path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


class NoLegacy:
    def reconcile(self, *_):
        raise ValueError('These exact 27 observations have no legacy migration lineage')


def reconcile(report,audit,manifest,before,counts,sources,raw,supervised,consumer,owners):
    """Pure saved-document checks; physical pin replay is a separate phase."""
    require(report['status']=='complete' and not report.get('active') and report['language']=='r'
            and report['sample_count']==3 and len(report['attempts'])==93,'Completed original R report required')
    require(audit['status']=='reviewed' and audit['language']=='r' and report['source_audit_sha256']==AUDIT_SHA,
            'Frozen source audit differs')
    same(report['workloads'],audit['workloads'],'Workload inventory changed')
    same(report['protocol'],audit['timing_boundary'],'Timing boundary changed')
    require(report['shared_timing_lock']==audit['shared_timing_lock']==str(LOCK),'Different timing mutex')
    require(len(before['attempts'])==87,'Continuation must preserve all 87 earlier observations')
    same(report['attempts'][:87],before['attempts'],'Original observations were rewritten')
    require(manifest['before_reports']['r']['sha256']==BEFORE_SHA and manifest['audits']['r']['sha256']==AUDIT_SHA,
            'Continuation ancestry differs')
    require(manifest['pins'][str(OLD/COHORT/'uiua-fann-compact-v5/controller_rev2/remaining_owner.py')]==SAMPLER_SHA
            and audit['pins'][str(OLD/COHORT/'run.py')]==RUNNER_SHA,'Recorded native runner differs')
    require(len(manifest['pins'])==1429 and len(audit['pins'])==104,'Original pin inventories changed')
    require(counts['canonical_loc_qualified'] is True and counts['source_count']==6,
            'Six independent canonical source decisions required')
    counted = {c['key']:c for c in counts['profiles']}
    require(set(counted)==set(owners.SOURCES)==set(sources),'Six exact measured R sources required')
    frozen = {p['key']:p for p in audit['programs']+audit['controls']}
    keys = set(counted)|{b+':mech-control-for-r' for b in BENCHES}
    require(len(keys)==9 and set(raw)==set(supervised)==set(range(88,94)),'Exact six continuation receipts required')
    selected = {}
    for key in sorted(keys):
        row = report['programs'][key]
        for field,value in frozen[key].items():
            if field!='measurement_status': same(row[field],value,'Frozen source/runtime row changed: '+key+' '+field)
        require(not row.get('timing_alias_of') and not row.get('full_failure'),'Unexpected alias or failed source')
        require(len(row['samples_seconds'])==len(row['attempts'])==3,'Three actual observations per source required')
        require(consumer._sample_evidence(row,report,audit,NoLegacy()),'Saved observations are incomplete')
        require(all(not report['attempts'][n-1].get('prior_guard_revision_attempt_number') for n in row['attempts']),
                'Unreviewed earlier runner lineage')
        if row['language']=='r':
            c=counted[key]; measured=owners.count_source(sources[key],key)
            require(row['source']==str(OLD/COHORT/Path(c['source']['path']).relative_to(BASE.relative_to(ROOT)))
                    and row['source_sha256']==c['source']['sha256']==measured['source_sha256'],
                    'Canonical count belongs to another source')
            require(c['canonical_loc']==measured['canonical_loc'] and c['physical_loc']==measured['physical_loc']
                    and c['canonical_loc_qualified'] is True and c['formatted_loc'] is None,'Canonical source units changed')
            require(row['algorithm']['strict'] is True and row['algorithm']['native_benchmark_kernel'] is False,
                    'Required source work differs')
            require(row['small_validation']['returncode']==0 and row['small_validation']['reference_match'] is True
                    and row['adversarial_validation'] and all(v['returncode']==0 and v['reference_match'] is True
                        for v in row['adversarial_validation']),'Retained correctness evidence differs')
            require(type(row['maximum_workers']) is int and 1<=row['maximum_workers']<=8,'Worker bound differs')
            if row['benchmark']=='binarytrees':
                allocation=row['allocation_fixture']
                require(allocation['depth']==5 and allocation['total_nodes']==allocation['unique_node_addresses']==63
                        and allocation['leaf_allocation'] is True,'Fresh per-node allocation evidence differs')
        selected[key]=copy.deepcopy(row)
    for bench,(size,start) in BENCHES.items():
        attempts=report['attempts'][start-1:start+8]
        expected_keys={k for k in keys if k.startswith(bench+':')}
        orders=report['orders'][bench]
        require(len(orders)==3 and all(len(order)==3 and set(order)==expected_keys for order in orders),
                'Three balanced rounds required')
        for offset,attempt in enumerate(attempts):
            number=start+offset
            require(attempt['attempt_number']==number and attempt['key']==orders[offset//3][offset%3]
                    and attempt['sample']==offset//3+1 and attempt['workload_n']==size,'Recorded round/size differs')
            require(attempt['exit_status']==0 and attempt['remaining_group_members']==[]
                    and not any(attempt.get(k) for k in ('error','cleanup_error','resource_violation',
                        'resource_monitor_errors','monitor_errors','monitor_finish_error','competing_compilers','power_changes')),
                    'Native completion or isolation failed')
            require(attempt['maximum_rss_mib']==10240 and attempt['peak_process_group_rss_kib']<=10240*1024,
                    'Recorded resource ceiling exceeded')
            if bench in OUTPUTS:
                require((attempt['stdout_bytes'],attempt['stdout_sha256'])==OUTPUTS[bench],'Full output reference differs')
            else:
                v=attempt['validation'];energy=v['energies']
                require(attempt['stdout_bytes']==26 and len(energy)==2 and v['tolerance']==1e-8
                        and all(type(x) in (int,float) and math.isfinite(x) and abs(x-y)<=1e-8
                            for x,y in zip(energy,(-0.169075164,-0.169059907))),'N-body energy reference differs')
            if number<88:
                require(not any(k in attempt for k in ('qualified','result_path','supervisor_result_path','pins_unchanged_at_end')),
                        'Report-only observations must retain their original schema')
            else:
                s=supervised[number]; native=s['supervised_native_group']
                require(set(attempt)-set(s)==REPORT_FIELDS and not set(s)-set(attempt),'Report enrichment changed')
                same(s,{k:v for k,v in attempt.items() if k not in REPORT_FIELDS},'Report differs from supervisor receipt')
                require(set(s)-set(raw[number])==SUPERVISOR_FIELDS and not set(raw[number])-set(s),'Sampler enrichment changed')
                same(raw[number],{k:v for k,v in s.items() if k not in SUPERVISOR_FIELDS},'Raw sampler receipt changed')
                require(attempt['continuation_manifest_sha256']==MANIFEST_SHA and s['qualified'] is True
                        and s['sampler_wait_status']==0 and s['supervisor_remaining_members']==[]
                        and s['pins_unchanged_at_end'] is True and set(s['qualification_checks'])==CHECKS
                        and all(x is True for x in s['qualification_checks'].values()),'Continuation qualification failed')
                require(native['type']=='native-group-started' and native['inherited_common_mutex'] is True
                        and type(native['pid']) is int and native['pid']==native['pgid']>0
                        and native['command']==s['command'],'Native process group identity differs')
    return dict(schema='r-retained-three-workload-reconciliation-v1',
        status='27-saved-observations-reconciled-awaiting-physical-evidence-review',
        profiles=selected,canonical_counts=copy.deepcopy(counted),subject_observations=18,control_observations=9,
        native_observations=27,report_only_observations=21,separate_sampler_supervisor_observations=6,
        preserved_prior_observations=87,source_work_qualified=True,canonical_loc_qualified=True,
        physical_file_integrity_verified=False,chart_admission=False,native_processes_started=0,
        timing_boundary=audit['timing_boundary'],
        limitations=['The original report-only runner did not save independent sampler or supervisor receipts.',
            'Recorded runtime overrides and pinned runner policy are available; the complete inherited ambient environment was not recorded.',
            'Formatted LOC remains unavailable. Original producer counts remain unchanged in the saved report.'])


@contextmanager
def review_files(tool_sha256,on_exit_failure=None,final_consumer_check=None):
    """Read completed evidence under its original leases and common mutex."""
    file_policy=load_policy('files');files=file_policy.Files()
    require(LOCK.is_file() and LOCK.stat().st_ino==LOCK_INODE,'Original common mutex missing or replaced')
    with ExitStack() as stack:
        lock=stack.enter_context(LOCK.open('r+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lock_identity=(os.fstat(lock.fileno()).st_dev,os.fstat(lock.fileno()).st_ino)
        require(lock_identity[1]==LOCK_INODE,'Locked common mutex is not the original inode')
        lease_identities={LOCK:lock_identity}
        def check_leases():
            for path,expected in lease_identities.items():
                current=path.stat()
                require((current.st_dev,current.st_ino)==expected,'Held lease pathname replaced: '+str(path))
        original_pins=()
        try:
            check_leases()
            files.verify(Path(__file__).resolve(),tool_sha256)
            for relative,digest in POLICIES.values():files.verify(ROOT/relative,digest)
            def document(relative,digest):
                saved=files.read(BASE/relative,digest)
                require(files.read(OLD/COHORT/relative,digest)==saved,'Original/retained evidence differs')
                return file_policy.strict_json(saved)
            report=document('results/timings-r.json',REPORT_SHA)
            audit=document('source-audit-r.json',AUDIT_SHA)
            manifest=document(CONTINUATION+'/manifest.json',MANIFEST_SHA)
            before=document(CONTINUATION+'/r-before.json',BEFORE_SHA)
            for name in manifest['owner_leases']:
                lease=stack.enter_context(Path(name).open('r+'));fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
                identity=os.fstat(lease.fileno())
                lease_identities[Path(name)]=(identity.st_dev,identity.st_ino)
            check_leases()
            for pins in (audit['pins'],manifest['pins']):
                for name,digest in pins.items():files.verify(Path(name),digest)
            counts=file_policy.strict_json(files.read(COUNTS,COUNTS_SHA))
            for item in [counts['owner_review'],*counts['evidence']]:files.verify(ROOT/item['path'],item['sha256'])
            sources={c['key']:files.read(ROOT/c['source']['path'],c['source']['sha256']) for c in counts['profiles']}
            raw,supervised={},{}
            for number in range(88,94):
                attempt=report['attempts'][number-1]
                for field,output in [('result_path',raw),('supervisor_result_path',supervised)]:
                    name=Path(attempt[field]);suffix='.supervisor.json' if field.startswith('supervisor') else '.json'
                    expected=OLD/COHORT/CONTINUATION/'attempts'/f'{number:03d}-{attempt["id"]}{suffix}'
                    require(name==expected,'Native receipt path differs')
                    saved=(BASE/CONTINUATION/'attempts'/name.name).read_bytes();digest=hashlib.sha256(saved).hexdigest()
                    output[number]=document(CONTINUATION+'/attempts/'+name.name,digest)
            result=reconcile(report,audit,manifest,before,counts,sources,raw,supervised,
                             load_policy('consumer'),load_policy('owners'))
            result.update(status='27-saved-observations-reconciled-awaiting-publication-review',
                physical_file_integrity_verified=True,verified_file_pins=copy.deepcopy(files.pins),
                common_mutex_held=True,common_mutex_inode=LOCK_INODE)
            original_pins=tuple(files.pins.items())
            yield result,files
        except BaseException:
            if on_exit_failure is not None:on_exit_failure()
            raise
        finally:
            try:
                check_leases()
                files.final_check(original_pins)
                check_leases()
                if final_consumer_check is not None:final_consumer_check()
            except BaseException:
                if on_exit_failure is not None:on_exit_failure()
                raise
