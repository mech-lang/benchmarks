import {formatMetric,comparisonLabel,comparisonPlot} from './campaigns-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial=new URLSearchParams(location.search);
let data,selected=initial.get('deflate-case'),filter=initial.get('deflate-filter')??'all',hovered;
let order=initial.get('deflate-order')==='reverse'?'reverse':'forward';
const ratio=row=>row.runs[order].ratio;
const direction=row=>ratio(row)<1?'faster':ratio(row)>1?'slower':'equal';
const label=row=>comparisonLabel({ratio:ratio(row)},'native_program_call_seconds');

function writeParameters() {
  const query=new URLSearchParams(location.search);
  for(const [key,value] of [['deflate-order',order==='forward'?'':order],['deflate-filter',filter==='all'?'':filter],['deflate-search',$('#deflate-search').value],['deflate-sort',$('#deflate-sort').value==='slowest'?'':$('#deflate-sort').value],['deflate-case',selected]]){
    if(value)query.set(key,value);else query.delete(key);
  }
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+location.hash);
}

function showView(view,write=true) {
  view=view==='suite'?'suite':'deflate';
  for(const button of document.querySelectorAll('[data-view]')){
    const active=button.dataset.view===view;
    button.classList.toggle('active',active);button.setAttribute('aria-selected',String(active));
  }
  $('#deflate-m3').hidden=view!=='deflate';$('#suite-panel').hidden=view!=='suite';
  if(write){const q=new URLSearchParams(location.search);q.set('view',view);history.replaceState(null,'',location.pathname+'?'+q);}
}
for(const button of document.querySelectorAll('[data-view]'))button.addEventListener('click',()=>showView(button.dataset.view));
$('.overview').addEventListener('keydown',event=>{
  if(!['ArrowLeft','ArrowRight'].includes(event.key))return;
  const next=event.target.dataset.view==='suite'?'deflate':'suite';showView(next);$(`[data-view="${next}"]`).focus();event.preventDefault();
});
showView(initial.get('view')??(initial.has('case')||initial.has('backend')||initial.has('campaign')?'suite':'deflate'),false);

