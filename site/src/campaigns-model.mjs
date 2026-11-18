export const backendLabels = {
  source:'Source artifact', bytecode:'Decoded bytecode', native:'Linked scalar application', jit:'Checked scalar JIT',
  'source-native':'K-nucleotide application', 'fused-native':'Numerical application',
  'program-jit':'Checked program JIT · source', 'program-jit-bytecode':'Checked program JIT · decoded',
  'program-linked':'Linked program qualification', 'process-workers':'Worker scaling',
  'related-managed':'Related posts · managed', 'related-compact':'Related posts · compact',
};
export function primaryMetric(campaign,backend) {
  return campaign?.results.find(r=>r.backend===backend&&r.lane==='candidate')?.measurement?.primary_metric ?? (backend==='native'?'source_to_executable_seconds':'resident_turn_seconds');
}
export function implementationFor(campaign,record) {
  if(record.implementation)return record.implementation;
  if(record.backend==='jvm')return {binary_sha256:campaign.java?.runtime_binary_sha256,adapter_sha256:record.source_sha256,rustc:campaign.java?.version};
  if(campaign.controls?.[record.backend])return {...campaign.controls[record.backend],adapter_sha256:campaign.controls.wrapper_sha256,rustc:record.backend==='roc'?`Roc ${campaign.controls.roc.compiler_revision}`:'Pinned libdeflate 1.26 · C release O2; host O3'};
  if(['source-native','fused-native'].includes(record.backend)) {
    const worker=campaign.workers?.applications;
    return {...worker,...worker?.applications?.[record.backend==='source-native'?'mech-application':'mech-numerical-application']};
  }
  return campaign.workers?.[record.lane]??{};
}
export const metrics = {
  native_compression_call_seconds: {label:'Native compression call',unit:'seconds',note:'In-memory native encoder call, including private heap construction, allocation transfer and physical cleanup. Process startup, compilation and external validation are excluded.'},
  rust_call_seconds: {label:'Rust checked task call',unit:'seconds',controlOnly:true,note:'Independent AOT Rust implementation, including typed input validation and owned publication. Mech runtime admission and accounting remain specific to Mech.'},
  output_bytes: {label:'Compressed output size',unit:'bytes',note:'Complete owned prefix plus raw DEFLATE stream. The level-12 reference is libdeflate. Historical zlib-rs level-9 observations are separate codec results. Smaller is better.'},
  post_json_seconds: {label:'Complete post-JSON work',unit:'seconds',note:'Related Post Gen: input admission, preparation, allocations, fresh worker creation/run/join, internal cleanup and result materialization. JSON IO and artifact restoration remain in whole-process time. The original Rust example excludes pool initialization; that advantage is preserved and disclosed.'},
  reported_processing_seconds: {label:'Rust example processing timer',unit:'seconds',note:'Unchanged related_post_gen rust_con timer. Its Rayon pool is initialized before the clock; this is retained as an explicitly asymmetric reference.'},
  jit_invocation_seconds: {label:'Checked scalar JIT call',unit:'seconds',note:'Warm checked native scalar call, including managed admission and result validation. Source compilation, native lowering and JIT preparation are separate.'},
  jit_compile_seconds: {label:'JIT preparation',unit:'seconds',note:'Checked native code generation and executable-memory preparation. The complete Deflate program is compiled once per independent fork, shared by its 12 corpus cases.'},
  native_program_call_seconds: {label:'Checked program call',unit:'seconds',note:'Complete stateless canonical native call, including activation, managed checks, publication and scratch cleanup. Input import, warmup and returned-output destruction are outside the call.'},
  control_call_seconds: {label:'Compressor control call',unit:'seconds',note:'Complete pinned libdeflate compressor call including scratch allocation and cleanup. Input loading, held aliases and output preparation are outside. Transport, allocator and ownership details differ from Mech; no automatic cross-runtime ratio is qualified.'},
  worker_group_process_seconds: {label:'Complete worker group',unit:'seconds',note:'Fixed total 196,608 accepted turns across 1, 2 or 4 independent Mech processes. Includes supervisor/process startup, compilation, activation, warmup, execution and complete teardown.'},
  accepted_turns_per_second: {label:'Accepted turns per second',unit:'rate',higherBetter:true,note:'Fixed total accepted turns divided by complete group lifecycle time. Higher is better. Worker counts are separate, explicit strong-scaling cases.'},
  source_to_executable_seconds: {label:'Source → executable',unit:'seconds',note:'Complete source compiler worker, dependency resolution, generated support build and final link. The separate qualification build warms support dependencies; each measured fork generates a new project.'},
  native_process_seconds: {label:'Whole process lifecycle',unit:'seconds',note:'Complete fresh-process startup, execution, output and shutdown. Compilation and JIT preparation are included when the selected application performs them at startup.'},
  object_text_bytes: {label:'Object code section',unit:'bytes',note:'Emitted object __text/.text section bytes, from the saved platform size report.'},
  linked_text_bytes: {label:'Linked code section',unit:'bytes',note:'Linked executable __text/.text section bytes. The generated release profile strips symbols.'},
  executable_bytes: {label:'Executable size',unit:'bytes',note:'Entire linked native executable under the generated release profile (strip=symbols).'},
  resident_turn_seconds: {label:'Resident turn',unit:'seconds',note:'Captured-input submission + managed turn + publication. Setup, output copying and destruction are separate; snapshot-retention and abort cases declare wider boundaries.'},
  initial_turn_seconds: {label:'Initial accepted turn',unit:'seconds',note:'First managed turn on the temporary warmup instance, separately timed. The main fresh-instance block also includes its own first accepted turn; its mean is not a pure unchanged-turn latency.'},
  source_to_artifact_seconds: {label:'Source → artifact',unit:'seconds',note:'Canonical ProgramCompiler source parsing and semantic compilation to ProgramArtifact. No native code generation or linking is implied.'},
  artifact_decode_seconds: {label:'Artifact decoding',unit:'seconds',note:'Bytecode-v1 decoding, reconstruction and validation. Execution is measured separately.'},
  activation_seconds: {label:'Resident activation',unit:'seconds',note:'Physical/memory planning, storage realization and instance creation, after process warmup.'},
  artifact_bytes: {label:'Artifact size',unit:'bytes',note:'Encoded canonical bytecode-v1 artifact. This is distinct from object code, linked text and executable size.'},
  managed_retained_bytes: {label:'Managed retained storage',unit:'bytes',note:'Live admitted Mech-owned backing after the execution block. This is an admission-account observation, not RSS or allocator fragmentation.'},
  execution_allocations: {label:'Allocations per block',unit:'count',note:'Allocator calls during the entire declared execution block. Compare only identical schedules and cycle counts.'},
  worker_process_peak_rss_bytes: {label:'Worker peak RSS',unit:'bytes',note:'Whole-worker lifetime high-water mark, including compilation and preparation. Independent Python oracles run in separate processes.'},
  owned_snapshot_seconds: {label:'Owned output snapshot',unit:'seconds',note:'One copied snapshot of the explicitly named result, outside the execution block.'},
  teardown_seconds: {label:'Teardown',unit:'seconds',note:'Destruction of the instance and retained output snapshots, outside the turn timer.'},
};

