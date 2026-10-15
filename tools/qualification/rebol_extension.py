"""Bounded build, generated-header layout and nine-command Rebol load capture.

The failed SDK producer is retained verbatim. Its separate output-reuse review,
an independently approved source packet and a concrete toolchain intake are
mandatory. This stage neither executes a benchmark nor admits the full fixtures.
"""
import argparse
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/extension-api-v2'
SDK = ROOT/'experiments/rebol/sdk-generation-v1'
SDK_COPY = SDK/'work-v1/source'
SDK_RUN = SDK/'run-v1'
OLD = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
RUNTIME = OLD/'rebol-comparison/20261013/.build/runtime-v1/runtime/rebol3'
RUNTIME_SHA = '27e255625d4d9928f5d726d3f2546fa64ff82a09a2b971cbc3a236a0bbed08a2'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
SUPPORT = ROOT/'archive/languages/rebol/20261013/drafts/private-v1/support'
FIXTURES = ROOT/'experiments/rebol/primitive-fixtures-v1'
REUSE = SDK/'generated-output-reuse-review-v1.json'
REUSE_SHA = '2994d3a29ca6d456d681549879563e9b9d19be5cf36822e87e7b7092938e17da'
CLOSURE = SDK/'failed-generation-closure-review-v1.json'
CLOSURE_SHA = '810365f4915ca011379bdb09ad8980087b180479b83e1d3156f88a482acc751b'
INSPECTOR = ROOT/'tools/qualification/julia_native_inspection.py'
INSPECTOR_SHA = '877bda82e014e16a5380cc46b283ba90dca71f02c4a285994df5c54ab883489a'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LEASE_PATHS = tuple(OLD/'continuation/owned-jobs'/name/'owner.lock' for name in (
    'rebol-builder-spec-only-v1', 'rebol-builder-intake-v1', 'rebol-saved-runtime-source-intake-v1')) + (
    ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-sdk-generation-v1/owner.lock',)
COMMANDS = ['gmp-add', 'gmp-subtract', 'gmp-multiply', 'gmp-floor-divide', 'gmp-compare',
            'pcre-find', 'read-stdin-chunk', 'write-stdout', 'format-fixed']
IDS = ['build-extension', 'build-layout-probe', 'layout-and-exports', 'load-nine-commands']
FILE_LIMIT = 64*1024**2
KIND = 'rebol-extension-build-layout-load'
SUCCESS = 'four-build-layout-load-captures-retained-awaiting-independent-review'
GATES = ('extension_abi_qualified', 'full_primitive_fixtures_qualified', 'runtime_source_equivalence_proven',
         'source_work_qualified', 'canonical_source_count_qualified', 'full_timing_qualified', 'chart_admission')
SOURCE_FILES = (Path(__file__).resolve(), Path(__file__).with_name('test_rebol_extension.py'),
                PACKET/'clbg_primitives.c', PACKET/'layout-probe.c', PACKET/'load-smoke.reb', PACKET/'BUILD.md')
LAYOUT_LINE = 'layout\t8\t8\t16\t4\t256\t8\t116\t16\t416\t128\t136\t216'
LOAD_OUTPUT = b'\x00\x80\xffok extension-load-v2\n'
HISTORICAL_FIXTURE_PINS = {
    SUPPORT/'clbg_primitives.reb': '2671ebf31535aee49afbf9f27de1122556dda5f8962b1fc92acf9c27bcffed34',
    FIXTURES/'common.reb': 'e0633162f20f8a86cc56377deca2d6f123aa948e8f36867e14c363783bf8da12',
    FIXTURES/'spec.json': '3962c9c0782f4b8fae81555821e5ad5573ea4aa36b55a2d3396e570fa5bb2a79',
}


def require(value, message):
    if not value: raise AssertionError(message)


def encoded(value): return (json.dumps(value, indent=2)+'\n').encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


@contextmanager
def regular(path):
    path = Path(path); before = path.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular file required: '+str(path))
    fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(fd)
        require((held.st_dev,held.st_ino) == (before.st_dev,before.st_ino), 'Input replaced before open')
        yield stream
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and (held.st_dev,held.st_ino) == (after.st_dev,after.st_ino),
                'Input replaced during read')


def read_bytes(path):
    with regular(path) as stream: return stream.read()


def sha(path):
    with regular(path) as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def physical(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'Physical absolute path required: '+str(path))
    return path


