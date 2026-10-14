"""Prepare a private Kotlin metadata/publication candidate from closed evidence.

This tool has no apply/publish mode. It writes one new candidate JSON outside
the original timing evidence and publication paths, only after independently
reproducing the pinned reconciliation under all three completed-job leases.
No runtime, compiler, benchmark, or measurement producer is imported or run.
"""
import argparse
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RECONCILER = Path(__file__).with_name('kotlin_reconcile.py')
# Independently reviewed source; the file phase binds this and both primitives.
RECONCILER_SHA = '568de52b6c0ea434e2aedfe61d50908ce39edb0ab9df4d21c3c362a244b3a0c0'


def load_reconciler():
    raw = RECONCILER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECONCILER_SHA:
        raise ValueError('Independent Kotlin reconciler changed')
    spec = importlib.util.spec_from_file_location('kotlin_candidate_reconciliation', RECONCILER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(RECONCILER), 'exec'), module.__dict__)
    return module


r = load_reconciler()
p, require, same = r.p, r.require, r.same
RUNTIME_METADATA = ROOT/'experiments/kotlin/full90-v2/runtime-metadata-v1.json'
RUNTIME_METADATA_SHA = '4d2fe53efc54f84765dc16ddb40c711ce51d1fff0b1d2daf351b8b86163e62dc'
JDK_RELEASE = ROOT/'experiments/kotlin/full90-v2/retained-jdk-release.txt'
JDK_RELEASE_SHA = 'e5e50f3c36e9ce7ac50ccbc499c8299880e8fb8fee57bb3a7a2b890477ce8498'
EXTRA_PINS = {str(RUNTIME_METADATA):RUNTIME_METADATA_SHA,str(JDK_RELEASE):JDK_RELEASE_SHA}
ROLES = ('application', 'application-helper')
SOURCE_ROOT = ROOT/'experiments/kotlin/source-counts-v3/run-v1/native-reader/sources'


def ref(path, digest):
    require(Path(path).is_absolute() and p.digest(digest), 'Invalid evidence reference')
    return dict(path=path, sha256=digest)


