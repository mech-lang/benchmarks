"""Reproduce the closed six-process APL tree evidence into a fresh candidate.

Every future plan/result and reviewed new-source digest is an explicit input.
No native command runs, and no source-review draft can satisfy the file phase.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/apl/binarytrees-workspace-v1/full6-v1'
WRITER = ROOT/'tools/qualification/import_uiua_fann.py'
WRITER_SHA = 'f57246c5ffb5d4c32f9dfb661f5e23c1e210c184aeb9145ea2a79f276b7e0a16'
PUBLICATION = ROOT/'tools/qualification/apl_workspace_publication.py'
RECONCILER = ROOT/'tools/qualification/apl_workspace_reconcile.py'


def require(value, message):
    if not value:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def snapshot(path, optional=False):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path, 'Physical file required')
    try:
        before = path.lstat()
    except FileNotFoundError:
        require(optional, 'Required file is absent: '+str(path))
        return None, None
    require(stat.S_ISREG(before.st_mode), 'Regular file required: '+str(path))
    fd = os.open(path, os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(stream.fileno())
        require((held.st_dev,held.st_ino) == (before.st_dev,before.st_ino), 'Input replaced before read')
        raw = stream.read()
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and
                (held.st_dev,held.st_ino,held.st_size,held.st_mtime_ns) ==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'Input changed during read')
    return raw, (held.st_dev,held.st_ino)


def checked(path, expected):
    require(type(expected) is str and len(expected) == 64 and all(c in '0123456789abcdef' for c in expected),
            'Explicit reviewed SHA256 required')
    raw, _ = snapshot(path)
    require(sha(raw) == expected, 'Pinned bytes differ: '+str(path))
    return raw


def module(path, expected):
    raw = checked(path, expected)
    spec = importlib.util.spec_from_file_location('apl_tree_'+path.stem, path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value


def safe_writer():
    original = module(WRITER, WRITER_SHA)
    class OwnedFiles(original.OwnedFiles):
        def write(self,path,raw):
            previous = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
            try:
                return super().write(path,raw)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,previous)

        def remove(self, path):
            path = Path(path)
            if path not in self.records:
                return
            raw, identity = snapshot(path, optional=True)
            if raw is None:
                self.records.pop(path, None)
                return
            owned, expected, complete = self.records[path]
            require(identity == owned and (raw == expected if complete else expected.startswith(raw)),
                    'Owned output changed; preserving '+str(path))
            path.unlink(); self.records.pop(path)

        def final_check(self):
            for path,(identity,raw,complete) in tuple(self.records.items()):
                actual, named = snapshot(path)
                require(complete and named == identity and actual == raw, 'Owned output changed before closure')
    return SimpleNamespace(OwnedFiles=OwnedFiles)


def refs(args):
    return {name:dict(path=str(getattr(args,name)), sha256=getattr(args,name+'_sha256'))
            for name in ('plan','report','terminal','durable_terminal')}


def context(r, args, **callbacks):
    values = refs(args)
    return r.review_context(values['plan'], values['report'], values['terminal'], args.producer_sha256,
                            values['durable_terminal'], args.reconciler_sha256, **callbacks)


def reproduce(p, review, read, reconciliation_ref, consumer_sources):
    """Only direct publication inputs are read here; physical maps stay private."""
    def document(ref):
        public = p.public_ref(ref)
        return json.loads(read(ROOT/public['path'], public['sha256']))
    counts = document(review['source_counts'])
    work = document(review['source_work'])
    require(counts == review['qualified_source_counts'] and work == review['qualified_source_work'],
            'Reconciler qualification payload changed')
    runtime = document(p.RUNTIME_REF)
    # Reuse the exact image's static metadata. Preserve the original receipt's
    # eleven-profile scope and all its original bytes.
    for name, expected in runtime['required_inherited_pins'].items():
        require(review['verified_file_pins'].get(name) == expected, 'Runtime prerequisite absent from independent review')
    source_bytes = {digest:read(ROOT/path,digest) for path,digest,_,_ in p.BUNDLE}
    references = dict(report=p.public_ref(review['report']), source_counts=p.public_ref(review['source_counts']),
        source_work=p.public_ref(review['source_work']), runtime_metadata_basis=copy.deepcopy(p.RUNTIME_REF),
        reconciliation=p.public_ref(reconciliation_ref), consumer_sources=copy.deepcopy(consumer_sources),
        native_cohort={name:p.public_ref(ref) for name,ref in review['references'].items()})
    return p.build_candidate(review, source_bytes, counts, work, runtime, references)


def source_refs(args):
    return {name:dict(path=str(path.relative_to(ROOT)), sha256=expected) for name,path,expected in (
        ('exporter',Path(__file__).resolve(),args.tool_sha256),
        ('publication',PUBLICATION,args.publication_sha256),('reconciler',RECONCILER,args.reconciler_sha256))}


def export(args):
    own = Path(__file__).resolve()
    checked(own,args.tool_sha256)
    p,r = module(PUBLICATION,args.publication_sha256),module(RECONCILER,args.reconciler_sha256)
    owner = safe_writer().OwnedFiles()
    output = args.output
    require(output.is_absolute() and output.resolve() == output and output.is_relative_to(PACKET/'publication')
            and not os.path.lexists(output), 'Fresh physical publication evidence directory required')
    pins = {own:args.tool_sha256,PUBLICATION:args.publication_sha256,RECONCILER:args.reconciler_sha256,WRITER:WRITER_SHA}
    def final():
        for path,expected in pins.items():
            checked(path,expected)
        owner.final_check()
    try:
        with context(r,args,on_exit_failure=owner.remove_all,final_consumer_check=final) as (review,files):
            def read(path,expected):
                files.verify(path,expected)
                return checked(path,expected)
            for path,expected in pins.items():
                read(path,expected)
            output.mkdir(parents=True)
            raw_review = encoded(review)
            owner.write(output/'reconciliation.json',raw_review)
            review_ref = dict(path=str(output/'reconciliation.json'),sha256=sha(raw_review))
            candidate = reproduce(p,review,read,review_ref,source_refs(args))
            raw = encoded(candidate)
            owner.write(output/'candidate.json',raw)
    except BaseException as error:
        try:
            owner.remove_all()
        except BaseException as cleanup:
            raise BaseExceptionGroup('APL candidate and cleanup failed',[error,cleanup])
        raise
    print(json.dumps(dict(candidate=str(output/'candidate.json'),sha256=sha(raw),native_runs=0,chart_admission=False)))


def evidence_arguments(parser):
    for name in ('plan','report','terminal','durable-terminal'):
        parser.add_argument('--'+name,type=Path,required=True)
        parser.add_argument('--'+name+'-sha256',required=True)
    for name in ('producer','reconciler','publication'):
        parser.add_argument('--'+name+'-sha256',required=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    evidence_arguments(parser)
    parser.add_argument('--tool-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Use retained Python -I -S -B')
    def interrupted(signum,frame):
        raise KeyboardInterrupt('APL candidate interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
        signal.signal(sig,interrupted)
    export(args)


if __name__ == '__main__':
    main()
