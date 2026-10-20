import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as math from '../src/math.mjs';
import * as formatted from '../src/formatted_axis.mjs';
import * as benchmarkFilters from '../src/benchmark_traits.mjs';
import * as labels from '../src/labels.mjs';

let nextFrame=0,autoFrames=true;
const frames=new Map();
const flushFrames=()=>{const queued=[...frames.values()];frames.clear();for(const run of queued)run(0);};

// Exercise the real SVG renderer with a small DOM adapter; no browser or benchmark workers.
class Element {
  constructor(tag='div') {
    this.tagName=tag;this.children=[];this.attributes={};this.dataset={};this.parentNode=null;
    this.clientWidth=1000;this.textContent='';this.innerHTML='';this.hidden=false;this.open=false;
    this.listeners={};
    const properties=new Map();
    this.style={setProperty:(name,value)=>properties.set(name,String(value)),removeProperty:name=>properties.delete(name),getPropertyValue:name=>properties.get(name)??''};
    const classes=new Set();
    this.classList={add:(...values)=>values.forEach(v=>classes.add(v)),remove:(...values)=>values.forEach(v=>classes.delete(v)),
      contains:value=>classes.has(value),toggle:(value,on=!classes.has(value))=>{on?classes.add(value):classes.delete(value);return on;}};
  }
  setAttribute(key,value){this.attributes[key]=String(value);if(key.startsWith('data-'))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,letter)=>letter.toUpperCase())]=String(value);if(key==='class')this.classList.add(...String(value).split(' '));}
  getAttribute(key){return this.attributes[key]??null;}
  removeAttribute(key){delete this.attributes[key];}
  append(child){if(child.parentNode)child.parentNode.children=child.parentNode.children.filter(node=>node!==child);child.parentNode=this;this.children.push(child);}
  insertBefore(child,before){this.children=this.children.filter(node=>node!==child);child.parentNode=this;this.children.splice(this.children.indexOf(before),0,child);}
  replaceChildren(){for(const child of this.children)child.parentNode=null;this.children=[];}
  addEventListener(type,callback){(this.listeners[type]??=[]).push(callback);}
  emit(type,event={}){
    const value={pointerType:'mouse',target:this,preventDefault(){this.defaultPrevented=true;},...event};
    const bubbling=new Set(['click','keydown','pointerover','pointermove','pointerout','focusin','focusout']);
    const dispatch=(name,bubbles)=>{for(let current=this;current;current=bubbles?current.parentNode:null)for(const callback of current.listeners[name]??[])callback(value);};
    dispatch(type,bubbling.has(type));
    const related={pointerenter:'pointerover',pointerleave:'pointerout',focus:'focusin',blur:'focusout'}[type];
    if(related)dispatch(related,true);
    if(autoFrames)flushFrames();
    return value;
  }
  getScreenCTM(){return null;}
  getBoundingClientRect(){return {top:0,left:0,width:this.clientWidth,height:400};}
  before(){} after(){} focus(){} scrollIntoView(){}
  closest(){return this.parentNode??this;}
  contains(node){return node===this||this.children.some(child=>child.contains(node));}
  getBBox(){return {x:0,y:-12,width:this.textContent.length*7,height:16};}
  querySelectorAll(selector){const key=selector.match(/^\[([^\]]+)\]$/)?.[1];return this.children.flatMap(child=>[...(key&&child.getAttribute(key)!==null?[child]:[]),...child.querySelectorAll(selector)]);}
}
const elements=new Map();
const element=selector=>{if(!elements.has(selector))elements.set(selector,new Element(selector));return elements.get(selector);};
const sampleClass=(node,name)=>node.parentNode.classList.contains(name);
const inheritedStyle=(node,name)=>{for(let current=node;current;current=current.parentNode){const value=current.style.getPropertyValue(name);if(value)return value;}return '';};
const document={querySelector:element,querySelectorAll:()=>[],createComment:()=>new Element('comment'),createElementNS:(_,tag)=>new Element(tag),
  documentElement:new Element('html'),body:new Element('body'),activeElement:null};
const source=fs.readFileSync(new URL('../src/app.mjs',import.meta.url),'utf8');
const html=fs.readFileSync(new URL('../src/index.html',import.meta.url),'utf8');
const css=fs.readFileSync(new URL('../src/style.css',import.meta.url),'utf8');
const context=vm.createContext({...math,...formatted,...benchmarkFilters,...labels,document,window:{addEventListener(){},innerHeight:900},innerWidth:1000,innerHeight:900,
  ResizeObserver:class{observe(){}},requestAnimationFrame:run=>{const id=++nextFrame;frames.set(id,run);return id;},cancelAnimationFrame:id=>frames.delete(id),
  matchMedia:()=>({matches:false,addEventListener(){}}),emptyTraitFilters:()=>({}),filterLanguageKeys:keys=>new Set(keys),
  axisData:data=>data,projectProgram:program=>program,console,Set,Map,
  realAxisData:formatted.axisData,realProjectProgram:formatted.projectProgram,
  setTimeout:()=>0,clearTimeout(){}});
const executable=source.replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'file:///test/app.mjs'")
  .replace(/start\(\)\.catch\(error=>\{[^\n]+\}\);\s*$/,'');