def pin(pins, resolutions, name, expected=None):
    path = Path(name); require(path.is_absolute() and '..' not in path.parts, 'Absolute input required')
    target = path.resolve(strict=True); actual = sha(target)
    require(expected is None or actual == expected, 'Input digest differs: '+str(path))
    require(str(path) not in pins or pins[str(path)] == actual, 'Conflicting input pin')
    require(str(path) not in resolutions or resolutions[str(path)] == str(target), 'Input alias changed')
    pins[str(path)] = actual; resolutions[str(path)] = str(target)
    return target


def document(ref, pins, resolutions):
    require(set(ref) >= {'path','sha256'}, 'Exact evidence reference required')
    name = Path(ref['path']); name = ROOT/name if not name.is_absolute() else name
    target = pin(pins,resolutions,name,ref['sha256']); raw = read_bytes(target)
    require(digest(raw) == ref['sha256'], 'Evidence changed during decode')
    return json.loads(raw)


def merge(target, values):
    for name,value in values.items():
        require(name not in target or target[name] == value, 'Conflicting closure member: '+name)
        target[name] = value


def inventory(root, exclude=(), tolerant=False):
    """Never open FIFOs/sockets. Failed stages retain every readable regular file."""
    physical(root); found, errors = {}, []
    for path in sorted(root.rglob('*')):
        name = str(path.relative_to(root))
        if name in exclude: continue
        try:
            mode = path.lstat().st_mode
            require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'Nonregular artifact: '+name)
            if stat.S_ISREG(mode):
                require(path.stat().st_size <= FILE_LIMIT+65536, 'Artifact exceeds stage bound')
                found[name] = dict(bytes=path.stat().st_size,sha256=sha(path))
        except BaseException as error:
            if not tolerant: raise
            errors.append(dict(path=name,error=str(error) or type(error).__name__))
    return found, errors


def verify(pins, resolutions, absent=(), closures=()):
    require(set(pins) == set(resolutions), 'Incomplete named-input closure')
    for name,expected in pins.items():
        require(str(Path(name).resolve(strict=True)) == resolutions[name] and sha(resolutions[name]) == expected,
                'Pinned input or named resolution changed: '+name)
    for name in absent: require(not os.path.lexists(name), 'Absent dependency appeared: '+name)
    for item in closures:
        actual,_ = inventory(Path(item['directory']))
        require(actual == item['artifacts'], 'Prerequisite artifact membership changed')


def load_support(pins, resolutions):
    raw = read_bytes(pin(pins,resolutions,INSPECTOR,INSPECTOR_SHA))
    module = types.ModuleType('rebol_extension_static_inspector'); module.__file__ = str(INSPECTOR)
    exec(compile(raw,str(INSPECTOR),'exec'),module.__dict__)
    kb = module.kb
    require((kb.TIMEOUT,kb.CLEANUP_TIMEOUT,kb.RSS_LIMIT,kb.FILE_LIMIT) == (30,5,2*1024**3,FILE_LIMIT),
            'Frozen observer policy differs')
    for path,expected in ((module.OBSERVER,module.OBSERVER_SHA), (Path(kb.kh.__file__),kb.HELPER_CONTROLLER_SHA),
                          (Path(kb.eb.__file__),kb.REFERENCE_CONTROLLER_SHA), (PYTHON.resolve(),PYTHON_SHA)):
        pin(pins,resolutions,path,expected)
    return module


def check_leases(leases):
    for path,stream,identity in leases:
        held,named = os.fstat(stream.fileno()),Path(path).lstat()
        require(stat.S_ISREG(named.st_mode) and (held.st_dev,held.st_ino) == (named.st_dev,named.st_ino) == identity,
                'Held named lease changed: '+str(path))


