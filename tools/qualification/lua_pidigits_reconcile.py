"""Reconcile the eighteen saved Lua-interpreter pi-digit observations.

Only immutable evidence and independent legacy consumers are read. No Lua,
Mech, compiler, sampler or producer entry point is imported or executed.
"""
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OLD=Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
COHORT='lua-pidigits-comparison/20261012'
ARCHIVE=ROOT/'archive/comparisons'/COHORT
PACKET=ROOT/'experiments/lua/retained-pidigits-v1'
INDEX_SHA='2a2f6f80ee82b8c9b840d6320a9a3f721ff50578dce3b91bab718f6612684c4b'
MANIFEST_SHA='aaf6af5fad6bb4d2f9008e8f91be7037025e117f2cb9532dfb14ae928f6f55dd'
REPORT_SHA='833761cabd812ff56d8f685097cbb664e87640e5d8a2f2043db945241315c789'
RUNTIME_SHA='83ea84efb4f7692a4452cfedf9325cc1f342edc6cf0d50b262add4eab1b75bea'
HELPER_SHA='ae50244bd96f7961201a40780c2dfeab4bb193fc0e2da2184c37753469ef4e6c'
MODULE_SHA='363d291c3b3b0b1298874a56eb40e76c8597cd4e11dbea4df2208fc398e0dab0'
GMP_SHA='571ffb9eb5b5110cda32f62197c1f039e5627d66524ba47bb0774eca184532b9'
HELPER_REVIEW='experiments/lua/retained-pidigits-v1/c-helper-owner-review.json'
HELPER_REVIEW_SHA='90a7075b8528b524e5c0c2d6ed7811a6bb9f91b5eb1aac1442e2eebc992d9041'
COUNTS_SHA='8725633b2ffc195953368d38286d35bf327e54256648b7e32abc8cd37df642bf'
APPLICATION_REVIEW='experiments/lua/retained-pidigits-v1/application-owner-review.json'
APPLICATION_REVIEW_SHA='8a208c41e0c9a7b2846f9fcdf470fb5efc2641cf5853a16409b38132851dfda8'
REFERENCE=dict(bytes=16893,sha256='bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c')
VARIANTS=(1,5,6,7)
IDS=tuple('lua-listed-'+str(n) for n in VARIANTS)
CONTROLS=('mech-fast-control','mech-small-control')
FORMS={1:'immutable bn LFT with impossible-candidate guard',5:'mutable four-coefficient LFT',
       6:'mutable endpoint-numerator LFT',7:'mutable triangular LFT'}
MODULES={
 'core':('tools/qualification/uiua_fann_reconcile.py','bf08aec948d4db505633e9e3898818f997fdd0738d6126c01fe9c9ac60e341dd'),
 'mandelbrot_study_data':('archive/site/explorer/mandelbrot_study_data.py','dd2202bed3aadac4087f71d39e8f8d3e899510bbcb8ef1ad1561f7345f2699f3'),
 'isolated_study_data':('archive/site/explorer/isolated_study_data.py','54f78787784d737cfa339ca5e8ea2e24401c5ead49f4b1a153abd7311efd84e4'),
 'lua_pidigits_study_data':('archive/site/explorer/lua_pidigits_study_data.py','920c9683c648fcecf716612f9f44b1f0880c6dcfe5c98b989b8f9de5476a7b4c'),
 'owners':('tools/qualification/lua_pidigits_source_units.py','46f810ef66e25d2f1c62c2fe4473d65f1e6d16f8243f2a8d3d65b2bcccaf8f16'),
}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def same(a,b,message):
    require(json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False),message)


@contextmanager
def modules():
    old={name:sys.modules.get(name) for name in MODULES};loaded={}
    try:
        for name,(relative,digest) in MODULES.items():
            path=ROOT/relative;raw=path.read_bytes()
            require(sha(raw)==digest,'Reviewed consumer changed: '+relative)
            spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
            sys.modules[name]=module;exec(compile(raw,str(path),'exec'),module.__dict__);loaded[name]=module
        yield loaded
    finally:
        for name,value in old.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value


