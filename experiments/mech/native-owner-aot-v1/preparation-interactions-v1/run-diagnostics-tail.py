"""Collect counters and current worker-appearance bounds after primary timing."""
import subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
def run(label,args):
 with (OUT/(label+'.controller.stdout')).open('wb') as stdout,(OUT/(label+'.controller.stderr')).open('wb') as stderr:
  r=subprocess.run([sys.executable,*args],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
run('hardware',['preparation-interactions-v1/hardware.py'])
run('threads',['preparation-interactions-v1/thread-driver.py','preparation-combined-thread-lifetimes-v1'])
run('preparation',['preparation-interactions-v1/preparation.py'])
