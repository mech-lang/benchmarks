import {validateEKF,mechMeasurements,selectedMeasurements,sampleChart,exportRows,escape,number,formatRatio} from './ekf-model.mjs';
import {comparisonStyle,formatMetric} from './campaigns-model.mjs';
const $=selector=>document.querySelector(selector),params=new URLSearchParams(location.search),metric='ekf_filter_turn_seconds';
let data,rows=[],lastPreview;
let mode=['checked','unchecked','both'].includes(params.get('mode'))?params.get('mode'):'checked';
let sort=['name','mode','mech','peer','reference','ratio'].includes(params.get('sort'))?params.get('sort'):'name',descending=params.get('dir')==='desc';
const time=value=>formatMetric(value,metric);
function plot(){lastPreview=undefined;$('#ekf-chart').innerHTML=sampleChart(rows.map(row=>({...row,label:row.variant})),{width:$('#ekf-chart').clientWidth,samples:$('#ekf-samples').checked,medians:$('#ekf-medians').checked});}
function render(){
  rows=selectedMeasurements(data,{mode,sort,descending,query:$('#ekf-search').value});
  const headers=[['name','Mech variant'],...(mode==='both'?[['mode','Mode']]:[]),['mech','Mech time'],['peer','Closest peer'],['reference','Peer time'],['ratio','Mech / peer']];
  $('#ekf-headings').innerHTML='<tr>'+headers.map(([key,label])=>'<th scope="col" aria-sort="'+(sort===key?(descending?'descending':'ascending'):'none')+'"><button class="column-sort" data-ekf-sort="'+key+'">'+label+(sort===key?(descending?' ▾':' ▴'):'')+'</button></th>').join('')+'</tr>';
  $('#ekf-rows').innerHTML=rows.map((row,i)=>'<tr data-ekf-row="'+i+'"><td><a href="'+escape(row.source_url)+'">'+escape(row.variant)+'</a></td>'+(mode==='both'?'<td>'+escape(row.mode)+'</td>':'')+'<td class="number">'+time(row.time_seconds)+'</td><td>'+(row.peer?'<a href="'+escape(row.peer.source_url)+'">'+escape(row.peer.label)+'</a>':'<span class="family">No matched peer retained</span>')+'</td><td class="number">'+time(row.peer?.time_seconds)+'</td><td>'+(row.ratio==null?'—':'<span class="result-tag '+(row.ratio===1?'equal':row.ratio<1?'faster':'slower')+'" style="'+comparisonStyle({ratio:row.ratio},metric)+'">'+formatRatio(row.ratio)+'×</span>')+'</td></tr>').join('');
  $('#ekf-row-count').textContent=rows.length+' Mech results';
  $('#ekf-readout').textContent='Hover or focus a Mech result for its timings, reference and measurement scope.';
  for(const button of $('#ekf-modes').querySelectorAll('[data-ekf-mode]'))button.setAttribute('aria-pressed',String(mode===button.dataset.ekfMode));
  plot();const query=new URLSearchParams(location.search);
  for(const key of [...query.keys()])if(['study','mode','sort','dir','q','samples','medians'].includes(key)||key.startsWith('peer_'))query.delete(key);
  for(const [key,value] of [['mode',mode==='checked'?'':mode],['sort',sort==='name'?'':sort],['dir',descending?'desc':''],['q',$('#ekf-search').value],['samples',$('#ekf-samples').checked?'':'0'],['medians',$('#ekf-medians').checked?'':'0']])if(value)query.set(key,value);
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+location.hash);
}
function preview(event){
  const id=event.target.closest('[data-ekf-row]')?.dataset.ekfRow;if(id==null||id===lastPreview)return;lastPreview=id;
  const row=rows[Number(id)];if(!row)return;
  $('#ekf-readout').innerHTML='<strong>'+escape(row.variant)+' · '+escape(row.mode)+'</strong><div class="readout-values"><span>Mech: '+row.time_seconds.toExponential(6)+' s/filter-turn · '+number(row.median)+' ± '+number(row.mad,2)+' M filter-turns/s · median ± MAD · n='+row.n+'</span>'+(row.peer?'<span>'+escape(row.peer.label)+': '+row.peer.time_seconds.toExponential(6)+' s/filter-turn · '+formatRatio(row.ratio)+'× peer time</span>':'')+'<span>'+escape(row.study.machine+' · '+row.study.recorded_at.slice(0,10)+' · '+row.study.scope)+'</span></div>';
}
function download(csv,name){const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),0);}
async function start(){
  const url=new URL('./ekf-results.json',import.meta.url);url.search=new URL(import.meta.url).search;
  const response=await fetch(url);if(!response.ok)throw Error('EKF evidence could not be loaded');data=validateEKF(await response.json());
  $('#ekf-search').value=params.get('q')??'';$('#ekf-samples').checked=params.get('samples')!=='0';$('#ekf-medians').checked=params.get('medians')!=='0';
  $('#ekf-methods').innerHTML='<p>'+escape(data.method)+'</p><p>Closest peers use the same recorded campaign, execution category, publication boundary and checked/unchecked mode. The fastest eligible external implementation supplies the reference. Single-worker backend results have no external measurement in their campaign; a blank ratio means no qualified comparison. These kernel timings exclude compilation and setup.</p>'+data.studies.map(study=>'<details><summary>'+escape(study.title)+'</summary><p>'+escape(study.machine+' · '+study.recorded_at.slice(0,10)+' · '+study.scope)+'</p><pre>'+escape(JSON.stringify(study.methods,null,2))+'</pre><a href="'+escape(study.evidence_url)+'">Raw evidence and versions</a></details>').join('');
  $('#ekf-modes').addEventListener('click',event=>{const key=event.target.closest('[data-ekf-mode]')?.dataset.ekfMode;if(key){mode=key;render();}});
  $('#ekf-headings').addEventListener('click',event=>{const key=event.target.closest('[data-ekf-sort]')?.dataset.ekfSort;if(key){descending=sort===key?!descending:false;sort=key;render();}});
  for(const id of ['#ekf-samples','#ekf-medians'])$(id).addEventListener('change',render);
  let timer;$('#ekf-search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,100);});
  for(const selector of ['#ekf-chart','#ekf-rows'])for(const type of ['pointerover','focusin'])$(selector).addEventListener(type,preview);
  $('#ekf-export-selection').addEventListener('click',()=>download(exportRows(data.studies,rows),'mech-ekf-selection.csv'));
  $('#ekf-export-all').addEventListener('click',()=>download(exportRows(data.studies,mechMeasurements(data)),'mech-ekf-samples.csv'));
  if(globalThis.ResizeObserver){let width=0;new ResizeObserver(entries=>{const next=Math.round(entries[0].contentRect.width);if(next>0&&width!==next){width=next;plot();}}).observe($('#ekf-chart'));}
  render();
}
start().catch(error=>{$('#ekf-error').hidden=false;$('#ekf-error').textContent=error.message;});