def check_counts(counts,sources,owners):
    require(counts['schema']=='lua-pidigits-five-source-counts-v1'
            and counts['status']=='passed-independent-source-owner-review'
            and counts['rule_version']==owners.RULE
            and counts['canonical_loc_qualified'] is True
            and counts['formatted_loc_qualified'] is False,'Independent complete-bundle count review required')
    expected={s['sha256'] for s in owners.SPECS.values()}|{HELPER_SHA}
    require(set(counts['files'])==set(sources)==expected and set(counts['profiles'])==set(IDS),
            'Four applications and one complete shared helper required')
    for digest,raw in sources.items():
        c=counts['files'][digest]
        require(sha(raw)==digest and c['sha256']==digest and c['canonical_loc_qualified'] is True
                and type(c['canonical_loc']) is int and c['canonical_loc']>0
                and type(c['physical_loc']) is int and c['physical_loc']>0
                and c['formatted_loc'] is None and c['formatted_loc_qualified'] is False,
                'Qualified source count identity or metric differs')
    helper=counts['files'][HELPER_SHA]
    require(helper['path']=='experiments/lua/retained-pidigits-v1/support/gmp.c'
            and helper['role']=='general-library-helper'
            and helper['canonical_loc']==218 and helper['physical_loc']==119,
            'Complete independently reviewed C helper must be counted once per bundle')
    require(dict(path=HELPER_REVIEW,sha256=HELPER_REVIEW_SHA) in counts['evidence'],
            'Independent complete C owner review missing')
    require(dict(path=APPLICATION_REVIEW,sha256=APPLICATION_REVIEW_SHA) in counts['evidence'],
            'Independent complete Lua owner review missing')
    for n,identity in zip(VARIANTS,IDS):
        digest=owners.SPECS[n]['sha256'];c=counts['files'][digest]
        actual=owners.count_source(sources[digest],n)
        require(c['path']==actual['source_path'] and c['role']=='application'
                and c['canonical_loc']==actual['canonical_loc'] and c['physical_loc']==actual['physical_loc'],
                'Lua source owner count differs')
        bundle=counts['profiles'][identity]
        require(bundle['files']==[digest,HELPER_SHA]
                and bundle['canonical_loc']==c['canonical_loc']+helper['canonical_loc']
                and bundle['physical_loc']==c['physical_loc']+helper['physical_loc'],
                'Application-plus-helper total differs')
    return copy.deepcopy(counts)


def check_helper_review(review,raw):
    require(review['schema']=='lua-pidigits-c-helper-owner-review-v1'
            and review['status']=='passed-independent-source-owner-review'
            and review['qualified'] is True and review['source']['sha256']==sha(raw)==HELPER_SHA
            and review['canonical_loc']==218 and review['physical_loc']==119
            and review['formatted_loc'] is None,'Approved complete helper owner review differs')
    text=raw.decode('utf-8');offset=0;units=0;physical=0
    require(len(review['rows'])==len(text.splitlines())==128,'Helper row coverage differs')
    for number,row in enumerate(review['rows'],1):
        require(row['line']==number and row['start']==offset and row['end']>offset
                and text[row['start']:row['end']].rstrip('\r\n')==row['source']
                and type(row['canonical_units']) is int and row['canonical_units']>=0,
                'Helper source spans or unit decisions differ')
        offset=row['end'];units+=row['canonical_units'];physical+=row['canonical_units']>0
    require(offset==len(text) and units==218 and physical==119,'Incomplete helper owner ledger')


