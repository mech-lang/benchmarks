"""Reconstruct plotting data from retained primary measurements; run no subjects."""
import csv
import hashlib
import json
import re
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from os.path import relpath

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
SOURCE = Path('/private/tmp/mech-native-hashmap-performance')
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

LABELS = {
 'library-hash-work':'Earlier library-update lowering',
 'available':'Initial canonical map execution',
 'candidate':'Retained map ownership',
 'cache':'Maintained call-cache totals',
 'key-span':'Borrowed String keys',
 'rust-span-diagnostic':'Borrowed String keys',
 'map-admission':'Grouped native admission',
 'caller-census':'Cached caller inventory',
 'map-path':'Native paths and fused admission',
 'closed-map':'Closed native map loops',
 'shape':'Reused range shapes',
 'call-scope':'Combined library-call setup',
 'lookup':'Reuse the current key lookup',
 'packed':'Generated compact-key table operations',
 'packed-ssa':'Native register loops',
 'parallel':'Seven parallel source tasks',
 'cold-origin':'Cold failure origins',
 'parallel-compact':'Source-derived character encoding',
 'parallel-simd':'SIMD hash-table control probes',
 'publication-batches':'Batched publication debits',
 'source-edge-facts':'Current-traversal scalar proofs',
 'narrow-slots':'Narrow table payloads',
 'tag-threading':'Thread source state through the CFG',
 'folded-hash':'Folded-product hashing',
 'frame-effects':'Narrow helper synchronization',
 'guarded-loop':'Prove window bounds',
 'frozen-map':'Retain maps for private reads',
 'lookup-facts':'Current-key lookup facts',
 'cfg-cleanup':'Bounded constant CFG cleanup',
 'loop-outlining':'Isolate closed-loop functions',
 'loop-invariants':'Guard helper calls and peel rolling keys',
 'cfg-prepass':'CFG cleanup before backend data pass',
 'source-match-insert':'Alternate source match/insert form',
 'source-loop-end':'Alternate source loop-end form',
 'source-control':'Alternate source control form',
 'preserving-calls':'Register-preserving helper bridge',
 'preserving-calls-qualified':'Qualified helper bridge',
 'scratch-calls':'Caller-owned cold-call scratch',
 'binding-calls':'Bind invariant helper words',
 'mutation-facts':'Certified insertion progress',
 'escrow-transaction':'One transaction per fuel refill',
 'count-values':'Prove source count bounds',
 'vector-control':'Direct SIMD control loads',
 'header-cache':'Clear cache at every header',
 'loop-constants':'Caller-owned loop constants',
 'escrow-spin':'Bounded mutex retry',
 'launch-order':'Reverse task launch',
 'lookup-thread':'Current-key states across joins',
 'steady':'Helper-free funded continuations',
 'steady-fold':'Simplify funded-loop CFG',
 'snapshot':'Immutable words in cold snapshots',
 'width-specialization':'Bounded width specialization',
 'fuel-edges':'Funded productive-entry checks',
 'productive-entry':'Enter at productive source headers',
 'funded-extent':'Hoist funded source extent',
 'caller-extent':'Pass source extent from caller',
 'cold-snapshots':'Separate header snapshots',
 'direct-entry':'Peel first probe entry',
 'proved-graphemes':'Elide proved decoder checks',
 'affine-cursor':'Source-certified adjacent byte cursor',
 'cold-recipes':'Reconstruct cold source words',
 'cold-frame':'Reload cold frame words',
 'direct-lookup-cache':'Bounded complete-domain lookup cache',
 'lookup-split':'Split cached and ordinary loops',
 'refill-fastpath':'Precompute refill charges',
 'escrow-backoff8':'Eight-round mutex retry',
 'escrow-backoff10':'Ten-round mutex retry',
 'escrow-backoff12':'Twelve-round mutex retry',
 'line-offset-crlf':'Fuse CRLF/offset preparation',
 'disjoint-state':'Separate private metadata alias regions',
 'preparation-interactions':'Combine retained preparation factors',
 'preparation-combined':'Combine retained preparation factors',
 'host-metadata-trim':'Compact host metadata',
 'prepared-refill':'Retest prepared refill charges',
 'host-input-chunk':'Change host input chunk size',
 'sized-schedule':'Schedule larger source tasks first',
 'packed-domain-validation':'Validate packed decoder once',
 'shared-string-facts':'Share immutable String facts',
 'aligned-probe-groups':'Align probes and simplify addressing',
 'utf8-fragment-facts':'Share UTF-8 fragment facts',
 'resource-admission-fixes':'Correct ownership and admission',
 'borrowed-offset-cursor':'Read borrowed line offsets directly',
 'line-join-copy':'Copy validated line spans directly',
 'join-map-fusion':'Compose selected join and String map',
 'worker-local-credit':'Local finite worker credit',
 'scalar-tail-registers':'Keep Tail funding in SSA',
 'scalar-cold-origins':'Cold scalar error origins',
 'credit-fragment-facts':'Combine credit and fragment facts',
 'scalar-traversal-count':'Exact scalar traversal count',
 'private-join-buffer':'Private join/map destination',
 'joined-transform-copy':'Transform directly into destination',
 'joined-byte-table':'Prepare byte mapping table once',
 'borrowed-field-loads':'Load only required view fields',
 'private-home-notrap':'Nontrapping private-home proof',
 'compact-ascii-map':'Verified compact immutable mapper',
 'pure-scalar-state':'Pure-scalar graph and SSA state',
}

