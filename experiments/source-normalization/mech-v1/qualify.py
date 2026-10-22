"""Replay exact native source-owner captures and handwritten fixture expectations."""
import json
from pathlib import Path
from capture import HERE,ROOT,process
from owners import qualify,QualificationError,POLICY
EXPECTED={'parent':{'FunctionDefine':11,'VariableDefine':26,'KindDefine':1},'shared-numerator':{'FunctionDefine':11,'VariableDefine':27,'KindDefine':1},'compact-shared':{'FunctionDefine':10,'VariableDefine':26,'KindDefine':1}}
def main():
    manifest=json.loads((HERE/'native-v1/results.json').read_bytes());fixtures=json.loads((HERE/'fixtures.json').read_bytes());saved=json.loads((HERE/'fixtures-v1/results.json').read_bytes())
    assert saved['status']=='all-manual-owner-fixtures-pass' and saved['fixtures_sha256']==process.sha(HERE/'fixtures.json')
    report={'schema':'mech-native-logical-source-qualification.v1','status':'native-qualified-exact-source-subset','policy':POLICY,'policy_source_sha256':process.sha(HERE/'owners.py'),'helper_source_sha256':process.sha(HERE/'helper/src/main.rs'),'helper_sha256':manifest['helper_sha256'],'compiler_commit':'6de19875e2266f39c93712800c400672a44b98c9','generic_language_certificate':False,'canonical_formatted_loc':None,'input_programs_executed':False,'proof_scope':'Three exact source forms and the handwritten fixture subset; no whole-language certificate or independent external reviewer is claimed.','sources':{},'fixtures':[]}
    assert report['helper_source_sha256']==manifest['helper_source_sha256'] and saved['helper_sha256']==manifest['helper_sha256']
    from collections import Counter
    for name,expected in EXPECTED.items():
        d=HERE/'native-v1'/name;capture=json.loads((d/'stdout.bin').read_bytes());row=qualify(capture)
        assert process.sha(ROOT/'experiments/mech/pidigits-performance-v1/sources'/(name+'.mec'))==row['source_sha256']
        assert row['source_sha256']==manifest['sources'][name]['source_sha256'] and process.sha(d/'stdout.bin')==manifest['sources'][name]['capture_sha256']
        assert dict(Counter(o['kind'] for o in row['owners']))==expected
        report['sources'][name]={**row,'native_capture_sha256':process.sha(d/'stdout.bin'),'manual_owner_breakdown':expected}
    for case in fixtures['cases']:
        d=HERE/'fixtures-v1'/case['id'];capture=json.loads((d/'stdout.bin').read_bytes());assert capture['source']==case['source']
        try:
            result=qualify(capture);assert not case.get('reject') and result['logical_units']==case['expected'],case['id']
            report['fixtures'].append({'id':case['id'],'logical_units':result['logical_units'],'status':'pass'})
        except QualificationError as error:
            assert case.get('reject'),(case,str(error));report['fixtures'].append({'id':case['id'],'status':'expected-rejection','reason':str(error)})
    # Removing native tokens must not silently turn a nonempty program into zero units.
    import copy
    sample=json.loads((HERE/'native-v1/compact-shared/stdout.bin').read_bytes())
    bad=copy.deepcopy(sample);bad['syntax']['children']=[]
    try:qualify(bad);raise AssertionError('Missing native tokens accepted')
    except QualificationError:pass
    closed=0
    for path in HERE.rglob('process.json'):
        r=json.loads(path.read_bytes());assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['cleanup_errors'];closed+=1
    assert closed==21;report['closed_owned_processes']=closed;report['native_processes_started_by_replay']=0
    process.save(HERE/'qualification.json',report);print(json.dumps({'status':report['status'],'counts':{k:v['logical_units'] for k,v in report['sources'].items()},'fixtures':len(report['fixtures']),'closed_owned_processes':closed}))
if __name__=='__main__':main()
