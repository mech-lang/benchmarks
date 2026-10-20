"""Prepare a guarded exact-source formatter overlay; never apply a catalog."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
PACKET=Path('experiments/source-formatting/v1')
PROFILE='knucleotide:nim-knucleotide-preencoded-v1'
SOURCE='b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b'
QUALIFICATION_SHA='ca06aec98485bd3af3b2cd3a9628785f997f931d141faa3a83ce96b02a919e79'
REVIEW_SHA='6f89bcaf526db39d3a4008751196fad785dafedb73d825dc0bde8beaca2a4efe'
FIELDS={'formatted_loc','formatted_loc_complete','formatted_loc_qualified','formatted_loc_status','formatted_loc_evidence','formatted_x'}

def encoded(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)

def format_evidence(report):
    run=PACKET/'nim-run-v1';replay=run/'replay-v1'
    return dict(key=PROFILE,language='nim',files=[dict(published_file=SOURCE,path=(run/'input.nim').as_posix(),sha256=SOURCE,
        language='nim',role='application',status='qualified',physical_loc=66,
        formatter_evidence=dict(provider='language-project',tool=dict(**report['formatter']['tool'],version='0.2'),
            official_sources=report['formatter']['official_sources'],config=report['formatter']['config'],
            input=dict(path=(run/'input.nim').as_posix(),sha256=SOURCE),
            output=dict(path=(run/'formatted.nim').as_posix(),sha256=report['formatted_sha256']),
            process_receipt=report['processes']['format']['receipt'],version_receipt=report['processes']['version']['receipt'],
            source_preservation_verified=True,ownership_verified=True,no_application_execution=True,
            native_preservation=report['native_preservation'],idempotence=report['idempotence']),
        counter_evidence=dict(definition='nonblank-noncomment-physical-lines-v1',function='mask_future',argument='nim',
            diagnostics=[],no_semantic_normalization=True,module_path='archive/validation/loc-normalization/20261012/foreign_future_mask.py',
            module_sha256='3b9a5c498459e5ae3ed04695faef938bbd15080c2c47ac1010ef87fb964cabd5',
            direct_adapter='Exact retained Nim operation for this non-BOM source; no owner counter.',
            row_ledger=dict(path=(replay/'row-ledger.json').as_posix(),sha256=report['row_ledger_sha256'])))],
        reasons=['Exact language-project nimpretty0.2 / Nim2.2.12, indent autodetect, width80; native AST/token equality and byte-idempotence, independently reviewable66-row physical ledger.'],
        qualification=dict(path=(replay/'qualification.json').as_posix(),sha256=QUALIFICATION_SHA),
        independent_review=dict(path=(run/'independent-review.json').as_posix(),sha256=REVIEW_SHA),
        limits=report['limits'])

def immutable_projection(data):
    result=copy.deepcopy(data)
    for pool in ('programs','program_inventory'):
        for row in result.get(pool,{}).values():
            for field in FIELDS:row.pop(field,None)
            for override in row.get('file_roles',{}).values():
                if isinstance(override,dict):override.pop('formatted_loc',None)
    for b in result['benchmarks']:
        b.pop('baseline_formatted_loc',None)
        for group in b['groups']:
            group.pop('formatted_fast',None);group.pop('formatted_small',None)
    result.pop('formatted_reference_summary',None)
    return result

def transform(before,report):
    require(report.get('profile')==PROFILE and report.get('source_sha256')==SOURCE and report.get('formatted_loc')==66
        and report.get('provider')=='language-project' and report.get('status')=='replayed-pending-independent-review','Wrong formatter qualification')
    data=copy.deepcopy(before);catalog={**data.get('program_inventory',{}),**data['programs']}
    require(PROFILE in catalog,'Missing exact Nim profile')
    row=catalog[PROFILE]
    require(row['language']=='nim' and row['benchmark']=='knucleotide' and row['files']==[SOURCE]
        and sha(data['files'][SOURCE]['code'].encode())==SOURCE,'Target source identity differs')
    require(row.get('formatted_loc') is None and row.get('formatted_loc_complete') is not True
        and row.get('formatted_loc_status')=='pending','Target is no longer the pending formatter profile')
    role=row.get('file_roles',{}).get(SOURCE,{})
    require(role.get('role','application')=='application' and not role.get('support_line_ranges')
        and role.get('included_in_application_loc',True) is True,'Target application partition differs')
    target_before=copy.deepcopy(row)
    for pool in ('programs','program_inventory'):
        if PROFILE not in data.get(pool,{}):continue
        target=data[pool][PROFILE]
        require(target==target_before,'Conflicting duplicate target profile')
        target.update(formatted_loc=66,formatted_loc_complete=True,formatted_loc_qualified=True,
            formatted_loc_status='qualified',formatted_loc_evidence=format_evidence(report))
        target.setdefault('file_roles',{}).setdefault(SOURCE,{})['formatted_loc']=66
    catalog={**data.get('program_inventory',{}),**data['programs']}
    for bench in data['benchmarks']:
        candidates=[catalog[key] for group in bench['groups'] for key in group['programs']
                    if catalog[key].get('eligible_for_chart') is not False]
        available=[r['formatted_loc'] for r in candidates if r.get('formatted_loc_complete') is True and r.get('formatted_loc')]
        if available:bench['baseline_formatted_loc']=min(available)
        for r in catalog.values():
            if r['benchmark']==bench['key'] and r.get('formatted_loc_complete') is True:
                r['formatted_x']=r['formatted_loc']/bench['baseline_formatted_loc']
        for group in bench['groups']:
            qualified=[catalog[key] for key in group['programs'] if catalog[key].get('eligible_for_chart') is not False and catalog[key].get('formatted_loc_complete') is True]
            timed=[r for r in qualified if r.get('seconds') is not None]
            group['formatted_fast']=min(timed,key=lambda r:(r['seconds'],r['formatted_loc'],r['key']))['key'] if timed else None
            group['formatted_small']=min(qualified,key=lambda r:(r['formatted_loc'],r.get('seconds') or math.inf,r['key']))['key'] if qualified else None
    # Reflect updated formatter coordinates in both ordered maps without touching
    # any source, sample, time, retained/logical count or canonical coordinate.
    for pool in ('programs','program_inventory'):
        data[pool]={key:copy.deepcopy(catalog[key]) for key in data.get(pool,{})}
    for reference in data.get('formatted_reference_summary',[]):
        selected=reference.get('measured_benchmarks')
        groups=[g for b in data['benchmarks'] if selected is None or b['key'] in selected for g in b['groups'] if g['language']==reference['lang']]
        for kind in ('fast','small'):
            rows=[catalog[g['formatted_'+kind]] for g in groups if g.get('formatted_'+kind)]
            if rows:reference[kind]=dict(x=statistics.geometric_mean(r['formatted_x'] for r in rows),y=statistics.geometric_mean(r['y'] for r in rows))
    require(immutable_projection(data)==immutable_projection(before),'Nonformatter catalog fields changed')
    old={**before.get('program_inventory',{}),**before['programs']}
    for key,r in catalog.items():
        if key!=PROFILE:
            require({f:r.get(f) for f in FIELDS-{'formatted_x'}}=={f:old[key].get(f) for f in FIELDS-{'formatted_x'}},'Another formatter measurement changed')
    return data

def _append_locked(before,root):
        root=Path(root).resolve()
        require(Path(__file__).resolve()==root/'tools/qualification/nim_formatted_overlay.py','Unexpected formatter module identity')
        require('nim_formatted_audit' not in before,'Formatter overlay already present')
        tool=root/PACKET/'replay_nim.py';spec=importlib.util.spec_from_file_location('closed_nim_formatter_replay',tool)
        replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay);report=replay.replay(check=True)
        qual=root/PACKET/'nim-run-v1/replay-v1/qualification.json';require(sha(qual.read_bytes())==QUALIFICATION_SHA,'Qualification drift')
        review=root/PACKET/'nim-run-v1/independent-review.json';require(sha(review.read_bytes())==REVIEW_SHA,'Independent review drift')
        after=transform(before,report)
        after['nim_formatted_audit']=dict(schema='exact-source-nim-formatted-overlay.v1',profile=PROFILE,source_sha256=SOURCE,
            formatted_loc=66,provider='language-project',qualification_sha256=QUALIFICATION_SHA,independent_review_sha256=REVIEW_SHA,
            producer=dict(path='tools/qualification/nim_formatted_overlay.py',sha256=sha(Path(__file__).read_bytes())),
            source_bytes_changed=False,timing_samples_changed=False,retained_loc_changed=False,old_formatter_measurements_changed=False)
        return after

def append_catalog(before,root=ROOT,*,common_fd=None):
    """Replay only this formatter overlay; no writes/native execution.

    A guarded caller may pass its already-held mutex descriptor. Ordinary
    historical replay takes the same lock nonblocking for lexical replay.
    """
    if common_fd is not None:
        actual,named=__import__('os').fstat(common_fd),Path('/tmp/mech-clbg-timing.lock').stat()
        require((actual.st_dev,actual.st_ino)==(named.st_dev,named.st_ino),'Wrong common descriptor')
        fcntl.flock(common_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _append_locked(before,root)
    with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _append_locked(before,root)

def prepare(output):
    with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        raw=(ROOT/'data/benchmarks.json').read_bytes();before=json.loads(raw)
        after=append_catalog(before,ROOT,common_fd=lock.fileno());after_raw=encoded(after)
        require(not output.exists(),'Fresh proposal directory required');output.mkdir(parents=True)
        (output/'.build').mkdir();(output/'.build/candidate-data.json').write_bytes(after_raw)
        proposal=dict(schema='guarded-nim-formatted-overlay-proposal.v1',status='prepared-pending-independent-review',
            base_catalog_sha256=sha(raw),candidate_catalog_sha256=sha(after_raw),profile=PROFILE,source_sha256=SOURCE,
            formatted_loc=66,qualification_sha256=QUALIFICATION_SHA,producer_sha256=sha(Path(__file__).read_bytes()),
            independent_review_sha256=REVIEW_SHA,candidate_catalog_path=(output/'.build/candidate-data.json').relative_to(ROOT).as_posix(),
            formatter_fields_only=True,source_bytes_changed=False,timing_samples_changed=False,retained_loc_changed=False,
            old_formatter_measurements_changed=False,canonical_applied=False,program_packages_changed=False,
            native_processes_executed=0,application_execution=False,
            apply_guard='Root must independently review and require exact base/candidate/qualification/producer hashes; no apply command exists here.')
        (output/'proposal.json').write_bytes(encoded(proposal))
    return proposal

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(prepare(args.prepare.resolve())))
if __name__=='__main__':main()
