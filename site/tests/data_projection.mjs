// Run against the canonical catalog and the emitted browser view. This replays
// browser calculations only; it never launches a benchmark or modifies data.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {comparison,comparisonMetrics,chartDomain,globalStatistics,medianRankings,
  recordedSamplePoints,sampleDensityPoints,languageRelativeComparisons,languageFamilies,
  languagesByYear} from '../src/math.mjs';
import {axisData,inspectorProgram} from '../src/formatted_axis.mjs';
import {languageTraits} from '../src/traits.mjs';

// Use the actual source/audit rendering functions without starting the page or
// constructing a DOM. These functions close over only data and HTML escaping.
const app=fs.readFileSync(new URL('../src/app.mjs',import.meta.url),'utf8');
const rendering=app.slice(app.indexOf('function programSource('),app.indexOf('function renderInspector('));
assert.ok(rendering.includes('function renderLocAudit('));
const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inspectors=new Function('data','esc',rendering+'\nreturn {source:programSource,audit:renderLocAudit};');

if(process.argv.length!==4)throw new Error('Usage: node site/tests/data_projection.mjs canonical.json browser.json');
const original=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const projected=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const oldInspector=inspectors(original,esc),newInspector=inspectors(projected,esc);
for(const field of ['schema','schema_version','languages','benchmarks','files','repository','archive_paths','protocol','reference_summary']){
  assert.equal(Object.hasOwn(projected,field),Object.hasOwn(original,field),field);
  assert.deepEqual(projected[field],original[field],field);
}
const displayedFields=['key','id','benchmark','language','loc','physical_loc','x','y','seconds','samples',
  'timing_sd','timing_summary','sample_details','files','report','report_sha256','source_report','loc_report',
  'binary_sha256','runtime_arguments','command','execution_mode','measured_backend','formatted_loc','formatted_loc_status',
  'formatted_loc_complete','formatted_x','eligible_for_chart','exclusion_reason','loc_expansion_format',
  'source_url','source_link_label','license_url','local_adaptation','source_provenance','runtime_policy','runtime_support'];
const fileFields=['name','path','code','sha256','role','physical_loc','normalized_loc','loc_note','source_url'];
let rowCount=0,sampleCount=0,auditCases=0,sourceCases=0;
for(const pool of ['programs','program_inventory']){
  assert.equal(Object.hasOwn(projected,pool),Object.hasOwn(original,pool),pool);
  assert.deepEqual(Object.keys(projected[pool]??{}),Object.keys(original[pool]??{}),`${pool} order`);
  for(const [key,row] of Object.entries(original[pool]??{})){
    const browserRow=projected[pool][key];
    for(const field of displayedFields){
      assert.equal(Object.hasOwn(browserRow,field),Object.hasOwn(row,field),`${key}/${field} presence`);
      assert.deepEqual(browserRow[field],row[field],`${key}/${field}`);
    }
    assert.deepEqual(browserRow.formatted_loc_evidence?.reasons,row.formatted_loc_evidence?.reasons);
    assert.deepEqual(browserRow.algorithm?.reason,row.algorithm?.reason);
    assert.equal(newInspector.audit(browserRow),oldInspector.audit(row),`${key}: rendered LOC audit HTML`);
    auditCases++;
    for(const file of row.files){
      const before=oldInspector.source(row,file),after=newInspector.source(browserRow,file);
      for(const field of fileFields)assert.deepEqual(after[field],before[field],`${key}/${file}/${field}`);
      sourceCases++;
    }
    assert.ok(!Object.hasOwn(browserRow,'publication_record'));
    assert.ok(!Object.hasOwn(browserRow,'sample_execution_metadata'));
    rowCount++;sampleCount+=(row.samples??[]).length;
  }
}
const catalog=data=>({...data.program_inventory,...data.programs});
assert.deepEqual(Object.keys(catalog(projected)),Object.keys(catalog(original)),'Source browsing/navigation order');
assert.deepEqual(languageFamilies(projected.languages),languageFamilies(original.languages));
assert.deepEqual(languageTraits(projected),languageTraits(original));
for(const year of new Set(original.languages.map(row=>row.release_year)))
  assert.deepEqual(languagesByYear(projected.languages,{to:year}),languagesByYear(original.languages,{to:year}));