@contextmanager
def held_inputs(intake_ref):
    with ExitStack() as stack:
        common = stack.enter_context(regular(LOCK)); fcntl.flock(common,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(os.fstat(common.fileno()).st_ino == 79859134, 'Wrong common mutex')
        leases = [(LOCK,common,(os.fstat(common.fileno()).st_dev,79859134))]
        pins,resolutions = {},{}
        intake = document(intake_ref,pins,resolutions)
        require(set(intake['prior_leases']) == {str(p) for p in LEASE_PATHS}, 'Exact four closed-stage leases required')
        for path in LEASE_PATHS:
            stream = stack.enter_context(regular(path)); fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            expected = intake['prior_leases'][str(path)]
            require(set(expected) == {'device','inode'} and all(type(v) is int for v in expected.values()), 'Lease identity required')
            leases.append((path,stream,(expected['device'],expected['inode'])))
        check_leases(leases)
        try: yield common,leases,intake,pins,resolutions
        finally: check_leases(leases)


def retained_sdk(pins, resolutions):
    reuse = document(dict(path=str(REUSE),sha256=REUSE_SHA),pins,resolutions)
    closure = document(dict(path=str(CLOSURE),sha256=CLOSURE_SHA),pins,resolutions)
    require(reuse['schema'] == 'rebol-sdk-generated-output-reuse-review-v1'
        and reuse['status'] == 'retained-generated-artifacts-available-for-header-review-failed-stage-preserved'
        and reuse['closed_failed_stage']['sha256'] == CLOSURE_SHA
        and closure['status'] == 'stopped-unqualified-owned-closure-and-partial-artifacts-verified'
        and closure['exit_status'] == 1 and closure['native_commands_started'] == 1,
        'Exact failed generation and separate reuse disposition required')
    generated = reuse['generation_evidence']['generated_files']
    require(len(generated) == 29 and generated == closure['generated_files']
        and reuse['generation_evidence']['unexpected_vendor_writes'] == []
        and reuse['generation_evidence']['original_898_source_bytes_preserved'] is True,
        'Complete 29-output preserved generation required')
    report = document(closure['report'],pins,resolutions)
    terminal = document(closure['terminal'],pins,resolutions)
    document(closure['plan'],pins,resolutions); document(closure['durable_terminal'],pins,resolutions)
    require(report['status'] == terminal['status'] == 'stopped-unqualified'
        and terminal['report_sha256'] == closure['report']['sha256']
        and terminal['integrity_errors'] == terminal['artifact_errors'] == []
        and terminal['common_mutex_held'] is True, 'Original failed terminal changed')
    # Initial generated-file pins are historical pre-generation identities.
    # Only the exact 29 reviewed output names use the recorded post-generation bytes.
    for name,expected in terminal['prerequisites'].items():
        if name not in generated: pin(pins,resolutions,name,expected)
    for collection in (terminal['available_evidence_pins'],generated):
        for name,expected in collection.items(): pin(pins,resolutions,name,expected)
    closures = []
    for directory in (SDK_COPY,SDK_RUN):
        expected = {str(Path(n).relative_to(directory)):dict(bytes=Path(n).stat().st_size,sha256=h)
            for n,h in terminal['available_evidence_pins'].items() if Path(n).is_relative_to(directory)}
        if directory == SDK_RUN:
            expected['terminal.json'] = dict(bytes=(SDK_RUN/'terminal.json').stat().st_size,
                                             sha256=closure['terminal']['sha256'])
        require(inventory(directory)[0] == expected, 'Retained SDK inventory differs')
        closures.append(dict(directory=str(directory),artifacts=expected))
    return generated, closures


def validate_intake(intake, review, source_ref, pins, resolutions):
    require(intake['schema'] == 'rebol-extension-concrete-toolchain-intake-v1'
        and intake['status'] == 'reviewed-concrete-compiler-sdk-and-library-inputs'
        and intake['source_review'] == source_ref and intake['target'] == 'arm64-apple-macos11.0'
        and intake['actual_loaded_images_observed'] is False, 'Reviewed concrete dependency intake required')
    require(review['schema'] == 'rebol-extension-build-source-review-v1'
        and review['status'] == 'source-reviewed-awaiting-native-build-layout-load'
        and review['commands'] == COMMANDS and review['sdk_output_reuse'] == dict(path=str(REUSE),sha256=REUSE_SHA)
        and all(review[k] is False for k in GATES), 'Source review cannot prequalify native observations')
    require(set(review['files']) == {str(p.relative_to(ROOT)) for p in SOURCE_FILES}, 'Exact reviewed source packet required')
    for name,expected in review['files'].items(): pin(pins,resolutions,ROOT/name,expected)
    require(set(intake['tools']) == {'clang','linker','runtime'}, 'Exact compiler/linker/runtime required')
    require(intake['tools']['runtime'] == dict(path=str(RUNTIME),sha256=RUNTIME_SHA), 'Retained interpreter identity differs')
    for ref in intake['tools'].values():
        path = pin(pins,resolutions,ref['path'],ref['sha256']); physical(Path(ref['path']))
        require(os.access(path,os.X_OK), 'Tool is not executable')
    require(set(intake['include_roots']) == {'rebol','clang_resource','macos_sdk','gmp','pcre2'}, 'Incomplete include roots')
    roots = {k:physical(Path(v)) for k,v in intake['include_roots'].items()}
    require(roots['rebol'] == SDK_COPY/'src/include', 'Generated SDK include path changed')
    for name,expected in intake['input_pins'].items(): pin(pins,resolutions,name,expected)
    for name in ('gmp','pcre2'):
        lib = intake['libraries'][name]
        require(set(lib) == {'path','sha256','runtime_version','source_provenance'}, 'Library intake incomplete')
        physical(Path(lib['path'])); pin(pins,resolutions,lib['path'],lib['sha256'])
        provenance = document(lib['source_provenance'],pins,resolutions)
        require(provenance['status'] == 'reviewed-exact-library-source-and-installed-image'
            and provenance['installed_image'] == {k:lib[k] for k in ('path','sha256')}, 'Library source/image join missing')
    require(set(intake['libraries']) == {'gmp','pcre2'}, 'Only general GMP and PCRE2-8 libraries allowed')
    required_headers = [roots['rebol']/n for n in ('reb-host.h','reb-lib.h','reb-ext.h','host-lib.h','gen-config.h')]
    required_headers += [roots['gmp']/'gmp.h', roots['pcre2']/'pcre2.h']
    require(all(str(p) in pins for p in required_headers), 'Header intake is incomplete')
    for name in ('compiler_version','sdk_identity','linker_version'):
        require(isinstance(intake[name],dict) and {'path','sha256'} <= set(intake[name]), 'Saved tool/SDK identity required')
        document(intake[name],pins,resolutions)
    require(type(intake['unavailable_inputs']) is list, 'Absent lookup inputs must be explicit')
    return roots


def environment(output, *, load=False):
    result = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',
        HOME=str(output/'home'),TMPDIR=str(output/'tmp'),REBOL_HOME=str(output/'home'),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
    if load:
        result.update(MECH_CLBG_REBOL_PRIMITIVES=str(output/'build/clbg_primitives.dylib'),
            MECH_REBOL_FIXTURE_SUPPORT=str(SUPPORT),MECH_REBOL_FIXTURE_COMMON=str(FIXTURES/'common.reb'))
    return result


def schedule(intake, output):
    roots = intake['include_roots']; tools = intake['tools']; build = output/'build'
    flags = [tools['clang']['path'],'--no-default-config','-target',intake['target'],'-std=c11','-O2','-DTO_MACOS','-DREB_EXT',
        '-D_DARWIN_C_SOURCE','-DREBOL_OPTIONS_FILE="gen-config.h"','-fno-modules','-nostdinc',
        '-isysroot',roots['macos_sdk'],'-resource-dir',str(Path(roots['clang_resource']).parent),
        '-fuse-ld='+tools['linker']['path'],'-isystem',roots['clang_resource'],
        '-isystem',str(Path(roots['macos_sdk'])/'usr/include'),'-I',roots['rebol'],
        '-I',roots['gmp'],'-I',roots['pcre2'],'-MD','-MT','dependencies']
    libs = [intake['libraries'][k]['path'] for k in ('gmp','pcre2')]
    commands = [flags+['-MF',str(build/'extension.d'),'-dynamiclib',str(PACKET/'clbg_primitives.c'),*libs,
        '-Wl,-install_name,@rpath/clbg_primitives.dylib','-Wl,-map,'+str(build/'extension.map'),'-o',str(build/'clbg_primitives.dylib')],
        flags+['-MF',str(build/'layout.d'),str(PACKET/'layout-probe.c'),*libs,'-Wl,-map,'+str(build/'layout.map'),
               '-o',str(build/'layout-probe')],
        [str(build/'layout-probe'),str(build/'clbg_primitives.dylib')],
        [tools['runtime']['path'],'--quiet','--no-color',str(PACKET/'load-smoke.reb')]]
    return [dict(id=name,directory=f'{i:02d}-'+name,command=command,timeout_seconds=300 if i<2 else 30,
        environment=environment(output,load=i==3),stdin_hex='0080ff' if i==3 else '')
        for i,(name,command) in enumerate(zip(IDS,commands))]


def build_plan(output, intake_ref, source_ref, intake, pins, resolutions, inspector):
    physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not os.path.lexists(output), 'Fresh packet output required')
    review = document(source_ref,pins,resolutions)
    validate_intake(intake,review,source_ref,pins,resolutions)
    generated,closures = retained_sdk(pins,resolutions)
    for path,expected in HISTORICAL_FIXTURE_PINS.items():
        require(intake['input_pins'].get(str(path))==expected, 'Original loader/fixture history changed')
        pin(pins,resolutions,path,expected)
    toolpins = {}
    toolclosure = inspector.tool_closure([Path(intake['tools'][k]['path']) for k in ('clang','linker','runtime')]
        +[Path(intake['libraries'][k]['path']) for k in ('gmp','pcre2')],toolpins)
    for name,expected in toolpins.items(): pin(pins,resolutions,name,expected)
    require(toolclosure == intake['declared_image_closure'], 'Reviewed static tool/library closure differs')
    absent = sorted(set(intake['unavailable_inputs'])|set(toolclosure['unavailable_candidates']))
    return dict(schema='rebol-extension-build-layout-load-plan-v1',status='prepared-awaiting-independent-review',
        repository=str(ROOT),controller=str(Path(__file__).resolve()),controller_sha256=sha(__file__),
        output=str(output),toolchain_intake=intake_ref,source_review=source_ref,schedule=schedule(intake,output),
        pins=dict(pins),input_resolutions=dict(resolutions),unavailable_inputs=absent,
        prerequisite_artifact_closures=closures,generated_outputs=generated,declared_image_closure=toolclosure,
        general_commands=COMMANDS,native_processes=4,compilations=2,benchmark_samples=0,automatic_retry=False,
        failed_sdk_producer_preserved=True,full_fixture_suite_executed=False,
        process_group_rss_limit_bytes=2*1024**3,stream_limit_bytes=FILE_LIMIT,cleanup_timeout_seconds=5,
        common_mutex_inode=79859134,**{k:False for k in GATES})