export function formatMetric(value, metric) {
  if (!Number.isFinite(value)) return '—';
  const unit=metrics[metric]?.unit;
  const fixed=(number,digits)=>number.toFixed(digits).replace(/(?:\.0+|(\.\d*?[1-9])0+)$/,'$1');
  if(unit==='seconds') {
    if(value<1e-6)return `${fixed(value*1e9,1)} ns`;
    if(value<1e-3)return `${fixed(value*1e6,2)} µs`;
    if(value<1)return `${fixed(value*1e3,2)} ms`;
    return `${fixed(value,3)} s`;
  }
  if(unit==='bytes') {
    if(value>=1024**2)return `${fixed(value/1024**2,2)} MiB`;
    if(value>=1024)return `${fixed(value/1024,2)} KiB`;
    return `${value.toLocaleString()} B`;
  }
  return value.toLocaleString(undefined,{maximumFractionDigits:2});
}

export function recordFor(campaign,id,backend,lane='candidate') {
  return campaign?.results.find(result=>result.case_id===id&&result.backend===backend&&result.lane===lane);
}

export function compareRecords(baseline,candidate,metric) {
  if(!baseline||!candidate)return {status:'unavailable',label:'—'};
  for(const field of ['task_hash','measurement_hash','source_sha256','environment_hash','backend','feature_profile']) {
    if(JSON.stringify(baseline[field])!==JSON.stringify(candidate[field]))return {status:'incompatible',label:'Different contract',reason:`${field} differs`};
  }
  const a=baseline.summary?.[metric]?.median,b=candidate.summary?.[metric]?.median;
  if(baseline.outcome!=='ok'||candidate.outcome!=='ok'||!(a>0)||!Number.isFinite(b))return {status:'unavailable',label:'—'};
  const percent=(b/a-1)*100;
  return {status:'informational',percent,ratio:b/a,label:comparisonLabel({ratio:b/a},metric),reason:'Median change; informational. Separate campaigns are independent samples.'};
}

