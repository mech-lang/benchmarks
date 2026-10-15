import {comparison,languageRelativeComparisons,same,chartDomain,comparisonMetrics,languagesByYear,globalStatistics,languageFamilies,median,releaseYearsInWindow,clampReleaseWindow,decadeWindow,medianRankings,timingOwner,observationSummary,recordedSamplePoints,sampleDensityPoints,densityGrid,layerPresentation,chartLayerState,summaryNumber,eligibleForChart} from './math.mjs?v=20261013-combined2';
import {traitDimensions,languageTraits,emptyTraitFilters,matchesTraits,filterLanguageKeys} from './traits.mjs?v=20261013-combined2';
import {benchmarkDimensions,benchmarkTraits,emptyBenchmarkFilters,matchesBenchmark,filterBenchmarkKeys} from './benchmark_traits.mjs';
import {renderRankingCharts} from './rankings.mjs?v=20261013-combined2';
import {axisData,projectProgram,hasFormattedLOC,formattedText,formattedValue} from './formatted_axis.mjs?v=20261013-combined2';
import {createLabelPlacer} from './labels.mjs';

const $=selector=>document.querySelector(selector);
// The same controls live in the desktop sidebar or the phone's modal drawer.
// Native dialog supplies the focus boundary and makes the background inert.
const filterDrawer=$('#filter-drawer'),filterTrigger=$('#open-filters');
const filterControls=$('.controls'),filterAnchor=document.createComment('desktop filter sidebar');
const mobileFilters=matchMedia('(max-width:720px)');
let filterScroll=null,backdropPointer=false;
filterControls.before(filterAnchor);
function restoreFilterScroll(){
  filterTrigger.setAttribute('aria-expanded','false');
  if(!filterScroll)return;
  const {x,y}=filterScroll;filterScroll=null;
  document.documentElement.classList.remove('filters-open');
  document.body.style.removeProperty('--filter-scroll-top');
  window.scrollTo(x,y);
}
function closeFilterDrawer(){
  if(filterDrawer.open)filterDrawer.close();
  restoreFilterScroll();
}
function syncFilterPlacement(){
  if(mobileFilters.matches){
    const hadFocus=filterControls.contains(document.activeElement);
    filterDrawer.append(filterControls);
    if(hadFocus&&!filterDrawer.open)filterTrigger.focus({preventScroll:true});
  }else{
    const wasOpen=filterDrawer.open,active=document.activeElement;
    closeFilterDrawer();filterAnchor.after(filterControls);
    if(wasOpen)(filterControls.contains(active)?active:$('#toggle-benchmark-filters')).focus({preventScroll:true});
  }
}
filterTrigger.addEventListener('click',()=>{
  if(!mobileFilters.matches||filterDrawer.open)return;
  filterScroll={x:window.scrollX,y:window.scrollY};
  document.body.style.setProperty('--filter-scroll-top',`${-filterScroll.y}px`);
  document.documentElement.classList.add('filters-open');
  filterDrawer.showModal();filterTrigger.setAttribute('aria-expanded','true');
});
$('#close-filters').addEventListener('click',closeFilterDrawer);
filterDrawer.addEventListener('cancel',event=>{event.preventDefault();closeFilterDrawer();});
filterDrawer.addEventListener('close',()=>{if(!filterDrawer.open)restoreFilterScroll();});
// Escape dismisses just this drawer, leaving an underlying program inspector open.
filterDrawer.addEventListener('keydown',event=>{if(event.key==='Escape')event.stopPropagation();});
const outsideDrawer=event=>{
  const box=filterDrawer.getBoundingClientRect();
  return event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom;
};
filterDrawer.addEventListener('pointerdown',event=>{backdropPointer=event.target===filterDrawer&&outsideDrawer(event);});
filterDrawer.addEventListener('click',event=>{
  if(backdropPointer&&event.target===filterDrawer&&outsideDrawer(event))closeFilterDrawer();
  backdropPointer=false;
});
mobileFilters.addEventListener('change',syncFilterPlacement);
syncFilterPlacement();

const svgNS='http://www.w3.org/2000/svg';
let data,model,traits,programCatalog,rememberedLanguageView=null;
let languageIndex,benchmarkIndex,familyIndex;
const programsByBenchmark=new Map(),comparisonViews=new Map(),formattedPrograms=new WeakMap();
const medianStatistics=new WeakMap(),sampleInputsByEntries=new WeakMap(),globalStatisticsByEntries=new WeakMap();
// One node per recorded program/run, shared across views and LOC metrics.
// The finite catalog bounds this cache; records contain no model or handlers.
const sampleNodes=new Map();
let renderedSamplePlot=null,renderedDensityLayer=null;
let benchmarkEntries=null,densityCache=null;
const state={benchmarks:new Set(),benchmarkFilters:emptyBenchmarkFilters(),languages:new Set(),disabled:new Set(),ellipses:new Set(['mech']),
  view:'summary',focus:'nbody',locMetric:'canonical',fast:true,small:true,sampleMode:'dim',medianMode:'highlight',densityMode:'off',focusMeans:true,global:false,playing:false,collapsedFamilies:new Set(),releaseYearStart:null,releaseYear:null,playbackYear:null,traits:emptyTraitFilters(),languageFocus:null,
  detail:{language:'mech',benchmark:'nbody',kind:'fast',program:null,aggregate:false,file:0}};
const colors={};
const mechViewColors={mech:'#F6C04E','mech-jit':'#FFE59A','mech-resident':'#C99B2E'};
const domains=new Map();
let currentDomain=null;
let playbackTimer=null;
let renderedChartWidth=null,renderedChartMobile=null,chartResizeFrame=null;
const tableSort={comparison:{key:'language',direction:1},timings:{key:'run',direction:1},implementations:{key:null,direction:1}};
const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ratio=n=>`${summaryNumber(n)}×`;
const seconds=n=>n==null?'Not measured':`${n.toFixed(n<1?6:n>=100?2:3)} s`;
const language=key=>languageIndex.get(key);
const benchmark=key=>benchmarkIndex.get(key);
const effectiveBenchmarks=()=>filterBenchmarkKeys(state.benchmarks,state.benchmarkFilters);
const catalogProgram=key=>Object.hasOwn(programCatalog,key)?programCatalog[key]:undefined;
const benchmarkPrograms=(b,key)=>programsByBenchmark.get(b)?.get(key)??[];
const measuredTiming=p=>Number.isFinite(p?.seconds)&&p.seconds>0;
const plotData=(metric=state.locMetric)=>axisData(comparisonData(),metric);
const plotProgram=(program,metric=state.locMetric)=>{
  if(metric==='canonical')return program;
  if(metric!=='formatted')return projectProgram(program,metric);
  if(!formattedPrograms.has(program))formattedPrograms.set(program,projectProgram(program,metric));
  return formattedPrograms.get(program);
};
const sampleProgram=program=>plotProgram(program);
const plottable=program=>eligibleForChart(program)&&measuredTiming(program)&&Number.isFinite(program.loc)&&program.loc>0&&Number.isFinite(program.x)&&program.x>0&&Number.isFinite(program.y)&&program.y>0;
const metricName=()=>state.locMetric==='formatted'?'formatted LOC':'canonical LOC';

