import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]??'site/public'),output=process.argv[3];
const live=process.env.VIEW_LINK_TEST_URL;
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
const expectedBuild=process.env.EXPECTED_BUILD_VERSION,expectedLeanPrograms=process.env.EXPECTED_LEAN_PROGRAMS;
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const rows=[],errors=[];
const settle=page=>page.evaluate(async()=>{await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
const normalize=view=>{
  for(const key of ['benchmarks','languages','ellipses','disabled','collapsedFamilies'])view[key].sort();
  for(const category of ['traits','benchmarkFilters'])for(const values of Object.values(view[category]))values.sort();
  if(!view.inspectorOpen)delete view.detail;
  if(view.languageTab)normalize(view.languageTab);
  return view;
};
const snapshot=async page=>({state:normalize(await page.evaluate(()=>window.benchmarkExplorer.getViewState())),
  content:await page.evaluate(()=>({title:document.querySelector('.chart-card').hidden?null:document.querySelector('#chart-title').textContent,
    overview:document.querySelector('#language-overview').hidden?null:document.querySelector('#language-overview-summary').textContent,
    rows:document.querySelector('#language-results').hidden?null:document.querySelectorAll('#language-timings tbody tr').length,
    source:document.querySelector('#inspector').open?document.querySelector('#source-code')?.textContent:null,
    sourceFile:document.querySelector('#inspector').open?document.querySelector('#detail-file')?.value:null,
    samples:document.querySelector('.chart-card').hidden?null:document.querySelectorAll('#chart [data-sample]').length,
    rankings:document.querySelector('#median-rankings').hidden?null:document.querySelector('#median-rankings-summary').textContent,
    languageTab:document.querySelector('#language-view-tab').hidden?null:document.querySelector('#language-view-tab').textContent,
    domain:document.querySelector('.chart-card').hidden?null:window.benchmarkExplorer.getDomains()}))});
async function open(url=base,viewport={width:1280,height:900}){
  const page=await browser.newPage({viewport});page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url,{waitUntil:'load'});await page.waitForFunction(()=>!!window.benchmarkExplorer);await settle(page);return page;
}
async function roundtrip(page,name,{mobile=false}={}){
  await settle(page);await page.waitForTimeout(380);
  const before=await snapshot(page),url=page.url();
  assert.equal(await page.evaluate(()=>window.benchmarkExplorer.getShareURL()),url,name+' address bar updates automatically');
  const fresh=await open(url,mobile?{width:390,height:844}:undefined);
  assert.deepEqual(await snapshot(fresh),before,name+' restores in a fresh browser context');
  assert.equal(new URL(fresh.url()).hash,new URL(url).hash,name+' canonical URL');
  assert.ok(await fresh.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal page overflow');
  if(before.state.languageTab){
    await fresh.locator('[data-view="language"]').click();await settle(fresh);
    const tab=normalize(await fresh.evaluate(()=>window.benchmarkExplorer.getViewState()));
    assert.equal(tab.languageFocus.selectionKey,before.state.languageTab.languageFocus.selectionKey,'Saved language tab remains usable');
    assert.deepEqual(tab.benchmarks,before.state.languageTab.benchmarks,'Saved tab keeps its benchmark selection');
  }
  rows.push({name,url,view:before.state.view,language:before.state.languageFocus?.selectionKey??null,benchmarks:before.state.benchmarks,inspectorOpen:before.state.inspectorOpen});
  await fresh.close();return url;
}
try{
  const page=await open();
  const actualBuild=await page.locator('script[type="module"]').getAttribute('src');
  if(expectedBuild)assert.equal(new URL(actualBuild,base).searchParams.get('v'),expectedBuild,'Expected deployed build');
  await roundtrip(page,'default');
  if(process.env.EXPECTED_LUAU_PROGRAMS){
    for(const [key,mobile] of [['luau',false],['luau-jit',true]]){
      const luau=await open(base+'#v=1&view=language&language='+key+'&variant='+key,mobile?{width:390,height:844}:undefined);
      const summary=await luau.locator('#language-overview-summary').textContent();
      assert.match(summary,/10\/10 selected benchmarks/);
      assert.match(summary,new RegExp(`\\b${Number(process.env.EXPECTED_LUAU_PROGRAMS)/2} programs\\b`));
      assert.match(summary,/33 recorded runs/);
      await roundtrip(luau,key+' complete language page',{mobile});
      await luau.locator('#reset').click();await settle(luau);
      assert.equal((await snapshot(luau)).state.view,'language');
      await luau.close();
    }
  }
  if(process.env.EXPECTED_ZJIT_PROGRAMS){
    const zjit=await open(base+'#v=1&view=language&language=ruby&variant=ruby-zjit');
    const summary=await zjit.locator('#language-overview-summary').textContent();
    assert.match(summary,/10\/10 selected benchmarks/);
    assert.match(summary,new RegExp(`\\b${process.env.EXPECTED_ZJIT_PROGRAMS} programs\\b`));
    assert.match(summary,/57 recorded runs/);
    await roundtrip(zjit,'Ruby ZJIT full language page');
    await zjit.close();
  }
  await page.locator('[data-open-language="lean4"]').click();
  const leanSummary=await page.locator('#language-overview-summary').textContent();
  if(expectedLeanPrograms)assert.match(leanSummary,new RegExp(`\\b${Number(expectedLeanPrograms)} programs\\b`),'Expected measured Lean catalog');
  await page.locator('#no-benchmarks').click();
  await page.locator('[data-benchmark="nbody"]').check();
  await page.locator('[data-benchmark="spectralnorm"]').check();
  await page.locator('#fast-profile').uncheck();
  await page.locator('#show-samples').selectOption('off');
  await page.locator('#show-medians').selectOption('off');
  await page.locator('#show-density').selectOption('highlight');
  await page.locator('#show-global').check();
  await page.locator('#chart-axes').selectOption('samples');
  const hero=await roundtrip(page,'Lean with two active benchmarks and density/global layers');
  await roundtrip(page,'Same language selection on mobile',{mobile:true});
  await page.locator('[data-view="summary"]').click();
  await roundtrip(page,'Summary with a saved language tab and two active benchmarks');
  await page.locator('[data-view="language"]').click();await settle(page);
  assert.deepEqual((await snapshot(page)).state.benchmarks,['nbody','spectralnorm']);
  await page.reload();await page.waitForFunction(()=>!!window.benchmarkExplorer);await settle(page);
  assert.equal(new URL(page.url()).hash,new URL(hero).hash,'Reload retains active benchmarks');
  await page.locator('#reset').click();await settle(page);
  assert.equal((await snapshot(page)).state.view,'language','Reset stays in language tab');
  assert.equal((await snapshot(page)).state.benchmarks.length,10);
  await page.locator('#overview-benchmark').selectOption('regexredux');
  await page.locator('#overview-inspect').click();
  await page.locator('#detail-file').selectOption('1');
  await page.locator('[data-sort-table="timings"][data-sort-key="elapsed"]').click();
  await roundtrip(page,'Selected program, helper source and timing sort');
  await page.locator('#overview-comparison-language').selectOption('rust');
  await page.locator('#overview-compare').click();
  await roundtrip(page,'Language benchmark comparison');
  await page.locator('#return-language-overview').click();await settle(page);
  await page.locator('[data-view="summary"]').click();
  await page.locator('#no-languages').click();
  for(const key of ['rust','lean4','mech'])await page.locator(`input[data-language="${key}"]`).check();
  await page.locator('[data-trait-option="typing:static"]').check();
  await page.locator('[data-benchmark-facet="resource:compute"]').check();
  await page.evaluate(()=>window.benchmarkExplorer.setReleaseWindow(1980,2026));
  await page.locator('[data-spread="rust"]').click();
  await page.locator('[data-toggle-family="mech"]').click();
  await page.locator('[data-sort-table="comparison"][data-sort-key="fastest"]').click();
  await page.locator('#toggle-benchmark-filters').click();
  await roundtrip(page,'Language and benchmark facets, years, ellipses, collapsed controls and sort');
  await page.locator('[data-view="rankings"]').click();
  await page.locator('#loc-metric').selectOption('formatted');
  await roundtrip(page,'Rankings and formatted LOC');
  await page.locator('[data-view="summary"]').click();
  await page.locator('#reset').click();
  await page.locator('[data-open-family="mech"]').click();
  await page.locator('#overview-variant').selectOption('mech-jit');
  await page.locator('#overview-benchmark').selectOption('spectralnorm');
  await page.locator('#overview-inspect').click();
  await roundtrip(page,'Language family, execution variant and program');
  await page.locator('[data-view="summary"]').click();await page.locator('#reset').click();
  await page.locator('[data-view="benchmark"]').click();
  await page.locator('#focused-benchmark').selectOption('nbody');
  await page.locator('#chart [data-sample]').first().click({force:true});
  await page.locator('#include-program').uncheck();
  await roundtrip(page,'Single benchmark with an excluded program');
  await page.locator('#close-inspector').click();
  await page.locator('#no-benchmarks').click();await page.locator('#no-languages').click();
  await roundtrip(page,'Empty benchmark and language sets');
  await page.locator('#reset').click();await settle(page);
  const prior=await snapshot(page);
  await page.locator('[data-open-language="lean4"]').click();await settle(page);
  const next=await snapshot(page);
  await page.goBack();await settle(page);assert.deepEqual(await snapshot(page),prior,'Back restores prior view');
  await page.goForward();await settle(page);assert.deepEqual(await snapshot(page),next,'Forward restores language view');
  await page.locator('[data-view="summary"]').click();await page.locator('#reset').click();await settle(page);
  await page.evaluate(()=>window.benchmarkExplorer.setReleaseWindow(1990,2026));
  const slider=await snapshot(page);
  await page.locator('[data-open-language="lean4"]').click();await settle(page);
  await page.goBack();await settle(page);assert.deepEqual(await snapshot(page),slider,'Navigation flushes a pending year-window URL');
  await page.context().grantPermissions(['clipboard-read','clipboard-write']);
  await page.locator('#copy-view-link').click();
  await page.waitForFunction(()=>document.querySelector('#copy-view-status').textContent==='Link copied');
  assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),page.url());
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Denied');}}}));
  await page.locator('#copy-view-link').click();
  await page.waitForFunction(()=>!document.querySelector('#view-link-fallback').hidden);
  assert.equal(await page.locator('#view-link-fallback').inputValue(),page.url());
  const malformed=await open(base+'#v=1&view=language&language=constructor&family=1&inspect=1&detail.program=__proto__&densityMode=no&traits=__proto__:x');
  assert.equal((await snapshot(malformed)).state.view,'summary');await malformed.close();
  await page.close();assert.deepEqual(errors,[]);
  const report={schema:'benchmark-view-link-browser-regression.v1',status:'PASSED',url:base,actual_build:actualBuild,initial_lean_summary:leanSummary,cases:rows,
    checks:['fresh-context round trips','desktop/mobile','reload','language reset','comparison','source/helper selection','filters','layers','axes','years','sorts','empty selections','Back/Forward','clipboard','clipboard fallback','malformed URL validation'],page_errors:errors,benchmark_executions:0};
  if(output)await writeFile(output,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,cases:rows.length,page_errors:errors}));
}finally{await browser.close();if(!live)await new Promise(resolve=>server.close(resolve));}
