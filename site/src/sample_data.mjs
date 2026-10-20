// One row per recorded observation. Only explicit timing aliases share rows;
// equal times or identical source files never imply shared measurements.
export function sourceSizeFields(program){
  const metrics=program.source_metrics;
  const logical=program.logical_source_units;
  return {normalized_loc_rule:metrics?.retained_application_loc?.metric??program.loc_metric??'unspecified-legacy',
    normalized_loc_status:metrics?.retained_application_loc?.status??'retained-not-uniformly-recertified',
    formatted_loc_status:metrics?.canonical_formatted_loc?.status??program.formatted_loc_status??'unavailable',
    qualified_logical_units:logical?.status==='qualified'&&Number.isSafeInteger(logical.application)&&logical.application>0?logical.application:null,
    logical_units_status:logical?.status??'unavailable',logical_units_policy:logical?.policy??null,
    ...Object.fromEntries(['application','submitted','excluded_support'].flatMap(scope=>
      ['utf8_bytes','gzip_bytes','cl100k_base_tokens'].map(metric=>[scope+'_'+metric,metrics?.[scope]?.[metric]??null])))};
}

export function sampleRows(data,catalog={...data.program_inventory,...data.programs}){
  const languages=new Map(data.languages.map(l=>[l.key,l])),benchmarks=new Map(data.benchmarks.map(b=>[b.key,b]));
  const aliases=new Map();
  for(const p of Object.values(catalog))if(p.timing_alias_of){
    if(!aliases.has(p.timing_alias_of))aliases.set(p.timing_alias_of,[]);
    aliases.get(p.timing_alias_of).push(p);
  }
  return Object.values(catalog).filter(p=>!p.timing_alias_of).flatMap(p=>{
    const l=languages.get(p.language),b=benchmarks.get(p.benchmark),related=aliases.get(p.key)??[];
    const execution=p.execution_mode??p.measured_backend?.execution??'unknown';
    const runtime=p.measured_backend?.label??p.runtime_policy??l.runtime??'';
    const implementations=[p,...related];
    const authorship=p.authorship?.label??'Unverified';
    const ai=p.authorship?.ai,ai_model=ai?.status==='not-applicable'?'—':
      ai?.models?.length?ai.models.join(', ')+(ai.status==='partial-source-writes'?' (partial)':''):ai?.model_family?`${ai.model_family} family · exact version unverified`:'Model unverified';
    const terms=p.authorship?.license;
    const license=[...new Set(terms?.licenses?.map(l=>l.id)??[])].join(' + ')+(terms?.status==='partial'?' (partial)':'')||'Unverified';
    const reproduction=data.reproducibility?.[p.key]??null;
    const original_sources=(p.authorship?.sources??[]).filter(s=>['implementation','reference implementation'].includes(s.relationship));
    if(!original_sources.length)original_sources.push(...(p.authorship?.parent_sources??[]));
    const original_source=original_sources.map(s=>s.url).join(' · ')||(p.authorship?.origin_status==='suite-authored'?'Suite authored':'Not established');
    const toolchain_version=reproduction?.version_label??'Not recorded';
    const platform=reproduction?.host?.hardware;
    const platform_label=typeof platform==='string'?platform:platform?JSON.stringify(platform):'Not recorded';
    const recorded_at=reproduction?.recorded_at??null;
    const reproduction_status=reproduction?.status==='recorded-recipe'?'Recorded recipe':`Gaps (${reproduction?.missing?.length??1})`;
    const common={program:p.key,implementation:p.id,language:p.language,language_label:l.label,
      benchmark:p.benchmark,benchmark_label:b.title,workload:b.workload,
      loc:p.loc,formatted_loc:p.formatted_loc_complete===true?p.formatted_loc:null,
      ...sourceSizeFields(p),source_metrics:p.source_metrics??null,source_metric_definitions:data.source_metrics??null,
      logical_source_units:p.logical_source_units??null,logical_source_definitions:data.logical_source_units??null,
      median_seconds:p.seconds,sd_seconds:p.timing_sd??null,execution,runtime,authorship,ai_model,license,
      original_source,original_sources,toolchain_version,platform_label,recorded_at,reproduction,reproduction_status,
      eligible:p.eligible_for_chart!==false,report:p.report??'',implementations,
      search:[l.label,l.family,b.title,b.key,b.workload,execution,runtime,authorship,ai_model,license,original_source,toolchain_version,platform_label,recorded_at,reproduction_status,
        ...(p.authorship?.sources??[]).map(r=>r.label),...(p.authorship?.attribution_notices??[]).map(n=>n.text),
        ...implementations.map(p=>p.id)].join(' ').toLocaleLowerCase('en')};
    return p.samples.map((seconds,i)=>({...common,id:p.key+'#'+(i+1),run:i+1,seconds,
      time_x_best:p.seconds!=null&&common.eligible?seconds/b.baseline_seconds:null,
      details:p.sample_details?.[i]??null}));
  });
}

export function filterSamples(rows,{languages,benchmarks,disabled=new Set(),query=''}={}){
  const terms=query.toLocaleLowerCase('en').trim().split(/\s+/).filter(Boolean);
  return rows.filter(r=>(!languages||languages.has(r.language))&&(!benchmarks||benchmarks.has(r.benchmark))&&
    r.implementations.some(p=>!disabled.has(p.key))&&terms.every(term=>r.search.includes(term)));
}

