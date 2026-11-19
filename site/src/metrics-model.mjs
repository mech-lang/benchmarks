import {backendLabels,metrics,measuredRows,controlFor,controlComparison,comparisonDirection,comparisonLabel,nativeMechSource} from './campaigns-model.mjs';
import {mechMeasurements} from './ekf-model.mjs';

export const metricGroups=[
  {id:'ekf',title:'EKF comparisons',description:'Mech execution paths and their closest comparable peers',href:'/metrics/ekf/',metrics:[]},
  {id:'deflate',title:'DEFLATE compression',description:'Native compression calls · libdeflate 1.26, level 12 · Apple M3',href:'/metrics/deflate/',metrics:['native_compression_call_seconds']},
  {id:'applications',title:'Applications',description:'Application timings and their measured peers',href:'/metrics/applications/',metrics:['native_process_seconds','post_json_seconds']},
  {id:'benchmarks-game',title:'Benchmarks Game',description:'Mech AOT vs Rust AOT · Apple M3 · October 2026 · whole process',href:'/metrics/benchmarks-game/',metrics:[]},
  {id:'jit',title:'JIT comparisons',description:'Mech JIT vs the fastest recorded JIT per workload · whole process, including startup',href:'/metrics/jit/',metrics:[]},
  {id:'runtime',title:'Microbenchmarks',description:'Mech resident operations · no equivalent runtime reference',href:'/metrics/runtime/',metrics:['resident_turn_seconds','jit_invocation_seconds']},
  {id:'scaling',title:'Worker scaling',description:'Mech worker groups · no equivalent runtime reference',href:'/metrics/scaling/',metrics:['worker_group_process_seconds','accepted_turns_per_second']},
  {id:'compiler',title:'Compiler',description:'Source-to-executable build time · Rust',href:'/metrics/compiler/',metrics:['source_to_executable_seconds','source_to_artifact_seconds','artifact_decode_seconds','jit_compile_seconds']},
  {id:'size',title:'Code size',description:'Compiled executable and code sizes · Rust',href:'/metrics/size/',metrics:['executable_bytes','linked_text_bytes','object_text_bytes','artifact_bytes','output_bytes']},
  {id:'memory',title:'Allocations',description:'Mech allocation counts and retained storage',href:'/metrics/memory/',metrics:['managed_retained_bytes','worker_process_peak_rss_bytes','execution_allocations']},
  {id:'lifecycle',title:'Activation & cleanup',description:'Initial turns, activation, snapshots and teardown',href:'/metrics/lifecycle/',metrics:['initial_turn_seconds','activation_seconds','owned_snapshot_seconds','teardown_seconds']},
  {id:'compression-history',title:'Checked compression · historical',description:'Earlier managed program calls · Mech measurements without a matched level-12 timer',href:'/metrics/compression-history/',metrics:['native_program_call_seconds']},
];
export const measurementOnlyGroups=['runtime','scaling','memory','lifecycle'];

export function metricsRoute(pathname,search='') {
  const parts=pathname.split('/').filter(Boolean),q=new URLSearchParams(search);
  const name=parts[0]==='metrics'?parts[1]:undefined;
  if(name==='tasks'&&parts[2])return {kind:'suite',group:'all',task:decodeURIComponent(parts[2])};
  if(['knucleotide','nbody','related-post-gen'].includes(name))return {kind:'suite',group:'applications',task:name};
  if(name==='deflate')return {kind:'deflate',group:'deflate'};
  if(name==='ekf')return {kind:'ekf',group:'ekf'};
  if(metricGroups.some(group=>group.id===name))return {kind:'suite',group:name};
  if(q.get('view')==='suite')return {kind:'suite',group:'all'};
  if(q.get('view')==='deflate'||[...q.keys()].some(key=>key.startsWith('deflate-')))return {kind:'deflate',group:'deflate'};
  if(q.get('view')==='suite'||['case','campaign','backend','baseline','metric'].some(key=>q.has(key)))return {kind:'suite',group:'all'};
  return {kind:'summary',group:'all'};
}

