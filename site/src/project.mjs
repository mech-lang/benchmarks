import {inventoryMetrics,number,bytes,latestByTrack,historyFor,jobSeconds,jobTotals,previousSnapshot} from './project-model.mjs';

const $=selector=>document.querySelector(selector);
const escape=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const option=(value,label)=>`<option value="${escape(value)}">${escape(label)}</option>`;
const date=value=>value?new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}):'Unavailable';
const parameters=new URLSearchParams(location.search);
let snapshots=[];
const current=()=>snapshots.find(s=>s.id===$('#snapshot').value);
const sourceURL=s=>`https://github.com/${s.repository.split('/').map(encodeURIComponent).join('/')}/tree/${encodeURIComponent(s.revision)}`;
const evidenceURL=(s,file)=>new URL(`${s.evidence_path}/${file}`,import.meta.url).href;
const githubURL=value=>{try{const url=new URL(value);return url.protocol==='https:'&&url.hostname==='github.com'?url.href:'#';}catch{return '#';}};
function chooseSnapshots(id){const rows=snapshots.filter(s=>s.track===$('#track').value).sort((a,b)=>b.captured_at.localeCompare(a.captured_at));$('#snapshot').innerHTML=rows.map(s=>option(s.id,`${date(s.captured_at)} · ${s.revision.slice(0,10)}`)).join('');if(rows.some(s=>s.id===id))$('#snapshot').value=id;}

function renderHistory(snapshot){
  const metric=$('#history-metric').value,rows=historyFor(snapshots,snapshot,metric);
  $('#history-count').textContent=`${rows.length} ${rows.length===1?'snapshot':'snapshots'}`;
  const value=snapshot.summary[metric],formatted=metric==='bytes'?bytes(value):number(value);
  if(rows.length<2){$('#project-history').innerHTML=`<div class="no-history"><strong class="inventory-number">${formatted}</strong><span class="inventory-label">${escape(inventoryMetrics[metric])}</span></div><p>First snapshot for this project track. Future collections will build its history.</p>`;return;}
  const values=rows.map(s=>s.summary[metric]),min=Math.min(...values),max=Math.max(...values),span=max-min||Math.max(max*.1,1);
  const x=i=>45+i/(rows.length-1)*460,y=v=>145-(v-min)/span*100;
  $('#project-history').innerHTML=`<svg class="project-trend" viewBox="0 0 550 190" role="img" aria-label="${escape(inventoryMetrics[metric])} across dated snapshots"><line class="axis" x1="45" x2="510" y1="150" y2="150"/><polyline points="${rows.map((s,i)=>`${x(i)},${y(s.summary[metric])}`).join(' ')}"/>${rows.map((s,i)=>`<circle cx="${x(i)}" cy="${y(s.summary[metric])}" r="3"><title>${escape(date(s.captured_at))}: ${number(s.summary[metric])}</title></circle>`).join('')}<text x="45" y="25">${number(max)}</text><text x="45" y="180">${escape(new Date(rows[0].captured_at).toLocaleDateString())}</text><text x="510" y="180" text-anchor="end">${escape(new Date(rows.at(-1).captured_at).toLocaleDateString())}</text></svg><p>Same track and inventory policy. Measurements are dated by collection time.</p>`;
}

