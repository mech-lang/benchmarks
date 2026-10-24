"""Partition observed main-thread locations and bound worker appearance."""
from collections import Counter
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(HERE))
from profile_hotspots import leaves,matches

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
counts=Counter();examples={};sources=[]
for index in range(1,4):
    path=HERE/f'full-profile-disjoint-state-v{index}/analysis.json'
    report=json.loads(path.read_text()); assert report['machine_code_identical'] and report['completed_output_verified']
    sources.append(dict(path=str(path.relative_to(HERE)),sha256=sha(path)))
    for item in report['samples']:
        path=HERE/item['stacks']; assert sha(path)==item['stacks_sha256']
        for thread,symbol,count,context in leaves(path.read_text()):
            if thread!=item['main_thread']['thread']:continue
            if matches(context,('_pthread_join',)):
                label='worker_join'
            elif symbol=='_dyld_start':
                label='unresolved_root_only'
            elif symbol.startswith('mech_string_map_region_'):
                label='generated_byte_map'
            elif matches(context,('finish_compiled_string_map',)) and matches(context,('from_utf8',)):
                label='mapped_output_utf8_validation'
            elif matches(context,('selected_join',)):
                label='selected_line_join'
            elif matches(context,('capture_chunk',)):
                label='input_capture_and_source_selection'
            elif matches(context,('text_graphemes',)):
                label='string_geometry'
            elif symbol=='read':
                label='input_read'
            else:
                label='other_main_locations'
            counts[label]+=count;examples.setdefault(label,context[-8:])
lifetimes=HERE/'disjoint-state-thread-lifetimes-v1/results.json'
j=json.loads(lifetimes.read_text());sources.append(dict(path=str(lifetimes.relative_to(HERE)),sha256=sha(lifetimes)))
rows=[]
for s in j['subjects']:
    mains=[t for t in s['threads'] if 'main' in t['names']];assert len(mains)==1
    main=mains[0]
    # Exclude the observed short-lived loader and pool helper threads; preserve
    # the full raw inventory and avoid claiming a mapping to source widths.
    workers=[t for t in s['threads'] if t['handle']!=main['handle'] and t['user_ns']+t['system_ns']>=10_000_000]
    assert len(workers)==7
    first=min(t['first_seen'] for t in workers)
    folder=HERE/'disjoint-state-thread-lifetimes-v1'/f"{len(rows)}-{s['subject']}"
    raw=json.loads((folder/'thread-observations.json').read_text())
    earlier=[t['seconds'] for t in raw['snapshots'] if t['seconds']<first]
    rows.append(dict(subject=s['subject'],first_worker_appearance_seconds=[max(earlier,default=0),first],main_cpu_seconds_lower_bound=(main['user_ns']+main['system_ns'])/1e9,worker_cpu_seconds_lower_bounds=[(t['user_ns']+t['system_ns'])/1e9 for t in workers],process_path=str((folder/'process.json').relative_to(HERE)),primary_timing=False))
result=dict(status='main-profile-and-worker-appearance-retained',sources=sources,script_sha256=sha(Path(__file__)),parser_sha256=sha(HERE/'profile_hotspots.py'),main_observations=sum(counts.values()),main_exclusive_observations=dict(counts),main_example_contexts=examples,thread_observations=rows,scope='Main-thread stack locations include waits and unresolved root-only stacks. They do not establish elapsed-time or CPU-time shares. Worker appearance is bounded by successive polls, not an exact phase timestamp; observed CPU endpoints are lower bounds. The seven substantial non-main threads are identified by at least 10 ms observed CPU, not mapped to source widths. Polling changes execution; these six processes are excluded from primary timing cohorts.')
(HERE/'disjoint-state-checkpoint-v1/preparation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(main_observations=result['main_observations'],main_exclusive_observations=dict(counts),thread_observations=rows),indent=2))
