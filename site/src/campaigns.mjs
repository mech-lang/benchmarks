import {backendLabels,primaryMetric,implementationFor,metrics,formatMetric,recordFor,compareRecords,stageFor,compatibleHistory,measuredRows,controlFor,controlComparison,isMechRecord,comparisonDirection,comparisonLabel,comparisonPlot,referenceName,referenceLink,implementationLink} from './campaigns-model.mjs';
import {metricsRoute,metricGroups,suiteMeasurements} from './metrics-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const pathURL=value=>String(value).split('/').map(encodeURIComponent).join('/');
const short=value=>String(value??'unknown').slice(0,10);
const nice=value=>String(value??'unknown').replaceAll('_',' ');
let bundle,selected,rows=[],detailGeneration=0;
const recordLoads=new WeakMap(),contextLoads=new WeakMap();
const parameters=new URLSearchParams(location.search);
const route=metricsRoute(location.pathname,location.search);
const scoped=route.group!=='all'||!!route.task;
const defaultMetric=route.task?'$primary':scoped?'$all':'$primary';
const defaultOutcome=['compiler','size','memory','lifecycle','compression-history'].includes(route.group)||route.task?'all':'matched';
let suiteSort=['name','mech','reference','ratio'].includes(parameters.get('sort'))?parameters.get('sort'):'name',suiteDescending=parameters.get('dir')==='desc';
let outcome=parameters.get('result')??(parameters.has('case')?'all':defaultOutcome);
if(!['matched','faster','slower','all'].includes(outcome))outcome='matched';

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
  const control=referenceFor(row);
  try {
    await Promise.all([loadContext(row.campaign),loadRecord(row.campaign,row.record,row.definition),
      ...(control.record?[loadContext(control.campaign),loadRecord(control.campaign,control.record)]:[])]);
    if(generation===detailGeneration){
      renderLoadedDetail(row);
      if(route.task){$('#page-title').textContent=row.definition.title;document.title=`Mech · ${row.definition.title}`;}
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
  let html=`<button class="back-summary" data-close-detail>Back to tasks</button><h2 id="detail-title">${escape(definition.title)}</h2>`;
  if(!record) {
    const available=[...bundle.campaigns].reverse().flatMap(c=>c.results.filter(r=>r.case_id===selected&&r.lane==='candidate'&&r.progress==='measured').map(r=>({c,r})));
    if(available.length)html+=`<p class="detail-note">Measured in another view:</p><div class="run-links">${available.slice(0,6).map(({c,r})=>`<a href="?${new URLSearchParams({campaign:c.id,backend:r.backend,metric:r.measurement.primary_metric??'resident_turn_seconds',case:selected})}">${escape(backendLabels[r.backend]??r.backend)}</a>`).join('')}</div>`;
    html+=`<p class="detail-note">${escape(definition.notes??'This run does not include the selected execution path. Choose an available measurement or another run.')}</p>`;
    if(definition.historical_contract)html+=`<p><a href="https://github.com/mech-lang/benchmarks/blob/main/${pathURL(definition.historical_contract)}">Preserved application contract</a></p>`;
  } else {
    const implementation=implementationFor(current,record);
    const verification=record.verification??{};
    const summary=record.summary?.[metric],comparison=compareRecords(baselineRecord(row),record,metric);
    const control=referenceFor(row),change=changeFor(row,control);
    const direction=comparisonDirection(change,metric);
    const screening=current.comparisons?.find(result=>result.case_id===selected&&result.backend===backend);
    html+=`<div class="measurement"><strong>${escape(formatMetric(summary?.median,metric))}</strong><span>${escape(metrics[metric].label)} · ${record.samples.length} independent ${record.samples.length===1?'fork':'forks'}</span></div>
      ${record.reason?`<p class="failure">${escape(record.reason)}</p>`:''}
      <p><span class="result-tag ${direction}">${escape(comparisonLabel(change,metric))}</span></p>
      <p class="implementation-links">${implementationLink(record)} source · ${referenceLink(control)} source</p>
      ${current.known_interference&&selected.startsWith(current.known_interference.case_prefix)?`<p class="detail-note">${escape(current.known_interference.reason)} <a href="?${new URLSearchParams({campaign:current.known_interference.replacement_campaign,backend,case:selected})}">Inspect the independent repeat</a></p>`:''}
      <section class="control-detail" aria-label="Benchmark control"><h3>Reference · ${referenceLink(control)}</h3><p>${control.kind==='pending'?'A matched comparison is not available for this measurement.':`${escape(formatMetric(control.record.summary[control.metric].median,control.metric))} · ${escape(comparisonLabel(change,metric))}.`}</p><details><summary>Comparison scope</summary><p>${escape(control.reason)}</p></details>${control.kind!=='pending'?`${record.summary?.output_bytes&&control.record.summary?.output_bytes?`<p class="compression-quality">Compressed output: Mech ${escape(formatMetric(record.summary.output_bytes.median,'output_bytes'))}; ${referenceLink(control)} ${escape(formatMetric(control.record.summary.output_bytes.median,'output_bytes'))}. Compare output size with time.</p>`:''}<p><a href="${rawLink(control.campaign,null)}">Control run and observations</a></p><details><summary>Control measurements</summary><div class="control-samples">${control.record.samples.map(sample=>`<a href="${rawLink(control.campaign,sample.raw,'supervised.json')}" target="_blank" rel="noopener"><span>Fork ${sample.fork+1}</span><span>${escape(formatMetric(sample.metrics[control.metric],control.metric))}</span></a>`).join('')}</div></details><details><summary>Control source and provenance</summary><p>Revision <code>${escape(control.record.revision)}</code></p><p>Source SHA-256 <code>${escape(control.record.source_sha256)}</code></p><pre>${escape(control.record.source)}</pre></details>`:''}${control.promotion?`<p>Confirmed against the fixed Rust example in 31 primary and 13 independent rounds. ${escape(control.promotion.rust_reference_note)}</p>`:''}</section>
      ${$('#baseline').value?`<p class="detail-note">History comparison: ${comparison.status==='informational'?escape(`${comparison.label} relative to the selected baseline. ${comparison.reason}`):escape(comparison.reason??'No compatible baseline observation.')}</p>`:''}
      ${$('#baseline').value==='$paired'&&screening?`<p class="detail-note">Paired turn screening: ${escape(nice(screening.status))}. ${escape(screening.reason??'')}${screening.interval_95?` 95% confidence interval: ${screening.interval_95.map(n=>n.toFixed(3)).join('–')}×.`:''}</p>`:''}
      <details><summary>Earlier matched measurements</summary>${trend(compatibleHistory(bundle.campaigns,record,metric),metric)}</details>
      <details><summary>Individual timing observations</summary>${summary?`<div class="sample-list">${record.samples.map(sample=>`<a href="${rawLink(current,sample.raw,'supervised.json')}" target="_blank" rel="noopener"><span>Fork ${sample.fork+1}</span><span>${escape(formatMetric(sample.metrics[metric],metric))}</span></a>`).join('')}</div>`:'<p>No accepted timings. Failed and partial observations remain in the campaign evidence.</p>'}</details>
      <details><summary>Task and measurement contracts</summary><p>Output: <code>${escape(record.task.outputs.join(', '))}</code></p><p>${escape(record.measurement.boundary)}</p><dl>${Object.entries(record.measurement).filter(([key])=>key!=='schedule').map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(typeof value==='string'?value:JSON.stringify(value))}</dd>`).join('')}</dl><p>Deterministic input schedule</p><pre>${escape(JSON.stringify(record.measurement.schedule))}</pre><p>${escape(record.task.arithmetic)}</p><p>Task <code>${escape(short(record.task_hash))}</code> · measurement <code>${escape(short(record.measurement_hash))}</code></p></details>
      <details><summary>Correctness and negative control</summary><p>${escape(verification.reason??(backend==='native'?'Every complete fresh-process output matched the independent oracle. Each scheduled input starts a new process.':'The complete declared input trajectory matched the independent Python oracle. Previously published outputs stayed unchanged before execution.'))}</p>${verification.output_count?`<p>${verification.output_count} outputs verified. Preview shows the first and last observations; the raw record includes the full trajectory.</p>`:''}<a href="${rawLink(current,verification.raw,'supervised.json')}" target="_blank" rel="noopener">Inspect verification observations</a><pre>${escape(JSON.stringify(verification.preview_outputs??verification.outputs,null,2))}</pre></details>
      <details><summary>Mech program source</summary><p>${implementationLink(record,'Open Mech source')} · SHA-256 <code>${escape(record.source_sha256)}</code></p><pre class="source"><code>${escape(record.source)}</code></pre></details>
      <details><summary>All measured outcomes</summary><dl>${Object.entries(record.summary??{}).map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(metrics[key]?formatMetric(value.median,key):value.median.toLocaleString(undefined,{maximumFractionDigits:6}))}</dd>`).join('')}</dl></details>
      <details><summary>Compiler and environment</summary><dl><dt>Version / revision</dt><dd><code>${escape(implementation.source_publication_revision??record.revision)}</code></dd><dt>Binary hash</dt><dd><code>${escape(implementation.binary_sha256)}</code></dd><dt>Adapter hash</dt><dd><code>${escape(implementation.adapter_sha256)}</code></dd><dt>Toolchain</dt><dd><pre>${escape(implementation.rustc)}</pre></dd><dt>Machine</dt><dd>${escape(current.environment.cpu)} · ${escape(current.environment.system)} ${escape(current.environment.release)}</dd></dl></details>
      <p class="downloads"><a href="${rawLink(current,null)}" download>Campaign JSON${current.compressed_evidence?.['campaign.json']?' (gzip)':''}</a>${current.raw_archive?`<a href="${rawLink(current,null,current.raw_archive)}" download>Raw evidence archive</a>`:''}<a href="${rawLink(current,null,'report.md')}" target="_blank" rel="noopener">Full report</a>${current.reproduction_url?`<a href="${escape(current.reproduction_url)}" target="_blank" rel="noopener">Reproduction sources</a>`:''}</p>`;
  }
  if(definition.compiler_tests?.length)html+=`<details><summary>Existing compiler test coverage</summary><ul>${definition.compiler_tests.map(test=>`<li><a href="https://github.com/${pathURL(test.repository)}/blob/${bundle.catalog.candidate_revision}/${pathURL(test.path)}" target="_blank" rel="noopener">${escape(test.path)}</a></li>`).join('')}</ul></details>`;
  $('#detail').innerHTML=html;
}

