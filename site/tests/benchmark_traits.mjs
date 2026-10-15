import assert from 'node:assert/strict';
import {benchmarkDimensions,benchmarkTraits,emptyBenchmarkFilters,matchesBenchmark,filterBenchmarkKeys} from '../src/benchmark_traits.mjs';

const keys=Object.keys(benchmarkTraits),filters=emptyBenchmarkFilters();
assert.equal(keys.length,10);
for(const [key,traits] of Object.entries(benchmarkTraits))for(const dimension of benchmarkDimensions){
  assert.ok(traits[dimension.key].length,`${key} needs a ${dimension.key} category`);
  assert.equal(new Set(traits[dimension.key]).size,traits[dimension.key].length);
  assert.ok(traits[dimension.key].every(value=>dimension.options.some(option=>option.key===value)));
}
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],keys,'Empty groups preserve manual selection.');
filters.resource.add('memory');
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],['binarytrees','knucleotide','regexredux','revcomp']);
filters.resource.add('compute');
assert.equal(filterBenchmarkKeys(keys,filters).size,10,'Resource choices form a union, not an intersection.');
filters.workload.add('numerical');
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],['mandelbrot','nbody','pidigits','spectralnorm']);
filters.resource=new Set(['io']);
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],['mandelbrot'],'Different groups intersect.');
filters.workload.add('strings');
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],['fasta','knucleotide','mandelbrot','regexredux','revcomp']);
filters.workload=new Set(['allocation']);
assert.equal(filterBenchmarkKeys(keys,filters).size,0,'A valid empty intersection stays empty.');
filters.resource.clear();
assert.deepEqual([...filterBenchmarkKeys(keys,filters)],['binarytrees']);
assert.ok(matchesBenchmark('binarytrees',filters,'workload'));
assert.deepEqual([...filterBenchmarkKeys(['nbody'],filters)],[],'Category filters cannot add a manually excluded benchmark.');
const other=emptyBenchmarkFilters();other.resource.add('memory');
assert.equal(filters.resource.size,0,'Filter sets are independent.');
assert.ok(matchesBenchmark('future-benchmark',emptyBenchmarkFilters()),'Unclassified future data stays visible without active facets.');
assert.equal(matchesBenchmark('future-benchmark',other),false);
console.log('Benchmark facets: ten mappings, overlapping tags, OR/AND semantics, empty intersections and manual selection passed.');
