"""Prepare a private Elixir metadata/publication candidate from closed evidence.

This tool has no apply/publish mode. It writes one new candidate JSON outside
the original timing evidence and publication paths, only after independently
reproducing the pinned reconciliation under all three completed-job leases.
No runtime, compiler, benchmark, or measurement producer is imported or run.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RECONCILER = Path(__file__).with_name('elixir_reconcile.py')
# Independently reviewed source; the file phase binds this and both primitives.
RECONCILER_SHA = '4528dc720240bf0b250c843b5a360e5b1f111e6c45f9370c71dc16ea3df56bbf'


def load_reconciler():
    raw = RECONCILER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RECONCILER_SHA:
        raise ValueError('Independent Elixir reconciler changed')
    spec = importlib.util.spec_from_file_location('elixir_candidate_reconciliation', RECONCILER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(RECONCILER), 'exec'), module.__dict__)
    return module


r = load_reconciler()
p, require, same = r.p, r.require, r.same
PROBE = str(ROOT/'experiments/elixir/compiled-work-v1/probe-v2.exs')
PROBE_SHA = 'aa46dbb8d4fee6350ca63fade5b9619fa4c3cb96ce850a54e880b1585711c946'
ERTS = Path('/opt/homebrew/Cellar/erlang/29.1.1_2/lib/erlang')
RUNTIME_PINS = {
    str(ERTS/'erts-17.1/bin/beam.smp'): '317a5aa96d7f488ee1f5377f76cb87f47279e235b3eff835ec3c98265074116b',
    str(ERTS/'erts-17.1/bin/erlexec'): '60877b262a4aa18ad0d6aaf528e4ded12ad33b89cba9f245678411668c6997e6',
    str(ERTS/'lib/stdlib-8.1/ebin/re.beam'): '7a6d8965ba7d802795f648a388ab243ec5f83df7816caf4d6552bbcb943deb6c',
}
RUNTIME = 'Elixir 1.20.4 on Erlang/OTP 29 / ERTS 17.1 BEAM JIT'
FLAGS = '+S 8:8 +A 1 +SDcpu 1:1 +SDio 1'
ROLES = ('application', 'application-helper', 'application-launcher')
GC_MARKERS = ('process_flag', 'system_flag', 'garbage_collect', 'fullsweep_after',
              'min_heap_size', 'min_bin_vheap_size', 'max_heap_size')


def ref(path, digest):
    require(Path(path).is_absolute() and p.digest(digest), 'Invalid evidence reference')
    return dict(path=path, sha256=digest)


def validate_prerequisites(plan, review, work, counts, compiled_report, compiled_plan):
    _, profiles = r.schedule(plan)
    require(review['schema'] == r.SCHEMA and
            review['status'] == 'full90-reconciled-awaiting-runtime-and-publication-review' and
            review['file_integrity_verified'] is True and review['common_mutex_held'] is True and
            p.integer(review['common_mutex_inode'], p.LOCK_INODE) and
            review['runtime_publication_metadata_qualified'] is False and review['chart_admission'] is False,
            'Completed independent result reconciliation required')
    same(review['plan'], ref(str(ROOT/'experiments/elixir/full90-v1/plan-v1.json'), r.PLAN_SHA),
         'Result review names another plan')
    require(review['verified_file_pins'].get(review['plan']['path']) == r.PLAN_SHA,
            'Reconciliation did not bind its plan')
    require(all(review['verified_file_pins'].get(path) == digest for path, digest in plan['pins'].items()),
            'Reconciliation omitted a prerequisite pin')
    require(work['schema'] == 'elixir-retained-compiled-work-qualified-v1' and
            work['status'] == 'all20-compiled-required-work-qualified' and work['source_work_qualified'] is True and
            p.integer(work['compiled_work_profiles'], 20) and p.integer(work['bounded_cases_reused'], 156),
            'Compiled required-work qualification missing')
    require(counts['schema'] == 'elixir-qualified-source-counts-v1' and
            counts['status'] == 'twenty-retained-source-counts-qualified' and
            counts['canonical_loc_qualified'] is counts['formatted_loc_qualified'] is True,
            'Qualified original and formatted source counts required')
    require(compiled_report['status'] == 'all20-compiled-work-observed-awaiting-direct-instruction-review'
            and compiled_report['active'] is None and len(compiled_report['profiles']) == 20,
            'Original compiled-work report is incomplete')
    require(plan['pins'].get(work['report']) == work['report_sha256'] and
            plan['pins'].get(compiled_report['plan']) == compiled_report['plan_sha256'] and
            compiled_plan['controller_sha256'] == '608789d1345606c2a8a3dafdc710e37b8b409956cc09708cc9dfbc616132572a' and
            compiled_plan['probe'] == PROBE and plan['pins'].get(PROBE) == PROBE_SHA,
            'Retained compiled probe/report binding differs')
    require(all(plan['pins'].get(path) == digest for path, digest in RUNTIME_PINS.items()),
            'Retained BEAM/launcher/Regex support pin differs')
    runtime = counts['reader_runtime']
    require(runtime['elixir_version'] == '1.20.4' and runtime['otp_release'] == '29' and
            runtime['system_version'] == 'Erlang/OTP 29 [erts-17.1] [source] [64-bit] [smp:8:8] [ds:1:1:1] [async-threads:1] [jit] [dtrace]\n',
            'Retained reader runtime identity differs')
    same(counts['formatter'], dict(api='Code.format_string!/2', elixir='1.20.4', line_length=98),
         'Qualified formatter identity differs')
    require(set(review['profiles']) == set(profiles), 'Reconciliation profile inventory differs')
    observed = {row['id']: row for row in compiled_report['profiles']}
    compiled = {row['id']: row for row in compiled_plan['profiles']}
    counted = {row['id']: row for row in counts['profiles']}
    expected = {row['id'] for row in profiles.values() if row['language'] == 'elixir'}
    require(len(observed) == len(compiled) == len(counted) == 20 and
            set(observed) == set(compiled) == set(counted) == expected, 'Qualified cohorts differ')
    for identity in expected:
        row, prior = profiles[identity], compiled[identity]
        for field in ('physical_inputs', 'beams', 'owners', 'runtime_environment'):
            same(row[field], prior[field], 'Retained work/runtime identity differs: '+field)
        same(row['command'], prior['retained_command'], 'Retained command differs')
        summary = observed[identity]['observation']['summary']
        require(summary['dynamic_assertions_passed'] is True and summary['subject_modules_recompiled'] == 0
                and summary['subject_main_executions'] == 1 and summary['common_mutex_inherited'] is True
                and summary['main_beam_sha256'] == row['beams'][0]['sha256']
                and summary['support_beam_sha256'] == row['beams'][1]['sha256'], 'Retained runtime assertion proof differs')
        count = counted[identity]
        require(count['canonical_loc_qualified'] is count['formatted_loc_qualified'] is True and
                (count['canonical_loc'], count['formatted_loc'], count['original_physical_loc']) ==
                (row['canonical_loc'], row['formatted_loc'], row['physical_loc']), 'Profile counts differ')
    return profiles, counted


def sample_records(measured, row, plan, review, read_raw):
    result, good = [], []
    for number in measured['attempts']:
        path = plan['output']+'/attempts/'+f'{number:03d}-{row["id"]}.json'
        digest = review['verified_file_pins'][path]
        supervised = path[:-5]+'.supervisor.json'
        item = p.strict_json(read_raw(supervised, review['verified_file_pins'][supervised]))
        require(item['attempt'] == number and item['key'] == row['key'] and item['id'] == row['id']
                and item['benchmark'] == row['benchmark'], 'Sample evidence belongs to another form')
        qualified = number != measured['failed_attempt']
        require(type(item['qualified']) is bool and item['qualified'] == qualified,
                'Sample qualification differs from independent reconciliation')
        if qualified:
            good.append(item['seconds'])
        outer = plan['output']+'/outer-supervisor/'+f'{number:03d}-{row["id"]}.json'
        result.append(dict(attempt=number, qualified=qualified, seconds=item.get('seconds'),
            started_at=item['started_at'], finished_at=item['finished_at'], stdout_bytes=item['stdout_bytes'],
            stdout_sha256=item['stdout_sha256'], validation=item.get('validation'), error=item.get('error'),
            error_type=item.get('error_type'), raw_evidence=ref(path, digest),
            supervisor_evidence=ref(supervised, review['verified_file_pins'][supervised]),
            outer_supervisor_evidence=ref(outer, review['verified_file_pins'][outer])))
    same(good, measured['samples_seconds'], 'Export samples differ from the independent reconciliation')
    return result


def build_candidate(plan, review, work, counts, compiled_report, compiled_plan, read_raw):
    profiles, counted = validate_prerequisites(plan, review, work, counts, compiled_report, compiled_plan)
    # The pinned probe assertions run in the separately closed qualification
    # processes. They are not claimed as observations in each timed process.
    probe = read_raw(PROBE, PROBE_SHA).decode('utf-8')
    for assertion in ('System.version() == "1.20.4"', ':erlang.system_info(:otp_release) == ~c"29"',
                      ':erlang.system_info(:version) == ~c"17.1"', ':erlang.system_info(:emu_flavor) == :jit',
                      ':erlang.system_info(:schedulers_online) == 8', ':erlang.system_info(:wordsize) == 8',
                      '"aarch64-apple-"'):
        require(assertion in probe, 'Pinned runtime assertion not found')
    first = next(row for row in profiles.values() if row['language'] == 'elixir')
    regex = str(Path(first['binary']).parent.parent/'lib/elixir/ebin/Elixir.Regex.beam')
    require(plan['pins'].get(regex) == 'd15a26fb6786e638e03573093b9c576d7b0105d3fe78d68ba20dde38324833e0',
            'Retained Elixir Regex module differs')
    inventory, controls, files, endpoints, excluded = {}, {}, {}, {}, []
    all_sources = []
    for bench in r.BENCHES:
        control_key = bench+':elixir-full-study:mech-control'
        control_row, measured_control = profiles[control_key], review['profiles'][control_key]
        control = copy.deepcopy(measured_control)
        control['source_evidence'] = ref(control_row['source'], control_row['source_sha256'])
        control['sample_execution_metadata'] = sample_records(measured_control, control_row, plan, review, read_raw)
        controls[bench] = control
        candidates = []
        for variant in ('compact', 'optimized'):
            identity = f'elixir-{bench}-{variant}'
            row, measured, count = profiles[identity], review['profiles'][identity], counted[identity]
            for field in ('id', 'language', 'benchmark', 'source', 'source_sha256', 'binary_sha256'):
                same(measured[field], row[field], 'Measured export identity differs: '+field)
            sources = [counts['files'][name] for name in count['inputs']]
            same([(s['source'], s['source_sha256'], s['role']) for s in sources],
                 [(s['path'], s['sha256'], s['role']) for s in row['physical_inputs']], 'Counted authored bundle differs')
            same([s['role'] for s in sources], list(ROLES), 'Export requires main, helper and launcher')
            file_ids, roles = [], {}
            for source in sources:
                digest = source['source_sha256']
                retained, formatted = source['retained_source'], source['formatted_source']
                require(plan['pins'].get(retained) == digest and
                        plan['pins'].get(formatted) == source['artifact_bindings']['formatted_source']['sha256'],
                        'Retained source/formatter artifact missing from physical closure')
                raw = read_raw(retained, digest)
                code = raw.decode('utf-8')
                require(not any(marker in code for marker in GC_MARKERS), 'Source GC/heap override requires review')
                original_name = {'application':'main.ex','application-helper':'support.ex',
                                 'application-launcher':'runner.exs'}[source['role']]
                public = str(Path(retained).relative_to(ROOT))
                record = dict(sha256=digest, name=original_name, code=code, archive_path=public)
                if digest in files:
                    require(files[digest]['code'] == code, 'Same source hash has different retained content')
                else:
                    files[digest] = record
                require(digest not in roles, 'Duplicate content within authored role bundle')
                file_ids.append(digest)
                roles[digest] = dict(role=source['role'], source_path=public,
                    original_source=ref(source['source'], digest), retained_source=ref(retained, digest),
                    normalized_loc=source['canonical_loc'], physical_loc=source['original_physical_loc'],
                    formatted_loc=source['formatted_loc'], formatted_source=ref(formatted,
                        source['artifact_bindings']['formatted_source']['sha256']),
                    native_ast=ref(source['native_ast'], source['artifact_bindings']['native_ast']['sha256']),
                    formatted_ast=ref(source['formatted_ast'], source['artifact_bindings']['formatted_ast']['sha256']))
                all_sources.append((retained,digest))
            for target, source_field in [('canonical_loc','canonical_loc'), ('formatted_loc','formatted_loc'),
                                         ('physical_loc','original_physical_loc')]:
                require(row[target] == sum(s[source_field] for s in sources), 'Export source total differs')
            successful, control_ok = measured['full_workload_qualified'], measured_control['full_workload_qualified']
            eligible = successful and control_ok
            if successful:
                median, sd = p.three_statistics(measured['samples_seconds'])
                require(median == measured['median_seconds'] and math_close(sd, measured['sample_stdev_seconds']),
                        'Export statistics differ')
            else:
                require(measured['median_seconds'] is measured['sample_stdev_seconds'] is measured['time_x_mech'] is None,
                        'Failed form cannot export a median or ratio')
            ratio = measured['median_seconds']/measured_control['median_seconds'] if eligible else None
            same(measured['time_x_mech'], ratio, 'Matched control ratio differs')
            public_key = bench+':'+identity
            entry = dict(key=public_key, receipt_key=identity, id=identity, benchmark=bench, variant=variant,
                language='elixir', loc=row['canonical_loc'], canonical_loc=row['canonical_loc'],
                formatted_loc=row['formatted_loc'], physical_loc=row['physical_loc'], loc_metric='statement-normalized',
                files=file_ids, file_roles=roles, seconds=measured['median_seconds'],
                samples=copy.deepcopy(measured['samples_seconds']), timing_sd=measured['sample_stdev_seconds'],
                measurement_status='measured' if successful else 'failed-full-workload',
                source_work_qualified=True, canonical_loc_qualified=True, formatted_loc_qualified=True,
                full_workload_qualified=successful, matched_control_qualified=control_ok,
                eligible_for_publication_review=eligible, chart_admission=False, source_alias_note=row['source_alias_note'],
                distinct_optimization_claimed=False, timing_alias_of=None,
                command=row['command'], runtime_environment=row['runtime_environment'], cwd=row['cwd'],
                source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'], beams=row['beams'],
                execution_mode='jit', retained_owner_evidence=row['retained_owner_evidence'],
                sample_execution_metadata=sample_records(measured, row, plan, review, read_raw),
                matched_mech_control_key=control_key, time_ratio_to_matched_mech=ratio,
                failed_attempt=measured['failed_attempt'], evidence=copy.deepcopy(review.get('source_evidence', {})),
                exclusion_reason=None if eligible else ('subject-full-workload-failed' if not successful else 'matched-Mech-control-failed'))
            inventory[public_key] = entry
            if eligible:
                candidates.append(entry)
            else:
                excluded.append(identity)
        if candidates:
            fast = min(candidates, key=lambda v:(v['seconds'], v['canonical_loc'], v['key']))
            small = min(candidates, key=lambda v:(v['canonical_loc'], v['seconds'], v['key']))
            endpoints[bench] = dict(fast=fast['key'], small=small['key'],
                programs=list(dict.fromkeys([small['key'], fast['key']])), chart_admission=False)
        else:
            endpoints[bench] = dict(fast=None, small=None, programs=[], chart_admission=False)
    metadata = dict(key='elixir', label='Elixir', family='elixir', platform='beam', runtime=RUNTIME,
        execution=['jit'], typing='dynamic', style=['functional'], memory=['gc', 'rc'],
        note='BEAM JIT with per-process tracing heaps and reference-counted large binaries; identical source aliases remain independently measured.',
        sources=['https://www.erlang.org/doc/system/beamjit.html',
                 'https://www.erlang.org/doc/apps/erts/garbagecollection.html',
                 'https://www.erlang.org/doc/system/binaryhandling.html'],
        taxonomy_basis='Existing reviewed BEAM taxonomy in data/languages.json; specific retained Elixir execution is bound below',
        runtime_policy=RUNTIME+'; '+FLAGS, memory_policy='Retained default BEAM GC; no GC/heap override in recorded flags or literal authored-source scan',
        normal_schedulers_online=8, dirty_cpu_schedulers=1, dirty_io_schedulers=1, async_threads=1,
        native_architecture='aarch64-apple', word_bytes=8,
        maximum_total_vm_threads_claimed=False, runtime_gc_configuration_observed=False,
        gc_numeric_defaults_claimed=False, regex_jit_observed=False, exact_regex_engine_version=None,
        regex_support='Elixir Regex with the pinned OTP :re general-purpose engine',
        observed_in_closed_qualification_processes=True, observed_in_each_timed_process=False,
        runtime_evidence=ref(PROBE, PROBE_SHA), runtime_pins=dict(RUNTIME_PINS, **{regex:plan['pins'][regex]}),
        qualification_evidence=copy.deepcopy(plan['qualified_work']), reader_runtime=counts['reader_runtime'],
        formatter=counts['formatter'], literal_gc_override_markers=list(GC_MARKERS),
        source_scan_files=len(all_sources), source_scan_limit='Literal marker scan; no numeric GC defaults or per-timed-process runtime probe is claimed',
        evidence_scope='Version, JIT, architecture and scheduler assertions belong to separately closed retained qualification processes. Timed-process evidence binds the unchanged launch, source/BEAM/runtime closure, full output and lifecycle; each timed process was not instrumented for runtime metadata.',
        runtime_publication_metadata_qualified=True, chart_admission=False)
    require(len(inventory) == 20 and len(all_sources) == 60 and len(controls) == len(endpoints) == 10,
            'Private export inventory incomplete')
    return dict(schema='elixir-private-publication-candidate-v1',
        status='validated-evidence-candidate-awaiting-explicit-publication-review',
        chart_admission=False, dataset_files_changed=False, native_processes_started=0,
        language_metadata=metadata, program_inventory=inventory, files=files, matched_mech_controls=controls,
        endpoint_proposals=endpoints, excluded_profiles=excluded,
        plan=review['plan'], report=review['report'], terminal=review['terminal'],
        actual_full_native_processes=review['actual_full_native_processes'], qualified_samples=review['qualified_samples'],
        planned_elixir_samples=60, planned_matched_mech_samples=30, skipped_slots=review['skipped_slots'],
        failed_profiles=review['failed_profiles'], complete_stdout_retained=False,
        full_output_evidence=review['full_output_evidence'], resource_evidence=review['resource_evidence'],
        publication_requirements=['explicit candidate review', 'dataset/catalog/site validation and separately authorized publication'])


def math_close(left, right):
    import math
    return p.finite(right) and right >= 0 and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--reconciliation', type=Path, required=True)
    parser.add_argument('--reconciliation-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    plan = p.strict_json(args.plan.read_bytes())
    target = args.output.resolve()
    require(not target.exists() and target.parent.is_dir() and
            not target.is_relative_to(Path(plan['output']).resolve()) and
            not any(target.is_relative_to(ROOT/name) for name in ('data', 'site')),
            'Candidate requires a new private file outside timing evidence and publication paths')
    with r.review_files(args.plan, args.plan_sha256, args.durable_directory) as fresh:
        saved_bytes = args.reconciliation.read_bytes()
        require(hashlib.sha256(saved_bytes).hexdigest() == args.reconciliation_sha256,
                'Independently saved reconciliation changed')
        saved = p.strict_json(saved_bytes)
        same(fresh, saved, 'Fresh independent reconciliation differs from reviewed result')
        def read_raw(path, digest):
            require(fresh['verified_file_pins'].get(path) == digest, 'Export reads only independently verified evidence')
            raw = Path(path).read_bytes()
            require(hashlib.sha256(raw).hexdigest() == digest, 'Export evidence changed during read')
            return raw
        def document(binding):
            return p.strict_json(read_raw(binding['path'], binding['sha256']))
        work = document(plan['qualified_work'])
        counts = document(plan['qualified_source_counts'])
        compiled_report = document(ref(work['report'], work['report_sha256']))
        compiled_plan = document(ref(compiled_report['plan'], compiled_report['plan_sha256']))
        result = build_candidate(plan, fresh, work, counts, compiled_report, compiled_plan, read_raw)
        result['reconciliation'] = ref(str(args.reconciliation.resolve()), args.reconciliation_sha256)
        result['export_controller'] = ref(str(Path(__file__).resolve()), hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        r.write_result(target, result)
        print(json.dumps(dict(output=str(target), sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                              inventory_forms=20, excluded_profiles=result['excluded_profiles'],
                              dataset_files_changed=False, chart_admission=False)), flush=True)


if __name__ == '__main__':
    main()
