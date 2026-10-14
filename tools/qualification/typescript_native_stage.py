"""Prepare and own one strict TypeScript compile and one AST capture.

No benchmark main or source counter runs. Native execution is serialized under
the established mutex. The reader owns one API compiler child and awaits close;
the frozen supervisor independently requires the process group to be empty.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'experiments/typescript/native-stage-v1'
TOOLS = ROOT/'experiments/typescript/toolchain-v1'
SOURCES = ROOT/'experiments/typescript/source-v1'
FIXTURES = ROOT/'experiments/typescript/source-counts-v1/fixtures.json'
ORIGINAL_READER = ROOT/'experiments/typescript/source-counts-v1/reader.mjs'
ORIGINAL_READER_SHA = '5376ab0a67541801ec3265d213f3fbb884101a49a15945638d8021600c36e219'
OBSERVER = ROOT/'tools/qualification/kotlin_bounded_v2.py'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
NODE = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
NODE_SHA = '27db838bb204ef7c21df2931f5656e4c8fb32e6e947f363a402b49714d32b5b1'
PINS = {
    TOOLS/'retained-packages-v1.json': '40fdd02167fa7cb5b2196255639bd28c0482b2a5e581746798f388b04d165810',
    TOOLS/'native-versions-v1/report.json': 'b981b918f2ccd6e1b26a3c4e90278405df8019754d1d325a0abb6b85580587d8',
    TOOLS/'native-versions-v1/terminal.json': '4887242c40097d7d1c08e8ec5e5ee00f13b8f2515d69f353a15b884b079a0121',
    SOURCES/'source-manifest.json': 'eedaf4ddfe7a89e7833f9fb0d124786cb83aed700d67a83dfb4720ef6a29ffde',
    FIXTURES: '1bb37feb2effab6984fbcf2895677c2ff79ea69ff01d2de39a9b4d3a360eb867',
}
BENCHES = ('binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
           'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm')
STAGED_FILES = tuple(b+'.ts' for b in BENCHES)+('tsconfig.json','package.json')
VENDOR_IMAGES = {
    'node': ['/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation',
             '/System/Library/Frameworks/Security.framework/Versions/A/Security',
             '/usr/lib/libc++.1.dylib', '/usr/lib/libSystem.B.dylib'],
    'tsc': ['/usr/lib/libSystem.B.dylib', '/usr/lib/libresolv.9.dylib',
            '/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation',
            '/System/Library/Frameworks/CoreServices.framework/Versions/A/CoreServices'],
}


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_observer():
    raw = OBSERVER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == OBSERVER_SHA, 'Frozen observer changed')
    spec = importlib.util.spec_from_file_location('typescript_stage_observer', OBSERVER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(OBSERVER), 'exec'), module.__dict__)
    return module


kb = load_observer()


def merge(pins, additions):
    for path, digest in additions.items():
        require(path not in pins or pins[path] == digest, 'Conflicting pin: '+path)
        pins[path] = digest


def metadata(path, digest, pins):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Metadata changed: '+str(path))
    merge(pins, {str(path): digest})
    return json.loads(raw)


def new_json(path, value):
    with Path(path).open('x') as stream: stream.write(json.dumps(value, indent=2)+'\n')


def physical_path(path):
    require(path.is_absolute() and str(path.resolve()) == str(path), 'Physical absolute path required')


def package_inventory(packages):
    for package in packages:
        directory = Path(package['installation_directory'])
        paths = list(directory.rglob('*'))
        require(directory.is_dir() and not directory.is_symlink() and not any(p.is_symlink() for p in paths)
                and all(p.is_file() or p.is_dir() for p in paths)
                and {str(p.relative_to(directory)) for p in paths if p.is_file()} == set(package['files']),
                'Retained package file inventory changed')
        require(all((directory/name).stat().st_size == item['bytes'] for name, item in package['files'].items()),
                'Retained package file size changed')


def macho_vendor_images(path, expected):
    # Header/load-command inspection only; no executable, loader or runtime runs.
    with Path(path).open('rb') as stream:
        header = stream.read(32)
        require(len(header) == 32, 'Missing Mach-O header')
        magic, cpu, _, kind, count, size, _, _ = struct.unpack('<8I', header)
        require(magic == 0xfeedfacf and cpu == 0x100000c and kind == 2
                and 0 < count <= 100 and 0 < size <= 65536, 'Unexpected retained arm64 executable header')
        data = stream.read(size)
    require(len(data) == size, 'Truncated Mach-O commands')
    offset, images = 0, []
    for _ in range(count):
        require(offset+8 <= len(data), 'Missing Mach-O command')
        command, length = struct.unpack_from('<II', data, offset)
        require(length >= 8 and length % 8 == 0 and offset+length <= len(data), 'Malformed Mach-O command')
        require(command != 0x8000001c, 'Unreviewed runtime search path')
        if command in (0xc, 0x80000018, 0x8000001f, 0x20, 0x80000023):
            require(length >= 24, 'Truncated dynamic image command')
            start = struct.unpack_from('<I', data, offset+8)[0]
            require(24 <= start < length, 'Invalid image install-name offset')
            images.append(data[offset+start:offset+length].split(b'\0')[0].decode('utf-8'))
        offset += length
    require(offset == size and images == expected, 'Retained vendor image boundary changed')
    return images


def draft(output):
    output = Path(output)
    require(output.is_absolute() and str(output.resolve()) == str(output) and not output.exists(),
            'Fresh physical absolute output required')
    pins = {}
    docs = {str(path): metadata(path, digest, pins) for path, digest in PINS.items()}
    retention = docs[str(TOOLS/'retained-packages-v1.json')]
    version = docs[str(TOOLS/'native-versions-v1/report.json')]
    terminal = docs[str(TOOLS/'native-versions-v1/terminal.json')]
    require(version['status'] == terminal['status'] == 'retained-node-and-typescript-versions-verified'
            and version['observed_versions'] == {'node': 'v24.19.0', 'typescript': 'Version 7.0.2'}
            and version['native_processes_started'] == terminal['native_processes_started'] == 2
            and version['integrity_errors'] == [] and version['active'] is None
            and terminal['report_sha256'] == PINS[TOOLS/'native-versions-v1/report.json'], 'Closed version evidence differs')
    packages = retention['packages']
    require([(p['name'], p['version']) for p in packages] == [('typescript', '7.0.2'),
            ('@typescript/typescript-darwin-arm64', '7.0.2'), ('@types/node', '24.19.2'), ('undici-types', '7.24.6')],
            'Exact four-package toolchain required')
    merge(pins, version['pins'])
    for package in packages:
        directory = Path(package['installation_directory'])
        require(directory.is_absolute() and directory == directory.resolve(), 'Nonphysical package root')
        for name, item in package['files'].items():
            part = Path(name)
            require(not part.is_absolute() and '..' not in part.parts, 'Unsafe package file')
            merge(pins, {str(directory/part): item['sha256']})
    for name, item in version['artifacts'].items():
        part = Path(name); require(not part.is_absolute() and '..' not in part.parts, 'Unsafe version artifact')
        merge(pins, {str(TOOLS/'native-versions-v1'/part): item['sha256']})
    manifest, fixtures = docs[str(SOURCES/'source-manifest.json')], docs[str(FIXTURES)]
    require([p['workload'] for p in manifest['profiles']] == list(BENCHES)
            and len(fixtures['fixtures']) == 30 and fixtures['native_cases_run'] == 0, 'Ten sources and thirty fixtures required')
    inputs = []
    for p in manifest['profiles']:
        require(p['source'] == p['workload']+'.ts' and p['id'] == 'typescript-'+p['workload']+'-v1', 'Source identity differs')
        source = SOURCES/p['source']; merge(pins, {str(source): p['source_sha256']})
        inputs.append(dict(id=p['id'], role='application', source_path=str(source), sha256=p['source_sha256'], expected_parse='ok'))
    for f in fixtures['fixtures']:
        require(re.fullmatch('[a-z0-9][a-z0-9-]*', f['id']) and f['expected_parse'] in ('ok', 'error')
                and hashlib.sha256(f['text'].encode()).hexdigest() == f['source_sha256'], 'Fixture text/policy changed')
        inputs.append(dict(id=f['id'], role='fixture', source_path=str(output/'fixture-inputs'/(f['id']+'.ts')),
                           sha256=f['source_sha256'], expected_parse=f['expected_parse']))
    require(len({p['id'] for p in inputs}) == 40, 'Duplicate input IDs')
    for filename, key in [('tsconfig.json', 'compiler_config'), ('package.json', 'package_config')]:
        require(manifest[key] == filename, 'Unexpected source configuration path')
        merge(pins, {str(SOURCES/filename): manifest['packet_files'][filename]})
    for filename,digest in manifest['packet_files'].items():
        require(Path(filename).name == filename, 'Unsafe source packet file')
        merge(pins,{str(SOURCES/filename):digest})
    merge(pins,{str(ORIGINAL_READER):ORIGINAL_READER_SHA})
    package_root = Path(packages[0]['installation_directory']); compiler = Path(packages[1]['installation_directory'])/'lib/tsc'
    types_root = str(Path(packages[2]['installation_directory']).parent)
    require(pins[str(NODE)] == NODE_SHA and str(compiler) in pins, 'Executable identity missing')
    for path in (Path(__file__).resolve(), HERE/'reader-v2.mjs', HERE/'README.md', OBSERVER,
                 Path(kb.kh.__file__), Path(kb.eb.__file__), kb.kh.PYTHON):
        # Interpreter bytes already have a retained pin; do not hash the runtime in draft mode.
        merge(pins, {str(path.resolve()): kb.kh.PYTHON_SHA if path == kb.kh.PYTHON else sha(path)})
    project = output/'compile/project'
    return dict(schema='typescript-compile-and-reader-plan-v1', status='metadata-only-not-executable', pins_verified=False,
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), output=str(output), pins=pins,
        packages=packages, node=str(NODE), node_sha256=NODE_SHA, compiler=str(compiler), types_root=types_root,
        reader=str(HERE/'reader-v2.mjs'), inputs=inputs, fixture_texts={f['id']:f['text'] for f in fixtures['fixtures']},
        compiler_command=[str(compiler), '--project', str(project/'tsconfig.json'), '--typeRoots', types_root,
                          '--pretty', 'false', '--listFiles', '--listEmittedFiles', '--incremental', 'false'],
        reader_plan=dict(schema='typescript-ast-reader-plan-v2', output=str(output/'reader/evidence'), inputs=inputs,
            node=dict(executable=str(NODE), version='v24.19.0'), reader=dict(path=str(HERE/'reader-v2.mjs'), sha256=sha(HERE/'reader-v2.mjs')),
            typescript=dict(version='7.0.2', package_root=str(package_root), executable=str(compiler),
                package_json_sha256=pins[str(package_root/'package.json')], api_entry_sha256=pins[str(package_root/'dist/api/sync/api.js')],
                ast_entry_sha256=pins[str(package_root/'dist/ast/index.js')])),
        owned_commands=2, expected_api_children=1, timeout_seconds=30, cleanup_seconds=5, maximum_rss_bytes=kb.RSS_LIMIT,
        automatic_retries=0, subject_main_invocations=0, benchmark_samples=0, native_transport_verified=False,
        conformance_qualified=False, required_work_qualified=False, runtime_dependency_closure_qualified=False,
        canonical_loc=None, formatted_loc=None, chart_admission=False,
        os_image_boundary='Recorded Mach-O vendor install names; operating-system images not newly file-hashed')


def environment(directory):
    return dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'), TMPDIR=str(directory/'tmp')+'/',
                LC_ALL='C', LANG='C', TZ='UTC', GOMAXPROCS='8', UV_THREADPOOL_SIZE='8')


def validate_compile(plan, directory, stdout):
    project = directory/'project'; emitted = project/'emitted'
    for filename in STAGED_FILES:
        source = project/filename
        require(source.is_file() and not source.is_symlink()
                and sha(source) == plan['pins'][str(SOURCES/filename)],
                'Staged compiler input differs from retained source: '+filename)
    expected = {b+suffix for b in BENCHES for suffix in ('.js', '.js.map')}
    require(emitted.is_dir() and not emitted.is_symlink() and
            {p.name for p in emitted.iterdir()} == expected and all(p.is_file() and not p.is_symlink() for p in emitted.iterdir()),
            'Exact twenty emitted JS/map files required')
    lines = stdout.decode('utf-8', errors='strict').splitlines()
    listed, emitted_lines = [], []
    allowed = set(plan['pins']) | {str(project/(b+'.ts')) for b in BENCHES}
    for line in lines:
        if line.startswith('TSFILE: '): emitted_lines.append(line[8:])
        else:
            require(line in allowed and (line.endswith('.d.ts') or line in {str(project/(b+'.ts')) for b in BENCHES}),
                    'Compiler diagnostic or unretained dependency: '+line)
            listed.append(line)
    require(len(listed) == len(set(listed)) and {str(project/(b+'.ts')) for b in BENCHES} <= set(listed)
            and len(emitted_lines) == len(set(emitted_lines)) == 20
            and set(emitted_lines) == {str(emitted/name) for name in expected}, 'Compiler file inventory differs')
    records = []
    for bench in BENCHES:
        source = project/(bench+'.ts'); js, mapping = emitted/(bench+'.js'), emitted/(bench+'.js.map')
        sm = json.loads(mapping.read_bytes())
        require(js.stat().st_size > 0 and sm['version'] == 3 and sm['file'] == js.name
                and sm['sourceRoot'] == '' and sm['sources'] == ['../'+source.name]
                and sm['sourcesContent'] == [source.read_bytes().decode('utf-8')] and type(sm['mappings']) is str,
                'Emitted source-map provenance differs')
        records.append(dict(id='typescript-'+bench+'-v1', source_sha256=sha(source),
                            javascript=dict(path=str(js), sha256=sha(js)), source_map=dict(path=str(mapping), sha256=sha(mapping))))
    return dict(status='strict-compile-output-recorded-awaiting-independent-review', profiles=records,
                compiler_file_inventory=listed, emitted_file_inventory=emitted_lines, subject_main_invocations=0)


def validate_child(start, terminal, receipt, plan):
    expected = [plan['compiler'], '--api', '--cwd', plan['reader_plan']['output'],
                '--callbacks=readFile,fileExists,directoryExists,getAccessibleEntries,realpath']
    require(type(start['pid']) is int and start['pid'] > 0 and start['pid'] != receipt['pid']
            and start['parent_pid'] == terminal['parent_pid'] == receipt['pid'] and terminal['pid'] == start['pid']
            and start['argv'] == expected and start['executable'] == plan['compiler']
            and start['cwd'] == receipt['cwd'] and start['language_cwd'] == plan['reader_plan']['output'],
            'API child executable/parent/argv identity differs')
    require(terminal['close_requested'] is terminal['close_observed'] is True
            and terminal['child_error'] is terminal['close_error'] is None, 'API child close incomplete')
    code, signal = terminal['exit_code'], terminal['signal_code']
    require((type(code) is int and code == 0 and signal is None) or (code is None and signal == 'SIGTERM'),
            'Unexpected API child exit')
    require(terminal['events'] == [dict(event='exit', code=code, signal=signal), dict(event='close', code=code, signal=signal)],
            'API exit/close event sequence differs')


def validate_ast(evidence, item, source):
    text = source.decode('utf-8', errors='strict'); u16 = text.encode('utf-16-le')
    require(evidence['id'] == item['id'] and evidence['source_path'] == item['source_path']
            and evidence['source_sha256'] == item['sha256'] == hashlib.sha256(source).hexdigest()
            and evidence['source_text'] == text and evidence['source_bytes'] == len(source)
            and evidence['source_utf16_length'] == len(u16)//2 and evidence['offset_units'] == 'UTF-16 code units'
            and evidence['native_transport_verified'] is False and evidence['canonical_loc'] is evidence['formatted_loc'] is None
            and evidence['chart_admission'] is False, 'AST source identity/scope differs')
    diagnostics, nodes = evidence['parse_diagnostics'], evidence['nodes']
    require(type(diagnostics) is list and (len(diagnostics) == 0) == (item['expected_parse'] == 'ok'), 'Parser outcome differs')
    if diagnostics:
        require(nodes == [], 'Rejected input has an owner tree'); return
    require(type(nodes) is list and 0 < len(nodes) <= 100000 and nodes[0]['kind'] == 'SourceFile'
            and nodes[0]['parent'] == -1 and nodes[0]['end_utf16'] == len(u16)//2, 'AST root differs')
    visited = set()
    for index, node in enumerate(nodes):
        require(node['id'] == index and type(node['native_kind']) is int and type(node['kind']) is str,
                'AST node identity differs')
        a, b, c = node['full_start_utf16'], node['start_utf16'], node['end_utf16']
        require(all(type(n) is int for n in (a,b,c)) and 0 <= a <= b <= c <= len(u16)//2,
                'Invalid UTF-16 node span')
        body = u16[b*2:c*2].decode('utf-16-le').encode('utf-8')
        require(hashlib.sha256(body).hexdigest() == node['text_sha256'], 'Node source slice differs')
        require(type(node['children']) is list and len(node['children']) == len(set(node['children'])), 'Duplicate AST edge')
        for child in node['children']:
            require(type(child) is int and index < child < len(nodes) and child not in visited
                    and nodes[child]['parent'] == index and a <= nodes[child]['full_start_utf16']
                    and nodes[child]['end_utf16'] <= c, 'Unowned AST child')
            visited.add(child)
        require(type(node['roles']) is dict, 'Missing AST role inventory')
        for value in node['roles'].values():
            members = value if type(value) is list else [value]
            require(all(type(child) is int and child in node['children'] for child in members), 'Unowned AST role')
    require(visited == set(range(1,len(nodes))), 'Disconnected AST tree')


def validate_reader(plan, directory, receipt, reader_plan_sha):
    output = directory/'evidence'; report = json.loads((output/'report.json').read_bytes())
    require(sha(output/'plan.json') == reader_plan_sha
            and json.loads((output/'plan.json').read_bytes()) == plan['reader_plan'], 'Reader retained plan differs')
    config = dict(compilerOptions=dict(target='ES2022', module='NodeNext', moduleResolution='NodeNext',
        noEmit=True, noLib=True, noResolve=True, types=[], allowJs=False, strict=True),
        files=['/typescript-source-counts/'+i['id']+'.ts' for i in plan['inputs']])
    require(json.loads((output/'parse-config.json').read_bytes()) == config, 'Reader parse-only configuration differs')
    require(report['schema'] == 'typescript-ast-reader-results-v1' and report['status'] == 'read-awaiting-transport-and-owner-review'
            and report['plan_sha256'] == reader_plan_sha and report['source_evaluations'] == report['subject_main_invocations'] == report['emitted_files'] == 0
            and report['native_transport_verified'] is report['chart_admission'] is False
            and report['canonical_loc'] is report['formatted_loc'] is None, 'Reader scope differs')
    start = json.loads((output/'started.json').read_bytes())
    require(start['pid'] == receipt['pid'] and start['ppid'] == os.getpid() and start['node'] == plan['node']
            and start['versions']['node'] == '24.19.0' and start['typescript_version'] == '7.0.2'
            and start['api_entry'] == plan['reader_plan']['typescript']['package_root']+'/dist/api/sync/api.js'
            and start['ast_entry'] == plan['reader_plan']['typescript']['package_root']+'/dist/ast/index.js'
            and start['compiler_executable'] == plan['compiler']
            and start['plan_sha256'] == reader_plan_sha, 'Reader runtime/parent identity differs')
    validate_child(json.loads((output/'compiler-child-start.json').read_bytes()),
                   json.loads((output/'compiler-child-terminal.json').read_bytes()), receipt, plan)
    require([r['id'] for r in report['items']] == [i['id'] for i in plan['inputs']], 'Reader input inventory differs')
    expected = {'plan.json', 'parse-config.json', 'started.json', 'compiler-child-start.json', 'compiler-child-terminal.json', 'report.json'}
    for item, result in zip(plan['inputs'], report['items']):
        source = Path(item['source_path']).read_bytes(); child = output/item['id']
        require((child/'source.ts').read_bytes() == source and sha(child/'ast.json') == result['ast_sha256'], 'Reader artifact bytes differ')
        ast = json.loads((child/'ast.json').read_bytes()); validate_ast(ast,item,source)
        require(result['role'] == item['role'] and result['source_sha256'] == item['sha256']
                and result['nodes'] == len(ast['nodes']) and result['parse_diagnostics'] == len(ast['parse_diagnostics'])
                and result['status'] == ('parsed' if item['expected_parse'] == 'ok' else 'expected-parse-rejection'), 'Reader result differs')
        expected |= {item['id']+'/source.ts', item['id']+'/ast.json'}
    paths = list(output.rglob('*'))
    require(not any(p.is_symlink() for p in paths) and {str(p.relative_to(output)) for p in paths if p.is_file()} == expected,
            'Unexpected reader artifact inventory')
    return dict(status='forty-source-ASTs-recorded-awaiting-independent-review', inputs=40, expected_parse_rejections=2,
                native_transport_verified=False, canonical_loc=None, formatted_loc=None, chart_admission=False)


def verify(pins):
    for path, digest in pins.items(): require(sha(path) == digest, 'Pinned input changed: '+path)


def checked_runtime():
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve() and sha(sys.executable) == kb.kh.PYTHON_SHA
            and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Retained isolated Python required')


def prepare(args):
    physical_path(args.plan); physical_path(args.output)
    require(not args.plan.exists(), 'Fresh plan required')
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); kb.kh.verify_lock(lock); checked_runtime()
        plan = draft(args.output.resolve())
        require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan must remain outside native output')
        verify(plan['pins']); package_inventory(plan['packages'])
        for key in ('node', 'tsc'): macho_vendor_images(plan['node' if key == 'node' else 'compiler'], VENDOR_IMAGES[key])
        plan.update(status='prepared-awaiting-independent-review', pins_verified=True)
        args.plan.parent.mkdir(parents=True,exist_ok=True); new_json(args.plan,plan); kb.kh.verify_lock(lock)
    print(json.dumps(dict(plan=str(args.plan.resolve()), sha256=sha(args.plan), native_executions=0)))


def validate_receipt(receipt, command, env, directory):
    require(receipt['status'] == 'native-passed' and receipt['native_process_started'] is True
            and receipt['command'] == command and receipt['environment'] == env and receipt['cwd'] == str(directory)
            and receipt['kind'] == 'typescript-'+directory.name
            and type(receipt['pid']) is int and type(receipt['pgid']) is int and receipt['pid'] > 0
            and receipt['pid'] == receipt['pgid'] and receipt['identity']['ppid'] == os.getpid()
            and receipt['identity']['pid'] == receipt['pid'] and receipt['identity']['pgid'] == receipt['pgid']
            and receipt['direct_child_reaped'] is True and type(receipt['exit_status']) is int and receipt['exit_status'] == 0
            and receipt['remaining_process_group'] == [] and receipt['inherited_common_mutex'] is True
            and receipt['common_mutex_inode'] == 79859134 and receipt['stop_signals'] == receipt['cleanup_errors'] == [],
            'Owned native receipt is not a clean closed command')
    before, after = receipt['identity'], receipt['leader_identity_before_reap']
    require(all(type(before[k]) is int and before[k] == after[k] for k in
                ('pid','ppid','pgid','birth_seconds','birth_microseconds')) and after['status'] == 5
            and receipt['stdin_bytes'] == 0 and receipt['stdin_sha256'] == hashlib.sha256(b'').hexdigest()
            and not any(receipt.get(k) for k in ('error','error_type','timed_out','remaining_after_cleanup','artifact_errors')),
            'Native birth/input/error observations differ')
    require(receipt['process_timeout_seconds'] == 30 and receipt['cleanup_timeout_seconds'] == 5
            and receipt['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and receipt['kernel_monitor_samples'] > 0
            and 0 <= receipt['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT
            and receipt['native_file_limit_bytes'] == kb.FILE_LIMIT
            and receipt['stdout_capture_limit_bytes'] == kb.FILE_LIMIT+kb.PIPE_CHUNK, 'Native resource limits differ')
    for name in ('start.json','active.json'):
        value = json.loads((directory/name).read_bytes())
        require(all(value[k] == receipt[k] for k in ('kind','command','environment','cwd','started_at')), 'Start/final linkage differs')
        if name == 'active.json': require(value['identity'] == receipt['identity'], 'Native birth identity changed')
    for name in ('stdout','stderr'):
        path = directory/(name+'.bin')
        require(path.stat().st_size == receipt[name+'_bytes'] and sha(path) == receipt[name+'_sha256'], 'Native stream receipt differs')
    require((directory/'stderr.bin').read_bytes() == b'', 'Native diagnostics are not empty')


def inventory(output, excluded=()):
    paths = list(output.rglob('*'))
    require(not any(p.is_symlink() for p in paths) and all(p.is_file() or p.is_dir() for p in paths),
            'Native artifact is a symlink or nonregular entry')
    files = [p for p in paths if p.is_file() and str(p.relative_to(output)) not in excluded]
    require(len(files) <= 1000 and sum(p.stat().st_size for p in files) <= 128*1024*1024, 'Native artifact bound exceeded')
    return {str(p.relative_to(output)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}


def process_closure(report, output):
    errors = []
    try:
        registered = report['registered_commands']
        require(len(registered) == report['owned_commands_started'] <= 2
                and [r['stage'] for r in registered] == ['compile','reader'][:len(registered)]
                and len({r['pid'] for r in registered}) == len(registered), 'Registered native schedule differs')
        require({str(p.parent.relative_to(output)) for p in output.rglob('process.json')} == {r['stage'] for r in registered},
                'Native process receipt inventory differs')
        for command in registered:
            directory = output/command['stage']; receipt = json.loads((directory/'process.json').read_bytes())
            require(type(command['pid']) is int and command['pid'] > 0 and command['pid'] == command['pgid']
                    and receipt['pid'] == receipt['pgid'] == command['pid'] and receipt['native_process_started'] is True
                    and receipt['direct_child_reaped'] is True and receipt.get('remaining_process_group',[]) == []
                    and receipt.get('remaining_after_cleanup',[]) == [] and receipt['cleanup_errors'] == [],
                    'Native process ownership/closure incomplete')
            if report['status'] == 'compile-and-AST-captures-recorded-awaiting-independent-review':
                require(receipt['status'] == 'native-passed', 'Successful stage has a failed native receipt')
        if report['status'] == 'compile-and-AST-captures-recorded-awaiting-independent-review':
            require(len(registered) == 2 and set(report['stages']) == {'compile','reader'}, 'Successful native stage incomplete')
    except BaseException as error: errors.append(str(error) or type(error).__name__)
    return errors


def check_snapshot(report, output, artifacts):
    for stage, snapshot in report['validated_stage_artifacts'].items():
        prefix = stage+'/'
        require({name[len(prefix):]: value for name, value in artifacts.items() if name.startswith(prefix)} == snapshot,
                'Validated stage differs from final artifact inventory: '+stage)
    for path, digest in report['generated_input_pins'].items():
        relative = str(Path(path).relative_to(output))
        require(relative in artifacts and artifacts[relative]['sha256'] == digest,
                'Generated input differs from final artifact inventory: '+relative)


def finish(report, plan, output, pins, lock):
    # Caller blocks interruption while preserving final failure evidence. The
    # final inventory must retain previously validated bytes, never adopt them.
    errors = []; mutex_valid = False
    child = output/'reader/evidence/compiler-child-start.json'
    if child.is_file():
        try: report['observed_api_children'] = [json.loads(child.read_bytes())]
        except BaseException as error: errors.append(dict(path=str(child),error=str(error)))
    report['api_child_start_unconfirmed'] = any(c['stage']=='reader' for c in report['registered_commands']) and not child.is_file()
    report['process_receipt_errors'] = process_closure(report,output)
    if report['process_receipt_errors']: errors.append(dict(path='<process-closure>',error='Native closure failed'))
    try:
        require(not (output/'terminal.json').exists(), 'Terminal already exists')
        report['artifacts'] = inventory(output,('report.json',))
        check_snapshot(report,output,report['artifacts'])
    except BaseException as error: errors.append(dict(path='<native-artifact-inventory>',error=str(error)))
    report['integrity_errors'] = errors; report['active'] = None
    if errors: report['status'] = 'failed-integrity'
    report['finished_at'] = datetime.now(timezone.utc).isoformat(); kb.save(output/'report.json',report)
    try:
        available = inventory(output)
        require({name:value for name,value in available.items() if name != 'report.json'} == report['artifacts'],
                'Native artifact changed after final validation')
        check_snapshot(report,output,available)
        require(available['report.json']['sha256'] == sha(output/'report.json'), 'Final report inventory differs')
    except BaseException as error:
        errors.append(dict(path='<terminal-artifact-inventory>',error=str(error))); available = {}
    # Recheck all prerequisites and generated inputs after the terminal inventory
    # has been constructed, including the immutable source and reviewed plan.
    for path,digest in {**pins,**report['generated_input_pins']}.items():
        try: require(sha(path)==digest,'Pinned input changed after final inventory')
        except BaseException as error: errors.append(dict(path=path,error=str(error)))
    try: package_inventory(plan['packages'])
    except BaseException as error: errors.append(dict(path='<package-inventory>',error=str(error)))
    try: kb.kh.verify_lock(lock); mutex_valid = True
    except BaseException as error: errors.append(dict(path='<common-mutex>',error=str(error)))
    if errors:
        report['status']='failed-integrity'; kb.save(output/'report.json',report)
        # An incomplete closure remains inspectable but is never success-shaped.
        available = {'report.json':dict(bytes=(output/'report.json').stat().st_size,sha256=sha(output/'report.json'))}
    new_json(output/'terminal.json',dict(schema='typescript-compile-and-reader-terminal-v1',status=report['status'],
        report_sha256=sha(output/'report.json'),owned_commands_started=report['owned_commands_started'],
        observed_api_children=report['observed_api_children'],available_evidence=available,integrity_errors=errors,
        process_receipt_errors=report['process_receipt_errors'],
        common_mutex_held=mutex_valid,common_mutex_inode=79859134,native_transport_verified=False,
        benchmark_samples=0,canonical_loc=None,formatted_loc=None,chart_admission=False))


def run(args):
    physical_path(args.plan)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); kb.kh.verify_lock(lock); checked_runtime()
        require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
        plan = json.loads(args.plan.read_bytes()); expected = draft(Path(plan['output']))
        expected.update(status='prepared-awaiting-independent-review', pins_verified=True)
        require(plan == expected, 'Plan differs from exact source/toolchain/policy')
        pins = dict(plan['pins']); merge(pins,{str(args.plan.resolve()):args.plan_sha256}); verify(pins); package_inventory(plan['packages'])
        output = Path(plan['output']); output.mkdir(parents=True,exist_ok=False)
        report = dict(schema='typescript-compile-and-reader-results-v1',status='running',pins=pins,
            plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,started_at=datetime.now(timezone.utc).isoformat(),
            owned_commands_started=0,registered_commands=[],active=None,stages={},observed_api_children=[],
            validated_stage_artifacts={},generated_input_pins={},
            subject_main_invocations=0,benchmark_samples=0,native_transport_verified=False,conformance_qualified=False,
            required_work_qualified=False,runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,chart_admission=False)
        kb.save(output/'report.json',report)
        try:
            for stage in ('compile','reader'):
                verify(pins); package_inventory(plan['packages']); kb.kh.verify_lock(lock)
                directory = output/stage; directory.mkdir()
                for sub in ('home','tmp'): (directory/sub).mkdir()
                env = environment(directory)
                if stage == 'compile':
                    project = directory/'project'; project.mkdir()
                    for filename in STAGED_FILES:
                        source = SOURCES/filename; raw = source.read_bytes()
                        require(hashlib.sha256(raw).hexdigest() == pins[str(source)], 'Source changed before staging')
                        (project/filename).write_bytes(raw)
                    command = plan['compiler_command']
                else:
                    fixtures = output/'fixture-inputs'; fixtures.mkdir()
                    for identity, text in plan['fixture_texts'].items(): (fixtures/(identity+'.ts')).write_text(text)
                    reader_plan = output/'reader-plan.json'; new_json(reader_plan,plan['reader_plan'])
                    command = [plan['node'], plan['reader'], str(reader_plan), sha(reader_plan)]
                    report['generated_input_pins'][str(reader_plan)] = command[-1]
                    report['generated_input_pins'].update({i['source_path']:i['sha256'] for i in plan['inputs'] if i['role']=='fixture'})
                def launched(pid):
                    report['owned_commands_started'] += 1
                    report['registered_commands'].append(dict(stage=stage,pid=pid,pgid=pid))
                    report['active'] = dict(stage=stage,pid=pid); kb.save(output/'report.json',report)
                kb.observe(command,env,directory,b'',lock,launched,kind='typescript-'+stage)
                snapshot = inventory(directory)
                receipt = json.loads((directory/'process.json').read_bytes()); validate_receipt(receipt,command,env,directory)
                if stage == 'compile': result = validate_compile(plan,directory,(directory/'stdout.bin').read_bytes())
                else:
                    require((directory/'stdout.bin').read_bytes() == b'', 'Reader stdout must be empty')
                    result = validate_reader(plan,directory,receipt,command[-1])
                report['stages'][stage] = result; report['active'] = None
                require(inventory(directory) == snapshot, 'Stage artifact changed during validation')
                report['validated_stage_artifacts'][stage] = snapshot
                kb.save(output/'report.json',report)
            report['status'] = 'compile-and-AST-captures-recorded-awaiting-independent-review'
        except BaseException as error:
            report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        finally:
            with kb.atomic(): finish(report,plan,output,pins,lock)
        print(json.dumps(dict(status=report['status'],report_sha256=sha(output/'report.json'))))
        return 0 if report['status']=='compile-and-AST-captures-recorded-awaiting-independent-review' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__); modes=parser.add_subparsers(dest='mode',required=True)
    prep=modes.add_parser('prepare'); prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    execute=modes.add_parser('run'); execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    def interrupted(signum,frame): raise KeyboardInterrupt('TypeScript native stage interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    return prepare(args) if args.mode=='prepare' else run(args)


if __name__ == '__main__': raise SystemExit(main())