ALIASES = {
 'cache-scale':'cache', 'vector-control-best':'vector-control',
 'loop-constants-prefix':'loop-constants', 'productive-entry-reference-prefix':'productive-entry',
 'steady-fold-reference-prefix':'steady-fold', 'lookup-split':'lookup-split',
 'shared-string-facts':'shared-string-facts',
 'rust-span-diagnostic':'key-span',
 'preparation-combined':'preparation-interactions',
 'escrow-backoff10-prefix-repeat':'escrow-backoff10',
 'escrow-spin-reference':'escrow-spin',
}

TRIALS = {
 'narrow-slots','frame-effects','loop-invariants','cfg-prepass','source-match-insert',
 'source-loop-end','header-cache','launch-order','lookup-thread','snapshot',
 'source-control',
 'funded-extent','proved-graphemes','cold-recipes','cold-frame','refill-fastpath',
 'line-offset-crlf','disjoint-state','prepared-refill','host-input-chunk','sized-schedule',
 'packed-domain-validation','shared-string-facts','utf8-fragment-facts',
 'scalar-tail-registers','scalar-cold-origins','scalar-traversal-count',
 'join-map-fusion','borrowed-field-loads','private-home-notrap',
}

def key_of(name):
    key = re.sub(r'^full-', '', name)
    key = re.sub(r'-(?:expanded-cohort|cohort|replication)-v\d+$', '', key)
    key = re.sub(r'-v\d+$', '', key)
    key = key.removesuffix('-timing')
    return ALIASES.get(key, key)

log = subprocess.check_output(['git','log','--all','--format=%H\t%ct\t%s'], cwd=SOURCE, text=True)
commits = {r.split('\t',2)[0]:r.split('\t',2)[1:] for r in log.splitlines()}
records, excluded = [], []

process_cache = {}
def process_paths(path):
    """Follow retained aggregate receipts without widening to other studies."""
    if path in process_cache:return process_cache[path]
    d = read(path)
    paths = list(path.parent.glob('*/process.json'))
    for evidence in d.get('evidence', []):
        if isinstance(evidence, dict) and evidence.get('path', '').endswith('/results.json'):
            child = HERE/evidence['path']
            assert child.is_file(),child
            paths.extend(process_paths(child))
    process_cache[path] = list(dict.fromkeys(paths))
    return process_cache[path]

def recover_clock(path, samples):
    candidates = [(p, read(p)) for p in process_paths(path)]
    recovered = []
    for seconds in samples:
        matches = [(p,d) for p,d in candidates if d.get('quantitative_benchmark')
                   and abs(d.get('elapsed_seconds', -1)-seconds)<1e-10]
        assert len(matches)==1,(path, seconds, [str(p) for p,d in matches])
        p,d = matches[0]
        assert d['reaped'] and d['group_closed'] and d['exit_status']==0,p
        birth = d['birth_identity']
        timestamp = birth['birth_seconds']+birth['birth_microseconds']/1e6
        recovered.append(dict(seconds=seconds,timestamp=timestamp,
            time_utc=datetime.fromtimestamp(timestamp,timezone.utc).isoformat(),
            process=relpath(p,HERE),process_sha256=sha(p)))
    return recovered