def reconcile(manifest,retained,report,validation,family,launch,index,raw,sources,counts,loaded):
    """Pure bounded saved-document checks; no runtime pins are opened here."""
    require(index['schema']=='lua-retained-pidigits-input-index-v1'
            and index['original_manifest_sha256']==MANIFEST_SHA
            and len(index['original_pins'])==46,'Retained input index differs')
    same(manifest['pins'],index['original_pins'],'Original 46-pin closure changed')
    same(dict(manifest,chart_policy=retained['chart_policy']),retained,
         'Archived manifest changed beyond its public documentation sentence')
    require(manifest['sample_count']==3 and manifest['samples']==3 and manifest['size']==10000
            and manifest['shared_timing_lock']=='/tmp/mech-clbg-timing.lock'
            and manifest['maximum_compute_workers']==1
            and manifest['maximum_rss_mib']==2048 and manifest['timeout_seconds']==300
            and manifest['preparation_full_output_checks']==10 and manifest['full_performance_runs']==0,
            'Original full study policy differs')
    require(report['manifest']==str(OLD/COHORT/'full-study/manifest.json')
            and report['manifest_sha256']==MANIFEST_SHA and len(report['attempts'])==18,
            'Exact completed eighteen-observation study required')
    require(type(launch['pid']) is int and launch['pid']==report['supervisor']['pid']
            and launch['manifest_sha256']==MANIFEST_SHA,'Original launch ownership differs')
    same(launch['identity'],report['supervisor'],'Original supervisor birth/argv listing differs')
    listing=report['supervisor']['process_listing']
    require(listing.endswith(' -u '+str(OLD/COHORT/'full_study.py')+' --run --manifest-sha256 '+MANIFEST_SHA),
            'Original durable controller command differs')
    legacy=loaded['lua_pidigits_study_data'];core=loaded['core']
    locs={f'lua-listed-{n}':legacy.PRODUCER_LOCS[n] for n in VARIANTS}|{'mech-fast-control':38,'mech-small-control':35}
    rows,discarded=loaded['isolated_study_data'].validate_full_records(
        manifest,report,MANIFEST_SHA,benchmark='pidigits',size=10000,locs=locs,
        workers=1,reference=REFERENCE,environment_retries=True)
    require(not discarded and set(raw)==set(range(1,19)),'No omitted, repeated or additional observations permitted')
    previous_end=None;native_ids=set()
    for a in report['attempts']:
        require(type(a['attempt']) is int and type(a['round']) is int
                and type(a['exit_status']) is int and a['exit_status']==0
                and type(a['sampler_wait_status']) is int and a['sampler_wait_status']==0
                and a['stderr']=='' and a['environment_attempt']==1,'Original successful execution fields differ')
        expected=dict(a);expected.pop('environment_attempt')
        same(raw[a['attempt']],expected,'Per-attempt original receipt differs from completed report')
        from datetime import datetime
        start=datetime.fromisoformat(a['started_at']);end=datetime.fromisoformat(a['finished_at'])
        require(end>start and (previous_end is None or start>=previous_end),'Observation intervals overlap or reverse')
        previous_end=end;pid=a['supervised_native_group']['pid']
        require(pid not in native_ids,'Native process identity reused within cohort');native_ids.add(pid)
        require(a['result_path']==str(OLD/COHORT/'full-study/attempts'/f'{a["attempt"]:03d}-{a["id"]}.json'),
                'Raw receipt route differs')
    require(validation['status']=='passed' and validation['scored_samples']==0
            and validation['generic_primitive_tests'] is True
            and validation['application_output_checks']==len(validation['output_validations'])==248
            and validation['mech_output_checks']==18,'Retained bounded qualification differs')
    require(len(validation['division_checks'])==4 and {c['variant'] for c in validation['division_checks']}==set(VARIANTS),
            'Four actual exact-division traces required')
    require(family['status']=='passed' and family['data_or_chart_write'] is False
            and family['studies']['lua']['actual_qualified_records']==18
            and family['studies']['lua']['manifest_sha256']==MANIFEST_SHA
            and family['studies']['lua']['report_sha256']==REPORT_SHA
            and family['studies']['lua']['discarded_attempts']==[],
            'Prior retained review no longer describes this cohort')
    for n,identity in zip(VARIANTS,IDS):
        row=rows[identity];digest=loaded['owners'].SPECS[n]['sha256']
        require(row['language']=='lua' and row['key']==f'pidigits:lua-interpreted-gmp-listed-{n}'
                and row['source']==str(OLD/COHORT/'sources'/f'pidigits-lua-{n}-normalized.lua')
                and row['source_sha256']==digest and sha(sources[digest])==digest
                and row['maximum_workers']==1,'Exact measured Lua source identity differs')
        require(row['runtime']['path']=='/opt/homebrew/bin/lua' and row['runtime']['sha256']==RUNTIME_SHA
                and row['runtime']['version']=='Lua 5.5.1  Copyright (C) 1994-2026 Lua.org, PUC-Rio'
                and row['command']==['/opt/homebrew/bin/lua',row['source'],'{n}']
                and row['runtime_environment']=={'LUA_CPATH':str(OLD/COHORT/'build')+'/?.so;;'},
                'Interpreter or library search boundary changed')
        require(manifest['pins'][row['runtime']['path']]==RUNTIME_SHA
                and row['algorithm']['strict'] is True and row['algorithm']['native_benchmark_kernel'] is False,
                'Required work or interpreter pin differs')
        check=next(c for c in validation['division_checks'] if c['variant']==n)
        same(check,row['algorithm']['division_check'],'Source and division evidence differ')
        require(check['n']==97 and check['accepted_digits']==97 and
                check['actual_divisions']==2*check['tested_candidates'] and
                check['both_exact_divisions_per_candidate'] is True and
                check['quotients_independently_verified'] is True and
                manifest['pins'][check['path']]==check['sha256'],'Both general division obligations missing')
        legacy._full_validation(row,REFERENCE,n)
        require(all(v['reference_match'] is True for v in validation['output_validations'] if v['variant']==n),
                'Failed saved source output validation')
        prior=family['studies']['lua']['profiles'][identity]
        for field in ('source','source_sha256','samples_seconds','median_seconds','sample_stdev_seconds'):
            same(row[field],prior[field],'Prior independent source/sample review differs')
    library=manifest['library'];require(library['source']==str(OLD/COHORT/'support/gmp.c')
        and library['source_sha256']==HELPER_SHA and sha(sources[HELPER_SHA])==HELPER_SHA,
        'General arithmetic helper source changed')
    same(library['modules'],{str(OLD/COHORT/'build'/name):MODULE_SHA for name in ('general-gmp.so','c-gmp.so','bn.so')}|
         {'/opt/homebrew/opt/gmp/lib/libgmp.10.dylib':GMP_SHA},'General GMP module/dependency identity differs')
    require(all(manifest['pins'][p]==d for p,d in library['modules'].items()),'Module missing from original closure')
    for identity in CONTROLS:
        row=rows[identity]
        require(row['language']=='mech' and row['source_sha256']==legacy.CONTROL_HASHES[identity]
                and manifest['pins'][row['binary']]==row['binary_sha256'],'Matched control identity differs')
    count_review=check_counts(counts,sources,loaded['owners'])
    return dict(schema='lua-retained-pidigits-reconciliation-v1',
        status='eighteen-saved-observations-reconciled-awaiting-physical-file-review',
        profiles=rows,canonical_counts=count_review,source_forms=4,subject_observations=12,
        matched_control_observations=6,total_observations=18,discarded_attempts=[],
        source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,
        execution_mode='interpreted',runtime_policy='Lua 5.5.1 bytecode interpreter with GNU GMP general arithmetic',
        library=copy.deepcopy(library),timing_boundary=manifest['timing_boundary'],
        algorithm_forms={identity:FORMS[n] for n,identity in zip(VARIANTS,IDS)},
        limitations=[
          'Original output files were temporary; complete output byte counts, SHA-256 and successful reference comparisons are retained.',
          'Native launch PGIDs and cleanup receipts are retained; per-native process birth listings and modern terminal receipts were not retained.',
          'Runtime and module identities are the original static pinned closure, not a per-process loaded-image inventory.',
          'LUA_CPATH explicitly selects the private GMP modules and retains the standard search-path suffix; the original harness inherits its recorded ambient environment.',
          'Short processes can finish between RSS observations; recorded zero peak RSS is not a measured zero memory footprint.',
          'Division-call instrumentation is an untimed N97 check of unchanged application bytes; timed N10000 commands contain no tracer.',
          'The original producer excluded the general helper from LOC; this admission requires the complete application-plus-helper canonical bundle.'
        ],physical_file_integrity_verified=False,common_mutex_held=False,native_processes_started=0,
        historical_reports_mutated=False,luajit_mutated=False,chart_admission=False,dataset_files_changed=False)


