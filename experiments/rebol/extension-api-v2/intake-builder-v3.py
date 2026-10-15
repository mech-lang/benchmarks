"""Finite file-only intake; uses the reviewed extension reader and original leases."""
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import types

E = Path('/private/tmp/mech-benchmark-completion')
P = E/'experiments/rebol/extension-api-v2'
PRIVATE = Path('/private/tmp/mech-history-candidate-validation')
SOURCE = E/'tools/qualification/rebol_extension.py'
RELOCATION = P/'library-relocation-v1/compare.py'
INVENTORY = PRIVATE/'rebol-extension-intake-inventory-v1.json'
OBS = P/'toolchain-observations-v1'
NIM = E/'archive/languages/nim/20261012/proposals/private-v5.json'
# The reviewed adapter is copied here only after independent source approval.
ADAPTER = E/'tools/qualification/rebol_extension_typed_images.py'
ADAPTER_SHA = 'bec9d1e020cfd2449ecdd5e1dced224f6ccbf050785fd9390e3d07931d499124'
module_raw = ADAPTER.read_bytes()
if hashlib.sha256(module_raw).hexdigest() != ADAPTER_SHA:
    raise ValueError('Reviewed typed-image adapter changed')
adapter = types.ModuleType('rebol_extension_typed_image_intake'); adapter.__file__ = str(ADAPTER)
exec(compile(module_raw,str(ADAPTER),'exec'),adapter.__dict__)
e = adapter.load_controller(ADAPTER_SHA)
REVIEW_SHAS = {
    'gmp':'2b9d39f463eebc0bd93ae862fb398a7302321fd7a614086f53e0bf4fdc5d75ff',
    'pcre2':'4ea04461c9a600f625fefe2e03f8d7b131c9d9f4b214816f16bad3d50cebae68'}
inventory = json.loads(INVENTORY.read_bytes())
observed_plan = json.loads((OBS/'plan.json').read_bytes())


def ref(path):
    return dict(path=str(path), sha256=e.sha(path))


def save(path, value):
    raw = e.encoded(value)
    if path.exists():
        e.require(e.read_bytes(path) == raw, 'Existing intake evidence differs: '+str(path))
    else:
        with path.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return dict(path=str(path), sha256=e.digest(raw))



