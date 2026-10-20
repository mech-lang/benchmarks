// Synthetic source-size projection tests. No browser, native parser or timings.
import assert from 'node:assert/strict';
import {axisData,projectProgram,sourceMetricValue,sourceMetricKeys,inspectorProgram} from '../src/formatted_axis.mjs';
import {comparison,chartDomain,recordedSamplePoints,sampleDensityPoints,medianRankings,languageRelativeComparisons} from '../src/math.mjs';

const scope=(utf8_bytes,gzip_bytes,cl100k_base_tokens)=>({utf8_bytes,gzip_bytes,cl100k_base_tokens});
const row=(key,language,loc,seconds,size,more={})=>({key,id:key,benchmark:'b',language,loc,x:loc/2,y:seconds/2,seconds,
  samples:seconds===null?[]:[seconds*.9,seconds,seconds*1.1],files:['source'],
  formatted_loc:loc+1,formatted_loc_status:'qualified',formatted_loc_complete:true,formatted_x:(loc+1)/3,
  source_metrics:{application:size,submitted:scope(999,999,999),excluded_support:scope(0,0,0)},...more});
const a=row('b:a','a',2,4,scope(120,80,30)),b=row('b:b','a',6,2,scope(100,70,50));
const inventory=row('b:inventory','a',20,3,scope(60,90,25));
const other=row('b:other','b',4,8,scope(150,40,20));
const alias=row('b:alias','a',20,3,scope(60,90,25),{timing_alias_of:inventory.key});
const excluded=row('b:excluded','a',1,1,scope(1,1,1),{eligible_for_chart:false});
const pending=row('b:pending','a',1,null,scope(1,1,1),{y:null});
const missing=row('b:missing','c',1,1,scope(null,null,null));
const zero=row('b:zero','c',1,1,scope(0,0,0));
const data={languages:[{key:'a'},{key:'b'},{key:'c'}],
  programs:Object.fromEntries([a,b,other].map(p=>[p.key,p])),
  program_inventory:Object.fromEntries([inventory,alias,excluded,pending,missing,zero].map(p=>[p.key,p])),
  benchmarks:[{key:'b',baseline_loc:2,baseline_formatted_loc:3,baseline_seconds:2,groups:[
    {language:'a',programs:[a.key,b.key],fast:b.key,small:a.key,formatted_fast:b.key,formatted_small:a.key},
    {language:'b',programs:[other.key],fast:other.key,small:other.key,formatted_fast:other.key,formatted_small:other.key}]}]};
const before=JSON.stringify(data),selection={benchmarks:new Set(['b']),languages:new Set(['a','b','c']),disabled:new Set()};
assert.deepEqual(sourceMetricKeys,['canonical','formatted','bytes','gzip','bpe']);
assert.equal(axisData(data,'canonical'),data);
assert.equal(axisData(data,'formatted').programs[a.key].loc,3);
assert.equal(axisData(data,'formatted').benchmarks[0].baseline_loc,3);
assert.deepEqual(axisData(data,'formatted').benchmarks[0].groups[0].programs,[a.key,b.key],'formatted pool unchanged');
const expected={bytes:{baseline:60,small:inventory.key,other:150/60},gzip:{baseline:40,small:b.key,other:1},bpe:{baseline:20,small:inventory.key,other:1}};
for(const [metric,want] of Object.entries(expected)){
  const projected=axisData(data,metric),model=comparison(projected,selection),entry=model.entries.find(e=>e.language.key==='a');
  assert.equal(projected,axisData(data,metric),'metric projection cached');
  assert.equal(projected.benchmarks[0].baseline_loc,want.baseline);
  assert.equal(entry.inputs[0].small.key,want.small,'smallest is reselected from all admitted candidates');
  assert.equal(entry.inputs[0].fast.key,b.key);
  assert.equal(projected.programs[other.key].x,want.other);
  assert.equal(inspectorProgram(data,projected,{benchmark:'b',language:'a',kind:'small'},new Set()).key,want.small);
  for(const p of [excluded,pending,missing,zero]){
    assert.equal(projected.programs[p.key].x,null,'unavailable/unmeasured/excluded coordinates absent');
    assert.ok(!model.entries.some(e=>e.inputs.some(i=>i.programs.some(r=>r.key===p.key))));
  }
  for(const p of Object.values(projected.programs)){
    const original=data.programs[p.key]??data.program_inventory[p.key];
    for(const field of ['seconds','samples','y','files','timing_alias_of','source_metrics'])assert.deepEqual(p[field],original[field]);
  }
  const points=recordedSamplePoints(model.entries),density=sampleDensityPoints(points);
  assert.equal(points.filter(p=>p.observation_source===inventory.key).length,3,'timing alias never creates independent runs');
  assert.equal(density.filter(p=>p.program===inventory.key).length,3);
  assert.ok(points.every(p=>p.y===p.elapsed/2));
  assert.ok(medianRankings(model.entries).loc.entries.every(r=>Number.isFinite(r.value)));
  const relative=languageRelativeComparisons(data,'a',{locData:projected}).find(r=>r.language.key==='b');
  assert.equal(relative.loc.ratio,sourceMetricValue(other,metric)/sourceMetricValue(data.programs[want.small]??data.program_inventory[want.small],metric));
  const domain=chartDomain(projected,{benchmarks:selection.benchmarks,focusMeans:false});
  assert.ok(Object.values(domain).every(Number.isFinite));
  const disabled=comparison(projected,{...selection,disabled:new Set([inventory.key,alias.key])}).entries.find(e=>e.language.key==='a');
  assert.equal(disabled.inputs[0].small.key,metric==='bpe'?a.key:b.key);
  assert.equal(projected.benchmarks[0].baseline_loc,want.baseline,'visibility does not renormalize');
  const locked={...data,benchmarks:[{...data.benchmarks[0],groups:[{...data.benchmarks[0].groups[0],programs:[a.key],source_metric_locked:true}]}]};
  const lockedAxis=axisData(locked,metric),lockedEntry=comparison(lockedAxis,selection).entries.find(e=>e.language.key==='a');
  assert.deepEqual(lockedEntry.inputs[0].programs.map(p=>p.key),[a.key],'explicit comparison source stays selected');
  assert.equal(lockedAxis.benchmarks[0].baseline_loc,want.baseline,'source locking does not renormalize');
}
const incomplete={...data,programs:{...data.programs,[b.key]:{...b,source_metrics:{application:scope(100,70,null)}}}};
const incompleteAxis=axisData(incomplete,'bpe');
const bpe=comparison(incompleteAxis,selection).entries.find(e=>e.language.key==='a');
assert.equal(bpe.inputs[0].fast.key,inventory.key,'missing BPE cannot borrow bytes or retain an invalid fastest endpoint');
assert.equal(languageRelativeComparisons(incompleteAxis,'a',{locData:incompleteAxis}).find(r=>r.language.key==='b').time.ratio,other.seconds/inventory.seconds,'Raw-axis hero time ratios use the chart candidate pool.');
assert.equal(projectProgram(a,'bytes').x,null,'standalone projection requires a baseline');
assert.equal(sourceMetricValue(missing,'bpe'),null);assert.equal(sourceMetricValue(zero,'bytes'),null);
assert.equal(JSON.stringify(data),before,'all original counts/source/timing records remain immutable');
console.log('Source axes: own minima, inventory endpoints, missing counts, exclusions, aliases, locking, rankings and immutable timing evidence PASS');
