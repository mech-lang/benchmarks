import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/campaigns-model.mjs';
import * as grouping from '../src/metrics-model.mjs';
import {validateNative} from '../src/metrics-data.mjs';
const native=validateNative(JSON.parse(fs.readFileSync(new URL('../src/deflate-m3-results-20261118.json',import.meta.url))));
const base={case_id:'scalar',backend:'source',lane:'candidate',outcome:'ok',progress:'measured',control_contract:'shared',task_hash:'t',measurement_hash:'m',environment_hash:'e',source_sha256:'s',revision:'r',measurement:{primary_metric:'resident_turn_seconds'},summary:{resident_turn_seconds:{median:1.0489},source_to_artifact_seconds:{median:.03},execution_allocations:{median:0},artifact_bytes:{median:256}}};
const reference={...base,backend:'rust',lane:'control',title:'Rust task control',summary:{resident_turn_seconds:{median:1},execution_allocations:{median:5}}};
const build={...base,case_id:'native-build',backend:'native',measurement:{primary_metric:'source_to_executable_seconds'},summary:{source_to_executable_seconds:{median:2},native_process_seconds:{median:.5},executable_bytes:{median:900}}};
const buildReference={...build,backend:'rust',lane:'control',summary:{source_to_executable_seconds:{median:1},native_process_seconds:{median:1},executable_bytes:{median:1000}}};
const bundle={schema:'mech.benchmark-dashboard.v2',catalog:{cases:[{id:'scalar',title:'Scalar <safe>',family:'arithmetic',backends:['source']},{id:'native-build',title:'Native build',family:'compilation',backends:['native']}]},campaigns:[{id:'run',started_at:'2026-11-17',results:[base,reference,build,buildReference]}]};
const all=[...grouping.suiteMeasurements(bundle),...grouping.nativeMeasurements(native)];
assert.equal(new Set(all.map(row=>row.key)).size,all.length);
assert.ok(all.filter(row=>row.group==='deflate').every(row=>row.metric==='native_compression_call_seconds'),'native timings retain a distinct measurement label from historical checked calls');
for(const group of ['runtime','compiler','applications','memory'])assert.ok(all.filter(row=>row.group===group).every(row=>row.control.kind!=='libdeflate'));
assert.equal(grouping.suiteMeasurements(bundle,{group:'compiler'}).length,2);
assert.equal(grouping.suiteMeasurements(bundle,{group:'compiler'}).filter(row=>row.control.kind==='rust').length,1);
assert.equal(grouping.countsFor(all.filter(row=>row.group==='deflate')).faster,61);
assert.equal(grouping.countsFor(grouping.nativeMeasurements(native,'reverse').filter(row=>row.group==='deflate')).faster,61);
assert.equal(model.comparisonLabel({ratio:1.0489},'resident_turn_seconds'),'1.049× time');
assert.equal(model.comparisonLabel({ratio:1.000001},'resident_turn_seconds'),'1.000001× time');
assert.equal(model.comparisonLabel({ratio:0},'execution_allocations'),'0× count');
assert.equal(model.comparisonLabel({ratio:Infinity},'execution_allocations'),'∞× count');
assert.equal(model.comparisonDirection({ratio:0},'execution_allocations'),'faster');
assert.equal(model.comparisonDirection({ratio:Infinity},'execution_allocations'),'slower');
assert.equal(model.comparisonDirection({ratio:null},'execution_allocations'),'unmatched');
assert.equal(model.comparisonDirection({ratio:1},'artifact_bytes'),'equal');
assert.equal(model.controlComparison({record:base,metric:'execution_allocations'},{kind:'rust',record:{summary:{execution_allocations:{median:0}}},metric:'execution_allocations'}).ratio,1);
for(const group of grouping.metricGroups)assert.equal(grouping.metricsRoute(group.href).group,group.id);
assert.equal(grouping.metricsRoute('/metrics/').kind,'summary');
assert.equal(grouping.metricsRoute('/metrics/','?view=suite&deflate-order=reverse').kind,'suite','explicit legacy tab selection wins over retained native filters');
assert.equal(grouping.metricsRoute('/metrics/','?case=scalar').kind,'suite');
assert.equal(grouping.metricsRoute('/metrics/','?deflate-case=empty').kind,'deflate');
assert.equal(grouping.metricsRoute('/metrics/tasks/scalar/').task,'scalar');
assert.equal(grouping.metricsRoute('/metrics/knucleotide/').task,'knucleotide');
assert.equal(new URL(grouping.taskURL(all.find(row=>row.group==='runtime')),'https://example.org').pathname,'/metrics/tasks/scalar/');

class Element {
  constructor(){this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.events={};this.clientWidth=900;this.attributes={};this.dataset={};}
  addEventListener(type,callback){this.events[type]=callback;}
  querySelectorAll(){return [];}
}
const source=fs.readFileSync(new URL('../src/metrics-summary.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
async function mount(path='/metrics/',query='',failure){
  const elements=new Map(),element=selector=>{if(!elements.has(selector))elements.set(selector,new Element());return elements.get(selector);};
  for(const [id,value] of [['summary-group','all'],['summary-sort','name'],['summary-order','forward']])element('#'+id).value=value;
  const location={pathname:path,search:query,hash:'',origin:'https://example.org'};
  const history={replaceState(_a,_b,url){this.url=url;}};
  let nativeRequests=0;
  const context=vm.createContext({...model,...grouping,URL,URLSearchParams,console,Blob,setTimeout,clearTimeout,location,history,
    document:{querySelector:element},loadCampaigns:async()=>bundle,loadNative:async()=>{nativeRequests++;if(failure)throw Error(failure);return native;}});
  vm.runInContext(source,context);await context.ready;
  return {element,history,nativeRequests};
}
let ui=await mount();
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,all.length);
assert.ok(ui.element('#summary-bodies').innerHTML.includes('scope="rowgroup"'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('Scalar &lt;safe&gt;'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('Scalar <safe>'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('1.049× time'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('%'));
ui.element('#summary-outcomes').events.click({target:{closest:()=>({dataset:{summaryOutcome:'faster'}})}});
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,grouping.countsFor(all).faster);
assert.ok(ui.history.url.includes('result=faster'));
ui=await mount('/metrics/','?group=deflate&result=slower&order=reverse');
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,20);
assert.equal(ui.element('#summary-order').value,'reverse');
assert.ok(ui.history.url.includes('order=reverse'));
ui=await mount('/metrics/compiler/');
assert.equal(ui.nativeRequests,0,'compiler pages do not load compressor references');
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('libdeflate'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('2× time'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('No matched comparison'));
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,2);
assert.equal(ui.element('#summary-group').disabled,true);
ui=await mount('/metrics/size/');
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,83,'size page includes all native compressed outputs as well as generic artifacts');
ui=await mount('/metrics/','','Unavailable');
assert.ok(ui.element('#summary-error').textContent.includes('Unavailable'));
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,grouping.suiteMeasurements(bundle).length,'a partial load keeps the other measurements visible and reports the omission');
console.log('Grouped summary, correct per-metric references, zero allocations, strict ratios, static routes, shared filters, all compression sizes and partial data loading pass.');
