"""Retain eleven offline LLVM captures of the existing trimmed Julia image.

prepare hashes the retained closure under the common mutex, without starting any
native process. run uses the frozen owned-process observer. Neither command
executes Julia/N-body or grants native-owner, fallback, AOT or chart admission.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/julia-aot/trimmed-native-inspection-v1'
DRAFT = PACKET/'command-draft.json'
DRAFT_SHA = '4be7d8cca7834f8b8c71d7a92a7283de4ffc9b42ba7c224d05eb41d5f386b9de'
OBSERVER = ROOT/'tools/qualification/kotlin_bounded_v2.py'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
LLVM = Path('/opt/homebrew/Cellar/llvm@22/22.1.8')
SUCCESS = 'eleven-offline-captures-retained-awaiting-native-owner-and-fallback-review'
KIND = 'julia-offline-native-inspection'
FILE_LIMIT = 64*1024**2
FALSE_GATES = ('native_owner_qualified', 'actual_ir_removal_qualified',
               'fallback_closure_qualified', 'runtime_aot_proven', 'chart_admission')
EMPTY_SHA = hashlib.sha256(b'').hexdigest()


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_observer():
    raw = OBSERVER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == OBSERVER_SHA, 'Frozen observer changed')
    module = types.ModuleType('julia_offline_observer'); module.__file__ = str(OBSERVER)
    exec(compile(raw, str(OBSERVER), 'exec'), module.__dict__)
    require((module.TIMEOUT, module.CLEANUP_TIMEOUT, module.RSS_LIMIT, module.FILE_LIMIT) ==
            (30, 5, 2*1024**3, 8*1024**2), 'Reviewed observer policy differs')
    # File-only diagnostics can expand substantially beyond compact bitcode.
    # The immutable observer and its deadline/RSS/ownership logic are unchanged.
    module.FILE_LIMIT = FILE_LIMIT
    return module


kb = load_observer()


def physical(path):
    require(path.is_absolute() and path.resolve() == path, 'Physical absolute path required: '+str(path))


def pin(pins, path, expected=None):
    path = Path(path)
    require(path.is_absolute() and path.is_file(), 'Missing regular input: '+str(path))
    digest = sha(path)
    require(expected is None or digest == expected, 'Input pin differs: '+str(path))
    require(str(path) not in pins or pins[str(path)] == digest, 'Conflicting input pin: '+str(path))
    pins[str(path)] = digest
    return path


def verify(pins, resolutions, unavailable=()):
    for name, digest in pins.items():
        require(Path(name).is_file() and sha(name) == digest, 'Input changed: '+name)
        require(str(Path(name).resolve()) == resolutions[name], 'Input name resolution changed: '+name)
    for name in unavailable:
        require(not os.path.lexists(name), 'Previously absent loader candidate appeared: '+name)


def document(path, expected, pins):
    return json.loads(pin(pins, path, expected).read_bytes())


def known_artifacts(value):
    """Read recorded artifact pairs without inventing a path relocation."""
    found = set()
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            found.add((value['path'], value['sha256']))
        for child in value.values(): found |= known_artifacts(child)
    elif isinstance(value, list):
        for child in value: found |= known_artifacts(child)
    return found


def validate_draft(draft, records):
    require(draft['schema'] == 'julia-trimmed-native-inspection-command-draft-v1'
            and draft['native_commands_planned'] == 11 and draft['native_commands_started'] == 0
            and draft['tool_pins_ready'] is False and draft['tool_hashes'] is None
            and draft['common_mutex_inode'] == 79859134 and draft['run_sequentially'] is True
            and draft['automatic_retry'] is False, 'Exact unexecuted command draft required')
    require(all(draft['proof_gates'][k] is False for k in FALSE_GATES), 'Draft admission changed')
    archive, link, build = (records[n] for n in ('archive_result','link_result','build_result'))
    require(archive['status'] == 'actual-archive-members-and-native-entry-observed-awaiting-root-owner-and-link-review'
            and archive['object_and_bitcode_members_captured'] is True
            and archive['actual_native_inspection_commands'] == 6
            and len(archive['object_members']) == len(archive['optimized_bitcode_members']) == 10,
            'Retained successful archive inspection required')
    require(link['status'] == 'retained-safe-archive-linked-awaiting-runtime-owner-and-fallback-review'
            and link['linker_commands'] == 1 and link['image_observation_commands'] == 4
            and link['original_archive_result_sha256'] == draft['source_records']['archive_result']['sha256'],
            'Retained successful link required')
    require(build['status'] == 'safe-trim-build-complete-awaiting-native-image-and-fallback-review'
            and build['safe_build_exit_status'] == 0
            and build['compiled_sources_and_original_bytes_preserved'] is True,
            'Retained successful unchanged source build required')
    require(all(d[k] is False for d in (archive,link,build) for k in FALSE_GATES), 'Prior admission changed')
    inputs = known_artifacts(archive) | known_artifacts(link) | known_artifacts(build)
    commands = draft['commands']
    require([c['id'] for c in commands] == ['decode-'+f'{i:02}' for i in range(9)]+['native-archive','final-executable'],
            'Exact eleven-command sequence required')
    for index, row in enumerate(commands):
        artifact = row['artifact_input']; name = Path(artifact['path']).name
        require((artifact['path'], artifact['sha256']) in inputs, 'Unbound retained artifact')
        if index < 9:
            expected_name = 'text_opt#'+str(index)+'.bc' if index < 8 else 'metadata_opt.bc'
            expected = [str(LLVM/'bin/llvm-dis'),artifact['path'],'-o','-']
            require(name == expected_name, 'Wrong optimized bitcode member')
        else:
            expected = [str(LLVM/'bin/llvm-objdump'),'--disassemble','--reloc','--syms',artifact['path']]
            require(artifact == ({k:link['archive'][k] for k in ('path','sha256')} if index == 9 else
                    {k:link['binary'][k] for k in ('path','sha256')}), 'Wrong linked archive or final image')
        require(row['argv'] == expected and row['expected_exit'] == row['expected_stderr_bytes'] == 0,
                'Inspection command changed')
    return commands


def macho(path):
    """Read only native arm64 load commands; no loader, dylib or tool is run.

    Layout/constants: selected Apple SDK mach-o/{loader,fat}.h. Universal
    containers must contain one arm64 slice. Unsupported image forms fail closed.
    """
    with path.open('rb') as stream:
        total = os.fstat(stream.fileno()).st_size
        head = stream.read(8); require(len(head) == 8, 'Truncated image header')
        offset, extent = 0, total
        if head[:4] in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'):
            wide = head[:4] == b'\xca\xfe\xba\xbf'; count = struct.unpack('>I', head[4:])[0]
            require(0 < count <= 16, 'Unexpected universal image slice count')
            fmt = '>IIQQII' if wide else '>IIIII'; width = struct.calcsize(fmt)
            slices = []
            for _ in range(count):
                raw = stream.read(width); require(len(raw) == width, 'Truncated universal slice')
                values = struct.unpack(fmt, raw)
                if values[0] == 0x0100000c: slices.append(values)
            require(len(slices) == 1, 'Unique arm64 image slice required')
            offset, extent = slices[0][2:4]
            require(offset >= 8+count*width and extent >= 32 and offset+extent <= total, 'Invalid arm64 slice range')
        stream.seek(offset); header = stream.read(32)
        require(len(header) == 32, 'Missing Mach-O64 header')
        magic,cpu,subtype,filetype,count,size,flags,reserved = struct.unpack('<8I',header)
        require(magic == 0xfeedfacf and cpu == 0x0100000c and filetype in (2,6)
                and 0 < count <= 4096 and 8*count <= size <= 4*1024**2
                and 32+size <= extent, 'Unsupported arm64 Mach-O image')
        data = stream.read(size); require(len(data) == size, 'Truncated load commands')
    imports, rpaths, linkers, commands = [], [], [], []
    position = 0
    for _ in range(count):
        require(position+8 <= size, 'Missing load command')
        command, length = struct.unpack_from('<II',data,position)
        require(length >= 8 and length % 8 == 0 and position+length <= size, 'Malformed load command')
        commands.append(command)
        require(command not in (0x10,0x27), 'Prebound image or embedded dyld environment is unsupported')
        if command in (0xc,0x80000018,0x8000001f,0x20,0x80000023,0x8000001c,0xe):
            minimum = 24 if command in (0xc,0x80000018,0x8000001f,0x20,0x80000023) else 12
            require(length >= minimum, 'Truncated named load command')
            index = struct.unpack_from('<I',data,position+8)[0]
            require(minimum <= index < length, 'Invalid load command name offset')
            value = data[position+index:position+length]
            require(b'\0' in value, 'Unterminated load command name')
            name = value.split(b'\0',1)[0].decode('utf-8')
            require(name and '\n' not in name, 'Empty or multiline load command name')
            if command == 0x8000001c: rpaths.append(name)
            elif command == 0xe: linkers.append(name)
            else: imports.append(dict(command=command, install_name=name))
        position += length
    require(position == size and all(n == '/usr/lib/dyld' for n in linkers), 'Unsupported command extent or dynamic linker')
    return dict(cpu=cpu, subtype=subtype, filetype=filetype, slice_offset=offset, slice_bytes=extent,
                commands=commands, imports=imports, rpaths=rpaths, dynamic_linker=linkers)


def os_image(name):
    return name.startswith('/usr/lib/') or name.startswith('/System/Library/')


def expand(name, image, executable):
    if name.startswith('@loader_path/'):
        value = image.parent/name[len('@loader_path/'):]
    elif name.startswith('@executable_path/'):
        value = executable.parent/name[len('@executable_path/'):]
    else:
        require(name.startswith('/'), 'Unsupported relative loader path: '+name)
        value = Path(name)
    return Path(os.path.normpath(value))


def tool_closure(executables, pins):
    """Declared non-OS dependency closure; never an actual loaded-image claim."""
    images, edges, aliases, system, unavailable = {}, [], {}, set(), set()
    for executable in executables:
        physical(executable)
        require(os.access(executable,os.X_OK), 'LLVM tool is not executable')
        pending = [(executable, ())]; visited = set()
        while pending:
            image, inherited = pending.pop(0)
            key = (str(image),inherited)
            if key in visited: continue
            visited.add(key); require(len(visited) <= 128, 'Unbounded declared tool dependency graph')
            pin(pins,image); info = macho(image)
            images[str(image)] = dict(sha256=pins[str(image)], bytes=image.stat().st_size, load_commands=info)
            paths = tuple(dict.fromkeys([str(expand(n,image,executable)) for n in info['rpaths']]+list(inherited)))
            for item in info['imports']:
                name = item['install_name']
                if name.startswith('@rpath/'):
                    candidates = [Path(os.path.normpath(Path(p)/name[len('@rpath/'):])) for p in paths]
                else: candidates = [expand(name,image,executable)]
                for candidate in candidates:
                    if not os_image(str(candidate)) and not candidate.is_file():
                        require(not os.path.lexists(candidate), 'Nonregular or dangling loader candidate')
                        unavailable.add(str(candidate))
                available = [p for p in candidates if os_image(str(p)) or p.is_file()]
                require(all(os_image(str(p)) or not os_image(str(p.resolve())) for p in available),
                        'Non-OS loader alias into OS-managed image is unsupported')
                targets = {str(p) if os_image(str(p)) else str(p.resolve()) for p in available}
                require(len(targets) == 1, 'Missing or ambiguous declared dependency: '+name)
                target = targets.pop()
                edges.append(dict(executable=str(executable),image=str(image),install_name=name,
                                  command=item['command'],target=target,os_managed=os_image(target)))
                if os_image(target): system.add(target); continue
                for alias in available:
                    aliases[str(alias)] = str(alias.resolve())
                    pin(pins,alias)
                target_path = Path(target); physical(target_path)
                pending.append((target_path,paths))
    return dict(scope='static Mach-O declared transitive non-OS load dependencies; not actual loaded images',
                images=images,edges=edges,named_path_resolutions=aliases,unavailable_candidates=sorted(unavailable),
                os_managed_install_names=sorted(system),
                os_boundary='OS images/dyld shared cache recorded by install name, not newly file-hashed',
                actual_loaded_images_observed=False)


def environment(directory):
    return dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C',
                HOME=str(directory/'home'), TMPDIR=str(directory/'tmp'),
                OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')


def build_plan(output):
    physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(), 'Fresh packet output required')
    pins = {}; draft = document(DRAFT,DRAFT_SHA,pins); records = {}
    for name, ref in draft['source_records'].items():
        path = pin(pins,ref['path'],ref['sha256'])
        if path.suffix == '.json': records[name] = json.loads(path.read_bytes())
    commands = validate_draft(draft,records)
    for record in records.values():
        for path,digest in record.get('pins',{}).items(): pin(pins,path,digest)
    for row in commands:
        item=row['artifact_input']; path=pin(pins,item['path'],item['sha256'])
        if 'bytes' in item: require(path.stat().st_size == item['bytes'], 'Retained artifact size changed')
    for path,digest in ((Path(__file__).resolve(),None), (Path(__file__).with_name('test_julia_native_inspection.py'),None),
        (PACKET/'README.md',None), (OBSERVER,OBSERVER_SHA), (Path(kb.kh.__file__),kb.HELPER_CONTROLLER_SHA),
        (Path(kb.eb.__file__),kb.REFERENCE_CONTROLLER_SHA), (kb.kh.PYTHON,kb.kh.PYTHON_SHA)):
        pin(pins,path,digest)
    tools = tool_closure([LLVM/'bin/llvm-dis',LLVM/'bin/llvm-objdump'],pins)
    resolutions = {name:str(Path(name).resolve()) for name in pins}
    schedule = [dict(id=row['id'], directory=f'{index:02}-'+row['id'], command=row['argv'],
                     input=dict(row['artifact_input'],bytes=Path(row['artifact_input']['path']).stat().st_size))
                for index,row in enumerate(commands)]
    return dict(schema='julia-eleven-offline-inspection-plan-v1', status='prepared-awaiting-independent-review',
        controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),output=str(output),
        draft=dict(path=str(DRAFT),sha256=DRAFT_SHA), pins=pins, input_resolutions=resolutions,
        source_records=draft['source_records'], tool_closure=tools, schedule=schedule,
        commands=[dict(argv=s['command'],cwd=str(output/s['directory']),environment=environment(output/s['directory'])) for s in schedule],
        native_commands=11, candidate_executions=0, compilations=0, links=0, debugger_attempts=0,
        benchmark_samples=0, automatic_retry=False, common_mutex_inode=79859134,
        process_timeout_seconds=kb.TIMEOUT,cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT,native_file_limit_bytes=kb.FILE_LIMIT,
        capture_limit_reason='64MiB per stream allows offline IR/relocation text expansion; bounded failure never retries',
        **{k:False for k in FALSE_GATES})


def inventory(directory, exclude=()):
    physical(directory); require(directory.is_dir(), 'Artifact directory missing')
    found = {}
    for path in sorted(directory.rglob('*')):
        mode=path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'Linked or nonregular capture artifact')
        name=str(path.relative_to(directory))
        if stat.S_ISREG(mode) and name not in exclude:
            size=path.stat().st_size
            require(size <= FILE_LIMIT+kb.PIPE_CHUNK, 'Captured artifact exceeds bound')
            found[name]=dict(bytes=size,sha256=sha(path))
    require(len(found) <= 11*5+2, 'Unexpected capture file count')
    return found


def stamp(value):
    parsed=datetime.fromisoformat(value); require(parsed.tzinfo is not None, 'Timezone required')
    return parsed


def checked_capture(slot, directory, parent):
    start,active,final = [json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start,active,final):
        require(record['command'] == slot['command'] and record['environment'] == environment(directory)
            and record['cwd'] == str(directory) and record['kind'] == KIND
            and record['started_at'] == start['started_at'] and record['stdin_bytes'] == 0
            and record['stdin_sha256'] == EMPTY_SHA and record['inherited_common_mutex'] is True
            and record['common_mutex_inode'] == 79859134 and record['process_timeout_seconds'] == kb.TIMEOUT
            and record['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT
            and record['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT
            and record['native_file_limit_bytes'] == FILE_LIMIT
            and record['stdout_capture_limit_bytes'] == FILE_LIMIT+kb.PIPE_CHUNK
            and record['stdout_transport'] == 'OS pipe, retained as received'
            and record['stderr_transport'] == 'exclusive artifact'
            and record['benchmark_samples'] == 0
            and record['source_work_qualified'] is record['chart_admission'] is False, 'Native launch contract differs')
    identity,leader,pid = final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status'] == 'starting' and start['native_process_started'] is False
        and active['status'] == 'running' and active['native_process_started'] is True
        and final['native_process_started'] is True and active['identity'] == identity
        and type(parent) is int and parent > 0 and identity['ppid'] == parent
        and all(type(identity[k]) is int and identity[k] == leader[k]
                for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and type(pid) is int and pid > 0
        and active['pid'] == active['pgid'] == pid == final['pgid'] == identity['pid'] == identity['pgid']
        and leader['status'] == 5 and final['direct_child_reaped'] is True
        and final['remaining_process_group'] == final.get('remaining_after_cleanup',[]) == []
        and final['stop_signals'] == final['cleanup_errors'] == [] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
        and final['status'] == 'native-passed' and type(final['exit_status']) is int and final['exit_status'] == 0
        and not final.get('error') and not final.get('error_type')
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples'] > 0
        and 0 < final['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT
        and stamp(start['started_at']) <= stamp(final['finished_at']), 'Native ownership or normal exit differs')
    for name in ('stdout','stderr'):
        path=directory/(name+'.bin')
        require(path.stat().st_size == final[name+'_bytes'] and sha(path) == final[name+'_sha256'], 'Captured stream changed')
    require(final['stdout_bytes'] > 0 and final['stderr_bytes'] == 0, 'Empty offline capture or unexpected stderr')
    snapshot=inventory(directory)
    require(set(snapshot) == {'start.json','active.json','process.json','stdout.bin','stderr.bin'}, 'Unexpected native files')
    return dict(id=slot['id'],directory=slot['directory'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        stdout_bytes=final['stdout_bytes'],stdout_sha256=final['stdout_sha256'],process_sha256=snapshot['process.json']['sha256'],
        captured_native_output=True,**{k:False for k in FALSE_GATES}),snapshot


def finish(report, plan, output, pins, resolutions, lock):
    errors=[]; available={}; held=False
    try:
        verify(pins,resolutions,plan.get('tool_closure',{}).get('unavailable_candidates',())); kb.kh.verify_lock(lock); held=True
        entries=report['registered_commands']; attempts=report['attempted_commands']
        require(attempts == [s['directory'] for s in plan['schedule'][:len(attempts)]] and len(attempts) <= 11,
                'Attempted command sequence differs')
        require(len(entries) == report['native_processes_started'] <= len(attempts)
            and [e['directory'] for e in entries] == attempts[:len(entries)]
            and len({e['pid'] for e in entries}) == len(entries), 'Native registration differs')
        receipts={str(p.relative_to(output)) for p in output.glob('*/process.json')}
        require(receipts == {d+'/process.json' for d in attempts}, 'Native receipt inventory differs')
        for directory in attempts:
            rec=json.loads((output/directory/'process.json').read_bytes())
            expected=next((e for e in entries if e['directory'] == directory),None)
            require(rec['cleanup_errors'] == [] and not rec.get('artifact_errors'), 'Failed cleanup/artifact retention')
            if expected:
                require(rec['native_process_started'] is True and rec['pid'] == expected['pid']
                    and rec['direct_child_reaped'] is True
                    and rec.get('remaining_process_group',[]) == rec.get('remaining_after_cleanup',[]) == [], 'Owned process not closed')
            else: require(rec['native_process_started'] is False and not rec.get('pid'), 'Unregistered native process')
        for slot,capture in zip(plan['schedule'],report['captures']):
            current,snapshot=checked_capture(slot,output/slot['directory'],os.getpid())
            require(current == capture and snapshot == report['validated_artifacts'][slot['directory']], 'Validated capture changed')
        require(len(report['captures']) == len(report['validated_artifacts']), 'Capture snapshot inventory differs')
        for previous,current in zip(report['captures'],report['captures'][1:]):
            require(stamp(previous['finished_at']) <= stamp(current['started_at']), 'Native commands overlapped')
        if report['status'] == SUCCESS:
            require(len(report['captures']) == len(entries) == len(attempts) == 11, 'Incomplete eleven-command stage')
        available=inventory(output,('report.json','terminal.json'))
        for directory,snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')} == snapshot,
                    'Final inventory adopted changed validated bytes')
    except BaseException as error: errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,artifacts=available)
    if errors: report['status']='failed-integrity'
    kb.save(output/'report.json',report)
    try:
        closure=inventory(output,('terminal.json',))
        require({n:v for n,v in closure.items() if n != 'report.json'} == available, 'Final artifact closure changed')
        require(closure['report.json']['sha256'] == sha(output/'report.json'), 'Final report changed')
        verify(pins,resolutions,plan.get('tool_closure',{}).get('unavailable_candidates',())); held=False; kb.kh.verify_lock(lock); held=True
        require(inventory(output,('terminal.json',)) == closure,
                'Captured bytes or report changed during final input verification')
        held=False; kb.kh.verify_lock(lock); held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__); report['status']='failed-integrity'; closure={}
        kb.save(output/'report.json',report)
    terminal=dict(schema='julia-eleven-offline-inspection-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),available_evidence=closure,integrity_errors=errors,
        native_processes_started=report['native_processes_started'],capture_count=len(report['captures']),
        common_mutex_held=held,common_mutex_inode=79859134,benchmark_samples=0,candidate_executions=0,
        **{k:False for k in FALSE_GATES})
    with (output/'terminal.json').open('x') as stream: stream.write(json.dumps(terminal,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run');run.add_argument('--plan',type=Path,required=True);run.add_argument('--plan-sha256',required=True)
    args=parser.parse_args();physical(args.plan)
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == kb.kh.PYTHON.resolve(), 'Use exact retained Python -I -S -B without -O')
    def interrupted(signum,frame): raise KeyboardInterrupt('Julia offline inspection interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA, 'Retained Python changed')
        if args.mode == 'prepare':
            require(not args.plan.exists() and not args.plan.is_relative_to(args.output), 'Fresh external plan required')
            plan=build_plan(args.output)
            verify(plan['pins'],plan['input_resolutions'],plan['tool_closure']['unavailable_candidates']);kb.kh.verify_lock(lock)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('x') as stream: stream.write(json.dumps(plan,indent=2)+'\n')
            print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes_started=0)));return 0
        pins={};plan=document(args.plan,args.plan_sha256,pins);output=Path(plan['output'])
        require(plan == build_plan(output), 'Concrete prepared plan differs')
        pins.update(plan['pins']); resolutions=dict(plan['input_resolutions'],**{str(args.plan):str(args.plan.resolve())})
        verify(pins,resolutions,plan['tool_closure']['unavailable_candidates']);output.mkdir(parents=True,exist_ok=False)
        report=dict(schema='julia-eleven-offline-inspection-results-v1',status='running',plan=str(args.plan),
            plan_sha256=args.plan_sha256,controller_sha256=sha(__file__),pins=pins,input_resolutions=resolutions,
            started_at=datetime.now(timezone.utc).isoformat(),active=None,attempted_commands=[],registered_commands=[],
            native_processes_started=0,captures=[],validated_artifacts={},benchmark_samples=0,candidate_executions=0,
            **{k:False for k in FALSE_GATES})
        kb.save(output/'report.json',report)
        try:
            for slot in plan['schedule']:
                # The full inherited closure was checked before the run and is
                # checked again at finalization. Recheck each command's exact
                # native inputs/tools between captures, not all old build files.
                names = set(plan['tool_closure']['images']) | set(plan['tool_closure']['named_path_resolutions'])
                names.add(slot['input']['path'])
                verify({n:pins[n] for n in names},{n:resolutions[n] for n in names},
                       plan['tool_closure']['unavailable_candidates']);kb.kh.verify_lock(lock)
                directory=output/slot['directory'];directory.mkdir()
                for name in ('home','tmp'):(directory/name).mkdir()
                report['attempted_commands'].append(slot['directory']);kb.save(output/'report.json',report)
                def launched(pid):
                    report['native_processes_started']+=1
                    report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
                    report['active']=dict(directory=slot['directory'],pid=pid);kb.save(output/'report.json',report)
                kb.observe(slot['command'],environment(directory),directory,b'',lock,launched,kind=KIND)
                capture,snapshot=checked_capture(slot,directory,os.getpid())
                with kb.atomic():
                    report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
                    report['active']=None;kb.save(output/'report.json',report)
            report['status']=SUCCESS
        except BaseException as error:
            report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        finally:
            with kb.atomic(): finish(report,plan,output,pins,resolutions,lock)
        print(json.dumps(dict(status=report['status'],captures=len(report['captures']),report_sha256=sha(output/'report.json'))))
        return 0 if report['status'] == SUCCESS else 1


if __name__ == '__main__': raise SystemExit(main())
