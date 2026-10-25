"""Qualify the intended layout/version changes without hiding image differences."""
from copy import deepcopy
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE))
from analyze_profile import text_section
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import read, process, source_state

plan = read(STUDY / 'execution-plan.json')
assert source_state()['commit'] == plan['source_commit'] and not source_state()['status']
parent = HERE / '.build' / (plan['parent_binary'] + '.project')
candidate = HERE / '.build' / (plan['binary'] + '.project')
for name in ('native-resources.json', 'program.mecb'):
    assert process.sha(parent / name) == process.sha(candidate / name)
a = read(parent / 'native-descriptor.json')
b = read(candidate / 'native-descriptor.json')
left, right = deepcopy(a), deepcopy(b)
for key in ('constant_bytes', 'scalar_bytes', 'identity'):
    left['descriptor'].pop(key)
    right['descriptor'].pop(key)
assert left == right
assert len(a['descriptor']['constant_bytes']) == len(b['descriptor']['constant_bytes']) == 38
assert all(y == x + 16 for x, y in zip(a['descriptor']['constant_bytes'], b['descriptor']['constant_bytes']))
assert b['descriptor']['scalar_bytes'] == a['descriptor']['scalar_bytes'] + 64
assert text_section(parent / 'program.o') == text_section(candidate / 'program.o')
assert read(parent / 'linked-manifest.json')['object']['work_policy_version'] == 66
assert read(candidate / 'linked-manifest.json')['object']['work_policy_version'] == 67
report = dict(status='only-accounted-owner-sizes-and-identity-differ', source=source_state(),
              constant_owner_byte_increase=16, constant_owner_count=38, scalar_owner_bytes_increase=64,
              guest_machine_code_identical=True, resources_identical=True, bytecode_identical=True,
              parent_descriptor_sha256=process.sha(parent / 'native-descriptor.bin'),
              candidate_descriptor_sha256=process.sha(candidate / 'native-descriptor.bin'),
              initial_resume_failure='The old identical-descriptor assertion did not allow the intended increase in concrete owner-size admission bounds. Both descriptors and all successful prefix observations are retained.',
              script_sha256=process.sha(Path(__file__)), benchmark_samples=0)
process.save(STUDY / 'image-qualification.json', report)
print(report['status'], flush=True)
