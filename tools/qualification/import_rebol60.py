"""Preview or apply a reproduced Rebol candidate to a separate checkout.

Only the three current catalog/taxonomy targets can change. Original evidence
modules, physical runtime paths and failed receipts remain unchanged. A new
baseline minimum requires a separate normalization review and is rejected here.
"""
import argparse
import ast
import copy
from contextlib import contextmanager
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import statistics
import sys
import types
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[2]
EXPORTER=ROOT/'tools/qualification/rebol_export60.py'
TRANSACTION=ROOT/'tools/qualification/import_typescript.py'
TRANSACTION_SHA='e8b1945e4b6848cff7953e8eb0d543edd2b7f6d89efc766bf850e065d9e38cf9'
PACKET=ROOT/'experiments/rebol/full60-v1/publication'
FILES=(Path(__file__).resolve(),Path(__file__).with_name('test_import_rebol60.py'),PACKET/'README.md')
TARGETS=('data/benchmarks.json','data/languages.json','site/src/languages.mjs')
META_FIELDS=('platform','runtime','execution','typing','style','memory','note','sources')
KEY='rebol3'
COMMON=Path('/tmp/mech-clbg-timing.lock')
COMMON_RESOLVED=Path('/private/tmp/mech-clbg-timing.lock')


def require(value,message):
    if not value:raise AssertionError(message)


def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def clone(value):return copy.deepcopy(value)
def positive(value):return type(value) in (int,float) and math.isfinite(value) and value>0


def physical(path,*,directory=False):
    path=Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve(strict=True)==path,'Physical path required')
    info=path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),'Regular file or directory required')
    return path


def read_bytes(path):
    path=physical(path);before=path.lstat()
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd)
        require(stat.S_ISREG(held.st_mode) and (held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'File replaced before open')
        raw=stream.read();after=path.lstat()
        require(stat.S_ISREG(after.st_mode) and
            (held.st_dev,held.st_ino,held.st_size,held.st_mtime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'File changed during read')
    return raw


def checked(path,sha):
    require(type(sha) is str and re.fullmatch('[0-9a-f]{64}',sha),'Explicit source/file digest required')
    raw=read_bytes(path);require(digest(raw)==sha,'Pinned bytes differ: '+str(path));return raw


def load(path,sha,name):
    raw=checked(path,sha);module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    require(module.ROOT==ROOT and Path(module.__file__)==path,'Original module root changed')
    return module


class RegularRead:
    """Guard only reads made by the privately loaded, unchanged transaction."""
    def __init__(self,path):self.path=physical(path)
    def read_bytes(self):return read_bytes(self.path)
    def lstat(self):return physical(self.path).lstat()


def load_transaction():
    """Reuse three unchanged functions without importing unrelated evidence."""
    raw=checked(TRANSACTION,TRANSACTION_SHA);tree=ast.parse(raw,filename=str(TRANSACTION))
    names={'apply_prepared','rollback_publication','write_private'}
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    require(len(functions)==3 and {node.name for node in functions}==names,'Frozen transaction function inventory differs')
    old=types.ModuleType('rebol_import_transaction');old.__file__=str(TRANSACTION)
    old.__dict__.update(require=require,regular=RegularRead,checked=checked,os=os)
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(TRANSACTION),'exec'),old.__dict__)
    return old


def source_intake(binding):
    source=json.loads(checked(binding['path'],binding['sha256']))
    require(source['schema']=='rebol-full60-import-source-review-v1'
        and source['status']=='independent-source-review-complete-actual-import-pending'
        and source['independent_review'] is True and source['native_execution'] is source['chart_admission'] is False
        and set(source['files'])=={str(p.relative_to(ROOT)) for p in FILES}
        and set(source['dependencies'])=={str(p.relative_to(ROOT)) for p in (EXPORTER,TRANSACTION)}
        and source['dependencies'][str(TRANSACTION.relative_to(ROOT))]==TRANSACTION_SHA,'Actual importer source review required')
    pins={str(ROOT/name):sha for name,sha in {**source['files'],**source['dependencies']}.items()}
    pins[binding['path']]=binding['sha256']
    for path,sha in pins.items():checked(path,sha)
    e=load(EXPORTER,pins[str(EXPORTER)],'rebol_import_exporter')
    old=load_transaction()
    return e,old,pins


