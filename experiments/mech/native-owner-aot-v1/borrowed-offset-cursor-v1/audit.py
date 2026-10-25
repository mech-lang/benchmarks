"""Retain the actual emitted compact-row instruction fragments and code pins."""
import fcntl
import hashlib
from pathlib import Path
import re
import sys
STUDY=Path(__file__).resolve().parent;HERE=STUDY.parent
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN,process,read,source_state
sys.path.insert(0,str(HERE));from analyze_profile import text_section
plan=read(STUDY/'plan-v2.json');before=source_state()
assert before['commit']==plan['source_commit'] and not before['status']
project=HERE/'.build'/(plan['binary']+'.project');obj=project/'program.o'
manifest=read(project/'linked-manifest.json')
assert (manifest['object']['typed_ir_version'],manifest['object']['abi_version'],manifest['object']['work_policy_version'])==(81,29,68)
profile=read(HERE/'profile-borrowed-offset-cursor-build-v1/results.json')
primary=HERE/'.build'/plan['binary'];profile_binary=Path(profile['binary'])
assert text_section(primary)==text_section(profile_binary)
assert process.sha(obj)==profile['object_sha256']
out=STUDY/'code-audit';out.mkdir(exist_ok=False)
env=read(HERE/plan['compiler']/'results.json')['environment']
with Path(PLAN['common_mutex']).open('a+') as lock:
 assert Path(PLAN['common_mutex']).stat().st_ino==83858837
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for label,command in [('guest-otool',['/usr/bin/otool','-tvV',str(obj)]),('guest-symbols',['/usr/bin/nm','-n',str(obj)])]:
  receipt=process.execute(command,out/label,env,lock,deadline=60,quantitative=False)
  assert receipt['exit_status']==0
lines=(out/'guest-otool/stdout.bin').read_text().splitlines()
positions=[i for i,line in enumerate(lines) if re.search(r'\band\b.*#0xfffffffffffffffe\b',line)]
# Keep every match and its context; do not infer wall time from instruction counts.
assert positions,'Expected the owned-row discriminator to be cleared before descriptor access'
fragments='\n\n'.join('\n'.join(lines[max(0,i-12):i+55]) for i in positions)+'\n'
(out/'compact-row-fragments.s').write_text(fragments)
assert source_state()==before
report=dict(status='emitted-row-discriminator-and-exact-code-pins-verified',source=before,source_after=before,driver_sha256=process.sha(Path(__file__)),object_sha256=process.sha(obj),primary_sha256=process.sha(primary),profile_sha256=process.sha(profile_binary),whole_text_sha256=hashlib.sha256(text_section(primary)).hexdigest(),whole_text_bytes=len(text_section(primary)),whole_profile_text_matches_primary=True,row_discriminator_fragments=len(positions),fragments_sha256=process.sha(out/'compact-row-fragments.s'),disassembly_sha256=process.sha(out/'guest-otool/stdout.bin'),primary_benchmark_samples=0,scope='The guest object exposes the actual low-bit discriminator clear, compact u32 LF loads and checked segment selection. Source/engine/native tests establish bounds and ownership; this is an emitted-code audit, not a recovered timing partition or a new performance claim.')
process.save(out/'results.json',report)
print({k:report[k] for k in ['status','row_discriminator_fragments','whole_text_bytes','whole_text_sha256']})
