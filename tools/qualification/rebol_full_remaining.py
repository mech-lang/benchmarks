"""Bind the split-evidence qualification intake to the unchanged full90 producer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/'tools/qualification/rebol_full.py'
ORIGINAL_SHA='62617612fee2c4047e23dd704f1da826349b68fcef270b9919d693238631bca6'
QUALIFIER_SHA='42c8ef4f7fe452c2fd072901237e1a1f6e244267cfd049cc338a45f3d1b548aa'
PACKET=ROOT/'experiments/rebol/full90-v1/remaining-intake-v1'
ADAPTERS={
    'qualification':dict(path=str(ROOT/'tools/qualification/rebol_qualification_remaining.py'),sha256='6aaadb890472d885fab5d84f1ca894c28b793fa261f25fc79f8beeca86e94afd'),
    'work':dict(path=str(ROOT/'tools/qualification/rebol_work_remaining.py'),sha256='c19f3d86c2ee38407b57ec9884173c77c40839a6070f5a29b1fe5848b1bfd31e'),
    'bounded':dict(path=str(ROOT/'tools/qualification/rebol_bounded_remaining.py'),sha256='4b620fdd96d789ba02b119a700c7028fa1f8b84cc2bd83dcd1d88ff494db40f4'),
    'primitive':dict(path=str(ROOT/'tools/qualification/rebol_primitive_remaining.py'),sha256='f28c9bbb5ed9a47bf6bd2d912e031312038228b6092e451e58a4e364332a7a4b')}

def require(value,message):
    if not value:raise AssertionError(message)

def digest(raw):return hashlib.sha256(raw).hexdigest()

def attach(f,adapter_ref,refs):
    old_build=f.build_plan
    files={str(path.relative_to(ROOT)) for path in f.SOURCE_FILES}|{
        str(Path(adapter_ref['path']).relative_to(ROOT)),
        str(Path(__file__).with_name('test_rebol_full_remaining.py').relative_to(ROOT)),
        str((PACKET/'README.md').relative_to(ROOT))}
    dependencies={str(path.relative_to(ROOT)) for path in (f.QUALIFIER,f.HELPERS,f.RECEIPTS)}|{
        str(Path(ref['path']).relative_to(ROOT)) for ref in refs.values()}
    expected_dependencies={str(f.QUALIFIER):QUALIFIER_SHA,str(f.HELPERS):f.HELPERS_SHA,str(f.RECEIPTS):f.RECEIPTS_SHA,
        **{ref['path']:ref['sha256'] for ref in refs.values()}}

    def source_intake(source_ref):
        raw=f.read_bytes(source_ref['path']);require(digest(raw)==source_ref['sha256'],'Independent source review changed')
        review=json.loads(raw)
        require(review['schema']=='rebol-full90-remaining-source-review-v1'
            and review['status']=='independent-source-review-complete-native-timing-pending'
            and review['independent_review'] is True and set(review['files'])==files
            and set(review['dependencies'])==dependencies
            and review['full_timing_qualified'] is False and review['chart_admission'] is False,
            'Actual additive full90 source review required')
        pins={str(ROOT/name):value for name,value in {**review['files'],**review['dependencies']}.items()}
        require(pins[str(ORIGINAL)]==ORIGINAL_SHA and pins[adapter_ref['path']]==adapter_ref['sha256']
            and all(pins[path]==expected for path,expected in expected_dependencies.items()),
            'Frozen producer, timing helpers or qualification adapters changed')
        for name,expected in pins.items():
            f.reference(name,expected);require(f.sha(name)==expected,'Reviewed source changed')
        pins=f.merge(pins,{source_ref['path']:source_ref['sha256']})
        original=f.load(f.QUALIFIER,pins[str(f.QUALIFIER)],'rebol_full90_qualification')
        require(original.ROOT==ROOT and Path(original.__file__)==f.QUALIFIER,'Original qualification proof root changed')
        adapter=f.load(Path(refs['qualification']['path']),refs['qualification']['sha256'],'rebol_full90_qualification_intake')
        qualifier=adapter.load_controller(*(refs[key]['sha256'] for key in ('qualification','work','bounded','primitive')))
        require(qualifier.ROOT==ROOT and Path(qualifier.__file__)==f.QUALIFIER
            and qualifier.intake_adapters==refs,'Adapted qualification identity differs')
        return qualifier,pins

    def build_plan(admission,held,helpers,receipts,output,qualification_ref,source_ref,source_pins):
        require(output.is_absolute() and output.is_relative_to(PACKET) and output!=PACKET
            and output.parent.resolve(strict=True)==output.parent and not os.path.lexists(output),
            'Fresh physical output under additive full90 packet required')
        value=old_build(admission,held,helpers,receipts,output,qualification_ref,source_ref,source_pins)
        value.update(intake_adapter=dict(adapter_ref),qualification_intake_adapter=dict(refs['qualification']),
            work_intake_adapter=dict(refs['work']),bounded_intake_adapter=dict(refs['bounded']),
            primitive_intake_adapter=dict(refs['primitive']),entrypoint=adapter_ref['path'])
        return value

    f.source_intake,f.build_plan=source_intake,build_plan
    return f

def load_controller(expected,qualification_expected,work_expected,bounded_expected,primitive_expected):
    require([qualification_expected,work_expected,bounded_expected,primitive_expected]==
        [ADAPTERS[key]['sha256'] for key in ('qualification','work','bounded','primitive')],
        'Exact reviewed qualification chain required')
    before=ORIGINAL.lstat()
    require(stat.S_ISREG(before.st_mode) and ORIGINAL.resolve()==ORIGINAL,'Physical regular original full90 producer required')
    with os.fdopen(os.open(ORIGINAL,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        current=os.fstat(stream.fileno());require((current.st_dev,current.st_ino)==(before.st_dev,before.st_ino),'Original full90 producer replaced')
        raw=stream.read(2*1024**2+1);require(len(raw)<=2*1024**2 and digest(raw)==ORIGINAL_SHA,'Frozen full90 producer changed')
    f=types.ModuleType('rebol_original_remaining_full90');f.__file__=str(ORIGINAL)
    exec(compile(raw,str(ORIGINAL),'exec'),f.__dict__)
    own=Path(__file__).resolve();adapter_ref=f.reference(own,expected)
    require(digest(f.read_bytes(own))==expected,'Full90 intake adapter changed')
    refs={key:f.reference(value['path'],value['sha256']) for key,value in ADAPTERS.items()}
    for ref in refs.values():require(digest(f.read_bytes(ref['path']))==ref['sha256'],'Qualification adapter changed')
    return attach(f,adapter_ref,refs)

def main():
    parser=argparse.ArgumentParser(add_help=False)
    for name in ('adapter','qualification-adapter','work-adapter','bounded-adapter','primitive-adapter'):
        parser.add_argument('--'+name+'-sha256',required=True)
    args,remaining=parser.parse_known_args()
    f=load_controller(args.adapter_sha256,args.qualification_adapter_sha256,args.work_adapter_sha256,
        args.bounded_adapter_sha256,args.primitive_adapter_sha256)
    previous=sys.argv
    try:sys.argv=[str(ORIGINAL),*remaining];f.main()
    finally:sys.argv=previous

if __name__=='__main__':main()
