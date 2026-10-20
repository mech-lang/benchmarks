import assert from 'node:assert/strict';
import {encodeView,decodeView} from '../src/view_state.mjs';
const defaults={view:'summary',focus:'nbody',locMetric:'canonical',fast:true,small:true,global:false,focusMeans:true,
  sampleMode:'dim',medianMode:'highlight',densityMode:'off',benchmarks:['nbody','spectralnorm'],languages:['lean4','mech'],
  ellipses:['mech'],disabled:[],collapsedFamilies:[],traits:{memory:[]},benchmarkFilters:{resource:[]},
  releaseYearStart:1950,releaseYear:2026,playbackYear:null,languageFocus:null,languageTab:null,
  inspectorOpen:false,detail:{language:'mech',benchmark:'nbody',program:null,kind:'fast',file:0,aggregate:false},
  tableSort:{comparison:{key:'language',direction:1}},benchmarkExpanded:true,languageExpanded:true};
const spec={benchmarks:defaults.benchmarks,languages:defaults.languages,ellipses:defaults.languages,disabled:['p'],
  collapsedFamilies:['lean'],families:{lean:['lean4']},programs:{p:{language:'lean4',benchmark:'nbody',files:['a','b']}},
  traits:{memory:['rc','gc']},benchmarkFilters:{resource:['compute']},yearMin:1950,yearMax:2026,sorts:{comparison:['language','loc']}};
const normalize=view=>({...view,...Object.fromEntries(['benchmarks','languages','ellipses','disabled','collapsedFamilies'].map(k=>[k,[...view[k]].sort()]))});
const roundtrip=view=>assert.deepEqual(normalize(decodeView(encodeView(view,defaults),defaults,spec)),normalize(view));
roundtrip(defaults);
for(const locMetric of ['canonical','formatted','logical','bytes','gzip','bpe'])roundtrip({...defaults,locMetric});
assert.equal(decodeView('#v=1&locMetric=unqualified-logical',defaults,spec).locMetric,'canonical');
roundtrip({...defaults,benchmarks:[],languages:[],ellipses:[],disabled:['p'],collapsedFamilies:['lean'],
  fast:false,small:false,global:true,focusMeans:false,sampleMode:'off',medianMode:'off',densityMode:'highlight',
  releaseYearStart:2000,releaseYear:2020,playbackYear:2010,traits:{memory:['rc']},benchmarkFilters:{resource:['compute']},
  benchmarkExpanded:false,tableSort:{comparison:{key:'loc',direction:-1}}});
roundtrip({...defaults,view:'language',benchmarks:['nbody'],inspectorOpen:true,
  languageFocus:{selectionKey:'lean',family:true,variant:'lean4',benchmark:'nbody',program:'p',comparison:true,comparisonLanguage:'mech',comparisonProgram:'p'},
  detail:{language:'lean4',benchmark:'nbody',program:'p',kind:'small',file:1,aggregate:true}});
assert.equal(decodeView('#v=999',defaults,spec),null);
const bad=decodeView('#v=1&view=language&language=constructor&family=1&benchmarks=bad&sampleMode=bad&traits=__proto__:gc&detail.program=constructor&inspect=1&releaseYear=9999',defaults,spec);
assert.equal(bad.view,'summary');assert.deepEqual(bad.benchmarks,[]);assert.equal(bad.sampleMode,'dim');
assert.equal(bad.inspectorOpen,false);assert.equal(bad.releaseYear,2026);assert.deepEqual(bad.traits,{memory:[]});
assert.equal({}.gc,undefined);
const stale=decodeView('#v=1&inspect=1&detail.program=removed&detail.language=lean4&detail.benchmark=nbody&detail.file=99999',defaults,spec);
assert.equal(stale.inspectorOpen,true);assert.equal(stale.detail.program,null);assert.equal(stale.detail.file,0);
assert.equal(decodeView('#v=1&inspect=1&detail.program=p&detail.file=99999',defaults,spec).detail.file,1);
roundtrip({...defaults,languageTab:{...defaults,view:'language',benchmarks:['nbody'],
  languageFocus:{selectionKey:'lean4',family:false,variant:'lean4',benchmark:'nbody',program:null,comparison:false,comparisonLanguage:null,comparisonProgram:null}}});
console.log('View links: round trips, empty selections, catalog validation, stale programs and file bounds PASS');
