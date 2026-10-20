"""Reconcile complete Ruby processes and append an unchanged-source ZJIT variant."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from qualification.lean_run import energy_output

HERE = ROOT / 'experiments/ruby-jit'
LANG = 'ruby-zjit'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(root, relative):
    return dict(path=relative, sha256=sha(root / relative))


def reconcile(root=ROOT):
    plan = json.loads((root/'experiments/ruby-jit/plan-v1.json').read_text())
    report_path = root/'experiments/ruby-jit/full-v1/report.json'
    report = json.loads(report_path.read_text())
    assert report['status'] == 'PASSED' and report['active'] is None
    assert report['plan_sha256'] == sha(root/'experiments/ruby-jit/plan-v1.json')
    assert len(report['cases']) == 66 and all(c['valid'] for c in report['cases'])
    by_key = {p['key']:p for p in plan['profiles']}
    for row in report['cases']:
        profile = by_key[row['key']]
        expected = plan['full_workloads'][profile['benchmark']]
        expected_command = [plan['runtime']['path']] + [
            '--'+row['jit'] if a == '{jit}' else str(expected[0]) if a == '{n}' else a
            for a in profile['argv']]
        assert row['command'] == expected_command
        assert row['environment'] == profile['environment']
        directory = root/Path(row['stdout']['path']).parent
        assert json.loads((directory/'process.json').read_text()) == row
        assert row['exit_code'] == 0 and not row['timed_out'] and row['elapsed_seconds'] > 0
        assert row['stdout']['bytes'] == (directory/'stdout.bin').stat().st_size
        assert row['stdout']['sha256'] == sha(directory/'stdout.bin')
        assert row['stderr']['bytes'] == 0 and sha(directory/'stderr.bin') == row['stderr']['sha256']
        if profile['benchmark'] == 'nbody':
            assert energy_output((directory/'stdout.bin').read_bytes(),b'-0.169075164\n-0.169059907\n')
        else:
            assert (row['stdout']['bytes'],row['stdout']['sha256']) == tuple(expected[1:])
    programs = []
    for p in plan['profiles']:
        assert sha(root/p['source_path']) == p['source_sha256']
        rows = [c for c in report['cases'] if c['key'] == p['key'] and c['jit'] == 'zjit']
        assert len(rows) == 3 and {r['sample'] for r in rows} == {1,2,3}
        assert all(r['source_sha256'] == p['source_sha256'] and r['runtime_sha256'] == plan['runtime']['sha256'] for r in rows)
        for row in rows:
            process = root/Path(row['stdout']['path']).parent/'process.json'
            assert json.loads(process.read_text()) == row
            assert row['exit_code'] == 0 and not row['timed_out'] and row['elapsed_seconds'] > 0
            assert row['n'] == plan['full_workloads'][p['benchmark']][0]
            assert '--zjit' in row['command'] and '--yjit' not in row['command']
            assert sha(root/row['stdout']['path']) == row['stdout']['sha256']
            assert row['stderr']['bytes'] == 0 and 'AC Power' in row['power']['after']
        yjit_rows = [c for c in report['cases'] if c['key'] == p['key'] and c['jit'] == 'yjit']
        old = p['historical_yjit']
        if old['reusable']:
            assert old['recorded_toolchain']['sha256'] == plan['runtime']['sha256'] and not yjit_rows
            assert sha(root/old['report']) == old['report_sha256']
            yjit_samples = old['samples']
            yjit_basis = 'historical, executable digest matched'
        else:
            assert len(yjit_rows) == 3 and all(c['valid'] for c in yjit_rows)
            yjit_samples = [c['elapsed_seconds'] for c in yjit_rows]
            yjit_basis = 'fresh complete-process samples'
        samples = [r['elapsed_seconds'] for r in rows]
        identity = p['id'] + '-zjit'
        programs.append(dict(id=identity, key=p['benchmark']+':'+identity,
            original_program_key=p['key'], benchmark=p['benchmark'], language=LANG,
            source_sha256=p['source_sha256'], loc=p['loc'], samples_seconds=samples,
            median_seconds=statistics.median(samples), sample_sd_seconds=statistics.stdev(samples),
            yjit_samples_seconds=yjit_samples, yjit_median_seconds=statistics.median(yjit_samples),
            yjit_basis=yjit_basis, zjit_over_yjit=statistics.median(samples)/statistics.median(yjit_samples),
            command=rows[0]['command'], runtime_environment=rows[0]['environment'],
            sample_execution_metadata=rows))
    results = dict(schema='ruby-jit-results.v1', status='RECONCILED',
        programs=programs, new_zjit_samples=57, fresh_yjit_samples=9,
        reused_yjit_profiles=16, historical_data_preserved=True,
        plan=pin(root,'experiments/ruby-jit/plan-v1.json'),
        producer_report=pin(root,'experiments/ruby-jit/full-v1/report.json'),
        toolchains={LANG:dict(version=plan['runtime']['probes']['zjit']['description'],
                              path=plan['runtime']['path'],sha256=plan['runtime']['sha256'])},
        hardware=plan['host'], os=plan['host']['os'], required_power=dict(source='AC Power',low_power_mode=0),
        inputs=copy.deepcopy(report['inputs']),workloads=plan['full_workloads'],timing_boundary=plan['timing_boundary'],
        runtime_details=plan['runtime'])
    fasta = next(p for p in plan['profiles'] if p['id']=='fasta-ruby-2')
    for path, value in results['inputs'].items():
        n=5000000 if Path(path).name=='n5000000.fasta' else 25000000
        value['reconstruction']=dict(command=[plan['runtime']['path']]+[
            '--yjit' if a=='{jit}' else str(n) if a=='{n}' else a for a in fasta['argv']],
            stdout=path,note='Reconstruct the pinned FASTA input; generation is outside subject timing.')
    return results


def append_catalog(before, root=ROOT):
    """Deterministic extension; older LOC and timing records must remain exact."""
    root = Path(root)
    plan = json.loads((root/'experiments/ruby-jit/plan-v1.json').read_text())
    results = json.loads((root/'experiments/ruby-jit/results-v1.json').read_text())
    assert results['status'] == 'RECONCILED' and len(results['programs']) == 19
    assert results['plan'] == pin(root,'experiments/ruby-jit/plan-v1.json')
    assert results['producer_report'] == pin(root,'experiments/ruby-jit/full-v1/report.json')
    report = json.loads((root/'experiments/ruby-jit/full-v1/report.json').read_text())
    assert report['status'] == 'PASSED' and len(report['cases']) == 66
    evidence = {name:pin(root,path) for name,path in dict(
        plan='experiments/ruby-jit/plan-v1.json',results='experiments/ruby-jit/results-v1.json',
        full='experiments/ruby-jit/full-v1/report.json',bounded='experiments/ruby-jit/bounded-v2/report.json').items()}
    data = copy.deepcopy(before)
    assert LANG not in {l['key'] for l in before['languages']}
    catalog = {**before.get('program_inventory',{}),**before['programs']}
    appended = []
    for r in results['programs']:
        parent = catalog[r['original_program_key']]
        assert parent['language'] == 'ruby' and parent['files'] == [r['source_sha256']]
        assert r['loc'] == parent['loc'] and len(r['samples_seconds']) == 3
        assert r['median_seconds'] == statistics.median(r['samples_seconds'])
        measured = [c for c in report['cases'] if c['key'] == parent['key'] and c['jit'] == 'zjit']
        assert len(measured) == 3 and all(c['valid'] and c['exit_code'] == 0 and not c['timed_out'] for c in measured)
        assert [c['elapsed_seconds'] for c in measured] == r['samples_seconds']
        assert measured == r['sample_execution_metadata']
        bench = next(b for b in data['benchmarks'] if b['key'] == r['benchmark'])
        assert r['median_seconds'] >= bench['baseline_seconds'], 'New best time needs a normalization review'
        row = copy.deepcopy(parent)
        for field in ['publication_record','timing_measurement','timing_correction','aliased_sample_source']:
            row.pop(field,None)
        row.update(key=r['key'],id=r['id'],receipt_key=r['id'],language=LANG,seconds=r['median_seconds'],
            samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],
            y=r['median_seconds']/bench['baseline_seconds'],
            report=evidence['results']['path'],report_sha256=evidence['results']['sha256'],
            command=r['command'],runtime_environment=r['runtime_environment'],cwd=str(root),
            binary_sha256=plan['runtime']['sha256'],execution_mode='jit',
            sample_execution_metadata=r['sample_execution_metadata'],
            native_observations=3,source_alias_of=parent['key'],timing_alias_of=None,
            distinct_optimization_claimed=False,
            source_alias_note='Exact retained Ruby submission, measured separately with ZJIT. Application LOC, source attribution and worker policy are unchanged.',
            timing_boundary=plan['timing_boundary'],
            timing_summary='Three fresh complete-process ZJIT samples. YJIT comparisons identify historical executable-matched samples or fresh samples explicitly.',
            full_output_validation=dict(all_three_samples_passed=True,evidence=evidence['full']),
            chart_admission=dict(historical_reports_unchanged=True,**evidence),
            measured_backend=dict(key=LANG,execution='jit',label='CRuby / ZJIT',verified=True,
                evidence=dict(verified=True,report=evidence['results']['path'],report_sha256=evidence['results']['sha256'],
                    command=r['command'],source_sha256=parent['files'],
                    runtime_receipt=dict(verified=True,report=evidence['results']['path'],report_sha256=evidence['results']['sha256'],
                                         field='/toolchains/ruby-zjit/version',value=results['toolchains'][LANG]['version'],value_encoding='literal-saved-string'))))
        row.pop('authorship',None)
        data['programs'][r['key']] = data['program_inventory'][r['key']] = row
        appended.append(r['key'])
    for bench in data['benchmarks']:
        candidates = [data['programs'][key] for key in appended if data['programs'][key]['benchmark'] == bench['key']]
        fast = min(candidates,key=lambda p:(p['seconds'],p['loc'],p['key']))
        small = min(candidates,key=lambda p:(p['loc'],p['seconds'],p['key']))
        formatted = [p for p in candidates if p.get('formatted_loc_complete') is True]
        bench['groups'].append(dict(language=LANG,label='Ruby (ZJIT)',fast=fast['key'],small=small['key'],
            programs=[p['key'] for p in candidates],
            formatted_fast=min(formatted,key=lambda p:(p['seconds'],p['formatted_loc'],p['key']))['key'] if formatted else None,
            formatted_small=min(formatted,key=lambda p:(p['formatted_loc'],p['seconds'],p['key']))['key'] if formatted else None))
    language = copy.deepcopy(next(l for l in before['languages'] if l['key']=='ruby'))
    language.update(key=LANG,label='Ruby (ZJIT)',runtime='CRuby / ZJIT',color='#db7193',
        coverage_note='10/10 full workloads; 19 unchanged submissions; three complete-process samples each.',
        classification_note='CRuby method JIT selected explicitly with --zjit; YJIT disabled. Same source and worker policies as the retained YJIT cohort.')
    data['languages'].append(language)
    for group in data['language_groups']:
        if 'ruby' in group['languages']:
            group['languages'].append(LANG)
    for section,prefix in [('reference_summary',''),('formatted_reference_summary','formatted_')]:
        groups = [g for b in data['benchmarks'] for g in b['groups'] if g['language']==LANG]
        summary = dict(lang=LANG,label='Ruby (ZJIT)',measured_benchmarks=[b['key'] for b in data['benchmarks']])
        for kind in ['fast','small']:
            rows = [data['programs'][g[prefix+kind]] for g in groups if g.get(prefix+kind)]
            summary[kind] = {axis:statistics.geometric_mean(p[axis] for p in rows) for axis in ['formatted_x' if prefix else 'x','y']} if rows else None
            if prefix and rows:
                summary[kind]['x'] = summary[kind].pop('formatted_x')
        if any(summary[k] is not None for k in ['fast','small']):
            data[section].append(summary)
    data['protocol'][LANG] = plan['timing_boundary']
    for ref in evidence.values():
        data['archive_paths'][ref['path']] = ref['path']
    data['ruby_zjit_audit'] = dict(schema='ruby-zjit-catalog-extension.v1',appended_programs=appended,
        evidence=evidence,new_observations=57,source_files_added=0,old_profiles_unchanged=True)
    from audit_authorship import audit
    models = json.loads((root/'data/source-model-evidence.json').read_text())['files']
    authorship = audit(data,models)
    for key in appended:
        data['programs'][key]['authorship'] = authorship[key]
    for pool in ['programs','program_inventory','files','archive_paths']:
        assert all(data[pool][key] == old for key,old in before[pool].items()), pool
    return data


def write_summary(results, root=ROOT):
    rows=results['programs']
    lines=['# Ruby JIT measurements','',
        'The retained Ruby submissions were measured with CRuby 4.0.7 on Apple M3. '
        'Both modes use unchanged source, normalized application LOC, full workload sizes, '
        'and the same worker policies. Times are medians of three complete-process samples, '
        'including startup and JIT warm-up. Output was independently checked in full.','',
        'Both engines use their default compilation thresholds. Cold methods can remain '
        'interpreted with a JIT enabled. These results measure the complete application '
        'under that policy; they do not claim exhaustive runtime tuning.','',
        'Sixteen YJIT profiles reuse historical samples whose recorded executable digest '
        'matches the current executable. The two regex profiles and the pi-digits profile '
        'have fresh YJIT samples because their historical reports lack that digest. '
        'Measurement dates and the comparison basis are retained per profile; this is not '
        'a claim that all YJIT samples were collected alongside ZJIT.','',
        'The ratio is ZJIT time divided by YJIT time; values below 1 favor ZJIT. '
        'The fastest retained source is selected separately for each mode.','',
        '| Workload | YJIT (s) | ZJIT (s) | ZJIT / YJIT |',
        '| --- | ---: | ---: | ---: |']
    for b in results['workloads']:
        candidates=[r for r in rows if r['benchmark']==b]
        y=min(r['yjit_median_seconds'] for r in candidates)
        z=min(r['median_seconds'] for r in candidates)
        lines.append(f'| {b} | {y:.3f} | {z:.3f} | {z/y:.2f}× |')
    lines.extend(['','Every retained source:', '',
        '| Submission | Application LOC | YJIT (s) | ZJIT (s) | ZJIT / YJIT |',
        '| --- | ---: | ---: | ---: | ---: |'])
    for r in sorted(rows,key=lambda r:(r['benchmark'],r['original_program_key'])):
        lines.append(f'| {r["original_program_key"].split(":",1)[1]} | {r["loc"]} | '
                     f'{r["yjit_median_seconds"]:.3f} | {r["median_seconds"]:.3f} | {r["zjit_over_yjit"]:.2f}× |')
    lines.extend(['','The measurements retain the original Benchmarks Game authorship and '
        'license records. No source was generated or rewritten for ZJIT. The [cohort record]'
        '(../experiments/ruby-jit/README.md), [runtime/source plan]'
        '(../experiments/ruby-jit/plan-v1.json), [full execution report]'
        '(../experiments/ruby-jit/full-v1/report.json), and [reconciled observations]'
        '(../experiments/ruby-jit/results-v1.json) retain commands, versions, environment, '
        'input/output digests, individual samples, power checks and source identities.',''])
    (root/'docs/ruby-jit.md').write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconcile',action='store_true')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.reconcile:
        result=reconcile()
        (HERE/'results-v1.json').write_text(json.dumps(result,indent=2)+'\n')
        write_summary(result)
        print('Reconciled 57 ZJIT and 9 fresh YJIT complete-process samples')
    if args.apply:
        path=ROOT/'data/benchmarks.json';before=json.loads(path.read_text())
        after=append_catalog(before)
        languages_path=ROOT/'data/languages.json';languages=json.loads(languages_path.read_text())
        metadata=copy.deepcopy(languages['languages']['ruby'])
        metadata.update(key=LANG,label='Ruby (ZJIT)',runtime='CRuby / ZJIT',
            note='All 19 unchanged submissions measured explicitly with --zjit; the same CRuby binary, full workloads and worker policies are used for YJIT comparison.',
            sources=['https://docs.ruby-lang.org/en/4.0/jit/zjit_md.html','https://docs.ruby-lang.org/en/4.0/GC.html'],
            measurement_basis=[pin(ROOT,'experiments/ruby-jit/results-v1.json')],displayed_program_count=19)
        languages['languages'][LANG]=metadata
        languages['scope']=f'{len(after["languages"])} measured variants; all classifications explicit.'
        module_path=ROOT/'site/src/languages.mjs';module=module_path.read_text()
        match=re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',module,re.S)
        assert match
        values=json.loads(match[2]);values[LANG]={k:metadata[k] for k in ['platform','runtime','execution','typing','style','memory','note','sources']}
        module_path.write_text(match[1]+json.dumps(values,indent=2)+match[3])
        languages_path.write_text(json.dumps(languages,indent=2)+'\n')
        path.write_text(json.dumps(after,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        print('Added 19 ZJIT profiles; all previous profiles, source bytes, samples and baselines unchanged')


if __name__=='__main__':main()
