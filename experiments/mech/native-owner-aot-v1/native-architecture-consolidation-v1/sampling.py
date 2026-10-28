"""Collect fixed-source timings separately from final correctness qualification.

All acceptance gates remain in campaign.prerequisites and qualify.py. This
module cannot authorize a performance claim or substitute pending test evidence.
"""
import hashlib
from pathlib import Path
import subprocess

from study import HERE, ROOT, process, read, build_receipt_path
from campaign import DEFERRED_VERIFICATION, fixed_prerequisites, evidence, check_changed_inputs
import wide_slot

FILES = {'program.o', 'program.mecb', 'native-descriptor.json',
         'native-descriptor.bin', 'object-identity.bin', 'native-resources.json'}
FINAL_CHECKS = {'correctness', 'generated_processes', 'baseline_correctness',
                'changed_inputs', 'guest_code', 'representative_objects', 'wide_slot_artifacts'}


def readiness(plan):
    assert plan['verification_order'] == DEFERRED_VERIFICATION
    assert plan['qualification_sha256'] is None
    assert plan['final_verification_attestation'] == 'final-verification-attestation.json'
    result = evidence(plan['sampling_readiness'])
    assert result['schema'] == 'mech.fixed-source-sampling-readiness.v1'
    assert result['status'] == 'fixed-binaries-ready-final-verification-still-required'
    assert result['performance_qualified'] is False
    assert result['final_qualification_requires'] == sorted(FINAL_CHECKS)
    assert result['source_commits'] == dict(F=plan['final_compiler_source'], I=plan['implementation_base'])
    assert result['subject_pins'] == plan['subject_pins']
    return result


def prerequisites(plan):
    targets, pins, final, initial = fixed_prerequisites(plan)
    ready = readiness(plan)
    assert ready['source'] == final['source'] and ready['baseline_source'] == initial['source']
    assert set(ready['guest_artifacts']) == FILES
    for subject, receipt in [('F', final), ('I', initial)]:
        project = Path(receipt['executable'] + '.project')
        hashes = {name: process.sha(project / name) for name in FILES}
        assert hashes == ready['guest_artifacts']
        validation = read(build_receipt_path(ready['public_build_validation'][subject], shared=True))
        assert validation['source'] == receipt['source'] and validation['guest_artifacts'] == hashes
        assert validation['receipt_sha256'] == process.sha(build_receipt_path(
            plan['candidate_receipt'] if subject == 'F' else plan['baseline_receipt'], shared=subject == 'I'))
    assert ready['guest_artifacts']['program.o'] == final['object_sha256'] == initial['object_sha256']
    assert ready['guest_artifacts']['program.mecb'] == plan['bytecode_sha256']
    check_changed_inputs(ready['completed_checks']['changed_inputs'], pins, final)
    wide_slot.check(ready['completed_checks']['wide_slot_artifacts'], final, initial)
    return targets, pins, final, initial


def committed(revision, plan):
    ready = readiness(plan)
    receipts = [build_receipt_path(plan['candidate_receipt']),
                build_receipt_path(plan['baseline_receipt'], shared=True),
                build_receipt_path(plan['runtime_environment_receipt'], shared=True)]
    paths = [HERE / 'plan.json', HERE / 'retained-controls.json',
             HERE / plan['sampling_readiness']['path'], *receipts,
             *(ROOT / path for path in plan['controller_pins']),
             *(build_receipt_path(ref, shared=True) for ref in ready['public_build_validation'].values())]
    changed_path = HERE / ready['completed_checks']['changed_inputs']['path']
    assert process.sha(changed_path) == ready['completed_checks']['changed_inputs']['sha256']
    paths += [path for path in changed_path.parent.rglob('*') if path.is_file()]
    paths += wide_slot.check(ready['completed_checks']['wide_slot_artifacts'], read(receipts[0]), read(receipts[1]))
    for path in paths:
        relative = str(path.resolve().relative_to(ROOT.resolve()))
        blob = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + relative])
        assert hashlib.sha256(blob).hexdigest() == process.sha(path), relative
