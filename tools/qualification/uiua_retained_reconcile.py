"""Reconcile the completed Uiua n-body and tree observations without reruns.

The retained report is the original sampler record for this schema. The scope
is fifteen accepted observations, one preserved environmental exclusion and
one source/timing alias. No producer or runtime is imported or executed.
"""
import argparse
from contextlib import contextmanager
import copy
from datetime import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
COHORT = 'r-apl-uiua-comparison/20261011'
ARCHIVE = ROOT/'archive/comparisons'/COHORT
PACKET = ROOT/'experiments/uiua/retained-native-v1'
REPORT_SHA = 'da5ccf102e90dc2755388414390f6401402b2f67edb177ba74a377f2c5cae709'
AUDIT_SHA = '82b15648d0c49c6393a0eec1efb441f1ee11237ceae4a8f41ca854c0b7ee0860'
RUNNER_SHA = '5b2a038cfae4112e9e2eee79c3cd57ccc6a1521812828c47bf28986d6a8e139b'
PREPARE_SHA = '27fcf050ed21db40e747f2e8801ca6f227d82f1ea98f8592bba7b10a768109e5'
TREE_WORK_SHA = '41a600a321f7206389a964332d54ec9cf7f4557cc9657470a9859dd285d852ad'
NBODY_WORK_SHA = '248f99a5bae5446e904d53a85bafd91fb9a80005df40420234856187ab27c4e9'
COUNT_APPROVAL = ROOT/'experiments/uiua/retained-counts-v1/qualified-source-counts.json'
COUNT_APPROVAL_SHA = 'f2d5763e6ef958a0dbffad3a5a9d72c20767642fb131e978f168c361b4bb7607'
MODULES = {
    'core': ('tools/qualification/uiua_fann_reconcile.py','bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd'),
    'legacy': ('archive/site/explorer/r_apl_uiua_data.py','bdbfdb4ec2db65e25f8fe05ec546ac027495dfb7a8ed33004ca2a5a399d3ab93'),
    'counter': ('tools/qualification/uiua_retained_source_units.py','38f3d5fc537d1eba999b105d1460990b429bc5746101b3b253a2b05bcac49db1'),
    'writer': ('tools/qualification/import_uiua_fann.py','f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'),
}
TREE = 'binarytrees:binarytrees-uiua-compact'
TREE_ALIAS = 'binarytrees:binarytrees-uiua-optimized'
TREE_CONTROL = 'binarytrees:mech-control-for-uiua'
NBODY_COMPACT = 'nbody:nbody-uiua-native-denominator-compact-v3'
NBODY_FAST = 'nbody:nbody-uiua-native-denominator-optimized-v3'
NBODY_CONTROL = 'nbody:mech-control-for-uiua-medium-v3'
ACCEPTED = {TREE:[59,61,63],TREE_CONTROL:[60,62,64],NBODY_COMPACT:[66,71,74],
            NBODY_FAST:[67,68,72],NBODY_CONTROL:[65,69,73]}
COUNTS = {TREE:'binarytrees',TREE_ALIAS:'binarytrees',NBODY_COMPACT:'nbody-compact',NBODY_FAST:'nbody-fast'}
REFERENCE = {
    'binarytrees':dict(bytes=455,sha256='341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1',reference_match=True),
    'nbody':dict(bytes=26,sha256='3e6c9ef9d26cfe312a4cd8e1b81b3f671b88fbce84de543e8c23c206a942504d',
                 reference_match=True,energies=[-0.169075164,-0.169059907],tolerance=1e-8),
}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load_modules():
    loaded={}
    for name,(relative,digest) in MODULES.items():
        path=ROOT/relative;raw=path.read_bytes()
        require(sha(raw)==digest,'Frozen independent consumer changed: '+relative)
        spec=importlib.util.spec_from_file_location('uiua_retained_'+name,path)
        module=importlib.util.module_from_spec(spec)
        exec(compile(raw,str(path),'exec'),module.__dict__)
        loaded[name]=module
    return loaded


class NoLegacyMigration:
    """These selected observations all record the repaired execution schema."""
    verified={}
    def reconcile(self,*args):
        raise ValueError('Unexpected migrated or pre-repair selected observation')


