import assert from 'node:assert/strict';
import {metrics,formatMetric,recordFor,compareRecords,stageFor,filteredCases,compatibleHistory,measuredRows,controlFor,controlComparison} from '../src/campaigns-model.mjs';

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

const application={...candidate,case_id:'app',backend:'program-jit',measurement:{primary_metric:'native_program_call_seconds'},summary:{native_program_call_seconds:{median:3}}};
const failed={...candidate,outcome:'error',progress:'implemented',summary:{}};
const reference={...candidate,backend:'rust',lane:'control',title:'Rust reference',control_contract:'matched',summary:{resident_turn_seconds:{median:2}}};
const measured={...candidate,control_contract:'matched'};
const data={catalog:{cases:[{...cases[0],backends:['source','bytecode']},{id:'app',title:'Full application',family:'applications',backends:['program-jit']},cases[1]]},campaigns:[
  {...campaign,id:'resident',results:[measured,reference]},
  {...campaign,id:'application',started_at:'2026-11-17',results:[application]},
  {...campaign,id:'failed',started_at:'2026-11-18',results:[failed,{...reference,case_id:'jvm',backend:'jvm',lane:'candidate'}]},
]};
let rows=measuredRows(data);
assert.equal(rows.length,2,'unmeasured catalog entries and external controls are not task rows');
assert.equal(rows[0].campaign.id,'resident','new failed run does not erase accepted result');
assert.equal(rows[1].metric,'native_program_call_seconds','each row retains its own measurement boundary');
assert.equal(measuredRows(data,{campaign:'application'}).length,1,'a campaign does not create empty rows for other tasks');
assert.equal(measuredRows(data,{backend:'bytecode'}).length,0);
assert.equal(measuredRows(data,{progress:'failed'})[0].record.outcome,'error');
assert.equal(measuredRows(data,{metric:'native_program_call_seconds'}).length,1);
assert.equal(controlFor(data,rows[0]).kind,'rust');
assert.equal(controlComparison(rows[0],controlFor(data,rows[0])).percent,-50);
assert.equal(controlFor(data,rows[1]).kind,'pending');
data.control_policy={controls:[{case_id:'scalar',backend:'source',metric:'resident_turn_seconds',campaign_id:'resident',label:'Mech frozen baseline'}]};
assert.equal(controlFor(data,rows[0]).record,measured);
assert.equal(controlComparison(rows[0],controlFor(data,rows[0])).label,'Baseline held');
const newer={...campaign,id:'new',started_at:'2026-11-19',results:[{...measured,summary:{resident_turn_seconds:{median:.5}}}]};
data.campaigns.push(newer);rows=measuredRows(data);
assert.equal(controlFor(data,rows[0]).record,measured,'a faster current run cannot replace the pinned control');
assert.equal(controlComparison(rows[0],controlFor(data,rows[0])).percent,-50);
newer.results[0]={...newer.results[0],source_sha256:'new-source'};
assert.equal(controlFor(data,measuredRows(data)[0]).kind,'pending','changed source cannot silently inherit a qualified Mech control');
console.log('Consolidated measured rows, side-by-side Rust controls and fixed Mech promotion checks passed.');
