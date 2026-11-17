// Run against tools/serve.py or the published metrics page with Playwright.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const base=process.env.METRICS_TEST_URL??'http://127.0.0.1:8766/metrics/';
const output=process.argv[2];
const manifest=JSON.parse(await readFile('site/public/build.json','utf8'));
const assetVersion=manifest.post_build_patches?.findLast(patch=>patch.files?.['campaigns.mjs'])?.asset_version??manifest.version;
const bundle=JSON.parse(await readFile('site/public/campaigns.json','utf8'));
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const errors=[],checks=[];
const check=(name,value)=>{assert.ok(value,name);checks.push(name);};
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const detailReady=page=>page.locator('#detail-title').waitFor();
const chooseTask=async(page,id)=>{await page.locator(`[data-case="${id}"]`).click();await detailReady(page);};

try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  const dataRequests=[],detailRequests=[];
  page.on('request',request=>{const pathname=new URL(request.url()).pathname;if(['/benchmarks/campaigns.json','/benchmarks/campaigns.json.gz'].includes(pathname))dataRequests.push(request.url());if(pathname.startsWith('/benchmarks/campaign-details/'))detailRequests.push(request.url());});
  await page.goto(base,{waitUntil:'networkidle',timeout:45000});
  await page.locator('#cases [data-case="scalar-changed"]').waitFor();
  check('catalog loads at /metrics',await page.locator('#cases tr').count()===bundle.catalog.cases.length);
  check('the initial page only loads summary data',detailRequests.length===0);
  check('task details are closed initially',!(await page.locator('#detail').isVisible()));
  check('summary data excludes program sources and observations',bundle.campaigns.every(c=>!c.environment&&c.results.every(r=>!r.source&&!r.samples&&!r.verification&&!r.measurement.schedule)));
  check('the compressed summary is under 100 KiB',(await readFile('site/public/campaigns.json.gz')).byteLength<100*1024);
  check('the browser fetches the compressed summary',dataRequests.length===1&&new URL(dataRequests[0]).pathname.endsWith('.json.gz'));
  check('latest view and all retained campaigns are selectable',await page.locator('#campaign option').count()===bundle.campaigns.length+1);
  check('the default view combines measured results',await page.locator('#campaign').inputValue()==='$latest');
  check('every default task row has a Mech measurement',await page.locator('.mech-value').evaluateAll(cells=>cells.every(c=>!c.textContent.includes('—'))));
  check('every default task has an actual measured control',await page.locator('.control-value').evaluateAll(cells=>cells.every(c=>c.querySelector('strong')&&!c.textContent.includes('not measured'))));
  check('every default row has a qualified comparison or an explicit reference',await page.locator('#cases .change').evaluateAll(cells=>cells.every(c=>/[%×]|Baseline held|Reference only/.test(c.textContent))));
  check('controls have a dedicated column',(await page.locator('thead').innerText()).includes('Control'));
  check('external controls are not execution paths',await page.locator('#backend option[value="jvm"], #backend option[value="rust"], #backend option[value="roc"], #backend option[value="libdeflate"]').count()===0);
  check('JVM is not a task row',await page.locator('[data-case="jvm"]').count()===0);
  const nbodyRow=page.locator('#cases tr').filter({has:page.locator('[data-case="nbody"]')});
  check('N-body has its measured Rust control',(await nbodyRow.locator('.control-value').innerText()).includes('Rust · Benchmarks Game #3'));
  const relatedRow=page.locator('#cases tr').filter({has:page.locator('[data-case="related-post-gen"]')});
  check('Related Post Gen retains the confirmed Mech control',(await relatedRow.locator('.control-value').innerText()).includes('Mech · IR355 baseline'));
  check('the first held checkpoint is labeled as a baseline',(await relatedRow.innerText()).includes('Baseline held'));
  await chooseTask(page,'related-post-gen');
  check('opening one task does not fetch other task details',detailRequests.length===2);
  check('detail requests use the current asset version',detailRequests.every(url=>new URL(url).searchParams.get('v')===assetVersion));
  check('Related Post Gen keeps its 13 confirmation observations',await page.locator('#detail .sample-list a').count()===13);
  check('Rust pool timing advantage is disclosed',(await page.locator('#detail').innerText()).includes('pool-before-timer'));
  await page.locator('#metric').selectOption('native_process_seconds');
  await detailReady(page);
  check('Related Post Gen whole-process comparison uses Rust',(await page.locator('#detail .control-detail').innerText()).includes('Rust · unchanged rust_con'));
  await page.locator('#metric').selectOption('$primary');
  await detailReady(page);
  check('data request uses the published asset version',dataRequests.some(url=>new URL(url).searchParams.get('v')===assetVersion));
  check('comparison navigation uses /benchmarks',await page.locator('nav a').first().getAttribute('href')==='/benchmarks/');

  await page.locator('#campaign').selectOption('2026-11-16-canonical-standard-001');
  await page.locator('#baseline').selectOption('$paired');
  await chooseTask(page,'scalar-changed');
  check('paired version comparison is visible',(await page.locator('#detail').innerText()).includes('relative to the selected baseline'));
  check('compatible history is plotted',await page.locator('#detail svg.trend').count()===1);

  for(const [label,locator] of [['raw observation','#detail .sample-list a'],['raw archive','#detail .downloads a[download]']]) {
    const link=locator.endsWith('[download]')?page.locator(locator).nth(1):page.locator(locator).first();
    const url=new URL(await link.getAttribute('href'),base);
    check(label+' stays under the shared evidence path',url.pathname.startsWith('/benchmarks/campaign-evidence/'));
    const response=await page.request.get(url.href);
    check(label+' is downloadable',response.status()===200);
    const relative=decodeURIComponent(url.pathname.slice('/benchmarks/'.length));
    const pin=manifest.external_files?.[relative];
    check(label+' matches its published hash',hash(await response.body())===(pin?.sha256??manifest.files[relative]));
    if(pin)check('archive redirect uses its immutable repository copy',new URL(response.url()).pathname===new URL(pin.url).pathname);
  }

  await page.locator('#backend').selectOption('bytecode');
  await detailReady(page);
  check('decoded artifact observations are visible',await page.locator('#detail .sample-list a').count()===3);
  await page.locator('#search').fill('matrix');
  const filtered=await page.locator('#cases tr').count();
  check('search narrows the task list',filtered>0&&filtered<bundle.catalog.cases.length);
  await page.locator('#search').fill('');
  await page.locator('#progress').selectOption('planned');
  check('unmeasured catalog placeholders do not appear as empty results',await page.locator('#cases tr').count()===0);
  await page.locator('#progress').selectOption('all');

  await page.locator('#backend').selectOption('native');
  await chooseTask(page,'native-build');
  const nativeRun=bundle.campaigns.findLast(c=>c.results.some(r=>r.backend==='native'&&r.progress==='measured'));
  check('native selection finds its measured campaign',await page.locator('#campaign').inputValue()===nativeRun.id);
  await page.locator('#metric').selectOption('object_text_bytes');
  await detailReady(page);
  check('native code size is measured',(await page.locator('#detail .measurement strong').innerText())!=='—');
  await page.locator('#campaign').selectOption('2026-11-16-native-build-001');
  await detailReady(page);
  check('failed qualification has no accepted timings',(await page.locator('#detail').innerText()).includes('No accepted timings'));
  check('failed qualification has no sample links',await page.locator('#detail .sample-list a').count()===0);

  const applicationRun=bundle.campaigns.find(c=>c.results.some(r=>r.backend==='program-jit-bytecode'&&r.progress==='measured'));
  if(applicationRun) {
    await page.locator('#backend').selectOption('program-jit-bytecode');
    await page.locator('#campaign').selectOption(applicationRun.id);
    check('historical decoded full application remains selectable',await page.locator('#campaign').inputValue()===applicationRun.id);
    await chooseTask(page,'deflate');
    check('full application chooses its checked-call measurement',(await page.locator('#detail .measurement').innerText()).includes('Checked program call'));
    check('full application has three independent forks',await page.locator('#detail .sample-list a').count()===3);
    await page.getByText('Other retained compressor observations',{exact:true}).click();
    check('older compressor controls remain inspectable',(await page.locator('#detail').innerText()).includes('d99c7b838fb05bb1047eb0c18d4d06d0f86f345d'));
    check('historical compression uses its retained level-12 reference',(await page.locator('#detail .control-detail').innerText()).includes('libdeflate · level 12'));
    check('historical timing boundary mismatch suppresses a speed ratio',(await page.locator('#detail .control-detail').innerText()).includes('Reference only'));
    await page.locator('#backend').selectOption('process-workers');
    await chooseTask(page,'concurrent');
    check('scaling chooses the whole group measurement',(await page.locator('#detail .measurement').innerText()).includes('Complete worker group'));
    check('all tasks have accepted measurements somewhere',(await page.locator('#coverage-summary').innerText()).includes(`${bundle.catalog.cases.length} of ${bundle.catalog.cases.length}`));
  }
  await page.goto(base,{waitUntil:'networkidle'});
  await chooseTask(page,'deflate');
  check('current compressor uses libdeflate level 12',(await page.locator('#detail .control-detail').innerText()).includes('libdeflate · level 12'));
  check('mixed-level and unmatched-boundary speed ratios are not displayed',(await page.locator('#detail .control-detail').innerText()).includes('Reference only'));
  check('compression size accompanies the timing reference',(await page.locator('#detail .compression-quality').innerText()).includes('Level-12 reference'));
  await page.getByText('Control measurements',{exact:true}).click();
  check('all three level-12 libdeflate samples are inspectable',await page.locator('#detail .control-samples a').count()===3);
  const libdeflateLink=await page.locator('#detail .control-samples a').first().getAttribute('href');
  const libdeflateResponse=await page.request.get(libdeflateLink);
  const libdeflateRaw=await libdeflateResponse.json();
  check('level-12 sample link resolves to its retained campaign',libdeflateResponse.status()===200&&new URL(libdeflateLink).pathname.includes('/2026-11-17-full-applications-001/'));
  check('libdeflate sample contains a real validated stream',libdeflateRaw.final_output.complete_stream===true&&libdeflateRaw.final_output.complete_input_consumption===true);
  await page.goto(base,{waitUntil:'networkidle'});
  await chooseTask(page,'scalar-changed');
  check('current scalar control retains its actual five forks',await page.locator('#detail .control-samples a').count()===5);
  const requestsBeforeClose=detailRequests.length;
  await page.locator('[data-close-detail]').click();
  check('returning to the summary closes task details',!(await page.locator('#detail').isVisible()));
  await chooseTask(page,'scalar-changed');
  check('reopening the same task uses cached details',detailRequests.length===requestsBeforeClose);
  await page.goto(base,{waitUntil:'networkidle'});
  if(output){await mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'metrics-desktop.png'),fullPage:true});}
  const shared=page.url();
  await page.reload({waitUntil:'networkidle'});
  check('shared campaign selection survives reload',page.url()===shared);

  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,deviceScaleFactor:1});
  mobile.on('pageerror',error=>errors.push(error.message));
  await mobile.goto(base,{waitUntil:'networkidle'});
  await mobile.locator('#cases [data-case="scalar-changed"]').waitFor();
  check('mobile layout stays inside the viewport',await mobile.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
  await chooseTask(mobile,'scalar-changed');
  check('mobile selection opens the task without the long summary table',!(await mobile.locator('.catalog').isVisible()));
  check('mobile selection brings the details into view',await mobile.locator('#detail-title').evaluate(node=>node.getBoundingClientRect().top>=0&&node.getBoundingClientRect().top<window.innerHeight));
  await mobile.locator('[data-close-detail]').click();
  check('mobile can return to the complete summary',await mobile.locator('.catalog').isVisible()&&await mobile.locator('#cases tr').count()===bundle.catalog.cases.length);
  await mobile.locator('#search').fill('unchanged input');
  check('mobile search remains usable',await mobile.locator('#cases tr').count()===1);
  await chooseTask(mobile,'scalar-unchanged');
  check('mobile task selection updates the details',(await mobile.locator('#detail-title').innerText()).includes('unchanged input'));
  if(output)await mobile.screenshot({path:path.join(output,'metrics-mobile.png'),fullPage:true});
  check('no browser errors',errors.length===0);
  const receipt={schema:'mech-metrics-browser.v1',status:'passed',url:base,build:manifest.version,asset_version:assetVersion,browser:browser.version(),checked_at:new Date().toISOString(),checks,errors};
  if(output)await writeFile(path.join(output,'browser.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));
} finally {await browser.close();}
