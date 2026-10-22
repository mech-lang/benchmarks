"""Re-extract captured originals and bind complete application identity across modes."""
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from collections import Counter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from audit_owned_implementations import classify,application_shas

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normal(raw):return raw.decode('utf-8').replace('\r\n','\n').strip().encode('utf-8')

def main():
    capture_path=HERE/'capture-v1/results.json';capture=json.loads(capture_path.read_bytes())
    data_path=ROOT/'data/benchmarks.json';assert sha(data_path)==capture['catalog_sha256']
    data=json.loads(data_path.read_bytes());catalog={**data.get('program_inventory',{}),**data['programs']}
    base_path=ROOT/'experiments/implementation-audit/v1/inventory.json';baseline=json.loads(base_path.read_bytes())
    coverage=json.loads((ROOT/'experiments/implementation-audit/coverage-v3/coverage.json').read_bytes())
    source_matches={}
    for url,row in capture['sources'].items():
        assert url.startswith('https://') and not any(prefix in url for prefix in ('github.com/mech-lang/','raw.githubusercontent.com/mech-lang/'))
        body_path=ROOT/row['response'];assert sha(body_path)==row['response_sha256']
        body=body_path.read_bytes()
        if '/benchmarksgame/program/' in url:
            blocks=re.findall(r'<pre\b[^>]*>(.*?)</pre>',body.decode('utf-8'),re.S|re.I);assert blocks
            code=html.unescape(re.sub(r'<[^>]*>','',blocks[0])).encode('utf-8')
        else:code=body
        assert code==(ROOT/row['source']).read_bytes() and hashlib.sha256(code).hexdigest()==row['source_sha256']
        digest=hashlib.sha256(normal(code)).hexdigest();assert digest==row['normalized_source_sha256']
        source_matches.setdefault(digest,[]).append(url)
    rows={};families=Counter()
    for key,old in baseline['programs'].items():
        ownership=old['ownership']
        if ownership['upstream_identity']!='normalized-source-match' or ownership['preserve_upstream_source']:continue
        p=catalog[key];matches={}
        for digest in application_shas(p):
            raw=data['files'][digest]['code'].encode('utf-8');assert hashlib.sha256(raw).hexdigest()==digest
            normalized=hashlib.sha256(normal(raw)).hexdigest();assert normalized in source_matches,(key,digest)
            matches[digest]=source_matches[normalized]
        current=classify(p);assert current['preserve_upstream_source'] and current['external_published_application_identity']
        family=coverage['programs'][key]['family'];families[family]+=1
        rows[key]=dict(program=key,family=family,source_bundle=old['source_bundle'],verified_external_source_urls=matches,
                       previous_classification=ownership['classification'],previous_preserve_upstream_source=False,
                       current_classification=current['classification'],preserve_upstream_source=True,
                       adaptation_metadata_conflict=current['protection_metadata_conflict'],authorship_reclassified=False)
    assert len(rows)==34 and len(source_matches)==26
    result=dict(schema='published-source-protection-reconciliation.v1',status='34-profiles-26-application-sources-verified-against-captured-originals',
                inputs=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in (Path(__file__),data_path,base_path,capture_path,ROOT/'tools/audit_owned_implementations.py')],
                profiles=rows,summary=dict(profiles=len(rows),distinct_normalized_application_sources=len(source_matches),families=dict(sorted(families.items()))),
                normalization='Only CRLF to LF and surrounding whitespace trim; no token/comment/identifier normalization.',
                execution_mode_alias_scope='Identical source may bind both AOT and JIT profiles. Source identity and edit protection only; no compile, output, timing or runtime evidence is transferred across modes.',
                native_processes_started=0,new_timing_samples=0,canonical_changes=False,source_bytes_changed=False,authorship_changes=False)
    target=HERE/'results.json'
    if '--check' in sys.argv:assert json.loads(target.read_bytes())==result
    else:target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary']))

if __name__=='__main__':main()
