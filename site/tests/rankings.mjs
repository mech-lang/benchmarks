import assert from 'node:assert/strict';
import {renderRankingCharts} from '../src/rankings.mjs';
import {languageRelativeComparisons} from '../src/math.mjs';
import {axisData} from '../src/formatted_axis.mjs';

// Target-relative means use the same benchmark on both sides, including
// incomplete suites; existing chart coordinates and sources remain untouched.
const relativeFixture={languages:['target','full','partial','missing'].map(key=>({key})),benchmarks:[],programs:{}};
for(const [index,key] of ['a','b','c'].entries()){
  const benchmark={key,baseline_seconds:100,baseline_loc:100,groups:[]};
  for(const language of ['target','full','partial']){
    if(language==='partial'&&key!=='b')continue;
    const id=`${language}-${key}`;
    const seconds=language==='target'?[2,20,200][index]:language==='full'?[4,10,400][index]:80;
    const loc=language==='target'?[10,100,1000][index]:language==='full'?[20,50,2000][index]:25;
    relativeFixture.programs[id]={key:id,language,benchmark:key,seconds,loc,x:loc/100,y:seconds/100,
      formatted_loc_status:'qualified',formatted_loc_complete:true,formatted_loc:loc*2,formatted_x:loc/50};
    benchmark.groups.push({language,programs:[id]});
  }
  relativeFixture.benchmarks.push(benchmark);
}
const savedFixture=JSON.stringify(relativeFixture);
const relative=languageRelativeComparisons(relativeFixture,'target');
assert.equal(relative.length,4,'Every published variant must remain listed.');
assert.equal(relative[0].time.ratio,1);assert.equal(relative[0].loc.ratio,1);
assert.ok(Math.abs(relative[1].time.ratio-Math.cbrt(2))<1e-12);
assert.equal(relative[2].time.ratio,4,'Partial suite denominator must use target b=20, not its full-suite mean.');
assert.equal(relative[2].loc.ratio,.25);assert.deepEqual(relative[2].time.benchmarks,['b']);
assert.equal(relative[2].time.selected,3);assert.equal(relative[3].time.ratio,null);
const subset=languageRelativeComparisons(relativeFixture,'target',{benchmarks:new Set(['a','c'])});
assert.equal(subset[1].time.ratio,2);assert.equal(subset[2].time.ratio,null);assert.equal(subset[2].time.selected,2);
relativeFixture.programs['partial-b'].formatted_loc_complete=false;
const formatted=languageRelativeComparisons(relativeFixture,'target',{locData:axisData(relativeFixture,'formatted')});
assert.equal(formatted[2].time.ratio,4,'Missing formatted LOC must not erase a qualified time comparison.');
assert.equal(formatted[2].loc.ratio,null);
relativeFixture.programs['partial-b'].formatted_loc_complete=true;
assert.equal(JSON.stringify(relativeFixture),savedFixture,'Pairwise views must not rewrite catalog values.');
relativeFixture.programs['partial-b'].eligible_for_chart=false;
assert.equal(languageRelativeComparisons(relativeFixture,'target')[2].time.ratio,null);
assert.ok(languageRelativeComparisons(relativeFixture,'missing').every(row=>row.time.ratio===null));
console.log('Language-relative comparisons: same-workload ratios, partial/missing coverage, formatted independence and source preservation passed.');

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