def add(path, d, medians, bases, candidate=None, variant=None, rows=None, key_override=None):
    candidate = candidate or next((k for k in ['candidate','mech','combined'] if k in medians), None)
    if candidate is None:return
    if bases == 125000000:
        assert d.get('input_sha256')=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa',path
    key = key_override or key_of(path.parent.name)
    if path.parent.parent.name == 'host-input-chunk-v1':key='host-input-chunk'
    assert key in LABELS,(path,key)
    commit = d.get('source_commit') or d.get('source',{}).get('commit') or d.get('mech_source_commit')
    assert commit in commits,(path,commit)
    samples = rows if rows is not None else d.get('samples_seconds',{}).get(candidate)
    if samples is None:
        samples = [r['seconds'] for r in d.get('samples',[]) if (r.get('label',r.get('subject'))==candidate)]
    assert samples and abs(statistics.median(samples)-medians[candidate])<1e-10,(path,candidate,samples,medians[candidate])
    rust = medians.get('rust')
    observations = recover_clock(path, samples)
    timestamp = statistics.median(r['timestamp'] for r in observations)
    evidence = d.get('evidence',[])
    parent = next((medians[k] for k in ['parent','baseline'] if k in medians), None)
    records.append(dict(key=key,label=LABELS[key],commit=commit,
        timestamp=timestamp,time_utc=datetime.fromtimestamp(timestamp,timezone.utc).isoformat(),
        time_basis='Median of exact candidate process birth timestamps',
        time_start=min(r['timestamp'] for r in observations),
        time_end=max(r['timestamp']+r['seconds'] for r in observations),
        commit_timestamp=int(commits[commit][0]),observations=observations,
        earlier_lowering=key=='library-hash-work',
        receipt=relpath(path,HERE),receipt_sha256=sha(path),bases=bases,
        seconds=medians[candidate],rust_seconds=rust,x_rust=medians[candidate]/rust if rust else None,
        parent_seconds=parent,n=len(samples),samples=samples,variant=variant or candidate,
        single_run=len(samples)==1,trial=key in TRIALS,
        evidence_paths=[e['path'] for e in evidence if isinstance(e,dict) and 'path' in e],
        comparisons=d.get('paired_comparisons',{}),input_sha256=d.get('input_sha256'),
        url='https://github.com/mech-lang/benchmarks/blob/codex/implementation-performance-audit/'+str(path.relative_to(HERE.parents[2]))))

for path in sorted(HERE.glob('*/results.json')):
    d=read(path);name=path.parent.name;m=d.get('median_seconds')
    if isinstance(m,dict) and ('candidate' in m or 'mech' in m or 'combined' in m):
        bases=d.get('input_bases',d.get('selected_bases'))
        if name.startswith('full-') and 'rust' in m:
            bases=125000000
        if bases not in [1000,100000,1000000,125000000]:continue
        if key_of(name) not in LABELS:
            excluded.append(dict(receipt=str(path.relative_to(HERE)),reason='Not a compiler optimization primary cohort',key=key_of(name)));continue
        add(path,d,m,bases)
    elif name=='available-timing-v1':
        add(path,d,{'mech':m},1000,rows=[r['seconds'] for r in d['samples']])

# Earlier required-work implementation: same input and machine, but a different
# source/lowering. Plot as an explicitly separate point, never as the source-map
# baseline or joined into its optimization trace.
path=HERE.parent/'native-hashmap-work-v1/rust-comparison-v2/results.json'
d=read(path)
add(path,d,{k:v['median_seconds'] for k,v in d['statistics'].items()},125000000,
    key_override='library-hash-work')

