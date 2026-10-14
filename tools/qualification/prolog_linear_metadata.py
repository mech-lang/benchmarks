"""Review runtime/publication metadata for the closed Prolog linear continuation.

No producer, sampler or native runtime is executed. CLI hashing and independent
ledger replay require the four original owner/suite/common leases. This additive
review preserves both sample cohorts and never admits charts or edits receipts.
"""
import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RECONCILER = Path(__file__).with_name('prolog_linear_reconcile.py')
RECONCILER_SHA = '28535a8268f6eba1947bf2e0d520d594684e153259604c136245d45ceb25ee1a'
METADATA = Path(__file__).with_name('prolog_metadata.py')
METADATA_SHA = '18b4b74fdec37e50fec922ce0ed9e5f99678864b28269933f9e9f76d3e49f7c5'


def module(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Frozen independent reviewer changed: '+str(path))
    spec = importlib.util.spec_from_file_location(path.stem+'_linear_metadata', path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


l = module(RECONCILER, RECONCILER_SHA)
m = module(METADATA, METADATA_SHA)
r, p, require, same = l.r, l.p, l.require, l.same
CONFIG, CONFIG_SHA, IMAGES, IMAGE_SHA = m.CONFIG, m.CONFIG_SHA, m.IMAGES, m.IMAGE_SHA
VERSION, PREFIX = m.VERSION, m.PREFIX
runtime_flags, successful = m.runtime_flags, m.successful
SCHEMA = 'prolog-linear-recorded-runtime-metadata-v1'
COMPILE_WARNING = (b'Warning: [Thread main] Local definition of clbg_prepare:main/0 '
                   b'overrides weak import from clbg_revcomp_linear\n')


def runtime_context(plan, read, read_raw):
    config = read(CONFIG, CONFIG_SHA)
    require(config['status'] == 'qualified-runtime-discovery' and config['chart_admission'] is False
            and config['architecture'] == 'arm64' and config['runtime_backend'] == 'swi-native-bytecode-vm'
            and config['default_gc_observed'] is True and config['bounded_observed'] is False,
            'Runtime discovery is unqualified')
    same(config['version_components'], [10, 0, 2], 'Runtime version differs')
    same(config['environment'], {'SWI_HOME_DIR': config['home']}, 'Runtime environment differs')
    require(plan['pins'][config['binary']] == config['binary_sha256'], 'Runtime executable unbound')
    feature = read(config['actual_feature_probe'], config['actual_feature_probe_sha256'])
    runtime_flags(feature['runtime'], config['home'])
    require(feature['pcre_version'] == config['pcre_version'] == '10.40 2022-04-14'
            and feature['regex_jit_requested'] is False, 'Regex runtime observation differs')
    for field in ('feature_probe_owned_receipt', 'version_receipt'):
        ref = config[field]
        require(ref['status'] == 'passed', 'Runtime receipt was not qualified')
        successful(read(ref['receipt'], ref['receipt_sha256']), ref['command'])
        stdout = read_raw(ref['stdout'], ref['stdout_sha256'])
        require(not read_raw(str(Path(ref['stdout']).with_suffix('.stderr'))), 'Runtime inspection stderr')
        if field == 'version_receipt':
            same(ref['command'], [config['binary'], '--version'], 'Version command differs')
            require(stdout.decode() == VERSION, 'Saved version output differs')
        else:
            same(ref['command'][:6], [config['binary'], *PREFIX], 'Probe uses different runtime flags')
            require(stdout == b'', 'Feature probe emitted unexpected stdout')
    library_ref = config['source_library_review']
    libraries = read(library_ref['path'], library_ref['sha256'])
    require(libraries['status'] == 'passed' and libraries['root_review'] is True
            and libraries['actual_feature_sha256'] == config['actual_feature_probe_sha256']
            and libraries['native_image_closure_sha256'] == IMAGE_SHA, 'Runtime source review is unbound')
    for path, sha in libraries['source_pins'].items():
        require(plan['pins'].get(path) == sha, 'Runtime source review input unpinned')
    images = read(IMAGES, IMAGE_SHA)
    require(images['status'] == 'passed-native-image-closure' and images['selected_architecture'] == 'arm64'
            and images['executable'] == config['binary'] and images['chart_admission'] is False,
            'Native image closure differs')
    same(sorted(images['image_pins']), sorted(config['loaded_native_images']), 'Native image inventory differs')
    require(len(images['image_pins']) == 7 and len(images['contexts']) == 7, 'Incomplete image contexts')
    for path, sha in images['image_pins'].items():
        require(plan['pins'].get(path) == sha, 'Native image unpinned')
    require({c['image'] for c in images['contexts']} == set(images['image_pins']), 'Image contexts disagree')
    os_images = set()
    for context in images['contexts']:
        require(context['selected_architecture'] == context['mach_header']['architecture'] == 'arm64'
                and 'arm64' in context['architectures'], 'Native architecture differs')
        for dep in context['dependencies']:
            if dep['scope'] == 'OS-image-not-hashed':
                require(dep['install_name'].startswith(('/usr/lib/', '/System/Library/')), 'Unexpected unbound image')
                os_images.add(dep['install_name'])
            else:
                require(dep['scope'] == 'private-app-image'
                        and images['image_pins'].get(dep['path']) == dep['sha256'], 'Dependency outside private closure')
    closed_ref = config['closed_review']
    closed = read(closed_ref['path'], closed_ref['sha256'])
    require(closed['status'] == 'corrected-feature-and-private-images-passed'
            and p.integer(closed['feature_exit'], 0) and p.integer(closed['native_images'], 7),
            'Runtime discovery lacks terminal review')
    same(closed['runtime'], feature['runtime'], 'Closed runtime flags differ')
    same(sorted(closed['images']), sorted(images['image_pins']), 'Closed image inventory differs')
    return config, feature, images, os_images


def original_profile(plan, outcome, row, config, images, read):
    ref = row['compiler_bound_input_inventory']
    require(outcome['outputs'][Path(ref['path']).name] == ref['sha256'], 'Compiler inventory outside source seal')
    inventory = read(ref['path'], ref['sha256'])
    require(inventory['status'] == 'qualified-exact-authored-compiler-inputs'
            and inventory['source_sha256'] == row['source_sha256']
            and inventory['binary_sha256'] == row['binary_sha256'], 'Qualified compiler inputs differ')
    retained = inventory['independently_retained_compiler_input_evidence']
    for field in ('id', 'key', 'benchmark', 'variant', 'source', 'source_sha256', 'measured_source',
                  'binary', 'binary_sha256', 'command', 'cwd', 'runtime_environment', 'source_alias_of'):
        same(retained[field], row[field], 'Retained compiler profile differs: '+field)
    authored = {(s['path'], s['origin'], s['sha256']) for s in row['source_bundle']}
    same(sorted(authored), sorted((s['path'], s['origin'], s['sha256']) for s in inventory['files']),
         'Authored source bundle differs')
    support_names = ['clbg_io.pl']
    if row['benchmark'] in ('revcomp', 'knucleotide'):
        support_names.append('clbg_records.pl')
    require(len(authored) == len(row['source_bundle']) == 1+len(support_names),
            'Expected main and all counted helpers')
    qlf = retained['application_artifact_pins']
    expected_qlf = {str(Path(s['path']).with_suffix('.qlf')) for s in row['source_bundle']}
    require(set(qlf) == expected_qlf and all(plan['pins'].get(path) == sha for path, sha in qlf.items()),
            'QLF application artifacts unbound')
    command = [config['binary'], *PREFIX]
    for name in support_names:
        helper = next(s['path'] for s in row['source_bundle'] if Path(s['path']).name == name)
        command += ['-l', str(Path(helper).with_suffix('.qlf'))]
    application_qlf = str(Path(row['measured_source']).with_suffix('.qlf'))
    command += ['-s', application_qlf, '-g', f'clbg_io:run(clbg_{row["benchmark"]}:main)']
    if row['benchmark'] not in ('regexredux', 'revcomp', 'knucleotide'):
        command += ['--', '{n}']
    same(row['command'], command, 'Measured QLF load or runtime arguments differ')
    require(len(retained['compile_receipts']) == len(authored), 'Expected every authored QLF compilation receipt')
    require({c['source'] for c in retained['compile_receipts']} == {s['path'] for s in row['source_bundle']},
            'Compilation does not cover the authored bundle')
    for compile_ref in retained['compile_receipts']:
        successful(read(compile_ref['receipt'], compile_ref['receipt_sha256']), compile_ref['command'])
    loaded_ref = inventory['original_compiler_input_evidence']
    loaded = read(loaded_ref['receipt'], loaded_ref['receipt_sha256'])
    require(loaded['mode'] == 'inspect' and loaded['target'] == application_qlf, 'Preparation inspected another QLF')
    runtime_flags(loaded['runtime'], config['home'])
    for lib in loaded['foreign_libraries']:
        require(lib['resolved_path'] in images['image_pins'], 'Preparation loaded unbound foreign library')
    return qlf, retained['vendor_libraries'], loaded


def linear_preparation(entry, directory, command, environment, read, read_raw):
    """Replay the actual warning-bearing compile/inspection lifetime, not a success label."""
    same(entry['command'], command, 'Linear preparation command differs')
    require(entry['cwd'] == directory and entry['environment'] == environment
            and entry['compiler_warning'] is True and entry['expected_failure'] is False
            and entry['status'] == 'native-lifetime-verified', 'Linear preparation scope differs')
    records = {name:read(directory+'/'+name+'.json') for name in ('start','active','process')}
    final, active = records['process'], records['active']
    identity = active['identity']
    for record in records.values():
        same(record['command'], command, 'Linear preparation launch differs')
        same(record['environment'], environment, 'Linear preparation environment differs')
        require(record['cwd'] == directory and p.integer(record['stdin_bytes'],0)
                and record['stdin_sha256'] == hashlib.sha256(b'').hexdigest()
                and record['kind'] == 'prolog-revcomp-bounded'
                and record['inherited_common_mutex'] is True
                and p.integer(record['common_mutex_inode'],79859134)
                and p.integer(record['process_timeout_seconds'],30)
                and p.integer(record['cleanup_timeout_seconds'],5)
                and p.integer(record['maximum_process_group_rss_bytes'],2147483648)
                and p.integer(record['native_file_limit_bytes'],8388608)
                and p.integer(record['stdout_capture_limit_bytes'],8454144), 'Linear preparation policy differs')
    require(records['start']['status']=='starting' and records['start']['native_process_started'] is False
            and active['status']=='running' and active['native_process_started'] is True
            and p.integer(entry['pid']) and entry['pid']>0
            and entry['pid']==active['pid']==active['pgid']==identity['pid']==identity['pgid']
            and p.integer(identity['ppid'],58761), 'Linear compiler owner differs')
    same(final['identity'], identity, 'Linear compiler identity changed')
    require(final['pid']==final['pgid']==entry['pid'] and final['native_process_started'] is True
            and final['direct_child_reaped'] is True and final['remaining_process_group']==[]
            and final['stop_signals']==[] and final['cleanup_errors']==[]
            and not final.get('artifact_errors') and final['timed_out'] is False
            and p.integer(final['kernel_monitor_samples']) and final['kernel_monitor_samples']>0
            and 0<final['observed_peak_process_group_rss_bytes']<=2147483648
            and final['status']=='failed' and p.integer(final['exit_status'],0)
            and final['error_type']=='AssertionError'
            and final['error']=='Unexpected stderr; raw bytes retained', 'Linear preparation did not close normally')
    leader=final['leader_identity_before_reap']
    require(p.integer(leader['status'],5) and all(leader[k]==identity[k] for k in
            ('pid','pgid','ppid','birth_seconds','birth_microseconds')), 'Linear compiler birth/reap differs')
    require(p.timestamp(final['started_at'])<=p.timestamp(final['finished_at']), 'Inverted preparation lifetime')
    for name,expected in (('stdout',b''),('stderr',COMPILE_WARNING)):
        raw=read_raw(directory+'/'+name+'.bin')
        require(raw==expected and p.integer(final[name+'_bytes'],len(raw))
                and final[name+'_sha256']==entry[name+'_sha256']==hashlib.sha256(raw).hexdigest(),
                'Unknown preparation diagnostic or changed stream')
    raw=read_raw(directory+'/process.json')
    require(hashlib.sha256(raw).hexdigest()==entry['process_sha256'], 'Preparation process binding differs')


def linear_profile(plan, row, config, images, read, read_raw):
    qualification=plan['linear_qualification']; bounded=qualification['bounded']
    require(qualification['source_work_qualified'] is qualification['canonical_LOC_admitted'] is True
            and qualification['measured_runtime_scaling_qualified'] is False
            and qualification['full_timings_qualified'] is qualification['chart_admission'] is False,
            'Linear source qualification scope differs')
    report=read(bounded['report'],bounded['report_sha256'])
    require(report['status']=='bounded-conformance-passed-awaiting-work-and-source-count-review'
            and report['bounded_conformance_qualified'] is True and report['active'] is None
            and report['integrity_errors']==report['artifact_errors']==[]
            and p.integer(report['native_processes_started'],542)
            and p.integer(report['qualified_cases'],540) and p.integer(report['successful_cases'],470)
            and p.integer(report['rejected_cases'],70) and len(report['commands'])==542,
            'Incomplete linear bounded conformance')
    same(report['compiled_artifact'],row['compiled_artifact'],'Linear QLF changed')
    same(report['compiler_bound_source'],dict(path=row['measured_source'],sha256=l.SOURCE_SHA,counted=True),
         'Linear compiler source changed')
    artifact=row['compiled_artifact'];qlf={artifact['path']:artifact['sha256']}
    require(plan['pins'][artifact['path']]==l.QLF_SHA==artifact['sha256']
            and p.integer(artifact['bytes'],3352),'Unbound linear QLF')
    authored=str(Path(row['measured_source']).parent)
    helper=str(ROOT/'archive/languages/prolog/20261013/revisions/prepare-success-halt-v1/tools/prepare_qlf.pl')
    loaded=None
    for index,(mode,target) in enumerate((('compile',row['measured_source']),('inspect',artifact['path']))):
        directory=str(l.LINEAR/'bounded-run-v1'/mode)
        command=[config['binary'],*PREFIX,'-l',helper,'-g','clbg_prepare:main','--',mode,target,
                 directory+'/loaded-inputs.json',directory+'/candidate.wam',authored]
        entry=report['commands'][index]
        require(entry['id']==mode,'Linear preparation order differs')
        linear_preparation(entry,directory,command,config['environment'],read,read_raw)
        loaded=read(directory+'/loaded-inputs.json')
        require(loaded['mode']==mode and loaded['target']==target
                and loaded['wam']==directory+'/candidate.wam','Linear compiler inspected another artifact')
        runtime_flags(loaded['runtime'],config['home'])
        require(row['measured_source'] in loaded['loaded_sources']
                and all(path in plan['pins'] for path in loaded['loaded_sources']), 'Unpinned loaded compiler source')
        for library in loaded['foreign_libraries']:
            require(library['resolved_path'] in images['image_pins'], 'Unbound preparation native image')
    require(row['compiler_bound_input_inventory']['path']==str(l.LINEAR/'bounded-run-v1/inspect/loaded-inputs.json'),
            'Linear compiler inventory path differs')
    ref=qualification['source_count_review'];counts=read(ref['path'],ref['sha256'])
    require(counts['schema']=='prolog-linear-canonical-owner-review-v1'
            and counts['status']=='candidate-canonical-source-count-qualified'
            and counts['canonical_LOC_admitted'] is True and counts['source_sha256']==l.SOURCE_SHA
            and counts['all_owner_source_slices_and_utf8_offsets_verified'] is True
            and counts['all_candidate_owners_manually_reviewed'] is True
            and counts['original_producer_receipts_unchanged'] is True and counts['chart_admission'] is False,
            'Linear canonical owner review is incomplete')
    for name,value in (('canonical_loc',242),('physical_loc',146),('native_source_reader_processes_replayed',9),
            ('fixture_projections_replayed',7),('candidate_projections_replayed',1),('predicate_count',22),('owner_events',253)):
        require(p.integer(counts[name],value),'Linear owner count differs: '+name)
    for path,digest in counts['pins'].items():
        require(plan['pins'].get(str(ROOT/path))==digest, 'Owner review evidence omitted')
    ref=qualification['projection'];projection=read(ref['path'],ref['sha256'])
    require(projection['source_sha256']==l.SOURCE_SHA and projection['exact_original_and_compiled_bytes_equal'] is True
            and projection['projection']['normalized_loc']==row['canonical_loc']==242
            and projection['projection']['physical_loc']==row['physical_loc']==146
            and projection['canonical_LOC_admitted'] is False, 'Producer projection or review scope differs')
    ref=qualification['required_work_review']
    require(ref['sha256']==l.WORK_SHA and ref['status']=='passed'
            and hashlib.sha256(read_raw(ref['path'],ref['sha256'])).hexdigest()==l.WORK_SHA,
            'Linear compiled-work review differs')
    return qlf, [], loaded


def inspect(plan, previous, reconciliation, outcome, read, read_raw):
    _,all_profiles,_=l.schedule(plan,previous)
    require(reconciliation['schema']==l.SCHEMA
            and reconciliation['status']=='full81-plus-retained9-reconciled-awaiting-runtime-and-publication-review'
            and reconciliation['file_integrity_verified'] is True
            and reconciliation['runtime_publication_metadata_qualified'] is False
            and reconciliation['full_timings_qualified'] is reconciliation['chart_admission'] is False,
            'Completed independent continuation reconciliation required')
    same(reconciliation['plan'],dict(path=str(l.PLAN),sha256=l.PLAN_SHA),'Wrong continuation plan')
    for path,digest in {**plan['pins'],str(RECONCILER):RECONCILER_SHA,str(l.RECONCILER):l.RECONCILER_SHA,
            str(r.HELPER):r.HELPER_SHA}.items():
        require(reconciliation['verified_file_pins'].get(path)==digest,'Reconciliation omitted a prerequisite')
    require(outcome['status']=='qualified-original-Prolog20-work-and-LOC-awaiting-full90'
            and outcome['source_work_qualified'] is outcome['canonical_LOC_admitted'] is True
            and outcome['chart_admission'] is False and p.integer(outcome['profiles'],20),
            'Original source-work/LOC seal incomplete')
    config,feature,images,os_images=runtime_context(plan,read,read_raw)
    rows=[row for row in all_profiles.values() if row['language']=='prolog']
    by_id={row['id']:row for row in rows};eligible=[];excluded=[]
    for row in rows:
        same(row['runtime_environment'],config['environment'],'Profile runtime environment differs')
        require(row['binary']==config['binary'] and row['binary_sha256']==config['binary_sha256']
                and p.integer(row['maximum_workers'],1),'Runtime or worker policy differs')
        if row['benchmark']=='revcomp':
            qlf,vendor,loaded=linear_profile(plan,row,config,images,read,read_raw)
        else:
            qlf,vendor,loaded=original_profile(plan,outcome,row,config,images,read)
        alias=row['source_alias_of']
        if row['variant']=='optimized':
            require(alias==row['id'].removesuffix('-optimized')+'-compact'
                    and by_id[alias]['source_sha256']==row['source_sha256'],'Source alias differs')
        else:require(row['variant']=='compact' and alias is None,'Unknown source form')
        observed=reconciliation['profiles'][row['key']]
        for field in ('key','id','language','benchmark','source','source_sha256','binary_sha256'):
            same(observed[field],row[field],'Reconciled source/runtime differs: '+field)
        if observed['full_workload_qualified'] is not True:
            require(row['key'] in reconciliation['failed_profiles'],'Unexplained failed profile')
            excluded.append(dict(key=row['key'],reason='failed-full-workload',failed_attempt=observed['failed_attempt']))
            continue
        require(row['key'] not in reconciliation['failed_profiles'] and len(observed['samples_seconds'])==3,
                'Failed or incomplete profile offered for publication')
        eligible.append(dict(key=row['key'],id=row['id'],benchmark=row['benchmark'],variant=row['variant'],
            source_alias_of=alias,optimization_claim=row['optimization_claim'],source=row['source'],
            source_sha256=row['source_sha256'],source_bundle=row['source_bundle'],binary=row['binary'],
            binary_sha256=row['binary_sha256'],qlf_artifact_pins=qlf,command=row['command'],cwd=row['cwd'],
            runtime_environment=row['runtime_environment'],canonical_loc=row['canonical_loc'],physical_loc=row['physical_loc'],
            execution_mode='swi-native-bytecode-vm',maximum_compute_workers=1,declared_vendor_libraries=vendor,
            preparation_foreign_libraries=loaded['foreign_libraries'],runtime_flags_observed_during_preparation=loaded['runtime'],
            timing=observed,chart_admission=False))
    return dict(schema=SCHEMA,status='recorded-runtime-metadata-reviewed-awaiting-file-verification',
        runtime_publication_metadata_qualified=False,file_integrity_verified=False,chart_admission=False,
        profiles=eligible,excluded_profiles=excluded,source_forms_reviewed=20,
        runtime_version='SWI-Prolog 10.0.2',native_architecture='arm64',application_execution='bytecode/QLF',
        memory_policy='SWI term, atom and clause garbage collection; retained preparation observed gc=true and bounded=false.',
        stack_limit_bytes=8589934592,maximum_compute_workers=1,probe_runtime_flags=feature['runtime'],
        probe_native_image_pins=images['image_pins'],os_install_names_not_file_hashed=sorted(os_images),
        pcre_version=config['pcre_version'],regex_policy='SWI library(pcre) calls bundled PCRE2 10.40; authored calls request jit(false).',
        arbitrary_integer_policy='Unbounded integers; bundled GMP image retained in the native runtime dependency closure.',
        timing_boundary=plan['timing_policy'],runtime_and_qlf_loading_inside_timer=True,compilation_outside_timer=True,
        new_native_probes=0,compiler_invocations=0,benchmark_samples=0,cohort_policy=reconciliation['cohort_policy'],
        original_source_outcome=previous['sealed_source_outcome'],linear_qualification=plan['linear_qualification'],
        limitations=['Loaded-image and GC observations are from retained probe/preparation commands, not timed processes.',
            'QLF contains application bytecode; native application AOT compilation is not claimed.',
            'Compact/optimized labels are explicit source aliases; distinct source algorithms are not claimed.',
            'Regex samples retain their original matched Mech controls; other workloads use the continuation controls.',
            'The cancelled original reverse-complement attempt supplies no timing or timeout result.',
            'Source-linear traversal is established separately from any empirical runtime scaling claim.'],
        remaining_gate='Explicit dataset import and website validation; failed profiles remain excluded.')


@contextmanager
def _yield_verified(result, recheck, on_exit_failure, final_consumer_check=None):
    """Restore a publication before the outer lease stack closes on an exit-check failure."""
    try:
        yield result
    finally:
        try:
            recheck()
            if final_consumer_check is not None:
                final_consumer_check()
        except BaseException as closure_error:
            if on_exit_failure is not None:
                try:
                    on_exit_failure()
                except BaseException as restoration_error:
                    raise BaseExceptionGroup('Evidence closure and publication restoration both failed',
                                             [closure_error,restoration_error])
            raise


@contextmanager
def review_context(reconciliation_path, expected_sha, *, on_exit_failure=None, final_consumer_check=None):
    """Keep all four leases through a caller's candidate construction or publication."""
    path=Path(reconciliation_path).resolve()
    require(path.is_relative_to(l.PACKET) and not path.is_relative_to(l.PACKET/'run-v1')
            and p.digest(expected_sha),'Wrong additive reconciliation location')
    with ExitStack() as stack:
        leases=[]
        for name,inode in ((l.JOB/'owner.lock',None),(l.OLD/'owned-jobs/full90/owner.lock',81764070),
                (ROOT/'experiments/prolog/prolog-full90.owner.lock',81764078),(r.LOCK,79859134)):
            handle=stack.enter_context(name.open('rb'));fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held,named=os.fstat(handle.fileno()),name.stat()
            require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)
                    and (inode is None or held.st_ino==inode),'Existing lease replaced')
            leases.append((name,handle,held.st_dev,held.st_ino))
        files=r.Files();files.verify(p.PYTHON,l.PYTHON_SHA)
        reconciliation=files.document(str(path),expected_sha)
        require(reconciliation['schema']==l.SCHEMA and reconciliation['file_integrity_verified'] is True
                and reconciliation['durable_directory']==str(l.JOB),'Wrong closed continuation review')
        for name,digest in reconciliation['verified_file_pins'].items():files.verify(name,digest)
        for name,digest in ((RECONCILER,RECONCILER_SHA),(METADATA,METADATA_SHA),
                (Path(__file__).resolve(),hashlib.sha256(Path(__file__).read_bytes()).hexdigest())):
            files.verify(str(name),digest)
        def saved(name):return files.document(str(name),reconciliation['verified_file_pins'][str(name)])
        plan=files.document(str(l.PLAN),l.PLAN_SHA)
        previous={key:files.document(str(name),digest) for key,(name,digest) in l.OLD_REFS.items()}
        output=Path(plan['output']);terminal=saved(output/'terminal.json');report=saved(output/'report.json')
        same(reconciliation['terminal'],dict(path=str(output/'terminal.json'),
            sha256=reconciliation['verified_file_pins'][str(output/'terminal.json')]),'Terminal binding differs')
        same(reconciliation['report'],dict(path=str(output/'report.json'),sha256=terminal['report_sha256']),
             'Report/terminal binding differs')
        require(terminal['report']==str(output/'report.json'),'Terminal report path differs')
        inventories=[]
        for directory,closed in ((output,terminal),(l.OLD/'results',previous['terminal'])):
            expected=set(closed['available_evidence_pins'])|{str(directory/'terminal.json')}
            require(r.inventory(directory)==expected,'Closed artifact inventory differs')
            for name,digest in closed['available_evidence_pins'].items():
                require(Path(name).is_relative_to(directory)
                        and reconciliation['verified_file_pins'].get(name)==digest,'Unbound native receipt')
            inventories.append((directory,expected))
        job_inventory={str(l.JOB/name) for name in ('request.json','launch.json','worker-started.json',
            'command-started.json','terminal.json','command.stdout','command.stderr','worker.log','owner.lock')}
        require(r.inventory(l.JOB)==job_inventory,'Closed durable inventory differs')
        require((l.JOB/'command.stderr').read_bytes()==b'','Durable stderr is not empty')
        require(job_inventory<=set(reconciliation['verified_file_pins']),'Durable evidence omitted')
        inventories.append((l.JOB,job_inventory))
        durable={name:saved(l.JOB/(name+'.json')) for name in
            ('request','launch','worker-started','command-started','terminal')}
        def documents(names):return {name:saved(name) for name in names}
        retained=previous['report']['attempts'][:9]
        fresh=l.reconcile(plan,previous,report,terminal,durable,
            documents(a['result_path'] for a in report['attempts']),
            documents(a['supervisor_result_path'] for a in report['attempts']),
            documents(a['path'] for a in report['independent_supervisors']),
            documents(a['result_path'] for a in retained),documents(a['supervisor_result_path'] for a in retained),
            documents(str(l.OLD/'results/outer-supervisor'/f'{a["attempt"]:03d}-{a["id"]}.json') for a in retained))
        for key,value in fresh.items():
            if key not in ('status','file_integrity_verified'):
                same(reconciliation[key],value,'Saved reconciliation semantics differ: '+key)
        # Original identity relocations and lossless compressed storage remain
        # exactly those of the original plan; only physical pins are extended.
        original=previous['plan']
        reader=m.Evidence(dict(original,pins=plan['pins']),saved(original['storage_manifest']['path']))
        outcome=reader.document(original['sealed_source_outcome']['path'],r.OUTCOME_SHA)
        result=inspect(plan,previous['plan'],reconciliation,outcome,reader.document,reader.raw)
        for name,digest in reader.read_pins.items():files.verify(name,digest)
        verified_pins=tuple(files.verified.items())
        def recheck():
            for name,digest in verified_pins:files.verify(name,digest)
            for directory,expected in inventories:
                require(r.inventory(directory)==expected,'Closed inventory changed during metadata review')
            for name,handle,device,inode in leases:
                held,named=os.fstat(handle.fileno()),name.stat()
                require((held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==(device,inode),'Lease identity changed')
        recheck()
        result.update(status='qualified-recorded-runtime-metadata',runtime_publication_metadata_qualified=True,
            file_integrity_verified=True,common_mutex_held=True,common_mutex_inode=79859134,
            plan=reconciliation['plan'],reconciliation=dict(path=str(path),sha256=expected_sha),
            verified_file_pins=dict(verified_pins),source_outcome=original['sealed_source_outcome'],
            new_full_native_processes=reconciliation['new_full_native_processes'],
            reused_qualified_samples=9,excluded_original_attempt=10)
        with _yield_verified(result,recheck,on_exit_failure,final_consumer_check) as verified:
            yield verified


def review_files(reconciliation_path, expected_sha):
    with review_context(reconciliation_path,expected_sha) as result:
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconciliation',type=Path,required=True)
    parser.add_argument('--reconciliation-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve()==Path(p.PYTHON).resolve(),'Use retained Python -I -S -B without -O')
    output=args.output.resolve()
    require(output.is_relative_to(l.PACKET) and not output.is_relative_to(l.PACKET/'run-v1')
            and not output.exists() and output.parent.is_dir(),'Fresh additive metadata output required')
    result=None
    try:result=review_files(args.reconciliation,args.reconciliation_sha256)
    except BaseException as error:
        result=dict(schema=SCHEMA,status='runtime-metadata-review-failed',error_type=type(error).__name__,
            error=str(error),runtime_publication_metadata_qualified=False,file_integrity_verified=False,
            chart_admission=False,new_native_probes=0,compiler_invocations=0,benchmark_samples=0)
        raise
    finally:
        if result is not None:
            with output.open('x') as stream:
                json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())


if __name__=='__main__':main()
