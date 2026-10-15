"""File-only review of the closed Julia debugger intake; starts no process."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import struct

E = Path('/private/tmp/mech-benchmark-completion')
HERE = E/'experiments/julia-aot/entry-dispatch-v1'
RUN = HERE/'intake-run-v2'
OUT = Path('/private/tmp/mech-history-candidate-validation/julia-entry-tool-intake-v1')
REPORT_SHA = '7092cebd79afc20b967c66843b2d6d803dd0f3bd2367db92251a6d6ff74496df'
READER = E/'tools/qualification/julia_native_inspection.py'
READER_SHA = '877bda82e014e16a5380cc46b283ba90dca71f02c4a285994df5c54ab883489a'
pins, resolutions = {}, {}


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(name, expected=None):
    named = Path(name)
    physical = named.resolve(strict=True)
    require(physical.is_absolute(), 'Absolute input required')
    before = physical.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular input required: '+str(physical))
    fd = os.open(physical, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    final = physical.lstat()
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    require(all(getattr(before,k)==getattr(opened,k)==getattr(after,k)==getattr(final,k)
                for k in fields), 'Input changed while reading: '+str(physical))
    require(expected is None or digest == expected, 'Input digest differs: '+str(named))
    require(str(physical) not in pins or pins[str(physical)] == digest, 'Conflicting pin')
    require(named.resolve(strict=True) == physical, 'Named input resolution changed')
    pins[str(physical)] = digest
    resolutions[str(named)] = str(physical)
    return dict(path=str(physical), sha256=digest)


def document(path, expected=None):
    ref = pin(path, expected)
    return json.loads(Path(ref['path']).read_bytes()), ref


def save(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


report, report_ref = document(RUN/'report.json', REPORT_SHA)
require(report['schema'] == 'julia-entry-two-tool-intake-results-v1'
        and report['status'] == 'two-tool-observations-closed-awaiting-intake-review'
        and report['subject_executions'] == 0 and report['static_api_complete'] is True
        and all(report[k] is True for k in ('all_owned_groups_empty',
            'all_owned_processes_absent','common_mutex_held_through_closure')),
        'Closed zero-subject observations required')
for name, expected in report['input_pins'].items():
    ref = pin(name, expected)
    require(ref['path'] == report['input_resolutions'][name], 'Original resolution differs')
for relative, item in report['artifacts'].items():
    path = RUN/relative
    require(path.stat().st_size == item['bytes'], 'Artifact size differs')
    pin(path, item['sha256'])
require(len(report['commands']) == 2, 'Exactly two intake commands required')
for index, row in enumerate(report['commands']):
    process, _ = document(Path(row['directory'])/'process.json')
    require(process == row['process'] and process['command'] == row['command']
        and process['direct_child_reaped'] is True and process['remaining_process_group'] == []
        and process['cleanup_errors'] == [] and process['stop_signals'] == []
        and process.get('timed_out', False) is False and process['benchmark_samples'] == 0,
        'Command ownership/closure differs')
    require(process['exit_status'] == (1 if index == 0 else 0)
        and process['status'] == ('failed' if index == 0 else 'native-passed'),
        'Actual intake exit/status differs')
    if index == 0:
        require(process['error'] == 'Native command exited unsuccessfully',
                'Unexpected debugserver failure')
    for kind in ('stdout','stderr'):
        content = (Path(row['directory'])/(kind+'.bin')).read_bytes()
        require(len(content) == process[kind+'_bytes']
            and hashlib.sha256(content).hexdigest() == process[kind+'_sha256'],
            'Process/stream identity differs')

observation, observation_ref = document(RUN/'01-static-api/observation.json')
stdout = (RUN/'01-static-api/stdout.bin').read_text()
offset = stdout.index('{\n')
parsed, end = json.JSONDecoder().raw_decode(stdout[offset:])
require(parsed == observation and stdout[offset+end:] == '\n',
        'Saved static observation differs from raw stdout')
require((RUN/'01-static-api/stderr.bin').read_bytes() == b''
        and (RUN/'00-debugserver-usage/stdout.bin').read_bytes() == b'',
        'Unexpected intake stream')
usage = (RUN/'00-debugserver-usage/stderr.bin').read_bytes()
require(len(usage) == 533 and b'debugserver /path/file --attach=<pid>' in usage,
        'Local Unix attach interface not observed')
require(observation['schema'] == 'julia-entry-zero-subject-api-observation-v1'
        and observation['status'] == 'zero-subject-static-api-observation-complete'
        and observation['subject_executions'] == 0 and observation['native_inferior_created'] is False,
        'Static no-subject observation incomplete')
require(all(all(fields.values()) for fields in observation['api_member_presence'].values()),
        'Required API absent')
require([x['command'] for x in observation['settings']] == [
    'settings set target.load-script-from-symbol-file false',
    'settings set symbols.enable-external-lookup false']
    and all(x['succeeded'] is True and x['stderr'] == '' for x in observation['settings']),
    'Required settings were not accepted')
require(observation['breakpoints'] == 27 and observation['module_subscription_mask'] == 6,
        'Static breakpoint/event subscription differs')

draft, draft_ref = document(HERE/'plan-draft.json', observation['source_pins']['draft_sha256'])
trace_ref = pin(HERE/'trace.py', observation['source_pins']['trace_sha256'])
trace_ast = ast.parse(Path(trace_ref['path']).read_bytes())
addresses = {node.targets[0].id: ast.literal_eval(node.value) for node in trace_ast.body
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    and node.targets[0].id in ('MAIN','RUNTIME')}
expected_breakpoints = [(role, name, hex(address)) for role, key in
    (('main','MAIN'),('runtime','RUNTIME')) for name,address in addresses[key].items()]
actual_breakpoints = [(event['role'],event['name'],event['file_address'])
    for event in observation['events'] if event['kind'] == 'breakpoint-installed']
require(actual_breakpoints == expected_breakpoints and len(set(actual_breakpoints)) == 27,
        'Static breakpoints differ from fixed source')
layout = observation['codeinstance_type']
required_layout = {'def':(0,8),'owner':(8,8),'next':(16,8),'min_world':(24,8),
    'max_world':(32,8),'inferred':(64,8),'flags':(108,1),'invoke':(112,8),'specptr':(120,8)}
require(layout['name'] == 'jl_code_instance_t' and layout['bytes'] == 128
        and {k:(v['offset'],v['bytes']) for k,v in layout['required_layout'].items()} == required_layout,
        'Observed CodeInstance layout differs from reviewed retained header')
modules = {'main': dict(path=draft['subject']['path'], uuid='ABB0315D-ABDF-3208-A9E7-97CD2EF84005'),
    'runtime': dict(path=draft['retained_runtime']['path'], uuid='A9EAD8CA-7573-3B14-8DD6-39BDC818E737')}
for role, module in modules.items():
    matches = [x for x in observation['modules'] if x['path'] == module['path']]
    require(len(matches) == 1 and matches[0]['uuid'] == module['uuid']
        and matches[0]['load_address'] == '0xffffffffffffffff', 'Static module identity differs')
require(observation['runtime_symbol_file'] == draft['retained_runtime']['matching_dwarf_path'],
        'Different DWARF selected')

# The frozen parser is reused unchanged. Only the private candidate walk below
# accepts bare loader tokens and records OS fallback alternatives without
# pretending that dyld-cache candidates are all simultaneously selected.
reader_ref = pin(READER, READER_SHA)
reader_ast = ast.parse(READER.read_bytes())
reader_ast.body = [node for node in reader_ast.body
    if isinstance(node, ast.FunctionDef) and node.name in ('require','macho','os_image')]
require({node.name for node in reader_ast.body} == {'require','macho','os_image'}, 'Reader extraction differs')
reader = dict(os=os, struct=struct, Path=Path)
exec(compile(reader_ast, str(READER), 'exec'), reader)
parser_text = ast.get_source_segment(READER.read_text(), next(node for node in reader_ast.body if node.name == 'macho'))
require(parser_text.count('if values[0] == 0x0100000c: slices.append(values)') == 1,
        'Frozen slice selector changed')
subtype_parser = parser_text.replace('def macho(path):', 'def macho(path, selected_subtype):').replace(
    'if values[0] == 0x0100000c: slices.append(values)',
    'if values[0] == 0x0100000c and values[1] == selected_subtype: slices.append(values)')
subtype_reader = dict(reader)
exec(compile(subtype_parser, str(READER)+'#explicit-subtype', 'exec'), subtype_reader)


def image_variants(path):
    # Only select the original parser's fat slice; its header/range/load-command
    # validation remains intact. Every arm64 subtype is retained, not selected
    # on the basis of an unobserved runtime CPU preference.
    with path.open('rb') as stream:
        head = stream.read(8)
        if head[:4] not in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'):
            return [reader['macho'](path)]
        count = struct.unpack('>I', head[4:])[0]
        require(0 < count <= 16, 'Unexpected fat slice count')
        fmt = '>IIQQII' if head[:4] == b'\xca\xfe\xba\xbf' else '>IIIII'
        rows = [struct.unpack(fmt, stream.read(struct.calcsize(fmt))) for _ in range(count)]
    subtypes = [row[1] for row in rows if row[0] == 0x0100000c]
    require(subtypes and len(set(subtypes)) == len(subtypes), 'Duplicate/missing arm64 subtype')
    return [subtype_reader['macho'](path, subtype) for subtype in subtypes]


def expand(name, image, executable):
    if name == '@loader_path' or name.startswith('@loader_path/'):
        path = image.parent/name[len('@loader_path'):].lstrip('/')
    elif name == '@executable_path' or name.startswith('@executable_path/'):
        path = executable.parent/name[len('@executable_path'):].lstrip('/')
    else:
        require(name.startswith('/'), 'Unsupported loader token: '+name)
        path = Path(name)
    return Path(os.path.normpath(path))


def declared_candidates(roots):
    images, edges, missing, system = {}, [], set(), set()
    for root in roots:
        executable = Path(root)
        require(executable.resolve(strict=True) == executable and os.access(executable,os.X_OK),
                'Physical executable root required')
        pending, visited = [(executable, ())], set()
        while pending:
            image, inherited = pending.pop(0)
            key = (str(image), inherited)
            if key in visited:
                continue
            visited.add(key)
            require(len(visited) <= 512, 'Unexpected tool dependency graph extent')
            ref = pin(image)
            variants = image_variants(image)
            info = variants[0]
            require(all(all(v[k] == info[k] for k in ('imports','rpaths','dynamic_linker'))
                for v in variants), 'Different subtype dependency policy needs explicit review: '+str(image))
            images[str(image)] = dict(**ref, bytes=image.stat().st_size, arm64_load_command_variants=variants)
            paths = tuple(dict.fromkeys([str(expand(p,image,executable)) for p in info['rpaths']]+list(inherited)))
            for item in info['imports']:
                name = item['install_name']
                candidates = ([Path(os.path.normpath(Path(p)/name[len('@rpath/'):])) for p in paths]
                    if name.startswith('@rpath/') else [expand(name,image,executable)])
                choices = []
                for candidate in candidates:
                    text = str(candidate)
                    if reader['os_image'](text):
                        system.add(text)
                        choices.append(dict(path=text, kind='os-managed-candidate-not-file-probed'))
                    elif candidate.exists():
                        target = pin(candidate)
                        require(not reader['os_image'](target['path']), 'Non-OS alias into OS-managed input')
                        choices.append(dict(path=text, kind='physical-non-os-candidate', **{
                            'resolved_path':target['path'], 'sha256':target['sha256']}))
                        pending.append((Path(target['path']),paths))
                    else:
                        require(not candidate.is_symlink(), 'Dangling candidate')
                        missing.add(text)
                        choices.append(dict(path=text, kind='absent-non-os-candidate'))
                require(any(x['kind'] != 'absent-non-os-candidate' for x in choices),
                        'Unresolved declared input: '+name)
                edges.append(dict(executable=str(executable), image=str(image),
                    install_name=name, command=item['command'], ordered_candidates=choices))
    return dict(scope='Declared Mach-O candidate closure, preserving ordered physical and OS-managed alternatives; not dynamic loader selection.',
        reader=reader_ref, images=images, edges=edges,
        absent_non_os_candidates=sorted(missing), os_managed_candidates=sorted(system),
        os_boundary='System images and dyld shared cache are named, not individually hashed.',
        actual_loaded_images_observed=False, dynamic_resolution_complete=False)


tools = dict(lldb=report['commands'][1]['command'][0], debugserver=report['commands'][0]['command'][0],
    scripting_python=str(Path(observation['scripting']['prefix'])/'Python3'))
require(observation['scripting']['version'].startswith('3.9.6 ')
    and observation['scripting']['executable'] == tools['lldb'], 'Embedded scripting identity differs')
closure = declared_candidates([tools['lldb'],tools['debugserver']])
require(tools['scripting_python'] in closure['images'], 'Python framework not in declared LLDB closure')
wrapper_ref = pin(observation['scripting']['lldb_wrapper'])

# Bind the supplied standard-library source/extension inventory used by this
# scripting runtime, without claiming all files were imported or all dlopen
# dependencies were dynamically observed. Test/GUI/package-installer modules
# and writable bytecode caches are outside this diagnostic's declared scope.
stdlib = Path(observation['scripting']['prefix'])/'lib/python3.9'
stdlib_refs = []
for directory, subdirs, names in os.walk(stdlib):
    subdirs[:] = sorted(d for d in subdirs if d not in
        ('__pycache__','site-packages','test','tests','idlelib','ensurepip'))
    for name in sorted(names):
        path = Path(directory)/name
        if path.suffix in ('.py','.so'):
            stdlib_refs.append(pin(path))
lldb_python_refs = [pin(path) for path in sorted(Path(wrapper_ref['path']).parent.rglob('*.py'))]

sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include')
sdk_refs = {name:pin(sdk/name) for name in ('spawn.h','sys/spawn.h','sys/_types.h',
    'sys/_types/_pid_t.h','sys/_types/_sigset_t.h','machine/_types.h','arm/_types.h')}
spawn = Path(sdk_refs['spawn.h']['path']).read_text()
flags = Path(sdk_refs['sys/spawn.h']['path']).read_text()
for token in ('typedef  void *posix_spawnattr_t;', 'typedef  void *posix_spawn_file_actions_t;',
              'posix_spawn_file_actions_addinherit_np', 'posix_spawn_file_actions_addchdir_np'):
    require(token in spawn, 'Required spawn declaration absent')
for name, number in (('SETPGROUP','0x0002'),('SETSIGDEF','0x0004'),('SETSIGMASK','0x0008'),
                     ('START_SUSPENDED','0x0080'),('CLOEXEC_DEFAULT','0x4000')):
    require(any('POSIX_SPAWN_'+name in line and number in line for line in flags.splitlines()),
            'Spawn flag declaration differs')
manual_ref = pin('/Library/Developer/CommandLineTools/usr/share/man/man1/lldb.1')
for name in ('controller.py','owned_processes.py','client.py','trace.py'):
    pin(HERE/name)
builder_ref = pin(Path(__file__))

require(not OUT.exists(), 'Fresh private intake directory required')
OUT.mkdir(mode=0o700)
for name in ('home','tmp'):
    (OUT/name).mkdir(mode=0o700)
environment = dict(HOME=str(OUT/'home'), TMPDIR=str(OUT/'tmp'),
    PATH='/usr/bin:/bin:/usr/sbin:/sbin', LANG='C', LC_ALL='C',
    OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
closure_ref = save(OUT/'declared-tool-closure.json', closure)
pin(closure_ref['path'], closure_ref['sha256'])
capability_evidence = [report_ref, observation_ref,
    pin(RUN/'00-debugserver-usage/stderr.bin'),pin(RUN/'00-debugserver-usage/process.json'),
    pin(RUN/'01-static-api/stdout.bin'),pin(RUN/'01-static-api/process.json'),
    wrapper_ref, manual_ref, *sdk_refs.values()]
capabilities = ('darwin_suspended_spawn_abi','owned_debugserver_unix_attach',
    'lldb_no_init_batch_source','lldb_python_client_apis','required_debugger_settings',
    'matching_module_uuids','matching_codeinstance_dwarf_fields')
intake = dict(schema='julia-entry-debugger-tool-intake-v1',
    status='reviewed-local-debugger-transport-and-api-intake',
    reviewed_at=datetime.now(timezone.utc).isoformat(), subject_executions=0,
    capabilities={name:True for name in capabilities},
    closure_scope='physical-tools-scripting-runtime-and-declared-dependencies',
    tools=tools, modules=modules, capability_evidence=capability_evidence,
    pins=dict(pins), input_resolutions=dict(resolutions),
    cwd=str(E), subject_environment=dict(environment,JULIA_LOAD_CODEGEN_LIB='0'),
    debugger_environment=environment,
    declared_tool_closure=closure_ref, builder=builder_ref,
    scripting=dict(observed=observation['scripting'], framework_image=pin(tools['scripting_python']),
        wrapper=wrapper_ref, standard_library_files=stdlib_refs, lldb_python_files=lldb_python_refs,
        inventory_scope='Exact .py and .so files under Python3.9 standard library except test/tests/idlelib/ensurepip/site-packages and bytecode caches; full LLDB wrapper Python source tree. File presence is not an observed-import claim.'),
    declarations=dict(headers=sdk_refs, abi='Darwin arm64: opaque void* handles, signed32 pid_t, unsigned32 sigset_t, short flags; pointer-to-handle spawn APIs.',
        suspended_spawn_executed=False),
    static_observation=dict(reference=observation_ref, breakpoints=27,
        codeinstance_bytes=128, required_layout=layout['required_layout'],
        process_apis_present_but_unexercised=observation['unexercised_process_methods']),
    debugserver_interface=dict(usage_exit_status=1, producer_status='failed',
        expected_error='Native command exited unsuccessfully', stderr_bytes=533,
        reviewed_form='debugserver /path/file --attach=<pid>',
        actual_owned_unix_transport_tested=False),
    preserved_prior_failure=report['preserved_prior_failure'],
    limitations=[
        'Capability approval is limited to local declarations, captured command interface, static LLDB APIs/settings, UUIDs and DWARF. It is not a successful attach or owned-process diagnostic.',
        'Declared Mach-O candidates preserve ordered OS fallbacks without claiming complete dynamic resolution or loaded-image coverage. Dynamic Python imports and OS cache contents are not an observed closure.',
        'Exact input aliases and absent candidates were checked during this intake; the existing controller replays physical file pins. Actual diagnostic module identities are checked by its unchanged trace logic.',
        'Private HOME and TMPDIR are fresh for the one-shot diagnostic; no prior capture directory is reused for writable runtime files.',
        'Version/source association is not bit-for-bit runtime source equivalence.'],
    owned_transport_native_verified=False, native_owner_qualified=False,
    actual_ir_removal_qualified=False, fallback_closure_qualified=False,
    runtime_aot_proven=False, timing_qualified=False, chart_admission=False)
# Final file-only replay binds every physical input and current named alias.
for name, expected in list(pins.items()):
    pin(name, expected)
for name, expected in list(resolutions.items()):
    require(str(Path(name).resolve(strict=True)) == expected, 'Final alias resolution differs')
for name in closure['absent_non_os_candidates']:
    require(not os.path.lexists(name), 'Absent candidate appeared')
intake['pins'] = dict(pins)
intake['input_resolutions'] = dict(resolutions)
ref = save(OUT/'tool-intake.json', intake)
print(json.dumps(dict(intake=ref, physical_pins=len(pins), declared_images=len(closure['images']),
    declared_edges=len(closure['edges']), standard_library_files=len(stdlib_refs),
    lldb_python_files=len(lldb_python_refs), native_processes_started=0), indent=2))
