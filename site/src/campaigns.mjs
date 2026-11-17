import {metrics,formatMetric,recordFor,compareRecords,stageFor,filteredCases,compatibleHistory} from './campaigns-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const pathURL=value=>String(value).split('/').map(encodeURIComponent).join('/');
const short=value=>String(value??'unknown').slice(0,10);
const nice=value=>String(value??'unknown').replaceAll('_',' ');
let bundle,selected;
const parameters=new URLSearchParams(location.search);

function campaign() {return bundle.campaigns.find(c=>c.id===$('#campaign').value);}
function baseline() {return bundle.campaigns.find(c=>c.id===$('#baseline').value);}
function baselineRecord(id,backend) {return $('#baseline').value==='$paired'?recordFor(campaign(),id,backend,'baseline'):recordFor(baseline(),id,backend);}
function option(value,label){return `<option value="${escape(value)}">${escape(label)}</option>`;}
function badge(value,extra=''){return `<span class="badge ${escape(extra)}">${escape(nice(value))}</span>`;}
function rawLink(campaign,record,suffix='campaign.json') {
  return new URL(`${pathURL(campaign.evidence_path)}/${record?pathURL(record)+'/':''}${pathURL(suffix)}`,import.meta.url).href;
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
    </svg><p class="caption">${points.length===1?'First compatible campaign. Subsequent runs will build this history.':`${points.length} compatible campaigns · medians shown · lower is better.`}</p>`;
}

function renderDetail() {
  const definition=bundle.catalog.cases.find(c=>c.id===selected);
  if(!definition)return;
  const current=campaign(),metric=$('#metric').value,backend=$('#backend').value;
  const record=recordFor(current,selected,backend);
  let html=`<p class="eyebrow">${escape(definition.family)}</p><h2 id="detail-title">${escape(definition.title)}</h2>
    <div class="badges">${badge(stageFor(definition,record))}${record?badge(record.outcome,record.outcome):''}</div>`;
  if(!record) {
    html+=`<p class="detail-note">${escape(definition.notes??'This case has an implementation. Run a campaign to qualify this backend and record measurements.')}</p>`;
    if(definition.historical_contract)html+=`<p><a href="https://github.com/mech-lang/benchmarks/blob/main/${pathURL(definition.historical_contract)}">Preserved application contract ↗</a></p>`;
  } else {
    const summary=record.summary?.[metric],comparison=compareRecords(baselineRecord(selected,backend),record,metric);
    const screening=current.comparisons?.find(result=>result.case_id===selected&&result.backend===backend);
    html+=`<div class="measurement"><strong>${escape(formatMetric(summary?.median,metric))}</strong><span>${escape(metrics[metric].label)} · ${record.samples.length} independent ${record.samples.length===1?'fork':'forks'}</span></div>
      ${record.reason?`<p class="failure">${escape(record.reason)}</p>`:''}
      <p class="detail-note">Capability: ${escape(nice(record.capability))}. ${comparison.status==='informational'?escape(`${comparison.label} relative to the selected baseline. ${comparison.reason}`):comparison.status==='incompatible'?escape(`Comparison unavailable: ${comparison.reason}.`):'Select a compatible baseline campaign to compare.'}</p>
      ${$('#baseline').value==='$paired'&&screening?`<p class="detail-note">Paired turn screening: ${escape(nice(screening.status))}. ${escape(screening.reason??'')}${screening.interval_95?` 95% interval: ${screening.interval_95.map(n=>n.toFixed(3)).join('–')}×.`:''}</p>`:''}
      <h3>Over time</h3>${trend(compatibleHistory(bundle.campaigns,record,metric),metric)}
      <details open><summary>Raw fork observations</summary>${summary?`<div class="sample-list">${record.samples.map(sample=>`<a href="${rawLink(current,sample.raw,'supervised.json')}" target="_blank" rel="noopener"><span>Fork ${sample.fork+1}</span><span>${escape(formatMetric(sample.metrics[metric],metric))}</span></a>`).join('')}</div>`:'<p>No accepted timings. Failed and partial observations remain in the campaign evidence.</p>'}</details>
      <details><summary>Task and measurement contracts</summary><p>Output: <code>${escape(record.task.outputs.join(', '))}</code></p><p>${escape(record.measurement.boundary)}</p><dl>${Object.entries(record.measurement).filter(([key])=>key!=='schedule').map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(typeof value==='string'?value:JSON.stringify(value))}</dd>`).join('')}</dl><p>Deterministic input schedule</p><pre>${escape(JSON.stringify(record.measurement.schedule))}</pre><p>${escape(record.task.arithmetic)}</p><p>Task <code>${escape(short(record.task_hash))}</code> · measurement <code>${escape(short(record.measurement_hash))}</code></p></details>
      <details><summary>Correctness and negative control</summary><p>${escape(record.verification.reason??(backend==='native'?'Every complete fresh-process output matched the independent oracle. Each scheduled input starts a new process.':'The complete declared input trajectory matched the independent Python oracle. Previously published outputs stayed unchanged before execution.'))}</p>${record.verification.output_count?`<p>${record.verification.output_count} outputs verified. Preview shows the first and last observations; the raw record includes the full trajectory.</p>`:''}<a href="${rawLink(current,record.verification.raw,'supervised.json')}" target="_blank" rel="noopener">Inspect verification observations ↗</a><pre>${escape(JSON.stringify(record.verification.preview_outputs??record.verification.outputs,null,2))}</pre></details>
      <details><summary>Mech source</summary><p>SHA-256 <code>${escape(record.source_sha256)}</code></p><pre class="source"><code>${escape(record.source)}</code></pre></details>
      <details><summary>All measured outcomes</summary><dl>${Object.entries(record.summary??{}).map(([key,value])=>`<dt>${escape(nice(key))}</dt><dd>${escape(metrics[key]?formatMetric(value.median,key):value.median.toLocaleString(undefined,{maximumFractionDigits:6}))}</dd>`).join('')}</dl></details>
      <details><summary>Compiler and environment</summary><dl><dt>Revision</dt><dd><code>${escape(record.revision)}</code></dd><dt>Binary hash</dt><dd><code>${escape(current.workers[record.lane].binary_sha256)}</code></dd><dt>Adapter hash</dt><dd><code>${escape(current.workers[record.lane].adapter_sha256)}</code></dd><dt>Toolchain</dt><dd><pre>${escape(current.workers[record.lane].rustc)}</pre></dd><dt>Machine</dt><dd>${escape(current.environment.cpu)} · ${escape(current.environment.system)} ${escape(current.environment.release)}</dd></dl></details>
      <p class="downloads"><a href="${rawLink(current,null)}" download>Campaign JSON ↓</a>${current.raw_archive?`<a href="${rawLink(current,null,current.raw_archive)}" download>Raw evidence archive ↓</a>`:''}<a href="${rawLink(current,null,'report.md')}" target="_blank" rel="noopener">Full report ↗</a></p>`;
  }
  if(definition.compiler_tests?.length)html+=`<details><summary>Existing compiler test coverage</summary><ul>${definition.compiler_tests.map(test=>`<li><a href="https://github.com/${pathURL(test.repository)}/blob/${bundle.catalog.candidate_revision}/${pathURL(test.path)}" target="_blank" rel="noopener">${escape(test.path)}</a></li>`).join('')}</ul></details>`;
  $('#detail').innerHTML=html;
}

