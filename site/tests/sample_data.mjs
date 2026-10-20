import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sampleRows,filterSamples,sortSamples,exportRows,samplesCSV,sampleColumns} from '../src/sample_data.mjs';
import {encodeView,decodeView} from '../src/view_state.mjs';

const data=JSON.parse(readFileSync(new URL('../public/data.json',import.meta.url))),catalog={...data.program_inventory,...data.programs};
const rows=sampleRows(data),owners=Object.values(catalog).filter(p=>!p.timing_alias_of);
assert.equal(rows.length,owners.reduce((sum,p)=>sum+p.samples.length,0));
assert.equal(new Set(rows.map(r=>r.id)).size,rows.length);
for(const r of rows){
  const p=catalog[r.program];assert.equal(r.seconds,p.samples[r.run-1]);assert.equal(r.loc,p.loc);
  assert.equal(r.median_seconds,p.seconds);assert.equal(r.report,p.report);
  assert.equal(r.formatted_loc,p.formatted_loc_complete===true?p.formatted_loc:null);
  assert.equal(r.qualified_logical_units,p.logical_source_units?.status==='qualified'?p.logical_source_units.application:null);
  assert.deepEqual(r.logical_source_definitions,data.logical_source_units??null);
  assert.equal(r.implementations[0].key,p.key);
}
for(const p of Object.values(catalog).filter(p=>p.timing_alias_of)){
  const shared=rows.filter(r=>r.implementations.some(i=>i.key===p.key));
  assert.equal(shared.length,p.samples.length);assert.ok(shared.every(r=>r.program===p.timing_alias_of));
}
const lean=filterSamples(rows,{languages:new Set(['lean4']),benchmarks:new Set(['nbody'])});
assert.equal(lean.length,9);assert.ok(lean.every(r=>r.language==='lean4'&&r.benchmark==='nbody'));
assert.equal(filterSamples(rows,{languages:new Set()}).length,0);
assert.equal(filterSamples(rows,{query:'LEAN n-body'}).length,lean.length);
for(const [key] of sampleColumns){
  const ascending=sortSamples(rows,{key,direction:1}),descending=sortSamples(rows,{key,direction:-1});
  assert.equal(ascending.length,rows.length);assert.equal(descending.length,rows.length);
  if(typeof rows.find(r=>r[key]!=null)?.[key]==='number')for(const list of [ascending,descending]){
    const values=list.map(r=>r[key]).filter(v=>v!=null),sign=list===ascending?1:-1;
    assert.ok(values.slice(1).every((v,i)=>sign*(v-values[i])>=0),key);
  }
}
const records=exportRows(lean,p=>'https://example.test/#'+encodeURIComponent(p.key));
assert.deepEqual(records.map(r=>r.seconds),lean.map(r=>r.seconds));
assert.ok(records.every(r=>r.implementation_url.includes(encodeURIComponent(r.program_key))));
const csv=samplesCSV(records);assert.equal(csv.split('\r\n').length,records.length+2);
assert.ok(csv.includes(String(lean[0].seconds)));
assert.ok(samplesCSV([{language:'=1+1',implementation:'a,"b"\nline'}]).includes('"\'=1+1"'));
assert.ok(samplesCSV([{implementation:'a,"b"\nline'}]).includes('"a,""b""\nline"'));
// Missing timing qualification must never be silently converted into a ratio;
// independent equal observations remain independent; filtering aliases is explicit.
const p=catalog[lean[0].program],fixture={...data,program_inventory:{},programs:{
  a:{...p,key:'a',id:'a',samples:[2,2,3],seconds:null},b:{...p,key:'b',id:'b',samples:[2,2,3],seconds:2},
  shared:{...p,key:'shared',id:'shared',timing_alias_of:'b',samples:[2,2,3],seconds:2}}};
const equal=sampleRows(fixture);assert.equal(equal.length,6);assert.equal(equal.filter(r=>r.time_x_best==null).length,3);
assert.equal(filterSamples(equal,{disabled:new Set(['b'])}).length,6);
assert.equal(filterSamples(equal,{disabled:new Set(['b','shared'])}).length,3);
fixture.programs.b.logical_source_units={status:'qualified',application:10,policy:'fixture.owner-v1'};
fixture.programs.shared.logical_source_units={status:'qualified',application:20,policy:'fixture.owner-v1'};
fixture.programs.a.logical_source_units={status:'draft',application:1,policy:'unreviewed'};
fixture.programs.a.eligible_for_chart=false;
fixture.logical_source_units={partial_coverage:true,policies:{'fixture.owner-v1':{report_sha256:'pinned'}}};
const logicalRows=sampleRows(fixture),logicalExports=exportRows(logicalRows,p=>p.key);
assert.equal(logicalRows.length,6,'Source owner aliases do not create extra timing observations.');
assert.equal(logicalRows.find(r=>r.program==='a').qualified_logical_units,null);
assert.equal(logicalRows.find(r=>r.program==='a').eligible,false,'Historical excluded observations remain in Data.');
assert.ok(logicalExports.filter(r=>r.program_key==='b').every(r=>r.qualified_logical_units===10&&r.logical_units_policy==='fixture.owner-v1'));
assert.equal(logicalExports.find(r=>r.program_key==='b').timing_aliases[0].logical_source_units.application,20);
assert.deepEqual(logicalExports[0].logical_source_definitions,fixture.logical_source_units);
assert.ok(samplesCSV(logicalExports).includes('qualified_logical_units,logical_units_status,logical_units_policy'));

const defaults={view:'summary',focus:'nbody',benchmarks:data.benchmarks.map(b=>b.key),languages:data.languages.map(l=>l.key),
  ellipses:[],disabled:[],collapsedFamilies:[],traits:{},benchmarkFilters:{},releaseYearStart:1950,releaseYear:2026,
  dataQuery:'',dataPage:0,dataPageSize:100,dataSelected:[],tableSort:{data:{key:'language_label',direction:1}}};
const spec={...defaults,yearMin:1950,yearMax:2026,families:{},programs:catalog,traits:{},benchmarkFilters:{},
  sorts:{data:sampleColumns.map(([k])=>k)},sampleIDs:rows.map(r=>r.id)};
const selected={...defaults,view:'data',dataQuery:'Lean nbody',dataPage:4,dataPageSize:250,
  dataSelected:rows.map(r=>r.id).sort(),tableSort:{data:{key:'seconds',direction:-1}}};
const hash=encodeView(selected,defaults);assert.ok(hash.length<100000);
const restored=decodeView(hash,defaults,spec);
for(const key of ['view','dataQuery','dataPage','dataPageSize','dataSelected','tableSort'])assert.deepEqual(restored[key],selected[key]);
const tab={...selected,view:'language',languageFocus:{selectionKey:'lean4',family:false,variant:'lean4',benchmark:'nbody',program:null,comparison:false,comparisonLanguage:null,comparisonProgram:null}};
const withTab=encodeView({...selected,languageTab:tab},defaults);
assert.ok(withTab.length<100000);assert.deepEqual(decodeView(withTab,defaults,spec).languageTab.dataSelected,selected.dataSelected);
assert.deepEqual(decodeView('#v=1&rows=notjson&dataPage=-1&dataPageSize=9999',defaults,spec).dataSelected,[]);
assert.deepEqual(decodeView('#v=1&rows='+encodeURIComponent(JSON.stringify([['__proto__',[1]],['missing',[2]]])),defaults,spec).dataSelected,[]);
console.log(`Sample data: ${rows.length} exact observations, aliases, filters, ${sampleColumns.length} sorts, CSV precision/escaping and full-selection URL (${hash.length} bytes) PASS`);
