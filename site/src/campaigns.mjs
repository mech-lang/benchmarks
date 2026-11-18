import {backendLabels,primaryMetric,implementationFor,metrics,formatMetric,recordFor,compareRecords,stageFor,compatibleHistory,measuredRows,controlFor,controlComparison,isMechRecord} from './campaigns-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const pathURL=value=>String(value).split('/').map(encodeURIComponent).join('/');
const short=value=>String(value??'unknown').slice(0,10);
const nice=value=>String(value??'unknown').replaceAll('_',' ');
let bundle,selected,rows=[],detailGeneration=0;
const recordLoads=new WeakMap(),contextLoads=new WeakMap();
const parameters=new URLSearchParams(location.search);

function campaign() {return bundle.campaigns.find(c=>c.id===$('#campaign').value);}
function baseline() {return bundle.campaigns.find(c=>c.id===$('#baseline').value);}
function baselineRecord(row) {return $('#baseline').value==='$paired'?recordFor(row.campaign,row.record.case_id,row.record.backend,'baseline'):recordFor(baseline(),row.record.case_id,row.record.backend);}
function option(value,label){return `<option value="${escape(value)}">${escape(label)}</option>`;}
function badge(value,extra=''){return `<span class="badge ${escape(extra)}">${escape(nice(value))}</span>`;}
function rawLink(campaign,record,suffix='campaign.json') {
  const name=(record?record+'/':'')+suffix;
  return new URL(`${pathURL(campaign.evidence_path)}/${pathURL(campaign.compressed_evidence?.[name]??name)}`,import.meta.url).href;
}

async function detailJSON(path,schema) {
  const url=new URL('./'+path,import.meta.url);
  url.search=new URL(import.meta.url).search;
  const response=await fetch(url);
  if(!response.ok)throw new Error(`Could not load benchmark details (${response.status})`);
  const data=await response.json();
  if(data.schema!==schema)throw new Error('Unsupported benchmark detail data');
  return data;
}

function loadContext(current) {
  if(!current.context_path)return Promise.resolve();
  if(!contextLoads.has(current)){
    const loading=detailJSON(current.context_path,'mech.benchmark-context.v1').then(data=>{
      if(data.campaign.id!==current.id)throw new Error('Benchmark run identity differs');
      Object.assign(current,data.campaign);
    }).catch(error=>{contextLoads.delete(current);throw error;});
    contextLoads.set(current,loading);
  }
  return contextLoads.get(current);
}

function loadRecord(current,record,definition) {
  if(!record?.detail_path)return Promise.resolve();
  if(!recordLoads.has(record)){
    const loading=detailJSON(record.detail_path,'mech.benchmark-observation.v1').then(data=>{
      if(data.campaign_id!==current.id||data.definition.id!==record.case_id)throw new Error('Benchmark observation identity differs');
      for(const key of ['case_id','backend','lane','revision','task_hash','measurement_hash','source_sha256','environment_hash','control_contract']){
        if(JSON.stringify(data.record[key])!==JSON.stringify(record[key]))throw new Error(`Benchmark ${key} differs from its summary`);
      }
      Object.assign(record,data.record);
      if(definition)Object.assign(definition,data.definition);
    }).catch(error=>{recordLoads.delete(record);throw error;});
    recordLoads.set(record,loading);
  }
  return recordLoads.get(record);
}

async function renderDetail() {
  const generation=++detailGeneration,row=rows.find(r=>r.definition.id===selected);
  $('#detail').hidden=!row;
  $('.workspace').className=row?'workspace':'workspace summary';
  if(!row){$('#detail').innerHTML='';return;}
  $('#detail').innerHTML='<p class="empty" role="status">Loading this task’s measurements and evidence…</p>';
  const control=controlFor(bundle,row);
  try {
    await Promise.all([loadContext(row.campaign),loadRecord(row.campaign,row.record,row.definition),
      ...(control.record?[loadContext(control.campaign),loadRecord(control.campaign,control.record)]:[])]);
    if(generation===detailGeneration){
      renderLoadedDetail(row);
      if(globalThis.matchMedia?.('(max-width:820px)')?.matches)$('#detail').scrollIntoView({block:'start'});
    }
  } catch(error){
    if(generation===detailGeneration)$('#detail').innerHTML=`<h2 id="detail-title">${escape(row.definition.title)}</h2><p role="alert">${escape(error.message)}</p><button data-close-detail>Back to summary</button>`;
  }
}

