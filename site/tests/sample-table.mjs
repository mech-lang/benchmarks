import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {sampleColumns} from '../src/sample_data.mjs';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]??'site/public'),output=process.argv[3];
const live=process.env.SAMPLE_TABLE_TEST_URL;
const server=createServer(async(req,res)=>{
  try{
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+(name==='/'?'/index.html':name));
    assert.ok(file.startsWith(root+path.sep)&&(await stat(file)).isFile());
    res.writeHead(200,{'Content-Type':({'.mjs':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]??'text/plain'});
    res.end(await readFile(file));
  }catch{res.writeHead(404);res.end();}
});
if(!live)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base=live??`http://127.0.0.1:${server.address().port}/`;
const expectedBuild=process.env.EXPECTED_BUILD_VERSION;
const expectedDataset=JSON.parse(await readFile(path.join(root,'build.json'),'utf8')).files['data.json'];
const expectedReproduction=JSON.parse(await readFile(path.join(root,'build.json'),'utf8')).files['reproduction.json'];
const expectedData=JSON.parse(await readFile(path.join(root,'data.json'),'utf8'));
const expectedCatalog={...expectedData.program_inventory,...expectedData.programs};
const expectedPrograms=Object.keys(expectedCatalog).length;
const expectedObservations=Object.values(expectedCatalog).filter(p=>!p.timing_alias_of).reduce((n,p)=>n+p.samples.length,0);
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const errors=[],checks=[],performanceRows=[];
async function open(url=base,viewport={width:1440,height:1000}){
  const page=await browser.newPage({viewport,acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));
  // Hash the actual fetch stream in-page. Chrome's inspector body cache can
  // evict this 10 MB response before its ordinary JSON parsing has completed.
  await page.addInitScript(()=>{
    const original=window.fetch.bind(window);
    window.fetch=async(...args)=>{
      const response=await original(...args);
      if(new URL(response.url).pathname.endsWith('/data.json'))window.sampleDatasetDigest=response.clone().arrayBuffer()
        .then(bytes=>crypto.subtle.digest('SHA-256',bytes)).then(hash=>[...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join(''));
      if(new URL(response.url).pathname.endsWith('/reproduction.json'))window.sampleReproductionDigest=response.clone().arrayBuffer()
        .then(bytes=>crypto.subtle.digest('SHA-256',bytes)).then(hash=>[...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join(''));
      return response;
    };
  });
  await page.goto(url);
  try{await page.waitForFunction(()=>!!window.benchmarkExplorer);}
  catch(error){throw new Error(JSON.stringify({url,page_errors:errors,load_error:await page.locator('#load-error').textContent()}),{cause:error});}
  assert.equal(await page.evaluate(()=>window.sampleDatasetDigest),expectedDataset,'Exact browser-delivered dataset');
  if(expectedBuild)assert.equal(await page.locator('script[type="module"]').getAttribute('src'),`./app.mjs?v=${expectedBuild}`);
  return page;
}
async function exported(page,scope,format){
  await page.selectOption('#sample-export-scope',scope);await page.selectOption('#sample-export-format',format);
  const download=page.waitForEvent('download');await page.click('#download-samples');
  const file=await download;assert.equal(file.suggestedFilename(),`benchmark-samples-${scope}.${format}`);
  return await readFile(await file.path(),'utf8');
}
function parseCSV(text){
  const result=[];let row=[],value='',quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}
    else if(c===','&&!quoted){row.push(value);value='';}
    else if(c==='\r'&&!quoted&&text[i+1]==='\n'){row.push(value);result.push(row);row=[];value='';i++;}
    else value+=c;
  }
  return result;
}
try{
  const page=await open();assert.equal(await page.evaluate(()=>window.sampleReproductionDigest),undefined,'Ordinary chart does not fetch full reproduction records');await page.click('[data-view="data"]');
  await page.waitForFunction(()=>document.querySelector('#sample-data').hidden===false);
  const initial=await page.evaluate(()=>window.benchmarkExplorer.getSampleData());
  assert.equal(initial.total,expectedObservations);assert.equal(initial.filtered.length,expectedObservations);
  assert.equal(await page.locator('#sample-data-table tbody tr').count(),100);
  assert.equal(await page.locator('[data-sort-table="data"]').count(),sampleColumns.length);
  assert.equal(await page.locator('[data-view="data"]').textContent(),'Data');
  assert.equal(await page.locator('.chart-card').isVisible(),false);
  const observed=[];
  while(true){
    observed.push(...await page.locator('#sample-data-table tbody tr').evaluateAll(rows=>rows.map(r=>r.dataset.sampleId)));
    if(await page.locator('[data-sample-page="next"]').isDisabled())break;
    await page.click('[data-sample-page="next"]');
  }
  assert.equal(observed.length,initial.total);assert.equal(new Set(observed).size,initial.total);
  assert.deepEqual(new Set(observed),new Set(initial.filtered));checks.push('every observation reachable across pages without duplicates');
  await page.click('[data-sample-page="first"]');
  await page.click('[data-sort-table="data"][data-sort-key="seconds"]');
  const ascending=await page.locator('#sample-data-table tbody td:nth-child(6) span').evaluateAll(nodes=>nodes.map(n=>Number(n.title)));
  assert.ok(ascending.slice(1).every((v,i)=>v>=ascending[i]));
  await page.click('[data-sort-table="data"][data-sort-key="seconds"]');
  const descending=await page.locator('#sample-data-table tbody td:nth-child(6) span').evaluateAll(nodes=>nodes.map(n=>Number(n.title)));
  assert.ok(descending.slice(1).every((v,i)=>v<=descending[i]));checks.push('numeric ascending/descending sorts');
  const csv=parseCSV(await exported(page,'all','csv')),headers=csv.shift();
  assert.equal(csv.length,expectedObservations);assert.ok(csv.every(r=>r.length===headers.length));
  assert.equal(new Set(csv.map(r=>r[headers.indexOf('sample_id')])).size,expectedObservations);
  const json=JSON.parse(await exported(page,'all','json'));assert.equal(json.row_count,expectedObservations);
  assert.equal(await page.evaluate(()=>window.sampleReproductionDigest),expectedReproduction,'Exact browser-delivered reproduction records');
  assert.equal(json.rows.length,expectedObservations);assert.equal(Object.keys(json.programs).length,expectedPrograms);assert.ok(Object.keys(json.files).length>900);
  for(const r of json.rows){assert.ok(json.programs[r.program_key]);assert.ok(r.implementation_url.includes('detail.program='));
    assert.ok(r.source_sha256.every(key=>json.files[key]));}
  assert.deepEqual(csv.map(r=>Number(r[headers.indexOf('seconds')])),json.rows.map(r=>r.seconds));checks.push('complete CSV/JSON exports with exact times, links and source bundles');
  assert.ok(['normalized_application_loc','normalized_loc_rule','normalized_loc_status','qualified_formatted_loc',
    'application_utf8_bytes','application_gzip_bytes','application_cl100k_base_tokens',
    'submitted_utf8_bytes','submitted_gzip_bytes','submitted_cl100k_base_tokens',
    'excluded_support_utf8_bytes','source_metrics','source_metric_definitions'].every(h=>headers.includes(h)));
  assert.equal(json.source_metrics.catalog_sha256,expectedData.source_metrics.catalog_sha256);
  assert.equal(json.source_metrics.report_sha256,expectedData.source_metrics.report_sha256);
  for(const row of json.rows){
    const metrics=json.programs[row.program_key].source_metrics;
    assert.equal(row.normalized_application_loc,row.canonical_loc);
    assert.equal(row.normalized_loc_rule,metrics.retained_application_loc.metric);
    assert.equal(row.qualified_formatted_loc,metrics.canonical_formatted_loc.value);
    for(const scope of ['application','submitted','excluded_support'])for(const metric of ['utf8_bytes','gzip_bytes','cl100k_base_tokens'])
      assert.equal(row[scope+'_'+metric],metrics[scope][metric]);
    assert.deepEqual(row.source_metrics,metrics);
  }
  checks.push('bound source scopes, qualified formatted gaps and retained normalized rules in CSV/JSON');
  assert.ok(['authorship','ai_model','license','license_status','authorship_details'].every(h=>headers.includes(h)));
  for(const row of json.rows){assert.ok(row.authorship_details);assert.deepEqual(row.authorship_details.source_sha256,json.programs[row.program_key].files);}
  for(const row of json.rows){assert.ok(row.reproduction);assert.deepEqual(row.reproduction.source_sha256,row.source_sha256);assert.equal(row.reproduction.replay_verified,false);}
  assert.ok(['original_sources','toolchain_version','platform','recorded_at','reproduction_status','reproduction'].every(h=>headers.includes(h)));
  const typed=json.rows.find(r=>r.implementation==='typescript-fasta-v1');
  assert.ok(typed.original_sources.some(s=>s.url.endsWith('/program/fasta-node-1.html')));
  assert.ok(typed.toolchain_version.includes('24.19.0'));
  await page.fill('#sample-data-search',typed.implementation);
  await page.locator('.sample-reproduction').first().click();
  assert.equal(await page.locator('#reproduction-details').getAttribute('open'),'');
  const recipe=await page.locator('.source-reproduction').textContent();
  assert.ok(recipe.includes('24.19.0')&&recipe.includes('25,000,000')&&recipe.includes('Timed command'));
  await page.click('#close-inspector');
  checks.push('source-bound reproduction exports, specific original source, recorded versions, input and accessible recipe');
  if(process.env.EXPECTED_LOCAL_PREDECESSORS==='1'){
    const prolog=json.rows.find(r=>r.implementation==='prolog-fasta-compact');
    assert.ok(prolog);assert.equal(prolog.authorship_details.origin_status,'unresolved');
    assert.deepEqual(prolog.authorship_details.parent_programs,['fasta:nim-fasta-compact']);
    const parent=prolog.authorship_details.parent_sources[0];
    assert.ok(parent.url.includes('/blob/c95f900435aca5ae51030eabeffae2e5dc9a2fc2/'));
    assert.ok(prolog.original_sources.some(r=>r.url===parent.url));
    await page.fill('#sample-data-search',prolog.implementation);
    const sourceLinks=await page.locator('#sample-data-table tbody tr').first().locator('a').evaluateAll(nodes=>nodes.map(n=>n.href));
    assert.ok(sourceLinks.includes(parent.url));
    assert.ok((await page.locator('#sample-data-table tbody tr').first().textContent()).includes('Earlier origin unverified'));
    await page.locator('[data-sample-program]').first().click();
    const inspector=await page.locator('.source-authorship').textContent();
    assert.ok(inspector.includes('local predecessor')&&inspector.includes('Original implementation source not established'));
    assert.ok((await page.locator('.source-authorship a').evaluateAll(nodes=>nodes.map(n=>n.href))).includes(parent.url));
    await page.click('#close-inspector');
    checks.push('hash-bound local predecessors in table, inspector and exports without erasing earlier-origin gaps');
  }
  if(process.env.EXPECTED_MOJO_LINEAGE==='1'){
    const mojo=json.rows.find(r=>r.implementation==='mojo-spectralnorm-small');
    assert.ok(mojo);assert.equal(mojo.authorship_details.origin_status,'cited');
    assert.equal(mojo.license_status,'partial');
    const upstream=mojo.original_sources.find(r=>r.url.includes('faster-python-bench/blob/')&&r.url.endsWith('/spectral_norm.mojo'));
    assert.ok(upstream?.upstream_sha256);
    const earlier=mojo.original_sources.find(r=>r.url.endsWith('/program/spectralnorm-python3-6.html'));
    assert.equal(earlier?.via_source,upstream.url);
    await page.fill('#sample-data-search',mojo.implementation);await page.locator('[data-sample-program]').first().click();
    const links=await page.locator('.source-authorship a').evaluateAll(nodes=>nodes.map(n=>n.href));
    assert.ok(links.includes(upstream.url)&&links.includes(earlier.url));
    assert.ok((await page.locator('.source-authorship').textContent()).includes('Upstream license not established'));
    await page.click('#close-inspector');
    checks.push('specific Mojo source and earlier Python reference preserved with unresolved upstream license');
  }
  if(process.env.EXPECTED_LUAU_PROGRAMS){
    const programs=Object.values(json.programs).filter(p=>['luau','luau-jit'].includes(p.language));
    assert.equal(programs.length,Number(process.env.EXPECTED_LUAU_PROGRAMS));
    for(const language of ['luau','luau-jit']){
      const rows=json.rows.filter(r=>r.language_key===language);
      assert.equal(new Set(rows.map(r=>r.benchmark_key)).size,10);
      assert.equal(rows.length,33);
      assert.ok(rows.every(r=>r.toolchain_version.includes('0.743')));
      assert.ok(rows.every(r=>r.authorship_details.kind==='ai-adapted'));
      assert.ok(rows.every(r=>r.original_sources.some(s=>s.url.includes('/program/')&&s.url.includes('-lua-'))));
      assert.ok(rows.every(r=>r.source_sha256.some(s=>json.files[s].name==='Host.cpp')));
    }
    const guarded=json.rows.find(r=>r.implementation==='luau-jit-revcomp-guarded-v1');
    await page.fill('#sample-data-search',guarded.implementation);
    await page.locator('[data-sample-program]').first().click();
    assert.ok((await page.locator('.source-authorship').textContent()).includes('AI adapted'));
    assert.ok((await page.locator('.source-authorship a').evaluateAll(nodes=>nodes.map(n=>n.href))).some(url=>url.includes('/program/revcomp-lua-2.html')));
    if(guarded.source_accounting){
      assert.equal(guarded.canonical_loc,52);
      assert.equal(guarded.source_accounting.previous_loc,160);
      assert.ok((await page.locator('.source-accounting').textContent()).includes('108 normalized LOC'));
      await page.selectOption('#detail-file','1');
      assert.ok((await page.locator('#source-code').textContent()).includes('Luau::compile'));
      assert.ok((await page.locator('#detail-file option:checked').textContent()).includes('support (excluded)'));
    }
    await page.click('#close-inspector');
    checks.push('both Luau modes retain ten workloads, samples, attribution, versions and inspectable host with corrected application LOC');
  }
  if(json.programs['pidigits:pidigits-rust-3']?.source_accounting){
    const rust=json.rows.find(r=>r.program_key==='pidigits:pidigits-rust-3');
    assert.equal(rust.canonical_loc,82);
    assert.equal(rust.source_accounting.previous_loc,175);
    await page.fill('#sample-data-search',rust.implementation);
    await page.locator('[data-sample-program]').first().click();
    const accounting=await page.locator('.source-accounting').textContent();
    assert.ok(accounting.includes('82 normalized application LOC')&&accounting.includes('97–199'));
    assert.ok((await page.locator('#source-code').textContent()).includes('extract_digit'));
    await page.click('#close-inspector');
    checks.push('embedded Rust GMP wrapper is separated while source and workload helpers remain available');
  }
  for(const [key,loc] of [['nbody:clojure-nbody-compact-hot-aset-v1',109],['spectralnorm:prolog-spectralnorm-blocks8-v1',128]]){
    const rows=json.rows.filter(r=>r.program_key===key);if(!rows.length)continue;
    assert.equal(rows.length,3);assert.ok(rows.every(r=>r.canonical_loc===loc));
    await page.fill('#sample-data-search',rows[0].implementation);
    await page.locator('[data-sample-program]').first().click();
    const accounting=await page.locator('.source-accounting').textContent();
    assert.ok(accounting.includes(`${loc} normalized application LOC`));
    assert.ok(!accounting.includes('undefined'),'An independently counted new source has no previous LOC to display.');
    if(key.startsWith('nbody:'))assert.ok((await page.locator('.logical-source-units').textContent()).includes('63 application logical units'));
    await page.click('#close-inspector');
  }
  checks.push('new compact Clojure and parallel Prolog profiles retain three independent observations and qualified source-count displays');
  const published=json.rows.find(r=>r.language_key==='c'&&r.authorship_details.kind==='upstream');
  await page.fill('#sample-data-search',published.implementation);
  await page.locator('[data-sample-program]').first().click();
  assert.ok((await page.locator('.source-authorship').textContent()).includes('Published'));
  assert.ok(await page.locator('.source-authorship a').filter({hasText:'BSD-3-Clause'}).count());
  assert.ok((await page.locator('.source-authorship').textContent()).includes(published.authorship_details.attribution_notices[0].text));
  await page.click('#close-inspector');
  const generated=json.rows.find(r=>r.language_key==='lean4'&&r.authorship_details.ai.models.length);
  await page.fill('#sample-data-search',generated.implementation);await page.locator('[data-sample-program]').first().click();
  assert.ok((await page.locator('.source-authorship').textContent()).includes(generated.authorship_details.ai.models[0]));
  assert.ok(await page.locator('.source-authorship a').filter({hasText:'Apache-2.0'}).count());await page.click('#close-inspector');
  const partial=json.rows.find(r=>r.license_status==='partial');await page.fill('#sample-data-search',partial.implementation);
  assert.ok((await page.locator('#sample-data-table tbody .sample-column-license').first().textContent()).includes('unverified'));
  await page.fill('#sample-data-search','gpt-6.1-sol');
  assert.ok(await page.locator('#sample-data-table tbody tr').count());
  await page.click('[data-sort-table="data"][data-sort-key="authorship"]');
  const provenanceURL=await page.evaluate(()=>window.benchmarkExplorer.getShareURL()),provenancePage=await open(provenanceURL);
  assert.equal((await provenancePage.evaluate(()=>window.benchmarkExplorer.getViewState())).tableSort.data.key,'authorship');
  assert.equal(await provenancePage.locator('#sample-data-search').inputValue(),'gpt-6.1-sol');await provenancePage.close();
  await page.fill('#sample-data-search','');await page.click('[data-sort-table="data"][data-sort-key="seconds"]');await page.click('[data-sort-table="data"][data-sort-key="seconds"]');
  checks.push('authorship/model/license columns, export metadata, original author notices, partial licenses and shareable provenance sort');
  const before=await page.evaluate(()=>document.querySelector('#chart').innerHTML);
  let start=Date.now();await page.fill('#sample-data-search','Lean n-body');
  await page.waitForFunction(()=>document.querySelectorAll('#sample-data-table tbody tr').length===9);
  performanceRows.push({operation:`filter ${expectedObservations} observations`,wall_ms:Date.now()-start});
  assert.equal(await page.evaluate(()=>document.querySelector('#chart').innerHTML),before);
  assert.equal((await page.evaluate(()=>window.benchmarkExplorer.getSampleData())).filtered.length,9);
  assert.equal(parseCSV(await exported(page,'all','csv')).length-1,expectedObservations);
  const filtered=JSON.parse(await exported(page,'filtered','json'));assert.equal(filtered.row_count,9);
  assert.ok(filtered.rows.every(r=>r.language_key==='lean4'&&r.benchmark_key==='nbody'));
  await page.locator('[data-select-sample]').nth(0).check();await page.locator('[data-select-sample]').nth(2).check();
  const chosen=(await page.evaluate(()=>window.benchmarkExplorer.getSampleData())).selected;
  assert.equal(chosen.length,2);assert.deepEqual(new Set(JSON.parse(await exported(page,'selected','json')).rows.map(r=>r.sample_id)),new Set(chosen));
  await page.fill('#sample-data-search','absent-no-results-xyz');
  assert.equal(await page.locator('#sample-data-table tbody tr').count(),0);assert.equal(await page.locator('#sample-data-empty').isVisible(),true);
  assert.equal(JSON.parse(await exported(page,'selected','json')).rows.length,2);
  await page.selectOption('#sample-export-scope','filtered');assert.equal(await page.locator('#download-samples').isDisabled(),true);
  checks.push('search, empty state, selection persistence across filters and exact selection exports');
  await page.fill('#sample-data-search','Lean');await page.selectOption('#sample-page-size','50');
  await page.click('[data-sample-page="next"]');
  const url=await page.evaluate(()=>window.benchmarkExplorer.getShareURL());const restored=await open(url);
  assert.equal(await restored.locator('#sample-data-search').inputValue(),'Lean');
  assert.equal(await restored.locator('#sample-page-size').inputValue(),'50');
  const restoredState=await restored.evaluate(()=>window.benchmarkExplorer.getViewState());
  assert.equal(restoredState.dataPage,1);assert.equal(restoredState.tableSort.data.direction,-1);
  assert.deepEqual(new Set(restoredState.dataSelected),new Set(chosen));await restored.close();checks.push('fresh-context URL restores query, page, sort and selected rows');
  await page.click('#reset-sample-data');
  await page.click('#select-filtered-samples');
  const allURL=await page.evaluate(()=>window.benchmarkExplorer.getShareURL()),allRestored=await open(allURL);
  assert.equal((await allRestored.evaluate(()=>window.benchmarkExplorer.getSampleData())).selected.length,expectedObservations);await allRestored.close();
  await page.click('#clear-selected-samples');
  checks.push(`full ${expectedObservations}-row selection survives a fresh browser URL`);
  assert.equal((await page.evaluate(()=>window.benchmarkExplorer.getSampleData())).filtered.length,expectedObservations);
  await page.fill('#sample-data-search','uiua binary');
  const alias=page.locator('[data-sample-program="binarytrees:binarytrees-uiua-optimized"]').first();await alias.click();
  assert.equal(await page.locator('#inspector').isVisible(),true);assert.equal(await page.locator('#detail-program').inputValue(),'binarytrees:binarytrees-uiua-optimized');
  assert.equal(await page.locator('#source-code').textContent().then(Boolean),true);
  assert.ok(await page.locator('.timing-alias').isVisible());
  const sourceURL=await page.evaluate(()=>window.benchmarkExplorer.getShareURL()),fresh=await open(sourceURL);
  assert.equal(await fresh.locator('#inspector').isVisible(),true);assert.equal(await fresh.locator('#detail-program').inputValue(),'binarytrees:binarytrees-uiua-optimized');
  await fresh.close();await page.click('#close-inspector');checks.push('timing-alias implementation links and source inspector round trips');
  await page.click('#reset-sample-data');await page.fill('#sample-data-search','Lean nbody');
  const link=await page.locator('[data-sample-program]').first().getAttribute('href'),linked=await open(link);
  assert.equal(await linked.locator('#inspector').isVisible(),true);assert.equal((await linked.evaluate(()=>window.benchmarkExplorer.getViewState())).view,'data');
  const currentProgram=await linked.locator('#detail-program').inputValue();await linked.click('[data-step-program="1"]');
  assert.notEqual(await linked.locator('#detail-program').inputValue(),currentProgram);await linked.close();checks.push('standalone source links and cross-implementation previous/next navigation');
  const mobile=await open(base+'#v=1&view=data',{width:390,height:844});
  assert.equal(await mobile.locator('#sample-data').isVisible(),true);
  const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert.equal(overflow,false);
  await mobile.click('#open-filters');await mobile.click('#only-mech');await mobile.click('#close-filters');
  assert.ok((await mobile.evaluate(()=>window.benchmarkExplorer.getSampleData())).filtered.length<expectedObservations);
  assert.ok((await mobile.locator('#sample-data-table tbody td:nth-child(2)').allTextContents()).every(v=>v.includes('Mech')));
  await mobile.screenshot({path:'/private/tmp/benchmark-sample-table-mobile.png',fullPage:false});
  await page.fill('#sample-data-search','Lean');await page.screenshot({path:'/private/tmp/benchmark-sample-table-desktop.png',fullPage:false});
  await mobile.close();await page.close();checks.push('mobile drawer filtering, horizontal table scrolling and no page overflow');
  assert.deepEqual(errors,[]);
  const report={schema:'benchmark-sample-table-browser.v1',status:'PASSED',url:base,expected_build:expectedBuild??null,dataset_sha256:expectedDataset,reproduction_sha256:expectedReproduction,checks,observations:expectedObservations,performance:performanceRows,page_errors:errors,benchmark_executions:0};
  if(output)await writeFile(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();if(!live)await new Promise(resolve=>server.close(resolve));}
