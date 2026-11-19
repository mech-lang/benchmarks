import {formatRatio} from './campaigns-model.mjs';

export const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const number=(value,digits=4)=>Number(value).toLocaleString(undefined,{maximumSignificantDigits:digits});
export const categoryLabels={'cpu-jit':'CPU · JIT','cpu-aot':'CPU · AOT','cpu-interpreted':'CPU · interpreted',metal:'Metal GPU'};
const median=values=>{const a=[...values].sort((x,y)=>x-y),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2;};
export function validateEKF(data){
  if(data?.schema!=='mech.ekf-study.v1'||!Array.isArray(data.studies)||!data.studies.length)throw Error('Unsupported EKF evidence');
  const ids=new Set();
  for(const study of data.studies){
    if(!/^[a-z0-9-]+$/.test(study.id)||ids.has(study.id)||!study.rows?.length)throw Error('Invalid EKF study');
    ids.add(study.id);const rows=new Set();
    for(const row of study.rows){
      if(rows.has(row.id)||!['checked','unchecked'].includes(row.mode)||typeof row.is_mech!=='boolean'||!categoryLabels[row.category]||!row.source_url||!/^https:\/\/|^\/benchmarks\//.test(row.source_url))throw Error('Invalid EKF implementation');
      rows.add(row.id);const samples=row.samples_million_filter_turns_per_second;
      if(samples?.length!==row.n||samples.length!==row.samples_seconds_per_filter_turn?.length||samples.some(x=>!Number.isFinite(x)||x<=0)||row.samples_seconds_per_filter_turn.some(x=>!Number.isFinite(x)||x<=0))throw Error('Incomplete EKF samples');
      const m=median(samples),mad=median(samples.map(x=>Math.abs(x-m)));
      if(Math.abs(m-row.median)>1e-8||Math.abs(mad-row.mad)>1e-8||Math.abs(median(row.samples_seconds_per_filter_turn)-row.time_seconds)>1e-12)throw Error('EKF summary differs from its samples');
    }
  }
  return data;
}
export function referenceOptions(study,category){
  return [...new Set(study.rows.filter(row=>!row.is_mech&&row.category===category).map(row=>row.label))].sort((a,b)=>a.localeCompare(b));
}
export function referenceFor(study,row,references={}){
  // A peer is external to Mech, in this study, category and checking mode.
  // Search and visibility never select a faster Mech backend or another cohort.
  const peers=study.rows.filter(peer=>!peer.is_mech&&peer.category===row.category&&peer.mode===row.mode);
  return peers.find(peer=>peer.label===references[row.category])??peers.sort((a,b)=>a.time_seconds-b.time_seconds||a.label.localeCompare(b.label))[0]??null;
}
export function relativeTime(study,row,references={}){
  const peer=referenceFor(study,row,references);return peer?row.time_seconds/peer.time_seconds:null;
}
export function selectedRows(study,{mode='both',query='',sort='name',descending=false,references={}}={}){
  const value=row=>({name:row.label,mode:row.mode,category:categoryLabels[row.category],peer:referenceFor(study,row,references)?.label,rate:row.median,mad:row.mad,n:row.n,time:row.time_seconds,ratio:relativeTime(study,row,references),version:row.version})[sort];
  return study.rows.filter(row=>(mode==='both'||row.mode===mode)&&`${row.label} ${row.version}`.toLowerCase().includes(query.toLowerCase().trim())).sort((a,b)=>{
    const x=value(a),y=value(b);if(x==null||y==null)return x==null&&y==null?a.label.localeCompare(b.label):x==null?1:-1;
    const difference=typeof x==='string'?x.localeCompare(y):x-y;
    return (descending?-1:1)*(difference||a.label.localeCompare(b.label)||a.mode.localeCompare(b.mode));
  });
}
export function sampleChart(rows,{width=900,samples=true,medians=true}={}){
  if(!rows.length)return '<p class="empty">No implementations match this selection.</p>';
  if(!samples&&!medians)return '<p class="empty">Samples and medians are hidden. The table still shows all selected results.</p>';
  width=Math.max(320,Math.round(width));const left=Math.min(260,Math.round(width*.42)),right=25,top=40,stride=48,height=top+rows.length*stride+42;
  const values=rows.flatMap(row=>samples?row.samples_million_filter_turns_per_second:[row.median-row.mad,row.median+row.mad]).filter(x=>x>0);
  const low=Math.floor(Math.log10(Math.min(...values)))-.08,high=Math.ceil(Math.log10(Math.max(...values)))+.08;
  const x=value=>left+(Math.log10(value)-low)/(high-low)*(width-left-right);
  const ticks=[];for(let p=Math.ceil(low);p<=Math.floor(high);p++)ticks.push(10**p);
  const label=(value,y)=>{const max=Math.max(13,Math.floor((left-18)/7.5)),words=value.split(' '),lines=[''];for(const word of words){if((lines.at(-1)+' '+word).trim().length>max&&lines.length<2)lines.push(word);else lines[lines.length-1]+=(lines.at(-1)?' ':'')+word;}return lines.map((line,i)=>'<text x="8" y="'+(y+(i?13:-3))+'">'+escape(line.length>max?line.slice(0,max-1)+'…':line)+'</text>').join('');};
  return '<svg class="ekf-chart" viewBox="0 0 '+width+' '+height+'" role="group" aria-label="EKF throughput; independent samples and median with median absolute deviation">'+
    '<text x="8" y="17">Throughput (M filter-turns/s) · log₁₀</text>'+
    ticks.map(t=>'<line class="chart-grid" x1="'+x(t)+'" x2="'+x(t)+'" y1="28" y2="'+(height-30)+'"/><text x="'+x(t)+'" y="'+(height-8)+'" text-anchor="middle">'+number(t)+'</text>').join('')+
    rows.map((row,i)=>{const y=top+i*stride+12,color=row.mode==='checked'?'var(--gold)':'#80bfea';return '<g class="ekf-series" data-ekf-row="'+i+'" tabindex="0" aria-label="'+escape(row.label+' · '+row.mode+' · '+number(row.median)+' million filter-turns per second')+'">'+label(row.label+' · '+row.mode,y)+
      (samples?row.samples_million_filter_turns_per_second.map((sample,j)=>'<circle class="ekf-sample" fill="'+color+'" cx="'+x(sample)+'" cy="'+(y+(j%5-2)*2)+'" r="2.6"/>').join(''):'')+
      (medians?'<line stroke="'+color+'" stroke-width="2" x1="'+x(Math.max(row.median-row.mad,Number.MIN_VALUE))+'" x2="'+x(row.median+row.mad)+'" y1="'+y+'" y2="'+y+'"/><rect fill="'+color+'" x="'+(x(row.median)-4)+'" y="'+(y-4)+'" width="8" height="8"/>':'')+'</g>';}).join('')+'</svg>';
}
export function exportRows(studies,selection,references={}){
  const quote=value=>'"'+String(value??'').replaceAll('"','""')+'"';
  const absolute=value=>value?new URL(value,'https://mech-lang.org').href:'';
  const header=['study','machine','precision','filters','turns','recorded_at','implementation','mode','sample','million_filter_turns_per_second','seconds_per_filter_turn','median_throughput','mad_throughput','median_seconds_per_filter_turn','category','peer','peer_median_seconds_per_filter_turn','time_divided_by_peer_time','peer_source','version','source','evidence','timing_scope'];
  const records=studies.flatMap(study=>(selection?.study===study.id?selection.rows:selection?[]:study.rows).flatMap(row=>{const peer=referenceFor(study,row,references);return row.samples_million_filter_turns_per_second.map((sample,i)=>[study.id,study.machine,study.precision,study.instances,study.turns,study.recorded_at,row.label,row.mode,i+1,sample,row.samples_seconds_per_filter_turn[i],row.median,row.mad,row.time_seconds,categoryLabels[row.category],peer?.label,peer?.time_seconds,relativeTime(study,row,references),absolute(peer?.source_url),row.version,absolute(row.source_url),absolute(study.evidence_url),study.scope]);}));
  return [header,...records].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
}
export {formatRatio};
