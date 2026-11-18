// Execute the real entry point with a minimal DOM adapter (no benchmark timing).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {gzipSync} from 'node:zlib';
import * as model from '../src/campaigns-model.mjs';
import * as routing from '../src/metrics-model.mjs';

class Element {
  constructor(){this._html='';this._value='';this.textContent='';this.hidden=false;this.events={};this.options=[];}
  set innerHTML(value){this._html=value;const options=[...value.matchAll(/<option value="([^"]*)">/g)].map(match=>({value:match[1]}));if(options.length){this.options=options;if(!options.some(o=>o.value===this._value))this._value=options[0].value;}}
  get innerHTML(){return this._html;}
  set value(value){this._value=value;} get value(){return this._value;}
  addEventListener(name,callback){this.events[name]=callback;}
}

const source=fs.readFileSync(new URL('../src/campaigns.mjs',import.meta.url),'utf8')
  .replace(/^import .*;\n/gm,'').replaceAll('import.meta.url',"'http://localhost/benchmarks/campaigns.mjs?v=test-build'")
  .replace('start().catch(error=>','globalThis.ready=start().catch(error=>');

async function mount(bundle,query='',detailFiles={},compressed=true) {
  const elements=new Map();
  const element=selector=>{if(!elements.has(selector))elements.set(selector,new Element());return elements.get(selector);};
  for(const [id,value] of [['family','all'],['progress','all'],['backend','source']])element('#'+id).value=value;
  element('#family').innerHTML='<option value="all">Every family</option>';
  element('#backend').options=['source','bytecode','native'].map(value=>({value}));
  const history={replaceState(_a,_b,url){this.url=url;}};
  const requests=[];
  const context=vm.createContext({...model,...routing,document:{querySelector:element},URL,URLSearchParams,console,Response,DecompressionStream:compressed?DecompressionStream:undefined,
    location:{search:query,pathname:'/metrics/'},history,
    fetch:async url=>{requests.push(String(url));const name=new URL(url).pathname.replace('/benchmarks/','');return new Response(name==='campaigns.json.gz'?gzipSync(JSON.stringify(bundle)):JSON.stringify(name==='campaigns.json'?bundle:detailFiles[name]));}});
  vm.runInContext(source,context);
  await context.ready;
  assert.equal(element('#load-error').textContent,'');
  return {element,history,fetchedURL:requests[0],requests};
}

const task={outputs:['result'],arithmetic:'f64',absolute_tolerance:1e-9,relative_tolerance:1e-10};
const base={case_id:'scalar',title:'Scalar <safe>',family:'arithmetic',backend:'source',lane:'candidate',
  revision:'abc123',progress:'measured',capability:'supported',outcome:'ok',task_hash:'task',measurement_hash:'measurement',
  source_sha256:'hash',environment_hash:'host',task,measurement:{boundary:'resident_turn',schedule:[[2],[3],[2]]},
  source:'answer := x * x\n<script>alert(1)</script>',verification:{outcome:'ok',outputs:[{kind:'scalar',value:4}],raw:'raw/verify'},
  summary:{resident_turn_seconds:{median:.0001,samples:[.0001,.00011,.00009]}},
  samples:[{fork:0,raw:'raw/fork-1',metrics:{resident_turn_seconds:.0001}}]};
const worker={revision:'abc123',binary_sha256:'binary',adapter_sha256:'adapter',rustc:'test compiler'};
const campaign={id:'run-001',started_at:'2026-11-16T12:00:00Z',evidence_path:'campaign-evidence/run-001',
  workers:{candidate:worker},environment:{cpu:'Test CPU',system:'TestOS',release:'1'},results:[base],comparisons:[]};
const catalog={candidate_revision:'abc123',cases:[{id:'scalar',title:'Scalar <safe>',family:'arithmetic',progress:'implemented',compiler_tests:[]},
  {id:'native-build',title:'Native build',family:'compilation',progress:'implemented'},
  {id:'graphs',title:'Graphs',family:'graphs',progress:'planned',notes:'Future coverage'}]};
const bundle={schema:'mech.benchmark-dashboard.v1',catalog,campaigns:[campaign]};

let {element,history,fetchedURL}=await mount(bundle,'?case=scalar');
assert.equal(fetchedURL,'http://localhost/benchmarks/campaigns.json.gz?v=test-build');
assert.ok(element('#cases').innerHTML.includes('Scalar &lt;safe&gt;'));
assert.ok(element('#detail').innerHTML.includes('100 µs'));
assert.ok(element('#detail').innerHTML.includes('&lt;script&gt;'));
assert.ok(!element('#detail').innerHTML.includes('<script>'));
assert.ok(element('#detail').innerHTML.includes('href="http://localhost/benchmarks/campaign-evidence/run-001/raw/fork-1/supervised.json"'));
assert.ok(history.url.includes('case=scalar'));
element('#search').value='graphs';element('#search').events.input();
assert.equal(element('#empty').hidden,false);
assert.ok(!element('#cases').innerHTML.includes('Graphs'));
element('#search').value='no matching case';element('#search').events.input();
assert.equal(element('#empty').hidden,false);
assert.equal(element('#detail').hidden,true);

const native={...base,case_id:'native-build',backend:'native',summary:{source_to_executable_seconds:{median:1,samples:[1]}},
  samples:[{fork:0,raw:'raw/fork-1',metrics:{source_to_executable_seconds:1}}]};
({element}=await mount({...bundle,campaigns:[{...campaign,results:[native]}]},'?case=native-build'));
assert.equal(element('#backend').value,'$auto');
assert.equal(element('#metric').value,'$primary');
assert.ok(element('#detail').innerHTML.includes('Native build'));
assert.ok(element('#detail').innerHTML.includes('1 s'));

({element}=await mount({...bundle,campaigns:[]}));
assert.ok(element('#campaign').innerHTML.includes('Latest measured'));
assert.equal(element('#detail').hidden,true);
console.log('Campaign entry point: rendering, filters, source escaping, raw links, empty history and native selection passed.');

const program={...base,case_id:'deflate',backend:'program-jit-bytecode',measurement:{boundary:'checked_native_program_call',primary_metric:'native_program_call_seconds',schedule:[[]]},summary:{native_program_call_seconds:{median:.004,samples:[.004]}},samples:[{fork:0,raw:'raw/fork-1',metrics:{native_program_call_seconds:.004}}]};
({element}=await mount({...bundle,catalog:{...catalog,cases:[{id:'deflate',title:'Deflate',family:'applications',progress:'implemented'}]},campaigns:[{...campaign,results:[program]}]},'?case=deflate'));
assert.equal(element('#metric').value,'$primary');
assert.equal(element('#backend').value,'$auto');
assert.ok(element('#detail').innerHTML.includes('4 ms'));
assert.ok(element('#coverage-summary').textContent.includes('1 of 1'));
assert.ok(!element('#backend').innerHTML.includes('JVM'));
assert.ok(!element('#backend').innerHTML.includes('Roc compressor'));
assert.ok(element('#cases').innerHTML.includes('No matched libdeflate timing'));
assert.ok(!element('#cases').innerHTML.includes('>—<'));
console.log('Complete application paths and per-contract primary metrics passed.');

const unmatchedCompressor={...base,case_id:'deflate',backend:'libdeflate',lane:'control',
  revision:'92e6a0db9fa848d742f9eb286c92afc60f2c3dda',
  source_sha256:'a82938cd20ecb3404f0b0e3fc7d1553706442b8b956443d8ca98ebebacecec05',
  measurement:{primary_metric:'control_call_seconds'},summary:{control_call_seconds:{median:99,samples:[99]}},
  samples:[{fork:0,raw:'raw/compressor',metrics:{control_call_seconds:99}}]};
({element}=await mount({...bundle,catalog:{...catalog,cases:[{id:'deflate',title:'Deflate',family:'applications',progress:'implemented'}]},
  campaigns:[{...campaign,results:[program,unmatchedCompressor]}]},'?case=deflate'));
assert.ok(element('#cases').innerHTML.includes('4 ms'),'the original Mech observation remains available');
assert.ok(element('#cases').innerHTML.includes('No matched comparison'));
for(const selector of ['#cases','#detail']){
  assert.ok(!element(selector).innerHTML.includes('99 s'),'unmatched compressor seconds are not presented alongside the Mech timing');
  assert.ok(!element(selector).innerHTML.includes('Reference only'));
  assert.ok(!element(selector).innerHTML.includes('Level-12 reference'));
}
console.log('Unmatched compressor timings are absent from task summaries and details.');

({element}=await mount({...bundle,campaigns:[{...campaign,raw_archive:'raw.tar.gz',raw_archive_url:'https://raw.githubusercontent.com/mech-lang/benchmarks/abc/results/campaigns/run-001/raw.tar.gz',compressed_evidence:{'raw/fork-1/supervised.json':'raw/fork-1/supervised.json.gz'}}]},'?case=scalar'));
assert.ok(element('#detail').innerHTML.includes('/raw/fork-1/supervised.json.gz"'));
assert.ok(element('#detail').innerHTML.includes('/campaign-evidence/run-001/raw.tar.gz"'),'archive download keeps its site URL for the pinned redirect');
console.log('Lossless compressed observation links and stable archive download routes passed.');

const candidate={...base,control_contract:'same-task'};
const control={...candidate,backend:'rust',lane:'control',title:'Rust',source:'independent Rust source',
  measurement:{primary_metric:'rust_call_seconds',metric_mapping:{resident_turn_seconds:'rust_call_seconds'}},
  summary:{rust_call_seconds:{median:.00001,samples:[.00001]}},samples:[{fork:0,raw:'raw/rust-1',metrics:{rust_call_seconds:.00001}}]};
const summary=(record,path)=>{
  const {source,samples,task,verification,...index}=record;
  return {...index,measurement:{primary_metric:record.measurement.primary_metric,metric_mapping:record.measurement.metric_mapping},detail_path:path};
};
const contextPath='campaign-details/run-001/context.json',candidatePath='campaign-details/run-001/0000.json',controlPath='campaign-details/run-001/0001.json';
const lazyBundle={schema:'mech.benchmark-dashboard.v2',catalog:structuredClone(catalog),campaigns:[{id:campaign.id,started_at:campaign.started_at,workers:{candidate:{revision:worker.revision}},context_path:contextPath,results:[summary(candidate,candidatePath),summary(control,controlPath)]}]};
const detailFiles={
  [contextPath]:{schema:'mech.benchmark-context.v1',campaign:{id:campaign.id,workers:campaign.workers,environment:campaign.environment,evidence_path:campaign.evidence_path}},
  [candidatePath]:{schema:'mech.benchmark-observation.v1',campaign_id:campaign.id,definition:catalog.cases[0],record:candidate},
  [controlPath]:{schema:'mech.benchmark-observation.v1',campaign_id:campaign.id,definition:catalog.cases[0],record:control},
};
let lazy=await mount(structuredClone(lazyBundle),'',detailFiles);
assert.equal(lazy.requests.length,1,'initial summary only fetches the index');
assert.equal(lazy.element('#detail').hidden,true);
assert.equal(lazy.element('.workspace').className,'workspace summary');
assert.ok(!lazy.history.url.includes('case='));
const fallback=await mount(structuredClone(lazyBundle),'',detailFiles,false);
assert.ok(fallback.fetchedURL.includes('campaigns.json?v='),'older browsers can use the uncompressed summary');
assert.ok(lazy.element('#cases').innerHTML.includes('Rust'));
const choose=()=>lazy.element('#cases').events.click({target:{closest:()=>({dataset:{case:'scalar'}})}});
await choose();
assert.equal(lazy.requests.length,4,'opening a task fetches its context, measurement and control only');
assert.ok(lazy.element('#detail').innerHTML.includes('independent Rust source'));
assert.ok(lazy.requests.slice(1).every(url=>new URL(url).searchParams.get('v')==='test-build'));
await lazy.element('#detail').events.click({target:{closest:()=>true}});
assert.equal(lazy.element('#detail').hidden,true);
await choose();
assert.equal(lazy.requests.length,4,'reopening a task uses cached details');
const invalid=structuredClone(detailFiles);invalid[candidatePath].record.task_hash='wrong-task';
lazy=await mount(structuredClone(lazyBundle),'?case=scalar',invalid);
assert.ok(lazy.element('#detail').innerHTML.includes('task_hash differs from its summary'));
assert.ok(!lazy.element('#detail').innerHTML.includes('class="measurement"'));
console.log('Summary-only loading, selected task/control requests, cache, shared links and detail identity checks passed.');

const standalone={...base,case_id:'no-reference',title:'Standalone measurement'};
({element,history}=await mount({...bundle,catalog:{...catalog,cases:[catalog.cases[0],{id:'no-reference',title:'Standalone measurement',family:'arithmetic',progress:'implemented'}]},campaigns:[{...campaign,results:[candidate,control,standalone]}]}));
assert.ok(element('#cases').innerHTML.includes('result-tag slower'));
assert.ok(!element('#cases').innerHTML.includes('Standalone measurement'),'the default comparison view excludes unmatched observations');
await element('#suite-outcomes').events.click({target:{closest:()=>({dataset:{outcome:'all'}})}});
assert.ok(element('#cases').innerHTML.includes('Standalone measurement'),'all original measurements remain accessible');
assert.ok(element('#cases').innerHTML.includes('No matched comparison'));
assert.ok(history.url.includes('result=all'));
await element('#suite-outcomes').events.click({target:{closest:()=>({dataset:{outcome:'faster'}})}});
assert.equal(element('#empty').hidden,false,'an empty faster selection cannot invent a win');
console.log('Default matched results, slower colors, access to standalone observations and shared outcome filters pass.');
