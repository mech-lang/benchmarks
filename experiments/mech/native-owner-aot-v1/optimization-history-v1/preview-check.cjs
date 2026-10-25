const fs = require('fs');
const { chromium } = require('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = '/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4';
(async () => {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,chromiumSandbox:true});
  try {
    const page = await browser.newPage({viewport:{width:780,height:1000}});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:8768/',{waitUntil:'networkidle'});
    const frame=page.frames().find(f=>f!==page.mainFrame());
    if(!frame)throw Error('Missing wrapped preview iframe');
    await frame.locator('svg.history-svg').nth(3).waitFor();
    if(await frame.locator('#history-ledger tr').count()!==94)throw Error('Incomplete step list');
    const results=[];
    for(const width of [780,360,320]){
      await page.setViewportSize({width,height:3000});
      await page.reload({waitUntil:'networkidle'});
      const freshFrame=page.frames().find(f=>f!==page.mainFrame());
      await freshFrame.waitForFunction(()=>[...document.querySelectorAll('svg.history-svg')].length===4&&[...document.querySelectorAll('svg.history-svg')].every(s=>s.clientWidth===s.viewBox.baseVal.width));
      await page.waitForTimeout(250);
      const sizes=await freshFrame.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth,rootHeight:document.querySelector('#mech-optimization-history').getBoundingClientRect().height,ledgerY:document.querySelector('summary').getBoundingClientRect().y,plots:[...document.querySelectorAll('svg.history-svg')].map(s=>({width:s.clientWidth,view:s.viewBox.baseVal.width,marks:s.querySelectorAll('.median').length}))}));
      if(sizes.scroll>sizes.viewport+1)throw Error('Horizontal overflow at '+width+': '+JSON.stringify(sizes));
      if(sizes.plots.some(p=>p.width!==p.view))throw Error('Stale chart width at '+width);
      await freshFrame.locator('#mech-optimization-history').screenshot({path:path+'/mech-history-'+width+'.png'});
      results.push({width,...sizes});
    }
    const lastFrame=page.frames().find(f=>f!==page.mainFrame());
    await lastFrame.locator('summary').click();
    await lastFrame.locator('[data-step-button="1"]').click();
    if(!((await lastFrame.locator('#history-step').textContent()).includes('Earlier library')))throw Error('First-step selection failed');
    await lastFrame.locator('[data-step-button="94"]').click();
    if(!((await lastFrame.locator('#history-full').textContent()).includes('0.55604')))throw Error('Latest selection failed');
    if(!((await lastFrame.locator('#history-date').textContent()).includes('Oct 25')))throw Error('Recovered timestamp not displayed');
    if(errors.length)throw Error(errors.join('\n'));
    fs.writeFileSync(path+'/mech-history-preview-check.json',JSON.stringify({status:'all-four-plots-responsive-and-step-selection-verified',results,errors},null,2));
    console.log(JSON.stringify({status:'verified',results,errors}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