function trend(points,metric) {
  if(!points.length)return '<p class="empty">No compatible measurements yet.</p>';
  const values=points.map(p=>p.value),low=Math.min(...values)*.9,high=Math.max(...values)*1.1;
  const x=index=>55+(points.length===1?.5:index/(points.length-1))*465;
  const y=value=>140-(value-low)/((high-low)||1)*108;
  return `<svg class="trend" viewBox="0 0 560 185" role="img" aria-label="${escape(metrics[metric].label)} across ${points.length} compatible campaigns">
    <line x1="55" y1="145" x2="530" y2="145" class="axis"/><line x1="55" y1="25" x2="55" y2="145" class="axis"/>
    <text x="50" y="22">${escape(formatMetric(high,metric))}</text><text x="50" y="162">${escape(formatMetric(low,metric))}</text>
    <polyline points="${points.map((p,i)=>`${x(i)},${y(p.value)}`).join(' ')}"/>
    ${points.map((p,i)=>`<circle cx="${x(i)}" cy="${y(p.value)}" r="4"><title>${escape(p.campaign)} · ${escape(short(p.revision))} · ${escape(formatMetric(p.value,metric))}</title></circle>`).join('')}
    <text x="55" y="180">${escape(new Date(points[0].date).toLocaleDateString())}</text><text x="525" y="180" text-anchor="end">${escape(new Date(points.at(-1).date).toLocaleDateString())}</text>
    </svg><p class="caption">${points.length===1?'First compatible campaign. Subsequent runs will build this history.':`${points.length} compatible campaigns · medians shown · ${metrics[metric].higherBetter?'higher':'lower'} is better.`}</p>`;
}