def dependencies(raw):
    """Clang -MD -MT dependencies syntax: one rule, escaped paths, no expansion."""
    text = raw.decode('utf-8').replace('\\\n','')
    require(text.startswith('dependencies:') and '$' not in text, 'Unsupported dependency rule')
    words,word,escaped = [],'',False
    for char in text[len('dependencies:'):]:
        if escaped: word += char; escaped=False
        elif char == '\\': escaped=True
        elif char.isspace():
            if word: words.append(word); word=''
        else: word += char
    require(not escaped, 'Unterminated dependency escape')
    if word: words.append(word)
    require(words and all(Path(w).is_absolute() for w in words), 'Absolute dependency paths required')
    return set(words)


def validate_compile_inputs(output, stem, source, pins, resolutions):
    paths = dependencies(read_bytes(output/'build'/(stem+'.d')))
    require(str(source) in paths and all(name in pins for name in paths), 'Compiler consumed an unreviewed header/source')
    verify({n:pins[n] for n in paths},{n:resolutions[n] for n in paths})
    return sorted(paths)


def built_image_closure(images, intake, inspector, pins):
    local={};closure=inspector.tool_closure(images,local)
    built={str(p) for p in images}
    allowed=set(intake['declared_image_closure']['images'])|built
    require(set(closure['images'])<=allowed,'Built image acquired an unreviewed dependency')
    for name,expected in local.items():
        if name not in built:
            require(pins.get(name)==expected or pins.get(str(Path(name).resolve()))==expected,
                    'Built loader dependency is not in the intake')
    return closure