function render(){
  const s=current();if(!s)return;
  const summary=s.summary,dependencies=s.dependencies,github=s.github,ci=github?.ci,totals=jobTotals(ci),prior=previousSnapshot(snapshots,s);
  $('#revision').innerHTML=`${escape(s.label)} · <a href="${sourceURL(s)}" target="_blank" rel="noopener">${s.revision.slice(0,12)}</a> · collected ${escape(date(s.captured_at))} · commit dated ${escape(date(s.committed_at))}`;
  $('#project-stats').innerHTML=[[number(summary.physical_lines),'Physical source lines','Comments and blanks included'],[number(summary.rust_test_files),'Rust test files','Static file inventory'],[number(dependencies.package_count),'Cargo packages','First-party manifests'],[number(dependencies.resolved_external_count),'Locked external packages','Recorded root Cargo.lock']].map(([value,label,note])=>`<div><strong>${value}</strong><span>${label}</span><small>${note}</small></div>`).join('');
  renderHistory(s);
  const latestRun=ci?.runs.find(r=>r.id===ci.latest_completed_run);
  $('#delivery').innerHTML=`<div class="facts"><div class="fact"><strong>${number(summary.rust_test_files)}</strong><span>Rust test files</span></div><div class="fact"><strong>${number(summary.mech_test_files)}</strong><span>Mech test / fixture files</span></div><div class="fact"><strong>${ci?.jobs.length?number(totals.success):'—'}</strong><span>Successful CI jobs${ci&&!ci.jobs_complete?' (partial listing)':''}</span></div><div class="fact"><strong>—</strong><span>Line coverage · no retained report</span></div></div>${latestRun?`<p>Job counts refer to <a href="${githubURL(latestRun.html_url)}" target="_blank" rel="noopener">${escape(latestRun.name)}</a>. ${number(totals.failure)} failed · ${number(totals.skipped)} skipped · ${number(totals.cancelled)} cancelled · ${number(totals.pending)} unfinished.</p>`:'<p>No completed workflow observation was retained for this revision.</p>'}<p>File counts describe the test inventory. Actual executed test counts need an execution report.</p>`;
  $('#languages').innerHTML=Object.entries(summary.languages).sort((a,b)=>b[1].physical_lines-a[1].physical_lines).map(([name,r])=>`<tr><td>${escape(name)}</td><td>${number(r.files)}</td><td>${number(r.physical_lines)}</td><td>${bytes(r.bytes)}</td></tr>`).join('');
  const components=Object.entries(summary.components).sort((a,b)=>b[1].physical_lines-a[1].physical_lines).slice(0,8),largest=components[0]?.[1].physical_lines||1;
  $('#components').innerHTML=components.map(([name,r])=>`<div class="component"><div class="component-label"><code>${escape(name)}</code><span>${number(r.physical_lines)} lines</span></div><div class="component-bar"><span style="width:${(r.physical_lines/largest*100).toFixed(2)}%"></span></div></div>`).join('');
  $('#ci-runs').innerHTML=ci?.runs.length?ci.runs.map(run=>`<tr><td><a href="${githubURL(run.html_url)}" target="_blank" rel="noopener">${escape(run.name)}</a></td><td class="outcome-${escape(run.conclusion??'pending')}">${escape(run.conclusion??run.status)}</td><td>${escape(run.event)}</td><td>${escape(date(run.created_at))}</td></tr>`).join(''):'<tr><td colspan="4">No workflow observations for this revision.</td></tr>';
  $('#ci-count').textContent=ci?`${ci.runs.length} recorded${ci.runs_complete?'':' · latest 20'}`:'Not collected';
  $('#ci-note').textContent=ci?.note??'GitHub evidence was not collected for this snapshot.';
  const durations=(ci?.jobs??[]).map(j=>({...j,seconds:jobSeconds(j)})).filter(j=>j.seconds!==null).sort((a,b)=>b.seconds-a.seconds).slice(0,5);
  if(durations.length)$('#ci-note').innerHTML+=`<details><summary>Longest jobs in the retained workflow</summary><ul>${durations.map(j=>`<li><a href="${githubURL(j.html_url)}">${escape(j.name)}</a> · ${(j.seconds/60).toFixed(1)} min</li>`).join('')}</ul><p>Wall time for each CI job, including its setup and validation. This is not a compiler-only build measurement.</p></details>`;
  $('#dependencies').innerHTML=`<div class="facts"><div class="fact"><strong>${number(dependencies.declared_external_count)}</strong><span>Declared registry / Git dependency names</span></div><div class="fact"><strong>${number(dependencies.multiple_version_names?.length)}</strong><span>Names with multiple locked resolutions</span></div></div><p>Declarations include optional, development, build and target-specific dependencies. The active dependency graph varies with the build profile.</p><details><summary>Inspect declared dependency names</summary><p class="dependency-names">${dependencies.declared_external_names.map(escape).join(' · ')}</p></details>`;
  $('#activity').innerHTML=github?`<div class="facts">${[['stars','Stars'],['forks','Forks'],['open_items','Open issues + pull requests']].map(([key,label])=>`<div class="fact"><strong>${number(github.repository[key])}</strong><span>${label}</span></div>`).join('')}</div><p>Observed ${escape(date(github.observed_at))}. Repository activity is observed now, independently of the selected source commit.</p><p>Default branch: <code>${escape(github.repository.default_branch)}</code></p>`:'<p>No GitHub repository observation was collected.</p>';
  $('#project-downloads').innerHTML=`<a href="${evidenceURL(s,'snapshot.json')}" download>Full source inventory JSON ↓</a><a href="${evidenceURL(s,'github.json.gz')}" download>GitHub evidence ↓</a><a href="${sourceURL(s)}" target="_blank" rel="noopener">Exact source revision ↗</a>${prior?`<span>${number(summary.physical_lines-prior.summary.physical_lines)} physical lines since the previous snapshot on this track.</span>`:''}`;
  history.replaceState(null,'',`${location.pathname}?${new URLSearchParams({track:s.track,snapshot:s.id,metric:$('#history-metric').value})}`);
}

async function start(){
  const url=new URL('./project.json',import.meta.url);url.search=new URL(import.meta.url).search;
  const response=await fetch(url);if(!response.ok)throw new Error(`Could not load project snapshots (${response.status})`);
  const bundle=await response.json();if(bundle.schema!=='mech.project-dashboard.v1')throw new Error('Unsupported project data');snapshots=bundle.snapshots;
  if(!snapshots.length){$('#revision').textContent='No project snapshots yet. Run tools/project_metrics.py, then rebuild the site.';return;}
  const tracks=latestByTrack(snapshots);$('#track').innerHTML=tracks.map(s=>option(s.track,s.label)).join('');
  const requested=snapshots.find(s=>s.id===parameters.get('snapshot'));
  const track=requested?.track??parameters.get('track')??'compiler-candidate';if(tracks.some(s=>s.track===track))$('#track').value=track;
  chooseSnapshots(requested?.id);$('#history-metric').innerHTML=Object.entries(inventoryMetrics).map(([key,label])=>option(key,label)).join('');
  if(Object.hasOwn(inventoryMetrics,parameters.get('metric')))$('#history-metric').value=parameters.get('metric');
  $('#track').addEventListener('change',()=>{chooseSnapshots();render();});$('#snapshot').addEventListener('change',render);$('#history-metric').addEventListener('change',render);render();
}
start().catch(error=>{$('#load-error').hidden=false;$('#load-error').textContent=error.message;$('#revision').textContent='Project metrics are unavailable.';});
