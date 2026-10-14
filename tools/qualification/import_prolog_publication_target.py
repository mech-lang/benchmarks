"""Publish the retained Prolog cohort into a separate, exact-byte checkout.

The original importer and evidence reviewers retain their physical roots and
five leases. Only catalog targets and private publication outputs use the new
destination. No benchmark, compiler or runtime probe is launched.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys


EVIDENCE_ROOT = Path('/private/tmp/mech-benchmark-completion')
IMPORTER_REL = 'tools/qualification/import_prolog_remaining.py'
IMPORTER_SHA = '359e5b45c4cf46da235a6f0cd98a84d86759d6398dd5137772a09fc620e1cd35'
ADAPTER_REL = 'tools/qualification/import_prolog_publication_target.py'
PACKET_REL = 'experiments/prolog/full50-remaining-v1'
TARGETS = ('data/benchmarks.json', 'data/languages.json', 'site/src/languages.mjs')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def physical(path, root, *, directory=False):
    """Reject lexical escapes and every symlink, including ancestor components."""
    path, root = Path(path), Path(root)
    require(path.is_absolute() and '..' not in path.parts and path.is_relative_to(root),
            'Path outside declared root: ' + str(path))
    for parent in (*reversed(path.parents), path):
        info = parent.lstat()
        require(not stat.S_ISLNK(info.st_mode), 'Symlinked path: ' + str(parent))
        if parent != path or directory:
            require(stat.S_ISDIR(info.st_mode), 'Non-directory ancestor: ' + str(parent))
        else:
            require(stat.S_ISREG(info.st_mode), 'Nonregular input: ' + str(parent))
    require(path.resolve() == path, 'Nonphysical path: ' + str(path))
    return path


def checked(path, expected, root):
    path = physical(path, root)
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
            'Input replaced while reading: ' + str(path))
    require(type(expected) is str and len(expected) == 64 and digest(raw) == expected,
            'Pinned bytes differ: ' + str(path))
    return raw


def roots(evidence, publication):
    evidence, publication = Path(evidence), Path(publication)
    require(evidence == EVIDENCE_ROOT, 'Original measurement checkout required')
    physical(evidence, evidence, directory=True)
    physical(publication, publication, directory=True)
    require(not evidence.is_relative_to(publication) and not publication.is_relative_to(evidence),
            'Evidence and publication roots must be disjoint')
    return evidence, publication


def load_original(evidence):
    require(Path(evidence) == EVIDENCE_ROOT, 'Original measurement checkout required')
    path = Path(evidence) / IMPORTER_REL
    raw = checked(path, IMPORTER_SHA, evidence)
    spec = importlib.util.spec_from_file_location('prolog_original_target_importer', path)
    old = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), old.__dict__)
    require(all(Path(module.__file__).resolve().parents[2] == evidence
                and getattr(module, 'ROOT', evidence) == evidence
                for module in (old, old.e, old.m, old.l, old.r)),
            'Evidence module root changed')
    require(tuple(old.TARGETS) == TARGETS, 'Original publication target contract changed')
    return old


def collect_publication_links(candidate, refs, evidence):
    """Collect exactly the local source/receipt links converted by the importer."""
    links = {}

    def add(relative, expected):
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == relative,
                'Nonportable publication link')
        require(relative not in TARGETS, 'Evidence link collides with a catalog target')
        require(relative not in links or links[relative] == expected, 'Conflicting publication link pin')
        links[relative] = expected

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if type(value.get('path')) is str and type(value.get('sha256')) is str:
                path = Path(value['path'])
                if path.is_absolute() and path.is_relative_to(evidence):
                    add(path.relative_to(evidence).as_posix(), value['sha256'])
            for item in value.values():
                visit(item)

    visit(candidate)
    for binding in refs.values():
        add(binding['path'], binding['sha256'])
    for source in candidate['files'].values():
        require(digest(source['code'].encode('utf-8')) == source['sha256'], 'Embedded source differs')
        add(source['archive_path'], source['sha256'])
    return links


def verify_links(links, evidence, publication):
    for relative, expected in links.items():
        original = checked(evidence / relative, expected, evidence)
        copied = checked(publication / relative, expected, publication)
        require(copied == original, 'Publication link copy differs: ' + relative)


class OwnedOutput:
    """Exclusive private files; never remove a replacement or unrelated edit."""
    def __init__(self, root, atomic):
        self.root, self.atomic = root, atomic
        self.files, self.directories = {}, {}

    def mkdir(self, path):
        if path in self.directories:
            return
        if path != self.root:
            self.mkdir(path.parent)
        with self.atomic():
            path.mkdir()
            info = path.lstat()
            self.directories[path] = (info.st_dev, info.st_ino)

    def write(self, relative, raw):
        path = self.root / relative
        self.mkdir(path.parent)
        with self.atomic():
            with path.open('xb') as stream:
                info = os.fstat(stream.fileno())
                self.files[path] = ((info.st_dev, info.st_ino), raw, False)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
                self.files[path] = ((info.st_dev, info.st_ino), raw, True)

    def verify(self):
        for path, identity in self.directories.items():
            info = path.lstat()
            require(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == identity,
                    'Private output directory changed: ' + str(path))
        for path, (identity, raw, complete) in self.files.items():
            info = path.lstat()
            require(complete and stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity
                    and path.read_bytes() == raw and path.lstat().st_ino == identity[1],
                    'Private output file changed: ' + str(path))

    def restore(self):
        errors = []
        with self.atomic():
            for path, (identity, raw, complete) in reversed(list(self.files.items())):
                try:
                    for parent in path.parents:
                        if parent in self.directories:
                            info = parent.lstat()
                            require(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == self.directories[parent],
                                    'Private output ancestor changed; preserving: ' + str(parent))
                    info = path.lstat()
                    current = path.read_bytes()
                    require(stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity
                            and (current == raw if complete else raw.startswith(current)),
                            'Private output changed; preserving: ' + str(path))
                    path.unlink()
                    del self.files[path]
                except FileNotFoundError:
                    self.files.pop(path, None)
                except BaseException as error:
                    errors.append(error)
            for path, identity in reversed(list(self.directories.items())):
                try:
                    info = path.lstat()
                    require(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == identity,
                            'Private directory changed; preserving: ' + str(path))
                    path.rmdir()
                    del self.directories[path]
                except FileNotFoundError:
                    self.directories.pop(path, None)
                except BaseException as error:
                    errors.append(error)
        if errors:
            raise BaseExceptionGroup('Private output restoration failed', errors)


def publish(args):
    evidence, publication = roots(args.evidence_root, args.publication_root)
    old = load_original(evidence)
    adapter = evidence / ADAPTER_REL
    require(Path(__file__).resolve() in (adapter, publication / ADAPTER_REL), 'Unexpected adapter source location')
    checked(adapter, args.adapter_sha256, evidence)
    output = Path(args.output)
    require(output.is_absolute() and '..' not in output.parts and not output.exists()
            and not output.is_symlink() and not output.is_relative_to(evidence)
            and not output.is_relative_to(publication), 'Fresh private output outside both checkouts required')
    physical(output.parent, output.parent, directory=True)
    refs = {}
    supplemental = {evidence / IMPORTER_REL: IMPORTER_SHA, adapter: args.adapter_sha256,
                    old.EXPORTER: old.EXPORTER_SHA, old.RELEASE: old.RELEASE_SHA,
                    old.TRAITS: old.TRAITS_SHA}
    for name in ('candidate', 'metadata', 'reconciliation'):
        path = Path(getattr(args, name))
        require(path.is_relative_to(evidence / PACKET_REL) and not path.is_relative_to(evidence / PACKET_REL / 'run-v1'),
                'Publication evidence outside original additive packet')
        expected = getattr(args, name + '_sha256')
        checked(path, expected, evidence)
        supplemental[path] = expected
        refs[name] = old.public_ref(old.e.ref(str(path), expected), evidence)
    refs.update(release=old.public_ref(old.e.ref(str(old.RELEASE), old.RELEASE_SHA), evidence),
                import_controller=dict(path=ADAPTER_REL, sha256=args.adapter_sha256),
                measurement_importer=dict(path=IMPORTER_REL, sha256=IMPORTER_SHA))
    pins = dict(zip(TARGETS, (args.benchmarks_sha256, args.languages_sha256, args.module_sha256)))
    originals, prepared, journal, links, names = {}, {}, [], {}, {}
    owned = OwnedOutput(output, old.atomic_publication)

    def restore():
        errors = []
        for operation in (lambda: old.restore_prepared(publication, prepared, originals, journal), owned.restore):
            try:
                operation()
            except BaseException as error:
                errors.append(error)
        if errors:
            raise BaseExceptionGroup('Publication restoration failed', errors)

    def verify():
        for path, expected in supplemental.items():
            checked(path, expected, evidence)
        for path, identity in names.items():
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity,
                    'Held lease pathname changed')
        verify_links(links, evidence, publication)
        old.verify_written(publication, prepared, journal)
        for name in TARGETS:
            checked(publication / name, digest(prepared[name]) if name in journal else pins[name], publication)
        owned.verify()

    with old.m.review_context(args.reconciliation, args.reconciliation_sha256,
                             on_exit_failure=restore, final_consumer_check=verify) as fresh:
        try:
            leases = (old.l.JOB/'owner.lock', old.l.PRIOR_JOB/'owner.lock',
                      old.l.OLD/'owned-jobs/full90/owner.lock', evidence/'experiments/prolog/prolog-full90.owner.lock', old.r.LOCK)
            names.update({path: (path.stat().st_dev, path.stat().st_ino) for path in leases})
            document = lambda path, expected: old.p.strict_json(checked(path, expected, evidence))
            old.same(document(args.metadata, args.metadata_sha256), fresh, 'Saved metadata did not reproduce')
            review = document(args.reconciliation, args.reconciliation_sha256)
            plan = document(old.l.PLAN, old.l.PLAN_SHA)
            prior = document(old.l.PRIOR/'plan-v1.json', old.l.PRIOR_PLAN_SHA)
            previous = document(*old.l.l.OLD_REFS['plan'])
            def read_raw(path, expected):
                require(fresh['verified_file_pins'].get(path) == expected, 'Unverified publication input')
                return old.e.checked(path, expected)
            candidate = document(args.candidate, args.candidate_sha256)
            rebuilt = old.e.reproduced_candidate(plan, prior, previous, review, fresh, read_raw,
                old.e.ref(str(args.reconciliation), args.reconciliation_sha256),
                old.e.ref(str(args.metadata), args.metadata_sha256))
            old.same(candidate, rebuilt, 'Pinned candidate is not the exact independent export')
            release = document(old.RELEASE, old.RELEASE_SHA)
            originals.update({name: checked(publication/name, expected, publication) for name, expected in pins.items()})
            values, audit = old.build_publication(originals, candidate, release, refs, plan, root=evidence)
            prepared.update(values)
            links.update(collect_publication_links(candidate, refs, evidence))
            traits_relative = old.TRAITS.relative_to(evidence).as_posix()
            require(links.get(traits_relative, old.TRAITS_SHA) == old.TRAITS_SHA, 'Conflicting target traits pin')
            links[traits_relative] = old.TRAITS_SHA
            verify()
            for name, raw in prepared.items():
                owned.write(name, raw)
                owned.write('originals/' + name, originals[name])
            if args.apply:
                old.apply_prepared(publication, prepared, originals, pins, verify, journal)
            verify()
            receipt = dict(audit, applied=args.apply, evidence_root=str(evidence), publication_root=str(publication),
                adapter=dict(path=ADAPTER_REL, sha256=args.adapter_sha256),
                original_importer=dict(path=IMPORTER_REL, sha256=IMPORTER_SHA),
                supplemental_evidence_pins={str(path): expected for path, expected in supplemental.items()},
                copied_publication_links=links, inputs=pins,
                outputs={name: digest(raw) for name, raw in prepared.items()},
                verified_artifact_count=len(fresh['verified_file_pins']),
                evidence_roots_changed=False, historical_receipts_changed=False)
            if args.apply:
                receipt['status'] = 'qualified-saved-cohort-imported'
            owned.write('import-receipt.json', (json.dumps(receipt, indent=2, allow_nan=False)+'\n').encode())
        except BaseException as body_error:
            try:
                restore()
            except BaseException as restoration_error:
                raise BaseExceptionGroup('Publication body and restoration both failed', [body_error, restoration_error])
            raise
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--publication-root', type=Path, required=True)
    for name in ('candidate', 'metadata', 'reconciliation'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    for name in ('adapter', 'benchmarks', 'languages', 'module'):
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    old = load_original(args.evidence_root)
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(old.p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Publication interrupted: ' + str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    receipt = publish(args)
    print(json.dumps({name: receipt[name] for name in ('status', 'applied', 'evidence_root', 'publication_root')}), flush=True)


if __name__ == '__main__':
    main()
