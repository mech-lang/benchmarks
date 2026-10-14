"""Export, preview or apply the retained Uiua fannkuch v5 admission.

Every mode independently reproduces the same closed study and holds the common
mutex through output creation and final evidence checks. Apply additionally
requires the exact input and prepared-output digests from a reviewed preview.
No native program, benchmark or measurement producer is executed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/uiua/fann-v5-publication-v1'
TARGETS = ('data/benchmarks.json','data/languages.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode('utf-8')


def checked(path, digest):
    require(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
            'Explicit SHA-256 required')
    raw = Path(path).read_bytes()
    require(sha(raw) == digest,'Pinned file changed: '+str(path))
    return raw


def module(name, path, digest):
    raw = checked(path,digest)
    spec = importlib.util.spec_from_file_location(name,path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),result.__dict__)
    return result


class OwnedFiles:
    """Only remove still-owned output; preserve unexpected external changes."""
    def __init__(self):
        self.records = {}

    def write(self, path, raw):
        path = Path(path)
        with path.open('xb') as stream:
            stat = os.fstat(stream.fileno())
            self.records[path] = ((stat.st_dev,stat.st_ino),raw,False)
            try:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
                self.records[path] = ((stat.st_dev,stat.st_ino),raw,True)
            except BaseException:
                # The descriptor closes before the cleanup reads its bytes.
                raise

    def remove(self, path):
        path = Path(path)
        record = self.records.get(path)
        if record is None or not path.exists():
            return
        identity, expected, complete = record
        stat = path.stat()
        require((stat.st_dev,stat.st_ino) == identity,'Owned output inode changed: '+str(path))
        actual = path.read_bytes()
        require(actual == expected if complete else expected.startswith(actual),
                'Owned output changed externally: '+str(path))
        path.unlink()
        self.records.pop(path,None)

    def remove_all(self):
        errors = []
        for path in list(self.records):
            try:
                self.remove(path)
            except BaseException as error:
                errors.append(str(error))
        if errors:
            raise ValueError('; '.join(errors))

    def final_check(self):
        for path,(identity,expected,complete) in tuple(self.records.items()):
            require(complete,'Owned output was not fully written: '+str(path))
            stat = path.stat()
            require((stat.st_dev,stat.st_ino) == identity and path.read_bytes() == expected,
                    'Owned output changed before final closure: '+str(path))


def replace_targets(root, originals, prepared, replaced):
    for name in TARGETS:
        path = root/name
        require(path.read_bytes() == originals[name],'Catalog changed before apply: '+name)
        temporary = path.with_name(path.name+'.uiua-fann-import.tmp')
        owner = OwnedFiles()
        try:
            owner.write(temporary,prepared[name])
            require(path.read_bytes() == originals[name],'Catalog changed during prepare: '+name)
            temporary.replace(path)
            replaced.append(name)
            owner.records.clear()
        finally:
            owner.remove_all()


def rollback(root, originals, prepared, replaced):
    errors = []
    for name in reversed(replaced):
        path = root/name
        try:
            actual = path.read_bytes()
        except BaseException as error:
            errors.append(str(error))
            continue
        if actual == originals[name]:
            continue
        if actual != prepared[name]:
            errors.append('Preserved externally changed catalog: '+name)
            continue
        temporary = path.with_name(path.name+'.uiua-fann-rollback.tmp')
        owner = OwnedFiles()
        try:
            owner.write(temporary,originals[name])
            require(path.read_bytes() == prepared[name],'Catalog changed during rollback: '+name)
            temporary.replace(path)
            owner.records.clear()
        except BaseException as error:
            errors.append(str(error))
        finally:
            try:
                owner.remove_all()
            except BaseException as error:
                errors.append(str(error))
    if errors:
        raise ValueError('; '.join(errors))


def run(args):
    own = Path(__file__).resolve()
    checked(own,args.tool_sha256)
    reconcile_path = own.with_name('uiua_fann_reconcile.py')
    publication_path = own.with_name('uiua_fann_publication.py')
    r = module('uiua_fann_closed_consumer',reconcile_path,args.reconciler_sha256)
    p = module('uiua_fann_publication_transform',publication_path,args.publication_sha256)
    output = args.output.resolve()
    require(output.is_relative_to(PACKET.resolve()) and not output.exists(),
            'Use a fresh output directory inside the Uiua publication packet')
    if args.mode != 'export':
        require(args.candidate is not None and args.candidate_sha256 is not None,
                'Explicit exported candidate and digest required')
        require(args.candidate.resolve().is_relative_to(PACKET.resolve()),'Candidate must be retained in its packet')
    if args.mode == 'apply':
        require(all((args.expected_catalog_sha256,args.expected_languages_sha256,
            args.expected_prepared_catalog_sha256,args.expected_prepared_languages_sha256)),
            'Apply requires all four reviewed preview digests')
    owned = OwnedFiles()
    originals, prepared, replaced = {}, {}, []
    failure_started = False
    def failure_cleanup():
        nonlocal failure_started
        failure_started = True
        errors = []
        # Both operations run even if either finds an external conflict.
        try:
            rollback(ROOT,originals,prepared,replaced)
        except BaseException as error:
            errors.append(str(error))
        try:
            if errors:
                # Keep before/after payloads if an external conflict prevents
                # restoration; remove success/candidate receipts independently.
                for path in list(owned.records):
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
    def final_consumer_check():
        if failure_started:
            return
        owned.final_check()
        if originals:
            expected = prepared if args.mode == 'apply' and len(replaced) == len(TARGETS) else originals
            for name in TARGETS:
                require((ROOT/name).read_bytes() == expected[name],
                        'Catalog changed before final evidence closure: '+name)
    result = None
    with r.review_context(args.reconciler_sha256,on_exit_failure=failure_cleanup,
                          final_consumer_check=final_consumer_check) as (review,files):
        files.verify(own,args.tool_sha256)
        files.verify(publication_path,args.publication_sha256)
        sources = {v:files.read(r.ARCHIVE/'sources'/(v+'.ua'),review['source_counts'][v]['source_sha256'])
                   for v in ('compact','fast')}
        fresh = p.build_candidate(review,sources)
        fresh['consumer_sources'] = {
            name:dict(path=str(path.relative_to(ROOT)),sha256=digest)
            for name,path,digest in [('driver',own,args.tool_sha256),('reconciler',reconcile_path,args.reconciler_sha256),
                                     ('publication',publication_path,args.publication_sha256)]}
        output.mkdir(parents=True)
        try:
            if args.mode == 'export':
                review_raw = encoded(review)
                review_ref = dict(path=str((output/'reconciliation.json').relative_to(ROOT)),sha256=sha(review_raw))
                fresh['reconciliation'] = review_ref
                owned.write(output/'reconciliation.json',review_raw)
                candidate_raw = encoded(fresh)
                owned.write(output/'candidate.json',candidate_raw)
                result = dict(status='candidate-exported',candidate_sha256=sha(candidate_raw),
                    reconciliation_sha256=sha(review_raw),catalog_changed=False)
            else:
                candidate_raw = files.read(args.candidate.resolve(),args.candidate_sha256)
                candidate = r.strict_json(candidate_raw)
                ref = candidate['reconciliation']
                require(not Path(ref['path']).is_absolute() and '..' not in Path(ref['path']).parts,
                        'Unsafe reconciliation reference')
                require((ROOT/ref['path']).resolve().is_relative_to(PACKET.resolve()),
                        'Reconciliation must be retained in its packet')
                saved_review = r.strict_json(files.read(ROOT/ref['path'],ref['sha256']))
                r.same(saved_review,review,'Independent reconciliation changed since export')
                fresh['reconciliation'] = ref
                r.same(candidate,fresh,'Candidate differs from newly reproduced evidence')
                originals = {name:(ROOT/name).read_bytes() for name in TARGETS}
                pins = {name:sha(raw) for name,raw in originals.items()}
                if args.mode == 'apply':
                    require(pins[TARGETS[0]] == args.expected_catalog_sha256 and
                            pins[TARGETS[1]] == args.expected_languages_sha256,'Catalog differs from reviewed preview')
                candidate_ref = dict(path=str(args.candidate.resolve().relative_to(ROOT)),sha256=args.candidate_sha256)
                data,languages,audit = p.build_publication(r.strict_json(originals[TARGETS[0]]),
                    r.strict_json(originals[TARGETS[1]]),candidate,candidate_ref)
                prepared = {TARGETS[0]:encoded(data),TARGETS[1]:encoded(languages)}
                digests = {name:sha(raw) for name,raw in prepared.items()}
                if args.mode == 'apply':
                    require(digests[TARGETS[0]] == args.expected_prepared_catalog_sha256 and
                            digests[TARGETS[1]] == args.expected_prepared_languages_sha256,
                            'Prepared publication differs from reviewed preview')
                for name in TARGETS:
                    # Preserve before/after payloads for independent review and recovery.
                    (output/'before'/Path(name).parent).mkdir(parents=True,exist_ok=True)
                    (output/'after'/Path(name).parent).mkdir(parents=True,exist_ok=True)
                    owned.write(output/'before'/name,originals[name])
                    owned.write(output/'after'/name,prepared[name])
                if args.mode == 'apply':
                    replace_targets(ROOT,originals,prepared,replaced)
                result = dict(status='applied' if args.mode == 'apply' else 'preview-ready',
                    originals=pins,prepared=digests,audit=audit,catalog_changed=args.mode == 'apply')
            owned.write(output/'SUCCESS.json',encoded(result))
        finally:
            final_consumer_check()
    # Final evidence recheck completed while the common lease was still held.
    print(json.dumps(result,indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('export','preview','apply'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    for flag in ('tool-sha256','reconciler-sha256','publication-sha256'):
        parser.add_argument('--'+flag,required=True)
    parser.add_argument('--candidate',type=Path)
    for flag in ('candidate-sha256','expected-catalog-sha256','expected-languages-sha256',
                 'expected-prepared-catalog-sha256','expected-prepared-languages-sha256'):
        parser.add_argument('--'+flag)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
