// Runtime families are audited per measured variant. Exact historical version,
// flag, and binary receipts are separate provenance facts, not prerequisites for
// knowing that (for example) a recorded dotnet command belongs to .NET.
import {languageMetadata} from './languages.mjs';

export const platformDimension={key:'platform',label:'Runtime / toolchain',
  note:'The measured runtime or toolchain family. .NET includes JIT and NativeAOT; Node.js / V8 includes JavaScript and Elm.',options:[
    {key:'native',label:'Native toolchains'},
    {key:'jvm',label:'JVM'},
    {key:'dotnet',label:'.NET'},
    {key:'beam',label:'BEAM'},
    {key:'javascript',label:'Node.js / V8'},
    {key:'runtime',label:'Other language runtimes'},
  ]};

export function measuredPlatform(_data,language) {
  const record=languageMetadata[language.key];
  return {
    platform:new Set(record?[record.platform]:['unknown']),
    execution:record?.execution.length===1?record.execution[0]:null,
    executions:new Set(record?.execution??['unknown']),
    execution_authoritative:!!record,
    runtime:record?.runtime??'Unaudited runtime',
    note:record?.note??'This variant is not in the reviewed language catalog.',
  };
}