function referenceFor(row) {
  if(!$('#baseline').value)return controlFor(bundle,row);
  const origin=$('#baseline').value==='$paired'?row.campaign:baseline();
  const record=baselineRecord(row),comparison=compareRecords(record,row.record,row.metric);
  if(comparison.status!=='informational')return {kind:'pending',label:'No matched Mech baseline',reason:comparison.reason??'The selected history does not include a comparable observation.'};
  return {kind:'history',label:'Mech',record,campaign:origin,metric:row.metric,reason:'Same task, source, execution path, environment and measurement contract.'};
}
function changeFor(row,control=referenceFor(row)) {
  return control.kind==='history'?compareRecords(control.record,row.record,row.metric):controlComparison(row,control);
}
function summarize(entries) {
  const counts={faster:0,slower:0,equal:0,unmatched:0};
  for(const row of entries)counts[comparisonDirection(changeFor(row),row.metric)]++;
  return counts;
}
function suiteMeasure() {
  if(new Set(rows.map(row=>metrics[row.metric]?.unit)).size>1)return 'measurement';
  const metric=rows[0]?.metric??'native_program_call_seconds';
  return metrics[metric]?.unit==='bytes'?'size':metrics[metric]?.unit==='rate'?'throughput':metrics[metric]?.unit==='count'?'count':'time';
}
function renderSuiteChart() {
  $('#suite-chart').innerHTML=comparisonPlot(rows.map(row=>{const c=changeFor(row);return {id:plotID(row),title:row.definition.title,ratio:c.ratio,direction:comparisonDirection(c,row.metric),label:comparisonLabel(c,row.metric)};}),{width:$('#suite-chart').clientWidth,measure:suiteMeasure(),label:'Mech compared with its reference'});
  $('#suite-chart-key').textContent=suiteMeasure()==='throughput'?'Above 1×: Mech has higher throughput. Below 1×: Mech has lower throughput.':suiteMeasure()==='time'?'Below 1×: Mech takes less time. Above 1×: Mech takes more time.':'Below 1×: Mech uses less. Above 1×: Mech uses more.';
}
function previewSuite(id) {
  const row=rows.find(r=>r.definition.id===id||plotID(r)===id);if(!row)return;
  const control=referenceFor(row),change=changeFor(row,control);
  $('#suite-readout').innerHTML=`<strong>${escape(row.definition.title)}</strong><div class="readout-values"><span>Mech <strong>${escape(formatMetric(row.record.summary?.[row.metric]?.median,row.metric))}</strong></span><span>${referenceLink(control)}${control.record?` <strong>${escape(formatMetric(control.record.summary?.[control.metric]?.median,control.metric))}</strong>`:''}</span><strong class="${comparisonDirection(change,row.metric)}">${escape(comparisonLabel(change,row.metric))}</strong></div>`;
}
function pageRows(options={}) {
  if(!scoped)return measuredRows(bundle,options);
  return suiteMeasurements(bundle,{...options,group:route.group,task:route.task}).filter(row=>
    (!options.query||`${row.definition.id} ${row.definition.title} ${row.definition.family}`.toLowerCase().includes(options.query.toLowerCase()))&&
    (!options.family||options.family==='all'||row.definition.family===options.family)&&
    (!options.progress||options.progress==='all'||(options.progress==='failed'?row.record.outcome!=='ok':stageFor(row.definition,row.record)===options.progress)));
}
const plotID=row=>`${row.definition.id}/${row.record.backend}/${row.metric}`;
function render() {
  const metric=$('#metric').value,backend=$('#backend').value;
  const available=pageRows({campaign:$('#campaign').value,backend,metric});
  const counts=summarize(available);
  const dates=available.map(row=>row.campaign.started_at).filter(Boolean).sort();
  const asof=dates.at(-1);
  $('#suite-asof').textContent=asof?'Latest measurement '+asof.slice(0,10):'Published measurements';
  $('#stats').innerHTML=[['Wins',counts.faster,'faster'],['Losses',counts.slower,'slower'],['Ties',counts.equal,'equal']].map(([label,value,kind])=>`<div><strong class="${kind}">${value}</strong><span>${label}</span></div>`).join('');
  $('#boundary').textContent=['$primary','$all'].includes(metric)?'Every row names its measurement and reference. Ratios are Mech divided by that reference; timings, sizes and counts remain separate measurements.':metrics[metric].note;
  $('#metric-heading').textContent=['$primary','$all'].includes(metric)?'Mech':`Mech · ${metrics[metric].label}`;
  const candidates=pageRows({campaign:$('#campaign').value,query:$('#search').value,family:$('#family').value,progress:$('#progress').value,backend,metric});
  rows=candidates.filter(row=>{const state=comparisonDirection(changeFor(row),row.metric);return outcome==='all'||(outcome==='matched'?state!=='unmatched':state===outcome);});
  rows.sort((a,b)=>{const value=row=>suiteSort==='name'?row.definition.title:suiteSort==='mech'?row.record.summary?.[row.metric]?.median:suiteSort==='reference'?referenceFor(row).record?.summary?.[referenceFor(row).metric]?.median:changeFor(row).ratio;const x=value(a),y=value(b);return (suiteDescending?-1:1)*(typeof x==='string'?x.localeCompare(y):(x??Infinity)-(y??Infinity));});
  for(const button of $('#suite-headings').querySelectorAll?.('[data-case-sort]')??[])button.closest('th').setAttribute('aria-sort',suiteSort===button.dataset.caseSort?(suiteDescending?'descending':'ascending'):'none');
  $('#case-count').textContent=`${rows.length} ${rows.length===1?'measurement':'measurements'}`;
  $('#empty').hidden=rows.length>0;
  for(const button of $('#suite-outcomes').querySelectorAll?.('[data-outcome]')??[])button.setAttribute('aria-pressed',String(button.dataset.outcome===outcome));
  if(!rows.some(r=>r.definition.id===selected))selected=undefined;
  $('#cases').innerHTML=rows.map(row=>{
    const {definition,record,metric:rowMetric}=row,control=referenceFor(row),change=changeFor(row,control);
    const direction=comparisonDirection(change,rowMetric);
    return `<tr class="${definition.id===selected?'selected':''}"><td><button data-case="${escape(definition.id)}" data-metric="${escape(rowMetric)}" aria-pressed="${definition.id===selected}">${escape(definition.title)}</button><span class="family">${escape(nice(definition.family))} · ${escape(backendLabels[record.backend])}</span>${record.outcome!=='ok'?badge(record.outcome,'failure'):''}</td><td class="number mech-value">${record.outcome==='ok'?escape(formatMetric(record.summary?.[rowMetric]?.median,rowMetric)):escape(nice(record.outcome))}<span class="family">${escape(metrics[rowMetric]?.label??rowMetric)}</span></td><td class="control-value"><span>${referenceLink(control)}</span>${control.record?`<strong>${escape(formatMetric(control.record.summary?.[control.metric]?.median,control.metric))}</strong>`:''}</td><td><span class="result-tag ${direction}">${escape(comparisonLabel(change,rowMetric))}</span></td></tr>`;
  }).join('');
  renderSuiteChart();
  if(selected)previewSuite(selected);else $('#suite-readout').textContent='Select a point or task to see its timings.';
  const details=renderDetail();
  const query=new URLSearchParams(location.search);
  for(const key of ['campaign','baseline','metric','backend','case','q','family','progress','result','sort','dir'])query.delete(key);
  for(const [key,value,defaultValue] of [['campaign',$('#campaign').value,'$latest'],['baseline',$('#baseline').value,''],['metric',metric,defaultMetric],['backend',backend,'$auto'],['case',selected,undefined],['q',$('#search').value,''],['family',$('#family').value,'all'],['progress',$('#progress').value,'all'],['result',outcome,defaultOutcome],['sort',suiteSort,'name'],['dir',suiteDescending?'desc':'','']])if(value&&value!==defaultValue)query.set(key,value);
  history.replaceState(null,'',location.pathname+(query.size?'?'+query:'')+(location.hash??''));
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
  $('#run-links').innerHTML=`<a href="${location.pathname}">All measured tasks</a>`+[['Resident suite','source'],['Full applications','program-jit'],['Related Post Gen','related-managed'],['Worker scaling','process-workers'],['Native compilation','native']].flatMap(([label,backend])=>{const c=choices.find(c=>c.results.some(r=>r.backend===backend&&r.progress==='measured'));const r=c?.results.find(r=>r.backend===backend&&r.progress==='measured');return r?[`<a href="?${new URLSearchParams({backend,case:r.case_id})}">${escape(label)}</a>`]:[];}).join('');
  $('#campaign').innerHTML=option('$latest','Latest measured result for every task')+choices.map(c=>option(c.id,`${c.id} · ${short(c.workers?.candidate?.revision)}`)).join('');
  $('#baseline').innerHTML=option('','Use task control')+option('$paired','Paired previous Mech worker')+choices.map(c=>option(c.id,c.id)).join('');
  $('#metric').innerHTML=(scoped?option('$all','All measurements in this group'):'')+option('$primary','Primary measurement for each task')+Object.entries(metrics).filter(([key,meta])=>!meta.controlOnly&&(route.group==='all'||metricGroups.find(group=>group.id===route.group)?.metrics.includes(key))).map(([key,meta])=>option(key,meta.label)).join('');
  $('#family').innerHTML+=Array.from(new Set(bundle.catalog.cases.map(c=>c.family))).sort().map(f=>option(f,nice(f))).join('');
  for(const selector of ['campaign','baseline','metric','backend'])if(parameters.has(selector)&&[...$(`#${selector}`).options].some(o=>o.value===parameters.get(selector)))$(`#${selector}`).value=parameters.get(selector);
  if(!parameters.has('campaign'))$('#campaign').value='$latest';
  if(!parameters.has('backend'))$('#backend').value='$auto';
  if(!parameters.has('metric'))$('#metric').value=defaultMetric;
  selected=route.task??parameters.get('case')??undefined;
  $('#search').value=parameters.get('q')??'';
  for(const selector of ['family','progress'])if(parameters.has(selector)&&[...$(`#${selector}`).options].some(o=>o.value===parameters.get(selector)))$(`#${selector}`).value=parameters.get(selector);
  if(route.task){$('#stats').hidden=true;$('#suite-outcomes').hidden=true;}
  $('#suite-headings').addEventListener('click',event=>{const button=event.target.closest('[data-case-sort]');if(button){const key=button.dataset.caseSort;suiteDescending=key===suiteSort?!suiteDescending:false;suiteSort=key;return render();}});
  $('#suite-outcomes').addEventListener('click',event=>{const button=event.target.closest('[data-outcome]');if(button){outcome=button.dataset.outcome;return render();}});
  let lastPreview;
  for(const type of ['pointerover','focusin'])$('#suite-chart').addEventListener(type,event=>{const id=event.target.closest('[data-compare]')?.dataset.compare;if(id&&id!==lastPreview){lastPreview=id;previewSuite(id);}});
  const choosePlot=event=>{const id=event.target.closest('[data-compare]')?.dataset.compare,row=rows.find(row=>plotID(row)===id);if(row){selected=row.definition.id;$('#metric').value=row.metric;return render();}};
  $('#suite-chart').addEventListener('click',choosePlot);
  $('#suite-chart').addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();return choosePlot(event);}});
  if(globalThis.ResizeObserver){let lastWidth=0;new ResizeObserver(entries=>{const width=Math.round(entries[0].contentRect.width);if(width>0&&width!==lastWidth){lastWidth=width;renderSuiteChart();}}).observe($('#suite-chart'));}

  for(const selector of ['#campaign','#baseline','#metric','#backend','#family','#progress'])$(selector).addEventListener('change',()=>{
    if(selector==='#backend'&&campaign()&&$('#backend').value!=='$auto'&&!campaign().results.some(r=>r.backend===$('#backend').value)){
      const matching=choices.find(c=>c.results.some(r=>r.backend===$('#backend').value&&isMechRecord(r)));
      if(matching)$('#campaign').value=matching.id;
    }
    if(selector==='#campaign'&&campaign()?.results.length&&!campaign().results.some(r=>r.backend===$('#backend').value))$('#backend').value='$auto';
    if(['#campaign','#backend'].includes(selector)){
      $('#metric').value=defaultMetric;
      if(!campaign()?.workers.baseline&&$('#baseline').value==='$paired')$('#baseline').value='';
    }
    return render();
  });
  $('#search').addEventListener('input',render);
  $('#cases').addEventListener('click',event=>{const button=event.target.closest('[data-case]');if(button){selected=button.dataset.case;if(button.dataset.metric)$('#metric').value=button.dataset.metric;return render();}});
  $('#detail').addEventListener('click',event=>{if(event.target.closest('[data-close-detail]')){selected=undefined;return render();}});
  await render();
}

start().catch(error=>{$('#load-error').hidden=false;$('#load-error').textContent=error.message;$('#stats').textContent='Benchmark history is unavailable. Rebuild the site after checking the campaign files.';});
