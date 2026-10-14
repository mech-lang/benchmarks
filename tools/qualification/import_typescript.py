#!/usr/bin/env python3
"""Admit a reproduced, explicitly pinned TypeScript candidate to the catalog.

Run after the cohort closes. The independent reconciler retains the durable,
language and common timing leases through verification and optional apply.
Default output is a fresh private directory, including exact original backups.
No runtime, compiler, sampler, benchmark or measurement producer is executed.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import statistics
import stat
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
EXPORTER = Path(__file__).with_name('typescript_export.py')
EXPORTER_SHA = '57cf88e20809c5454234def201fdf87231f3196d6f1ffa9800a2876b2eca87ce'
RELEASE = ROOT/'experiments/typescript/full60-v1/release-metadata-v1.json'
RELEASE_SHA = '65bd9eb3ad7ba37496787b421cf0d19743e5d504386edb11fe926dc210720ba8'
TARGETS = ('data/benchmarks.json', 'data/languages.json', 'site/src/languages.mjs')
META_FIELDS = ('platform', 'runtime', 'execution', 'typing', 'style', 'memory', 'note', 'sources')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_exporter():
    raw = EXPORTER.read_bytes()
    if sha(raw) != EXPORTER_SHA:
        raise ValueError('Frozen TypeScript candidate exporter changed')
    spec = importlib.util.spec_from_file_location('typescript_import_exporter', EXPORTER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(EXPORTER), 'exec'), module.__dict__)
    return module


e = load_exporter()
r, p, require, same = e.r, e.p, e.require, e.same


def checked(path, digest):
    require(p.digest(digest), 'Explicit SHA-256 required: '+str(path))
    raw = regular(path).read_bytes()
    require(sha(raw) == digest, 'Pinned bytes changed: '+str(path))
    return raw


def regular(path):
    path = Path(path).absolute()
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
            'Publication paths must be physical and nonsymlinked: '+str(path))
    require(stat.S_ISREG(path.lstat().st_mode), 'Regular publication file required: '+str(path))
    return path


def destination_root(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path and path.is_dir(),
            'Publication root must be an existing physical directory')
    require(not path.is_relative_to(ROOT) and not ROOT.is_relative_to(path),
            'Publication and evidence roots must be disjoint')
    return path


def publication_links(candidate, refs):
    """Direct portable links only; original physical proof pin maps stay original."""
    links = {}
    def add(relative, expected):
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == relative
                and relative not in TARGETS and p.digest(expected), 'Unsafe publication link')
        require(relative not in links or links[relative] == expected, 'Conflicting publication link')
        links[relative] = expected
    def visit(value):
        if type(value) is list:
            for item in value: visit(item)
        elif type(value) is dict:
            if type(value.get('path')) is str and p.digest(value.get('sha256')):
                path = Path(value['path'])
                if path.is_absolute() and path.is_relative_to(ROOT):
                    add(path.relative_to(ROOT).as_posix(), value['sha256'])
            for item in value.values(): visit(item)
    visit(candidate)
    for binding in refs.values(): add(binding['path'], binding['sha256'])
    for source in candidate['files'].values():
        require(sha(source['code'].encode('utf-8')) == source['sha256'], 'Embedded source bytes differ')
        add(source['archive_path'], source['sha256'])
    return links


def verify_publication_links(links, publication):
    for relative, expected in links.items():
        original = checked(regular(ROOT/relative), expected)
        copied = checked(regular(publication/relative), expected)
        require(copied == original, 'Copied publication link differs: '+relative)


def public_ref(binding, root=ROOT):
    path = Path(binding['path'])
    require(path.is_absolute() and '..' not in path.parts and p.digest(binding['sha256']),
            'Malformed artifact reference')
    require(path.is_relative_to(root) and path.resolve().is_relative_to(root),
            'Public artifact must be retained in the repository: '+str(path))
    return dict(path=path.relative_to(root).as_posix(), sha256=binding['sha256'])


def public_refs(value, root=ROOT):
    """Public links become relative; external original provenance stays explicit."""
    if type(value) is list:
        return [public_refs(v, root) for v in value]
    if type(value) is dict:
        result = {k: public_refs(v, root) for k, v in value.items()}
        if type(value.get('path')) is str and p.digest(value.get('sha256')):
            path = Path(value['path'])
            if path.is_absolute() and path.is_relative_to(root):
                result.update(public_ref(value, root))
        return result
    return value


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def lease_identities(paths):
    result = {}
    for path in paths:
        stat = path.stat()
        result[path] = (stat.st_dev, stat.st_ino)
    return result


def verify_named_leases(expected):
    require(lease_identities(expected) == expected, 'Completed-job lease pathname changed')


def verify_private_outputs(owned):
    for path,record in owned.items():
        identity=regular(path).lstat()
        require((identity.st_dev,identity.st_ino)==record['identity'],
                'Private publication artifact replaced: '+str(path))
        require(path.read_bytes()==record['raw'],'Private publication artifact changed: '+str(path))
        identity=regular(path).lstat()
        require((identity.st_dev,identity.st_ino)==record['identity'],
                'Private publication artifact replaced during read: '+str(path))


def write_private(path,raw,owned):
    require(path.parent.resolve() == path.parent, 'Private output parent redirected')
    with path.open('xb') as stream:
        identity=os.fstat(stream.fileno())
        owned[path]=dict(identity=(identity.st_dev,identity.st_ino),raw=raw)
        stream.write(raw);stream.flush();os.fsync(stream.fileno())


def validate_candidate(candidate):
    require(candidate['schema'] == 'typescript-private-publication-candidate-v1'
            and candidate['status'] == 'validated-evidence-candidate-awaiting-publication-review'
            and candidate['chart_admission'] is False and candidate['dataset_files_changed'] is False
            and p.integer(candidate['native_processes_started'], 0), 'Private candidate policy changed')
    metadata = candidate['language_metadata']
    require(metadata['key'] == metadata['family'] == 'typescript' and metadata['label'] == 'TypeScript (Node)'
            and metadata['platform'] == 'javascript' and metadata['execution'] == ['jit']
            and metadata['typing'] == 'static' and metadata['style'] == ['imperative','object','functional']
            and metadata['memory'] == ['gc'] and metadata['chart_admission'] is False
            and metadata['runtime_publication_metadata_qualified'] is True,
            'Reviewed typed TypeScript / Node taxonomy required')
    require(metadata['runtime_gc_configuration_observed'] is False
            and metadata['gc_numeric_defaults_claimed'] is False
            and metadata['observed_in_each_timed_process'] is False
            and metadata['actual_loaded_image_inventory_observed'] is False, 'Runtime evidence scope changed')
    expected = {b+':typescript-'+b+'-v1' for b in r.BENCHES}
    require(set(candidate['program_inventory']) == expected
            and set(candidate['matched_mech_controls']) == set(candidate['endpoint_proposals']) == set(r.BENCHES),
            'Exact ten real sources and ten matched controls required')
    excluded = []
    for key, row in candidate['program_inventory'].items():
        require(row['key'] == key and row['language'] == 'typescript'
                and row['receipt_key'] == row['id'] and key == row['benchmark']+':'+row['id']
                and row['chart_admission'] is False and row['distinct_optimization_claimed'] is False
                and row['timing_alias_of'] is None and row['source_alias_of'] is None, 'Source-form identity or producer policy changed')
        require(row['source_work_qualified'] is row['canonical_loc_qualified'] is True and row['formatted_loc_qualified'] is False and row['formatted_loc'] is None,
                'Source/work/count gates incomplete')
        require(len(row['files']) == len(set(row['files'])) == 1 and set(row['files']) == set(row['file_roles'])
                and {v['role'] for v in row['file_roles'].values()} == set(e.ROLES), 'One authored application source required')
        for field, role_field in (('loc', 'normalized_loc'), ('physical_loc', 'physical_loc')):
            values = [v[role_field] for v in row['file_roles'].values()]
            require(all(type(v) is int and v > 0 for v in values) and row[field] == sum(values),
                    'Counted bundle total differs: '+field)
        require(row['canonical_loc'] == row['loc'], 'Canonical LOC differs')
        control = candidate['matched_mech_controls'][row['benchmark']]
        require(control['key'] == row['matched_mech_control_key'] == row['benchmark']+':typescript-full-study:mech-control'
                and control['language'] == 'mech', 'Matched control identity differs')
        success, control_ok = row['full_workload_qualified'], control['full_workload_qualified']
        require(type(success) is type(control_ok) is bool
                and row['matched_control_qualified'] is control_ok
                and row['eligible_for_publication_review'] is (success and control_ok), 'Eligibility differs')
        if success:
            require(len(row['samples']) == 3 and all(positive(x) for x in row['samples']), 'Three subject samples required')
            median, sd = p.three_statistics(row['samples'])
            require(row['seconds'] == median and e.math_close(sd, row['timing_sd']), 'Subject statistics differ')
        else:
            require(row['seconds'] is row['timing_sd'] is row['time_ratio_to_matched_mech'] is None
                    and row['failed_attempt'] is not None, 'Failed form must retain failure and null summary')
        if success and control_ok:
            require(len(control['samples_seconds']) == 3 and all(positive(x) for x in control['samples_seconds'])
                    and control['median_seconds'] == sorted(control['samples_seconds'])[1]
                    and row['time_ratio_to_matched_mech'] == row['seconds']/control['median_seconds'],
                    'Matched-control statistics differ')
        else:
            require(row['time_ratio_to_matched_mech'] is None, 'Excluded form has a control ratio')
            excluded.append(row['id'])
        samples = row['sample_execution_metadata']
        same([s['seconds'] for s in samples if s['qualified']], row['samples'], 'Sample receipt values differ')
        require(len({s['attempt'] for s in samples}) == len(samples), 'Repeated sample receipt')
        require([s['attempt'] for s in samples if not s['qualified']] ==
                ([] if success else [row['failed_attempt']]), 'Failure evidence missing')
    same(sorted(excluded), sorted(candidate['excluded_profiles']), 'Excluded inventory differs')
    used = {f for row in candidate['program_inventory'].values() for f in row['files']}
    require(used == set(candidate['files']), 'Unowned source content')
    for digest, source in candidate['files'].items():
        require(digest == source['sha256'] == sha(source['code'].encode('utf-8')), 'Authored source hash differs')




def build_publication(originals, candidate, release, refs, plan, root=ROOT):
    """Pure transformation; caller must reproduce the candidate under live leases."""
    validate_candidate(candidate)
    require(release['schema'] == 'typescript-publication-release-metadata-v1' and release['language'] == 'typescript'
            and release['release_year'] == 2012 and release['chart_admission'] is False,
            'Reviewed release metadata required')
    data, languages = (p.strict_json(originals[name]) for name in TARGETS[:2])
    match = re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',
                         originals[TARGETS[2]].decode('utf-8'), re.S)
    require(match is not None, 'Unexpected taxonomy module syntax')
    module = p.strict_json(match[2])
    before = copy.deepcopy(data)
    require('typescript' not in {v['key'] for v in data['languages']} and 'typescript' not in languages['languages']
            and 'typescript' not in module and 'typescript_audit' not in data, 'TypeScript already admitted')
    require(not any(v['language'] == 'typescript' for pool in ('programs', 'program_inventory')
                    for v in data[pool].values()), 'TypeScript programs already present')
    require({b['key'] for b in data['benchmarks']} == set(r.BENCHES), 'Dataset benchmark cohort differs')
    public = public_refs(candidate, root)
    meta = public['language_metadata']
    for source in public['files'].values():
        source['path'] = source['archive_path']
        path = Path(source['path'])
        require(not path.is_absolute() and '..' not in path.parts and (root/path).resolve().is_relative_to(root),
                'Unsafe public source path')
        digest = source['sha256']
        if digest in data['files']:
            same(data['files'][digest]['code'], source['code'], 'Existing source hash collision')
        else:
            data['files'][digest] = source
        data['archive_paths'].setdefault(source['path'], source['archive_path'])
    for binding in (*refs.values(), public['report'], public['terminal'], public['plan']):
        name = binding['path']
        require(not Path(name).is_absolute(), 'Public review/report link is not portable')
        require(data['archive_paths'].get(name, name) == name, 'Existing archive mapping conflicts')
        data['archive_paths'][name] = name
    endpoints, admitted = {}, []
    for bench in data['benchmarks']:
        name = bench['key']
        control = public['matched_mech_controls'][name]
        rows = []
        for variant in ('v1',):
            key = name+':typescript-'+name+'-'+variant
            row = copy.deepcopy(public['program_inventory'][key])
            require(key not in data['program_inventory'] and key not in data['programs'], 'Program identity already exists')
            eligible = row['eligible_for_publication_review']
            require(positive(bench['baseline_loc']) and positive(bench['baseline_seconds']), 'Invalid retained baseline')
            if eligible:
                require(row['loc'] >= bench['baseline_loc'] and row['seconds'] >= bench['baseline_seconds'],
                        'New TypeScript minimum requires a separately reviewed baseline update: '+key)
            role = next(v for v in row['file_roles'].values() if v['role'] == 'application')
            source = role['retained_source']
            row.update(eligible_for_chart=eligible, required_work_validated=True,
                original_admission_policy=dict(candidate_chart_admission=False, program_chart_admission=False,
                    runtime_chart_admission=False, eligible_for_publication_review=eligible),
                chart_admission=(dict(historical_reports_unchanged=True, independent_candidate=refs['candidate'],
                    reconciliation=refs['reconciliation'], release_metadata=refs['release']) if eligible else False),
                report=public['report']['path'], report_sha256=public['report']['sha256'],
                loc_report=public_refs(plan['qualified_source_counts'], root)['path'],
                source_report=public_refs(plan['qualified_source_counts'], root)['path'],
                loc_expansions=[],
                formatted_loc_status='unavailable', formatted_loc_complete=False,
                formatted_loc_evidence=None,
                runtime_policy=meta['runtime_policy'], memory_policy=meta['memory_policy'],
                runtime_support=meta['regex_support'] if name == 'regexredux' else 'Retained emitted JavaScript and Node/V8 runtime',
                runtime_evidence=copy.deepcopy(meta), runtime_evidence_scope=meta['evidence_scope'],
                runtime_gc_configuration_observed=False, gc_numeric_defaults_claimed=False,
                timing_boundary=plan['timing_policy'],
                timing_summary='Median of three qualified full fresh-process runs; Node startup, JavaScript loading, runtime JIT, input, work, output and shutdown included. Failed forms retain partial samples without a median.',
                source_provenance='One retained authored application; canonical source-parser counts and required work independently qualified. Formatted LOC is unavailable.',
                source_provenance_record=dict(source_evidence=source, canonical_source_evidence=public_refs(plan['qualified_source_counts'], root),
                    required_work_evidence=public_refs(plan['qualified_work'], root), authored_roles=copy.deepcopy(row['file_roles'])),
                source_url=data['repository']['url'].rstrip('/')+'/blob/main/'+quote(source['path']),
                source_link_label='Exact retained source', local_adaptation=True,
                matched_mech_control=copy.deepcopy(control),
                full_output_validation=[v['validation'] for v in row['sample_execution_metadata']],
                x=row['loc']/bench['baseline_loc'] if eligible else None,
                y=row['seconds']/bench['baseline_seconds'] if eligible else None,
                formatted_x=None,
                measured_backend=dict(key='node-jit', execution='jit', label=meta['runtime_policy'], verified=True,
                    evidence=dict(verified=True, report=public['report']['path'], report_sha256=public['report']['sha256'],
                        command=row['command'], source_sha256=list(row['files']),
                        runtime_receipt=dict(verified=True, report=refs['candidate']['path'], report_sha256=refs['candidate']['sha256'],
                            field='/language_metadata/execution/0', value='jit', value_encoding='literal-saved-string'))))
            row['publication_record'] = copy.deepcopy(row)
            data['program_inventory'][key] = row
            if eligible:
                rows.append(row)
        proposal = candidate['endpoint_proposals'][name]
        if not rows:
            same(proposal, dict(fast=None, small=None, programs=[], chart_admission=False), 'Excluded endpoint proposal differs')
            endpoints[name] = dict(fast=None, small=None, formatted_fast=None, formatted_small=None, programs=[])
            continue
        fast = min(rows, key=lambda v:(v['seconds'], v['loc'], v['key']))
        small = min(rows, key=lambda v:(v['loc'], v['seconds'], v['key']))
        same(proposal, dict(fast=fast['key'], small=small['key'],
             programs=list(dict.fromkeys([small['key'], fast['key']])), chart_admission=False), 'Endpoint proposal differs')
        formatted = [v for v in rows if positive(v['formatted_x'])]
        ffast = min(formatted, key=lambda v:(v['seconds'], v['formatted_loc'], v['key'])) if formatted else None
        fsmall = min(formatted, key=lambda v:(v['formatted_loc'], v['seconds'], v['key'])) if formatted else None
        selected = list(dict.fromkeys(v['key'] for v in (fast, small, ffast, fsmall) if v))
        data['programs'].update({key:data['program_inventory'][key] for key in selected})
        endpoint = dict(fast=fast['key'], small=small['key'], formatted_fast=ffast['key'] if ffast else None,
                        formatted_small=fsmall['key'] if fsmall else None, programs=selected)
        bench['groups'].append(dict(language='typescript', label='TypeScript (Node)', **endpoint))
        endpoints[name] = endpoint
        admitted.append(name)
    formatted_benches = [name for name in admitted if endpoints[name]['formatted_fast']]
    language = dict(meta, **{key:release[key] for key in ('release_year', 'release_name', 'release_source', 'release_note')})
    module['typescript'] = {key:copy.deepcopy(language[key]) for key in META_FIELDS}
    data['languages'].append(dict(key='typescript', label='TypeScript (Node)', family='typescript', color='#3178c6',
        release_year=release['release_year'], release_name=release['release_name'], release_source=release['release_source'],
        release_note=release['release_note'], timed_benchmarks=admitted, source_benchmarks=[b['key'] for b in data['benchmarks']],
        formatted_timed_benchmarks=formatted_benches, formatted_source_benchmarks=[],
        runtime_family='javascript', runtime=meta['runtime'], execution_modes=['jit'], typing='static', execution='JIT',
        line_style='solid', runtime_policy=meta['runtime_policy'], paradigms=['imperative','object','functional'], memory_models=['gc'],
        classification_note=meta['note'], coverage_note=f'{len(admitted)}/10 workloads admitted; failed forms and controls retain evidence without chart coordinates.'))
    displayed = sum(v['language'] == 'typescript' for v in data['programs'].values())
    languages['languages']['typescript'] = dict(language, displayed_program_count=displayed,
        measurement_basis=[dict(refs['candidate'], status='independently-reproduced-publication-candidate')])
    languages['audited_on'] = datetime.now(timezone.utc).date().isoformat()
    languages['scope'] = str(len(data['languages']))+' measured variants; all classifications explicit.'
    if admitted:
        reference = dict(lang='typescript', label='TypeScript (Node)', measured_benchmarks=admitted)
        for kind in ('fast', 'small'):
            rows = [data['program_inventory'][endpoints[name][kind]] for name in admitted]
            reference[kind] = {axis:statistics.geometric_mean(v[axis] for v in rows) for axis in ('x', 'y')}
        data['reference_summary'].append(reference)
    data['protocol']['typescript'] = (meta['runtime_policy']+'. Ten real source records and ten matched Mech controls; '
        'only complete qualified forms with complete qualified controls are chart eligible. The authored application counts in canonical LOC; formatted LOC is unavailable. '
        'Each workload has one implementation without source or timing aliases. Retained toolchain metadata and default timed Node policy bind runtime identity; no per-sample diagnostic probe or numeric GC defaults are claimed.')
    for group in data['language_groups']:
        if group['key'] in ('jit', 'functional'):
            require('typescript' not in group['languages'], 'Duplicate filter membership')
            group['languages'].append('typescript')
    audit = dict(schema='typescript-publication-import-v1', status='qualified-saved-cohort-prepared',
        **refs, full_report=public['report'], terminal=public['terminal'], endpoints=endpoints,
        imported_program_inventory=10, imported_endpoint_programs=displayed, admitted_workloads=admitted,
        excluded_profiles=candidate['excluded_profiles'], failed_profiles=candidate['failed_profiles'],
        skipped_slots=candidate['skipped_slots'], actual_full_native_processes=candidate['actual_full_native_processes'],
        qualified_samples=candidate['qualified_samples'], planned_typescript_samples=30, planned_matched_mech_samples=30,
        baseline_changed=False, historical_reports_mutated=False, original_producer_chart_flags_preserved=True,
        native_commands=0, benchmark_runs=0, runtime_gc_configuration_observed=False)
    data['typescript_audit'] = audit
    for field in ('programs', 'program_inventory', 'files', 'archive_paths'):
        same({key:data[field][key] for key in before[field]}, before[field], 'Existing '+field+' changed')
    for old, new in zip(before['benchmarks'], data['benchmarks']):
        same(dict(new, groups=[v for v in new['groups'] if v['language'] != 'typescript']), old, 'Existing workload/baseline changed')
    for field in ('languages', 'reference_summary', 'formatted_reference_summary'):
        same(data[field][:len(before[field])], before[field], 'Existing '+field+' changed')
    allowed = {'programs', 'program_inventory', 'files', 'archive_paths', 'benchmarks', 'languages',
               'reference_summary', 'formatted_reference_summary', 'protocol', 'language_groups'}
    for key in set(before)-allowed:
        same(data[key], before[key], 'Unrelated dataset value changed')
    require(set(module) == set(languages['languages']) == {v['key'] for v in data['languages']}, 'Taxonomy keys differ')
    encoded = {TARGETS[0]:(json.dumps(data, indent=2, allow_nan=False)+'\n').encode(),
               TARGETS[1]:(json.dumps(languages, indent=2, allow_nan=False)+'\n').encode(),
               TARGETS[2]:(match[1]+json.dumps(module, indent=2, allow_nan=False)+match[3]).encode()}
    return encoded, audit


def apply_prepared(root, prepared, originals, pins, verify_leases, journal=None):
    """Checked three-file replacement; restore only still-owned replacements."""
    replaced = [] if journal is None else journal
    require(not replaced, 'Publication journal must start empty')
    temporaries = []
    try:
        for name, raw in prepared.items():
            verify_leases()
            for previous in replaced:
                require(regular(root/previous).read_bytes()==prepared[previous],
                        'Earlier catalog replacement changed: '+previous)
            checked(root/name, pins[name])
            temporary = root/(name+'.typescript-import.tmp')
            with temporary.open('xb') as stream:
                identity=os.fstat(stream.fileno())
                temporaries.append((temporary,(identity.st_dev,identity.st_ino),raw))
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            checked(root/name, pins[name])
            # Record intent before the rename: interruption after replacement
            # must never leave a changed catalog outside the rollback journal.
            replaced.append(name)
            temporary.replace(root/name)
        verify_leases()
        for name,raw in prepared.items():
            require(regular(root/name).read_bytes()==raw,'Catalog changed during apply: '+name)
    except BaseException as failure:
        restoration_errors=[]
        try:
            rollback_publication(root,{name:prepared[name] for name in replaced},originals)
        except BaseException as error:restoration_errors.append(error)
        for path,identity,raw in temporaries:
            try:
                if not path.exists() and not path.is_symlink():continue
                current=path.lstat()
                require(not path.is_symlink() and (current.st_dev,current.st_ino)==identity
                        and raw.startswith(regular(path).read_bytes()),'Temporary file changed; preserving unrelated bytes')
                path.unlink()
            except BaseException as error:restoration_errors.append(error)
        if restoration_errors:
            raise BaseExceptionGroup('Publication apply and guarded restoration failed',[failure,*restoration_errors])
        raise


def rollback_publication(root, prepared, originals):
    errors=[]
    for name in reversed(tuple(prepared)):
        try:
            current=regular(root/name).read_bytes()
            require(current in (prepared[name],originals[name]),
                    'Catalog changed after apply; preserving unrelated bytes: '+name)
            if current==prepared[name]:
                (root/name).write_bytes(originals[name])
                require(regular(root/name).read_bytes()==originals[name], 'Restored catalog bytes changed: '+name)
        except BaseException as error:
            errors.append(name+': '+str(error))
    require(not errors,'Publication restoration conflicts: '+str(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'reconciliation', 'plan'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--importer-sha256', required=True, help='Independently reviewed importer source SHA-256')
    for name in ('benchmarks', 'languages', 'module'):
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--publication-root', type=Path, required=True,
                        help='Distinct physical checkout containing the three current publication targets')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    tool_path = Path(__file__).resolve()
    tool_sha = args.importer_sha256
    checked(tool_path, tool_sha)
    publication = destination_root(args.publication_root)
    identity = publication.stat()
    publication_identity = (identity.st_dev, identity.st_ino)
    output = args.output.absolute()
    require(output.resolve() == output and not output.exists() and not output.is_relative_to(ROOT)
            and not output.is_relative_to(publication), 'Fresh physical private output must be outside both repositories')
    pins = dict(zip(TARGETS, (args.benchmarks_sha256, args.languages_sha256, args.module_sha256)))
    # Capture names before entering the independently verified lock context.
    # Once it yields, its live handles have been matched to these same inodes;
    # names are rechecked before every publication replacement below.
    names = lease_identities((args.durable_directory.resolve()/'owner.lock',
                              ROOT/'experiments/typescript/typescript-full60.owner.lock', r.LOCK))
    require(names[r.LOCK][1] == p.LOCK_INODE, 'Original common mutex changed')
    applied=False
    mutation_journal=[]
    prepared=originals=None
    owned_private={}
    links={}
    def undo_success():
        nonlocal applied
        errors=[]
        if mutation_journal:
            try:
                check_destination()
                rollback_publication(publication,{name:prepared[name] for name in mutation_journal},originals)
                mutation_journal.clear()
                applied=False
            except BaseException as error: errors.append(str(error))
        try:
            receipt_path=output/'import-receipt.json'
            record=owned_private.get(receipt_path)
            if record:
                if receipt_path.exists() or receipt_path.is_symlink():
                    identity=regular(receipt_path).lstat()
                    require((identity.st_dev,identity.st_ino)==record['identity'],
                            'Success receipt replaced; preserving unrelated bytes')
                    e.remove_owned(receipt_path,sha(record['raw']))
                owned_private.pop(receipt_path)
            elif record is not None:
                # Exclusive creation never completed; no receipt was adopted.
                owned_private.pop(receipt_path)
        except BaseException as error:errors.append(str(error))
        require(not errors,'Publication rollback errors: '+str(errors))
    def check_destination():
        require(destination_root(publication) == publication, 'Publication root changed')
        current = publication.stat()
        require((current.st_dev,current.st_ino) == publication_identity, 'Publication root replaced')
    def check_publication_inputs():
        check_destination()
        verify_publication_links(links, publication)
        for path,digest in e.EXTRA_PINS.items():checked(path,digest)
        for path,digest in ((args.candidate,args.candidate_sha256),(args.reconciliation,args.reconciliation_sha256),
                            (RELEASE,RELEASE_SHA),(EXPORTER,EXPORTER_SHA),(tool_path,tool_sha)):
            checked(path,digest)
        verify_named_leases(names)
        verify_private_outputs(owned_private)
        if originals is not None:
            expected=prepared if applied else originals
            for name,raw in expected.items():
                require(regular(publication/name).read_bytes()==raw,'Catalog changed before publication closure: '+name)
    with r.review_files(args.plan,args.plan_sha256,args.durable_directory,on_exit_failure=undo_success,
                        final_consumer_check=check_publication_inputs) as fresh:
        with e.guarded_closure(check_publication_inputs,undo_success):
            try:
                verify_named_leases(names)
                plan = p.strict_json(checked(args.plan, args.plan_sha256))
                saved = p.strict_json(checked(args.reconciliation, args.reconciliation_sha256))
                same(fresh, saved, 'Independent reconciliation changed')
                candidate = p.strict_json(checked(args.candidate, args.candidate_sha256))
                def read_raw(path, digest):
                    require((fresh['verified_file_pins'].get(path) == digest or e.EXTRA_PINS.get(path) == digest), 'Unverified export input')
                    return checked(path, digest)
                def document(binding):
                    return p.strict_json(read_raw(binding['path'], binding['sha256']))
                work, counts = document(plan['qualified_work']), document(plan['qualified_source_counts'])
                metadata = document(e.ref(str(e.RUNTIME_METADATA),e.RUNTIME_METADATA_SHA))
                rebuilt = e.build_candidate(plan, fresh, work, counts, metadata, read_raw)
                rebuilt['reconciliation'] = e.ref(str(args.reconciliation.resolve()), args.reconciliation_sha256)
                rebuilt['export_controller'] = e.ref(str(EXPORTER), EXPORTER_SHA)
                same(candidate, rebuilt, 'Pinned candidate is not the exact independent export')
                release = p.strict_json(checked(RELEASE, RELEASE_SHA))
                refs = {name:public_ref(e.ref(str(path.resolve()), digest), root=ROOT) for name,path,digest in (
                    ('candidate', args.candidate, args.candidate_sha256),
                    ('reconciliation', args.reconciliation, args.reconciliation_sha256), ('release', RELEASE, RELEASE_SHA),
                    ('import_controller', tool_path, tool_sha))}
                links = publication_links(candidate, refs)
                verify_publication_links(links, publication)
                originals = {name:checked(publication/name, digest) for name,digest in pins.items()}
                prepared, audit = build_publication(originals, candidate, release, refs, plan, root=ROOT)
                # Full physical closure was independently established above. Recheck it
                # before any write, retaining every lease through write/apply/receipt.
                for path, digest in fresh['verified_file_pins'].items():
                    with Path(path).open('rb') as stream:
                        require(hashlib.file_digest(stream, 'sha256').hexdigest() == digest, 'Evidence changed during import')
                for name,digest in pins.items():
                    checked(publication/name, digest)
                checked(args.candidate, args.candidate_sha256)
                checked(args.reconciliation, args.reconciliation_sha256)
                checked(RELEASE, RELEASE_SHA)
                for path,digest in e.EXTRA_PINS.items(): checked(path,digest)
                checked(EXPORTER, EXPORTER_SHA)
                checked(tool_path, tool_sha)
                expected_inventory = {path for path in fresh['verified_file_pins'] if Path(path).is_relative_to(Path(plan['output']))}
                require(r.inventory(Path(plan['output'])) == expected_inventory, 'Closed artifact inventory changed during import')
                verify_named_leases(names)
                checked(tool_path, tool_sha)
                check_publication_inputs()
                output.mkdir(parents=True)
                for name, raw in prepared.items():
                    checked(tool_path, tool_sha)
                    target, backup = output/name, output/'originals'/name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    checked(tool_path, tool_sha)
                    write_private(target,raw,owned_private)
                    checked(tool_path, tool_sha)
                    write_private(backup,originals[name],owned_private)
                receipt = dict(audit, generated_at=datetime.now(timezone.utc).isoformat(), applied=False,
                    evidence_root=str(ROOT), publication_root=str(publication),
                    copied_publication_links=dict(links), inputs=pins, outputs={name:sha(raw) for name,raw in prepared.items()},
                    import_tool=dict(path=str(tool_path), sha256=tool_sha),
                    verified_artifact_count=len(fresh['verified_file_pins']))
                if args.apply:
                    def verify_apply():
                        check_destination()
                        verify_publication_links(links, publication)
                        verify_named_leases(names)
                        checked(tool_path, tool_sha)
                    apply_prepared(publication, prepared, originals, pins, verify_apply, mutation_journal)
                    applied=True
                    receipt.update(applied=True, status='qualified-saved-cohort-imported')
                checked(tool_path, tool_sha)
                receipt_path=output/'import-receipt.json';receipt_ownership={}
                # The writer fills this caller-owned record immediately after
                # exclusive creation, before a completed-write return can fail.
                owned_private[receipt_path]=receipt_ownership
                e.write_new(receipt_path,receipt,receipt_ownership)
            except BaseException as failure:
                try:
                    undo_success()
                except BaseException as cleanup:
                    raise BaseExceptionGroup('Publication and guarded restoration failed',[failure,cleanup])
                raise
    print(json.dumps({key:receipt[key] for key in ('status', 'applied', 'imported_program_inventory',
        'imported_endpoint_programs', 'admitted_workloads', 'excluded_profiles', 'baseline_changed')}), flush=True)



if __name__ == '__main__':
    main()