export function stageFor(caseDefinition,record) { return record?.progress ?? caseDefinition.progress; }

export function filteredCases(cases, campaign, {query='',family='all',progress='all',backend='source'}={}) {
  return cases.filter(item=>{
    const record=recordFor(campaign,item.id,backend),stage=stageFor(item,record);
    return (family==='all'||item.family===family)&&
      (progress==='all'||(progress==='failed'?record&&record.outcome!=='ok':stage===progress))&&
      `${item.id} ${item.title} ${item.family}`.toLowerCase().includes(query.toLowerCase());
  });
}

export function compatibleHistory(campaigns,record,metric) {
  if(!record)return [];
  return campaigns.flatMap(campaign=>{
    const candidate=recordFor(campaign,record.case_id,record.backend);
    const comparison=compareRecords(record,candidate,metric);
    return comparison.status==='informational'?[{campaign:campaign.id,date:campaign.started_at,revision:candidate.revision,
      value:candidate.summary[metric].median,samples:candidate.summary[metric].samples}]:[];
  });
}

export function isMechRecord(record) {
  return record.lane==='candidate' && Object.hasOwn(backendLabels,record.backend);
}

export function rowMetric(record,selected='$primary') {
  return selected==='$primary' ? record?.measurement?.primary_metric ?? (record?.backend==='native'?'source_to_executable_seconds':'resident_turn_seconds') : selected;
}

// Prefer the declared execution path, then the newest accepted observation on
// that path. A later failed qualification never erases a successful measurement.
export function measuredRows(bundle,{campaign='$latest',backend='$auto',metric='$primary',query='',family='all',progress='all'}={}) {
  const campaigns=campaign==='$latest'?bundle.campaigns:bundle.campaigns.filter(c=>c.id===campaign);
  return bundle.catalog.cases.flatMap(definition=>{
    let entries=campaigns.flatMap(c=>c.results.filter(r=>r.case_id===definition.id&&isMechRecord(r)&&(backend==='$auto'||r.backend===backend)).map(record=>({campaign:c,record,definition})));
    if(progress==='failed')entries=entries.filter(e=>e.record.outcome!=='ok');
    else if(progress!=='all')entries=entries.filter(e=>stageFor(definition,e.record)===progress);
    if(!entries.length||!(family==='all'||definition.family===family)||!`${definition.id} ${definition.title} ${definition.family}`.toLowerCase().includes(query.toLowerCase()))return [];
    const accepted=entries.filter(e=>e.record.outcome==='ok'&&Number.isFinite(e.record.summary?.[rowMetric(e.record,metric)]?.median));
    // A requested secondary metric can be absent on an otherwise measured path.
    if(metric!=='$primary'&&!accepted.length&&progress!=='failed')return [];
    if(accepted.length)entries=accepted;
    if(backend==='$auto'){
      const order=definition.backends??[];
      const rank=e=>{const i=order.indexOf(e.record.backend);return i<0?Infinity:i;};
      const first=Math.min(...entries.map(rank));entries=entries.filter(e=>rank(e)===first);
    }
    entries.sort((a,b)=>a.campaign.started_at.localeCompare(b.campaign.started_at)||a.campaign.id.localeCompare(b.campaign.id));
    const row=entries.at(-1);row.metric=rowMetric(row.record,metric);return [row];
  });
}

