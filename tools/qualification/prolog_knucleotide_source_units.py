"""Exact atom_string binding added to the frozen Prolog owner counter.

Consumes native read_term packets and metadata; never starts a process.
All projections remain unadmitted until independent actual-owner review.
"""
import hashlib
import importlib.util
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
GRAMMAR=ROOT/'archive/validation/loc-normalization/20261013/prolog-proposal-v5'
COUNTER_SHA='6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8'
READER_SHA='b48e07039914d448e4f313235f347f4604269d0a9802896f0d019ed3e7c52021'
SOURCE_SHA='b3f524485ccfc29204efecc2f0da47b91b7a63041f4591512ecb2af844ade1e6'
HELPERS={'clbg_io.pl':'bc6361457988de3b8d7dbce526bf738f0268e96e1c7bb59c35bb4798c71ebdb3',
         'clbg_records.pl':'efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19'}


def require(value,message):
    if not value:raise AssertionError(message)


def load_counter():
    path=GRAMMAR/'foreign_prolog.py';raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==COUNTER_SHA,'Frozen counter changed')
    spec=importlib.util.spec_from_file_location('knucleotide_original_counter',path)
    result=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),result.__dict__)
    return result


original=load_counter()


def validate_metadata(metadata,home):
    require(metadata['schema']=='prolog-knucleotide-loc-builtin-metadata-v1' and
            metadata['version']==[10,0,2] and metadata['version_data']=='swi(10,0,2,[])' and
            metadata['architecture']=='arm64-darwin' and metadata['home']==home,'Wrong builtin runtime')
    expected=dict(module='system',name='atom_string',arity=2,built_in=True,
                  foreign=True,defined=True,meta_predicate=False)
    target=metadata['selected_target']
    require(set(target)==set(expected) and all(type(target[k]) is type(v) and target[k]==v
            for k,v in expected.items()),'Unproved ordinary atom_string/2 binding')


class BuiltinContext(original.BundleContext):
    def __init__(self,packets,metadata,home):
        validate_metadata(metadata,home)
        super().__init__(packets)

    def resolve(self,module,target):
        found=super().resolve(module,target)
        if found is not None:return found
        if target=='atom_string/2' and (module in self.sources or module=='system'):
            return 'system','atom_string/2'
        return None


def fixtures():
    header=':- module(m, []).\n'
    rows=[('ordinary',header+'p(A,S) :- atom_string(A,S).\n',4,[]),
          ('system-qualified',header+'p(A,S) :- system:atom_string(A,S).\n',4,[]),
          ('comments',header+'% atom_string(fake, goals).\np(A,S) :- atom_string(A,S). /* ! */\n',4,[]),
          ('local-definition',header+'atom_string(_,_).\np(A,S) :- atom_string(A,S).\n',5,[]),
          ('other-module',header+'p(A,S) :- other:atom_string(A,S).\n',None,['prolog-unproved-call-target']),
          ('other-builtin',header+'p(A,S) :- atom_chars(A,S).\n',None,['prolog-unproved-call-target']),
          ('hidden-control',header+'p(A) :- atom_string(A,(true,fail)).\n',None,['prolog-hidden-goal-data'])]
    return [dict(id=identity,source_text=text,expected_canonical_loc=count,expected_diagnostic_kinds=issues)
            for identity,text,count,issues in rows]


def project_fixture(packet,metadata,home,row):
    require(packet['source_text']==row['source_text'],'Fixture reader bytes differ')
    context=BuiltinContext([packet],metadata,home)
    metric=original.count_prolog(row['source_text'].encode(),packet,language='prolog',context=context)
    require(metric['normalized_loc']==row['expected_canonical_loc'] and
            [i['kind'] for i in metric['diagnostics']]==row['expected_diagnostic_kinds'],
            'Source fixture projection differs')
    if row['id']=='local-definition':
        calls=[e for e in metric['canonical_events'] if e['kind']=='call']
        require(len(calls)==1 and tuple(calls[0]['resolved_target'])==('m','atom_string/2'),
                'Local definition must shadow builtin')
    return metric


def project_bundle(packets,source_bytes,compiled_bytes,metadata,home,wam):
    require(len(packets)==len(source_bytes)==len(compiled_bytes)==3,'Expected main plus two helpers')
    context=BuiltinContext(packets,metadata,home)
    require(not context.diagnostics and set(context.sources)=={'clbg_knucleotide','clbg_io','clbg_records'},
            'Authored bundle unresolved')
    expected={module+':'+predicate for module,predicate in context.definitions}
    actual=set(re.findall(r'^(clbg_(?:knucleotide|io|records):\w+/\d+)$',wam,re.M))
    require(actual==expected,'WAM predicate inventory differs from exact reader bundle')
    outputs=[]
    for packet,raw,compiled in zip(packets,source_bytes,compiled_bytes):
        name=Path(packet['source']).name
        expected_sha=SOURCE_SHA if name in ('compact.pl','optimized.pl') else HELPERS.get(name)
        require(expected_sha is not None and raw==compiled and packet['source_text'].encode()==raw and
                hashlib.sha256(raw).hexdigest()==expected_sha,'Original/compiled/reader source differs')
        metric=original.count_prolog(raw,packet,language='prolog',context=context)
        require(metric['diagnostics']==[] and type(metric['normalized_loc']) is int,'Unresolved source owner')
        text=raw.decode('utf8')
        outputs.append(dict(source=packet['source'],source_sha256=expected_sha,projection=metric,
            full_owner_expansions=[dict(e,original_source=text[e['full_owner_start']:e['full_owner_end']])
                                   for e in metric['canonical_events']]))
    return dict(schema='prolog-knucleotide-source-projection-v1',files=outputs,
        canonical_loc=sum(x['projection']['normalized_loc'] for x in outputs),
        physical_loc=sum(x['projection']['physical_loc'] for x in outputs),formatted_loc=None,
        compiled_predicate_inventory=sorted(actual),original_counter_sha256=COUNTER_SHA,
        original_reader_sha256=READER_SHA,additional_ordinary_builtin='system:atom_string/2',
        canonical_LOC_admitted=False,source_work_qualified=False,chart_admission=False)