def destination(value):
    require(ROOT==Path('/private/tmp/mech-benchmark-completion'),'Original evidence checkout required')
    path=physical(value,directory=True)
    require(not path.is_relative_to(ROOT) and not ROOT.is_relative_to(path),'Evidence and destination must be disjoint')
    return path


def public_ref(binding,links):
    path=Path(binding['path']);sha=binding['sha256']
    require(path.is_absolute() and '..' not in path.parts and re.fullmatch('[0-9a-f]{64}',sha),'Malformed evidence reference')
    if not path.is_relative_to(ROOT):return clone(binding)
    name=path.relative_to(ROOT).as_posix()
    require(name not in TARGETS and links.get(name,sha)==sha,'Conflicting public link')
    links[name]=sha
    return dict(path=name,sha256=sha)


def public_values(value,links):
    if type(value) is list:return [public_values(v,links) for v in value]
    if type(value) is dict:
        result={k:public_values(v,links) for k,v in value.items()}
        if type(value.get('path')) is str and type(value.get('sha256')) is str:
            result.update(public_ref(value,links))
        return result
    return value


def public_candidate(candidate,refs):
    """Convert source/receipt links; retain physical image and proof provenance."""
    value=clone(candidate);links={}
    for key in ('plan','report','terminal','reconciliation','metadata_review','export_source_review',
                'export_controller','qualification_manifest','cohort_policy_file'):
        value[key]=public_ref(candidate[key],links)
        require(not Path(value[key]['path']).is_absolute(),'Public receipt is outside evidence checkout')
    for source in value['files'].values():
        require(digest(source['code'].encode())==source['sha256'],'Embedded source bytes differ')
        for name in source['source_paths']:
            require(not Path(name).is_absolute() and '..' not in Path(name).parts and name not in TARGETS,'Unsafe public source path')
            public_ref(dict(path=str(ROOT/name),sha256=source['sha256']),links)
        require(source['archive_path'] in source['source_paths'],'Source display path lacks physical provenance')
        source['path']=source['archive_path']
    for row in value['program_inventory'].values():
        for name in ('file_roles','sample_execution_metadata','evidence'):
            row[name]=public_values(row[name],links)
    for control in value['matched_mech_controls'].values():
        for name in ('source_evidence','sample_execution_metadata'):
            control[name]=public_values(control[name],links)
        # Original profile/algorithm paths retain their original namespace.
    value['language_metadata']['evidence']=public_values(value['language_metadata']['evidence'],links)
    public_refs={key:public_ref(binding,links) for key,binding in refs.items()}
    require(all(not Path(v['path']).is_absolute() for v in public_refs.values()),'Publication receipt must be retained')
    return value,public_refs,links


def release_contract(release,metadata):
    require(release['schema']=='rebol-publication-release-metadata-v1'
        and release['status']=='independently-reviewed-release-metadata' and release['independent_review'] is True
        and release['language']==KEY and release['family']==metadata['family'] and release['chart_admission'] is False
        and type(release['release_year']) is int and 1<=release['release_year']<=2100
        and all(type(release[k]) is str and release[k] for k in ('release_name','release_source','release_note','reviewed_on'))
        and release['evidence'],'Reviewed historical release metadata required')
    require(date.fromisoformat(release['reviewed_on']).isoformat()==release['reviewed_on'],'Exact reviewed date required')
    require(metadata['key']==KEY and metadata['execution']==['interpreted'] and metadata['typing']=='dynamic'
        and type(metadata['platform']) is str and metadata['platform'] and metadata['runtime_publication_metadata_qualified'] is True
        and metadata['chart_admission'] is False and metadata['runtime_source_equivalence_proven'] is False
        and all(type(metadata[k]) is str and metadata[k] for k in ('label','family','runtime','note','runtime_policy','memory_policy'))
        and re.fullmatch('#[0-9a-fA-F]{6}',metadata['color'])
        and all(type(metadata[k]) is list and metadata[k] and all(type(x) is str for x in metadata[k])
                for k in ('style','memory','sources')),'Reviewed publication taxonomy incomplete')


