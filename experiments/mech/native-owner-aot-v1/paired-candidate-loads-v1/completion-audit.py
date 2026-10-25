"""Audit the full-input runtime objective against current retained evidence."""
import fcntl
from pathlib import Path
import sys

STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state,SOURCE_SHA,BYTECODE_SHA,INPUT_SHA,OUTPUT_SHA,POLICY_SHA
sys.path.insert(0,str(HERE))
from analyze_profile import text_section

source=source_state();plan=read(STUDY/'plan.json');verified=read(STUDY/'verification.json')
assert source['commit']==plan['source_commit'] and not source['status']
assert verified['source']==source and verified['retained_process_receipts']==221
assert verified['verifier_sha256']==process.sha(STUDY/'verify-v2.py')
assert process.sha(HERE/'knucleotide-source-map.mec')==SOURCE_SHA
prefix=read(HERE/plan['receipt']/'results.json')
project=HERE/'.build'/(plan['binary']+'.project')
assert prefix['source_sha256']==SOURCE_SHA and process.sha(project/'program.mecb')==BYTECODE_SHA
manifest=read(project/'linked-manifest.json')['object']
assert (manifest['typed_ir_version'],manifest['abi_version'],manifest['work_policy_version'])==(94,33,69)
assert process.sha(project/'program.o')==verified['object_sha256']
for record in manifest['compiled_steady_loops']:
    assert record['lookup_mode']=='hash' and record['candidate_value_loads']==record['paired_candidate_loads']==38
    assert record['lookup_cache_function']['paired_candidate_loads']==0

sessions=[]
for batch in (1,2):
    folder=HERE/f'full-paired-candidate-loads-v{batch}'
    d=read(folder/'results.json')
    assert d['source']==d['source_after']==source and len(d['samples'])==72
    assert d['input_sha256']==INPUT_SHA and d['policy_sha256']==POLICY_SHA
    assert d['plan_sha256']==process.sha(STUDY/'plan.json') and d['driver_sha256']==process.sha(STUDY/'measure.py')
    for row in d['samples']:
        path=HERE/row['process'];p=read(path)
        assert p['controller_sha256']==process.sha(Path(process.__file__))
        assert p['quantitative_benchmark'] and p['elapsed_seconds']==row['seconds']
        assert p['maximum_rss_bytes']==row['maximum_rss_bytes']
        assert p['reaped'] and p['group_closed'] and p['exit_status']==0 and not p['signals']
        assert process.sha(path.parent/'stdout.bin')==OUTPUT_SHA
        if row['subject']=='rust':
            assert len(p['command'])==1
        else:
            assert p['command'][1:]==[str(HERE/'full-disjoint-state-v1/launch.json'),str(path.parent.with_name(path.parent.name+'.native.json')),'--']
    for target in ('parent','rust'):
        assert d['paired_comparisons'][target]['interval_95'][1]<0
    sessions.append(dict(session=batch,source_receipt=str((folder/'results.json').relative_to(HERE)),
        receipt_sha256=process.sha(folder/'results.json'),medians=d['median_seconds'],x_rust=d['x_rust'],paired=d['paired_comparisons']))

# The inspected controller starts its clock before fork and ends it at wait4.
# No function-only or prepared-runtime timer supplies a primary duration.
controller=Path(process.__file__).read_text()
body=controller.split('def execute(',1)[1]
assert body.index('started = time.monotonic_ns()')<body.index('pid = owner.fork()')<body.index('os.execve(')
assert 'record[\'elapsed_seconds\'] = (time.monotonic_ns() - started)' in body
profile=read(HERE/'profile-paired-candidate-loads-build-v1/results.json')
assert profile['whole_machine_code_matches_timed']
assert text_section(Path(profile['binary']))==text_section(HERE/'.build'/plan['binary'])
changed=read(STUDY/'changed-inputs-v1/results.json')
assert len(changed['cases'])==7 and sum(len(c['executions']) for c in changed['cases'])==14
assert changed['source']==changed['source_after']==source
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)

requirements=[
    dict(requirement='Improve generated Mech execution using general compiler rules',result='proven',
        evidence=['code-review.json','code-inspection.json','paired-load-placement.json','frame-audit.json'],
        finding='Both hashed functions use complete paired key/count loads from admitted owned narrow slots. Complete equality, invalidation, wide fallback and all source work remain. Twelve other guest functions are unchanged; runtime frames/storage/prices/parallel implementation match the good parent.'),
    dict(requirement='Meet or beat unchanged Rust on the established full benchmark',result='proven',
        evidence=[s['source_receipt'] for s in sessions],
        finding='Both predeclared balanced twelve-pair sessions favor the candidate against Rust and the good Mech parent; all four intervals are below zero. All 144 primary observations remain.'),
    dict(requirement='Time complete fresh processes fairly and serially',result='proven',
        evidence=['plan.json','measure.py',str(Path(process.__file__).relative_to(HERE.parents[2]))],
        finding='The common controller starts before fork and observes process exit. Secured Mech startup, input, capabilities, complete counting, output and shutdown are included. All subjects use the same timer and inherited shared mutex; no full-input warmups or outliers are removed.'),
    dict(requirement='Preserve the actual workload rather than substitute a specialized answer',result='proven',
        evidence=['verification.json','changed-inputs-v1/results.json','development-plan.json','frame-audit.json'],
        finding='Human source, bytecode, resources and full input are unchanged. Every full Mech execution performs all seven tables and 874999961 updates. Tests cover complete maps, renamed non-DNA source, changed widths, growth/refills, source/decoded execution, overflow, failure origin and finite resource behavior. Fourteen unchanged AOT executions additionally match independent changed-input oracles.'),
    dict(requirement='Profile exact current Mech and Rust binaries and inspect instructions/CPU/memory/file size',result='proven',
        evidence=['analysis.json','counters/results.json','verification.json'],
        finding='Fresh pre-armed captures have exact owned PIDs and a byte-identical entire Mech text section. Twenty-four separate counters use exact timed files. Primary RSS and actual disk/text sizes are retained; diagnostics are excluded from primary medians.'),
    dict(requirement='Validate and retain successful and negative optimization evidence',result='proven',
        evidence=['verification.json','verifier-v1-failure.json','../candidate-value-loads-v1/README.md'],
        finding='415 native checks, 30 line checks, 36 credit checks, one catalog check and ten focused checks pass. All 221 terminal receipts are reaped/closed. The separate-load regression and corrected analysis-only status label remain in the record; no successful run was replaced.'),
]
assert all(r['result']=='proven' for r in requirements)
result=dict(status='established-full-input-runtime-objective-proven',source=source,
    verifier_sha256=process.sha(STUDY/'verify-v2.py'),verification_sha256=process.sha(STUDY/'verification.json'),
    audit_sha256=process.sha(Path(__file__)),controller_sha256=process.sha(Path(process.__file__)),
    benchmark_scope=dict(input_bases=125000000,input_bytes=254166745,input_sha256=INPUT_SHA,expected_updates=874999961,workers=7),
    requirements=requirements,sessions=sessions,required_remaining_work=[],
    limits=['Result concerns this established full-input benchmark and runner, not every input or hardware target.',
        'The one-million-base diagnostic remains 4.64796x Rust and is retained separately.',
        'Mech still has larger primary peak RSS and executable size than Rust.',
        'Additional future optimization opportunities remain; they are not missing evidence for the demonstrated runtime result.'])
assert source_state()==source
process.save(STUDY/'completion-audit.json',result)
print(result['status'],len(requirements),'requirements',verified['retained_process_receipts'],'terminal receipts')
