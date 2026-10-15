"""Import only the qualified APL tree cohort into a separate publication root.

The existing transaction owns both catalogs, history, exact before/after copies
and rollback. Original evidence roots and all six measurement leases stay intact.
"""
import argparse
import copy
from contextlib import contextmanager
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
EXPORTER = ROOT/'tools/qualification/apl_workspace_export.py'
TARGET = ROOT/'tools/qualification/import_retained_publication_target_v2.py'
TARGET_SHA = '204ddfc7e49e36efdbebea1754bf2fc5526f08581b9c1b8483434e1fba5b35f7'
TRANSACTION = ROOT/'tools/qualification/import_retained_catalog.py'
TRANSACTION_SHA = 'd5dd6d091af4cae7dc6dd7dd7e5c6bda402309e2ae7b214ba2b31bed72d54ad4'
HISTORY = ROOT/'tools/normalization_history_apl_trees.py'
PREVIOUS_HISTORY = ROOT/'tools/normalization_history_v2.py'
PREVIOUS_HISTORY_SHA = '67d252c4c8ae7435b7a4f5ac220ca1974436046871618d5898281de4b3b27683'


def require(value,message):
    if not value:
        raise ValueError(message)


def load_exporter(expected):
    # The bootstrap is also nonblocking and rejects symlinks/FIFOs before read.
    require(EXPORTER.resolve() == EXPORTER, 'Original exporter physical path changed')
    before = EXPORTER.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular exporter source required')
    fd = os.open(EXPORTER,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        held = os.fstat(stream.fileno())
        require((held.st_dev,held.st_ino) == (before.st_dev,before.st_ino), 'Exporter replaced before read')
        raw = stream.read()
        after = EXPORTER.lstat()
        require((held.st_dev,held.st_ino,held.st_size,held.st_mtime_ns) ==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'Exporter changed while reading')
    require(hashlib.sha256(raw).hexdigest() == expected, 'Explicit reviewed exporter source digest required')
    spec = importlib.util.spec_from_file_location('apl_tree_import_exporter',EXPORTER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(EXPORTER),'exec'),module.__dict__)
    return module


def publication_links(original, candidate, candidate_ref, pins, evidence, runtime_scope=None):
    """Exclude only the duplicated historical control algorithm path namespace.

    Those entries are relative to the original compiler worktree, not portable
    repository links. The original reconciler still validates their fingerprint.
    The candidate and every counted source/native receipt reference stay intact.
    """
    value = copy.deepcopy(candidate)
    control = value.get('matched_mech_controls',{}).get('binarytrees',{})
    algorithm = control.get('original_profile',{}).get('algorithm')
    if type(algorithm) is dict:
        algorithm.pop('evidence',None)
    return original(value,candidate_ref,pins,evidence,runtime_scope)


def dependencies(args):
    e = load_exporter(args.exporter_sha256)
    require(ROOT == Path('/private/tmp/mech-benchmark-completion') and Path(__file__).resolve() ==
            ROOT/'tools/qualification/import_apl_workspace.py', 'Launch from the unchanged original evidence root')
    e.checked(Path(__file__).resolve(),args.adapter_sha256)
    p = e.module(e.PUBLICATION,args.publication_sha256)
    r = e.module(e.RECONCILER,args.reconciler_sha256)
    old = e.module(TRANSACTION,TRANSACTION_SHA)
    target = e.module(TARGET,TARGET_SHA)
    leaf = e.module(HISTORY,args.normalization_sha256)
    require(leaf.PUBLICATION_SHA == args.publication_sha256 and leaf.PARENT_SHA == PREVIOUS_HISTORY_SHA,
            'Standalone history verifier must bind these same reviewed source bytes')
    n = leaf.attach(e.module(PREVIOUS_HISTORY,PREVIOUS_HISTORY_SHA),p)
    writer = e.safe_writer()
    # Private module instances only: frozen source files and their ROOT values
    # remain unchanged. Existing journal reads gain the same nonblocking guard.
    old.snapshot = e.snapshot
    def history_read(root,name):
        return e.snapshot(Path(root)/n.safe_path(name))[0]
    n.read_bytes = history_read
    pins = {Path(__file__).resolve():args.adapter_sha256, EXPORTER:args.exporter_sha256,
        e.PUBLICATION:args.publication_sha256,e.RECONCILER:args.reconciler_sha256,
        TARGET:TARGET_SHA,TRANSACTION:TRANSACTION_SHA,e.WRITER:e.WRITER_SHA,
        HISTORY:args.normalization_sha256,PREVIOUS_HISTORY:PREVIOUS_HISTORY_SHA}
    # The existing adapter adds its own original source pin. This new router is
    # an additional dependency; neither module's __file__ identity is changed.
    source_pins = {path:digest for path,digest in pins.items() if path != TARGET}
    export_args = SimpleNamespace(**vars(args))
    export_args.tool_sha256 = args.exporter_sha256

    def reproduce(_args,_deps,review,read):
        saved = json.loads(read(args.candidate,args.candidate_sha256))
        p.validate_candidate(saved)
        reconciliation_ref = p.public_ref(saved['reconciliation'])
        require(reconciliation_ref == saved['reconciliation'], 'Portable reconciliation link required')
        require(e.encoded(json.loads(read(ROOT/reconciliation_ref['path'],reconciliation_ref['sha256']))) == e.encoded(review),
                'Saved reconciliation does not match an independent held replay')
        expected = e.reproduce(p,review,read,reconciliation_ref,e.source_refs(export_args))
        require(expected == saved, 'Candidate does not reproduce exactly from closed native evidence')
        return saved

    @contextmanager
    def held(reconciler_sha,**callbacks):
        require(reconciler_sha == args.reconciler_sha256, 'Reconciler source binding differs')
        with e.context(r,args,**callbacks) as result:
            yield result

    spec = dict(packet=p.PACKET,language='apl',audit_key=p.AUDIT,reconciler_sha=args.reconciler_sha256)
    deps = dict(spec=spec,reconciler=SimpleNamespace(review_context=held),publication=p,normalization=n,
                writer=writer,pins=source_pins)
    old.reproduce = reproduce
    target.load_original = lambda actual,evidence:(old,deps)
    original_links = target.publication_links
    target.publication_links = lambda *values,**options:publication_links(original_links,*values,**options)
    return target, e


def publish(args):
    require(args.cohort == 'apl-trees', 'Only the new APL tree cohort is supported')
    target,_ = dependencies(args)
    delegated = SimpleNamespace(**vars(args))
    delegated.adapter_sha256 = TARGET_SHA
    return target.publish(delegated)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--publication-root',type=Path,required=True)
    parser.add_argument('--cohort',choices=('apl-trees',),default='apl-trees')
    parser.add_argument('--mode',choices=('preview','apply'),required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--candidate-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply-output',type=Path)
    for name in ('plan','report','terminal','durable-terminal'):
        parser.add_argument('--'+name,type=Path,required=True)
        parser.add_argument('--'+name+'-sha256',required=True)
    for name in ('producer','reconciler','publication','exporter','normalization','adapter'):
        parser.add_argument('--'+name+'-sha256',required=True)
    for name in ('catalog','languages','history','prepared-catalog','prepared-languages','prepared-history'):
        parser.add_argument('--expected-'+name+'-sha256')
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Use retained Python -I -S -B')
    def interrupted(signum,frame):
        raise KeyboardInterrupt('APL tree import interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
        signal.signal(sig,interrupted)
    print(json.dumps(publish(args),indent=2),flush=True)


if __name__ == '__main__':
    main()