with ExitStack() as stack:
    common = stack.enter_context(e.regular(e.LOCK))
    fcntl.flock(common, fcntl.LOCK_EX | fcntl.LOCK_NB)
    e.require(os.fstat(common.fileno()).st_ino == 79859134, 'Wrong common mutex')
    leases = [(e.LOCK, common, (os.fstat(common.fileno()).st_dev, 79859134))]
    for path in e.LEASE_PATHS:
        stream = stack.enter_context(e.regular(path)); fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ident = observed_plan['leases'][str(path)]
        leases.append((path, stream, (ident['device'], ident['inode'])))
    e.check_leases(leases)
    pins, resolutions = {}, {}
    for name, expected in observed_plan['pins'].items():
        e.pin(pins, resolutions, name, expected)
    for path in (RELOCATION, P/'library-relocation-v1/test_compare.py', P/'library-relocation-v1/README.md',
                 Path('/opt/homebrew/Cellar/llvm@22/22.1.8/include/llvm/BinaryFormat/MachO.h'),
                 Path('/opt/homebrew/Library/Homebrew/keg_relocate.rb'),
                 Path('/opt/homebrew/Library/Homebrew/extend/os/mac/keg_relocate.rb')):
        e.pin(pins, resolutions, path)
    e.require(pins[str(SOURCE)] == e.sha(SOURCE), 'Observed controller changed')
    inspector = e.load_support(pins, resolutions)
    pure_root = E/'experiments/shared/pure-validation-20261015'
    pure_report = pure_root/'post-prolog-pure-validation-run-v1/report.json'
    pure_stderr = pure_report.parent/'05-test_rebol_extension.stderr'
    pure = json.loads(e.read_bytes(pure_report))
    # The recorded report contains the actual successful isolated test invocation.
    tests = [v for v in pure.values() if isinstance(v, list)]
    rows = [r for rows in tests for r in rows if isinstance(r, dict) and r.get('source') == 'tools/qualification/test_rebol_extension.py']
    e.require(len(rows) == 1 and rows[0]['exit_code'] == 0 and rows[0]['actual_methods'] == 13
              and rows[0]['passed'] is True, 'Actual thirteen-method test receipt missing')
    e.require(b'Ran 13 tests' in e.read_bytes(pure_stderr) and e.read_bytes(pure_stderr).endswith(b'\nOK\n'), 'Actual pure test stderr differs')
    source_review = dict(schema='rebol-extension-build-source-review-v1',
        status='source-reviewed-awaiting-native-build-layout-load',
        commands=e.COMMANDS, sdk_output_reuse=dict(path=str(e.REUSE), sha256=e.REUSE_SHA),
        files={str(path.relative_to(E)):e.sha(path) for path in e.SOURCE_FILES},
        pure_tests=dict(report=ref(pure_report), stderr=ref(pure_stderr), methods=13, exit_status=0,
                        rerun_by_this_intake=False),
        review_scope=[
            'The complete four-stage source, generated-header layout probe, ordinary nine-command smoke and focused fault tests received independent source review before their recorded pure validation.',
            'The corrected binary finish path reserves tail-zero width-one capacity before native-owned resources, expands without allocation, reacquires DATA, copies raw bytes and writes the terminator. Root and independent source reviews found no remaining blocker.',
            'The frozen observer and prior failed SDK/output-reuse evidence remain unchanged. Exact native layout, image origins and loaded behavior still require the four actual captures.',
            'Both compiler commands use the reviewed --no-default-config policy and explicit resource/SDK/linker roots; actual dry-run observations are linked separately.'
        ], observations=ref(P/'toolchain-observations-review-v1.json'),
        **{key:False for key in e.GATES})
    source_ref = save(P/'build-source-review-v1.json', source_review)
    e.pin(pins, resolutions, source_ref['path'], source_ref['sha256'])
    for name in (pure_report, pure_stderr, P/'toolchain-observations-review-v1.json', OBS/'plan.json', OBS/'report.json', OBS/'terminal.json'):
        e.pin(pins, resolutions, name)
    for name in e.SOURCE_FILES: e.pin(pins, resolutions, name, source_review['files'][str(name.relative_to(E))])
    libraries = {}
    provenance_records = {}
    for name in ('gmp', 'pcre2'):
        item = inventory['libraries'][name]
        for key in ('header', 'installed_image'):
            e.pin(pins, resolutions, item[key]['path'], item[key]['recorded_sha256'])
        formula = Path(item['installed_formula']); install = Path(item['installation_receipt'])
        manifest_path = Path(item['bottle_manifest_path']); bottle_path = Path(item['bottle_archive_path'])
        for path in (formula, install, manifest_path): e.pin(pins, resolutions, path)
        e.pin(pins, resolutions, bottle_path, item['bottle_declared_sha256'])
        e.require(bottle_path.stat().st_size == item['bottle_declared_bytes'], 'Bottle size differs')
        formula_raw = e.read_bytes(formula).decode()
        e.require(item['source_url'] in formula_raw and item['source_archive_declared_sha256'] in formula_raw, 'Formula source association differs')
        manifest = json.loads(e.read_bytes(manifest_path))
        selected = [row for row in manifest['manifests'] if row['digest'] == 'sha256:'+item['selected_oci_manifest_digest']]
        e.require(len(selected) == 1, 'Exact selected bottle manifest missing')
        entry = selected[0]; ann = entry['annotations']; tab = json.loads(ann['sh.brew.tab'])
        e.require(entry['platform']['architecture'] == 'arm64' and entry['platform']['os'] == 'darwin'
                  and ann['sh.brew.bottle.digest'] == item['bottle_declared_sha256']
                  and int(ann['sh.brew.bottle.size']) == item['bottle_declared_bytes']
                  and tab['binary_relocation_files'] == [], 'Selected bottle provenance differs')
        installed = json.loads(e.read_bytes(install))
        e.require(installed['source']['versions']['stable'] == item['version_from_package_and_header']
                  and installed['poured_from_bottle'] is True
                  and installed['changed_files'] == tab['changed_files'], 'Installed package provenance differs')
        # Reuse the completed exact comparison; never rerun or replace it.
        pref = dict(path=str(P/(name+'-source-image-review-v1.json')),sha256=REVIEW_SHAS[name])
        provenance = e.document(pref,pins,resolutions)
        e.require(provenance['schema']=='rebol-extension-library-package-provenance-v1'
            and provenance['status']=='reviewed-exact-library-source-and-installed-image'
            and provenance['library']==name and provenance['version']==item['version_from_package_and_header']
            and provenance['source_rebuild_equivalence_proven'] is False
            and provenance['actual_library_runtime_version_observed'] is False,
            'Original completed library review scope differs')
        for field, path in (('formula',formula),('installation_receipt',install),
                            ('bottle_manifest',manifest_path),('bottle_archive',bottle_path),
                            ('relocation_validator',RELOCATION)):
            e.require(provenance[field]==dict(path=str(path),sha256=pins[str(path)]),
                      'Library comparison prerequisite changed: '+field)
        e.require(provenance['selected_manifest']==entry
            and provenance['source_release']['url']==item['source_url']
            and provenance['source_release']['declared_sha256']==item['source_archive_declared_sha256']
            and all(provenance[k]==tab[k] for k in ('binary_relocation_files','linkage_files','changed_files')),
            'Library comparison package association differs')
        e.require([m['role'] for m in provenance['members']]==['header','image'],
                  'Exact completed member comparisons required')
        for role,key in (('header','header'),('image','installed_image')):
            member=next(m for m in provenance['members'] if m['role']==role)
            path=Path(item[key]['path']); expected=item[key]['recorded_sha256']
            e.require(provenance[key]==dict(path=str(path),sha256=expected)
                and member['installed_path']==str(path) and member['installed_sha256']==expected
                and member['member']==str(path.relative_to('/opt/homebrew/Cellar')),
                'Completed library member does not bind the selected current file')
        # Exact review digest binds all comparison details, including original
        # bottle-member bytes, code-page hashes and the narrowly allowed changes.
        provenance_records[name]=pref
        libraries[name]=dict(path=item['installed_image']['path'],sha256=item['installed_image']['recorded_sha256'],
            runtime_version='6.3.0' if name=='gmp' else '10.49 2026-09-28',source_provenance=pref)
    roots=dict(rebol=str(e.SDK_COPY/'src/include'),clang_resource=inventory['compiler']['resource_include_root'],
        macos_sdk=inventory['sdk']['selected_candidate_root'],gmp=str(Path(inventory['libraries']['gmp']['header']['path']).parent),
        pcre2=str(Path(inventory['libraries']['pcre2']['header']['path']).parent))
    retained=json.loads(e.read_bytes(NIM))['pins']; e.pin(pins,resolutions,NIM)
    header_roots=[Path(roots['rebol']),Path(roots['clang_resource']),Path(roots['macos_sdk'])/'usr/include',Path(roots['gmp']),Path(roots['pcre2'])]
    header_members={}
    for directory in header_roots:
        names=[]
        for path in sorted(directory.rglob('*')):
            if path.is_dir(): continue
            e.require(path.is_file(), 'Special or dangling include input: '+str(path))
            e.pin(pins,resolutions,path,retained.get(str(path))); names.append(str(path))
        header_members[str(directory)]=names
    for path,expected in e.HISTORICAL_FIXTURE_PINS.items(): e.pin(pins,resolutions,path,expected)
    # Exact compiler/linker selections exposed by the retained -### observations.
    extras=[Path('/opt/homebrew/Cellar/llvm@22/22.1.8/lib/libLTO.dylib'),
        Path('/opt/homebrew/Cellar/llvm@22/22.1.8/lib/clang/22/lib/darwin/libclang_rt.osx.a'),
        Path(roots['macos_sdk'])/'usr/lib/libSystem.B.tbd',Path(roots['macos_sdk'])/'usr/lib/libSystem.tbd',
        Path(inventory['sdk']['identity_path']),Path(inventory['compiler']['default_configuration_read']['path'])]
    for path in extras: e.pin(pins,resolutions,path,retained.get(str(path)))
    compiler_version=E/inventory['compiler']['observation']['path']
    compiler_stdout=E/inventory['compiler']['observation']['stdout_path']
    e.pin(pins,resolutions,compiler_version,inventory['compiler']['observation']['recorded_sha256'])
    e.pin(pins,resolutions,compiler_stdout,inventory['compiler']['observation']['recorded_stdout_sha256'])
    tools=dict(clang=dict(path=inventory['compiler']['path'],sha256=inventory['compiler']['recorded_sha256']),
        linker=ref(Path(inventory['linker']['candidate_physical_path'])),runtime=dict(path=str(e.RUNTIME),sha256=e.RUNTIME_SHA))
    local={}; closure=inspector.tool_closure([Path(tools[k]['path']) for k in ('clang','linker','runtime')]+[Path(libraries[k]['path']) for k in ('gmp','pcre2')],local)
    extra_pins={}; auxiliary=inspector.tool_closure([extras[0]],extra_pins)
    for values in (local,extra_pins):
        for name,expected in values.items(): e.pin(pins,resolutions,name,expected)
    intake=dict(schema='rebol-extension-concrete-toolchain-intake-v1',
        status='reviewed-concrete-compiler-sdk-and-library-inputs',source_review=source_ref,
        typed_image_adapter=dict(e.TYPED_IMAGE_ADAPTER),
        intake_entrypoint=ref(Path(__file__).resolve()),
        preserved_failed_intake=dict(path=str(P/'intake-v2-failure.json'),
            sha256='4d36c49f42132b435d557b48089bc0a524873c5a04b3042d3638b58467953888'),
        target='arm64-apple-macos11.0',actual_loaded_images_observed=False,tools=tools,include_roots=roots,
        input_pins=dict(pins), input_resolutions=dict(resolutions),libraries=libraries,
        compiler_version=ref(compiler_version), linker_version=ref(OBS/'00-linker-version/process.json'),
        sdk_identity=ref(Path(inventory['sdk']['identity_path'])),
        observations=ref(P/'toolchain-observations-review-v1.json'),
        declared_image_closure=closure,auxiliary_linker_image_closure=auxiliary,
        header_membership=header_members,
        unavailable_inputs=sorted(set(closure['unavailable_candidates'])|set(auxiliary['unavailable_candidates'])),
        prior_leases={str(path):dict(device=ident[0],inode=ident[1]) for path,stream,ident in leases[1:]},
        policy=dict(default_compiler_config_disabled=True,explicit_roots=True,ambient_loader_overrides=False,
            library_runtime_versions='Header/package expectations; observed by the future layout probe.',
            source_rebuild_equivalence_proven=False,native_processes_started=0,actual_compilation_performed=False),
        source_provenance=provenance_records,
        limits=['Static Mach-O closure records declared non-OS imports, not actual loaded images.',
            'OS/dyld-cache images are retained by install name, without invented file hashes.',
            'Clang target-linker-version27037.1 differs from selected ld1053.12; actual compilation/link compatibility remains untested.',
            'The original SDK failed stage and exact generated-output reuse disposition remain unchanged.'])
    # Bind every raw observation used by this intake, without changing the closed run.
    for path in sorted(OBS.rglob('*')):
        if path.is_file():e.pin(pins,resolutions,path)
    intake['input_pins']=dict(pins);intake['input_resolutions']=dict(resolutions)
    e.pin(pins,resolutions,__file__,intake['intake_entrypoint']['sha256'])
    e.pin(pins,resolutions,intake['preserved_failed_intake']['path'],intake['preserved_failed_intake']['sha256'])
    intake['input_pins']=dict(pins);intake['input_resolutions']=dict(resolutions)
    e.verify(pins,resolutions,intake['unavailable_inputs']);e.check_leases(leases)
    intake_ref=save(P/'toolchain-intake-v1.json',intake)
    e.validate_intake(intake,source_review,source_ref,{}, {})
    e.verify(pins,resolutions,intake['unavailable_inputs']);e.check_leases(leases)
    print(json.dumps(dict(intake=intake_ref,source_review=source_ref,input_pins=len(pins),
        header_counts={k:len(v) for k,v in header_members.items()},declared_images=len(closure['images']),
        auxiliary_images=len(auxiliary['images']),native_processes_started=0),indent=2))
