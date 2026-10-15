"""Use the split primitive completion for the unchanged three work observations.

Only intake and entrypoint metadata change. The frozen controller retains its
identity, diagnostic paths, schedule, observer, capture checks and finalizer.
"""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT/'tools/qualification/rebol_work_observations.py'
ORIGINAL_SHA = '7f8076a5fc83b0343c2fdde021ad0e73833fa3d8c9e4b945f97f39fe926e37e2'
BOUNDED = ROOT/'tools/qualification/rebol_bounded.py'
BOUNDED_SHA = '7a308c92f20c54a039bba87490fa3bbedec332333e106041acb128e4e4ade3b9'
BOUNDED_ADAPTER = ROOT/'tools/qualification/rebol_bounded_remaining.py'
PRIMITIVE_ADAPTER = ROOT/'tools/qualification/rebol_primitive_remaining.py'
PRIMITIVE_ADAPTER_SHA = 'f28c9bbb5ed9a47bf6bd2d912e031312038228b6092e451e58a4e364332a7a4b'
PACKET = ROOT/'experiments/rebol/work-observations-v1/remaining-intake-v1'


def require(value, message):
    if not value:
        raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_small(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve(strict=True) == path, 'Physical absolute source required')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular source required')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        held = os.fstat(stream.fileno())
        require((held.st_dev, held.st_ino) == (before.st_dev, before.st_ino), 'Source replaced before read')
        raw = stream.read(2*1024**2+1)
        require(len(raw) <= 2*1024**2, 'Source exceeds intake bound')
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and (after.st_dev, after.st_ino) == (held.st_dev, held.st_ino),
                'Source replaced during read')
    return raw


def attach(w, bounded_adapter, adapter_ref, bounded_ref, primitive_ref):
    original_load, original_build = w.load, w.build_plan
    require(w.ROOT == ROOT and Path(w.__file__) == ORIGINAL and w.HELPER == BOUNDED
            and PACKET.parent == w.PACKET, 'Frozen work controller identity differs')
    files = w.FILES | {str(path.relative_to(ROOT)) for path in (
        Path(adapter_ref['path']), Path(__file__).with_name('test_rebol_work_remaining.py'), PACKET/'README.md')}
    dependencies = {str(BOUNDED.relative_to(ROOT)): BOUNDED_SHA,
                    str(BOUNDED_ADAPTER.relative_to(ROOT)): bounded_ref['sha256'],
                    str(PRIMITIVE_ADAPTER.relative_to(ROOT)): primitive_ref['sha256']}

    def source_review(value):
        require(value['schema'] == 'rebol-three-work-observations-remaining-source-review-v1'
            and value['status'] == 'independent-source-review-complete-native-observations-pending'
            and value['independent_review'] is True and set(value['files']) == files
            and value['dependencies'] == dependencies
            and value['files'][str(ORIGINAL.relative_to(ROOT))] == ORIGINAL_SHA
            and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))] == adapter_ref['sha256']
            and all(value[key] is False for key in w.GATES), 'Exact additive work source review required')

    def load(raw, path, name):
        if Path(path) == BOUNDED:
            require(digest(raw) == BOUNDED_SHA, 'Original shared149 helper changed before intake')
            r = bounded_adapter.load_controller(bounded_ref['sha256'], primitive_ref['sha256'])
            require(r.ROOT == ROOT and Path(r.__file__) == BOUNDED, 'Original bounded helper identity differs')
            return r
        return original_load(raw, path, name)

    def build_plan(r,p,e,adapter,consumers,inspector,output,primitive_review,bounded_source_review,work_source_review,
                   intake,extension,review,pins,resolutions):
        require(output.is_relative_to(PACKET) and output != PACKET,
                'Fresh output inside the additive work packet required')
        value = original_build(r,p,e,adapter,consumers,inspector,output,primitive_review,bounded_source_review,
                               work_source_review,intake,extension,review,pins,resolutions)
        value.update(intake_adapter=dict(adapter_ref), bounded_intake_adapter=dict(bounded_ref),
                     primitive_intake_adapter=dict(primitive_ref), entrypoint=adapter_ref['path'])
        return value

    w.source_review, w.load, w.build_plan = source_review, load, build_plan
    return w


def load_controller(expected, bounded_expected, primitive_expected):
    require(primitive_expected == PRIMITIVE_ADAPTER_SHA, 'Exact reviewed remaining16 adapter required')
    raw = read_small(ORIGINAL)
    require(digest(raw) == ORIGINAL_SHA, 'Frozen work controller changed')
    w = types.ModuleType('rebol_original_work_observations')
    w.__file__ = str(ORIGINAL)
    exec(compile(raw, str(ORIGINAL), 'exec'), w.__dict__)
    own = Path(__file__).resolve()
    adapter_ref = w.ref(str(own), expected)
    bounded_ref = w.ref(str(BOUNDED_ADAPTER), bounded_expected)
    primitive_ref = w.ref(str(PRIMITIVE_ADAPTER), primitive_expected)
    require(digest(read_small(own)) == expected, 'Work intake adapter changed')
    raw = read_small(BOUNDED_ADAPTER)
    require(digest(raw) == bounded_expected, 'Bounded intake adapter changed')
    require(digest(read_small(PRIMITIVE_ADAPTER)) == primitive_expected, 'Primitive intake adapter changed')
    bounded_adapter = w.load(raw, BOUNDED_ADAPTER, 'rebol_work_remaining_shared149')
    return attach(w, bounded_adapter, adapter_ref, bounded_ref, primitive_ref)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--adapter-sha256', required=True)
    parser.add_argument('--bounded-adapter-sha256', required=True)
    parser.add_argument('--primitive-adapter-sha256', required=True)
    args, remaining = parser.parse_known_args()
    controller = load_controller(args.adapter_sha256, args.bounded_adapter_sha256, args.primitive_adapter_sha256)
    sys.argv = [str(ORIGINAL), *remaining]
    controller.main()


if __name__ == '__main__':
    main()