def reconcile(report,audit,tree_work,nbody_work,count_approval,sources,modules):
    core,old,counter=(modules[k] for k in ('core','legacy','counter'))
    require(report['status']=='partial' and report.get('active') is None and
            report['language']==audit['language']=='uiua' and audit['status']=='reviewed' and
            report['sample_count']==3 and len(report['attempts'])==77,'Exact retained suite scope differs')
    require(report['source_audit']==str(HISTORICAL/COHORT/'source-audit-uiua.json') and
            report['source_audit_sha256']==AUDIT_SHA,'Source-audit binding differs')
    require(report['workloads']==audit['workloads'] and
            audit['workloads']['binarytrees']==[10,21] and audit['workloads']['nbody']==[1000,50000000] and
            audit['power_required']==dict(source='AC Power',low_power_mode=0),'Canonical workload/power differs')
    require(report['shared_timing_lock']==audit['shared_timing_lock']==str(core.LOCK) and
            report['protocol']==audit['timing_boundary'] and
            report['baseline_endpoints']==audit['baseline_endpoints'],'Recorded timing protocol differs')
    require(audit['pins'][str(HISTORICAL/COHORT/'run.py')]==RUNNER_SHA and
            audit['pins'][str(HISTORICAL/COHORT/'prepare.py')]==PREPARE_SHA,'Repaired guard binding differs')
    require({'nbody','binarytrees'}<=set(report['completed_benchmarks']),'Selected workload incomplete')
    require(count_approval['status']=='three-exact-source-owner-counts-independently-qualified' and
            count_approval['canonical_loc_qualified'] is True,'Independent canonical owner approval required')
    approved={p['identity']:p for p in count_approval['profiles']}
    frozen={row['key']:row for row in audit['programs']+audit['controls']}
    keys=set(ACCEPTED)|{TREE_ALIAS}
    require({k for k,v in report['programs'].items() if v['benchmark'] in ('nbody','binarytrees')}==keys,
            'Selected profile inventory differs')
    selected=[a for a in report['attempts'] if a['benchmark'] in ('nbody','binarytrees')]
    require([a['attempt_number'] for a in selected]==list(range(59,75)), 'Selected attempt inventory differs')
    require([i for i in report['discarded'] if i in range(59,75)]==[70],'Environmental exclusion differs')
    require(report['orders']['binarytrees']==[[TREE,TREE_CONTROL]]*3 and
            report['orders']['nbody']==[[NBODY_CONTROL,NBODY_COMPACT,NBODY_FAST],
              [NBODY_FAST,NBODY_CONTROL,NBODY_COMPACT],[NBODY_FAST,NBODY_CONTROL,NBODY_COMPACT]],
            'Interleaved execution orders differ')
    prior_end=None
    for attempt in selected:
        require(attempt.get('prior_guard_revision_attempt_number') is None and
                'runtime_environment' in attempt and 'execution_fingerprint' in attempt,
                'Selected observation is not the original repaired-guard record')
        require(attempt['remaining_group_members']==[] and not attempt.get('cleanup_error') and
                not attempt.get('error') and attempt['exit_status']==0 and not attempt.get('resource_violation'),
                'Native completion or cleanup differs')
        require(attempt['maximum_rss_mib']==10240 and
                type(attempt['peak_process_group_rss_kib']) is int and
                0<=attempt['peak_process_group_rss_kib']<=10240*1024 and
                old._positive_number(attempt['timeout_seconds']) and
                0<attempt['seconds']<attempt['timeout_seconds'],'Recorded time/resource limit differs')
        core.same(attempt['validation'],REFERENCE[attempt['benchmark']],'Full output validation differs')
        start,end=(datetime.fromisoformat(attempt[k]) for k in ('started_at','finished_at'))
        require(start<end and (prior_end is None or prior_end<=start),'Selected native intervals overlap')
        prior_end=end
    dropped=report['attempts'][69]
    require(dropped['key']==NBODY_COMPACT and dropped['sample']==2 and
            dropped['valid_environment'] is False and bool(dropped['competing_compilers']),
            'Attempt 70 compiler-contention exclusion must remain intact')
    require(tree_work['binarytrees']['status']=='passed-source-audit' and
            all(tree_work['binarytrees'][k] is True for k in
                ('fresh_node_allocation','fresh_leaf_allocation','retained_long_lived_tree')),
            'Retained tree allocation/retention proof differs')
    require(nbody_work['status']=='passed-source-audit' and nbody_work['full_n']==50000000 and
            nbody_work['bodies']==5 and nbody_work['state_components']==30 and nbody_work['dt']==.01 and
            nbody_work['norm_already_native_and_unchanged'] is nbody_work['reduction_order_unchanged'] is True and
            all(nbody_work[k] is False for k in ('native_benchmark_kernel','host_helpers','input_specific_shortcuts')),
            'Retained n-body work proof differs')
    profiles={};no_migration=NoLegacyMigration()
    for key in sorted(keys):
        row=report['programs'][key]
        require(row['key']==key and row['measurement_status']=='measured' and
                row['algorithm']['strict'] is True and row['algorithm']['native_benchmark_kernel'] is False,
                'Source work/measurement identity differs')
        for field,value in frozen[key].items():
            if field in ('samples_seconds','sample_validation','attempts'):
                require(value==[],'Frozen preparation contains measurements')
            elif field!='measurement_status':
                core.same(row.get(field),value,'Report/frozen preparation differs: '+key+'/'+field)
        require(old._sample_evidence(row,report,audit,no_migration),'Incomplete selected sample evidence')
        owner=row.get('timing_alias_of') or key
        accepted=[a for a in selected if a['key']==owner and a['valid_environment'] and not a.get('error')]
        require([a['attempt_number'] for a in accepted]==ACCEPTED[owner] and
                [a['sample'] for a in accepted]==[1,2,3],'Accepted sample schedule differs')
        count=None
        if key in COUNTS:
            require(row['maximum_workers']==1,'Uiua worker policy differs')
            identity=COUNTS[key];count=counter.count_source(sources[key],identity)
            require(count['source_sha256']==row['source_sha256'] and
                    count['canonical_loc']==row['loc']==approved[identity]['canonical_loc'],
                    'Independent exact-source count differs')
            for field,value in count.items():
                core.same(approved[identity].get(field),value,'Qualified count receipt differs: '+field)
        profiles[key]=dict(key=key,benchmark=row['benchmark'],language=row['language'],
            source_sha256=row['source_sha256'],canonical_source_count=count,
            timing_alias_of=row.get('timing_alias_of'),native_observations=0 if key==TREE_ALIAS else 3,
            samples_seconds=copy.deepcopy(row['samples_seconds']),median_seconds=statistics.median(row['samples_seconds']),
            sample_stdev_seconds=statistics.stdev(row['samples_seconds']),
            sample_execution_metadata=old._execution_metadata(row,report,no_migration),
            sample_evidence=[dict(attempt_number=a['attempt_number'],sample=a['sample'],seconds=a['seconds'],
                stdout_bytes=a['stdout_bytes'],stdout_sha256=a['stdout_sha256'],validation=copy.deepcopy(a['validation']),
                evidence_kind='original-report-attempt',report='archive/comparisons/'+COHORT+'/results/timings-uiua.json',
                report_sha256=REPORT_SHA) for a in accepted],original_profile=copy.deepcopy(row))
    require(report['programs'][TREE_ALIAS]['timing_alias_of']==TREE and
            sources[TREE_ALIAS]==sources[TREE],'Tree alias source/owner differs')
    return dict(schema='uiua-retained-nbody-trees-independent-reconciliation-v1',
        status='fifteen-retained-observations-reconciled-awaiting-file-phase-and-publication',
        report_status='partial',selected_workloads_complete=True,accepted_native_observations=15,
        subject_native_observations=9,control_native_observations=6,preserved_excluded_native_observations=1,
        source_forms=4,distinct_subject_sources=3,timing_aliases=1,profiles=profiles,
        excluded_attempt=copy.deepcopy(dropped),guard_revisions=copy.deepcopy(report['guard_revisions']),
        guard= dict(path=str(HISTORICAL/COHORT/'run.py'),sha256=RUNNER_SHA,
            schema='original-report-attempt-with-recorded-execution-fingerprint',separate_sampler_receipts_written=False,
            selected_migrated_or_pre_repair_attempts=0),
        environment_limitation='Recorded row overrides and pinned runner policy; complete inherited ambient values were not captured.',
        resource_observation_limitation='The three subsecond tree controls ended before the first periodic RSS observation; their stored zero is an unobserved peak, not a zero-memory claim.',
        tree_work_scope=copy.deepcopy(tree_work['binarytrees']),nbody_work=copy.deepcopy(nbody_work),
        original_timing_boundary=audit['timing_boundary'],
        timing_scope='Fresh full process from immediately before launch through process exit; Uiua source compilation inside run is included. External preparation/builds, output validation and hashing are excluded.',
        native_processes_started=0,file_integrity_verified=False,canonical_loc_qualified=True,
        source_work_qualified=True,formatted_loc_qualified=False,chart_admission=False,dataset_files_changed=False)