export function groupForMetric(metric) {
  return metricGroups.find(group=>group.metrics.includes(metric));
}
export function groupForMeasurement(definition,metric) {
  const group=groupForMetric(metric);
  if(group?.id==='runtime'&&(definition.family==='applications'||definition.id==='ekf'))return metricGroups.find(group=>group.id==='applications');
  return group;
}
export function countsFor(rows) {
  const counts={faster:0,slower:0,equal:0,unmatched:0};
  for(const row of rows)counts[row.direction]++;
  return counts;
}
export function suiteMeasurements(bundle,{group='all',task,campaign='$latest',backend='$auto',metric='$all'}={}) {
  const measures=metric==='$all'?metricGroups.flatMap(item=>item.metrics):metric==='$primary'?['$primary']:[metric];
  return measures.flatMap(measure=>measuredRows(bundle,{campaign,backend,metric:measure}).flatMap(row=>{
    const category=groupForMeasurement(row.definition,row.metric);
    if(!category||(group!=='all'&&category.id!==group)||(task&&row.definition.id!==task))return [];
    const control=controlFor(bundle,row),change=controlComparison(row,control);
    return [{...row,group:category.id,key:`${row.definition.id}:${row.record.backend}:${row.metric}`,title:row.definition.title,
      value:row.record.summary[row.metric]?.median,reference:control.record?.summary[control.metric]?.median,
      control,change,ratio:change.ratio,direction:comparisonDirection(change,row.metric),label:comparisonLabel(change,row.metric),
      date:row.campaign.started_at,href:taskURL(row)}];
  }));
}
export function taskURL(row) {
  const query=new URLSearchParams({metric:row.metric,backend:row.record.backend});
  return `/metrics/tasks/${encodeURIComponent(row.definition.id)}/?${query}`;
}
export function nativeMeasurements(data,order='forward') {
  return data.cases.flatMap(row=>[
    {key:`native:${row.id}:time`,group:'deflate',title:row.title,metric:'native_compression_call_seconds',value:row.runs[order].mech_seconds,reference:row.runs[order].libdeflate_seconds,
      ratio:row.runs[order].ratio,scope:`${row.input_bytes.toLocaleString()} input bytes · native call`,kind:'time'},
    {key:`native:${row.id}:size`,group:'size',title:row.title,metric:'output_bytes',value:row.mech_output_bytes,reference:row.libdeflate_output_bytes,
      ratio:row.mech_output_bytes/row.libdeflate_output_bytes,scope:'Native compression · complete output bytes',kind:'size'},
  ].map(entry=>({...entry,record:{source_url:nativeMechSource,execution_mode:'aot'},control:{kind:'libdeflate',label:'libdeflate'},date:'2026-11-18',
    direction:comparisonDirection({ratio:entry.ratio},entry.metric),label:comparisonLabel({ratio:entry.ratio},entry.metric),
    href:`/metrics/deflate/?${new URLSearchParams({'deflate-case':row.id,...(order==='reverse'?{'deflate-order':order}:{})})}`})));
}
export function measurementScope(row) {
  return row.scope??`${backendLabels[row.record.backend]??row.record.backend} · ${row.definition.family}`;
}
export function outcomeText(direction) {
  return {faster:'Win',slower:'Loss',equal:'Tie',unmatched:'Unmatched'}[direction];
}
export function filterMeasurements(rows,{group='all',result='all',query=''}={}) {
  query=query.trim().toLowerCase();
  return rows.filter(row=>(group==='all'||row.group===group)&&(result==='all'||(result==='matched'?row.direction!=='unmatched':row.direction===result))
    &&`${row.title} ${metrics[row.metric]?.label} ${measurementScope(row)} ${row.control.label}`.toLowerCase().includes(query));
}

export function gameMeasurements(data) {
  return (data?.cases??[]).map(row=>{
    const ratio=row.mech.seconds/row.rust.seconds,metric='native_process_seconds';
    return {key:'game:'+row.key,group:'benchmarks-game',title:row.title+' · '+row.workload,metric,
      value:row.mech.seconds,reference:row.rust.seconds,ratio,
      record:{source_url:row.mech.source_url,execution_mode:'aot'},
      control:{kind:'rust',label:'Rust',record:{reference_url:row.rust.original_url??row.rust.source_url}},
      scope:'AOT · '+data.hardware+' · October 2026 · whole process',
      direction:comparisonDirection({ratio},metric),label:comparisonLabel({ratio},metric),
      date:row.mech.recorded_at,referenceDate:row.rust.recorded_at,
      href:row.mech.implementation_url};
  });
}