export function controlFor(bundle,row) {
  const {record,campaign,metric}=row;
  if(record.case_id==='deflate'||record.case_id.startsWith('deflate-')) {
    const mapped={native_program_call_seconds:'control_call_seconds',output_bytes:'output_bytes'}[metric];
    if(!mapped)return {kind:'pending',label:'No matched reference',reason:'No reference measures the same compiler, preparation or support operation. A compressor execution time is not a compiler measurement.'};
    // These immutable source identities bind the retained wrapper's explicit
    // libdeflate_alloc_compressor(12) call and its pinned libdeflate 1.26 build.
    const references=mapped&&record.control_contract?bundle.campaigns.flatMap(origin=>origin.started_at<=campaign.started_at
      ?origin.results.filter(reference=>reference.case_id===record.case_id&&reference.backend==='libdeflate'&&reference.outcome==='ok'
        &&reference.revision==='92e6a0db9fa848d742f9eb286c92afc60f2c3dda'
        &&reference.source_sha256==='a82938cd20ecb3404f0b0e3fc7d1553706442b8b956443d8ca98ebebacecec05'
        &&reference.control_contract===record.control_contract
        &&reference.task_hash===record.task_hash&&reference.environment_hash===record.environment_hash
        &&Number.isFinite(reference.summary?.[mapped]?.median)).map(reference=>({origin,reference})):[]):[];
    references.sort((a,b)=>a.origin.started_at.localeCompare(b.origin.started_at)||a.origin.id.localeCompare(b.origin.id));
    const retained=references.at(-1);
    if(retained)return {kind:'libdeflate',label:'libdeflate · level 12',record:retained.reference,campaign:retained.origin,metric:mapped,
      reason:'Same task, environment and explicitly shared measurement contract; libdeflate 1.26 level 12.'};
    return {kind:'pending',label:'No matched libdeflate timing',
      reason:'This row reports a Mech measurement. No level-12 libdeflate timing has the same task, environment and shared measurement contract.'};
  }
  const held=bundle.control_policy?.controls?.find(c=>c.case_id===record.case_id&&c.backend===record.backend&&c.metric===metric);
  if(held){
    const origin=bundle.campaigns.find(c=>c.id===held.campaign_id);
    const reference=recordFor(origin,held.case_id,held.backend);
    // A retained control remains pinned; new source or boundary needs qualification.
    if(reference&&origin.started_at<=campaign.started_at&&compareRecords(reference,record,metric).status==='informational')return {kind:'mech',label:held.label,record:reference,campaign:origin,metric,reason:held.reason,promotion:held};
  }
  const control=campaign.results.find(r=>r.case_id===record.case_id&&r.lane==='control'&&r.backend==='rust'&&r.outcome==='ok');
  if(control){
    const mapped=control.measurement?.metric_mapping?.[metric]??metric;
    if(record.control_contract&&record.control_contract===control.control_contract&&Number.isFinite(control.summary?.[mapped]?.median))return {kind:'rust',label:control.title??'Rust',record:control,campaign,metric:mapped,reason:control.measurement?.comparison_note??'Same task and timed boundary; independent Rust implementation.'};
  }
  return {kind:'pending',label:['source_to_artifact_seconds','artifact_decode_seconds','jit_compile_seconds','source_to_executable_seconds'].includes(metric)?'No matched compiler reference':'Rust · not measured',reason:'No qualified Rust control for this task, execution boundary and run. Previous Mech revisions remain available in the history comparison.'};
}

export function controlComparison(row,control) {
  if(control.kind==='pending')return {status:'unavailable',label:'No matched comparison',reason:control.reason};
  if(control.kind==='mech'){
    if(control.record===row.record)return {status:'baseline',label:'Baseline held',reason:control.reason};
    return compareRecords(control.record,row.record,row.metric);
  }
  const a=control.record.summary[control.metric].median,b=row.record.summary?.[row.metric]?.median;
  if(!(a>=0)||!(b>=0)||!Number.isFinite(a)||!Number.isFinite(b)||row.record.outcome!=='ok')return {status:'unavailable',label:'No comparison'};
  const percent=(b/a-1)*100;
  const ratio=a===0?(b===0?1:Infinity):b/a;
  const label=comparisonLabel({ratio},row.metric);
  return {status:'informational',percent,ratio,label,reason:control.reason+' Median change; informational.'};
}