def validate_prerequisites(plan, review, work, counts, metadata, read_raw):
    _, profiles = r.schedule(plan)
    require(review['schema'] == r.SCHEMA and
            review['status'] == 'full90-reconciled-awaiting-runtime-and-publication-review' and
            review['file_integrity_verified'] is True and review['common_mutex_held'] is True and
            p.integer(review['common_mutex_inode'], p.LOCK_INODE) and
            review['runtime_publication_metadata_qualified'] is False and review['chart_admission'] is False,
            'Completed independent result reconciliation required')
    same(review['plan'], ref(str(ROOT/'experiments/kotlin/full90-v2/plan-v1.json'),r.PLAN_SHA),
         'Result review names another plan')
    require(review['verified_file_pins'].get(review['plan']['path']) == r.PLAN_SHA and
            all(review['verified_file_pins'].get(path)==digest for path,digest in plan['pins'].items()),
            'Reconciliation omitted a prerequisite pin')
    require(work['schema']=='kotlin-retained-compiled-work-qualified-v2' and
            work['status']=='all20-retained-required-work-qualified' and work['source_work_qualified'] is True and
            p.integer(work['compiled_work_profiles'],20),'Required-work qualification missing')
    require(counts['schema']=='kotlin-qualified-source-counts-v1' and
            counts['status']=='twenty-retained-canonical-source-counts-qualified' and
            counts['canonical_loc_qualified'] is True and counts['formatted_loc_qualified'] is False and
            counts['formatted_loc'] is None,'Qualified canonical-only source counts required')
    same(metadata,p.strict_json(read_raw(str(RUNTIME_METADATA),RUNTIME_METADATA_SHA)),
         'Reviewed runtime metadata differs')
    require(metadata['schema']=='kotlin-publication-runtime-metadata-v1' and
            metadata['runtime_publication_metadata_qualified'] is True and metadata['chart_admission'] is False and
            metadata['key']==metadata['family']=='kotlin' and metadata['platform']=='jvm' and
            metadata['execution']==['jit'] and metadata['typing']=='static' and metadata['memory']==['gc'] and
            metadata['observed_in_each_timed_process'] is False,'Runtime metadata scope differs')
    same(metadata['plan'],review['plan'],'Runtime metadata names another plan')
    version=metadata['compiler_version_evidence']; original=metadata['jdk_release_original']
    require(plan['pins'].get(version['path'])==version['sha256'] and
            plan['pins'].get(original['path'])==original['sha256']==JDK_RELEASE_SHA,
            'Runtime versions are not bound to measured closure')
    require('info: kotlinc-jvm 2.4.21 (JRE 25.0.4.1+1-LTS)' in read_raw(version['path'],version['sha256']).decode(),
            'Retained compiler version differs')
    release=read_raw(original['path'],original['sha256'])
    require(release==read_raw(str(JDK_RELEASE),JDK_RELEASE_SHA),'Retained JDK release copy differs')
    for entry in ('IMPLEMENTOR="Eclipse Adoptium"','JVM_VERSION="25.0.4.1+1-LTS"','OS_ARCH="aarch64"','OS_NAME="Darwin"'):
        require(entry in release.decode(),'JDK identity differs: '+entry)
    counted={row['id']:row for row in counts['profiles']}
    qualified={row['id']:row for row in work['profiles']}
    expected={row['id'] for row in profiles.values() if row['language']=='kotlin'}
    require(len(counted)==len(qualified)==20 and set(counted)==set(qualified)==expected and
            set(review['profiles'])==set(profiles),'Qualified cohorts differ')
    for identity in expected:
        row,count=profiles[identity],counted[identity]
        require(qualified[identity]['source_work_qualified'] is True and
                row['source_work_qualified'] is row['canonical_loc_qualified'] is count['canonical_loc_qualified'] is True and
                row['formatted_loc_qualified'] is count['formatted_loc_qualified'] is False and
                row['formatted_loc'] is count['formatted_loc'] is None and
                (row['canonical_loc'],row['physical_loc'])==(count['canonical_loc'],count['original_physical_loc']),
                'Profile work/count qualification differs')
        same(row['command'][1:5],metadata['jvm_flags'],'Measured JVM policy differs')
        require(row['optimization_claim'] is False and row['alias_of'], 'Alias policy differs')
    return profiles,counted


def sample_records(measured, row, plan, review, read_raw):
    result, good = [], []
    for number in measured['attempts']:
        path = plan['output']+'/attempts/'+f'{number:03d}-{row["id"]}.json'
        digest = review['verified_file_pins'][path]
        supervised = path[:-5]+'.supervisor.json'
        item = p.strict_json(read_raw(supervised, review['verified_file_pins'][supervised]))
        require(item['attempt'] == number and item['key'] == row['key'] and item['id'] == row['id']
                and item['benchmark'] == row['benchmark'], 'Sample evidence belongs to another form')
        qualified = number != measured['failed_attempt']
        require(type(item['qualified']) is bool and item['qualified'] == qualified,
                'Sample qualification differs from independent reconciliation')
        if qualified:
            good.append(item['seconds'])
        outer = plan['output']+'/outer-supervisor/'+f'{number:03d}-{row["id"]}.json'
        result.append(dict(attempt=number, qualified=qualified, seconds=item.get('seconds'),
            started_at=item['started_at'], finished_at=item['finished_at'], stdout_bytes=item['stdout_bytes'],
            stdout_sha256=item['stdout_sha256'], validation=item.get('validation'), error=item.get('error'),
            error_type=item.get('error_type'), raw_evidence=ref(path, digest),
            supervisor_evidence=ref(supervised, review['verified_file_pins'][supervised]),
            outer_supervisor_evidence=ref(outer, review['verified_file_pins'][outer])))
    same(good, measured['samples_seconds'], 'Export samples differ from the independent reconciliation')
    return result


