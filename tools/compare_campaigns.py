#!/usr/bin/env python3
"""Compare independent campaigns only under identical task and measurement contracts."""
import argparse
import json
import math
from pathlib import Path
import random
import statistics

from benchmark_suite import save


def compare(baseline, candidate, metric, seed=1729):
    for field in ('task_hash','measurement_hash','source_sha256','backend','environment_hash'):
        if baseline.get(field)!=candidate.get(field):return {'status':'incompatible','reason':f'{field} differs'}
    if baseline['outcome']!='ok' or candidate['outcome']!='ok':
        return {'status':'inconclusive','reason':'one or both records did not qualify'}
    a=baseline.get('summary',{}).get(metric,{}).get('samples',[])
    b=candidate.get('summary',{}).get(metric,{}).get('samples',[])
    if not a or not b or any(not math.isfinite(n) or n<=0 for n in a+b):
        return {'status':'inconclusive','reason':'no positive accepted samples for this metric'}
    ratio=statistics.median(b)/statistics.median(a)
    result={'status':'informational','ratio':ratio,'percent_change':100*(ratio-1),'performance_gate':False,
            'method':'independent fork resampling; ratio of medians','baseline_forks':len(a),'candidate_forks':len(b)}
    if min(len(a),len(b))<5:
        result['reason']='at least five independent forks in each campaign required for screening'
        return result
    rng=random.Random(seed)
    estimates=sorted(statistics.median(rng.choices(b,k=len(b)))/statistics.median(rng.choices(a,k=len(a))) for _ in range(4000))
    low,high=estimates[100],estimates[3899]
    result['interval_95']=[low,high]
    result['status']='suspected_regression' if low>1.05 else 'improvement' if high<.95 else 'inconclusive'
    result['reason']='independent confirmation required; separate campaigns do not form paired blocks'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--metric',default='resident_turn_seconds')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    a=json.loads(args.baseline.read_text());b=json.loads(args.candidate.read_text())
    previous={(r['case_id'],r['backend']):r for r in a['results'] if r['lane']=='candidate'}
    results=[]
    for record in b['results']:
        key=record['case_id'],record['backend']
        if record['lane']!='candidate' or key not in previous:continue
        result=compare(previous[key],record,args.metric)
        if b.get('experiment')=='compiler_acceleration' and record['backend']=='native':
            for field in ('object_sha256','executable_sha256'):
                left={s[field] for s in previous[key]['samples']}
                right={s[field] for s in record['samples']}
                if len(left)!=1 or left!=right:
                    result={'status':'incompatible','reason':f'preserved-output experiment changed {field}'}
                    break
        results.append({'case_id':key[0],'backend':key[1],**result})
    save(args.output,{'schema':'mech.benchmark-comparison.v1','baseline':a['id'],'candidate':b['id'],
                      'metric':args.metric,'performance_gate':False,'results':results})
    print(f'Comparison: {args.output}')


if __name__=='__main__':main()
