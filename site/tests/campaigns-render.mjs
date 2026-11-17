// Execute the real entry point with a minimal DOM adapter (no benchmark timing).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as model from '../src/campaigns-model.mjs';

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

async function mount(bundle,query='') {
  const elements=new Map();
  const element=selector=>{if(!elements.has(selector))elements.set(selector,new Element());return elements.get(selector);};
  for(const [id,value] of [['family','all'],['progress','all'],['backend','source']])element('#'+id).value=value;
  element('#family').innerHTML='<option value="all">Every family</option>';
  element('#backend').options=['source','bytecode','native'].map(value=>({value}));
  const history={replaceState(_a,_b,url){this.url=url;}};
  let fetchedURL;
  const context=vm.createContext({...model,document:{querySelector:element},URL,URLSearchParams,console,
    location:{search:query,pathname:'/metrics/'},history,
    fetch:async url=>{fetchedURL=String(url);return {ok:true,json:async()=>bundle};}});
  vm.runInContext(source,context);
  await context.ready;
  assert.equal(element('#load-error').textContent,'');
  return {element,history,fetchedURL};
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

let {element,history,fetchedURL}=await mount(bundle);
assert.equal(fetchedURL,'http://localhost/benchmarks/campaigns.json?v=test-build');
assert.ok(element('#cases').innerHTML.includes('Scalar &lt;safe&gt;'));
assert.ok(element('#detail').innerHTML.includes('100.00 µs'));
assert.ok(element('#detail').innerHTML.includes('&lt;script&gt;'));
assert.ok(!element('#detail').innerHTML.includes('<script>'));
assert.ok(element('#detail').innerHTML.includes('href="http://localhost/benchmarks/campaign-evidence/run-001/raw/fork-1/supervised.json"'));
assert.ok(history.url.includes('case=scalar'));
element('#search').value='graphs';element('#search').events.input();
assert.ok(element('#cases').innerHTML.includes('Graphs'));
assert.ok(element('#detail').innerHTML.includes('Future coverage'));
element('#search').value='no matching case';element('#search').events.input();
assert.equal(element('#empty').hidden,false);
assert.ok(element('#detail').innerHTML.includes('another filter'));

const native={...base,case_id:'native-build',backend:'native',summary:{source_to_executable_seconds:{median:1,samples:[1]}},
  samples:[{fork:0,raw:'raw/fork-1',metrics:{source_to_executable_seconds:1}}]};
({element}=await mount({...bundle,campaigns:[{...campaign,results:[native]}]}));
assert.equal(element('#backend').value,'native');
assert.equal(element('#metric').value,'source_to_executable_seconds');
assert.ok(element('#detail').innerHTML.includes('Native build'));
assert.ok(element('#detail').innerHTML.includes('1.000 s'));

({element}=await mount({...bundle,campaigns:[]}));
assert.ok(element('#campaign').innerHTML.includes('No campaigns yet'));
assert.ok(element('#detail').innerHTML.includes('does not include'));
console.log('Campaign entry point: rendering, filters, source escaping, raw links, empty history and native selection passed.');

const program={...base,case_id:'deflate',backend:'program-jit-bytecode',measurement:{boundary:'checked_native_program_call',primary_metric:'native_program_call_seconds',schedule:[[]]},summary:{native_program_call_seconds:{median:.004,samples:[.004]}},samples:[{fork:0,raw:'raw/fork-1',metrics:{native_program_call_seconds:.004}}]};
({element}=await mount({...bundle,catalog:{...catalog,cases:[{id:'deflate',title:'Deflate',family:'applications',progress:'implemented'}]},campaigns:[{...campaign,results:[program]}]}));
assert.equal(element('#metric').value,'native_program_call_seconds');
assert.equal(element('#backend').value,'program-jit-bytecode');
assert.ok(element('#detail').innerHTML.includes('4.00 ms'));
assert.ok(element('#coverage-summary').textContent.includes('1 of 1'));
assert.ok(element('#backend').innerHTML.includes('JVM control'));
console.log('Complete application paths and per-contract primary metrics passed.');
