#!/usr/bin/env python3
"""Direct nonlinear least-squares exponential fits of full-input runtime ratios."""
import hashlib
import html
import json
import math
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
VIS=Path('/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4')
previous=ROOT/'optimization-history-hours-v1/analysis.json'
data=json.loads(previous.read_text())
rows=data['records']
assert len(rows)==118 and sum(r['n'] for r in rows)==708
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in rows:
    assert sha(ROOT/r['receipt'])==r['receipt_sha256']
    assert abs(statistics.median(r['samples'])/r['rust_seconds']-r['x_rust'])<1e-10
xs=[r['hours'] for r in rows]
ys=[r['x_rust'] for r in rows]
n=len(rows)
sy=sum(ys)
sst=sum((y-sy/n)**2 for y in ys)


def projection(k, offset):
    """At fixed k solve the linear least-squares A and C exactly."""
    g=[math.exp(-k*x) for x in xs]
    sg=sum(g);squared=sum(v*v for v in g);cross=sum(v*y for v,y in zip(g,ys))
    if offset:
        A=(cross-sg*sy/n)/(squared-sg*sg/n)
        C=(sy-A*sg)/n
        if C<0:
            C=0.;A=cross/squared
    else:
        A=cross/squared;C=0.
    assert A>0 and C>=0
    residual=[y-C-A*v for y,v in zip(ys,g)]
    return dict(A=A,C=C,k_per_hour=k,sse=sum(v*v for v in residual),residuals=residual)


def fit(offset):
    # Profile out A/C, bracket every local minimum on a broad log-k grid, then
    # refine each bracket. No initial point, parity floor or intercept is fixed.
    grid=[math.exp(math.log(1e-6)+(math.log(100)-math.log(1e-6))*i/1600) for i in range(1601)]
    scan=[projection(k,offset)['sse'] for k in grid]
    indices=[i for i in range(1,len(grid)-1) if scan[i]<scan[i-1] and scan[i]<=scan[i+1]]
    candidates=[]
    phi=(1+math.sqrt(5))/2
    for i in indices:
        lo,hi=grid[i-1],grid[i+1]
        for _ in range(150):
            a=hi-(hi-lo)/phi;b=lo+(hi-lo)/phi
            if projection(a,offset)['sse']<projection(b,offset)['sse']:hi=b
            else:lo=a
        candidates.append(projection((lo+hi)/2,offset))
    result=min(candidates,key=lambda r:r['sse'])
    assert result['sse']<=min(scan)+1e-8
    assert result['sse']<scan[0] and result['sse']<scan[-1]
    A,C,k=result['A'],result['C'],result['k_per_hour']
    residual=result.pop('residuals')
    g=[math.exp(-k*x) for x in xs]
    gradient=dict(A=-2*sum(e*v for e,v in zip(residual,g)),
        k=2*A*sum(e*x*v for e,x,v in zip(residual,xs,g)))
    if offset:gradient['C']=-2*sum(residual)
    assert max(abs(v) for v in gradient.values())<.01,gradient
    result.update(model='C + A exp(-k h)' if offset else 'A exp(-k h)',
        r_squared_original=1-result['sse']/sst,rmse_ratio=math.sqrt(result['sse']/n),
        method='Direct nonlinear least squares in measured Mech/Rust ratios; one equal weight per retained cohort.',
        profile_grid=dict(k_min=grid[0],k_max=grid[-1],points=len(grid),local_minima=len(indices)),
        first_derivatives_sse=gradient,
        prediction_at_zero=C+A,prediction_at_48h=C+A*math.exp(-k*48))
    return result


simple=fit(False)
offset=fit(True)
assert offset['sse']<simple['sse']
report=dict(schema='mech-history-direct-exponential-fit-v2',source_analysis_sha256=sha(previous),
    builder_sha256=sha(Path(__file__)),cohorts=n,process_observations=708,t0_timestamp=data['t0_timestamp'],
    simple_exponential=simple,offset_exponential=offset,
    scope='Same 118 full-input cohorts and same exact launch coordinates as v1. Only the fitting objective and display change; no subjects are executed.',
    notes=['The prior plot fit log ratios; this plot minimizes squared error in the original runtime ratios.',
        'The offset is fitted freely, not fixed to Rust parity. A and C are nonnegative, k is positive.',
        'Large early ratios dominate original-scale R-squared. The tail inset shows the remaining mismatch.',
        'The fitted 1.55x offset is not a physical floor: actual later cohorts reach approximately 1x.',
        'All retained trials and repeated cohorts remain. This is descriptive and not a forecast.'])
(HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(VIS/'mech-history-hours-best-fit-analysis.json').write_text(json.dumps(report,indent=2)+'\n')

W,H=1800,1250
L,R,T,B=115,1738,168,888
xmax=54
X=lambda x:L+(R-L)*x/xmax
Y=lambda y:B-(B-T)*y/240
parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
    '<title id="title">K-nucleotide optimization history with direct best-fit exponentials</title>',
    '<desc id="desc">A linear main plot shows the exponential initial decline. A magnified log-scale inset shows the later trajectory continuing below the fitted offset.</desc>',
    f'<rect width="{W}" height="{H}" fill="white"/>',
    '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#182532}.muted{fill:#536171}.tick{font-size:17px}.halo{paint-order:stroke;stroke:white;stroke-width:7;stroke-linejoin:round}.label{font-size:19px;font-weight:600}.number{font-size:16px;font-weight:700;fill:#176cc1}</style>']
def text(x,y,value,size=17,cls='',anchor='start',extra=''):
    parts.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" class="{cls}" text-anchor="{anchor}" {extra}>{html.escape(str(value))}</text>')
def line(x1,y1,x2,y2,color='#e3e9ef',width=1,dash=None):
    parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def curve(model,xf,yf,start,end,color,width=2.5,dash=None):
    points=[]
    for i in range(801):
        x=start+(end-start)*i/800
        y=model['C']+model['A']*math.exp(-model['k_per_hour']*x)
        points.append(('M' if i==0 else 'L')+f'{xf(x):.2f},{yf(y):.2f}')
    parts.append(f'<path d="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def observations(xf,yf,predicate=lambda r:True):
    for r in rows:
        if not predicate(r):continue
        for o in r['observations']:
            x=(o['timestamp']-data['t0_timestamp'])/3600
            y=o['seconds']/r['rust_seconds']
            parts.append(f'<circle cx="{xf(x):.2f}" cy="{yf(y):.2f}" r="2.5" fill="#176cc1" opacity=".2"/>')
        parts.append(f'<circle cx="{xf(r["hours"]):.2f}" cy="{yf(r["x_rust"]):.2f}" r="4.5" fill="#176cc1"/>')

text(36,47,'K-nucleotide: exponential fits to the measured runtimes',34,extra='font-weight="700"')
text(36,80,'125 million bases · complete-process timings · elapsed hours from the initial ≈218× checkpoint',19,'muted')
parts.append('<circle cx="44" cy="115" r="5" fill="#176cc1"/>')
text(58,121,'118 cohort medians / early single runs')
line(505,115,549,115,'#6f7c89',2.7,'9 6');text(562,121,'Direct exponential fit')
line(850,115,894,115,'#b85f12',3);text(908,121,'Direct fit with a free offset')
text(1738,121,'Blue dots: measured results',17,'muted',anchor='end')
for v in range(0,241,40):
    line(L,Y(v),R,Y(v));text(L-16,Y(v)+6,f'{v}×',anchor='end')
for v in range(0,55,6):
    line(X(v),T,X(v),B,'#e8edf2');text(X(v),B+30,v,anchor='middle')
line(L,B,R,B,'#8b9aa9',1.2);line(L,T,L,B,'#8b9aa9',1.2)
text((L+R)/2,B+68,'Elapsed hours since the first completed full-input run',21,anchor='middle')
text(28,(T+B)/2,'Mech runtime / Rust runtime (linear scale)',21,anchor='middle',extra=f'transform="rotate(-90 28 {(T+B)/2})"')
parts.append(f'<clipPath id="main"><rect x="{L-8}" y="{T-8}" width="{R-L+16}" height="{B-T+16}"/></clipPath><g clip-path="url(#main)">')
curve(simple,X,Y,0,max(xs),'#6f7c89',2.7,'9 6')
curve(offset,X,Y,0,max(xs),'#b85f12',3)
observations(X,Y)
parts.append('</g>')
text(X(0)+17,Y(rows[0]['x_rust'])-14,'t=0 · 216.2× · 118.60 s',19,'halo')

# Label the three largest early steps on the linear main plot. Later steps are
# labeled in the inset, which magnifies the same observations rather than
# substituting a smaller input or a best-so-far envelope.
for key,lx,ly in [('packed',4.2,142),('packed-ssa',8.0,95),('parallel',12.0,49)]:
    e=next(a for a in data['discontinuities'] if a['key']==key)
    line(X(e['hours']),Y(e['x_rust']),X(lx)-16,Y(ly)-8,'#91a7bd',1.3)
    text(X(lx),Y(ly),f"{e['number']}  {e['label']}",19,'label halo')
    text(X(lx),Y(ly)+25,f"{e['hours']:.1f} h · {e['reduction_percent']:.1f}% less time",17,'muted halo')

parts.append('<rect x="832" y="186" width="880" height="154" rx="10" fill="#f6f8fa" stroke="#dce3ea"/>')
text(854,215,'DIRECT LEAST SQUARES IN RUNTIME RATIOS',16,'muted',extra='font-weight="700"')
text(854,248,f"r(h) = {offset['C']:.2f} + {offset['A']:.2f} exp(−{offset['k_per_hour']:.3f} h)",23)
text(854,278,f"With offset: R² = {offset['r_squared_original']:.4f}   ·   without offset: R² = {simple['r_squared_original']:.4f}",18)
text(854,310,'Early values dominate this score; the later results keep improving.',18,'muted')

# Tail inset inside the same full-input figure.
iL,iR,iT,iB=902,1681,411,751
iX=lambda x:iL+(iR-iL)*(x-3)/(51-3)
iY=lambda y:iB-(iB-iT)*(math.log(y)-math.log(.8))/(math.log(12)-math.log(.8))
parts.append('<rect x="830" y="363" width="884" height="450" rx="10" fill="white" stroke="#becbd7"/>')
text(850,392,'Same data from hour 3 onward · magnified log scale',18,'muted')
for v in [1,2,5,10]:
    line(iL,iY(v),iR,iY(v),'#b8c6d2' if v==1 else '#e3e9ef',1.5 if v==1 else 1,'6 4' if v==1 else None)
    text(iL-13,iY(v)+5,f'{v}×',15,anchor='end')
for v in [3,12,24,36,48]:
    line(iX(v),iT,iX(v),iB,'#e8edf2');text(iX(v),iB+26,f'{v} h',15,anchor='middle')
parts.append(f'<clipPath id="inset"><rect x="{iL-5}" y="{iT}" width="{iR-iL+10}" height="{iB-iT}"/></clipPath><g clip-path="url(#inset)">')
curve(simple,iX,iY,3,max(xs),'#6f7c89',2.2,'7 5')
curve(offset,iX,iY,3,max(xs),'#b85f12',2.7)
observations(iX,iY,lambda r:r['hours']>=3)
parts.append('</g>')
text(iR-4,iY(offset['C'])-9,f"Fitted offset: {offset['C']:.2f}×",16,'halo',anchor='end')
text(iR-4,iY(1)+22,'Actual later results: ≈1×',16,'halo',anchor='end')
for e in data['discontinuities'][3:]:
    dx,dy={4:(29,-18),5:(42,-11),6:(35,-18),7:(0,-24),8:(-8,-24),9:(-8,-23)}[e['number']]
    px,py=iX(e['hours']),iY(e['x_rust'])
    line(px,py,px+dx,py+dy,'#8fa8bf',1.1)
    text(px+dx,py+dy,str(e['number']),17,'number halo',anchor='middle')

line(36,980,1764,980,'#dce3ea')
for index,e in enumerate(data['discontinuities']):
    col=index//3;row=index%3
    x=36+col*582;y=1010+row*48
    text(x,y,f"{e['number']}  {e['label']}",17,'label')
    text(x,y+20,f"{e['hours']:.1f} h · {e['x_rust']:.2f}× Rust · −{e['reduction_percent']:.1f}% vs parent",15,'muted')
text(36,1151,'Both curves minimize squared errors in the original ratios; the starting point and the offset are not fixed. Curves stop at the last observation.',16,'muted')
text(36,1176,'All 118 cohorts and 708 process observations remain, including negative trials. Drop labels compare each change with its contemporaneous parent.',16,'muted')
text(36,1201,'The first three highlighted checkpoints are single runs. The ≈218× checkpoint is 216.1647× in its retained receipt. Elapsed hours include all gaps.',16,'muted')
text(36,1226,'The fitted offset is not a floor or a forecast: the tail inset shows the later data continuing below it. Each cohort uses its own Rust median.',16,'muted')
parts.append('</svg>')
svg='\n'.join(parts)+'\n'
(HERE/'mech-history-hours-best-fit.svg').write_text(svg)
(VIS/'mech-history-hours-best-fit.svg').write_text(svg)
print(json.dumps(report,indent=2))
