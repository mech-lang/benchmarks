import {formatRatio} from './campaigns-model.mjs';

export const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const number=(value,digits=4)=>Number(value).toLocaleString(undefined,{maximumSignificantDigits:digits});
export const categoryLabels={'cpu-jit':'CPU · JIT','cpu-aot':'CPU · AOT','cpu-interpreted':'CPU · interpreted',metal:'Metal GPU',resident:'Managed resident'};
const median=values=>{const a=[...values].sort((x,y)=>x-y),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2;};
export function validateEKF(data){
  if(data?.schema!=='mech.ekf-study.v1'||!Array.isArray(data.studies)||!data.studies.length)throw Error('Unsupported EKF evidence');
  const ids=new Set();
  for(const study of data.studies){
    if(!/^[a-z0-9-]+$/.test(study.id)||ids.has(study.id)||!study.rows?.length)throw Error('Invalid EKF study');
    ids.add(study.id);const rows=new Set();
    for(const row of study.rows){
      if(rows.has(row.id)||!['checked','unchecked'].includes(row.mode)||!['per-turn','fused-block'].includes(row.publication)||typeof row.is_mech!=='boolean'||!categoryLabels[row.category]||!row.source_url||!/^https:\/\/|^\/benchmarks\//.test(row.source_url))throw Error('Invalid EKF implementation');
      rows.add(row.id);const samples=row.samples_million_filter_turns_per_second;
      if(samples?.length!==row.n||samples.length!==row.samples_seconds_per_filter_turn?.length||samples.some(x=>!Number.isFinite(x)||x<=0)||row.samples_seconds_per_filter_turn.some(x=>!Number.isFinite(x)||x<=0))throw Error('Incomplete EKF samples');
      const m=median(samples),mad=median(samples.map(x=>Math.abs(x-m)));
      if(Math.abs(m-row.median)>1e-8||Math.abs(mad-row.mad)>1e-8||Math.abs(median(row.samples_seconds_per_filter_turn)-row.time_seconds)>1e-12)throw Error('EKF summary differs from its samples');
    }
  }
  return data;
}
export function referenceFor(study,row){
  // A peer is external to Mech, in this study, category and checking mode.
  // Search and visibility never select a faster Mech backend or another cohort.
  const peers=study.rows.filter(peer=>!peer.is_mech&&peer.category===row.category&&peer.mode===row.mode&&peer.publication===row.publication);
  return peers.sort((a,b)=>a.time_seconds-b.time_seconds||a.label.localeCompare(b.label))[0]??null;
}
export function relativeTime(study,row){
  const peer=referenceFor(study,row);return peer?row.time_seconds/peer.time_seconds:null;
}
export function mechMeasurements(data){
  const names={resident:'Resident',jit:'JIT',aot:'AOT','aot-managed':'AOT managed',gpu:'GPU','gpu-batched':'GPU batched','workers-8':'8 workers'};
  return data.studies.flatMap(study=>study.rows.filter(row=>row.is_mech).flatMap(row=>{
    const path=row.summary_path??(study.id==='backends'&&row.backend==='scalar-jit'?'jit':study.id==='backends'&&row.backend==='simd-aot'?'aot-managed':
      study.id==='cpu'&&row.label==='Mech fused SIMD/JIT'?'workers-8':study.id==='metal'?'gpu':null);
    return names[path]?[{...row,study,path,result_id:study.id+':'+row.id,variant:names[path],peer:referenceFor(study,row),ratio:relativeTime(study,row)}]:[];
  }));
}
export function selectedMeasurements(data,{mode='primary',query='',sort='name',descending=false}={}){
  const value=row=>({name:row.variant,mode:row.mode,mech:row.time_seconds,peer:row.peer?.label,reference:row.peer?.time_seconds,ratio:row.ratio})[sort];
  const measured=mechMeasurements(data),preferred=mode==='primary'?[...new Set(measured.map(row=>row.path))].map(path=>measured.find(row=>row.path===path&&row.mode==='checked')??measured.find(row=>row.path===path)):measured;
  return preferred.filter(row=>(mode==='primary'||mode==='both'||row.mode===mode)&&`${row.variant} ${row.label} ${row.peer?.label??''}`.toLowerCase().includes(query.toLowerCase().trim())).sort((a,b)=>{
    const x=value(a),y=value(b);if(x==null||y==null)return x==null&&y==null?a.label.localeCompare(b.label):x==null?1:-1;
    const difference=typeof x==='string'?x.localeCompare(y):x-y;
    return (descending?-1:1)*(difference||a.label.localeCompare(b.label)||a.mode.localeCompare(b.mode));
  });
}
export function peerChartRows(rows){
  return rows.filter(row=>row.peer).map(row=>{const values=row.samples_seconds_per_filter_turn.map(time=>time/row.peer.time_seconds),m=median(values);return {...row,label:row.variant,samples_million_filter_turns_per_second:values,median:m,mad:median(values.map(value=>Math.abs(value-m)))};});
}
export function sampleChart(rows,{width=900,samples=true,medians=true,axisLabel='Throughput (M filter-turns/s) · log₁₀',valueUnit='million filter-turns per second',tickSuffix='',reference}={}){
  if(!rows.length)return '<p class="empty">No implementations match this selection.</p>';
  if(!samples&&!medians)return '<p class="empty">Samples and medians are hidden. The table still shows all selected results.</p>';
  width=Math.max(320,Math.round(width));const left=Math.min(260,Math.round(width*.42)),right=25,top=40,stride=48,height=top+rows.length*stride+42;
  const values=rows.flatMap(row=>samples?row.samples_million_filter_turns_per_second:[row.median-row.mad,row.median+row.mad]).filter(x=>x>0);
  if(reference>0)values.push(reference);
  const min=Math.log10(Math.min(...values)),max=Math.log10(Math.max(...values)),span=Math.max(.2,max-min),low=min-span*.1,high=max+span*.1;
  const x=value=>left+(Math.log10(value)-low)/(high-low)*(width-left-right);
  const ticks=[];for(let p=Math.floor(low);p<=Math.ceil(high);p++)for(const multiplier of high-low<1?[1,2,3,4,5,6,7,8,9]:[1]){const value=multiplier*10**p;if(Math.log10(value)>=low&&Math.log10(value)<=high)ticks.push(value);}
  const label=(value,y)=>{const max=Math.max(13,Math.floor((left-18)/7.5)),words=value.split(' '),lines=[''];for(const word of words){if((lines.at(-1)+' '+word).trim().length>max&&lines.length<2)lines.push(word);else lines[lines.length-1]+=(lines.at(-1)?' ':'')+word;}return lines.map((line,i)=>'<text x="8" y="'+(y+(i?13:-3))+'">'+escape(line.length>max?line.slice(0,max-1)+'…':line)+'</text>').join('');};
  return '<svg class="ekf-chart" viewBox="0 0 '+width+' '+height+'" role="group" aria-label="'+escape(axisLabel)+'; independent samples and median with median absolute deviation">'+
    '<text x="8" y="17">'+escape(axisLabel)+'</text>'+
    ticks.map(t=>'<line class="chart-grid" x1="'+x(t)+'" x2="'+x(t)+'" y1="28" y2="'+(height-30)+'"/><text x="'+x(t)+'" y="'+(height-8)+'" text-anchor="middle">'+number(t)+escape(tickSuffix)+'</text>').join('')+
    (reference>0?'<line class="reference-line" x1="'+x(reference)+'" x2="'+x(reference)+'" y1="28" y2="'+(height-30)+'"/>':'')+
    rows.map((row,i)=>{const y=top+i*stride+12,color=row.mode==='checked'?'var(--gold)':'#80bfea';return '<g class="ekf-series" data-ekf-row="'+(row.chart_index??i)+'" tabindex="0" aria-label="'+escape(row.label+' · '+row.mode+' · '+number(row.median)+' '+valueUnit)+'">'+label(row.label+' · '+row.mode,y)+
      (samples?row.samples_million_filter_turns_per_second.map((sample,j)=>'<circle class="ekf-sample" fill="'+color+'" cx="'+x(sample)+'" cy="'+(y+(j%5-2)*2)+'" r="2.6"/>').join(''):'')+
      (medians?'<line stroke="'+color+'" stroke-width="2" x1="'+x(Math.max(row.median-row.mad,Number.MIN_VALUE))+'" x2="'+x(row.median+row.mad)+'" y1="'+y+'" y2="'+y+'"/><rect fill="'+color+'" x="'+(x(row.median)-4)+'" y="'+(y-4)+'" width="8" height="8"/>':'')+'</g>';}).join('')+'</svg>';
}
export function exportRows(studies,selection){
  const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const absolute=value=>value?new URL(value,'https://mech-lang.org').href:'';
  const header=['study','machine','precision','filters','turns','recorded_at','implementation','mode','sample','million_filter_turns_per_second','seconds_per_filter_turn','median_throughput','mad_throughput','median_seconds_per_filter_turn','category','peer','peer_median_seconds_per_filter_turn','time_divided_by_peer_time','peer_source','peer_version','publication','version','source','source_identity_basis','evidence','timing_scope'];
  const chosen=selection??mechMeasurements({studies});
  const records=studies.flatMap(study=>chosen.filter(row=>row.study.id===study.id&&row.is_mech).flatMap(row=>{const peer=referenceFor(study,row);return row.samples_million_filter_turns_per_second.map((sample,i)=>[study.id,study.machine,study.precision,study.instances,study.turns,study.recorded_at,row.label,row.mode,i+1,sample,row.samples_seconds_per_filter_turn[i],row.median,row.mad,row.time_seconds,categoryLabels[row.category],peer?.label,peer?.time_seconds,relativeTime(study,row),absolute(peer?.source_url),peer?.version,row.publication,row.version,absolute(row.source_url),row.source_identity_basis??'Retained source snapshot; see provenance.',absolute(study.evidence_url),study.scope]);}));
  return [header,...records].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
}
export {formatRatio};
