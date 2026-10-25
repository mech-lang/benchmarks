"""Sequential separate instrumentation build, prefix qualification and full capture."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
for label,args in [('build',['build.py','candidate']),('capture',['capture.py']),('analyze',['analyze.py']),('verify',['verify.py'])]:
 with (STUDY/(label+'.controller.stdout')).open('xb') as stdout,(STUDY/(label+'.controller.stderr')).open('xb') as stderr:
  result=subprocess.run([sys.executable,str(STUDY/args[0]),*args[1:]],cwd=HERE,stdout=stdout,stderr=stderr)
 print(label,'exit',result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
print('Fresh candidate/parent/Rust phases and all task widths verified',flush=True)
