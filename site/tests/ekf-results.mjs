import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/ekf-model.mjs';
import {comparisonStyle} from '../src/campaigns-model.mjs';
const row=(id,label,mode,samples)=>{const median=samples[1];return {id,label,mode,n:3,samples_million_filter_turns_per_second:samples,median,mad:0,time_seconds:1e-6/median,samples_seconds_per_filter_turn:samples.map(x=>1e-6/x),version:'v1',source_url:'/benchmarks/ekf-sources/measured.mec.txt'};};
const study={id:'backends',title:'Execution backends',machine:'Apple M1',precision:'f32',instances:500000,turns:40,recorded_at:'2026-09-25',scope:'One publication per turn.',methods:{sample:'fresh process'},evidence_url:'/benchmarks/ekf-evidence/raw.json',rows:[row('a','AOT <safe>','checked',[10,10,10]),row('b','GPU','checked',[100,100,100]),row('c','AOT <safe>','unchecked',[20,20,20])]};
const data={schema:'mech.ekf-study.v1',studies:[study],method:'Retained trials.',article_url:'https://mech-lang.org/iros-r4r-2026/index.html'};
assert.equal(model.validateEKF(data),data);
assert.equal(model.relativeTime(study,study.rows[0]),10);
assert.equal(model.relativeTime(study,study.rows[2]),1,'unchecked rows use a different denominator');
assert.equal(model.selectedRows(study,{query:'safe'}).length,2);
assert.equal(model.relativeTime(study,model.selectedRows(study,{mode:'checked',query:'safe'})[0]),10,'search cannot change the best-time reference');
assert.equal(model.selectedRows(study,{sort:'rate',descending:true})[0].label,'GPU');
const noMedians=model.sampleChart(study.rows,{medians:false});assert.ok(noMedians.includes('ekf-sample'));assert.ok(!noMedians.includes('<rect'));
const noSamples=model.sampleChart(study.rows,{samples:false});assert.ok(noSamples.includes('<rect'));assert.ok(!noSamples.includes('class="ekf-sample"'));
assert.ok(model.sampleChart(study.rows,{samples:false,medians:false}).includes('table still shows'));
const invalid=structuredClone(data);invalid.studies[0].rows[0].median=20;assert.throws(()=>model.validateEKF(invalid),/differs/);
const csv=model.exportRows([study],{study:'backends',rows:[study.rows[1]]});assert.equal(csv.trim().split('\r\n').length,4);assert.ok(csv.includes('https://mech-lang.org/benchmarks/ekf-sources/'));assert.ok(!csv.includes('AOT <safe>'));

class Element{constructor(){this.innerHTML='';this.textContent='';this.hidden=false;this.value='';this.checked=true;this.clientWidth=900;this.events={};}addEventListener(type,callback){this.events[type]=callback;}querySelectorAll(){return [];}}
const script=fs.readFileSync(new URL('../src/ekf-results.mjs',import.meta.url),'utf8').replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'https://mech-lang.org/benchmarks/ekf-results.mjs?v=build'").replace('start().catch(error=>','globalThis.ready=start().catch(error=>');
const elements=new Map(),element=key=>{if(!elements.has(key))elements.set(key,new Element());return elements.get(key);};let fetches=0;
const context=vm.createContext({...model,comparisonStyle,URL,URLSearchParams,Blob,console,setTimeout,clearTimeout,location:{pathname:'/metrics/ekf/',search:'?mode=checked&samples=0',hash:''},history:{replaceState(_a,_b,url){this.url=url;}},document:{querySelector:element},fetch:async url=>{fetches++;assert.ok(String(url).endsWith('?v=build'));return {ok:true,json:async()=>data};}});
vm.runInContext(script,context);await context.ready;
assert.equal(element('#ekf-error').textContent,'');assert.equal(element('#ekf-samples').checked,false);assert.ok(!element('#ekf-chart').innerHTML.includes('class="ekf-sample"'));assert.ok(element('#ekf-rows').innerHTML.includes('AOT &lt;safe&gt;'));assert.ok(element('#ekf-rows').innerHTML.includes('10×'));assert.ok(context.history.url.includes('samples=0'));
const event={target:{closest:()=>({dataset:{ekfRow:'0'}})}};element('#ekf-chart').events.pointerover(event);const chart=element('#ekf-chart').innerHTML;element('#ekf-chart').events.pointerover(event);assert.equal(fetches,1,'rollover cannot refetch evidence');assert.equal(element('#ekf-chart').innerHTML,chart,'rollover cannot rebuild the chart');assert.ok(element('#ekf-readout').innerHTML.includes('median ± MAD'));
console.log('EKF samples, independent layers, per-mode denominators, source links, CSV selection, shared state and fixed rollover rendering pass.');