function renderLoadedDetail(row) {
  const {definition,campaign:current,record,metric}=row,backend=record.backend;
  let html=`<button class="back-summary" data-close-detail>← Back to summary</button><p class="eyebrow">${escape(definition.family)}</p><h2 id="detail-title">${escape(definition.title)}</h2>
    <div class="badges">${badge(stageFor(definition,record))}${record?badge(record.outcome,record.outcome):''}</div>`;
  if(!record) {
    const available=[...bundle.campaigns].reverse().flatMap(c=>c.results.filter(r=>r.case_id===selected&&r.lane==='candidate'&&r.progress==='measured').map(r=>({c,r})));
    if(available.length)html+=`<p class="detail-note">Measured in another view:</p><div class="run-links">${available.slice(0,6).map(({c,r})=>`<a href="?${new URLSearchParams({campaign:c.id,backend:r.backend,metric:r.measurement.primary_metric??'resident_turn_seconds',case:selected})}">${escape(backendLabels[r.backend]??r.backend)} ↗</a>`).join('')}</div>`;
    html+=`<p class="detail-note">${escape(definition.notes??'This run does not include the selected execution path. Choose an available measurement or another run.')}</p>`;
    if(definition.historical_contract)html+=`<p><a href="https://github.com/mech-lang/benchmarks/blob/main/${pathURL(definition.historical_contract)}">Preserved application contract ↗</a></p>`;
  } else {
    const implementation=implementationFor(current,record);
    const verification=record.verification??{};
    const summary=record.summary?.[metric],comparison=compareRecords(baselineRecord(row),record,metric);
    const control=controlFor(bundle,row),change=controlComparison(row,control);
    const screening=current.comparisons?.find(result=>result.case_id===selected&&result.backend===backend);
    html+=`<div class="measurement"><strong>${escape(formatMetric(summary?.median,metric))}</strong><span>${escape(metrics[metric].label)} · ${record.samples.length} independent ${record.samples.length===1?'fork':'forks'}</span></div>
      ${record.reason?`<p class="failure">${escape(record.reason)}</p>`:''}
      <p class="detail-note">${escape(backendLabels[backend])} · ${escape(current.id)}. Capability: ${escape(nice(record.capability))}.</p>
      ${current.known_interference&&selected.startsWith(current.known_interference.case_prefix)?`<p class="detail-note">${escape(current.known_interference.reason)} <a href="?${new URLSearchParams({campaign:current.known_interference.replacement_campaign,backend,case:selected})}">Inspect the independent repeat ↗</a></p>`:''}
      <section class="control-detail" aria-label="Benchmark control"><h3>Control · ${escape(control.label)}</h3><p>${control.kind==='pending'?'No reference is available for this measurement.':`${escape(formatMetric(control.record.summary[control.metric].median,control.metric))} · ${escape(change.label)}.`} ${escape(control.reason)}</p>${control.kind!=='pending'?`${record.summary?.output_bytes&&control.record.summary?.output_bytes?`<p class="compression-quality">Compressed output: Mech ${escape(formatMetric(record.summary.output_bytes.median,'output_bytes'))}; ${escape(control.label)} ${escape(formatMetric(control.record.summary.output_bytes.median,'output_bytes'))}. Level-12 reference; compare output size with time.</p>`:''}<p><a href="${rawLink(control.campaign,null)}">Control run and observations ↗</a></p><details><summary>Control measurements</summary><div class="control-samples">${control.record.samples.map(sample=>`<a href="${rawLink(control.campaign,sample.raw,'supervised.json')}" target="_blank" rel="noopener"><span>Fork ${sample.fork+1}</span><span>${escape(formatMetric(sample.metrics[control.metric],control.metric))}</span></a>`).join('')}</div></details><details><summary>Control source and provenance</summary><p>Revision <code>${escape(control.record.revision)}</code></p><p>Source SHA-256 <code>${escape(control.record.source_sha256)}</code></p><pre>${escape(control.record.source)}</pre></details>`:''}${control.promotion?`<p>Confirmed against the fixed Rust example in 31 primary and 13 independent rounds. ${escape(control.promotion.rust_reference_note)}</p>`:''}</section>
      ${$('#baseline').value?`<p class="detail-note">History comparison: ${comparison.status==='informational'?escape(`${comparison.label} relative to the selected baseline. ${comparison.reason}`):escape(comparison.reason??'No compatible baseline observation.')}</p>`:''}
      ${$('#baseline').value==='$paired'&&screening?`<p class="detail-note">Paired turn screening: ${escape(nice(screening.status))}. ${escape(screening.reason??'')}${screening.interval_95?` 95% interval: ${screening.interval_95.map(n=>n.toFixed(3)).join('–')}×.`:''}</p>`:''}
      <h3>Over time</h3>${trend(compatibleHistory(bundle.campaigns,record,metric),metric)}
      <details open><summary>Raw fork observations</summary>${summary?`<div class="sample-list">${record.samples.map(sample=>`<a href="${rawLink(current,sample.raw,'supervised.json')}" target="_blank" rel="noopener"><span>Fork ${sample.fork+1}</span><span>${escape(formatMetric(sample.metrics[metric],metric))}</span></a>`).join('')}</div>`:'<p>No accepted timings. Failed and partial observations remain in the campaign evidence.</p>'}</details>
      <details><summary>Task and measurement contracts</summary><p>Output: <code>${escape(record.task.outputs.join(', '))}</code></p><p>${escape(record.measurement.boundary)}</p><dl>${Object.entries(record.measurement).filter(([key])=>key!=='schedule').map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(typeof value==='string'?value:JSON.stringify(value))}</dd>`).join('')}</dl><p>Deterministic input schedule</p><pre>${escape(JSON.stringify(record.measurement.schedule))}</pre><p>${escape(record.task.arithmetic)}</p><p>Task <code>${escape(short(record.task_hash))}</code> · measurement <code>${escape(short(record.measurement_hash))}</code></p></details>
      <details><summary>Correctness and negative control</summary><p>${escape(verification.reason??(backend==='native'?'Every complete fresh-process output matched the independent oracle. Each scheduled input starts a new process.':'The complete declared input trajectory matched the independent Python oracle. Previously published outputs stayed unchanged before execution.'))}</p>${verification.output_count?`<p>${verification.output_count} outputs verified. Preview shows the first and last observations; the raw record includes the full trajectory.</p>`:''}<a href="${rawLink(current,verification.raw,'supervised.json')}" target="_blank" rel="noopener">Inspect verification observations ↗</a><pre>${escape(JSON.stringify(verification.preview_outputs??verification.outputs,null,2))}</pre></details>
      <details><summary>Program source</summary><p>SHA-256 <code>${escape(record.source_sha256)}</code></p><pre class="source"><code>${escape(record.source)}</code></pre></details>
      <details><summary>All measured outcomes</summary><dl>${Object.entries(record.summary??{}).map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(metrics[key]?formatMetric(value.median,key):value.median.toLocaleString(undefined,{maximumFractionDigits:6}))}</dd>`).join('')}</dl></details>
      <details><summary>Compiler and environment</summary><dl><dt>Version / revision</dt><dd><code>${escape(record.revision)}</code></dd><dt>Binary hash</dt><dd><code>${escape(implementation.binary_sha256)}</code></dd><dt>Adapter hash</dt><dd><code>${escape(implementation.adapter_sha256)}</code></dd><dt>Toolchain</dt><dd><pre>${escape(implementation.rustc)}</pre></dd><dt>Machine</dt><dd>${escape(current.environment.cpu)} · ${escape(current.environment.system)} ${escape(current.environment.release)}</dd></dl></details>
      <p class="downloads"><a href="${rawLink(current,null)}" download>Campaign JSON${current.compressed_evidence?.['campaign.json']?' (gzip)':''} ↓</a>${current.raw_archive?`<a href="${rawLink(current,null,current.raw_archive)}" download>Raw evidence archive ↓</a>`:''}<a href="${rawLink(current,null,'report.md')}" target="_blank" rel="noopener">Full report ↗</a>${current.reproduction_url?`<a href="${escape(current.reproduction_url)}" target="_blank" rel="noopener">Reproduction sources ↗</a>`:''}</p>`;
  }
  if(definition.compiler_tests?.length)html+=`<details><summary>Existing compiler test coverage</summary><ul>${definition.compiler_tests.map(test=>`<li><a href="https://github.com/${pathURL(test.repository)}/blob/${bundle.catalog.candidate_revision}/${pathURL(test.path)}" target="_blank" rel="noopener">${escape(test.path)}</a></li>`).join('')}</ul></details>`;
  $('#detail').innerHTML=html;
}

