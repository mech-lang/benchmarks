"""Explicit exact-source extensions to the sealed Clojure21 owner proof.

prepare replays saved source/native evidence without a JVM. review is invoked
only after independent approval. project binds the approved extension to current
catalog bytes; browser binding validates saved hashes/counts, never recounts.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKET=Path('experiments/source-normalization/clojure-extensions/v1')
BASE=Path('experiments/source-normalization/clojure-v1')
SUPPLEMENT=Path('experiments/clojure/compact-primitive-v1/source-owner-v1')
PROFILE='nbody:clojure-nbody-compact-hot-aset-v1'
SOURCE='e73abcb37312c1f54fd71e4fbc80042d0581b5e36bc26e06a2d46aebe575ef05'
SUPPORT='ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446'
POLICY='logical-source-owners.clojure-v1'
NATIVE_QUAL='48ea213a06b46d3d6fa54216473cf6991f9897c4865453144d66f6b42048e9f4'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def require(ok,message):
    if not ok:raise ValueError('Invalid Clojure logical extension: '+message)
def read(root,path):return json.loads((root/path).read_bytes())
def ref(root,path):
    raw=(root/path).read_bytes();return dict(path=Path(path).as_posix(),sha256=sha(raw),bytes=len(raw))
def write_once(path,value):
    raw=encoded(value);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():require(path.read_bytes()==raw,'sealed artifact differs: '+str(path))
    else:path.write_bytes(raw)

def source_proof(root=ROOT):
    root=Path(root);review=read(root,BASE/'independent-review.json');scope=review['approved_source_scope']
    tool_path=root/'tools/clojure_logical_source_units.py'
    require(sha(tool_path.read_bytes())==scope['tool_sha256'],'counter drift')
    spec=importlib.util.spec_from_file_location('approved_clojure_extension_counter',tool_path)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    supplemental=read(root,SUPPLEMENT/'qualification.json');inputs=read(root,SUPPLEMENT/'inputs.json')
    native_raw=(root/SUPPLEMENT/'stdout.json').read_bytes();native=json.loads(native_raw)
    process=read(root,SUPPLEMENT/'process.json');terminal=read(root,SUPPLEMENT/'terminal.json')
    require(sha((root/SUPPLEMENT/'qualification.json').read_bytes())==NATIVE_QUAL,'native qualification drift')
    require(supplemental['input_manifest_sha256']==sha((root/SUPPLEMENT/'inputs.json').read_bytes())
        and supplemental['native_output_sha256']==process['stdout_sha256']==sha(native_raw)
        and supplemental['process_receipt_sha256']==sha((root/SUPPLEMENT/'process.json').read_bytes()),'native/input/process chain differs')
    require(process['exit_status']==0 and process['common_lock_inherited'] is True and not process.get('timeout_or_interrupt')
        and (root/SUPPLEMENT/'stderr.bin').read_bytes()==b'' and terminal['status']=='completed-pending-review'
        and process['stderr_sha256']==sha(b'') and terminal['report_sha256']==NATIVE_QUAL
        and terminal['canonical_changed'] is terminal['chart_admission'] is terminal['application_execution'] is False,'native process did not close')
    require(supplemental['analysis_tool_sha256']==scope['tool_sha256'] and supplemental['helper_sha256']==scope['helper_sha256']
        and supplemental['policy_sha256']==scope['policy_sha256'] and supplemental['java_sha256']==tool.JAVA_SHA
        and supplemental['jars']==tool.JAR_PINS,'reviewed parser/counter/policy/runtime differs')
    require(sha((root/BASE/'capture.clj').read_bytes())==scope['helper_sha256']
        and sha((root/BASE/'policy.json').read_bytes())==scope['policy_sha256']
        and sha((root/BASE/'test_replay.py').read_bytes())==scope['tests_sha256'],'sealed helper/policy/tests changed')
    require(native['clojure_version']=='1.12.6' and native['tools_reader_version']=='1.6.0'
        and set(native['jobs'])==set(inputs['jobs'])==set(supplemental['outcomes']),'native source inventory differs')
    jobs=inputs['jobs'];replayed={}
    for key,job in jobs.items():
        require(sha(job['text'].encode())==job['source_sha256'],'source text changed')
        require(native['jobs'][key]['accepted'] is True and native['jobs'][key]['source_sha256']==job['source_sha256']
            and all(native['jobs'][key][flag] is False for flag in ('read_eval','source_evaluated','macroexpanded','custom_data_readers')),'native reader scope differs')
        result=tool.owners(job['text'],tool.source_tree(job['text']),native['jobs'][key])
        require(result==supplemental['outcomes'][key] and result['coverage']['unowned_significant_tokens']==0,'native/source owner replay differs')
        replayed[key]=result
    source_records=[]
    for digest,role,included in ((SOURCE,'application',True),(SUPPORT,'runtime-support',False)):
        key='file:'+digest;result=replayed[key]
        require(result['status']=='native-qualified-exact-source-subset' and result['logical_units']==(63 if included else 18),'exact source count differs')
        source_records.append(dict(source_sha256=digest,job=key,role=role,included_in_application=included,
            logical_units=result['logical_units'],outcome_sha256=sha(encoded(result)),support_line_ranges=[]))
    required=[BASE/'qualification.json',BASE/'inputs.json',BASE/'independent-review.json',BASE/'policy.json',BASE/'capture.clj',BASE/'test_replay.py',
        Path('tools/clojure_logical_source_units.py'),Path('experiments/source-formatting/v1/capture_compact_clojure.py'),
        Path('tools/test_clojure_logical_extensions.py'),
        *[SUPPLEMENT/name for name in ('inputs.json','inputs.edn','qualification.json','stdout.json','stderr.bin','process.json','terminal.json')]]
    artifacts={path.as_posix():ref(root,path) for path in required}
    return dict(schema='clojure-exact-source-owner-extension-proof.v1',status='source-qualified-pending-independent-review',
        extension_id='compact-hot-aset-v1',policy=POLICY,profile=PROFILE,source_records=source_records,
        application_logical_units=63,submitted_logical_units=81,excluded_support_logical_units=18,
        retained_application_loc=109,retained_physical_loc=49,artifacts=artifacts,
        producer=ref(root,Path('tools/clojure_logical_extensions.py')),
        native_qualification_sha256=NATIVE_QUAL,native_jobs_replayed=len(replayed),unowned_significant_tokens=0,
        approved_subset='This one profile and exact application/support partition only; other captured variants remain unadmitted.',
        generic_language_certificate=False,canonical_changed=False,native_processes_executed=0,
        evidence_path=(PACKET/'README.md').as_posix())

def approve(root=ROOT):
    root=Path(root);proof=read(root,PACKET/'proof.json')
    require(proof==source_proof(root),'source qualification drift')
    receipt=dict(schema='clojure-exact-source-owner-extension-review.v1',decision='qualified-exact-source-extension',
        profile=PROFILE,policy=POLICY,proof_sha256=sha(encoded(proof)),producer_sha256=proof['producer']['sha256'],
        application_logical_units=63,submitted_logical_units=81,excluded_support_logical_units=18,
        review_basis='Independent review of exact-source native-reader/counter replay, source/support boundary and immutable sealed21profile policy. No inference from matching count or performance result.',
        generic_language_certificate=False,canonical_changed=False,
        limits=['Exact e73abc application plus unchanged ae37ff support only.','Original21profile proof remains sealed.',
                'Other supplemental variants are not qualified browser profiles by this receipt.','No source execution, macro expansion or new owner-policy version.'])
    write_once(root/PACKET/'independent-review.json',receipt);return receipt

def validate(root=ROOT):
    root=Path(root);proof=read(root,PACKET/'proof.json');review=read(root,PACKET/'independent-review.json')
    require(proof.get('schema')=='clojure-exact-source-owner-extension-proof.v1' and proof.get('policy')==POLICY
        and proof.get('profile')==PROFILE and proof.get('status')=='source-qualified-pending-independent-review'
        and proof.get('generic_language_certificate') is proof.get('canonical_changed') is False
        and proof.get('native_processes_executed')==0 and proof.get('native_qualification_sha256')==NATIVE_QUAL,'wrong proof scope')
    require(review.get('decision')=='qualified-exact-source-extension' and review.get('profile')==PROFILE
        and review.get('policy')==POLICY and review.get('proof_sha256')==sha(encoded(proof))
        and review.get('producer_sha256')==proof['producer']['sha256'],'independent review missing/drifted')
    require(ref(root,Path('tools/clojure_logical_extensions.py'))==proof['producer'],'extension producer drift')
    expected={str(BASE/name) for name in ('qualification.json','inputs.json','independent-review.json','policy.json','capture.clj','test_replay.py')}
    expected|={'tools/clojure_logical_source_units.py','experiments/source-formatting/v1/capture_compact_clojure.py','tools/test_clojure_logical_extensions.py'}
    expected|={str(SUPPLEMENT/name) for name in ('inputs.json','inputs.edn','qualification.json','stdout.json','stderr.bin','process.json','terminal.json')}
    require(set(proof['artifacts'])==expected,'proof artifact inventory differs')
    for path,binding in proof['artifacts'].items():require(ref(root,Path(path))==binding,'proof artifact drift: '+path)
    require(proof['source_records']==[dict(source_sha256=SOURCE,job='file:'+SOURCE,role='application',included_in_application=True,
                logical_units=63,outcome_sha256=proof['source_records'][0]['outcome_sha256'],support_line_ranges=[]),
            dict(source_sha256=SUPPORT,job='file:'+SUPPORT,role='runtime-support',included_in_application=False,
                logical_units=18,outcome_sha256=proof['source_records'][1]['outcome_sha256'],support_line_ranges=[])], 'profile source whitelist differs')
    native=read(root,SUPPLEMENT/'qualification.json');jobs=read(root,SUPPLEMENT/'inputs.json')['jobs']
    for record in proof['source_records']:
        outcome=native['outcomes'][record['job']]
        require(sha(encoded(outcome))==record['outcome_sha256'] and outcome['logical_units']==record['logical_units']
            and outcome['coverage']['unowned_significant_tokens']==0,'saved source outcome differs')
        require(sha(jobs[record['job']]['text'].encode())==record['source_sha256'],'saved source bytes differ')
    require([proof[field] for field in ('application_logical_units','submitted_logical_units','excluded_support_logical_units')]==[63,81,18]
        and [review[field] for field in ('application_logical_units','submitted_logical_units','excluded_support_logical_units')]==[63,81,18],'reviewed scoped counts differ')
    return proof,review

def project(catalog,catalog_raw,root=ROOT):
    root=Path(root);proof,review=validate(root);rows={**catalog.get('program_inventory',{}),**catalog['programs']}
    require(sha((root/'data/benchmarks.json').read_bytes())==sha(catalog_raw),'projection catalog bytes differ')
    base_inputs=read(root,BASE/'inputs.json');base_report=read(root,BASE/'qualification.json')
    base_keys=set(base_inputs['programs'])
    require(len(base_keys)==21 and base_keys==set(base_report['programs'])
        and {key for key,row in rows.items() if row['language']=='clojure'}==base_keys|{PROFILE}
        and PROFILE not in base_keys,'only the reviewed one-profile source inventory extension is permitted')
    base_projection={}
    for key in sorted(base_keys):
        current=rows[key];old=base_inputs['programs'][key];qualified=base_report['programs'][key]
        require(current['loc']==old['retained_loc']==qualified['retained_loc']
            and current.get('physical_loc')==old['retained_physical_loc']
            and current['files']==[part['source_sha256'] for part in old['files']],'old profile identity/count drift')
        for part in old['files']:
            source=catalog['files'][part['source_sha256']];override=current.get('file_roles',{}).get(part['source_sha256'],{})
            override=dict(role=override) if isinstance(override,str) else override
            meta={**source,**override};role=meta.get('role','application');included=role!='runtime-support'
            require(sha(source['code'].encode())==part['source_sha256']
                and meta.get('code',source['code'])==source['code'] and meta.get('sha256',part['source_sha256'])==part['source_sha256']
                and role==part['role'] and included is part['included_in_application']
                and meta.get('included_in_application_loc',included) is included and not meta.get('support_line_ranges'),'old source/role partition drift')
        base_projection[key]=dict(files=old['files'],retained_loc=qualified['retained_loc'],
            application=qualified['application_logical_units'],submitted=qualified['submitted_logical_units'],excluded_support=qualified['excluded_support_logical_units'])
    require(PROFILE in rows,'qualified extension profile has not been admitted')
    row=rows[PROFILE]
    require(row['language']=='clojure' and row['benchmark']=='nbody' and row['files']==[SOURCE,SUPPORT]
        and row['loc']==109 and row['physical_loc']==49,'new exact catalog profile differs')
    for record in proof['source_records']:
        source=catalog['files'][record['source_sha256']];override=row.get('file_roles',{}).get(record['source_sha256'],{})
        override=dict(role=override) if isinstance(override,str) else override
        role=override.get('role',source.get('role','application'));included=role!='runtime-support'
        require(sha(source['code'].encode())==record['source_sha256'] and override.get('code',source['code'])==source['code']
            and override.get('sha256',record['source_sha256'])==record['source_sha256'] and role==record['role']
            and included is record['included_in_application'] and override.get('included_in_application_loc',included) is included
            and not override.get('support_line_ranges',source.get('support_line_ranges',[])),'new source/role partition differs')
    return dict(schema='clojure-logical-extension-catalog-projection.v1',catalog_sha256=sha(catalog_raw),
        base_profiles=base_projection,
        base_inputs_sha256=proof['artifacts'][(BASE/'inputs.json').as_posix()]['sha256'],
        base_report_sha256=proof['artifacts'][(BASE/'qualification.json').as_posix()]['sha256'],
        base_review_sha256=proof['artifacts'][(BASE/'independent-review.json').as_posix()]['sha256'],
        extension_proof=ref(root,PACKET/'proof.json'),extension_review=ref(root,PACKET/'independent-review.json'),
        profiles={PROFILE:dict(status='qualified',application=63,submitted=81,excluded_support=18,policy=POLICY,
            sources=[dict(source_sha256=r['source_sha256'],application_projection_sha256=r['source_sha256'] if r['included_in_application'] else None,
                application=r['logical_units'] if r['included_in_application'] else 0,submitted=r['logical_units'],
                excluded_support=0 if r['included_in_application'] else r['logical_units'],role=r['role'],support_line_ranges=[]) for r in proof['source_records']],
            evidence=dict(report_path=(PACKET/'proof.json').as_posix(),report_sha256=sha(encoded(proof)),
                independent_review_path=(PACKET/'independent-review.json').as_posix(),independent_review_sha256=sha(encoded(review)),
                evidence_path=(PACKET/'README.md').as_posix()))},
        generic_language_certificate=False,partial_coverage=True,canonical_changed=False)

def bind(catalog,catalog_raw,root=ROOT):
    root=Path(root);path=root/PACKET/'projection.json'
    if not path.exists():return None
    expected=project(catalog,catalog_raw,root);require(read(root,PACKET/'projection.json')==expected,'saved current projection drift')
    return expected

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('prepare','review','project','check'));args=parser.parse_args()
    with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.mode=='prepare':
            value=source_proof();write_once(ROOT/PACKET/'proof.json',value)
        elif args.mode=='review':value=approve()
        else:
            raw=(ROOT/'data/benchmarks.json').read_bytes();value=project(json.loads(raw),raw)
            path=ROOT/PACKET/'projection.json'
            if args.mode=='check':require(json.loads(path.read_bytes())==value,'current projection differs')
            else:path.write_bytes(encoded(value))
    print(json.dumps({key:value[key] for key in ('schema','status','decision','application_logical_units','catalog_sha256') if key in value}))
if __name__=='__main__':main()
