import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as math from '../src/math.mjs';

// Exercise the real SVG renderer with a small DOM adapter; no browser or benchmark workers.
class Element {
  constructor(tag='div') {
    this.tagName=tag;this.children=[];this.attributes={};this.dataset={};this.parentNode=null;
    this.clientWidth=1000;this.textContent='';this.innerHTML='';this.hidden=false;this.open=false;
    this.style={setProperty(){},removeProperty(){}};
    const classes=new Set();
    this.classList={add:(...values)=>values.forEach(v=>classes.add(v)),remove:(...values)=>values.forEach(v=>classes.delete(v)),
      contains:value=>classes.has(value),toggle:(value,on=!classes.has(value))=>{on?classes.add(value):classes.delete(value);return on;}};
  }
  setAttribute(key,value){this.attributes[key]=String(value);if(key.startsWith('data-'))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]=String(value);if(key==='class')this.classList.add(...String(value).split(' '));}
  getAttribute(key){return this.attributes[key]??null;}
  removeAttribute(key){delete this.attributes[key];}
  append(child){child.parentNode=this;this.children.push(child);}
  insertBefore(child,before){this.children=this.children.filter(node=>node!==child);child.parentNode=this;this.children.splice(this.children.indexOf(before),0,child);}
  replaceChildren(){this.children=[];}
  addEventListener(){} before(){} after(){} focus(){} scrollIntoView(){}
  contains(node){return node===this||this.children.some(child=>child.contains(node));}
  getBBox(){return {x:0,y:-12,width:this.textContent.length*7,height:16};}
  querySelectorAll(selector){const key=selector.match(/^\[([^\]]+)\]$/)?.[1];return this.children.flatMap(child=>[...(key&&child.getAttribute(key)!==null?[child]:[]),...child.querySelectorAll(selector)]);}
}
const elements=new Map();
const element=selector=>{if(!elements.has(selector))elements.set(selector,new Element(selector));return elements.get(selector);};
const document={querySelector:element,createComment:()=>new Element('comment'),createElementNS:(_,tag)=>new Element(tag),
  documentElement:new Element('html'),body:new Element('body'),activeElement:null};
const source=fs.readFileSync(new URL('../src/app.mjs',import.meta.url),'utf8');
const html=fs.readFileSync(new URL('../src/index.html',import.meta.url),'utf8');
const css=fs.readFileSync(new URL('../src/style.css',import.meta.url),'utf8');
const context=vm.createContext({...math,document,window:{},innerWidth:1000,
  matchMedia:()=>({matches:false,addEventListener(){}}),emptyTraitFilters:()=>({}),filterLanguageKeys:keys=>new Set(keys),
  axisData:data=>data,projectProgram:program=>program,console,Set,Map,
  setTimeout:()=>0,clearTimeout(){}});
const executable=source.replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'file:///test/app.mjs'")
  .replace(/start\(\)\.catch\(error=>\{[^\n]+\}\);\s*$/,'');
