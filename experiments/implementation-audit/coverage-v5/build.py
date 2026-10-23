"""Add newly admitted Mech profiles without changing frozen inspections or protection."""
import argparse,copy,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))
def summary(rows):
 editable=[r for r in rows if r['editable_source_scope']]
 return dict(profiles=len(rows),protected_upstream=sum(r['protected_upstream'] for r in rows),editable_profiles=len(editable),distinct_editable_source_bundles=len({tuple((s['sha256'],s['role']) for s in r['source_bundle'] if s['included_in_application_loc']) for r in editable}),reviewed_editable_profiles=sum(r['source_reviewed'] for r in editable),unreviewed_editable_profiles=sum(not r['source_reviewed'] for r in editable),unresolved_ownership_profiles=sum(r['ownership']=='unknown' and not r['protected_upstream'] for r in rows),supplemental_exact_source_profiles=sum(r['supplemental_source_review'] is not None for r in rows))
def build():
 baseline=HERE.parent/'coverage-v4/coverage.json';catalog=ROOT/'data/benchmarks.json';data=json.loads(catalog.read_bytes());old=json.loads(baseline.read_bytes());rows=copy.deepcopy(old['programs']);programs={**data.get('program_inventory',{}),**data['programs']}
 assert set(rows)<=set(programs)
 shared={'pidigits:mech-pi-advance-parent-20261022':'pidigits:mech-pi-final-advance-signed',**{f'revcomp:mech-revcomp-{name}-20261022':'revcomp:mech-revcomp-optimized' for name in ['parent','compacted','reused-4','reused-8']}}
 fresh={f'pidigits:mech-pi-{name}-20261022' for name in ['shared-numerator','compact-shared']}
 assert set(programs)-set(rows)==set(shared)|fresh
 review=ROOT/'experiments/mech/pidigits-performance-v1/RESULTS.md';readme=ROOT/'experiments/mech/pidigits-performance-v1/README.md'
 for key,parent in shared.items():
  p=programs[key];r=copy.deepcopy(rows[parent]);assert p['language']=='mech' and p['benchmark']==r['benchmark']
  assert set(p['files'])=={s['sha256'] for s in r['source_bundle']}
  assert p['authorship']['kind']=='unverified' and p['authorship']['origin_status']=='unresolved'
  assert r['ownership']=='unknown' and r['source_reviewed'] and not r['editable_source_scope'] and not r['protected_upstream']
  r['program']=key;r['retained_exact_source_review_from']=parent;r['new_native_or_count_qualification']=False;rows[key]=r
 for key in sorted(fresh):
  p=programs[key];assert p['language']=='mech' and p['benchmark']=='pidigits' and len(p['files'])==1
  assert p['authorship']['kind']=='ai-adapted' and p['authorship']['origin_status']=='unresolved'
  digest=p['files'][0];f=data['files'][digest];source=ROOT/f['archive_path'];assert sha(source)==digest
  bundle=[dict(sha256=digest,path=f['archive_path'],role='application',included_in_application_loc=True)]
  rows[key]=dict(program=key,language='mech',family='mech',benchmark='pidigits',ownership='derived-adapted',protected_upstream=False,editable_source_scope=True,source_reviewed=True,source_review_status='source-and-arithmetic-reuse-reviewed; qualifications-retained-separately',source_bundle=bundle,base_review_evidence=[],supplemental_source_review=dict(report=pin(review),document=pin(readme),source_sha256_reviewed=[digest],qualification_scope='Static inspection of the exact local derivative only. Existing native/count evidence remains separate; unresolved predecessor origin and licensing gaps are not repaired.'),new_native_or_count_qualification=False)
 identities={};missing=[]
 for key,r in rows.items():
  assert set(programs[key]['files'])=={s['sha256'] for s in r['source_bundle']},key
  for s in r['source_bundle']:
   digest=s['sha256'];assert hashlib.sha256(data['files'][digest]['code'].encode()).hexdigest()==digest
   path=ROOT/s['path'];assert s['path'] not in identities or identities[s['path']]==digest;identities[s['path']]=digest
   if path.is_file():assert sha(path)==digest
   elif not any(m['path']==s['path'] for m in missing):missing.append(dict(path=s['path'],source_sha256=digest,retained_representation='Exact UTF-8 source in data/benchmarks.json files[source_sha256].code'))
 groups=defaultdict(list)
 for row in rows.values():groups[row['family']].append(row)
 totals=summary(list(rows.values()));assert totals==dict(profiles=1077,protected_upstream=385,editable_profiles=641,distinct_editable_source_bundles=572,reviewed_editable_profiles=336,unreviewed_editable_profiles=305,unresolved_ownership_profiles=51,supplemental_exact_source_profiles=72),totals
 assert all(rows[k]==v for k,v in old['programs'].items())
 return dict(schema='exact-source-review-coverage.v5',inputs=[pin(p) for p in [Path(__file__),baseline,catalog,ROOT/'data/languages.json',review,readme]],policy=old['policy'],scope=old['scope'],summary=totals,retained_source_identities_rehashed=len(identities),missing_legacy_paths_with_verified_catalog_bytes=missing,source_review_statuses=dict(sorted(Counter(r['source_review_status'] for r in rows.values()).items())),families={f:summary(r) for f,r in sorted(groups.items())},programs=rows,reconciliation=dict(retained_profiles_unchanged=1070,new_profiles=7,exact_source_review_reused_profiles=5,local_derivative_source_inspections=2,origin_or_license_gaps_resolved=0,upstream_protection_changed=False),native_processes_started=0,new_benchmark_samples=0,canonical_changed=False,source_counts_changed=False,chart_admission=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();out=HERE/'coverage.json'
 if args.check:assert json.loads(out.read_bytes())==r
 else:
  with out.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 print(json.dumps(r['summary']))