@contextmanager
def review_context(tool_sha256,count_path,count_sha256,on_exit_failure=None,final_consumer_check=None):
    """Full physical replay only while the original common timing mutex is free."""
    require(sys.flags.optimize==0,'Legacy assertions must remain enabled')
    with modules() as loaded:
        core=loaded['core'];files=core.Files();files.verify(Path(__file__).resolve(),tool_sha256)
        require(core.LOCK.is_file() and core.LOCK.stat().st_ino==core.LOCK_INODE,'Original common mutex missing')
        with core.LOCK.open('r+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            identity=(os.fstat(lock.fileno()).st_dev,os.fstat(lock.fileno()).st_ino)
            require(identity[1]==core.LOCK_INODE,'Opened mutex is not the original inode')
            original_pins=()
            def verify_lock():
                st=core.LOCK.stat()
                require((st.st_dev,st.st_ino)==identity,'Named timing mutex changed')
            try:
                verify_lock()
                for path,digest in MODULES.values():files.verify(ROOT/path,digest)
                index=core.strict_json(files.read(PACKET/'input-index.json',INDEX_SHA))
                docs={}
                for name,ref in index['retained_evidence'].items():
                    content=files.read(ROOT/ref['path'],ref['sha256'])
                    if name.endswith('.json') or name=='family-review':docs[name]=core.strict_json(content)
                original=core.strict_json(files.read(OLD/COHORT/'full-study/manifest.json',MANIFEST_SHA))
                for path,digest in original['pins'].items():files.verify(Path(path),digest)
                require(files.read(OLD/COHORT/'results/full-study.json',REPORT_SHA)==
                        files.read(ARCHIVE/'results/full-study.json',REPORT_SHA),'Original report changed')
                count_path=Path(count_path).resolve()
                require(count_path==PACKET/'qualified-source-counts-v1.json' and count_sha256==COUNTS_SHA,
                        'Exact reviewed count approval path and digest required')
                counts=core.strict_json(files.read(count_path,count_sha256))
                for ref in counts['evidence']:
                    p=Path(ref['path']);require(not p.is_absolute() and '..' not in p.parts,'Unsafe count evidence path')
                    files.verify(ROOT/p,ref['sha256'])
                sources={}
                for n in VARIANTS:
                    digest=loaded['owners'].SPECS[n]['sha256'];name=f'pidigits-lua-{n}-normalized.lua'
                    content=files.read(PACKET/'sources'/name,digest)
                    require(content==files.read(OLD/COHORT/'sources'/name,digest),'Retained application changed')
                    sources[digest]=content
                sources[HELPER_SHA]=files.read(PACKET/'support/gmp.c',HELPER_SHA)
                require(sources[HELPER_SHA]==files.read(OLD/COHORT/'support/gmp.c',HELPER_SHA),'Retained helper changed')
                helper_review=core.strict_json(files.read(ROOT/HELPER_REVIEW,HELPER_REVIEW_SHA))
                check_helper_review(helper_review,sources[HELPER_SHA])
                for ref in helper_review['rules']:files.verify(ROOT/ref['path'],ref['sha256'])
                raw={}
                for a in docs['results/full-study.json']['attempts']:
                    rel='full-study/attempts/'+Path(a['result_path']).name;ref=index['retained_evidence'][rel]
                    raw[a['attempt']]=docs[rel]
                    require(files.read(OLD/COHORT/rel,ref['sha256'])==files.read(ROOT/ref['path'],ref['sha256']),
                            'Original per-attempt receipt differs')
                result=reconcile(original,docs['full-study/manifest.json'],docs['results/full-study.json'],
                    docs['results/validation.json'],docs['family-review'],docs['full-study/launch.json'],
                    index,raw,sources,counts,loaded)
                result.update(status='eighteen-saved-observations-file-verified-awaiting-publication-review',
                    physical_file_integrity_verified=True,common_mutex_held=True,
                    common_mutex_inode=core.LOCK_INODE,verified_file_pins=copy.deepcopy(files.pins),
                    source_counts=dict(path=count_path.relative_to(ROOT).as_posix(),sha256=count_sha256),
                    report=copy.deepcopy(index['retained_evidence']['results/full-study.json']),
                    source_manifest=copy.deepcopy(index['retained_evidence']['full-study/manifest.json']),
                    original_manifest_sha256=MANIFEST_SHA)
                original_pins=tuple(files.pins.items())
                yield result,files,sources
            except BaseException:
                if on_exit_failure is not None:on_exit_failure()
                raise
            finally:
                try:
                    verify_lock();files.final_check(original_pins);verify_lock()
                    if final_consumer_check is not None:final_consumer_check()
                except BaseException:
                    if on_exit_failure is not None:on_exit_failure()
                    raise
