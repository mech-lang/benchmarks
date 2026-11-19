import {formatMetric,comparisonLabel,comparisonPlot,referenceLink,implementationLink,nativeMechSource,comparisonStyle} from './campaigns-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial=new URLSearchParams(location.search);
let data,selected=initial.get('deflate-case'),filter=initial.get('deflate-filter')??'all',hovered;
let order=initial.get('deflate-order')==='reverse'?'reverse':'forward';
const legacySort=initial.get('deflate-sort');
let sort=['name','mech','reference','ratio','output'].includes(legacySort)?legacySort:['slowest','fastest'].includes(legacySort)?'ratio':'name';
let descending=initial.get('deflate-dir')==='desc'||legacySort==='slowest';
const ratio=row=>row.runs[order].ratio;
const direction=row=>ratio(row)<1?'faster':ratio(row)>1?'slower':'equal';
const label=row=>comparisonLabel({ratio:ratio(row)},'native_compression_call_seconds');

function writeParameters() {
  const query=new URLSearchParams(location.search);
  for(const [key,value] of [['deflate-order',order==='forward'?'':order],['deflate-filter',filter==='all'?'':filter],['deflate-search',$('#deflate-search').value],['deflate-sort',sort==='name'?'':sort],['deflate-dir',descending?'desc':''],['deflate-case',selected]]){
    if(value)query.set(key,value);else query.delete(key);
  }
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+location.hash);
}

function visibleRows() {
  const query=$('#deflate-search').value.trim().toLowerCase();
  return data.cases.filter(row=>(filter==='all'||direction(row)===filter)&&`${row.title} ${row.id} ${row.input_bytes}`.toLowerCase().includes(query));
}
function readout(row) {
  if(!row)return;
  const run=row.runs[order];
  $('#deflate-readout').innerHTML=`<strong>${escape(row.title)}</strong> · ${row.input_bytes.toLocaleString()} input bytes${row.prefix_bytes?` · ${row.prefix_bytes.toLocaleString()} prefix bytes`:''}<div class="readout-values"><span>${implementationLink({source_url:nativeMechSource,execution_mode:'aot'})} <strong>${escape(formatMetric(run.mech_seconds,'native_compression_call_seconds'))}</strong></span><span>${referenceLink({kind:'libdeflate'})} <strong>${escape(formatMetric(run.libdeflate_seconds,'native_compression_call_seconds'))}</strong></span><strong class="${direction(row)}" style="${comparisonStyle({ratio:ratio(row)},'native_compression_call_seconds')}">${escape(label(row))}</strong></div>`;
}
function renderChart(rows=visibleRows()) {
  $('#deflate-chart').innerHTML=comparisonPlot(rows.map(row=>({id:row.id,title:row.title,ratio:ratio(row),direction:direction(row),label:label(row)})),{width:$('#deflate-chart').clientWidth,label:'Mech and libdeflate level 12, one point per input case'});
}
function renderTable(rows) {
  const value=row=>sort==='name'?row.title:sort==='mech'?row.runs[order].mech_seconds:sort==='reference'?row.runs[order].libdeflate_seconds:sort==='output'?row.mech_output_bytes:ratio(row);
  rows=[...rows].sort((a,b)=>{const x=value(a),y=value(b);return (descending?-1:1)*(typeof x==='string'?x.localeCompare(y):x-y);});
  for(const button of $('#deflate-headings').querySelectorAll('[data-native-sort]'))button.closest('th').setAttribute('aria-sort',button.dataset.nativeSort===sort?(descending?'descending':'ascending'):'none');
  $('#deflate-count').textContent=`${rows.length} ${rows.length===1?'case':'cases'}`;
  $('#deflate-cases').innerHTML=rows.map(row=>{
    const run=row.runs[order];
    return `<tr data-native-row="${escape(row.id)}" class="${selected===row.id?'selected':''}"><td><button data-native-case="${escape(row.id)}">${escape(row.title)}</button><span class="family">${row.input_bytes.toLocaleString()} input bytes${row.prefix_bytes?` · ${row.prefix_bytes.toLocaleString()} prefix`:''}</span></td><td class="number">${escape(formatMetric(run.mech_seconds,'native_compression_call_seconds'))}</td><td class="number">${escape(formatMetric(run.libdeflate_seconds,'native_compression_call_seconds'))}</td><td><span class="result-tag ${direction(row)}" style="${comparisonStyle({ratio:ratio(row)},'native_compression_call_seconds')}">${escape(label(row))}</span></td><td class="number">${row.mech_output_bytes.toLocaleString()} / ${row.libdeflate_output_bytes.toLocaleString()}</td></tr>`;
  }).join('')||'<tr><td colspan="5" class="empty">No input cases match this selection.</td></tr>';
}
function render() {
  const rows=visibleRows();
  if(selected&&!rows.some(row=>row.id===selected))selected=undefined;
  renderChart(rows);renderTable(rows);
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
  if(!['all','faster','slower'].includes(filter))filter='all';
  $('#deflate-filters').addEventListener('click',event=>{const b=event.target.closest('[data-native-filter]');if(b){filter=b.dataset.nativeFilter;render();}});
  $('#deflate-order').addEventListener('change',()=>{order=$('#deflate-order').value;render();});
  $('#deflate-search').addEventListener('input',render);
  $('#deflate-headings').addEventListener('click',event=>{const button=event.target.closest('[data-native-sort]');if(button){const key=button.dataset.nativeSort;descending=key===sort?!descending:false;sort=key;render();}});
  for(const element of [$('#deflate-chart'),$('#deflate-cases')]){
    element.addEventListener('pointerover',preview);element.addEventListener('focusin',preview);element.addEventListener('click',choose);
    element.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)&&event.target.matches('[data-compare]')){event.preventDefault();choose(event);}});
  }
  let lastWidth=0;
  if(globalThis.ResizeObserver)new ResizeObserver(entries=>{const width=Math.round(entries[0].contentRect.width);if(width>0&&width!==lastWidth){lastWidth=width;renderChart();}}).observe($('#deflate-chart'));
  render();
}
start().catch(error=>{$('#deflate-error').hidden=false;$('#deflate-error').textContent=error.message;$('#deflate-chart').innerHTML='';});
