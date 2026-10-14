import assert from 'node:assert/strict';
import {renderRankingCharts} from '../src/rankings.mjs';

// Exercise label packing at phone and desktop widths without a browser process.
let viewportWidth;
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.dataset={};this.style={};this.listeners={};this.textContent='';}
  get clientWidth(){return viewportWidth;}
  append(child){
    if(child.parentNode)child.parentNode.children=child.parentNode.children.filter(node=>node!==child);
    child.parentNode=this;this.children.push(child);
  }
  replaceChildren(){this.children=[];}
  setAttribute(name,value){this.attributes[name]=String(value);}
  removeAttribute(name){delete this.attributes[name];}
  getBBox(){return {width:this.textContent.length*7,height:11};}
  addEventListener(name,callback){this.listeners[name]=callback;}
}
globalThis.document={createElement:tag=>new Element(tag),createElementNS:(_ns,tag)=>new Element(tag)};
const descendants=node=>node.children.flatMap(child=>[child,...descendants(child)]);
const names=['Common Lisp (SBCL)','Mech interpreted','JavaScript','C','Rust'];
const rows=Array.from({length:55},(_,index)=>({
  entry:{language:{key:String(index)},coverage:{measured:10,selected:10}},
  value:1+index,ratio_to_median:(1+index)/28,
  sigma_distance:index===0?-3:index===54?3:(index-27)/45,
}));
const metric={n:rows.length,median:28,log_sample_sd:1,max_abs_sigma:3,entries:rows};
const opened=[];
for(viewportWidth of [240,320,640,1200]){
  const container=new Element('div');
  renderRankingCharts({container,rankings:{speed:metric,loc:metric},
    labelFor:key=>names[Number(key)%names.length],colorFor:()=>'#abcdef',onOpenLanguage:key=>opened.push(key)});
  assert.equal(container.children.length,2);
  for(const card of container.children){
    const chart=card.children.find(node=>node.tagName==='svg');
    const width=Number(chart.attributes.viewBox.split(' ')[2]);
    assert.equal(width,viewportWidth);
    const marks=chart.children.filter(node=>node.attributes.class==='ranking-mark');
    assert.equal(marks.length,55);
    assert.equal(descendants(chart).filter(node=>node.tagName==='text'&&node.attributes.class==='ranking-language-label').length,55);
    const lanes=new Map();
    for(const mark of marks){
      const dot=mark.children.find(node=>node.tagName==='circle'),label=mark.children.find(node=>node.tagName==='text');
      const id=Number(mark.attributes['data-ranking-language']),x=Number(dot.attributes.cx),y=Number(dot.attributes.cy);
      assert.equal(x,32+(rows[id].sigma_distance+3)/6*(width-56),'A label must never move its data point horizontally.');
      assert.equal(label.textContent,names[id%names.length]);
      assert.equal(label.attributes.visibility,undefined);
      assert.equal(mark.attributes.role,'button');
      const labelX=Number(label.attributes.x),labelWidth=label.getBBox().width;
      const start=label.attributes['text-anchor']==='end'?labelX-labelWidth:labelX;
      const end=start+labelWidth;
      assert.ok(start>=0&&end<=width,`Label clipped at width ${width}`);
      const span=[Math.min(start,x-4.5),Math.max(end,x+4.5)];
      for(const prior of lanes.get(y)??[])assert.ok(span[0]>=prior[1]+12||prior[0]>=span[1]+12,'Same-row labels and dots overlap.');
      lanes.set(y,[...(lanes.get(y)??[]),span]);
      mark.listeners.focus();mark.listeners.click();
      assert.equal(opened.at(-1),String(id));
      let prevented=false;mark.listeners.keydown({key:'Enter',preventDefault(){prevented=true;}});assert.ok(prevented);
    }
  }
}
console.log('Ranking labels: 440 marks checked across four widths; positions, spacing and interactions passed.');
