"""Close the saved exact Nim formatter proof; offline, under the common lock.

No formatter/compiler/native parser/application runs. New overlay admission is
separate. The first replay retains the verification helper image compressed;
--check thereafter can replay from retained bytes without the ignored build.
"""
import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
RUN=HERE/'nim-run-v1'
REPLAY=RUN/'replay-v1'
NIM=ROOT/'experiments/nim/optimization-v1'
DIST=NIM/'.build/nim/nim-2.2.12'
PROFILE='knucleotide:nim-knucleotide-preencoded-v1'
SOURCE='b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b'
OUTPUT='f89f1d009db71981a321cb7d5c2137569eb53e3edcc8b164bd4e061c300ec0c2'
HELPER='941cdbc64879ab62b41314ac31efce433f61474c980d99da3036e03d429e8a01'
BINARY='2c866a513395f7ddf4116098dee4fe81de5a0d372384f2363c1b88102e910890'
PLAN='f748ede4551be175bd83cd0b9358e8fd31098e73a142ec5c59fd3a1f96e8435a'
MASK='3b9a5c498459e5ae3ed04695faef938bbd15080c2c47ac1010ef87fb964cabd5'
WARNINGS='1c1ff5bb5ec8e57fc2e84927c332db0310ad518c685955b2a0aa3660a004a699'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def read(path):return json.loads(path.read_bytes())
def require(ok,message):
    if not ok:raise ValueError(message)
def pin(path,expected=None):
    raw=path.read_bytes();digest=sha(raw)
    require(expected is None or digest==expected,'Changed pinned artifact: '+str(path))
    return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest,bytes=len(raw))

