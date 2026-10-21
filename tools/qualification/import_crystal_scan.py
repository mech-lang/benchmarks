"""Admit exact reviewed Crystal scan sources using saved evidence only.

No subprocess, compiler, counter, network request or benchmark is started.
Preparation additionally rehashes local ignored runtime artifacts; offline replay
checks their frozen manifests and the archived standard-library source snapshot.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from qualification import import_bqn_knucleotide as shared

BASE = 'experiments/crystal/regex-byte-offsets-v1/'
SCAN = BASE+'scan-v1/'
ADMISSION = BASE+'admission-v1/'
PLAN, RESULTS, PREPARED = [ADMISSION+name+'.json' for name in ('plan','results','prepared')]
SOURCE_REVISION = 'e5176304b4d0ca771137c61cb0affb62f0e46b3e'
CONTROL = 'regexredux:crystal-regexredux-optimized'
VARIANTS = {
    'block-parallel': ('ba9752096484a652b2cea36da8ff21673299774b7fea17b39f412920acd5c773',54,46,CONTROL),
    'inline-parallel': ('49e48b96021f34f55a8aefde780712402f83c38303c8f02216faa5740ee6f1ec',47,41,CONTROL),
    'inline-compact': ('c2f3174388879f0d61b75bc879ad8474e45b2a7903da8326ecf63480762d0e69',32,28,'regexredux:crystal-regexredux-compact'),
}
FROZEN = {
    'review': (BASE+'independent-review-v1.json','9f6cfdaafc5c10d905968f0e5a82df50a87ae8b187c2d412bd201a452f05b2f0'),
    'full_plan': (BASE+'full-v1/plan.json','6df00a899d9b8872a4b6ea699e5be20b51cd906e7112b8cca930742c206a566e'),
    'full': (BASE+'full-v1/run-v1/report.json','a30de30110d3f7159822fbd810feff10cebe884f97e1687bb669773e15c0b6ec'),
    'bounded_plan': (SCAN+'native-plan-v1.json','7cde296c5fa3a27e5e3e488b41190c37266bfc69600251dd57dc10445af61524'),
    'bounded': (SCAN+'native-v1/report.json','61b3baad813d6e87fd9e5d2f12f0e31f852b43841c556ae78c3a8e63227f30e6'),
    'counts': (SCAN+'source-counts-v1/receipt.json','52aeec015c5a11ea2626a8934c9612614ea20908b42acfee22cd33369cab22e1'),
    'stdlib': (ADMISSION+'runtime-source/manifest.json','4e27342156c2e192723cc25f6686b022e37c2b08add0ef41c40eee6af92c1cc5'),
    'relative': (BASE+'full-v1/mech-aot-relative-v1.json','d255f9085c2cd676df32d9229de7872540a0920a877f52ea32233461b6911d6c'),
}
AUTHOR_CONTEXT = dict(tool='OpenAI Codex',model_family='Codex GPT-6',exact_model=None,
                      status='developer-identity-family-only',original_predecessor_model='unverified')
ENV = dict(PATH='/opt/homebrew/bin:/usr/bin:/bin',LC_ALL='C',LANG='C',TZ='UTC',
           UV_THREADPOOL_SIZE='8',CRYSTAL_WORKERS='8',OMP_NUM_THREADS='1',
           OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
OUTPUT_SHA = 'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'
INPUT_SHA = '97197f5957a12f8a859ba7edff6d97994daa18afacd77db21fa68c6f2e447e38'
VERSION = 'experiments/implementation-audit/remaining-v1/native-v1/crystal-version/stdout.bin'
sha, pin, load, require, relative = shared.sha, shared.pin, shared.load, shared.require, shared.relative


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded(value))


def key(variant):
    return 'regexredux:crystal-regexredux-scan-'+variant+'-v1'


def make_plan(root=ROOT):
    refs={name:dict(path=path,sha256=digest) for name,(path,digest) in FROZEN.items()}
    refs.update(importer=pin(root,'tools/qualification/import_crystal_scan.py'),
                shared_helpers=pin(root,'tools/qualification/import_bqn_knucleotide.py'))
    return dict(schema='crystal-scan-admission-plan.v1',evidence=refs,author_context=AUTHOR_CONTEXT,
        source_revision=SOURCE_REVISION,appended_programs=[key(v) for v in VARIANTS],
        historical_measurements_unchanged=True,chart_admission=False,
        scope='Three exact independently reviewed standard-library scan sources; retained application counts only. Uniform logical and native formatter counts remain unavailable.')


def clean(row,quantitative):
    require(row.get('exit_code')==0 and row.get('timed_out') is False
        and row.get('remaining_process_group') is False and row.get('quantitative_benchmark') is quantitative
        and row.get('common_mutex_inherited') is True and row.get('common_mutex_inode')==82961857,
        'Unclean process or changed timing/mutex scope')
    require(type(row.get('elapsed_seconds')) in (int,float) and math.isfinite(row['elapsed_seconds'])
        and row['elapsed_seconds']>0,'Invalid process time')


def stream(evidence,row,name,expected_path,recorded):
    ref=row[name]
    require(relative(evidence.root,ref['path'],recorded)==expected_path,'Wrong stream path/root')
    return evidence.check(dict(ref,path=expected_path)).read_bytes()


def check_full(evidence,plan,report,recorded):
    require(report['status']=='passed-full-process-comparison' and report['full_size_results'] is True
        and report['chart_admission'] is False and report['pins_unchanged'] is True
        and report['lock_identity_unchanged'] is True and report['plan_sha256']==FROZEN['full_plan'][1],
        'Incomplete or wrong full cohort')
    labels=['cr-parent','cr-scan-block-parallel','cr-scan-inline-parallel','cr-scan-inline-compact']
    require(list(plan['commands'])==labels and plan['workload_size']==5000000 and plan['input_bytes']==50833411
        and plan['full_mode_available'] is True and plan['chart_admission'] is False
        and plan['common_mutex_inode']==82961857 and len(plan['cases'])==1,'Wrong source pool/workload')
    case=plan['cases'][0]
    require(case['labels']==labels and case['language']=='crystal'
        and case['input']==recorded+'/experiments/lean4/.build/inputs/n5000000.fasta'
        and plan['pins'][case['input']]==INPUT_SHA,'Wrong full input')
    reference=recorded+'/archive/workloads/regexredux/inputs/output-full.txt'
    require(case['expected']==reference and plan['pins'][reference]==OUTPUT_SHA,'Wrong full reference')
    expected=evidence.check(dict(path='archive/workloads/regexredux/inputs/output-full.txt',sha256=OUTPUT_SHA)).read_bytes()
    require(len(expected)==298,'Wrong full output length')
    rng=random.Random(910317);order=[]
    for number in range(1,4):
        shuffled=labels.copy();rng.shuffle(shuffled)
        order.extend(dict(language='crystal',round=number,label=label) for label in shuffled)
    require(plan['order']==order and [{k:r[k] for k in ('language','round','label')} for r in report['observations']]==order,
            'Missing, duplicate or reordered full observations')
    metadata={label:[] for label in labels}
    for i,row in enumerate(report['observations']):
        directory=f'{i:02d}-'+row['label'];path=BASE+'full-v1/run-v1/'+directory
        require(row['directory']==directory,'Wrong process directory')
        raw=evidence.document(pin(evidence.root,path+'/process.json'));clean(raw,True)
        require(raw['command']==plan['commands'][row['label']] and raw['cwd']==recorded+'/'+BASE+'full-v1/run-v1'
            and raw['stdin']==case['input'] and raw['environment']==ENV
            and raw['elapsed_seconds']==row['seconds'] and raw['maximum_rss_bytes']==row['maximum_rss_bytes'],
            'Changed full process/command/environment/source join')
        require(stream(evidence,raw,'stdout',path+'/stdout.bin',recorded)==expected
            and stream(evidence,raw,'stderr',path+'/stderr.bin',recorded)==b'','Full process output differs')
        metadata[row['label']].append(dict(raw,producer_plan=dict(path=FROZEN['full_plan'][0],sha256=FROZEN['full_plan'][1]),
            producer_report=dict(path=FROZEN['full'][0],sha256=FROZEN['full'][1]),raw_evidence=pin(evidence.root,path+'/process.json'),workload_n=5000000))
    for label,rows in metadata.items():
        values=[r['elapsed_seconds'] for r in rows];summary=report['summary'][label]
        require(len(values)==3 and summary['samples']==values and summary['median_seconds']==statistics.median(values)
            and math.isclose(summary['stdev_seconds'],statistics.stdev(values),rel_tol=1e-14,abs_tol=0)
            and summary['peak_rss_bytes']==max(r['maximum_rss_bytes'] for r in rows),'Stale full aggregates')
    # Power and competing-process captures exist at cohort level, not per sample.
    for name in ('power-source','power-settings','processes-before'):
        path=BASE+'full-v1/run-v1/'+name;raw=evidence.document(pin(evidence.root,path+'/process.json'));clean(raw,True)
        require(stream(evidence,raw,'stderr',path+'/stderr.bin',recorded)==b'','Power/process capture error')
        content=stream(evidence,raw,'stdout',path+'/stdout.bin',recorded)
        if name=='power-source':require(b'AC Power' in content,'Missing AC power')
        if name=='power-settings':require(not any('lowpowermode' in line and line.split()[-1]!='0' for line in content.decode().splitlines()),'Low power mode differs')
    return metadata


def reconcile(root=ROOT,local_artifacts=True):
    root=Path(root);evidence=shared.Evidence(root);plan=load(root/PLAN)
    require(plan==make_plan(root),'Stale admission plan/importer identity')
    docs={name:evidence.document(ref) for name,ref in plan['evidence'].items() if name not in ('importer','shared_helpers')}
    for name in ('importer','shared_helpers'):evidence.check(plan['evidence'][name])
    review,full,protocol=docs['review'],docs['full'],docs['full_plan']
    require(review['status']=='INDEPENDENT-EXACT-SOURCE-RETAINED-POLICY-AND-COHORT-REVIEW-COMPLETE'
        and review['blockers']==[] and review['canonical_admission_approved'] is None
        and review['review_scope']['native_processes_started']==0,'Incomplete independent review')
    suffix='/'+SCAN+'.build/native-v1/block-parallel';binary=protocol['commands']['cr-scan-block-parallel'][0]
    require(binary.endswith(suffix),'Wrong exact recorded binary root');recorded=binary[:-len(suffix)]
    require(recorded and '..' not in Path(recorded).parts and Path(recorded).is_absolute(),'Unsafe recorded root')
    snapshots={item['recorded']['path']:item['archived'] for item in docs['stdlib']['files']}
    require(set(snapshots)=={item['source']['path'] for item in review['stdlib_bindings']},'Wrong standard-library snapshot scope')
    evidence.check(docs['stdlib']['license'])
    for ref in review['evidence']:
        if ref['path'] in snapshots:
            require(snapshots[ref['path']]['sha256']==ref['sha256'],'Library snapshot differs from reviewed build')
            evidence.check(snapshots[ref['path']])
        else:evidence.check(ref)
    # The frozen full plan binds every compiler/distribution/runtime input.
    # Offline replay deliberately does not claim to rehash absent ignored binaries.
    for path,digest in protocol['pins'].items():
        if path.startswith(recorded+'/'):
            rel=relative(root,path,recorded)
            if '/.build/' not in rel:evidence.check(dict(path=rel,sha256=digest))
            elif local_artifacts:require(sha(root/rel)==digest,'Changed local runtime/input: '+rel)
        elif local_artifacts:require(sha(path)==digest,'Changed external runtime: '+path)
    bounded=docs['bounded'];require(bounded['status']=='passed-bounded-outputs-and-invalid-utf8-rejection' and bounded['pins_unchanged'] is True
        and bounded['lock_identity_unchanged'] is True and len(bounded['cases'])==32
        and all(r['passed'] is True for r in bounded['cases']) and bounded['plan_sha256']==FROZEN['bounded_plan'][1],
        'Incomplete bounded output checks')
    require(docs['counts']['counter_or_constants_modified'] is False,'Source counter was changed')
    metadata=check_full(evidence,protocol,full,recorded);programs=[]
    reviewed={r['variant']:r for r in review['reviewed_candidates']}
    compiled={r['variant']:r for r in bounded['compilations']}
    for variant,(digest,loc,physical,parent) in VARIANTS.items():
        owner=reviewed[variant];source=SCAN+'source/'+variant+'.cr';count=evidence.document(owner['retained_policy_count'])
        require(owner['source']==dict(path=source,sha256=digest,bytes=(root/source).stat().st_size)
            and owner['reviewed_retained_application_loc']==loc and owner['reviewed_physical_loc']==physical
            and count['source_sha256']==digest and count['candidate']['normalized_loc']==loc
            and count['candidate']['physical_loc']==physical and count['parent_full_retained_metric_matches'] is True
            and count['application_loc'] is None and count['independent_approval'] is None,
            'Unbound exact-source/retained-count review')
        label='cr-scan-'+variant;build=compiled[variant];buildref=pin(root,SCAN+'native-v1/compile-'+variant+'/process.json')
        raw=evidence.document(buildref);clean(raw,False)
        require(build['source_sha256']==digest and build['binary']==recorded+'/'+SCAN+'.build/native-v1/'+variant
            and protocol['commands'][label]==[build['binary']] and protocol['pins'][build['binary']]==build['binary_sha256']
            and raw['command'][-1]==recorded+'/'+source and raw['command'][-2]==build['binary']
            and raw['command'][1:12]==['build','--release','--no-debug','--no-color','--error-trace','--mcpu','native','--threads','1','--link-flags',raw['command'][11]],
            'Source/build/binary binding differs')
        require(protocol['pins'][raw['command'][0]]==docs['bounded_plan']['pins'][raw['command'][0]],'Compiler identity differs')
        summary=full['summary'][label];programs.append(dict(id=key(variant).split(':',1)[1],key=key(variant),variant=variant,
            parent=parent,parent_source_sha256=count['parent_sha256'],source_sha256=digest,source=source,loc=loc,physical_loc=physical,
            loc_expansions=count['candidate']['expansions'],samples_seconds=summary['samples'],median_seconds=summary['median_seconds'],
            sample_sd_seconds=summary['stdev_seconds'],peak_rss_bytes=summary['peak_rss_bytes'],binary_sha256=build['binary_sha256'],
            command=protocol['commands'][label],build_command=raw['command'],build_evidence=buildref,
            sample_execution_metadata=metadata[label],source_count_review=owner['retained_policy_count'],
            matched_control_speedup=full['summary']['cr-parent']['median_seconds']/summary['median_seconds'],
            time_x_mech_aot=docs['relative']['programs'][label]['median_x_mech_aot']))
    version_path=evidence.check(pin(root,VERSION));version=version_path.read_text()
    require(version.startswith('Crystal 1.21.1 [73ea5c2b1]'),'Wrong compiler version')
    os_path=BASE+'full-v1/runtime-discovery/os-build/stdout.bin';os_text=evidence.check(pin(root,os_path)).read_text()
    return dict(schema='crystal-scan-admission-results.v1',status='RECONCILED',plan=pin(root,PLAN),
        evidence=plan['evidence'],author_context=AUTHOR_CONTEXT,recorded_execution_root=recorded,
        programs=programs,toolchains=dict(crystal=dict(version=version,evidence=pin(root,VERSION))),
        os=os_text,host=dict(scope='Suite Apple M3 runner; exact OS captured, no separate cohort hardware probe.'),
        input=dict(path='experiments/lean4/.build/inputs/n5000000.fasta',bytes=50833411,sha256=INPUT_SHA),
        full_workload_n=5000000,library_pins={p:h for p,h in protocol['pins'].items() if p.startswith('/opt/homebrew/') and '/lib/' in p},
        runtime_environment=ENV,timing_boundary=protocol['sample_scope'],required_work=review['required_work'],
        mech_aot_baseline=docs['relative']['mech_aot_baseline'],matched_control=full['summary']['cr-parent'],
        new_observations=9,matched_control_observations_retained=3,old_profiles_unchanged=True,
        source_size_scope='Approved exact retained Crystal policy only; uniform logical and native formatted metrics unavailable.',
        protocol_limits=review['full_cohort']['protocol_limits'],
        artifacts=[dict(path=p,sha256=h) for p,h in sorted(evidence.fingerprints.items())])


def authorship_record(parent,result,refs):
    record=copy.deepcopy(parent['authorship']);digest=result['source_sha256']
    record.update(kind='ai-adapted',label='AI adapted · retained Crystal implementation',source_sha256=[digest],
        parent_programs=[result['parent']],parent_sources=[dict(program_key=result['parent'],relationship='local predecessor',**r)
            for r in parent['authorship'].get('retained_sources',[])],
        retained_sources=[dict(source_sha256=digest,url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+result['source'])],
        ai=dict(tool=AUTHOR_CONTEXT['tool'],models=[],model_family=AUTHOR_CONTEXT['model_family'],exact_model=None,
            status='family-identified-exact-model-unverified',matched_source_files=[digest],total_source_files=1,
            evidence=[refs['plan'],refs['results'],refs['review']]),
        evidence=[refs[name]['path'] for name in ('plan','results','review')])
    return record


def bound_authorship(data,profile,root=ROOT):
    root=Path(root);results=load(root/RESULTS);refs=dict(results['evidence'],plan=pin(root,PLAN),results=pin(root,RESULTS))
    matches=[r for r in results['programs'] if r['key']==profile.get('key')]
    require(len(matches)==1,'Unbound Crystal source/authorship');r=matches[0];detail=profile.get('source_provenance_record',{})
    require(profile['files']==[r['source_sha256']] and detail.get('source_sha256')==r['source_sha256']
        and detail.get('original_program_key')==r['parent'] and detail.get('admission')==refs['results']
        and detail.get('author_context')==AUTHOR_CONTEXT and results['status']=='RECONCILED'
        and sha(root/r['source'])==r['source_sha256']
        and hashlib.sha256(data['files'][r['source_sha256']]['code'].encode()).hexdigest()==r['source_sha256'],
        'Unbound Crystal source/authorship')
    shared.Evidence(root).check(refs['review'])
    return authorship_record(data['programs'][r['parent']],r,refs)


def append_catalog(before,root=ROOT):
    root=Path(root);results=load(root/RESULTS)
    require(results==reconcile(root,local_artifacts=False),'Stale Crystal admission results')
    require('crystal_scan_audit' not in before and all(key(v) not in before['programs'] for v in VARIANTS),'Crystal scan already admitted')
    data=copy.deepcopy(before);bench=next(b for b in data['benchmarks'] if b['key']=='regexredux')
    refs=dict(results['evidence'],plan=pin(root,PLAN),results=pin(root,RESULTS))
    for r in results['programs']:
        parent=before['programs'][r['parent']];digest=r['source_sha256'];source=r['source'];k=r['key']
        require(parent['files']==[r['parent_source_sha256']] and digest not in data['files'],'Historical Crystal source changed/duplicate new source')
        require(r['loc']>=bench['baseline_loc'] and r['median_seconds']>=bench['baseline_seconds'],'New global baseline needs separate review')
        data['files'][digest]=dict(name=Path(source).name,path=source,archive_path=source,sha256=digest,code=(root/source).read_text(),
            role='application',normalized_loc=r['loc'],physical_loc=r['physical_loc'])
        row=dict(key=k,id=r['id'],benchmark='regexredux',language='crystal',loc=r['loc'],physical_loc=r['physical_loc'],
            seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],files=[digest],
            x=r['loc']/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],
            formatted_loc=None,formatted_x=None,formatted_loc_status='pending',formatted_loc_complete=False,formatted_loc_evidence={},
            file_roles={digest:dict(role='application',included_in_application_loc=True,normalized_loc=r['loc'],physical_loc=r['physical_loc'])},
            loc_metric='statement-normalized',loc_expansions=r['loc_expansions'],loc_report=r['source_count_review']['path'],
            loc_report_sha256=r['source_count_review']['sha256'],source_report=refs['review']['path'],report=RESULTS,report_sha256=refs['results']['sha256'],
            measurement_status='measured',execution_mode='aot',binary_sha256=r['binary_sha256'],native_observations=3,
            command=r['command'],runtime_arguments=r['command'],build_command=r['build_command'],
            cwd=results['recorded_execution_root']+'/'+BASE+'full-v1/run-v1',runtime_environment=ENV,
            sample_execution_metadata=r['sample_execution_metadata'],timing_boundary=results['timing_boundary'],
            runtime_policy='Crystal 1.21.1 native release AOT; ordinary PCRE2; '+('one execution context worker' if r['variant']=='inline-compact' else 'eight execution context workers'),
            memory_policy=parent['memory_policy'],runtime_support=parent['runtime_support'],
            timing_summary='Three fresh complete processes on canonical N5m input. Startup, runtime regex preparation, full input/work/output and shutdown included. Historical parent samples remain unchanged.',
            source_url=None,source_link_label='Audited Crystal standard scan source',local_adaptation=True,original_program_key=r['parent'],
            retained_source_revision=SOURCE_REVISION,candidate_role='speed-and-expressiveness-candidate',
            source_provenance='Adapted retained Crystal application using ordinary String.scan; upstream implementation citations and licenses retained, current exact authoring model unverified.',
            source_provenance_record=dict(kind='suite-authored-optimization',original_program_key=r['parent'],source_sha256=digest,
                admission=refs['results'],author_context=AUTHOR_CONTEXT),
            source_accounting=dict(policy='application-loc-v1',application_loc=r['loc'],physical_loc=r['physical_loc'],
                evidence=refs['review']['path'],review_sha256=refs['review']['sha256'],files=[],
                qualification=results['source_size_scope']),
            required_work_validated=True,algorithm=dict(strict=True,status='required-work-reviewed',native_benchmark_kernel=False,
                reason='Nine separate prescribed standard-library scans and five ordered global substitutions; full input and complete output. All authored helpers and scheduling count.',
                full_work=dict(input_bytes=50833411,count_patterns=9,ordered_substitutions=5),evidence=refs['review']),
            full_output_validation=[dict(bytes=298,sha256=OUTPUT_SHA,reference_match=True) for _ in range(3)],
            matched_control=dict(program_key=CONTROL,report=refs['full'],median_seconds=results['matched_control']['median_seconds'],
                speedup=r['matched_control_speedup'],historical_profile_observations_unchanged=True),
            time_x_mech_aot=r['time_x_mech_aot'],mech_aot_comparison=results['mech_aot_baseline'],
            chart_admission=dict(historical_reports_unchanged=True,**refs),
            measured_backend=dict(key='crystal',execution='aot',label='Crystal native AOT',verified=True,
                evidence=dict(verified=True,report=RESULTS,report_sha256=refs['results']['sha256'],command=r['command'],source_sha256=[digest],
                    actual_native_build_command=r['build_command'],historical_executable=dict(path=r['command'][0],sha256=r['binary_sha256']),
                    runtime_receipt=dict(verified=True,report=RESULTS,report_sha256=refs['results']['sha256'],field='/toolchains/crystal/version',
                        value=results['toolchains']['crystal']['version'],value_encoding='literal-saved-string'))))
        row['authorship']=authorship_record(parent,r,refs)
        data['programs'][k]=row;data['program_inventory'][k]=copy.deepcopy(row)
    group=next(g for g in bench['groups'] if g['language']=='crystal');group['programs'].extend(key(v) for v in VARIANTS)
    candidates=[data['programs'][k] for k in group['programs']]
    group['fast']=min(candidates,key=lambda p:(p['seconds'],p['loc'],p['key']))['key']
    group['small']=min(candidates,key=lambda p:(p['loc'],p['seconds'],p['key']))['key']
    require(group['fast']==key('block-parallel') and group['small']==key('inline-compact'),'Unexpected Crystal endpoints')
    for summary in data['reference_summary']:
        if summary['lang']!='crystal':continue
        groups=[g for b in data['benchmarks'] for g in b['groups'] if g['language']=='crystal']
        for kind in ('fast','small'):
            selected=[data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind]=dict(x=statistics.geometric_mean(p['x'] for p in selected),y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*results['artifacts'],*refs.values(),*[dict(path=r['source'],sha256=r['source_sha256']) for r in results['programs']]]:
        data['archive_paths'][ref['path']]=ref['path']
    data['crystal_scan_audit']=dict(schema='crystal-scan-catalog-extension.v1',appended_programs=[key(v) for v in VARIANTS],
        evidence=refs,new_observations=9,source_files_added=3,old_profiles_unchanged=True,old_baselines_unchanged=True,
        historical_cohorts_not_rematched=True)
    for pool in ('programs','program_inventory','files','archive_paths'):
        require(all(data[pool][k]==v for k,v in before[pool].items()),'Historical '+pool+' changed')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true');parser.add_argument('--apply',action='store_true')
    parser.add_argument('--expected-before-sha256');parser.add_argument('--expected-prepared-sha256');args=parser.parse_args()
    require(args.prepare!=args.apply,'Choose exactly one of prepare/apply');catalog=ROOT/'data/benchmarks.json'
    if args.prepare:
        before_sha=sha(catalog);before=load(catalog);write(ROOT/PLAN,make_plan());write(ROOT/RESULTS,reconcile())
        after=append_catalog(before);require(sha(catalog)==before_sha,'Catalog changed during preparation');write(ROOT/PREPARED,after)
        print(dict(before_sha256=before_sha,prepared_sha256=sha(ROOT/PREPARED),results_sha256=sha(ROOT/RESULTS),canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256,'Both reviewed hashes required')
        require(sha(catalog)==args.expected_before_sha256 and sha(ROOT/PREPARED)==args.expected_prepared_sha256,'Reviewed catalog identities differ')
        after=append_catalog(load(catalog));require(encoded(after)==(ROOT/PREPARED).read_bytes(),'Preview does not reproduce')
        require(sha(catalog)==args.expected_before_sha256,'Catalog changed during replay');write(catalog,after)
        print('Appended three exact Crystal scan sources; all older profiles, sources and observations preserved.')


if __name__=='__main__':main()
