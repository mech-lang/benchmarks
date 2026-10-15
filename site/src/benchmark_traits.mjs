// Descriptive workload categories; these do not change measured catalog data.
// I/O denotes bulk input/output, rather than small result printing. Memory
// denotes substantial buffers, allocation or indexing state, not every load.
export const benchmarkDimensions = [
  {key:'resource',label:'Resource emphasis',note:'Workload emphasis, not a measured bottleneck; implementations vary. I/O means bulk input or output.',options:[
    {key:'compute',label:'Compute'},{key:'memory',label:'Memory'},{key:'io',label:'I/O'}]},
  {key:'workload',label:'Workload type',options:[
    {key:'numerical',label:'Numerical'},{key:'strings',label:'Strings & sequences'},
    {key:'allocation',label:'Allocation'},{key:'data-structures',label:'Data structures'},
    {key:'combinatorial',label:'Combinatorial'},{key:'graphics',label:'Graphics'}]},
];

export const benchmarkTraits = {
  binarytrees:{resource:['memory'],workload:['allocation','data-structures']},
  fannkuchredux:{resource:['compute'],workload:['combinatorial']},
  fasta:{resource:['compute','io'],workload:['strings']},
  knucleotide:{resource:['compute','memory','io'],workload:['strings','data-structures']},
  mandelbrot:{resource:['compute','io'],workload:['numerical','graphics']},
  nbody:{resource:['compute'],workload:['numerical']},
  pidigits:{resource:['compute'],workload:['numerical']},
  regexredux:{resource:['compute','memory','io'],workload:['strings']},
  revcomp:{resource:['memory','io'],workload:['strings']},
  spectralnorm:{resource:['compute'],workload:['numerical']},
};

export const emptyBenchmarkFilters = ()=>Object.fromEntries(benchmarkDimensions.map(({key})=>[key,new Set()]));

export function matchesBenchmark(key,filters,skipDimension=null){
  return benchmarkDimensions.every(({key:dimension})=>dimension===skipDimension||!filters[dimension]?.size||
    [...filters[dimension]].some(option=>benchmarkTraits[key]?.[dimension]?.includes(option)));
}

export function filterBenchmarkKeys(keys,filters){
  return new Set([...keys].filter(key=>matchesBenchmark(key,filters)));
}
