// Serial native-browser QA of the bound source-size projections. No benchmarks.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createServer} from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]??'site/public'),output=process.argv[3];
assert.ok(output,'Asset directory and fresh receipt path required');await assert.rejects(fs.access(output));
const manifest=JSON.parse(await fs.readFile(path.join(root,'build.json'),'utf8'));
const raw=await fs.readFile(path.join(root,'data.json')),data=JSON.parse(raw);
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
assert.equal(digest(raw),manifest.files['data.json']);
const catalog={...data.program_inventory,...data.programs};
const definitions={canonical:['Normalized LOC','LOC'],formatted:['Qualified formatted LOC','LOC'],
  logical:['Qualified logical units · partial coverage','logical units','logical_units'],
  bytes:['Application UTF-8 bytes','UTF-8 bytes','utf8_bytes'],
  gzip:['Application gzip bytes','gzip bytes','gzip_bytes'],bpe:['Application BPE tokens','BPE tokens','cl100k_base_tokens']};
const close=(a,b,label)=>assert.ok(Math.abs(a-b)<=1e-11*Math.max(1,Math.abs(a),Math.abs(b)),`${label}: ${a} != ${b}`);
const mean=values=>Math.exp(values.reduce((sum,n)=>sum+Math.log(n),0)/values.length);
function expected(metric,state){
  const field=definitions[metric][2],rawSize=!!field,disabled=new Set(state.disabled);
  const counts=p=>metric==='logical'?(p.logical_source_units?.status==='qualified'?p.logical_source_units.application:null):rawSize?p.source_metrics?.application?.[field]:metric==='formatted'?
    (p.formatted_loc_status==='qualified'&&p.formatted_loc_complete===true?p.formatted_loc:null):p.loc;
  const valid=p=>p.eligible_for_chart!==false&&Number.isFinite(p.seconds)&&p.seconds>0&&Number.isFinite(p.y)&&p.y>0&&Number.isSafeInteger(counts(p))&&counts(p)>0;
  const baselines=new Map(data.benchmarks.map(b=>{const rows=Object.values(catalog).filter(p=>p.benchmark===b.key&&valid(p));
    return [b.key,rawSize&&rows.length?Math.min(...rows.map(counts)):metric==='formatted'?b.baseline_formatted_loc:b.baseline_loc];}));
  const rows=[],owners=new Map();
  for(const language of data.languages.filter(l=>state.languages.includes(l.key))){
    const inputs=[];
    for(const b of data.benchmarks.filter(b=>state.benchmarks.includes(b.key))){
      const group=b.groups.find(g=>g.language===language.key);
      const pool=rawSize?Object.values(catalog).filter(p=>p.language===language.key&&p.benchmark===b.key):(group?.programs??[]).map(k=>data.programs[k]);
      const candidates=pool.filter(p=>valid(p)&&!disabled.has(p.key)).map(p=>({...p,value:counts(p),
        axisX:rawSize?counts(p)/baselines.get(b.key):metric==='formatted'?p.formatted_x:p.x})).filter(p=>Number.isFinite(p.axisX)&&p.axisX>0);
      if(!candidates.length)continue;
      const fast=candidates.reduce((a,p)=>p.seconds<a.seconds||p.seconds===a.seconds&&p.value<a.value?p:a);
      const small=candidates.reduce((a,p)=>p.value<a.value||p.value===a.value&&p.seconds<a.seconds?p:a);
      inputs.push({b,fast,small});
      const endpoints=[state.fast?fast:null,state.small?small:null].filter(Boolean);
      for(const p of candidates.filter(p=>endpoints.some(e=>p.key===e.key||p.seconds===e.seconds&&p.value===e.value))){
        const owner=p.timing_alias_of||p.key;
        if(!owners.has(owner)||p.key===owner)owners.set(owner,{p,b});
      }
    }
    if(inputs.length)rows.push({language:language.key,n:inputs.length,
      fast:{x:mean(inputs.map(i=>i.fast.axisX)),y:mean(inputs.map(i=>i.fast.y))},
      small:{x:mean(inputs.map(i=>i.small.axisX)),y:mean(inputs.map(i=>i.small.y))}});
  }
  const samples=[...owners].flatMap(([owner,{p,b}])=>p.samples.map((elapsed,i)=>({id:owner+'#'+(i+1),x:p.axisX,y:elapsed/b.baseline_seconds,elapsed}))).sort((a,b)=>a.id.localeCompare(b.id));
  return {rows,samples,baselines:Object.fromEntries(baselines)};
}
const server=createServer(async(req,res)=>{try{
  const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(root,'.'+(name==='/'?'/index.html':name));
  assert.ok(file.startsWith(root+path.sep));
  res.writeHead(200,{'Content-Type':({'.mjs':'text/javascript','.html':'text/html','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream'});res.end(await fs.readFile(file));
}catch{res.writeHead(404);res.end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const rows=[],notes=[],errors=[];const base=`http://127.0.0.1:${server.address().port}/`;
const settle=page=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
try{
  for(const width of [1280,390]){
    const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>errors.push(e.message));
    await page.addInitScript(()=>{const original=fetch.bind(window);window.fetch=async(...args)=>{const response=await original(...args);
      if(new URL(response.url).pathname.endsWith('/data.json'))window.sourceAxisDataSHA=response.clone().arrayBuffer().then(bytes=>crypto.subtle.digest('SHA-256',bytes)).then(hash=>[...new Uint8Array(hash)].map(n=>n.toString(16).padStart(2,'0')).join(''));
      return response;};});
    await page.goto(base);await page.waitForFunction(()=>window.benchmarkExplorer);await settle(page);
    assert.equal(await page.evaluate(()=>window.sourceAxisDataSHA),manifest.files['data.json']);
    assert.equal(await page.locator('script[type=module]').getAttribute('src'),`./app.mjs?v=${manifest.version}`);
    assert.deepEqual(await page.locator('#loc-metric option').evaluateAll(nodes=>nodes.map(n=>n.value)),Object.keys(definitions));
    let timeDomain=null;
    for(const metric of Object.keys(definitions)){
      await page.selectOption('#loc-metric',metric);await settle(page);
      const state=await page.evaluate(()=>({...benchmarkExplorer.getSelection(),fast:benchmarkExplorer.getViewState().fast,small:benchmarkExplorer.getViewState().small})),want=expected(metric,state);
      const observed=await page.evaluate(()=>({summary:benchmarkExplorer.getSummary(),domain:benchmarkExplorer.getDomains(),
        samples:[...document.querySelectorAll('#chart [data-sample]')].map(n=>({id:n.dataset.observationSource+'#'+n.dataset.timingRun,
          x:Number(n.dataset.ratioX),y:Number(n.dataset.ratioY),elapsed:Number(n.dataset.runSeconds)})).sort((a,b)=>a.id.localeCompare(b.id))}));
      assert.deepEqual(observed.summary.map(r=>r.language),want.rows.map(r=>r.language));
      for(let i=0;i<want.rows.length;i++){assert.equal(observed.summary[i].n,want.rows[i].n);
        for(const profile of ['fast','small'])for(const axis of ['x','y'])close(observed.summary[i][profile][axis],want.rows[i][profile][axis],`${metric}/${want.rows[i].language}/${profile}/${axis}`);}
      assert.equal(observed.samples.length,want.samples.length,`${width}/${metric} recorded samples`);assert.equal(new Set(observed.samples.map(s=>s.id)).size,observed.samples.length);
      for(let i=0;i<want.samples.length;i++){assert.equal(observed.samples[i].id,want.samples[i].id);for(const field of ['x','y','elapsed'])close(observed.samples[i][field],want.samples[i][field],metric+'/'+field);}
      const y=[observed.domain.yMin,observed.domain.yMax];if(timeDomain)assert.deepEqual(y,timeDomain);else timeDomain=y;
      assert.ok((await page.locator('#chart .axis-title').first().textContent())!==null);
      assert.ok((await page.locator('#mean-table thead').textContent()).includes(definitions[metric][0]));
      assert.equal(await page.locator('#source-size-note').isVisible(),!!definitions[metric][2]&&metric!=='logical');
      assert.equal(await page.locator('#qualified-logical-note').isVisible(),metric==='logical');
      if(metric==='logical'){const note=await page.locator('#qualified-logical-note').textContent();for(const word of ['partial coverage','Python/Julia (v2)','Clojure (v1)','no retained-LOC fallback'])assert.ok(note.includes(word));}
      else if(definitions[metric][2]){const note=await page.locator('#source-size-note').textContent();for(const word of ['comments and whitespace','Unicode','cl100k_base'])assert.ok(note.includes(word));}
      const hover=await page.evaluate(async unit=>{const chart=document.querySelector('#chart'),children=[...chart.children],sample=chart.querySelector('[data-sample]');
        if(!sample)return {skipped:true};const mutations=[],observer=new MutationObserver(r=>mutations.push(...r));observer.observe(chart,{childList:true,subtree:true});
        sample.dispatchEvent(new PointerEvent('pointerover',{bubbles:true,pointerType:'mouse'}));await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        const readout=document.querySelector('#hover-details').textContent;sample.dispatchEvent(new PointerEvent('pointerout',{bubbles:true,pointerType:'mouse'}));await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));observer.disconnect();
        // Existing rollover intentionally mounts cached covariance paths in
        // this dedicated group. No base plot/sample rebuilding is permitted.
        const nonHoverStructuralMutations=mutations.filter(r=>!r.target.closest?.('.hover-spreads')&&[...r.addedNodes,...r.removedNodes].some(n=>n.nodeType===Node.ELEMENT_NODE)).length;
        return {sameChildren:children.length===chart.children.length&&children.every((n,i)=>chart.children[i]===n),sameSample:sample.isConnected,childListMutations:mutations.length,nonHoverStructuralMutations,unitVisible:readout.includes(unit)};
      },definitions[metric][1]);
      assert.ok(hover.skipped||hover.sameChildren&&hover.sameSample&&hover.nonHoverStructuralMutations===0&&hover.unitVisible,JSON.stringify(hover));
      const share=await page.evaluate(()=>benchmarkExplorer.getShareURL());await page.goto(share);await page.waitForFunction(()=>window.benchmarkExplorer);await settle(page);
      assert.equal(await page.evaluate(()=>benchmarkExplorer.getSelection().locMetric),metric);
      rows.push({width,metric,variants:want.rows.length,samples:want.samples.length,baselines:want.baselines,domain:observed.domain,hover,share_restored:true});
    }
    await page.selectOption('#loc-metric','bpe');
    await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'off',medians:'off',density:'highlight'}));await settle(page);
    const density=await page.evaluate(()=>benchmarkExplorer.getDensity());assert.ok(density.runs>0);assert.equal(await page.locator('#chart [data-sample]').count(),0);
    assert.equal(Number(await page.locator('#chart [data-layer="density"]').getAttribute('data-density-runs')),density.runs);
    await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'dim',medians:'highlight',density:'off'}));
    for(const view of ['rankings','mech','benchmark']){await page.click(`[data-view="${view}"]`);await page.selectOption('#loc-metric','bpe');await settle(page);assert.equal(await page.locator('#source-size-note').isVisible(),true);notes.push({width,view,bias_note_visible:true});}
    for(const view of ['rankings','mech','benchmark']){await page.click(`[data-view="${view}"]`);await page.selectOption('#loc-metric','logical');await settle(page);assert.equal(await page.locator('#qualified-logical-note').isVisible(),true);notes.push({width,view,logical_partial_note_visible:true});}
    if(width<=720)await page.click('#open-filters');await page.click('[data-open-language="bqn"]');await page.selectOption('#loc-metric','bpe');await settle(page);
    assert.equal(await page.locator('#source-size-note').isVisible(),true);notes.push({width,view:'language',bias_note_visible:true});
    await page.evaluate(()=>benchmarkExplorer.inspectProgram('regexredux:matlab-case-compact'));await settle(page);
    const details=await page.locator('#inspector-body').textContent();for(const text of ['comments and whitespace','Unicode','Submitted bundle','Excluded support'])assert.ok(details.includes(text));
    assert.ok(!details.includes('Previous count: undefined'));await page.click('#close-inspector');
    await page.evaluate(()=>benchmarkExplorer.inspectProgram('nbody:clojure-nbody-primitive-updates-v1'));await settle(page);
    const logicalDetails=await page.locator('#inspector-body').textContent();for(const text of ['66 application logical units','logical-source-owners.clojure-v1','Qualification report SHA-256','comments and whitespace','Unicode'])assert.ok(logicalDetails.includes(text));
    await page.click('#close-inspector');
    await page.click('[data-view="data"]');assert.equal(await page.locator('.sample-source-metrics-note').isVisible(),true);
    const dataNote=await page.locator('.sample-source-metrics-note').textContent();for(const text of ['comments and whitespace','Unicode','cl100k_base','Qualified logical units','Python/Julia v2 and Clojure v1'])assert.ok(dataNote.includes(text));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
    await page.close();
  }
  assert.deepEqual(errors,[]);
  await fs.mkdir(path.dirname(path.resolve(output)),{recursive:true});
  await fs.writeFile(output,JSON.stringify({schema:'source-axis-native-browser-qa.v1',status:'PASSED',build:manifest.version,
    browser:browser.version(),files:manifest.files,catalog_profiles:Object.keys(catalog).length,source_files:Object.keys(data.files).length,
    metrics_report_sha256:data.source_metrics.report_sha256,logical_source_units:data.logical_source_units,rows,notes,page_errors:errors,native_benchmark_processes:0},null,2)+'\n');
  console.log(JSON.stringify({status:'PASSED',build:manifest.version,choices:rows.length,note_views:notes.length,profiles:Object.keys(catalog).length,source_files:Object.keys(data.files).length,output}));
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
