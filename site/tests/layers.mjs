import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as math from '../src/math.mjs';
import * as formatted from '../src/formatted_axis.mjs';

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
const context=vm.createContext({...math,...formatted,document,window:{},innerWidth:1000,
  matchMedia:()=>({matches:false,addEventListener(){}}),emptyTraitFilters:()=>({}),filterLanguageKeys:keys=>new Set(keys),
  axisData:data=>data,projectProgram:program=>program,console,Set,Map,
  setTimeout:()=>0,clearTimeout(){}});
const executable=source.replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'file:///test/app.mjs'")
  .replace(/start\(\)\.catch\(error=>\{[^\n]+\}\);\s*$/,'');
vm.runInContext(executable+`\nglobalThis.harness={
  initialize(fixture){data=fixture;programCatalog={...fixture.program_inventory,...fixture.programs};Object.assign(state,{benchmarks:new Set(fixture.benchmarks.map(b=>b.key)),languages:new Set(fixture.languages.map(l=>l.key)),releaseYearStart:1960,releaseYear:2026,focus:'b1'});for(const l of fixture.languages)colors[l.key]='#f6c04e';},
  render(options){Object.assign(state,options);model=comparison(data,allSelection());renderChart();},
  table(){renderTable();},
  locAudit:renderLocAudit,
  programSource,
  compare(key){state.languageFocus={keys:[catalogProgram(key).language],comparison:true,comparisonProgram:key};return comparisonData();},
  inspect(key){state.detail={...state.detail,program:key};const original=renderLanguageOverview,originalRankings=renderMedianRankings;renderLanguageOverview=renderMedianRankings=()=>{};try{renderInspector();}finally{renderLanguageOverview=original;renderMedianRankings=originalRankings;}},
  selection(){return state;},
  relativeTable(){renderLanguageComparisons();},
  rankings(){model=comparison(data,allSelection());return currentRankings();},
  overview(){renderLanguageOverview();},
  resetLanguage(){const original=update;update=()=>{};try{reset();}finally{update=original;}},
  compareLanguage(key){const original=update;update=()=>{};try{compareOverviewLanguage(key);}finally{update=original;}},
  selectBenchmarks(keys){const original=update;update=()=>{};try{selectBenchmarks(keys);}finally{update=original;}},
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
// The navigation tests exercise the real Reset default (nbody). Restore the
// synthetic fixture's benchmark identity before the exhaustive render matrix.
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
// The saved Pony audit groups line entries by source, including the counted Pi helper.
const recorded=JSON.parse(fs.readFileSync(new URL('../../data/benchmarks.json',import.meta.url),'utf8'));
context.harness.initialize(recorded);
const pony=Object.values(recorded.program_inventory).filter(program=>program.language==='pony');
assert.equal(pony.length,20);
let helperLinks=0;
for(const program of pony){
  const audit=context.harness.locAudit(program);
  assert.doesNotMatch(audit,/undefined|\[object Object\]/);
  assert.match(audit,/canonical LOC/);
  for(const source of program.loc_expansions){
    for(const entry of source.expansions)assert.ok(audit.includes(`Line ${entry.line} · ${entry.units} canonical LOC`));
  }
  for(const key of program.files){
    const source=context.harness.programSource(program,key);
    assert.equal(source.role,program.file_roles[key].role);
    assert.equal(decodeURI(source.source_url),recorded.repository.url+'/blob/main/'+program.file_roles[key].source_path);
    if(source.role==='application-helper'){
      helperLinks++;
      assert.notEqual(source.source_url,program.source_url);
      assert.match(audit,/application helper/);
      assert.ok(source.loc_note);
    }
  }
}
assert.equal(helperLinks,2);
// Every newly admitted Elixir form exposes its counted application, helper and
// launcher, including the source aliases retained outside selected endpoints.
const elixir=Object.values(recorded.program_inventory).filter(program=>program.language==='elixir');
assert.equal(elixir.length,20);
for(const program of elixir){
  assert.equal(program.samples.length,3);
  assert.equal(program.eligible_for_chart,true);
  assert.equal(program.formatted_loc_status,'qualified');
  assert.deepEqual(program.files.map(key=>program.file_roles[key].role),
    ['application','application-helper','application-launcher']);
  for(const key of program.files){
    const source=context.harness.programSource(program,key);
    assert.equal(source.role,program.file_roles[key].role);
    assert.equal(decodeURI(source.source_url),recorded.repository.url+'/blob/main/'+program.file_roles[key].source_path);
  }
  context.harness.inspect(program.key);
  const detail=element('#inspector-body').innerHTML;
  assert.doesNotMatch(detail,/undefined|\[object Object\]/);
  assert.match(detail,/application helper/);
  assert.match(detail,/application launcher/);
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