function visibleRows() {
  const query=$('#deflate-search').value.trim().toLowerCase();
  return data.cases.filter(row=>(filter==='all'||direction(row)===filter)&&`${row.title} ${row.id} ${row.input_bytes}`.toLowerCase().includes(query));
}
function readout(row) {
  if(!row)return;
  const run=row.runs[order];
  $('#deflate-readout').innerHTML=`<strong>${escape(row.title)}</strong> · ${row.input_bytes.toLocaleString()} input bytes${row.prefix_bytes?` · ${row.prefix_bytes.toLocaleString()} prefix bytes`:''}<div class="readout-values"><span>Mech <strong>${escape(formatMetric(run.mech_seconds,'native_program_call_seconds'))}</strong></span><span>libdeflate <strong>${escape(formatMetric(run.libdeflate_seconds,'native_program_call_seconds'))}</strong></span><strong class="${direction(row)}">${escape(label(row))}</strong></div>`;
}
function renderChart(rows=visibleRows()) {
  $('#deflate-chart').innerHTML=comparisonPlot(rows.map(row=>({id:row.id,title:row.title,ratio:ratio(row),direction:direction(row),label:label(row)})),{width:$('#deflate-chart').clientWidth,label:'Mech and libdeflate level 12, one point per input case'});
}
function renderTable(rows) {
  const sort=$('#deflate-sort').value;
  rows=[...rows].sort((a,b)=>sort==='name'?a.title.localeCompare(b.title):sort==='size'?a.input_bytes-b.input_bytes:sort==='fastest'?ratio(a)-ratio(b):ratio(b)-ratio(a));
  $('#deflate-count').textContent=`${rows.length} ${rows.length===1?'case':'cases'}`;
  $('#deflate-cases').innerHTML=rows.map(row=>{
    const run=row.runs[order];
    return `<tr data-native-row="${escape(row.id)}" class="${selected===row.id?'selected':''}"><td><button data-native-case="${escape(row.id)}">${escape(row.title)}</button><span class="family">${row.input_bytes.toLocaleString()} input bytes${row.prefix_bytes?` · ${row.prefix_bytes.toLocaleString()} prefix`:''}</span></td><td class="number">${escape(formatMetric(run.mech_seconds,'native_program_call_seconds'))}</td><td class="number">${escape(formatMetric(run.libdeflate_seconds,'native_program_call_seconds'))}</td><td><span class="result-tag ${direction(row)}">${escape(label(row))}</span></td><td class="number">${row.mech_output_bytes.toLocaleString()} / ${row.libdeflate_output_bytes.toLocaleString()}</td></tr>`;
  }).join('')||'<tr><td colspan="5" class="empty">No input cases match this selection.</td></tr>';
}
function render() {
  const rows=visibleRows();renderChart(rows);renderTable(rows);
  for(const b of document.querySelectorAll('[data-native-filter]'))b.setAttribute('aria-pressed',String(b.dataset.nativeFilter===filter));
  hovered=undefined;
  const row=data.cases.find(r=>r.id===selected);if(row)readout(row);else $('#deflate-readout').textContent='Each point is one input case. Select a point or row for its timings.';
  writeParameters();
}
function caseFromEvent(event) {
  const target=event.target.closest('[data-compare],[data-native-case]');
  return target?.dataset.compare??target?.dataset.nativeCase;
}
function preview(event) {
  const id=caseFromEvent(event);if(!id||id===hovered)return;
  hovered=id;readout(data.cases.find(r=>r.id===id));
}
function choose(event) {
  const id=caseFromEvent(event);if(!id)return;
  selected=id;readout(data.cases.find(r=>r.id===id));
  for(const row of $('#deflate-cases').querySelectorAll('[data-native-row]'))row.classList.toggle('selected',row.dataset.nativeRow===id);
  writeParameters();
  if(event.currentTarget===$('#deflate-chart'))$(`[data-native-row="${CSS.escape(id)}"]`)?.scrollIntoView({block:'nearest',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
}
async function start() {
  const url=new URL('./deflate-m3-results-20261118.json',import.meta.url);url.search=new URL(import.meta.url).search;
  const response=await fetch(url);if(!response.ok)throw new Error('The compression results could not be loaded. The timing download remains available.');
  data=await response.json();
  if(data.schema!=='mech.deflate-results.v1'||data.cases.length!==81||new Set(data.cases.map(r=>r.id)).size!==81)throw new Error('The compression result set is incomplete.');
  for(const run of ['forward','reverse']){
    if(data.cases.some(row=>!['ratio','mech_seconds','libdeflate_seconds'].every(k=>Number.isFinite(row.runs?.[run]?.[k])&&row.runs[run][k]>0)))throw new Error('A compression measurement is missing.');
    if(data.cases.filter(row=>row.runs[run].ratio<1).length!==data.wins[run])throw new Error('The compression counts differ from the measurements.');
  }
  $('#deflate-order').value=order;
  $('#deflate-search').value=initial.get('deflate-search')??'';
  if(['slowest','fastest','name','size'].includes(initial.get('deflate-sort')))$('#deflate-sort').value=initial.get('deflate-sort');
  if(!['all','faster','slower'].includes(filter))filter='all';
  $('#deflate-filters').addEventListener('click',event=>{const b=event.target.closest('[data-native-filter]');if(b){filter=b.dataset.nativeFilter;render();}});
  $('#deflate-order').addEventListener('change',()=>{order=$('#deflate-order').value;render();});
  $('#deflate-search').addEventListener('input',render);
  $('#deflate-sort').addEventListener('change',render);
  for(const element of [$('#deflate-chart'),$('#deflate-cases')]){
    element.addEventListener('pointerover',preview);element.addEventListener('focusin',preview);element.addEventListener('click',choose);
    element.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)&&event.target.matches('[data-compare]')){event.preventDefault();choose(event);}});
  }
  let lastWidth=0;
  if(globalThis.ResizeObserver)new ResizeObserver(entries=>{const width=Math.round(entries[0].contentRect.width);if(width>0&&width!==lastWidth){lastWidth=width;renderChart();}}).observe($('#deflate-chart'));
  render();
}
start().catch(error=>{$('#deflate-error').hidden=false;$('#deflate-error').textContent=error.message;$('#deflate-chart').innerHTML='';});
