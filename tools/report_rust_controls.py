#!/usr/bin/env python3
"""Reproduce the frozen 17 November 2026 Rust-control study from retained campaigns."""

from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
ids=['2026-11-17-rust-resident-001','2026-11-17-rust-capacity-002','2026-11-17-rust-concurrent-001','2026-11-17-rust-native-001','2026-11-17-rust-applications-001','2026-11-17-rust-strings-002']
campaigns=[json.loads((root/'results/campaigns'/id/'campaign.json').read_text()) for id in ids]
assert all(c.get('complete') and c.get('outcome')=='ok' for c in campaigns)
records=[]
for c in campaigns:
 for r in c['results']:
  if r['lane']!='candidate':continue
  control=next(x for x in c['results'] if x['case_id']==r['case_id'] and x['lane']=='control' and x['backend']=='rust')
  assert r['control_contract']==control['control_contract']
  metric=r['measurement'].get('primary_metric','resident_turn_seconds')
  mapped=control['measurement'].get('metric_mapping',{}).get(metric,metric)
  n=len(r['measurement'].get('schedule',[]))*r['measurement'].get('cycles',1)
  records.append({'case_id':r['case_id'],'backend':r['backend'],'campaign':c['id'],'metric':metric,
    'mech':r['summary'][metric], 'rust':control['summary'][mapped], 'mech_over_rust':r['summary'][metric]['median']/control['summary'][mapped]['median'],
    'turns_per_fork':n if metric in ['resident_turn_seconds','jit_invocation_seconds'] else None,
    'mech_metrics':r['summary'],'rust_metrics':control['summary'],
    'mech_source_sha256':r['source_sha256'],'rust_source_sha256':control['source_sha256'],'control_contract':r['control_contract']})
records=list({(r['case_id'],r['backend']):r for r in records}.values())
study={'schema':'mech.rust-control-study.v1','date':'2026-11-17','campaigns':ids,
 'new_tasks_with_rust':len({r['case_id'] for r in records}),'new_mech_samples':sum(len(r['samples']) for c in campaigns for r in c['results'] if r['lane']=='candidate'),
 'new_rust_samples':sum(len(r['samples']) for c in campaigns for r in c['results'] if r['lane']=='control'),'records':records}
assert study['new_tasks_with_rust']==61
out=root/'site/reports'
(out/'rust-controls-2026-11-17.json').write_text(json.dumps(study,indent=2)+'\n')
def get(id,backend='source'):return next(r for r in records if r['case_id']==id and r['backend']==backend)
def us(r,which='mech'):return r[which]['median']*1e6
f=get('filter-cardinality'); retained=get('retained-snapshots'); scalar=get('scalar-changed');unchanged=get('scalar-unchanged');ekf=get('ekf')
kn=get('knucleotide','source-native'); native=get('native-build','native');df=get('deflate','program-jit')
alloc=lambda r,who:r[who+'_metrics']['execution_allocations']['median']/r['turns_per_fork']
lines=['# What the Rust controls show — 17 November 2026','',
 f"Implemented and measured Rust controls for the 61 remaining tasks: {study['new_rust_samples']} new Rust observations and {study['new_mech_samples']} paired Mech observations, five fresh forks per implementation and path. Together with the retained N-body and related-post controls, all 63 active tasks now have a measured control in the default metrics view.",'',
 'The resident results below use the preferred source path. Decoded artifacts were measured separately in the same randomized blocks. Both languages run the same input schedules; verification checks complete trajectories, owned snapshots and recovery against independent Python oracles. Rust is an independent AOT task implementation. Mech also performs runtime scheduling, admission and resource accounting. These are task comparisons, not matched kernel attribution.','',
 '| Task | Mech median µs | Rust median µs | Mech / Rust |','| --- | ---: | ---: | ---: |']
for id in ['scalar-changed','scalar-unchanged','numerical-pipeline','ekf','filter-cardinality','retained-snapshots','table-joins','graphs','strings','jit']:
 r=get(id,'jit' if id=='jit' else 'source');lines.append(f"| {id} | {us(r):.6f} | {us(r,'rust'):.6f} | {r['mech_over_rust']:.2f}× |")
