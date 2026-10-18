"""Admit reconciled Luau VM/JIT programs while preserving historical results."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'experiments/luau'
TARGETS=('data/benchmarks.json','data/languages.json','site/src/languages.mjs','data/source-predecessor-evidence.json')
META_FIELDS=('platform','runtime','execution','typing','style','memory','note','sources')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def pin(path):return dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()))


def transform(originals,results,counts,metadata,report,provenance):
    data=json.loads(originals[TARGETS[0]])
    before=copy.deepcopy(data)
    languages=json.loads(originals[TARGETS[1]])
    match=re.fullmatch(r'(\s*//[^\n]*\nexport const languageMetadata = )(\{.*\})(;\s*)',originals[TARGETS[2]].decode(),re.S)
    assert match
    module=json.loads(match[2])
    lineage=json.loads(originals[TARGETS[3]])
    assert results['status']=='SIXTY_FULL_SIZE_SAMPLES_RECONCILED' and results['benchmark_samples']==60
    assert results['all_full_outputs_validated'] and results['all_process_records_reconciled']
    assert counts['status']=='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES'
    assert report['status']=='PASSED' and report['sources']==provenance['sources']
    refs={name:pin(HERE/path) for name,path in {
        'results':'results-v1.json','source_counts':'source-counts-v1/qualified-v1/qualified-counts.json',
        'required_work':'required-work-v2/review.json','runtime':'runtime-metadata-v1.json',
        'build':'build-v2/report.json','origin':'source-provenance-v1.json','full_report':'full-v1/report.json'}.items()}
    revision=report['source_commit']
    assert re.fullmatch('[0-9a-f]{40}',revision)
    for name,unit in counts['units'].items():
        path=HERE/'source-v1'/name;raw=path.read_bytes()
        assert digest(raw)==unit['sha256']
        relative=path.relative_to(ROOT).as_posix()
        assert subprocess.check_output(['git','show',revision+':'+relative],cwd=ROOT)==raw
        data['files'].setdefault(unit['sha256'],dict(sha256=unit['sha256'],name=name,code=raw.decode(),path=relative,archive_path=relative))
        data['archive_paths'][relative]=relative
    for r in refs.values():data['archive_paths'][r['path']]=r['path']
    catalog={**before['program_inventory'],**before['programs']}
    appended=[]
    for language,mode in [('luau','vm'),('luau-jit','jit')]:
        assert language not in module and language not in languages['languages']
        meta=metadata['variants'][language]
        language_programs=[]
        for bench in data['benchmarks']:
            b=bench['key'];timing=results['results'][language][b];bundle=counts['profiles'][b]
            assert timing['median_seconds']>=bench['baseline_seconds'] and bundle['canonical_loc']>=bench['baseline_loc'],'New minimum requires separate normalization review'
            rows=[r for r in report['cases'] if r['benchmark']==b and r['execution_mode']==mode]
            assert len(rows)==3 and all(r['valid'] and r['exit_code']==0 and not r['timed_out'] for r in rows)
            assert timing['samples_seconds']==[r['elapsed_seconds'] for r in rows]
            assert timing['median_seconds']==statistics.median(timing['samples_seconds'])
            identity=f'{language}-{b}-v1';key=b+':'+identity
            assert key not in data['program_inventory'] and key not in data['programs']
            files=[counts['units'][name]['sha256'] for name in bundle['files']]
            roles={counts['units'][name]['sha256']:dict(role='application' if name.endswith('.luau') else 'application-helper',
                source_path=counts['units'][name]['path'],normalized_loc=counts['units'][name]['canonical_loc'],
                physical_loc=counts['units'][name]['physical_loc'],canonical_projection=refs['source_counts']) for name in bundle['files']}
            expansions=[]
            for name in bundle['files']:
                unit=counts['units'][name];lines=(HERE/'source-v1'/name).read_text().splitlines()
                expansions.append(dict(source=unit['path'],name=name,sha256=unit['sha256'],source_language=unit['source_language'],
                    physical_loc=unit['physical_loc'],normalized_loc=unit['canonical_loc'],
                    expansions=[dict(line=e['line'],units=e['extra_units']+1,original=lines[e['line']-1],reason=e['reason']) for e in unit['expansions']]))
            build=json.loads((HERE/'build-v2/report.json').read_text())
            row=dict(key=key,id=identity,receipt_key=identity,benchmark=b,language=language,variant='v1',
                loc=bundle['canonical_loc'],canonical_loc=bundle['canonical_loc'],physical_loc=bundle['physical_loc'],
                loc_metric='statement-normalized',files=files,file_roles=roles,
                seconds=timing['median_seconds'],samples=timing['samples_seconds'],timing_sd=timing['sample_sd_seconds'],native_observations=3,
                source_alias_of=None,timing_alias_of=None,distinct_optimization_claimed=False,
                command=rows[0]['command'],cwd=str(ROOT),binary_sha256=report['binaries'][b],
                build_command=results['rebuild_commands'],
                runtime_environment={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','TZ':'UTC'},
                execution_mode=meta['execution'][0],sample_execution_metadata=rows,
                source_work_qualified=True,canonical_loc_qualified=True,full_workload_qualified=True,
                required_work_validated=True,eligible_for_chart=True,exclusion_reason=None,
                formatted_loc=None,formatted_x=None,formatted_loc_qualified=False,formatted_loc_complete=False,
                formatted_loc_status='unavailable',formatted_loc_evidence=None,
                chart_admission=dict(historical_reports_unchanged=True,**refs),
                report=refs['results']['path'],report_sha256=refs['results']['sha256'],
                loc_report=refs['source_counts']['path'],source_report=refs['origin']['path'],loc_expansions=expansions,
                runtime_policy=meta['runtime_policy'],memory_policy=meta['memory_policy'],runtime_support=meta['note'],
                runtime_evidence=meta,runtime_evidence_scope=meta['evidence_scope'],
                timing_boundary=report['timing_boundary'],
                timing_summary='Median of three fresh complete-process samples, including source compilation, optional native JIT, input, complete work/output and shutdown. Other language timings are preserved historical cohorts; no fresh Mech controls.',
                source_provenance='AI adaptation of the specifically cited Lua submission and declared consulted local references. All authored C++ host and library bindings count with Luau source; no benchmark algorithm is implemented by the native helpers. Exact AI serving model ID is unavailable; no Sol/Astra model is inferred.',
                source_provenance_record=dict(canonical_source_evidence=refs['source_counts'],required_work_evidence=refs['required_work'],origin_evidence=refs['origin']),
                source_url=data['repository']['url']+'/blob/'+revision+'/experiments/luau/source-v1/'+b+'.luau',
                upstream_source_url=provenance['source_origins'][b]['original_sources'][0]['url'],
                source_link_label='Exact retained Luau source',retained_source_revision=revision,local_adaptation=True,
                full_output_validation=dict(all_three_samples_passed=True,expected='Complete reference output; N-body energy tolerance 1e-8',evidence=refs['full_report']),
                x=bundle['canonical_loc']/bench['baseline_loc'],y=timing['median_seconds']/bench['baseline_seconds'])
            row['measured_backend']=dict(key=language,execution=meta['execution'][0],label=meta['runtime'],verified=True,
                evidence=dict(verified=True,report=refs['full_report']['path'],report_sha256=refs['full_report']['sha256'],
                    command=row['command'],source_sha256=files,runtime_receipt=dict(verified=True,report=refs['full_report']['path'],
                    report_sha256=refs['full_report']['sha256'],field='/toolchain/version',value='0.743',value_encoding='literal-saved-string')))
            row['publication_record']=copy.deepcopy(row)
            data['programs'][key]=data['program_inventory'][key]=row
            bench['groups'].append(dict(language=language,label=meta['label'],fast=key,small=key,formatted_fast=None,formatted_small=None,programs=[key]))
            origin=provenance['source_origins'][b]
            parent=origin['predecessor_program'];assert parent in catalog and origin['predecessor_sha256'] in catalog[parent]['files']
            predecessors=[dict(program_key=parent,source_sha256=catalog[parent]['files'])]
            for reference in origin.get('consulted_local_references',[]):
                parent=reference['program_key'];assert parent in catalog and reference['sha256'] in catalog[parent]['files']
                assert digest((ROOT/reference['path']).read_bytes())==reference['sha256']
                predecessors.append(dict(program_key=parent,source_sha256=catalog[parent]['files']))
            lineage['programs'][key]=dict(source_sha256=files,evidence=refs['origin'],
                predecessors=predecessors,
                external_sources=[dict(url=r['url'],relationship='reference implementation',declared_in_source=refs['origin'],source_marker=r['url']) for r in origin['original_sources']])
            appended.append(key);language_programs.append(row)
        benches=[b['key'] for b in data['benchmarks']]
        language_row=dict(key=language,label=meta['label'],family='luau',color='#00a2ff' if mode=='jit' else '#2376b9',
            timed_benchmarks=benches,source_benchmarks=benches,formatted_timed_benchmarks=[],formatted_source_benchmarks=[],
            runtime_family=meta['platform'],runtime=meta['runtime'],execution_modes=meta['execution'],typing='gradual',
            execution='JIT' if mode=='jit' else 'Interpreted',line_style='solid',runtime_policy=meta['runtime_policy'],
            paradigms=meta['style'],memory_models=meta['memory'],classification_note=meta['note'],
            coverage_note='10/10 full workloads; three complete-process samples each; all authored embedding helpers count.')
        language_row.update({k:meta[k] for k in ('release_year','release_name','release_source','release_note')})
        data['languages'].append(language_row)
        module[language]={k:meta[k] for k in META_FIELDS}
        languages['languages'][language]=dict(meta,displayed_program_count=10,measurement_basis=[refs['results']])
        aggregate={axis:statistics.geometric_mean(p[axis] for p in language_programs) for axis in ('x','y')}
        data['reference_summary'].append(dict(lang=language,label=meta['label'],fast=aggregate,small=aggregate,measured_benchmarks=benches))
        for group in data['language_groups']:
            if group['key'] in (meta['execution'][0],'functional'):group['languages'].append(language)
        data['protocol'][language]=row['timing_summary']+' '+meta['runtime_policy']
    languages['scope']=f'{len(data["languages"])} measured variants; all classifications explicit.'
    for section in ('programs','program_inventory','files','archive_paths'):
        assert all(data[section][k]==v for k,v in before[section].items()),section
    for old,new in zip(before['benchmarks'],data['benchmarks']):
        assert dict(new,groups=[g for g in new['groups'] if g['language'] not in ('luau','luau-jit')])==old
    for section in ('languages','reference_summary','formatted_reference_summary'):
        assert data[section][:len(before[section])]==before[section]
    allowed={'programs','program_inventory','files','archive_paths','benchmarks','languages','reference_summary','language_groups','protocol'}
    assert all(data[k]==v for k,v in before.items() if k not in allowed)
    assert set(module)==set(languages['languages'])=={l['key'] for l in data['languages']}
    encoded={TARGETS[0]:(json.dumps(data,indent=2,allow_nan=False)+'\n').encode(),
        TARGETS[1]:(json.dumps(languages,indent=2,allow_nan=False)+'\n').encode(),
        TARGETS[2]:(match[1]+json.dumps(module,indent=2,allow_nan=False)+match[3]).encode(),
        TARGETS[3]:(json.dumps(lineage,indent=2,allow_nan=False)+'\n').encode()}
    receipt=dict(schema='luau-catalog-import.v1',status='PREPARED',evidence=refs,appended_programs=appended,
        full_samples=60,matched_controls=0,historical_data_preserved=True,baseline_changed=False,benchmark_executions=0,
        before={p:digest(b) for p,b in originals.items()},after={p:digest(b) for p,b in encoded.items()})
    return encoded,receipt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    results=json.loads((HERE/'results-v1.json').read_text())
    counts=json.loads((HERE/'source-counts-v1/qualified-v1/qualified-counts.json').read_text())
    metadata=json.loads((HERE/'runtime-metadata-v1.json').read_text())
    report=json.loads((HERE/'full-v1/report.json').read_text())
    origins=json.loads((HERE/'source-provenance-v1.json').read_text())
    provenance=dict(sources=origins['measured_source_sha256'],source_origins=origins['sources'])
    provenance['sources']={'experiments/luau/source-v1/'+k:v for k,v in provenance['sources'].items()}
    originals={p:(ROOT/p).read_bytes() for p in TARGETS}
    encoded,receipt=transform(originals,results,counts,metadata,report,provenance)
    backup=HERE/'.build/catalog-before-v1';backup.mkdir(parents=True,exist_ok=False)
    for relative,raw in originals.items():
        p=backup/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    if args.apply:
        for relative,raw in encoded.items():(ROOT/relative).write_bytes(raw)
        receipt['status']='APPLIED'
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
