import {metrics,formatMetric,comparisonPlot,referenceLink,referenceName,referenceURL,implementationLink,implementationURL,implementationName} from './campaigns-model.mjs';
import {metricGroups,publishedComparisons,countsFor,filterMeasurements,outcomeText,metricsRoute} from './metrics-model.mjs';
import {loadCampaigns,loadNative,loadGames} from './metrics-data.mjs';
const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial=new URLSearchParams(location.search),route=metricsRoute(location.pathname,location.search);
const pageGroup=route.group==='all'?undefined:route.group;
const groupOrder=['benchmarks-game','jit','applications','compiler','deflate','runtime','scaling','size','memory','lifecycle'];
let bundle,native,games,all=[],visible=[],result=initial.get('result')??'all';
if(!['all','faster','slower','equal'].includes(result))result='all';
let sort=['name','mech','reference','ratio','outcome'].includes(initial.get('sort'))?initial.get('sort'):'name';
let descending=initial.get('dir')==='desc';
const defaultExpanded='applications,benchmarks-game,compiler';
const expanded=new Set((initial.get('expand')??defaultExpanded).split(',').filter(id=>groupOrder.includes(id)));
let lastQuery=initial.has('expand')?(initial.get('q')??''):'';
const countLabel=(count,singular,plural=singular+'s')=>`${count} ${count===1?singular:plural}`;
const countText=rows=>{const c=countsFor(rows);return `${countLabel(c.faster,'win')} · ${countLabel(c.slower,'loss','losses')}${c.equal?` · ${countLabel(c.equal,'tie')}`:''}`;};
function renderGroupChart(){
  if(pageGroup)$('#group-chart').innerHTML=comparisonPlot(visible.map(row=>({id:row.key,ratio:row.ratio,direction:row.direction,title:row.title,label:row.label})),{width:$('#group-chart').clientWidth,measure:'measurement',label:'Mech divided by its reference'});
}
function compare(a,b){
  const value=row=>sort==='name'?row.title:sort==='mech'?row.value:sort==='reference'?row.reference:sort==='ratio'?row.ratio:outcomeText(row.direction);
  const left=value(a),right=value(b),order=typeof left==='string'?left.localeCompare(right):left-right;
  return (descending?-1:1)*order||a.title.localeCompare(b.title);
}
function render(){
  all=publishedComparisons(bundle,native,{group:pageGroup??'all',games});
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
    const counts=countsFor(rows);
    const heading=pageGroup?'':`<tr class="group-heading"><th colspan="5" scope="rowgroup"><div><button class="group-toggle" data-group-toggle="${id}" aria-expanded="${open}"><span class="disclosure-icon" aria-hidden="true">${open?'−':'+'}</span>${escape(group.title)} <span class="group-total">${rows.length}</span></button><span class="group-counts"><span class="faster">${countLabel(counts.faster,'win')}</span><span class="slower">${countLabel(counts.slower,'loss','losses')}</span>${counts.equal?`<span class="equal">${countLabel(counts.equal,'tie')}</span>`:''}</span><a class="group-details" href="${group.href}">View results</a></div>${['benchmarks-game','jit'].includes(id)?`<p class="group-description">${escape(group.description)}</p>`:''}</th></tr>`;
    return [`<tbody id="group-${id}">${heading}${rows.map(row=>`<tr data-summary-row="${escape(row.key)}"${open?'':' hidden'}><td><a class="task-link" href="${escape(row.href)}">${escape(row.title)}</a>${['applications','runtime'].includes(row.group)||pageGroup&&['size','memory','lifecycle'].includes(pageGroup)?`<span class="family">${escape(metrics[row.metric]?.label??row.metric)}${row.date?' · '+escape(row.date.slice(0,10)):''}</span>`:''}</td><td class="control-value">${implementationLink(row.record)}<strong>${escape(formatMetric(row.value,row.metric))}</strong></td><td class="control-value">${referenceLink(row.control)}<strong>${escape(formatMetric(row.reference,row.metric))}</strong></td><td><span class="result-tag ${row.direction}">${escape(row.label)}</span></td><td class="${row.direction}">${outcomeText(row.direction)}</td></tr>`).join('')}</tbody>`];
  }).join('');
  $('#summary-bodies').innerHTML=head+(bodies||'<tbody><tr><td colspan="5" class="empty">No comparisons match this selection. Supporting measurements are available in each task’s details.</td></tr></tbody>');
  if(!pageGroup){
    $('#summary-highlights').innerHTML=[['benchmarks-game','Benchmarks Game · AOT'],['jit','Benchmarks Game · JIT'],['deflate','DEFLATE']].map(([id,title])=>{
      const rows=all.filter(row=>row.group===id),counts=countsFor(rows),group=metricGroups.find(group=>group.id===id);
      const main=id==='deflate'?`${counts.faster}/${rows.length} wins`:countText(rows);
      return `<a class="performance-highlight" href="${group.href}"><span>${title}</span><strong class="${id==='deflate'?'faster':''}">${escape(main)}</strong><span>${id==='deflate'?'libdeflate':id==='benchmarks-game'?'Mech AOT / Rust AOT':'Fastest recorded JIT per workload'}</span></a>`;
    }).join('');
  }
  renderGroupChart();
  const params=new URLSearchParams(location.search);
  for(const key of ['group','order','sort','dir','expand','result','q'])params.delete(key);
  for(const [key,value] of [['q',query],['result',result==='all'?'':result],['sort',sort==='name'?'':sort],['dir',descending?'desc':''],['expand',!pageGroup&&[...expanded].join(',')!==defaultExpanded?([...expanded].join(',')||'none'):'']])if(value)params.set(key,value);
  history.replaceState(null,'',location.pathname+(params.size?'?'+params:'')+location.hash);
}
function exportCSV(){
  const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const columns=['group','task','measurement','unit','mech_implementation','mech_value','reference','reference_execution_mode','reference_value','mech_divided_by_reference','outcome','mech_recorded_at','reference_recorded_at','mech_source','reference_source','reference_measured_source','implementation'];
  const csv=[columns,...visible.map(row=>[row.group,row.title,metrics[row.metric]?.label,metrics[row.metric]?.unit,implementationName(row.record),row.value,referenceName(row.control),row.control.kind==='jit'?'jit':['rust','libdeflate'].includes(row.control.kind)?'aot':'',row.reference,row.ratio,row.direction,row.date,row.referenceDate,implementationURL(row.record)?new URL(implementationURL(row.record),location.origin).href:'',referenceURL(row.control)?new URL(referenceURL(row.control),location.origin).href:'',implementationURL(row.control.record)?new URL(implementationURL(row.control.record),location.origin).href:'',new URL(row.href,location.origin).href])].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download='mech-comparisons.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),0);
}
async function start(){
  $('#summary-search').value=initial.get('q')??'';
  const loaded=await Promise.allSettled([loadCampaigns(),!pageGroup?loadNative():Promise.resolve(undefined),!pageGroup||['benchmarks-game','jit'].includes(pageGroup)?loadGames():Promise.resolve(undefined)]);
  if(loaded[0].status==='rejected')throw loaded[0].reason;
  bundle=loaded[0].value;
  if(loaded[1].status==='fulfilled')native=loaded[1].value;
  else{$('#summary-error').hidden=false;$('#summary-error').textContent='Compression comparisons could not be loaded. '+loaded[1].reason.message;}
  if(loaded[2].status==='fulfilled')games=loaded[2].value;
  else{$('#summary-error').hidden=false;$('#summary-error').textContent+=' Benchmarks Game comparisons could not be loaded. '+loaded[2].reason.message;}
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
    for(const type of ['pointerover','focusin'])$('#group-chart').addEventListener(type,event=>{const key=event.target.closest('[data-compare]')?.dataset.compare;if(!key||key===lastPreview)return;lastPreview=key;const row=visible.find(row=>row.key===key);if(row)$('#group-readout').innerHTML=`<strong>${escape(row.title)}</strong><div class="readout-values"><span>${implementationLink(row.record)} <strong>${escape(formatMetric(row.value,row.metric))}</strong></span><span>${referenceLink(row.control)} <strong>${escape(formatMetric(row.reference,row.metric))}</strong></span><strong class="${row.direction}">${escape(row.label)}</strong></div>`;});
    const choose=event=>{const key=event.target.closest('[data-compare]')?.dataset.compare,row=visible.find(row=>row.key===key);if(row)location.href=row.href;};
    $('#group-chart').addEventListener('click',choose);$('#group-chart').addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();choose(event);}});
    if(globalThis.ResizeObserver){let width=0;new ResizeObserver(entries=>{const next=Math.round(entries[0].contentRect.width);if(next>0&&next!==width){width=next;renderGroupChart();}}).observe($('#group-chart'));}
  }
  render();
}
start().catch(error=>{$('#summary-error').hidden=false;$('#summary-error').textContent=error.message;});
