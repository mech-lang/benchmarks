import assert from 'node:assert/strict';
import {metrics,formatMetric,recordFor,compareRecords,stageFor,filteredCases,compatibleHistory} from '../src/campaigns-model.mjs';

const baseline={case_id:'scalar',backend:'source',lane:'candidate',task_hash:'t',measurement_hash:'m',source_sha256:'s',
  environment_hash:'e',outcome:'ok',progress:'measured',revision:'abc',summary:{resident_turn_seconds:{median:2,samples:[1,2,3]}}};
const candidate={...baseline,summary:{resident_turn_seconds:{median:1,samples:[.8,1,1.2]}}};
const campaign={id:'latest',started_at:'2026-11-16T12:00:00Z',results:[candidate]};
assert.equal(compareRecords(baseline,candidate,'resident_turn_seconds').percent,-50);
for(const field of ['task_hash','measurement_hash','source_sha256','environment_hash','backend']) {
  assert.equal(compareRecords(baseline,{...candidate,[field]:'different'},'resident_turn_seconds').status,'incompatible');
}
assert.equal(compareRecords(null,candidate,'resident_turn_seconds').label,'—');
assert.equal(compareRecords(baseline,{...candidate,outcome:'incorrect'},'resident_turn_seconds').status,'unavailable');
assert.equal(formatMetric(undefined,'resident_turn_seconds'),'—');
assert.equal(formatMetric(2e-7,'resident_turn_seconds'),'200.0 ns');
assert.equal(formatMetric(.002,'resident_turn_seconds'),'2.00 ms');
assert.equal(formatMetric(1024,'artifact_bytes'),'1.00 KiB');
assert.equal(recordFor(campaign,'scalar','source'),candidate);
assert.equal(recordFor(campaign,'scalar','bytecode'),undefined);
const cases=[{id:'scalar',title:'Scalar arithmetic',family:'arithmetic',progress:'implemented'},
  {id:'graph',title:'Graph traversal',family:'graphs',progress:'planned'}];
assert.equal(stageFor(cases[1]),'planned');
assert.equal(stageFor(cases[0],candidate),'measured');
assert.deepEqual(filteredCases(cases,campaign,{progress:'measured'}),[cases[0]]);
assert.deepEqual(filteredCases(cases,campaign,{progress:'planned'}),[cases[1]]);
assert.deepEqual(filteredCases(cases,campaign,{query:'GRAPH'}),[cases[1]]);
assert.deepEqual(filteredCases(cases,campaign,{family:'arithmetic'}),[cases[0]]);
assert.deepEqual(filteredCases(cases,campaign,{progress:'failed'}),[]);
assert.equal(compatibleHistory([campaign],candidate,'resident_turn_seconds').length,1);
assert.equal(compatibleHistory([campaign],{...candidate,measurement_hash:'other'},'resident_turn_seconds').length,0);
assert.ok(metrics.worker_process_peak_rss_bytes.note.includes('Whole-worker'));
assert.ok(metrics.source_to_artifact_seconds.note.includes('No native code'));
console.log('Campaign filtering, compatibility, units, missing data and history checks passed.');
