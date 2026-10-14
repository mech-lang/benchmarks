"""Guarded admission of already measured Uiua, R and GNU APL cohorts.

Preview reproduces saved evidence and proposes exact catalog/history bytes.
Apply requires that preview's six digests and installs the two catalogs plus
normalization history in one rollback journal. No native program is executed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOGS = ('data/benchmarks.json', 'data/languages.json')
HISTORY = 'data/normalization-history.json'
TARGETS = CATALOGS + (HISTORY,)
ABSENT = 'absent'
WRITER_SHA = 'f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'
SHARED_SHA = 'e8a14b971bd07b041c1a08e7a46821a70bd068c5a931ac33a9f98227626c836f'
COHORTS = {
    'r': dict(packet='experiments/r/retained-native-v1', reconciler='r_retained_reconcile.py',
        reconciler_sha='8015461d228fa1d72acb1fdf76373f20bcc257b813534bf874d850df308e062b',
        exporter='r_retained_export.py', exporter_sha='3ba5c93901ad1911d0c9446bbc61a29a58e8f7b7f62d6bc91c1448fffff8996a',
        audit_key='r_retained_publication_audit', language='r'),
    'apl': dict(packet='experiments/apl/retained-native-v1', reconciler='apl_retained_reconcile.py',
        reconciler_sha='3abf092426f9febb692a049907fb9ea12822e78f672a949c28efc82ea3a4942c',
        exporter='apl_retained_export.py', exporter_sha='24802484ccaa005d8d638b6d96ed028888c62c2f56ae375fdaed7be504899179',
        audit_key='apl_retained_publication_audit', language='apl'),
    'uiua': dict(packet='experiments/uiua/retained-native-v1', reconciler='uiua_retained_reconcile.py',
        reconciler_sha='6ffbc98941b3e4e60ac63a899f0e8e4e0cb10def2d3d66ba60c61d25ad3a5523',
        exporter='export_uiua_retained.py', exporter_sha='dd2298c2ce98613f3e6aa2b9cfa942647d5af9fb976eaf0a600693eac0a7cfa6',
        audit_key='uiua_retained_publication_audit', language='uiua'),
    'uiua-fann': dict(packet='experiments/uiua/fann-v5-publication-v1', reconciler='uiua_fann_reconcile.py',
        reconciler_sha='bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd',
        exporter='import_uiua_fann.py', exporter_sha=WRITER_SHA,
        audit_key='uiua_fann_v5_publication_audit', language='uiua'),
}
FANN_PUBLICATION_SHA = '793d2bce677760cce6b0e2479742aee17e39094950b7486449416a9bc225f8a7'
APL_RUNTIME_REVIEW = dict(path='experiments/apl/retained-native-v1/runtime-publication-scope-review-v1.json',
    sha256='76a28e0e75497ebc181c95cbaa3a529b69fe8b2cbac3ae04ed011468565a41d6')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return ABSENT if raw is None else hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode('utf-8')


def checked(path, digest):
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
            'Explicit SHA-256 required')
    raw = Path(path).read_bytes()
    require(sha(raw) == digest, 'Pinned input changed: '+str(path))
    return raw


def module(name, path, digest):
    raw = checked(path, digest)
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value


def relative(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT.resolve()), 'Repository path required')
    return path.relative_to(ROOT.resolve()).as_posix()


def snapshot(path, optional=False):
    path = Path(path)
    require(not path.is_symlink() and path.resolve() == path.absolute(),
            'Catalog symlink is not an owned target: '+str(path))
    if not path.exists():
        require(optional, 'Required catalog is absent: '+str(path))
        return None, None
    with path.open('rb') as stream:
        stat = os.fstat(stream.fileno())
        raw = stream.read()
    identity = stat.st_dev, stat.st_ino
    named = path.stat()
    require((named.st_dev, named.st_ino) == identity, 'Catalog changed while reading: '+str(path))
    return raw, identity


def check_state(root, contents, identities):
    for name, expected in contents.items():
        raw, identity = snapshot(root/name, optional=expected is None)
        require(raw == expected and identity == identities[name], 'Catalog changed: '+name)


class Journal:
    """Track exact installed inodes; restore every still-owned target on error."""
    def __init__(self, root, writer, originals, identities, prepared):
        self.root, self.writer = root, writer
        self.originals, self.identities, self.prepared = originals, identities, prepared
        self.installed = {}
        self.restoring = {}

    def apply(self):
        check_state(self.root, self.originals, self.identities)
        for name in TARGETS:
            path = self.root/name
            temporary = path.with_name(path.name+'.retained-admission.tmp')
            owner = self.writer.OwnedFiles()
            try:
                owner.write(temporary, self.prepared[name])
                check_state(self.root, {name:self.originals[name]}, {name:self.identities[name]})
                identity = owner.records[temporary][0]
                # Record intent first: even an interruption immediately after
                # the atomic rename leaves the installed inode journaled.
                self.installed[name] = identity
                temporary.replace(path)
                owner.records.clear()
            finally:
                owner.remove_all()

    def final_check(self):
        require(set(self.installed) == set(TARGETS), 'Catalog transaction is incomplete')
        check_state(self.root, self.prepared, self.installed)

    def rollback(self):
        errors = []
        for name, identity in reversed(tuple(self.installed.items())):
            path = self.root/name
            owner = self.writer.OwnedFiles()
            try:
                actual, named = snapshot(path, optional=True)
                restored_identity = self.restoring.get(name, self.identities[name])
                if actual == self.originals[name] and named in (self.identities[name], restored_identity):
                    # Rename never happened, or a prior rollback completed but
                    # was interrupted before its bookkeeping acknowledgement.
                    self.installed.pop(name)
                    continue
                check_state(self.root, {name:self.prepared[name]}, {name:identity})
                if self.originals[name] is None:
                    self.restoring[name] = None
                    path.unlink()
                else:
                    temporary = path.with_name(path.name+'.retained-rollback.tmp')
                    owner.write(temporary, self.originals[name])
                    check_state(self.root, {name:self.prepared[name]}, {name:identity})
                    self.restoring[name] = owner.records[temporary][0]
                    temporary.replace(path)
                    owner.records.clear()
                self.installed.pop(name)
            except BaseException as error:
                errors.append(str(error))
            finally:
                try:
                    owner.remove_all()
                except BaseException as error:
                    errors.append(str(error))
        if errors:
            raise ValueError('; '.join(errors))


def load_dependencies(args):
    own = Path(__file__).resolve()
    checked(own, args.tool_sha256)
    spec = COHORTS[args.cohort]
    directory = own.parent
    publication_name = 'uiua_fann_publication.py' if args.cohort == 'uiua-fann' else 'retained_catalog_publication.py'
    publication_sha = FANN_PUBLICATION_SHA if args.cohort == 'uiua-fann' else SHARED_SHA
    pins = {
        own:args.tool_sha256,
        directory/spec['reconciler']:spec['reconciler_sha'],
        directory/spec['exporter']:spec['exporter_sha'],
        directory/'import_uiua_fann.py':WRITER_SHA,
        directory/publication_name:publication_sha,
        directory.parent/'normalization_history.py':args.normalization_sha256,
    }
    return dict(spec=spec, pins=pins,
        reconciler=module('retained_catalog_closed_evidence', directory/spec['reconciler'], spec['reconciler_sha']),
        exporter=module('retained_catalog_candidate_source', directory/spec['exporter'], spec['exporter_sha']),
        publication=module('retained_catalog_transform', directory/publication_name, publication_sha),
        normalization=module('retained_catalog_history', directory.parent/'normalization_history.py', args.normalization_sha256),
        writer=module('retained_catalog_owned_files', directory/'import_uiua_fann.py', WRITER_SHA))


def reproduce(args, deps, review, read):
    """Rebuild the exact frozen export, including its producer annotations."""
    spec, r, e, p, n = (deps[k] for k in ('spec','reconciler','exporter','publication','normalization'))
    candidate = n.strict_json(read(args.candidate.resolve(), args.candidate_sha256))
    ref = candidate['reconciliation']
    n.safe_path(ref['path'])
    review_path = (ROOT/ref['path']).resolve()
    require(review_path.is_relative_to((ROOT/spec['packet']).resolve()), 'Reconciliation must remain in its packet')
    saved_review = n.strict_json(read(review_path, ref['sha256']))
    require(saved_review == review, 'Independent reconciliation changed since export')
    if args.cohort == 'r':
        sources = {key:read(ROOT/c['source']['path'], c['source']['sha256'])
                   for key,c in review['canonical_counts'].items()}
        fresh = e.build_candidate(review, sources, r)
    elif args.cohort == 'apl':
        index, documents, _, sources = r.metadata()
        fresh = e.build_candidate(review, sources, index, documents['counts'], documents['report'])
    elif args.cohort == 'uiua':
        read(e.REVIEW, e.REVIEW_SHA)
        sources = {key:read(Path(review['profiles'][key]['original_profile']['source']),
                           review['profiles'][key]['source_sha256']) for key in r.COUNTS}
        fresh = e.build_candidate(review, sources)
        fresh['independent_source_review'] = dict(path=relative(e.REVIEW), sha256=e.REVIEW_SHA)
        fresh['consumer_sources'] = {
            'exporter':dict(path='tools/qualification/'+spec['exporter'], sha256=spec['exporter_sha']),
            'reconciler':dict(path='tools/qualification/'+spec['reconciler'], sha256=spec['reconciler_sha'])}
    else:
        sources = {v:read(r.ARCHIVE/'sources'/(v+'.ua'), review['source_counts'][v]['source_sha256'])
                   for v in ('compact','fast')}
        fresh = p.build_candidate(review, sources)
        fresh['consumer_sources'] = {
            'driver':dict(path='tools/qualification/import_uiua_fann.py', sha256=WRITER_SHA),
            'reconciler':dict(path='tools/qualification/uiua_fann_reconcile.py', sha256=spec['reconciler_sha']),
            'publication':dict(path='tools/qualification/uiua_fann_publication.py', sha256=FANN_PUBLICATION_SHA)}
    fresh['reconciliation'] = ref
    if args.cohort in ('r','apl'):
        fresh['exporter'] = dict(path='tools/qualification/'+spec['exporter'], sha256=spec['exporter_sha'])
    require(candidate == fresh, 'Candidate differs from independently reproduced frozen export')
    return candidate


def validate_apl_runtime(candidate, review, read, normalization):
    approval = normalization.strict_json(read(ROOT/APL_RUNTIME_REVIEW['path'], APL_RUNTIME_REVIEW['sha256']))
    require(approval['schema'] == 'apl-retained-runtime-publication-scope-review-v1' and
            approval['status'] == 'qualified-recorded-runtime-metadata-with-explicit-static-scope' and
            approval['runtime_publication_metadata_qualified'] is True, 'Separate APL runtime approval missing')
    documents = {}
    for name,ref in approval['inputs'].items():
        normalization.safe_path(ref['path'])
        documents[name] = read(ROOT/ref['path'],ref['sha256'])
    status = normalization.strict_json(documents['closed_recovery_status'])
    inherited = status['retained_input_and_actual_result_pins']
    for path,digest in approval['required_inherited_pins'].items():
        require(inherited.get(path) == review['verified_file_pins'].get(path) == digest,
                'APL runtime scope lacks the completed inherited physical pin: '+path)
    bindings = approval['profile_bindings']
    require(len(bindings) == 11 and set(bindings) == set(candidate['program_inventory']) and
            candidate['runtime_publication_metadata_qualified'] is False, 'APL runtime scope inventory changed')
    for key,expected in bindings.items():
        row = candidate['program_inventory'][key]
        original = review['profiles'][key]['source_profile']
        actual = {field:copy.deepcopy(original[field]) for field in
                  ('source_sha256','runtime_sha256','binary','binary_sha256','command','runtime_environment','library_support')}
        actual['requested_worker_ceiling'] = row['maximum_workers']
        require(actual == expected and row['runtime'] == approval['runtime'] == original['runtime'] and
                row['source_sha256'] == expected['source_sha256'] and row['runtime_arguments'] == expected['command'] and
                row['runtime_environment'] == expected['runtime_environment'] and
                row['runtime_publication_metadata_qualified'] is False, 'APL runtime profile binding differs: '+key)
    return copy.deepcopy(APL_RUNTIME_REVIEW)


def plan_publication(args, deps, candidate, originals, apply_output, runtime_scope_ref=None):
    p, n, spec = (deps[k] for k in ('publication','normalization','spec'))
    before = n.strict_json(originals[CATALOGS[0]])
    before_languages = n.strict_json(originals[CATALOGS[1]])
    # Verify the real preceding history; a proposed future receipt is never
    # supplied to historical_view during preview.
    n.historical_view(ROOT, before)
    history = (dict(schema='canonical-loc-normalization-history-v1', admissions=[])
               if originals[HISTORY] is None else n.strict_json(originals[HISTORY]))
    n.validate_registry(history)
    require(all(e['audit_key'] != spec['audit_key'] for e in history['admissions']), 'Admission already registered')
    candidate_ref = dict(path=relative(args.candidate), sha256=args.candidate_sha256)
    options = dict(runtime_scope_ref=runtime_scope_ref) if args.cohort == 'apl' else {}
    data, languages, audit = p.build_publication(before, before_languages, candidate, candidate_ref, **options)
    require(data[spec['audit_key']] == audit, 'Transform admission identity differs')
    endpoints = audit.get('endpoints', {'fannkuchredux':audit.get('endpoint')})
    selected = {key for group in endpoints.values() for key in group['programs']}
    additions = dict(programs=selected, program_inventory=set(candidate['program_inventory']))
    references = ({spec['language']} if spec['language'] not in {r['lang'] for r in before['reference_summary']} else set())
    n.validate_transition(before, data, audit, additions, references)
    prepared = {CATALOGS[0]:encoded(data), CATALOGS[1]:encoded(languages)}
    # Deliberately exclude the new registry digest from the actual SUCCESS;
    # its own digest is the registry entry, so including it would be circular.
    applied = dict(schema='retained-catalog-guarded-apply-v1', status='applied',
        cohort=args.cohort, receipt_path=relative(apply_output/'SUCCESS.json'),
        originals={name:sha(originals[name]) for name in CATALOGS},
        prepared={name:sha(prepared[name]) for name in CATALOGS},
        prior_normalization_history_sha256=sha(originals[HISTORY]),
        audit=audit, candidate=candidate_ref,
        publication_sources=[dict(path=relative(path), sha256=digest) for path,digest in deps['pins'].items()],
        catalog_changed=True, native_processes_started=0)
    applied_raw = encoded(applied)
    entry = dict(audit_key=spec['audit_key'], success=dict(path=applied['receipt_path'], sha256=sha(applied_raw)))
    proposed_history = copy.deepcopy(history)
    proposed_history['admissions'].append(entry)
    n.validate_registry(proposed_history)
    prepared[HISTORY] = encoded(proposed_history)
    return data, audit, prepared, applied, applied_raw, entry


def run(args, deps=None):
    deps = load_dependencies(args) if deps is None else deps
    spec, r, n, writer = (deps[k] for k in ('spec','reconciler','normalization','writer'))
    packet = (ROOT/spec['packet']).resolve()
    output = args.output.resolve()
    candidate_path = args.candidate.resolve()
    require(output.is_relative_to(packet) and not output.exists(), 'Fresh output directory inside cohort packet required')
    require(candidate_path.is_relative_to(packet), 'Candidate must remain inside its cohort packet')
    if args.mode == 'preview':
        require(args.apply_output is not None, 'Preview requires the intended future --apply-output')
        apply_output = args.apply_output.resolve()
        require(apply_output.is_relative_to(packet) and not apply_output.exists() and
                not (apply_output.is_relative_to(output) or output.is_relative_to(apply_output)),
                'Separate fresh apply directory inside cohort packet required')
    else:
        require(args.apply_output is None, '--apply-output is only used during preview')
        apply_output = output
        require(all(getattr(args, field, None) for field in (
            'expected_catalog_sha256','expected_languages_sha256','expected_history_sha256',
            'expected_prepared_catalog_sha256','expected_prepared_languages_sha256','expected_prepared_history_sha256')),
            'Apply requires all six reviewed preview digests (history may originally be absent)')
    owned = writer.OwnedFiles()
    originals, identities, input_pins = {}, {}, {}
    journal = None
    failure_started = False
    result = None
    after_data = None

    def cleanup():
        nonlocal failure_started
        failure_started = True
        errors = []
        if journal is not None:
            try:
                journal.rollback()
            except BaseException as error:
                errors.append(str(error))
        try:
            if errors:
                # Recovery payloads survive an external catalog conflict;
                # unaltered success receipts are still removed independently.
                for path in tuple(owned.records):
                    if path.parent == output:
                        try:
                            owned.remove(path)
                        except BaseException as error:
                            errors.append(str(error))
            else:
                owned.remove_all()
        except BaseException as error:
            errors.append(str(error))
        if errors:
            raise ValueError('; '.join(errors))

    def final_check():
        if failure_started:
            return
        for path,digest in tuple(input_pins.items()):
            checked(path, digest)
        owned.final_check()
        if originals:
            if args.mode == 'apply' and journal is not None:
                journal.final_check()
                n.historical_view(ROOT, after_data)
                journal.final_check()
            else:
                check_state(ROOT, originals, identities)
        # History replay must not be able to change outputs unnoticed.
        owned.final_check()
        for path,digest in tuple(input_pins.items()):
            checked(path, digest)

    context = r.review_files if args.cohort == 'r' else r.review_context
    with context(spec['reconciler_sha'], on_exit_failure=cleanup, final_consumer_check=final_check) as (review, files):
        def read(path, digest):
            path = Path(path)
            require(path not in input_pins or input_pins[path] == digest, 'Consumer pin was rebound')
            files.verify(path, digest)
            raw = checked(path, digest)
            input_pins[path] = digest
            return raw
        for path,digest in deps['pins'].items():
            read(path, digest)
        candidate = reproduce(args, deps, review, read)
        runtime_scope_ref = validate_apl_runtime(candidate, review, read, n) if args.cohort == 'apl' else None
        for name in TARGETS:
            originals[name], identities[name] = snapshot(ROOT/name, optional=name == HISTORY)
        if args.mode == 'apply':
            for name,field in zip(TARGETS, ('expected_catalog_sha256','expected_languages_sha256','expected_history_sha256')):
                require(sha(originals[name]) == getattr(args,field), 'Original differs from reviewed preview: '+name)
        after_data, audit, prepared, applied, applied_raw, entry = plan_publication(
            args, deps, candidate, originals, apply_output, runtime_scope_ref)
        if args.mode == 'apply':
            for name,field in zip(TARGETS, ('expected_prepared_catalog_sha256','expected_prepared_languages_sha256','expected_prepared_history_sha256')):
                require(sha(prepared[name]) == getattr(args,field), 'Prepared bytes differ from reviewed preview: '+name)
        output.mkdir(parents=True)
        for name in TARGETS:
            (output/'before'/Path(name).parent).mkdir(parents=True, exist_ok=True)
            (output/'after'/Path(name).parent).mkdir(parents=True, exist_ok=True)
            if originals[name] is None:
                owned.write(output/'before'/(name+'.absent'), b'absent\n')
            else:
                owned.write(output/'before'/name, originals[name])
            owned.write(output/'after'/name, prepared[name])
        if args.mode == 'apply':
            # The receipt is genuine only if the complete transaction and final
            # held-context replay close; cleanup removes it on any failure.
            owned.write(output/'SUCCESS.json', applied_raw)
            journal = Journal(ROOT, writer, originals, identities, prepared)
            journal.apply()
            result = applied
        else:
            result = dict(schema='retained-catalog-guarded-preview-v1', status='preview-ready',
                cohort=args.cohort, originals={name:sha(raw) for name,raw in originals.items()},
                prepared={name:sha(raw) for name,raw in prepared.items()}, audit=audit,
                proposed_apply=entry['success'], catalog_changed=False, native_processes_started=0)
            owned.write(output/'SUCCESS.json', encoded(result))
        final_check()
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort', choices=tuple(COHORTS), required=True)
    parser.add_argument('--mode', choices=('preview','apply'), required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply-output', type=Path)
    for flag in ('tool-sha256','normalization-sha256','candidate-sha256'):
        parser.add_argument('--'+flag, required=True)
    for flag in ('catalog','languages','history','prepared-catalog','prepared-languages','prepared-history'):
        parser.add_argument('--expected-'+flag+'-sha256')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
