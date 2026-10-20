"""Lossless deterministic archival of large native diagnostics, no subject run.

Original raw paths and sealed receipts remain unchanged. Archived checks hash
decompressed bytes, explicitly distinguish local raw comparison, and recover only
inside this packet's ignored .build tree. No parsed summary substitutes for bytes.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from native_process import atom,sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ARCHIVE=HERE/'lossless-archive-v1'
MANIFEST=ARCHIVE/'manifest.json'


def require(value,message):
    if not value:raise ValueError(message)


def file_fingerprint(path):return dict(bytes=path.stat().st_size,sha256=sha(path))


def decompressed_fingerprint(path,output=None):
    digest=hashlib.sha256();size=0
    with gzip.open(path,'rb') as source:
        while block:=source.read(1024*1024):
            digest.update(block);size+=len(block)
            if output is not None:output.write(block)
    return dict(bytes=size,sha256=digest.hexdigest())


def build():
    require(not ARCHIVE.exists(),'Fresh lossless archive required');ARCHIVE.mkdir()
    # All framed VM traces, including the failed partial trace; JSON above1MiB
    # is likewise preserved byte for byte instead of reformatted or summarized.
    files=sorted(p for p in HERE.rglob('*') if p.is_file() and
        (p.name=='trace-framed.etf' or (p.suffix=='.json' and p.stat().st_size>1024*1024)) and ARCHIVE not in p.parents)
    rows=[]
    for source in files:
        relative=source.relative_to(HERE);target=ARCHIVE/relative;target=target.with_name(target.name+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
        before=file_fingerprint(source)
        with source.open('rb') as raw,target.open('xb') as encoded:
            with gzip.GzipFile(filename='',fileobj=encoded,mode='wb',compresslevel=6,mtime=0) as compressed:shutil.copyfileobj(raw,compressed,1024*1024)
        require(file_fingerprint(source)==before and decompressed_fingerprint(target)==before,'Lossless compression differs')
        rows.append(dict(raw=dict(path=str(source.relative_to(ROOT)),**before),gzip=dict(path=str(target.relative_to(ROOT)),**file_fingerprint(target))))
    atom(MANIFEST,dict(schema='elixir-rolling-lossless-native-archive.v1',controller=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(__file__)),
        status='LOSSLESS-VERIFIED',entries=rows,raw_bytes=sum(r['raw']['bytes'] for r in rows),gzip_bytes=sum(r['gzip']['bytes'] for r in rows),
        raw_paths_and_sealed_receipts_changed=False,
        archived_replay='Hash all retained gzip bytes and decompressed bytes against exact original raw SHA/length. Missing local originals are explicitly reported, not claimed freshly rehashed.',
        recovery='Optional --recover writes only into experiments/elixir/rolling-v1/.build/recovered-traces-v1; never overwrites sealed raw paths.'))


def check(recover=False):
    manifest=json.loads(MANIFEST.read_bytes());require(manifest['status']=='LOSSLESS-VERIFIED','Unsealed lossless archive')
    require(manifest['controller']['sha256']==sha(__file__),'Archive controller changed')
    seen=set();local=0;missing=0
    destination=HERE.parent/'.build/recovered-traces-v1'
    if recover:require(not destination.exists(),'Fresh ignored recovery tree required');destination.mkdir(parents=True)
    for row in manifest['entries']:
        for name in ['raw','gzip']:
            value=row[name]['path'];require(not Path(value).is_absolute() and '..' not in Path(value).parts,'Unsafe archive path')
        raw=ROOT/row['raw']['path'];compressed=ROOT/row['gzip']['path']
        require(compressed.is_relative_to(ARCHIVE) and raw.is_relative_to(HERE) and str(raw) not in seen,'Ambiguous archive entry');seen.add(str(raw))
        require(file_fingerprint(compressed)=={k:v for k,v in row['gzip'].items() if k!='path'},'Changed compressed native evidence')
        expected={k:v for k,v in row['raw'].items() if k!='path'}
        if recover:
            target=destination/raw.relative_to(HERE);target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:observed=decompressed_fingerprint(compressed,stream)
        else:observed=decompressed_fingerprint(compressed)
        require(observed==expected,'Decompressed original byte identity differs')
        if raw.exists():require(file_fingerprint(raw)==expected,'Changed local original native evidence');local+=1
        else:missing+=1
    print(json.dumps(dict(status='PASSED-LOSSLESS-ARCHIVE',entries=len(seen),local_raw_rehashed=local,local_raw_absent=missing,
        all_archived_decompressed_bytes_rehashed=True,raw_bytes=manifest['raw_bytes'],gzip_bytes=manifest['gzip_bytes'],recovered=recover)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--create',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--recover',action='store_true');args=parser.parse_args()
    require(sum([args.create,args.check,args.recover])==1,'Choose one mode')
    if args.create:build()
    check(args.recover)