const modelView=model=>({benchmarks:model.benchmarks.map(b=>b.key),entries:model.entries.map(entry=>({
  language:entry.language,fast:entry.fast,small:entry.small,spread:entry.spread,spread2:entry.spread2,
  coverage:{...entry.coverage,missing:entry.coverage.missing.map(b=>b.key)},
  inputs:entry.inputs.map(input=>({benchmark:input.benchmark.key,fast:input.fast.key,small:input.small.key,
    programs:input.programs.map(program=>program.key)}))}))});
const sampleView=samples=>samples.map(s=>({program:s.program.key,language:s.entry.language.key,
  benchmark:s.benchmark.key,run:s.run,elapsed:s.elapsed,x:s.x,y:s.y}));
const rankInputs=entries=>entries.map(({language,fast,small})=>({language,fast,small}));
const all=original.benchmarks.map(b=>b.key),languages=new Set(original.languages.map(l=>l.key));
const scopes=[all,...all.map(key=>[key]),all.filter((_,index)=>index%2===0)];
const disabled=[new Set(),new Set(Object.keys(original.programs).filter((_,index)=>index%3===0))];
let modelCases=0,relativeCases=0,inspectorCases=0;
for(const metric of ['canonical','formatted']){
  const left=axisData(original,metric),right=axisData(projected,metric);
  for(const scope of scopes)for(const hidden of disabled){
    const selection={benchmarks:new Set(scope),languages,disabled:hidden};
    const before=comparison(left,selection),after=comparison(right,selection);
    assert.deepEqual(modelView(after),modelView(before),`${metric}/${scope}: endpoints/means/covariance`);
    assert.deepEqual(after.entries.map(comparisonMetrics),before.entries.map(comparisonMetrics));
    assert.deepEqual(globalStatistics(after.entries),globalStatistics(before.entries));
    const oldSamples=recordedSamplePoints(before.entries,{disabled:hidden});
    const newSamples=recordedSamplePoints(after.entries,{disabled:hidden});
    assert.deepEqual(sampleView(newSamples),sampleView(oldSamples),'Every recorded plotted sample');
    assert.deepEqual(sampleDensityPoints(newSamples),sampleDensityPoints(oldSamples),'Density inputs');
    assert.deepEqual(medianRankings(rankInputs(after.entries)),medianRankings(rankInputs(before.entries)));
    for(const language of original.languages){
      assert.deepEqual(medianRankings(rankInputs(after.entries),{referenceLanguage:language.key}),
        medianRankings(rankInputs(before.entries),{referenceLanguage:language.key}),'Hero ranking origin');
    }
    modelCases++;
  }
  for(const scope of scopes){
    const benchmarks=new Set(scope);
    for(const target of original.languages){
      assert.deepEqual(languageRelativeComparisons(projected,target.key,{benchmarks,locData:right}),
        languageRelativeComparisons(original,target.key,{benchmarks,locData:left}),`${target.key}: same-workload ratios`);
      relativeCases++;
    }
    for(const focusMeans of [false,true])
      assert.deepEqual(chartDomain(right,{benchmarks,focusMeans}),chartDomain(left,{benchmarks,focusMeans}),'Fixed axes');
  }
  for(const benchmark of original.benchmarks)for(const group of benchmark.groups)
    for(const kind of ['fast','small'])for(const hidden of disabled){
      const detail={benchmark:benchmark.key,language:group.language,kind};
      assert.equal(inspectorProgram(projected,right,detail,hidden)?.key,
        inspectorProgram(original,left,detail,hidden)?.key,'Inspector endpoint/fallback');
      inspectorCases++;
    }
}
console.log(JSON.stringify({status:'browser-projection-parity-passed',ordered_pool_rows:rowCount,
  unique_programs:Object.keys(catalog(original)).length,recorded_pool_samples:sampleCount,
  source_files:Object.keys(original.files).length,model_cases:modelCases,
  relative_comparisons:relativeCases,inspector_cases:inspectorCases,rendered_loc_audits:auditCases,
  source_and_link_cases:sourceCases,source_bytes_samples_and_displayed_metadata_identical:true}));