const shortName=key=>({c:'C',cpp:'C++',mech:'Mech (AOT)',python:'Python',ruby:'Ruby',javascript:'JavaScript'}[key]??language(key).label);
const chartName=key=>({mech:'Mech AOT','mech-jit':'Mech JIT','mech-resident':'Mech interpreted',bqn:'BQN',k:'K'}[key]??shortName(key));
const partialEntry=entry=>entry.coverage.measured<entry.coverage.selected;
const coverageLabel=entry=>`${entry.coverage.measured}/${entry.coverage.selected}`;
const missingNames=entry=>entry.coverage.missing.map(b=>b.title).join(', ');
const meanChartName=entry=>chartName(entry.language.key)+(partialEntry(entry)?` · ${coverageLabel(entry)}`:'');
const isMechLanguage=key=>language(key)?.family==='mech'||key==='mech';
const mechKeys=()=>data.languages.filter(l=>isMechLanguage(l.key)).map(l=>l.key);
const displayColor=key=>state.view==='mech'?(mechViewColors[key]??colors[key]):colors[key];
const inLanguageView=()=>state.view==='language'&&!!state.languageFocus;
const languageOverviewVisible=()=>!!state.languageFocus&&(inLanguageView()||state.languageFocus.comparison);
const samplesVisible=()=>layerPresentation(state.sampleMode).visible;
const densityVisible=()=>layerPresentation(state.densityMode).visible;
const focusKeys=()=>new Set(state.languageFocus?.keys??[]);
function savedChartSelection(){
  return {...state,benchmarks:new Set(state.benchmarks),benchmarkFilters:Object.fromEntries(Object.entries(state.benchmarkFilters).map(([key,values])=>[key,new Set(values)])),languages:new Set(state.languages),disabled:new Set(state.disabled),ellipses:new Set(state.ellipses),collapsedFamilies:new Set(state.collapsedFamilies),traits:Object.fromEntries(Object.entries(state.traits).map(([key,values])=>[key,new Set(values)])),detail:{...state.detail},languageFocus:null,playing:false,inspectorOpen:$('#inspector').open};
}
function focusPrograms(){
  const keys=focusKeys();
  return data.benchmarks.flatMap(b=>[...keys].flatMap(key=>benchmarkPrograms(b.key,key)));
}
function comparisonData(){
  const focus=state.languageFocus,selected=focus?.comparison?catalogProgram(focus.comparisonProgram):null;
  if(!selected)return data;
  if(comparisonViews.has(selected.key))return comparisonViews.get(selected.key);
  // An explicit source comparison gets a separate view. The canonical model,
  // source records, endpoint pools and fixed baselines remain unchanged.
  const view={...data,programs:{...data.programs,[selected.key]:selected},benchmarks:data.benchmarks.map(b=>{
    if(b.key!==selected.benchmark)return b;
    const admitted=eligibleForChart(selected);
    const replacement={language:selected.language,label:shortName(selected.language),programs:admitted?[selected.key]:[],
      fast:admitted&&measuredTiming(selected)?selected.key:null,small:admitted?selected.key:null,
      formatted_fast:admitted&&measuredTiming(selected)&&hasFormattedLOC(selected)?selected.key:null,
      formatted_small:admitted&&hasFormattedLOC(selected)?selected.key:null};
    const present=b.groups.some(g=>g.language===selected.language);
    return {...b,groups:present?b.groups.map(g=>g.language===selected.language?{...g,...replacement}:g):[...b.groups,replacement]};
  })};
  if(comparisonViews.size===4)comparisonViews.delete(comparisonViews.keys().next().value);
  comparisonViews.set(selected.key,view);
  return view;
}
function showLanguageOverview(key,{family=false,restoreProgram=false}={}){
  closeFilterDrawer();
  pauseYears();
  const group=family?families().find(f=>f.key===key):null;
  const keys=group?group.members.map(l=>l.key):[key];
  if(!keys.every(k=>language(k)))return;
  const sameFocus=state.languageFocus&&keys.join(',')===state.languageFocus.keys.join(',');
  const origin=state.languageFocus?.origin??savedChartSelection();
  const savedDetail=sameFocus?state.languageFocus.savedDetail:null;
  const prior=sameFocus?state.languageFocus:null;
  state.languageFocus={keys,selectionKey:key,family:!!group,label:group?.label??shortName(key),origin,
    program:restoreProgram&&savedDetail?.program?savedDetail.program:prior?.program??null,
    variant:restoreProgram&&savedDetail? savedDetail.language:prior?.variant??keys[0],
    benchmark:restoreProgram&&savedDetail?savedDetail.benchmark:prior?.benchmark??state.focus,
    comparison:false,comparisonProgram:null,savedDetail,savedInspectorOpen:prior?.savedInspectorOpen??false};
  if(!restoreProgram&&$('#inspector').open){$('#inspector').close();$('#chart-detail-layout').classList.remove('inspector-open');}
  state.view='language';state.traits=emptyTraitFilters();state.benchmarkFilters=emptyBenchmarkFilters();fullReleaseWindow();
  state.benchmarks=new Set(data.benchmarks.map(b=>b.key));state.languages=new Set(data.languages.map(l=>l.key));
  state.disabled.clear();state.ellipses=new Set(keys);
  Object.assign(state,{fast:true,small:true,focusMeans:false,global:true});
  for(const k of keys)state.collapsedFamilies.delete(language(k).family??k);
  if(restoreProgram&&savedDetail){
    state.detail={...savedDetail};
    if(prior.savedInspectorOpen&&!$('#inspector').open){$('#inspector').show();$('#chart-detail-layout').classList.add('inspector-open');}
    if(!prior.savedInspectorOpen&&$('#inspector').open){$('#inspector').close();$('#chart-detail-layout').classList.remove('inspector-open');}
  }
  update();
  if(restoreProgram&&savedDetail&&$('#inspector').open)renderInspector();
  $('#language-overview-title').focus({preventScroll:true});
  $('#language-overview').scrollIntoView({block:'start',behavior:'auto'});
}
function leaveLanguageFocusForSelection(){
  if(!state.languageFocus)return;
  rememberedLanguageView={...savedChartSelection(),languageFocus:{...state.languageFocus}};
  state.languageFocus=null;if(state.view==='language')state.view='summary';state.global=false;
}
function selectBenchmarks(keys,{clearFilters=false}={}){
  state.benchmarks=new Set(keys);
  if(clearFilters)state.benchmarkFilters=emptyBenchmarkFilters();
  // A new scope leaves a single-source comparison inside the same language view.
  if(state.languageFocus?.comparison&&state.view==='benchmark'){
    Object.assign(state.languageFocus,{comparison:false,comparisonProgram:null,comparisonLanguage:null});
    state.view='language';
  }
  update();
}
function selectBenchmarkFacet(dimension,option,checked){
  if(!benchmarkDimensions.find(item=>item.key===dimension)?.options.some(item=>item.key===option))return;
  checked?state.benchmarkFilters[dimension].add(option):state.benchmarkFilters[dimension].delete(option);
  selectBenchmarks(state.benchmarks);
}
function selectView(view){
  if(view==='language'){
    const focus=state.languageFocus;
    if(focus){if(focus.comparison)showLanguageOverview(focus.selectionKey,{family:focus.family});return;}
    if(rememberedLanguageView){
      closeFilterDrawer();pauseYears();
      const {inspectorOpen,...selection}=rememberedLanguageView;
      Object.assign(state,selection);
      if(inspectorOpen&&!$('#inspector').open){$('#inspector').show();$('#chart-detail-layout').classList.add('inspector-open');}
      if(!inspectorOpen&&$('#inspector').open){$('#inspector').close();$('#chart-detail-layout').classList.remove('inspector-open');}
      update();$('#language-overview-title').focus({preventScroll:true});
    }
    return;
  }
  const wasLanguage=languageOverviewVisible();leaveLanguageFocusForSelection();
  if(view==='summary'&&wasLanguage){reset();return;}
  if(view==='mech')enterMechView();else state.view=view;
  update();
}
function languageMedianStatistics(entry){
  if(medianStatistics.has(entry))return medianStatistics.get(entry);
  const statistics=Object.fromEntries(['fast','small'].map(kind=>{
    const points=entry.inputs.map(input=>input[kind]).filter(plottable);
    if(!points.length)return [kind,null];
    const midpoint={x:2**median(points.map(p=>Math.log2(p.x))),y:2**median(points.map(p=>Math.log2(p.y)))};
    const atMedian=region=>region&&({...region,center:midpoint,boundary:region.boundary.map(p=>({x:p.x*midpoint.x/region.center.x,y:p.y*midpoint.y/region.center.y}))});
    return [kind,{n:points.length,median:midpoint,spread:atMedian(entry.spread[kind]),spread2:atMedian(entry.spread2[kind])}];
  }));
  medianStatistics.set(entry,statistics);
  return statistics;
}
function renderLanguageOverview(){
  const focus=state.languageFocus,panel=$('#language-overview');
  panel.hidden=!languageOverviewVisible();
  $('#language-results').hidden=$('#language-comparisons').hidden=panel.hidden;
  $('#mean-table-wrap').hidden=$('#table-metric-note').hidden=!panel.hidden;
  const tabFocus=focus??rememberedLanguageView?.languageFocus;
  $('#language-view-tab').hidden=!tabFocus;
  if(tabFocus)$('#language-view-tab').textContent=tabFocus.label;
  if(panel.hidden)return;
  const selectedBenchmarks=effectiveBenchmarks();
  const programs=focusPrograms().filter(p=>selectedBenchmarks.has(p.benchmark)),measured=programs.filter(measuredTiming);
  const covered=data.benchmarks.filter(b=>measured.some(p=>p.benchmark===b.key)),observations=observationSummary(measured);
  $('#language-overview-title').textContent=`${focus.label} · ${focus.comparison?'comparison':'language overview'}`;
  $('#language-overview-summary').textContent=`${covered.length}/${selectedBenchmarks.size} selected benchmarks · ${measured.length} programs · ${observations.runs} recorded runs. ${data.program_inventory?'Every qualified program retained in this publication is listed below.':'This publication retains its fastest and fewest-LOC program pool.'} Unavailable timings stay blank.${measured.some(p=>p.timing_alias_of)?' Timing aliases share recorded runs.':''}`;
  if(state.locMetric==='formatted')$('#language-overview-summary').textContent+=` ${measured.filter(p=>plottable(plotProgram(p))).length} timed programs have qualified formatted coordinates; the chart omits the others. Their original timings and sources remain listed.`;
  if(focus.comparison&&state.view==='benchmark'){
    const viewData=plotData(),active=viewData.benchmarks.find(b=>b.key===state.focus);
    const missing=[...state.languages].filter(key=>!active?.groups.some(g=>g.language===key&&g.programs.some(id=>plottable(viewData.programs[id]))));
    if(missing.length)$('#language-overview-summary').textContent+=` ${missing.map(shortName).join(', ')}: no eligible ${metricName()} comparison for ${benchmark(state.focus).title}.`;
  }
  $('#return-language-overview').hidden=!focus.comparison;
  $('#overview-variant').innerHTML=focus.keys.map(k=>`<option value="${k}">${esc(shortName(k))}</option>`).join('');
  $('#overview-variant').closest('label').hidden=focus.keys.length===1;
  if(!focus.keys.includes(focus.variant))focus.variant=focus.keys[0];
  if(!benchmark(focus.benchmark))focus.benchmark=data.benchmarks[0].key;
  $('#overview-variant').value=focus.variant;
  $('#overview-benchmark').innerHTML=data.benchmarks.map(b=>`<option value="${b.key}" ${b.key===focus.benchmark?'selected':''}>${esc(b.title)}</option>`).join('');
  const others=data.languages.filter(l=>l.key!==focus.variant);
  const previous=focus.comparisonLanguage??$('#overview-comparison-language').value;
  $('#overview-comparison-language').innerHTML=others.map(l=>`<option value="${l.key}">${esc(shortName(l.key))}</option>`).join('');
  $('#overview-comparison-language').value=others.some(l=>l.key===previous)?previous:others.some(l=>l.key==='mech')?'mech':others[0]?.key??'';
  $('#overview-compare').disabled=!others.length;
  $('#overview-inspect').disabled=!programs.some(p=>p.language===focus.variant&&p.benchmark===focus.benchmark);
  $('#language-timings tbody').innerHTML=data.benchmarks.filter(b=>selectedBenchmarks.has(b.key)).map(b=>{
    const rows=programs.filter(p=>p.benchmark===b.key);
    if(!rows.length)return `<tr><th scope="row">${esc(b.title)}</th><td colspan="8" class="missing-timing">No published program or timing.</td></tr>`;
    return rows.map((p,i)=>`<tr class="${p.key===focus.program?'chosen':''}">${i===0?`<th scope="rowgroup" rowspan="${rows.length}">${esc(b.title)}</th>`:''}<td>${esc(shortName(p.language))}</td><td><button data-inspect-program="${p.key}">${esc(p.id)}</button></td><td class="ratio">${p.loc}</td><td class="ratio" title="${esc(formattedText(p))}">${formattedValue(p)}</td><td class="ratio">${measuredTiming(p)?seconds(p.seconds):'—'}</td><td class="ratio">${measuredTiming(p)&&eligibleForChart(p)?`${(p.seconds/b.baseline_seconds).toFixed(3)}×`:'—'}</td><td class="ratio">${measuredTiming(p)&&Number.isFinite(p.timing_sd)&&p.timing_sd>=0?seconds(p.timing_sd):'—'}</td><td class="sample-values">${p.samples.length?p.samples.map(value=>Number(value).toFixed(6)).join(' · '):'—'}${!eligibleForChart(p)?' · excluded from charts':''}${renderAliasDisclosure(p)}<button class="row-comparison" data-compare-program="${p.key}">Compare</button></td></tr>`).join('');
  }).join('');
  renderLanguageComparisons();
}
function renderLanguageComparisons(){
  const focus=state.languageFocus,target=focus.variant,label=shortName(target);
  const rows=languageRelativeComparisons(data,target,{benchmarks:effectiveBenchmarks(),locData:axisData(data,state.locMetric)});
  rows.sort((a,b)=>Number(b.target)-Number(a.target)||shortName(a.language.key).localeCompare(shortName(b.language.key),'en',{sensitivity:'base'}));
  const scope=data.benchmarks.filter(b=>effectiveBenchmarks().has(b.key)).map(b=>b.title);
  $('#language-comparisons-title').textContent=`Every language relative to ${label}`;
  $('#language-comparisons-note').textContent=`${label} = 1.0×. Lower time is faster; lower LOC is smaller. Equal-weight geometric means of other / ${label} on shared workloads only: fastest published medians for time, fewest ${metricName()} for LOC. Each row can use a different shared subset; missing results are not estimated. All published variants are listed, independently of language filters. Scope: ${scope.join(', ')||'no benchmarks selected'}.`;
  $('#language-comparison-table thead').innerHTML=`<tr><th scope="col">Language / execution variant</th><th scope="col">Time × ${esc(label)}</th><th scope="col">Shared time workloads</th><th scope="col">${esc(metricName())} × ${esc(label)}</th><th scope="col">Shared LOC workloads</th></tr>`;
  const coverage=metric=>`<span title="${esc(metric.benchmarks.map(key=>benchmark(key).title).join(', ')||'No shared qualified workloads')}" aria-label="${esc(metric.benchmarks.map(key=>benchmark(key).title).join(', ')||'No shared qualified workloads')}">${metric.benchmarks.length}/${metric.selected}</span>`;
  $('#language-comparison-table tbody').innerHTML=rows.map(row=>`<tr class="${row.target?'comparison-reference':''}"><th scope="row">${row.target?`${esc(shortName(row.language.key))} · reference`:`<button data-compare-language="${row.language.key}" ${row.loc.benchmarks.length?'':'disabled'} title="Compare ${esc(label)} with ${esc(shortName(row.language.key))} on their shared ${metricName()} workloads">${esc(shortName(row.language.key))}</button>`}</th><td class="ratio">${row.time.ratio==null?'—':ratio(row.time.ratio)}</td><td>${coverage(row.time)}</td><td class="ratio">${row.loc.ratio==null?'—':ratio(row.loc.ratio)}</td><td>${coverage(row.loc)}</td></tr>`).join('');
}
function compareOverviewLanguage(key){
  const focus=state.languageFocus;if(!focus||key===focus.variant)return;
  const row=languageRelativeComparisons(data,focus.variant,{benchmarks:effectiveBenchmarks(),locData:axisData(data,state.locMetric)}).find(row=>row.language.key===key);
  if(!row?.loc.benchmarks.length)return;
  focus.comparison=true;focus.comparisonProgram=null;focus.comparisonLanguage=key;
  state.view='summary';state.benchmarks=new Set(row.loc.benchmarks);state.benchmarkFilters=emptyBenchmarkFilters();state.languages=new Set([focus.variant,key]);
  state.traits=emptyTraitFilters();fullReleaseWindow();state.disabled.clear();state.global=false;
  if($('#inspector').open){$('#inspector').close();$('#chart-detail-layout').classList.remove('inspector-open');}
  update();$('#chart-title').scrollIntoView({block:'start',behavior:'auto'});
}
function compareOverviewProgram(key=null){
  const focus=state.languageFocus;if(!focus)return;
  const p=key?catalogProgram(key):null,from=p?.language??focus.variant,b=p?.benchmark??focus.benchmark,to=$('#overview-comparison-language').value;
  if(!language(from)||!language(to)||!benchmark(b))return;
  const current=selectedProgram();
  focus.savedInspectorOpen=$('#inspector').open;
  focus.savedDetail=p&&current?.key!==p.key?{language:p.language,benchmark:p.benchmark,kind:'fast',program:p.key,aggregate:false,file:0}:
    {...state.detail,program:current?.key??state.detail.program};
  if(p)focus.program=p.key;
  focus.variant=from;focus.benchmark=b;focus.comparisonProgram=p?.key??null;focus.comparisonLanguage=to;
  state.detail=p?{...focus.savedDetail}:{language:from,benchmark:b,kind:'fast',program:null,aggregate:false,file:0};
  focus.comparison=true;state.view='benchmark';state.focus=b;state.benchmarks=new Set([b]);state.benchmarkFilters=emptyBenchmarkFilters();state.languages=new Set([from,to]);
  state.traits=emptyTraitFilters();fullReleaseWindow();state.disabled.clear();
  Object.assign(state,{fast:true,small:true,focusMeans:false,global:false});
  if(!selectedProgram()&&$('#inspector').open){$('#inspector').close();$('#chart-detail-layout').classList.remove('inspector-open');}
  update();
  const viewData=plotData();
  const missing=[from,to].filter(k=>!viewData.benchmarks.find(item=>item.key===b).groups.some(g=>g.language===k&&g.programs.some(id=>plottable(viewData.programs[id]))));
  if(missing.length)showHoverDetails(`${missing.map(shortName).join(', ')} has no eligible ${metricName()} comparison for ${benchmark(b).title}. Original timing and source records remain available.`);
}
function languageViewDomain(metric=state.locMetric){
  const domain={...chartDomain(axisData(data,metric),{...state,benchmarks:effectiveBenchmarks()})},keys=focusKeys();
  const include=point=>{
    if(!(point.x>0&&point.y>0))return;
    domain.xMin=Math.min(domain.xMin,Math.log2(point.x)-.15);domain.xMax=Math.max(domain.xMax,Math.log2(point.x)+.25);
    domain.yMin=Math.min(domain.yMin,Math.log2(point.y)-.18);domain.yMax=Math.max(domain.yMax,Math.log2(point.y)+.25);
  };
  for(const p of focusPrograms().filter(p=>effectiveBenchmarks().has(p.benchmark)).map(p=>plotProgram(p,metric)).filter(plottable)){
    include(p);
    const b=benchmark(p.benchmark);
    if(!state.focusMeans)for(const elapsed of p.samples)if(Number.isFinite(elapsed)&&elapsed>0)include({x:p.x,y:elapsed/b.baseline_seconds});
  }
  const entries=comparison(axisData(data,metric),{benchmarks:effectiveBenchmarks(),languages:keys,disabled:new Set()}).entries;
  for(const entry of entries){
    const statistics=languageMedianStatistics(entry);
    for(const kind of ['fast','small']){
      if(!state.focusMeans){
        for(const p of entry.spread2[kind]?.boundary??[])include(p);
        for(const p of statistics[kind]?.spread2?.boundary??[])include(p);
      }
      if(statistics[kind])include(statistics[kind].median);
    }
  }
  return domain;
}
function sourceComparisonDomain(metric=state.locMetric){
  const domain={...chartDomain(plotData(metric),{...state,benchmarks:effectiveBenchmarks()})},original=catalogProgram(state.languageFocus?.comparisonProgram);
  const p=original?plotProgram(original,metric):null;
  if(!p||!plottable(p))return domain;
  const b=benchmark(p.benchmark);
  if(Number.isFinite(p.x)&&p.x>0){domain.xMin=Math.min(domain.xMin,Math.log2(p.x)-.15);domain.xMax=Math.max(domain.xMax,Math.log2(p.x)+.25);}
  if(Number.isFinite(p.y)&&p.y>0){domain.yMin=Math.min(domain.yMin,Math.log2(p.y)-.18);domain.yMax=Math.max(domain.yMax,Math.log2(p.y)+.25);}
  if(!state.focusMeans)for(const elapsed of p.samples)if(Number.isFinite(elapsed)&&elapsed>0){
    const y=Math.log2(elapsed/b.baseline_seconds);
    domain.yMin=Math.min(domain.yMin,y-.18);domain.yMax=Math.max(domain.yMax,y+.25);
  }
  return domain;
}
function enterMechView(){
  pauseYears();
  state.languageFocus=null;
  state.traits=emptyTraitFilters();
  state.benchmarkFilters=emptyBenchmarkFilters();
  state.view='mech';fullReleaseWindow();
  state.benchmarks=new Set(data.benchmarks.map(b=>b.key));
  for(const key of mechKeys())state.languages.add(key);
  for(const program of Object.values(data.programs))if(isMechLanguage(program.language))state.disabled.delete(program.key);
  state.collapsedFamilies.delete('mech');
  Object.assign(state,{fast:true,small:true,focusMeans:false,global:false});
}
const families=()=>familyIndex;
const familyCount=keys=>new Set([...keys].map(key=>language(key).family??key)).size;
const lineDash=key=>({dashed:'7 4',dotted:'2 4'}[language(key).line_style]??null);
const yearBounds=()=>({min:Math.min(...data.languages.map(l=>l.release_year)),max:Math.max(...data.languages.map(l=>l.release_year))});
const selectedYearWindow=()=>({from:state.releaseYearStart,to:state.releaseYear});
const shownReleaseYear=()=>Math.max(state.releaseYearStart,Math.min(state.releaseYear,state.playbackYear??state.releaseYear));
const yearKeys=()=>new Set(languagesByYear(data.languages,{from:state.releaseYearStart,to:shownReleaseYear()}));
const traitLanguageKeys=()=>filterLanguageKeys(state.languages,traits,state.traits);
const effectiveLanguages=()=>{const allowed=yearKeys();return new Set([...traitLanguageKeys()].filter(key=>allowed.has(key)));};
const playbackYears=()=>{const eligible=traitLanguageKeys();return releaseYearsInWindow(data.languages.filter(l=>eligible.has(l.key)&&(state.view!=='mech'||isMechLanguage(l.key))),selectedYearWindow());};
function pauseYears({clearCursor=false}={}){clearTimeout(playbackTimer);playbackTimer=null;state.playing=false;if(clearCursor)state.playbackYear=null;}
function fullReleaseWindow(){const {min,max}=yearBounds();state.releaseYearStart=min;state.releaseYear=max;state.playbackYear=null;}
function setReleaseWindow(from,to,{moving='both'}={}){
  const window=clampReleaseWindow({from,to},yearBounds(),moving);
  pauseYears({clearCursor:true});state.releaseYearStart=window.from;state.releaseYear=window.to;update();
}
function setReleaseYear(year){
  const {min,max}=yearBounds();
  if(!Number.isInteger(year)||year<min||year>max)throw new Error('Invalid language release year filter.');
  setReleaseWindow(state.releaseYearStart,year,{moving:'end'});
}
function playYears(){
  if(state.playing){pauseYears();renderYears();return;}
  const years=playbackYears();
  if(!years.length){pauseYears({clearCursor:true});update();return;}
  state.playing=true;
  if(!years.includes(state.playbackYear)||state.playbackYear===years.at(-1))state.playbackYear=years[0];
  update();
  const advance=()=>{
    const next=playbackYears().find(year=>year>state.playbackYear);
    if(next==null){pauseYears({clearCursor:true});update();return;}
    state.playbackYear=next;update();
    playbackTimer=setTimeout(advance,850);
  };
  playbackTimer=setTimeout(advance,850);
}
function renderYears(){
  const {min,max}=yearBounds(),eligible=effectiveLanguages(),from=state.releaseYearStart,to=state.releaseYear;
  for(const [id,year,label,limitMin,limitMax] of [['release-year-start',from,'First',min,to],['release-year-end',to,'Last',from,max]]){
    const input=$('#'+id);input.min=min;input.max=max;input.value=year;
    input.setAttribute('aria-valuemin',String(limitMin));input.setAttribute('aria-valuemax',String(limitMax));
    input.setAttribute('aria-valuetext',`${label} release year ${year}, inclusive. Selected window ${from} to ${to}.`);
  }
  $('#release-year-window').style.setProperty('--year-from',`${100*(from-min)/(max-min||1)}%`);
  $('#release-year-window').style.setProperty('--year-to',`${100*(to-min)/(max-min||1)}%`);
  $('#release-year-value').textContent=from===to?String(from):`${from}–${to}`;
  $('#release-year-min').textContent=`From ${from}`;$('#release-year-max').textContent=`To ${to}`;
  for(const button of document.querySelectorAll('[data-release-decade]')){
    const window=decadeWindow(Number(button.dataset.releaseDecade),{min,max});button.disabled=!window;
    button.setAttribute('aria-pressed',String(!!window&&window.from===from&&window.to===to));
    button.title=window?`${window.from}–${window.to}, inclusive`:'Outside the published release-year span';
  }
  const shown=shownReleaseYear(),progress=state.playbackYear==null?'':` ${state.playing?'Playback through':'Playback paused at'} ${shown}; selected window ends ${to}.`;
  $('#release-year-status').textContent=`${eligible.size} of ${traitLanguageKeys().size} matching entries in ${from}–${shown}.${progress}`;
  $('#playback-year').textContent=state.playbackYear==null?`${from}–${to}`:`${state.playing?'Through':'Paused at'} ${shown}`;
  $('#play-years').textContent=state.playing?'Pause window':'Play window';
  $('#play-years').disabled=!playbackYears().length;
  $('#play-years').setAttribute('aria-pressed',String(state.playing));
}
function colorKeyStyle(key){
  const color=displayColor(key),style=language(key).line_style;
  return `background:${style==='dashed'?`repeating-linear-gradient(to right,${color} 0 5px,transparent 5px 8px)`:style==='dotted'?`repeating-linear-gradient(to right,${color} 0 2px,transparent 2px 5px)`:color}`;
}

