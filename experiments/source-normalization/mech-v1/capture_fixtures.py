"""Capture handwritten source-owner fixtures using the same read-only native helper."""
from capture import HERE,ROOT,process,PLAN
import fcntl,json
from pathlib import Path
from owners import qualify,QualificationError
def main():
    out=HERE/'fixtures-v1';out.mkdir(exist_ok=False);exe=HERE/'.build/target/release/mech-source-owners-capture';spec=json.loads((HERE/'fixtures.json').read_bytes());report={'status':'running','helper_sha256':process.sha(exe),'fixtures_sha256':process.sha(HERE/'fixtures.json'),'cases':[]}
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for case in spec['cases']:
            source=out/(case['id']+'.mec');source.write_text(case['source']);d=out/case['id'];r=process.execute([str(exe),str(source)],d,PLAN['environment'],lock)
            assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
            x=json.loads((d/'stdout.bin').read_bytes())
            try:
                row=qualify(x);assert not case.get('reject') and row['logical_units']==case['expected'],(case,row)
                result={'id':case['id'],'status':'pass','logical_units':row['logical_units']}
            except QualificationError as e:
                assert case.get('reject'),(case,str(e),x['diagnostics']);result={'id':case['id'],'status':'expected-rejection','reason':str(e)}
            report['cases'].append(result);process.save(out/'results.json',report)
    for a,b in spec['equivalent_pairs']:assert next(x for x in report['cases'] if x['id']==a)['logical_units']==next(x for x in report['cases'] if x['id']==b)['logical_units']
    report['status']='all-manual-owner-fixtures-pass';process.save(out/'results.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
