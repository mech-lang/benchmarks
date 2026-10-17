// One row per recorded observation. Only explicit timing aliases share rows;
// equal times or identical source files never imply shared measurements.
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
    const common={program:p.key,implementation:p.id,language:p.language,language_label:l.label,
      benchmark:p.benchmark,benchmark_label:b.title,workload:b.workload,
      loc:p.loc,formatted_loc:p.formatted_loc_complete===true?p.formatted_loc:null,
      median_seconds:p.seconds,sd_seconds:p.timing_sd??null,execution,runtime,
      eligible:p.eligible_for_chart!==false,report:p.report??'',implementations,
      search:[l.label,l.family,b.title,b.key,b.workload,execution,runtime,...implementations.map(p=>p.id)].join(' ').toLocaleLowerCase('en')};
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
  ['run','Run'],['seconds','Seconds'],['time_x_best','Time × best'],['loc','Canonical LOC'],['formatted_loc','Formatted LOC'],
  ['median_seconds','Median (s)'],['sd_seconds','SD (s)'],['execution','Execution'],['runtime','Runtime / toolchain']];

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
    time_x_best:r.time_x_best,canonical_loc:r.loc,formatted_loc:r.formatted_loc,
    median_seconds:r.median_seconds,sd_seconds:r.sd_seconds,execution:r.execution,runtime:r.runtime,
    chart_eligible:r.eligible,implementation_url:linkFor(r.implementations[0]),
    timing_aliases:r.implementations.slice(1).map(p=>({program_key:p.key,implementation:p.id,url:linkFor(p)})),
    source_sha256:r.implementations[0].files,report:r.report,sample_details:r.details}));
}

const exportColumns=['sample_id','language','language_key','benchmark','benchmark_key','workload','implementation','program_key',
  'run','seconds','time_x_best','canonical_loc','formatted_loc','median_seconds','sd_seconds','execution','runtime',
  'chart_eligible','implementation_url','timing_aliases','source_sha256','report','sample_details'];
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
