#!/usr/bin/env python3
"""Reconcile a completed Julia AOT cohort and add its qualified profiles.

The reconcile command reads the original sampler and supervisor evidence under
the completed job, suite and common timing leases. The import command repeats
that reconciliation and requires its exact saved bytes. Import defaults to a
private preview; --apply replaces the three explicitly pinned catalog files.
Neither command imports a measurement producer or starts native processes.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import statistics
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/julia/packagecompiler-v1'
HELPER = Path(__file__).with_name('prolog_reconcile.py')
HELPER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
TARGETS = ('data/benchmarks.json', 'data/languages.json', 'site/src/languages.mjs')
PROFILE_IDS = frozenset(('binarytrees-julia-3', 'binarytrees-julia-4',
    'fannkuchredux-julia-1', 'fannkuchredux-julia-2', 'fasta-julia-3',
    'knucleotide-julia-1', 'knucleotide-julia-6', 'mandelbrot-julia-1',
    'mandelbrot-julia-7', 'nbody-julia-5', 'pidigits-julia-3', 'pidigits-julia-4',
    'regexredux-julia-1', 'regexredux-julia-3', 'revcomp-julia-7',
    'revcomp-julia-9', 'spectralnorm-julia-4'))
META_FIELDS = ('platform', 'runtime', 'execution', 'typing', 'style', 'memory', 'note', 'sources')
RUNTIME_ENVIRONMENT = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',
    JULIA_NUM_THREADS='8,0',JULIA_LOAD_CODEGEN_LIB='0',OPENBLAS_NUM_THREADS='1',
    OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
FULL_OUTPUT = {
    'regexredux': (298,'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'),
    'revcomp': (254166745,'e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'),
    'pidigits': (16893,'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
    'spectralnorm': (12,'f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'),
    'mandelbrot': (32000015,'609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'),
    'fasta': (254166745,'3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
    'knucleotide': (259,'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'),
    'binarytrees': (455,'341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'fannkuchredux': (29,'4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20')}
METADATA = dict(key='julia-aot', label='Julia (AOT)', family='julia',
    platform='runtime', runtime='Julia / LLVM; PackageCompiler native application',
    execution=['aot'], typing='dynamic', style=['imperative', 'functional', 'array'], memory=['gc'],
    note='PackageCompiler applications use a native system image compiled before measurement. '
         'Timed processes disable Julia code generation and use --compile=no. The Julia runtime and tracing GC remain; '
         'PCRE may use its own regex JIT. Historical Julia JIT measurements are retained separately.',
    sources=['https://julialang.github.io/PackageCompiler.jl/stable/apps.html',
             'https://docs.julialang.org/en/v1/devdocs/aot/',
             'https://docs.julialang.org/en/v1/devdocs/gc/'])


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, digest):
    if not re.fullmatch('[0-9a-f]{64}', digest or ''):
        raise ValueError('Explicit SHA-256 required: '+str(path))
    raw = Path(path).read_bytes()
    if sha(raw) != digest:
        raise ValueError('Pinned bytes changed: '+str(path))
    return raw


def primitives():
    raw = checked(HELPER, HELPER_SHA)
    spec = importlib.util.spec_from_file_location('julia_aot_independent_receipts', HELPER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(HELPER), 'exec'), module.__dict__)
    return module


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(left, right, message):
    require(json.dumps(left, sort_keys=True, allow_nan=False) ==
            json.dumps(right, sort_keys=True, allow_nan=False), message)


def ref(path, digest=None):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=digest or sha(path.read_bytes()))


def public_ref(binding):
    path = Path(binding['path'])
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(ROOT)
            and path.resolve().is_relative_to(ROOT), 'Public evidence must be retained in the repository')
    checked(path, binding['sha256'])
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=binding['sha256'])


def public(value):
    if isinstance(value, list):
        return [public(v) for v in value]
    if isinstance(value, dict):
        result = {k:public(v) for k,v in value.items()}
        path = value.get('path')
        if isinstance(path, str) and re.fullmatch('[0-9a-f]{64}', value.get('sha256', '')):
            if Path(path).is_absolute() and Path(path).is_relative_to(ROOT):
                result.update(public_ref(value))
        return result
    return value


def write_new(path, value):
    raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    identity = None
    try:
        with Path(path).open('xb') as stream:
            info = os.fstat(stream.fileno())
            identity = (info.st_dev,info.st_ino)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if identity is not None:
            info = Path(path).lstat()
            require((info.st_dev,info.st_ino)==identity and not Path(path).is_symlink()
                    and raw.startswith(Path(path).read_bytes()),'Refusing to remove replaced result')
            Path(path).unlink()
        raise
    return sha(raw)


def validate_plan(plan, p):
    require(plan['schema'] == 'julia-aot-full81-plan-v1'
            and plan['status'] == 'prepared-awaiting-independent-review', 'Prepared Julia AOT plan required')
    for name, count in (('source_work_profiles',17), ('canonical_loc_profiles',17),
                        ('formatted_loc_profiles',0), ('samples',3), ('full_processes',81),
                        ('julia_aot_samples',51), ('matched_mech_samples',30)):
        require(p.integer(plan[name], count), 'Changed plan count: '+name)
    require(plan['no_automatic_retry'] is True and plan['chart_admission'] is False
            and plan['full_timings_qualified'] is False, 'Changed measurement policy')
    controller = ROOT/'tools/qualification/julia_aot_full.py'
    require(plan['controller']==str(controller) and p.digest(plan['pins'].get(str(controller)))
            and plan['repository']==str(ROOT) and plan['shared_timing_lock']==str(p.LOCK)
            and plan['suite_lease']==str(WORK/'julia-aot-full81.owner.lock')
            and plan['continuous_common_mutex'] is True and plan['common_mutex_inode']==p.LOCK_INODE
            and plan['pins_verified'] is True,'Prepared source or timing ownership policy differs')
    require(set(plan['manifests']) == set(p.BENCHES), 'Ten workload manifests required')
    rows, slots, original_ids = {}, [], set()
    for bench in p.BENCHES:
        manifest = plan['manifests'][bench]
        require(manifest['benchmark'] == bench and p.integer(manifest['size'], p.SIZES[bench])
                and p.integer(manifest['samples'],3), 'Changed full workload')
        expected_output = None if bench=='nbody' else dict(zip(('bytes','sha256'),FULL_OUTPUT[bench]))
        same(manifest['full_output_reference'],expected_output,'Changed canonical full-output oracle')
        require(manifest['canonical_full_workload'] is True and manifest['timeout_seconds']==21600
                and manifest['supervisor_timeout_seconds']==22200 and manifest['maximum_rss_mib']==10240
                and manifest['compilation_outside_timer'] is True
                and manifest['runtime_and_app_image_loading_inside_timer'] is True
                and manifest['regular_file_stdin'] is True,'Changed canonical full-process timing policy')
        profiles = manifest['profiles']
        subjects = [row for row in profiles if row['language'] == 'julia-aot']
        controls = [row for row in profiles if row['language'] == 'mech']
        require(len(controls) == 1 and len(subjects) in (1,2)
                and len(subjects)+1 == len(profiles), 'Workload profile cohort differs')
        ids = [row['id'] for row in profiles]
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        same(manifest['orders'], orders, 'Changed three-round rotation')
        for row in profiles:
            require(row['benchmark'] == bench and row['key'] not in rows, 'Duplicate profile identity')
            rows[row['key']] = row
        for row in subjects:
            original = row['original_profile_id']
            require(original in PROFILE_IDS and original not in original_ids
                    and row['id'] == original+'-aot' and row['key'] == bench+':'+row['id'],
                    'Julia source profile identity differs')
            original_ids.add(original)
            require(row['source_work_qualified'] is True and row['canonical_loc_qualified'] is True
                    and row['formatted_loc'] is None and row['loc'] == row['canonical_loc'],
                    'Source/count qualification incomplete')
            require(row['runtime_environment']['JULIA_LOAD_CODEGEN_LIB'] == '0'
                    and '--compile=no' in row['command'], 'Timed Julia compilation must be disabled')
            same(row['runtime_environment'],RUNTIME_ENVIRONMENT,'Julia native runtime environment differs')
            arguments = ['--julia-args','--startup-file=no','--history-file=no','--compile=no']
            same(row['command'],[row['binary']]+([] if bench in ('regexredux','revcomp','knucleotide')
                 else ['{n}'])+arguments,'Direct native application command differs')
            same(row['runtime_arguments'],arguments,'Julia runtime arguments differ')
            for field in ('source', 'binary'):
                require(plan['pins'].get(row[field]) == row[field+'_sha256'], 'Unpinned '+field)
            physical = row['physical_inputs']
            require(len(physical)==1 and physical[0]['path']==row['source']
                    and physical[0]['sha256']==row['source_sha256']
                    and physical[0]['role']=='application' and physical[0]['counted'] is True
                    and physical[0]['canonical_loc']==row['loc']
                    and physical[0]['physical_loc']==row['physical_loc'],
                    'Counted application source-role mapping differs')
            require(p.integer(row['loc']) and row['loc'] > 0
                    and p.integer(row['physical_loc']) and row['physical_loc'] > 0,
                    'Invalid source counts')
        keys = {row['id']:row['key'] for row in profiles}
        slots.extend([bench, order['round'], ident, keys[ident]]
                     for order in orders for ident in order['profiles'])
    require(original_ids == PROFILE_IDS and len(rows) == 27 and len(slots) == 81,
            'Exact seventeen source profiles and ten controls required')
    same(plan['schedule'], slots, 'Saved schedule differs')
    require(set(plan['execution_pins']) == set(rows),'Per-profile execution pin inventory differs')
    for key,pins in plan['execution_pins'].items():
        require(all(plan['pins'].get(path)==digest for path,digest in pins.items()),
                'Scoped execution pin differs from global closure')
    return rows, slots


def verify_bundle_structure(plan):
    """Hashes are checked separately; independently bind names, modes and links."""
    require(set(plan['bundle_inventories'])==PROFILE_IDS,'Exact seventeen app bundle inventories required')
    for profile,expected in plan['bundle_inventories'].items():
        root = Path(expected['root'])
        require(root.is_absolute() and not root.is_symlink() and root.resolve()==root and root.is_dir(),
                'Physical absolute app bundle required')
        entries = {}
        def visit(path,relative,ancestors):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                resolved = path.resolve(strict=True)
                entries[relative] = dict(kind='symlink',mode=stat.S_IMODE(mode),
                    target=os.readlink(path),resolved=str(resolved))
                if resolved.is_dir():
                    require(resolved not in ancestors,'Cyclic app directory link')
                    for child in sorted(path.iterdir()):
                        visit(child,relative+'/'+child.name,ancestors|{resolved})
                else:
                    require(resolved.is_file(),'App link target is nonregular')
                    digest = plan['pins'].get(str(path))
                    require(digest is not None and plan['pins'].get(str(resolved))==digest,
                            'App link target not byte-pinned')
                    entries[relative].update(bytes=resolved.stat().st_size,
                        target_mode=stat.S_IMODE(resolved.stat().st_mode),sha256=digest)
            elif stat.S_ISDIR(mode):
                resolved = path.resolve()
                require(resolved not in ancestors,'Cyclic app directory')
                entries[relative] = dict(kind='directory',mode=stat.S_IMODE(mode))
                for child in sorted(path.iterdir()):
                    visit(child,relative+'/'+child.name if relative else child.name,ancestors|{resolved})
            else:
                require(stat.S_ISREG(mode),'Nonregular app bundle member')
                digest = plan['pins'].get(str(path))
                require(digest is not None,'Unpinned app bundle file')
                entries[relative] = dict(kind='file',bytes=path.stat().st_size,
                    mode=stat.S_IMODE(mode),sha256=digest)
        visit(root,'',set())
        same(dict(root=str(root),entries=entries),expected,'App bundle membership, modes or links changed: '+profile)


def verify_build_evidence(plan,files):
    """Read completed build/validation facts without importing their producers."""
    def document(binding):
        require(plan['pins'].get(binding['path'])==binding['sha256'],'Unpinned prerequisite evidence')
        return files.document(binding['path'],binding['sha256'])
    for manifest in plan['manifests'].values():
        for row in manifest['profiles']:
            if row['language']!='julia-aot':
                continue
            build = document(row['build_evidence'])
            terminal = document(row['build_terminal_evidence'])
            require(build['schema']=='julia-packagecompiler-build-v1'
                    and build['status']==terminal['status']=='built-awaiting-output-validation'
                    and build['exit_code']==0 and build['errors']==[]
                    and build['input_files_unchanged'] is True and build['remaining_process_group']==[]
                    and build['benchmark_samples']==terminal['benchmark_samples']==0,
                    'Clean completed native build required')
            require(terminal['report_sha256']==row['build_evidence']['sha256']
                    and build['executable']==dict(path=row['binary'],sha256=row['binary_sha256'])
                    and build['input_sha256'].get(row['source'])==row['source_sha256'],
                    'Build source or executable identity differs')
            if row['original_profile_id']=='fannkuchredux-julia-2':
                require(build['environment']['JULIA_NUM_THREADS']=='8,0',
                        'Fannkuch thread-indexed state requires the headless build/training configuration')
            same(row['bundle_inventory'],plan['bundle_inventories'][row['original_profile_id']],
                 'Per-profile app bundle inventory differs')
            require(plan['pins'].get(row['sysimage'])==row['sysimage_sha256'],'Unpinned native app image')
            training = document(row['training_inputs_evidence'])
            training_rows = [item for item in training['profiles'] if item['profile']==row['original_profile_id']]
            require(len(training_rows)==1 and training_rows[0]['workload']==row['benchmark'],
                    'Training profile mapping differs')
            training_row = training_rows[0]
            training_path = ROOT/training_row['training']
            require(training_path.is_relative_to(ROOT) and '..' not in training_path.parts
                    and build['command'][-2]==str(training_path)
                    and build['input_sha256'].get(str(training_path))==training_row['sha256'],
                    'Completed build did not use the selected exact training recipe')
            corpus_binding = training_row.get('corpus_manifest',training['corpus_manifest'])
            corpus_path = ROOT/corpus_binding['path']
            require(corpus_path.is_relative_to(ROOT) and '..' not in corpus_path.parts,
                    'Selected fixture manifest escaped repository')
            same(row['bounded_corpus_evidence'],dict(path=str(corpus_path),sha256=corpus_binding['sha256']),
                 'Selected per-profile fixture manifest differs')
            corpus = document(row['bounded_corpus_evidence'])
            validated_cases = []
            image_bound = False
            require(row['validation_evidence'],'Completed native output validation required')
            for binding in row['validation_evidence']:
                validation = document(binding)
                require(validation['schema']=='julia-packagecompiler-native-output-v1'
                        and validation['status']=='passed' and validation['profile']==row['original_profile_id']
                        and validation['errors']==[] and validation['exit_code']==0
                        and validation['complete_output_matches'] is True
                        and validation['executable_unchanged'] is True and validation['remaining_process_group']==[]
                        and validation['executable_sha256']==row['binary_sha256']
                        and validation['benchmark_samples']==0,'Incomplete no-codegen output validation')
                same(validation['environment'],row['runtime_environment'],'Validated/timed runtime policy differs')
                require(validation['command'][0]==row['binary']
                        and validation['command'][-4:]==row['runtime_arguments'],
                        'Validated native executable or Julia flags differ')
                cases = [case for case in corpus['cases'] if case['benchmark']==row['benchmark']
                         and case['case']==validation['case']]
                require(len(cases)==1 and cases[0]['expected_exit']==0,'Unknown successful validation case')
                case = cases[0]
                validated_cases.append(case['case'])
                same(validation['command'],[row['binary']]
                     +([str(case['n'])] if case['input_kind']=='integer-argument' else [])
                     +row['runtime_arguments'],'Validated fixture argv differs')
                require(validation['stdin_sha256']==case['stdin']['sha256']
                        and validation['expected_sha256']==case['expected']['sha256'],
                        'Validated input or independent reference differs')
                for field in ('stdin','expected'):
                    path = corpus_path.parent/case[field]['path']
                    require(path.is_relative_to(corpus_path.parent) and '..' not in path.parts
                            and plan['pins'].get(str(path))==case[field]['sha256'],
                            'Selected fixture bytes are not pinned')
                if 'sysimage' in validation:
                    same(validation['sysimage'],dict(path=row['sysimage'],sha256=row['sysimage_sha256']),
                         'Validated native image differs')
                    require(validation['sysimage_unchanged'] is True,'Validated image changed')
                    image_bound = True
            require(training_row['case'] in validated_cases,'Selected default validation case did not pass')
            if row['image_identity_evidence']:
                image = document(row['image_identity_evidence'])
                require(image['schema']=='julia-packagecompiler-built-image-identity-v1'
                        and image['profile']==row['original_profile_id'] and image['path']==row['sysimage']
                        and image['sha256']==row['sysimage_sha256']
                        and image['bytes']==Path(row['sysimage']).stat().st_size,'Native image identity differs')
                image_bound = True
            require(image_bound,'Validation does not bind the actual native image')


def check_durable(durable, plan_path, plan_sha, plan, p):
    command = [p.PYTHON, '-I', '-S', '-B', plan['controller'], 'run',
               '--plan', str(plan_path), '--plan-sha256', plan_sha]
    unbuffered = command[:4]+['-u']+command[4:]
    require(durable['request']['command'] in (command, unbuffered), 'Unexpected durable command')
    expected = durable['request']['command']
    for name in ('launch', 'worker-started', 'command-started'):
        same(durable[name]['command'], expected, 'Durable command disagreement')
    ended = durable['terminal']
    require(ended['status'] == 'command-exited-zero-awaiting-report-review'
            and p.integer(ended['exit_code'],0) and ended['actual_command_started'] is True,
            'Durable command has not completed normally')
    require(ended['automatic_retry'] is False and ended['qualification_granted'] is False,
            'Durable policy changed')
    same(ended['stop_signals'], [], 'Durable stop signals recorded')
    require(not any(ended.get(k) for k in ('error','error_type','exception_cleanup')),
            'Durable terminal contains an error')
    same(p.process_identity(ended['command_identity']),
         p.process_identity(durable['command-started']['command_identity']), 'Controller identity changed')
    return durable['command-started']['command_pid']


def reconcile(plan, plan_path, plan_sha, report, terminal, documents, durable, r):
    p = r.p
    originals, slots = validate_plan(plan,p)
    pid = check_durable(durable,plan_path,plan_sha,plan,p)
    require(report['status'] == terminal['status'] == 'complete' and report['active'] is None,
            'Complete successful cohort required; failures retain evidence without admission')
    require(not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors')),
            'Cohort contains integrity or execution errors')
    require(report['plan'] == str(plan_path) and report['plan_sha256'] == plan_sha,
            'Report belongs to another plan')
    require(report['pins_unchanged_at_end'] is True and terminal['common_mutex_held'] is True
            and terminal['common_mutex_held_continuously'] is True
            and terminal['common_mutex_inode'] == p.LOCK_INODE, 'Timing ownership or pins not verified')
    same(terminal['integrity_errors'], [], 'Terminal integrity error')
    same(terminal['bundle_inventories'],plan['bundle_inventories'],'Final app bundle inventories differ')
    same(terminal['prerequisite_pins'], dict(plan['pins'], **{str(plan_path):plan_sha}),
         'Terminal prerequisite closure differs')
    same(report['completed_benchmarks'], list(p.BENCHES), 'Incomplete workload accounting')
    require(set(report['programs']) == set(originals), 'Measured profile inventory differs')
    attempts = report['attempts']
    require(len(attempts) == len(report['independent_supervisors']) == 81,
            'Exactly 81 independently supervised native observations required')
    grouped = {key:[] for key in originals}
    provenance, gaps, previous_end, used = [], [], None, set()
    for index,(slot,attempt,outer_ref) in enumerate(zip(slots,attempts,report['independent_supervisors']),1):
        require(p.integer(attempt['attempt'],index) and attempt['qualified'] is True,
                'Missing, repeated or unqualified observation')
        base = str(Path(plan['output'])/'attempts'/f'{index:03d}-{slot[2]}')
        require(attempt['result_path'] == base+'.json'
                and attempt['supervisor_result_path'] == base+'.supervisor.json', 'Attempt paths differ')
        outer_path = str(Path(plan['output'])/'outer-supervisor'/f'{index:03d}-{slot[2]}.json')
        require(outer_ref['path'] == outer_path and outer_ref['status'] == 'returned'
                and terminal['available_evidence_pins'][outer_path] == outer_ref['sha256'],
                'Outer supervisor binding differs')
        scoped_pins = dict(plan['execution_pins'][slot[3]], **{str(plan_path):plan_sha})
        begin,end = r.check_attempt(attempt,documents[attempt['result_path']],
            documents[attempt['supervisor_result_path']],slot,originals[slot[3]],
            plan['manifests'][slot[0]],scoped_pins,provenance)
        require(previous_end is None or previous_end <= begin, 'Native timing intervals overlap')
        previous_end = end
        gaps.extend(r.check_outer(documents[outer_path],attempt,pid))
        used.update((attempt['result_path'],attempt['supervisor_result_path'],outer_path))
        grouped[slot[3]].append(attempt)
    summaries = {}
    for key,original in originals.items():
        row = report['programs'][key]
        same({k:v for k,v in row.items() if k not in r.AGGREGATE},original,'Measured profile metadata changed')
        observations = grouped[key]
        values = [a['seconds'] for a in observations]
        median,sd = p.three_statistics(values)
        same(row['samples_seconds'],values,'Summary sample values differ')
        same(row['attempts'],[a['attempt'] for a in observations],'Profile observation membership differs')
        same(row['sample_validation'],[a['validation'] for a in observations],'Profile validations differ')
        require(row['measurement_status'] == 'measured' and not row.get('full_failure')
                and row['median_seconds'] == median
                and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),
                'Independent median/sample deviation differs')
        summaries[key] = dict(key=key, benchmark=row['benchmark'], id=row['id'], language=row['language'],
            samples_seconds=values, median_seconds=median, sample_stdev_seconds=sd,
            attempts=[a['attempt'] for a in observations], full_workload_qualified=True)
    for key,row in report['programs'].items():
        control = row['matched_mech_control']
        require(control in summaries and originals[control]['language'] == 'mech'
                and originals[control]['benchmark'] == row['benchmark'], 'Wrong matched Mech control')
        require(row['matched_mech_source_sha256'] == originals[control]['source_sha256'],
                'Matched control source differs')
        ratio = summaries[key]['median_seconds']/summaries[control]['median_seconds']
        same(row['time_x_mech'],ratio,'Matched control ratio differs')
        summaries[key]['time_x_mech'] = ratio
    for item in (report,terminal):
        for name in ('saved_attempts','full_performance_runs','qualified_samples'):
            require(p.integer(item[name],81),'Incorrect completed observation count')
        same(item['registered_native_attempts'],list(range(1,82)),'Native registration ledger differs')
        same(item['native_launch_unconfirmed_attempts'],[],'Unconfirmed native launch')
        require(item['chart_admission'] is False,'Producer cannot grant publication')
    same(report['isolated_failed_profiles'],[],'Failed profile present')
    same(report['skipped_failed_profile_slots'],[],'Skipped observations present')
    same(terminal['skipped_failed_profile_slots'],[],'Skipped observations present')
    for name in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','count_replays',
                 'repeated_completed_samples'):
        require(p.integer(terminal[name],0),'Unexpected compilation or repeated preparatory work')
    require(terminal['original_files_mutated'] is False,'Original source files were mutated')
    same(sorted(terminal['available_evidence_pins']),sorted(used|{str(Path(plan['output'])/'report.json')}),
         'Closed measurement evidence inventory differs')
    require(p.timestamp(report['started_at']) <= p.timestamp(attempts[0]['started_at'])
            and previous_end <= p.timestamp(report['finished_at']), 'Native intervals outside cohort')
    require(p.timestamp(durable['command-started']['started_at']) <= p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at']) <= p.timestamp(durable['terminal']['finished_at']),
            'Cohort outside durable process lifetime')
    return dict(schema='julia-aot-independent-full81-reconciliation-v1',
        status='full81-reconciled-awaiting-explicit-publication-review',
        actual_full_native_processes=81,actual_julia_aot_processes=51,actual_matched_mech_processes=30,
        qualified_samples=81,profiles=summaries,failed_profiles=[],skipped_slots=[],
        native_timing_intervals_nonoverlapping=True,kernel_identity_observation_gaps=gaps,
        complete_stdout_retained=False,chart_admission=False,
        output_evidence='Original sampler complete-output byte counts, hashes and validation receipts; N-body tolerance is retained.',
        resource_evidence='Sampled process-group RSS; not an unsampled maximum.')


@contextmanager
def review_files(plan_path,plan_sha,durable_directory,on_failure=None):
    r = primitives()
    p = r.p
    plan_path,durable_directory = Path(plan_path).resolve(),Path(durable_directory).resolve()
    plan = p.strict_json(checked(plan_path,plan_sha))
    validate_plan(plan,p)
    files = r.Files()
    leases = []
    def verify():
        for path,handle,device,inode in leases:
            held,named = os.fstat(handle.fileno()),path.stat()
            require((held.st_dev,held.st_ino) == (named.st_dev,named.st_ino) == (device,inode),
                    'Completed-job lease replaced')
        for name,digest in tuple(files.verified.items()):
            files.verify(name,digest)
        require(r.inventory(Path(plan['output'])) == expected_inventory,'Closed run artifact inventory changed')
        verify_bundle_structure(plan)
    with ExitStack() as stack:
        for path in (durable_directory/'owner.lock',WORK/'julia-aot-full81.owner.lock',p.LOCK):
            handle = stack.enter_context(path.open('rb'))
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held,named = os.fstat(handle.fileno()),path.stat()
            require((held.st_dev,held.st_ino) == (named.st_dev,named.st_ino),'Lease replaced')
            if path == p.LOCK:
                require(held.st_ino == p.LOCK_INODE,'Original common timing mutex replaced')
            leases.append((path,handle,held.st_dev,held.st_ino))
        files.verify(str(plan_path),plan_sha)
        for name,digest in plan['pins'].items():
            files.verify(name,digest)
        verify_bundle_structure(plan)
        verify_build_evidence(plan,files)
        for path,digest in ((HELPER,HELPER_SHA),(r.HELPER,r.HELPER_SHA)):
            files.verify(str(path),digest)
        durable = {}
        for name in ('request','launch','worker-started','command-started','terminal'):
            path = durable_directory/(name+'.json')
            durable[name] = files.document(str(path),sha(path.read_bytes()))
        require((durable_directory/'command.stderr').read_bytes() == b'','Durable controller emitted errors')
        for name in ('command.stdout','command.stderr','worker.log'):
            path = durable_directory/name
            files.verify(str(path),sha(path.read_bytes()))
        output = Path(plan['output'])
        terminal_path = output/'terminal.json'
        terminal_sha = sha(terminal_path.read_bytes())
        terminal = files.document(str(terminal_path),terminal_sha)
        require(terminal['report'] == str(output/'report.json'),'Terminal report path differs')
        report = files.document(terminal['report'],terminal['report_sha256'])
        expected_inventory = set(terminal['available_evidence_pins'])|{str(terminal_path)}
        require(r.inventory(output) == expected_inventory,'Closed measurement artifact inventory differs')
        documents = {}
        for name,digest in terminal['available_evidence_pins'].items():
            require(Path(name).is_relative_to(output),'Measurement evidence escaped output directory')
            documents[name] = files.document(name,digest)
        result = reconcile(plan,plan_path,plan_sha,report,terminal,documents,durable,r)
        result.update(plan=ref(plan_path,plan_sha),report=ref(terminal['report'],terminal['report_sha256']),
            terminal=ref(terminal_path,terminal_sha),verified_file_pins=dict(files.verified),
            common_mutex_held=True,common_mutex_inode=p.LOCK_INODE,file_integrity_verified=True)
        verify()
        try:
            yield result,plan,report,verify
        except BaseException:
            if on_failure is not None:
                on_failure()
            raise
        finally:
            try:
                verify()
            except BaseException:
                if on_failure is not None:
                    on_failure()
                raise


def source_records(plan,report):
    """Bind source-adaptation and the complete counted module for every profile."""
    adaptation_path,counts_path = WORK/'source-adaptation.json',WORK/'source-counts.json'
    for path in (adaptation_path,counts_path):
        require(plan['pins'].get(str(path)) == sha(path.read_bytes()),'Source/count evidence is not pinned')
    adaptation = json.loads(adaptation_path.read_bytes())
    counts = json.loads(counts_path.read_bytes())
    require(adaptation['profile_count'] == counts['profile_count'] == 17
            and counts['status'] == 'counted-and-source-diagnostics-reviewed','Reviewed complete source counts required')
    same(counts['source_adaptation'],dict(path=str(adaptation_path.relative_to(ROOT)),
         sha256=sha(adaptation_path.read_bytes())),'Count/adaptation binding differs')
    records = {row['profile']:row for row in adaptation['profiles']}
    counted = {row['profile']:row for row in counts['profiles']}
    require(set(records) == set(counted) == PROFILE_IDS,'Count/source profile inventory differs')
    for row in report['programs'].values():
        if row['language'] != 'julia-aot':
            continue
        original = row['original_profile_id']
        record,count = records[original],counted[original]
        binding = record['adapted_source']
        path = ROOT/binding['path']
        checked(path,binding['sha256'])
        require(str(path) == row['source'] and binding['sha256'] == row['source_sha256']
                and count['source'] == binding,'Measured and counted source differs')
        require(row['loc'] == count['canonical_loc'] == count['source_specific_review']['canonical_loc']
                and row['physical_loc'] == count['physical_loc'],'Publication source counts differ')
    return records,counted


def build_publication(originals,plan,report,reconciliation,reconciliation_ref):
    data,languages = (json.loads(originals[name]) for name in TARGETS[:2])
    match = re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',
                         originals[TARGETS[2]].decode(),re.S)
    require(match is not None,'Unexpected taxonomy module syntax')
    module = json.loads(match[2])
    before = copy.deepcopy(data)
    require('julia-aot' not in module and 'julia-aot' not in languages['languages']
            and 'julia_aot_audit' not in data,'Julia AOT is already admitted')
    old_julia = {k:v for k,v in data['programs'].items() if v['language']=='julia'}
    require({v['id'] for v in old_julia.values()} == PROFILE_IDS,'Existing Julia JIT profile cohort changed')
    source_adaptations,source_counts = source_records(plan,report)
    public_report = public_ref(reconciliation['report'])
    counts_ref = public_ref(ref(WORK/'source-counts.json'))
    adaptation_ref = public_ref(ref(WORK/'source-adaptation.json'))
    published_review = public_ref(reconciliation_ref)
    for binding in (public_report,counts_ref,adaptation_ref,published_review,
                    public_ref(reconciliation['plan']),public_ref(reconciliation['terminal'])):
        name = binding['path']
        require(data['archive_paths'].get(name,name)==name,'Existing archive mapping conflicts')
        data['archive_paths'][name] = name
    controls = {row['benchmark']:row for row in report['programs'].values() if row['language']=='mech'}
    benchmarks = {b['key']:b for b in data['benchmarks']}
    new_rows,new_minima = {},[]
    for raw in report['programs'].values():
        if raw['language'] != 'julia-aot':
            continue
        row = public(copy.deepcopy(raw))
        key,bench = row['key'],benchmarks[row['benchmark']]
        require(key not in data['programs'] and key not in data['program_inventory'],'Duplicate new profile')
        original = row['original_profile_id']
        adaptation,count = source_adaptations[original],source_counts[original]
        binding = adaptation['adapted_source']
        path = ROOT/binding['path']
        digest = binding['sha256']
        code = checked(path,digest).decode()
        source = dict(name=path.name,path=binding['path'],archive_path=binding['path'],sha256=digest,code=code)
        if digest in data['files']:
            same(data['files'][digest]['code'],code,'Source hash collision')
        else:
            data['files'][digest] = source
        data['archive_paths'].setdefault(binding['path'],binding['path'])
        seconds = row['median_seconds']
        if seconds < bench['baseline_seconds'] or row['loc'] < bench['baseline_loc']:
            new_minima.append(dict(key=key,seconds=seconds,loc=row['loc'],
                retained_baseline_seconds=bench['baseline_seconds'],retained_baseline_loc=bench['baseline_loc']))
        samples = [a for a in report['attempts'] if a['key']==key]
        source_evidence = dict(path=binding['path'],sha256=digest)
        row.update(seconds=seconds,samples=list(row['samples_seconds']),timing_sd=row['sample_stdev_seconds'],
            files=[digest],file_roles={digest:dict(role='application',retained_source=source_evidence,
                normalized_loc=row['loc'],physical_loc=row['physical_loc'],formatted_loc=None)},
            loc_metric='statement-normalized',loc_report=counts_ref['path'],source_report=public_report['path'],
            source_provenance_record=dict(original_source=adaptation['original_source'],
                original_program_key=adaptation['program_key'],source_adaptation=adaptation_ref,
                canonical_source_evidence=counts_ref,authored_roles=[source_evidence]),
            source_provenance='Existing Julia benchmark kernel adapted to an ordinary PackageCompiler application package. '
                'The complete containing module, entry and runtime initialization count in canonical LOC.',
            source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(binding['path']),
            source_link_label='Exact retained application source',local_adaptation=True,
            report=public_report['path'],report_sha256=public_report['sha256'],
            execution_mode='aot',runtime_policy='Julia PackageCompiler native application; Julia code generation disabled',
            memory_policy='Julia tracing GC; no numeric GC-default claims',
            runtime_support=('Julia Base PCRE and its native regex library; PCRE may use its own JIT'
                             if row['benchmark']=='regexredux' else 'Julia standard libraries and runtime'),
            formatted_loc=None,formatted_loc_status='unavailable',formatted_loc_complete=False,
            formatted_loc_evidence=None,formatted_x=None,
            eligible_for_chart=True,required_work_validated=True,canonical_loc_qualified=True,
            timing_alias_of=None,distinct_optimization_claimed=False,
            timing_boundary='Fresh complete process: application/runtime loading, input, initialization, benchmark work, output and shutdown included; image compilation excluded.',
            timing_summary='Median of three qualified full fresh-process runs. No in-process timing or warm application reuse.',
            matched_mech_control=public(copy.deepcopy(controls[row['benchmark']])),
            sample_execution_metadata=public(samples),full_output_validation=[a['validation'] for a in samples],
            x=row['loc']/bench['baseline_loc'],y=seconds/bench['baseline_seconds'],
            chart_admission=dict(reconciliation=published_review,historical_reports_unchanged=True),
            measured_backend=dict(key='julia-packagecompiler-aot',execution='aot',label='Julia (AOT)',verified=True,
                evidence=dict(verified=True,report=public_report['path'],report_sha256=public_report['sha256'],
                    command=row['command'],source_sha256=[digest],
                    runtime_receipt=dict(verified=True,report=public_report['path'],report_sha256=public_report['sha256'],
                        field='/programs/'+key+'/runtime_environment/JULIA_LOAD_CODEGEN_LIB',value='0',value_encoding='literal-saved-string'),
                    aot_evidence_scope='Pinned native PackageCompiler image, disabled Julia code generation, --compile=no and complete successful output; no debugger required.')))
        row['publication_record'] = copy.deepcopy(row)
        data['program_inventory'][key] = row
        new_rows[key] = row
    require(len(new_rows)==17,'Exact seventeen qualified AOT profiles required')
    endpoints = {}
    for bench in data['benchmarks']:
        rows = [r for r in new_rows.values() if r['benchmark']==bench['key']]
        fast = min(rows,key=lambda r:(r['seconds'],r['loc'],r['key']))
        small = min(rows,key=lambda r:(r['loc'],r['seconds'],r['key']))
        selected = list(dict.fromkeys((fast['key'],small['key'])))
        data['programs'].update({key:new_rows[key] for key in selected})
        endpoint = dict(fast=fast['key'],small=small['key'],formatted_fast=None,formatted_small=None,programs=selected)
        bench['groups'].append(dict(language='julia-aot',label='Julia (AOT)',**endpoint))
        endpoints[bench['key']] = endpoint
    admitted = [b['key'] for b in data['benchmarks']]
    release = dict(release_year=2012,release_name='Julia',
        release_source='https://julialang.org/blog/2012/02/why-we-created-julia/',
        release_note='Julia public introduction on February 14, 2012; this variant measures PackageCompiler applications.')
    language = dict(METADATA,**release)
    module['julia-aot'] = {k:copy.deepcopy(language[k]) for k in META_FIELDS}
    displayed = sum(r['language']=='julia-aot' for r in data['programs'].values())
    languages['languages']['julia-aot'] = dict(language,displayed_program_count=displayed,
        measurement_basis=[dict(public_report,status='independently-reconciled-full81')],
        evidence_scope='Exact retained application source, native image/bundle, build and validation receipts, '
                       'serial full fresh-process observations and independent reconciliation. Numeric GC configuration is not claimed.')
    languages['audited_on'] = datetime.now(timezone.utc).date().isoformat()
    languages['scope'] = str(len(data['languages'])+1)+' measured variants; all classifications explicit.'
    data['languages'].append(dict(key='julia-aot',label='Julia (AOT)',family='julia',color='#c69cde',**release,
        timed_benchmarks=admitted,source_benchmarks=admitted,formatted_timed_benchmarks=[],formatted_source_benchmarks=[],
        runtime_family='runtime',runtime=METADATA['runtime'],execution_modes=['aot'],typing='dynamic',
        paradigms=METADATA['style'],memory_models=['gc'],classification_note=METADATA['note']))
    reference = dict(lang='julia-aot',label='Julia (AOT)',measured_benchmarks=admitted)
    for kind in ('fast','small'):
        rows = [new_rows[endpoints[b][kind]] for b in admitted]
        reference[kind] = {axis:statistics.geometric_mean(r[axis] for r in rows) for axis in ('x','y')}
    data['reference_summary'].append(reference)
    data['protocol']['julia-aot'] = ('Seventeen original Julia source profiles compiled into separate PackageCompiler applications. '
        'Three full fresh-process observations per profile and three matched Mech controls per workload; '
        'complete process startup, runtime loading, input, work, output and shutdown are timed. '
        'Julia code generation is disabled and --compile=no is passed. Native-image compilation and training are outside the timer. '
        'The entire authored application module and entry count in canonical LOC; formatted LOC is unavailable. '
        'Matched controls are retained as evidence and never replace historical Mech measurements.')
    for group in data['language_groups']:
        if group['key'] in ('aot','functional','dynamic','array'):
            group['languages'].append('julia-aot')
    audit = dict(schema='julia-aot-publication-import-v1',status='qualified-saved-cohort-prepared',
        reconciliation=published_review,full_report=public_report,plan=public_ref(reconciliation['plan']),
        terminal=public_ref(reconciliation['terminal']),source_counts=counts_ref,source_adaptation=adaptation_ref,
        endpoints=endpoints,imported_program_inventory=17,imported_endpoint_programs=displayed,
        admitted_workloads=admitted,actual_full_native_processes=81,qualified_samples=81,
        planned_julia_aot_samples=51,planned_matched_mech_samples=30,
        baseline_changed=False,new_minimum_candidates=new_minima,historical_reports_mutated=False,
        old_julia_jit_profiles_preserved=17,controls_replace_mech=False,
        original_producer_chart_flags_preserved=True,native_commands=0,benchmark_runs=0)
    data['julia_aot_audit'] = audit
    for field in ('programs','program_inventory','files','archive_paths'):
        same({key:data[field][key] for key in before[field]},before[field],'Existing '+field+' changed')
    for old,new in zip(before['benchmarks'],data['benchmarks']):
        same(dict(new,groups=[g for g in new['groups'] if g['language']!='julia-aot']),old,
             'Existing benchmark, baseline or language group changed')
    for field in ('languages','reference_summary','formatted_reference_summary'):
        same(data[field][:len(before[field])],before[field],'Existing '+field+' changed')
    allowed = {'programs','program_inventory','files','archive_paths','benchmarks','languages',
               'reference_summary','protocol','language_groups'}
    for field in set(before)-allowed:
        same(data[field],before[field],'Unrelated dataset value changed')
    require(set(module)==set(languages['languages'])=={v['key'] for v in data['languages']},'Taxonomy keys differ')
    encoded = {TARGETS[0]:(json.dumps(data,indent=2,allow_nan=False)+'\n').encode(),
        TARGETS[1]:(json.dumps(languages,indent=2,allow_nan=False)+'\n').encode(),
        TARGETS[2]:(match[1]+json.dumps(module,indent=2,allow_nan=False)+match[3]).encode()}
    return encoded,audit


def import_catalog(args):
    pins = dict(zip(TARGETS,(args.benchmarks_sha256,args.languages_sha256,args.module_sha256)))
    output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(ROOT),'Fresh private output required')
    originals = {name:checked(ROOT/name,digest) for name,digest in pins.items()}
    saved_raw = checked(args.reconciliation,args.reconciliation_sha256)
    saved = json.loads(saved_raw)
    prepared,replaced,temporaries = None,[],[]
    receipt_path = output/'import-receipt.json'
    receipt_sha = None
    def undo():
        for name in reversed(replaced[:]):
            actual = (ROOT/name).read_bytes()
            require(actual==prepared[name],'Catalog changed after apply; preserving unrelated bytes')
            (ROOT/name).write_bytes(originals[name])
            replaced.remove(name)
        for temporary in temporaries[:]:
            if temporary.exists():
                require(not temporary.is_symlink(),'Publication temporary was replaced')
                temporary.unlink()
            temporaries.remove(temporary)
        if receipt_sha is not None and receipt_path.exists():
            checked(receipt_path,receipt_sha)
            receipt_path.unlink()
    try:
        with review_files(args.plan,args.plan_sha256,args.durable_directory,on_failure=undo) as (fresh,plan,report,verify):
            same(fresh,saved,'Independent reconciliation changed')
            prepared,audit = build_publication(originals,plan,report,fresh,
                ref(args.reconciliation,args.reconciliation_sha256))
            checked(__file__,args.importer_sha256)
            verify()
            for name,digest in pins.items():
                checked(ROOT/name,digest)
            output.mkdir(parents=True)
            for name,raw in prepared.items():
                target,backup = output/name,output/'originals'/name
                target.parent.mkdir(parents=True,exist_ok=True)
                backup.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(raw)
                backup.write_bytes(originals[name])
            if args.apply:
                for name,raw in prepared.items():
                    verify()
                    checked(__file__,args.importer_sha256)
                    checked(ROOT/name,pins[name])
                    temporary = ROOT/(name+'.julia-aot-import.tmp')
                    with temporary.open('xb') as stream:
                        temporaries.append(temporary)
                        stream.write(raw)
                        stream.flush()
                        os.fsync(stream.fileno())
                    temporary.replace(ROOT/name)
                    temporaries.remove(temporary)
                    replaced.append(name)
            verify()
            checked(__file__,args.importer_sha256)
            receipt = dict(audit,generated_at=datetime.now(timezone.utc).isoformat(),applied=bool(args.apply),
                inputs=pins,outputs={name:sha(raw) for name,raw in prepared.items()},
                importer=public_ref(ref(__file__,args.importer_sha256)))
            if args.apply:
                receipt['status'] = 'qualified-saved-cohort-imported'
            receipt_sha = write_new(receipt_path,receipt)
        return receipt
    except BaseException:
        undo()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    for action in ('reconcile','import'):
        sub = commands.add_parser(action)
        sub.add_argument('--plan',type=Path,required=True)
        sub.add_argument('--plan-sha256',required=True)
        sub.add_argument('--durable-directory',type=Path,required=True)
        sub.add_argument('--importer-sha256',required=True)
        sub.add_argument('--output',type=Path,required=True)
        if action=='import':
            sub.add_argument('--reconciliation',type=Path,required=True)
            sub.add_argument('--reconciliation-sha256',required=True)
            for name in ('benchmarks','languages','module'):
                sub.add_argument('--'+name+'-sha256',required=True)
            sub.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
            and not sys.flags.optimize,'Use retained Python -I -S -B')
    checked(__file__,args.importer_sha256)
    if args.action=='import':
        receipt = import_catalog(args)
        print(json.dumps({k:receipt[k] for k in ('status','applied','imported_program_inventory',
              'imported_endpoint_programs','new_minimum_candidates','baseline_changed')}),flush=True)
        return
    path,owned = args.output.resolve(),None
    require(not path.exists(),'Fresh reconciliation output required')
    def remove_owned():
        nonlocal owned
        if owned is not None:
            checked(path,owned)
            require(not path.is_symlink(),'Reconciliation result was replaced')
            path.unlink()
            owned = None
    try:
        with review_files(args.plan,args.plan_sha256,args.durable_directory,on_failure=remove_owned) as (result,plan,report,verify):
            source_records(plan,report)
            verify()
            checked(__file__,args.importer_sha256)
            digest = write_new(path,result)
            owned = digest
        print(json.dumps(dict(status=result['status'],path=str(path),sha256=digest,
            qualified_samples=result['qualified_samples'])),flush=True)
    except BaseException:
        remove_owned()
        raise


if __name__=='__main__':
    main()