function render() {
  const current=campaign(),metric=$('#metric').value,backend=$('#backend').value;
  const cases=bundle.catalog.cases;
  const records=cases.map(c=>recordFor(current,c.id,backend)).filter(Boolean);
  const measured=records.filter(r=>r.progress==='measured'&&r.outcome==='ok').length;
  const failed=records.filter(r=>r.outcome!=='ok').length;
  const planned=cases.filter(c=>c.progress==='planned').length;
  $('#stats').innerHTML=[['Measured tasks',measured],['Families',new Set(cases.map(c=>c.family)).size],['Planned tasks',planned],['Need attention',failed]].map(([label,value])=>`<div><strong>${value}</strong><span>${label}</span></div>`).join('');
  $('#boundary').textContent=metrics[metric].note;
  $('#metric-heading').textContent=metrics[metric].label;
  const visible=filteredCases(cases,current,{query:$('#search').value,family:$('#family').value,progress:$('#progress').value,backend});
  $('#case-count').textContent=`${visible.length} / ${cases.length} tasks`;
  $('#empty').hidden=visible.length>0;
  if(!visible.some(c=>c.id===selected))selected=visible[0]?.id;
  $('#cases').innerHTML=visible.map(definition=>{
    const record=recordFor(current,definition.id,backend),stage=stageFor(definition,record);
    const change=compareRecords(baselineRecord(definition.id,backend),record,metric);
    return `<tr class="${definition.id===selected?'selected':''}"><td><button data-case="${escape(definition.id)}" aria-pressed="${definition.id===selected}">${escape(definition.title)}</button><span class="family">${escape(definition.family)}</span></td><td>${badge(stage)}${record&&record.outcome!=='ok'?badge(record.outcome,'failure'):''}</td><td class="number">${escape(formatMetric(record?.summary?.[metric]?.median,metric))}</td><td class="number change ${change.percent<0?'faster':''}" title="${escape(change.reason??'')}">${escape(change.label)}</td></tr>`;
  }).join('');
  if(selected)renderDetail();else $('#detail').innerHTML='<p class="empty">Select another filter to inspect a task.</p>';
  const query=new URLSearchParams();
  for(const [key,value] of [['campaign',$('#campaign').value],['baseline',$('#baseline').value],['metric',metric],['backend',backend],['case',selected]])if(value)query.set(key,value);
  history.replaceState(null,'',`${location.pathname}?${query}`);
}

