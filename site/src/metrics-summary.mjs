import {metrics,formatMetric,comparisonPlot,referenceLink,referenceName,referenceURL} from './campaigns-model.mjs';
import {metricGroups,publishedComparisons,countsFor,filterMeasurements,outcomeText,metricsRoute} from './metrics-model.mjs';
import {loadCampaigns,loadNative} from './metrics-data.mjs';
const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial=new URLSearchParams(location.search),route=metricsRoute(location.pathname,location.search);
const pageGroup=route.group==='all'?undefined:route.group;
const groupOrder=['applications','compiler','deflate','runtime','scaling','size','memory','lifecycle'];
let bundle,native,all=[],visible=[],result=initial.get('result')??'all';
if(!['all','faster','slower','equal'].includes(result))result='all';
let sort=['name','mech','reference','ratio','outcome'].includes(initial.get('sort'))?initial.get('sort'):'name';
let descending=initial.get('dir')==='desc';
const expanded=new Set((initial.get('expand')??'applications,compiler').split(',').filter(id=>groupOrder.includes(id)));
let lastQuery=initial.has('expand')?(initial.get('q')??''):'';
const countText=rows=>{const c=countsFor(rows);return `${c.faster} ${c.faster===1?'win':'wins'} · ${c.slower} ${c.slower===1?'loss':'losses'}${c.equal?` · ${c.equal} ${c.equal===1?'tie':'ties'}`:''}`;};
function renderGroupChart(){
  if(pageGroup)$('#group-chart').innerHTML=comparisonPlot(visible.map(row=>({id:row.key,ratio:row.ratio,direction:row.direction,title:row.title,label:row.label})),{width:$('#group-chart').clientWidth,measure:'measurement',label:'Mech divided by its reference'});
}
function compare(a,b){
  const value=row=>sort==='name'?row.title:sort==='mech'?row.value:sort==='reference'?row.reference:sort==='ratio'?row.ratio:outcomeText(row.direction);
  const left=value(a),right=value(b),order=typeof left==='string'?left.localeCompare(right):left-right;
  return (descending?-1:1)*order||a.title.localeCompare(b.title);
}
function render(){
  all=publishedComparisons(bundle,native,{group:pageGroup??'all'});
  const query=$('#summary-search').value;
  visible=filterMeasurements(all,{result,query});
  if(query.trim()&&query!==lastQuery)for(const row of visible)expanded.add(row.group);
  lastQuery=query;
  $('#summary-count').textContent=`${visible.length} ${visible.length===1?'comparison':'comparisons'}`;
  for(const button of $('#summary-outcomes').querySelectorAll('[data-summary-outcome]'))button.setAttribute('aria-pressed',String(button.dataset.summaryOutcome===result));
  $('#summary-ties').hidden=!all.some(row=>row.direction==='equal');
  const headers=[['name','Benchmark'],['mech','Mech'],['reference','Reference'],['ratio','Mech / reference'],['outcome','Result']];
  const head='<thead><tr>'+headers.map(([key,name])=>`<th scope="col" aria-sort="${sort===key?(descending?'descending':'ascending'):'none'}"><button class="column-sort" data-summary-sort="${key}">${name}${sort===key?`<span aria-hidden="true">${descending?'▾':'▴'}</span>`:''}</button></th>`).join('')+'</tr></thead>';
  const bodies=groupOrder.flatMap(id=>{
    const group=metricGroups.find(group=>group.id===id),rows=visible.filter(row=>row.group===id).sort(compare);
    if(!rows.length)return [];
    const open=!!pageGroup||expanded.has(id);
    const heading=pageGroup?'':`<tr class="group-heading"><th colspan="5" scope="rowgroup"><div><button class="group-toggle" data-group-toggle="${id}" aria-expanded="${open}">${open?'−':'+'} ${escape(group.title)} <span class="group-total">${rows.length}</span></button><span class="group-counts"><span class="faster">${countsFor(rows).faster} wins</span><span class="slower">${countsFor(rows).slower} losses</span>${countsFor(rows).equal?`<span class="equal">${countsFor(rows).equal} ties</span>`:''}</span><a class="group-details" href="${group.href}">View results</a></div></th></tr>`;
    return [`<tbody id="group-${id}">${heading}${rows.map(row=>`<tr data-summary-row="${escape(row.key)}"${open?'':' hidden'}><td><a class="task-link" href="${escape(row.href)}">${escape(row.title)}</a>${pageGroup&&['size','memory','lifecycle'].includes(pageGroup)?`<span class="family">${escape(metrics[row.metric]?.label??row.metric)}</span>`:''}</td><td class="number">${escape(formatMetric(row.value,row.metric))}</td><td class="control-value">${referenceLink(row.control)}<strong>${escape(formatMetric(row.reference,row.metric))}</strong></td><td><span class="result-tag ${row.direction}">${escape(row.label)}</span></td><td class="${row.direction}">${outcomeText(row.direction)}</td></tr>`).join('')}</tbody>`];
  }).join('');
  $('#summary-bodies').innerHTML=head+(bodies||'<tbody><tr><td colspan="5" class="empty">No comparisons match this selection. Supporting measurements are available in each task’s details.</td></tr></tbody>');
  if(!pageGroup){
    $('#summary-highlights').innerHTML=[['applications','Applications'],['deflate','DEFLATE'],['compiler','Compiler']].map(([id,title])=>{
      const rows=all.filter(row=>row.group===id),counts=countsFor(rows),group=metricGroups.find(group=>group.id===id);
      const main=id==='deflate'?`${counts.faster}/${rows.length} wins`:id==='compiler'?(rows[0]?.label??'No comparison'):countText(rows);
      return `<a class="performance-highlight" href="${group.href}"><span>${title}</span><strong class="${id==='compiler'?'slower':id==='deflate'?'faster':''}">${escape(main)}</strong><span>${id==='deflate'?'libdeflate':'Rust'}</span></a>`;
    }).join('');
  }
  renderGroupChart();
  const params=new URLSearchParams(location.search);
  for(const key of ['group','order','sort','dir','expand','result','q'])params.delete(key);
  for(const [key,value] of [['q',query],['result',result==='all'?'':result],['sort',sort==='name'?'':sort],['dir',descending?'desc':''],['expand',!pageGroup&&[...expanded].join(',')!=='applications,compiler'?([...expanded].join(',')||'none'):'']])if(value)params.set(key,value);
  history.replaceState(null,'',location.pathname+(params.size?'?'+params:'')+location.hash);
}
function exportCSV(){
  const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const columns=['group','task','measurement','unit','mech_value','reference','reference_value','mech_divided_by_reference','outcome','reference_source','implementation'];
  const csv=[columns,...visible.map(row=>[row.group,row.title,metrics[row.metric]?.label,metrics[row.metric]?.unit,row.value,referenceName(row.control),row.reference,row.ratio,row.direction,referenceURL(row.control)?new URL(referenceURL(row.control),location.origin).href:'',new URL(row.href,location.origin).href])].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download='mech-comparisons.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),0);
}
async function start(){
  $('#summary-search').value=initial.get('q')??'';
  const loaded=await Promise.allSettled([loadCampaigns(),!pageGroup?loadNative():Promise.resolve(undefined)]);
  if(loaded[0].status==='rejected')throw loaded[0].reason;
  bundle=loaded[0].value;
  if(loaded[1].status==='fulfilled')native=loaded[1].value;
  else{$('#summary-error').hidden=false;$('#summary-error').textContent='Compression comparisons could not be loaded. '+loaded[1].reason.message;}
  $('#summary-outcomes').addEventListener('click',event=>{const b=event.target.closest('[data-summary-outcome]');if(b){result=b.dataset.summaryOutcome;render();}});
  $('#summary-bodies').addEventListener('click',event=>{
    const button=event.target.closest('[data-summary-sort],[data-group-toggle]');if(!button)return;
    if(button.dataset.summarySort){const key=button.dataset.summarySort;descending=sort===key?!descending:false;sort=key;}
    else{const group=button.dataset.groupToggle;if(expanded.has(group))expanded.delete(group);else expanded.add(group);}
    render();
  });
  let timer;$('#summary-search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,100);});
  $('#summary-export').addEventListener('click',exportCSV);
  if(pageGroup){
    let lastPreview;
    for(const type of ['pointerover','focusin'])$('#group-chart').addEventListener(type,event=>{const key=event.target.closest('[data-compare]')?.dataset.compare;if(!key||key===lastPreview)return;lastPreview=key;const row=visible.find(row=>row.key===key);if(row)$('#group-readout').innerHTML=`<strong>${escape(row.title)}</strong><div class="readout-values"><span>Mech <strong>${escape(formatMetric(row.value,row.metric))}</strong></span><span>${referenceLink(row.control)} <strong>${escape(formatMetric(row.reference,row.metric))}</strong></span><strong class="${row.direction}">${escape(row.label)}</strong></div>`;});
    const choose=event=>{const key=event.target.closest('[data-compare]')?.dataset.compare,row=visible.find(row=>row.key===key);if(row)location.href=row.href;};
    $('#group-chart').addEventListener('click',choose);$('#group-chart').addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();choose(event);}});
    if(globalThis.ResizeObserver){let width=0;new ResizeObserver(entries=>{const next=Math.round(entries[0].contentRect.width);if(next>0&&next!==width){width=next;renderGroupChart();}}).observe($('#group-chart'));}
  }
  render();
}
start().catch(error=>{$('#summary-error').hidden=false;$('#summary-error').textContent=error.message;});