export function comparisonDirection(change,metric) {
  if(typeof change?.ratio!=='number'||!(change.ratio>=0)||Number.isNaN(change.ratio))return 'unmatched';
  if(change.ratio===1)return 'equal';
  return (change.ratio<1)!==!!metrics[metric]?.higherBetter?'faster':'slower';
}

export function comparisonLabel(change,metric) {
  if(change?.status==='baseline')return 'Fixed Mech baseline';
  const direction=comparisonDirection(change,metric);
  if(direction==='unmatched')return 'No matched comparison';
  if(direction==='equal')return '1× · equal';
  const ratio=change.ratio,unit=metrics[metric]?.unit;
  const suffix=unit==='bytes'?'size':unit==='count'?'count':unit==='rate'?'throughput':'time';
  return `${formatRatio(ratio)}× ${suffix}`;
}

export function formatRatio(ratio) {
  if(ratio===Infinity)return '∞';
  let digits=ratio<10?3:ratio<100?2:1;
  // A rounded label must never turn a non-tie into 1× or a positive value into 0×.
  if(ratio!==1&&ratio>0){
    while(digits<15&&(Number(ratio.toFixed(digits))===1||Number(ratio.toFixed(digits))===0))digits++;
    if(Number(ratio.toFixed(digits))===1)return ratio.toPrecision(17);
  }
  return ratio.toLocaleString(undefined,{maximumFractionDigits:digits});
}

export function comparisonPlot(points,{width=900,label='Mech compared with its reference',measure='time'}={}) {
  const valid=points.filter(p=>p.ratio>0&&Number.isFinite(p.ratio)).sort((a,b)=>a.ratio-b.ratio);
  if(!valid.length)return '<p class="empty">No matched comparisons in this selection.</p>';
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  width=Math.max(300,Math.round(width));
  const height=300,left=58,right=20,top=26,bottom=58;
  const logs=valid.map(p=>Math.log10(p.ratio));
  const low=Math.min(0,...logs)-.18,high=Math.max(0,...logs)+.18;
  const y=r=>top+(high-Math.log10(r))/(high-low)*(height-top-bottom);
  const x=i=>left+(valid.length===1?.5:i/(valid.length-1))*(width-left-right);
  const ticks=Array.from({length:Math.floor(high)-Math.ceil(low)+1},(_,i)=>Math.ceil(low)+i).map(e=>({e,r:10**e}));
  const tickText=r=>r>=1e6?`${(r/1e6).toLocaleString()}m`:r>=1000?`${(r/1000).toLocaleString()}k`:r<1?r.toLocaleString(undefined,{maximumFractionDigits:Math.min(12,Math.ceil(-Math.log10(r)))}):r.toLocaleString();
  return `<svg class="comparison-plot" viewBox="0 0 ${width} ${height}" role="group" aria-label="${escape(label)}">
    ${ticks.map(({r})=>`<line x1="${left}" x2="${width-right}" y1="${y(r)}" y2="${y(r)}" class="${r===1?'reference-line':'chart-grid'}"/><text x="${left-9}" y="${y(r)+4}" text-anchor="end">${tickText(r)}×</text>`).join('')}
    <text x="${left}" y="15" class="chart-axis-label">Mech / reference ${escape(measure)} · log₁₀</text>
    ${valid.map((p,i)=>`<circle data-compare="${escape(p.id)}" class="plot-point ${escape(p.direction??(p.ratio<1?'faster':p.ratio>1?'slower':'equal'))}" cx="${x(i)}" cy="${y(p.ratio)}" r="4.2" tabindex="0" role="button" aria-label="${escape(p.title)} · ${escape(p.label??p.ratio+' times reference')}"/>`).join('')}
    <text x="${left}" y="${height-30}">Lowest ratio</text><text x="${width-right}" y="${height-30}" text-anchor="end">Highest ratio</text>
    <text x="${(left+width-right)/2}" y="${height-9}" text-anchor="middle">${valid.length} cases, ordered by relative ${escape(measure)}</text>
  </svg>`;
}