lines += ['',
 f"Changed scalar work costs {us(scalar)*1000:.1f} ns in Mech; unchanged work costs {us(unchanged)*1000:.1f} ns. Skipping the scalar computation saves {(1-us(unchanged)/us(scalar))*100:.1f}% here. Both Mech cases allocate zero times inside the timed block. The remaining turn cost matters for tiny tasks.",'',
 f"The eight-element filter costs {us(f):.2f} µs and {alloc(f,'mech'):,.0f} allocations per Mech turn, versus {us(f,'rust'):.4f} µs and {alloc(f,'rust'):.0f} allocations in Rust. Keeping all 5,000 snapshots costs {us(retained):.2f} µs per Mech turn with the same allocation count. Its retained managed storage grows from {f['mech_metrics']['managed_retained_bytes']['median']:,.0f} to {retained['mech_metrics']['managed_retained_bytes']['median']:,.0f} bytes. The similar filter timings suggest that snapshot retention is not the main source of the execution gap; investigate the filter path and its allocation volume first.",'',
 f"The full 4,096-step EKF trajectory costs {us(ekf):.3f} µs per Mech step, with zero allocations in the timed block. It is {ekf['mech_over_rust']:.2f}× the Rust time. This separates allocation-heavy collection paths from the numerical path rather than suggesting one universal Mech overhead.",'',
 '## Cardinality sweep','', 'The initial sweep is preserved in full. A progress monitor was found reading the growing result index during later capacity measurements. The capacity figures below use a fresh independent five-fork sweep with that monitor disabled and 256 complete schedule cycles (1,280 accepted turns per fork). No original samples were removed. The campaign index now keeps previews and links to complete raw trajectories, avoiding repeated serialization of all outputs between forks.','',
 'Every row scans 65 input elements. The schedule crosses each indicated output-cardinality boundary, including A → B → A and unchanged output. These are output-capacity tests, not larger input-size tests.','',
 '| Output threshold | Mech median µs | Rust median µs | Mech allocations/turn |','| ---: | ---: | ---: | ---: |']
for threshold in [0,7,8,9,15,16,17,31,32,33,63,64,65]:
 r=get('capacity-growth'+('' if threshold==0 else '-'+str(threshold)))
 lines.append(f"| {threshold} | {us(r):.3f} | {us(r,'rust'):.6f} | {alloc(r,'mech'):,.0f} |")
lines += ['', 'Even the almost-empty result scans all 65 inputs. This exposes the scan/evaluation cost before most output storage is needed. Exact shapes, complete values and every retained sample are in the linked campaign.','',
 '## Complete applications and builds','', f"Full compressor native-code preparation takes {df['mech_metrics']['jit_compile_seconds']['median']:.3f} seconds, plus {df['mech_metrics']['source_to_artifact_seconds']['median']:.3f} seconds to compile the source artifact. One full 6.6 MB warm compression call takes {df['mech']['median']:.3f} seconds. Native-code preparation alone is {df['mech_metrics']['jit_compile_seconds']['median']/df['mech']['median']:.1f}× the warm call duration. At this tested size, it remains a major cost for one-shot use. Preparation is shared across the 12 inputs in each complete worker fork; it is not charged twelve times.",'',
 f"Full K-nucleotide (254,166,745 input bytes): Mech {kn['mech']['median']:.6f} s; unchanged upstream Rust #7 {kn['rust']['median']:.6f} s, {kn['mech_over_rust']:.3f}×. Both clocks include fresh process startup, input reading, all computation, full output and exit. Mech uses four partitions; Rust retains its upstream thread-pool policy.",'',
 f"Native scalar source → executable: Mech {native['mech']['median']:.6f} s; Rust {native['rust']['median']:.6f} s. Each measured build starts from a fresh project/source after a separate support-cache qualification. The resulting executable is run and checked on all six scheduled inputs. The paths have different support machinery: Mech includes compiler-worker startup, dependency resolution and checked runtime support; rustc uses its prebuilt standard library.",'',
 f"Full Reymont compression (6,627,202 bytes): Mech level 12 {df['mech']['median']:.6f} s, {df['mech_metrics']['output_bytes']['median']:,.0f} output bytes; Rust zlib-rs maximum level 9 {df['rust']['median']:.6f} s, {df['rust_metrics']['output_bytes']['median']:,.0f} bytes. Output allocation and scratch destruction are included in the call, input import/warmup/returned-output destruction excluded. Both complete streams independently inflate to the exact input, preserve prefix/aliases and contain no trailing data. Different codec output sizes must be considered with time; this is not equal-quality compression.",'',
 '## Fixed total work across processes','',
 '196,608 accepted numerical turns in total, with complete supervised group startup through exit. One application execution thread per process.','',
 '| Processes | Mech group seconds | Rust group seconds | Mech turns/s | Rust turns/s |','| ---: | ---: | ---: | ---: | ---: |']
for workers,id in [(1,'concurrent'),(2,'concurrent-2'),(4,'concurrent-4')]:
 r=get(id,'process-workers');lines.append(f"| {workers} | {r['mech']['median']:.6f} | {r['rust']['median']:.6f} | {r['mech_metrics']['accepted_turns_per_second']['median']:,.0f} | {r['rust_metrics']['accepted_turns_per_second']['median']:,.0f} |")
lines += ['', 'The full-process application gaps and tiny resident gaps describe different tasks and boundaries. They do not establish a same-task input-size crossover. Every median, range, standard deviation, source hash, compiler command and raw fork remains inspectable. No adverse observations were removed and these exploratory results do not automatically move a pinned Mech control.','',
 '## Evidence','', '[Machine-readable study](rust-controls-2026-11-17.json). These reports include the complete per-task tables and raw-evidence archives:','']
for id in ids:lines.append(f'- [{id}](campaign-evidence/{id}/report.md)')
(out/'rust-controls-2026-11-17.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in study.items() if k!='records'},indent=2))
