import {chromium} from '/Users/coreymontella/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {performance} from 'node:perf_hooks';
const [base,output]=process.argv.slice(2);
if(!base||!output)throw new Error('Asset directory and fresh report path required');
try{await fs.access(output);throw new Error('Report already exists');}catch(error){if(error.code!=='ENOENT')throw error;}
const manifest=JSON.parse(await fs.readFile(path.join(base,'build.json'),'utf8'));
const mime={'.html':'text/html','.mjs':'text/javascript','.json':'application/json','.css':'text/css'};
const server=http.createServer(async(req,res)=>{
  try{
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(base,'.'+(name==='/'?'/index.html':name));
    if(!file.startsWith(path.resolve(base)+path.sep))throw new Error('Outside root');
    const info=await fs.stat(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]??'text/plain','Content-Length':info.size,'Cache-Control':'public,max-age=3600'});
    createReadStream(file).pipe(res);
  }catch{res.writeHead(404);res.end('not found');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=`http://127.0.0.1:${server.address().port}/`;
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const results=[];
const topFrames=profile=>{
  const nodes=new Map(profile.nodes.map(node=>[node.id,node])),totals=new Map();
  for(let i=0;i<(profile.samples??[]).length;i++){
    const frame=nodes.get(profile.samples[i])?.callFrame;if(!frame)continue;
    const key=JSON.stringify([frame.functionName,frame.url,frame.lineNumber]);
    totals.set(key,(totals.get(key)??0)+(profile.timeDeltas?.[i]??0)/1000);
  }
  return [...totals].map(([key,self_ms])=>{const [functionName,url,line]=JSON.parse(key);return {functionName,url,line:line+1,self_ms};}).sort((a,b)=>b.self_ms-a.self_ms).slice(0,15);
};
const operations=[
  ['summary_refresh',"benchmarkExplorer.setLayerModes({samples:'dim',medians:'highlight',density:'off'})"],
  ['memory_filter',"(()=>{const x=document.querySelector('[data-benchmark-facet=\"resource:memory\"]');x.checked=true;x.dispatchEvent(new Event('change',{bubbles:true}));})()"],
  ['clear_filter',"document.querySelector('#clear-benchmark-filters').click()"],
  ['density_on',"benchmarkExplorer.setLayerModes({density:'dim'})"],
  ['density_highlight',"benchmarkExplorer.setLayerModes({density:'highlight'})"],
  ['density_dim',"benchmarkExplorer.setLayerModes({density:'dim'})"],
  ['density_off',"benchmarkExplorer.setLayerModes({density:'off'})"],
  ['rankings_open',"document.querySelector('[data-view=\"rankings\"]').click()"],
  ['rankings_reset',"document.querySelector('#reset-rankings').click()"],
  ['summary_open',"document.querySelector('[data-view=\"summary\"]').click()"],
  ['language_open',"document.querySelector('[data-table-language=\"rust\"]').click()"],
  ['language_axes_medians',"(()=>{const x=document.querySelector('#chart-axes');x.value='means';x.dispatchEvent(new Event('change',{bubbles:true}));})()"],
  ['language_axes_samples',"(()=>{const x=document.querySelector('#chart-axes');x.value='samples';x.dispatchEvent(new Event('change',{bubbles:true}));})()"],
  ['language_density_on',"benchmarkExplorer.setLayerModes({density:'dim'})"],
  ['language_density_highlight',"benchmarkExplorer.setLayerModes({density:'highlight'})"],
  ['language_reset',"document.querySelector('#reset').click()"],
  ['program_open',"document.querySelector('#language-timings [data-inspect-program]').click()"],
  ['program_close',"document.querySelector('#close-inspector').click()"],
];
try{
  for(const config of [{width:1280,rate:1},{width:390,rate:1},{width:390,rate:4}])for(let repetition=0;repetition<3;repetition++){
    console.log(JSON.stringify({stage:'start',...config,repetition}));
    const context=await browser.newContext({viewport:{width:config.width,height:1000}}),page=await context.newPage(),cdp=await context.newCDPSession(page),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await cdp.send('Emulation.setCPUThrottlingRate',{rate:config.rate});await cdp.send('Performance.enable');await cdp.send('Profiler.enable');
    await page.addInitScript(()=>{
      window.__perf={bbox_calls:0,bbox_ms:0,ready_ms:null,longtasks:[]};
      const bbox=SVGGraphicsElement.prototype.getBBox;
      SVGGraphicsElement.prototype.getBBox=function(...args){const started=performance.now();try{return bbox.apply(this,args);}finally{__perf.bbox_calls++;__perf.bbox_ms+=performance.now()-started;}};
      new PerformanceObserver(list=>{for(const entry of list.getEntries())__perf.longtasks.push({start_ms:entry.startTime,duration_ms:entry.duration});}).observe({type:'longtask',buffered:true});
      const watch=()=>{if(window.benchmarkExplorer)__perf.ready_ms=performance.now();else requestAnimationFrame(watch);};requestAnimationFrame(watch);
    });
    await cdp.send('Profiler.start');const started=performance.now();
    await page.goto(url,{waitUntil:'load',timeout:120000});await page.waitForFunction(()=>window.__perf.ready_ms!==null,null,{timeout:120000});
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const initial={wall_ms:performance.now()-started,observed:await page.evaluate(()=>({...__perf,dom_nodes:document.querySelectorAll('*').length,samples:document.querySelectorAll('#chart [data-sample]').length,variants:benchmarkExplorer.getSelection().selectedLanguages.length})),metrics:Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(x=>[x.name,x.value])),profile:topFrames((await cdp.send('Profiler.stop')).profile)};
    const measured=[];
    for(const [name,expression] of operations){
      const before=Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(x=>[x.name,x.value]));await cdp.send('Profiler.start');
      const value=await page.evaluate(async expression=>{
        const calls=__perf.bbox_calls,bbox=__perf.bbox_ms,longtasks=__perf.longtasks.length,t=performance.now();
        (0,eval)(expression);const synchronous_ms=performance.now()-t;
        await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        return {synchronous_ms,two_frame_ms:performance.now()-t,bbox_calls:__perf.bbox_calls-calls,bbox_ms:__perf.bbox_ms-bbox,longtasks:__perf.longtasks.slice(longtasks),samples:document.querySelectorAll('#chart [data-sample]').length,view:document.querySelector('[data-view][aria-pressed=\"true\"]')?.dataset.view,layers:benchmarkExplorer.getSelection().layers??null};
      },expression);
      const profile=topFrames((await cdp.send('Profiler.stop')).profile),after=Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(x=>[x.name,x.value]));
      measured.push({name,...value,metrics:Object.fromEntries(['LayoutCount','LayoutDuration','RecalcStyleCount','RecalcStyleDuration','ScriptDuration','TaskDuration'].map(key=>[key,after[key]-before[key]])),profile});
    }
    if(errors.length)throw new Error(JSON.stringify(errors));
    results.push({...config,repetition,initial,operations:measured,errors});
    await fs.writeFile(output,JSON.stringify({status:'running',build:manifest.version,results},null,2)+'\n');
    console.log(JSON.stringify({stage:'completed',...config,repetition,ready_ms:initial.observed.ready_ms,operations:measured.map(x=>({name:x.name,ms:x.synchronous_ms,layouts:x.metrics.LayoutCount})),errors}));
    await context.close();
  }
  const sourceHashes={};for(const name of Object.keys(manifest.files))sourceHashes[name]=crypto.createHash('sha256').update(await fs.readFile(path.join(base,name))).digest('hex');
  await fs.writeFile(output,JSON.stringify({schema:'explorer-performance-v2-browser',status:'complete',recorded_at:new Date().toISOString(),build:manifest.version,host:{hostname:os.hostname(),platform:os.platform(),arch:os.arch()},node:process.version,browser:browser.version(),scope:'Same separate host, loopback uncompressed assets, fresh serial browser contexts, identical CDP CPU profiling and getBBox instrumentation. 4x CPU slowdown simulates slower hardware. Two-frame timing retains intervening rendering opportunities.',sourceHashes,results},null,2)+'\n');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
console.log(JSON.stringify({stage:'complete',build:manifest.version,output}));