async function start() {
  const dataURL=new URL('./campaigns.json',import.meta.url);
  dataURL.search=new URL(import.meta.url).search;
  const response=await fetch(dataURL);
  if(!response.ok)throw new Error(`Could not load campaign data (${response.status})`);
  bundle=await response.json();
  if(bundle.schema!=='mech.benchmark-dashboard.v1')throw new Error('Unsupported dashboard data');
  const choices=[...bundle.campaigns].reverse();
  $('#campaign').innerHTML=choices.length?choices.map(c=>option(c.id,`${c.id} · ${short(c.workers.candidate.revision)}`)).join(''):option('','No campaigns yet');
  $('#baseline').innerHTML=option('','No comparison')+option('$paired','Paired baseline worker')+choices.map(c=>option(c.id,c.id)).join('');
  $('#metric').innerHTML=Object.entries(metrics).map(([key,meta])=>option(key,meta.label)).join('');
  $('#family').innerHTML+=Array.from(new Set(bundle.catalog.cases.map(c=>c.family))).sort().map(f=>option(f,nice(f))).join('');
  if(!parameters.has('campaign')){
    const resident=choices.find(c=>c.results.some(r=>r.backend==='source'&&r.lane==='candidate'));
    if(resident)$('#campaign').value=resident.id;
  }
  for(const selector of ['campaign','baseline','metric','backend'])if(parameters.has(selector)&&[...$(`#${selector}`).options].some(o=>o.value===parameters.get(selector)))$(`#${selector}`).value=parameters.get(selector);
  if(!parameters.has('backend')&&campaign()?.results.length)$('#backend').value=campaign().results[0].backend;
  if(!parameters.has('metric'))$('#metric').value=$('#backend').value==='native'?'source_to_executable_seconds':'resident_turn_seconds';
  if(!parameters.has('baseline')&&campaign()?.workers.baseline)$('#baseline').value='$paired';
  selected=parameters.get('case')??campaign()?.results.find(r=>r.backend===$('#backend').value)?.case_id??bundle.catalog.cases[0]?.id;
  for(const selector of ['#campaign','#baseline','#metric','#backend','#family','#progress'])$(selector).addEventListener('change',()=>{
    if(selector==='#backend'&&!campaign()?.results.some(r=>r.backend===$('#backend').value)){
      const matching=choices.find(c=>c.results.some(r=>r.backend===$('#backend').value));
      if(matching)$('#campaign').value=matching.id;
    }
    if(selector==='#campaign'&&campaign()?.results.length&&!campaign().results.some(r=>r.backend===$('#backend').value))$('#backend').value=campaign().results[0].backend;
    if(['#campaign','#backend'].includes(selector)){
      $('#metric').value=$('#backend').value==='native'?'source_to_executable_seconds':'resident_turn_seconds';
      selected=campaign()?.results.find(r=>r.backend===$('#backend').value)?.case_id??selected;
      if(!campaign()?.workers.baseline&&$('#baseline').value==='$paired')$('#baseline').value='';
    }
    render();
  });
  $('#search').addEventListener('input',render);
  $('#cases').addEventListener('click',event=>{const button=event.target.closest('[data-case]');if(button){selected=button.dataset.case;render();}});
  render();
}

start().catch(error=>{$('#load-error').hidden=false;$('#load-error').textContent=error.message;$('#stats').textContent='Benchmark history is unavailable. Rebuild the site after checking the campaign files.';});
