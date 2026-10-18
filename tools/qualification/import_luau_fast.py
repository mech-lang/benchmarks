"""Retain guarded-error candidates and select Luau speed/size endpoints."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

from import_luau import ROOT,HERE,pin,digest


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    catalog_path=ROOT/'data/benchmarks.json';raw=catalog_path.read_bytes();data=json.loads(raw);before=copy.deepcopy(data)
    lineage_path=ROOT/'data/source-predecessor-evidence.json';lineage_raw=lineage_path.read_bytes();lineage=json.loads(lineage_raw)
    languages_path=ROOT/'data/languages.json';languages_raw=languages_path.read_bytes();languages=json.loads(languages_raw)
    results=json.loads((HERE/'results-guarded-revcomp-v1.json').read_text())
    report=json.loads((HERE/'full-guarded-revcomp-v1/report.json').read_text())
    counts=json.loads((HERE/'bounded-guarded-revcomp-v1/qualified-counts.json').read_text())
    assert results['status']=='SIX_FULL_SIZE_SAMPLES_RECONCILED' and results['benchmark_samples']==6
    assert report['status']=='PASSED' and report['active'] is None and len(report['cases'])==6
    assert counts['status']=='QUALIFIED_FOR_RETAINED_SOURCE_BUNDLES'
    refs={name:pin(HERE/relative) for name,relative in {
        'results':'results-guarded-revcomp-v1.json','full_report':'full-guarded-revcomp-v1/report.json',
        'source_counts':'bounded-guarded-revcomp-v1/qualified-counts.json','origin':'revcomp-candidate-v1.json'}.items()}
    for ref in refs.values():data['archive_paths'][ref['path']]=ref['path']
    source=HERE/'source-fast-v1/revcomp.luau';source_raw=source.read_bytes();source_hash=digest(source_raw)
    source_relative=source.relative_to(ROOT).as_posix();revision=report['source_commit']
    assert subprocess.check_output(['git','show',revision+':'+source_relative],cwd=ROOT)==source_raw
    assert source_hash==counts['units']['revcomp.luau']['sha256']
    data['files'][source_hash]=dict(sha256=source_hash,name='revcomp.luau',code=source_raw.decode(),path=source_relative,archive_path=source_relative)
    data['archive_paths'][source_relative]=source_relative
    bench=next(b for b in data['benchmarks'] if b['key']=='revcomp')
    appended=[];comparison={}
    for language,mode in [('luau','vm'),('luau-jit','jit')]:
        parent_key=f'revcomp:{language}-revcomp-v1';parent=data['programs'][parent_key]
        rows=[r for r in report['cases'] if r['execution_mode']==mode]
        assert len(rows)==3 and all(r['valid'] and r['exit_code']==0 and not r['timed_out'] for r in rows)
        samples=[r['elapsed_seconds'] for r in rows];summary=results['results'][language]
        assert summary['samples_seconds']==samples and summary['median_seconds']==statistics.median(samples)
        assert summary['median_seconds']>=bench['baseline_seconds'] and counts['canonical_loc']>=bench['baseline_loc']
        row=copy.deepcopy(parent);row.pop('publication_record',None);row.pop('authorship',None)
        identity=f'{language}-revcomp-guarded-v1';key='revcomp:'+identity
        assert key not in data['programs'] and key not in data['program_inventory']
        files=[source_hash,counts['units']['Host.cpp']['sha256']]
        roles={}
        expansions=[]
        for name,unit in counts['units'].items():
            unit_path=ROOT/unit['path'];assert digest(unit_path.read_bytes())==unit['sha256']
            roles[unit['sha256']]=dict(role='application' if name.endswith('.luau') else 'application-helper',
                source_path=unit['path'],normalized_loc=unit['canonical_loc'],physical_loc=unit['physical_loc'],canonical_projection=refs['source_counts'])
            lines=unit_path.read_text().splitlines()
            expansions.append(dict(source=unit['path'],name=name,sha256=unit['sha256'],source_language=unit['source_language'],
                physical_loc=unit['physical_loc'],normalized_loc=unit['canonical_loc'],
                expansions=[dict(line=e['line'],units=e['extra_units']+1,original=lines[e['line']-1],reason=e['reason']) for e in unit['expansions']]))
        row.update(key=key,id=identity,receipt_key=identity,variant='guarded-v1',
            loc=counts['canonical_loc'],canonical_loc=counts['canonical_loc'],physical_loc=counts['physical_loc'],files=files,file_roles=roles,loc_expansions=expansions,
            seconds=summary['median_seconds'],samples=samples,timing_sd=summary['sample_sd_seconds'],command=rows[0]['command'],sample_execution_metadata=rows,
            report=refs['results']['path'],report_sha256=refs['results']['sha256'],loc_report=refs['source_counts']['path'],
            source_report=refs['origin']['path'],source_url=data['repository']['url']+'/blob/'+revision+'/'+source_relative,
            retained_source_revision=revision,x=counts['canonical_loc']/bench['baseline_loc'],y=summary['median_seconds']/bench['baseline_seconds'],
            distinct_optimization_claimed=True,source_provenance='Guarded-error adaptation of the retained Luau reverse-complement program: construct the invalid-byte message only on failure. Two additional normalized source units; original program and all its observations are preserved.')
        row['chart_admission']=dict(row['chart_admission'],**refs)
        row['source_provenance_record']=dict(canonical_source_evidence=refs['source_counts'],origin_evidence=refs['origin'],original_program_key=parent_key,
            required_work_evidence=parent['source_provenance_record']['required_work_evidence'])
        row['full_output_validation']=dict(all_three_samples_passed=True,expected='Complete reference output, exact bytes and SHA-256',evidence=refs['full_report'])
        backend=row['measured_backend']['evidence'];backend.update(report=refs['full_report']['path'],report_sha256=refs['full_report']['sha256'],command=row['command'],source_sha256=files)
        # Version/build proof still identifies the exact same runtime executable.
        backend['runtime_receipt']=copy.deepcopy(parent['measured_backend']['evidence']['runtime_receipt'])
        assert row['binary_sha256']==report['binary_sha256']
        row['publication_record']=copy.deepcopy(row)
        data['programs'][key]=data['program_inventory'][key]=row
        group=next(g for g in bench['groups'] if g['language']==language);group['programs'].append(key)
        group['fast']=min(group['programs'],key=lambda k:(data['programs'][k]['seconds'],data['programs'][k]['loc']))
        group['small']=min(group['programs'],key=lambda k:(data['programs'][k]['loc'],data['programs'][k]['seconds']))
        language_row=next(l for l in data['languages'] if l['key']==language)
        language_row['coverage_note']='10/10 full workloads; eleven measured candidates, each with three complete-process samples; all authored helpers count.'
        languages['languages'][language]['displayed_program_count']=11
        entry=next(r for r in data['reference_summary'] if r['lang']==language)
        for endpoint in ('fast','small'):
            programs=[data['programs'][next(g for g in b['groups'] if g['language']==language)[endpoint]] for b in data['benchmarks']]
            entry[endpoint]={axis:statistics.geometric_mean(p[axis] for p in programs) for axis in ('x','y')}
        lineage['programs'][key]=dict(source_sha256=files,evidence=refs['origin'],predecessors=[dict(program_key=parent_key,source_sha256=parent['files'])])
        comparison[language]=dict(baseline_seconds=parent['seconds'],guarded_seconds=row['seconds'],speedup=parent['seconds']/row['seconds'],baseline_loc=parent['loc'],guarded_loc=row['loc'])
        appended.append(key)
    for section in ('programs','program_inventory','files'):
        assert all(data[section][k]==v for k,v in before[section].items()),section
    for old,new in zip(before['benchmarks'],data['benchmarks']):
        if old['key']!='revcomp':assert old==new
        else:assert dict(new,groups=[g for g in new['groups'] if g['language'] not in ('luau','luau-jit')])==dict(old,groups=[g for g in old['groups'] if g['language'] not in ('luau','luau-jit')])
    encoded=(json.dumps(data,indent=2,allow_nan=False)+'\n').encode();encoded_lineage=(json.dumps(lineage,indent=2)+'\n').encode()
    receipt=dict(schema='luau-guarded-revcomp-admission.v1',status='PREPARED',appended_programs=appended,benchmark_samples=6,
        baseline_measurements_preserved=True,historical_data_preserved=True,baseline_changed=False,comparison=comparison,evidence=refs,
        before={'data/benchmarks.json':digest(raw),'data/source-predecessor-evidence.json':digest(lineage_raw),'data/languages.json':digest(languages_raw)},
        after={'data/benchmarks.json':digest(encoded),'data/source-predecessor-evidence.json':digest(encoded_lineage),
               'data/languages.json':digest((json.dumps(languages,indent=2)+'\n').encode())})
    if args.apply:
        catalog_path.write_bytes(encoded);lineage_path.write_bytes(encoded_lineage)
        languages_path.write_text(json.dumps(languages,indent=2)+'\n');receipt['status']='APPLIED'
        assert digest(catalog_path.read_bytes())==receipt['after']['data/benchmarks.json']
        assert all(digest((ROOT/unit['path']).read_bytes())==unit['sha256'] for unit in counts['units'].values()),'Source changed during catalog write'
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
