"""Independently reconcile the published selection summary with all primary reports."""
import json,hashlib,statistics
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(STUDY/'plan.json');selection=read(STUDY/'credit-selection.json')
assert selection['source']==plan['source_commit']
assert selection['source_visits_per_funded_batch']==1024 and selection['credit_capacity']==64 and selection['headroom']==4
expected_batches=sum((125000000-width+2+1023)//1024 for width in [1,2,3,4,6,12,18])
assert expected_batches==854497
receipts=[]
for session in [1,2]:
 folder=HERE/f'full-scalar-tail-registers-v{session}'
 full=read(folder/'results.json');rows=[r for r in full['samples'] if r['subject']=='candidate']
 assert len(rows)==6
 claims=[]
 for row in rows:
  receipt=HERE/row['process'];native=receipt.parent.with_name(receipt.parent.name+'.native.json')
  assert sha(native)==row['native_sha256']
  n=read(native)
  assert n['native_worker_credit_batches']==expected_batches and n['native_hash_table_updates']==874999961
  claims.append(n['native_worker_credit_claims']);receipts.append(dict(path=str(native.relative_to(HERE)),sha256=sha(native)))
 expected=dict(session=session,batches=expected_batches,median_claims=statistics.median(claims),minimum_claims=min(claims),maximum_claims=max(claims),batches_per_claim=expected_batches/statistics.median(claims))
 assert selection['sessions'][session-1]==expected
result=dict(status='all-twelve-full-credit-selections-and-summary-reconciled',source_commit=plan['source_commit'],original_updates=874999961,full_billing_batches=expected_batches,selection_sha256=sha(STUDY/'credit-selection.json'),verifier_sha256=sha(Path(__file__)),native_reports=receipts)
(STUDY/'selection-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'])
