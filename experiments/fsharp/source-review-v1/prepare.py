"""Seal pending native JIT/AOT cases and source identities; never compile F#."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
FAMILY=HERE.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    review=json.loads((HERE/'review.json').read_bytes())
    assert len(review['inspected_profiles'])==21 and len(review['protected_profiles'])==9
    pins={}
    def pin(p):
        pins[str(p.relative_to(ROOT))]=sha(p)
    for row in review['inspected_profiles']+review['protected_profiles']:
        for source in row['source_bundle']:
            p=ROOT/source['path'];assert sha(p)==source['sha256'];pin(p)
    corpus_path=ROOT/'experiments/shared/bounded-corpus-v1/cases/manifest.json'
    corpus=json.loads(corpus_path.read_bytes());pin(corpus_path)
    candidates=json.loads((FAMILY/'candidates-v1.json').read_bytes());pin(FAMILY/'candidates-v1.json');pin(FAMILY/'global.json')
    cases=[]
    for row in candidates['candidates']:
        source=ROOT/row['source'];parent=ROOT/row['parent']
        assert sha(source)==row['source_sha256'] and sha(parent)==row['parent_sha256']
        pin(source);pin(parent)
        project=source.with_name('app.fsproj');pin(project)
        tree=ET.fromstring(project.read_bytes())
        assert tree.findtext('.//TargetFramework')=='net10.0' and tree.find('.//Compile').attrib['Include']=='Program.fs'
        benchmark='binarytrees' if row['name'].startswith('binarytrees') else 'spectralnorm' if row['name'].startswith('spectral') else 'regexredux'
        for index,case in enumerate(corpus['cases']):
            if case['benchmark']!=benchmark:continue
            assert case['expected_exit']==0
            for mode in ('jit','aot'):
                cases.append(dict(candidate=row['name'],benchmark=benchmark,mode=mode,corpus_index=index,case=case['case'],status='not-built-not-executed'))
    assert len(cases)==58
    return dict(schema='fsharp-native-case-preparation.v1',pins=pins,cases=cases,case_count=58,
                native_processes_started=0,new_timing_samples=0,native_controller_qualified=False,
                source_counts_qualified=False,chart_admission=False,
                limitations=['Drafts have not been accepted by the F# compiler.','SDK restoration, native preflight and separately pinned JIT/AOT artifacts are required.','Output validation alone does not establish allocation/lifetime, dense-product or regex-work requirements.','Raw source rows do not qualify normalized ownership or native formatted LOC.'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build();output=HERE/'preparation-v1.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',pending_native_cases=result['case_count'],native_processes_started=0)))
