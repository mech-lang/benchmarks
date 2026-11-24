from pathlib import Path
from hashlib import sha256
import json, os, shutil, subprocess, time

S = Path(__file__).resolve().parent
read = lambda p: json.loads(Path(p).read_text())
pin = lambda p: sha256(Path(p).read_bytes()).hexdigest()
build = read(S / 'probe-build.json')
assert build['exit_code'] == 0 and len(build['executables']) == 1
executable = Path(build['executables'][0]['path'])
assert pin(executable) == build['executables'][0]['sha256']
shutil.copy2(executable, S / 'native-probe-executable')
out = S / 'native-probe-v1'
out.mkdir()
env = {k: v for k, v in os.environ.items() if not k.startswith('MECH_')}
records = []
for role, flags in [('off', {}), ('on', {'MECH_ARM64_INSERT_MASKED_FIELDS': '1'}), ('wide-copy', {'MECH_ARM64_INSERT_MASKED_FIELDS': 'wide-copy'}), ('wide', {'MECH_ARM64_INSERT_MASKED_FIELDS': 'wide'})]:
    folder = out / role
    folder.mkdir()
    command = [str(executable), 'masked_field_inserts_preserve_values_effects_and_fallbacks', '--exact', '--nocapture', '--test-threads=1']
    started = time.monotonic()
    with (folder / 'execution.log').open('w') as log:
        result = subprocess.run(command, env=env | flags | {'MECH_NARROW_PACK_PROBE': str(folder)}, stdout=log, stderr=log)
    record = {'role': role, 'command': command, 'flags': flags, 'seconds': time.monotonic() - started, 'exit_code': result.returncode, 'log_sha256': pin(folder / 'execution.log')}
    records.append(record)
    (out / 'runs.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 0, (folder / 'execution.log').read_text()[-7000:]
    data = read(folder / 'masked-fields.json')
    assert data['native_observations'] == 1677312 and len(data['functions']) == 4032
    record.update(native_calls=data['native_observations'], observations_sha256=pin(folder / 'masked-fields.json'))
    print(role, 'passed', record['native_calls'], 'native calls', flush=True)
off = read(out / 'off/masked-fields.json')['functions']
on = read(out / 'on/masked-fields.json')['functions']
changed = []
fallbacks = []
for a, b in zip(off, on, strict=True):
    assert {k: v for k, v in a.items() if k not in ('body', 'vcode')} == {k: v for k, v in b.items() if k not in ('body', 'vcode')}
    if a['body'] != b['body']:
        assert a['op'] != 'And', a['name']
        changed.append({'name': a['name'], 'before_bytes': len(a['body']), 'after_bytes': len(b['body'])})
    elif a['op'] == 'And':
        fallbacks.append(a['name'])
assert len(changed) >= 40 and len(fallbacks) == 1344
wide = read(out / 'wide/masked-fields.json')['functions']
widened = []
for a, b in zip(on, wide, strict=True):
    assert {k:v for k,v in a.items() if k not in ('body','vcode')} == {k:v for k,v in b.items() if k not in ('body','vcode')}
    if a['body'] != b['body']:
        assert a['op'] != 'And' and a['form'] != 'Variable', a['name']
        widened.append({'name':a['name'],'before_bytes':len(a['body']),'after_bytes':len(b['body'])})
assert len(widened) >= 10
retained = 0
retained_wide = 0
summary = {'complete': True, 'all_pass': True, 'test_executions': 4, 'native_calls': sum(r['native_calls'] for r in records), 'executable_sha256': pin(executable), 'runs': records, 'changed_functions': len(changed), 'exact_and_fallbacks': len(fallbacks), 'changes': changed, 'fallbacks': fallbacks, 'widened_functions': len(widened), 'widened': widened, 'retained_prior_functions': retained, 'retained_wide_functions': retained_wide, 'scope': 'Four independent native executions, option off/on; dirty integer words, I32/I64, none/speed, ordered aliased loads/stores, shared values, joins, signed and variable shifts, overlapping/noncontiguous masks, modulo counts, zero-fill boundaries and rejected null pointers; exact RA checker enabled.'}
(out / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print('PROBE', {k: v for k, v in summary.items() if k not in ('runs', 'changes', 'fallbacks', 'scope', 'widened')}, flush=True)
