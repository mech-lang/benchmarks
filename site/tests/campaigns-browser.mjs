// Run against tools/serve.py or the published metrics page with Playwright.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const base=process.env.METRICS_TEST_URL??'http://127.0.0.1:8766/metrics/';
const output=process.argv[2];
const manifest=JSON.parse(await readFile('site/public/build.json','utf8'));
const bundle=JSON.parse(await readFile('site/public/campaigns.json','utf8'));
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const errors=[],checks=[];
const check=(name,value)=>{assert.ok(value,name);checks.push(name);};
const hash=raw=>createHash('sha256').update(raw).digest('hex');

try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  const dataRequests=[];
  page.on('request',request=>{if(new URL(request.url()).pathname==='/benchmarks/campaigns.json')dataRequests.push(request.url());});
  await page.goto(base,{waitUntil:'networkidle',timeout:45000});
  await page.locator('#cases [data-case="scalar-changed"]').waitFor();
  check('catalog loads at /metrics',await page.locator('#cases tr').count()===bundle.catalog.cases.length);
  check('all retained campaigns are selectable',await page.locator('#campaign option').count()===bundle.campaigns.length);
  check('data request uses the published build version',dataRequests.some(url=>new URL(url).searchParams.get('v')===manifest.version));
  check('comparison navigation uses /benchmarks',await page.locator('nav a').first().getAttribute('href')==='/benchmarks/');

  await page.locator('#campaign').selectOption('2026-11-16-canonical-standard-001');
  await page.locator('#baseline').selectOption('$paired');
  await page.locator('[data-case="scalar-changed"]').click();
  check('paired version comparison is visible',(await page.locator('#detail').innerText()).includes('relative to the selected baseline'));
  check('compatible history is plotted',await page.locator('#detail svg.trend').count()===1);

  for(const [label,locator] of [['raw observation','#detail .sample-list a'],['raw archive','#detail .downloads a[download]']]) {
    const link=locator.endsWith('[download]')?page.locator(locator).nth(1):page.locator(locator).first();
    const url=new URL(await link.getAttribute('href'),base);
    check(label+' stays under the shared evidence path',url.pathname.startsWith('/benchmarks/campaign-evidence/'));
    const response=await page.request.get(url.href);
    check(label+' is downloadable',response.status()===200);
    const relative=decodeURIComponent(url.pathname.slice('/benchmarks/'.length));
    check(label+' matches its published hash',hash(await response.body())===manifest.files[relative]);
  }

  await page.locator('#backend').selectOption('bytecode');
  check('decoded artifact observations are visible',await page.locator('#detail .sample-list a').count()===3);
  await page.locator('#search').fill('matrix');
  const filtered=await page.locator('#cases tr').count();
  check('search narrows the task list',filtered>0&&filtered<bundle.catalog.cases.length);
  await page.locator('#search').fill('');
  await page.locator('#progress').selectOption('planned');
  check('planned work is separate from measured results',await page.locator('#cases tr').count()===bundle.catalog.cases.filter(c=>c.progress==='planned').length);
  if(bundle.catalog.cases.some(c=>c.progress==='planned')) {
    await page.locator('#cases button').first().click();
    check('planned tasks have no timing samples',await page.locator('#detail .sample-list a').count()===0);
  } else check('all named tasks now have implementations',await page.locator('#cases tr').count()===0);
  await page.locator('#progress').selectOption('all');

  await page.locator('#backend').selectOption('native');
  check('native selection finds its measured campaign',await page.locator('#campaign').inputValue()==='2026-11-16-native-build-003');
  await page.locator('#metric').selectOption('object_text_bytes');
  check('native code size is measured',(await page.locator('#detail .measurement strong').innerText())!=='—');
  await page.locator('#campaign').selectOption('2026-11-16-native-build-001');
  check('failed qualification has no accepted timings',(await page.locator('#detail').innerText()).includes('No accepted timings'));
  check('failed qualification has no sample links',await page.locator('#detail .sample-list a').count()===0);

  const applicationRun=bundle.campaigns.find(c=>c.results.some(r=>r.backend==='program-jit-bytecode'&&r.progress==='measured'));
  if(applicationRun) {
    await page.locator('#backend').selectOption('program-jit-bytecode');
    check('decoded full application selects its measured run',await page.locator('#campaign').inputValue()===applicationRun.id);
    await page.locator('[data-case="deflate"]').click();
    check('full application chooses its checked-call measurement',await page.locator('#metric').inputValue()==='native_program_call_seconds');
    check('full application has three independent forks',await page.locator('#detail .sample-list a').count()===3);
    await page.locator('#backend').selectOption('roc');
    check('Roc uses its own complete-call measurement',await page.locator('#metric').inputValue()==='control_call_seconds');
    await page.getByText('Compiler and environment',{exact:true}).click();
    check('Roc compiler provenance is not the Mech worker',(await page.locator('#detail').innerText()).includes('d99c7b838fb05bb1047eb0c18d4d06d0f86f345d'));
    await page.locator('#backend').selectOption('jvm');
    check('JVM chooses whole-process time',await page.locator('#metric').inputValue()==='native_process_seconds');
    await page.getByText('Compiler and environment',{exact:true}).click();
    check('JVM provenance names the real runtime',(await page.locator('#detail').innerText()).includes('OpenJDK'));
    await page.locator('#backend').selectOption('process-workers');
    check('scaling chooses the whole group measurement',await page.locator('#metric').inputValue()==='worker_group_process_seconds');
    check('all tasks have accepted measurements somewhere',(await page.locator('#coverage-summary').innerText()).includes(`${bundle.catalog.cases.length} of ${bundle.catalog.cases.length}`));
  }
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
  await mobile.locator('#search').fill('unchanged input');
  check('mobile search remains usable',await mobile.locator('#cases tr').count()===1);
  await mobile.locator('[data-case="scalar-unchanged"]').click();
  check('mobile task selection updates the details',(await mobile.locator('#detail-title').innerText()).includes('unchanged input'));
  if(output)await mobile.screenshot({path:path.join(output,'metrics-mobile.png'),fullPage:true});
  check('no browser errors',errors.length===0);
  const receipt={schema:'mech-metrics-browser.v1',status:'passed',url:base,build:manifest.version,browser:browser.version(),checked_at:new Date().toISOString(),checks,errors};
  if(output)await writeFile(path.join(output,'browser.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));
} finally {await browser.close();}
