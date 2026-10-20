"""Admit only the exact qualified, full-process typed-array Clojure candidate.

Preparation verifies local compiled/runtime artifacts. Offline catalog replay
verifies their retained manifests and all durable sources/streams, without
pretending that ignored JDK/class binaries are present in an archived checkout.
No path starts a compiler, runtime, benchmark, browser or network request.
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

BASE = 'experiments/clojure/optimization-v1/primitive-v1/'
ADMISSION = BASE+'admission-v1/'
PLAN, RESULTS, PREPARED = [ADMISSION+name+'.json' for name in ['plan', 'results', 'prepared']]
KEY, PARENT = 'nbody:clojure-nbody-primitive-updates-v1', 'nbody:clojure-nbody-compact'
SOURCE = BASE+'sources/clbg/nbody/primitive_updates.clj'
SOURCE_SHA = '12d61dd8a07254f6ba94652fb30b63cc305ec0145e482f1136044a1dc8c88fe2'
PARENT_SHA = '193e26ad8dfd011fd1835d9d67be04bb223d088e6cdd3e2d6302ca8cae2f46d4'
SUPPORT_SHA = 'ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446'
SOURCE_REVISION = 'cf702da9e68a81da37a9c8ab4278302b93a10cb1'
FULL = b'-0.169075164\n-0.169059907\n'
NAMES = ['parent', 'scalar-updates', 'primitive-updates']
SELECTED = ['parent', 'primitive-updates']
NS = [0, 1, 2, 3, 7, 10, 31, 1000, 1001, 10000]
AUTHOR_CONTEXT = copy.deepcopy(shared.AUTHOR_CONTEXT)
FROZEN = {
    'foundation': ('execution-plan.json', 'cb43a5a01cfafa8c441e0c9ee8a13d1abcfe84cc1b14f3ff247bc74f96c92195'),
    'runtime': ('runtime-build.json', '8a77c406dacff8f397359bba295d2f92ece05ee2270c2f7c83f517ac576e9f3a'),
    'builds': ('builds.json', '1f3099f38ebc295bfb3173c3ead7cde039b0204ba7891e41c5a0687a6445c159'),
    'state': ('state-probe-report.json', '9cbbb2b59c533207e624f51723c0a986f4a2ab8b087bd5bbc17754e9d3ea3805'),
    'bounded': ('bounded-v1/report.json', 'c3f0777f69307134fe9383e4aab8fe1b10e59d9a55d185dd10e785ce9b288d56'),
    'pilot': ('pilot-v1/report.json', 'ce91252e209b8c3458e0441e1a15df0200fd4fe961d7dcb14960ae374829b4a8'),
    'selected_plan': ('selected-full-v1/plan.json', 'aeb77e8c01e21e3136c09240ca2657a3d71bb61a460117eeab994bb71696e736'),
    'full': ('selected-full-v1/run-v1/report.json', '9f385e274051e1294380a64c150124ba73f389ad64b756f4e0f41b5f6b1fa1c4'),
    'ownership': ('source-ownership-approved.json', '89e695f8c980441c922f8158ce8f0806242dc32db882d3dfaf557ed96f608d14'),
}
sha, pin, load, encoded, require, relative = shared.sha, shared.pin, shared.load, shared.encoded, shared.require, shared.relative


def make_plan(root=ROOT):
    root = Path(root)
    evidence = {name: dict(path=BASE+path, sha256=digest) for name, (path, digest) in FROZEN.items()}
    evidence.update(importer=pin(root, 'tools/qualification/import_clojure_nbody.py'),
                    shared_helpers=pin(root, 'tools/qualification/import_bqn_knucleotide.py'))
    return dict(schema='clojure-nbody-admission-plan.v1', key=KEY, parent=PARENT,
        source=dict(path=SOURCE, sha256=SOURCE_SHA), source_revision=SOURCE_REVISION,
        evidence=evidence, author_context=AUTHOR_CONTEXT,
        selection='Admit the preselected typed-array candidate from three full matched rounds; preserve the intermediate pilot and all predecessors. No global optimality is claimed.',
        chart_admission=False, historical_measurements_unchanged=True)


def check_closure(evidence, pins, local_artifacts, recorded):
    require(isinstance(pins, dict) and pins, 'Empty evidence closure')
    for path, digest in pins.items():
        path = relative(evidence.root, path, recorded)
        if '/.build/' in path and not local_artifacts:
            continue
        evidence.check(dict(path=path, sha256=digest))


def check_processes(evidence, report, label, foundation, recorded):
    require(report['status'] == 'PASSED' and report['active'] is None and report['pins_unchanged'] is True
        and report['chart_admission'] is False and report['diagnostic_profile'] is (label == 'pilot')
        and report['timing_boundary'] == foundation['timing_boundary']
        and report['required_work'] == foundation['required_work'], 'Incomplete or changed process cohort')
    full = label == 'full'
    names = SELECTED if full else NAMES
    require(report['sources'] == names and report['full_workload'] is full, 'Wrong source/timing cohort')
    rows = report['cases']
    expected = [(n, sample, name) for n, sample in ([(50000000, i) for i in [1,2,3]] if full
        else [(n, 1) for n in NS] if label == 'bounded' else [(1000000, 1)]) for name in names]
    require(sorted((r['n'], r['sample'], r['source']) for r in rows) == sorted(expected), 'Missing/duplicate process observation')
    folder = str(Path(FROZEN[label][0]).parent)
    extra = {'source','n','sample','case','output_valid','exact_reference_bytes','exact_parent_bytes','source_sha256','power_before','power_after'}
    for row in rows:
        name = row['source']; program = foundation['programs'][name]
        require(row['command'] == program['run_argv']+[str(row['n'])]
            and row['environment'] == foundation['environment'] and row['cwd'] == recorded
            and row['stdin'] == '/dev/null' and row['source_sha256'] == program['source']['sha256']
            and row['exit_code'] == 0 and row['timed_out'] is False and row['remaining_process_group'] == []
            and row['output_valid'] is True and row['common_mutex_inherited'] is True
            and row['common_mutex_inode'] == report['common_mutex_inode']
            and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds'] > 0
            and row['maximum_rss_bytes'] <= 10*1024**3, 'Invalid process/work/runtime boundary')
        directory = BASE+folder+'/round-'+str(row['sample'])+'-'+name
        # Bounded and pilot directory names are bound by their exact stream refs.
        if not full:
            directory = str(Path(relative(evidence.root, row['stdout']['path'], recorded)).parent)
            require(directory.startswith(BASE+folder+'/') and directory != BASE+folder, 'Wrong bounded/pilot output directory')
        raw = evidence.document(pin(evidence.root, directory+'/process.json'))
        require(raw == {k:v for k,v in row.items() if k not in extra}, 'Raw process receipt differs')
        for stream in ['stdout','stderr']:
            require(relative(evidence.root, row[stream]['path'], recorded) == directory+'/'+stream+'.bin', 'Wrong stream path')
            evidence.check({**row[stream], 'path': directory+'/'+stream+'.bin'})
        shared.check_power(row['power_before']); shared.check_power(row['power_after'])
        if full:
            require(row['exact_reference_bytes'] is True and (evidence.root/(directory+'/stdout.bin')).read_bytes() == FULL,
                    'Full output is not exact independent reference bytes')
    if full:
        rng = random.Random(20261020); expected_order=[]
        for sample in [1,2,3]:
            order = SELECTED.copy(); rng.shuffle(order); expected_order.append(dict(n=50000000,sample=sample,sources=order))
        require(report['orders'] == expected_order and [(r['source'],r['sample']) for r in rows]
            == [(name,order['sample']) for order in expected_order for name in order['sources']], 'Predeclared round order differs')
        samples = {name:[r['elapsed_seconds'] for r in rows if r['source']==name] for name in names}
        require(report['samples'] == samples and report['medians'] == {k:statistics.median(v) for k,v in samples.items()}
            and report['sample_sd_seconds'] == {k:statistics.stdev(v) for k,v in samples.items()}, 'Stale full aggregates')


def reconcile(root=ROOT, local_artifacts=True):
    evidence = shared.Evidence(root); root = evidence.root
    plan = load(root/PLAN)
    require(plan == make_plan(root), 'Changed/stale admission plan')
    docs = {name:evidence.document(ref) for name,ref in plan['evidence'].items() if name in FROZEN}
    for ref in plan['evidence'].values(): evidence.check(ref)
    require(plan['evidence']['shared_helpers']['sha256'] == '5e79b71fc96822ece4604f4075bae444f25ecaf2b65bd3af07d9cea66c6f1843', 'Changed frozen evidence helper')
    foundation, selected, full = [docs[k] for k in ['foundation','selected_plan','full']]
    recorded = full['cases'][0]['cwd']
    require(Path(recorded).is_absolute() and str(Path(recorded)) == recorded and '..' not in Path(recorded).parts, 'Unsafe recorded root')
    require(foundation['programs']['primitive-updates']['source'] == dict(path=SOURCE,sha256=SOURCE_SHA)
        and foundation['programs']['parent']['source']['sha256'] == PARENT_SHA
        and all(p['support']['sha256'] == SUPPORT_SHA for p in foundation['programs'].values()), 'Source/support identity differs')
    require(selected['sources'] == SELECTED and selected['full_n'] == 50000000 and selected['rounds'] == 3
        and selected['foundation'] == plan['evidence']['foundation'] and len(selected['pins']) == 659
        and full['plan'] == plan['evidence']['selected_plan'] and full['pins'] == selected['pins'], 'Wrong selected/full prerequisite closure')
    for name in ['runtime','builds','state']:
        require(docs[name]['status'] == 'PASSED', 'Incomplete runtime/build/state gate')
    require(docs['state']['raw_bit_state_slots'] == 35 and docs['state']['advance_function_invocations'] == 348
        and docs['state']['inner_pair_store_counters'] == 'not-instrumented-source-proof-only'
        and docs['state']['timing_sample'] is False, 'State qualification scope differs')
    count=docs['ownership']; source=evidence.check(plan['source']).read_text()
    require(count['independent_review_approved'] is True and count['application_loc']==111 and count['physical_loc']==52
        and count['source']==plan['source'] and sum(r['retained_rule_proposed_units'] for r in count['line_ledger'])==111
        and [r['text'] for r in count['line_ledger']]==source.splitlines(), 'Source count lacks exact approved ledger')
    require(source.count('(aset a ')==3 and source.count('(aset b ')==3 and source.count('(aset body ')==1
        and '(doseq ' not in source and 'Math/sqrt' in source, 'Unreviewed typed-store source delta')
    check_closure(evidence, selected['pins'], local_artifacts, recorded)
    for document in docs.values():
        if isinstance(document.get('pins'),dict): check_closure(evidence,document['pins'],local_artifacts,recorded)
    for name in NAMES:
        require(docs['builds']['programs'][name] == foundation['programs'][name], 'Measured classes differ from compiled source')
        for ref in foundation['programs'][name]['evidence']: evidence.check(ref)
        check_closure(evidence, foundation['programs'][name]['class_pins'], local_artifacts, recorded)
        evidence.check(dict(path=BASE+'selected-full-v1/run-v1/sources/'+name+'.clj',
            sha256=foundation['programs'][name]['source']['sha256']))
    evidence.check(dict(path=BASE+'selected-full-v1/run-v1/sources/support.clj',sha256=SUPPORT_SHA))
    for key, name in [('controller','run_selected_full.py'),('frozen_helper','run_serial.py')]:
        evidence.check(dict(path=BASE+'selected-full-v1/run-v1/controllers/'+name,sha256=full[key]['sha256']))
    for label in ['bounded','pilot','full']: check_processes(evidence,docs[label],label,foundation,recorded)
    require(docs['bounded']['common_mutex_inode']==full['common_mutex_inode'], 'Different serial mutexes')
    rows = [copy.deepcopy(r) for r in full['cases'] if r['source']=='primitive-updates']
    for row in rows: row.update(producer_report=plan['evidence']['full'],producer_plan=plan['evidence']['selected_plan'])
    samples=[r['elapsed_seconds'] for r in rows]; program=foundation['programs']['primitive-updates']
    artifacts=[dict(path=p,sha256=d) for p,d in sorted(evidence.fingerprints.items()) if '/.build/' not in p]
    return dict(schema='clojure-nbody-admission-results.v1',status='RECONCILED',plan=pin(root,PLAN),evidence=plan['evidence'],
        programs=[dict(key=KEY,id=KEY.split(':')[1],source_sha256=SOURCE_SHA,loc=111,physical_loc=52,
            samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=statistics.stdev(samples),
            command=rows[0]['command'],build_command=program['compile_command'],sample_execution_metadata=rows)],
        recorded_at=full['finished_utc'],recorded_execution_root=recorded,author_context=AUTHOR_CONTEXT,
        matched_candidate_medians=full['medians'],matched_control_speedup=full['medians']['parent']/statistics.median(samples),
        source_count_review=count,required_work=foundation['required_work'],timing_boundary=foundation['timing_boundary'],
        runtime_environment=foundation['environment'],toolchains=dict(clojure=dict(version='Clojure 1.12.6; Temurin 25.0.4.1+1 ARM64; spec.alpha 0.5.238; core.specs.alpha 0.4.74')),
        archive_replay_limit='Durable replay verifies retained runtime/class manifests, sources and complete streams. Ignored runtime/class binaries are rehashed only during local-artifact preparation; archived manifests are not a new binary verification.',
        historical_data_preserved=True,new_observations=3,selection=plan['selection'],artifacts=artifacts)


def authorship_record(parent,results,evidence):
    record=copy.deepcopy(parent['authorship'])
    record.update(kind='ai-adapted',label='AI adapted · retained local predecessor',source_sha256=[SOURCE_SHA,SUPPORT_SHA],origin_status='unresolved',
        parent_programs=[PARENT],parent_sources=[dict(program_key=PARENT,relationship='local predecessor',**copy.deepcopy(r)) for r in parent['authorship'].get('retained_sources',[])],
        retained_sources=[dict(source_sha256=SOURCE_SHA,url='https://github.com/mech-lang/benchmarks/blob/'+SOURCE_REVISION+'/'+SOURCE)]
            +[copy.deepcopy(r) for r in parent['authorship'].get('retained_sources',[]) if r['source_sha256']==SUPPORT_SHA],
        ai=dict(tool=AUTHOR_CONTEXT['tool'],models=[],model_family=AUTHOR_CONTEXT['model_family'],exact_model=None,
            status='family-identified-exact-model-unverified',matched_source_files=[SOURCE_SHA],total_source_files=2,evidence=[evidence['plan'],evidence['results']]),
        local_change_license=dict(status='suite-license',id='Apache-2.0',evidence='LICENSE',scope='New local changes only; inherited terms remain unresolved.'),
        evidence=[evidence['plan']['path'],evidence['results']['path'],evidence['ownership']['path']])
    return record


def bound_authorship(data,profile,root=ROOT):
    results=load(Path(root)/RESULTS); evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    detail=profile.get('source_provenance_record') or {}
    require(profile.get('key')==KEY and profile.get('files')==[SOURCE_SHA,SUPPORT_SHA]
        and detail.get('kind')=='suite-authored-optimization' and detail.get('source_sha256')==SOURCE_SHA
        and detail.get('original_program_key')==PARENT and detail.get('admission')==evidence['results']
        and detail.get('author_context')==AUTHOR_CONTEXT and results['author_context']==AUTHOR_CONTEXT
        and results['status']=='RECONCILED' and results['plan']==evidence['plan']
        and sha(Path(root)/SOURCE)==SOURCE_SHA
        and hashlib.sha256(data['files'][SOURCE_SHA]['code'].encode()).hexdigest()==SOURCE_SHA,'Unbound Clojure authorship/source')
    shared.Evidence(root).check(evidence['ownership'])
    return authorship_record(data['programs'][PARENT],results,evidence)


def append_catalog(before,root=ROOT):
    root=Path(root);results=load(root/RESULTS)
    require(results==reconcile(root,local_artifacts=False),'Stale Clojure admission results')
    require(KEY not in before['programs'] and KEY not in before['program_inventory'] and 'clojure_nbody_audit' not in before,'Already admitted')
    data=copy.deepcopy(before);parent=before['programs'][PARENT];r=results['programs'][0]
    require(parent['files']==[PARENT_SHA,SUPPORT_SHA] and parent['loc']==109 and parent['physical_loc']==49,'Historical parent changed')
    bench=next(b for b in data['benchmarks'] if b['key']=='nbody')
    require(r['loc']>=bench['baseline_loc'] and r['median_seconds']>=bench['baseline_seconds'],'Global baseline requires separate review')
    require(SOURCE_SHA not in data['files'],'Source already cataloged')
    evidence={**results['evidence'],'plan':pin(root,PLAN),'results':pin(root,RESULTS)}
    data['files'][SOURCE_SHA]=dict(name='primitive_updates.clj',path=SOURCE,archive_path=SOURCE,sha256=SOURCE_SHA,code=(root/SOURCE).read_text())
    row=copy.deepcopy(parent)
    for field in ['publication_record','timing_measurement','timing_correction','aliased_sample_source','source_alias_of','source_alias_note','loc_expansions','source_accounting','authorship','source_metrics','reproducibility','execution']:
        row.pop(field,None)
    runtime=load(root/(BASE+'runtime-build.json'))
    row.update(key=KEY,id=r['id'],receipt_key=r['id'],files=[SOURCE_SHA,SUPPORT_SHA],loc=111,physical_loc=52,
        seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],x=111/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],
        formatted_loc=None,formatted_x=None,formatted_loc_status='pending',formatted_loc_complete=False,formatted_loc_evidence={},
        report=RESULTS,report_sha256=evidence['results']['sha256'],source_report=evidence['ownership']['path'],loc_report=evidence['ownership']['path'],
        command=r['command'],runtime_arguments=['50000000'],build_command=r['build_command'],cwd=results['recorded_execution_root'],execution_mode='jvm-aot-classes-jit',
        binary_sha256=None,runtime_sha256=runtime['java']['sha256'],native_observations=3,timing_alias_of=None,sample_execution_metadata=r['sample_execution_metadata'],
        original_program_key=PARENT,retained_source_revision=SOURCE_REVISION,local_adaptation=True,distinct_optimization_claimed=True,
        source_provenance='Suite-authored typed-array optimization of the retained local Clojure n-body source; predecessor origin and inherited terms remain unresolved.',
        source_provenance_record=dict(kind='suite-authored-optimization',original_program_key=PARENT,source_sha256=SOURCE_SHA,admission=evidence['results'],origin_status='inherited-unresolved',author_context=AUTHOR_CONTEXT),
        runtime_policy='Clojure 1.12.6; Temurin 25.0.4.1+1 ARM64; direct-linking classes, fresh HotSpot JVM; ActiveProcessorCount=8 Xms64m Xmx8g G1GC',
        runtime_support='Unchanged generic clbg.support; no foreign n-body kernel or new workload helper.',runtime_environment=results['runtime_environment'],timing_boundary=results['timing_boundary'],
        timing_summary='Three fresh complete-process matched observations, all 50 million steps and exact full output; historical samples retained. No global optimality claim.',
        algorithm=dict(strict=True,status='required-work-reviewed',native_benchmark_kernel=False,
            reason='Same ordered ten body pairs in every sequential step, original floating groupings, delayed position updates, momentum and both energies; typed primitive array stores replace generic operations.',
            full_work=results['required_work'],evidence=evidence['state']),
        source_accounting=dict(policy='application-loc-v1',application_loc=111,physical_loc=52,evidence=evidence['ownership']['path'],review_sha256=evidence['ownership']['sha256'],qualification='Exact-source approved retained Clojure109-to111 owner extension; separate logical-source measure required.',files=[]),
        file_roles={SOURCE_SHA:dict(role='application',included_in_application_loc=True,normalized_loc=111,physical_loc=52),SUPPORT_SHA:copy.deepcopy(parent['file_roles'][SUPPORT_SHA])},
        full_output_validation=dict(all_three_samples_passed=True,exact_reference_bytes=True,evidence=evidence['full']),chart_admission=dict(historical_reports_unchanged=True,**evidence),
        measured_backend=dict(key='clojure',execution='jit',label='Clojure (HotSpot)',verified=True,
            evidence=dict(verified=True,report=RESULTS,report_sha256=evidence['results']['sha256'],command=r['command'],source_sha256=[SOURCE_SHA,SUPPORT_SHA],
                runtime_receipt=dict(verified=True,report=RESULTS,report_sha256=evidence['results']['sha256'],field='/toolchains/clojure/version',value=results['toolchains']['clojure']['version'],value_encoding='literal-saved-string'))))
    row['authorship']=authorship_record(parent,results,evidence)
    data['programs'][KEY]=row;data['program_inventory'][KEY]=copy.deepcopy(row)
    group=next(g for g in bench['groups'] if g['language']=='clojure');group['programs'].append(KEY)
    candidates=[data['programs'][k] for k in group['programs']]
    group['fast']=min(candidates,key=lambda p:(p['seconds'],p['loc'],p['key']))['key'];group['small']=min(candidates,key=lambda p:(p['loc'],p['seconds'],p['key']))['key']
    for summary in data['reference_summary']:
        if summary['lang']!='clojure':continue
        groups=[g for b in data['benchmarks'] for g in b['groups'] if g['language']=='clojure']
        for kind in ['fast','small']:
            selected=[data['programs'][g[kind]] for g in groups if g.get(kind)]
            summary[kind]=dict(x=statistics.geometric_mean(p['x'] for p in selected),y=statistics.geometric_mean(p['y'] for p in selected))
    for ref in [*evidence.values(),*results['artifacts'],dict(path=SOURCE,sha256=SOURCE_SHA)]:data['archive_paths'][ref['path']]=ref['path']
    data['clojure_nbody_audit']=dict(schema='clojure-nbody-catalog-extension.v1',appended_programs=[KEY],evidence=evidence,new_observations=3,source_files_added=1,old_profiles_unchanged=True,old_baselines_unchanged=True)
    for pool in ['programs','program_inventory','files','archive_paths']:
        require(all(data[pool][key]==old for key,old in before[pool].items()),'Historical '+pool+' changed')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--apply',action='store_true')
    parser.add_argument('--expected-before-sha256');parser.add_argument('--expected-prepared-sha256');args=parser.parse_args()
    require(args.prepare!=args.apply,'Choose prepare or apply');catalog=ROOT/'data/benchmarks.json'
    if args.prepare:
        before_raw=catalog.read_bytes();before=json.loads(before_raw,object_pairs_hook=shared.no_duplicates)
        before_sha=hashlib.sha256(before_raw).hexdigest();shared.write(ROOT/PLAN,make_plan());shared.write(ROOT/RESULTS,reconcile())
        shared.write(ROOT/PREPARED,append_catalog(before));require(sha(catalog)==before_sha,'Catalog changed during preparation')
        print(dict(before_sha256=before_sha,prepared_sha256=sha(ROOT/PREPARED),results_sha256=sha(ROOT/RESULTS),canonical_changed=False))
    else:
        require(args.expected_before_sha256 and args.expected_prepared_sha256,'Apply needs reviewed hashes')
        require(sha(catalog)==args.expected_before_sha256 and sha(ROOT/PREPARED)==args.expected_prepared_sha256,'Reviewed input/preview differ')
        after=append_catalog(load(catalog));require(encoded(after)==(ROOT/PREPARED).read_bytes(),'Preview does not reproduce')
        require(sha(catalog)==args.expected_before_sha256,'Catalog changed during replay');shared.write(catalog,after)
        print('Added exact qualified Clojure source; all historical observations retained.')


if __name__=='__main__':main()
