const fs = require('fs');
const crypto = require('crypto');
const { chromium } = require('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const output = '/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4';
const input = output + '/mech-rust-optimization-history.html';
const files = [];
(async () => {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,chromiumSandbox:true});
  try {
    const page = await browser.newPage({viewport:{width:1232,height:3200},deviceScaleFactor:2,colorScheme:'light'});
    const errors = []; page.on('pageerror', e => errors.push(String(e)));
    await page.goto('file:///private/tmp/mech-history-png-preview.html',{waitUntil:'networkidle'});
    const frame = page.frames().find(f => f !== page.mainFrame());
    if (!frame) throw Error('Missing render frame');
    await frame.locator('svg.history-svg').nth(3).waitFor();
    await frame.addStyleTag({content:`
      :root { color-scheme:light; --background:#ffffff; --foreground:#111111; --muted-foreground:#555555; --border:#dddddd; --viz-series-1:#176cc1; --viz-series-2:#176cc1; }
      html,body { background:#ffffff !important; }
      #mech-optimization-history { background:#ffffff; box-sizing:border-box; padding:24px; }
      #mech-optimization-history .summary, #mech-optimization-history details, #history-announcement { display:none; }
      #mech-optimization-history .history-svg text { fill:#111111; font-size:16px; }
      #mech-optimization-history figcaption { font-size:15px; }
      #mech-optimization-history .history-svg .median,
      #mech-optimization-history .history-svg g[clip-path] > circle { fill:#176cc1 !important; }
      #mech-optimization-history .history-svg g[clip-path] > g,
      #mech-optimization-history .history-svg line[pointer-events="none"] { display:none; }
    `});
    await frame.waitForFunction(() => [...document.querySelectorAll('svg.history-svg')].every(s => s.clientWidth === s.viewBox.baseVal.width));
    await frame.evaluate(() => {
      const root = document.getElementById('mech-optimization-history');
      root.querySelector('h2').textContent = 'K-nucleotide: Mech optimization history';
      root.querySelector('.legend').textContent = 'Blue dots: cohort medians / single runs · faint dots: individual processes · all trials retained';
      root.querySelector('.legend').style.marginBlock = '8px 20px';
      root.querySelector(':scope > .text-small.text-muted:last-of-type').style.display = 'none';
      const symbol = d3.symbol().type(d3.symbolCircle).size(48)();
      d3.select(root).selectAll('path.median').attr('d',symbol);
    });
    const plots = [
      ['history-full-plot','mech-history-full-125m.png'],
      ['history-prefix-plot','mech-history-prefix-1m.png'],
      ['history-tiny-plot','mech-history-initial-1000.png'],
      ['history-small-plot','mech-history-early-100k.png']
    ];
    for (const [id,name] of plots) {
      await frame.locator('#'+id).locator('..').screenshot({path:output+'/'+name,omitBackground:false});
      files.push(name);
    }
    await frame.locator('#mech-optimization-history').screenshot({path:output+'/mech-history-all-plots.png',omitBackground:false});
    files.push('mech-history-all-plots.png');
    const marks = await frame.locator('svg.history-svg .median').count();
    if (marks !== 220 || errors.length) throw Error(JSON.stringify({marks,errors}));
    const report = {status:'white-background-blue-dot-pngs-exported',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex'),cohorts:marks,timezone:'America/New_York',files:files.map(name=>({name,sha256:crypto.createHash('sha256').update(fs.readFileSync(output+'/'+name)).digest('hex')})),errors};
    fs.writeFileSync(output+'/mech-history-png-export.json',JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report));
  } finally { await browser.close(); }
})().catch(e=>{ console.error(e); process.exitCode=1; });
