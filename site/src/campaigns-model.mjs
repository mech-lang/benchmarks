export const metrics = {
  source_to_executable_seconds: {label:'Source → executable',unit:'seconds',note:'Complete source compiler worker, dependency resolution, generated support build and final link. The separate qualification build warms support dependencies; each measured fork generates a new project.'},
  native_process_seconds: {label:'Native process lifecycle',unit:'seconds',note:'Complete fresh-process startup, metadata admission, checked scalar invocation, output and shutdown. Mean across the declared input schedule within each independent build fork.'},
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
  if(unit==='seconds') {
    if(value<1e-6)return `${(value*1e9).toFixed(1)} ns`;
    if(value<1e-3)return `${(value*1e6).toFixed(2)} µs`;
    if(value<1)return `${(value*1e3).toFixed(2)} ms`;
    return `${value.toFixed(3)} s`;
  }
  if(unit==='bytes') {
    if(value>=1024**2)return `${(value/1024**2).toFixed(2)} MiB`;
    if(value>=1024)return `${(value/1024).toFixed(2)} KiB`;
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
  return {status:'informational',percent,ratio:b/a,label:`${percent>0?'+':''}${percent.toFixed(1)}%`,reason:'Median change; informational. Separate campaigns are independent samples.'};
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
