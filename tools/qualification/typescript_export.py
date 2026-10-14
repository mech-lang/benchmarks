"""Prepare a private TypeScript metadata/publication candidate from closed evidence.

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
RECONCILER = Path(__file__).with_name('typescript_reconcile.py')
# Independently reviewed source; the file phase binds this and both primitives.
RECONCILER_SHA = '6278c660388210906b28338f1b288281e0b2b3c81adaba12300708ac55f9c9ee'


def load_reconciler():
    raw = RECONCILER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECONCILER_SHA:
        raise ValueError('Independent TypeScript reconciler changed')
    spec = importlib.util.spec_from_file_location('typescript_candidate_reconciliation', RECONCILER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(RECONCILER), 'exec'), module.__dict__)
    return module


r = load_reconciler()
p, require, same = r.p, r.require, r.same
RUNTIME_METADATA = ROOT/'experiments/typescript/full60-v1/runtime-metadata-v1.json'
RUNTIME_METADATA_SHA = '6d5332b6fd973ad4344aa8c0743c9361562384bb434005011a77e2b92c01e602'
EXTRA_PINS = {'/private/tmp/mech-benchmark-completion/experiments/typescript/full60-v1/runtime-metadata-v1.json': '6d5332b6fd973ad4344aa8c0743c9361562384bb434005011a77e2b92c01e602',
 '/private/tmp/mech-benchmark-completion/experiments/typescript/native-stage-v1/run-v1/reader/evidence/started.json': 'd02b2d37716f26ddd72fcb6d00cd6f33d2095ef0a337d719b62b6b484e1d1d08',
 '/private/tmp/mech-benchmark-completion/experiments/typescript/source-v1/tsconfig.json': 'ebde65206600290649a1ab699767c8da341f1460ebb6e50c8d4b7c83d1d2053d',
 '/private/tmp/mech-benchmark-completion/experiments/typescript/toolchain-v1/native-versions-v1/node/stdout.bin': 'b7677d3ec37ee1897ba07dc2cfe8292fe421c9ac93396cca5bbece486d1a2a41',
 '/private/tmp/mech-benchmark-completion/experiments/typescript/toolchain-v1/native-versions-v1/typescript/stdout.bin': '41024334022fa58f9c7337359517de307cbcfc6055c19f2b734245eacc2fe97a'}
ROLES = ('application',)


def ref(path, digest):
    require(Path(path).is_absolute() and p.digest(digest), 'Invalid evidence reference')
    return dict(path=path, sha256=digest)


def validate_prerequisites(plan, review, work, counts, metadata, read_raw):
    _,profiles=r.schedule(plan)
    require(review['schema']==r.SCHEMA and review['status']=='full60-reconciled-awaiting-publication-review'
        and review['file_integrity_verified'] is review['common_mutex_held'] is True
        and p.integer(review['common_mutex_inode'],p.LOCK_INODE)
        and review['runtime_publication_metadata_qualified'] is True and review['chart_admission'] is False,
        'Completed independent TypeScript reconciliation required')
    require(p.digest(review['plan']['sha256'])
        and review['verified_file_pins'].get(review['plan']['path'])==review['plan']['sha256']
        and all(review['verified_file_pins'].get(path)==digest for path,digest in plan['pins'].items()),
        'Reconciliation omitted a prerequisite pin')
    require(work['schema']=='typescript-qualified-required-work-v1' and work['source_work_qualified'] is work['required_work_qualified'] is True
        and work['qualified_contracts']==27 and work['full_timings_qualified'] is work['chart_admission'] is False,
        'Retained required-work admission missing')
    require(counts['schema']=='typescript-canonical-source-owner-review-v1'
        and counts['status']=='ten-authored-source-canonical-counts-qualified'
        and counts['canonical_loc_qualified'] is True and counts['formatted_loc_qualified'] is False and counts['formatted_loc'] is None,
        'Canonical authored-source admission missing')
    same(metadata,p.strict_json(read_raw(str(RUNTIME_METADATA),RUNTIME_METADATA_SHA)),'Reviewed publication metadata differs')
    require(metadata['schema']=='typescript-publication-runtime-metadata-v1'
        and metadata['key']==metadata['family']=='typescript' and metadata['platform']=='javascript'
        and metadata['execution']==['jit'] and metadata['typing']=='static' and metadata['memory']==['gc']
        and metadata['runtime_publication_metadata_qualified'] is True and metadata['chart_admission'] is False
        and metadata['runtime_flags']==[],'Publication runtime or classification differs')
    binding=metadata['qualified_runtime_evidence'];same(binding,plan['qualified_runtime'],'Runtime qualification link differs')
    runtime=p.strict_json(read_raw(binding['path'],binding['sha256']))
    require(runtime['runtime_publication_metadata_qualified'] is runtime['declared_runtime_dependency_closure_qualified'] is True,
        'Runtime metadata is unqualified')
    same(metadata['runtime_evidence_scope'],runtime['qualification_scope'],'Runtime scope differs')
    same(review['runtime_dependency_scope'],runtime['qualification_scope'],'Reconciliation runtime scope differs')
    for item in (metadata,review,runtime):
        require(item['actual_loaded_image_inventory_observed'] is item['observed_in_each_timed_process'] is False,
            'Static dependency evidence cannot become a per-process observation')
    same(metadata['node'],ref(r.NODE,r.NODE_SHA),'Another runtime executable')
    for field,expected in [('compiler_version_evidence','Version7.0.2'),('node_version_evidence','v24.19.0')]:
        binding=metadata[field];observed=read_raw(binding['path'],binding['sha256']).decode().strip().replace(' ','')
        same(observed,expected,'Retained native version differs')
    binding=metadata['native_versions_evidence'];started=p.strict_json(read_raw(binding['path'],binding['sha256']))
    require(started['typescript_version']=='7.0.2' and started['versions']['node']=='24.19.0'
        and started['versions']['v8']=='13.6.233.17-node.51' and started['node']==r.NODE,'Recorded native versions differ')
    binding=metadata['compiler_options_evidence'];options=p.strict_json(read_raw(binding['path'],binding['sha256']))['compilerOptions']
    require(options['strict'] is options['noEmitOnError'] is options['sourceMap'] is options['inlineSources'] is True
        and options['allowJs'] is False,'Typed strict source compilation differs')
    compiled=metadata['compiled_artifact_evidence']
    require(plan['pins'].get(compiled['path'])==compiled['sha256']==r.QUALIFICATION_REFS['compiled_report'][1],
        'Runtime metadata names another compiler stage')
    counted={row['id']:row for row in counts['profiles']}
    expected={row['id'] for row in profiles.values() if row['language']=='typescript'}
    require(len(counted)==10 and set(counted)==set(work['qualified_profiles'])==expected and set(review['profiles'])==set(profiles),
        'Qualified cohorts differ')
    for identity in expected:
        row,count=profiles[identity],counted[identity]
        require(row['source_work_qualified'] is row['canonical_loc_qualified'] is count['canonical_loc_qualified'] is True
            and row['formatted_loc_qualified'] is count['formatted_loc_qualified'] is False
            and row['formatted_loc'] is count['formatted_loc'] is None
            and (row['canonical_loc'],row['physical_loc'])==(count['canonical_loc'],count['physical_loc'])
            and (row['source'],row['source_sha256'])==(r.absolute_ref(count['source'])['path'],count['source']['sha256']),
            'Source work/count identity differs')
        require(row['command'][:2]==[r.NODE,row['javascript']['path']] and row['diagnostic_flags']==row['runtime_policy_changes']==[]
            and row['runtime_environment']['UV_THREADPOOL_SIZE']=='8'
            and row['optimization_claim'] is False and row['source_alias_of'] is None,
            'Direct default Node source identity differs')
        for field in ('javascript','source_map'):
            binding=row[field];require(plan['pins'].get(binding['path'])==binding['sha256'],'Unbound emitted application evidence')
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
            started_at=item['started_at'], finished_at=item['finished_at'],
            stdout_bytes=item['stdout_bytes'] if qualified else item.get('stdout_bytes'),
            stdout_sha256=item['stdout_sha256'] if qualified else item.get('stdout_sha256'),
            validation=item.get('validation'), error=item.get('error'),
            error_type=item.get('error_type'), raw_evidence=ref(path, digest),
            supervisor_evidence=ref(supervised, review['verified_file_pins'][supervised]),
            outer_supervisor_evidence=ref(outer, review['verified_file_pins'][outer])))
    same(good, measured['samples_seconds'], 'Export samples differ from the independent reconciliation')
    return result


def build_candidate(plan, review, work, counts, metadata, read_raw):
    profiles, counted = validate_prerequisites(plan, review, work, counts, metadata, read_raw)
    inventory, controls, files, endpoints, excluded = {}, {}, {}, {}, []
    for bench in r.BENCHES:
        control_key = bench+':typescript-full-study:mech-control'
        control_row, measured_control = profiles[control_key], review['profiles'][control_key]
        control = copy.deepcopy(measured_control)
        control['source_evidence'] = ref(control_row['source'], control_row['source_sha256'])
        control['sample_execution_metadata'] = sample_records(measured_control, control_row, plan, review, read_raw)
        controls[bench] = control
        identity = 'typescript-'+bench+'-v1'
        row, measured, count = profiles[identity], review['profiles'][identity], counted[identity]
        for field in ('id', 'language', 'benchmark', 'source', 'source_sha256', 'binary_sha256'):
            same(measured[field], row[field], 'Measured export identity differs: '+field)
        same(row['physical_inputs'], [dict(path=row['source'], sha256=row['source_sha256'],
                                          role='application', counted=True)], 'Authored bundle differs')
        digest, source = row['source_sha256'], row['source']
        require(plan['pins'].get(source) == digest and plan['pins'].get(row['compiled_source']) == digest,
                'Authored/compiled source missing from measured closure')
        raw = read_raw(source, digest)
        require(raw == read_raw(row['compiled_source'], digest), 'Compiled source differs from counted source')
        public = str(Path(source).relative_to(ROOT))
        code = raw.decode('utf-8')
        if digest in files:
            same(files[digest]['code'], code, 'Source hash collision')
        else:
            files[digest] = dict(sha256=digest, name=Path(source).name, code=code, archive_path=public)
        projection = r.absolute_ref(count['projection'])
        require(plan['pins'].get(projection['path']) == projection['sha256'], 'Canonical projection missing')
        roles = {digest:dict(role='application', source_path=public, original_source=ref(source,digest),
            retained_source=ref(source,digest), compiled_source=ref(row['compiled_source'],digest),
            normalized_loc=row['canonical_loc'], physical_loc=row['physical_loc'], formatted_loc=None,
            canonical_projection=projection)}
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
        key = bench+':'+identity
        entry = dict(key=key, receipt_key=identity, id=identity, benchmark=bench, variant='v1', language='typescript',
            loc=row['canonical_loc'], canonical_loc=row['canonical_loc'], formatted_loc=None, physical_loc=row['physical_loc'],
            loc_metric='statement-normalized', files=[digest], file_roles=roles, seconds=measured['median_seconds'],
            samples=copy.deepcopy(measured['samples_seconds']), timing_sd=measured['sample_stdev_seconds'],
            measurement_status='measured' if successful else 'failed-full-workload', source_work_qualified=True,
            canonical_loc_qualified=True, formatted_loc_qualified=False, full_workload_qualified=successful,
            matched_control_qualified=control_ok, eligible_for_publication_review=eligible, chart_admission=False,
            source_alias_of=None, distinct_optimization_claimed=False, timing_alias_of=None,
            command=row['command'], runtime_environment=row['runtime_environment'], cwd=row['cwd'],
            source_sha256=digest, binary_sha256=row['binary_sha256'], javascript=copy.deepcopy(row['javascript']),source_map=copy.deepcopy(row['source_map']),native_ast=copy.deepcopy(count['native_ast']),
            execution_mode='jit',retained_owner_evidence=dict(authored_source=ref(source,digest),compiled_source=ref(row['compiled_source'],digest)),
            sample_execution_metadata=sample_records(measured,row,plan,review,read_raw),
            matched_mech_control_key=control_key, time_ratio_to_matched_mech=ratio,
            failed_attempt=measured['failed_attempt'], evidence=copy.deepcopy(review['source_evidence']),
            exclusion_reason=None if eligible else ('subject-full-workload-failed' if not successful else 'matched-Mech-control-failed'))
        inventory[key] = entry
        endpoints[bench] = dict(fast=key if eligible else None, small=key if eligible else None,
                               programs=[key] if eligible else [], chart_admission=False)
        if not eligible:
            excluded.append(identity)
    metadata = copy.deepcopy(metadata)
    metadata.update(runtime_policy=metadata['runtime']+'; direct Node defaults; UV_THREADPOOL_SIZE=8',
        regex_support='Retained V8 RegExp implementation', evidence_scope=metadata['runtime_evidence_scope'],
        runtime_gc_configuration_observed=False, gc_numeric_defaults_claimed=False,
        qualification_evidence=copy.deepcopy(plan['qualified_work']), metadata_evidence=ref(str(RUNTIME_METADATA),RUNTIME_METADATA_SHA))
    require(len(inventory) == 10 and len(controls) == len(endpoints) == 10, 'Private export inventory incomplete')
    return dict(schema='typescript-private-publication-candidate-v1',
        status='validated-evidence-candidate-awaiting-publication-review', chart_admission=False,
        dataset_files_changed=False, native_processes_started=0, language_metadata=metadata,
        program_inventory=inventory, files=files, matched_mech_controls=controls, endpoint_proposals=endpoints,
        excluded_profiles=excluded, plan=review['plan'], report=review['report'], terminal=review['terminal'],
        actual_full_native_processes=review['actual_full_native_processes'], qualified_samples=review['qualified_samples'],
        planned_typescript_samples=30, planned_matched_mech_samples=30, skipped_slots=review['skipped_slots'],
        failed_profiles=review['failed_profiles'], complete_stdout_retained=False,
        full_output_evidence=review['full_output_evidence'], resource_evidence=review['resource_evidence'],
        publication_requirements=['candidate review', 'dataset/catalog/site validation'])

def math_close(left, right):
    import math
    return p.finite(right) and right >= 0 and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def write_new(path, value, ownership=None):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    identity=None
    try:
        with path.open('xb') as stream:
            stat=os.fstat(stream.fileno());identity=(stat.st_dev,stat.st_ino)
            if ownership is not None:ownership.update(identity=identity,raw=raw)
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
    owned={}
    controller=Path(__file__).resolve()
    controller_sha=hashlib.sha256(controller.read_bytes()).hexdigest()
    def remove_success():
        if owned_sha is not None and (target.exists() or target.is_symlink()):
            identity=target.lstat()
            require(not target.is_symlink() and (identity.st_dev,identity.st_ino)==owned['identity'],
                    'Owned candidate path replaced; preserving unrelated bytes')
            remove_owned(target,owned_sha)
    def check_metadata():
        final_pins=dict(EXTRA_PINS,**{str(controller):controller_sha,
            str(args.reconciliation):args.reconciliation_sha256})
        for path,digest in final_pins.items():
            require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,'Publication metadata changed at closure')
        if owned_sha is not None:
            identity=target.lstat()
            require(not target.is_symlink() and (identity.st_dev,identity.st_ino)==owned['identity'],
                    'Candidate path changed before closure')
            require(target.read_bytes()==owned['raw'],'Candidate bytes changed before closure')
            identity=target.lstat()
            require(not target.is_symlink() and (identity.st_dev,identity.st_ino)==owned['identity'],
                    'Candidate path changed during closure')
    try:
        with r.review_files(args.plan,args.plan_sha256,args.durable_directory,on_exit_failure=remove_success, final_consumer_check=check_metadata) as fresh:
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
                owned_sha=write_new(target,result,owned)
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
    print(json.dumps(dict(output=str(target),sha256=digest,inventory_forms=10,
        excluded_profiles=result['excluded_profiles'],dataset_files_changed=False,chart_admission=False)),flush=True)


if __name__=='__main__':main()
