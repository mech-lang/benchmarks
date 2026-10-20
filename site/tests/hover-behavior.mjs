import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createServer} from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]),output=process.argv[3],live=process.env.HOVER_TEST_URL;
assert.ok(output);await assert.rejects(fs.access(output));
const manifest=JSON.parse(await fs.readFile(path.join(root,'build.json'),'utf8'));
const server=createServer(async(req,res)=>{
  try{
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(root,'.'+(name==='/'?'/index.html':name));
    assert.ok(file.startsWith(root+path.sep));
    res.writeHead(200,{'Content-Type':({'.mjs':'text/javascript','.html':'text/html','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream'});res.end(await fs.readFile(file));
  }catch{res.writeHead(404);res.end();}
});
if(!live)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const rows=[],errors=[];
try{
  for(const width of [1280,390]){
    const page=await browser.newPage({viewport:{width,height:1000}});page.on('pageerror',e=>errors.push(e.message));
    await page.goto(live??`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.benchmarkExplorer);
    assert.equal(await page.locator('script[type=module]').getAttribute('src'),`./app.mjs?v=${manifest.version}`);
    const settle=()=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const emit=async(selector,type)=>{await page.locator(selector).first().evaluate((n,type)=>n.dispatchEvent(new PointerEvent(type,{bubbles:!['pointerenter','pointerleave'].includes(type),pointerType:'mouse'})),type);await settle();};
    const snapshot=async name=>{
      // The control animates opacity; compare its settled appearance with the
      // candidate's immediate appearance, including ancestor opacity products.
      await page.waitForTimeout(200);
      await page.waitForFunction(()=>document.querySelector('#chart').getAnimations({subtree:true}).length===0);
      const state=await page.evaluate(()=>{
        const chart=document.querySelector('#chart');
        const effectiveOpacity=n=>{let value=1;for(let p=n;p&&p!==chart.parentElement;p=p.parentElement)value*=Number(getComputedStyle(p).opacity);return Math.round(value*1e6)/1e6;};
        const marks=[...chart.querySelectorAll('[data-chart-language],[data-global-statistic],[data-global-sigma]')].map(n=>{
          const css=getComputedStyle(n);
          return {tag:n.tagName,language:n.dataset.chartLanguage??null,program:n.dataset.program??null,run:n.dataset.timingRun??null,
            geometry:Object.fromEntries(['cx','cy','r','x','y','width','height','x1','x2','y1','y2','d','transform'].map(k=>[k,n.getAttribute(k)])),
            fill:css.fill,fillOpacity:css.fillOpacity,stroke:css.stroke,strokeOpacity:css.strokeOpacity,strokeWidth:css.strokeWidth,opacity:effectiveOpacity(n),text:n.tagName==='text'?n.textContent:null};
        });
        return {marks,active:chart.dataset.highlightLanguage??null,samples:chart.querySelectorAll('[data-sample]').length,
          domains:benchmarkExplorer.getDomains(),density:document.querySelector('[data-layer=density]')?.dataset.densityRuns??null,
          layers:benchmarkExplorer.getSelection(),readout:document.querySelector('#hover-details').textContent};
      });
      const hash=crypto.createHash('sha256').update(JSON.stringify(state.marks)).digest('hex');delete state.marks;
      rows.push({width,name,geometry_and_paint_sha256:hash,...state});
    };
    const mark=language=>`#chart [data-profile-median][data-chart-language="${language}"]`;
    for(const mode of ['off','dim','highlight']){
      await page.evaluate(mode=>benchmarkExplorer.setLayerModes({samples:mode,medians:'highlight',density:'off'}),mode);await settle();
      await snapshot(`${mode}:baseline`);
      await emit(mark('rust'),'pointerenter');await snapshot(`${mode}:median-hover`);
      await emit(mark('rust'),'pointerleave');await snapshot(`${mode}:exit`);
      await page.locator(mark('rust')).first().focus();await settle();await snapshot(`${mode}:keyboard-focus`);
      await page.locator(mark('rust')).first().evaluate(n=>n.blur());await settle();
    }
    await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'dim',medians:'off',density:'highlight'}));await settle();
    await snapshot('density-and-samples');
    await emit('#chart [data-sample][data-chart-language="rust"]','pointerover');await snapshot('sample-hover-without-medians');
    await emit('#chart [data-sample][data-chart-language="rust"]','pointerout');
    await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'off',medians:'off',density:'highlight'}));await settle();await snapshot('density-only');
    await page.locator('#show-global').check();await settle();await snapshot('global-without-samples-or-medians');
    if(width<=720)await page.locator('#open-filters').click();
    await page.locator('[data-open-language="rust"]').click();
    if(width<=720&&await page.locator('#filter-drawer').evaluate(n=>n.open))await page.locator('#close-filters').click();
    await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'dim',medians:'highlight',density:'off'}));await settle();await snapshot('hero-baseline');
    await emit(mark('ruby'),'pointerenter');await snapshot('hero-context-hover');
    await emit(mark('ruby'),'pointerleave');await snapshot('hero-restored');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
    // New implementation: stable-language rollover does not rewrite dots or
    // labels. These assertions test bounded updates, not elapsed-time guesses.
    if(process.env.EXPECT_FRAME_HOVER==='1'){
      const result=await page.evaluate(async()=>{
        const chart=document.querySelector('#chart'),samples=[...chart.querySelectorAll('[data-sample][data-chart-language="rust"]')];
        const next=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        const send=(n,type)=>n.dispatchEvent(new PointerEvent(type,{bubbles:true,pointerType:'mouse'}));
        send(samples[0],'pointerover');await next();
        const records=[],observer=new MutationObserver(r=>records.push(...r));observer.observe(chart,{attributes:true,childList:true,subtree:true});
        for(let i=0;i<200;i++){send(samples[i%samples.length],'pointerout');send(samples[(i+1)%samples.length],'pointerover');}
        await next();observer.disconnect();
        const sameLanguageMutations=records.length;
        const oldSample=samples[0];send(oldSample,'pointerover');
        benchmarkExplorer.setLayerModes({samples:'off'});
        // Even a late blur/leave from a removed node cannot revive its queue.
        oldSample.dispatchEvent(new FocusEvent('focusout',{bubbles:true}));await next();
        return {sameLanguageMutations,afterReplacement:chart.dataset.highlightLanguage??null,samples:chart.querySelectorAll('[data-sample]').length};
      });
      assert.equal(result.sameLanguageMutations,0,'Same-language rollover makes no chart mutations.');
      assert.equal(result.afterReplacement,null);assert.equal(result.samples,0);
      rows.push({width,name:'bounded-updates-and-teardown',...result});
      await page.evaluate(()=>benchmarkExplorer.setLayerModes({samples:'dim',medians:'highlight',density:'off'}));await settle();
      await page.locator('#chart').scrollIntoViewIfNeeded();
      const visibleTarget=selector=>page.evaluate(selector=>{
        for(const node of document.querySelectorAll(selector)){
          const b=node.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;
          if(x>0&&x<innerWidth&&y>0&&y<innerHeight&&document.elementFromPoint(x,y)===node)
            return {x,y,language:node.dataset.chartLanguage,program:node.dataset.program};
        }
        return null;
      },selector);
      const median=await visibleTarget('#chart [data-profile-median]');assert.ok(median,'A visible median receives native pointer input.');
      await page.mouse.move(median.x,median.y);await settle();
      const medianLanguage=await page.locator('#chart').getAttribute('data-highlight-language');assert.ok(medianLanguage);
      await page.evaluate(()=>benchmarkExplorer.setLayerModes({medians:'off'}));await settle();
      const sample=await visibleTarget('#chart [data-sample]');assert.ok(sample,'A visible dot receives native pointer input.');
      await page.mouse.move(sample.x,sample.y);await settle();
      assert.equal(await page.locator('#chart').getAttribute('data-highlight-language'),sample.language);
      await page.mouse.click(sample.x,sample.y);await settle();
      assert.equal(await page.locator('#inspector').evaluate(n=>n.open),true);
      assert.equal(await page.locator('#detail-program').inputValue(),sample.program);
      await page.locator('#close-inspector').click();await page.locator('[data-view="rankings"]').click();await settle();
      const rankingMutations=await page.evaluate(async()=>{
        const mark=document.querySelector('.ranking-mark');
        mark.dispatchEvent(new PointerEvent('pointerenter',{pointerType:'mouse'}));
        const records=[],observer=new MutationObserver(r=>records.push(...r));
        for(const readout of document.querySelectorAll('.ranking-readout'))observer.observe(readout,{attributes:true,childList:true,subtree:true});
        for(let i=0;i<200;i++){
          mark.dispatchEvent(new PointerEvent('pointermove',{pointerType:'mouse',bubbles:true}));
          mark.dispatchEvent(new FocusEvent('focus'));
        }
        await new Promise(resolve=>requestAnimationFrame(resolve));observer.disconnect();return records.length;
      });
      assert.equal(rankingMutations,0,'Stable ranking hover/focus must not rewrite the readout.');
      rows.push({width,name:'native-median-and-dot-input',medianLanguage,sampleLanguage:sample.language,inspectedProgram:sample.program,rankingMutations});
    }
    await page.close();
  }
  assert.deepEqual(errors,[]);
  await fs.writeFile(output,JSON.stringify({schema:'chart-hover-behavior.v1',status:'PASSED',build:manifest.version,url:live??'loopback',rows,page_errors:errors,benchmark_executions:0},null,2)+'\n');
  console.log(JSON.stringify({status:'PASSED',build:manifest.version,states:rows.length,page_errors:errors}));
}finally{await browser.close();if(!live)await new Promise(resolve=>server.close(resolve));}
