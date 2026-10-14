// Pure synthetic admission tests. No browser, benchmark or saved timing replay.
import assert from 'node:assert/strict';
import {eligibleForChart,comparison,sharedBenchmarks,recordedSamplePoints,sampleDensityPoints,chartDomain} from '../src/math.mjs';
import {axisData,projectProgram,inspectorProgram} from '../src/formatted_axis.mjs';

const subject={key:'b:subject',id:'subject',language:'test',benchmark:'b',loc:2,x:2,y:3,
  seconds:3,samples:[2,3,4],formatted_loc:4,formatted_loc_status:'qualified',
  formatted_loc_complete:true,formatted_x:4};
const excluded={...subject,key:'b:excluded',id:'excluded',eligible_for_chart:false,
  loc:100000,x:100000,y:100000,seconds:100000,samples:[90000,100000,110000],formatted_loc:200000,formatted_x:200000};
const benchmark={key:'b',baseline_loc:1,baseline_formatted_loc:1,baseline_seconds:1,
  groups:[{language:'test',programs:[subject.key,excluded.key],fast:excluded.key,small:excluded.key,
    formatted_fast:excluded.key,formatted_small:excluded.key}]};
const data={languages:[{key:'test'}],benchmarks:[benchmark],programs:{[subject.key]:subject,[excluded.key]:excluded}};
const selection={languages:new Set(['test']),benchmarks:new Set(['b']),disabled:new Set()};
const withoutExcluded={...data,programs:{[subject.key]:subject},benchmarks:[{...benchmark,
  groups:[{...benchmark.groups[0],programs:[subject.key]}]}]};
const before=JSON.stringify(data);
assert.equal(eligibleForChart(subject),true,'legacy rows remain eligible');
assert.equal(eligibleForChart({...subject,eligible_for_chart:true}),true);
assert.equal(eligibleForChart(excluded),false);
for(const metric of ['canonical','formatted']){
  const projected=axisData(data,metric),entries=comparison(projected,selection).entries;
  assert.deepEqual(entries[0].inputs[0].programs.map(p=>p.key),[subject.key]);
  assert.equal(entries[0].inputs[0].fast.key,subject.key);
  assert.equal(entries[0].inputs[0].small.key,subject.key);
  assert.equal(sharedBenchmarks(projected,selection).length,1);
  const forced=recordedSamplePoints(entries,{programsForInput:()=>Object.values(projected.programs)});
  assert.equal(forced.length,3,'inventory/custom sample callbacks cannot bypass exclusion');
  assert.ok(forced.every(point=>point.program.key===subject.key));
  assert.deepEqual(chartDomain(projected,{benchmarks:selection.benchmarks,focusMeans:false}),
    chartDomain(axisData(withoutExcluded,metric),{benchmarks:selection.benchmarks,focusMeans:false}),
    'excluded outliers cannot change chart bounds');
  assert.equal(inspectorProgram(data,projected,{benchmark:'b',language:'test',kind:'fast'},new Set()).key,subject.key);
}
assert.deepEqual(sampleDensityPoints([{program:excluded,run:1,x:excluded.x,y:excluded.y,entry:{language:{key:'test'}}}]),[]);
const onlyExcluded={...data,programs:{[excluded.key]:excluded},benchmarks:[{...benchmark,
  groups:[{...benchmark.groups[0],programs:[excluded.key]}]}]};
assert.equal(comparison(onlyExcluded,selection).entries.length,0);
assert.equal(sharedBenchmarks(onlyExcluded,selection).length,0);
assert.equal(projectProgram(excluded,'formatted').formatted_loc,200000,'count evidence remains inspectable');
assert.equal(inspectorProgram(data,data,{program:excluded.key},new Set()).key,excluded.key,'explicit source inspection remains available');
assert.equal(JSON.stringify(data),before,'gating never mutates saved observations');
console.log('Passed explicit publication eligibility across canonical/formatted endpoints, samples, density, bounds and source inspection.');