vm.runInContext(executable+`\nglobalThis.harness={
  initialize(fixture){
    data=fixture;programCatalog={...fixture.program_inventory,...fixture.programs};
    languageIndex=new Map(fixture.languages.map(item=>[item.key,item]));benchmarkIndex=new Map(fixture.benchmarks.map(item=>[item.key,item]));
    familyIndex=languageFamilies(data.languages).map(f=>({...f,label:f.members.length>1?f.label:shortName(f.members[0].key)}));
    programsByBenchmark.clear();comparisonViews.clear();domains.clear();benchmarkEntries=null;densityCache=null;
    if(renderedSamplePlot)renderedSamplePlot.replaceChildren();renderedSamplePlot=null;renderedDensityLayer=null;sampleNodes.clear();
    for(const program of Object.values(programCatalog)){
      if(!programsByBenchmark.has(program.benchmark))programsByBenchmark.set(program.benchmark,new Map());
      const languages=programsByBenchmark.get(program.benchmark);if(!languages.has(program.language))languages.set(program.language,[]);
      languages.get(program.language).push(program);
    }
    Object.assign(state,{benchmarks:new Set(fixture.benchmarks.map(b=>b.key)),benchmarkFilters:emptyBenchmarkFilters(),languages:new Set(fixture.languages.map(l=>l.key)),releaseYearStart:1960,releaseYear:2026,playbackYear:null,playing:false,focus:'b1'});for(const l of fixture.languages)colors[l.key]='#f6c04e';
  },
  render(options){Object.assign(state,options);benchmarkEntries=null;model=comparison(plotData(),allSelection());renderChart();},
  derived(){return {model,entries:currentEntries(),samples:currentSampleInputs(),density:currentDensityField(),view:plotData()};},
  cachedSamples(){return [...sampleNodes.values()].flatMap(nodes=>[...nodes.values()]);},
  layerModes:setLayerModes,
  updateWork(options,{rankingsReset=false}={}){
    const originals=[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector,renderChart];
    const calls={years:0,controls:0,overview:0,rankings:0,table:0,inspector:0,chart:0};
    renderYears=()=>calls.years++;renderControls=()=>calls.controls++;
    renderLanguageOverview=()=>calls.overview++;renderMedianRankings=()=>calls.rankings++;
    renderTable=()=>calls.table++;renderInspector=()=>calls.inspector++;
    renderChart=()=>{calls.chart++;return originals[6]();};
    try{Object.assign(state,options);rankingsReset?reset({rankings:true}):update();return calls;}
    finally{[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector,renderChart]=originals;}
  },
  globalRequests(options){
    const original=currentGlobalStatistics;let count=0;
    currentGlobalStatistics=(...args)=>{count++;return original(...args);};
    try{Object.assign(state,options);benchmarkEntries=null;model=comparison(plotData(),allSelection());renderChart();return count;}
    finally{currentGlobalStatistics=original;}
  },
  sampleAction(node,type,event){const original=openPoint,calls=[];openPoint=info=>calls.push(info);try{const emitted=node.emit(type,event);return {calls,prevented:emitted.defaultPrevented===true};}finally{openPoint=original;}},
  visual(options){
    const originals=[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector];
    const unexpected=()=>{throw new Error('Visual-only changes must not rebuild unrelated controls or results.');};
    renderYears=renderControls=renderLanguageOverview=renderMedianRankings=renderTable=renderInspector=unexpected;
    try{Object.assign(state,options);updatePlot();}finally{[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector]=originals;}
  },
  selectionUpdate(options,resetAll=false){
    const originals=[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector];
    renderYears=renderControls=renderLanguageOverview=renderMedianRankings=renderTable=renderInspector=()=>{};
    try{Object.assign(state,options);resetAll?reset():update();}finally{[renderYears,renderControls,renderLanguageOverview,renderMedianRankings,renderTable,renderInspector]=originals;}
  },
  formatting(real){axisData=real?realAxisData:data=>data;projectProgram=real?realProjectProgram:program=>program;},
  table(){renderTable();},
  locAudit:renderLocAudit,
  sameJSONValue,
  programSource,
  compare(key){state.languageFocus={keys:[catalogProgram(key).language],comparison:true,comparisonProgram:key};return comparisonData();},
  inspect(key){state.detail={...state.detail,program:key};const original=renderLanguageOverview,originalRankings=renderMedianRankings;renderLanguageOverview=renderMedianRankings=()=>{};try{renderInspector();}finally{renderLanguageOverview=original;renderMedianRankings=originalRankings;}},
  selection(){return state;},
  relativeTable(){renderLanguageComparisons();},
  rankings(){benchmarkEntries=null;model=comparison(plotData(),allSelection());return currentRankings();},
  overview(){renderLanguageOverview();},
  resetLanguage(){const original=update;update=()=>{};try{reset();}finally{update=original;}},
  compareLanguage(key){const original=update;update=()=>{};try{compareOverviewLanguage(key);}finally{update=original;}},
  selectBenchmarks(keys,options){const original=update;update=()=>{};try{selectBenchmarks(keys,options);}finally{update=original;}},
  selectBenchmarkFacet(dimension,option,checked){const original=update;update=()=>{};try{selectBenchmarkFacet(dimension,option,checked);}finally{update=original;}},
  effectiveBenchmarks,
  domain:selectedPlotDomain,
  savedSelection:savedChartSelection,
  switchView(view){const original=update;update=()=>{};try{selectView(view);}finally{update=original;}},
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
assert.equal(context.harness.sameJSONValue({a:[1,{proof:'retained',value:null}]},{a:[1,{proof:'retained',value:null}]}),true);
assert.equal(context.harness.sameJSONValue({a:[1,{proof:'retained'}]},{a:[1,{proof:'changed'}]}),false);
assert.equal(context.harness.sameJSONValue({a:1,b:2},{b:2,a:1}),false,'Startup identity checks retain JSON key-order equality.');
assert.equal(context.harness.sameJSONValue([],{}),false);
// Language hero order follows the reading order, including narrow screens.
const sections=['id="language-overview"','class="chart-card"','id="median-rankings"','id="language-results"','id="language-comparisons"'];
for(let index=1;index<sections.length;index++)assert.ok(html.indexOf(sections[index-1])<html.indexOf(sections[index]));
assert.match(html,/data-view="summary"[^>]*>All benchmarks/);
assert.doesNotMatch(html,/id="leave-language-overview"/);
const hero=context.harness.selection();
hero.languageFocus={keys:['alpha'],selectionKey:'alpha',family:false,label:'Alpha',variant:'alpha',benchmark:'b1'};
hero.view='language';hero.languages=new Set(['alpha']);
assert.equal(context.harness.rankings().speed.reference_language,'alpha');
assert.equal(context.harness.rankings().speed.entries[0].sigma_distance,0);
context.harness.relativeTable();
const comparisonTable=element('#language-comparison-table tbody').innerHTML;
assert.match(comparisonTable,/Alpha · reference/);assert.match(comparisonTable,/1\.0×/);
assert.match(comparisonTable,/data-compare-language="mech"/,'Other variants remain listed even when filtered off.');
assert.ok(comparisonTable.indexOf('data-compare-language="beta"')<comparisonTable.indexOf('data-compare-language="mech"'));
context.harness.compareLanguage('beta');
assert.equal(hero.languageFocus.variant,'alpha');assert.equal(hero.languageFocus.label,'Alpha');
assert.equal(hero.languageFocus.comparisonLanguage,'beta');assert.deepEqual([...hero.languages],['alpha','beta']);
assert.deepEqual([...hero.benchmarks],['b1','b2']);
assert.equal(context.harness.rankings().speed.reference_language,'alpha','Pair comparisons preserve the hero origin.');
context.harness.resetLanguage();
assert.equal(hero.view,'language');assert.equal(hero.languageFocus.variant,'alpha');
assert.equal(hero.languageFocus.selectionKey,'alpha');assert.equal(hero.languageFocus.comparison,false);
assert.equal(context.harness.rankings().loc.reference_language,'alpha','Local reset preserves the hero origin.');
hero.languageFocus.variant='mech';
assert.equal(context.harness.rankings().speed.reference_language,'mech','Variant changes recenter both rankings.');
hero.languageFocus.variant='alpha';
context.harness.selectBenchmarks(['b2']);
assert.equal(hero.view,'language');assert.equal(hero.languageFocus.variant,'alpha');
context.harness.relativeTable();
assert.match(element('#language-comparisons-note').textContent,/Scope: Benchmark 2\./);
assert.doesNotMatch(element('#language-comparisons-note').textContent,/Benchmark 1/);
assert.match(element('#language-comparison-table tbody').innerHTML,/>1\/1<\/span>/);
context.harness.selectBenchmarks([]);context.harness.relativeTable();
assert.match(element('#language-comparison-table tbody').innerHTML,/data-compare-language="beta" disabled/);
assert.match(element('#language-comparison-table tbody').innerHTML,/<td class="ratio">—<\/td>/);
assert.equal(hero.view,'language');
hero.view='benchmark';hero.languageFocus.comparison=true;hero.languageFocus.comparisonProgram='alpha-b1-fast';
context.harness.selectBenchmarks(['b1','b2']);
assert.equal(hero.view,'language');assert.equal(hero.languageFocus.comparison,false);
assert.equal(hero.languageFocus.comparisonProgram,null);
context.harness.switchView('summary');
assert.equal(hero.view,'summary');assert.equal(hero.languageFocus,null);
assert.deepEqual([...hero.languages],fixture.languages.map(language=>language.key));
assert.deepEqual([...hero.benchmarks],['b1','b2']);
context.harness.overview();
assert.equal(element('#language-view-tab').hidden,false);
assert.equal(element('#language-view-tab').textContent,'Alpha');
context.harness.resetLanguage();assert.equal(hero.view,'summary');assert.equal(hero.languageFocus,null);
context.harness.switchView('language');
assert.equal(hero.view,'language');assert.equal(hero.languageFocus.variant,'alpha');
context.harness.selectBenchmarks(['b2']);context.harness.switchView('rankings');
assert.equal(hero.view,'rankings');assert.equal(hero.languageFocus,null);
assert.equal(context.harness.rankings().speed.reference_language,null,'Global Rankings retain the median origin.');
context.harness.resetLanguage();assert.equal(hero.languageFocus,null);
context.harness.switchView('language');
assert.equal(hero.view,'language');assert.equal(hero.languageFocus.variant,'alpha');
assert.deepEqual([...hero.benchmarks],['b2'],'The remembered hero retains its benchmark scope across global Reset.');
context.harness.switchView('summary');
console.log('Language hero: chart/results/table order, all-variant ratios, preserved target, local reset and separate All benchmarks tab passed.');
if(process.argv.includes('--language-view-only'))process.exit(0);
// Hover/focus brightens only existing sample marks, without moving them or
// changing the layer switches. Exit restores the hero's baseline emphasis.
context.harness.initialize(fixture);
for(const view of ['summary','language'])for(const sampleMode of ['off','dim','highlight']){
  context.harness.render({view,sampleMode,medianMode:'highlight',densityMode:'off',global:true,
    languageFocus:view==='language'?{keys:['alpha'],label:'Alpha',variant:'alpha'}:null});
  const svg=element('#chart'),samples=svg.querySelectorAll('[data-sample]');
  const layer=svg.querySelectorAll('[data-layer]').find(node=>node.dataset.layer==='samples');
  const medianLayer=svg.querySelectorAll('[data-layer]').find(node=>node.dataset.layer==='medians');
  assert.ok(layer.parentNode.children.indexOf(layer)<layer.parentNode.children.indexOf(medianLayer),'Background samples must not cover median hover targets.');
  const mark=view==='language'?svg.querySelectorAll('[data-median-language]').find(node=>node.dataset.medianLanguage==='alpha'):
    svg.querySelectorAll('[data-profile-median]').find(node=>node.dataset.chartLanguage==='alpha');
  assert.ok(mark,'Both the profile median and hero coordinate median are interactive.');
  const baseline=samples.map(node=>[sampleClass(node,'chart-dimmed'),sampleClass(node,'sample-highlighted')]);
  const positions=samples.map(node=>[node.getAttribute('cx'),node.getAttribute('cy')]);
  const baseOpacity=math.layerPresentation(sampleMode).opacity;
  for(const [enter,leave] of [['pointerenter','pointerleave'],['focus','blur']]){
    mark.emit(enter);
    assert.equal(svg.dataset.highlightLanguage,'alpha');
    assert.equal(Number(layer.getAttribute('opacity')),sampleMode==='off'?0:1);
    assert.equal(svg.querySelectorAll('[data-sample]').length,samples.length,'Hover cannot reveal Off samples or create points.');
    for(const node of samples){
      assert.equal(sampleClass(node,'sample-highlighted'),node.dataset.chartLanguage==='alpha');
      assert.equal(sampleClass(node,'chart-dimmed'),node.dataset.chartLanguage!=='alpha');
      assert.equal(inheritedStyle(node,'--chart-opacity'),String(baseOpacity));
    }
    assert.match(element('#hover-details').textContent,/Alpha/);
    for(const spread of svg.querySelectorAll('[data-hover-spread]')){
      assert.equal(spread.dataset.chartLanguage,'alpha');
      assert.equal(spread.classList.contains('chart-dimmed'),false,'New hover spreads belong to the highlighted language.');
    }
    assert.equal(element('#hover-details').style.getPropertyValue('left'),'','Details remain in the fixed readout.');
    assert.deepEqual(samples.map(node=>[node.getAttribute('cx'),node.getAttribute('cy')]),positions);
    mark.emit(leave);
    assert.equal(svg.dataset.highlightLanguage,undefined);
    assert.equal(Number(layer.getAttribute('opacity')),baseOpacity);
    assert.deepEqual(samples.map(node=>[sampleClass(node,'chart-dimmed'),sampleClass(node,'sample-highlighted')]),baseline);
    assert.equal(context.harness.selection().sampleMode,sampleMode);
  }
  mark.emit('pointerenter',{pointerType:'touch'});
  assert.equal(svg.dataset.highlightLanguage,undefined,'Touch does not leave a sticky hover state.');
  // Focus can switch directly between languages while the sample layer stays
  // lifted; both old and new indexed groups must update and then restore.
  const other=svg.querySelectorAll('[data-profile-median]').find(node=>node.dataset.chartLanguage==='beta');
  mark.emit('focus');other.emit('pointerenter');
  for(const node of samples){
    assert.equal(sampleClass(node,'sample-highlighted'),node.dataset.chartLanguage==='beta');
    assert.equal(sampleClass(node,'chart-dimmed'),node.dataset.chartLanguage!=='beta');
  }
  other.emit('pointerleave');assert.equal(svg.dataset.highlightLanguage,'alpha');
  mark.emit('blur');
  assert.deepEqual(samples.map(node=>[sampleClass(node,'chart-dimmed'),sampleClass(node,'sample-highlighted')]),baseline);
}

// A pointer burst publishes the final target once. Leaving one point for a
// second point in the same frame must not clear/dim the whole chart between.
context.harness.render({view:'summary',sampleMode:'dim',languageFocus:null});
const hoverChart=element('#chart'),hoverSamples=hoverChart.querySelectorAll('[data-sample]');
const alphaSamples=hoverSamples.filter(n=>n.dataset.chartLanguage==='alpha');
const betaMark=hoverChart.querySelectorAll('[data-profile-median]').find(n=>n.dataset.chartLanguage==='beta');
betaMark.emit('focus');autoFrames=false;
for(let i=0;i<200;i++){
  alphaSamples[i%alphaSamples.length].emit('pointerout');
  alphaSamples[(i+1)%alphaSamples.length].emit('pointerover');
}
assert.equal(frames.size,1,'Only one hover callback is queued per animation frame.');
assert.equal(hoverChart.dataset.highlightLanguage,'beta','The burst does no synchronous highlight writes.');
flushFrames();assert.equal(hoverChart.dataset.highlightLanguage,'alpha');
assert.equal(frames.size,0);
alphaSamples[0].emit('pointerout');flushFrames();
assert.equal(hoverChart.dataset.highlightLanguage,'beta','Keyboard focus survives pointer exit.');
assert.match(element('#hover-details').textContent,/beta/i,'Restored focus also restores its readout.');
alphaSamples[0].emit('pointerover');assert.equal(frames.size,1);
context.harness.render({sampleMode:'off'});
assert.equal(frames.size,0,'Replacing the plot cancels its pending hover callback.');
betaMark.emit('blur');betaMark.emit('pointerenter');
assert.equal(frames.size,0,'Late events from a retired marker cannot restart its hover queue.');
flushFrames();assert.equal(hoverChart.dataset.highlightLanguage,undefined);
assert.equal(hoverChart.querySelectorAll('[data-sample]').length,0);
autoFrames=true;
const facetFixture=structuredClone(fixture),names={b1:'binarytrees',b2:'nbody'};
for(const b of facetFixture.benchmarks)b.key=names[b.key];
for(const p of Object.values(facetFixture.programs))p.benchmark=names[p.benchmark];
context.harness.initialize(facetFixture);
context.harness.render({view:'language',languageFocus:{keys:['alpha'],selectionKey:'alpha',family:false,label:'Alpha',variant:'alpha',benchmark:'nbody'},global:true});
context.harness.selectBenchmarkFacet('resource','memory',true);
assert.deepEqual([...context.harness.effectiveBenchmarks()],['binarytrees']);
assert.equal(context.harness.selection().view,'language','Facets preserve the language hero.');
context.harness.relativeTable();
assert.match(element('#language-comparisons-note').textContent,/Scope: Benchmark 1\./);
const saved=context.harness.savedSelection();
context.harness.selectBenchmarkFacet('workload','numerical',true);
assert.equal(context.harness.effectiveBenchmarks().size,0);
assert.equal(saved.benchmarkFilters.workload.size,0,'Saved hero filters must not share mutable sets.');
context.harness.relativeTable();
assert.match(element('#language-comparisons-note').textContent,/no benchmarks selected/);
context.harness.selectBenchmarks(['nbody'],{clearFilters:true});
assert.deepEqual([...context.harness.effectiveBenchmarks()],['nbody']);
context.harness.selectBenchmarkFacet('resource','memory',true);
context.harness.selectBenchmarkFacet('resource','memory',false);
assert.deepEqual([...context.harness.effectiveBenchmarks()],['nbody'],'Clearing a facet preserves manual exclusions.');
context.harness.selectBenchmarkFacet('resource','memory',true);context.harness.resetLanguage();
assert.equal(context.harness.selection().benchmarkFilters.resource.size,0);
assert.equal(context.harness.selection().languageFocus.variant,'alpha');
assert.equal(context.harness.selection().view,'language');
// The same subset must fit the same axes whether chosen by checkbox or facet.
// A large excluded workload gap makes an unfiltered geometric mean too small.
const domainFixture=structuredClone(facetFixture);
for(const p of Object.values(domainFixture.programs)){
  const value=p.benchmark==='binarytrees'?(p.language==='beta'?2**20:4):1;
  Object.assign(p,{x:value,y:value,loc:value,seconds:value,samples:[value,value,value]});
}
context.harness.initialize(domainFixture);
for(const mode of ['summary','language','source-comparison']){
  Object.assign(context.harness.selection(),{view:mode==='language'?'language':'summary',focusMeans:true,
    languageFocus:mode==='summary'?null:{keys:['alpha'],label:'Alpha',variant:'alpha',comparison:mode==='source-comparison',
      comparisonProgram:mode==='source-comparison'?'alpha-b1-fast':null}});
  context.harness.selectBenchmarks(['binarytrees'],{clearFilters:true});
  const manual=context.harness.domain();
  context.harness.selectBenchmarks(['binarytrees','nbody']);
  const full=context.harness.domain();
  context.harness.selectBenchmarkFacet('resource','memory',true);
  assert.deepEqual(context.harness.domain(),manual,`${mode}: facet and manual subsets must share the fitted domain.`);
  assert.ok(manual.xMax>full.xMax&&manual.yMax>full.yMax,'The fixture must expose an undersized full-suite mean range.');
}
assert.match(html,/id="benchmark-groups"/);assert.match(html,/id="benchmark-filter-status" aria-live="polite"/);
assert.match(css,/#filter-drawer \.control-row,#filter-drawer \.trait-choice\{min-height:44px\}/);
// Reuse measured derivations for visual-only edits, then invalidate them for
// every selection boundary. Exercise the real update/updatePlot paths without
// rebuilding unrelated synthetic controls or requiring a browser.
const cacheFixture=structuredClone(facetFixture);
for(const b of cacheFixture.benchmarks)b.baseline_formatted_loc=1;
for(const p of Object.values(cacheFixture.programs))Object.assign(p,{formatted_loc:p.loc*3,formatted_x:p.x*3,formatted_loc_status:'qualified',formatted_loc_complete:true});
context.harness.formatting(true);context.harness.initialize(cacheFixture);
context.harness.render({view:'summary',languageFocus:null,locMetric:'canonical',focusMeans:true,global:false,fast:true,small:true,
  disabled:new Set(),sampleMode:'dim',medianMode:'highlight',densityMode:'off'});
const initial=context.harness.derived();
const originalSampleLayer=element('#chart').querySelectorAll('[data-layer]').find(node=>node.dataset.layer==='samples');
const initialSampleNodes=element('#chart').querySelectorAll('[data-sample]');
const initialByKey=new Map(initialSampleNodes.map(node=>[`${node.dataset.program}:${node.dataset.timingRun}`,node]));
for(const options of [{sampleMode:'off'},{sampleMode:'highlight',densityMode:'highlight'},{densityMode:'dim',medianMode:'off'},{global:true}]){
  context.harness.visual(options);
  const next=context.harness.derived();
  assert.equal(next.model,initial.model);assert.equal(next.samples,initial.samples);
  assert.equal(next.density,initial.density,'Opacity and layer visibility reuse the identical density estimator.');
  const visibleSamples=element('#chart').querySelectorAll('[data-sample]');
  if(options.sampleMode==='off'){
    assert.equal(visibleSamples.length,0);assert.ok(initialSampleNodes.every(node=>node.parentNode===null));
  }else for(const node of visibleSamples)assert.equal(node,initialByKey.get(`${node.dataset.program}:${node.dataset.timingRun}`));
}
assert.equal(originalSampleLayer.children.length,0,'The circle cache must not retain its old SVG parent.');
assert.ok(context.harness.cachedSamples().every(record=>Object.values(record).every(value=>value instanceof Element||typeof value==='string'||typeof value==='number')),
  'Persistent sample records retain only a circle and scalar display values, never old models or handlers.');
assert.ok(initialSampleNodes.every(node=>Object.keys(node.listeners).length===0),'Sample callbacks belong to the fresh parent layer.');
const sampleFor=(program,run=1)=>element('#chart').querySelectorAll('[data-sample]').find(node=>node.dataset.program===program&&Number(node.dataset.timingRun)===run);
const assertSampleActions=(node,program)=>{
  node.emit('pointerover');assert.equal(element('#chart').dataset.highlightLanguage,node.dataset.chartLanguage);
  assert.ok(element('#hover-details').textContent.includes(program));
  node.emit('pointerout');assert.equal(element('#chart').dataset.highlightLanguage,undefined);
  node.emit('focusin');assert.equal(element('#chart').dataset.highlightLanguage,node.dataset.chartLanguage);
  assert.ok(element('#hover-details').textContent.includes(`${Number(node.dataset.runSeconds).toFixed(3)} s`));
  for(const [type,event] of [['click',{}],['keydown',{key:'Enter'}],['keydown',{key:' '}]]){
    const result=context.harness.sampleAction(node,type,event);
    assert.equal(result.calls.length,1);assert.equal(result.calls[0].program,program);
    if(type==='keydown')assert.equal(result.prevented,true);
  }
  node.emit('focusout');assert.equal(element('#chart').dataset.highlightLanguage,undefined);
};
assertSampleActions(sampleFor('alpha-b1-fast'),'alpha-b1-fast');
context.harness.visual({sampleMode:'off'});
assert.equal(element('#chart').querySelectorAll('[data-sample]').length,0);
assert.ok(initialSampleNodes.every(node=>node.parentNode===null));
context.harness.visual({sampleMode:'dim'});
assert.equal(sampleFor('alpha-b1-fast'),initialByKey.get('alpha-b1-fast:1'));
assertSampleActions(sampleFor('alpha-b1-fast'),'alpha-b1-fast');
context.harness.selectBenchmarkFacet('resource','memory',true);context.harness.selectionUpdate({});
const filtered=context.harness.derived();
assert.notEqual(filtered.model,initial.model);assert.notEqual(filtered.samples,initial.samples);assert.notEqual(filtered.density,initial.density);
assert.ok(filtered.samples.length<initial.samples.length);assert.ok(filtered.samples.every(point=>point.benchmark.key==='binarytrees'));
context.harness.selectionUpdate({disabled:new Set(['alpha-b1-fast'])});
const disabled=context.harness.derived();
assert.ok(disabled.samples.every(point=>point.program.key!=='alpha-b1-fast'));assert.notEqual(disabled.samples,filtered.samples);
context.harness.selectionUpdate({view:'language',languageFocus:{keys:['alpha'],label:'Alpha',variant:'alpha'},disabled:new Set()});
const heroCache=context.harness.derived();assert.notEqual(heroCache.samples,disabled.samples);
const heroSample=sampleFor('alpha-b1-fast');assert.equal(heroSample,initialByKey.get('alpha-b1-fast:1'));
assertSampleActions(heroSample,'alpha-b1-fast');
context.harness.selectionUpdate({locMetric:'formatted'});
const formattedCache=context.harness.derived();assert.notEqual(formattedCache.model,heroCache.model);
assert.equal(formattedCache.samples.length,heroCache.samples.length);
assert.deepEqual(formattedCache.samples.map(point=>point.x),heroCache.samples.map(point=>point.x*3));
assert.deepEqual(formattedCache.samples.map(point=>point.elapsed),heroCache.samples.map(point=>point.elapsed));
const formattedSample=sampleFor('alpha-b1-fast');assert.equal(formattedSample,heroSample);
assert.equal(Number(formattedSample.dataset.ratioX),cacheFixture.programs['alpha-b1-fast'].x*3);
assert.ok(formattedSample.getAttribute('aria-label').includes(`${cacheFixture.programs['alpha-b1-fast'].loc*3} LOC`));
assertSampleActions(formattedSample,'alpha-b1-fast');
context.harness.compare('alpha-b1-fast');context.harness.selectionUpdate({view:'benchmark',focus:'binarytrees'});
const sourceCache=context.harness.derived();
context.harness.visual({sampleMode:'dim',medianMode:'highlight'});
assert.equal(context.harness.derived().view,sourceCache.view,'Source comparisons retain their formatted projection identity.');
assert.equal(context.harness.derived().samples,sourceCache.samples);
context.harness.compare('alpha-b1-small');context.harness.selectionUpdate({});
assert.notEqual(context.harness.derived().view,sourceCache.view,'Changing the explicit source replaces its projection.');
context.harness.selectionUpdate({languageFocus:null},true);
const resetCache=context.harness.derived();
assert.equal(context.harness.selection().locMetric,'canonical');assert.equal(context.harness.selection().disabled.size,0);
assert.deepEqual([...context.harness.effectiveBenchmarks()],['binarytrees','nbody']);
assert.equal(resetCache.samples.length,initial.samples.length);assert.notEqual(resetCache.samples,initial.samples);
const resetSample=sampleFor('alpha-b1-fast');assert.equal(resetSample,heroSample);
assert.equal(Number(resetSample.dataset.ratioX),cacheFixture.programs['alpha-b1-fast'].x);
assert.equal(context.harness.cachedSamples().length,initialSampleNodes.length,'Filtering and LOC changes cannot duplicate recorded run nodes.');
assertSampleActions(resetSample,'alpha-b1-fast');

// Density contrast does not change the estimator or foreground. Exercise the
// same setter used by the controls and public interaction API, including the
// fallback when visibility, another layer or the chart width also changes.
const densityLayer=()=>element('#chart').querySelectorAll('[data-layer]').find(node=>node.dataset.layer==='density');
context.harness.layerModes({density:'highlight'});
const heat=densityLayer(),heatCells=[...heat.children],contrastSample=sampleFor('alpha-b1-fast');
const contrastChartChildren=[...element('#chart').children],contrastField=context.harness.derived().density;
const contrastDomain=Object.fromEntries(['xMin','xMax','yMin','yMax'].map(key=>[key,element('#chart').dataset[key]]));
contrastSample.emit('focusin');
const focusedDescription=element('#hover-details').textContent;
for(const mode of ['dim','highlight']){
  context.harness.layerModes({density:mode});
  assert.equal(densityLayer(),heat);assert.ok(heat.children.every((node,index)=>node===heatCells[index]));
  assert.equal(element('#chart').children.length,contrastChartChildren.length);
  assert.ok(element('#chart').children.every((node,index)=>node===contrastChartChildren[index]),'Density contrast preserves the full chart tree.');
  assert.equal(heat.getAttribute('opacity'),String(math.layerPresentation(mode).opacity));
  assert.equal(heat.dataset.layerMode,mode);assert.equal(element('#show-density').value,mode);
  assert.equal(context.harness.derived().density,contrastField);
  assert.equal(element('#chart').dataset.highlightLanguage,'alpha');
  assert.equal(element('#hover-details').textContent,focusedDescription);
  assert.deepEqual(Object.fromEntries(['xMin','xMax','yMin','yMax'].map(key=>[key,element('#chart').dataset[key]])),contrastDomain);
}
contrastSample.emit('focusout');
assertSampleActions(contrastSample,'alpha-b1-fast');
context.harness.layerModes({density:'off'});
assert.equal(densityLayer(),undefined,'Off removes the density layer.');
context.harness.layerModes({density:'dim'});
const beforeOtherLayer=densityLayer();
context.harness.layerModes({density:'highlight',samples:'off'});
assert.notEqual(densityLayer(),beforeOtherLayer,'Simultaneous layer changes use a complete render.');
assert.equal(element('#chart').querySelectorAll('[data-sample]').length,0,'Samples Off stays absent.');
const beforeResize=densityLayer();element('#chart').clientWidth=900;
context.harness.layerModes({density:'dim'});
assert.notEqual(densityLayer(),beforeResize,'A pending width change cannot use the contrast-only path.');
assert.match(element('#chart').getAttribute('viewBox'),/^0 0 900 /);
element('#chart').clientWidth=1000;
context.harness.layerModes({density:'off',samples:'dim'});

// Selection updates render only visible results. Reset on global Rankings
// applies its final destination before the single update; hero Reset retains
// the selected language and still renders its scatter plot once.
const beforeRankings=[...element('#chart').children];
const rankingsWork=context.harness.updateWork({view:'rankings',languageFocus:null});
assert.equal(rankingsWork.chart,0);assert.equal(rankingsWork.table,0);
assert.deepEqual(element('#chart').children,beforeRankings,'Rankings does not rebuild its hidden scatter plot.');
const resetRankingsWork=context.harness.updateWork({},{rankingsReset:true});
assert.equal(resetRankingsWork.controls,1);assert.equal(resetRankingsWork.rankings,1);assert.equal(resetRankingsWork.chart,0);
assert.equal(context.harness.selection().view,'rankings');
const focusedHero={keys:['alpha'],selectionKey:'alpha',family:false,label:'Alpha',variant:'alpha',benchmark:'binarytrees'};
const heroWork=context.harness.updateWork({view:'language',languageFocus:focusedHero});
assert.equal(heroWork.chart,1);assert.equal(heroWork.table,0,'The hidden aggregate table is not rebuilt in a language page.');
const resetHeroWork=context.harness.updateWork({},{rankingsReset:true});
assert.equal(resetHeroWork.controls,1);assert.equal(resetHeroWork.rankings,1);assert.equal(resetHeroWork.chart,1);assert.equal(resetHeroWork.table,0);
assert.equal(context.harness.selection().view,'language');assert.equal(context.harness.selection().languageFocus.variant,'alpha');
assert.equal(context.harness.globalRequests({view:'language',global:true}),0,'Language overlays use their own statistics, not an unused global covariance.');
assert.equal(context.harness.globalRequests({view:'summary',languageFocus:null,global:false}),0);
assert.equal(context.harness.globalRequests({global:true,fast:false,small:false}),0,'Hidden profiles need no global covariance.');
assert.equal(context.harness.globalRequests({global:true,fast:true,small:true}),1);
const visibleSummary=context.harness.updateWork({global:false});
assert.equal(visibleSummary.chart,1);assert.equal(visibleSummary.table,1,'Returning to summary refreshes both visible results.');
console.log('Render scope: hidden results, single reset, conditional global covariance and density contrast identity passed.');
context.harness.formatting(false);
console.log('Median hover/focus and benchmark facets: visible samples, Off, static readout, restoration, hero scope and reset passed.');
if(process.argv.includes('--interactions-only'))process.exit(0);
// The navigation tests exercise the real Reset default (nbody). Restore the
// synthetic fixture's benchmark identity before the exhaustive render matrix.
context.harness.initialize(fixture);
const modes=['off','dim','highlight'];
let mathCases=0,renderCases=0;
for(const samples of modes)for(const medians of modes)for(const density of modes)for(const global of [false,true])for(const fast of [false,true])for(const small of [false,true]){
  const state=math.chartLayerState({samples,medians,density,global,fast,small,sampleCount:6,entryCount:3});
  assert.equal(state.showSamples,samples!=='off'&&(fast||small));assert.equal(state.showDensity,density!=='off'&&(fast||small));
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
// Profile controls select one observation set for dots, program medians and
// density. Layer Off/Dim/Highlight changes presentation without changing it.
for(const view of ['summary','benchmark','mech','language'])for(const fast of [false,true])for(const small of [false,true]){
  let selectedSamples=null,selectedDensity=null;
  for(const sampleMode of modes)for(const medianMode of modes){
    context.harness.render({view,fast,small,sampleMode,medianMode,densityMode:'highlight',global:true,
      languageFocus:view==='language'?{keys:['alpha'],label:'Alpha',variant:'alpha'}:null});
    const derived=context.harness.derived(),svg=element('#chart');
    const programs=new Set(derived.entries.flatMap(entry=>entry.inputs.flatMap(input=>
      [fast?input.fast:null,small?input.small:null].filter(Boolean).map(program=>program.key))));
    const runs=derived.samples.map(point=>`${point.program.key}:${point.run}`);
    assert.equal(runs.length,programs.size*3,`${view}: each active endpoint contributes its three runs`);
    assert.ok(derived.samples.every(point=>programs.has(point.program.key)));
    if(selectedSamples===null){selectedSamples=derived.samples;selectedDensity=derived.density;}
    else{assert.equal(JSON.stringify(derived.samples.map(point=>`${point.program.key}:${point.run}`)),JSON.stringify(selectedSamples.map(point=>`${point.program.key}:${point.run}`)));assert.equal(JSON.stringify(derived.density),JSON.stringify(selectedDensity));}
    assert.equal(derived.density.runs,runs.length,`${view}: density uses the active observation set`);
    assert.equal(derived.density.programs,programs.size);
    const visible=svg.querySelectorAll('[data-sample]');
    assert.equal(visible.length,sampleMode==='off'?0:runs.length);
    assert.ok(visible.every(mark=>programs.has(mark.dataset.program)));
    for(const mark of svg.querySelectorAll('[data-profile-median]')){
      if(mark.dataset.program)assert.ok(programs.has(mark.dataset.program));
      if(mark.dataset.mean)continue;
      assert.ok(fast||small);
    }
    const heat=svg.querySelectorAll('[data-layer]').find(mark=>mark.dataset.layer==='density');
    assert.equal(Number(heat.dataset.densityRuns),runs.length);
  }
}
// Revisit the same entries without rebuilding the model: cached profile masks
// must change observations and density, while re-enabling reuses the first set.
context.harness.render({view:'summary',fast:true,small:true,sampleMode:'highlight',medianMode:'highlight',densityMode:'highlight',global:false,languageFocus:null});
const bothProfiles=context.harness.derived();
context.harness.visual({fast:false});const fewestOnly=context.harness.derived();
assert.equal(fewestOnly.model,bothProfiles.model);assert.notEqual(fewestOnly.samples,bothProfiles.samples);
assert.equal(fewestOnly.samples.length,bothProfiles.samples.length/2);assert.equal(fewestOnly.density.runs,fewestOnly.samples.length);
context.harness.visual({fast:true,small:false});const fastestOnly=context.harness.derived();
assert.equal(fastestOnly.samples.length,bothProfiles.samples.length/2);
assert.ok(fastestOnly.samples.every(point=>point.program.key.endsWith('-fast')));
assert.ok(fewestOnly.samples.every(point=>point.program.key.endsWith('-small')));
context.harness.visual({fast:false});assert.equal(context.harness.derived().samples.length,0);assert.equal(context.harness.derived().density.runs,0);
context.harness.visual({fast:true,small:true});assert.equal(context.harness.derived().samples,bothProfiles.samples);
console.log('Profile selection: samples, medians and density follow the active endpoint union in all four chart views.');
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
// Explicit shared timing observations are distinct from independently timed
// source aliases, even when every sample and source coordinate is equal.
const owner={...fixture.programs['alpha-b1-fast'],files:['source'],physical_loc:2,timing_sd:0.2,
  report:'synthetic/report.json',native_observations:3,formatted_loc:null,formatted_x:null,
  formatted_loc_status:'unavailable',formatted_loc_complete:false,samples:[2,2,2]};
const alias={...owner,key:'alpha-b1-alias',id:'alias',timing_alias_of:owner.key,
  source_alias_of:owner.key,aliased_sample_source:owner.key,native_observations:0};
const independent={...owner,key:'alpha-b1-independent',id:'independent',source_alias_of:owner.key};
const bench={...fixture.benchmarks[0],groups:[{language:'alpha',programs:[owner.key]}]};
const entry={language:{key:'alpha'},inputs:[{benchmark:bench,programs:[alias,owner,independent]}]};
const shared=math.recordedSamplePoints([entry]);
assert.equal(shared.length,6);assert.ok(shared.slice(0,3).every(p=>p.program===owner));
assert.deepEqual(shared.map(p=>p.observation_source),[...Array(3).fill(owner.key),...Array(3).fill(independent.key)]);
assert.deepEqual(math.observationSummary([alias,owner,independent]),{timingOwners:2,runs:6});
const allAliasSamples=math.recordedSamplePoints([{...entry,inputs:[{benchmark:bench,programs:[alias]}]}]);
assert.equal(allAliasSamples.length,3);assert.ok(allAliasSamples.every(p=>p.program===alias));
const density=math.sampleDensityPoints([...allAliasSamples,...shared]);
assert.equal(density.length,6);assert.equal(density.reduce((n,p)=>n+p.weight,0),6);
assert.equal(new Set(density.map(p=>p.program)).size,2);
assert.equal(math.densityGrid(density,{xMin:0,xMax:4,yMin:0,yMax:4}).runs,6);
assert.equal(math.recordedSamplePoints([entry],{disabled:new Set([owner.key,independent.key])}).length,3);
assert.equal(math.recordedSamplePoints([entry],{disabled:new Set([alias.key])}).length,6);
assert.equal(math.recordedSamplePoints([entry],{samples:false}).length,0);
assert.equal(math.recordedSamplePoints([{...entry,inputs:[{benchmark:bench,programs:[{...owner,eligible_for_chart:false},alias]}]}]).length,3);
const aliasFixture={languages:[fixture.languages[1]],benchmarks:[bench],programs:{[owner.key]:owner},
  program_inventory:{[alias.key]:alias,[independent.key]:independent},
  files:{source:{name:'main.apl',path:'retained/main.apl',sha256:'a'.repeat(64),code:'1+1\n'}}};
context.harness.initialize(aliasFixture);
const aliasView={view:'language',languageFocus:{keys:['alpha'],label:'Alpha',variant:'alpha',benchmark:'b1'},
  sampleMode:'dim',medianMode:'highlight',densityMode:'highlight',global:false,disabled:new Set(),locMetric:'canonical'};
context.harness.render(aliasView);context.harness.overview();
assert.match(element('#language-overview-summary').textContent,/3 programs · 6 recorded runs/);
assert.match(element('#language-timings tbody').innerHTML,/Reuses the 3 runs recorded for/);
const sampleMarks=()=>element('#chart').querySelectorAll('[data-sample]');
assert.equal(sampleMarks().length,6);
context.harness.visual({fast:false,small:true});assert.equal(sampleMarks().length,6,'Independent tied timings stay selected by the shared fewest-LOC endpoint.');
assert.equal(context.harness.derived().density.runs,6);
context.harness.visual({fast:false,small:false});assert.equal(sampleMarks().length,0);assert.equal(context.harness.derived().density.runs,0);
context.harness.visual({fast:true,small:false});assert.equal(sampleMarks().length,6,'The same independent observations also belong to the tied fastest endpoint.');
context.harness.visual({fast:true,small:true});
assert.ok(sampleMarks().every(n=>n.dataset.program!==alias.key),'Owner wins even when alias precedes it in the inventory.');
context.harness.inspect(alias.key);
assert.match(element('#inspector-body').innerHTML,/Shared recorded timing samples/);
assert.match(element('#inspector-body').innerHTML,/shared median time/);
assert.match(element('#inspector-body').innerHTML,/no additional runs/);
assert.ok(element('#inspector-body').innerHTML.includes(`data-inspect-program="${owner.key}"`));
context.harness.inspect(independent.key);
assert.match(element('#inspector-body').innerHTML,/Its recorded timings are independent/);
assert.doesNotMatch(element('#inspector-body').innerHTML,/Shared recorded timing samples/);
context.harness.render({...aliasView,view:'benchmark',focus:'b1',languageFocus:{...aliasView.languageFocus,comparison:true,comparisonProgram:alias.key}});
assert.equal(sampleMarks().length,3);assert.ok(sampleMarks().every(n=>n.dataset.program===alias.key));
for(const mark of sampleMarks()){
  assert.equal(mark.dataset.observationSource,owner.key);
  assert.match(mark.getAttribute('aria-label'),/shared from alpha-b1-fast/);
  assert.equal(context.harness.sampleAction(mark,'keydown',{key:'Enter'}).calls[0].program,alias.key);
}
const aliasNodes=sampleMarks();
context.harness.visual({sampleMode:'off'});assert.equal(sampleMarks().length,0);
assert.equal(context.harness.derived().density.runs,3,'Density retains shared observations with sample dots Off.');
context.harness.visual({sampleMode:'dim'});assert.deepEqual(sampleMarks(),aliasNodes);
context.harness.render({...aliasView,disabled:new Set()});assert.equal(sampleMarks().length,6);
const ownerMark=sampleMarks().find(n=>n.dataset.program===owner.key);
assert.equal(context.harness.sampleAction(ownerMark,'click').calls[0].program,owner.key,'Reused owner markers route to their current source.');
context.harness.formatting(true);context.harness.render({...aliasView,locMetric:'formatted'});
assert.equal(sampleMarks().length,0,'Unavailable formatted coordinates must not be invented for either alias.');
context.harness.overview();assert.match(element('#language-overview-summary').textContent,/6 recorded runs/);
context.harness.formatting(false);
console.log('Timing aliases: explicit owner/run deduplication, equal independent samples, disclosure, density, Off and source actions passed.');
// The saved Pony audit groups line entries by source, including the counted Pi helper.
const recorded=JSON.parse(fs.readFileSync(new URL('../../data/benchmarks.json',import.meta.url),'utf8'));
context.harness.initialize(recorded);
const recordedCatalog={...recorded.program_inventory,...recorded.programs};
const actualTimingAliases=Object.values(recordedCatalog).filter(program=>program.timing_alias_of);
assert.ok(actualTimingAliases.length>=3,'The retained catalog includes its three original explicit timing aliases.');
for(const program of actualTimingAliases){
  const projected=formatted.projectProgram(program,'formatted');
  for(const field of ['timing_alias_of','source_alias_of','aliased_sample_source','native_observations'])
    assert.deepEqual(projected[field],program[field],`Formatted projection preserves ${field}.`);
}
const hasAPLTree=!!recordedCatalog['binarytrees:apl-workspace200-compact'];
for(const [key,labels,runs] of [['apl',hasAPLTree?19:17,hasAPLTree?48:45],['uiua',17,48]]){
  context.harness.render({view:'language',languageFocus:{keys:[key],label:recorded.languages.find(l=>l.key===key).label,
    variant:key,benchmark:'nbody'},languages:new Set([key]),disabled:new Set(),locMetric:'canonical',
    sampleMode:'dim',medianMode:'off',densityMode:'highlight',global:false});
  context.harness.overview();
  assert.ok(element('#language-overview-summary').textContent.includes(`${labels} programs · ${runs} recorded runs`));
  // The retained timing table includes every implementation. The chart's
  // profiles exclude this measured source, which is neither endpoint.
  const other=recordedCatalog[key==='apl'?'mandelbrot:mandelbrot-apl-active-v2-optimized':'nbody:nbody-uiua-native-denominator-compact-v3'];
  assert.equal(other.samples.length,3);
  assert.equal(sampleMarks().length,runs-other.samples.length,`${key} hero plots each active native observation once.`);
  assert.ok(sampleMarks().every(mark=>mark.dataset.program!==other.key));
  assert.equal(context.harness.derived().density.runs,runs-other.samples.length);
}
for(const key of ['kotlin','prolog']){
  const programs=Object.values(recordedCatalog).filter(p=>p.language===key&&p.seconds>0);
  assert.ok(programs.some(p=>p.source_alias_of));
  assert.ok(programs.every(p=>!p.timing_alias_of));
  assert.equal(math.observationSummary(programs).runs,programs.reduce((n,p)=>n+p.samples.length,0),`${key} source aliases retain their independent runs.`);
}
context.harness.initialize(recorded);
Object.assign(context.harness.selection(),{view:'summary',languageFocus:null,disabled:new Set(),locMetric:'canonical'});
const pony=Object.values(recorded.program_inventory).filter(program=>program.language==='pony');
assert.equal(pony.length,20);
let helperLinks=0;
for(const program of pony){
  const audit=context.harness.locAudit(program);
  assert.doesNotMatch(audit,/undefined|\[object Object\]/);
  if(program.source_accounting){
    assert.match(audit,/application LOC/);
    assert.ok(audit.includes(`Previous count: ${program.source_accounting.previous_loc} LOC`));
    assert.ok(audit.includes('aliases.pony')&&audit.includes('5 normalized LOC'));
  }else{
    assert.match(audit,/normalized LOC \(retained rules\)/);
    for(const source of program.loc_expansions){
      for(const entry of source.expansions)assert.ok(audit.includes(`Line ${entry.line} · ${entry.units} normalized LOC (retained rules)`));
    }
  }
  for(const key of program.files){
    const source=context.harness.programSource(program,key);
    assert.equal(source.role,program.file_roles[key].role);
    assert.equal(decodeURI(source.source_url),recorded.repository.url+'/blob/main/'+program.file_roles[key].source_path);
    if(source.role==='application-helper'||source.role==='runtime-support'){
      helperLinks++;
      assert.notEqual(source.source_url,program.source_url);
      assert.match(audit,source.role==='runtime-support'?/support excluded/:/application helper/);
      assert.ok(source.loc_note);
    }
  }
}
assert.equal(helperLinks,2);
// Elixir retains every source while separating reusable support and launcher
// from both normalized and formatted application LOC, including source aliases.
const elixir=Object.values(recorded.program_inventory).filter(program=>program.language==='elixir');
assert.equal(elixir.length,20);
for(const program of elixir){
  assert.equal(program.samples.length,3);
  assert.equal(program.eligible_for_chart,true);
  assert.equal(program.formatted_loc_status,'qualified');
  assert.deepEqual(program.files.map(key=>program.file_roles[key].role),
    ['application','runtime-support','runtime-support']);
  assert.equal(program.loc+62,program.source_accounting.previous_loc);
  assert.equal(program.formatted_loc+69,program.source_accounting.previous_formatted_loc);
  for(const key of program.files){
    const source=context.harness.programSource(program,key);
    assert.equal(source.role,program.file_roles[key].role);
    assert.equal(decodeURI(source.source_url),recorded.repository.url+'/blob/main/'+program.file_roles[key].source_path);
  }
  context.harness.inspect(program.key);
  const detail=element('#inspector-body').innerHTML;
  assert.doesNotMatch(detail,/undefined|\[object Object\]/);
  assert.match(detail,/support \(excluded\)/);
  assert.match(detail,/62 normalized LOC/);
  assert.match(detail,/3 samples/);
  assert.match(detail,/best-comparison/);
}
// Ranked interpreted observations must be the saved outer wall interval, even
// though historical diagnostic details still retain their internal phase.
const interpreted=Object.values(recorded.program_inventory).filter(program=>program.language==='mech-resident');
assert.equal(interpreted.length,15);
for(const program of interpreted){
  assert.deepEqual(program.samples,program.sample_details.map(sample=>sample.wall_seconds));
  assert.notDeepEqual(program.samples,program.sample_details.map(sample=>sample.kernel_seconds));
  context.harness.inspect(program.key);
  const detail=element('#inspector-body').innerHTML;
  assert.match(detail,/Whole process seconds/);
  assert.doesNotMatch(detail,/Measured seconds|undefined|\[object Object\]/);
  for(const value of program.samples)assert.ok(detail.includes(`<td class="sample-value">${value.toFixed(6)}</td>`));
}
// A successful subject with a failed matched control remains inspectable, but
// neither inventory selection nor the language-view renderer may chart it.
const excludedFixture=structuredClone(fixture);
excludedFixture.files={source:{name:'main.ex',path:'retained/main.ex',sha256:'a'.repeat(64),code:'IO.puts(1)\n'}};
const excluded={...excludedFixture.programs['alpha-b1-fast'],key:'alpha-b1-excluded',id:'excluded',files:['source'],
  eligible_for_chart:false,exclusion_reason:'Matched control failed.',timing_sd:0.2,report:'synthetic/report.json',
  physical_loc:1,formatted_loc:2,formatted_loc_status:'qualified',formatted_loc_complete:true,formatted_x:2};
excludedFixture.program_inventory={[excluded.key]:excluded};
context.harness.initialize(excludedFixture);
const compared=context.harness.compare(excluded.key),excludedGroup=compared.benchmarks[0].groups.find(g=>g.language==='alpha');
assert.equal(excludedGroup.programs.length,0);
assert.equal(excludedGroup.fast,null);assert.equal(excludedGroup.small,null);
assert.equal(excludedGroup.formatted_fast,null);assert.equal(excludedGroup.formatted_small,null);
context.harness.render({view:'language',languageFocus:{keys:['alpha'],label:'Alpha'},global:true,sampleMode:'highlight',medianMode:'highlight',densityMode:'highlight'});
assert.ok(element('#chart').querySelectorAll('[data-program]').every(node=>node.dataset.program!==excluded.key));
context.harness.inspect(excluded.key);
assert.match(element('#inspector-body').innerHTML,/Excluded from charts and comparisons/);
assert.match(element('#inspector-body').innerHTML,/Matched control failed/);
assert.match(element('#inspector-body').innerHTML,/3 samples/);
assert.doesNotMatch(element('#inspector-body').innerHTML,/best-comparison/);
assert.equal(element('#source-code').textContent,excludedFixture.files.source.code);
excluded.seconds=null;excluded.timing_sd=null;excluded.samples=[1,2];excluded.exclusion_reason='Failed third sample.';
context.harness.inspect(excluded.key);
assert.match(element('#inspector-body').innerHTML,/No qualified timing median/);
assert.match(element('#inspector-body').innerHTML,/2 samples/);
assert.doesNotMatch(element('#inspector-body').innerHTML,/undefined|\[object Object\]/);
console.log(`Passed ${mathCases} layer combinations and ${renderCases} SVG renders across summary, benchmark, Mech and language views; alphabetical table, fixed axes, independent playback, trail removal, ${pony.length} Pony source audits and ${elixir.length} Elixir inspectors.`);
