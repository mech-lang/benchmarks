#!/usr/bin/env python3
"""Fit fast and slow exponential components; preserve the original log chart."""
import hashlib
import html
import json
import math
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
VIS=Path('/Users/cim310/.codex/visualizations/2026/10/18/01a14f74-07a7-7010-8f8b-700f121ee1e4')
source_data=ROOT/'optimization-history-hours-v1/analysis.json'
source_svg=ROOT/'optimization-history-hours-v1/mech-history-hours-exponential.svg'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=json.loads(source_data.read_text());rows=data['records']
assert len(rows)==118 and sum(r['n'] for r in rows)==708
for r in rows:
    assert sha(ROOT/r['receipt'])==r['receipt_sha256']
xs=[r['hours'] for r in rows];ys=[r['x_rust'] for r in rows];zs=[math.log(y) for y in ys]


def parameters(p):
    C,A,B,slow,delta=[math.exp(v) for v in p]
    return dict(C=C,A_fast=A,A_slow=B,k_fast=slow+delta,k_slow=slow)


def predictions(p):
    return [p['C']+p['A_fast']*math.exp(-p['k_fast']*x)+p['A_slow']*math.exp(-p['k_slow']*x) for x in xs]


def loss(p,logs):
    if max(p)>30 or min(p)<-40:return 1e100
    predicted=predictions(parameters(p))
    return sum((math.log(v)-z)**2 for v,z in zip(predicted,zs)) if logs else sum((v-y)**2 for v,y in zip(predicted,ys))


def minimize(start,logs):
    points=[list(start)]+[[v+(.2 if j==i else 0) for j,v in enumerate(start)] for i in range(5)]
    vals=[loss(p,logs) for p in points]
    for iteration in range(3500):
        order=sorted(range(6),key=lambda i:vals[i]);points=[points[i] for i in order];vals=[vals[i] for i in order]
        if max(abs(v-vals[0]) for v in vals)<1e-12 and max(abs(points[i][j]-points[0][j]) for i in range(6) for j in range(5))<1e-6:break
        center=[sum(p[j] for p in points[:-1])/5 for j in range(5)]
        reflect=[2*c-w for c,w in zip(center,points[-1])];fr=loss(reflect,logs)
        if fr<vals[0]:
            expand=[c+2*(r-c) for c,r in zip(center,reflect)];fe=loss(expand,logs)
            points[-1],vals[-1]=(expand,fe) if fe<fr else (reflect,fr)
        elif fr<vals[-2]:points[-1],vals[-1]=reflect,fr
        else:
            outside=fr<vals[-1]
            contract=[c+.5*((r if outside else w)-c) for c,r,w in zip(center,reflect,points[-1])];fc=loss(contract,logs)
            if fc<(fr if outside else vals[-1]):points[-1],vals[-1]=contract,fc
            else:
                for i in range(1,6):
                    points[i]=[(a+b)/2 for a,b in zip(points[0],points[i])];vals[i]=loss(points[i],logs)
    assert iteration<3499,'Optimizer did not converge'
    idx=min(range(6),key=lambda i:vals[i])
    p=parameters(points[idx]);pred=predictions(p)
    raw_sse=sum((y-v)**2 for y,v in zip(ys,pred))
    log_sse=sum((z-math.log(v))**2 for z,v in zip(zs,pred))
    p.update(objective='squared log-ratio errors' if logs else 'squared original-ratio errors',iterations=iteration,
        raw_sse=raw_sse,log_sse=log_sse,
        r_squared_original=1-raw_sse/sum((y-sum(ys)/len(ys))**2 for y in ys),
        r_squared_log=1-log_sse/sum((z-sum(zs)/len(zs))**2 for z in zs),
        multiplicative_rmse=math.exp(math.sqrt(log_sse/len(xs))))
    return p


starts=[(.7,213,2.5,.04,1.2),(.2,210,6,.08,1.0),(1,215,3,.02,1.5),(1,210,6,.2,.8),(.1,215,2,.01,2)]
fits={}
for logs in [False,True]:
    runs=[minimize([math.log(v) for v in initial],logs) for initial in starts]
    key='log_sse' if logs else 'raw_sse'
    best=min(runs,key=lambda r:r[key])
    assert max(r[key] for r in runs)-min(r[key] for r in runs)<1e-8
    fits['log_objective' if logs else 'original_objective']=dict(best=best,starts=starts,runs=runs)
