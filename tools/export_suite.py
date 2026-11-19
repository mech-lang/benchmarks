#!/usr/bin/env python3
"""Export modern campaigns beside (never into) the historical cross-language dataset."""
import json
from pathlib import Path
import shutil
import gzip
import hashlib
import math
import re

from reference_sources import source_link, mech_source_link
from benchmark_suite import ROOT, SCHEMA, load_catalog, validate_campaign, EvidenceReader


def archive_locations(root, campaigns):
    path=root/'suite/evidence-hosting.json'
    if not path.exists():return {}
    policy=json.loads(path.read_text())
    if policy.get('schema')!='mech.benchmark-evidence-hosting.v1' or not re.fullmatch('[0-9a-f]{40}',policy.get('source_commit','')):
        raise ValueError('invalid immutable archive hosting policy')
    by_id={c['id']:p.parent for p,c in campaigns}
    locations={}
    for identifier,pin in policy['archives'].items():
        if identifier not in by_id:raise ValueError('archive hosting refers to missing campaign')
        archive=by_id[identifier]/'raw.tar.gz'
        if not archive.is_file() or archive.stat().st_size!=pin['bytes'] or hashlib.sha256(archive.read_bytes()).hexdigest()!=pin['sha256']:
            raise ValueError('immutable archive hosting pin differs from retained bytes')
        locations[identifier]={**pin,'url':f"https://raw.githubusercontent.com/mech-lang/benchmarks/{policy['source_commit']}/results/campaigns/{identifier}/raw.tar.gz"}
    return locations


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
    archives=archive_locations(root,validated)
    external={}
    # Validate every incoming record before replacing the last successful export.
    for directory in (evidence, output/'campaign-details'):
        if directory.exists():shutil.rmtree(directory)
    definitions={case['id']:case for case in catalog['cases']}
    def write_json(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
    for path,campaign in validated:
        # The page only needs supervision receipts. Complete requests, stdout,
        # reproduction sources and binaries remain in the immutable archive/repo.
        destination = evidence / path.parent.name
        destination.mkdir(parents=True)
        compressed={}
        def write_evidence(name,content):
            target=destination/name
            target.parent.mkdir(parents=True,exist_ok=True)
            packed=gzip.compress(content,mtime=0) if len(content)>64*1024 and not name.endswith('.gz') else None
            if packed is not None and len(packed)<len(content):
                target=target.with_name(target.name+'.gz')
                target.write_bytes(packed)
                compressed[name]=name+'.gz'
            else:target.write_bytes(content)
        for item in path.parent.rglob('*'):
            if item.is_file() and item.suffix in ('.json', '.txt', '.md', '.mec', '.rs', '.c', '.h', '.toml', '.lock', '.gz') and 'raw' not in item.relative_to(path.parent).parts:
                if item.name=='raw.tar.gz' and campaign['id'] in archives:continue
                name=item.relative_to(path.parent).as_posix()
                if campaign['id'] in archives and name not in {'campaign.json','report.md','evidence.json'}:continue
                write_evidence(name,item.read_bytes())
        with EvidenceReader(path.parent) as reader:
            for name in reader.manifest['files']:
                if name.startswith('raw/') and name.endswith('/supervised.json'):
                    write_evidence(name,reader.read(name))
            if reader.manifest.get('archives'):campaign['raw_archive']='raw.tar.gz'
            if compressed:campaign['compressed_evidence']=compressed
        if campaign['id'] in archives:
            pin=archives[campaign['id']]
            campaign['raw_archive_url']=pin['url']
            campaign['reproduction_url']=pin['url'].replace('raw.githubusercontent.com','github.com').replace('/benchmarks/','/benchmarks/tree/',1).removesuffix('/raw.tar.gz')
            external['campaign-evidence/'+campaign['id']+'/raw.tar.gz']=pin
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
        detail_root='campaign-details/'+campaign['id']
        context_path=detail_root+'/context.json'
        write_json(output/context_path,{'schema':'mech.benchmark-context.v1',
            'campaign':{k:v for k,v in campaign.items() if k not in {'results','order'}}})
        index={k:campaign[k] for k in ('id','started_at','complete')}
        index['workers']={lane:{'revision':worker['revision']} for lane,worker in campaign.get('workers',{}).items() if 'revision' in worker}
        index['context_path']=context_path
        index['results']=[]
        for number,record in enumerate(campaign['results']):
            detail_path=f'{detail_root}/{number:04}.json'
            write_json(output/detail_path,{'schema':'mech.benchmark-observation.v1','campaign_id':campaign['id'],
                'definition':definitions.get(record['case_id'],{k:record[k] for k in ('title','family','progress') if k in record}|{'id':record['case_id']}),'record':record})
            summary={k:record[k] for k in ('case_id','title','family','backend','lane','revision','progress','capability','outcome',
                'task_hash','measurement_hash','source_sha256','environment_hash','feature_profile','control_contract') if k in record}
            summary['measurement']={k:v for k,v in record.get('measurement',{}).items() if k in {'primary_metric','metric_mapping','comparison_note'}}
            summary['summary']={key:{'median':value['median'],'samples':len(value.get('samples',[]))} for key,value in record.get('summary',{}).items()}
            summary['detail_path']=detail_path
            reference=source_link(record,campaign,output,root)
            if reference:summary['reference_url']=reference
            implementation=mech_source_link(record,output)
            if implementation:summary['source_url']=implementation
            index['results'].append(summary)
        campaigns.append(index)
    catalog_summary={k:catalog[k] for k in ('schema','candidate_revision') if k in catalog}
    catalog_summary['cases']=[{k:case[k] for k in ('id','title','family','progress','backends') if k in case} for case in catalog['cases']]
    bundle = {'schema': 'mech.benchmark-dashboard.v2', 'catalog': catalog_summary,'control_policy':policy,
              'campaigns': sorted(campaigns, key=lambda c: c['started_at']),'external_evidence':external}
    payload=(json.dumps(bundle,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    (output / 'campaigns.json').write_bytes(payload)
    (output / 'campaigns.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    return bundle


if __name__ == '__main__':
    export(ROOT / 'site/public')