function render() {
  const metric=$('#metric').value,backend=$('#backend').value;
  const cases=bundle.catalog.cases;
  const available=measuredRows(bundle,{campaign:$('#campaign').value,backend,metric});
  const controls=available.map(row=>controlFor(bundle,row));
  $('#stats').innerHTML=[['Measured tasks',available.filter(r=>r.record.outcome==='ok').length],['Families',new Set(available.map(r=>r.definition.family)).size],['External references',controls.filter(c=>['rust','reference'].includes(c.kind)).length],['Mech controls held',controls.filter(c=>c.kind==='mech').length]].map(([label,value])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
  $('#boundary').textContent=metric==='$primary'?'Each task shows its own measured boundary. Rust is the default control for other tasks; DEFLATE uses a libdeflate level-12 reference. A confirmed Mech win establishes a fixed Mech control. Choose a task to inspect the run, control and evidence.':metrics[metric].note;
  $('#metric-heading').textContent=metric==='$primary'?'Mech · median':`Mech · ${metrics[metric].label}`;
  rows=measuredRows(bundle,{campaign:$('#campaign').value,query:$('#search').value,family:$('#family').value,progress:$('#progress').value,backend,metric});
  $('#case-count').textContent=`${rows.length} / ${cases.length} tasks`;
  $('#empty').hidden=rows.length>0;
  if(!rows.some(r=>r.definition.id===selected))selected=undefined;
  $('#cases').innerHTML=rows.map(row=>{
    const {definition,record,metric:rowMetric}=row,stage=stageFor(definition,record),control=controlFor(bundle,row);
    const change=$('#baseline').value?compareRecords(baselineRecord(row),record,rowMetric):controlComparison(row,control);
    const compressed=record.summary?.output_bytes&&rowMetric!=='output_bytes';
    return `<tr class="${definition.id===selected?'selected':''}"><td><button data-case="${escape(definition.id)}" aria-pressed="${definition.id===selected}">${escape(definition.title)}</button><span class="family">${escape(definition.family)} · ${escape(backendLabels[record.backend])}</span>${record.outcome!=='ok'?badge(record.outcome,'failure'):''}</td><td class="number mech-value">${record.outcome==='ok'?escape(formatMetric(record.summary?.[rowMetric]?.median,rowMetric)):escape(nice(record.outcome))}<span class="family">${escape(metrics[rowMetric]?.label??rowMetric)}</span>${compressed?`<span class="family">${escape(formatMetric(record.summary.output_bytes.median,'output_bytes'))} output</span>`:''}</td><td class="control-value" title="${escape(control.reason)}"><span>${escape(control.label)}</span>${control.kind!=='pending'?`<strong>${escape(formatMetric(control.record.summary[control.metric].median,control.metric))}</strong>${compressed&&control.record.summary?.output_bytes?`<span class="family">${escape(formatMetric(control.record.summary.output_bytes.median,'output_bytes'))} output</span>`:''}`:''}</td><td class="number change ${change.percent<0?'faster':''}" title="${escape(change.reason??'')}">${escape(change.label)}${compressed?'<span class="family">Level-12 reference</span>':''}</td></tr>`;
  }).join('');
  const details=renderDetail();
  const query=new URLSearchParams();
  for(const [key,value] of [['campaign',$('#campaign').value],['baseline',$('#baseline').value],['metric',metric],['backend',backend],['case',selected]])if(value)query.set(key,value);
  history.replaceState(null,'',`${location.pathname}?${query}`);
  return details;
}

async function start() {
  const compressed=typeof DecompressionStream==='function';
  const dataURL=new URL(compressed?'./campaigns.json.gz':'./campaigns.json',import.meta.url);
  dataURL.search=new URL(import.meta.url).search;
  const response=await fetch(dataURL);
  if(!response.ok)throw new Error(`Could not load campaign data (${response.status})`);
  bundle=compressed&&response.headers.get('content-encoding')!=='gzip'
    ?await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json()
    :await response.json();
  if(!['mech.benchmark-dashboard.v1','mech.benchmark-dashboard.v2'].includes(bundle.schema))throw new Error('Unsupported dashboard data');
  const choices=[...bundle.campaigns].reverse();
  $('#backend').innerHTML=option('$auto','Preferred path for each task')+Object.entries(backendLabels).map(([key,label])=>option(key,label)).join('');
  const complete=new Set(measuredRows(bundle).filter(row=>row.record.progress==='measured'&&row.record.outcome==='ok').map(row=>row.definition.id));
  $('#coverage-summary').textContent=`${complete.size} of ${bundle.catalog.cases.length} tasks have accepted measurements across all runs.`;
  $('#run-links').innerHTML=`<a href="${location.pathname}">All measured tasks</a>`+[['Resident suite','source'],['Full applications','program-jit'],['Related Post Gen','related-managed'],['Worker scaling','process-workers'],['Native compilation','native']].flatMap(([label,backend])=>{const c=choices.find(c=>c.results.some(r=>r.backend===backend&&r.progress==='measured'));const r=c?.results.find(r=>r.backend===backend&&r.progress==='measured');return r?[`<a href="?${new URLSearchParams({backend,case:r.case_id})}">${escape(label)} ↗</a>`]:[];}).join('');
  $('#campaign').innerHTML=option('$latest','Latest measured result for every task')+choices.map(c=>option(c.id,`${c.id} · ${short(c.workers?.candidate?.revision)}`)).join('');
  $('#baseline').innerHTML=option('','Use task control')+option('$paired','Paired previous Mech worker')+choices.map(c=>option(c.id,c.id)).join('');
  $('#metric').innerHTML=option('$primary','Primary measurement for each task')+Object.entries(metrics).filter(([,meta])=>!meta.controlOnly).map(([key,meta])=>option(key,meta.label)).join('');
  $('#family').innerHTML+=Array.from(new Set(bundle.catalog.cases.map(c=>c.family))).sort().map(f=>option(f,nice(f))).join('');
  for(const selector of ['campaign','baseline','metric','backend'])if(parameters.has(selector)&&[...$(`#${selector}`).options].some(o=>o.value===parameters.get(selector)))$(`#${selector}`).value=parameters.get(selector);
  if(!parameters.has('campaign'))$('#campaign').value='$latest';
  if(!parameters.has('backend'))$('#backend').value='$auto';
  if(!parameters.has('metric'))$('#metric').value='$primary';
  selected=parameters.get('case')??undefined;
  for(const selector of ['#campaign','#baseline','#metric','#backend','#family','#progress'])$(selector).addEventListener('change',()=>{
    if(selector==='#backend'&&campaign()&&$('#backend').value!=='$auto'&&!campaign().results.some(r=>r.backend===$('#backend').value)){
      const matching=choices.find(c=>c.results.some(r=>r.backend===$('#backend').value&&isMechRecord(r)));
      if(matching)$('#campaign').value=matching.id;
    }
    if(selector==='#campaign'&&campaign()?.results.length&&!campaign().results.some(r=>r.backend===$('#backend').value))$('#backend').value='$auto';
    if(['#campaign','#backend'].includes(selector)){
      $('#metric').value='$primary';
      if(!campaign()?.workers.baseline&&$('#baseline').value==='$paired')$('#baseline').value='';
    }
    return render();
  });
  $('#search').addEventListener('input',render);
  $('#cases').addEventListener('click',event=>{const button=event.target.closest('[data-case]');if(button){selected=button.dataset.case;return render();}});
  $('#detail').addEventListener('click',event=>{if(event.target.closest('[data-close-detail]')){selected=undefined;return render();}});
  await render();
}

start().catch(error=>{$('#load-error').hidden=false;$('#load-error').textContent=error.message;$('#stats').textContent='Benchmark history is unavailable. Rebuild the site after checking the campaign files.';});
