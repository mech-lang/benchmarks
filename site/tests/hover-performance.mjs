// Serial browser measurements of rollover work, including rendering costs.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createServer} from 'node:http';
import path from 'node:path';
import os from 'node:os';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]),output=process.argv[3];
assert.ok(output,'Asset directory and fresh output path required');
await assert.rejects(fs.access(output));
const manifest=JSON.parse(await fs.readFile(path.join(root,'build.json'),'utf8'));
const server=createServer(async(req,res)=>{
  try{
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+(name==='/'?'/index.html':name));
    assert.ok(file.startsWith(root+path.sep));
    const data=await fs.readFile(file);
    res.writeHead(200,{'Content-Type':({'.mjs':'text/javascript','.html':'text/html','.css':'text/css','.json':'application/json'})[path.extname(file)]??'application/octet-stream'});res.end(data);
  }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const rows=[];
const metrics=async cdp=>Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(x=>[x.name,x.value]));
try{
  for(const config of [{width:1280,rate:1},{width:390,rate:4}])for(let repetition=0;repetition<3;repetition++){
    const page=await browser.newPage({viewport:{width:config.width,height:1000}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    const cdp=await page.context().newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate',{rate:config.rate});await cdp.send('Performance.enable');
    await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.benchmarkExplorer);
    await page.locator('#chart').scrollIntoViewIfNeeded();
    await page.evaluate(()=>{
      window.hoverPerf={mutations:0,ctm:0,frames:[],longtasks:[]};
      const original=SVGGraphicsElement.prototype.getScreenCTM;
      SVGGraphicsElement.prototype.getScreenCTM=function(...args){hoverPerf.ctm++;return original.apply(this,args);};
      new MutationObserver(records=>hoverPerf.mutations+=records.length).observe(document.querySelector('#chart'),{attributes:true,childList:true,subtree:true});
      new PerformanceObserver(list=>hoverPerf.longtasks.push(...list.getEntries().map(e=>e.duration))).observe({type:'longtask'});
      const frame=t=>{hoverPerf.frames.push(t);requestAnimationFrame(frame);};requestAnimationFrame(frame);
      window.hoverTargets=()=>{
        const samples=[...document.querySelectorAll('#chart [data-sample]')];
        const languages=[...new Set(samples.map(n=>n.dataset.chartLanguage))];
        return languages.slice(0,12).map(key=>samples.filter(n=>n.dataset.chartLanguage===key).slice(0,2)).flat();
      };
    });
    await page.waitForTimeout(250);
    const operations=[];
    for(const kind of ['within-language-burst','cross-language-burst','single-marker-movement','cross-language-frames']){
      const before=await metrics(cdp);
      const result=await page.evaluate(async kind=>{
        const chart=document.querySelector('#chart'),targets=hoverTargets();
        // Geometry is captured before measurement, rather than forcing layout
        // from the test between pointer handlers.
        const positions=targets.map(node=>{const b=node.getBoundingClientRect();return {clientX:b.x+b.width/2,clientY:b.y+b.height/2};});
        const medians=[...chart.querySelectorAll('[data-profile-median]')];
        const mark=medians.find(n=>n.dataset.chartLanguage===targets[0].dataset.chartLanguage),b=mark.getBoundingClientRect();
        const emit=(node,type,relatedTarget=null,pos=positions[targets.indexOf(node)]??positions[0])=>node.dispatchEvent(new PointerEvent(type,{bubbles:!['pointerenter','pointerleave'].includes(type),pointerType:'mouse',relatedTarget,...pos}));
        const settle=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        const start={...hoverPerf,frames:hoverPerf.frames.length,longtasks:hoverPerf.longtasks.length},t=performance.now();
        let dispatch_ms=0;
        if(kind==='single-marker-movement'){
          const a=performance.now();emit(mark,'pointerenter',null,{clientX:b.x+b.width/2,clientY:b.y+b.height/2});
          for(let i=0;i<200;i++)emit(mark,'pointermove',null,{clientX:b.x+b.width/2,clientY:b.y+b.height/2});
          dispatch_ms=performance.now()-a;await settle();
        }else{
          const count=kind==='cross-language-frames'?24:200;
          let previous=null;
          for(let i=0;i<count;i++){
            const node=targets[kind==='within-language-burst'?i%2:i%targets.length],a=performance.now();
            if(previous){emit(previous,'pointerleave',node);emit(previous,'pointerout',node);}
            emit(node,'pointerenter',previous);emit(node,'pointerover',previous);emit(node,'pointermove');
            previous=node;dispatch_ms+=performance.now()-a;
            if(kind==='cross-language-frames')await new Promise(resolve=>requestAnimationFrame(resolve));
          }
          await settle();
        }
        const frames=hoverPerf.frames.slice(start.frames),gaps=frames.slice(1).map((v,i)=>v-frames[i]);
        return {dispatch_ms,through_two_frames_ms:performance.now()-t,mutations:hoverPerf.mutations-start.mutations,ctm_reads:hoverPerf.ctm-start.ctm,
          frame_intervals_ms:gaps,longtasks_ms:hoverPerf.longtasks.slice(start.longtasks),highlight:chart.dataset.highlightLanguage,samples:chart.querySelectorAll('[data-sample]').length};
      },kind);
      const after=await metrics(cdp);
      operations.push({kind,...result,metrics:Object.fromEntries(['RecalcStyleCount','RecalcStyleDuration','LayoutCount','LayoutDuration','ScriptDuration','TaskDuration'].map(k=>[k,after[k]-before[k]]))});
      await page.evaluate(()=>document.querySelector('#chart').dispatchEvent(new PointerEvent('pointerleave',{pointerType:'mouse'})));
      await page.waitForTimeout(220);
    }
    // A real pointer sweep exercises native hit testing and painting as well.
    const box=await page.locator('#chart').boundingBox(),before=await metrics(cdp);
    await page.evaluate(()=>{hoverPerf.frames=[];hoverPerf.longtasks=[];hoverPerf.mutations=0;hoverPerf.ctm=0;});
    for(let i=0;i<70;i++)await page.mouse.move(box.x+box.width*(.18+.64*i/69),box.y+box.height*(.38+.1*Math.sin(i/8)));
    await page.waitForTimeout(220);
    const sweep=await page.evaluate(()=>({mutations:hoverPerf.mutations,ctm_reads:hoverPerf.ctm,longtasks_ms:hoverPerf.longtasks,frame_intervals_ms:hoverPerf.frames.slice(1).map((t,i)=>t-hoverPerf.frames[i])})),after=await metrics(cdp);
    sweep.metrics=Object.fromEntries(['RecalcStyleCount','RecalcStyleDuration','LayoutCount','LayoutDuration','ScriptDuration','TaskDuration'].map(k=>[k,after[k]-before[k]]));
    assert.deepEqual(errors,[]);rows.push({...config,repetition,operations,real_pointer_sweep:sweep,page_errors:errors});
    console.log(JSON.stringify({build:manifest.version,...config,repetition,operations:operations.map(({kind,dispatch_ms,mutations,ctm_reads})=>({kind,dispatch_ms,mutations,ctm_reads}))}));
    await page.close();
  }
  await fs.writeFile(output,JSON.stringify({schema:'chart-hover-performance.v1',status:'PASSED',build:manifest.version,files:manifest.files,recorded_at:new Date().toISOString(),host:{hostname:os.hostname(),arch:os.arch(),platform:os.platform()},browser:browser.version(),scope:'Same serial loopback browser contexts and dataset. Desktop and 390px layout with simulated 4x CPU slowdown; not a physical phone. Mutations and CTM reads include RAF work. Dispatch bursts are intentionally higher frequency than rendered frames; a separate native pointer sweep measures rendering.',rows},null,2)+'\n');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