def build_candidate(plan, review, work, counts, metadata, read_raw):
    profiles,counted=validate_prerequisites(plan,review,work,counts,metadata,read_raw)
    inventory, controls, files, endpoints, excluded = {}, {}, {}, {}, []
    all_sources = []
    for bench in r.BENCHES:
        control_key = bench+':kotlin-full-study:mech-control'
        control_row, measured_control = profiles[control_key], review['profiles'][control_key]
        control = copy.deepcopy(measured_control)
        control['source_evidence'] = ref(control_row['source'], control_row['source_sha256'])
        control['sample_execution_metadata'] = sample_records(measured_control, control_row, plan, review, read_raw)
        controls[bench] = control
        candidates = []
        for variant in ('compact', 'optimized'):
            identity = f'kotlin-{bench}-{variant}'
            row, measured, count = profiles[identity], review['profiles'][identity], counted[identity]
            for field in ('id', 'language', 'benchmark', 'source', 'source_sha256', 'binary_sha256'):
                same(measured[field], row[field], 'Measured export identity differs: '+field)
            sources = [counts['files'][name] for name in count['inputs']]
            same([(item['source'],item['source_sha256'],item['role']) for item in sources],
                 [(item['path'],item['sha256'],item['role']) for item in row['physical_inputs']],
                 'Counted authored bundle differs')
            same([item['role'] for item in sources],list(ROLES),'Both authored roles required')
            file_ids,roles=[],{}
            for owner_id,source in zip(count['inputs'],sources):
                digest=source['source_sha256']; retained=str(SOURCE_ROOT/owner_id/'source.kt')
                psi=str(SOURCE_ROOT/owner_id/'psi.json')
                require(plan['pins'].get(retained)==digest==source['native_artifacts']['source.kt']['sha256'] and
                        plan['pins'].get(psi)==source['native_artifacts']['psi.json']['sha256'],
                        'Counted retained source/PSI missing from measured closure')
                raw=read_raw(retained,digest);code=raw.decode('utf-8')
                require(hashlib.sha256(raw).hexdigest()==digest,'Retained source bytes differ')
                public=str(Path(retained).relative_to(ROOT))
                record=dict(sha256=digest,name='Main.kt' if source['role']=='application' else 'Support.kt',
                            code=code,archive_path=public)
                if digest in files: same(files[digest]['code'],code,'Source hash collision')
                else: files[digest]=record
                require(digest not in roles,'Duplicate content within authored role bundle')
                file_ids.append(digest)
                roles[digest]=dict(role=source['role'],source_path=public,
                    original_source=ref(source['source'],digest),retained_source=ref(retained,digest),
                    normalized_loc=source['canonical_loc'],physical_loc=source['original_physical_loc'],
                    formatted_loc=None,native_psi=ref(psi,source['native_artifacts']['psi.json']['sha256']))
                all_sources.append((retained,digest))
            require(row['canonical_loc']==sum(item['canonical_loc'] for item in sources) and
                    row['physical_loc']==sum(item['original_physical_loc'] for item in sources),
                    'Export source totals differ')
            successful, control_ok = measured['full_workload_qualified'], measured_control['full_workload_qualified']
            eligible = successful and control_ok
            if successful:
                median, sd = p.three_statistics(measured['samples_seconds'])
                require(median == measured['median_seconds'] and math_close(sd, measured['sample_stdev_seconds']),
                        'Export statistics differ')
            else:
                require(measured['median_seconds'] is measured['sample_stdev_seconds'] is measured['time_x_mech'] is None,
                        'Failed form cannot export a median or ratio')
            ratio = measured['median_seconds']/measured_control['median_seconds'] if eligible else None
            same(measured['time_x_mech'], ratio, 'Matched control ratio differs')
            public_key = bench+':'+identity
            entry = dict(key=public_key, receipt_key=identity, id=identity, benchmark=bench, variant=variant,
                language='kotlin', loc=row['canonical_loc'], canonical_loc=row['canonical_loc'],
                formatted_loc=row['formatted_loc'], physical_loc=row['physical_loc'], loc_metric='statement-normalized',
                files=file_ids, file_roles=roles, seconds=measured['median_seconds'],
                samples=copy.deepcopy(measured['samples_seconds']), timing_sd=measured['sample_stdev_seconds'],
                measurement_status='measured' if successful else 'failed-full-workload',
                source_work_qualified=True, canonical_loc_qualified=True, formatted_loc_qualified=False,
                full_workload_qualified=successful, matched_control_qualified=control_ok,
                eligible_for_publication_review=eligible, chart_admission=False, source_alias_note='Retained compact/optimized labels are source aliases with independently measured samples.', source_alias_of=row['alias_of'],
                distinct_optimization_claimed=False, timing_alias_of=None,
                command=row['command'], runtime_environment=row['runtime_environment'], cwd=row['cwd'],
                source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'], class_artifacts=row['class_artifacts'],
                execution_mode='jit', retained_owner_evidence=dict(classes=row['classes'], class_owner_names=row['class_owner_names']),
                sample_execution_metadata=sample_records(measured, row, plan, review, read_raw),
                matched_mech_control_key=control_key, time_ratio_to_matched_mech=ratio,
                failed_attempt=measured['failed_attempt'], evidence=copy.deepcopy(review.get('source_evidence', {})),
                exclusion_reason=None if eligible else ('subject-full-workload-failed' if not successful else 'matched-Mech-control-failed'))
            inventory[public_key] = entry
            if eligible:
                candidates.append(entry)
            else:
                excluded.append(identity)
        if candidates:
            fast = min(candidates, key=lambda v:(v['seconds'], v['canonical_loc'], v['key']))
            small = min(candidates, key=lambda v:(v['canonical_loc'], v['seconds'], v['key']))
            endpoints[bench] = dict(fast=fast['key'], small=small['key'],
                programs=list(dict.fromkeys([small['key'], fast['key']])), chart_admission=False)
        else:
            endpoints[bench] = dict(fast=None, small=None, programs=[], chart_admission=False)
    metadata=copy.deepcopy(metadata)
    metadata.update(runtime_policy=metadata['runtime']+'; '+' '.join(metadata['jvm_flags']),
        regex_support='Retained JVM regular-expression library',evidence_scope=metadata['runtime_evidence_scope'],
        runtime_gc_configuration_observed=False,gc_numeric_defaults_claimed=False,
        qualification_evidence=copy.deepcopy(plan['qualified_work']),
        metadata_evidence=ref(str(RUNTIME_METADATA),RUNTIME_METADATA_SHA))
    require(len(inventory) == 20 and len(all_sources) == 40 and len(controls) == len(endpoints) == 10,
            'Private export inventory incomplete')
    return dict(schema='kotlin-private-publication-candidate-v1',
        status='validated-evidence-candidate-awaiting-explicit-publication-review',
        chart_admission=False, dataset_files_changed=False, native_processes_started=0,
        language_metadata=metadata, program_inventory=inventory, files=files, matched_mech_controls=controls,
        endpoint_proposals=endpoints, excluded_profiles=excluded,
        plan=review['plan'], report=review['report'], terminal=review['terminal'],
        actual_full_native_processes=review['actual_full_native_processes'], qualified_samples=review['qualified_samples'],
        planned_kotlin_samples=60, planned_matched_mech_samples=30, skipped_slots=review['skipped_slots'],
        failed_profiles=review['failed_profiles'], complete_stdout_retained=False,
        full_output_evidence=review['full_output_evidence'], resource_evidence=review['resource_evidence'],
        publication_requirements=['explicit candidate review', 'dataset/catalog/site validation and separately authorized publication'])


