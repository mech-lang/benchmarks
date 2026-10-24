"""Resolve the observed small full-input effect in a predeclared larger batch."""
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
plan=json.loads((OUT/'expanded-plan.json').read_text())
assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==plan['source_commit']
assert not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True)
def run(label,args):
    with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
        result=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
    print(label,'exit',result.returncode,flush=True)
    if result.returncode: sys.exit(result.returncode)
for index,order in enumerate(plan['orders'],1):
    run('expanded-'+str(index),['qualify_full.py','--timing','disjoint-state-timing-v1','--compiler','compiler-v68','--binary','counting-disjoint-state','--receipt',f'full-disjoint-state-expanded-v{index}','--parent-receipt','escrow-backoff12-timing-v1','--parent-binary','counting-escrow-backoff12','--comparison-work','72057594037927936','--minimum-parallel-peak','7','--require-packed-map','--require-parallel-tasks','7','--order',*order])
run('expanded-cohort',['summarize_full.py','--receipt','full-disjoint-state-expanded-cohort-v1',*[f'full-disjoint-state-expanded-v{i}' for i in range(1,31)]])
r=json.loads((HERE/'full-disjoint-state-expanded-cohort-v1/results.json').read_text())
change=100*(r['median_seconds']['mech']/r['median_seconds']['baseline']-1)
pairs=sum(a<b for a,b in zip(r['samples_seconds']['mech'],r['samples_seconds']['baseline']))
print(json.dumps(dict(median_seconds=r['median_seconds'],x_rust=r['x_rust'],change_percent=change,faster_pairs=pairs,passes_promotion_threshold=change<=-1 and pairs>=20)),flush=True)
