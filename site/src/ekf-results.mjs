import {validateEKF,selectedRows,relativeTime,referenceFor,referenceOptions,categoryLabels,sampleChart,exportRows,escape,number,formatRatio} from './ekf-model.mjs';
import {comparisonStyle} from './campaigns-model.mjs';
const $=selector=>document.querySelector(selector),params=new URLSearchParams(location.search);
let data,study,rows=[],lastPreview;
const references={};for(const category of Object.keys(categoryLabels)){const peer=params.get('peer_'+category);if(peer)references[category]=peer;}
let mode=['checked','unchecked','both'].includes(params.get('mode'))?params.get('mode'):'both';
let sort=['name','mode','category','peer','rate','mad','n','time','ratio','version'].includes(params.get('sort'))?params.get('sort'):'name',descending=params.get('dir')==='desc';
const option=(value,label)=>'<option value="'+escape(value)+'">'+escape(label)+'</option>';
function plot(){lastPreview=undefined;$('#ekf-chart').innerHTML=sampleChart(rows,{width:$('#ekf-chart').clientWidth,samples:$('#ekf-samples').checked,medians:$('#ekf-medians').checked});}
function render(){
  study=data.studies.find(s=>s.id===$('#ekf-study').value);rows=selectedRows(study,{mode,sort,descending,query:$('#ekf-search').value,references});
  const hasPeers=study.rows.some(row=>!row.is_mech);
  $('#ekf-references').innerHTML=Object.keys(categoryLabels).map(category=>{const peers=referenceOptions(study,category);return peers.length?'<label>'+escape(categoryLabels[category])+' peer<select data-ekf-reference="'+category+'">'+[['','Fastest external'],...peers.map(peer=>[peer,peer])].map(([value,label])=>'<option value="'+escape(value)+'"'+((references[category]??'')===value?' selected':'')+'>'+escape(label)+'</option>').join('')+'</select></label>':'';}).join('');
  $('#ekf-comparison-note').innerHTML=hasPeers?'Time ratios use the selected external peer in the same study, execution category and checked/unchecked mode. The peer is 1×; lower is faster.':'This study contains only Mech backends. Compare with other languages in the <a href="/metrics/ekf/?study=cpu">CPU</a> and <a href="/metrics/ekf/?study=metal">Metal</a> studies.';
  $('#ekf-study-title').textContent=study.title;
  $('#ekf-study-meta').textContent=study.machine+' · '+study.precision+' · '+study.instances.toLocaleString()+' filters'+(study.turns?' · '+study.turns+' turns':'')+' · '+study.recorded_at.slice(0,10);
  $('#ekf-scope').textContent=study.scope;
  $('#ekf-methods').innerHTML='<p>'+escape(data.method)+'</p><p>Compilation and setup are outside the native throughput timers. These results do not measure complete-process startup. Each study retains its own source, machine and publication boundary.</p><pre>'+escape(JSON.stringify(study.methods,null,2))+'</pre><p><a href="'+escape(study.evidence_url)+'">Raw measurements and provenance</a>'+(study.original_evidence_url?' · <a href="'+escape(study.original_evidence_url)+'">Original record</a>':'')+' · <a href="'+escape(data.article_url)+'">IROS article</a></p>';
  const headers=[['name','Implementation'],['category','Category'],['mode','Mode'],['rate','Million filter-turns/s'],['mad','MAD'],['n','n'],['time','Seconds / filter-turn'],...(hasPeers?[['peer','Peer'],['ratio','× peer time']]:[]),['version','Version']];
  $('#ekf-headings').innerHTML='<tr>'+headers.map(([key,label])=>'<th scope="col" aria-sort="'+(sort===key?(descending?'descending':'ascending'):'none')+'"><button class="column-sort" data-ekf-sort="'+key+'">'+label+(sort===key?(descending?' ▾':' ▴'):'')+'</button></th>').join('')+'<th scope="col">Source</th></tr>';
  $('#ekf-rows').innerHTML=rows.map((row,i)=>{const peer=referenceFor(study,row,references),ratio=relativeTime(study,row,references);return '<tr data-ekf-row="'+i+'"><td>'+escape(row.label)+'</td><td>'+escape(categoryLabels[row.category])+'</td><td>'+escape(row.mode)+'</td><td class="number">'+number(row.median)+'</td><td class="number">'+number(row.mad,2)+'</td><td>'+row.n+'</td><td class="number" title="'+row.time_seconds+'">'+row.time_seconds.toExponential(3)+'</td>'+(hasPeers?(peer?'<td><a href="'+escape(peer.source_url)+'">'+escape(peer.label)+'</a><span class="family">'+peer.time_seconds.toExponential(3)+' s/filter-turn</span></td><td><span class="result-tag '+(ratio===1?'equal':ratio<1?'faster':'slower')+'" style="'+comparisonStyle({ratio},'native_process_seconds')+'">'+formatRatio(ratio)+'×</span></td>':'<td>—</td><td>—</td>'):'')+'<td class="ekf-version">'+escape(row.version)+'</td><td><a href="'+escape(row.source_url)+'">Code</a>'+(row.implementation_url?' · <a href="'+escape(row.implementation_url)+'">Original</a>':'')+'</td></tr>';}).join('');
  $('#ekf-row-count').textContent=rows.length+' results · every sample retained';
  $('#ekf-readout').textContent='Hover or focus a row to inspect its median, spread and timing scope.';
  for(const button of $('#ekf-modes').querySelectorAll('[data-ekf-mode]'))button.setAttribute('aria-pressed',String(mode===button.dataset.ekfMode));
  plot();const query=new URLSearchParams(location.search);
  for(const key of ['study','mode','sort','dir','q','samples','medians',...Object.keys(categoryLabels).map(category=>'peer_'+category)])query.delete(key);
  for(const [key,value] of [['study',study.id==='cpu'?'':study.id],['mode',mode==='both'?'':mode],['sort',sort==='name'?'':sort],['dir',descending?'desc':''],['q',$('#ekf-search').value],['samples',$('#ekf-samples').checked?'':'0'],['medians',$('#ekf-medians').checked?'':'0'],...Object.entries(references).map(([category,peer])=>['peer_'+category,peer])])if(value)query.set(key,value);
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+location.hash);
}
function preview(event){
  const id=event.target.closest('[data-ekf-row]')?.dataset.ekfRow;if(id==null||id===lastPreview)return;lastPreview=id;
  const row=rows[Number(id)];if(!row)return;
  const peer=referenceFor(study,row,references);
  $('#ekf-readout').innerHTML='<strong>'+escape(row.label)+' · '+escape(row.mode)+'</strong><div class="readout-values"><span>'+number(row.median)+' ± '+number(row.mad,2)+' million filter-turns/s · median ± MAD</span><span>'+row.time_seconds.toExponential(6)+' s/filter-turn'+(peer?' · '+formatRatio(relativeTime(study,row,references))+'× '+escape(peer.label)+' time ('+peer.time_seconds.toExponential(6)+' s/filter-turn)':'')+'</span><a href="'+escape(row.source_url)+'">Implementation</a></div>';
}
function download(csv,name){const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),0);}
async function start(){
  const url=new URL('./ekf-results.json',import.meta.url);url.search=new URL(import.meta.url).search;
  const response=await fetch(url);if(!response.ok)throw Error('EKF evidence could not be loaded');data=validateEKF(await response.json());
  for(const category of Object.keys(references))if(!data.studies.some(study=>referenceOptions(study,category).includes(references[category])))delete references[category];
  $('#ekf-study').innerHTML=data.studies.map(s=>option(s.id,s.title)).join('');$('#ekf-study').value=data.studies.some(s=>s.id===params.get('study'))?params.get('study'):(data.studies.some(s=>s.id==='cpu')?'cpu':data.studies[0].id);
  $('#ekf-search').value=params.get('q')??'';$('#ekf-samples').checked=params.get('samples')!=='0';$('#ekf-medians').checked=params.get('medians')!=='0';
  $('#ekf-study').addEventListener('change',render);$('#ekf-modes').addEventListener('click',event=>{const key=event.target.closest('[data-ekf-mode]')?.dataset.ekfMode;if(key){mode=key;render();}});
  $('#ekf-references').addEventListener('change',event=>{const category=event.target.dataset.ekfReference;if(categoryLabels[category]){if(event.target.value)references[category]=event.target.value;else delete references[category];render();}});
  $('#ekf-headings').addEventListener('click',event=>{const key=event.target.closest('[data-ekf-sort]')?.dataset.ekfSort;if(key){descending=sort===key?!descending:false;sort=key;render();}});
  for(const id of ['#ekf-samples','#ekf-medians'])$(id).addEventListener('change',render);
  let timer;$('#ekf-search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,100);});
  for(const selector of ['#ekf-chart','#ekf-rows'])for(const type of ['pointerover','focusin'])$(selector).addEventListener(type,preview);
  $('#ekf-export-selection').addEventListener('click',()=>download(exportRows(data.studies,{study:study.id,rows},references),'ekf-selection.csv'));
  $('#ekf-export-all').addEventListener('click',()=>download(exportRows(data.studies,undefined,references),'ekf-all-samples.csv'));
  if(globalThis.ResizeObserver){let width=0;new ResizeObserver(entries=>{const next=Math.round(entries[0].contentRect.width);if(next>0&&width!==next){width=next;plot();}}).observe($('#ekf-chart'));}
  render();
}
start().catch(error=>{$('#ekf-error').hidden=false;$('#ekf-error').textContent=error.message;});
