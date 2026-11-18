import {metrics,formatMetric,comparisonPlot} from './campaigns-model.mjs';
import {metricGroups,suiteMeasurements,nativeMeasurements,countsFor,filterMeasurements,measurementScope,outcomeText,metricsRoute} from './metrics-model.mjs';
import {loadCampaigns,loadNative} from './metrics-data.mjs';
const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial=new URLSearchParams(location.search);
const route=metricsRoute(location.pathname,location.search);
const pageGroup=route.group==='all'?undefined:route.group;
let suite=[],native,all=[],visible=[],result=initial.get('result')??'all';
if(!['all','matched','faster','slower','equal','unmatched'].includes(result))result='all';
const countLabels={faster:'wins',slower:'losses',equal:'ties',unmatched:'unmatched'};
const countsHTML=counts=>Object.entries(counts).map(([state,count])=>`<span class="${state}">${count.toLocaleString()} ${countLabels[state]}</span>`).join('');
function renderGroupChart(){
  if(pageGroup)$('#group-chart').innerHTML=comparisonPlot(visible.map(row=>({id:row.key,ratio:row.ratio,direction:row.direction,title:row.title,label:row.label})),{width:$('#group-chart').clientWidth,measure:'measurement',label:'Mech divided by each named reference'});
}
function render() {
  const order=$('#summary-order').value;
  all=[...suite,...(native?nativeMeasurements(native,order):[])].filter(row=>!pageGroup||row.group===pageGroup);
  visible=filterMeasurements(all,{group:$('#summary-group').value,result,query:$('#summary-search').value});
  const counts=countsFor(visible);
  renderGroupChart();
  $('#summary-stats').innerHTML=Object.entries(counts).map(([state,count])=>`<div><strong class="${state}">${count.toLocaleString()}</strong><span>Measurement ${countLabels[state]}</span></div>`).join('');
  $('#summary-count').textContent=`${visible.length.toLocaleString()} of ${all.length.toLocaleString()} measurements`;
  for(const button of $('#summary-outcomes').querySelectorAll('[data-summary-outcome]'))button.setAttribute('aria-pressed',String(button.dataset.summaryOutcome===result));
  const sort=$('#summary-sort').value;
  const bodies=metricGroups.flatMap(group=>{
    const rows=visible.filter(row=>row.group===group.id).sort((a,b)=>sort==='ratio-low'?(a.ratio??Infinity)-(b.ratio??Infinity):sort==='ratio-high'?(b.ratio??-Infinity)-(a.ratio??-Infinity):a.title.localeCompare(b.title)||a.metric.localeCompare(b.metric));
    if(!rows.length)return [];
    const counts=countsFor(rows);
    return [`<tbody id="group-${group.id}"><tr class="group-heading"><th colspan="7" scope="rowgroup"><div><a href="${group.href}">${escape(group.title)}</a><span class="group-counts">${countsHTML(counts)}</span></div><span class="family">${escape(group.description)}</span></th></tr>${rows.map(row=>`<tr data-summary-row="${escape(row.key)}"><td><a class="task-link" href="${escape(row.href)}">${escape(row.title)}</a><span class="family">${escape(measurementScope(row))}</span></td><td>${escape(metrics[row.metric]?.label??row.metric)}</td><td class="number">${escape(formatMetric(row.value,row.metric))}</td><td class="control-value">${escape(row.control.label)}${Number.isFinite(row.reference)?`<strong>${escape(formatMetric(row.reference,row.metric))}</strong>`:''}</td><td><span class="result-tag ${row.direction}">${escape(row.label)}</span></td><td class="${row.direction}">${outcomeText(row.direction)}</td><td class="number">${escape(row.date.slice(0,10))}</td></tr>`).join('')}</tbody>`];
  }).join('')||'<tbody><tr><td colspan="7" class="empty">No measurements match this selection.</td></tr></tbody>';
  $('#summary-bodies').innerHTML='<thead><tr><th scope="col">Task / input</th><th scope="col">Measurement</th><th scope="col">Mech</th><th scope="col">Reference</th><th scope="col">Mech / reference</th><th scope="col">Result</th><th scope="col">Run date</th></tr></thead>'+bodies;
  $('#summary-groups').innerHTML=metricGroups.map(group=>{
    const rows=all.filter(row=>row.group===group.id),counts=countsFor(rows);
    return `<a class="group-link" href="${group.href}"><strong>${escape(group.title)}</strong><span>${rows.length} measurements</span><span class="group-counts">${countsHTML(counts)}</span></a>`;
  }).join('');
  const query=new URLSearchParams(location.search);
  for(const [key,value] of [['group',pageGroup||$('#summary-group').value==='all'?'':$('#summary-group').value],['result',result==='all'?'':result],['q',$('#summary-search').value],['sort',sort==='name'?'':sort],['order',order==='forward'?'':order]])if(value)query.set(key,value);else query.delete(key);
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+location.hash);
}
function exportCSV(rows,name) {
  const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const columns=['group','task','measurement','unit','mech_value','reference','reference_value','mech_divided_by_reference','outcome','date','execution_path','campaign','implementation'];
  const csv=[columns,...rows.map(row=>[row.group,row.title,metrics[row.metric]?.label,metrics[row.metric]?.unit,row.value,row.control.label,row.reference,row.ratio,row.direction,row.date,row.record?.backend??'native',row.campaign?.id??`M3-${$('#summary-order').value}`,new URL(row.href,location.origin).href])].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),0);
}
async function start() {
  $('#summary-group').innerHTML='<option value="all">All groups</option>'+metricGroups.map(group=>`<option value="${group.id}">${escape(group.title)}</option>`).join('');
  if(metricGroups.some(group=>group.id===initial.get('group')))$('#summary-group').value=initial.get('group');
  if(pageGroup){$('#summary-group').value=pageGroup;$('#summary-group').disabled=true;$('#summary-order-label').hidden=!['size','deflate'].includes(pageGroup);}
  $('#summary-search').value=initial.get('q')??'';
  if(['name','ratio-low','ratio-high'].includes(initial.get('sort')))$('#summary-sort').value=initial.get('sort');
  $('#summary-order').value=initial.get('order')==='reverse'?'reverse':'forward';
  const results=await Promise.allSettled([loadCampaigns(),!pageGroup||pageGroup==='size'?loadNative():Promise.resolve(undefined)]);
  const errors=[];
  if(results[0].status==='fulfilled')suite=suiteMeasurements(results[0].value);else errors.push(results[0].reason.message);
  if(results[1].status==='fulfilled')native=results[1].value;else errors.push(results[1].reason.message);
  if(errors.length){$('#summary-error').hidden=false;$('#summary-error').textContent='Some results could not be loaded. '+errors.join(' ');}
  $('#summary-outcomes').addEventListener('click',event=>{const button=event.target.closest('[data-summary-outcome]');if(button){result=button.dataset.summaryOutcome;render();}});
  for(const id of ['summary-group','summary-sort','summary-order'])$('#'+id).addEventListener('change',render);
  let inputTimer;
  $('#summary-search').addEventListener('input',()=>{clearTimeout(inputTimer);inputTimer=setTimeout(render,100);});
  $('#summary-export').addEventListener('click',()=>exportCSV(visible,'mech-metrics-selection.csv'));
  $('#summary-export-all').addEventListener('click',()=>exportCSV(all,'mech-metrics-all.csv'));
  if(pageGroup){
    let lastPreview;
    for(const type of ['pointerover','focusin'])$('#group-chart').addEventListener(type,event=>{const key=event.target.closest('[data-compare]')?.dataset.compare;if(!key||key===lastPreview)return;lastPreview=key;const row=visible.find(row=>row.key===key);if(row)$('#group-readout').innerHTML=`<strong>${escape(row.title)}</strong> · ${escape(metrics[row.metric]?.label)}<div class="readout-values"><span>Mech <strong>${escape(formatMetric(row.value,row.metric))}</strong></span><span>${escape(row.control.label)} <strong>${escape(formatMetric(row.reference,row.metric))}</strong></span><strong class="${row.direction}">${escape(row.label)}</strong></div>`;});
    $('#group-chart').addEventListener('click',event=>{const key=event.target.closest('[data-compare]')?.dataset.compare,row=visible.find(row=>row.key===key);if(row)location.href=row.href;});
    $('#group-chart').addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){const key=event.target.closest('[data-compare]')?.dataset.compare,row=visible.find(row=>row.key===key);if(row){event.preventDefault();location.href=row.href;}}});
    if(globalThis.ResizeObserver){let width=0;new ResizeObserver(entries=>{const next=Math.round(entries[0].contentRect.width);if(next>0&&next!==width){width=next;renderGroupChart();}}).observe($('#group-chart'));}
  }
  render();
}
start().catch(error=>{$('#summary-error').hidden=false;$('#summary-error').textContent=error.message;});
