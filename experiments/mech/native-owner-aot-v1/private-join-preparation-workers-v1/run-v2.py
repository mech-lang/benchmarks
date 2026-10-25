"""Resume unchanged diagnostic binaries, reusing the successful candidate prefix."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
for label,name in [('capture-v2','capture-v2.py'),('analyze-v2','analyze-v2.py'),('verify-v2','verify-v2.py')]:
 with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
  r=subprocess.run([sys.executable,str(STUDY/name)],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
print('Fresh fused-path phases and all widths verified; successful prefix was not repeated',flush=True)