fit=fits['original_objective']['best']
residual=[y-v for y,v in zip(ys,predictions(fit))]
gf=[math.exp(-fit['k_fast']*x) for x in xs]
gs=[math.exp(-fit['k_slow']*x) for x in xs]
gradient=dict(C=-2*sum(residual),A_fast=-2*sum(e*g for e,g in zip(residual,gf)),A_slow=-2*sum(e*g for e,g in zip(residual,gs)),
    k_fast=2*fit['A_fast']*sum(e*x*g for e,x,g in zip(residual,xs,gf)),k_slow=2*fit['A_slow']*sum(e*x*g for e,x,g in zip(residual,xs,gs)))
assert max(abs(v) for v in gradient.values())<.01,gradient

# Only the fit path and fit-related text change. Axes, original dot coordinates,
# colors, dimensions, nine annotations and their leader lines remain identical.
original_svg=source_svg.read_text()
svg=original_svg
paths=re.findall(r'<path\b[^>]*stroke="#697887"[^>]*>',svg)
assert len(paths)==1
def X(x):return 115+(1738-115)*x/54
def Y(y):return 864-(864-166)*(math.log(y)-math.log(.5))/(math.log(320)-math.log(.5))
curve=[]
for i in range(801):
    h=max(xs)*i/800
    y=fit['C']+fit['A_fast']*math.exp(-fit['k_fast']*h)+fit['A_slow']*math.exp(-fit['k_slow']*h)
    curve.append(('M' if i==0 else 'L')+f'{X(h):.2f},{Y(y):.2f}')
path=re.sub(r'\bd="[^"]*"','d="'+' '.join(curve)+'"',paths[0],count=1)
svg=svg.replace(paths[0],path)
def replace(old,new,size=None):
    global svg
    found=list(re.finditer(r'(<text\b[^>]*>)'+re.escape(html.escape(old))+r'(</text>)',svg))
    assert len(found)==1,(old,len(found))
    match=found[0];opening=match[1]
    if size:opening=re.sub(r'font-size="[^"]*"',f'font-size="{size}"',opening)
    svg=svg.replace(match[0],opening+html.escape(new)+match[2],1)
replace('Single exponential fit','Fast + slow exponential fit')
replace('ONE EXPONENTIAL, FITTED TO ALL COHORTS','FAST + SLOW EXPONENTIALS · ALL 118 COHORTS')
replace('r(h) = 4.64 × exp(−0.0388 h)',f"r(h) = {fit['C']:.3f} + {fit['A_fast']:.2f} exp(−{fit['k_fast']:.3f} h)",20)
replace('R² in log space: 0.52 · multiplicative RMSE: 1.67×',f"             + {fit['A_slow']:.3f} exp(−{fit['k_slow']:.4f} h)",20)
replace('Poor global fit: sharp early steps, then a much slower tail.',f"R² (log scale): {fit['r_squared_log']:.4f} · multiplicative RMSE: {fit['multiplicative_rmse']:.3f}×",18)
replace('A free-intercept log-space fit is descriptive, not a forecast. Each runtime ratio uses that cohort’s own Rust median.',
    'Both rates and the offset are fitted to all cohorts. This descriptive curve is not a forecast; each ratio uses its own Rust median.')
circles=lambda s:re.findall(r'<circle\b[^>]*>',s)
assert circles(original_svg)==circles(svg),'A measured dot changed'
(HERE/'mech-history-hours-log-fit.svg').write_text(svg)
(VIS/'mech-history-hours-log-fit.svg').write_text(svg)
report=dict(schema='mech-history-two-exponential-v3',model='r(h)=C+A_fast exp(-k_fast h)+A_slow exp(-k_slow h)',
    source_analysis_sha256=sha(source_data),source_svg_sha256=sha(source_svg),builder_sha256=sha(Path(__file__)),
    fitted_cohorts=118,process_observations=708,drawn_fit=fit,optimization=fits,first_derivatives_sse=gradient,
    unchanged_dot_count=len(circles(svg)),
    notes=['Exact original single log-scale chart; only the fit curve and fit-related text change.',
        'All 118 full-input cohort ratios and original elapsed-hour coordinates are retained.',
        'The plotted fit minimizes original-ratio squared errors; its log-scale R-squared is also reported.',
        'Five positive-parameter starting points converge to the same optimum for each fitting objective.',
        'Offset, amplitudes and both decay rates are free; Rust parity is not imposed.',
        'Both original-scale and log-error optimization are retained for sensitivity; no extrapolation or causal interpretation.'])
(HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
(VIS/'mech-history-hours-log-fit-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(drawn_fit=fit,gradient=gradient,measured_dots_unchanged=report['unchanged_dot_count']),indent=2))