export function jitMeasurements(data) {
  return (data?.jit_cases??[]).map(row=>{
    const ratio=row.mech.seconds/row.reference.seconds,metric='native_process_seconds';
    return {key:'jit:'+row.key,group:'jit',title:row.title+' · '+row.workload,metric,
      value:row.mech.seconds,reference:row.reference.seconds,ratio,
      record:{source_url:row.mech.source_url,execution_mode:'jit'},
      control:{kind:'jit',label:row.reference.label,record:{reference_url:row.reference.original_url??row.reference.source_url,source_url:row.reference.source_url}},
      scope:'JIT · '+data.hardware+' · whole process including startup',
      direction:comparisonDirection({ratio},metric),label:comparisonLabel({ratio},metric),
      date:row.mech.recorded_at,referenceDate:row.reference.recorded_at,
      href:row.mech.implementation_url};
  });
}

// The comparison overview uses one main timing per task. Supporting measurements
// stay in task details; size and allocation pages show their matched metrics.
export function ekfMeasurements(data){
  if(!data)return [];
  return mechMeasurements(data).filter(row=>row.mode==='checked'&&row.peer).map(row=>{
    const metric='ekf_filter_turn_seconds';
    return {key:'ekf:'+row.result_id,group:'applications',title:'EKF · '+row.variant.replace(/^Mech /,''),metric,
      value:row.time_seconds,reference:row.peer.time_seconds,ratio:row.ratio,
      record:{source_url:row.source_url,execution_mode:row.category==='cpu-jit'?'jit':row.category==='cpu-aot'?'aot':'gpu'},
      control:{kind:row.category==='cpu-jit'?'jit':row.category==='cpu-aot'?'aot':'gpu',label:row.peer.label,record:{reference_url:row.peer.implementation_url??row.peer.source_url,source_url:row.peer.source_url}},
      scope:row.study.machine+' · '+row.study.precision+' · '+row.study.instances.toLocaleString()+' filters · checked · per filter-turn · '+row.publication,
      direction:comparisonDirection({ratio:row.ratio},metric),label:comparisonLabel({ratio:row.ratio},metric),
      date:row.study.recorded_at,referenceDate:row.study.recorded_at,
      href:'/metrics/ekf/?'+new URLSearchParams({q:row.label})};
  });
}

export function publishedComparisons(bundle,data,{group='all',games,ekf}={}) {
  const secondary=['size','memory','lifecycle'].includes(group);
  const suite=suiteMeasurements(bundle,{group:secondary?group:'all',metric:secondary?'$all':'$primary'})
    .filter(row=>row.direction!=='unmatched'&&(group==='all'||row.group===group))
    // The newer source-JIT run is retained in task details. It does not replace
    // the separately measured Mech AOT/Rust AOT Benchmarks Game comparison.
    .filter(row=>secondary||row.record.backend!=='source-native');
  const native=(!group||group==='all'||group==='deflate')&&data?nativeMeasurements(data).filter(row=>row.group==='deflate'):[];
  const processing=suite.map(row=>row.definition.id==='related-post-gen'&&row.metric==='post_json_seconds'?{...row,title:row.title+' · processing'}:row);
  const process=(!secondary&&(group==='all'||group==='applications'))?suiteMeasurements(bundle,{task:'related-post-gen',metric:'native_process_seconds'}).filter(row=>row.direction!=='unmatched').map(row=>({...row,title:row.title+' · whole process'})):[];
  return [...processing,...process,...native,...(group==='all'||group==='benchmarks-game'?gameMeasurements(games):[]),...(group==='all'||group==='jit'?jitMeasurements(games):[]),...(group==='all'||group==='applications'?ekfMeasurements(ekf):[])];
}
