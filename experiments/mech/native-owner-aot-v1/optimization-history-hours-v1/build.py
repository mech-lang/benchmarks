#!/usr/bin/env python3
"""Reconstruct one full-input elapsed-hours figure; never execute a subject."""
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import statistics
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VIS = Path('/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4')
ORIGINAL = ROOT / 'optimization-history-v1/history.json'
INPUT_SHA = '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


rows = [r for r in read(ORIGINAL)['records']
        if r['bases'] == 125000000 and not r.get('earlier_lowering')]
# Preserve the existing snapshot, and explicitly append the subsequently
# measured negative trial. Parent controls are not new implementation stages.
for session in (1, 2):
    rel = f'full-candidate-value-loads-state-v{session}/results.json'
    p = ROOT / rel
    d = read(p)
    assert d['input_sha256'] == INPUT_SHA
    observations = []
    for sample in d['samples']:
        if sample['subject'] != 'candidate':
            continue
        proc = ROOT / sample['process']
        assert sha(proc) == sample['process_sha256']
        receipt = read(proc)
        assert receipt['quantitative_benchmark'] and receipt['exit_status'] == 0
        assert receipt['group_closed'] and receipt['reaped']
        assert receipt['elapsed_seconds'] == sample['seconds']
        birth = receipt['birth_identity']
        timestamp = birth['birth_seconds'] + birth['birth_microseconds'] / 1e6
        observations.append(dict(seconds=sample['seconds'], timestamp=timestamp,
            process=sample['process'], process_sha256=sample['process_sha256']))
    values = [o['seconds'] for o in observations]
    m = d['median_seconds']
    assert statistics.median(values) == m['candidate']
    rows.append(dict(key='candidate-value-loads', label='Separate early count loads (not promoted)',
        commit=d['source']['commit'], timestamp=statistics.median(o['timestamp'] for o in observations),
        time_start=min(o['timestamp'] for o in observations),
        time_end=max(o['timestamp'] + o['seconds'] for o in observations),
        observations=observations, receipt=rel, receipt_sha256=sha(p), bases=125000000,
        seconds=m['candidate'], rust_seconds=m['rust'], x_rust=m['candidate']/m['rust'],
        parent_seconds=m['parent'], n=len(values), samples=values, variant='candidate',
        single_run=False, trial=True, comparisons=d['paired_comparisons'], input_sha256=INPUT_SHA))

rows.sort(key=lambda r: r['timestamp'])
t0 = rows[0]['timestamp']
processes = {}
for r in rows:
    assert r['input_sha256'] == INPUT_SHA
    assert sha(ROOT/r['receipt']) == r['receipt_sha256']
    assert abs(statistics.median(r['samples']) - r['seconds']) < 1e-10
    assert abs(r['seconds']/r['rust_seconds'] - r['x_rust']) < 1e-10
    assert r['n'] == len(r['observations']) == len(r['samples'])
    r['hours'] = (r['timestamp'] - t0)/3600
    for o in r['observations']:
        p = ROOT/o['process']
        assert sha(p) == o['process_sha256']
        receipt = read(p)
        assert receipt['exit_status'] == 0 and receipt['group_closed'] and receipt['reaped']
        assert abs(receipt['elapsed_seconds']-o['seconds']) < 1e-10
        b = receipt['birth_identity']
        assert abs(b['birth_seconds']+b['birth_microseconds']/1e6-o['timestamp']) < 1e-6
        processes[o['process']] = o['process_sha256']

