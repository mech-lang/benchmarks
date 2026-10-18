// Each measured variant has explicit reviewed metadata. Choices within a
// dimension are alternatives; active dimensions are intersected. Paradigms and
// memory models intentionally overlap and do not claim per-source usage.
import {platformDimension,measuredPlatform} from './platform.mjs';
import {languageMetadata} from './languages.mjs';

export const traitDimensions = [
  platformDimension,
  {key:'execution',label:'Execution',note:'Native AOT, native JIT, or interpretation in the measured variant. A series may contain more than one mode.',options:[
    {key:'aot',label:'AOT'}, {key:'jit',label:'JIT'}, {key:'interpreted',label:'Interpreted'}]},
  {key:'typing',label:'Typing',options:[
    {key:'static',label:'Static'}, {key:'dynamic',label:'Dynamic'}, {key:'gradual',label:'Gradual'}]},
  {key:'style',label:'Paradigm',note:'Established language styles; a language may support several.',options:[
    {key:'imperative',label:'Imperative'}, {key:'object',label:'Object-oriented'},
    {key:'functional',label:'Functional'}, {key:'logic',label:'Logic'}, {key:'array',label:'Array'},
    {key:'reactive',label:'Reactive / dataflow'}]},
  {key:'memory',label:'Memory management',note:'Standard models of the measured language/runtime. Strategies can coexist; foreign libraries and optional alternate collectors are excluded.',options:[
    {key:'manual',label:'Manual allocation'}, {key:'owned',label:'Ownership / RAII'},
    {key:'rc',label:'Reference counting'}, {key:'gc',label:'Tracing GC'},
    {key:'cycles',label:'Cycle collection'}]},
];

export function languageTraits(data) {
  return new Map(data.languages.map(language=>{
    const record=languageMetadata[language.key];
    const measured=measuredPlatform(data,language);
    return [language.key,{
      platform:measured.platform,
      execution:measured.executions,
      typing:new Set(record?[record.typing]:['unknown']),
      style:new Set(record?.style??['unknown']),
      memory:new Set(record?.memory??['unknown']),
      runtime:measured.runtime,
      note:measured.note,
    }];
  }));
}

export const emptyTraitFilters = ()=>Object.fromEntries(traitDimensions.map(dimension=>[dimension.key,new Set()]));

export function matchesTraits(traits,filters,skipDimension=null) {
  return traitDimensions.every(({key})=>key===skipDimension||!filters[key]?.size||
    [...filters[key]].some(option=>traits?.[key]?.has(option)));
}

export function filterLanguageKeys(keys,traits,filters) {
  return new Set([...keys].filter(key=>matchesTraits(traits.get(key),filters)));
}
