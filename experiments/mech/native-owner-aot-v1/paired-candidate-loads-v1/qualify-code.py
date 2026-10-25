"""Verify source-pinned qualification and actual paired loads before timing."""
import sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import process,read,source_state
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
development=read(STUDY/'development-plan.json')
scopes=development['already_qualified_scopes']+development['scopes']
for row in scopes:
    folder=HERE.parent/'native-owner-dispatch-v1'/row['folder']
    receipt=read(folder/'process.json');source=read(folder/'source-provenance.json')
    assert receipt['exit_status']==0 and receipt['reaped'] and receipt['group_closed']
    assert not receipt['signals'] and not receipt['cleanup_errors']
    assert source['clean_revision_qualified'] and source['source_unchanged']
    assert source['before']['commit']==before['commit']
    assert f"{row['expected_tests']} passed; 0 failed" in (folder/'stdout.bin').read_text()
prefix=read(HERE/plan['receipt']/'results.json')
assert prefix['source_commit']==before['commit']
assert prefix['status']=='all-outputs-and-update-counts-verified'
assert prefix['source_sha256']=='ddd2a78102f727abd838dfc8628bf877410532377b00e5e6bcdf34c2d33410da'
assert prefix['bytecode_sha256']=='050db3a016f0caea04900d48940db5bbefc880c3ada507eff82c22c5b84418b0'
project=HERE/'.build'/(plan['binary']+'.project')
parent=HERE/'.build'/(plan['parent_binary']+'.project')
for name in ['program.mecb','native-resources.json']:
    assert process.sha(project/name)==process.sha(parent/name)
inspection=read(STUDY/'code-inspection.json')
assert inspection['source']==before
assert sum(row['identical'] for row in inspection['function_comparisons'])==12
assert len(inspection['function_comparisons'])==14
placement=read(STUDY/'paired-load-placement.json')
assert placement['source']==before and placement['object_sha256']==prefix['object_sha256']
assert len(placement['functions'])==2
for name,windows in placement['functions'].items():
    assert len(windows)==38
    for w in windows:
        start=next(i for i,r in enumerate(w['instructions']) if r['address']==w['address'])
        after=[r['assembly'].split()[0] for r in w['instructions'][start+1:start+4]]
        assert 'cmp' in after and 'b.ne' in after,(name,w)
gate=dict(status='correctness-and-actual-paired-load-gates-passed',source=before,
    proceed_to_primary=True,inspection_sha256=process.sha(STUDY/'code-inspection.json'),
    load_placement_sha256=process.sha(STUDY/'paired-load-placement.json'),
    candidate_value_loads=76,paired_candidate_loads=76,unchanged_function_bodies=12,
    scopes=[dict(folder=r['folder'],tests=r['expected_tests']) for r in scopes],
    scope='Actual LDP key/count reads precede complete key comparison in both hashed functions; unchanged source, bytecode, resources, finite work, maps and prefix output qualify. No full-input speedup is inferred.')
assert source_state()==before
process.save(STUDY/'code-review.json',gate)
print(gate['status'])
