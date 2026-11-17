#!/usr/bin/env python3
"""Keep full trajectories in lossless evidence, with small previews in the campaign index."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from benchmark_suite import archive_evidence,save,seal_evidence,validate_campaign


def compact(directory):
    directory=Path(directory)
    path=directory/'campaign.json'
    original=path.read_bytes();campaign=json.loads(original)
    validate_campaign(directory,campaign)
    if campaign.get('index_compaction'):return campaign
    archive=directory/'complete-campaign.json.gz'
    archive.write_bytes(gzip.compress(original,mtime=0))
    if gzip.decompress(archive.read_bytes())!=original:raise ValueError('lossless campaign preservation failed')
    for result in campaign['results']:
        verification=result.get('verification',{})
        for field in ('outputs','before_execution','retained_outputs'):
            values=verification.get(field)
            if isinstance(values,list) and len(values)>6:
                verification[field[:-1]+'_count' if field!='outputs' else 'output_count']=len(values)
                verification['preview_'+field]=values[:3]+values[-3:]
                del verification[field]
    campaign['index_compaction']={'complete_campaign':'complete-campaign.json.gz',
        'sha256':hashlib.sha256(original).hexdigest(),'gzip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'note':'Full verification trajectories and all original fields are retained losslessly; accepted samples and contracts are unchanged.'}
    save(path,campaign)
    # Keep the already sealed raw archive byte-identical; add only new index/reproduction files.
    manifest=json.loads((directory/'evidence.json').read_text())
    for file in directory.rglob('*'):
        name=file.relative_to(directory).as_posix()
        if file.is_file() and not name.startswith('raw/') and file.name not in ('campaign.json','report.md','evidence.json','raw.tar.gz'):
            manifest['files'][name]=hashlib.sha256(file.read_bytes()).hexdigest()
    save(directory/'evidence.json',manifest)
    validate_campaign(directory,campaign)
    return campaign


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('campaign',type=Path);args=p.parse_args()
    compact(args.campaign);print('Compacted losslessly:',args.campaign)
