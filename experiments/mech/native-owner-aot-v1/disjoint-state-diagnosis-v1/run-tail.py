"""Complete bounded Mech-only prefix observations and retained profile partitions."""
import subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
def run(label,args):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout, (OUT/(label+'.controller.stderr')).open('wb') as stderr:
  r=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
run('prefix-threads-v2',['disjoint-state-diagnosis-v1/thread-prefix-driver-v2.py','disjoint-state-prefix-thread-lifetimes-v2','--prefix'])
run('preparation',['disjoint-state-diagnosis-v1/preparation.py'])
run('kernel-routes',['disjoint-state-diagnosis-v1/kernel_routes.py'])
