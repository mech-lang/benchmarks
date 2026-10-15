"""Bind the unchanged three work observations to the completed split corpus."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'tools/qualification/rebol_work_remaining.py'
BASE_SHA = 'c19f3d86c2ee38407b57ec9884173c77c40839a6070f5a29b1fe5848b1bfd31e'
BOUNDED_SHA = '4b620fdd96d789ba02b119a700c7028fa1f8b84cc2bd83dcd1d88ff494db40f4'
PRIMITIVE_SHA = 'f28c9bbb5ed9a47bf6bd2d912e031312038228b6092e451e58a4e364332a7a4b'
FINAL = ROOT/'tools/qualification/rebol_bounded_final.py'
FINAL_SHA = 'ba354558de43f830953e8a17f85115ec07213b0ff91e3860cfbcaa85ed9f4db4'
BOUNDED_PACKET = ROOT/'experiments/rebol/bounded-v1/tree-continuation-v1/final8-v1'
PACKET = ROOT/'experiments/rebol/work-observations-v1/remaining-intake-v1/final-bounded-v1'
JOB = ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/rebol-bounded-final8-v1'
BASE_REVIEW = dict(path=str(PACKET.parent/'source-review-v1.json'),sha256='3327768236a8b94f63c4b994f5594105139f5ed0e4ff3300bc20cde8e30c4a27')
BOUNDED_REVIEW = dict(path=str(BOUNDED_PACKET/'combined-bounded-review-v1.json'),sha256='e0514bb96b47a5420ffc300dff0aeac898b5547ece3e4b1d17384c90120c9e5c')
CLOSURE = dict(path=str(BOUNDED_PACKET/'independent-closure-v1.json'),sha256='fa47ee3f736e6c3572a575833d8db06234c1442da17e7880eac0dc3df503f79e')
BOUNDED_SOURCE = dict(path=str(BOUNDED_PACKET/'source-review-v1.json'),sha256='3df9e689570764f3eef1c8eacb53955ea4b3db9a8808d2556e64e046c1521d7d')
REFS = dict(
    plan=dict(path=str(BOUNDED_PACKET/'plan-v1.json'),sha256='1a50e95803c013797bfa92349e3118b286adcd1b823fba0614a9f2f18bc92bf9'),
    report=dict(path=str(BOUNDED_PACKET/'run-v1/report.json'),sha256='da4180dca00b71f5af4f39a208bf04c0663f57b3f8ca01273428ac1d77d6bfd3'),
    terminal=dict(path=str(BOUNDED_PACKET/'run-v1/terminal.json'),sha256='80d0fadb7139cab6bdd202737997d6f54c72e400bee939a73399d822dd75806e'))
TREE = dict(path=str(ROOT/'experiments/rebol/tree-leaves-v1/binarytrees.reb'),sha256='571983a57c50c71fbe23a9a51758518fdfb0d1b7b5400a9955cbdebb91ea18e6')
TREE_REVIEW = dict(path=str(ROOT/'experiments/rebol/tree-leaves-v1/source-review-v1.json'),sha256='6e29eb3605990bf09b26ccc92fe0c65e1917aa265e6d4d2ea0a5af1108c7a9ce')


def require(value, message):
    if not value:
        raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_small(path):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.is_absolute() and path.resolve(strict=True) == path,
            'Physical regular source required')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        held = os.fstat(stream.fileno())
        require((held.st_dev,held.st_ino) == (before.st_dev,before.st_ino), 'Source replaced before read')
        raw = stream.read(2*1024**2+1)
        require(len(raw) <= 2*1024**2, 'Source exceeds intake bound')
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and (after.st_dev,after.st_ino) == (held.st_dev,held.st_ino),
                'Source replaced during read')
    return raw


def check_approval(w, approval, closure, primitive_ref):
    refs = dict(REFS, primitive_review=primitive_ref, source_review=BOUNDED_SOURCE)
    counts = dict(native_attempts=150,successful_output_contracts=149,success_cases=142,
                  rejection_cases=7,unique_case_count=149,failed_attempts=1,unstarted_cases=0,benchmark_samples=0)
    require(approval['schema'] == 'rebol-combined-independent-bounded-review-v1'
        and approval['status'] == 'exact149-output-contracts-qualified' and approval['independent_review'] is True
        and approval['references'] == refs and approval['current_closure'] == CLOSURE
        and all(type(approval[k]) is int and approval[k] == v for k,v in counts.items())
        and approval['actual_attempts_by_cohort'] == dict(original=24,corrected_tree=118,final8=8)
        and approval['benchmark_correctness_qualified'] is True
        and all(approval[k] is False for k in w.GATES if k != 'benchmark_correctness_qualified'),
        'Exact independently qualified split149 approval required')
    require(closure['schema'] == 'rebol8-independent-closure-v1'
        and closure['status'] == 'eight-output-contracts-verified-owned-stage-closed'
        and closure['independent_review'] is True and closure['references'] == refs
        and closure['durable'] == approval['durable'] and closure['successful_output_contracts'] == 8
        and len(closure['successful_captures']) == 8
        and closure['preserved_successful_cases'] == 141 and all(closure[k] is False for k in w.GATES),
        'Exact final8 independent physical closure required')


@contextmanager
def final_lease(e, inherited, durable):
    lease = durable['lease']
    path = Path(lease['path'])
    require(durable['directory'] == str(JOB) and path == JOB/'owner.lock'
        and path not in [Path(item[0]) for item in inherited]
        and all(type(lease[k]) is int for k in ('device','inode')), 'Exact distinct final8 lease required')
    with e.regular(path) as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        combined = [*inherited,(path,stream,(lease['device'],lease['inode']))]
        e.check_leases(combined)
        try:
            yield combined
        finally:
            e.check_leases(combined)


def closed_job(e, durable, pins, resolutions):
    require(durable['directory'] == str(JOB)
        and set(durable['artifacts']) == {'launch.json','command-started.json','terminal.json','request.json',
            'worker-started.json','command.stdout','command.stderr','worker.log'}
        and e.inventory(JOB,('owner.lock',))[0] == durable['artifacts'], 'Final8 durable inventory differs')
    for name,item in durable['artifacts'].items(): e.pin(pins,resolutions,JOB/name,item['sha256'])
    launch,started,ended = [json.loads(e.read_bytes(JOB/name))
                           for name in ('launch.json','command-started.json','terminal.json')]
    argv = [str(e.PYTHON),'-I','-S','-B',str(FINAL),'--adapter-sha256',FINAL_SHA,
            'run','--plan',REFS['plan']['path'],'--plan-sha256',REFS['plan']['sha256']]
    require(launch['command'] == started['command'] == argv and launch['cwd'] == started['cwd'] == str(ROOT)
        and ended['status'] == 'command-exited-zero-awaiting-report-review'
        and type(ended['exit_code']) is int and ended['exit_code'] == 0
        and ended['actual_command_started'] is True and ended['automatic_retry'] is False and ended['stop_signals'] == []
        and started['command_identity_observation_missing'] is ended['command_identity_observation_missing'] is False
        and started['command_pid'] == ended['command_pid'] == started['command_identity']['pid'] == ended['command_identity']['pid']
        and started['command_identity'] == ended['command_identity'], 'Final8 durable command or identity differs')
    return started['command_pid']


def bounded_inputs(w,r,e,kb,final,primitive_ref,pins,resolutions):
    """Reuse the fixed independent149 disposition; replay only its last eight captures."""
    approval = e.document(BOUNDED_REVIEW,pins,resolutions)
    closure = e.document(CLOSURE,pins,resolutions)
    check_approval(w,approval,closure,primitive_ref)
    plan,report,terminal = [e.document(REFS[name],pins,resolutions) for name in ('plan','report','terminal')]
    require(plan['schema'] == 'rebol8-bounded-plan-v1' and plan['repository'] == str(ROOT)
        and plan['final_adapter'] == dict(path=str(FINAL),sha256=FINAL_SHA) and plan['entrypoint'] == str(FINAL)
        and plan['source_review'] == BOUNDED_SOURCE and plan['primitive_review'] == primitive_ref
        and plan['output'] == str(BOUNDED_PACKET/'run-v1')
        and report['schema'] == 'rebol8-bounded-results-v1' and terminal['schema'] == 'rebol8-bounded-terminal-v1'
        and report['status'] == terminal['status'] == r.SUCCESS
        and report['plan'] == REFS['plan']['path'] and report['plan_sha256'] == REFS['plan']['sha256']
        and report['active'] is None and report['integrity_errors'] == report['artifact_errors'] == []
        and terminal['integrity_errors'] == terminal['artifact_errors'] == []
        and terminal['report_sha256'] == terminal['expected_report_sha256'] == REFS['report']['sha256']
        and terminal['common_mutex_held'] is True and terminal['native_processes_started'] == terminal['validated_cases'] == 8
        and report['preserved_successful_cases'] == terminal['preserved_successful_cases'] == 141
        and report['pins'] == dict(plan['pins'],**{REFS['plan']['path']:REFS['plan']['sha256']})
        and report['input_resolutions'] == dict(plan['input_resolutions'],**{REFS['plan']['path']:REFS['plan']['path']})
        and all(plan[k] is report[k] is terminal[k] is False for k in w.GATES), 'Final8 producer closure differs')
    for name,expected in report['pins'].items():
        e.pin(pins,resolutions,name,expected)
        require(resolutions[name] == report['input_resolutions'][name], 'Bounded named input changed')
    for ref in approval['prior_cohorts'].values(): e.document(ref,pins,resolutions)
    for refs in approval['cohort_references'].values():
        for ref in refs.values(): e.document(ref,pins,resolutions)
    cases = r.corpus(e,pins,resolutions)
    spec = e.document(plan['historical_spec'],pins,resolutions)
    mapping = e.document(dict(path=str(r.ORIGINAL/'bounded-corpus-map.json'),
        sha256=spec['fixture_source_pins']['bounded-corpus-map.json']),pins,resolutions)
    selected = r.source_selection(e,spec,mapping,cases,pins,resolutions)
    require(approval['sources'] == plan['sources'] == selected and approval['corpus'] == plan['corpus']
        and approval['extension_image'] == plan['extension_image']
        and approval['quoted_checker'] == plan['quoted_checker'] == final.CHECKER
        and approval['checker_source_review'] == plan['checker_source_review'] == final.CHECKER_REVIEW,
        'Bounded source, image or checker association differs')
    ledger = approval['cases']
    require(len(ledger) == len(cases) == 149 and [x['case'] for x in ledger] == cases
        and [x['id'] for x in ledger] == [x['benchmark']+':'+x['case'] for x in cases]
        and len({x['id'] for x in ledger}) == 149
        and [x['cohort'] for x in ledger] == ['original23']*23+['corrected-tree117']*117+['retained-quoted-rejection']+['final8']*8
        and all(x['source'] == selected[x['case']['benchmark']] for x in ledger),
        'Independent149 case/source ledger differs')
    raw = e.read_bytes(final.CHECKER['path'])
    require(digest(raw) == final.CHECKER['sha256'], 'Quoted checker changed before replay')
    checker = r.load(raw,Path(final.CHECKER['path']),'rebol_work_final_checker')
    output = Path(plan['output'])
    slots = final.final_schedule(r.schedule(e,checker,cases,selected,plan['extension_image'],output,plan['limits']))
    require(slots == plan['schedule'] and report['attempts'] == [s['id'] for s in slots]
        and [x['id'] for x in report['registered']] == report['attempts']
        and len({x['pid'] for x in report['registered']}) == 8 and len(report['captures']) == 8,
        'Final8 schedule or registered captures differ')
    parent = closed_job(e,approval['durable'],pins,resolutions)
    previous = plan['prior_continuation_stage']['report_finished_at']
    validated = {}
    for index,slot in enumerate(slots):
        directory = output/slot['directory']
        capture,snapshot = r.checked_case(e,kb,checker,slot,directory,parent)
        entry = ledger[141+index]
        require(capture == report['captures'][index] == entry['capture']
            and capture['pid'] == report['registered'][index]['pid']
            and r.stamp(previous) <= r.stamp(capture['started_at'])
            and entry['capture_directory'] == str(directory) and entry['capture_files'] == snapshot,
            'Final8 capture differs from independently accepted bytes')
        previous = capture['finished_at']
        validated.update({str(Path(slot['directory'])/name):item for name,item in snapshot.items()})
    require(validated == report['validated_files'] == report['artifacts']
        and e.inventory(output,('report.json','terminal.json'))[0] == validated
        and e.inventory(output,('terminal.json',))[0] == terminal['available_evidence']
        and e.inventory(output)[0] == closure['artifacts'], 'Final8 artifact closure differs')
    for name,item in closure['artifacts'].items(): e.pin(pins,resolutions,output/name,item['sha256'])
    closures = [*plan['prerequisite_artifact_closures'],dict(directory=str(output),artifacts=closure['artifacts'])]
    jobs = [*plan['prior_durable_jobs'],dict(directory=str(JOB),artifacts=approval['durable']['artifacts'])]
    # Every old receipt remains pinned and inventoried; its independent acceptance is not rerun.
    for item in closures:
        require(e.inventory(Path(item['directory']))[0] == item['artifacts'], 'Retained bounded artifact closure changed')
    for item in jobs:
        require(e.inventory(Path(item['directory']),('owner.lock',))[0] == item['artifacts'], 'Retained bounded durable changed')
    return plan,closures,jobs,dict(review=BOUNDED_REVIEW,closure=CLOSURE,references=approval['references'],
        prior_cohorts=approval['prior_cohorts'],durable=approval['durable'],successful_output_contracts=149,native_attempts=150)


def attach(w,base,final,base_review,adapter_ref):
    original_load,original_held,original_build,original_schedule = w.load,w.held,w.build_plan,w.schedule
    additions = {str(p.relative_to(ROOT)) for p in (Path(__file__).resolve(),
        Path(__file__).with_name('test_rebol_work_final.py'),PACKET/'README.md',Path(TREE['path']))}
    dependencies = dict(base_review['dependencies'],**{str(FINAL.relative_to(ROOT)):FINAL_SHA,
        str(Path(final.CHECKER['path']).relative_to(ROOT)):final.CHECKER['sha256']})
    def source_review(value):
        require(value['schema'] == 'rebol-three-work-observations-final-source-review-v1'
            and value['status'] == 'independent-source-review-complete-native-observations-pending'
            and value['independent_review'] is True and set(value['files']) == set(base_review['files'])|additions
            and all(value['files'][key] == sha for key,sha in base_review['files'].items())
            and value['files'][str(Path(adapter_ref['path']).relative_to(ROOT))] == adapter_ref['sha256']
            and value['files'][str(Path(TREE['path']).relative_to(ROOT))] == TREE['sha256']
            and value['dependencies'] == dependencies and value['base_source_review'] == BASE_REVIEW
            and value['bounded_review'] == BOUNDED_REVIEW and value['tree_source_review'] == TREE_REVIEW
            and all(value[k] is False for k in w.GATES), 'Exact final work source review required')
    def load(raw,path,name):
        if Path(path) == w.HELPER:
            require(digest(raw) == base.BOUNDED_SHA, 'Original bounded helper changed')
            r = final.load_controller(FINAL_SHA)
            require(r.ROOT == ROOT and Path(r.__file__) == w.HELPER, 'Original bounded identity differs')
            return r
        return original_load(raw,path,name)
    @contextmanager
    def held(primitive_ref,bounded_source_ref,source_ref):
        require(bounded_source_ref == BOUNDED_SOURCE, 'Final8 bounded source approval required')
        with original_held(primitive_ref,bounded_source_ref,source_ref) as inherited:
            r,p,e,transport,consumers,inspector,common,leases,intake,extension,review,pins,resolutions = inherited
            require(e.document(BASE_REVIEW,pins,resolutions) == base_review, 'Original work source review changed')
            tree = e.document(TREE_REVIEW,pins,resolutions)
            require(tree['files']['binarytrees.reb']['path'] == TREE['path']
                and tree['files']['binarytrees.reb']['sha256'] == TREE['sha256'], 'Corrected diagnostic approval differs')
            approval = e.document(BOUNDED_REVIEW,pins,resolutions)
            check_approval(w,approval,e.document(CLOSURE,pins,resolutions),primitive_ref)
            with final_lease(e,leases,approval['durable']) as combined:
                yield r,p,e,transport,consumers,inspector,common,combined,intake,extension,review,pins,resolutions
    def schedule(e,cases,image,output):
        slots = original_schedule(e,cases,image,output)
        require(slots[0]['command'][3] == str(w.PACKET/'binarytrees.reb'), 'Original tree diagnostic changed')
        slots[0]['command'][3] = TREE['path']
        return slots
    def build_plan(r,p,e,transport,consumers,inspector,output,primitive_ref,bounded_source_ref,source_ref,
                   intake,extension,review,pins,resolutions):
        require(output.is_relative_to(PACKET) and output != PACKET, 'Fresh final work packet output required')
        value = original_build(r,p,e,transport,consumers,inspector,output,primitive_ref,bounded_source_ref,source_ref,
                               intake,extension,review,pins,resolutions)
        prior,closures,jobs,record = bounded_inputs(w,r,e,inspector.kb,final,primitive_ref,pins,resolutions)
        require(value['extension_image'] == prior['extension_image'] and value['corrected_source'] == prior['corrected_source']
            and value['unavailable_inputs'] == prior['unavailable_inputs']
            and prior['prerequisite_artifact_closures'][:len(value['prerequisite_artifact_closures'])] == value['prerequisite_artifact_closures']
            and prior['prior_durable_jobs'][:len(value['prior_durable_jobs'])] == value['prior_durable_jobs'],
            'Work prerequisites differ from qualified corpus')
        value.update(final_intake_adapter=adapter_ref,bounded_final_intake_adapter=dict(path=str(FINAL),sha256=FINAL_SHA),
            quoted_checker=final.CHECKER,entrypoint=adapter_ref['path'],bounded_correctness=record,
            selected_tree_diagnostic=TREE,tree_source_review=TREE_REVIEW,
            prerequisite_artifact_closures=closures,prior_durable_jobs=jobs,pins=dict(pins),input_resolutions=dict(resolutions))
        return value
    w.source_review,w.load,w.held,w.schedule,w.build_plan = source_review,load,held,schedule,build_plan
    w.bounded_inputs = lambda *args: bounded_inputs(w,*args)
    return w


def load_controller(expected):
    raw = read_small(BASE)
    require(digest(raw) == BASE_SHA, 'Frozen work intake adapter changed')
    base = types.ModuleType('rebol_final_work_base'); base.__file__ = str(BASE)
    exec(compile(raw,str(BASE),'exec'),base.__dict__)
    w = base.load_controller(BASE_SHA,BOUNDED_SHA,PRIMITIVE_SHA)
    own = Path(__file__).resolve()
    require(digest(read_small(own)) == expected, 'Final work intake adapter changed')
    raw = read_small(FINAL)
    require(digest(raw) == FINAL_SHA, 'Final8 intake adapter changed')
    final = w.load(raw,FINAL,'rebol_final_work_bounded')
    raw = read_small(BASE_REVIEW['path'])
    require(digest(raw) == BASE_REVIEW['sha256'], 'Original work source review changed')
    return attach(w,base,final,json.loads(raw),dict(path=str(own),sha256=expected))


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--adapter-sha256',required=True)
    args,remaining = parser.parse_known_args()
    w = load_controller(args.adapter_sha256)
    previous = sys.argv
    try:
        sys.argv = [previous[0],*remaining]
        w.main()
    finally:
        sys.argv = previous


if __name__ == '__main__':
    main()
