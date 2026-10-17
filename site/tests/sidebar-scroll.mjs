import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile,stat,writeFile} from 'node:fs/promises';
import path from 'node:path';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE??'playwright');
const root=path.resolve(process.argv[2]??'site/public');
const output=process.argv[3];
const live=process.env.SIDEBAR_TEST_URL;
const server=createServer(async(req,res)=>{
  try{
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+(name==='/'?'/index.html':name));
    assert.ok(file.startsWith(root+path.sep));
    assert.ok((await stat(file)).isFile());
    const types={'.mjs':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'};
    res.writeHead(200,{'Content-Type':types[path.extname(file)]??'text/plain'});
    res.end(await readFile(file));
  }catch{res.writeHead(404);res.end();}
});
if(!live)await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const url=live??`http://127.0.0.1:${server.address().port}/`;
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BINARY?{executablePath:process.env.CHROME_BINARY}:{})});
const rows=[],errors=[];
const settle=page=>page.evaluate(async()=>{
  await Promise.all(document.querySelector('#filter-drawer').getAnimations().map(a=>a.finished.catch(()=>{})));
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
});
const snapshot=page=>page.evaluate(()=>{
  const el=document.querySelector('.controls'),r=el.getBoundingClientRect();
  return {pageY:scrollY,chartY:document.querySelector('#chart').getBoundingClientRect().top,
    top:r.top,bottom:r.bottom,height:r.height,clientHeight:el.clientHeight,
    scrollTop:el.scrollTop,scrollHeight:el.scrollHeight,
    viewport:visualViewport?.height??innerHeight,overflow:getComputedStyle(el).overflowY,
    overscroll:getComputedStyle(el).overscrollBehaviorY,
    desktop:el.parentElement.classList.contains('workspace')};
});
function fits(s){
  assert.ok(s.height>100,`Usable sidebar height: ${JSON.stringify(s)}`);
  assert.ok(s.top>=-1&&s.bottom<=s.viewport+1,`Sidebar fits viewport: ${JSON.stringify(s)}`);
  assert.equal(s.overflow,'auto');assert.equal(s.overscroll,'contain');
}
function stationary(before,after){
  assert.ok(Math.abs(before.pageY-after.pageY)<1,'Sidebar scroll must not move the document');
  assert.ok(Math.abs(before.chartY-after.chartY)<1,'Sidebar scroll must not move the chart');
}
async function wheel(page,dy){
  const box=await page.locator('.controls').boundingBox();
  await page.mouse.move(box.x+box.width/2,box.y+Math.min(box.height/2,150));
  await page.mouse.wheel(0,dy);
  await page.waitForTimeout(180);
  await settle(page);
}
try{
  for(const [width,height] of [[1280,900],[900,600],[721,500]]){
    const page=await browser.newPage({viewport:{width,height}});
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url,{waitUntil:'load'});
    await page.waitForFunction(()=>!!window.benchmarkExplorer);
    await settle(page);
    const initial=await snapshot(page);fits(initial);
    assert.ok(initial.desktop&&initial.scrollHeight>initial.clientHeight);
    const selection=await page.evaluate(()=>window.benchmarkExplorer.getSelection());
    await wheel(page,2000);
    const scrolled=await snapshot(page);stationary(initial,scrolled);
    assert.ok(scrolled.scrollTop>0);
    await page.locator('#language-controls .language-name').last().scrollIntoViewIfNeeded();
    await settle(page);stationary(initial,await snapshot(page));
    const last=await page.locator('#language-controls .language-name').last().boundingBox();
    assert.ok(last.y>=initial.top-1&&last.y+last.height<=initial.bottom+1,'Last language is reachable inside the sidebar');
    await page.locator('.controls').evaluate(el=>{el.scrollTop=el.scrollHeight;});
    await wheel(page,2000);stationary(initial,await snapshot(page));
    await page.locator('.controls').focus();
    await page.keyboard.press('Home');await page.waitForTimeout(180);
    stationary(initial,await snapshot(page));
    await page.keyboard.press('PageDown');await page.waitForTimeout(180);
    assert.ok((await snapshot(page)).scrollTop>0);
    stationary(initial,await snapshot(page));
    assert.deepEqual(await page.evaluate(()=>window.benchmarkExplorer.getSelection()),selection);
    await page.evaluate(()=>scrollTo(0,500));await settle(page);
    const sticky=await snapshot(page);fits(sticky);
    assert.ok(Math.abs(sticky.top-16)<1,'Sidebar stays pinned while the page scrolls');
    await page.setViewportSize({width,height:height-120});await settle(page);
    fits(await snapshot(page));
    rows.push({width,height,initial,scrolled,sticky,checks:['wheel','last language','scroll chaining','keyboard','selection unchanged','sticky','viewport resize']});
    await page.close();
  }
  const page=await browser.newPage({viewport:{width:390,height:844}});
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url,{waitUntil:'load'});
  await page.waitForFunction(()=>!!window.benchmarkExplorer);
  await page.evaluate(()=>scrollTo(0,250));await settle(page);
  const pageY=await page.evaluate(()=>scrollY);
  await page.locator('#open-filters').click();await settle(page);
  const initial=await snapshot(page);fits(initial);assert.equal(initial.desktop,false);
  await wheel(page,2000);const scrolled=await snapshot(page);
  stationary(initial,scrolled);assert.ok(scrolled.scrollTop>0);
  await page.locator('#language-controls .language-name').last().scrollIntoViewIfNeeded();
  await settle(page);stationary(initial,await snapshot(page));
  await page.locator('.controls').evaluate(el=>{el.scrollTop=el.scrollHeight;});
  await wheel(page,2000);stationary(initial,await snapshot(page));
  await page.locator('#close-filters').click();await settle(page);
  assert.equal(await page.evaluate(()=>scrollY),pageY,'Closing mobile filters restores page position');
  await page.locator('#open-filters').click();await settle(page);
  await page.setViewportSize({width:1280,height:800});await settle(page);
  fits(await snapshot(page));
  assert.equal(await page.locator('#filter-drawer').evaluate(el=>el.open),false);
  assert.equal(await page.evaluate(()=>document.documentElement.classList.contains('filters-open')),false);
  rows.push({width:390,height:844,initial,scrolled,checks:['mobile drawer','scroll chaining','last language','page position restored','open drawer resized to desktop']});
  await page.close();
  assert.deepEqual(errors,[]);
  const result={status:'PASSED',url,viewports:rows,page_errors:errors};
  if(output)await writeFile(output,JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({status:result.status,viewports:rows.map(r=>[r.width,r.height]),page_errors:errors}));
}finally{
  await browser.close();
  if(!live)await new Promise(resolve=>server.close(resolve));
}