def build_inventory(output, index):
    expected={'extension.d','extension.map','clbg_primitives.dylib'}
    if index>=1: expected|={'layout.d','layout.map','layout-probe'}
    snapshot,_=inventory(output/'build')
    require(set(snapshot)==expected and all(v['bytes']>0 for v in snapshot.values()),
            'Missing or unexpected compiler/linker outputs')
    return {str(Path('build')/n):v for n,v in snapshot.items()}


def validate_layout(raw, output, intake, inspector, pins, resolutions):
    lines = raw.decode('utf-8').splitlines()
    require(lines[3:6] == [LAYOUT_LINE,'gmp\t'+intake['libraries']['gmp']['runtime_version'],
        'pcre2\t'+intake['libraries']['pcre2']['runtime_version']], 'Actual ABI/library version differs')
    dylib = output/'build/clbg_primitives.dylib'; probe = output/'build/layout-probe'
    for line,symbol in zip(lines[:3],('RX_Init','RX_Quit','RX_Call')):
        parts = line.split('\t'); require(len(parts)==3 and parts[:2] == ['export',symbol]
            and Path(parts[2]).resolve() == dylib, 'Entry symbol is not owned by the built extension')
    closure=built_image_closure([probe,dylib],intake,inspector,pins)
    allowed=set(closure['images'])
    observed = []
    for line in lines[6:]:
        parts=line.split('\t'); require(len(parts)==2 and parts[0]=='image', 'Unexpected layout probe output')
        path=Path(parts[1]); require(path.is_absolute(), 'Relative loaded image')
        if not inspector.os_image(str(path)):
            require(not inspector.os_image(str(path.resolve())) and str(path.resolve()) in allowed,
                    'Probe loaded an unreviewed non-OS image')
        observed.append(str(path))
    require(len(observed)==len(set(observed)) and {str(probe),str(dylib)} <= {str(Path(p).resolve()) for p in observed},
            'Probe image observation incomplete')
    return dict(declared_image_closure=closure,layout_probe_loaded_images=observed,
                interpreter_loaded_images_observed=False,os_images_file_hashed=False)


