// Source coordinates are views of immutable source/timing evidence. Missing
// evidence never falls back to a different measure or to a zero count.
import {eligibleForChart} from './math.mjs';
const cache=new WeakMap();
export const sourceMetricDefinitions={
  canonical:{label:'Normalized LOC (retained)',name:'normalized LOC (retained rules)',unit:'LOC',fewest:'Fewest LOC'},
  formatted:{label:'Qualified formatted LOC',name:'qualified formatted LOC',unit:'formatted LOC',fewest:'Fewest LOC'},
  logical:{label:'Qualified logical units · partial coverage',name:'qualified logical source units (partial coverage)',unit:'logical units',fewest:'Fewest units',field:'logical_units'},
  bytes:{label:'Application UTF-8 bytes',name:'application UTF-8 bytes',unit:'UTF-8 bytes',fewest:'Fewest bytes',field:'utf8_bytes'},
  gzip:{label:'Application gzip bytes',name:'application gzip bytes',unit:'gzip bytes',fewest:'Fewest gzip bytes',field:'gzip_bytes'},
  bpe:{label:'Application BPE tokens',name:'application cl100k_base BPE tokens',unit:'BPE tokens',fewest:'Fewest tokens',field:'cl100k_base_tokens'},
};
export const sourceMetricKeys=Object.keys(sourceMetricDefinitions);
export const isSourceSizeMetric=metric=>!!sourceMetricDefinitions[metric]?.field;
export function sourceMetricValue(program,metric='canonical'){
  if(metric==='canonical')return program.loc;
  if(metric==='formatted')return hasFormattedLOC(program)?program.formatted_loc:null;
  if(metric==='logical'){
    const value=program.logical_source_units?.application;
    return program.logical_source_units?.status==='qualified'&&Number.isSafeInteger(value)&&value>0?value:null;
  }
  if(!isSourceSizeMetric(metric))throw new Error('Unknown source metric.');
  const value=program.source_metrics?.application?.[sourceMetricDefinitions[metric].field];
  return Number.isSafeInteger(value)&&value>0?value:null;
}
export const hasFormattedLOC=p=>p.formatted_loc_status==='qualified'&&p.formatted_loc_complete===true&&
  Number.isSafeInteger(p.formatted_loc)&&p.formatted_loc>0;