vm.runInContext(executable+`\nglobalThis.harness={
  initialize(fixture){data=fixture;programCatalog=fixture.programs;Object.assign(state,{benchmarks:new Set(fixture.benchmarks.map(b=>b.key)),languages:new Set(fixture.languages.map(l=>l.key)),releaseYearStart:1960,releaseYear:2026,focus:'b1'});for(const l of fixture.languages)colors[l.key]='#f6c04e';},
  render(options){Object.assign(state,options);model=comparison(data,allSelection());renderChart();},
  table(){renderTable();},
  selection(){return state;},
  play(){const original=update;update=()=>{};try{playYears();}finally{update=original;pauseYears();}}
};`,context);
const fixture={languages:[{key:'mech',label:'Zeta',family:'mech',release_year:2026},{key:'alpha',label:'Alpha',release_year:1970},{key:'beta',label:'beta',release_year:1990}],benchmarks:[],programs:{}};
for(let bi=0;bi<2;bi++){
  const benchmark={key:`b${bi+1}`,title:`Benchmark ${bi+1}`,workload:'fixture',baseline_seconds:1,baseline_loc:1,groups:[]};
  for(const [li,language] of fixture.languages.entries()){
    const keys=[];
    for(const kind of ['fast','small']){
      const key=`${language.key}-${benchmark.key}-${kind}`,x=(li+1)*(bi+1)*(kind==='fast'?2:1),seconds=(li+1)*(bi+1)*(kind==='fast'?1:2);
      fixture.programs[key]={key,id:key,language:language.key,benchmark:benchmark.key,loc:x,x,y:seconds,seconds,samples:[seconds*.8,seconds,seconds*1.2]};keys.push(key);
    }
    benchmark.groups.push({language:language.key,programs:keys});
  }
  fixture.benchmarks.push(benchmark);
}
context.harness.initialize(fixture);
const modes=['off','dim','highlight'];
let mathCases=0,renderCases=0;
for(const samples of modes)for(const medians of modes)for(const density of modes)for(const global of [false,true])for(const fast of [false,true])for(const small of [false,true]){
  const state=math.chartLayerState({samples,medians,density,global,fast,small,sampleCount:6,entryCount:3});
  assert.equal(state.showSamples,samples!=='off');assert.equal(state.showDensity,density!=='off');
  assert.equal(state.showMedians,medians!=='off'&&(fast||small));assert.equal(state.showGlobal,global&&(fast||small));
  assert.equal(state.globalLayer.opacity,global?1:0);
  assert.equal(state.empty,!(state.showSamples||state.showDensity||state.showMedians||state.showGlobal));mathCases++;
}
const ancestors=node=>{const result=[];for(let current=node;current;current=current.parentNode)result.push(current);return result;};
const opacity=node=>ancestors(node).reduce((value,parent)=>value*Number(parent.getAttribute('opacity')??1),1);
const expectedDomains=new Map();
for(const view of ['summary','benchmark','mech','language'])for(const focusMeans of [false,true])for(const samples of modes)for(const medians of modes)for(const density of modes)for(const global of [false,true]){
  context.harness.render({view,focusMeans,sampleMode:samples,medianMode:medians,densityMode:density,global,fast:true,small:true,
    languageFocus:view==='language'?{keys:['alpha'],label:'Alpha'}:null,ellipses:new Set(['mech','alpha','beta'])});
  const svg=element('#chart'),globals=svg.querySelectorAll('[data-global-statistic]'),profiles=svg.querySelectorAll('[data-profile-median]'),runs=svg.querySelectorAll('[data-sample]');
  assert.equal(globals.length,global?2:0,`${view}: global visibility must be independent`);
  for(const mark of globals){assert.equal(opacity(mark),1,`${view}: Global must have full opacity with Medians ${medians}`);assert.ok(ancestors(mark).some(parent=>parent.dataset.layer==='global'));assert.ok(!ancestors(mark).some(parent=>parent.dataset.layer==='medians'));}
  const spreads=svg.querySelectorAll('[data-global-sigma]');
  if(global&&view!=='mech')assert.ok(spreads.length>0,'Global covariance remains available without Medians');
  for(const spread of spreads)assert.equal(opacity(spread),1,'Global covariance cannot inherit the Medians opacity');
  assert.equal(profiles.length>0,medians!=='off');assert.equal(runs.length>0,samples!=='off');
  assert.equal(element('#empty-state').hidden,global||samples!=='off'||medians!=='off'||density!=='off');
  const key=`${view}:${focusMeans}`,domain=Object.fromEntries(['xMin','xMax','yMin','yMax'].map(key=>[key,svg.dataset[key]]));
  if(!expectedDomains.has(key))expectedDomains.set(key,domain);else assert.deepEqual(domain,expectedDomains.get(key),'Layer switches must preserve fixed axes');
  renderCases++;
}
// Summary data starts in display-name order and advertises that ordering accessibly.
context.harness.render({view:'summary',languageFocus:null,global:true});context.harness.table();
const table=element('#mean-table tbody').innerHTML;
assert.ok(table.indexOf('data-table-language="alpha"')<table.indexOf('data-table-language="beta"'));
assert.ok(table.indexOf('data-table-language="beta"')<table.indexOf('data-table-language="mech"'));
assert.match(element('#mean-table thead').innerHTML,/<th scope="col" aria-sort="ascending">.*data-sort-key="language"/);
// Playback changes only the window; it no longer turns on a trail-related overlay.
context.harness.selection().global=false;context.harness.play();assert.equal(context.harness.selection().global,false);
assert.ok(!('trail' in context.harness.selection()));
assert.doesNotMatch(source+html+css,/median-trail|medianHistory|currentHistory|historyCache|getMedianHistory/);
assert.ok(!('medianHistory' in math));
assert.match(source,/filterDrawer\.append\(filterControls\)/,'Keep the shared mobile filter drawer');
console.log(`Passed ${mathCases} layer combinations and ${renderCases} SVG renders across summary, benchmark, Mech and language views; alphabetical table, fixed axes, independent playback and trail removal.`);
