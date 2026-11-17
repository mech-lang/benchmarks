#!/usr/bin/env python3
"""Build unmodified pinned Roc and libdeflate compressors with the declared host wrapper."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.request
from benchmark_suite import ROOT, execute, file_digest, save

ROC_PIN = 'd99c7b838fb05bb1047eb0c18d4d06d0f86f345d'
LIBDEFLATE_PIN = '92e6a0db9fa848d742f9eb286c92afc60f2c3dda'


def checked(command, directory, timeout=600):
    result=execute([str(x) for x in command],directory,timeout)
    if result['outcome']!='ok':
        raise ValueError(f'build failed; inspect {directory}')
    return result


def build(roc, reference, libdeflate, output):
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    roc=Path(roc).resolve();reference=Path(reference).resolve();libdeflate=Path(libdeflate).resolve()
    pins=json.loads((ROOT/'suite/controls/pins.json').read_text())
    archive=output/'libdeflate-source.tar.gz'
    with urllib.request.urlopen(pins['libdeflate']['source_url'],timeout=60) as response:
        archive.write_bytes(response.read(4*1024*1024+1))
    if file_digest(archive)!=pins['libdeflate']['source_archive_sha256']:raise ValueError('libdeflate source archive hash mismatch')
    with tarfile.open(archive) as source_archive:
        for member in source_archive.getmembers():
            if not member.isfile():continue
            parts=Path(member.name).parts
            if not parts or '..' in parts:raise ValueError('unsafe upstream source path')
            relative=Path(*parts[1:])
            expected=hashlib.sha256(source_archive.extractfile(member).read()).hexdigest()
            if file_digest(libdeflate/relative)!=expected:raise ValueError('libdeflate source differs from pin: '+str(relative))
    fixture=json.loads((ROOT/'suite/applications/deflate-compress-reference.json').read_text())
    for relative,checksum in fixture['reference']['package_source_sha256'].items():
        if file_digest(reference/relative)!=checksum:raise ValueError('Roc reference source changed: '+relative)
    checked([roc,'version'],output/'roc-version')
    if ROC_PIN[:8] not in (output/'roc-version/stdout.txt').read_text():raise ValueError('incorrect Roc compiler revision')
    if '#define LIBDEFLATE_VERSION_STRING\t"1.26"' not in (libdeflate/'libdeflate.h').read_text():raise ValueError('incorrect libdeflate version')
    project=output/'roc';(project/'platform/targets/arm64mac').mkdir(parents=True)
    shutil.copyfile(ROOT/'suite/controls/roc/platform/main.roc',project/'platform/main.roc')
    # The package is immutable; the host wrapper has its own recorded source.
    source='app [run] { pf: platform "platform/main.roc", deflate: '+json.dumps(str(reference/'package/main.roc'))+' }\nimport deflate.Deflate\nrun : List(U8), List(U8) -> List(U8)\nrun = |input, output| Deflate.compress_into(input, 12, output)\n'
    (project/'app.roc').write_text(source)
    checked([roc,'build','--no-cache','--opt=speed','--jobs=1','--target=arm64mac','--output='+str(project/'compressor.a'),project/'app.roc'],output/'roc-build')
    wrapper=ROOT/'suite/controls/deflate_control.c'
    checked(['clang','-O3','-DROC_CONTROL',wrapper,project/'compressor.a','-o',project/'control'],output/'roc-link')
    cproject=output/'libdeflate';cproject.mkdir()
    units=['lib/arm/cpu_features.c','lib/x86/cpu_features.c','lib/utils.c','lib/deflate_compress.c','lib/deflate_decompress.c','lib/adler32.c','lib/crc32.c','lib/zlib_compress.c','lib/zlib_decompress.c','lib/gzip_compress.c','lib/gzip_decompress.c']
    objects=[]
    for i,unit in enumerate(units):
        obj=cproject/(unit.replace('/','-')+'.o');objects.append(obj)
        checked(['clang','-O2','-DNDEBUG','-I',libdeflate,'-c',libdeflate/unit,'-o',obj],output/f'c-compile-{i}')
    checked(['ar','rcs',cproject/'libdeflate.a',*objects],output/'c-archive')
    checked(['clang','-O3','-I',libdeflate,wrapper,cproject/'libdeflate.a','-o',cproject/'control'],output/'c-link')
    receipt={'schema':'mech.compression-controls.v1','allocator':'system malloc; distinct output reservation; held input and prepared-output aliases survive the complete call',
        'wrapper':str(wrapper),'wrapper_sha256':file_digest(wrapper),
        'roc':{'binary':str(project/'control'),'binary_sha256':file_digest(project/'control'),
            'source_revision':fixture['reference']['source_pin'],'compiler_revision':ROC_PIN,'compiler_binary':str(roc),'compiler_binary_sha256':file_digest(roc),
            'package_source_sha256':fixture['reference']['package_source_sha256'],'app_source':source,'archive_sha256':file_digest(project/'compressor.a')},
        'libdeflate':{'binary':str(cproject/'control'),'binary_sha256':file_digest(cproject/'control'),'source_revision':LIBDEFLATE_PIN,
            'source_archive_sha256':pins['libdeflate']['source_archive_sha256'],'source_files_sha256':{str(p.relative_to(libdeflate)):file_digest(p) for p in sorted(libdeflate.rglob('*')) if p.is_file()},'archive_sha256':file_digest(cproject/'libdeflate.a')}}
    save(output/'controls.json',receipt)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('roc','reference','libdeflate','output'):parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args()
    try:
        build(args.roc,args.reference,args.libdeflate,args.output)
        print(args.output/'controls.json')
    except (OSError,ValueError) as error:parser.exit(1,f'{error}\n')
