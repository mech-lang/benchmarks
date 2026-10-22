"""Preserve frozen inspection coverage while enforcing captured published-source protection."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def pin(p):return dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())

def summary(rows):
    editable=[r for r in rows if r['editable_source_scope']]
    bundles={tuple((s['sha256'],s['role']) for s in row['source_bundle'] if s['included_in_application_loc']) for row in editable}
    return dict(profiles=len(rows),protected_upstream=sum(r['protected_upstream'] for r in rows),editable_profiles=len(editable),
                distinct_editable_source_bundles=len(bundles),reviewed_editable_profiles=sum(r['source_reviewed'] for r in editable),
                unreviewed_editable_profiles=sum(not r['source_reviewed'] for r in editable),
                unresolved_ownership_profiles=sum(r['ownership']=='unknown' and not r['protected_upstream'] for r in rows),
                supplemental_exact_source_profiles=sum(r['supplemental_source_review'] is not None for r in rows))

def build():
    baseline=HERE.parent/'coverage-v3/coverage.json';evidence=HERE.parent/'upstream-protection-v1/results.json'
    result=json.loads(baseline.read_bytes());protection=json.loads(evidence.read_bytes())
    assert protection['status']=='34-profiles-26-application-sources-verified-against-captured-originals'
    catalog=ROOT/'data/benchmarks.json';assert any(p==pin(catalog) for p in protection['inputs'])
    for row in protection['inputs']:assert pin(ROOT/row['path'])==row
    for key,entry in protection['profiles'].items():
        row=result['programs'][key];assert not row['protected_upstream'] and row['editable_source_scope']
        assert row['source_bundle']==entry['source_bundle']
        row['protected_upstream']=True;row['editable_source_scope']=False
        row['published_source_protection']=dict(evidence=pin(evidence),basis='Complete application bytes match captured external published source; adaptation flags do not authorize rewriting it.',authorship_reclassified=False)
    catalog_data=json.loads(catalog.read_bytes())
    groups=defaultdict(list)
    for row in result['programs'].values():
        for source in row['source_bundle']:
            path=ROOT/source['path']
            if path.is_file():assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
            else:
                assert hashlib.sha256(catalog_data['files'][source['sha256']]['code'].encode()).hexdigest()==source['sha256']
        groups[row['family']].append(row)
    result['families']={family:summary(rows) for family,rows in sorted(groups.items())}
    result['summary']=summary(list(result['programs'].values()))
    assert result['summary']['profiles']==1070 and result['summary']['protected_upstream']==385
    assert result['summary']['editable_profiles']==639 and result['summary']['reviewed_editable_profiles']==334 and result['summary']['unreviewed_editable_profiles']==305
    result['schema']='exact-source-review-coverage.v4'
    result['inputs'].extend([pin(Path(__file__)),pin(baseline),pin(evidence)])
    result['reconciliation']=dict(baseline=pin(baseline),protection=pin(evidence),new_source_reviews=0,
        explanation='Protect 34 matching published profiles across 26 source blobs without granting any native/count qualification or changing historical attribution. All 34 leave the unreviewed editable queue; no static inspection is newly claimed.')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r=build();p=HERE/'coverage.json'
    if args.check:assert json.loads(p.read_bytes())==r
    else:
        with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r['summary']))