def math_close(left, right):
    import math
    return p.finite(right) and right >= 0 and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def write_new(path, value):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    identity=None
    try:
        with path.open('xb') as stream:
            stat=os.fstat(stream.fileno());identity=(stat.st_dev,stat.st_ino)
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
    except BaseException:
        if identity is not None and path.is_file() and not path.is_symlink():
            stat=path.stat()
            if (stat.st_dev,stat.st_ino)==identity:
                current=path.read_bytes()
                if len(current)<=len(raw) and raw.startswith(current):path.unlink()
        raise
    return hashlib.sha256(raw).hexdigest()


def remove_owned(path, expected_sha):
    if expected_sha is not None and path.is_file():
        require(hashlib.sha256(path.read_bytes()).hexdigest()==expected_sha,
                'Owned output changed; preserving altered bytes')
        path.unlink()


@contextmanager
def guarded_closure(check, cleanup):
    """Recheck publication-only pins and clean failures while outer leases live."""
    try:
        yield
        check()
    except BaseException:
        cleanup()
        raise


def save_candidate(args, target):
    owned_sha=None
    controller=Path(__file__).resolve()
    controller_sha=hashlib.sha256(controller.read_bytes()).hexdigest()
    def remove_success(): remove_owned(target,owned_sha)
    def check_metadata():
        final_pins=dict(EXTRA_PINS,**{str(controller):controller_sha,
            str(args.reconciliation):args.reconciliation_sha256})
        for path,digest in final_pins.items():
            require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,'Publication metadata changed at closure')
    try:
        with r.review_files(args.plan,args.plan_sha256,args.durable_directory,on_exit_failure=remove_success) as fresh:
            with guarded_closure(check_metadata,remove_success):
                saved_bytes=args.reconciliation.read_bytes()
                require(hashlib.sha256(saved_bytes).hexdigest()==args.reconciliation_sha256,
                        'Independently saved reconciliation changed')
                same(fresh,p.strict_json(saved_bytes),'Fresh independent reconciliation differs from reviewed result')
                plan=p.strict_json(args.plan.read_bytes())
                def read_raw(path,digest):
                    require(fresh['verified_file_pins'].get(path)==digest or EXTRA_PINS.get(path)==digest,
                            'Export reads only independently verified evidence')
                    raw=Path(path).read_bytes()
                    require(hashlib.sha256(raw).hexdigest()==digest,'Export evidence changed during read')
                    return raw
                def document(binding):return p.strict_json(read_raw(binding['path'],binding['sha256']))
                work,counts=document(plan['qualified_work']),document(plan['qualified_source_counts'])
                metadata=document(ref(str(RUNTIME_METADATA),RUNTIME_METADATA_SHA))
                result=build_candidate(plan,fresh,work,counts,metadata,read_raw)
                result['reconciliation']=ref(str(args.reconciliation.resolve()),args.reconciliation_sha256)
                result['export_controller']=ref(str(controller),controller_sha)
                for path,digest in EXTRA_PINS.items():read_raw(path,digest)
                owned_sha=write_new(target,result)
        # No success is returned until the independent context exit recheck passes.
        return result,owned_sha
    except BaseException:
        remove_success()
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--durable-directory',type=Path,required=True)
    parser.add_argument('--reconciliation',type=Path,required=True)
    parser.add_argument('--reconciliation-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B')
    plan=p.strict_json(args.plan.read_bytes());target=args.output.resolve()
    require(not target.exists() and target.parent.is_dir() and
            not target.is_relative_to(Path(plan['output']).resolve()) and
            not any(target.is_relative_to(ROOT/name) for name in ('data','site')),
            'Candidate requires a new private file outside timing evidence and publication paths')
    result,digest=save_candidate(args,target)
    print(json.dumps(dict(output=str(target),sha256=digest,inventory_forms=20,
        excluded_profiles=result['excluded_profiles'],dataset_files_changed=False,chart_admission=False)),flush=True)


if __name__=='__main__':main()