def build_publication(originals,candidate,release,refs,plan):
    """Pure append-only transform after exact independently reproduced export."""
    require(candidate['schema']=='rebol-full60-publication-candidate-v1' and candidate['chart_admission'] is False
        and candidate['dataset_files_changed'] is False and type(candidate['native_processes_started']) is int
        and candidate['native_processes_started']==0 and candidate['source_forms']==10
        and candidate['planned_rebol_samples']==30 and candidate['planned_matched_mech_samples']==30
        and candidate['subject_policy']==dict(authored_source_forms_per_workload=1,publication_forms=['compact'],
            duplicate_program_records=0,distinct_optimization_claim=False)
        and candidate['subject_policy']==plan['subject_policy']
        and candidate['cohort_policy_file']==plan['cohort_policy_file']
        and candidate['distinct_subject_bundles']==10 and candidate['counted_physical_sources']==15
        and candidate['timing_aliases']==0 and candidate['formatted_loc_qualified'] is False,'Reproduced Rebol candidate required')
    release_contract(release,candidate['language_metadata'])
    data,languages=(json.loads(originals[name]) for name in TARGETS[:2])
    match=re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',originals[TARGETS[2]].decode(),re.S)
    require(match is not None,'Unexpected taxonomy module syntax');module=json.loads(match[2]);before=clone(data)
    require(KEY not in module and KEY not in languages['languages'] and KEY not in {x['key'] for x in data['languages']}
        and 'rebol_audit' not in data and not any(v['language']==KEY for pool in ('programs','program_inventory')
        for v in data[pool].values()),'Rebol already admitted')
    public,refs,links=public_candidate(candidate,refs);meta=public['language_metadata']
    benches=[b['key'] for b in data['benchmarks']]
    require(len(benches)==10 and set(benches)==set(public['matched_mech_controls'])==set(public['endpoint_proposals'])
        and set(public['program_inventory'])=={b+':rebol-'+b+'-'+f for b in benches for f in ('compact',)},'Exact ten canonical rows required')
    for sha,source in public['files'].items():
        if sha in data['files']:require(data['files'][sha]['code']==source['code'],'Existing source hash collision')
        else:data['files'][sha]=source
    for name in sorted(links):
        require(data['archive_paths'].get(name,name)==name,'Existing archive mapping conflicts')
        data['archive_paths'].setdefault(name,name)
    endpoints={};admitted=[]
    for bench in data['benchmarks']:
        name=bench['key'];rows=[];control=public['matched_mech_controls'][name]
        require(positive(bench['baseline_loc']) and positive(bench['baseline_seconds']),'Invalid retained baseline')
        for form in ('compact',):
            key=name+':rebol-'+name+'-'+form;row=clone(public['program_inventory'][key]);eligible=row['eligible_for_publication_review']
            require(key not in data['program_inventory'] and key not in data['programs'] and type(eligible) is bool
                and eligible is (row['full_workload_qualified'] and control['full_workload_qualified'])
                and row['timing_alias_of'] is None and row['formatted_loc'] is None,'Eligibility or source alias differs')
            require(row['source_alias_of'] is None,'Authored alias differs')
            require(len(row['files'])==(5 if name in ('pidigits','regexredux') else 4)
                and set(row['files'])==set(row['file_roles']) and row['loc']==row['canonical_loc']==
                sum(v['normalized_loc'] for v in row['file_roles'].values()),'Counted complete bundle differs')
            if eligible:
                require(positive(row['seconds']) and row['loc']>=bench['baseline_loc'] and row['seconds']>=bench['baseline_seconds'],
                    'New Rebol minimum requires a separately reviewed normalization: '+key)
            role=next(v for v in row['file_roles'].values() if v['role']=='application');source=role['retained_source']
            row.update(eligible_for_chart=eligible,required_work_validated=True,
                original_admission_policy=dict(candidate_chart_admission=False,program_chart_admission=False,
                    runtime_chart_admission=False,eligible_for_publication_review=eligible),
                chart_admission=dict(independent_candidate=refs['candidate'],reconciliation=refs['reconciliation'],
                    release_metadata=refs['release'],historical_reports_unchanged=True) if eligible else False,
                report=public['report']['path'],report_sha256=public['report']['sha256'],
                loc_report=row['evidence']['counts']['path'],source_report=row['evidence']['counts']['path'],loc_expansions=[],
                formatted_loc_status='unavailable',formatted_loc_complete=False,formatted_loc_evidence=None,
                runtime_policy=meta['runtime_policy'],memory_policy=meta['memory_policy'],runtime_evidence=clone(meta),
                runtime_evidence_scope=clone(meta['runtime_evidence_scope']),runtime_gc_configuration_observed=False,
                gc_numeric_defaults_claimed=False,timing_boundary=plan['timing_policy'],
                timing_summary='Median of three qualified fresh processes per program, including interpreter startup, authored source and extension loading, input, work, output and shutdown. Failed programs retain partial samples without a median.',
                source_provenance='The complete authored application, loader, helper facades and general C extension count once per bundle. Each workload has one measured implementation without copied samples or duplicate program records. Formatted LOC is unavailable.',
                source_provenance_record=dict(source_evidence=source,authored_roles=clone(row['file_roles']),
                    canonical_source_evidence=row['evidence']['counts'],required_work_evidence=row['evidence']['work']),
                source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(source['path']),
                source_link_label='Exact retained source',local_adaptation=True,matched_mech_control=clone(control),
                full_output_validation=[x['validation'] for x in row['sample_execution_metadata']],
                x=row['loc']/bench['baseline_loc'] if eligible else None,y=row['seconds']/bench['baseline_seconds'] if eligible else None,
                formatted_x=None,measured_backend=dict(key='rebol-interpreted',execution='interpreted',label=meta['runtime_policy'],
                    verified=True,evidence=dict(verified=True,report=public['report']['path'],report_sha256=public['report']['sha256'],
                        command=row['command'],source_sha256=list(row['files']),runtime_receipt=dict(verified=True,
                            report=public['metadata_review']['path'],report_sha256=public['metadata_review']['sha256'],
                            field='/execution/0',value='interpreted',value_encoding='literal-saved-string'))))
            row['publication_record']=clone(row);data['program_inventory'][key]=row
            if eligible:rows.append(row)
        fast=min(rows,key=lambda v:(v['seconds'],v['loc'],v['key'])) if rows else None
        small=min(rows,key=lambda v:(v['loc'],v['seconds'],v['key'])) if rows else None
        proposal=dict(fast=fast['key'] if fast else None,small=small['key'] if small else None,
            programs=list(dict.fromkeys([small['key'],fast['key']])) if fast else [],chart_admission=False)
        require(candidate['endpoint_proposals'][name]==proposal,'Independently selected endpoints differ')
        selected=list(dict.fromkeys([fast['key'],small['key']])) if rows else []
        endpoint=dict(fast=proposal['fast'],small=proposal['small'],formatted_fast=None,formatted_small=None,programs=selected)
        endpoints[name]=endpoint
        if rows:
            admitted.append(name);data['programs'].update({k:data['program_inventory'][k] for k in selected})
            bench['groups'].append(dict(language=KEY,label=meta['label'],**endpoint))
    release_fields={k:release[k] for k in ('release_year','release_name','release_source','release_note')}
    language=dict(meta,**release_fields);module[KEY]={k:clone(language[k]) for k in META_FIELDS}
    displayed=sum(v['language']==KEY for v in data['programs'].values())
    data['languages'].append(dict(key=KEY,label=meta['label'],family=meta['family'],color=meta['color'],**release_fields,
        timed_benchmarks=admitted,source_benchmarks=benches,formatted_timed_benchmarks=[],formatted_source_benchmarks=[],
        runtime_family=meta['family'],runtime=meta['runtime'],execution_modes=['interpreted'],typing='dynamic',execution='Interpreted',
        line_style='solid',runtime_policy=meta['runtime_policy'],paradigms=clone(meta['style']),memory_models=clone(meta['memory']),
        classification_note=meta['note'],coverage_note=f'{len(admitted)}/10 workloads admitted; one canonical implementation per workload.'))
    languages['languages'][KEY]=dict(language,displayed_program_count=displayed,
        measurement_basis=[dict(refs['candidate'],status='independently-reproduced-publication-candidate')])
    languages['audited_on']=release['reviewed_on'];languages['scope']=str(len(data['languages']))+' measured variants; all classifications explicit.'
    if admitted:
        aggregate=dict(lang=KEY,label=meta['label'],measured_benchmarks=admitted)
        for kind in ('fast','small'):
            rows=[data['program_inventory'][endpoints[b][kind]] for b in admitted]
            aggregate[kind]={axis:statistics.geometric_mean(row[axis] for row in rows) for axis in ('x','y')}
        data['reference_summary'].append(aggregate)
    data['protocol'][KEY]=meta['runtime_policy']+'. Ten canonical programs use ten authored bundles; 30 planned subject and 30 matched control processes. Canonical counts include the complete helper and extension sources. Failed programs or controls have no chart coordinates; formatted counts are unavailable.'
    for group in data['language_groups']:
        if group['key'] in ('interpreted',*meta['style']):
            require(KEY not in group['languages'],'Duplicate filter membership');group['languages'].append(KEY)
    audit=dict(schema='rebol-full60-publication-import-v1',status='qualified-saved-cohort-prepared',**refs,
        full_report=public['report'],terminal=public['terminal'],endpoints=endpoints,imported_program_inventory=10,
        imported_endpoint_programs=displayed,admitted_workloads=admitted,excluded_profiles=clone(candidate['excluded_profiles']),
        failed_profiles=clone(candidate['failed_profiles']),skipped_slots=clone(candidate['skipped_slots']),
        actual_full_native_processes=candidate['actual_full_native_processes'],qualified_samples=candidate['qualified_samples'],
        planned_rebol_samples=30,planned_matched_mech_samples=30,counted_physical_sources=15,distinct_subject_bundles=10,
        baseline_changed=False,historical_reports_mutated=False,original_producer_chart_flags_preserved=True,
        native_commands=0,benchmark_runs=0,runtime_source_equivalence_proven=False)
    data['rebol_audit']=audit
    for field in ('programs','program_inventory','files','archive_paths'):
        require({k:data[field][k] for k in before[field]}==before[field],'Existing '+field+' changed')
    for old,new in zip(before['benchmarks'],data['benchmarks']):
        require(dict(new,groups=[v for v in new['groups'] if v['language']!=KEY])==old,'Existing workload or baseline changed')
    for field in ('languages','reference_summary','formatted_reference_summary'):
        require(data[field][:len(before[field])]==before[field],'Existing '+field+' changed')
    require({k:v for k,v in data['protocol'].items() if k!=KEY}==before['protocol'],'Existing protocol changed')
    require([dict(g,languages=[x for x in g['languages'] if x!=KEY]) for g in data['language_groups']]==before['language_groups'],
        'Existing filter membership changed')
    allowed={'programs','program_inventory','files','archive_paths','benchmarks','languages','reference_summary','protocol','language_groups'}
    require(all(data[k]==v for k,v in before.items() if k not in allowed),'Unrelated catalog field changed')
    require(set(module)==set(languages['languages'])=={v['key'] for v in data['languages']},'Taxonomy keys differ')
    return {TARGETS[0]:encoded(data),TARGETS[1]:encoded(languages),TARGETS[2]:(match[1]+json.dumps(module,indent=2,allow_nan=False)+match[3]).encode()},audit,links


