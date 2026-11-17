#!/usr/bin/env python3
"""Export modern campaigns beside (never into) the historical cross-language dataset."""
import json
from pathlib import Path
import shutil

from benchmark_suite import ROOT, SCHEMA, load_catalog


def export(output):
    output = Path(output)
    catalog = load_catalog()
    campaigns = []
    evidence = output / 'campaign-evidence'
    # Rebuilding must also remove campaigns that were removed from the input.
    if evidence.exists():
        shutil.rmtree(evidence)
    directory = ROOT / 'results/campaigns'
    for path in sorted(directory.glob('*/campaign.json')):
        campaign = json.loads(path.read_text())
        if campaign.get('schema') != SCHEMA:
            raise ValueError(f'unsupported campaign schema: {path}')
        if campaign['id'] != path.parent.name:
            raise ValueError(f'campaign identity does not match directory: {path}')
        # Preserve raw requests, stdout, supervision outcomes and reports as inspectable downloads.
        destination = evidence / path.parent.name
        destination.mkdir(parents=True)
        for item in path.parent.rglob('*'):
            if item.is_symlink():
                raise ValueError(f'symlink in campaign evidence: {item}')
            if item.is_file() and item.suffix in ('.json', '.txt', '.md', '.mec'):
                target = destination / item.relative_to(path.parent)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, target)
        campaign['evidence_path'] = 'campaign-evidence/' + path.parent.name
        campaigns.append(campaign)
    bundle = {'schema': 'mech.benchmark-dashboard.v1', 'catalog': catalog,
              'campaigns': sorted(campaigns, key=lambda c: c['started_at'])}
    (output / 'campaigns.json').write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + '\n')
    return bundle


if __name__ == '__main__':
    export(ROOT / 'site/public')
