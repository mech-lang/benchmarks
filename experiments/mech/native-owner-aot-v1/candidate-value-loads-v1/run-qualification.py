"""Sequential regression, compiler build and exact source prefix qualification."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state
plan=read(STUDY/'plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
for args in [[sys.executable,str(STUDY/'validate.py')],
             [sys.executable,str(HERE/'build_cli.py'),plan['compiler']],
             [sys.executable,str(STUDY/'qualify-prefix.py')]]:
    result=subprocess.run(args,cwd=HERE)
    if result.returncode:sys.exit(result.returncode)
    assert source_state()==before
print('All candidate-value load regressions, compiler and prefix qualify at one clean source.',flush=True)