@contextmanager
def atomic():
    mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
    try:yield
    finally:signal.pthread_sigmask(signal.SIG_SETMASK,mask)


def stop_handler(signum,_frame):raise KeyboardInterrupt('Publication stopped by signal '+str(signum))


def verify_links(links,publication):
    for name,sha in links.items():
        require(checked(ROOT/name,sha)==checked(publication/name,sha),'Copied publication link differs: '+name)


def lease_stat(path):
    path=Path(path)
    if path==COMMON:
        require(path.resolve(strict=True)==COMMON_RESOLVED,'Original common-lock alias changed')
        named=path.lstat();resolved=physical(COMMON_RESOLVED).lstat()
        require(stat.S_ISREG(named.st_mode) and (named.st_dev,named.st_ino)==(resolved.st_dev,resolved.st_ino)
            and named.st_ino==79859134,'Original common-lock named identity changed')
        return named
    return physical(path).lstat()


def named_leases(records):
    for path,identity in records.items():
        info=lease_stat(path)
        require((info.st_dev,info.st_ino)==identity,'Original named lease changed')


def verify_owned(files,directories):
    for path,identity in directories.items():
        info=physical(path,directory=True).lstat()
        require((info.st_dev,info.st_ino)==identity,'Private output directory replaced')
    for path,record in files.items():
        info=physical(path).lstat()
        require(record.get('complete') is True and (info.st_dev,info.st_ino)==record['identity']
            and read_bytes(path)==record['raw'],'Private output replaced or edited')
        info=physical(path).lstat();require((info.st_dev,info.st_ino)==record['identity'],'Private output replaced during read')


