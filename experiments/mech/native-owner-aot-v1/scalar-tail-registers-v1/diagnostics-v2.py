"""Retry only the sandbox-denied profile with fresh immutable output paths."""
from pathlib import Path
import subprocess,sys
STUDY=Path(__file__).resolve().parent
for label,name in [('profile-capture-v2','profile-capture-v2.py'),('profile-analysis-v2','analyze-v2.py'),('counter','counters.py')]:
 with (STUDY/(label+'.controller.stdout')).open('xb') as out,(STUDY/(label+'.controller.stderr')).open('xb') as err:
  r=subprocess.run([sys.executable,str(STUDY/name)],stdout=out,stderr=err)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
