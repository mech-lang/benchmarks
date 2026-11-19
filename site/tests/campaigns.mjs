import assert from 'node:assert/strict';
import {metrics,formatMetric,recordFor,compareRecords,stageFor,filteredCases,compatibleHistory,measuredRows,controlFor,controlComparison,comparisonDirection,comparisonLabel,comparisonPlot,ratioColor,comparisonStyle,formatRatio} from '../src/campaigns-model.mjs';

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
assert.equal(formatMetric(2e-7,'resident_turn_seconds'),'200 ns');
assert.equal(formatMetric(.002,'resident_turn_seconds'),'2 ms');
assert.equal(formatMetric(1024,'artifact_bytes'),'1 KiB');
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
const reference={...candidate,backend:'rust',lane:'control',title:'Rust reference',control_contract:'matched',summary:{native_process_seconds:{median:2}}};
const measured={...candidate,backend:'native',control_contract:'matched',measurement:{primary_metric:'native_process_seconds'},summary:{native_process_seconds:{median:1}}};
const data={catalog:{cases:[{...cases[0],backends:['native','source','bytecode']},{id:'app',title:'Full application',family:'applications',backends:['program-jit']},cases[1]]},campaigns:[
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
assert.equal(controlComparison(rows[0],controlFor(data,rows[0])).label,'0.5× time');
assert.equal(formatMetric(3e-8,'rust_call_seconds'),'30 ns');
assert.equal(controlFor(data,rows[1]).kind,'pending');
data.control_policy={controls:[{case_id:'scalar',backend:'source',metric:'resident_turn_seconds',campaign_id:'resident',label:'Mech frozen baseline'}]};
assert.equal(controlFor(data,rows[0]).record,reference,'a retained Mech checkpoint cannot displace a measured Rust reference');
assert.equal(controlFor(data,rows[0]).label,'Rust');
const newer={...campaign,id:'new',started_at:'2026-11-19',results:[{...measured,summary:{native_process_seconds:{median:.5}}}]};
data.campaigns.push(newer);rows=measuredRows(data);
assert.equal(controlFor(data,rows[0]).kind,'pending','a missing Rust run does not automatically substitute an internal Mech checkpoint');
assert.equal(compareRecords(measured,rows[0].record,rows[0].metric).percent,-50,'explicit history comparisons remain available');
newer.results[0]={...newer.results[0],source_sha256:'new-source'};
assert.equal(controlFor(data,measuredRows(data)[0]).kind,'pending','changed source cannot silently inherit a qualified Mech control');
console.log('Consolidated measured rows, side-by-side Rust controls and fixed Mech promotion checks passed.');

// Matching inputs and hardware do not establish an equivalent timed scope.
const deflate={...candidate,case_id:'deflate',backend:'program-linked',control_contract:'checked-call',
  measurement:{primary_metric:'native_program_call_seconds'},summary:{native_program_call_seconds:{median:1}}};
const compressor={...baseline,case_id:'deflate',backend:'libdeflate',lane:'control',
  revision:'92e6a0db9fa848d742f9eb286c92afc60f2c3dda',
  source_sha256:'a82938cd20ecb3404f0b0e3fc7d1553706442b8b956443d8ca98ebebacecec05',
  measurement:{primary_metric:'control_call_seconds'},summary:{control_call_seconds:{median:2}}};
const deflateRun={...campaign,results:[deflate,compressor]};
const deflateData={campaigns:[deflateRun]};
const deflateRow={campaign:deflateRun,record:deflate,metric:'native_program_call_seconds'};
assert.equal(controlFor(deflateData,deflateRow).kind,'pending','a compressor call cannot be attached to a checked call without a shared timing contract');
assert.equal(controlFor(deflateData,deflateRow).record,undefined,'an unmatched timing is not displayed in the comparison column');
compressor.control_contract='compressor-call';
assert.equal(controlFor(deflateData,deflateRow).kind,'pending','different timing contracts remain separate');
compressor.control_contract='checked-call';
assert.equal(controlFor(deflateData,deflateRow).kind,'libdeflate');
assert.equal(controlComparison(deflateRow,controlFor(deflateData,deflateRow)).ratio,.5);
assert.equal(controlFor(deflateData,{...deflateRow,record:{...deflate,backend:'program-jit-bytecode'}}).kind,'pending','a native library must not become a JIT peer');
compressor.environment_hash='different-machine';
assert.equal(controlFor(deflateData,deflateRow).kind,'pending','a shared timing contract does not permit a different machine');
console.log('DEFLATE comparisons require the same task, machine and explicit measurement contract.');
for(const backend of ['source','bytecode','process-workers'])for(const metric of ['resident_turn_seconds','execution_allocations','teardown_seconds','worker_group_process_seconds','accepted_turns_per_second']){
  const record={...candidate,backend,control_contract:'same-task-and-timer',summary:{[metric]:{median:2}}};
  const bare={...record,backend:'rust',lane:'control',summary:{[metric]:{median:1}}};
  const origin={...campaign,results:[record,bare]};
  const row={campaign:origin,record,metric};
  const control=controlFor({campaigns:[origin]},row);
  assert.equal(control.kind,'pending','a shared task hash cannot qualify '+backend+' '+metric+' runtime semantics');
  assert.ok(control.reason.includes('rollback'));
  assert.equal(controlComparison(row,control).ratio,undefined,'an unqualified runtime comparison cannot produce a ratio');
}
for(const backend of ['source-native','fused-native','jit','program-jit','program-jit-bytecode']){
  const record={...candidate,backend,control_contract:reference.control_contract};
  const origin={...campaign,results:[record,reference]};
  const comparison=controlFor({campaigns:[origin]},{campaign:origin,record,metric:'resident_turn_seconds'});
  assert.equal(comparison.kind,'pending',backend+' must not fall back to AOT Rust');
  assert.ok(comparison.reason.includes('JIT peer'));
}

assert.equal(comparisonDirection({ratio:.5},'native_program_call_seconds'),'faster');
assert.equal(comparisonDirection({ratio:2},'native_program_call_seconds'),'slower');
assert.equal(comparisonDirection({ratio:2},'accepted_turns_per_second'),'faster','higher throughput has the opposite direction from time');
assert.equal(comparisonDirection({ratio:.5},'accepted_turns_per_second'),'slower');
assert.equal(comparisonDirection({ratio:1},'native_program_call_seconds'),'equal');
assert.equal(comparisonDirection({ratio:1.000001},'native_program_call_seconds'),'slower','rounding cannot turn a measured difference into a tie');
assert.equal(comparisonLabel({ratio:.5},'native_program_call_seconds'),'0.5× time');
assert.equal(comparisonLabel({ratio:2},'artifact_bytes'),'2× size');
assert.equal(comparisonLabel({ratio:1.000001},'native_program_call_seconds'),'1.000001× time');
assert.equal(ratioColor(.5),'var(--faster)');
assert.equal(ratioColor(1),'var(--equal)');
assert.equal(ratioColor(10),'#e7ac4c','tenfold losses stay in the yellow/amber band');
assert.equal(ratioColor(10.00001),'#f29b89','losses above tenfold enter the red band');
assert.equal(ratioColor(1000),'#ff6b7a');
assert.equal(ratioColor(Infinity),'#ff6b7a');
assert.notEqual(ratioColor(2),ratioColor(5),'smaller losses have distinct yellow shades');
assert.notEqual(ratioColor(11),ratioColor(1000),'larger losses have distinct red shades');
for(const invalid of [NaN,undefined,-1])assert.equal(ratioColor(invalid),'var(--unknown)');
assert.equal(comparisonStyle({ratio:.05},'accepted_turns_per_second'),'--comparison-color:'+ratioColor(20),'throughput losses use reciprocal slowdown severity');
assert.equal(comparisonStyle({ratio:0},'accepted_turns_per_second'),'--comparison-color:#ff6b7a');
assert.ok(Number(formatRatio(10.00001))>10,'rounding cannot hide the red-band threshold');
const plot=comparisonPlot([{id:'low',title:'Low',ratio:.1},{id:'same',title:'Same',ratio:1},{id:'high',title:'High',ratio:10}],{width:700});
assert.ok(plot.includes('style="--comparison-color:#e7ac4c"'),'chart points use the same scale as table ratios');
const coordinates=[...plot.matchAll(/cx="([0-9.]+)" cy="([0-9.]+)"/g)].map(m=>m.slice(1).map(Number));
assert.equal(coordinates.length,3);
assert.ok(Math.abs((coordinates[1][0]-coordinates[0][0])-(coordinates[2][0]-coordinates[1][0]))<1e-8,'case positions are evenly spaced');
assert.ok(Math.abs((coordinates[0][1]-coordinates[1][1])-(coordinates[1][1]-coordinates[2][1]))<1e-8,'equal log intervals occupy equal vertical distances');
assert.ok(coordinates[0][1]>coordinates[1][1]&&coordinates[1][1]>coordinates[2][1],'smaller time ratios appear below the baseline');
console.log('Comparison colors respect metric direction; strict ties and logarithmic chart spacing pass.');