def restore_owned(files,directories):
    errors=[]
    with atomic():
        for path,record in reversed(list(files.items())):
            try:
                if not os.path.lexists(path):files.pop(path);continue
                for parent in path.parents:
                    if parent in directories:
                        info=physical(parent,directory=True).lstat()
                        require((info.st_dev,info.st_ino)==directories[parent],'Private ancestor replaced; preserving external bytes')
                info=physical(path).lstat()
                require((info.st_dev,info.st_ino)==record['identity'],'Private file replaced; preserving external bytes')
                raw=read_bytes(path)
                require(raw==record['raw'] if record.get('complete') else record['raw'].startswith(raw),
                    'Private file edited; preserving external bytes')
                info=physical(path).lstat();require((info.st_dev,info.st_ino)==record['identity'],'Private file replaced before cleanup')
                path.unlink();files.pop(path)
            except BaseException as error:errors.append(error)
        for path,identity in reversed(list(directories.items())):
            try:
                info=physical(path,directory=True).lstat()
                require((info.st_dev,info.st_ino)==identity,'Private directory replaced; preserving external bytes')
                path.rmdir();directories.pop(path)
            except FileNotFoundError:directories.pop(path)
            except BaseException as error:errors.append(error)
    if errors:raise BaseExceptionGroup('Owned output cleanup conflicts',errors)