@contextmanager
def review_context(tool_sha256,on_exit_failure=None,final_consumer_check=None):
    modules=load_modules();core=modules['core'];files=core.Files()
    files.verify(Path(__file__).resolve(),tool_sha256)
    require(core.LOCK.is_file() and core.LOCK.stat().st_ino==core.LOCK_INODE,'Original common mutex missing')
    with core.LOCK.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        identity=(os.fstat(lock.fileno()).st_dev,os.fstat(lock.fileno()).st_ino)
        require(identity[1]==core.LOCK_INODE,'Opened common mutex is not the original inode')
        original_pins=()
        def verify_lock():
            current=core.LOCK.stat()
            require((current.st_dev,current.st_ino)==identity,'Common mutex pathname replaced')
        try:
            verify_lock()
            for relative,digest in MODULES.values():files.verify(ROOT/relative,digest)
            docs={}
            for name,digest in [('results/timings-uiua.json',REPORT_SHA),('source-audit-uiua.json',AUDIT_SHA),
                ('results/uiua/source-audit.json',TREE_WORK_SHA),('uiua-nbody-v3/results/source-audit.json',NBODY_WORK_SHA),
                ('run.py',RUNNER_SHA),('prepare.py',PREPARE_SHA)]:
                raw=files.read(ARCHIVE/name,digest)
                require(raw==files.read(HISTORICAL/COHORT/name,digest),'Retained/original evidence differs')
                if name.endswith('.json'):docs[name]=core.strict_json(raw)
            report,audit=docs['results/timings-uiua.json'],docs['source-audit-uiua.json']
            for path,digest in audit['pins'].items():files.verify(Path(path),digest)
            approval=core.strict_json(files.read(COUNT_APPROVAL,COUNT_APPROVAL_SHA))
            for ref in [approval['proposal']]+approval['evidence']:files.verify(ROOT/ref['path'],ref['sha256'])
            sources={}
            for key in COUNTS:
                row=report['programs'][key];original=Path(row['source'])
                raw=files.read(original,row['source_sha256'])
                retained=ROOT/'archive/comparisons'/original.relative_to(HISTORICAL)
                require(raw==files.read(retained,row['source_sha256']),'Retained exact source differs')
                sources[key]=raw
            result=reconcile(report,audit,docs['results/uiua/source-audit.json'],
                docs['uiua-nbody-v3/results/source-audit.json'],approval,sources,modules)
            result.update(status='fifteen-retained-observations-file-verified-awaiting-publication',
                file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=core.LOCK_INODE,
                verified_file_pins=copy.deepcopy(files.pins),report=dict(path=str(ARCHIVE/'results/timings-uiua.json'),sha256=REPORT_SHA),
                source_audit=dict(path=str(ARCHIVE/'source-audit-uiua.json'),sha256=AUDIT_SHA),
                count_approval=dict(path=str(COUNT_APPROVAL),sha256=COUNT_APPROVAL_SHA))
            original_pins=tuple(files.pins.items())
            yield result,files
        except BaseException:
            if on_exit_failure is not None:on_exit_failure()
            raise
        finally:
            try:
                verify_lock();files.final_check(original_pins);verify_lock()
                if final_consumer_check is not None:final_consumer_check()
            except BaseException:
                if on_exit_failure is not None:on_exit_failure()
                raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    require(output.is_relative_to(PACKET.resolve()) and not output.exists(),'Fresh retained packet receipt required')
    writer=load_modules()['writer'];owner=writer.OwnedFiles()
    with review_context(args.tool_sha256,on_exit_failure=owner.remove_all,final_consumer_check=owner.final_check) as (result,files):
        output.parent.mkdir(parents=True,exist_ok=True)
        raw=writer.encoded(result)
        owner.write(output,raw)
    print(json.dumps(dict(status=result['status'],observations=15,native_runs=0,output=str(output),sha256=sha(raw))))


if __name__=='__main__':main()
