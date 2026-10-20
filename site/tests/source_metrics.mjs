// Small source-metric display/export fixtures. No browser or recorded suite.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sourceSizeFields,sampleRows,exportRows,samplesCSV,sampleColumns} from '../src/sample_data.mjs';

const scope=(bytes,gzip,tokens)=>({utf8_bytes:bytes,gzip_bytes:gzip,cl100k_base_tokens:tokens});
const metrics={retained_application_loc:{value:2,metric:'retained-owner-rule',status:'retained-not-uniformly-recertified'},
  canonical_formatted_loc:{value:null,complete:false,status:'formatter-unavailable'},
  application:scope(9,29,5),submitted:scope(50,70,21),excluded_support:scope(41,61,16),
  files:[{name:'λ.ua',role:'application',source_sha256:'a'.repeat(64),application_line_ranges:[{start:1,end:2},{start:5,end:5}],
    embedded_support_line_ranges:[{start:3,end:4}],application:{...scope(9,29,5),sha256:'b'.repeat(64)},
    submitted:{...scope(50,70,21),sha256:'a'.repeat(64)},excluded_support:{...scope(41,61,16),sha256:'c'.repeat(64)}}]};
const program={key:'task:first',id:'first',language:'test',benchmark:'task',files:['a'.repeat(64)],
  loc:2,formatted_loc_complete:false,formatted_loc:null,formatted_loc_status:'formatter-unavailable',
  seconds:1,samples:[1,1.1,0.9],source_metrics:metrics};
const definitions={schema:'benchmark-source-metrics.v1',report_sha256:'d'.repeat(64),
  tokenizer:{name:'cl100k_base',status:'available'},uniform_logical_loc:{status:'unavailable'},
  scope_definition:{application:'Exact source partitions.'}};
const data={languages:[{key:'test',label:'Test'}],benchmarks:[{key:'task',title:'Task',workload:'full',baseline_seconds:0.5}],
  programs:{[program.key]:program},program_inventory:{},source_metrics:definitions,
  repository:{url:'https://example.test/repository'}};
const rows=sampleRows(data),row=rows[0];
assert.equal(rows.length,3);assert.equal(row.application_utf8_bytes,9);assert.equal(row.submitted_utf8_bytes,50);
assert.equal(row.excluded_support_utf8_bytes,41);assert.equal(row.application_gzip_bytes,29);
assert.equal(row.application_cl100k_base_tokens,5);assert.equal(row.normalized_loc_rule,'retained-owner-rule');
assert.equal(row.formatted_loc,null);assert.equal(row.formatted_loc_status,'formatter-unavailable');
for(const key of ['loc','formatted_loc','application_utf8_bytes','application_gzip_bytes','application_cl100k_base_tokens',
  'submitted_utf8_bytes','submitted_gzip_bytes','submitted_cl100k_base_tokens'])assert.ok(sampleColumns.some(([column])=>column===key));
const record=exportRows(rows,p=>'https://example.test/#'+p.key)[0];
assert.equal(record.canonical_loc,2);assert.equal(record.normalized_application_loc,2);
assert.equal(record.qualified_formatted_loc,null);assert.equal(record.application_utf8_bytes,9);
assert.equal(record.submitted_cl100k_base_tokens,21);assert.deepEqual(record.source_metrics,metrics);
assert.deepEqual(record.source_metric_definitions,definitions);
assert.deepEqual(record.source_metrics.files[0].application_line_ranges,[{start:1,end:2},{start:5,end:5}]);
const csv=samplesCSV([record]);
for(const name of ['normalized_application_loc','normalized_loc_status','qualified_formatted_loc','application_utf8_bytes',
  'submitted_gzip_bytes','excluded_support_cl100k_base_tokens','source_metrics','source_metric_definitions'])assert.ok(csv.split('\r\n')[0].split(',').includes(name));
assert.ok(csv.includes('retained-not-uniformly-recertified'));assert.ok(csv.includes('cl100k_base'));
const familyRows=sampleRows({...data,programs:{[program.key]:{...program,authorship:{label:'AI adapted',ai:{models:[],model_family:'Codex GPT-6',status:'family-identified-exact-model-unverified'}}}}});
assert.equal(familyRows[0].ai_model,'Codex GPT-6 family · exact version unverified');
const absent=sourceSizeFields({...program,source_metrics:undefined});
assert.equal(absent.application_utf8_bytes,null);assert.equal(absent.application_cl100k_base_tokens,null);
const disabled=sourceSizeFields({...program,source_metrics:{...metrics,application:{...metrics.application,cl100k_base_tokens:null}}});
assert.equal(disabled.application_cl100k_base_tokens,null);
const alias={...program,key:'task:alias',id:'alias',timing_alias_of:program.key,source_metrics:{...metrics,application:scope(12,32,6)}};
const shared=sampleRows({...data,program_inventory:{[alias.key]:alias}});
assert.equal(shared.length,3);
assert.equal(exportRows(shared,p=>p.key)[0].timing_aliases[0].source_metrics.application.utf8_bytes,12);

const app=readFileSync(new URL('../src/app.mjs',import.meta.url),'utf8');
const rendering=app.slice(app.indexOf('function renderSourceMetrics('),app.indexOf('function renderInspector('));
const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const render=new Function('data','esc',rendering+'\nreturn renderSourceMetrics;')(data,esc);
const html=render(program,program.files[0]);
for(const text of ['UTF-8 bytes','gzip bytes','cl100k_base','Submitted bundle','Excluded support','1–2, 5','3–4',
  'not been uniformly recertified','comments and whitespace',definitions.report_sha256])assert.ok(html.includes(text),text);
assert.ok(render({...program,source_metrics:undefined},program.files[0]).includes('unavailable'));
assert.ok(!render({...program,source_metrics:undefined},program.files[0]).includes('>0<'));
const unavailableRender=new Function('data','esc',rendering+'\nreturn renderSourceMetrics;')(
  {...data,source_metrics:{...definitions,tokenizer:{status:'unavailable',reason:'Pinned tokenizer missing.'}}},esc);
assert.ok(unavailableRender(program,program.files[0]).includes('Blank token cells are not estimated'));
console.log('Source metrics: scoped counts, missing evidence, aliases, CSV/JSON fields and exact partition inspector PASS');
