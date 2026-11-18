import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/campaigns-model.mjs';
import * as grouping from '../src/metrics-model.mjs';
import {validateNative} from '../src/metrics-data.mjs';
const native=validateNative(JSON.parse(fs.readFileSync(new URL('../src/deflate-m3-results-20261118.json',import.meta.url))));
const base={case_id:'scalar',backend:'source',lane:'candidate',outcome:'ok',progress:'measured',control_contract:'shared',task_hash:'t',measurement_hash:'m',environment_hash:'e',source_sha256:'s',revision:'r',measurement:{primary_metric:'resident_turn_seconds'},summary:{resident_turn_seconds:{median:1.0489},source_to_artifact_seconds:{median:.03},execution_allocations:{median:0},artifact_bytes:{median:256}}};
const reference={...base,backend:'rust',lane:'control',title:'Rust · task control',reference_url:'https://example.org/scalar.rs',summary:{resident_turn_seconds:{median:1},execution_allocations:{median:5}}};
const build={...base,case_id:'native-build',backend:'native',measurement:{primary_metric:'source_to_executable_seconds'},summary:{source_to_executable_seconds:{median:2},native_process_seconds:{median:.5},executable_bytes:{median:900}}};
const buildReference={...build,backend:'rust',lane:'control',reference_url:'https://example.org/build.rs',summary:{source_to_executable_seconds:{median:1},native_process_seconds:{median:1},executable_bytes:{median:1000}}};
const alone={...base,case_id:'no-reference'};
const bundle={schema:'mech.benchmark-dashboard.v2',catalog:{cases:[{id:'scalar',title:'Scalar <safe>',family:'arithmetic',backends:['source']},{id:'native-build',title:'Native build',family:'compilation',backends:['native']},{id:'no-reference',title:'Not a comparison',family:'arithmetic',backends:['source']}]},campaigns:[{id:'run',started_at:'2026-11-17',results:[base,reference,build,buildReference,alone]}]};
const all=grouping.publishedComparisons(bundle,native);
assert.equal(all.length,83,'the main view has one matched primary timing per task and 81 compression cases');
assert.ok(!all.some(row=>row.definition?.id==='no-reference'));
assert.ok(all.every(row=>row.direction!=='unmatched'));
assert.equal(grouping.publishedComparisons(bundle,native,{group:'compiler'}).length,1,'supporting compiler stages are not additional benchmarks');
assert.equal(grouping.publishedComparisons(bundle,native,{group:'size'}).length,1,'native output bytes are not duplicated as 81 size benchmarks');
assert.equal(grouping.nativeMeasurements(native).filter(row=>row.group==='deflate').length,81);
assert.equal(model.comparisonLabel({ratio:1.0489},'resident_turn_seconds'),'1.049× time');
assert.equal(model.comparisonLabel({ratio:0},'execution_allocations'),'0× count');
assert.equal(model.comparisonLabel({ratio:Infinity},'execution_allocations'),'∞× count');
assert.equal(model.comparisonDirection({ratio:null},'execution_allocations'),'unmatched');
assert.equal(model.referenceLink({kind:'rust',record:reference}),'<a href="https://example.org/scalar.rs">Rust</a>');
assert.equal(model.referenceLink({kind:'mech',label:'Mech · IR355 baseline',record:{reference_url:'/benchmarks/source.txt'}}),'<a href="/benchmarks/source.txt">Mech</a>');
assert.equal(model.referenceLink({kind:'rust',record:{reference_url:'javascript:alert(1)'}}),'Rust');
assert.equal(grouping.metricsRoute('/metrics/','?view=suite&deflate-order=reverse').kind,'suite');

class Element {
  constructor(){this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.events={};this.clientWidth=900;this.attributes={};this.dataset={};}
  addEventListener(type,callback){this.events[type]=callback;}
  querySelectorAll(){return [];}
}
const source=fs.readFileSync(new URL('../src/metrics-summary.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
async function mount(path='/metrics/',query='',failure){
  const elements=new Map(),element=selector=>{if(!elements.has(selector))elements.set(selector,new Element());return elements.get(selector);};
  const location={pathname:path,search:query,hash:'',origin:'https://example.org'};
  const history={replaceState(_a,_b,url){this.url=url;}};
  let nativeRequests=0;
  const context=vm.createContext({...model,...grouping,URL,URLSearchParams,console,Blob,setTimeout,clearTimeout,location,history,
    document:{querySelector:element},loadCampaigns:async()=>bundle,loadNative:async()=>{nativeRequests++;if(failure)throw Error(failure);return native;}});
  vm.runInContext(source,context);await context.ready;
  return {element,history,nativeRequests};
}
let ui=await mount();
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,83);
assert.equal((ui.element('#summary-bodies').innerHTML.match(/ hidden>/g)||[]).length,82,'compression inputs and small runtime tests start collapsed');
assert.ok(ui.element('#summary-bodies').innerHTML.includes('Scalar &lt;safe&gt;'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('href="https://example.org/scalar.rs">Rust</a>'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('task control'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('Not a comparison'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('source_to_artifact'));
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('Unmatched'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('1.049× time'));
ui.element('#summary-bodies').events.click({target:{closest:()=>({dataset:{summarySort:'mech'}})}});
assert.ok(ui.history.url.includes('sort=mech'));
assert.ok(ui.element('#summary-bodies').innerHTML.includes('aria-sort="ascending"><button class="column-sort" data-summary-sort="mech"'));
ui.element('#summary-bodies').events.click({target:{closest:()=>({dataset:{summarySort:'mech'}})}});
assert.ok(ui.history.url.includes('dir=desc'));
ui.element('#summary-bodies').events.click({target:{closest:()=>({dataset:{groupToggle:'deflate'}})}});
assert.equal((ui.element('#summary-bodies').innerHTML.match(/ hidden>/g)||[]).length,1);
assert.ok(ui.history.url.includes('expand='));
ui.element('#summary-outcomes').events.click({target:{closest:()=>({dataset:{summaryOutcome:'faster'}})}});
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,61);
assert.ok(!ui.element('#summary-bodies').innerHTML.includes(' hidden>'),'a chosen result filter reveals matching tests');
ui=await mount('/metrics/','?expand=none');
assert.equal((ui.element('#summary-bodies').innerHTML.match(/ hidden>/g)||[]).length,83);
assert.ok(ui.history.url.includes('expand=none'));
ui=await mount('/metrics/compiler/');
assert.equal(ui.nativeRequests,0);
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,1);
assert.ok(!ui.element('#summary-bodies').innerHTML.includes('libdeflate'));
ui=await mount('/metrics/','','Unavailable');
assert.ok(ui.element('#summary-error').textContent.includes('Unavailable'));
assert.equal((ui.element('#summary-bodies').innerHTML.match(/data-summary-row=/g)||[]).length,2);
console.log('Curated primary comparisons, collapsed detail groups, sortable columns, linked reference names, omission of unpaired observations and correct compiler references pass.');