def checked_capture(slot, directory, parent, kb):
    snapshot,_ = inventory(directory)
    require(set(snapshot) == {'start.json','active.json','process.json','stdout.bin','stderr.bin'}, 'Unexpected native capture files')
    start,active,final = [json.loads(read_bytes(directory/(n+'.json'))) for n in ('start','active','process')]
    for value in (start,active,final):
        require(value['command']==slot['command'] and value['environment']==slot['environment']
            and value['cwd']==str(directory) and value['kind']==KIND and value['started_at']==start['started_at']
            and value['process_timeout_seconds']==slot['timeout_seconds'] and value['cleanup_timeout_seconds']==5
            and value['maximum_process_group_rss_bytes']==2*1024**3 and value['native_file_limit_bytes']==FILE_LIMIT
            and value['stdout_capture_limit_bytes']==FILE_LIMIT+kb.PIPE_CHUNK
            and value['stdout_transport']=='OS pipe, retained as received' and value['stderr_transport']=='exclusive artifact'
            and value['stdin_bytes']==len(bytes.fromhex(slot['stdin_hex']))
            and value['stdin_sha256']==digest(bytes.fromhex(slot['stdin_hex']))
            and value['inherited_common_mutex'] is True and value['common_mutex_inode']==79859134
            and value['source_work_qualified'] is value['chart_admission'] is False, 'Native capture contract differs')
    identity,leader,pid=final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status']=='starting' and start['native_process_started'] is False
        and active['status']=='running' and active['native_process_started'] is final['native_process_started'] is True
        and active['identity']==identity and identity['ppid']==parent
        and all(type(identity[k]) is int and identity[k]==leader[k] for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and active['pid']==active['pgid']==pid==final['pgid']==identity['pid']==identity['pgid']
        and leader['status']==5 and final['direct_child_reaped'] is True
        and final['remaining_process_group']==final.get('remaining_after_cleanup',[])==[]
        and final['stop_signals']==final['cleanup_errors']==[] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and not final.get('error') and not final.get('error_type')
        and final.get('timed_out',False) is False and final['status']=='native-passed'
        and type(final['exit_status']) is int and final['exit_status']==0
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples']>0,
        'Native ownership/exit/cleanup differs')
    require(datetime.fromisoformat(start['started_at'])<=datetime.fromisoformat(final['finished_at']), 'Inverted capture interval')
    peak=final['observed_peak_process_group_rss_bytes']
    require(type(peak) is int and 0<=peak<=2*1024**3, 'Invalid observed RSS')
    if peak==0: require(identity['status']==5 and not final.get('live_rss_observation_obtained',False), 'Zero RSS lacks owned zombie')
    for name in ('stdout','stderr'):
        require(snapshot[name+'.bin']==dict(bytes=final[name+'_bytes'],sha256=final[name+'_sha256']), 'Stream changed')
    require(final['stderr_bytes']==0, 'Unknown stderr')
    require(inventory(directory)[0]==snapshot, 'Capture changed during checking')
    return dict(id=slot['id'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        observed_peak_process_group_rss_bytes=peak or None,rss_observation_complete=False,memory_usage_qualified=False),snapshot


def finish(report, plan, output, pins, resolutions, kb, check):
    errors=[]; held=False
    available,artifact_errors=inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        require(not artifact_errors, 'Nonregular/unreadable artifacts retained')
        require(report['attempts']==IDS[:len(report['attempts'])] and len(report['attempts'])<=4, 'Attempt order differs')
        require([r['id'] for r in report['registered']]==report['attempts'][:len(report['registered'])]
            and len({r['pid'] for r in report['registered']})==len(report['registered']), 'Native registration differs')
        require(report['active'] is None, 'Unclosed active command')
        for slot in plan['schedule'][:len(report['attempts'])]:
            record=json.loads(read_bytes(output/slot['directory']/'process.json'))
            registration=next((r for r in report['registered'] if r['id']==slot['id']),None)
            require(record['cleanup_errors']==[] and not record.get('artifact_errors'), 'Native cleanup failed')
            if registration:
                require(record['pid']==registration['pid'] and record['direct_child_reaped'] is True
                    and record.get('remaining_process_group',[])==record.get('remaining_after_cleanup',[])==[], 'Child/group not closed')
            else: require(record['native_process_started'] is False, 'Unregistered native process')
        for name,snapshot in report['validated_artifacts'].items():
            require({k[len(name)+1:]:v for k,v in available.items() if k.startswith(name+'/')}==snapshot,
                    'Previously validated capture changed')
        for name,snapshot in report['validated_build_artifacts'].items():
            require(available.get(name)==snapshot, 'Validated build output changed')
        if report['status']==SUCCESS:
            require(len(report['captures'])==len(report['registered'])==len(report['attempts'])==4,
                    'Incomplete four-process stage')
            expected={str(Path(slot['directory'])/n) for slot in plan['schedule']
                for n in ('start.json','active.json','process.json','stdout.bin','stderr.bin')}
            require(set(available)==expected|set(report['validated_build_artifacts']), 'Unexpected completed artifact')
        verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures']);check();held=True
    except BaseException as error: errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors: report['status']='failed-integrity'
    raw=encoded(report); kb.save(output/'report.json',report); closure={}; held=False
    try:
        require(read_bytes(output/'report.json')==raw, 'Serialized report changed')
        closure,_=inventory(output,('terminal.json',))
        require(closure==dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}), 'Final report/artifact inventory differs')
        verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures'])
        require(inventory(output,('terminal.json',))[0]==closure, 'Artifacts changed during final input replay')
        check();held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__); report['status']='failed-integrity';closure={}
    terminal=dict(schema='rebol-extension-build-layout-load-terminal-v1',status=report['status'],
        expected_report_sha256=digest(raw),report_sha256=None,available_evidence=closure,integrity_errors=errors,
        artifact_errors=artifact_errors,common_mutex_held=held,common_mutex_inode=79859134,
        native_processes_started=len(report['registered']),validated_captures=len(report['captures']),
        producer_success_is_not_qualification=True,benchmark_samples=0,**{k:False for k in GATES})
    try:
        terminal['report_sha256']=sha(output/'report.json')
        if closure: require(terminal['report_sha256']==digest(raw),'Report changed before terminal creation')
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
        terminal.update(status='failed-integrity',common_mutex_held=False,available_evidence={})
    # The named-lock check follows the last artifact/report read as well.
    try: check()
    except BaseException as error:
        errors.append(str(error) or type(error).__name__);terminal.update(status='failed-integrity',common_mutex_held=False,available_evidence={})
    with (output/'terminal.json').open('xb') as stream: stream.write(encoded(terminal))
    require(not errors and not artifact_errors, 'Final integrity failed; saved failure evidence retained')


