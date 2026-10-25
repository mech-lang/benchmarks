const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {chromium} = require('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const here = __dirname;
const visualizations = '/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4';
const source = path.join(here,'mech-history-hours-log-fit.svg');
const output = path.join(visualizations,'mech-history-hours-log-fit.png');
const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async () => {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,chromiumSandbox:true});
  try {
    const page = await browser.newPage({viewport:{width:1800,height:1080},deviceScaleFactor:2,colorScheme:'light'});
    const errors=[];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto('file://'+source,{waitUntil:'load'});
    await page.evaluate(() => document.fonts.ready);
    const layout = await page.locator('svg').evaluate(svg => {
      const texts=[...svg.querySelectorAll('text')].map(t=>{
        const r=t.getBoundingClientRect();
        return {text:t.textContent,x:r.x,y:r.y,width:r.width,height:r.height};
      });
      const overflow=texts.filter(r=>r.x<0||r.y<0||r.x+r.width>1800.5||r.y+r.height>1080.5);
      const labels=[...svg.querySelectorAll('text.label, text.detail')].map(t=>{
        const r=t.getBoundingClientRect();return {text:t.textContent,x:r.x,y:r.y,width:r.width,height:r.height};
      });
      const overlaps=[];
      for(let i=0;i<labels.length;i++) for(let j=i+1;j<labels.length;j++) {
        const a=labels[i],b=labels[j];
        if(Math.min(a.x+a.width,b.x+b.width)>Math.max(a.x,b.x)&&Math.min(a.y+a.height,b.y+b.height)>Math.max(a.y,b.y)) overlaps.push([a.text,b.text]);
      }
      return {width:svg.clientWidth,height:svg.clientHeight,overflow,overlaps,texts};
    });
    if(errors.length||layout.overflow.length||layout.overlaps.length) throw Error(JSON.stringify({errors,layout}));
    await page.locator('svg').screenshot({path:output,omitBackground:false});
    fs.copyFileSync(output,path.join(here,'mech-history-hours-log-fit.png'));
    const verification={status:'exported-and-layout-checked',source_sha256:hash(source),png_sha256:hash(output),png_width:3600,png_height:2160,errors,layout};
    fs.writeFileSync(path.join(here,'export-verification.json'),JSON.stringify(verification,null,2)+'\n');
    fs.writeFileSync(path.join(visualizations,'mech-history-hours-log-fit-export-verification.json'),JSON.stringify(verification,null,2)+'\n');
    console.log(JSON.stringify({status:verification.status,png:output,png_sha256:verification.png_sha256,overflow:layout.overflow,overlaps:layout.overlaps,errors}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