export function projectProgram(program,metric='canonical',baseline=null){
  if(metric==='canonical')return program;
  if(isSourceSizeMetric(metric)){
    const value=sourceMetricValue(program,metric);
    const timed=eligibleForChart(program)&&Number.isFinite(program.seconds)&&program.seconds>0&&Number.isFinite(program.y)&&program.y>0;
    return {...program,loc:value,x:timed&&value!==null&&Number.isFinite(baseline)&&baseline>0?value/baseline:null};
  }
  if(metric!=='formatted')throw new Error('Unknown source metric.');
  return {...program,loc:hasFormattedLOC(program)?program.formatted_loc:null,
    x:hasFormattedLOC(program)&&Number.isFinite(program.formatted_x)&&program.formatted_x>0?program.formatted_x:null};
}
export function axisData(data,metric='canonical'){
  if(metric==='canonical')return data;
  if(!sourceMetricKeys.includes(metric))throw new Error('Unknown source metric.');
  if(!cache.has(data))cache.set(data,new Map());
  if(cache.get(data).has(metric))return cache.get(data).get(metric);
  if(isSourceSizeMetric(metric)){
    // Every admitted, timed candidate can become a size endpoint. Canonical
    // LOC endpoints do not constrain a qualified owner/text-size comparison.
    const catalog={...data.program_inventory,...data.programs};
    const admitted=p=>eligibleForChart(p)&&Number.isFinite(p.seconds)&&p.seconds>0&&
      Number.isFinite(p.y)&&p.y>0&&sourceMetricValue(p,metric)!==null;
    const candidates=new Map(data.benchmarks.map(b=>[b.key,Object.values(catalog).filter(p=>p.benchmark===b.key&&admitted(p))]));
    const baselines=new Map([...candidates].map(([key,rows])=>[key,rows.length?Math.min(...rows.map(p=>sourceMetricValue(p,metric))):null]));
    const programs=Object.fromEntries(Object.entries(catalog).map(([key,p])=>[key,projectProgram(p,metric,baselines.get(p.benchmark))]));
    const benchmarks=data.benchmarks.map(b=>{
      const rows=candidates.get(b.key),groups=new Map(b.groups.map(g=>[g.language,g]));
      for(const p of rows)if(!groups.has(p.language))groups.set(p.language,{language:p.language,programs:[]});
      return {...b,baseline_loc:baselines.get(b.key),groups:[...groups.values()].map(g=>{
        const available=rows.filter(p=>p.language===g.language&&(!g.source_metric_locked||g.programs.includes(p.key))).map(p=>programs[p.key]);
        const fast=available.reduce((a,p)=>!a||p.seconds<a.seconds||p.seconds===a.seconds&&p.loc<a.loc?p:a,null);
        const small=available.reduce((a,p)=>!a||p.loc<a.loc||p.loc===a.loc&&p.seconds<a.seconds?p:a,null);
        return {...g,programs:available.map(p=>p.key),fast:fast?.key??null,small:small?.key??null};
      })};
    });
    const projected={...data,programs,benchmarks,source_axis_metric:metric,
      ...(data.program_inventory?{program_inventory:Object.fromEntries(Object.keys(data.program_inventory).map(key=>[key,programs[key]]))}:{})};
    cache.get(data).set(metric,projected);return projected;
  }
  const projectMap=pool=>Object.fromEntries(Object.entries(pool).map(([key,p])=>[key,projectProgram(p,metric)]));
  const projected={...data,programs:projectMap(data.programs),
    ...(data.program_inventory?{program_inventory:projectMap(data.program_inventory)}:{}),
    benchmarks:data.benchmarks.map(b=>({...b,baseline_loc:b.baseline_formatted_loc??null,
    groups:b.groups.map(g=>({...g,fast:g.formatted_fast??null,small:g.formatted_small??null}))}))};
  cache.get(data).set(metric,projected);return projected;
}
export function formattedText(program){
  return hasFormattedLOC(program)?`${program.formatted_loc} formatted LOC`:
    `— formatted LOC (${program.formatted_loc_status??'pending'})`;
}
export const formattedValue=program=>hasFormattedLOC(program)?String(program.formatted_loc):'—';
export function inspectorProgram(data,projected,detail,disabled){
  const catalog={...data.program_inventory,...data.programs};
  if(detail.program)return catalog[detail.program]??null;
  const group=projected.benchmarks.find(b=>b.key===detail.benchmark)?.groups.find(g=>g.language===detail.language);
  if(!group)return null;
  let candidates=group.programs.filter(k=>!disabled.has(k)).map(k=>projected.programs[k])
    .filter(p=>eligibleForChart(p)&&Number.isFinite(p.loc)&&p.loc>0&&Number.isFinite(p.x)&&p.x>0);
  if(!candidates.length){
    // The original source remains inspectable when the formatted endpoint is
    // unavailable. This selection never supplies a formatted chart coordinate.
    const canonical=data.benchmarks.find(b=>b.key===detail.benchmark)?.groups.find(g=>g.language===detail.language);
    return data.programs[canonical?.[detail.kind]??canonical?.small]??null;
  }
  if(detail.kind==='fast'&&candidates.some(p=>p.seconds!=null))candidates=candidates.filter(p=>p.seconds!=null);
  const chosen=candidates.reduce((a,b)=>detail.kind==='fast'?
    (b.seconds<a.seconds||b.seconds===a.seconds&&b.loc<a.loc?b:a):
    (b.loc<a.loc||b.loc===a.loc&&b.seconds<a.seconds?b:a));
  return catalog[chosen.key];
}
// Both controls must independently name qualified counts of the exact source
// comparison. Generic canonical control_loc is deliberately ignored.
export function formattedMechRatio(program){
  // This packet does not admit matched-control formatter evidence. A future
  // source/receipt-bound control overlay must add that gate before any ratio.
  // Canonical control counts and unverified boolean labels cannot supply it.
  return null;
}
