// Versioned, catalog-validated links. Defaults stay compact; empty selections
// are explicit. URL data never supplies markup, source code or object keys.
const lists={benchmarks:'benchmarks',languages:'languages',ellipses:'ellipses',disabled:'disabled',collapsedFamilies:'collapsed'};
const enums={view:['summary','benchmark','mech','rankings','language','data'],locMetric:['canonical','formatted','logical','bytes','gzip','bpe'],sampleMode:['off','dim','highlight'],medianMode:['off','dim','highlight'],densityMode:['off','dim','highlight']};
const booleans=['fast','small','focusMeans','global','benchmarkExpanded','languageExpanded'];
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const sorted=values=>[...values].sort();

export function encodeView(view,defaults){
  const p=new URLSearchParams({v:'1'});
  const put=(key,value,baseline)=>{if(!equal(value,baseline))p.set(key,String(value));};
  for(const [key,param] of Object.entries(lists))put(param,sorted(view[key]).join(','),sorted(defaults[key]).join(','));
  for(const key of Object.keys(enums))put(key,view[key],defaults[key]);
  for(const key of booleans)put(key,Number(view[key]),Number(defaults[key]));
  put('benchmark',view.focus,defaults.focus);
  for(const key of ['releaseYearStart','releaseYear','playbackYear'])if(view[key]!=null)put(key,view[key],defaults[key]);
  for(const category of ['traits','benchmarkFilters']){
    const active=Object.entries(view[category]).flatMap(([key,values])=>sorted(values).map(value=>key+':'+value));
    if(active.length)p.set(category,active.join(','));
  }
  const focus=view.languageFocus;
  if(focus){
    p.set('language',focus.selectionKey);
    if(focus.family)p.set('family','1');
    p.set('variant',focus.variant);p.set('languageBenchmark',focus.benchmark);
    if(focus.program)p.set('languageProgram',focus.program);
    if(focus.comparison)p.set('compare','1');
    if(focus.comparisonLanguage)p.set('with',focus.comparisonLanguage);
    if(focus.comparisonProgram)p.set('compareProgram',focus.comparisonProgram);
  }
  if(view.inspectorOpen){
    p.set('inspect','1');
    for(const key of ['language','benchmark','kind','program','file','aggregate'])
      if(view.detail[key]!=null)p.set('detail.'+key,String(view.detail[key]));
  }
  for(const [table,sort] of Object.entries(view.tableSort))
    if(!equal(sort,defaults.tableSort[table]))p.set('sort.'+table,`${sort.key??''}:${sort.direction}`);
  if((view.dataQuery??'')!==(defaults.dataQuery??''))p.set('query',view.dataQuery??'');
  for(const key of ['dataPage','dataPageSize'])if(view[key]!=null)put(key,view[key],defaults[key]);
  if(!equal(sorted(view.dataSelected??[]),sorted(defaults.dataSelected??[]))){
    // Group run numbers by stable program key to keep a full selection compact.
    const groups=new Map();
    for(const id of sorted(view.dataSelected??[])){
      const at=id.lastIndexOf('#'),key=id.slice(0,at),run=Number(id.slice(at+1));
      if(!groups.has(key))groups.set(key,[]);groups.get(key).push(run);
    }
    p.set('rows',JSON.stringify([...groups]));
  }
  if(view.languageTab&&!focus){
    const tabDefaults={...defaults};
    for(const key of ['dataQuery','dataPage','dataPageSize','dataSelected'])if(Object.hasOwn(defaults,key))tabDefaults[key]=view[key];
    p.set('tab',encodeView({...view.languageTab,languageTab:null},tabDefaults).slice(1));
  }
  return '#'+p.toString();
}