function sortHeader(table,key,label,subtitle=''){
  const sort=tableSort[table],active=sort.key===key;
  const chevrons=active?(sort.direction===1?'M4 10 8 6 12 10':'M4 6 8 10 12 6'):'M4 6 8 2 12 6 M4 10 8 14 12 10';
  return `<th scope="col" aria-sort="${active?(sort.direction===1?'ascending':'descending'):'none'}"><button class="sort-header" data-sort-table="${table}" data-sort-key="${key}" data-sort-label="${esc(label+(subtitle?' '+subtitle:''))}"><span class="sort-label">${esc(label)}${subtitle?`<small>${esc(subtitle)}</small>`:''}</span><svg class="sort-indicator" viewBox="0 0 16 16" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="${chevrons}"/></svg></button></th>`;
}
function sortedRows(table,rows,value){
  const sort=tableSort[table];
  if(!sort.key)return rows;
  return rows.slice().sort((a,b)=>{
    const x=value(a,sort.key),y=value(b,sort.key);
    if(x==null||y==null)return x==null?(y==null?0:1):-1;
    return sort.direction*(typeof x==='string'?x.localeCompare(y,'en',{numeric:true,sensitivity:'base'}):x-y);
  });
}
function sortTable(button){
  const {sortTable:table,sortKey:key,sortLabel:label}=button.dataset,sort=tableSort[table];
  sort.direction=sort.key===key?-sort.direction:1;sort.key=key;
  const inspector=$('#inspector'),scrollTop=inspector.scrollTop;
  const variantScroll=$('.variant-list')?.scrollTop??0;
  if(table==='comparison')renderTable();else{
    renderInspector();inspector.scrollTop=scrollTop;
    $('.variant-list').scrollTop=variantScroll;
  }
  $(`[data-sort-table="${table}"][data-sort-key="${key}"]`).focus({preventScroll:true});
  $('#sort-status').textContent=`Sorted ${label} ${sort.direction===1?'ascending':'descending'}.`;
}

