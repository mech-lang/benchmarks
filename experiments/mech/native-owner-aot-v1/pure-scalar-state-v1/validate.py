"""Serial source-pinned regression qualification after callback/window tests."""
import subprocess,sys
from pathlib import Path
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent;DISPATCH=HERE.parent/'native-owner-dispatch-v1'
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import read,source_state
plan=read(STUDY/'development-plan.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
def qualify(folder,count):
 p=DISPATCH/folder;r=read(p/'process.json');s=read(p/'source-provenance.json')
 assert r['exit_status']==0 and r['reaped'] and r['group_closed'] and not r['signals'] and not r['cleanup_errors']
 assert s['clean_revision_qualified'] and s['before']['commit']==before['commit'] and s['source_unchanged']
 assert f'{count} passed; 0 failed' in (p/'stdout.bin').read_text()
for row in plan['already_qualified_scopes']:qualify(row['folder'],row['expected_tests'])
for row in plan['scopes']:
 args=[sys.executable,str(DISPATCH/'validate_native.py'),row['folder'],row['filter'],'/private/tmp/mech-native-hashmap-performance']
 if row['engine']:args.append('--engine-budget')
 result=subprocess.run(args,cwd=HERE)
 if result.returncode:sys.exit(result.returncode)
 qualify(row['folder'],row['expected_tests']);print(row['folder'],row['expected_tests'],'passed',flush=True)
assert source_state()==before
print('All pure-scalar correctness scopes qualify at the same clean source.',flush=True)
