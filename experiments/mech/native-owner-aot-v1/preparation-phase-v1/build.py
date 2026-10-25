"""Build a separately instrumented host around the unchanged guest object."""
import difflib
import fcntl
import json
import re
from pathlib import Path
import shutil
import sys

STUDY=Path(__file__).resolve().parent
HERE=STUDY.parent
SOURCE=Path('/private/tmp/mech-native-hashmap-performance')
sys.path.insert(0,str(HERE/'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state
label=sys.argv[1]
spec=read(STUDY/('build-'+label+'.json'))
before=source_state(); assert not before['status'] and before['commit']==spec['source_commit']
probe=SOURCE/'hosts/gpu/src/native_artifact/program_preparation_probe.rs'
assert process.sha(probe)==process.sha(STUDY/'phase_probe.rs')==spec['probe_sha256']
parent=HERE/'.build'/(spec['parent_binary']+'.project')
project=HERE/'.build'/(spec['output']+'.project')
if not project.exists(): shutil.copytree(parent,project)
launcher=project/'src/main.rs'
old=(parent/'src/main.rs').read_text(); marker='fn main() {\n'; assert old.count(marker)==1
new=old.replace(marker,marker+'    let _preparation_diagnostic = mech_gpu::native_artifact::preparation_probe::Root::new();\n')
launcher.write_text(new)
out=STUDY/('build-'+label+'-v2'); out.mkdir(exist_ok=False)
(out/'launcher.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='parent-launcher.rs',tofile='diagnostic-launcher.rs')))
# Regenerate only the copied launcher's source pin and the script's own pin.
# Every other canonical object/resource/input pin and every check remains.
manifest=read(parent/'linked-manifest.json')
original_pins=dict(manifest['pins'])
script=(parent/'build.rs').read_text()
match=re.search(r'^const EXPECTED: &str = ("(?:[^"\\]|\\.)*");$',script,re.M)
assert match
expected=json.loads(json.loads(match[1]))
assert expected['src/main.rs']==process.sha(parent/'src/main.rs')
expected['src/main.rs']=process.sha(launcher)
new_literal=json.dumps(json.dumps(expected,sort_keys=True,separators=(',',':')))
script=script[:match.start(1)]+new_literal+script[match.end(1):]
(project/'build.rs').write_text(script)
manifest['pins']['src/main.rs']=process.sha(launcher)
manifest['pins']['build.rs']=process.sha(project/'build.rs')
assert {k for k in original_pins if original_pins[k]!=manifest['pins'][k]}=={'src/main.rs','build.rs'}
process.save(project/'linked-manifest.json',manifest)
process.save(out/'diagnostic-manifest.json',manifest)
(out/'diagnostic-build.rs').write_text(script)
process.save(out/'pin-update.json',dict(before=original_pins,after=manifest['pins'],checks_removed=0))
receipt=read(HERE/spec['parent_receipt']/'results.json')
assert process.sha(project/'program.o')==receipt['object_sha256']
prepared=read(HERE/spec['environment_receipt']/'results.json')
env={k:v for k,v in prepared['environment'].items() if not ((k.startswith('CARGO_') and k!='CARGO_HOME') or (k.startswith('RUST') and k!='RUSTUP_HOME'))}
target=SOURCE/'target/mech-native/cargo-target'
command=['/Users/cim310/.cargo/bin/cargo','+nightly-2026-03-03','rustc','--manifest-path',str(project/'Cargo.toml'),'--release','--offline','--locked','--jobs','1','--bin',spec['package'],'--target-dir',str(target),'--','-C','lto=fat','-C','codegen-units=1','-C','strip=none']
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino==83858837
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    result=process.execute(command,out/'build',env,lock,deadline=1800,quantitative=False)
    report=dict(status='build-failed',source_before=before,source_after=source_state(),spec_sha256=process.sha(STUDY/('build-'+label+'.json')),driver_sha256=process.sha(Path(__file__)),environment=env,primary_benchmark_samples=0,guest_object_sha256=receipt['object_sha256'],launcher_sha256=process.sha(launcher),probe_sha256=process.sha(probe))
    if result['exit_status']==0:
        binary=HERE/'.build'/spec['output'];shutil.copy2(target/'release'/spec['package'],binary)
        report.update(status='diagnostic-host-built',binary=str(binary),binary_sha256=process.sha(binary))
    process.save(out/'results.json',report)
    assert report['source_before']==report['source_after'] and result['exit_status']==0
    print(label,'diagnostic built, unchanged guest',receipt['object_sha256'],flush=True)