function node(tag,attributes={},parent){
  const element=document.createElementNS(svgNS,tag);
  for(const [key,value] of Object.entries(attributes))if(value!==null&&value!==undefined)element.setAttribute(key,String(value));
  if(parent)parent.append(element);
  return element;
}
function text(parent,value,x,y,attributes={}){
  const element=node('text',{x,y,...attributes},parent);element.textContent=value;return element;
}
function luminance(rgb){return rgb.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);}
function darkColor(hex){
  const original=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
  const background=luminance([21,27,33]);
  for(let tint=0;tint<=1;tint+=.025){
    const rgb=original.map(v=>Math.round(v+(255-v)*tint));
    if((luminance(rgb)+.05)/(background+.05)>=4.2)return '#'+rgb.map(v=>v.toString(16).padStart(2,'0')).join('');
  }
  return hex;
}
function allSelection(){const enabled=effectiveLanguages();return {benchmarks:effectiveBenchmarks(),languages:state.view==='mech'?new Set(mechKeys().filter(key=>enabled.has(key))):enabled,disabled:state.disabled};}
function currentRankings(){
  return medianRankings(currentEntries(),{referenceLanguage:languageOverviewVisible()?state.languageFocus.variant:null});
}
function renderMedianRankings(){
  const active=state.view==='rankings'||languageOverviewVisible(),panel=$('#median-rankings');panel.hidden=!active;$('.chart-card').hidden=state.view==='rankings';
  if(!active)return;
  const rankings=currentRankings(),count=rankings.speed.entries.length,reference=rankings.speed.reference_language;
  const origin=reference===null?'the ratio-coordinate median':shortName(reference);
  $('#median-rankings-summary').textContent=`${count} variant${count===1?'':'s'} · ${effectiveBenchmarks().size} benchmarks · ${state.releaseYearStart}–${shownReleaseYear()}`;
  $('#ranking-origin-note').textContent=`Zero is ${origin}.`;
  $('#median-rankings-empty').textContent=reference!==null&&rankings.speed.reference===null?
    `${shortName(reference)} has no eligible measured coordinates in this selection. Adjust the year window, benchmarks, language filters or disabled programs.`:
    'No eligible measured comparisons in this selection. Adjust the year window, benchmarks, language filters or disabled programs.';
  $('#median-rankings-empty').hidden=count!==0;$('#median-ranking-cards').hidden=count===0;
  if(!count){$('#median-ranking-cards').replaceChildren();return;}
  renderRankingCharts({container:$('#median-ranking-cards'),rankings,labelFor:shortName,colorFor:displayColor,onOpenLanguage:showLanguageOverview,locTitle:state.locMetric==='formatted'?'Formatted LOC':'Canonical LOC'});
}
function update(){
  benchmarkEntries=null;
  model=comparison(plotData(),allSelection());
  renderYears();renderControls();
  // The inspector also renders the overview and rankings after selecting its
  // program. Avoid constructing those tables and SVGs twice in one update.
  if($('#inspector').open)renderInspector({renderRelated:false});
  renderLanguageOverview();renderMedianRankings();
  if(state.view!=='rankings')renderChart();
  if(state.view!=='rankings'&&!languageOverviewVisible())renderTable();
  $('#selection-summary').textContent=`${effectiveBenchmarks().size}/${data.benchmarks.length} selected · ${familyCount(model.entries.map(e=>e.language.key))} languages · ${model.entries.length} variants · ${state.disabled.size} hidden`;
  const visible=currentEntries();
  const enabled=effectiveLanguages();
  const partial=visible.filter(partialEntry);
  $('#coverage-message').textContent=partial.length?`${partial.map(e=>`${shortName(e.language.key)} uses ${coverageLabel(e)} selected benchmarks; missing ${missingNames(e)}.`).join(' ')} Each mean uses that language's measured tests from your selection. Failed tests contribute no timing or LOC ratio.`:'Enabled languages cover the compared benchmarks. The means give each benchmark equal weight.';
  $('#benchmark-filter-count').textContent=effectiveBenchmarks().size;
  $('#language-filter-count').textContent=familyCount(state.view==='mech'?mechKeys().filter(key=>enabled.has(key)):enabled);
  for(const button of document.querySelectorAll('[data-view]'))button.setAttribute('aria-pressed',button.dataset.view===(languageOverviewVisible()?'language':state.view));
  $('#focused-benchmark').hidden=state.view!=='benchmark';
  $('#focused-benchmark').value=state.focus;
  renderPlotOptions();
  for(const [id,key] of [['fast-profile','fast'],['small-profile','small'],['show-global','global']])$('#'+id).checked=state[key];
}
function updatePlot(){
  // Layer, profile and axis visibility do not change the measured selection.
  renderChart();renderPlotOptions();
  for(const [id,key] of [['fast-profile','fast'],['small-profile','small'],['show-global','global']])$('#'+id).checked=state[key];
}
function setLayerModes({samples=state.sampleMode,medians=state.medianMode,density=state.densityMode}={}){
  for(const mode of [samples,medians,density])layerPresentation(mode);
  const densityOnly=samples===state.sampleMode&&medians===state.medianMode;
  const previousDensity=state.densityMode;
  Object.assign(state,{sampleMode:samples,medianMode:medians,densityMode:density});
  // A visible density layer changes only its contrast. Keep its exact cells,
  // the foreground geometry, current hover/focus and sample handlers intact.
  if(densityOnly&&previousDensity!=='off'&&density!=='off'&&state.view!=='rankings'&&
      renderedDensityLayer?.parentNode===$('#chart')&&renderedDensityLayer.dataset.layerMode===previousDensity&&
      Math.max(290,$('#chart').clientWidth)===renderedChartWidth&&(innerWidth<=720)===renderedChartMobile){
    renderedDensityLayer.setAttribute('opacity',layerPresentation(density).opacity);
    renderedDensityLayer.setAttribute('data-layer-mode',density);
    renderPlotOptions();
    return;
  }
  updatePlot();
}
function renderPlotOptions(){
  const samples=$('#show-samples'),medians=$('#show-medians'),density=$('#show-density'),axes=$('#chart-axes');
  const samplesNote='Actual recorded runs: Off removes dots, Dim shows them faintly, Highlight shows them at full contrast. Independent of medians and density.';
  const medianNote='Profile summaries, benchmark medians, links, labels and SD. Independent of Samples, Density and Global median & SD.';
  const densityNote='Density of actual recorded runs, each run weighted equally. Independent of dots, medians, profiles and global overlay.';
  const axesNote='Medians fits source/profile summaries; All samples fits every recorded run and covariance envelope. Changing any layer leaves this range unchanged.';
  samples.disabled=medians.disabled=density.disabled=axes.disabled=false;
  samples.value=state.sampleMode;medians.value=state.medianMode;density.value=state.densityMode;axes.value=state.focusMeans?'means':'samples';
  $('#median-option-label').textContent=inLanguageView()?'Language median & SD':'Global median & SD';
  $('#show-global').closest('label').title='Show coordinate medians and covariance at full contrast, independently of Samples, Medians and Density.';
  for(const [input,note] of [[samples,samplesNote],[medians,medianNote],[density,densityNote],[axes,axesNote]]){
    input.closest('label').title=note;input.title=note;input.setAttribute('aria-description',note);
  }
}
function renderControls(){
  $('#loc-metric').value=state.locMetric;
  $('#formatted-loc-note').hidden=state.locMetric!=='formatted';
  const allowed=yearKeys(),enabled=effectiveLanguages();
  const active=document.activeElement;
  const focusAttribute=filterControls.contains(active)?['data-language','data-family','data-open-language','data-open-family','data-trait-option','data-benchmark-facet','data-spread','data-benchmark'].find(attribute=>active.hasAttribute(attribute)):null;
  const focusValue=focusAttribute?active.getAttribute(focusAttribute):null;
  const selectedBenchmarks=effectiveBenchmarks();
  $('#benchmark-groups').innerHTML=benchmarkDimensions.map(dimension=>`<fieldset class="trait-dimension"><legend>${esc(dimension.label)}</legend>${dimension.options.map(option=>{
    const count=data.benchmarks.filter(b=>state.benchmarks.has(b.key)&&matchesBenchmark(b.key,state.benchmarkFilters,dimension.key)&&benchmarkTraits[b.key]?.[dimension.key]?.includes(option.key)).length;
    return `<label class="trait-choice"><input type="checkbox" data-benchmark-facet="${dimension.key}:${option.key}" aria-label="Filter ${esc(dimension.label)}: ${esc(option.label)}" ${state.benchmarkFilters[dimension.key].has(option.key)?'checked':''}><span>${esc(option.label)}</span><small>${count}</small></label>`;
  }).join('')}${dimension.note?`<p>${esc(dimension.note)}</p>`:''}</fieldset>`).join('');
  $('#benchmark-filter-status').textContent=`${selectedBenchmarks.size} matching benchmarks`;
  $('#clear-benchmark-filters').disabled=!benchmarkDimensions.some(({key})=>state.benchmarkFilters[key].size);
  $('#benchmark-controls').innerHTML=data.benchmarks.map(b=>{
    const matches=matchesBenchmark(b.key,state.benchmarkFilters);
    return `<div class="control-row ${matches?'':'benchmark-excluded'}"><input type="checkbox" data-benchmark="${b.key}" aria-label="Include ${esc(b.title)}" ${selectedBenchmarks.has(b.key)?'checked':''} ${matches?'':'disabled'}><button class="benchmark-name ${state.focus===b.key&&state.view==='benchmark'?'active':''}" data-inspect-benchmark="${b.key}">${esc(b.title)}</button></div>`;
  }).join('');
  const languageRow=(l,child=false)=>`<div class="control-row ${child?'variant-row':''} ${allowed.has(l.key)?'':'year-excluded'} ${matchesTraits(traits.get(l.key),state.traits)?'':'trait-excluded'}"><input type="checkbox" data-language="${l.key}" aria-label="Include ${esc(shortName(l.key))}" ${enabled.has(l.key)?'checked':''} ${!matchesTraits(traits.get(l.key),state.traits)||!allowed.has(l.key)||state.view==='mech'&&!isMechLanguage(l.key)?'disabled':''}><button class="language-name ${child?'':'family-name'} ${focusKeys().has(l.key)?'active':''}" data-open-language="${l.key}" title="Open ${esc(shortName(l.key))} timings and programs"><span class="color-key" style="${colorKeyStyle(l.key)}"></span><span>${esc(child?l.variant_label:shortName(l.key))}${child?'':`<small class="release-label">${l.release_year}</small>`}${l.timed_benchmarks.length<10?`<small class="coverage-label" title="${esc(l.coverage_note??'Incomplete measured coverage')}">${l.timed_benchmarks.length}/10 admitted</small>`:''}</span></button><button class="spread-toggle" data-spread="${l.key}" aria-label="Toggle ${esc(shortName(l.key))} standard deviation" aria-pressed="${state.ellipses.has(l.key)}" title="${esc(shortName(l.key))}: standard-deviation ellipses" ${!enabled.has(l.key)||state.view==='mech'&&!isMechLanguage(l.key)?'disabled':''}><svg viewBox="0 0 28 18" aria-hidden="true"><ellipse cx="14" cy="9" rx="11" ry="5.5" transform="rotate(-22 14 9)" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="14" cy="9" r="1.5" fill="currentColor"/></svg></button></div>`;
  $('#language-controls').innerHTML=families().map(family=>{
    if(family.members.length===1)return `<div class="language-family" data-language-family="${family.key}">${languageRow(family.members[0])}</div>`;
    const eligible=family.members.filter(l=>matchesTraits(traits.get(l.key),state.traits)&&allowed.has(l.key)&&(state.view!=='mech'||isMechLanguage(l.key))),count=eligible.filter(l=>enabled.has(l.key)).length;
    const expanded=!state.collapsedFamilies.has(family.key),first=family.members[0];
    return `<div class="language-family" data-language-family="${family.key}"><div class="control-row family-row ${eligible.length?'':'year-excluded'}"><input type="checkbox" data-family="${family.key}" aria-label="Include all ${esc(family.label)} variants" ${count&&count===eligible.length?'checked':''} ${eligible.length?'':'disabled'}><button class="language-name family-name ${family.members.some(l=>focusKeys().has(l.key))?'active':''}" data-open-family="${family.key}" title="Open all ${esc(family.label)} execution variants"><span class="color-key" style="${colorKeyStyle(first.key)}"></span><span>${esc(family.label)}<small class="release-label">${first.release_year}</small></span></button><button class="family-disclosure" data-toggle-family="${family.key}" aria-label="${expanded?'Collapse':'Expand'} ${esc(family.label)} variants" aria-expanded="${expanded}" aria-controls="variants-${family.key}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 3 10 8 5 13"/></svg></button></div><div class="family-variants" id="variants-${family.key}" ${expanded?'':'hidden'}>${family.members.map(l=>languageRow(l,true)).join('')}</div></div>`;
  }).join('');
  for(const input of document.querySelectorAll('[data-family]')){
    const family=families().find(f=>f.key===input.dataset.family);
    const eligible=family.members.filter(l=>matchesTraits(traits.get(l.key),state.traits)&&allowed.has(l.key)&&(state.view!=='mech'||isMechLanguage(l.key))),count=eligible.filter(l=>enabled.has(l.key)).length;
    input.indeterminate=count>0&&count<eligible.length;
  }
  $('#language-groups').innerHTML=traitDimensions.map(dimension=>`<fieldset class="trait-dimension"><legend>${esc(dimension.label)}</legend>${dimension.options.map(option=>{
    const count=data.languages.filter(l=>allowed.has(l.key)&&state.languages.has(l.key)&&matchesTraits(traits.get(l.key),state.traits,dimension.key)&&traits.get(l.key)[dimension.key].has(option.key)).length;
    return `<label class="trait-choice"><input type="checkbox" data-trait-dimension="${dimension.key}" data-trait-option="${dimension.key}:${option.key}" aria-label="Filter ${esc(dimension.label)}: ${esc(option.label)}" ${state.traits[dimension.key].has(option.key)?'checked':''} ${state.view==='mech'?'disabled':''}><span>${esc(option.label)}</span><small>${count}</small></label>`;
  }).join('')}${dimension.note?`<p>${esc(dimension.note)}</p>`:''}</fieldset>`).join('');
  $('#trait-filter-status').textContent=`${enabled.size} matching variants`;
  $('#clear-traits').disabled=state.view==='mech'||!traitDimensions.some(({key})=>state.traits[key].size);
  if(focusAttribute)filterControls.querySelector(`[${focusAttribute}="${focusValue}"]`)?.focus({preventScroll:true});
}
function currentEntries(){
  if(state.view!=='benchmark')return model.entries;
  if(benchmarkEntries===null)benchmarkEntries=effectiveBenchmarks().has(state.focus)?
    comparison(plotData(),{benchmarks:new Set([state.focus]),languages:effectiveLanguages(),disabled:state.disabled}).entries:[];
  return benchmarkEntries;
}
function currentSampleInputs(entries=currentEntries()){
  if(sampleInputsByEntries.has(entries))return sampleInputsByEntries.get(entries);
  const languageView=inLanguageView(),selectedKeys=focusKeys();
  const inputs=recordedSamplePoints(entries,{disabled:state.disabled,programsForInput:(input,entry)=>
    (languageView&&selectedKeys.has(entry.language.key)?benchmarkPrograms(input.benchmark.key,entry.language.key):input.programs)
      .filter(program=>program.language===entry.language.key&&program.benchmark===input.benchmark.key).map(sampleProgram)});
  sampleInputsByEntries.set(entries,inputs);
  return inputs;
}
function selectedPlotDomain(){
  const metricDomain=metric=>inLanguageView()?languageViewDomain(metric):
    state.languageFocus?.comparisonProgram?sourceComparisonDomain(metric):chartDomain(axisData(data,metric),{...state,benchmarks:effectiveBenchmarks()});
  const canonical=metricDomain('canonical'),formatted=metricDomain('formatted'),selected=state.locMetric==='formatted'?formatted:canonical;
  // LOC changes its own normalization. All timing records and time baselines
  // remain fixed; use one time extent for both source metrics and all layers.
  return {...selected,yMin:Math.min(canonical.yMin,formatted.yMin),yMax:Math.max(canonical.yMax,formatted.yMax)};
}
function densityField(inputs,domain){
  if(densityCache?.inputs!==inputs)densityCache={inputs,points:sampleDensityPoints(inputs),fields:new Map()};
  const key=JSON.stringify([domain.xMin,domain.xMax,domain.yMin,domain.yMax]);
  if(!densityCache.fields.has(key)){
    if(densityCache.fields.size===4)densityCache.fields.delete(densityCache.fields.keys().next().value);
    densityCache.fields.set(key,densityGrid(densityCache.points,domain));
  }
  return densityCache.fields.get(key);
}
function currentDensityField(){return densityField(currentSampleInputs(),selectedPlotDomain());}
function currentGlobalStatistics(entries=currentEntries()){
  if(!globalStatisticsByEntries.has(entries))globalStatisticsByEntries.set(entries,globalStatistics(entries));
  return globalStatisticsByEntries.get(entries);
}
function openPoint(info){
  closeFilterDrawer();
  const explicit=catalogProgram(info.program);
  state.detail={language:explicit?.language??info.language,benchmark:explicit?.benchmark??info.benchmark??state.focus,kind:info.kind??'fast',
    program:info.program??null,aggregate:!!info.aggregate,file:0};
  if(!benchmark(state.detail.benchmark))state.detail.benchmark=data.benchmarks[0].key;
  if(!explicit&&!benchmark(state.detail.benchmark).groups.some(g=>g.language===state.detail.language))state.detail.benchmark=data.benchmarks.find(b=>b.groups.some(g=>g.language===state.detail.language)).key;
  if(state.languageFocus&&focusKeys().has(state.detail.language)){
    state.languageFocus.program=selectedProgram()?.key??null;
    state.languageFocus.variant=state.detail.language;state.languageFocus.benchmark=state.detail.benchmark;
  }
  renderInspector();
  if(!$('#inspector').open){
    $('#chart-detail-layout').classList.add('inspector-open');
    $('#inspector').show();
    renderChart();
  }
  clearHoverDetails();
  $('#close-inspector').focus({preventScroll:true});
}
function closeInspector(){
  $('#inspector').close();
  $('#chart-detail-layout').classList.remove('inspector-open');
  renderChart();
}
function clearHoverDetails(){
  const details=$('#hover-details');
  details.textContent='Hover a point or line for details.';
  details.classList.remove('active');
}
function showHoverDetails(description){
  const details=$('#hover-details');
  if(details.textContent!==description)details.textContent=description;
  details.classList.add('active');
}
function renderChart(){
  // The Rankings tab has no visible scatter plot. Rebuild it when that view
  // is shown again, including any selection changes made while it was hidden.
  if(state.view==='rankings')return;
  // Cached circles must not keep a retired plot, its handlers or its sibling
  // SVG tree alive. They are attached only to the current visible sample layer.
  if(renderedSamplePlot){renderedSamplePlot.replaceChildren();renderedSamplePlot=null;}
  const svg=$('#chart');svg.replaceChildren();renderedDensityLayer=null;
  const languageView=inLanguageView(),selectedKeys=focusKeys();
  svg.classList.remove('median-focus');
  delete svg.dataset.highlightLanguage;svg.onpointerleave=null;clearHoverDetails();
  const entries=currentEntries(),isMech=state.view==='mech',single=state.view==='benchmark',density=densityVisible();
  const selectedComparison=state.languageFocus?.comparison?catalogProgram(state.languageFocus.comparisonProgram):null;
  const pairComparison=state.languageFocus?.comparisonLanguage&&state.languageFocus.comparison&&!single;
  const sampleInputs=currentSampleInputs(entries);
  const layers=chartLayerState({samples:state.sampleMode,medians:state.medianMode,density:state.densityMode,fast:state.fast,small:state.small,global:state.global,sampleCount:sampleInputs.length,entryCount:entries.length});
  const rawSamples=layers.showSamples?sampleInputs:[];
  const selectedBenchmarks=effectiveBenchmarks();
  $('#chart-title').textContent=pairComparison?`${shortName(state.languageFocus.variant)} and ${shortName(state.languageFocus.comparisonLanguage)} · ${selectedBenchmarks.size} shared benchmarks`:languageView?`${state.languageFocus.label} across selected benchmarks`:single?benchmark(state.focus).title:isMech?'Mech across selected benchmarks':`${selectedBenchmarks.size} selected benchmark${selectedBenchmarks.size===1?'':'s'}`;
  if(isMech){
    $('#chart-subtitle').innerHTML=mechKeys().map(key=>`<span class="mech-mode-key" data-mode-key="${key}" style="color:${displayColor(key)}"><svg width="22" height="8" viewBox="0 0 22 8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke="currentColor" stroke-width="2.5" ${lineDash(key)?`stroke-dasharray="${lineDash(key)}"`:''}/></svg>${esc(language(key).variant_label)}</span>`).join('')+'<span>Benchmark endpoints</span>';
  }else{
    const selectedSource=state.languageFocus?.comparison?catalogProgram(state.languageFocus.comparisonProgram):null;
    $('#chart-subtitle').textContent=languageView?'Highlighted program medians, individual runs and benchmark covariance · other languages provide context':single?`${selectedSource?`${selectedSource.id} · selected source · `:''}${benchmark(state.focus).workload}`:entries.some(partialEntry)?'Equal-weight geometric means · partial suites labelled n/selected':'Equal-weight geometric means · selected benchmark subset';
  }
  const empty=layers.empty;
  $('#empty-state').hidden=!empty;
  $('#empty-state').textContent=single&&!selectedBenchmarks.has(state.focus)?'Include this benchmark and adjust its category filters to show it on the chart.':!selectedBenchmarks.size?'Select a benchmark or clear its category filters.':entries.length&&!layers.showSamples&&!layers.showMedians&&!layers.showDensity&&!layers.showGlobal?'Enable Global median & SD, or choose Dim or Highlight for Samples, Medians or Density.':state.languages.size&&!allSelection().languages.size?'No enabled languages match this release-year window. Adjust either handle or choose All years.':'No measured comparisons. Enable a language or restore its programs.';
  const width=Math.max(290,svg.clientWidth),height=innerWidth<=720?Math.max(330,width*.86):Math.min(690,Math.max(440,width*.59));
  renderedChartWidth=width;renderedChartMobile=innerWidth<=720;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.style.aspectRatio=`${width}/${height}`;
  const margins={left:innerWidth<=720?75:80,right:25,top:30,bottom:72};
  const w=width-margins.left-margins.right,h=height-margins.top-margins.bottom;
  const visibleKinds=['fast','small'].filter(k=>state[k]);
  const overlayEntries=!layers.showGlobal?[]:languageView?
    entries.filter(e=>selectedKeys.has(e.language.key)).map(entry=>({entry,statistics:languageMedianStatistics(entry)})):
    [{entry:null,statistics:currentGlobalStatistics(entries)}];
  const globalNote=$('#global-statistics-note');
  globalNote.classList.toggle('inactive',!layers.showGlobal||empty);
  globalNote.setAttribute('aria-hidden',!layers.showGlobal||empty);
  globalNote.innerHTML=languageView?'Language coordinate medians · 1σ / 2σ covariance across measured benchmarks · run-to-run SD is in the timings table':`Global median: <span style="color:#edf3f6;opacity:${state.fast?1:.4}">Fastest</span> / <span style="color:#f6c04e;opacity:${state.small?1:.4}">Fewest LOC</span> · 1σ / 2σ covariance · <span class="global-count">${entries.length}</span> visible variants`;
  const shapes=[];
  if(layers.showMedians&&!single)for(const sigma of [2,1])for(const entry of entries)if(state.ellipses.has(entry.language.key)&&!(languageView&&state.global&&selectedKeys.has(entry.language.key)))for(const kind of visibleKinds){
    const region=(sigma===2?entry.spread2:entry.spread)[kind];if(region)shapes.push({entry,kind,region,sigma});
  }
  const domainKey=JSON.stringify([state.locMetric,state.view,state.focusMeans,single?state.focus:[...selectedBenchmarks].sort(),languageView?[...selectedKeys].sort():null,state.languageFocus?.comparisonProgram??null]);
  if(!domains.has(domainKey))domains.set(domainKey,selectedPlotDomain());
  currentDomain=domains.get(domainKey);
  svg.dataset.locMetric=state.locMetric;
  const {xMin:xmin,xMax:xmax,yMin:ymin,yMax:ymax}=currentDomain;
  for(const [key,value] of Object.entries(currentDomain))svg.dataset[key]=value;
  const dx=xmax-xmin,dy=ymax-ymin;
  const X=x=>margins.left+(Math.log2(x)-xmin)/dx*w,Y=y=>margins.top+h-(Math.log2(y)-ymin)/dy*h;
  const defs=node('defs',{},svg),clip=node('clipPath',{id:'plot-clip'},defs);
  node('rect',{x:margins.left,y:margins.top,width:w,height:h},clip);
  const baselineClip=node('clipPath',{id:'baseline-clip'},defs);
  node('rect',{x:X(1),y:margins.top,width:margins.left+w-X(1),height:Y(1)-margins.top},baselineClip);
  $('#density-legend').hidden=!density;
  if(density){
    const field=densityField(sampleInputs,currentDomain);
    const heat=node('g',{class:'density-field','clip-path':'url(#plot-clip)','pointer-events':'none',opacity:layers.densityLayer.opacity,
      'data-layer':'density','data-layer-mode':state.densityMode,'data-density-variants':field.variants,'data-density-runs':field.runs,'data-density-programs':field.programs,'data-density-peak':field.peak},svg);
    renderedDensityLayer=heat;
    const stops=[[21,27,33],[30,92,122],[48,176,160],[246,192,78]];
    const color=value=>{
      const scaled=field.peak?Math.sqrt(value/field.peak)*3:0,index=Math.min(2,Math.floor(scaled)),fraction=scaled-index;
      return `rgb(${stops[index].map((v,i)=>Math.round(v+(stops[index+1][i]-v)*fraction)).join(',')})`;
    };
    for(const cell of field.cells)node('rect',{x:margins.left+cell.column*w/field.columns,y:margins.top+h-(cell.row+1)*h/field.rows,
      width:w/field.columns+.25,height:h/field.rows+.25,fill:color(cell.value),'data-density-cell':`${cell.column}:${cell.row}`},heat);
    $('#density-population').textContent=field.runs?`${field.runs} recorded runs · ${field.programs} measured programs · ${field.variants} variants · equal run weights · smoothing ${summaryNumber(field.bandwidth_x)} × ${summaryNumber(field.bandwidth_y)} log₂ doublings. Relative intensity; dot visibility does not change density.`:'No recorded runs in the current data selection.';
  }
  for(let exponent=Math.ceil(xmin);exponent<=Math.floor(xmin+dx);exponent++){
    const value=2**exponent,x=X(value);node('line',{x1:x,x2:x,y1:margins.top,y2:margins.top+h,class:'grid-line'},svg);
    text(svg,`${summaryNumber(value)}×`,x,margins.top+h+23,{class:'tick','text-anchor':'middle'});
  }
  for(let exponent=Math.ceil(ymin);exponent<=Math.floor(ymin+dy);exponent++){
    const value=2**exponent,y=Y(value);node('line',{x1:margins.left,x2:margins.left+w,y1:y,y2:y,class:'grid-line'},svg);
    text(svg,`${summaryNumber(value)}×`,margins.left-12,y+5,{class:'tick','text-anchor':'end'});
  }
  text(svg,state.locMetric==='formatted'?'Formatted source lines / fewest formatted lines · log₂':'Canonical source lines / fewest canonical lines · log₂',margins.left+w/2,height-17,{class:'axis-title','text-anchor':'middle'});
  text(svg,'Time / fastest median · log₂',0,0,{class:'axis-title','text-anchor':'middle',transform:`translate(${innerWidth<=720?14:19} ${margins.top+h/2}) rotate(-90)`});
  if(empty)return;
  const plot=node('g',{'clip-path':'url(#plot-clip)'},svg);
  const samplePlot=node('g',{'data-layer':'samples','data-layer-mode':state.sampleMode,opacity:layers.sampleLayer.opacity},plot);
  renderedSamplePlot=samplePlot;
  const sampleRecords=new Map();
  const medianPlot=node('g',{'data-layer':'medians','data-layer-mode':state.medianMode,opacity:layers.medianLayer.opacity},plot);
  const globalPlot=node('g',{'data-layer':'global','data-layer-mode':layers.showGlobal?'highlight':'off',opacity:layers.globalLayer.opacity},plot);
  const globalRegions=node('g',{class:'global-regions','pointer-events':'none'},globalPlot);
  if(layers.showGlobal)for(const {entry,statistics} of overlayEntries)for(const kind of visibleKinds)for(const sigma of [2,1]){
    if(entry&&!state.ellipses.has(entry.language.key))continue;
    const region=(sigma===2?statistics[kind]?.spread2:statistics[kind]?.spread);if(!region)continue;
    const color=entry?displayColor(entry.language.key):kind==='fast'?'#edf3f6':'#f6c04e';
    node('path',{d:region.boundary.map((p,i)=>`${i?'L':'M'}${X(p.x)},${Y(p.y)}`).join(' ')+'Z',
      class:'global-spread','data-global-profile':kind,'data-global-sigma':sigma,
      fill:color,'fill-opacity':sigma===2?.025:.065,
      stroke:color,'stroke-opacity':sigma===2?.4:.85,
      'stroke-width':sigma===2?1:1.5,'stroke-dasharray':sigma===2?'2 5':kind==='small'?'6 4':null,
      'clip-path':languageView?null:'url(#baseline-clip)',
      'aria-label':`${entry?shortName(entry.language.key):'Global'} ${kind==='fast'?'fastest':'fewest LOC'} ${sigma}σ covariance across ${region.n} ${languageView?'benchmarks':'visible execution variants'}`},globalRegions);
  }
  const hoverSpreads=node('g',{class:'hover-spreads'},medianPlot);
  const lineLabels=[],labelObstacles=[],hitPoints=[],hitLines=[];
  const piecesByLanguage=new Map();
  let chartPieces=[];
  let hoveredLanguage=null,focusedLanguage=null,highlightedLanguage;
  function updateHighlight(){
    const key=hoveredLanguage??focusedLanguage;
    if(key===highlightedLanguage)return;
    const previous=highlightedLanguage;
    highlightedLanguage=key;
    if(key)svg.dataset.highlightLanguage=key;else delete svg.dataset.highlightLanguage;
    // A child cannot brighten above its layer's Dim opacity. Lift only an
    // already-visible sample layer during hover/focus; restore it on exit.
    samplePlot.setAttribute('opacity',key&&layers.showSamples?1:layers.sampleLayer.opacity);
    hoverSpreads.replaceChildren();
    if(layers.showMedians&&key&&!single&&!state.ellipses.has(key)){
      const entry=entries.find(item=>item.language.key===key);
      if(entry)for(const sigma of [2,1])for(const kind of visibleKinds){
        const region=(sigma===2?entry.spread2:entry.spread)[kind];
        if(region)drawSpread({entry,kind,region,sigma},hoverSpreads,true);
      }
    }
    // Once hover is active, only the old and new languages change. The node
    // index is built once per render, outside pointer/focus handlers.
    const pieces=previous&&key?[...(piecesByLanguage.get(previous)??[]),...(piecesByLanguage.get(key)??[])]:chartPieces;
    for(const {piece,language:pieceLanguage,sample,crowded} of pieces){
      const selected=key?pieceLanguage===key:languageView&&selectedKeys.has(pieceLanguage);
      if(sample&&!(previous&&key))piece.style.setProperty('--chart-opacity',key?layers.sampleLayer.opacity:1);
      piece.classList.toggle('chart-dimmed',(!!key||languageView)&&!selected);
      piece.classList.toggle('sample-highlighted',selected&&sample);
      if(crowded)piece.classList.toggle('label-revealed',selected);
    }
  }
  function highlightPointer(event,key,description){
    if(event.pointerType==='touch')return;
    hoveredLanguage=key;updateHighlight();showHoverDetails(description);
  }
  function clearHover(){hoveredLanguage=null;updateHighlight();clearHoverDetails();}
  svg.onpointerleave=clearHover;
  function pointerPosition(event){
    const transform=svg.getScreenCTM();if(!transform)return null;
    const pointer=svg.createSVGPoint();pointer.x=event.clientX;pointer.y=event.clientY;
    return pointer.matrixTransform(transform.inverse());
  }
  function closestMarker(event,fallback){
    const position=pointerPosition(event);if(!position)return fallback;
    let chosen=fallback,distance=Math.hypot(position.x-fallback.x,position.y-fallback.y);
    for(const point of hitPoints){
      if(point.faint!==fallback.faint)continue;
      const dx=position.x-point.x,dy=position.y-point.y,d=Math.hypot(dx,dy);
      const inside=point.kind==='small'?Math.abs(dx)<=point.size+.7&&Math.abs(dy)<=point.size+.7:d<=point.size+.7;
      if(inside&&d<distance-.25){chosen=point;distance=d;}
    }
    return chosen;
  }
  function closestLine(event,fallback){
    const position=pointerPosition(event);if(!position)return fallback;
    const distance=line=>{
      const dx=line.b.x-line.a.x,dy=line.b.y-line.a.y;
      const t=Math.max(0,Math.min(1,((position.x-line.a.x)*dx+(position.y-line.a.y)*dy)/(dx*dx+dy*dy)));
      return Math.hypot(position.x-line.a.x-t*dx,position.y-line.a.y-t*dy);
    };
    let chosen=fallback,nearest=distance(fallback);
    for(const line of hitLines){const d=distance(line);if(d<nearest-.25){chosen=line;nearest=d;}}
    return chosen;
  }
  function drawSpread({entry,kind,region,sigma},parent=medianPlot,hover=false){
    const d=region.boundary.map((p,i)=>`${i?'L':'M'}${X(p.x)},${Y(p.y)}`).join(' ')+'Z';
    node('path',{d,fill:displayColor(entry.language.key),'fill-opacity':sigma===2?(kind==='fast'?.035:.018):(kind==='fast'?.10:.05),
      stroke:displayColor(entry.language.key),'stroke-opacity':sigma===2?.3:.6,'stroke-width':sigma===2?.9:1.2,
      'stroke-dasharray':sigma===2?'2 5':kind==='small'?'5 4':lineDash(entry.language.key),class:'spread-area',
      'clip-path':languageView?null:'url(#baseline-clip)',
      'data-chart-language':entry.language.key,'data-spread-language':entry.language.key,'data-spread-profile':kind,'data-spread-sigma':sigma,
      'data-hover-spread':hover?'true':null,
      'aria-label':`${shortName(entry.language.key)} ${kind==='fast'?'fastest':'fewest LOC'} ${sigma}σ covariance area across ${region.n} benchmarks`},parent);
  }
  for(const shape of shapes)drawSpread(shape);
  // Wide line hover targets sit below every marker, preserving point clicks.
  const connectorHits=node('g',{class:'connector-hit-regions'},medianPlot);
  function marker(point,entry,kind,{faint=false,mean=false,program=null,benchmarkKey=null,label=null}={}){
    if(!layers.showMedians)return null;
    const color=displayColor(entry.language.key),size=faint?3.3:mean?state.ellipses.has(entry.language.key)?8.5:7.2:7;
    const attrs={fill:color,stroke:mean&&state.ellipses.has(entry.language.key)?'#f3f3e6':color,'stroke-width':mean?1:.7,
      opacity:1,class:`endpoint ${mean?'mean-mark':''}`,'data-language':entry.language.key,'data-profile':kind,
      'data-chart-language':entry.language.key,style:'--chart-opacity:1',
      'data-program':program?.key??null,'data-mean':mean?'true':null,'data-profile-median':'true',tabindex:0,role:'button'};
    const name=label??`${shortName(entry.language.key)} · ${kind==='fast'?'fastest':'fewest LOC'}`;
    const description=program?`${name}\n${benchmark(benchmarkKey).title} · ${program.loc} LOC · ${seconds(program.seconds)}\n${program.samples.length} ${program.timing_alias_of?'shared timing samples':'timing samples'}`:`${name}\n${ratio(point.x)} LOC · ${ratio(point.y)} time\n${coverageLabel(entry)} selected benchmarks${partialEntry(entry)?` · missing ${missingNames(entry)}`:''}`;
    attrs['aria-label']=description.replaceAll('\n',', ');
    const mark=kind==='small'?node('rect',{...attrs,x:X(point.x)-size,y:Y(point.y)-size,width:size*2,height:size*2},medianPlot):node('circle',{...attrs,cx:X(point.x),cy:Y(point.y),r:size},medianPlot);
    if(!faint)labelObstacles.push({x:X(point.x)-size-2,y:Y(point.y)-size-2,width:size*2+4,height:size*2+4});
    const info={language:entry.language.key,kind,program:program?.key,benchmark:benchmarkKey,aggregate:mean};
    const hit={x:X(point.x),y:Y(point.y),size,faint,kind,info,description};hitPoints.push(hit);
    // Dense means can overlap. Pick the closest visible center within that
    // marker layer instead of whichever SVG element happens to be on top.
    mark.addEventListener('click',event=>openPoint(closestMarker(event,hit).info));
    mark.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();openPoint(info);}});
    const hover=event=>{const nearest=closestMarker(event,hit);highlightPointer(event,nearest.info.language,nearest.description);};
    mark.addEventListener('pointerenter',hover);mark.addEventListener('pointermove',hover);
    mark.addEventListener('pointerleave',clearHover);
    mark.addEventListener('focus',()=>{focusedLanguage=entry.language.key;updateHighlight();showHoverDetails(description);});
    mark.addEventListener('blur',()=>{focusedLanguage=null;updateHighlight();clearHoverDetails();});
    return mark;
  }
  function pair(entry,fast,small,{mean=false,faint=false,benchmarkKey=null,label=null}={}){
    if(!layers.showMedians)return;
    if(state.fast&&state.small&&!same(fast,small)){
      const geometry={x1:X(small.x),y1:Y(small.y),x2:X(fast.x),y2:Y(fast.y)};
      node('line',{...geometry,stroke:displayColor(entry.language.key),
        'stroke-width':mean&&isMechLanguage(entry.language.key)?2.8:1.9,'stroke-dasharray':lineDash(entry.language.key),opacity:faint?.15:1,
        class:'connector','data-chart-language':entry.language.key,style:`--chart-opacity:${faint?.15:1}`},medianPlot);
      const hit={a:{x:geometry.x1,y:geometry.y1},b:{x:geometry.x2,y:geometry.y2},language:entry.language.key,
        description:`${label??shortName(entry.language.key)}\nFastest: ${ratio(fast.x)} LOC · ${ratio(fast.y)} time\nFewest LOC: ${ratio(small.x)} LOC · ${ratio(small.y)} time`};
      hitLines.push(hit);
      const target=node('line',{...geometry,class:'connector-hit','data-chart-language':entry.language.key,'data-connector-mean':mean},connectorHits);
      const hover=event=>{const nearest=closestLine(event,hit);highlightPointer(event,nearest.language,nearest.description);};
      target.addEventListener('pointerenter',hover);target.addEventListener('pointermove',hover);target.addEventListener('pointerleave',clearHover);
    }
    if(state.small&&(!state.fast||!same(fast,small)))marker(small,entry,'small',{faint,mean,program:mean?null:small,benchmarkKey});
    if(state.fast)marker(fast,entry,'fast',{faint,mean,program:mean?null:fast,benchmarkKey,label});
    if(label&&!faint&&(state.fast||state.small)){
      const a=state.small?small:fast,b=state.fast?fast:small;
      lineLabels.push({label,language:entry.language.key,benchmark:benchmarkKey,a:{x:X(a.x),y:Y(a.y)},b:{x:X(b.x),y:Y(b.y)}});
    }
  }
  // Recorded runs supply the background cloud. Keep summary endpoints in Medians.
  for(const point of rawSamples){
    const {program,entry,benchmark:inputBenchmark,run:runNumber,elapsed}=point;
    // Runs share the program's actual source coordinate; no jitter or invented values.
    if(!sampleNodes.has(program.key))sampleNodes.set(program.key,new Map());
    const programNodes=sampleNodes.get(program.key);
    if(!programNodes.has(runNumber))programNodes.set(runNumber,{node:node('circle',{
      r:2.4,fill:'none','stroke-width':1.15,class:'timing-run','data-sample':'true',
      'data-chart-language':program.language,'data-program':program.key,'data-timing-run':runNumber,
      'data-run-seconds':elapsed,'data-observation-source':timingOwner(program),style:'--chart-opacity:1',tabindex:0,role:'button'})});
    const cached=programNodes.get(runNumber),run=cached.node,x=X(point.x),y=Y(point.y),color=displayColor(entry.language.key);
    if(cached.x!==x){run.setAttribute('cx',x);cached.x=x;}
    if(cached.y!==y){run.setAttribute('cy',y);cached.y=y;}
    if(cached.color!==color){run.setAttribute('stroke',color);cached.color=color;}
    if(cached.ratioX!==point.x){run.setAttribute('data-ratio-x',point.x);cached.ratioX=point.x;}
    if(cached.loc!==program.loc||cached.ratioY!==point.y){
      cached.description=`${shortName(program.language)} · ${inputBenchmark.title}\n${program.id} · run ${runNumber}: ${seconds(elapsed)} · ${program.loc} LOC${program.timing_alias_of?` · shared from ${program.timing_alias_of}`:''}\nRun time / fixed benchmark median baseline: ${ratio(point.y)}`;
      run.setAttribute('aria-label',cached.description.replaceAll('\n',', '));
      run.setAttribute('data-ratio-y',point.y);cached.ratioY=point.y;cached.loc=program.loc;
    }
    sampleRecords.set(run,{point,description:cached.description});
    samplePlot.append(run);
  }
  // Each new layer owns its current records and handlers. Reused circles carry
  // no callbacks from earlier selections, and Off attaches no sample circles.
  const sampleFor=event=>sampleRecords.get(event.target);
  const inspectSample=record=>{const {program}=record.point;openPoint({language:program.language,benchmark:program.benchmark,program:program.key});};
  const hoverSample=event=>{const record=sampleFor(event);if(record)highlightPointer(event,record.point.program.language,record.description);};
  samplePlot.addEventListener('click',event=>{const record=sampleFor(event);if(record)inspectSample(record);});
  samplePlot.addEventListener('keydown',event=>{const record=sampleFor(event);if(record&&(event.key==='Enter'||event.key===' ')){event.preventDefault();inspectSample(record);}});
  samplePlot.addEventListener('pointerover',hoverSample);samplePlot.addEventListener('pointermove',hoverSample);
  samplePlot.addEventListener('pointerout',event=>{if(sampleFor(event))clearHover();});
  samplePlot.addEventListener('focusin',event=>{const record=sampleFor(event);if(record){focusedLanguage=record.point.program.language;updateHighlight();showHoverDetails(record.description);}});
  samplePlot.addEventListener('focusout',event=>{if(sampleFor(event)){focusedLanguage=null;updateHighlight();clearHoverDetails();}});
  if(layers.showMedians&&(languageView||selectedComparison)){
    const seenPrograms=new Set();
    for(const {program,entry} of sampleInputs){
      if(seenPrograms.has(program.key)||!(languageView?selectedKeys.has(entry.language.key):entry.language.key===selectedComparison.language))continue;
      seenPrograms.add(program.key);
      const mark=marker(program,entry,state.fast?'fast':'small',{faint:true,program,benchmarkKey:program.benchmark,label:`${shortName(program.language)} · ${program.id} median`});
      mark.classList.add('overview-program-median');mark.removeAttribute('data-sample');mark.setAttribute('tabindex','0');
    }
  }
  for(const entry of entries){
    if(single||isMech||languageView&&selectedKeys.has(entry.language.key))for(const input of entry.inputs)pair(entry,input.fast,input.small,{benchmarkKey:input.benchmark.key,label:isMech||languageView?`${input.benchmark.title} · ${entry.language.variant_label??chartName(entry.language.key)}`:chartName(entry.language.key)});
    if(!single)pair(entry,entry.fast,entry.small,{mean:true,label:isMech?`${entry.language.execution??'AOT'} geometric mean`:meanChartName(entry)});
  }
  if(layers.showGlobal)for(const {entry,statistics} of overlayEntries)for(const kind of visibleKinds){
    if(!statistics[kind])continue;
    const statistic='median',point=statistics[kind].median,x=X(point.x),y=Y(point.y),size=8;
    const name=`${entry?shortName(entry.language.key):'Global'} ${kind==='fast'?'fastest':'fewest LOC'} median`;
    const description=`${name}\n${ratio(point.x)} LOC · ${ratio(point.y)} time\n${statistics[kind].n} ${languageView?'benchmarks':'visible execution variants'}, equal weight`;
    const color=entry?displayColor(entry.language.key):kind==='fast'?'#edf3f6':'#f6c04e';
    const mark=node('path',{d:`M${x},${y-size}l${size},${size}l${-size},${size}l${-size},${-size}Z`,
      class:'global-center','data-global-profile':kind,'data-global-statistic':statistic,
      'data-ratio-x':point.x,'data-ratio-y':point.y,'data-median-language':entry?.language.key??null,fill:color,
      stroke:'#151b21','stroke-width':2,tabindex:0,role:'img','aria-label':description.replaceAll('\n',', ')},globalPlot);
    text(globalPlot,`${entry?`${entry.language.variant_label??chartName(entry.language.key)} · `:''}${kind==='fast'?'Fastest':'Fewest LOC'} median`,x+12,y-12,{class:'median-label',fill:color});
    labelObstacles.push({x:x-size-3,y:y-size-3,width:2*size+6,height:2*size+6});
    const hover=event=>{if(entry)highlightPointer(event,entry.language.key,description);else{clearHover();showHoverDetails(description);}};
    mark.addEventListener('pointerenter',hover);mark.addEventListener('pointermove',hover);mark.addEventListener('pointerleave',clearHover);
    mark.addEventListener('focus',()=>{focusedLanguage=entry?.language.key??null;updateHighlight();showHoverDetails(description);});
    mark.addEventListener('blur',()=>{focusedLanguage=null;updateHighlight();clearHoverDetails();});
  }
  // Label only the visible profiles, not their faint benchmark samples. Prefer
  // a nearby offset along the line and avoid covering another label or marker.
  const labels=node('g',{class:'line-labels'},medianPlot),pendingLabels=[];
  for(const item of lineLabels){
    // A means-focused range can crop benchmark pairs. Keep their labels with
    // their lines rather than pinning labels for offscreen pairs to the border.
    if(Math.max(item.a.x,item.b.x)<margins.left||Math.min(item.a.x,item.b.x)>margins.left+w||
      Math.max(item.a.y,item.b.y)<margins.top||Math.min(item.a.y,item.b.y)>margins.top+h)continue;
    const label=text(labels,item.label,0,0,{class:'line-label clickable-chart-label',fill:displayColor(item.language),'data-label-language':item.language,'data-chart-language':item.language,tabindex:0,role:'button','aria-label':item.benchmark?`Inspect ${shortName(item.language)} ${benchmark(item.benchmark).title}`:`Open ${shortName(item.language)} language overview`});
    const activate=()=>item.benchmark?openPoint({language:item.language,benchmark:item.benchmark}):showLanguageOverview(item.language);
    label.addEventListener('click',activate);label.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();activate();}});
    label.addEventListener('pointerenter',event=>highlightPointer(event,item.language,item.benchmark?`${shortName(item.language)} · ${benchmark(item.benchmark).title}\nClick to inspect its programs.`:`${shortName(item.language)}\nClick for all timings, programs and comparisons.`));label.addEventListener('pointerleave',clearHover);
    label.addEventListener('focus',()=>{focusedLanguage=item.language;updateHighlight();showHoverDetails(item.benchmark?`${shortName(item.language)} · ${benchmark(item.benchmark).title}\nPress Enter to inspect its programs.`:`${shortName(item.language)}\nPress Enter for all timings, programs and comparisons.`);});label.addEventListener('blur',()=>{focusedLanguage=null;updateHighlight();clearHoverDetails();});
    pendingLabels.push({item,label});
  }
  // Attach all text, measure it together, then position it. Alternating each
  // SVG insertion/getBBox/write forces a separate layout for every label.
  const measuredLabels=pendingLabels.map(value=>({...value,box:value.label.getBBox()}));
  const placeLabel=createLabelPlacer({left:margins.left,top:margins.top,width:w,height:h,obstacles:labelObstacles});
  for(const {item,label,box} of measuredLabels){
    const lw=box.width,lh=box.height;
    const best=placeLabel(item,box);
    label.setAttribute('x',best.x-box.x);label.setAttribute('y',best.y-box.y);
    const crowded=w<500&&best.collisions>0;
    label.classList.toggle('label-crowded',crowded);
    const nearest={x:Math.max(best.x,Math.min(best.x+lw,best.anchor.x)),y:Math.max(best.y,Math.min(best.y+lh,best.anchor.y))};
    if(Math.hypot(nearest.x-best.anchor.x,nearest.y-best.anchor.y)>19){
      const guide=node('line',{x1:best.anchor.x,y1:best.anchor.y,x2:nearest.x,y2:nearest.y,stroke:displayColor(item.language),class:'label-guide','data-chart-language':item.language},labels);
      guide.classList.toggle('label-crowded',crowded);
      labels.insertBefore(guide,label);
    }
  }
  if(single)text(svg,`${state.locMetric==='formatted'?benchmark(state.focus).baseline_formatted_loc??'—':benchmark(state.focus).baseline_loc} ${metricName()} baseline · ${seconds(benchmark(state.focus).baseline_seconds)} time baseline`,margins.left,16,{class:'chart-symbol-legend'});
  else if(shapes.length){
    const counts=shapes.map(s=>s.region.n),min=Math.min(...counts),max=Math.max(...counts);
    text(svg,`${new Set(shapes.map(s=>s.entry.language.key)).size} language spread${new Set(shapes.map(s=>s.entry.language.key)).size===1?'':'s'} · n = ${min===max?min:`${min}–${max}`}`,margins.left,16,{class:'chart-symbol-legend'});
  }
  chartPieces=[...plot.querySelectorAll('[data-chart-language]')].map(piece=>({piece,language:piece.dataset.chartLanguage,sample:piece.classList.contains('timing-run'),crowded:piece.classList.contains('label-crowded')}));
  for(const item of chartPieces){
    if(!piecesByLanguage.has(item.language))piecesByLanguage.set(item.language,[]);
    piecesByLanguage.get(item.language).push(item);
  }
  updateHighlight();
}
function renderTable(){
  const entries=sortedRows('comparison',currentEntries().map(entry=>({...entry,metrics:comparisonMetrics(entry)})),(entry,key)=>key==='language'?shortName(entry.language.key):entry.metrics[key]);
  $('#mean-table thead').innerHTML='<tr>'+[
    sortHeader('comparison','language','Language'),
    sortHeader('comparison','loc',state.locMetric==='formatted'?'Formatted LOC ×':'Canonical LOC ×'),sortHeader('comparison','fastest','Time × best'),
    sortHeader('comparison','slope','Slope'),sortHeader('comparison','length','Length'),
    sortHeader('comparison','areaFast','2σ area','Fastest'),
    sortHeader('comparison','areaSmall','2σ area','Fewest LOC')].join('')+'</tr>';
  const slope=value=>value==null?'—':Number.isFinite(value)?summaryNumber(value):value<0?'−∞':'∞';
  const area=value=>value==null?'—':summaryNumber(value);
  $('#mean-table tbody').innerHTML=entries.map(entry=>`<tr><td><button data-table-language="${entry.language.key}" class="table-language"><span class="color-key" style="${colorKeyStyle(entry.language.key)}"></span>${esc(shortName(entry.language.key))}${partialEntry(entry)?` <small class="coverage-badge" title="${esc(`${coverageLabel(entry)} selected benchmarks; missing ${missingNames(entry)}`)}">${coverageLabel(entry)}</small>`:''}</button></td><td class="ratio">${ratio(entry.metrics.loc)}</td><td class="ratio">${ratio(entry.metrics.fastest)}</td><td class="ratio" title="${entry.metrics.slope==null?'Same endpoint: no line slope':'Change in log₂ time divided by change in log₂ LOC'}">${slope(entry.metrics.slope)}</td><td class="ratio" title="Euclidean distance between endpoints in log₂ coordinates">${summaryNumber(entry.metrics.length)}</td><td class="ratio" data-area-profile="fast" title="Fastest-profile 2σ covariance ellipse area in squared doublings">${area(entry.metrics.areaFast)}</td><td class="ratio" data-area-profile="small" title="Fewest-LOC-profile 2σ covariance ellipse area in squared doublings">${area(entry.metrics.areaSmall)}</td></tr>`).join('');
}
function selectedProgram(){
  if(state.detail.program)return catalogProgram(state.detail.program);
  const viewData=plotData();
  const group=viewData.benchmarks.find(b=>b.key===state.detail.benchmark)?.groups.find(g=>g.language===state.detail.language);
  if(!group)return null;
  let candidates=group.programs.filter(k=>!state.disabled.has(k)).map(k=>viewData.programs[k]).filter(p=>eligibleForChart(p)&&Number.isFinite(p.loc)&&p.loc>0&&Number.isFinite(p.x)&&p.x>0);
  if(!candidates.length){
    const original=comparisonData().benchmarks.find(b=>b.key===state.detail.benchmark)?.groups.find(g=>g.language===state.detail.language);
    return catalogProgram(original?.[state.detail.kind]??original?.small);
  }
  if(state.detail.kind==='fast'&&candidates.some(p=>p.seconds!=null))candidates=candidates.filter(p=>p.seconds!=null);
  const selected=candidates.reduce((a,b)=>state.detail.kind==='fast'?(b.seconds<a.seconds||b.seconds===a.seconds&&b.loc<a.loc?b:a):(b.loc<a.loc||b.loc===a.loc&&b.seconds<a.seconds?b:a));
  return catalogProgram(selected.key);
}
function renderAliasDisclosure(program){
  if(program.timing_alias_of){
    const owner=catalogProgram(program.timing_alias_of);
    const target=owner?`<button data-inspect-program="${esc(owner.key)}">${esc(owner.id)}</button>`:esc(program.timing_alias_of);
    return `<p class="profile-note timing-alias">Reuses the ${program.samples.length} runs recorded for ${target}; no additional runs.</p>`;
  }
  if(program.source_alias_of){
    const reference=program.source_alias_of;
    const owner=catalogProgram(reference)??benchmarkPrograms(program.benchmark,program.language).find(p=>p.id===reference);
    const target=owner&&owner.key!==program.key?`<button data-inspect-program="${esc(owner.key)}">${esc(owner.id)}</button>`:esc(reference);
    return `<p class="profile-note source-alias">Shares authored source with ${target}.${measuredTiming(program)?' Its recorded timings are independent.':''}</p>`;
  }
  return '';
}
function programSource(program,key){
  const file=data.files[key],metadata=program.file_roles?.[key];
  const details=metadata&&typeof metadata==='object'?metadata:{};
  const sourceURL=details.source_path&&data.repository?.url?`${data.repository.url.replace(/\/$/,'')}/blob/main/${details.source_path.split('/').map(encodeURIComponent).join('/')}`:program.source_url;
  return {...file,...details,role:typeof metadata==='string'?metadata:details.role??file.role,source_url:sourceURL};
}
function sourceRoleLabel(role){
  return role==='runtime-support'?' · runtime support':role==='application-helper'?' · application helper':role==='application-launcher'?' · application launcher':'';
}
function renderLocAudit(program){
  if(!Array.isArray(program.loc_expansions)||!program.loc_expansions.length)return '';
  if(program.loc_expansion_format!=='source-bound-canonical-owner-audit-v1'&&program.loc_expansions?.some(source=>typeof source.source==='string'&&Array.isArray(source.expansions))){
    return `<details class="loc-audit"><summary>LOC audit: ${program.physical_loc} physical lines → ${program.loc} canonical LOC</summary><p class="profile-note">Counts include every authored source and helper. The recorded line entries show canonical units, including wrapped lines counted within another entry.</p>${program.loc_expansions.map(source=>{
      const key=program.files.find(key=>source.source.endsWith('/'+data.files[key].path));
      const file=key?programSource(program,key):null;
      const name=file?.name??source.source.split('/').pop();
      return `<details><summary>${esc(name)}${sourceRoleLabel(file?.role)}${file?.normalized_loc!=null?` · ${file.physical_loc} physical lines → ${file.normalized_loc} canonical LOC`:''}</summary>${source.expansions.map(entry=>`<p class="profile-note">Line ${entry.line} · ${entry.units} canonical LOC</p><pre>${esc(entry.original??entry.reason??'')}</pre>`).join('')}</details>`;
    }).join('')}</details>`;
  }
  if(program.loc_expansion_format==='source-bound-canonical-owner-audit-v1'){
    return `<details class="loc-audit"><summary>LOC audit: ${program.physical_loc} physical lines → ${program.loc} canonical LOC</summary><p class="profile-note">Reviewed owners from every counted source and helper. Owner units are shown directly; they are not inferred extra physical lines.</p>${program.loc_expansions.map(source=>{
      const file=data.files[source.sha256];
      const owners=source.source_language==='gleam'?source.expansions:source.canonical_events;
      return `<details><summary>${esc(source.name)} · ${source.physical_loc} physical lines → ${source.normalized_loc} canonical LOC</summary>${owners.map(owner=>{
        const start=source.source_language==='gleam'?owner.full_owner_start:owner.start;
        const line=file.code.slice(0,start).split('\n').length;
        return `<p class="profile-note">Line ${line} · ${esc(owner.kind)} · ${owner.units} canonical LOC${owner.units===0?' (structural, uncounted)':''}</p><pre>${esc(owner.original_source)}</pre>`;
      }).join('')}</details>`;
    }).join('')}</details>`;
  }
  return program.physical_loc!=null&&program.physical_loc!==program.loc?`<details class="loc-audit"><summary>LOC audit: ${program.physical_loc} physical lines → ${program.loc} normalized LOC</summary><p class="profile-note">Packed sequential statements and nested assignments count separately. The original source is preserved below.</p>${program.loc_expansions.map(e=>`<p class="profile-note">Source line ${e.line}: ${e.extra_lines} extra LOC</p><pre>${esc(Array.isArray(e.units)?e.units.join('\n'):e.reason??e.original??'')}</pre>`).join('')}</details>`:'';
}
function renderInspector({renderRelated=true}={}){
  const program=selectedProgram();
  if(!program){$('#inspector-context').textContent='Program unavailable';$('#inspector-title').textContent='Program details';$('#inspector-body').replaceChildren();return;}
  const b=benchmark(program.benchmark),lang=language(program.language),group=b.groups.find(g=>g.language===program.language);
  const entry=model.entries.find(e=>e.language.key===program.language);
  const pending=program.seconds==null;
  if(inLanguageView()&&focusKeys().has(program.language)){
    state.languageFocus.program=program.key;state.languageFocus.variant=program.language;state.languageFocus.benchmark=program.benchmark;
  }
  if(pending)state.detail.kind='small';
  const available=data.benchmarks.filter(item=>item.groups.some(g=>g.language===program.language)||benchmarkPrograms(item.key,program.language).length);
  $('#inspector-context').textContent=state.detail.aggregate?'Geometric mean contributors':b.title;
  $('#inspector-title').textContent=lang.label;
  const aggregate=state.detail.aggregate&&entry?`<p class="profile-note">${state.detail.kind==='fast'?'Fastest':'Fewest-LOC'} profile: <strong>${ratio(entry[state.detail.kind].x)} LOC · ${ratio(entry[state.detail.kind].y)} time</strong>, geometric means across ${coverageLabel(entry)} selected benchmarks.${partialEntry(entry)?` Missing: ${esc(missingNames(entry))}.`:''} Choose a benchmark below to inspect a contributor.</p>`:'';
  const file=programSource(program,program.files[Math.min(state.detail.file,program.files.length-1)]);
  if(tableSort.timings.key==='wall_seconds')tableSort.timings.key='elapsed';
  const samples=sortedRows('timings',program.samples.map((elapsed,i)=>({...program.sample_details?.[i],run:i+1,elapsed})),(sample,key)=>sample[key]);
  const availablePrograms=benchmarkPrograms(b.key,program.language);
  const implementations=sortedRows('implementations',availablePrograms,(item,key)=>({show:state.disabled.has(item.key)?1:0,program:item.id,loc:item.loc,median:item.seconds})[key]);
  const canonicalProgram=group?.programs.includes(program.key)??false;
  const browsing=state.languageFocus&&focusKeys().has(program.language)?focusPrograms():availablePrograms;
  const browsingIndex=browsing.findIndex(p=>p.key===program.key);
  const navigation=`<div class="program-navigation"><button class="quiet-button" data-step-program="-1" ${browsingIndex<=0?'disabled':''}>Previous program</button><span>${browsingIndex+1} / ${browsing.length} published programs</span><button class="quiet-button" data-step-program="1" ${browsingIndex>=browsing.length-1?'disabled':''}>Next program</button></div>${state.languageFocus&&focusKeys().has(program.language)?`<button class="inspector-comparison quiet-button" data-compare-program="${program.key}">Compare this benchmark</button>`:`<button class="inspector-comparison quiet-button" data-open-language="${program.language}">Open language overview</button>`}`;
  const bestComparison=pending||!eligibleForChart(program)?'':`<p class="profile-note best-comparison">This program: <strong>${program.seconds.toFixed(6)} s</strong> · <strong>${(program.seconds/b.baseline_seconds).toFixed(3)}× best time</strong>, against this benchmark’s fixed best-time baseline (<strong>${b.baseline_seconds.toFixed(6)} s</strong>).</p>`;
  const formattedNote=`<p class="profile-note formatted-source-count">${esc(formattedText(program))}. ${esc((program.formatted_loc_evidence?.reasons??[]).join(' '))}${state.locMetric==='formatted'&&!plottable(plotProgram(program))?' This program has no eligible formatted chart coordinate; its original source and measured timing remain available.':''}</p>`;
  $('#inspector-body').innerHTML=`${aggregate}${navigation}<div class="inspector-controls"><label>Benchmark<select id="detail-benchmark">${available.map(item=>`<option value="${item.key}" ${item.key===b.key?'selected':''}>${esc(item.title)}</option>`).join('')}</select></label><label>Profile<select id="detail-profile"><option value="fast" ${pending?'disabled':''} ${state.detail.kind==='fast'?'selected':''}>Fastest</option><option value="small" ${state.detail.kind==='small'?'selected':''}>Fewest LOC</option></select></label><label class="program-choice">Program<select id="detail-program">${availablePrograms.map(p=>`<option value="${p.key}" ${program.key===p.key?'selected':''}>${esc(p.id)} · ${p.loc} LOC · ${seconds(p.seconds)}</option>`).join('')}</select></label></div>
    ${canonicalProgram?`<label class="inclusion"><input id="include-program" type="checkbox" ${pending||!eligibleForChart(program)||inLanguageView()?'disabled':''} ${pending||!eligibleForChart(program)||state.disabled.has(program.key)?'':'checked'}>Include this program in the speed comparison${inLanguageView()?' · all published programs shown in this view':''}</label>`:'<p class="profile-note">This qualified program is retained in the language overview. The main comparison uses the published fastest and fewest-LOC endpoints.</p>'}<p class="profile-note">${esc(b.workload)}</p>
    <div class="detail-stats"><div class="detail-stat"><strong>${program.loc}</strong><span>canonical source LOC</span></div><div class="detail-stat"><strong>${formattedValue(program)}</strong><span>formatted source LOC</span></div><div class="detail-stat"><strong>${seconds(program.seconds)}</strong><span>${program.timing_alias_of?'shared median time':'median measured time'}</span></div><div class="detail-stat"><strong>${pending?'Not measured':seconds(program.timing_sd)}</strong><span>${program.timing_alias_of?'shared run-to-run SD':'run-to-run SD'}</span></div></div>
    ${formattedNote}${renderAliasDisclosure(program)}
    ${!eligibleForChart(program)?`<p class="profile-note publication-exclusion">Excluded from charts and comparisons. ${esc(program.exclusion_reason??'Publication qualification is incomplete.')} Saved timings and sources remain available for inspection.</p>`:''}
    ${bestComparison}
    ${program.timing_summary?`<p class="profile-note timing-boundary">${esc(program.timing_summary)}</p>`:''}
    <section class="detail-section"><h3>${program.timing_alias_of?'Shared recorded timing samples':'Recorded timing samples'}</h3>${pending?'<p class="profile-note">No qualified timing median is available. Any retained successful samples below do not supply a speed ratio, geometric mean, or standard-deviation ellipse.</p>':''}${program.samples.length?`<div class="timings-table-wrap"><table class="timings-table"><thead><tr>${sortHeader('timings','run','Run')}${sortHeader('timings','elapsed','Whole process seconds')}<th scope="col">${program.samples.length} ${program.timing_alias_of?'shared samples':'samples'}</th></tr></thead><tbody>${samples.map(sample=>`<tr><td>${sample.run}</td><td class="sample-value">${sample.elapsed.toFixed(6)}</td><td><div class="sample-bar" style="width:${sample.elapsed/Math.max(...program.samples)*100}%"></div></td></tr>`).join('')}</tbody></table></div>`:''}</section>
    ${renderLocAudit(program)}
    <section class="detail-section"><div class="code-toolbar"><select id="detail-file" aria-label="Source file">${program.files.map((key,i)=>`<option value="${i}" ${i===Math.min(state.detail.file,program.files.length-1)?'selected':''}>${esc(data.files[key].name)}${sourceRoleLabel(programSource(program,key).role)}</option>`).join('')}</select><a id="download-source" href="#">Download source</a>${file.source_url?`<a href="${esc(file.source_url)}" target="_blank" rel="noopener">${esc(program.source_link_label??'Upstream listing')}</a>`:''}${program.license_url?`<a href="${esc(program.license_url)}" target="_blank" rel="noopener">License</a>`:''}</div><pre><code id="source-code"></code></pre><div class="source-meta">${file.loc_note?esc(file.loc_note)+'<br>':''}Verified source SHA-256: ${file.sha256}<br>Timing report: ${esc(program.report)}</div></section>
    ${program.local_adaptation?`<p class="profile-note source-provenance">${esc(program.source_provenance)}</p>`:''}${program.algorithm?.reason?`<p class="profile-note">${esc(program.algorithm.reason)}</p>`:''}${program.runtime_policy?`<p class="profile-note">Runtime policy: ${esc(program.runtime_policy)}</p>`:''}${program.runtime_support?`<p class="profile-note">${esc(program.runtime_support)}</p>`:''}
    <section class="detail-section"><h3>Benchmark programs</h3><div class="variant-list"><table><thead><tr>${sortHeader('implementations','show','Show')}${sortHeader('implementations','program','Program')}${sortHeader('implementations','loc','LOC')}${sortHeader('implementations','median','Median')}</tr></thead><tbody>${implementations.map(item=>`<tr class="${item.key===program.key?'chosen':''}"><td><label><input data-toggle-program="${item.key}" type="checkbox" aria-label="Include ${esc(item.id)}" ${item.seconds==null||!eligibleForChart(item)||inLanguageView()||!group?.programs.includes(item.key)?'disabled':''} ${item.seconds==null||!eligibleForChart(item)||state.disabled.has(item.key)?'':'checked'}></label></td><td><button data-inspect-program="${item.key}">${esc(item.id)}</button></td><td>${item.loc}</td><td>${seconds(item.seconds)}</td></tr>`).join('')}</tbody></table></div></section>`;
  $('#source-code').textContent=file.code;
  if(renderRelated){
    renderLanguageOverview();
    if(languageOverviewVisible())renderMedianRankings();
  }
  $('#download-source').onclick=event=>{event.preventDefault();const url=URL.createObjectURL(new Blob([file.code],{type:'text/plain'}));const link=document.createElement('a');link.href=url;link.download=file.name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
}
function reset({rankings=false}={}){
  const focus=state.languageFocus;
  pauseYears();
  state.benchmarks=new Set(data.benchmarks.map(b=>b.key));state.languages=new Set(data.languages.map(l=>l.key));
  state.disabled.clear();state.ellipses=new Set(['mech']);state.view=rankings?'rankings':'summary';state.focus='nbody';state.languageFocus=null;
  state.collapsedFamilies.clear();
  state.traits=emptyTraitFilters();
  state.benchmarkFilters=emptyBenchmarkFilters();
  Object.assign(state,{locMetric:'canonical',fast:true,small:true,sampleMode:'dim',medianMode:'highlight',densityMode:'off',focusMeans:true,global:false});fullReleaseWindow();
  if(focus){state.languageFocus={...focus,program:null,savedDetail:null,savedInspectorOpen:false};showLanguageOverview(focus.selectionKey,{family:focus.family});}
  else update();
}
function setLOCMetric(metric){
  if(!['canonical','formatted'].includes(metric))throw new Error('Unknown LOC metric.');
  state.locMetric=metric;update();
}
function registerTools(){
  if(!document.modelContext?.registerTool)return;
  const controller=new AbortController();
  const tool={name:'configure_benchmark_chart',title:'Configure benchmark chart',
    description:'Select the benchmarks, languages, and standard-deviation ellipses shown in the explorer.',
    inputSchema:{type:'object',properties:{benchmarks:{type:'array',items:{type:'string'}},languages:{type:'array',items:{type:'string'}},ellipses:{type:'array',items:{type:'string'}}},additionalProperties:false},
    annotations:{readOnlyHint:false,untrustedContentHint:false},
    execute(input){
      if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Expected a selection object.');
      const allowed={benchmarks:data.benchmarks.map(b=>b.key),languages:data.languages.map(l=>l.key),ellipses:data.languages.map(l=>l.key)};
      for(const key of Object.keys(input))if(!allowed[key])throw new Error('Unknown selection field.');
      for(const [key,values] of Object.entries(input))if(!Array.isArray(values)||values.some(v=>typeof v!=='string'||!allowed[key].includes(v)))throw new Error(`Invalid ${key} selection.`);
      for(const [key,values] of Object.entries(input))state[key]=new Set(values);
      if(input.languages)state.traits=emptyTraitFilters();
      if(input.benchmarks)state.benchmarkFilters=emptyBenchmarkFilters();
      state.languageFocus=null;state.view='summary';update();return {benchmarks:[...effectiveBenchmarks()],languages:model.entries.map(e=>e.language.key),ellipses:[...state.ellipses]};
    }};
  try{Promise.resolve(document.modelContext.registerTool(tool,{signal:controller.signal})).catch(()=>{});}catch{}
  addEventListener('pagehide',()=>controller.abort(),{once:true});
}
function sameJSONValue(left,right){
  if(left===right)return true;
  if(left===null||right===null||typeof left!=='object'||typeof right!=='object'||Array.isArray(left)!==Array.isArray(right))return false;
  const keys=Object.keys(left),otherKeys=Object.keys(right);
  return keys.length===otherKeys.length&&keys.every((key,index)=>key===otherKeys[index]&&sameJSONValue(left[key],right[key]));
}
async function start(){
  const dataURL=new URL('./data.json',import.meta.url),assetVersion=new URL(import.meta.url).searchParams.get('v');
  if(assetVersion)dataURL.searchParams.set('v',assetVersion);
  data=await fetch(dataURL).then(response=>{if(!response.ok)throw new Error('Could not load measured benchmark data.');return response.json();});
  languageIndex=new Map(data.languages.map(item=>[item.key,item]));
  benchmarkIndex=new Map(data.benchmarks.map(item=>[item.key,item]));
  familyIndex=languageFamilies(data.languages).map(f=>({...f,label:f.members.length>1?f.label:shortName(f.members[0].key)}))
    .sort((a,b)=>a.label.localeCompare(b.label,'en',{sensitivity:'base'}));
  // The qualified inventory keeps source navigation complete without changing
  // the canonical comparison pool or its immutable normalization baselines.
  const inventory=data.program_inventory??{};
  if(typeof inventory!=='object'||Array.isArray(inventory))throw new Error('Invalid qualified program inventory.');
  for(const [key,p] of Object.entries(inventory))if(Object.hasOwn(data.programs,key)){
    const canonical=data.programs[key];
    for(const field of ['id','benchmark','language','loc','physical_loc','x','y','seconds','samples','files','report','binary_sha256','runtime_arguments','command','measured_backend','execution_mode','formatted_loc','formatted_loc_status','formatted_loc_complete','formatted_loc_evidence','formatted_x','eligible_for_chart'])
      if(!sameJSONValue(p[field],canonical[field]))throw new Error(`Conflicting qualified program identity: ${key}.`);
  }
  programCatalog=Object.fromEntries(Object.entries({...inventory,...data.programs}).map(([key,p])=>{
    const b=benchmark(p.benchmark);
    if(Object.hasOwn(p,'eligible_for_chart')&&typeof p.eligible_for_chart!=='boolean')throw new Error(`Invalid publication eligibility: ${key}.`);
    if(p.key!=null&&p.key!==key||!b||!language(p.language)||!Array.isArray(p.files)||!p.files.length||p.files.some(file=>!Object.hasOwn(data.files,file)))throw new Error(`Invalid published program/source identity: ${key}.`);
    if(!Array.isArray(p.samples)||p.seconds!=null&&(!measuredTiming(p)||p.samples.length<3||p.samples.some(sample=>!Number.isFinite(sample)||sample<=0)))throw new Error(`Invalid published timing samples: ${key}.`);
    const x=eligibleForChart(p)?p.x??p.loc/b.baseline_loc:null,y=eligibleForChart(p)&&p.seconds!=null?p.y??p.seconds/b.baseline_seconds:null;
    if(!Number.isSafeInteger(p.loc)||p.loc<=0||eligibleForChart(p)&&(!Number.isFinite(x)||x<=0||p.seconds!=null&&(!Number.isFinite(y)||y<=0)))throw new Error(`Invalid published source/timing coordinates: ${key}.`);
    return [key,{...p,key,x,y}];
  }));
  // Preserve catalog insertion order for defaults and previous/next browsing.
  for(const program of Object.values(programCatalog)){
    if(!programsByBenchmark.has(program.benchmark))programsByBenchmark.set(program.benchmark,new Map());
    const languages=programsByBenchmark.get(program.benchmark);
    if(!languages.has(program.language))languages.set(program.language,[]);
    languages.get(program.language).push(program);
  }
  // Backend aggregates cover the complete qualified inventory, independently
  // of endpoint, LOC metric and visibility selections.
  traits=languageTraits({...data,programs:programCatalog});
  for(const l of data.languages)colors[l.key]=darkColor(l.color);
  const yearSources=[...new Map(data.languages.map(l=>[l.release_name,l])).values()].sort((a,b)=>a.release_year-b.release_year||a.release_name.localeCompare(b.release_name));
  $('#release-year-sources').innerHTML=yearSources.map(l=>`<li><a href="${esc(l.release_source)}" target="_blank" rel="noopener">${esc(l.release_name)} · ${l.release_year}</a><span>${esc(l.release_note)}</span></li>`).join('');
  $('#release-decades').innerHTML=Array.from({length:8},(_,index)=>1950+index*10).map(decade=>`<button data-release-decade="${decade}" aria-pressed="false">${decade}s</button>`).join('');
  $('#focused-benchmark').innerHTML=data.benchmarks.map(b=>`<option value="${b.key}">${esc(b.title)}</option>`).join('');
  reset();registerTools();
  for(const kind of ['benchmark','language']){
    const toggle=$(`#toggle-${kind}-filters`),body=$(`#${kind}-filter-body`);
    const setExpanded=value=>{toggle.setAttribute('aria-expanded',value);body.hidden=!value;};
    setExpanded(true);
    toggle.onclick=()=>setExpanded(body.hidden);
  }
  $('#all-benchmarks').onclick=()=>selectBenchmarks(data.benchmarks.map(b=>b.key),{clearFilters:true});
  $('#no-benchmarks').onclick=()=>selectBenchmarks([],{clearFilters:true});
  $('#clear-benchmark-filters').onclick=()=>selectBenchmarks(state.benchmarks,{clearFilters:true});
  $('#all-languages').onclick=()=>{leaveLanguageFocusForSelection();state.traits=emptyTraitFilters();state.languages=new Set(data.languages.map(l=>l.key));if(state.view==='mech')state.view='summary';update();};
  $('#no-languages').onclick=()=>{leaveLanguageFocusForSelection();state.traits=emptyTraitFilters();state.languages.clear();update();};
  $('#only-mech').onclick=()=>{leaveLanguageFocusForSelection();state.traits=emptyTraitFilters();state.languages=new Set(mechKeys());update();};
  $('#clear-traits').onclick=()=>{leaveLanguageFocusForSelection();state.traits=emptyTraitFilters();update();};
  for(const [id,moving] of [['release-year-start','start'],['release-year-end','end']])$('#'+id).oninput=()=>{
    const from=Number($('#release-year-start').value),to=Number($('#release-year-end').value);
    leaveLanguageFocusForSelection();setReleaseWindow(from,to,{moving});
  };
  $('#all-release-years').onclick=()=>{leaveLanguageFocusForSelection();const {min,max}=yearBounds();setReleaseWindow(min,max);};
  $('#play-years').onclick=()=>{leaveLanguageFocusForSelection();playYears();};
  addEventListener('pagehide',pauseYears,{once:true});
  $('#reset').onclick=()=>reset();
  $('#reset-rankings').onclick=()=>reset({rankings:true});
  $('#close-inspector').onclick=closeInspector;
  $('#return-language-overview').onclick=()=>{const focus=state.languageFocus;showLanguageOverview(focus.selectionKey,{family:focus.family,restoreProgram:true});};
  $('#overview-compare').onclick=()=>compareOverviewProgram();
  $('#overview-inspect').onclick=()=>{
    const focus=state.languageFocus,rows=benchmarkPrograms(focus.benchmark,focus.variant);
    const p=rows.find(p=>p.key===focus.program)??rows[0];if(p)openPoint({language:p.language,benchmark:p.benchmark,program:p.key});
  };
  $('#focused-benchmark').onchange=event=>{state.focus=event.target.value;update();};
  for(const [id,key] of [['fast-profile','fast'],['small-profile','small'],['show-global','global']])$('#'+id).onchange=event=>{if(event.target.disabled)return;state[key]=event.target.checked;updatePlot();};
  $('#loc-metric').onchange=event=>setLOCMetric(event.target.value);
  $('#chart-axes').onchange=event=>{if(!['means','samples'].includes(event.target.value))return;state.focusMeans=event.target.value==='means';updatePlot();};
  for(const [id,key] of [['show-samples','samples'],['show-medians','medians'],['show-density','density']])$('#'+id).onchange=event=>setLayerModes({[key]:event.target.value});
  document.addEventListener('click',event=>{
    const decade=event.target.closest('[data-release-decade]');if(decade&&!decade.disabled){
      const window=decadeWindow(Number(decade.dataset.releaseDecade),yearBounds());
      if(window){leaveLanguageFocusForSelection();setReleaseWindow(window.from,window.to);}return;
    }
    const openLanguage=event.target.closest('[data-open-language]');if(openLanguage){showLanguageOverview(openLanguage.dataset.openLanguage);return;}
    const openFamily=event.target.closest('[data-open-family]');if(openFamily){showLanguageOverview(openFamily.dataset.openFamily,{family:true});return;}
    const compareLanguage=event.target.closest('[data-compare-language]');if(compareLanguage&&!compareLanguage.disabled){compareOverviewLanguage(compareLanguage.dataset.compareLanguage);return;}
    const compareProgram=event.target.closest('[data-compare-program]');if(compareProgram){compareOverviewProgram(compareProgram.dataset.compareProgram);return;}
    const stepProgram=event.target.closest('[data-step-program]');if(stepProgram&&!stepProgram.disabled){
      const current=selectedProgram(),browsing=state.languageFocus&&focusKeys().has(current.language)?focusPrograms():benchmarkPrograms(current.benchmark,current.language);
      const p=browsing[browsing.findIndex(p=>p.key===current.key)+Number(stepProgram.dataset.stepProgram)];
      if(p)openPoint({language:p.language,benchmark:p.benchmark,program:p.key});return;
    }
    const disclosure=event.target.closest('[data-toggle-family]');if(disclosure){
      const key=disclosure.dataset.toggleFamily;state.collapsedFamilies.has(key)?state.collapsedFamilies.delete(key):state.collapsedFamilies.add(key);
      renderControls();$(`[data-toggle-family="${key}"]`).focus({preventScroll:true});return;
    }
    const sort=event.target.closest('[data-sort-table]');if(sort){sortTable(sort);return;}
    const view=event.target.closest('[data-view]');if(view){selectView(view.dataset.view);return;}
    const inspect=event.target.closest('[data-inspect-benchmark]');if(inspect){leaveLanguageFocusForSelection();state.focus=inspect.dataset.inspectBenchmark;state.view='benchmark';update();openPoint({language:'mech',benchmark:state.focus});}
    const spread=event.target.closest('[data-spread]');if(spread){const key=spread.dataset.spread;state.ellipses.has(key)?state.ellipses.delete(key):state.ellipses.add(key);spread.setAttribute('aria-pressed',state.ellipses.has(key));updatePlot();}
    const table=event.target.closest('[data-table-language]');if(table){showLanguageOverview(table.dataset.tableLanguage);return;}
    const program=event.target.closest('[data-inspect-program]');if(program){const p=catalogProgram(program.dataset.inspectProgram);openPoint({language:p.language,benchmark:p.benchmark,program:p.key});}
  });
  document.addEventListener('change',event=>{
    const element=event.target;
    if(element.disabled)return;
    if(element.id==='overview-variant'||element.id==='overview-benchmark'){
      const focus=state.languageFocus;if(!focus)return;
      focus[element.id==='overview-variant'?'variant':'benchmark']=element.value;focus.program=null;
      if(inLanguageView()&&$('#inspector').open)state.detail={...state.detail,language:focus.variant,benchmark:focus.benchmark,program:null,file:0};
      if(focus.comparison&&element.id==='overview-variant')showLanguageOverview(focus.selectionKey,{family:focus.family});else update();return;
    }
    if(element.dataset.family){
      leaveLanguageFocusForSelection();
      const family=families().find(f=>f.key===element.dataset.family),allowed=yearKeys();
      for(const l of family.members)if(matchesTraits(traits.get(l.key),state.traits)&&allowed.has(l.key)&&(state.view!=='mech'||isMechLanguage(l.key)))element.checked?state.languages.add(l.key):state.languages.delete(l.key);
      update();return;
    }
    if(element.dataset.traitOption){
      leaveLanguageFocusForSelection();
      const [dimension,option]=element.dataset.traitOption.split(':');
      element.checked?state.traits[dimension].add(option):state.traits[dimension].delete(option);
      update();return;
    }
    if(element.dataset.benchmarkFacet){
      const [dimension,option]=element.dataset.benchmarkFacet.split(':');
      selectBenchmarkFacet(dimension,option,element.checked);return;
    }
    if(element.dataset.benchmark){const selected=new Set(state.benchmarks);element.checked?selected.add(element.dataset.benchmark):selected.delete(element.dataset.benchmark);selectBenchmarks(selected);}
    if(element.dataset.language){leaveLanguageFocusForSelection();element.checked?state.languages.add(element.dataset.language):state.languages.delete(element.dataset.language);update();}
    const key=element.dataset.toggleProgram??(element.id==='include-program'?selectedProgram().key:null);
    if(key){state.detail.program=selectedProgram().key;element.checked?state.disabled.delete(key):state.disabled.add(key);update();}
    if(element.id==='detail-benchmark'){state.detail.benchmark=element.value;state.detail.program=null;state.detail.file=0;renderInspector();}
    if(element.id==='detail-profile'){state.detail.kind=element.value;state.detail.program=null;state.detail.file=0;renderInspector();}
    if(element.id==='detail-program'){state.detail.program=element.value;state.detail.file=0;renderInspector();}
    if(element.id==='detail-file'){state.detail.file=Number(element.value);renderInspector();}
  });
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('#inspector').open)closeInspector();});
  const chartSizeChanged=()=>state.view!=='rankings'&&(Math.max(290,$('#chart').clientWidth)!==renderedChartWidth||(innerWidth<=720)!==renderedChartMobile);
  new ResizeObserver(()=>{
    if(!chartSizeChanged()||chartResizeFrame!==null)return;
    chartResizeFrame=requestAnimationFrame(()=>{chartResizeFrame=null;if(chartSizeChanged())renderChart();});
  }).observe($('#chart-wrap'));
  let rankingWidth=-1;
  new ResizeObserver(entries=>{const width=entries[0].contentRect.width;if(width!==rankingWidth){rankingWidth=width;requestAnimationFrame(renderMedianRankings);}}).observe($('#median-ranking-cards'));
  window.benchmarkExplorer={getSelection:()=>({benchmarks:[...effectiveBenchmarks()],selectedBenchmarks:[...state.benchmarks],benchmarkFilters:Object.fromEntries(benchmarkDimensions.map(({key})=>[key,[...state.benchmarkFilters[key]]])),languages:[...effectiveLanguages()],selectedLanguages:[...state.languages],traits:Object.fromEntries(traitDimensions.map(({key})=>[key,[...state.traits[key]]])),releaseYearStart:state.releaseYearStart,releaseYear:state.releaseYear,shownReleaseYear:shownReleaseYear(),playbackYear:state.playbackYear,ellipses:[...state.ellipses],disabled:[...state.disabled],view:state.view,locMetric:state.locMetric,languageFocus:state.languageFocus?{keys:[...state.languageFocus.keys],program:state.languageFocus.program,comparison:state.languageFocus.comparison}:null,samples:samplesVisible(),sampleMode:state.sampleMode,medianMode:state.medianMode,densityMode:state.densityMode,focusMeans:state.focusMeans,global:state.global,playing:state.playing}),
    getDensity:()=>structuredClone(currentDensityField()),
    setLayerModes,
    getMedianRankings:currentRankings,
    getGlobalStatistics:()=>structuredClone(inLanguageView()?currentEntries().filter(e=>focusKeys().has(e.language.key)).map(entry=>({language:entry.language.key,statistics:languageMedianStatistics(entry)})):currentGlobalStatistics()),
    getDomains:()=>({...currentDomain}),
    getSummary:()=>model.entries.map(e=>({language:e.language.key,fast:e.fast,small:e.small,n:e.inputs.length,selected:e.coverage.selected,missing:e.coverage.missing.map(b=>b.key),metrics:comparisonMetrics(e)})),setReleaseYear,setReleaseWindow,setLOCMetric,inspectProgram:key=>{const program=catalogProgram(key);if(!program)throw new Error('Unknown program.');openPoint({language:program.language,benchmark:program.benchmark,program:key});}};
}
start().catch(error=>{$('#load-error').hidden=false;$('#load-error').textContent=error.message;$('#selection-summary').textContent='Data unavailable';console.error(error);});
