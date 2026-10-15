"""Prepare and own 81 fresh whole-process Julia AOT/control timing slots.

Draft reads source/count metadata without requiring completed native apps.
Prepare and run require completed builds and separate no-codegen validations,
bind every app bundle file/link, and reuse the frozen sampler and supervisor.
This module launches nothing on import and never imports benchmark results.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/julia/packagecompiler-v1'
LOCK = Path('/tmp/mech-clbg-timing.lock')
SUITE_LEASE = PACKET/'julia-aot-full81.owner.lock'
HELPERS = ROOT/'tools/qualification/elixir_full.py'
HELPERS_SHA = '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'
SUPERVISOR = ROOT/'tools/qualification/prolog_supervisor.py'
SUPERVISOR_SHA = '5458bdf5e58465cb21156a2140657066b4706aa2a0941fe3efde8758207574b4'
BENCHES = ('regexredux','revcomp','pidigits','spectralnorm','mandelbrot',
           'fasta','knucleotide','binarytrees','nbody','fannkuchredux')
PROFILES = {
    'binarytrees': ('binarytrees-julia-3','binarytrees-julia-4'),
    'fannkuchredux': ('fannkuchredux-julia-1','fannkuchredux-julia-2'),
    'fasta': ('fasta-julia-3',), 'knucleotide': ('knucleotide-julia-1','knucleotide-julia-6'),
    'mandelbrot': ('mandelbrot-julia-1','mandelbrot-julia-7'), 'nbody': ('nbody-julia-5',),
    'pidigits': ('pidigits-julia-3','pidigits-julia-4'),
    'regexredux': ('regexredux-julia-1','regexredux-julia-3'),
    'revcomp': ('revcomp-julia-7','revcomp-julia-9'), 'spectralnorm': ('spectralnorm-julia-4',),
}
STDIN_BENCHES = {'regexredux','knucleotide','revcomp'}
RUNTIME_ARGUMENTS = ['--julia-args','--startup-file=no','--history-file=no','--compile=no']
RUNTIME_ENVIRONMENT = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',
    JULIA_NUM_THREADS='8,0',JULIA_LOAD_CODEGEN_LIB='0',OPENBLAS_NUM_THREADS='1',
    OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
POLICY = ('Fresh direct PackageCompiler executable including process/runtime startup, app image and '
    'bundled library loading, full regular-file stdin, all work, complete output and shutdown; '
    'Julia code generation disabled by --compile=no and JULIA_LOAD_CODEGEN_LIB=0. '
    'JULIA_NUM_THREADS=8,0 fixes eight compute threads and zero interactive threads for every '
    'scored process and its separate output validation; application algorithms are unchanged. '
    'Offline app compilation/training, harness setup, pin hashing, environment waits and output '
    'validation excluded. Existing JIT measurements and fixed baselines are unchanged.')
_HELPERS = None


def require(condition,message):
    if not condition:raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def binding(path):
    path=Path(path).absolute()
    require(path.is_file() and not path.is_symlink(),'Regular evidence file required: '+str(path))
    return dict(path=str(path),sha256=sha(path))


def merge(*groups):
    result={}
    for group in groups:
        for path,digest in group.items():
            require(path not in result or result[path]==digest,'Conflicting pin: '+path)
            result[path]=digest
    return result


def read_ref(reference,pins):
    path=Path(reference['path'])
    require(path.is_absolute() and '..' not in path.parts and re.fullmatch('[0-9a-f]{64}',reference['sha256']),
            'Exact absolute evidence reference required')
    require(sha(path)==reference['sha256'],'Evidence changed: '+str(path))
    pins.update(merge(pins,{str(path):reference['sha256']}))
    return json.loads(path.read_bytes())


def new_json(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def cold(path,expected,name):
    raw=Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected,'Frozen implementation changed: '+str(path))
    require(name not in sys.modules,'Unexpected cached prerequisite module')
    module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def helpers():
    global _HELPERS
    if _HELPERS is None:_HELPERS=cold(HELPERS,HELPERS_SHA,'julia_aot_full81_frozen_helpers')
    return _HELPERS


def checked_runtime():helpers().checked_runtime()
def common_lock():return helpers().common_lock()
def held_lock(lock):return helpers().held_lock(lock)
def verify_lock(lock):helpers().verify_lock(lock)
def verify(pins):helpers().verify(pins)
def load_measurement():return helpers().load_measurement()
def refresh_attempt_accounting(report):helpers().refresh_attempt_accounting(report)
def preserve_wrapper_failure(*args):return helpers().preserve_wrapper_failure(*args)
def isolated_failure(*args):return helpers().isolated_failure(*args)


def qualified_sample(attempt,manifest,row,fingerprint):
    helpers().qualified_sample(attempt,manifest,row,fingerprint)
    require(attempt.get('stderr')=='','Qualified native sample requires empty stderr')


def absolute_source(value):
    path=Path(value)
    require(not path.is_absolute() and '..' not in path.parts,'Source must be repository-relative')
    return ROOT/path


def source_rows(adaptation_ref,counts_ref,pins):
    adaptation=read_ref(adaptation_ref,pins);counts=read_ref(counts_ref,pins)
    require(adaptation['schema']=='julia-packagecompiler-source-adaptation-v1'
            and counts['schema']=='julia-packagecompiler-source-counts-v1'
            and counts['status']=='counted-and-source-diagnostics-reviewed','Source/count metadata differs')
    require(counts['source_adaptation']['sha256']==adaptation_ref['sha256']
            and str(absolute_source(counts['source_adaptation']['path']))==adaptation_ref['path'],
            'Counts do not bind the exact supplied adaptation receipt')
    adapted={row['profile']:row for row in adaptation['profiles']}
    counted={row['profile']:row for row in counts['profiles']}
    expected={profile for group in PROFILES.values() for profile in group}
    require(len(adaptation['profiles'])==len(counts['profiles'])==len(expected)==17
            and set(adapted)==set(counted)==expected,'Exact seventeen profiles required')
    result={}
    for bench,profiles in PROFILES.items():
        for profile in profiles:
            a,c=adapted[profile],counted[profile]
            require(a['workload']==c['workload']==bench and a['program_key']==c['program_key']==bench+':'+profile
                    and a['adapted_source']==c['source'],'Adaptation/count source identity differs')
            require(all(type(c[field]) is int and c[field]>0 for field in ('canonical_loc','physical_loc')),
                    'Positive complete adapted source counts required')
            source=absolute_source(c['source']['path'])
            for item in (a['adapted_source'],a['original_source'],a['original_manifest'],a['project']):
                path=absolute_source(item['path']);pins[str(path)]=item['sha256']
            physical=dict(path=str(source),sha256=c['source']['sha256'],role='application',counted=True,
                          canonical_loc=c['canonical_loc'],physical_loc=c['physical_loc'])
            result[profile]=dict(id=profile+'-aot',key=bench+':'+profile+'-aot',original_profile_id=profile,
                original_program_key=a['program_key'],benchmark=bench,language='julia-aot',
                source=str(source),source_sha256=c['source']['sha256'],physical_inputs=[physical],
                loc=c['canonical_loc'],canonical_loc=c['canonical_loc'],physical_loc=c['physical_loc'],
                formatted_loc=None,source_work_qualified=False,canonical_loc_qualified=True,
                formatted_loc_qualified=False,execution_mode='aot',maximum_workers=8,
                source_alias_of=None,timing_alias_of=None,separate_fresh_samples_required=True,
                counts_evidence=copy.deepcopy(counts_ref),source_adaptation_evidence=copy.deepcopy(adaptation_ref),
                original_source=dict(a['original_source'],path=str(absolute_source(a['original_source']['path']))),
                original_source_repository_path=a['original_source']['path'],package=str(absolute_source(a['package'])),
                memory_policy='Retained Julia default garbage collection',
                runtime_policy_changes=[],diagnostic_flags=[],chart_admission=False)
    return result


def schedule_for(manifests):
    require(set(manifests)==set(BENCHES),'Exactly ten workload manifests required')
    slots=[]
    for bench in BENCHES:
        manifest=manifests[bench];rows=manifest['profiles']
        ids=[profile+'-aot' for profile in PROFILES[bench]]+['mech-aot-control']
        require([row['id'] for row in rows]==ids and manifest['samples']==3,'Cohort or sample count differs')
        orders=[dict(round=index+1,profiles=ids[index%len(ids):]+ids[:index%len(ids)]) for index in range(3)]
        require(manifest['orders']==orders,'Three rotating rounds differ')
        keys={row['id']:row['key'] for row in rows}
        slots.extend((bench,order['round'],identifier,keys[identifier]) for order in orders for identifier in order['profiles'])
    require(len(slots)==len(set(slots))==81 and len({slot[3] for slot in slots})==27,'Full81 schedule differs')
    return slots


def build_draft(output,adaptation_ref,counts_ref,bundle_root,evidence_map_ref=None):
    pins={};rows=source_rows(adaptation_ref,counts_ref,pins)
    # Fixture selection is metadata, so it is bound by the draft even while
    # completed app build/validation reports are still unavailable.
    training=read_ref(binding(PACKET/'training-inputs.json'),pins)
    for item in training['profiles']:
        if item.get('corpus_manifest'):
            reference=item['corpus_manifest']
            pins.update(merge(pins,{str(absolute_source(reference['path'])):reference['sha256']}))
    overrides=read_ref(evidence_map_ref,pins) if evidence_map_ref else {}
    require(type(overrides) is dict and set(overrides)<=set(rows),'Unknown evidence-map profile')
    h=helpers();controls=h.controls(pins);manifests={}
    pins.update(merge(pins,h.SAMPLER_PINS,{str(HELPERS):HELPERS_SHA,str(h.SHARED):h.SHARED_SHA,
        str(h.SUPERVISOR):h.SUPERVISOR_SHA,str(h.PYTHON):h.PYTHON_SHA,
        str(Path(__file__).resolve()):sha(Path(__file__).resolve())}))
    for bench in BENCHES:
        subjects=[]
        for profile in PROFILES[bench]:
            row=copy.deepcopy(rows[profile]);override=overrides.get(profile,{})
            require(set(override)<= {'bundle','build_report','build_terminal','validation_reports','image_identity'},
                    'Unknown per-profile evidence override')
            bundle=Path(override.get('bundle',str(Path(bundle_root)/profile/'bundle'))).absolute()
            require(not '..' in bundle.parts,'Noncanonical bundle path')
            executable=bundle/'bin'/profile
            row.update(binary=str(executable),bundle=str(bundle),sysimage=str(bundle/'lib/julia/sys.dylib'),
                command=[str(executable)]+([] if bench in STDIN_BENCHES else ['{n}'])+RUNTIME_ARGUMENTS,
                cwd=str(bundle),runtime_environment=copy.deepcopy(RUNTIME_ENVIRONMENT),
                build_report_path=override.get('build_report',str(PACKET/'builds'/(profile+'-v1')/'report.json')),
                build_terminal_path=override.get('build_terminal',str(PACKET/'builds'/(profile+'-v1')/'terminal.json')),
                validation_report_paths=override.get('validation_reports',[str(PACKET/'validation'/(profile+'-v1')/'report.json')]),
                image_identity_path=override.get('image_identity',
                    str(PACKET/'validation'/(profile+'-v1')/'image-identity.json') if profile=='nbody-julia-5' else None))
            subjects.append(row)
        control=controls[bench];control['key']=bench+':julia-aot-full-study:mech-control'
        group=subjects+[control];ids=[row['id'] for row in group]
        size,count,digest=h.FULL[bench]
        manifests[bench]=dict(benchmark=bench,profiles=group,samples=3,size=size,
            orders=[dict(round=index+1,profiles=ids[index%len(ids):]+ids[:index%len(ids)]) for index in range(3)],
            canonical_full_workload=True,timeout_seconds=21600,supervisor_timeout_seconds=22200,maximum_rss_mib=10240,
            full_output_reference=None if bench=='nbody' else dict(bytes=count,sha256=digest),
            compilation_outside_timer=True,runtime_and_app_image_loading_inside_timer=True,
            julia_codegen_disabled=True,regular_file_stdin=True,no_automatic_retry=True,
            shared_timing_lock=str(LOCK),chart_admission=False)
    return dict(schema='julia-aot-full81-plan-v1',status='draft-awaiting-completed-builds-and-validation',
        controller=str(Path(__file__).resolve()),repository=str(ROOT),output=str(Path(output).absolute()),
        source_adaptation=adaptation_ref,qualified_source_counts=counts_ref,evidence_map=evidence_map_ref,
        bundle_root=str(Path(bundle_root).absolute()),pins=pins,manifests=manifests,
        schedule=[list(slot) for slot in schedule_for(manifests)],source_work_profiles=17,canonical_loc_profiles=17,
        formatted_loc_profiles=0,samples=3,julia_aot_samples=51,matched_mech_samples=30,full_processes=81,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,new_native_probes=0,
        original_files_mutated=False,shared_timing_lock=str(LOCK),suite_lease=str(SUITE_LEASE),
        common_mutex_inode=79859134,continuous_common_mutex=True,no_automatic_retry=True,
        pins_verified=False,full_timings_qualified=False,chart_admission=False,timing_policy=POLICY)


def bundle_inventory(bundle,hash_files=True):
    """Bind names, modes, link text/resolution, and every reachable regular file."""
    bundle=Path(bundle)
    require(bundle.is_absolute() and not bundle.is_symlink() and bundle.resolve()==bundle and bundle.is_dir(),
            'Physical absolute app bundle required')
    inventory={};pins={}
    def visit(path,relative,ancestors):
        mode=path.lstat().st_mode
        if stat.S_ISLNK(mode):
            resolved=path.resolve(strict=True)
            inventory[relative]=dict(kind='symlink',mode=stat.S_IMODE(mode),target=os.readlink(path),resolved=str(resolved))
            if resolved.is_dir():
                require(resolved not in ancestors,'Cyclic bundle directory link')
                for child in sorted(path.iterdir()):visit(child,relative+'/'+child.name,ancestors|{resolved})
            else:
                require(resolved.is_file(),'Symlink target is not a regular file or directory')
                inventory[relative].update(bytes=resolved.stat().st_size,target_mode=stat.S_IMODE(resolved.stat().st_mode))
                if hash_files:
                    digest=sha(path);pins[str(path)]=pins[str(resolved)]=digest
                    inventory[relative]['sha256']=digest
        elif stat.S_ISDIR(mode):
            resolved=path.resolve();require(resolved not in ancestors,'Cyclic bundle directory')
            inventory[relative]=dict(kind='directory',mode=stat.S_IMODE(mode))
            for child in sorted(path.iterdir()):visit(child,relative+'/'+child.name if relative else child.name,ancestors|{resolved})
        else:
            require(stat.S_ISREG(mode),'Nonregular app bundle member')
            inventory[relative]=dict(kind='file',bytes=path.stat().st_size,mode=stat.S_IMODE(mode))
            if hash_files:
                digest=sha(path);pins[str(path)]=digest;inventory[relative]['sha256']=digest
    visit(bundle,'',set())
    return dict(root=str(bundle),entries=inventory),pins


def completed_subject(row,pins):
    """No runtime is launched here; validate completed, separately saved evidence."""
    report_ref=binding(row['build_report_path']);terminal_ref=binding(row['build_terminal_path'])
    report=read_ref(report_ref,pins);terminal=read_ref(terminal_ref,pins)
    require(report['schema']=='julia-packagecompiler-build-v1' and report['status']=='built-awaiting-output-validation'
            and terminal['status']==report['status'] and report['exit_code']==0 and report['errors']==[]
            and report['input_files_unchanged'] is True and report['remaining_process_group']==[]
            and report['benchmark_samples']==terminal['benchmark_samples']==0
            and terminal['report_sha256']==report_ref['sha256'],'Completed clean build required: '+row['id'])
    require(report['executable']['path']==row['binary'] and report['command'][-1]==row['original_profile_id']
            and report['command'][-3]==row['bundle'],'Build app identity differs')
    command=report['command'];profile=row['original_profile_id']
    training_ref=binding(PACKET/'training-inputs.json');training=read_ref(training_ref,pins)
    training_rows=[item for item in training['profiles'] if item['profile']==profile]
    require(len(training_rows)==1 and training_rows[0]['workload']==row['benchmark'],
            'Exact retained training/validation profile mapping required')
    training_path=str(absolute_source(training_rows[0]['training']))
    build_threads=report['environment'].get('JULIA_NUM_THREADS')
    require(build_threads in ('8','8,0')
            and (profile!='fannkuchredux-julia-2' or build_threads=='8,0'),
            'Fannkuch2 corrected build/training requires eight compute and zero interactive threads; '
            'other retained builds may use the historical eight-thread build environment')
    require(command==[command[0],'--startup-file=no','--history-file=no','--color=no',
        '--project='+str(PACKET/'toolchain'),str(PACKET/'build_app.jl'),row['package'],row['bundle'],
        training_path,profile],'Expected PackageCompiler recipe/package/training command required')
    required_inputs=[str(PACKET/'build_app.jl'),training_path,
        str(PACKET/'toolchain/Project.toml'),str(PACKET/'toolchain/Manifest.toml'),
        str(Path(row['package'])/'Project.toml'),row['source'],command[0]]
    require(set(required_inputs)<=set(report['input_sha256']),'Build recipe input closure is incomplete')
    require(report['input_sha256'][training_path]==training_rows[0]['sha256'],
            'Build did not bind the selected training source')
    pins.update(merge(pins,report['input_sha256']))
    require(report['input_sha256'].get(row['source'])==row['source_sha256'],'Build did not bind the counted adapted source')
    for name,field in (('stdout.txt','stdout_sha256'),('stderr.txt','stderr_sha256')):
        path=Path(row['build_terminal_path']).parent/name
        require(sha(path)==terminal[field],'Build output log changed');pins[str(path)]=terminal[field]
    inventory,artifacts=bundle_inventory(row['bundle']);pins.update(merge(pins,artifacts))
    executable_sha=sha(row['binary']);image_sha=sha(row['sysimage'])
    require(report['executable']['sha256']==executable_sha,'Launcher differs from the completed build')
    validation_refs=[];image_bound=False;validation_artifacts={};validated_cases=[]
    selected=training_rows[0].get('corpus_manifest')
    corpus_ref=(dict(path=str(absolute_source(selected['path'])),sha256=selected['sha256']) if selected
                else binding(ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json'))
    corpus=Path(corpus_ref['path']).parent
    cases=read_ref(corpus_ref,pins)['cases']
    require(type(row['validation_report_paths']) is list and row['validation_report_paths'],
            'At least one completed no-codegen output validation required')
    for path in row['validation_report_paths']:
        reference=binding(path);validation=read_ref(reference,pins)
        require(validation['schema']=='julia-packagecompiler-native-output-v1' and validation['status']=='passed'
                and validation['profile']==row['original_profile_id'] and validation['errors']==[]
                and validation['exit_code']==0 and validation['complete_output_matches'] is True
                and validation['executable_unchanged'] is True and validation['remaining_process_group']==[]
                and validation['executable_sha256']==executable_sha and validation['benchmark_samples']==0
                and validation['environment']==RUNTIME_ENVIRONMENT
                and validation['command'][0]==row['binary'] and validation['command'][-4:]==RUNTIME_ARGUMENTS,
                'Clean completed no-codegen validation required: '+row['id'])
        matches=[case for case in cases if case['benchmark']==row['benchmark'] and case['case']==validation['case']]
        require(len(matches)==1 and matches[0]['expected_exit']==0,'Known successful bounded case required')
        case=matches[0]
        validated_cases.append(case['case'])
        expected_command=[row['binary']]+([str(case['n'])] if case['input_kind']=='integer-argument' else [])+RUNTIME_ARGUMENTS
        require(validation['command']==expected_command and validation['stdin_sha256']==case['stdin']['sha256']
            and validation['expected_sha256']==case['expected']['sha256'],'Bounded case argv/input/oracle differs')
        for field in ('stdin','expected'):
            path=corpus/case[field]['path'];require(sha(path)==case[field]['sha256'],'Bounded corpus changed')
            pins[str(path)]=case[field]['sha256'];validation_artifacts[str(path)]=case[field]['sha256']
        if 'sysimage' in validation:
            require(validation['sysimage']==dict(path=row['sysimage'],sha256=image_sha)
                    and validation['sysimage_unchanged'] is True,'Validated sysimage differs')
            image_bound=True
        directory=Path(reference['path']).parent
        for name,field in (('actual.stdout','stdout_sha256'),('actual.stderr','stderr_sha256')):
            artifact=directory/name;require(sha(artifact)==validation[field],'Validation output log changed')
            pins[str(artifact)]=validation[field]
            validation_artifacts[str(artifact)]=validation[field]
        validation_refs.append(reference)
    require(training_rows[0]['case'] in validated_cases,'Default retained validation case was not completed')
    image_ref=None
    if row['image_identity_path']:
        image_ref=binding(row['image_identity_path']);identity=read_ref(image_ref,pins)
        require(identity['schema']=='julia-packagecompiler-built-image-identity-v1'
                and identity['profile']==row['original_profile_id'] and identity['path']==row['sysimage']
                and identity['sha256']==image_sha and identity['bytes']==Path(row['sysimage']).stat().st_size,
                'Supplementary image identity differs')
        image_bound=True
    require(image_bound,'Validation must bind the actual sysimage, directly or through supplementary identity')
    row.update(binary_sha256=executable_sha,sysimage_sha256=image_sha,build_evidence=report_ref,
        build_terminal_evidence=terminal_ref,validation_evidence=validation_refs,image_identity_evidence=image_ref,
        bounded_corpus_evidence=corpus_ref,training_inputs_evidence=training_ref,source_work_qualified=True,
        validation_artifact_pins=validation_artifacts,bundle_inventory=inventory,support=dict(pins=artifacts),
        runtime_arguments=copy.deepcopy(RUNTIME_ARGUMENTS))
    return inventory


def prepare_plan(draft):
    plan=copy.deepcopy(draft);pins=plan['pins'];inventories={}
    for manifest in plan['manifests'].values():
        for row in manifest['profiles']:
            if row['language']=='julia-aot':inventories[row['original_profile_id']]=completed_subject(row,pins)
    h=helpers()
    shared=merge(h.SAMPLER_PINS,{str(HELPERS):HELPERS_SHA,str(h.SHARED):h.SHARED_SHA,
        str(SUPERVISOR):SUPERVISOR_SHA,str(h.PYTHON):h.PYTHON_SHA,
        plan['controller']:pins[plan['controller']],plan['source_adaptation']['path']:plan['source_adaptation']['sha256'],
        plan['qualified_source_counts']['path']:plan['qualified_source_counts']['sha256']})
    execution={}
    for bench,manifest in plan['manifests'].items():
        active_input={}
        if bench in STDIN_BENCHES:
            path=str(h.CLBG/('regexredux/.build/input5000000.txt' if bench=='regexredux'
                           else 'knucleotide/.build/knucleotide-input25000000.txt'))
            active_input[path]=pins[path]
        if bench in ('pidigits','regexredux'):
            path=str(h.CLBG/bench/'inputs/output-full.txt');active_input[path]=pins[path]
        for row in manifest['profiles']:
            selected=merge(shared,active_input,{row['source']:row['source_sha256'],row['binary']:row['binary_sha256']},
                           row.get('support',{}).get('pins',row.get('support',{})))
            if row['language']=='julia-aot':
                refs=[row['build_evidence'],row['build_terminal_evidence'],row['counts_evidence'],
                      row['source_adaptation_evidence'],row['bounded_corpus_evidence'],row['training_inputs_evidence'],row['original_source']]
                refs+=row['validation_evidence']
                if row['image_identity_evidence']:refs.append(row['image_identity_evidence'])
                selected=merge(selected,{ref['path']:ref['sha256'] for ref in refs},row['validation_artifact_pins'])
            elif row.get('control_provenance'):
                ref=row['control_provenance'];selected=merge(selected,{ref['path']:ref['sha256']})
            require(all(pins.get(path)==digest for path,digest in selected.items()),'Scoped execution pin is outside global closure')
            execution[row['key']]=selected
    plan.update(status='prepared-awaiting-independent-review',pins_verified=True,bundle_inventories=inventories,
                shared_execution_pins=shared,execution_pins=execution)
    verify(pins)
    return plan


def validate_plan(plan,prepared=False):
    expected=build_draft(plan['output'],plan['source_adaptation'],plan['qualified_source_counts'],
                         plan['bundle_root'],plan['evidence_map'])
    if prepared:expected=prepare_plan(expected)
    require(plan==expected,'Plan differs from exact source/count/build/validation/bundle closure or schedule')


def check_execution_inputs(plan,harness,active_row=None):
    helpers().check_execution_inputs(plan,harness)
    for profile,expected in plan['bundle_inventories'].items():
        if active_row is not None and (active_row['language']!='julia-aot' or active_row['original_profile_id']!=profile):continue
        actual,_=bundle_inventory(expected['root'],hash_files=active_row is None)
        wanted=expected if active_row is None else dict(expected,entries={name:{key:value for key,value in entry.items()
            if key!='sha256'} for name,entry in expected['entries'].items()})
        require(actual==wanted,'App bundle membership, bytes, modes or symlink targets changed: '+profile)
    for manifest in plan['manifests'].values():
        if manifest['benchmark'] in STDIN_BENCHES:
            source=harness.INPUTS[manifest['benchmark']][1]
            require(stat.S_ISREG(source.stat().st_mode),'Full stdin must remain a regular seekable file')
        for row in manifest['profiles']:
            if row['language']=='julia-aot':
                require(row['runtime_environment']==RUNTIME_ENVIRONMENT and row['command']==[row['binary']]
                    +([] if row['benchmark'] in STDIN_BENCHES else ['{n}'])+RUNTIME_ARGUMENTS,
                    'Julia AOT command/runtime policy changed')


def draft(args):
    require(not args.plan.exists() and not args.output.exists(),'Fresh draft and output required')
    plan=build_draft(args.output,binding(args.source_adaptation),binding(args.source_counts),args.bundle_root,
                     binding(args.evidence_map) if args.evidence_map else None)
    require(not args.plan.absolute().is_relative_to(args.output.absolute()),'Plan overlaps output')
    new_json(args.plan,plan)
    print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_executions=0,pins_verified=False)),flush=True)


def prepare(args):
    checked_runtime();require(not args.plan.exists(),'Prepared plan must be fresh')
    require(sha(args.draft)==args.draft_sha256,'Reviewed draft changed')
    with common_lock() as lock:
        plan=json.loads(args.draft.read_bytes());validate_plan(plan)
        require(not Path(plan['output']).exists(),'Timing output already exists')
        plan=prepare_plan(plan);_,harness=load_measurement();check_execution_inputs(plan,harness)
        verify_lock(lock);new_json(args.plan,plan)
        print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),full_processes=81,native_executions=0)),flush=True)


def run_locked(args, live_lock):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan, prepared=True)
    output = Path(plan['output'])
    require(not output.exists(), 'No overwrite, implicit resume, or repeated sample')
    output.parent.mkdir(parents=True,exist_ok=True)
    # The suite lease also excludes another cohort using a different output.
    lease_path = SUITE_LEASE
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with held_lock(live_lock) as lock:
            verify(plan['pins'])
            guard,harness = load_measurement()
            check_execution_inputs(plan, harness)
            supervisor = cold(SUPERVISOR, SUPERVISOR_SHA, 'julia_aot_full81_independent_supervisor')
            verify_lock(lock)
            schedule = schedule_for(plan['manifests'])
            require([list(slot) for slot in schedule] == plan['schedule'], 'Reviewed schedule changed')
            pins = merge(plan['pins'],{str(args.plan.resolve()):args.plan_sha256})
            manifests = copy.deepcopy(plan['manifests'])
            for bench,manifest in manifests.items():
                require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                        and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                        and manifest['maximum_rss_mib'] == 10240,
                        'Workload or resource policy changed')
            output.mkdir()
            guard.OUT,guard.REPORT = output,output/'report.json'
            harness.install_interrupt_handlers()
            rows = {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],measurement_status='pending')
                    for manifest in manifests.values() for row in manifest['profiles']}
            require(len(rows) == 27,'Full cohort changed')
            report = dict(schema='julia-aot-full81-report-v1',status='running',started_at=guard.now(),supervisor=guard.identity(os.getpid()),
                plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,programs=rows,attempts=[],active=None,
                benchmark_order=BENCHES,completed_benchmarks=[],sample_count=3,full_performance_runs=0,
                skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=str(LOCK),
                source_work_profiles=17,canonical_loc_profiles=17,formatted_loc_profiles=0,
                planned_julia_aot_samples=51,planned_matched_mech_samples=30,full_timings_qualified=False,
                chart_admission=False,no_automatic_retry=True)
            refresh_attempt_accounting(report)
            guard.save(guard.REPORT,report)
        try:
            for bench,round_index,identifier,key in schedule:
                row,manifest = rows[key],manifests[bench]
                if row.get('full_failure'):
                    report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                    guard.save(guard.REPORT,report)
                    continue
                with held_lock(live_lock) as lock:
                    active_pins=merge(plan['execution_pins'][key],{str(args.plan.resolve()):args.plan_sha256})
                    active_manifest=dict(manifest,pins=active_pins)
                    verify(active_pins)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    check_execution_inputs(plan, harness,active_row=row)
                    verify_lock(lock)
                    print('JULIA AOT FULL',bench,round_index,identifier,manifest['size'],flush=True)
                    try:
                        attempt = supervisor.one_attempt(guard,harness,row,active_manifest,report,round_index,lock.fileno())
                    except BaseException as error:
                        preserve_wrapper_failure(guard,report,row,round_index,error)
                        raise
                    verify_lock(lock)
                    report['attempts'].append(attempt)
                    report['active']=None
                    row['attempts'].append(attempt['attempt'])
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    # Frozen sampler and supervisor artifacts are never edited.
                    raw = json.loads(Path(attempt['result_path']).read_bytes())
                    supervised = json.loads(Path(attempt['supervisor_result_path']).read_bytes())
                    require(supervised == attempt and all(attempt.get(k) == v for k,v in raw.items()),
                            'Raw sampler and supervised records differ')
                    if attempt['qualified']:
                        qualified_sample(attempt,manifest,row,harness.execution_fingerprint(row))
                        row['samples_seconds'].append(attempt['seconds'])
                        row['sample_validation'].append(attempt['validation'])
                        row['measurement_status']='measured' if len(row['samples_seconds']) == 3 else 'partial'
                    elif isolated_failure(guard,attempt):
                        row['measurement_status']='failed-full-workload'
                        row['full_failure']=dict(attempt)
                        report['isolated_failed_profiles'].append(key)
                    else:
                        row['measurement_status']='stopped-unqualified'
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')
                group = [rows[r['key']] for r in manifest['profiles']]
                if all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in group):
                    control = next(r for r in group if r['language']=='mech')
                    for r in group:
                        if not r.get('full_failure'):
                            r.update(median_seconds=statistics.median(r['samples_seconds']),
                                     sample_stdev_seconds=statistics.stdev(r['samples_seconds']))
                    for r in group:
                        r['time_x_mech'] = (r['median_seconds']/control['median_seconds']
                                           if not r.get('full_failure') and not control.get('full_failure') else None)
                        r['matched_mech_control']=control['key']
                        r['matched_mech_source_sha256']=control['source_sha256']
                    if bench not in report['completed_benchmarks']:
                        report['completed_benchmarks'].append(bench)
                    guard.save(guard.REPORT,report)
            require(len(report['attempts'])+len(report['skipped_failed_profile_slots']) == 81
                    and len(report['completed_benchmarks']) == 10,'Incomplete full81 accounting')
            require(report['full_performance_runs'] == len(report['attempts']),'Native attempt accounting mismatch')
            report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                          finished_at=guard.now())
        except BaseException as error:
            report.update(status='stopped-unqualified',finished_at=guard.now(),error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
            (output/'error.log').write_text(traceback.format_exc())
            raise
        finally:
            with held_lock(live_lock) as lock:
                errors=[]
                for path,expected in pins.items():
                    try:
                        require(sha(path)==expected,'Pinned bytes changed')
                    except BaseException as error:
                        errors.append(dict(path=path,error=str(error) or type(error).__name__,error_type=type(error).__name__))
                try:
                    check_execution_inputs(plan, harness)
                except BaseException as error:
                    errors.append(dict(path='<prerequisite-and-app-bundle-inventories>',
                        error=str(error) or type(error).__name__, error_type=type(error).__name__))
                report['pins_unchanged_at_end'] = not errors
                refresh_attempt_accounting(report)
                if errors:
                    report['status_before_terminal_integrity_failure'] = report['status']
                    report['status'] = 'failed-terminal-integrity'
                    report['terminal_integrity_errors'] = errors
                verify_lock(lock)
                guard.save(guard.REPORT,report)
                available={str(p):sha(p) for p in output.rglob('*') if p.is_file()}
                new_json(output/'terminal.json',dict(schema='julia-aot-full81-terminal-v1',status='failed-terminal-integrity' if errors else report['status'],
                    report=str(guard.REPORT),report_sha256=sha(guard.REPORT),prerequisite_pins=pins,
                    available_evidence_pins=available,integrity_errors=errors,common_mutex_held=True,
                    common_mutex_held_continuously=True,common_mutex_inode=os.fstat(lock.fileno()).st_ino,
                    suite_lease=str(SUITE_LEASE),bundle_inventories=plan['bundle_inventories'],
                    full_performance_runs=report['full_performance_runs'],saved_attempts=len(report['attempts']),
                    registered_native_attempts=report['registered_native_attempts'],
                    native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
                    qualified_samples=report['qualified_samples'],
                    skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
                    compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,
                    repeated_completed_samples=0,original_files_mutated=False,full_timings_qualified=False,chart_admission=False))
                verify_lock(lock)
                require(not errors,'Terminal integrity failed; actual attempts preserved')


def run(args):
    # A single inherited descriptor remains locked through environment waits,
    # all 81 slots, every cleanup and the final evidence/terminal write.
    with common_lock() as lock:
        run_locked(args, lock)



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_subparsers(dest='mode',required=True)
    source=modes.add_parser('draft',help='Read source/count metadata; completed apps are not yet required')
    source.add_argument('--source-adaptation',type=Path,default=PACKET/'source-adaptation.json')
    source.add_argument('--source-counts',type=Path,default=PACKET/'source-counts.json')
    source.add_argument('--bundle-root',type=Path,default=Path('/private/tmp/mech-julia-packagecompiler-builds-v1'))
    source.add_argument('--evidence-map',type=Path,help='Optional JSON mapping original profile IDs to actual bundle/build/validation paths')
    source.add_argument('--plan',type=Path,required=True)
    source.add_argument('--output',type=Path,required=True)
    prep=modes.add_parser('prepare',help='Require completed builds, no-codegen validation, and exact full app closures')
    prep.add_argument('--draft',type=Path,required=True)
    prep.add_argument('--draft-sha256',required=True)
    prep.add_argument('--plan',type=Path,required=True)
    execute=modes.add_parser('run',help='Execute only the exact prepared plan, without retry or import')
    execute.add_argument('--plan',type=Path,required=True)
    execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    {'draft':draft,'prepare':prepare,'run':run}[args.mode](args)


if __name__=='__main__':main()
