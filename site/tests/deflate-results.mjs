import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/campaigns-model.mjs';

const data=JSON.parse(fs.readFileSync(new URL('../src/deflate-m3-results-20261118.json',import.meta.url)));
const csv=fs.readFileSync(new URL('../src/deflate-m3-libdeflate-20261118.csv',import.meta.url),'utf8').trim().split('\n').slice(1).map(line=>line.split(','));
assert.equal(csv.length,162);
for(const [order,id,mech,libdeflate,ratio] of csv){
  const run=data.cases.find(row=>row.id===id).runs[order];
  assert.equal(run.mech_seconds,Number(mech));assert.equal(run.libdeflate_seconds,Number(libdeflate));assert.equal(run.ratio,Number(ratio));
}
for(const order of ['forward','reverse']){
  assert.equal(data.cases.filter(row=>row.runs[order].ratio<1).length,61);
  assert.equal(data.cases.filter(row=>row.runs[order].ratio>1).length,20);
  assert.ok(data.cases.every(row=>Number.isSafeInteger(row.mech_output_bytes)&&Number.isSafeInteger(row.libdeflate_output_bytes)));
}

class Element {
  constructor(dataset={}){this.dataset=dataset;this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.events={};this.attributes={};this.clientWidth=900;this.classList={toggle(){}};}
  addEventListener(type,fn){this.events[type]=fn;}
  querySelectorAll(){return [];}
  setAttribute(key,value){this.attributes[key]=value;}
  focus(){this.focused=true;}
  scrollIntoView(){this.scrolled=true;}
}
const source=fs.readFileSync(new URL('../src/deflate-results.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'')
  .replaceAll('import.meta.url',"'http://localhost/benchmarks/deflate-results.mjs?v=test-build'").replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
async function mount(query='',payload=data){
  const elements=new Map(),element=selector=>{if(!elements.has(selector))elements.set(selector,new Element());return elements.get(selector);};
  element('#deflate-sort').value='slowest';element('#deflate-error').hidden=true;
  const tabs=[new Element({view:'deflate'}),new Element({view:'suite'})];
  const filters=['all','faster','slower'].map(nativeFilter=>new Element({nativeFilter}));
  const location={pathname:'/metrics/',search:query,hash:''};
  const history={replaceState(_a,_b,value){this.url=value;const url=new URL(value,'http://localhost');location.search=url.search;location.hash=url.hash;}};
  const requests=[];
  const context=vm.createContext({...model,URL,URLSearchParams,Response,console,CSS:{escape:value=>value},matchMedia:()=>({matches:true}),location,history,
    document:{querySelector:element,querySelectorAll:selector=>selector==='[data-view]'?tabs:filters},
    fetch:async url=>{requests.push(String(url));return new Response(JSON.stringify(payload));}});
  vm.runInContext(source,context);await context.ready;
  return {element,tabs,filters,history,requests};
}
let ui=await mount();
assert.equal(ui.element('#deflate-error').hidden,true);
assert.equal(ui.element('#deflate-error').textContent,'');
assert.equal(ui.requests.length,1);
assert.ok(ui.requests[0].endsWith('?v=test-build'));
assert.equal((ui.element('#deflate-cases').innerHTML.match(/data-native-row=/g)||[]).length,81);
assert.equal((ui.element('#deflate-chart').innerHTML.match(/class="plot-point faster"/g)||[]).length,61);
assert.equal((ui.element('#deflate-chart').innerHTML.match(/class="plot-point slower"/g)||[]).length,20);
assert.ok(ui.element('#deflate-chart').innerHTML.includes('reference time · log₁₀'));
await ui.element('#deflate-filters').events.click({target:{closest:()=>({dataset:{nativeFilter:'slower'}})}});
assert.equal((ui.element('#deflate-cases').innerHTML.match(/data-native-row=/g)||[]).length,20);
assert.ok(ui.history.url.includes('deflate-filter=slower'));
ui.element('#deflate-order').value='reverse';ui.element('#deflate-order').events.change();
assert.equal((ui.element('#deflate-cases').innerHTML.match(/data-native-row=/g)||[]).length,20);
assert.ok(ui.history.url.includes('deflate-order=reverse'));
ui.element('#deflate-cases').events.click({target:{closest:()=>({dataset:{nativeCase:'prefix-random-8192'}})},currentTarget:ui.element('#deflate-cases')});
assert.ok(ui.history.url.includes('deflate-case=prefix-random-8192'));
assert.ok(ui.element('#deflate-readout').innerHTML.includes('Prefix random 8192'));
ui.tabs[1].events.click();assert.equal(ui.element('#suite-panel').hidden,false);assert.equal(ui.element('#deflate-m3').hidden,true);
assert.ok(ui.history.url.includes('view=suite'));
ui=await mount('?view=deflate&deflate-filter=slower&deflate-order=reverse&deflate-search=prefix&deflate-sort=name');
const visible=data.cases.filter(row=>row.runs.reverse.ratio>1&&row.title.toLowerCase().includes('prefix'));
assert.equal((ui.element('#deflate-cases').innerHTML.match(/data-native-row=/g)||[]).length,visible.length);
assert.equal(ui.element('#deflate-order').value,'reverse');assert.equal(ui.element('#deflate-sort').value,'name');
ui=await mount('?case=scalar');assert.equal(ui.element('#suite-panel').hidden,false,'existing task links open the runtime/compiler view');
ui=await mount('',{...data,cases:data.cases.slice(1)});assert.equal(ui.element('#deflate-error').textContent,'The compression result set is incomplete.');
console.log('All 162 native rows match the verified CSV; outcome colors, filtering, reversed order, output sizes, shared links and incomplete-data handling pass.');