def run(plan, plan_path, plan_sha, intake, pins, resolutions, inspector, common, leases):
    kb=inspector.kb;output=Path(plan['output']);pin(pins,resolutions,plan_path,plan_sha)
    verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures']);check_leases(leases)
    output.mkdir(parents=True,exist_ok=False)
    for name in ('build','home','tmp'): (output/name).mkdir()
    report=dict(schema='rebol-extension-build-layout-load-results-v1',status='running',plan=str(plan_path),plan_sha256=plan_sha,
        started_at=now(),active=None,attempts=[],registered=[],captures=[],validated_artifacts={},validated_build_artifacts={},
        pins=pins,input_resolutions=resolutions,general_commands=COMMANDS,benchmark_samples=0,
        failed_sdk_producer_preserved=True,full_fixture_suite_executed=False,**{k:False for k in GATES})
    kb.save(output/'report.json',report)
    try:
        for index,slot in enumerate(plan['schedule']):
            verify(pins,resolutions,plan['unavailable_inputs']);check_leases(leases)
            for name,snapshot in report['validated_build_artifacts'].items():
                require(dict(bytes=(output/name).stat().st_size,sha256=sha(output/name))==snapshot,'Build input changed between stages')
            directory=output/slot['directory'];directory.mkdir()
            with kb.atomic(): report['attempts'].append(slot['id']);kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid));report['active']=dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT=slot['timeout_seconds']
            kb.observe(slot['command'],slot['environment'],directory,bytes.fromhex(slot['stdin_hex']),common,launched,kind=KIND)
            with kb.atomic():
                report['active']=None
                capture,snapshot=checked_capture(slot,directory,os.getpid(),kb)
                stdout=read_bytes(directory/'stdout.bin')
                if index<2:
                    require(stdout==b'', 'Compiler emitted unexpected stdout')
                    stem='extension' if index==0 else 'layout'; source=PACKET/('clbg_primitives.c' if index==0 else 'layout-probe.c')
                    capture['actual_compiler_inputs']=validate_compile_inputs(output,stem,source,pins,resolutions)
                    images=[output/'build/clbg_primitives.dylib']
                    if index==1: images.append(output/'build/layout-probe')
                    capture['built_declared_image_closure']=built_image_closure(images,intake,inspector,pins)
                elif index==2: capture['native_layout_and_images']=validate_layout(stdout,output,intake,inspector,pins,resolutions)
                else: require(stdout==LOAD_OUTPUT,'Nine-command smoke output differs')
                built=build_inventory(output,index)
                require(all(built.get(n)==v for n,v in report['validated_build_artifacts'].items()),
                        'Later native stage changed an earlier validated build output')
                if report['captures']:
                    require(datetime.fromisoformat(report['captures'][-1]['finished_at'])<=datetime.fromisoformat(capture['started_at']), 'Stages overlapped')
                report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
                report['validated_build_artifacts']=built
                kb.save(output/'report.json',report)
        report['status']=SUCCESS
    except BaseException as error:
        with kb.atomic():
            report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic(): finish(report,plan,output,pins,resolutions,kb,lambda:check_leases(leases))


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare');prep.add_argument('--plan',type=Path,required=True);prep.add_argument('--output',type=Path,required=True)
    for name in ('toolchain-intake','source-review'):
        prep.add_argument('--'+name,type=Path,required=True);prep.add_argument('--'+name+'-sha256',required=True)
    execute=sub.add_parser('run');execute.add_argument('--plan',type=Path,required=True);execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
        and Path(sys.executable).resolve()==PYTHON.resolve(), 'Use retained Python -I -S -B')
    def interrupted(signum,frame): raise KeyboardInterrupt('Rebol extension stage interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP): signal.signal(sig,interrupted)
    if args.mode=='prepare':
        intake_ref=dict(path=str(physical(args.toolchain_intake)),sha256=args.toolchain_intake_sha256)
        source_ref=dict(path=str(physical(args.source_review)),sha256=args.source_review_sha256)
        saved=None; output=args.output
    else:
        require(sha(physical(args.plan))==args.plan_sha256,'Prepared plan changed')
        saved=json.loads(read_bytes(args.plan));intake_ref=saved['toolchain_intake'];source_ref=saved['source_review'];output=Path(saved['output'])
    with held_inputs(intake_ref) as (common,leases,intake,pins,resolutions):
        inspector=load_support(pins,resolutions)
        plan=build_plan(output,intake_ref,source_ref,intake,pins,resolutions,inspector)
        verify(pins,resolutions,plan['unavailable_inputs'],plan['prerequisite_artifact_closures']);check_leases(leases)
        if args.mode=='prepare':
            physical(args.plan);require(args.plan.is_relative_to(PACKET) and not args.plan.is_relative_to(output),'Plan must be separate inside packet')
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('xb') as stream: stream.write(encoded(plan))
            print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_processes_started=0)))
        else:
            require(saved==plan,'Prepared stage does not replay exactly')
            run(plan,args.plan,args.plan_sha256,intake,pins,resolutions,inspector,common,leases)


if __name__=='__main__': main()
