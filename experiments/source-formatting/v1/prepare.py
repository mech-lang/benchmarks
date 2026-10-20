"""Prepare exact-source formatter plans; reads/hashes only, starts no process."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CATALOG = ROOT/'data/benchmarks.json'
NIM = ROOT/'experiments/nim/optimization-v1'
DISTRIBUTION = NIM/'.build/nim/nim-2.2.12'
OLD = ROOT/'archive/qualification/nim/records/formatted-nim-plan-v1'
NEW_NIM = 'knucleotide:nim-knucleotide-preencoded-v1'


def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(doc): return (json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def pin(path):
    path = Path(path)
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path.read_bytes()))
def require(ok,message):
    if not ok: raise ValueError(message)

def scopes(catalog,language):
    rows={key:row for key,row in {**catalog.get('program_inventory',{}),**catalog['programs']}.items() if row['language']==language}
    profiles,files={},{}
    for key,row in sorted(rows.items()):
        parts=[]
        for digest in row['files']:
            source=catalog['files'][digest];raw=source['code'].encode();require(sha(raw)==digest,'source drift')
            override=row.get('file_roles',{}).get(digest,{})
            override=dict(role=override) if isinstance(override,str) else override
            meta={**source,**override};role=meta.get('role','application');included=role!='runtime-support'
            require(role in ('application','application-helper','runtime-setup','runtime-support'),'unknown role')
            require(meta.get('included_in_application_loc',included)==included,'contradictory role')
            require(not meta.get('support_line_ranges'),'new embedded formatter partition needs review')
            require(meta.get('code',source['code'])==source['code'] and meta.get('sha256',digest)==digest,'override drift')
            files[digest]=dict(source_sha256=digest,catalog_path=source['path'],name=source['name'],bytes=len(raw),
                future_formatted_output_sha256=None,future_second_pass_sha256=None,future_physical_loc=None,
                future_preservation_receipt_sha256=None,status='not-executed')
            parts.append(dict(source_sha256=digest,role=role,included_in_application=included,support_line_ranges=[]))
        profiles[key]=dict(files=parts,retained_loc=row['loc'],retained_physical_loc=row.get('physical_loc'),
            current_formatted_loc=row.get('formatted_loc'),current_formatted_status=row.get('formatted_loc_status'),
            timing_alias_of=row.get('timing_alias_of'),eligible_for_chart=row.get('eligible_for_chart',True))
    return profiles,files,rows


def main():
    raw=CATALOG.read_bytes();catalog=json.loads(raw)
    common=dict(schema='source-only-formatter-qualification-plan.v1',status='prepared-not-native-qualified',
        catalog_sha256=sha(raw),catalog_profiles=len({**catalog.get('program_inventory',{}),**catalog['programs']}),
        producer=pin(__file__),native_processes_executed=0,formatter_processes_executed=0,
        application_execution=False,macro_expansion=False,compilation_performed=False,chart_admission=False,
        canonical_fields_changed=False,published_sources_changed=False,
        physical_definition='nonblank-noncomment-physical-lines-v1',
        publication='Separate later reviewed additive formatted overlay only; no retained/logical/timing changes.')
    profiles,files,rows=scopes(catalog,'nim')
    restoration=json.loads((NIM/'runtime-restoration.json').read_bytes())
    old_plan=json.loads((OLD/'jobs/actual-plans-v1/cohort-plan.json').read_bytes())
    formatter=old_plan['formatters']['nim'];tool=pin(DISTRIBUTION/'bin/nimpretty')
    require(tool['sha256']==formatter['tool']['sha256'],'restored formatter differs')
    source_pins={}
    config_path=OLD/'jobs/actual-plans-v1/native-formatter-config.json'; config=json.loads(config_path.read_bytes())
    require(sha(config_path.read_bytes())==formatter['config']['sha256'],'formatter configuration differs')
    for path,expected in config['source_pins'].items():
        relative=path.split('/nim/nim-2.2.12/',1)[1];actual=pin(DISTRIBUTION/relative)
        require(actual['sha256']==expected==restoration['checked_distribution_pins'][relative],'formatter source differs')
        source_pins[actual['path']]=expected
    historical={}
    for key,row in rows.items():
        if row.get('formatted_loc_complete') is not True: continue
        entries=[];application=0
        roles={part['source_sha256']:part for part in profiles[key]['files']}
        for evidence in row['formatted_loc_evidence']['files']:
            digest=evidence['published_file'];f=evidence['formatter_evidence']; original=f['output']['path']
            path=ROOT/'archive/validation/loc-normalization/20261013'/original.split('/loc-normalization/20261013/',1)[1]
            output=pin(path);require(output['sha256']==f['output']['sha256'],'historical output drift')
            require(f['input']['sha256']==digest and f['tool']['sha256']==tool['sha256'],'historical source/tool mismatch')
            current_role=roles[digest]
            if current_role['included_in_application']: application+=evidence['physical_loc']
            entries.append(dict(source_sha256=digest,original_evidence_role=evidence['role'],current_role=current_role['role'],
                included_in_application=current_role['included_in_application'],formatted_output=output,
                archived_physical_loc=evidence['physical_loc'],formatter_evidence_sha256=f['receipt']['sha256'],
                process_receipt_sha256=f['process_receipt']['sha256'],version_receipt_sha256=f['version_receipt']['sha256'],
                counter_evidence_sha256=evidence['counter_evidence']['receipt']['sha256']))
        require(application==row['formatted_loc'],'historical application total mismatch')
        historical[key]=dict(application_formatted_loc=application,files=entries)
    require(len(historical)==20 and set(profiles)-set(historical)=={NEW_NIM},'Nim target set changed')
    nim=dict(common,language='nim',target_profiles=[NEW_NIM],profiles=profiles,sources=files,
        coverage=dict(retained_profiles=len(profiles),unique_attached_sources=len(files),already_qualified_profiles=20,new_target_profiles=1),
        runtime=dict(restoration=pin(NIM/'runtime-restoration.json'),version_receipt=pin(NIM/'runtime-version.json'),
            compiler=pin(DISTRIBUTION/'bin/nim'),source_commit=restoration['compiler_source_commit'],
            full_tree_reverification='Required before native execution; preparation only checks selected formatter bytes.'),
        formatter=dict(provider='language-project',tool=tool,expected_version='0.2',expected_version_stdout='0.2\n',
            version_receipt=None,arguments=formatter['arguments'],environment=formatter['environment'],
            config=pin(config_path),source_pins=source_pins,official_sources=formatter['official_sources']),
        current_counter=old_plan['counters']['nim'],historical_counter_modules={k:v for k,v in old_plan['code_modules'].items() if not k.startswith('pygments')},
        historical_counter_vendor='Exact Pygments import closure remains in retained cohort plan; isolate and verify before import.',
        retained_framework={name:pin(ROOT/'archive/validation/loc-normalization/20261013/formatted-loc-v1'/name)
                            for name in ('measure.py','overlay.py','load_evidence.py')},
        historical_plan=pin(OLD/'jobs/actual-plans-v1/cohort-plan.json'),historical_formatted_evidence=historical,
        next_native_requirements=['common timing mutex + owned bounded serial processes','exact formatter --version stdout/stderr',
            'format isolated copy twice; second pass byte identical','original source hash unchanged before/after',
            'native parse-only input/output AST equivalence, excluding positions/comments only; no semantic compiler pipeline',
            'code/literal token preservation or reviewed formatter-specific token delta; parse success alone is insufficient',
            'diagnostic-free exact retained lexical mask physical count, preserving source row boundaries',
            'bind output/AST/token/count/raw process/version/config/tool hashes; fail closed on any missing gate'])
    (HERE/'nim-plan.json').write_bytes(encoded(nim))
    profiles,files,_=scopes(catalog,'clojure')
    clojure=dict(common,language='clojure',profiles=profiles,sources=files,
        coverage=dict(retained_profiles=len(profiles),unique_attached_sources=len(files),already_qualified_profiles=0,new_target_profiles=len(profiles)),
        candidates=[dict(project='zprint',candidate_version='1.3.0',provider='community-project',selected_for_next_design=True,
            version_verified=False,tool_sha256=None,dependency_closure=None,config_sha256=None,
            release='https://github.com/kkinnear/zprint/releases/tag/1.3.0',
            reason='Source-oriented width/layout formatting; exact release/config/dependencies still require restoration and review.'),
          dict(project='cljfmt',candidate_version='0.16.6',provider='community-project',selected_for_next_design=False,
            version_verified=False,tool_sha256=None,dependency_closure=None,config_sha256=None,
            primary_docs='https://github.com/weavejester/cljfmt/blob/0.16.6/README.md',
            reason='Genuine source formatter, but deliberately preserves much input structure; less suitable for packed-form canonical line layout.')],
        native_reader_evidence=pin(ROOT/'experiments/source-normalization/clojure-v1/independent-review.json'),
        admission_blocker='Retained overlay requires provider=language-project; community formatter admission needs explicit provider/schema review, never relabel Clojure core.',
        next_native_requirements=['pin release artifact + all dependencies/licenses; no latest/global installer',
            'isolated empty home/cwd, explicit source-format config; no code config/directive/function execution',
            'no input eval/load/require/macroexpand; helper classpath excludes application source',
            'format each of 22 exact source units twice, byte-identical second pass',
            'lossless concrete code/literal/metadata token sequence invariant; comments explicitly classified',
            'pinned Clojure/tools.reader read-eval false accepts original and output; reader sugar gensyms require structural treatment',
            'count nonblank noncomment physical rows from source nodes, retaining multiline string/docstring code rows',
            '21 mains count as application; shared worker support is submitted/excluded only',
            'missing formatter/provider/partition/preservation proof leaves total unavailable, not logical-owner fallback'])
    (HERE/'clojure-plan.json').write_bytes(encoded(clojure))
    print(json.dumps(dict(status='source-only-prepared',nim=nim['coverage'],clojure=clojure['coverage'],native_processes=0)))

if __name__=='__main__': main()
