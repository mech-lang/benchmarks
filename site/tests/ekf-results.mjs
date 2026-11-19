import assert from 'node:assert/strict';
import fs from 'node:fs';import vm from 'node:vm';
import * as model from '../src/ekf-model.mjs';
import {comparisonStyle,formatMetric} from '../src/campaigns-model.mjs';
import {ekfMeasurements} from '../src/metrics-model.mjs';
const row=(id,label,mode,rate,{is_mech=false,category='cpu-jit',publication='fused-block',backend}={})=>({id,label,mode,category,publication,is_mech,backend,n:3,samples_million_filter_turns_per_second:[rate,rate,rate],median:rate,mad:0,time_seconds:1e-6/rate,samples_seconds_per_filter_turn:[rate,rate,rate].map(x=>1e-6/x),version:'v1',source_url:'/benchmarks/ekf-sources/'+id+'.txt'});
const study={id:'cpu',title:'CPU implementations',machine:'Apple M1',precision:'f32',instances:500000,turns:40,recorded_at:'2026-09-25',scope:'Warm numerical execution.',methods:{sample:'fresh process'},evidence_url:'/benchmarks/ekf-evidence/raw.json',rows:[
 row('a','Mech fused <safe>','checked',30,{is_mech:true}),row('b','Julia','checked',20),row('c','Numba','checked',10),
 row('d','Rust','checked',100,{category:'cpu-aot'}),row('e','Mech fused <safe>','unchecked',40,{is_mech:true}),row('f','Julia','unchecked',25),row('g','Numba','unchecked',50),
 row('h','Mech per-turn','checked',50,{is_mech:true,publication:'per-turn'}),row('i','Taichi','checked',15,{publication:'per-turn'})]};
const backends={...study,id:'backends',title:'Mech backends',rows:[row('j','Resident numerical evaluator','checked',1,{is_mech:true,publication:'per-turn',backend:'evaluator'}),row('k','Metal backend cohort','checked',500,{is_mech:true,category:'metal',publication:'per-turn',backend:'metal'})]};
const metal={...study,id:'metal',title:'Metal',rows:[row('l','Mech Metal','checked',90,{is_mech:true,category:'metal',publication:'per-turn'}),row('m','Rust + MSL','checked',100,{category:'metal',publication:'per-turn'})]};
const data={schema:'mech.ekf-study.v1',studies:[backends,study,metal],method:'Retained trials.',article_url:'https://mech-lang.org/iros-r4r-2026/index.html'};
assert.equal(model.validateEKF(data),data);
assert.equal(model.referenceFor(study,study.rows[0]).label,'Julia');
assert.equal(model.referenceFor(study,study.rows[7]).label,'Taichi','per-turn Mech uses a per-turn peer, not the faster fused reference');
assert.equal(model.referenceFor(study,study.rows[4]).label,'Numba','checking modes remain separate');
assert.equal(model.referenceFor(backends,backends.rows[0]),null,'another Mech backend is never a peer');
const all=model.mechMeasurements(data);assert.ok(all.every(row=>row.is_mech));assert.equal(all.length,5);assert.ok(!all.some(row=>row.label==='Metal backend cohort'),'the matched GPU campaign supplies one GPU summary row');
const visible=model.selectedMeasurements(data);assert.equal(visible.length,4);assert.ok(visible.every(row=>row.mode==='checked'&&row.is_mech));
assert.equal(model.selectedMeasurements(data,{query:'Julia'})[0].label,'Mech fused <safe>','search returns Mech rows whose peer matches');
assert.equal(model.selectedMeasurements(data,{sort:'mech'})[0].label,'Mech Metal');
assert.equal(ekfMeasurements(data).length,3);assert.ok(ekfMeasurements(data).every(row=>row.value>0&&row.reference>0&&row.record.source_url));
assert.equal(ekfMeasurements(data).find(row=>row.title.includes('per-turn')).control.label,'Taichi');
assert.ok(model.sampleChart(visible,{medians:false}).includes('ekf-sample'));assert.ok(!model.sampleChart(visible,{samples:false}).includes('class="ekf-sample"'));
assert.ok(model.sampleChart(visible,{samples:false,medians:false}).includes('table still shows'));
const invalid=structuredClone(data);invalid.studies[1].rows[0].median=20;assert.throws(()=>model.validateEKF(invalid),/differs/);
const csv=model.exportRows(data.studies);assert.equal(csv.trim().split('\r\n').length,16);assert.ok(csv.includes('"time_divided_by_peer_time"'));assert.ok(!csv.includes('"cpu","Apple M1","f32","500000","40","2026-09-25","Julia"'),'peers appear only in reference columns, not as result rows');

class Element{constructor(){this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.checked=true;this.clientWidth=900;this.events={};}addEventListener(type,callback){this.events[type]=callback;}querySelectorAll(){return [];}}
const script=fs.readFileSync(new URL('../src/ekf-results.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'https://mech-lang.org/benchmarks/ekf-results.mjs?v=build'").replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
const elements=new Map(),element=key=>{if(!elements.has(key))elements.set(key,new Element());return elements.get(key);};let fetches=0;
const context=vm.createContext({...model,comparisonStyle,formatMetric,URL,URLSearchParams,Blob,console,setTimeout,clearTimeout,location:{pathname:'/metrics/ekf/',search:'?samples=0&study=cpu&peer_cpu-jit=Numba',hash:''},history:{replaceState(_a,_b,url){this.url=url;}},document:{querySelector:element},fetch:async()=>{fetches++;return {ok:true,json:async()=>data};}});
vm.runInContext(script,context);await context.ready;
assert.equal(element('#ekf-error').textContent,'');assert.equal((element('#ekf-rows').innerHTML.match(/data-ekf-row=/g)||[]).length,4);assert.equal((element('#ekf-headings').innerHTML.match(/<th /g)||[]).length,5);assert.ok(element('#ekf-headings').innerHTML.includes('Mech / peer'));assert.ok(element('#ekf-rows').innerHTML.includes('Mech fused &lt;safe&gt;'));assert.ok(!/<tr[^>]*><td><a[^>]*>Julia<\/a>/.test(element('#ekf-rows').innerHTML));
assert.ok(!element('#ekf-chart').innerHTML.includes('class="ekf-sample"'));assert.ok(!context.history.url.includes('peer_'));assert.ok(!context.history.url.includes('study='));
const rowIndex=String(model.selectedMeasurements(data).findIndex(row=>row.id==='a'));const event={target:{closest:()=>({dataset:{ekfRow:rowIndex}})}};element('#ekf-chart').events.pointerover(event);const chart=element('#ekf-chart').innerHTML;element('#ekf-chart').events.pointerover(event);assert.equal(fetches,1);assert.equal(element('#ekf-chart').innerHTML,chart);assert.ok(element('#ekf-readout').innerHTML.includes('Julia'));assert.ok(element('#ekf-readout').innerHTML.includes('median ± MAD'));
element('#ekf-modes').events.click({target:{closest:()=>({dataset:{ekfMode:'both'}})}});assert.equal((element('#ekf-rows').innerHTML.match(/data-ekf-row=/g)||[]).length,5);assert.equal((element('#ekf-headings').innerHTML.match(/<th /g)||[]).length,6);assert.ok(context.history.url.includes('mode=both'));
console.log('Mech-only summary rows, fixed closest peers, publication/mode matching, paired overview rows, compact table, exports and stable hover pass.');
