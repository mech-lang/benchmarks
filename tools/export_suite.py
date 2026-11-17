#!/usr/bin/env python3
"""Export modern campaigns beside (never into) the historical cross-language dataset."""
import json
from pathlib import Path
import shutil
import gzip
import hashlib
import math

from benchmark_suite import ROOT, SCHEMA, load_catalog, validate_campaign, EvidenceReader


def control_policy(root, campaigns):
    path=root/'suite/control-policy.json'
    policy=json.loads(path.read_text()) if path.exists() else {'schema':'mech.benchmark-controls.v1','default':'rust','controls':[]}
    if policy.get('schema')!='mech.benchmark-controls.v1' or policy.get('default')!='rust':
        raise ValueError('invalid benchmark control policy')
    identities=set()
    for held in policy['controls']:
        key=held['case_id'],held['backend'],held['metric']
        if key in identities:raise ValueError('duplicate retained control')
        identities.add(key)
        found=[(path,c) for path,c in campaigns if c['id']==held['campaign_id']]
        if len(found)!=1:raise ValueError('retained control campaign missing')
        campaign_path,campaign=found[0]
        records=[r for r in campaign['results'] if r['case_id']==held['case_id'] and r['backend']==held['backend'] and r['lane']=='candidate' and r['outcome']=='ok']
        if len(records)!=1 or held['metric'] not in records[0]['summary']:raise ValueError('retained control observation missing')
        qualification=(campaign_path.parent/held['qualification']).resolve()
        if not qualification.is_relative_to(campaign_path.parent.resolve()):raise ValueError('invalid control qualification path')
        raw=qualification.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=held['qualification_sha256']:raise ValueError('control qualification changed')
        proof=json.loads(raw)
        from import_related_posts import VARIANTS
        variant=VARIANTS.get(held['backend'])
        for cohort,pairs in [('primary',31),('confirmation',13)]:
            comparisons=[x for x in proof['comparisons'] if x['variant']==variant and x['cohort']==cohort]
            if len(comparisons)!=1:raise ValueError('control needs primary and independent confirmation')
            comparison=comparisons[0]
            if comparison['pairs']!=pairs or comparison['reference']!='rust-preinitialized' or comparison['bootstrap95_percent'][1]>=0:
                raise ValueError('control promotion is not confirmed against fixed Rust')
            if cohort=='confirmation' and not math.isclose(comparison['median_ms']/1000,records[0]['summary'][held['metric']]['median'],rel_tol=0,abs_tol=1e-15):
                raise ValueError('retained control differs from confirmed checkpoint')
    return policy


def export(output, root=ROOT):
    output = Path(output)
    root = Path(root)
    catalog = load_catalog(root / 'suite/catalog.json', root=root)
    campaigns = []
    evidence = output / 'campaign-evidence'
    validated = []
    directory = root / 'results/campaigns'
    for path in sorted(directory.glob('*/campaign.json')):
        campaign = json.loads(path.read_text())
        if campaign.get('schema') != SCHEMA:
            raise ValueError(f'unsupported campaign schema: {path}')
        if campaign['id'] != path.parent.name:
            raise ValueError(f'campaign identity does not match directory: {path}')
        if not campaign.get('complete'):
            print(f'Skipping incomplete campaign: {path.parent.name}')
            continue
        validate_campaign(path.parent, campaign)
        if path.parent.is_symlink() or any(item.is_symlink() for item in path.parent.rglob('*')):
            raise ValueError(f'symlink in campaign evidence: {path.parent}')
        validated.append((path,campaign))
    policy=control_policy(root,validated)
    # Validate every incoming record before replacing the last successful export.
    if evidence.exists():
        shutil.rmtree(evidence)
    for path,campaign in validated:
        # Preserve raw requests, stdout, supervision outcomes and reports as inspectable downloads.
        destination = evidence / path.parent.name
        destination.mkdir(parents=True)
        for item in path.parent.rglob('*'):
            if item.is_file() and item.suffix in ('.json', '.txt', '.md', '.mec', '.rs', '.c', '.h', '.toml', '.lock', '.gz') and 'raw' not in item.relative_to(path.parent).parts:
                target = destination / item.relative_to(path.parent)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, target)
        with EvidenceReader(path.parent) as reader:
            for name in reader.manifest['files']:
                if name.startswith('raw/'):
                    if name.endswith('.class'):
                        continue  # Compiled JVM products and their exact names remain in the lossless archive.
                    target=destination/name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    content=reader.read(name)
                    if len(content)>4*1024*1024:
                        target=target.with_name(target.name+'.gz')
                        target.write_bytes(gzip.compress(content,mtime=0))
                    else:
                        target.write_bytes(content)
            if reader.manifest.get('archives'):campaign['raw_archive']='raw.tar.gz'
        campaign['evidence_path'] = 'campaign-evidence/' + path.parent.name
        for record in campaign['results']:
            verification=record.get('verification',{})
            outputs=verification.get('outputs')
            if isinstance(outputs,list):
                verification['output_count']=len(outputs)
                verification['preview_outputs']=outputs if len(outputs)<=6 else outputs[:3]+outputs[-3:]
                del verification['outputs']
            for field in ('before_execution','retained_outputs'):
                values=verification.get(field)
                if isinstance(values,list) and len(values)>6:
                    verification[field+'_count']=len(values)
                    verification['preview_'+field]=values[:3]+values[-3:]
                    del verification[field]
        campaigns.append(campaign)
    bundle = {'schema': 'mech.benchmark-dashboard.v1', 'catalog': catalog,'control_policy':policy,
              'campaigns': sorted(campaigns, key=lambda c: c['started_at'])}
    payload=(json.dumps(bundle,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    (output / 'campaigns.json').write_bytes(payload)
    (output / 'campaigns.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    return bundle


if __name__ == '__main__':
    export(ROOT / 'site/public')
