#!/usr/bin/env python3
"""Validate only the reviewed native-counter functions; execute no subjects."""
import ast, copy, hashlib, json, tempfile
from pathlib import Path
draft=Path('/private/tmp/native-prefix-secondary-draft.py')
notes=Path('/private/tmp/native-prefix-secondary-preparation-v1.json')
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=read(notes)
native=Path(prep['historical_prefix_process_evidence'][0]['native_report']['path'])
policy=Path(prep['proposed_policy']['path'])
pins={str(p):sha(p) for p in [draft,notes,native,policy,Path(__file__)]}
tree=ast.parse(draft.read_text(),filename=str(draft))
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('require','native_counters')]
assert {node.name for node in functions}=={'require','native_counters'}
namespace={'read':read}
exec(compile(ast.Module(body=functions,type_ignores=[]),str(draft),'exec'),namespace)
validate=namespace['native_counters']
protocol={'native_checks':prep['native_checks']}
original=read(native);resource=read(policy);cases=[]
with tempfile.TemporaryDirectory(prefix='native-prefix-counter-contract-') as directory:
    path=Path(directory)/'native.json'
    def check(name,value,accepted):
        path.write_text(json.dumps(value))
        error=None
        try:validate(path,protocol,resource)
        except ValueError as exception:error=str(exception)
        assert (error is None)==accepted,(name,error)
        cases.append(dict(case=name,accepted=accepted,result='passed',rejection=error))
    check('retained-actual-prefix-report',original,True)
    for workers in (1,7):
        n=copy.deepcopy(original);n['native_parallel_peak_workers']=workers;check('valid-worker-bound-'+str(workers),n,True)
    for key,expected in protocol['native_checks']['required_flags'].items():
        n=copy.deepcopy(original);n[key]=(not expected) if isinstance(expected,bool) else 'invalid';check('reject-'+key,n,False)
    for key in protocol['native_checks']['exact_counters']:
        for mutation,value in [('value',original[key]+1),('bool',True)]:
            n=copy.deepcopy(original);n[key]=value;check('reject-'+key+'-'+mutation,n,False)
    mutations=[('native_parallel_peak_workers',0),('native_parallel_peak_workers',8),('native_parallel_peak_workers',True),('native_worker_credit_claims',0),('native_worker_credit_claims',True),('native_worker_credit_reclaims',original['native_worker_credit_claims']+1),('native_worker_credit_reclaims',True)]
    for key,cap in [('native_work',resource['work']),('native_comparison_work',resource['library']['comparison_work'])]:
        mutations += [(key,0),(key,-1),(key,True),(key,cap+1)]
    for index,(key,value) in enumerate(mutations):
        n=copy.deepcopy(original);n[key]=value;check('reject-scheduled-'+key+'-'+str(index),n,False)
assert pins=={p:sha(Path(p)) for p in pins}
result=dict(status='controller-counter-contracts-verified-without-subject-execution',controller_sha256=sha(draft),pins=pins,cases=cases,checks=len(cases),primary_observations=0,secondary_observations=0,scope='AST extraction executes only require/native_counters against one retained historical report and mutated copies; no entrypoint import, subprocess, compiler, benchmark, or process owner is invoked.')
Path('/private/tmp/native-prefix-controller-validation-v1.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','controller_sha256','checks','primary_observations','secondary_observations']},indent=2))
