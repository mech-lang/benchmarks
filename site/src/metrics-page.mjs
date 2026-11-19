import {metricGroups,metricsRoute} from './metrics-model.mjs';
const route=metricsRoute(location.pathname,location.search);
const $=selector=>document.querySelector(selector);
const view=route.kind==='suite'&&!route.task&&route.group!=='all'?'summary':route.kind;
for(const [kind,id] of [['summary','summary-panel'],['deflate','deflate-m3'],['suite','suite-panel']])$('#'+id).hidden=view!==kind;
for(const link of document.querySelectorAll('.metrics-nav a')){
  if(link.getAttribute('href')===(route.kind==='summary'?'/metrics/':route.kind==='deflate'?'/metrics/deflate/':metricGroups.find(group=>group.id===route.group)?.href))link.setAttribute('aria-current','page');
  else link.removeAttribute('aria-current');
}
const group=metricGroups.find(group=>group.id===route.group);
const title=route.task?{knucleotide:'K-nucleotide',nbody:'N-body','related-post-gen':'Related Post Gen'}[route.task]??'Task measurements':group?.title??'Mech performance';
$('#page-title').textContent=title;
$('#page-intro').textContent=route.kind==='summary'?'Compare Mech with measured reference implementations. The reference is always 1×.':group?.description??'Measurements, matched references and implementation details for this task.';
if(route.kind==='suite'){
  $('#suite-title').textContent=route.task?'Task measurements':group?.title??'All task measurements';
  $('#suite-reference-note').textContent=route.group==='compiler'?'Compiler costs are compared only with matched compiler costs. Source-to-artifact and JIT preparation without an equivalent reference are shown as Mech-only measurements.':route.group==='compression-history'?'Historical managed calls; no matched level-12 reference shares this timing scope.':'Each row names its own reference and measurement scope. The reference is 1×.';
  if(route.group==='compiler')$('#suite-report').hidden=true;
}
document.title=`Mech · ${title}`;
if(view==='summary'){
  if(route.group!=='all'){
    $('#summary-highlights').hidden=true;
    $('#summary-title').textContent=group.title;
    $('#group-chart-card').hidden=false;
    $('#summary-scope').textContent=route.group==='compiler'?'Complete source-to-executable compilation, compared with Rust. Supporting compilation stages are in the benchmark details.':route.group==='memory'?'Allocation counts compared with Rust. Lower is better.':route.group==='size'?'Compiled code sizes compared with Rust. Lower is better.':'Ratios are Mech ÷ reference; lower time is faster.';
    if(route.group==='jit')$('#summary-scope').textContent='Mech JIT divided by the fastest recorded eligible external JIT for each workload. Both sides measure the complete fresh process, including startup, JIT compilation, input/output and shutdown. Sources and individual runs are retained in the language dataset.';
  }
  await import('./metrics-summary.mjs');
}
else if(route.kind==='deflate')await import('./deflate-results.mjs');
else await import('./campaigns.mjs');
