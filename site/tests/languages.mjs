import fs from 'node:fs';
import assert from 'node:assert/strict';
import {languageTraits,traitDimensions,emptyTraitFilters,filterLanguageKeys} from '../src/traits.mjs';
import {languageMetadata} from '../src/languages.mjs';
const data=process.argv[2]?JSON.parse(fs.readFileSync(process.argv[2])):{languages:Object.keys(languageMetadata).map(key=>({key}))};
const traits=languageTraits(data);
assert.deepEqual(data.languages.map(language=>language.key).sort(),Object.keys(languageMetadata).sort());
if(process.argv[2])for(const language of data.languages){
 const record=languageMetadata[language.key];
 assert.ok(record,`missing metadata: ${language.key}`);
 for(const [dataField,moduleField] of Object.entries({runtime_family:'platform',runtime:'runtime',execution_modes:'execution',typing:'typing',paradigms:'style',memory_models:'memory'}))
  assert.deepEqual(language[dataField],record[moduleField],`${language.key}: dataset / filter ${dataField} mismatch`);
}
assert.equal(traits.size,data.languages.length);
for (const [key,row] of traits) for(const dim of traitDimensions) {
 const valid=new Set(dim.options.map(x=>x.key));
 assert.ok(row[dim.key].size>0,`${key}:empty ${dim.key}`);
 for(const value of row[dim.key]) assert.ok(valid.has(value),`${key}:${dim.key}:${value}`);
}
for(const key of ['csharp','csharp-aot','fsharp','fsharp-aot']) assert.ok(traits.get(key).platform.has('dotnet'));
assert.ok(traits.get('clojure').platform.has('jvm'));
assert.ok(traits.get('java').platform.has('jvm'));
assert.ok(traits.get('java').execution.has('jit'));
assert.ok(!traits.get('java').execution.has('aot'));
assert.ok(traits.get('elm').platform.has('javascript'));
assert.ok(traits.get('c').memory.has('manual'));
assert.ok(!traits.get('c').memory.has('owned'));
assert.ok(traits.get('rust').memory.has('owned'));
assert.ok(!traits.get('rust').memory.has('manual'));
if(traits.has('luau')){
 assert.ok(traits.get('luau').typing.has('gradual'));
 assert.ok(traits.get('luau').execution.has('interpreted'));
 assert.ok(!traits.get('luau').execution.has('jit'));
 assert.ok(traits.get('luau-jit').execution.has('jit'));
 assert.ok(traits.get('luau-jit').typing.has('gradual'));
 const gradual=emptyTraitFilters();gradual.typing.add('gradual');
 assert.deepEqual([...filterLanguageKeys(new Set(traits.keys()),traits,gradual)].sort(),['luau','luau-jit']);
}
assert.ok(traits.get('nim').memory.has('cycles'));
assert.ok(!traits.get('nim').memory.has('gc'));
assert.ok(traits.get('php').execution.has('jit')&&traits.get('php').execution.has('interpreted'));
const filters=emptyTraitFilters(); filters.platform.add('dotnet'); filters.execution.add('aot');
assert.deepEqual([...filterLanguageKeys(new Set(traits.keys()),traits,filters)].sort(),['csharp-aot','fsharp-aot']);
console.log(`Passed: all ${traits.size} variants classified; JVM/.NET/V8, execution, memory distinctions, and combined filters.`);
console.log(JSON.stringify(Object.fromEntries(traitDimensions.map(d=>[d.key,Object.fromEntries(d.options.map(o=>[o.label,[...traits.values()].filter(t=>t[d.key].has(o.key)).length]))])),null,2));
