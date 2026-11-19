import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/ekf-model.mjs';
import {comparisonStyle} from '../src/campaigns-model.mjs';
const row=(id,label,mode,rate,category='cpu-jit',is_mech=false)=>({id,label,mode,category,is_mech,n:3,samples_million_filter_turns_per_second:[rate,rate,rate],median:rate,mad:0,time_seconds:1e-6/rate,samples_seconds_per_filter_turn:[rate,rate,rate].map(x=>1e-6/x),version:'v1',source_url:'/benchmarks/ekf-sources/'+id+'.mec.txt'});
const study={id:'cpu',title:'CPU implementations',machine:'Apple M1',precision:'f32',instances:500000,turns:40,recorded_at:'2026-09-25',scope:'One publication per turn.',methods:{sample:'fresh process'},evidence_url:'/benchmarks/ekf-evidence/raw.json',rows:[
 row('a','Mech <safe>','checked',30,'cpu-jit',true),row('b','Julia','checked',20),row('c','Numba','checked',10),
 row('d','Rust','checked',100,'cpu-aot'),row('e','Mech <safe>','unchecked',40,'cpu-jit',true),row('f','Julia','unchecked',25),row('g','Numba','unchecked',50),
 row('h','Mech faster','checked',1000,'cpu-jit',true),row('i','GPU','checked',10000,'metal')]};
const backends={...study,id:'backends',title:'Mech execution backends',rows:study.rows.filter(row=>row.is_mech)};
const data={schema:'mech.ekf-study.v1',studies:[backends,study],method:'Retained trials.',article_url:'https://mech-lang.org/iros-r4r-2026/index.html'};
assert.equal(model.validateEKF(data),data);
assert.equal(model.referenceFor(study,study.rows[0]).label,'Julia','CPU JIT cannot use a Mech, AOT or GPU result as its reference');
assert.ok(Math.abs(model.relativeTime(study,study.rows[0])-2/3)<1e-12);
assert.equal(model.referenceFor(study,study.rows[4]).label,'Numba','checking modes select their own peers');
assert.ok(Math.abs(model.relativeTime(study,study.rows[4])-1.25)<1e-12);
assert.equal(model.referenceFor(study,study.rows[3]).label,'Rust','CPU AOT peers stay in their category');
assert.equal(model.referenceFor(backends,backends.rows[0]),null,'Mech-only studies have no external reference');
assert.equal(model.relativeTime(backends,backends.rows[0]),null);
assert.equal(model.referenceFor(study,study.rows[0],{'cpu-jit':'Rust'}).label,'Julia','an incompatible URL selection cannot bypass category matching');
assert.equal(model.referenceFor(study,study.rows[0],{'cpu-jit':'Mech faster'}).label,'Julia','Mech cannot select itself as a peer');
assert.deepEqual(model.referenceOptions(study,'cpu-jit'),['Julia','Numba']);
const references={'cpu-jit':'Numba'};
assert.ok(Math.abs(model.relativeTime(study,study.rows[0],references)-1/3)<1e-12);
assert.ok(Math.abs(model.relativeTime(study,model.selectedRows(study,{query:'safe'})[0],references)-1/3)<1e-12,'search cannot change the peer denominator');
assert.equal(model.selectedRows(study,{sort:'rate',descending:true})[0].label,'GPU');
const noMedians=model.sampleChart(study.rows,{medians:false});assert.ok(noMedians.includes('ekf-sample'));assert.ok(!noMedians.includes('<rect'));
const noSamples=model.sampleChart(study.rows,{samples:false});assert.ok(noSamples.includes('<rect'));assert.ok(!noSamples.includes('class="ekf-sample"'));
assert.ok(model.sampleChart(study.rows,{samples:false,medians:false}).includes('table still shows'));
const invalid=structuredClone(data);invalid.studies[1].rows[0].median=20;assert.throws(()=>model.validateEKF(invalid),/differs/);
const csv=model.exportRows([study],{study:'cpu',rows:[study.rows[0]]},references);assert.equal(csv.trim().split('\r\n').length,4);assert.ok(csv.includes('"time_divided_by_peer_time"'));assert.ok(csv.includes('"Numba"'));assert.ok(csv.includes('https://mech-lang.org/benchmarks/ekf-sources/c.mec.txt'));assert.ok(!csv.includes('best_same_mode'));

class Element{constructor(){this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.checked=true;this.clientWidth=900;this.events={};}addEventListener(type,callback){this.events[type]=callback;}querySelectorAll(){return [];}}
const script=fs.readFileSync(new URL('../src/ekf-results.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'https://mech-lang.org/benchmarks/ekf-results.mjs?v=build'").replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
const elements=new Map(),element=key=>{if(!elements.has(key))elements.set(key,new Element());return elements.get(key);};let fetches=0;
const context=vm.createContext({...model,comparisonStyle,URL,URLSearchParams,Blob,console,setTimeout,clearTimeout,location:{pathname:'/metrics/ekf/',search:'?mode=checked&samples=0&peer_cpu-jit=Numba',hash:''},history:{replaceState(_a,_b,url){this.url=url;}},document:{querySelector:element},fetch:async url=>{fetches++;assert.ok(String(url).endsWith('?v=build'));return {ok:true,json:async()=>data};}});
vm.runInContext(script,context);await context.ready;
assert.equal(element('#ekf-error').textContent,'');assert.equal(element('#ekf-study').value,'cpu');assert.equal(element('#ekf-samples').checked,false);assert.ok(!element('#ekf-chart').innerHTML.includes('class="ekf-sample"'));assert.ok(element('#ekf-rows').innerHTML.includes('Mech &lt;safe&gt;'));assert.ok(element('#ekf-rows').innerHTML.includes('result-tag faster'));assert.ok(element('#ekf-headings').innerHTML.includes('× peer time'));assert.ok(context.history.url.includes('samples=0'));assert.ok(context.history.url.includes('peer_cpu-jit=Numba'));assert.ok(element('#ekf-references').innerHTML.includes('value="Numba" selected'));
element('#ekf-references').events.change({target:{dataset:{ekfReference:'cpu-jit'},value:'Julia'}});assert.ok(context.history.url.includes('peer_cpu-jit=Julia'));
const rowIndex=String(model.selectedRows(study,{mode:'checked'}).findIndex(row=>row.id==='a'));const event={target:{closest:()=>({dataset:{ekfRow:rowIndex}})}};element('#ekf-chart').events.pointerover(event);const chart=element('#ekf-chart').innerHTML;element('#ekf-chart').events.pointerover(event);assert.equal(fetches,1,'rollover cannot refetch evidence');assert.equal(element('#ekf-chart').innerHTML,chart,'rollover cannot rebuild the chart');assert.ok(element('#ekf-readout').innerHTML.includes('median ± MAD'));assert.ok(element('#ekf-readout').innerHTML.includes('Julia time'));
element('#ekf-study').value='backends';element('#ekf-study').events.change();assert.ok(!element('#ekf-headings').innerHTML.includes('× peer time'));assert.equal(element('#ekf-references').innerHTML,'');assert.ok(element('#ekf-comparison-note').innerHTML.includes('only Mech backends'));assert.ok(context.history.url.includes('study=backends'));
console.log('EKF external peers, category/mode matching, no Mech self-reference, selected peer URLs/exports, independent layers and fixed rollover rendering pass.');
