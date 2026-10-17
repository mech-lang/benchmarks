#!/usr/bin/env python3
"""Verify a published Pages build from its exact publication receipt and assets.

Runs once: exit 75 means deployment is pending; no success receipt is written.
No build, push, benchmark, automatic retry or repository modification occurs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.parse
import urllib.request

BASE='https://mech-lang.org/benchmarks/'
API='https://gitlab.com/api/v4/projects/5692990/'
PIPELINE_UI='https://gitlab.com/mech-lang/web/website/-/pipelines/'
USER_AGENT=f'Python-urllib/{sys.version_info.major}.{sys.version_info.minor}'


def require(value,message):
    if not value:raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={
        'Accept-Encoding':'identity','Cache-Control':'no-cache',
        'User-Agent':USER_AGENT}),timeout=50)


def fetch(url):
    with request(url) as response:
        require(response.status==200,'Unexpected HTTP status')
        raw=response.read(4*1024*1024+1)
        require(len(raw)<=4*1024*1024,'Metadata response exceeds bounded size')
        return raw


def paged_jobs(pipeline_id,nonce):
    jobs=[]
    for page in range(1,11):
        url=API+'pipelines/'+str(pipeline_id)+'/jobs?'+urllib.parse.urlencode(
            dict(per_page=100,page=page,include_retried='false',probe=nonce))
        with request(url) as response:
            require(response.status==200,'Unexpected jobs HTTP status')
            raw=response.read(4*1024*1024+1)
            require(len(raw)<=4*1024*1024,'Jobs response exceeds bounded size')
            values=json.loads(raw);require(type(values) is list,'Invalid job listing')
            jobs.extend(values)
            following=response.headers.get('X-Next-Page','')
        if not following:return jobs
        require(following==str(page+1),'Unexpected jobs pagination')
    raise RuntimeError('Unexpectedly large pipeline job inventory')


def check_local_assets(directory,manifest):
    names=set(manifest['files'])|{'build.json'}
    require({p.name for p in directory.iterdir()}==names,'Local asset inventory differs')
    files={}
    for name,wanted in manifest['files'].items():
        require(type(name) is str and re.fullmatch('[A-Za-z0-9_.-]+',name) and name not in ('.','..') and
                type(wanted) is str and re.fullmatch('[0-9a-f]{64}',wanted),'Invalid manifest entry')
        path=directory/name
        require(path.is_file() and not path.is_symlink() and path.resolve().parent==directory,
                'Unsafe local asset: '+name)
        require(file_digest(path)==wanted,'Local asset differs from reviewed manifest: '+name)
        files[name]=dict(sha256=wanted,bytes=path.stat().st_size)
    return files


def pending(observation,stage,**details):
    value=dict(observation,status='pending',stage=stage,
               observed_at=datetime.now(timezone.utc).isoformat(),**details)
    print(json.dumps(value),flush=True)
    raise SystemExit(75)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publication-receipt',type=Path,required=True)
    parser.add_argument('--site-public',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    publication_path=args.publication_receipt.resolve();directory=args.site_public.resolve();output=args.output.resolve()
    require(not output.exists(),'Verification output must be fresh')
    require(output not in (publication_path,directory/'build.json') and not output.is_relative_to(directory),
            'Verification output overlaps inputs')
    publication_raw=publication_path.read_bytes();publication=json.loads(publication_raw)
    require(publication['schema']=='benchmark-pages-publication.v1' and
            publication['status']=='pushed-awaiting-live-pages-verification' and
            publication['remote_ref_verified'] is True and type(publication['asset_count']) is int and publication['asset_count']>0,
            'Expected an actual successful website push receipt')
    for key in ('benchmark_source_commit','website_commit','website_base','website_tree'):
        require(type(publication[key]) is str and re.fullmatch('[0-9a-f]{40}',publication[key]),'Invalid '+key)
    for key in ('build_manifest_sha256','dataset_sha256'):
        require(type(publication[key]) is str and re.fullmatch('[0-9a-f]{64}',publication[key]),'Invalid '+key)
    require(type(publication['build_version']) is str and re.fullmatch('[0-9a-f]{16}',publication['build_version']),
            'Invalid build version')
    manifest_path=directory/'build.json'
    require(manifest_path.is_file() and not manifest_path.is_symlink(),'Regular local build manifest required')
    manifest_raw=manifest_path.read_bytes();manifest=json.loads(manifest_raw)
    require(digest(manifest_raw)==publication['build_manifest_sha256'] and
            manifest['version']==publication['build_version'] and type(manifest['files']) is dict and
            len(manifest['files'])==publication['asset_count'] and manifest['files'].get('data.json')==publication['dataset_sha256'],
            'Publication and local build manifest disagree')
    local=check_local_assets(directory,manifest)
    commit=publication['website_commit'];nonce=str(time.time_ns())
    listing=json.loads(fetch(API+'pipelines?'+urllib.parse.urlencode(
        dict(sha=commit,ref='main',per_page=100,probe=nonce))))
    require(type(listing) is list,'Invalid pipeline listing')
    candidates=[p for p in listing if p.get('sha')==commit and p.get('ref')=='main']
    # Live bytes are inspected even when GitLab has not exposed its deploy job.
    live=fetch(BASE+'build.json?verify='+nonce)
    observation=dict(website_commit=commit,expected_build=manifest['version'],
                     observed_build=json.loads(live).get('version'))
    if not candidates:pending(observation,'pipeline-discovery')
    selected=max(candidates,key=lambda p:p['id'])
    pipeline=json.loads(fetch(API+'pipelines/'+str(selected['id'])+'?probe='+nonce))
    require(pipeline['sha']==commit and pipeline['ref']=='main','Selected pipeline identity differs')
    jobs=paged_jobs(pipeline['id'],nonce)
    pages=[j for j in jobs if j.get('name')=='pages']
    observation['pipeline']={key:pipeline.get(key) for key in ('id','sha','status','web_url','finished_at')}
    observation['jobs']=[{key:j.get(key) for key in ('id','name','status','web_url','finished_at')} for j in pages]
    if pipeline['status']!='success' or not pages or any(j['status']!='success' for j in pages):
        pending(observation,'pipeline')
    if live!=manifest_raw:pending(observation,'live-manifest')

    def verify(item):
        name,expected=item;measured=hashlib.sha256();size=0
        # Match the application's versioned dataset/module/style URLs and its
        # bare HTML entry point. Other retained reports use a fresh probe.
        query=urllib.parse.urlencode(dict(v=manifest['version'])) if name in ('data.json','data.json.gz') or name.endswith(('.mjs','.css')) else 'verify='+nonce
        url=BASE if name=='index.html' else BASE+urllib.parse.quote(name,safe='')+'?'+query
        try: response=request(url)
        except Exception as error: raise RuntimeError('Live asset request failed: '+name) from error
        with response:
            require(response.status==200,'Unexpected live asset status: '+name)
            for chunk in iter(lambda:response.read(1024*1024),b''):
                size+=len(chunk)
                require(size<=expected['bytes'],'Live asset exceeds expected size: '+name)
                measured.update(chunk)
        return name,dict(sha256=measured.hexdigest(),bytes=size)

    with ThreadPoolExecutor(max_workers=4) as pool:
        files=dict(pool.map(verify,local.items()))
    require(len(files)==publication['asset_count'],'Live asset inventory incomplete')
    mismatches={name:dict(expected=local[name],observed=row) for name,row in files.items() if row!=local[name]}
    if mismatches:pending(observation,'live-assets',mismatches=mismatches)
    require(files['data.json']['sha256']==publication['dataset_sha256'],'Live dataset differs')
    internal=[];inspection_error=None
    try:
        ui=json.loads(fetch(PIPELINE_UI+str(pipeline['id'])+'.json?probe='+nonce))
        require(ui['commit']['id']==commit,'Pipeline UI commit differs')
        internal=[dict(id=j['id'],name=j['name'],status=j['status']['group'],
                       web_url='https://gitlab.com'+j['build_path'])
                  for stage in ui['details']['stages'] for group in stage['groups'] for j in group['jobs']
                  if j['name']=='pages:deploy']
    except Exception as error:
        inspection_error=str(error)[:500]
    # The exact live assets are authoritative. The implicit deployment job is
    # retained when visible; missing UI metadata is never fabricated as success.
    require(publication_path.read_bytes()==publication_raw and manifest_path.read_bytes()==manifest_raw,
            'Publication or local manifest changed during verification')
    require(check_local_assets(directory,manifest)==local,'Local assets changed during verification')
    final_live=fetch(BASE+'build.json?verify=final-'+str(time.time_ns()))
    if final_live!=manifest_raw:pending(observation,'final-live-manifest')
    receipt=dict(schema='benchmark-pages-deployment.v1',status='passed',
        verified_at=datetime.now(timezone.utc).isoformat(),url=BASE,
        benchmark_source_commit=publication['benchmark_source_commit'],website_commit=commit,
        prior_website_commit=publication['website_base'],website_tree=publication['website_tree'],
        build_version=manifest['version'],build_manifest_sha256=publication['build_manifest_sha256'],
        dataset_sha256=publication['dataset_sha256'],publication_receipt_sha256=digest(publication_raw),
        verified_assets=publication['asset_count'],files=files,request_user_agent=USER_AGENT,pipeline=observation['pipeline'],jobs=observation['jobs'],
        pages_deployment_jobs=internal,live_manifest_rechecked_after_assets=True,
        dataset_requested_with_application_build_version=manifest['version'])
    if inspection_error is not None:receipt['pages_deployment_job_inspection_error']=inspection_error
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps({key:value for key,value in receipt.items() if key!='files'},indent=2),flush=True)


if __name__=='__main__':main()
