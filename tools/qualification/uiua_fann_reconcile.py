"""Reconcile the retained nine-observation Uiua fannkuch v5 study.

Only the independently reviewed archived consumer is loaded. No benchmark,
sampler, runtime, compiler or producer is imported or executed. The file phase
holds the original common mutex through caller work and its final pin recheck.
"""
import argparse
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
COHORT = 'r-apl-uiua-comparison/20261011/uiua-fann-compact-v5'
ARCHIVE = ROOT/'archive/comparisons'/COHORT
PACKET = ROOT/'experiments/uiua/fann-v5-publication-v1'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
MANIFEST_SHA = 'd8b6ad100671b3fef5ae46d90dcb36b044733b25ea8d65e3ba7a4589e5b62513'
REPORT_SHA = 'f5ab40f30c8add188c4e7a0ac87dc7fd18475ff28c5bba8838dc08b10ff71a6c'
CANDIDATE_SHA = '41462f55b1c1f6c800d08cca9ba9ba46cb5e3c6efd7f0ff3d21cfde514b70b7c'
RETAINED_CANDIDATE_SHA = '9d8972f3254500ad14cbbf56e0378a7a47661edaaeb7afba04b50dcad3cc6534'
PRIOR_REVIEW = ROOT/'archive/comparisons/r-apl-uiua-comparison/20261011/evidence/new-results-review-20261012/independent-study-reconciliation.json'
PRIOR_REVIEW_SHA = '23e728205fdcbbe1eb974db4dbaefb26bf1b93330e65f8a561f61e3ca3bde404'
OWNER_REVIEW = PACKET/'source-owner-review.md'
OWNER_REVIEW_SHA = '1e6ec65fbb85d8ad90902683b124509e3c35820ef46b1b2f489679ec0ca11c10'
SOURCE_APPROVAL = PACKET/'independent-source-review.json'
SOURCE_APPROVAL_SHA = 'c594c29d38f869a2add722d3f4d4c282117bb1ac3556a3e3c4ccb3963625c826'
HELPERS = {
    'mandelbrot_study_data': ('archive/site/explorer/mandelbrot_study_data.py', 'dd2202bed3aadac4087f71d39e8f8d3e899510bbcb8ef1ad1561f7345f2699f3'),
    'isolated_study_data': ('archive/site/explorer/isolated_study_data.py', '54f78787784d737cfa339ca5e8ea2e24401c5ead49f4b1a153abd7311efd84e4'),
    'uiua_fann_study_data': ('archive/site/explorer/uiua_fann_study_data.py', '5b9259f3cd9fd7c3d7111682559fa247e4d53af84e8e781ebe5880214cf40b3a'),
    'uiua_fann_source_units': ('tools/qualification/uiua_fann_source_units.py', '3f29af8b3d4598e578039fa90b3de9dbc9ab9f4a4ded64777f6e628fe58efc42'),
}
SUPERVISOR_FIELDS = {'attempt', 'qualification_checks', 'qualified', 'result_path',
    'round', 'sampler_wait_status', 'supervised_native_group', 'supervisor_remaining_members'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: '+key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON value: '+value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def same(a, b, message):
    require(json.dumps(a, sort_keys=True, allow_nan=False) ==
            json.dumps(b, sort_keys=True, allow_nan=False), message)


def check_retained_candidate(original, retained):
    """The archived public copy changes only a reviewed documentation sentence."""
    require(type(original.get('migration_policy')) is str and
            type(retained.get('migration_policy')) is str,'Candidate documentation field missing')
    expected = dict(original,migration_policy=retained['migration_policy'])
    same(expected,retained,'Retained candidate differs beyond its documentation-only migration policy')


@contextmanager
def helper_modules():
    previous = {name:sys.modules.get(name) for name in HELPERS}
    loaded = {}
    try:
        for name, (relative, digest) in HELPERS.items():
            path = ROOT/relative
            raw = path.read_bytes()
            require(sha(raw) == digest, 'Reviewed consumer source changed: '+relative)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            exec(compile(raw, str(path), 'exec'), module.__dict__)
            loaded[name] = module
        yield loaded
    finally:
        for name, prior in previous.items():
            if prior is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prior


def reconcile(manifest, report, candidate, source_audit, runner_qualification,
              prior_review, source_bytes, raw_records, modules):
    """Pure replay; file hashes/leases are the separate caller responsibility."""
    old = modules['uiua_fann_study_data']
    rows, discarded = modules['isolated_study_data'].validate_full_records(
        manifest, report, MANIFEST_SHA, benchmark='fannkuchredux', size=12,
        locs=old.LOCS, workers=8, reference=old.REFERENCE, expected_checks=old.CHECKS)
    require(not discarded and len(report['attempts']) == 9 and len(manifest['pins']) == 1245,
            'Exact completed nine-record study required')
    require(manifest['canonical_full_workload'] is True and manifest['full_permutations'] == 479001600,
            'Full N12 required work differs')
    require(candidate['status'] == 'prepared-validated' and candidate['full_performance_runs'] == 0,
            'Source candidate preparation differs')
    require(source_audit['status'] == 'passed-source-audit' and
            all(source_audit[k] is False for k in ('native_benchmark_kernel','new_host_helpers',
                'permutation_cache','flip_result_cache','input_specific_shortcuts')) and
            source_audit['parent_only_output'] is True, 'Required source work differs')
    require(runner_qualification['status'] == 'passed', 'Existing runner qualification is not passed')
    require(prior_review['status'] == 'passed' and prior_review['data_admission'] is False,
            'Existing independent study review differs')
    prior = prior_review['fann']
    require(prior['status'] == 'complete-independent-reconciliation-passed' and
            prior['manifest_sha256'] == MANIFEST_SHA and prior['report_sha256'] == REPORT_SHA and
            prior['actual_records'] == 9 and prior['input_pins_verified'] == 1245 and
            prior['consumer_dry_import'] is True and prior['chart_or_file_write'] is False,
            'Prior independent nine-record review differs')
    require(set(raw_records) == set(range(1, 10)), 'Exact nine sampler receipts required')
    for attempt in report['attempts']:
        raw = raw_records[attempt['attempt']]
        require(set(attempt)-set(raw) == SUPERVISOR_FIELDS and not set(raw)-set(attempt),
                'Unexpected raw/supervisor schema changes')
        same(raw, {k:v for k,v in attempt.items() if k not in SUPERVISOR_FIELDS},
             'Saved sampler receipt differs from its report')
    programs = {row['source_profile']:row for row in candidate['programs']}
    require(set(programs) == set(source_bytes) == {'compact','fast'}, 'Two complete source bundles required')
    counts = {}
    for variant, original in programs.items():
        row = rows['uiua-'+variant]
        for field in ('source','source_sha256','command','runtime_environment','loc','maximum_workers'):
            same(row[field], original[field], 'Source candidate/study identity differs: '+field)
        require(row['language'] == 'uiua' and row['command'][0] == candidate['runtime']['path'] and
                candidate['runtime']['version'] == 'Uiua 0.19.1' and
                original['algorithm']['strict'] is True and original['algorithm']['native_benchmark_kernel'] is False,
                'Source/runtime/work identity differs')
        count = modules['uiua_fann_source_units'].count_source(source_bytes[variant], variant)
        require(count['source_sha256'] == row['source_sha256'] and
                count['canonical_loc'] == row['loc'] == original['physical_loc'] and
                original['loc_expansions'] == [], 'Independent owner count differs from the exact source')
        counts[variant] = count
        same(row['samples_seconds'], prior['profiles']['uiua-'+variant]['samples'],
             'Samples differ from prior independent reconciliation')
    control = rows['mech59-aot-control']
    require(control['source_sha256'] == old.CONTROL_SHA and control['loc'] == 59 and control['language'] == 'mech',
            'Matched Mech control differs')
    same(control['samples_seconds'], prior['control']['samples'], 'Control samples differ from prior review')
    return dict(schema='uiua-fann-v5-retained-reconciliation-v1',
        status='nine-retained-observations-reconciled-awaiting-publication-review',
        benchmark='fannkuchredux', language='uiua', native_processes_started=0,
        retained_subject_samples=6, retained_control_samples=3, native_observations=9,
        source_counts=counts, source_work_qualified=True, canonical_loc_qualified=True,
        formatted_loc_qualified=False, formatted_loc=None, rows=rows,
        runtime=copy.deepcopy(candidate['runtime']), source_programs=copy.deepcopy(programs),
        timing_boundary=manifest['timing_boundary'], original_report_status=report['status'],
        matched_control=copy.deepcopy(control), chart_admission=False,
        dataset_files_changed=False, historical_reports_mutated=False)


class Files:
    def __init__(self):
        self.pins = {}

    def verify(self, path, digest):
        path = Path(path)
        require(path.is_absolute() and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
                'Explicit absolute file and SHA-256 required')
        if str(path) in self.pins:
            require(self.pins[str(path)] == digest, 'Conflicting file pin')
        with path.open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == digest, 'Pinned file changed: '+str(path))
        self.pins[str(path)] = digest

    def read(self, path, digest):
        self.verify(path, digest)
        raw = Path(path).read_bytes()
        require(sha(raw) == digest, 'File changed during read: '+str(path))
        return raw

    def final_check(self, original_pins=()):
        # Consumer-added pins are additive; deleting/rebinding an original
        # entry cannot remove a member of the verified native closure.
        checks = dict(original_pins)
        for path,digest in self.pins.items():
            require(path not in checks or checks[path] == digest,'Original closure pin rebound')
            checks[path] = digest
        for path, digest in checks.items():
            self.verify(path, digest)