# Ordinary least squares in log runtime: equal weight for each retained cohort.
# A free intercept is essential: this tests a single exponential, rather than
# forcing it through the extreme first observation. This is descriptive only.
xs = [r['hours'] for r in rows]
zs = [math.log(r['x_rust']) for r in rows]
xmean, zmean = statistics.mean(xs), statistics.mean(zs)
slope = sum((x-xmean)*(z-zmean) for x,z in zip(xs,zs))/sum((x-xmean)**2 for x in xs)
intercept = zmean - slope*xmean
A, k = math.exp(intercept), -slope
residuals = [z-intercept-slope*x for x,z in zip(xs,zs)]
assert abs(sum(residuals)) < 1e-9
assert abs(sum(x*e for x,e in zip(xs,residuals))) < 1e-8
sse = sum(e*e for e in residuals)
log_r2 = 1-sse/sum((z-zmean)**2 for z in zs)
raw_mean = statistics.mean(r['x_rust'] for r in rows)
raw_r2 = 1-sum((r['x_rust']-A*math.exp(-k*r['hours']))**2 for r in rows)/sum((r['x_rust']-raw_mean)**2 for r in rows)
fit = dict(model='r(h) = A * exp(-k * h)', A=A, k_per_hour=k,
    half_life_hours=math.log(2)/k, r_squared_log=log_r2, r_squared_original=raw_r2,
    exp_rmse_log=math.exp(math.sqrt(sse/len(rows))),
    method='Unweighted least squares of natural-log runtime ratios, one observation per retained cohort; free intercept, not anchored to t=0.',
    interpretation='Poor global fit: the sharp initial drops and slower long tail are not one constant exponential rate. Not a forecast or an estimate of causal gain per hour.')

events = [
    ('packed', 'Compact-key tables', 4.5, 82),
    ('packed-ssa', 'Register-based loops', 5.5, 32),
    ('parallel', 'Seven parallel workers', 8.0, 15),
    ('cold-origin', 'Move error work off the hot path', 9.5, 8.2),
    ('source-edge-facts', 'Prove traversal facts once', 13.3, 5.2),
    ('frozen-map', 'Retain maps for private reads', 16.2, 3.0),
    ('escrow-spin', 'Bounded lock retry', 26.0, 2.35),
    ('worker-local-credit', 'Worker-local budget credit', 32.3, 5.2),
    ('pure-scalar-state', 'Pure scalar graph + SSA', 40.5, 2.05),
]
callouts = []
for i,(key,label,lx,ly) in enumerate(events,1):
    r = next(r for r in rows if r['key'] == key)
    callouts.append(dict(number=i,key=key,label=label,hours=r['hours'],
        seconds=r['seconds'],parent_seconds=r['parent_seconds'],x_rust=r['x_rust'],
        parent_x_rust=r['parent_seconds']/r['rust_seconds'],
        reduction_percent=100*(1-r['seconds']/r['parent_seconds']),
        speedup=r['parent_seconds']/r['seconds'],n=r['n'],receipt=r['receipt'],
        label_hours=lx,label_ratio=ly,
        basis='Candidate median versus its own contemporaneous parent median; descriptive, not adjacent historical ratios.'))

report = dict(schema='mech-history-hours-v1', t0_timestamp=t0,
    t0_utc=datetime.fromtimestamp(t0,timezone.utc).isoformat(),
    t0_seconds=rows[0]['seconds'],t0_x_rust=rows[0]['x_rust'],
    original_history_sha256=sha(ORIGINAL), builder_sha256=sha(Path(__file__)),
    cohorts=len(rows), stages=len({r['key'] for r in rows}),
    process_observations=sum(r['n'] for r in rows), unique_processes=len(processes),
    final_cohort_hours=rows[-1]['hours'], fit=fit, discontinuities=callouts, records=rows,
    exclusions=['Earlier different library-update lowering', 'All smaller inputs',
        'Timeouts without completed durations', 'Instrumented profiles and counter runs',
        'Parent/anchor controls as additional implementation stages'],
    notes=['Elapsed hours use recovered process births, including all gaps; not active working time.',
        'All retained full-input candidate cohorts and negative trials are included, not a best-so-far envelope.',
        'Each ratio uses its own contemporaneous Rust median; Rust denominators change across cohorts.',
        'The initial checkpoint was referred to as approximately 218x; the exact retained ratio is 216.164749x.',
        'The last two cohorts are an unpromoted regression; the retained production source remains 93015bc6298b77fd10402e88baea5e3bfd89b28d.',
        'First three highlighted changes have one candidate process each; later cohorts have repeat observations.'])