def replay(check=False):
    pins={}
    def bind(path,expected=None):
        item=pin(path,expected);pins[item['path']]=item;return item
    plan=read(HERE/'nim-plan.json');bind(HERE/'nim-plan.json',PLAN)
    bind(HERE/'capture_window.py');bind(Path(__file__))
    producer=ROOT/plan['producer']['path'];bind(producer,plan['producer']['sha256'])
    restoration_path=ROOT/plan['runtime']['restoration']['path']
    bind(restoration_path,plan['runtime']['restoration']['sha256']);restoration=read(restoration_path)
    require(len(restoration['checked_distribution_pins'])==6770,'Restoration inventory differs')
    bind(ROOT/plan['runtime']['version_receipt']['path'],plan['runtime']['version_receipt']['sha256'])
    bind(ROOT/plan['formatter']['config']['path'],plan['formatter']['config']['sha256'])
    terminal=read(RUN/'terminal.json');bind(RUN/'terminal.json')
    require(terminal['status']=='native-evidence-captured-pending-review' and terminal['profile']==PROFILE
        and terminal['source_sha256']==SOURCE and terminal['formatted_output_sha256']==terminal['second_output_sha256']==OUTPUT,
        'Wrong exact-source terminal')
    require(all(terminal[name] is True for name in ('native_ast_identical','native_token_payload_identical','native_comments_identical','idempotent'))
        and all(terminal[name] is False for name in ('application_execution','canonical_changed','chart_admission'))
        and terminal['verified_distribution_files']==6770 and terminal['formatted_physical_loc']==66,
        'Incomplete capture decision')
    sources=[RUN/'input.nim',RUN/'formatted.nim',RUN/'formatted-again.nim']
    for path,expected in zip(sources,(SOURCE,OUTPUT,OUTPUT)):bind(path,expected)
    bind(RUN/'parse_proof.nim',HELPER)
    image_path=REPLAY/'verifier-binary.gz'
    if check:
        image=gzip.decompress(image_path.read_bytes())
    else:
        image=(RUN/'.build/parse_proof').read_bytes();require(sha(image)==BINARY,'Verification image differs')
    require(sha(image)==BINARY and terminal['helper_binary_sha256']==BINARY
        and terminal['helper_sha256']==HELPER,'Helper source/binary binding differs')
    buffer=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',fileobj=buffer,mtime=0) as archive:archive.write(image)
    image_encoded=buffer.getvalue()
    if check:require(image_path.read_bytes()==image_encoded,'Compressed helper image differs')
    image_relative=image_path.relative_to(ROOT).as_posix()
    pins[image_relative]=dict(path=image_relative,sha256=sha(image_encoded),bytes=len(image_encoded))
    captured_run=Path(read(RUN/'version.json')['cwd']);captured_root=captured_run.parents[3]
    require(captured_run==captured_root/RUN.relative_to(ROOT),'Wrong captured repository layout')
    captured_sources=[captured_run/path.name for path in sources]
    captured_dist=captured_root/DIST.relative_to(ROOT)
    expected_env=dict(HOME=str(captured_run/'home'),XDG_CONFIG_HOME=str(captured_run/'home'),PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC')
    pretty=str(captured_dist/'bin/nimpretty');binary=str(captured_run/'.build/parse_proof');helper=str(captured_run/'parse_proof.nim')
    expected_commands={
        'version':[pretty,'--version'],
        'format':[pretty,'--indent:0','--maxLineLen:80','--out:'+str(captured_sources[1]),str(captured_sources[0])],
        'format-again':[pretty,'--indent:0','--maxLineLen:80','--out:'+str(captured_sources[2]),str(captured_sources[1])],
        'build-verifier':[str(captured_dist/'bin/nim'),'c','--skipUserCfg','--skipParentCfg','--skipProjCfg','--hints:off','--verbosity:0',
            '--path:'+str(captured_dist),'--nimcache:'+str(captured_run/'.build/cache'),'--out:'+binary,helper],
        'native-proof':[binary,*map(str,captured_sources)]}
    processes={};pids=set()
    for name,command in expected_commands.items():
        path=RUN/(name+'.json');record=read(path);bind(path)
        require(record['command']==command and record['cwd']==str(captured_run) and record['environment']==expected_env,
            'Process command/environment/cwd differs: '+name)
        require(type(record['exit_status']) is int and record['exit_status']==0 and record['common_lock_inherited'] is True
            and not record.get('timeout_or_interrupt') and record['started']<=record['finished']
            and record['finished']-record['started']<=record['timeout'] and record['pid'] not in pids,'Process failed/incomplete: '+name)
        pids.add(record['pid'])
        for stream in ('stdout','stderr'):bind(RUN/(name+'.'+stream),record[stream+'_sha256'])
        if name not in ('native-proof','version'):require((RUN/(name+'.stdout')).read_bytes()==b'','Unexpected process stdout')
        if name!='build-verifier':require((RUN/(name+'.stderr')).read_bytes()==b'','Unexpected native diagnostics')
        processes[name]=dict(receipt=pin(path),stdout=pin(RUN/(name+'.stdout')),stderr=pin(RUN/(name+'.stderr')))
    require((RUN/'version.stdout').read_bytes()==b'0.2\n','Formatter version differs')
    warning_raw=(RUN/'build-verifier.stderr').read_bytes();require(len(warning_raw)==5129 and sha(warning_raw)==WARNINGS,'Compiler warning bytes differ')
    warning_lines=warning_raw.decode().splitlines()
    unused=helper+"(3, 56) Warning: imported and not used: 'msgs' [UnusedImport]"
    fallback="clang: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead"
    require(warning_lines.count(unused)==1 and warning_lines.count(fallback)==len(warning_lines)-1,'Unclassified verification-build diagnostic')
    proof=read(RUN/'native-proof.stdout')
    require(type(proof) is list and len(proof)==3 and [r['path'] for r in proof]==list(map(str,captured_sources)),'Wrong native proof paths/inventory')
    for row in proof:
        require(type(row['errors']) is int and row['errors']==0 and row['application_evaluated'] is row['macroexpanded'] is False,'Native proof scope/errors differ')
    for name in ('ast','tokens','comments'):require(proof[0][name]==proof[1][name]==proof[2][name],'Native '+name+' differ')
    require(len(proof[0]['tokens'])==614,'Native token inventory differs')
    mask_path=ROOT/'archive/validation/loc-normalization/20261012/foreign_future_mask.py';bind(mask_path,MASK)
    # This pinned module has no imports or execution entry. Only mask_future is
    # called; no candidate, formatter, normalized owner or compiler is imported.
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location('exact_nim_physical_mask',mask_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    raw=sources[1].read_bytes();text=raw.decode();require(not text.startswith('\ufeff'),'Direct mask/BOM scope needs separate review')
    masked=module.mask_future(text,'nim')
    require(masked['diagnostics']==[] and len(masked['cleaned'])==len(text),'Nim lexical mask diagnostics/span differs')
    boundaries='\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029'
    require(all(a==b for a,b in zip(text,masked['cleaned']) if a in boundaries or b in boundaries),'Physical row boundaries differ')
    rows=[];offset=0
    for number,(original,cleaned) in enumerate(zip(text.splitlines(keepends=True),masked['cleaned'].splitlines(keepends=True)),1):
        rows.append(dict(line=number,source_start_utf8=len(text[:offset].encode()),source_end_utf8=len(text[:offset+len(original)].encode()),
            source_sha256=sha(original.encode()),masked_sha256=sha(cleaned.encode()),counted=bool(cleaned.strip()),source=original,masked=cleaned))
        offset+=len(original)
    require(offset==len(text) and sum(row['counted'] for row in rows)==66,'Physical row ledger total differs')
    ledger=dict(schema='source-bound-formatted-physical-row-ledger.v1',definition='nonblank-noncomment-physical-lines-v1',
        source_sha256=OUTPUT,physical_loc=66,mask_sha256=MASK,diagnostics=[],source_row_boundaries_preserved=True,rows=rows)
    # Existing native streams, executable source and plan/config/runtime receipts
    # are all mandatory durable evidence. The optional future fixtures are not
    # included or represented as executed qualification evidence.
    manifest=dict(schema='nim-formatter-artifact-manifest.v1',artifacts=pins,
        verifier_image=dict(path=image_path.relative_to(ROOT).as_posix(),sha256=BINARY,uncompressed_bytes=len(image)),
        runtime_scope='Capture attests full6770file restoration verification; offline replay binds that exact saved map, not a fresh whole-tree rehash.')
    report=dict(schema='exact-source-nim-formatted-qualification.v1',status='replayed-pending-independent-review',
        profile=PROFILE,policy='nimpretty-0.2.nim-2.2.12.indent-auto.width-80.physical-v1',provider='language-project',
        catalog_sha256_at_capture=plan['catalog_sha256'],source_sha256=SOURCE,formatted_sha256=OUTPUT,
        formatted_loc=66,scope='application',embedded_support_ranges=[],included_sources=[SOURCE],
        formatter=plan['formatter'],runtime_restoration=plan['runtime']['restoration'],
        verification_helper_source=pin(RUN/'parse_proof.nim'),verification_helper_binary_sha256=BINARY,
        idempotence=dict(equal=True,first_output=OUTPUT,second_output=OUTPUT),
        native_preservation=dict(ast_identical=True,token_payloads_identical=True,significant_tokens=614,comments_identical=True,errors=0,
            evidence=pin(RUN/'native-proof.stdout'),definition='Exact raw AST kind/child/identifier/literal and significant native token payload equality; positions/indentation omitted; no semantic compilation.'),
        row_ledger_sha256=sha(encoded(ledger)),artifact_manifest_sha256=sha(encoded(manifest)),
        processes=processes,verification_build_diagnostics=dict(raw=pin(RUN/'build-verifier.stderr'),unused_import=1,
            clang_temporary_directory_fallback=len(warning_lines)-1,classification='Trusted verification-helper build warnings preserved verbatim; not a benchmark/application build waiver.'),
        limits=['Exact source only; broader prepared fixture contract not executed.',
            'Physical mask is the exact retained Nim lexical operation via a direct adapter for this non-BOM source.',
            'Recorded capture runtime tree verification; offline replay does not launch or reconstruct the runtime.',
            'No canonical/history/publication edits or admission; later reviewed additive overlay required.'],
        canonical_fields_changed=False,source_bytes_changed=False,timing_samples_changed=False,chart_admission=False,
        native_processes_executed_by_replay=0)
    outputs={'row-ledger.json':encoded(ledger),'artifact-manifest.json':encoded(manifest),'qualification.json':encoded(report)}
    if check:
        for name,raw in outputs.items():require((REPLAY/name).read_bytes()==raw,'Saved replay output differs: '+name)
    else:
        require(not REPLAY.exists(),'Fresh replay output required');REPLAY.mkdir()
        # Deterministic gzip retains the exact observed tooling image in the
        # durable packet; users do not need the ignored local build to check it.
        image_path.write_bytes(image_encoded)
        for name,raw in outputs.items():(REPLAY/name).write_bytes(raw)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        report=replay(args.check)
    print(json.dumps({key:report[key] for key in ('status','profile','formatted_loc','native_processes_executed_by_replay','chart_admission')}))

if __name__=='__main__':main()
