"""Add one ordinary builtin binding to the unchanged qualified Prolog counter.

This module starts no process. Native commands returned here must be executed
by an owner holding the common timing mutex and retaining their whole closure.
Numeric projections await that evidence and manual owner review.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GRAMMAR = ROOT/'archive/validation/loc-normalization/20261013/prolog-proposal-v5'
PACKET = ROOT/'experiments/prolog/revcomp-linear-v1/source-counts-v1'
COUNTER_SHA = '6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8'
READER_SHA = 'b48e07039914d448e4f313235f347f4604269d0a9802896f0d019ed3e7c52021'
CANDIDATE_SHA = 'bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322'


def require(value, message):
    if not value:
        raise AssertionError(message)


def load_counter():
    path = GRAMMAR/'foreign_prolog.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == COUNTER_SHA, 'Qualified original counter changed')
    spec = importlib.util.spec_from_file_location('linear_revcomp_original_v5_counter',path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


original = load_counter()


def validate_builtin_metadata(metadata, runtime_home):
    require(metadata['schema'] == 'prolog-linear-loc-builtin-metadata-v1' and
            metadata['version'] == [10,0,2] and metadata['version_data'] == 'swi(10,0,2,[])' and
            metadata['architecture'] == 'arm64-darwin' and metadata['home'] == runtime_home,
            'Unselected builtin metadata runtime')
    expected = dict(module='system',name='string_codes',arity=2,built_in=True,
                    foreign=True,defined=True,meta_predicate=False)
    target = metadata['selected_target']
    require(set(target) == set(expected) and all(type(target[key]) is type(value) and target[key] == value
                                                for key,value in expected.items()),
            'string_codes/2 is not the exact ordinary builtin')


class BuiltinContext(original.BundleContext):
    def __init__(self, packets, metadata, runtime_home):
        validate_builtin_metadata(metadata,runtime_home)
        super().__init__(packets)

    def resolve(self, module, target):
        # Existing local definitions/imports/builtins always win. The extra
        # binding has no meta slots, and no other module/name/arity is admitted.
        existing = super().resolve(module,target)
        if existing is not None:
            return existing
        if target == 'string_codes/2' and (module in self.sources or module == 'system'):
            return 'system','string_codes/2'
        return None


def project(source_bytes, packet, metadata, runtime_home):
    context = BuiltinContext([packet],metadata,runtime_home)
    metric = original.count_prolog(source_bytes,packet,language='prolog',context=context)
    return dict(schema='prolog-linear-source-projection-v1',original_counter_sha256=COUNTER_SHA,
        original_reader_sha256=READER_SHA,additional_ordinary_builtin='system:string_codes/2',
        projection=metric,canonical_LOC_admitted=False,formatted_loc=None,
        source_work_qualified=False,chart_admission=False)


def project_candidate(source_bytes, compiled_source_bytes, packet, metadata, runtime_home, compiled_wam):
    require(type(source_bytes) is bytes and hashlib.sha256(source_bytes).hexdigest() == CANDIDATE_SHA and
            source_bytes == compiled_source_bytes,'Candidate and actual compiler input differ')
    result = project(source_bytes,packet,metadata,runtime_home)
    context = BuiltinContext([packet],metadata,runtime_home)
    require(not context.diagnostics and set(context.sources) == {'clbg_revcomp_linear'},
            'Unexpected candidate authored bundle')
    expected = {module+':'+predicate for module,predicate in context.definitions}
    actual = set(re.findall(r'^(clbg_revcomp_linear:\w+/\d+)$',compiled_wam,re.M))
    require(actual == expected,'Candidate WAM definition inventory differs from original reader')
    text=source_bytes.decode('utf8')
    result['source_sha256']=CANDIDATE_SHA
    result['exact_original_and_compiled_bytes_equal']=True
    result['compiled_predicate_inventory']=sorted(actual)
    result['full_owner_expansions']=[dict(event,original_source=text[event['full_owner_start']:event['full_owner_end']])
        for event in result['projection']['canonical_events']]
    return result


def fixtures():
    header=':- module(m, []).\n'
    rows=[
        ('ordinary',header+'p(S,C) :- string_codes(S,C).\n',4,[]),
        ('system-qualified',header+'p(S,C) :- system:string_codes(S,C).\n',4,[]),
        ('comments',header+"% . :- , ; -> string_codes(fake, goals)\np(S,C) :- string_codes(S,C). /* ! */\n",4,[]),
        ('local-definition',header+'string_codes(_,_).\np(S,C) :- string_codes(S,C).\n',5,[]),
        ('other-module',header+'p(S,C) :- other:string_codes(S,C).\n',None,['prolog-unproved-call-target']),
        ('other-builtin',header+'p(S,C) :- string_chars(S,C).\n',None,['prolog-unproved-call-target']),
        ('hidden-control',header+'p(S) :- string_codes(S,(true,fail)).\n',None,['prolog-hidden-goal-data']),
    ]
    return [dict(id=identity,source_text=text,expected_canonical_loc=count,expected_diagnostic_kinds=diagnostics)
            for identity,text,count,diagnostics in rows]


def reader_command(binary, source):
    require(Path(binary).is_absolute() and Path(source).is_absolute(),'Absolute retained binary/source required')
    return [str(binary),'-q','-f','none','-l',str(GRAMMAR/'scan_source.pl'),
            '-g','prolog_source_scan_v1:main','--',str(source)]


def metadata_command(binary):
    require(Path(binary).is_absolute(),'Absolute retained binary required')
    return [str(binary),'-q','-f','none','-l',str(PACKET/'inspect_targets.pl'),
            '-g','prolog_linear_loc_targets:main','--']


def write_fixtures(directory):
    directory=Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    records=[]
    for row in fixtures():
        path=directory/(row['id']+'.pl')
        raw=row['source_text'].encode('utf8');path.write_bytes(raw)
        records.append(dict(row,source=str(path),source_sha256=hashlib.sha256(raw).hexdigest()))
    manifest=dict(schema='prolog-linear-source-fixtures-v1',fixtures=records,native_executions=0,
        fixtures_qualified=False,canonical_LOC_admitted=False,chart_admission=False)
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Write seven fresh source-only fixtures; no native execution')
    parser.add_argument('--write-fixtures',type=Path,required=True)
    args=parser.parse_args()
    value=write_fixtures(args.write_fixtures)
    print(json.dumps(dict(fixtures=len(value['fixtures']),native_executions=0,canonical_LOC_admitted=False)))
