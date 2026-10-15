import assert from 'node:assert/strict';
import {comparison,languageRelativeComparisons,eligibleForChart,gm,spread} from '../src/math.mjs';
import {axisData} from '../src/formatted_axis.mjs';

// The previous full chart-model path is the independent selection/aggregation
// oracle. Keep its group search, reductions and summation order unchanged.
function previousComparison(data,selection){
  const benchmarks=data.benchmarks.filter(b=>selection.benchmarks.has(b.key));
  const entries=[];
  for(const language of data.languages){
    if(!selection.languages.has(language.key))continue;
    const inputs=[];
    for(const benchmark of benchmarks){
      const group=benchmark.groups.find(g=>g.language===language.key);
      const programs=(group?.programs??[]).filter(k=>!selection.disabled.has(k)).map(k=>data.programs[k]).filter(p=>eligibleForChart(p)&&Number.isFinite(p.seconds)&&p.seconds>0&&Number.isFinite(p.loc)&&p.loc>0&&Number.isFinite(p.x)&&p.x>0&&Number.isFinite(p.y)&&p.y>0);
      if(!programs.length)continue;
      const fast=programs.reduce((a,b)=>b.seconds<a.seconds||(b.seconds===a.seconds&&b.loc<a.loc)?b:a);
      const small=programs.reduce((a,b)=>b.loc<a.loc||(b.loc===a.loc&&b.seconds<a.seconds)?b:a);
      inputs.push({benchmark,fast,small,programs});
    }
    if(!inputs.length)continue;
    const included=new Set(inputs.map(input=>input.benchmark.key));
    const coverage={measured:inputs.length,selected:benchmarks.length,missing:benchmarks.filter(b=>!included.has(b.key))};
    const mean=kind=>({x:gm(inputs.map(i=>i[kind].x)),y:gm(inputs.map(i=>i[kind].y))});
    entries.push({language,inputs,coverage,fast:mean('fast'),small:mean('small'),
      spread:{fast:spread(inputs.map(i=>i.fast)),small:spread(inputs.map(i=>i.small))},
      spread2:{fast:spread(inputs.map(i=>i.fast),{sigma:2}),small:spread(inputs.map(i=>i.small),{sigma:2})}});
  }
  return {benchmarks,entries};
}
function previousRelative(data,target,{benchmarks,locData=data}={}){
  const selected=benchmarks??new Set(data.benchmarks.map(b=>b.key));
  const selection={benchmarks:selected,languages:new Set(data.languages.map(l=>l.key)),disabled:new Set()};
  const times=previousComparison(data,selection),lines=locData===data?times:previousComparison(locData,selection);
  const metric=(model,key,kind,field)=>{
    const reference=new Map((model.entries.find(e=>e.language.key===target)?.inputs??[]).map(i=>[i.benchmark.key,i]));
    const shared=(model.entries.find(e=>e.language.key===key)?.inputs??[]).filter(i=>reference.has(i.benchmark.key));
    return {ratio:shared.length?gm(shared.map(i=>i[kind][field]/reference.get(i.benchmark.key)[kind][field])):null,
      benchmarks:shared.map(i=>i.benchmark.key),selected:model.benchmarks.length};
  };
  return data.languages.map(language=>({language,target:language.key===target,
    time:metric(times,language.key,'fast','seconds'),loc:metric(lines,language.key,'small','loc')}));
}

function fixture(){
  const data={languages:['target','full','partial','missing'].map(key=>({key})),benchmarks:[],programs:{}};
  for(const [index,key] of ['z','a','m'].entries()){
    const b={key,baseline_seconds:7,baseline_loc:11,baseline_formatted_loc:13,groups:[]};
    for(const language of ['target','full','partial']){
      if(language==='partial'&&key!=='a')continue;
      const ids=[];
      for(const [variant,seconds,loc] of [['fast',2+index,29+index],['small',7+index,13+index],['tie',2+index,29+index]]){
        const id=`${language}-${key}-${variant}`,factor=language==='target'?1:language==='full'?[.3,7,1.1][index]:3;
        ids.push(id);
        data.programs[id]={key:id,language,benchmark:key,seconds:seconds*factor,loc,x:loc/11,y:seconds*factor/7,
          formatted_loc:loc+index+3,formatted_x:(loc+index+3)/13,
          formatted_loc_status:'qualified',formatted_loc_complete:true};
      }
      b.groups.push({language,programs:ids});
    }
    data.benchmarks.push(b);
  }
  // A later duplicate must never replace the first matching group. An empty
  // first group must likewise remain empty despite a later available group.
  data.benchmarks[0].groups.push({language:'target',programs:['full-z-small']});
  data.benchmarks[0].groups.push({language:'missing',programs:[]},{language:'missing',programs:['full-z-fast']});
  data.benchmarks[1].groups[0].programs.push('unknown-program');
  return data;
}
let comparisons=0,relatives=0;
function equivalent(data,label){
  const before=structuredClone(data),formatted=axisData(data,'formatted');
  const scopes=[undefined,new Set(['m','z']),new Set(['a']),new Set(),new Set(['unpublished'])];
  for(const benchmarks of scopes){
    for(const locData of [data,formatted])for(const target of ['target','full','partial','missing','unknown']){
      const options={benchmarks,locData};
      assert.deepEqual(languageRelativeComparisons(data,target,options),previousRelative(data,target,options),`${label}: exact ratios, membership and ordering`);
      relatives++;
    }
    for(const axis of [data,formatted])for(const languages of [new Set(data.languages.map(l=>l.key)),new Set(['target','partial']),new Set()]){
      for(const disabled of [new Set(),new Set(['target-z-fast','full-a-small'])]){
        const selection={benchmarks:benchmarks??new Set(data.benchmarks.map(b=>b.key)),languages,disabled};
        assert.deepEqual(comparison(axis,selection),previousComparison(axis,selection),`${label}: exact complete chart model`);
        comparisons++;
      }
    }
  }
  assert.deepEqual(data,before,`${label}: input values remain unchanged`);
}