def write_owned(old,output,name,raw,files,directories):
    path=output/name
    require(path.is_relative_to(output),'Private output escape')
    def mkdir(parent):
        if parent in directories:return
        if parent!=output:mkdir(parent.parent)
        parent.mkdir();info=parent.lstat();directories[parent]=(info.st_dev,info.st_ino)
    with atomic():
        mkdir(path.parent)
        # The original writer registers its inode/raw bytes before writing.
        old.write_private(path,raw,files)
        files[path]['complete']=True


def publish(args):
    own_ref=dict(path=str(Path(args.source_review).absolute()),sha256=args.source_review_sha256)
    e,old,extra=source_intake(own_ref)
    publication=destination(args.publication_root);info=publication.stat();root_identity=(info.st_dev,info.st_ino)
    output=Path(args.output).absolute()
    require(output.parent.resolve(strict=True)==output.parent and not os.path.lexists(output)
        and not output.is_relative_to(ROOT) and not output.is_relative_to(publication),'Fresh private output outside both roots required')
    before_pins=dict(zip(TARGETS,(args.benchmarks_sha256,args.languages_sha256,args.module_sha256)))
    preview_pins=dict(zip(TARGETS,(args.prepared_benchmarks_sha256,args.prepared_languages_sha256,args.prepared_module_sha256)))
    require(all(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) for v in before_pins.values()),'Three original target pins required')
    require(all(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) for v in preview_pins.values()) if args.apply
        else all(v is None for v in preview_pins.values()),'Apply requires exactly three reviewed preview-output digests')
    refs={}
    for name in ('candidate','reconciliation','plan','metadata','release'):
        path=Path(getattr(args,name)).absolute();sha=getattr(args,name+'_sha256')
        require(path.is_relative_to(ROOT) and path not in (ROOT/name for name in TARGETS),'Original retained evidence references required')
        extra[str(path)]=sha;refs[name]=dict(path=str(path),sha256=sha)
    release=json.loads(checked(refs['release']['path'],refs['release']['sha256']))
    metadata=json.loads(checked(refs['metadata']['path'],refs['metadata']['sha256']))
    release_contract(release,metadata)
    for evidence in (release['evidence'],metadata['evidence']):
        for binding in evidence.values():
            path=binding['path'];sha=binding['sha256']
            require(extra.get(path,sha)==sha,'Conflicting reviewed metadata evidence');extra[path]=sha
    refs['import_source_review']=own_ref
    refs['import_controller']=dict(path=str(Path(__file__).resolve()),sha256=extra[str(Path(__file__).resolve())])
    originals=prepared=None;links={};lease_names={};journal=[];files={};directories={};applied=False

    def inputs():
        require(destination(publication)==publication,'Destination root changed')
        current=publication.stat();require((current.st_dev,current.st_ino)==root_identity,'Destination root replaced')
        for path,sha in extra.items():checked(path,sha)
        verify_links(links,publication);verify_owned(files,directories);named_leases(lease_names)

    def final_check():
        inputs()
        if originals is not None:
            for name,raw in (prepared if applied else originals).items():
                require(read_bytes(publication/name)==raw,'Publication target changed before final closure: '+name)

    def cleanup():
        nonlocal applied
        errors=[]
        if journal:
            try:
                require(destination(publication)==publication and
                    (publication.stat().st_dev,publication.stat().st_ino)==root_identity,'Restoration destination replaced')
                with atomic():
                    old.rollback_publication(publication,{name:prepared[name] for name in journal},originals)
                    journal.clear();applied=False
            except BaseException as error:errors.append(error)
        try:restore_owned(files,directories)
        except BaseException as error:errors.append(error)
        if errors:raise BaseExceptionGroup('Publication rollback preserved unrelated changes',errors)

    export_args=types.SimpleNamespace(**vars(args));export_args.source_review=args.export_source_review
    export_args.source_review_sha256=args.export_source_review_sha256
    r,export_pins,context=e.export_context(export_args,final_consumer_check=final_check,on_exit_failure=cleanup)
    for path,sha in export_pins.items():
        require(extra.get(path,sha)==sha,'Conflicting exporter dependency');extra[path]=sha
    with e.preserve_failure_cleanup(cleanup):
        with context as review:
            for item in review['qualification']['lease_identities']:
                lease_names[Path(item['path'])]=(item['device'],item['inode'])
            for path in (Path(args.durable_directory)/'owner.lock',r.SUITE,COMMON):
                info=lease_stat(path);identity=(info.st_dev,info.st_ino)
                require(lease_names.get(path,identity)==identity,'Qualification lease identity changed')
                lease_names[path]=identity
            require(lease_names[COMMON][1]==79859134,'Common timing mutex changed')
            final_check()
            plan=json.loads(checked(refs['plan']['path'],refs['plan']['sha256']))
            require(json.loads(checked(refs['reconciliation']['path'],refs['reconciliation']['sha256']))==review,
                'Saved reconciliation differs from held independent replay')
            def read_raw(path,sha):
                require(review['verified_file_pins'].get(path)==sha or extra.get(path)==sha,'Unverified export input')
                return checked(path,sha)
            candidate=json.loads(checked(refs['candidate']['path'],refs['candidate']['sha256']))
            rebuilt=e.build_candidate(r,plan,review,metadata,read_raw)
            rebuilt.update(reconciliation=refs['reconciliation'],metadata_review=refs['metadata'],
                export_source_review=e.ref(Path(args.export_source_review).absolute(),args.export_source_review_sha256),
                export_controller=e.ref(EXPORTER,extra[str(EXPORTER)]))
            require(candidate==rebuilt,'Candidate does not reproduce exactly from independent evidence')
            originals={name:checked(publication/name,sha) for name,sha in before_pins.items()}
            prepared,audit,links=build_publication(originals,candidate,release,refs,plan)
            for binding in release['evidence'].values():public_ref(binding,links)
            if args.apply:require({name:digest(raw) for name,raw in prepared.items()}==preview_pins,'Prepared bytes differ from reviewed preview')
            final_check()
            for name,raw in prepared.items():
                write_owned(old,output,name,raw,files,directories)
                write_owned(old,output,'originals/'+name,originals[name],files,directories)
            inputs()
            if args.apply:
                with atomic():
                    old.apply_prepared(publication,prepared,originals,before_pins,inputs,journal)
                    applied=True
            receipt=dict(audit,applied=applied,status='qualified-saved-cohort-imported' if applied else 'qualified-saved-cohort-prepared',
                evidence_root=str(ROOT),publication_root=str(publication),copied_publication_links=dict(sorted(links.items())),
                inputs=before_pins,outputs={name:digest(raw) for name,raw in prepared.items()},
                reviewed_preview_outputs=preview_pins if args.apply else None,
                import_tool=refs['import_controller'],verified_artifact_count=len(review['verified_file_pins']))
            write_owned(old,output,'import-receipt.json',encoded(receipt),files,directories)
            final_check()
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','reconciliation','plan','metadata','release','source-review','export-source-review'):
        parser.add_argument('--'+name,type=Path,required=True);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--durable-directory',type=Path,required=True)
    parser.add_argument('--publication-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    for name in ('benchmarks','languages','module'):
        parser.add_argument('--'+name+'-sha256',required=True);parser.add_argument('--prepared-'+name+'-sha256')
    args=parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
        and Path(sys.executable).resolve()==Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12').resolve(),
        'Use retained Python -I -S -B')
    for number in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(number,stop_handler)
    receipt=publish(args)
    print(json.dumps({key:receipt[key] for key in ('status','applied','imported_program_inventory','admitted_workloads','baseline_changed')}),flush=True)


if __name__=='__main__':main()