# The first successful full stages predate repeated aggregate cohorts.
for name in ['full-call-scope-v2','full-packed-v1','full-packed-ssa-v1','full-parallel-v2']:
    path=HERE/name/'results.json';d=read(path)
    assert d['status']=='full-output-and-update-counts-verified'
    m={r['label']:r['seconds'] for r in d['samples']}
    add(path,d,m,125000000)

path=HERE/'cache-timing-v2/results.json';d=read(path)
add(path,d,d['diagnostic']['median_seconds'],1000,
    rows=[r['seconds'] for r in d['samples'] if r['cohort']=='diagnostic' and r['label']=='candidate'])

# Preserve the chunk-size experiment's independent sessions and variants.
for rel in read(HERE/'host-input-chunk-v1/results.json')['sessions']:
    path=HERE/rel;d=read(path);m=d['median_seconds']
    bases=1000000 if 'prefix-' in rel else 125000000
    for candidate in m:
        if candidate not in ['rust','baseline','parent']:
            add(path,d,m,bases,candidate=candidate,variant=candidate)

# Later aggregate expansions contain the exact earlier observations. Retain
# the largest cohort, rather than plotting the subset twice as replication.
keep=[]
for row in records:
    own=set(row['evidence_paths'])
    superset=next((r for r in records if r is not row and r['key']==row['key']
        and r['bases']==row['bases'] and r['variant']==row['variant']
        and own and own < set(r['evidence_paths'])),None)
    if superset:
        excluded.append(dict(receipt=row['receipt'],reason='Exact observation subset of expanded cohort',covered_by=superset['receipt']))
    else:keep.append(row)
records=keep

stages=[]
for key in sorted({r['key'] for r in records},key=lambda k:(min(r['timestamp'] for r in records if r['key']==k),list(LABELS).index(k))):
    stage=dict(index=len(stages)+1,key=key,label=LABELS[key],trial=key in TRIALS,
        timestamp=min(r['timestamp'] for r in records if r['key']==key))
    stages.append(stage)
    for row in records:
        if row['key']==key:row['stage']=stage['index']
records.sort(key=lambda r:(r['stage'],r['bases'],r['receipt'],r['variant']))
notes=[
 dict(key='initial-timeout',receipt='full-timing-v1/results.json',seconds_lower_bound=180,
      reason='Full-input process exceeded the deadline; no completed time or paired Rust denominator. Excluded from numeric curves.'),
 dict(key='historical-m1',seconds=0.4828,
      reason='PR909 historical M1 executable used a different lowering. Not on the current-machine compiler timeline.'),
 dict(key='nontrapping-full-gate',receipt='private-home-notrap-v1/code-review.json',
      reason='Generated functions identical; full-input campaign was not run. Prefix qualification is shown separately.'),
]
clock=dict(first_measurement=min(r['time_start'] for r in records),
    last_measurement=max(r['time_end'] for r in records),
    sample_time_basis='Exact macOS process birth seconds and microseconds from retained process.json receipts; no filesystem mtimes or commit-time estimates',
    cohort_time_basis='Median process launch time, with first launch / last completion retained',
    display_timezone='America/New_York')
result=dict(schema='mech.optimization-history.v2',stages=stages,records=records,excluded=excluded,notes=notes,clock=clock,
 scope='Current-machine source-map optimization history. Each point is its own complete-process cohort median or explicitly marked single run. Each ratio uses its own Rust cohort median. Input sizes are separate; no full-input timings are extrapolated. Uncertain and negative trials remain. No new benchmark is run.',
 builder_sha256=sha(Path(__file__)))
(STUDY/'history.json').write_text(json.dumps(result,indent=2)+'\n')
with (STUDY/'history.csv').open('w',newline='') as f:
    fields=['stage','label','timestamp','time_utc','time_basis','time_start','time_end','commit_timestamp','bases','variant','n','seconds','rust_seconds','x_rust','parent_seconds','trial','earlier_lowering','commit','receipt','receipt_sha256','url']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(records)
print('stages',len(stages),'cohorts',len(records),'excluded',len(excluded))
print('by input',{b:sum(r['bases']==b for r in records) for b in [1000,100000,1000000,125000000]})
print('first full',next(r for r in records if r['bases']==125000000)['seconds'])
print('last stage',stages[-1])
