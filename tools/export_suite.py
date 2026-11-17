#!/usr/bin/env python3
"""Export modern campaigns beside (never into) the historical cross-language dataset."""
import json
from pathlib import Path
import shutil
import gzip

from benchmark_suite import ROOT, SCHEMA, load_catalog, validate_campaign, EvidenceReader


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
    # Validate every incoming record before replacing the last successful export.
    if evidence.exists():
        shutil.rmtree(evidence)
    for path,campaign in validated:
        # Preserve raw requests, stdout, supervision outcomes and reports as inspectable downloads.
        destination = evidence / path.parent.name
        destination.mkdir(parents=True)
        for item in path.parent.rglob('*'):
            if item.is_file() and item.suffix in ('.json', '.txt', '.md', '.mec', '.rs', '.toml', '.lock', '.gz') and 'raw' not in item.relative_to(path.parent).parts:
                target = destination / item.relative_to(path.parent)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, target)
        with EvidenceReader(path.parent) as reader:
            for name in reader.manifest['files']:
                if name.startswith('raw/'):
                    target=destination/name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(reader.read(name))
            if reader.manifest.get('archives'):campaign['raw_archive']='raw.tar.gz'
        campaign['evidence_path'] = 'campaign-evidence/' + path.parent.name
        for record in campaign['results']:
            verification=record.get('verification',{})
            outputs=verification.get('outputs')
            if isinstance(outputs,list):
                verification['output_count']=len(outputs)
                verification['preview_outputs']=outputs if len(outputs)<=6 else outputs[:3]+outputs[-3:]
                del verification['outputs']
        campaigns.append(campaign)
    bundle = {'schema': 'mech.benchmark-dashboard.v1', 'catalog': catalog,
              'campaigns': sorted(campaigns, key=lambda c: c['started_at'])}
    payload=(json.dumps(bundle,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    (output / 'campaigns.json').write_bytes(payload)
    (output / 'campaigns.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    return bundle


if __name__ == '__main__':
    export(ROOT / 'site/public')
