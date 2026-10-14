"""Review retained Prolog runtime metadata after full-workload reconciliation.

No runtime, compiler, or benchmark is executed. The CLI requires all three
existing leases and rechecks the completed reconciliation's file closure.
Probe and preparation observations are not timed-process observations.
"""
import argparse
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RECONCILER = Path(__file__).with_name('prolog_reconcile.py')
RECONCILER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
raw = RECONCILER.read_bytes()
if hashlib.sha256(raw).hexdigest() != RECONCILER_SHA:
    raise ValueError('Reviewed reconciliation tool changed')
spec = importlib.util.spec_from_file_location('prolog_metadata_reconciliation', RECONCILER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw, str(RECONCILER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/prolog-comparison/20261013')
CONFIG = str(HOST/'runtime-qualified/success-halt-v1/runtime-config.json')
CONFIG_SHA = '7fa470a9827e60e84eb9c6ad343cc8385e411b400f0ae8a322fbefda488bb448'
IMAGES = str(HOST/'.build/swi-runtime-success-halt-v1/images/closure.json')
IMAGE_SHA = '266d1d6a01d87fd2dd7baf274e018061519de9ffdf9b54c70b010ef4011a219a'
VERSION = 'SWI-Prolog version 10.0.2 for fat-darwin\n'
PREFIX = ['-q', '-O', '-f', 'none', '--stack-limit=8g']
SCHEMA = 'prolog-recorded-runtime-metadata-v1'


def runtime_flags(flags, home):
    same(flags, dict(architecture='arm64-darwin', bounded=False, gc=True, home=home,
        stack_limit=8589934592, version_components=[10, 0, 2], version_data='swi(10,0,2,[])'),
        'Retained runtime flags differ')


def successful(receipt, command):
    same(receipt['command'], command, 'Metadata command changed')
    require(p.integer(receipt['exit_status'], 0) and p.integer(receipt['final_exit_status'], 0),
            'Metadata command did not exit normally')
    require(receipt['inherited_common_mutex'] is True and receipt['preparation_only'] is True
            and receipt['never_chart_eligible'] is True, 'Metadata command ownership/scope changed')
    require(not any(receipt.get(k) for k in ('error', 'error_type', 'timed_out', 'cleanup_errors',
            'remaining_group_members')), 'Metadata command records failure')
    require(p.integer(receipt['pid']) and receipt['pid'] > 0
            and p.integer(receipt['identity']['pid'], receipt['pid']), 'Missing metadata process identity')
    require(p.timestamp(receipt['started_at']) <= p.timestamp(receipt['finished_at']), 'Metadata times inverted')


class Evidence:
    """Read only exact identity relocations and declared lossless gzip storage."""
    def __init__(self, plan, storage):
        self.plan = plan
        self.root = Path(plan['repository'])
        self.compressed = {str(self.root/a['logical_path']): a for a in storage['artifacts']}
        require(len(self.compressed) == len(storage['artifacts']), 'Duplicate compressed artifact')
        self.read_pins = {}

    def raw(self, name, expected=None):
        require(Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe metadata path')
        pins = self.plan['pins']
        if name in self.compressed:
            item = self.compressed[name]
            require(item['storage_encoding'] == 'gzip' and expected == item['original_sha256'],
                    'Compressed metadata identity changed')
            path = str(self.root/item['stored_path'])
            require(Path(path).is_relative_to(self.root) and '..' not in Path(path).parts
                    and pins[path] == item['stored_sha256'], 'Unpinned compressed metadata')
            stored = Path(path).read_bytes()
            require(len(stored) == item['stored_bytes'] and hashlib.sha256(stored).hexdigest() == pins[path],
                    'Compressed metadata bytes changed')
            data = gzip.decompress(stored)
            require(len(data) == item['original_bytes'], 'Decoded metadata size differs')
        else:
            path = name
            if path not in pins:
                relocation = self.plan['path_reconciliation'][name]
                require(relocation['historical_path'] == name and relocation['storage_encoding'] == 'identity'
                        and relocation['editorial_substitution'] is None
                        and relocation['expected_sha256'] == relocation['actual_content_sha256'] == expected,
                        'Runtime metadata requires an exact identity relocation')
                path = relocation['resolved_path']
            require(path in pins and (expected is None or pins[path] == expected), 'Unpinned metadata')
            data = Path(path).read_bytes()
            expected = pins[path]
        require(p.digest(expected) and hashlib.sha256(data).hexdigest() == expected, 'Metadata bytes changed')
        self.read_pins[path] = pins[path]
        return data

    def document(self, name, expected=None):
        return p.strict_json(self.raw(name, expected))


def inspect(plan, reconciliation, outcome, read, read_raw):
    """Semantic metadata checks; callers separately bind all files and leases."""
    _, all_profiles = r.schedule(plan)
    require(reconciliation['schema'] == r.SCHEMA
            and reconciliation['status'] == 'full90-reconciled-awaiting-runtime-and-publication-review'
            and reconciliation['file_integrity_verified'] is True
            and reconciliation['chart_admission'] is False
            and reconciliation['runtime_publication_metadata_qualified'] is False,
            'Completed independent reconciliation required')
    same(reconciliation['plan'], dict(path=str(Path(plan['repository'])/'experiments/prolog/full90-v1/plan.json'),
        sha256=r.PLAN_SHA), 'Reconciliation belongs to another plan')
    require(reconciliation['verified_file_pins'][str(RECONCILER.resolve())] == RECONCILER_SHA,
            'Reconciliation tool was not independently bound')
    require(reconciliation['verified_file_pins'].get(str(r.HELPER.resolve())) == r.HELPER_SHA,
            'Reconciliation primitive helper was not bound')
    for path, sha in plan['pins'].items():
        require(reconciliation['verified_file_pins'].get(path) == sha, 'Reconciliation omitted an input pin')
    require(outcome['status'] == 'qualified-original-Prolog20-work-and-LOC-awaiting-full90'
            and outcome['source_work_qualified'] is True and outcome['canonical_LOC_admitted'] is True
            and outcome['chart_admission'] is False and p.integer(outcome['profiles'], 20),
            'Source-work/LOC seal is incomplete')
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
    profiles = [row for row in all_profiles.values() if row['language'] == 'prolog']
    by_id = {row['id']: row for row in profiles}
    eligible, excluded = [], []
    for row in profiles:
        same(row['runtime_environment'], config['environment'], 'Profile runtime environment differs')
        require(row['binary'] == config['binary'] and row['binary_sha256'] == config['binary_sha256']
                and p.integer(row['maximum_workers'], 1), 'Profile runtime/worker policy differs')
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
        alias = row['source_alias_of']
        if row['variant'] == 'optimized':
            require(alias == 'prolog-'+row['benchmark']+'-compact'
                    and by_id[alias]['source_sha256'] == row['source_sha256'], 'Source alias changed')
        else:
            require(row['variant'] == 'compact' and alias is None, 'Unexpected source form')
        observed = reconciliation['profiles'][row['key']]
        for field in ('key', 'id', 'language', 'benchmark', 'source', 'source_sha256', 'binary_sha256'):
            same(observed[field], row[field], 'Reconciled profile metadata differs')
        if observed['full_workload_qualified'] is not True:
            require(row['key'] in reconciliation['failed_profiles'], 'Missing failure explanation')
            excluded.append(dict(key=row['key'], reason='failed-full-workload', failed_attempt=observed['failed_attempt']))
            continue
        require(row['key'] not in reconciliation['failed_profiles'] and len(observed['samples_seconds']) == 3,
                'Failed or incomplete profile offered for import')
        eligible.append(dict(key=row['key'], id=row['id'], benchmark=row['benchmark'], variant=row['variant'],
            source_alias_of=alias, optimization_claim=row['optimization_claim'],
            source=row['source'], source_sha256=row['source_sha256'], source_bundle=row['source_bundle'],
            binary=row['binary'], binary_sha256=row['binary_sha256'], qlf_artifact_pins=qlf,
            command=row['command'], cwd=row['cwd'], runtime_environment=row['runtime_environment'],
            canonical_loc=row['canonical_loc'], physical_loc=row['physical_loc'],
            execution_mode='swi-native-bytecode-vm', maximum_compute_workers=1,
            declared_vendor_libraries=retained['vendor_libraries'],
            preparation_foreign_libraries=loaded['foreign_libraries'],
            runtime_flags_observed_during_preparation=loaded['runtime'],
            timing=observed, chart_admission=False))
    return dict(schema=SCHEMA, status='recorded-runtime-metadata-reviewed-awaiting-file-verification',
        runtime_publication_metadata_qualified=False, file_integrity_verified=False, chart_admission=False,
        profiles=eligible, excluded_profiles=excluded, source_forms_reviewed=20,
        runtime_version='SWI-Prolog 10.0.2', native_architecture='arm64', application_execution='bytecode/QLF',
        memory_policy='SWI term, atom and clause garbage collection; retained preparation observed gc=true and bounded=false.',
        stack_limit_bytes=8589934592, maximum_compute_workers=1,
        probe_runtime_flags=feature['runtime'], probe_native_image_pins=images['image_pins'],
        os_install_names_not_file_hashed=sorted(os_images), pcre_version=config['pcre_version'],
        regex_policy='SWI library(pcre) calls bundled PCRE2 10.40 through pcre4pl; authored calls request jit(false).',
        arbitrary_integer_policy='Unbounded integers; bundled GMP image retained in the native runtime dependency closure.',
        timing_boundary=plan['timing_policy'], runtime_and_qlf_loading_inside_timer=True,
        compilation_outside_timer=True, new_native_probes=0, compiler_invocations=0, benchmark_samples=0,
        limitations=['Loaded-image and GC observations are from retained probe/preparation commands, not timed processes.',
            'Native application AOT compilation is not claimed; QLF stores application bytecode.',
            'GMP package version and numeric GC tuning defaults are not inferred from library filenames.',
            'Compact/optimized aliases retain distinct measured profiles without claiming distinct source algorithms.'],
        remaining_gate='Explicit dataset import and website validation; failed profiles remain excluded.')


def review_files(reconciliation_path, expected_sha, durable_directory):
    reconciliation_path = Path(reconciliation_path).resolve()
    raw = reconciliation_path.read_bytes()
    require(p.digest(expected_sha) and hashlib.sha256(raw).hexdigest() == expected_sha, 'Reconciliation digest differs')
    reconciliation = p.strict_json(raw)
    plan_path = Path(reconciliation['plan']['path'])
    require(reconciliation['plan']['sha256'] == r.PLAN_SHA, 'Wrong reconciliation plan')
    plan_raw = plan_path.read_bytes()
    require(hashlib.sha256(plan_raw).hexdigest() == r.PLAN_SHA, 'Retained plan changed')
    plan = p.strict_json(plan_raw)
    job = Path(durable_directory).resolve()
    with ExitStack() as stack:
        leases = []
        for path in (job/'owner.lock', Path(plan['repository'])/'experiments/prolog/prolog-full90.owner.lock', r.LOCK):
            handle = stack.enter_context(path.open('rb'))
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino), 'Lease replaced')
            if path == r.LOCK: require(held.st_ino == p.LOCK_INODE, 'Original common mutex replaced')
            leases.append((path, handle, held.st_dev, held.st_ino))
        files = r.Files()
        files.verify(str(reconciliation_path), expected_sha)
        files.verify(str(plan_path), r.PLAN_SHA)
        for path, sha in reconciliation['verified_file_pins'].items(): files.verify(path, sha)
        for path in (Path(__file__).resolve(), RECONCILER.resolve()):
            files.verify(str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        def saved(path):
            return files.document(path, reconciliation['verified_file_pins'][path])
        require(reconciliation['terminal']['path'] == plan['output']+'/terminal.json',
                'Reconciliation terminal outside completed study')
        for binding in (reconciliation['plan'], reconciliation['report'], reconciliation['terminal']):
            require(reconciliation['verified_file_pins'][binding['path']] == binding['sha256'],
                    'Reconciliation reference differs from verified bytes')
        report = saved(reconciliation['report']['path'])
        terminal = saved(reconciliation['terminal']['path'])
        same(reconciliation['report'], dict(path=plan['output']+'/report.json', sha256=terminal['report_sha256']),
             'Terminal binds another report')
        require(terminal['report'] == reconciliation['report']['path'], 'Terminal report path differs')
        for path, sha in terminal['available_evidence_pins'].items():
            require(reconciliation['verified_file_pins'].get(path) == sha,
                    'Reconciliation omitted completed evidence')
        durable = {name: saved(str(job/(name+'.json'))) for name in
            ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
        fresh = r.reconcile(plan, report, terminal,
            {a['result_path']: saved(a['result_path']) for a in report['attempts']},
            {a['supervisor_result_path']: saved(a['supervisor_result_path']) for a in report['attempts']},
            {a['path']: saved(a['path']) for a in report['independent_supervisors']},
            durable, str(plan_path), r.PLAN_SHA)
        for key, value in fresh.items():
            if key not in ('status', 'file_integrity_verified'):
                same(reconciliation[key], value, 'Saved reconciliation semantics differ: '+key)
        expected_inventory = set(terminal['available_evidence_pins']) | {reconciliation['terminal']['path']}
        require(r.inventory(plan['output']) == expected_inventory, 'Completed evidence inventory changed')
        storage = saved(plan['storage_manifest']['path'])
        reader = Evidence(plan, storage)
        outcome = reader.document(plan['sealed_source_outcome']['path'], r.OUTCOME_SHA)
        result = inspect(plan, reconciliation, outcome, reader.document, reader.raw)
        for path, sha in reader.read_pins.items(): files.verify(path, sha)
        for path, sha in list(files.verified.items()): files.verify(path, sha)
        require(r.inventory(plan['output']) == expected_inventory, 'Evidence inventory changed during review')
        for path, handle, device, inode in leases:
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == (device, inode), 'Lease identity changed')
        result.update(status='qualified-recorded-runtime-metadata', runtime_publication_metadata_qualified=True,
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=p.LOCK_INODE,
            plan=reconciliation['plan'], reconciliation=dict(path=str(reconciliation_path), sha256=expected_sha),
            verified_file_pins=files.verified, source_outcome=plan['sealed_source_outcome'])
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconciliation', type=Path, required=True)
    parser.add_argument('--reconciliation-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    require(not args.output.exists() and args.output.parent.is_dir(), 'Fresh output with an existing parent required')
    require(not args.output.resolve().is_relative_to(ROOT/'experiments/prolog/full90-v1/results'),
            'Metadata review cannot alter the closed measurement directory')
    result = None
    try:
        result = review_files(args.reconciliation, args.reconciliation_sha256, args.durable_directory)
    except BaseException as error:
        result = dict(schema=SCHEMA, status='runtime-metadata-review-failed', error_type=type(error).__name__,
            error=str(error), runtime_publication_metadata_qualified=False, file_integrity_verified=False,
            chart_admission=False, new_native_probes=0, compiler_invocations=0, benchmark_samples=0)
        raise
    finally:
        if result is not None:
            with args.output.open('x') as stream:
                json.dump(result, stream, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


if __name__ == '__main__':
    main()