export const sampleColumns=[['language_label','Language'],['benchmark_label','Benchmark'],['implementation','Implementation'],
  ['run','Run'],['seconds','Seconds'],['time_x_best','Time × best'],['loc','Normalized app LOC (retained)'],
  ['normalized_loc_rule','Retained count rule'],['formatted_loc','Qualified formatted app LOC'],
  ['qualified_logical_units','Qualified logical units · partial'],['logical_units_policy','Logical owner policy'],
  ['application_utf8_bytes','App UTF-8 bytes'],['application_gzip_bytes','App gzip bytes'],['application_cl100k_base_tokens','App BPE tokens (cl100k_base)'],
  ['submitted_utf8_bytes','Submitted UTF-8 bytes'],['submitted_gzip_bytes','Submitted gzip bytes'],['submitted_cl100k_base_tokens','Submitted BPE tokens (cl100k_base)'],
  ['median_seconds','Median (s)'],['sd_seconds','SD (s)'],['execution','Execution'],['runtime','Runtime / toolchain'],
  ['authorship','Authorship'],['ai_model','AI model'],['license','License'],['original_source','Original source'],
  ['toolchain_version','Versions'],['workload','Input'],['platform_label','Platform'],['recorded_at','Recorded'],['reproduction_status','Reproduce']];

const collator=new Intl.Collator('en',{numeric:true,sensitivity:'base'});
export function sortSamples(rows,{key='language_label',direction=1}={}){
  return rows.slice().sort((a,b)=>{
    const x=a[key],y=b[key];
    if(x==null||y==null){if(x!==y)return x==null?1:-1;}
    else{const order=typeof x==='string'?collator.compare(x,y):x-y;if(order)return direction*order;}
    return collator.compare(a.language_label,b.language_label)||collator.compare(a.benchmark_label,b.benchmark_label)||
      collator.compare(a.implementation,b.implementation)||a.run-b.run;
  });
}

export function exportRows(rows,linkFor){
  return rows.map(r=>({sample_id:r.id,language:r.language_label,language_key:r.language,
    benchmark:r.benchmark_label,benchmark_key:r.benchmark,workload:r.workload,
    implementation:r.implementation,program_key:r.program,run:r.run,seconds:r.seconds,
    time_x_best:r.time_x_best,canonical_loc:r.loc,normalized_application_loc:r.loc,
    normalized_loc_rule:r.normalized_loc_rule,normalized_loc_status:r.normalized_loc_status,
    formatted_loc:r.formatted_loc,qualified_formatted_loc:r.formatted_loc,formatted_loc_status:r.formatted_loc_status,
    qualified_logical_units:r.qualified_logical_units,logical_units_status:r.logical_units_status,
    logical_units_policy:r.logical_units_policy,logical_source_units:r.logical_source_units,
    logical_source_definitions:r.logical_source_definitions,
    ...Object.fromEntries(['application','submitted','excluded_support'].flatMap(scope=>
      ['utf8_bytes','gzip_bytes','cl100k_base_tokens'].map(metric=>[scope+'_'+metric,r[scope+'_'+metric]]))),
    source_metrics:r.source_metrics,source_metric_definitions:r.source_metric_definitions,
    source_accounting:r.implementations[0].source_accounting??null,
    median_seconds:r.median_seconds,sd_seconds:r.sd_seconds,execution:r.execution,runtime:r.runtime,
    authorship:r.authorship,ai_model:r.ai_model,license:r.license,license_status:r.implementations[0].authorship?.license?.status??'unverified',
    authorship_details:r.implementations[0].authorship??null,
    original_sources:r.original_sources,toolchain_version:r.toolchain_version,platform:r.platform_label,
    recorded_at:r.recorded_at,reproduction_status:r.reproduction_status,reproduction:r.reproduction,
    chart_eligible:r.eligible,implementation_url:linkFor(r.implementations[0]),
    timing_aliases:r.implementations.slice(1).map(p=>({program_key:p.key,implementation:p.id,url:linkFor(p),authorship:p.authorship??null,source_metrics:p.source_metrics??null,logical_source_units:p.logical_source_units??null})),
    source_sha256:r.implementations[0].files,report:r.report,sample_details:r.details}));
}

const exportColumns=['sample_id','language','language_key','benchmark','benchmark_key','workload','implementation','program_key',
  'run','seconds','time_x_best','canonical_loc','normalized_application_loc','normalized_loc_rule','normalized_loc_status',
  'formatted_loc','qualified_formatted_loc','formatted_loc_status',
  'qualified_logical_units','logical_units_status','logical_units_policy','logical_source_units','logical_source_definitions',
  ...['application','submitted','excluded_support'].flatMap(scope=>['utf8_bytes','gzip_bytes','cl100k_base_tokens'].map(metric=>scope+'_'+metric)),
  'source_metrics','source_metric_definitions','source_accounting','median_seconds','sd_seconds','execution','runtime',
  'authorship','ai_model','license','license_status','authorship_details','original_sources','toolchain_version','platform',
  'recorded_at','reproduction_status','reproduction','chart_eligible','implementation_url','timing_aliases','source_sha256','report','sample_details'];
export function samplesCSV(rows){
  const cell=value=>{
    if(value==null)return '';
    let text=typeof value==='object'?JSON.stringify(value):String(value);
    // Spreadsheet imports must treat catalog strings as text, not formulas.
    if(typeof value==='string'&&/^[\s]*[=+@-]/.test(text))text="'"+text;
    return '"'+text.replaceAll('"','""')+'"';
  };
  return [exportColumns.join(','),...rows.map(row=>exportColumns.map(key=>cell(row[key])).join(','))].join('\r\n')+'\r\n';
}
