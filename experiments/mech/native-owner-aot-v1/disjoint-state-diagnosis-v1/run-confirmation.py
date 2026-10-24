"""Run the predeclared confirmation batch and separate thread diagnostics serially."""
import subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
def run(label,args):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  r=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
run('expanded',['disjoint-state-diagnosis-v1/run-expanded.py'])
run('threads',['disjoint-state-diagnosis-v1/thread-driver.py','disjoint-state-thread-lifetimes-v1'])
run('prefix-threads',['disjoint-state-diagnosis-v1/thread-driver.py','disjoint-state-prefix-thread-lifetimes-v1','--prefix'])
run('preparation',['disjoint-state-diagnosis-v1/preparation.py'])
run('kernel-routes',['disjoint-state-diagnosis-v1/kernel_routes.py'])
