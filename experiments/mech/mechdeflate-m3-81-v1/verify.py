"""Verify archived M3 observations independently, including rejected trials."""
import argparse
from hashlib import file_digest
import json
from pathlib import Path
from runpy import run_path
import shutil,sys,tarfile

HERE=Path(__file__).resolve().parent
ROUTES=HERE.parent/'mechdeflate-phase-routes-v1'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()
def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,required=True,help='New directory for extracted evidence.')
    parser.add_argument('--all-studies',action='store_true',help='Also recompute every exploratory timing study.')
    parser.add_argument('--study',action='append',help='Recompute these recorded roles instead of the two qualification runs.')
    args=parser.parse_args();out=args.output.resolve()
    if out.exists() and any(out.iterdir()):parser.error('Choose a new or empty directory.')
    out.mkdir(parents=True,exist_ok=True)
    manifest=read(HERE/'evidence/manifest.json')
    for archive in manifest['archives']:
        source=HERE/'evidence'/archive['file'];assert sha(source)==archive['sha256']
        with tarfile.open(source,'r:gz') as stream:
            for member in stream.getmembers():
                if not member.isfile():raise ValueError('Only regular evidence files are admitted.')
                target=(out/member.name).resolve();target.relative_to(out)
                target.parent.mkdir(parents=True,exist_ok=True)
                with stream.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
    for relative,digest in manifest['files_sha256'].items():assert sha(out/relative)==digest,relative
    sys.path.insert(0,str(ROUTES));verify=run_path(str(ROUTES/'verify_timings.py'))['verify']
    oracle={v['case']:v for v in read(HERE/'support/libdeflate-output-oracle.json')}
    studies=read(HERE/'studies.json')
    selected=set(args.study or ['llvm-oz-primary','llvm-oz-confirmation'])
    reports=[]
    for study in studies:
        if not study.get('verified'):continue
        if not args.all_studies and study['name'] not in selected:continue
        directory=out/study['archive_directory']
        reports.append(verify(directory,directory/(study['name']+'-results.json'),study['name'],oracle))
    assert reports,'No selected study was found.'
    if not args.all_studies:assert {v['role'] for v in reports}==selected
    result={'verified_archives':len(manifest['archives']),'verified_files':len(manifest['files_sha256']),
            'observations_recomputed':sum(v['runtime_observations_recomputed'] for v in reports),'studies':reports}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