const base=fixture();
equivalent(base,'first groups, ties, partial and empty selections');
const input=comparison(base,{benchmarks:new Set(['z']),languages:new Set(['target']),disabled:new Set()}).entries[0].inputs[0];
assert.equal(input.fast,base.programs['target-z-fast'],'An exact tie keeps the first original program object.');
assert.equal(input.small,base.programs['target-z-small']);
assert.equal(input.benchmark,base.benchmarks[0]);
assert.deepEqual(input.programs.map(p=>p.key),['target-z-fast','target-z-small','target-z-tie']);
assert.deepEqual(languageRelativeComparisons(base,'target',{benchmarks:new Set(['m','z'])})[1].time.benchmarks,['z','m'],'Benchmark order comes from the dataset, not Set insertion order.');

for(const [field,values] of [['seconds',[0,-1,null,NaN,Infinity,true]],['loc',[0,null,NaN]],['x',[0,Infinity]],['y',[-1,NaN]]]){
  for(const value of values){
    const data=fixture();
    for(const id of data.benchmarks[1].groups.find(g=>g.language==='partial').programs)data.programs[id][field]=value;
    equivalent(data,`invalid ${field} ${String(value)}`);
  }
}
const excluded=fixture();
for(const id of excluded.benchmarks[1].groups.find(g=>g.language==='partial').programs)excluded.programs[id].eligible_for_chart=false;
equivalent(excluded,'explicit publication exclusions');
const incomplete=fixture();
for(const id of incomplete.benchmarks[1].groups.find(g=>g.language==='partial').programs)incomplete.programs[id].formatted_loc_complete=false;
equivalent(incomplete,'missing formatted counts');
const mixed=languageRelativeComparisons(incomplete,'target',{locData:axisData(incomplete,'formatted')}).find(row=>row.language.key==='partial');
assert.equal(mixed.time.ratio,gm([3]));assert.equal(mixed.loc.ratio,null);

// No persistent cache may hide a caller's later change to this public API.
const mutable=fixture(),beforeMutation=languageRelativeComparisons(mutable,'target');
mutable.programs['full-z-fast'].seconds=1000;
mutable.programs['full-z-tie'].eligible_for_chart=false;
assert.deepEqual(languageRelativeComparisons(mutable,'target'),previousRelative(mutable,'target'));
assert.notDeepEqual(languageRelativeComparisons(mutable,'target'),beforeMutation);

// A separately supplied LOC dataset can have different coverage and order.
const otherLOC=fixture();
otherLOC.benchmarks.reverse();otherLOC.benchmarks.pop();
otherLOC.languages.reverse();
assert.deepEqual(languageRelativeComparisons(base,'target',{locData:otherLOC}),previousRelative(base,'target',{locData:otherLOC}));

// Relative ratios use Math.log through gm; they must not enter the log2
// covariance/contour path merely to discard its result.
const expectedEndpointOnly=previousRelative(base,'target'),log2=Math.log2;
try{
  Math.log2=()=>{throw new Error('Unexpected chart geometry in endpoint-only comparison.');};
  assert.deepEqual(languageRelativeComparisons(base,'target'),expectedEndpointOnly);
}finally{Math.log2=log2;}
console.log(`Relative endpoint extraction: ${relatives} exact relative comparisons and ${comparisons} complete-model comparisons passed; no chart geometry, input mutation or persistent cache.`);
