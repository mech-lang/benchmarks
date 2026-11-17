import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const base=process.env.PROJECT_TEST_URL??'http://127.0.0.1:8766/metrics/project/';
const output=process.argv[2],manifest=JSON.parse(await readFile('site/public/build.json','utf8'));
const bundle=JSON.parse(await readFile('site/public/project.json','utf8'));
const candidate=bundle.snapshots.find(s=>s.track==='compiler-candidate');
const main=bundle.snapshots.find(s=>s.track==='default-branch');
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const checks=[],errors=[];
const check=(name,value)=>{assert.ok(value,name);checks.push(name);};
const hash=raw=>createHash('sha256').update(raw).digest('hex');
try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',error=>errors.push(error.message));
  const requested=[];page.on('request',request=>{if(new URL(request.url()).pathname==='/benchmarks/project.json')requested.push(request.url());});
  await page.goto(base,{waitUntil:'networkidle',timeout:45000});
  await page.locator('#project-stats strong').first().waitFor();
  check('three explicit project tracks load',await page.locator('#track option').count()===3);
  check('default track matches the benchmarked compiler',await page.locator('#track').inputValue()==='compiler-candidate');
  check('revision is visible',(await page.locator('#revision').innerText()).includes(candidate.revision.slice(0,12)));
  check('source count matches the retained inventory',await page.locator('#project-stats strong').first().innerText()===candidate.summary.physical_lines.toLocaleString('en-US'));
  check('data is versioned with the page build',requested.some(url=>new URL(url).searchParams.get('v')===manifest.version));
  check('coverage remains unavailable without an execution report',(await page.locator('#delivery').innerText()).includes('Line coverage · no retained report'));
  check('CI workflows are visible',await page.locator('#ci-runs tr').count()===candidate.github.ci.runs.length);
  check('first observation does not invent historical data',(await page.locator('#project-history').innerText()).includes('First snapshot'));
  check('language counts are visible',await page.locator('#languages tr').count()===Object.keys(candidate.summary.languages).length);
  for(const [index,label] of [[0,'source inventory'],[1,'GitHub evidence']]){
    const url=new URL(await page.locator('#project-downloads a').nth(index).getAttribute('href'));
    check(label+' uses the shared evidence directory',url.pathname.startsWith('/benchmarks/project-evidence/'));
    const response=await page.request.get(url.href);check(label+' is downloadable',response.status()===200);
    const raw=await response.body(),relative=decodeURIComponent(url.pathname.slice('/benchmarks/'.length));
    check(label+' has its published hash',hash(raw)===manifest.files[relative]);
    if(index===0){const inventory=JSON.parse(raw);check('full download includes every source file',inventory.files.length===candidate.summary.files);}
    else {const responses=JSON.parse(gunzipSync(raw));check('original API bytes match each retained response hash',responses.length>0&&responses.every(row=>hash(Buffer.from(row.raw_json))===row.sha256));}
  }
  if(output){await mkdir(output,{recursive:true});await page.screenshot({path:path.join(output,'project-desktop.png'),fullPage:true});}
  await page.locator('#track').selectOption('default-branch');
  check('switching branches changes the source revision',(await page.locator('#revision').innerText()).includes(main.revision.slice(0,12)));
  check('switching branches changes the source count',await page.locator('#project-stats strong').first().innerText()===main.summary.physical_lines.toLocaleString('en-US'));
  await page.locator('#history-metric').selectOption('bytes');
  const shared=page.url();await page.reload({waitUntil:'networkidle'});
  check('shared links retain the track and metric',page.url()===shared&&await page.locator('#history-metric').inputValue()==='bytes');
  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,deviceScaleFactor:1});
  mobile.on('pageerror',error=>errors.push(error.message));
  await mobile.goto(base,{waitUntil:'networkidle'});
  await mobile.locator('#project-stats strong').first().waitFor();
  check('mobile page fits its viewport',await mobile.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
  await mobile.locator('#track').selectOption('compiler-baseline');
  check('mobile revision selection works',(await mobile.locator('#revision').innerText()).includes('fc2b73103ce9'));
  if(output)await mobile.screenshot({path:path.join(output,'project-mobile.png'),fullPage:true});
  check('no browser errors',errors.length===0);
  const receipt={schema:'mech-project-browser.v1',status:'passed',url:base,build:manifest.version,browser:browser.version(),checked_at:new Date().toISOString(),checks,errors};
  if(output)await writeFile(path.join(output,'browser.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));
} finally {await browser.close();}