HERE.mkdir(exist_ok=True)
(HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
with (HERE/'cohorts.csv').open('w') as f:
    fields=['hours','key','commit','n','seconds','rust_seconds','x_rust','parent_seconds','receipt']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
with (HERE/'discontinuities.csv').open('w') as f:
    fields=['number','hours','key','label','parent_seconds','seconds','parent_x_rust','x_rust','reduction_percent','speedup','n','receipt']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(callouts)

# A self-contained SVG figure, exported unchanged to PNG by the companion script.
W,H=1800,1080
left,right,top,bottom=115,1738,166,864
xmax=math.ceil(max(xs)/6)*6
ymin,ymax=.5,320
def X(x): return left+(right-left)*x/xmax
def Y(y): return bottom-(bottom-top)*(math.log(y)-math.log(ymin))/(math.log(ymax)-math.log(ymin))
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
    '<title id="title">K-nucleotide optimization history in elapsed hours, with an exponential fit and the largest measured drops</title>',
    '<desc id="desc">Blue dots show every full-input candidate cohort. A dashed exponential fits log runtime. Numbered labels identify major changes using their contemporaneous parent comparison.</desc>',
    '<rect width="1800" height="1080" fill="white"/>',
    '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#182532} .muted{fill:#536171} .tick{font-size:17px} .label{font-size:19px;font-weight:600} .detail{font-size:16px;fill:#40556a} .halo{paint-order:stroke;stroke:white;stroke-width:7;stroke-linejoin:round}</style>']
