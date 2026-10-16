#!/usr/bin/env python3
"""Publish only an already-built site/public directory, with an exact main lease.

This script performs publication when invoked. It neither builds the site nor
fetches benchmark history. The caller supplies reviewed build/source identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import tempfile

HOST='mac-mini-runner'
STAGING='/tmp/mech-julia-aot-full81-pages-20261015'
BARE='/Users/coreymontella/mech-lang/website-benchmark-pages-publish.git'

REMOTE=r'''
import hashlib,json,os,pathlib,re,subprocess,sys,tarfile,urllib.parse
from datetime import datetime,timezone
root=pathlib.Path(sys.argv[1]);bare=pathlib.Path(sys.argv[2])
source,manifest_sha,version,dataset_sha,archive_sha=sys.argv[3:8]
def check(value,message):
    if not value:raise RuntimeError(message)
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()
def save(name,value):
    with (root/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
check(re.fullmatch('[0-9a-f]{40}',source),'Invalid source commit')
check(all(re.fullmatch('[0-9a-f]{64}',s) for s in (manifest_sha,dataset_sha,archive_sha)),'Invalid digest')
check(re.fullmatch('[0-9a-f]{16}',version),'Invalid build version')
check(bare.is_dir(),'Missing established publishing repository')
root.mkdir(mode=0o700,parents=False,exist_ok=False)
archive=root/'site-public.tar'
digest=hashlib.sha256()
with archive.open('xb') as output:
    while True:
        chunk=sys.stdin.buffer.read(1024*1024)
        if not chunk:break
        digest.update(chunk);output.write(chunk)
check(digest.hexdigest()==archive_sha,'Transfer archive changed')
assets=root/'site/public';assets.mkdir(parents=True)
with tarfile.open(archive,'r:') as bundle:
    members=bundle.getmembers();names=[m.name for m in members]
    check(len(names)==len(set(names))==37 and 'build.json' in names,'Unexpected asset inventory')
    for member in members:
        check(member.isfile() and re.fullmatch('[A-Za-z0-9_.-]+',member.name) and
              member.name not in ('.','..'),'Unsafe/nonregular asset')
        with bundle.extractfile(member) as incoming,(assets/member.name).open('xb') as out:
            while True:
                chunk=incoming.read(1024*1024)
                if not chunk:break
                out.write(chunk)
check(sha(assets/'build.json')==manifest_sha,'Transferred build manifest differs')
manifest=json.loads((assets/'build.json').read_bytes())
check(manifest['version']==version and len(manifest['files'])==36 and
      set(manifest['files'])==set(names)-{'build.json'},'Build manifest scope differs')
check(manifest['files']['data.json']==dataset_sha,'Dataset binding differs')
for name,wanted in manifest['files'].items():
    check(re.fullmatch('[0-9a-f]{64}',wanted) and sha(assets/name)==wanted,'Asset changed: '+name)

env=dict(os.environ,GIT_INDEX_FILE=str(root/'website.index'),GIT_NO_LAZY_FETCH='1',
         GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(*args,input=None):
    result=subprocess.run(['git','--git-dir',str(bare),*args],input=input,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,env=env,check=False)
    if result.returncode:
        raise RuntimeError('Git command failed ('+' '.join(args[:2])+'), exit '+str(result.returncode))
    return result.stdout.decode().strip()
def advertised():
    lines=git('ls-remote','--heads','origin','refs/heads/main').splitlines()
    check(len(lines)==1,'Expected one advertised website main')
    oid,ref=lines[0].split()
    check(ref=='refs/heads/main' and re.fullmatch('[0-9a-f]{40}',oid),'Unexpected main ref')
    return oid
def website_remote(url):
    if url in ('git@gitlab.com:mech-lang/web/website.git','git@gitlab.com:mech-lang/web/website'):
        return True
    parsed=urllib.parse.urlsplit(url)
    return (parsed.scheme=='https' and parsed.hostname=='gitlab.com' and parsed.port in (None,443) and
            parsed.path.rstrip('/') in ('/mech-lang/web/website','/mech-lang/web/website.git') and
            not parsed.query and not parsed.fragment)
fetch_urls=git('remote','get-url','--all','origin').splitlines()
push_urls=git('remote','get-url','--push','--all','origin').splitlines()
check(len(fetch_urls)==len(push_urls)==1 and website_remote(fetch_urls[0]) and
      website_remote(push_urls[0]),'Unexpected website remote identity')
base=advertised()
check(git('cat-file','-t',base)=='commit','Current website base is not retained; fetch separately before publishing')
git('read-tree',base)
for name in sorted(names):
    oid=git('hash-object','-w','--',str(assets/name))
    git('update-index','--add','--cacheinfo','100644,'+oid+',public/benchmarks/'+name)
tree=git('write-tree','--missing-ok')
check(tree!=git('rev-parse',base+'^{tree}'),'Build has no website change')
changed=git('diff-tree','--no-commit-id','--name-only','-r',base,tree).splitlines()
check(changed and all(path.startswith('public/benchmarks/') and
      path[len('public/benchmarks/'):] in names for path in changed),'Change escapes selected assets')
check(set(git('ls-tree','-r','--name-only',tree,'--','public/benchmarks').splitlines())==
      {'public/benchmarks/'+name for name in names},'Website benchmark subtree has unexpected assets')
for name in names:
    blob=git('rev-parse',tree+':public/benchmarks/'+name)
    check(blob==git('hash-object','--',str(assets/name)),'Website tree asset binding differs')
message='Add qualified Julia AOT benchmark series\n\nBenchmark source: '+source+'\nBuild: '+version+'\n'
commit=git('commit-tree',tree,'-p',base,input=message.encode())
check(git('rev-parse',commit+'^')==base and git('rev-parse',commit+'^{tree}')==tree,'Candidate parent/tree differs')
check(advertised()==base,'Website main advanced before push; candidate retained, no retry')
# Recheck the transferred inputs immediately before the only remote ref write.
check(sha(assets/'build.json')==manifest_sha,'Manifest changed before push')
for name,wanted in manifest['files'].items():check(sha(assets/name)==wanted,'Asset changed before push')
candidate=dict(schema='benchmark-julia-aot-full81-pages-publication-v1',status='candidate-verified-awaiting-push',
    created_at=datetime.now(timezone.utc).isoformat(),benchmark_source_commit=source,
    website_base=base,website_commit=commit,website_tree=tree,build_version=version,
    build_manifest_sha256=manifest_sha,dataset_sha256=dataset_sha,asset_count=36,
    changed_paths=changed,benchmark_history_fetched=False,raw_evidence_transferred=False)
save('candidate.json',candidate)
git('push','--force-with-lease=refs/heads/main:'+base,'origin',commit+':refs/heads/main')
check(advertised()==commit,'Remote website head did not match published commit')
candidate.update(status='pushed-awaiting-live-pages-verification',remote_ref_verified=True,
                 pushed_at=datetime.now(timezone.utc).isoformat())
save('website-publication.json',candidate)
print(json.dumps(candidate),flush=True)
'''


def check(value,message):
    if not value:raise RuntimeError(message)


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-public',type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--build-version',required=True)
    parser.add_argument('--dataset-sha256',required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    source=args.site_public.resolve();receipt=args.receipt.resolve()
    check(not receipt.exists(),'Local publication receipt must be fresh')
    check(source.name=='public' and source.parent.name=='site' and source.is_dir(),'Select the actual site/public directory')
    check(re.fullmatch('[0-9a-f]{40}',args.source_commit),'Expected exact benchmark source commit')
    check(sha(source/'build.json')==args.manifest_sha256,'Reviewed local manifest differs')
    manifest=json.loads((source/'build.json').read_bytes())
    check(manifest['version']==args.build_version and len(manifest['files'])==36 and
          manifest['files']['data.json']==args.dataset_sha256,'Reviewed build/dataset scope differs')
    expected=dict(manifest['files'],**{'build.json':args.manifest_sha256})
    check({p.name for p in source.iterdir()}==set(expected),'Unexpected file or directory in site/public')
    for name,wanted in expected.items():
        path=source/name
        check(re.fullmatch('[A-Za-z0-9_.-]+',name) and name not in ('.','..') and
              path.is_file() and not path.is_symlink() and path.resolve().parent==source,
              'Unsafe asset: '+name)
        check(re.fullmatch('[0-9a-f]{64}',wanted) and sha(path)==wanted,'Local asset changed: '+name)
    with tempfile.TemporaryDirectory(prefix='mech-julia-aot-full81-assets-') as temporary:
        archive=Path(temporary)/'site-public.tar'
        with tarfile.open(archive,'w') as bundle:
            for name in sorted(expected):bundle.add(source/name,arcname=name,recursive=False)
        for name,wanted in expected.items():check(sha(source/name)==wanted,'Local asset changed during packaging')
        remote=shlex.join(['python3','-c',REMOTE,STAGING,BARE,args.source_commit,args.manifest_sha256,
                          args.build_version,args.dataset_sha256,sha(archive)])
        with archive.open('rb') as incoming:
            result=subprocess.run(['ssh',HOST,remote],stdin=incoming,stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,check=False)
        if result.returncode:
            raise RuntimeError('Publication stopped; remote staging retained. '+result.stderr.decode(errors='replace'))
        value=json.loads(result.stdout)
        check(value['status']=='pushed-awaiting-live-pages-verification' and value['remote_ref_verified'] is True and
              value['benchmark_source_commit']==args.source_commit and value['build_manifest_sha256']==args.manifest_sha256,
              'Unexpected publication receipt')
        receipt.parent.mkdir(parents=True,exist_ok=True)
        with receipt.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
        print(json.dumps(value),flush=True)


if __name__=='__main__':main()