@contextmanager
def review_context(tool_sha256, on_exit_failure=None, final_consumer_check=None):
    """Nonblocking common lease; no work starts while a timing owner holds it."""
    files = Files()
    files.verify(Path(__file__).resolve(), tool_sha256)
    require(LOCK.is_file() and LOCK.stat().st_ino == LOCK_INODE, 'Original common mutex missing or replaced')
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        identity = (os.fstat(lock.fileno()).st_dev, os.fstat(lock.fileno()).st_ino)
        def verify_lock():
            current = LOCK.stat()
            require((current.st_dev,current.st_ino) == identity and current.st_ino == LOCK_INODE,
                    'Common mutex pathname changed')
        original_pins = ()
        try:
            verify_lock()
            for relative, digest in HELPERS.values():
                files.verify(ROOT/relative, digest)
            files.verify(OWNER_REVIEW, OWNER_REVIEW_SHA)
            approval = strict_json(files.read(SOURCE_APPROVAL,SOURCE_APPROVAL_SHA))
            require(approval['status'] == 'passed-independent-source-owner-review' and
                    approval['checker']['sha256'] == HELPERS['uiua_fann_source_units'][1] and
                    approval['source_owner_review']['sha256'] == OWNER_REVIEW_SHA and
                    approval['sources']['compact']['canonical_loc'] == 20 and
                    approval['sources']['fast']['canonical_loc'] == 21,
                    'Independent source-owner approval differs')
            prior = strict_json(files.read(PRIOR_REVIEW, PRIOR_REVIEW_SHA))
            values = {}
            for name, digest in [('full-study/manifest.json',MANIFEST_SHA),('full-study/report.json',REPORT_SHA)]:
                retained = files.read(ARCHIVE/name, digest)
                require(files.read(HISTORICAL/COHORT/name,digest) == retained, 'Retained/original evidence differs')
                values[name] = strict_json(retained)
            manifest, report = (values[k] for k in ('full-study/manifest.json','full-study/report.json'))
            candidate = strict_json(files.read(HISTORICAL/COHORT/'manifest.json',CANDIDATE_SHA))
            retained_candidate = strict_json(files.read(ARCHIVE/'manifest.json',RETAINED_CANDIDATE_SHA))
            check_retained_candidate(candidate,retained_candidate)
            require(report['manifest'] == str(HISTORICAL/COHORT/'full-study/manifest.json') and
                    manifest['candidate_manifest_sha256'] == CANDIDATE_SHA and
                    manifest['candidate_manifest'] == str(HISTORICAL/COHORT/'manifest.json'),
                    'Original cohort paths differ')
            for path, digest in manifest['pins'].items():
                files.verify(Path(path), digest)
            audit = strict_json(files.read(Path(candidate['source_audit']),candidate['source_audit_sha256']))
            qualification = strict_json(files.read(Path(manifest['runner_qualification']),manifest['runner_qualification_sha256']))
            sources = {}
            for row in candidate['programs']:
                variant = row['source_profile']
                raw = files.read(Path(row['source']),row['source_sha256'])
                require(raw == files.read(ARCHIVE/'sources'/(variant+'.ua'),row['source_sha256']), 'Retained source differs')
                sources[variant] = raw
                v = row['validation_evidence']
                files.verify(Path(v['path']),v['sha256'])
            raw_records = {}
            for attempt in report['attempts']:
                original = Path(attempt['result_path'])
                expected = HISTORICAL/COHORT/'full-study/attempts'/f'{attempt["attempt"]:03d}-{attempt["id"]}.json'
                require(original == expected, 'Sampler receipt path differs')
                # The exact pinned report constrains every raw sampler field.
                raw = original.read_bytes()
                digest = sha(raw)
                files.verify(original,digest)
                archived = ARCHIVE/'full-study/attempts'/original.name
                require(files.read(archived,digest) == raw, 'Retained sampler receipt differs')
                raw_records[attempt['attempt']] = strict_json(raw)
            with helper_modules() as modules:
                result = reconcile(manifest,report,candidate,audit,qualification,prior,sources,raw_records,modules)
            result.update(file_integrity_verified=True, common_mutex_held=True,
                common_mutex_inode=LOCK_INODE, verified_file_pins=copy.deepcopy(files.pins),
                report=dict(path=str(ARCHIVE/'full-study/report.json'),sha256=REPORT_SHA),
                manifest=dict(path=str(ARCHIVE/'full-study/manifest.json'),sha256=MANIFEST_SHA),
                source_owner_review=dict(path=str(OWNER_REVIEW),sha256=OWNER_REVIEW_SHA),
                independent_source_approval=dict(path=str(SOURCE_APPROVAL),sha256=SOURCE_APPROVAL_SHA),
                prior_independent_reconciliation=dict(path=str(PRIOR_REVIEW),sha256=PRIOR_REVIEW_SHA),
                source_candidate_archive=dict(path=str(ARCHIVE/'manifest.json'),sha256=RETAINED_CANDIDATE_SHA,
                    original_sealed_sha256=CANDIDATE_SHA,
                    documentation_only_changed_fields=['migration_policy'],measurement_fields_changed=False))
            original_pins = tuple(files.pins.items())
            yield result, files
        except BaseException:
            if on_exit_failure is not None:
                on_exit_failure()
            raise
        finally:
            try:
                verify_lock()
                files.final_check(original_pins)
                if final_consumer_check is not None:
                    final_consumer_check()
            except BaseException:
                if on_exit_failure is not None:
                    on_exit_failure()
                raise
