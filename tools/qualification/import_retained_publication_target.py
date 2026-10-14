"""Preview or apply retained cohorts in a separate publication checkout.

Original evidence reviewers keep their physical roots, pins and timing lease.
Only current catalogs, normalization history and publication transaction files
use the destination checkout. No native program is executed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import stat
import sys
from types import SimpleNamespace


EVIDENCE_ROOT = Path('/private/tmp/mech-benchmark-completion')
DRIVER = 'tools/qualification/import_retained_catalog.py'
DRIVER_SHA = 'd5dd6d091af4cae7dc6dd7dd7e5c6bda402309e2ae7b214ba2b31bed72d54ad4'
NORMALIZATION = 'tools/normalization_history.py'
NORMALIZATION_SHA = 'f22249bc06a18b84cf45f6e4de50061575fc6ae640fa0c380bf01ad0a4c9bfa0'
ADAPTER = 'tools/qualification/import_retained_publication_target.py'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return 'absent' if raw is None else hashlib.sha256(raw).hexdigest()


def directory(path):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path
            and stat.S_ISDIR(path.lstat().st_mode), 'Physical directory required: ' + str(path))
    return path


def relative(path, root):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(root)
            and path.resolve() == path, 'Nonphysical or escaped repository path: ' + str(path))
    return path.relative_to(root).as_posix()


def regular(path, optional=False):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
            'Nonphysical file path: ' + str(path))
    try:
        info = path.lstat()
    except FileNotFoundError:
        require(optional, 'Required file is absent: ' + str(path))
        return
    require(stat.S_ISREG(info.st_mode), 'Regular file required: ' + str(path))


def snapshot(old, path, optional=False):
    regular(path, optional)
    return old.snapshot(path, optional=optional)


def roots(evidence, publication):
    require(Path(evidence) == EVIDENCE_ROOT, 'Original measurement checkout required')
    evidence, publication = directory(evidence), directory(publication)
    require(not evidence.is_relative_to(publication) and not publication.is_relative_to(evidence),
            'Evidence and publication checkouts must be disjoint')
    return evidence, publication


def load_original(args, evidence):
    require(evidence == EVIDENCE_ROOT, 'Original measurement checkout required')
    path = evidence/DRIVER
    relative(path, evidence)
    regular(path)
    raw = path.read_bytes()
    require(sha(raw) == DRIVER_SHA, 'Original retained driver changed')
    spec = importlib.util.spec_from_file_location('retained_original_publication_driver', path)
    old = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), old.__dict__)
    require(old.ROOT == evidence and Path(old.__file__) == path, 'Original driver root changed')
    policy = old.COHORTS[args.cohort]
    expected = dict(reconciler=evidence/'tools/qualification'/policy['reconciler'],
                    exporter=evidence/'tools/qualification'/policy['exporter'],
                    writer=evidence/'tools/qualification/import_uiua_fann.py',
                    normalization=evidence/NORMALIZATION,
                    publication=evidence/'tools/qualification'/(
                        'uiua_fann_publication.py' if args.cohort == 'uiua-fann' else 'retained_catalog_publication.py'))
    for source in expected.values():
        regular(source)
    deps = old.load_dependencies(SimpleNamespace(cohort=args.cohort, tool_sha256=DRIVER_SHA,
                                               normalization_sha256=NORMALIZATION_SHA))
    for name, source in expected.items():
        module = deps[name]
        require(Path(module.__file__) == source and getattr(module, 'ROOT', evidence) == evidence
                and source in deps['pins'], 'Original consumer location/pin changed: ' + name)
        relative(source, evidence)
    require(deps['pins'][path] == DRIVER_SHA and deps['pins'][evidence/NORMALIZATION] == NORMALIZATION_SHA,
            'Original dependency pins changed')
    return old, deps


def checked(old, path, expected):
    raw, _ = snapshot(old, path)
    require(sha(raw) == expected, 'Pinned bytes differ: ' + str(path))
    return raw


def publication_links(candidate, candidate_ref, pins, evidence, runtime_scope=None):
    """Direct publication links only; never traverse physical pin-map contents."""
    links = {}
    def add(name, expected):
        path = Path(name)
        require(name and not path.is_absolute() and '..' not in path.parts and path.as_posix() == name,
                'Nonportable publication evidence link')
        require(type(expected) is str and len(expected) == 64
                and all(c in '0123456789abcdef' for c in expected), 'Invalid publication evidence digest')
        require(name not in links or links[name] == expected, 'Conflicting publication link')
        links[name] = expected
    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if type(value.get('path')) is str and type(value.get('sha256')) is str:
                path = Path(value['path'])
                if not path.is_absolute():
                    add(value['path'], value['sha256'])
                elif path.is_relative_to(evidence):
                    add(path.relative_to(evidence).as_posix(), value['sha256'])
            for item in value.values():
                visit(item)
    visit(candidate)
    visit(candidate_ref)
    if runtime_scope is not None:
        visit(runtime_scope)
    for path, expected in pins.items():
        add(relative(path, evidence), expected)
    for expected, source in candidate['files'].items():
        require(source['sha256'] == expected == sha(source['code'].encode('utf-8')), 'Embedded source differs')
        for name in (source['path'], *source.get('source_paths', [])):
            add(name, expected)
    return links


def verify_links(old, links, evidence, publication):
    for name, expected in links.items():
        require(checked(old, evidence/name, expected) == checked(old, publication/name, expected),
                'Copied publication evidence differs: ' + name)


def plan_publication(old, deps, args, candidate, originals, apply_output, publication, pins, runtime_scope):
    """Preserve the existing transform and registry format on target-local bytes."""
    p, n, spec = (deps[key] for key in ('publication', 'normalization', 'spec'))
    require(spec['audit_key'] in n.ADAPTERS, 'Reviewed history adapter required')
    before = n.strict_json(originals[old.CATALOGS[0]])
    languages = n.strict_json(originals[old.CATALOGS[1]])
    n.historical_view(publication, before)
    history = (dict(schema='canonical-loc-normalization-history-v1', admissions=[])
               if originals[old.HISTORY] is None else n.strict_json(originals[old.HISTORY]))
    n.validate_registry(history)
    require(all(row['audit_key'] != spec['audit_key'] for row in history['admissions']), 'Admission already registered')
    candidate_ref = dict(path=relative(args.candidate, EVIDENCE_ROOT), sha256=args.candidate_sha256)
    options = dict(runtime_scope_ref=runtime_scope) if args.cohort == 'apl' else {}
    data, languages, audit = p.build_publication(before, languages, candidate, candidate_ref, **options)
    require(data[spec['audit_key']] == audit, 'Transform admission identity differs')
    groups = audit.get('endpoints', {'fannkuchredux': audit.get('endpoint')})
    selected = {key for group in groups.values() for key in group['programs']}
    additions = dict(programs=selected, program_inventory=set(candidate['program_inventory']))
    references = ({spec['language']} if spec['language'] not in {row['lang'] for row in before['reference_summary']} else set())
    n.validate_transition(before, data, audit, additions, references)
    # Portable evidence joins are also checked before creating transaction files.
    actual_additions, actual_references = n.ADAPTERS[spec['audit_key']](publication, audit, before, data)
    require(n.additions_by_pool(actual_additions) == n.additions_by_pool(additions)
            and actual_references == references, 'Portable admission scope differs')
    prepared = {old.CATALOGS[0]: old.encoded(data), old.CATALOGS[1]: old.encoded(languages)}
    applied = dict(schema='retained-catalog-guarded-apply-v1', status='applied', cohort=args.cohort,
        receipt_path=relative(apply_output/'SUCCESS.json', publication),
        originals={name: sha(originals[name]) for name in old.CATALOGS},
        prepared={name: sha(prepared[name]) for name in old.CATALOGS},
        prior_normalization_history_sha256=sha(originals[old.HISTORY]), audit=audit, candidate=candidate_ref,
        publication_sources=[dict(path=relative(path, EVIDENCE_ROOT), sha256=value) for path, value in pins.items()],
        evidence_root=str(EVIDENCE_ROOT), publication_root=str(publication),
        original_driver=dict(path=DRIVER, sha256=DRIVER_SHA),
        catalog_changed=True, native_processes_started=0)
    raw = old.encoded(applied)
    entry = dict(audit_key=spec['audit_key'], success=dict(path=applied['receipt_path'], sha256=sha(raw)))
    history = copy.deepcopy(history)
    history['admissions'].append(entry)
    n.validate_registry(history)
    prepared[old.HISTORY] = old.encoded(history)
    return data, audit, prepared, applied, raw, entry


def publish(args):
    evidence, publication = roots(args.evidence_root, args.publication_root)
    old, deps = load_original(args, evidence)
    spec, r, n, writer = (deps[key] for key in ('spec', 'reconciler', 'normalization', 'writer'))
    adapter = evidence/ADAPTER
    require(Path(__file__).resolve() in (adapter, publication/ADAPTER), 'Unexpected adapter location')
    checked(old, adapter, args.adapter_sha256)
    candidate_path = Path(args.candidate)
    relative(candidate_path, evidence)
    require(candidate_path.is_relative_to(evidence/spec['packet']), 'Candidate must stay in original evidence packet')
    output = Path(args.output)
    relative(output, publication)
    packet = publication/spec['packet']
    require(output.is_relative_to(packet) and output != packet and not output.exists(), 'Fresh target packet output required')
    directory(output.parent)
    if args.mode == 'preview':
        require(args.apply_output is not None, 'Preview requires future apply output')
        apply_output = Path(args.apply_output)
        relative(apply_output, publication)
        require(apply_output.is_relative_to(packet) and apply_output != packet and not apply_output.exists()
                and not apply_output.is_relative_to(output) and not output.is_relative_to(apply_output),
                'Separate fresh target apply directory required')
        directory(apply_output.parent)
    else:
        require(args.mode == 'apply' and args.apply_output is None, 'Invalid publication mode')
        apply_output = output
        require(all(getattr(args, field, None) for field in (
            'expected_catalog_sha256', 'expected_languages_sha256', 'expected_history_sha256',
            'expected_prepared_catalog_sha256', 'expected_prepared_languages_sha256', 'expected_prepared_history_sha256')),
            'Apply requires six exact reviewed preview digests')
    pins = dict(deps['pins'])
    require(adapter not in pins, 'Adapter collides with original dependency')
    pins[adapter] = args.adapter_sha256
    owned = writer.OwnedFiles()
    originals, identities, input_pins, links = {}, {}, {}, {}
    journal = None
    failed = False
    after_data = None

    def cleanup():
        nonlocal failed
        failed = True
        errors = []
        if journal is not None:
            unsafe = {}
            for name in tuple(journal.installed):
                try:
                    regular(publication/name, optional=True)
                except BaseException as error:
                    unsafe[name] = journal.installed.pop(name)
                    errors.append(error)
            try:
                journal.rollback()
            except BaseException as error:
                errors.append(error)
            finally:
                journal.installed.update(unsafe)
        preserve_recovery = bool(errors)
        for path in tuple(owned.records):
            if preserve_recovery and path.parent != output:
                continue
            try:
                regular(path, optional=True)
                owned.remove(path)
            except BaseException as error:
                errors.append(error)
        if errors:
            raise BaseExceptionGroup('Publication restoration failed', errors)

    def check_inputs():
        for path, expected in tuple(input_pins.items()):
            checked(old, path, expected)
        verify_links(old, links, evidence, publication)

    def check_owned():
        for path in owned.records:
            regular(path)
        owned.final_check()

    def check_targets():
        for name in old.TARGETS:
            regular(publication/name, optional=originals[name] is None and journal is None)
        if args.mode == 'apply' and journal is not None:
            journal.final_check()
        else:
            old.check_state(publication, originals, identities)

    def final_check():
        if failed:
            return
        check_inputs()
        check_owned()
        if originals:
            check_targets()
            if args.mode == 'apply' and journal is not None:
                n.historical_view(publication, after_data)
                check_targets()
        check_owned()
        check_inputs()

    context = r.review_files if args.cohort == 'r' else r.review_context
    context_args = ((spec['reconciler_sha'], evidence/spec['source_counts'], spec['source_counts_sha'])
                    if args.cohort == 'lua' else (spec['reconciler_sha'],))
    with context(*context_args, on_exit_failure=cleanup, final_consumer_check=final_check) as values:
        require(len(values) == (3 if args.cohort == 'lua' else 2), 'Unexpected original review shape')
        review, files = values[:2]
        def read(path, expected):
            path = Path(path)
            require(path not in input_pins or input_pins[path] == expected, 'Consumer input pin rebound')
            regular(path)
            files.verify(path, expected)
            raw = checked(old, path, expected)
            input_pins[path] = expected
            return raw
        for path, expected in pins.items():
            read(path, expected)
        candidate = old.reproduce(args, deps, review, read)
        runtime_scope = old.validate_apl_runtime(candidate, review, read, n) if args.cohort == 'apl' else None
        candidate_ref = dict(path=relative(candidate_path, evidence), sha256=args.candidate_sha256)
        links.update(publication_links(candidate, candidate_ref, pins, evidence, runtime_scope))
        require(not set(links) & set(old.TARGETS), 'Publication evidence collides with mutable target')
        check_inputs()
        for name in old.TARGETS:
            originals[name], identities[name] = snapshot(old, publication/name, optional=name == old.HISTORY)
        if args.mode == 'apply':
            for name, field in zip(old.TARGETS, ('expected_catalog_sha256', 'expected_languages_sha256', 'expected_history_sha256')):
                require(sha(originals[name]) == getattr(args, field), 'Original differs from reviewed preview: ' + name)
        after_data, audit, prepared, applied, applied_raw, entry = plan_publication(
            old, deps, args, candidate, originals, apply_output, publication, pins, runtime_scope)
        if args.mode == 'apply':
            for name, field in zip(old.TARGETS, ('expected_prepared_catalog_sha256', 'expected_prepared_languages_sha256', 'expected_prepared_history_sha256')):
                require(sha(prepared[name]) == getattr(args, field), 'Prepared bytes differ from reviewed preview: ' + name)
        final_check()
        output.mkdir()
        for name in old.TARGETS:
            (output/'before'/Path(name).parent).mkdir(parents=True, exist_ok=True)
            (output/'after'/Path(name).parent).mkdir(parents=True, exist_ok=True)
            if originals[name] is None:
                owned.write(output/'before'/(name+'.absent'), b'absent\n')
            else:
                owned.write(output/'before'/name, originals[name])
            owned.write(output/'after'/name, prepared[name])
        if args.mode == 'apply':
            owned.write(output/'SUCCESS.json', applied_raw)
            journal = old.Journal(publication, writer, originals, identities, prepared)
            for name in old.TARGETS:
                regular(publication/name, optional=originals[name] is None)
            journal.apply()
            result = applied
        else:
            result = dict(schema='retained-catalog-guarded-preview-v1', status='preview-ready', cohort=args.cohort,
                evidence_root=str(evidence), publication_root=str(publication),
                originals={name: sha(raw) for name, raw in originals.items()},
                prepared={name: sha(raw) for name, raw in prepared.items()}, audit=audit,
                proposed_apply=entry['success'], catalog_changed=False, native_processes_started=0)
            owned.write(output/'SUCCESS.json', old.encoded(result))
        final_check()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--publication-root', type=Path, required=True)
    parser.add_argument('--cohort', choices=('uiua-fann', 'r', 'uiua', 'apl', 'lua'), required=True)
    parser.add_argument('--mode', choices=('preview', 'apply'), required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--candidate-sha256', required=True)
    parser.add_argument('--adapter-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply-output', type=Path)
    for name in ('catalog', 'languages', 'history', 'prepared-catalog', 'prepared-languages', 'prepared-history'):
        parser.add_argument('--expected-'+name+'-sha256')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Use Python -I -S -B with assertions enabled')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Publication interrupted: ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    result = publish(args)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