def text(x,y,s,cls='',size=None,anchor='start',extra=''):
    parts.append(f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" text-anchor="{anchor}"'+(f' font-size="{size}"' if size else '')+f' {extra}>{html.escape(s)}</text>')
def line(x1,y1,x2,y2,stroke='#dce3ea',width=1,dash=None):
    parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
text(36,47,'K-nucleotide: the path to Rust parity',size=34,extra='font-weight="700"')
text(36,80,'125 million bases · complete process including startup · t=0 at the initial ≈218× checkpoint',cls='muted',size=19)
parts.append('<circle cx="44" cy="115" r="5" fill="#176cc1"/>')
text(58,121,f"{len(rows)} cohort medians / early single runs",size=17)
parts.append('<circle cx="458" cy="115" r="3" fill="#176cc1" opacity=".25"/>')
text(470,121,f"{sum(r['n'] for r in rows):,} individual process observations",size=17)
line(900,115,942,115,'#697887',2.5,'9 6')
text(954,121,'Single exponential fit',size=17)
text(1738,121,'Lower is faster',cls='muted',size=17,anchor='end')
for v in [.5,1,2,5,10,20,50,100,200]:
    line(left,Y(v),right,Y(v),'#b8c6d2' if v==1 else '#e3e9ef',1.7 if v==1 else 1,'7 5' if v==1 else None)
    text(left-15,Y(v)+6,f'{v:g}×',cls='tick',anchor='end')
for v in range(0,xmax+1,6):
    line(X(v),top,X(v),bottom,'#e8edf2')
    text(X(v),bottom+31,str(v),cls='tick',anchor='middle')
line(left,bottom,right,bottom,'#8b9aa9',1.2)
line(left,top,left,bottom,'#8b9aa9',1.2)
text((left+right)/2,bottom+68,'Elapsed hours since the first completed full-input run',size=21,anchor='middle')
text(27,(top+bottom)/2,'Mech runtime / Rust runtime (log scale)',size=21,anchor='middle',extra=f'transform="rotate(-90 27 {(top+bottom)/2})"')
parts.append(f'<clipPath id="plot"><rect x="{left-8}" y="{top-8}" width="{right-left+16}" height="{bottom-top+16}"/></clipPath><g clip-path="url(#plot)">')
path=' '.join(('M' if i==0 else 'L')+f'{X(max(xs)*i/600):.2f},{Y(A*math.exp(-k*max(xs)*i/600)):.2f}' for i in range(601))
parts.append(f'<path d="{path}" fill="none" stroke="#697887" stroke-width="2.7" stroke-dasharray="9 6"/>')
first=[];seen=set()
for r in rows:
    if r['key'] not in seen:
        first.append(r);seen.add(r['key'])
path=' '.join(('M' if i==0 else 'L')+f'{X(r["hours"]):.2f},{Y(r["x_rust"]):.2f}' for i,r in enumerate(first))
parts.append(f'<path d="{path}" fill="none" stroke="#176cc1" stroke-opacity=".24" stroke-width="1.6"/>')
for r in rows:
    for o in r['observations']:
        parts.append(f'<circle cx="{X((o["timestamp"]-t0)/3600):.2f}" cy="{Y(o["seconds"]/r["rust_seconds"]):.2f}" r="2.8" fill="#176cc1" opacity=".2"/>')
for r in rows:
    parts.append(f'<circle cx="{X(r["hours"]):.2f}" cy="{Y(r["x_rust"]):.2f}" r="4.6" fill="#176cc1"/>')
parts.append('</g>')
text(X(0)+15,Y(rows[0]['x_rust'])-10,'t=0 · 216.2× · 118.60 s',cls='halo',size=18)
text(right-3,Y(1)-10,'Rust = 1×',cls='halo muted',size=17,anchor='end')

# Keep the fit summary in the empty upper-right of the data region.
parts.append('<rect x="977" y="193" width="700" height="149" rx="10" fill="#f6f8fa" stroke="#dce3ea"/>')
text(1000,224,'ONE EXPONENTIAL, FITTED TO ALL COHORTS',cls='muted',size=16,extra='font-weight="700"')
text(1000,258,f'r(h) = {A:.2f} × exp(−{k:.4f} h)',size=24)
text(1000,288,f'R² in log space: {log_r2:.2f} · multiplicative RMSE: {fit["exp_rmse_log"]:.2f}×',size=18)
text(1000,318,'Poor global fit: sharp early steps, then a much slower tail.',cls='muted',size=18)

for a in callouts:
    px,py=X(a['hours']),Y(a['x_rust'])
    lx,ly=X(a['label_hours']),Y(a['label_ratio'])
    line(px,py,lx-15,ly-8,'#8fa8bf',1.2)
    parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5.6" fill="#176cc1"/>')
    text(lx,ly,f"{a['number']}  {a['label']}",cls='label halo')
    text(lx,ly+23,f"{a['hours']:.1f} h · {a['x_rust']:.2f}× Rust · {a['reduction_percent']:.1f}% less time",cls='detail halo')

line(36,956,1764,956,'#dce3ea')
text(36,983,'Drop labels compare each change with its contemporaneous parent. The first three highlighted checkpoints are single runs.',cls='muted',size=16)
text(36,1008,'All trials are shown, including regressions; the last separate-load trial was not promoted. No small-input or instrumented timings are mixed in.',cls='muted',size=16)
text(36,1033,'The ≈218× checkpoint is 216.1647× in the retained receipt. Time comes from process launches; elapsed hours include all intervening gaps.',cls='muted',size=16)
text(36,1058,'A free-intercept log-space fit is descriptive, not a forecast. Each runtime ratio uses that cohort’s own Rust median.',cls='muted',size=16)
parts.append('</svg>')
svg='\n'.join(parts)+'\n'
(HERE/'mech-history-hours-exponential.svg').write_text(svg)
(VIS/'mech-history-hours-exponential.svg').write_text(svg)
(VIS/'mech-history-hours-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('records','discontinuities')},indent=2))