export function decodeView(hash,defaults,spec,nested=false){
  const p=new URLSearchParams(hash.replace(/^#/,''));
  if(p.get('v')!=='1'||hash.length>100000)return null;
  const result=structuredClone(defaults);
  for(const [key,param] of Object.entries(lists))if(p.has(param)){
    const allowed=new Set(spec[key]);
    result[key]=[...new Set(p.get(param).split(',').filter(value=>allowed.has(value)))];
  }
  for(const [key,values] of Object.entries(enums))if(values.includes(p.get(key)))result[key]=p.get(key);
  for(const key of booleans)if(['0','1'].includes(p.get(key)))result[key]=p.get(key)==='1';
  if(spec.benchmarks.includes(p.get('benchmark')))result.focus=p.get('benchmark');
  for(const key of ['releaseYearStart','releaseYear','playbackYear'])if(p.has(key)){
    const value=Number(p.get(key));
    if(Number.isInteger(value)&&value>=spec.yearMin&&value<=spec.yearMax)result[key]=value;
  }
  if(result.releaseYearStart>result.releaseYear)[result.releaseYearStart,result.releaseYear]=[result.releaseYear,result.releaseYearStart];
  if(result.playbackYear!=null)result.playbackYear=Math.max(result.releaseYearStart,Math.min(result.releaseYear,result.playbackYear));
  for(const category of ['traits','benchmarkFilters'])if(p.has(category)){
    for(const item of p.get(category).split(',')){
      const [key,value]=item.split(':');
      if(Object.hasOwn(result[category],key)&&spec[category][key]?.includes(value)&&!result[category][key].includes(value))result[category][key].push(value);
    }
  }
  const selectionKey=p.get('language'),family=p.get('family')==='1';
  const keys=family?(Object.hasOwn(spec.families,selectionKey)?spec.families[selectionKey]:null):spec.languages.includes(selectionKey)?[selectionKey]:null;
  if(keys?.length){
    const variant=keys.includes(p.get('variant'))?p.get('variant'):keys[0];
    const validProgram=(param,language=variant)=>{
      const key=p.get(param),program=Object.hasOwn(spec.programs,key)?spec.programs[key]:null;
      return program?.language===language?key:null;
    };
    result.languageFocus={selectionKey,family,variant,
      benchmark:spec.benchmarks.includes(p.get('languageBenchmark'))?p.get('languageBenchmark'):result.focus,
      program:validProgram('languageProgram'),comparison:p.get('compare')==='1',
      comparisonLanguage:spec.languages.includes(p.get('with'))?p.get('with'):null,
      comparisonProgram:validProgram('compareProgram')};
    if(result.languageFocus.comparison&&!result.languageFocus.comparisonLanguage)result.languageFocus.comparison=false;
  }else if(result.view==='language')result.view='summary';
  if(p.get('inspect')==='1'){
    const programKey=p.get('detail.program');
    const program=Object.hasOwn(spec.programs,programKey)?spec.programs[programKey]:null;
    const language=program?.language??p.get('detail.language'),benchmark=program?.benchmark??p.get('detail.benchmark');
    if(spec.languages.includes(language)&&spec.benchmarks.includes(benchmark)&&
        Object.values(spec.programs).some(item=>item.language===language&&item.benchmark===benchmark)){
      const file=Number(p.get('detail.file'));
      result.detail={language,benchmark,program:program?programKey:null,
        kind:p.get('detail.kind')==='small'?'small':'fast',aggregate:p.get('detail.aggregate')==='true',
        file:Number.isSafeInteger(file)&&file>=0?Math.min(file,(program?.files.length??1)-1):0};
      result.inspectorOpen=true;
    }
  }
  for(const [table,keys] of Object.entries(spec.sorts))if(p.has('sort.'+table)){
    const [key,direction]=p.get('sort.'+table).split(':');
    if(keys.includes(key)&&['1','-1'].includes(direction))result.tableSort[table]={key:key||null,direction:Number(direction)};
  }
  if(Object.hasOwn(defaults,'dataQuery')){
    if(p.has('query'))result.dataQuery=p.get('query').slice(0,500);
    for(const key of ['dataPage','dataPageSize']){
      if(!p.has(key))continue;
      const value=Number(p.get(key));
      if(Number.isSafeInteger(value)&&(key==='dataPage'?value>=0&&value<100000:[50,100,250].includes(value)))result[key]=value;
    }
    if(p.has('rows'))try{
      const groups=JSON.parse(p.get('rows')),allowed=new Set(spec.sampleIDs??[]);
      if(Array.isArray(groups))result.dataSelected=[...new Set(groups.flatMap(group=>
        Array.isArray(group)&&typeof group[0]==='string'&&Array.isArray(group[1])?
          group[1].filter(Number.isSafeInteger).map(run=>group[0]+'#'+run).filter(id=>allowed.has(id)):[]))].sort();
    }catch{/* Malformed row selections leave the catalog defaults intact. */}
  }
  if(!nested&&!result.languageFocus&&p.has('tab')){
    const tabDefaults={...defaults};
    for(const key of ['dataQuery','dataPage','dataPageSize','dataSelected'])if(Object.hasOwn(defaults,key))tabDefaults[key]=result[key];
    const tab=decodeView('#'+p.get('tab'),tabDefaults,spec,true);
    if(tab?.languageFocus)result.languageTab=tab;
  }
  return result;
}
