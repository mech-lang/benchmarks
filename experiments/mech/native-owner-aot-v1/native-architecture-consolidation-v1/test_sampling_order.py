"""Collection may precede verification; final qualification still cannot."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import campaign
import sampling
from study import process


class SamplingOrderTests(unittest.TestCase):
    def test_sampling_receipt_cannot_assert_final_qualification_or_drop_gates(self):
        plan = dict(verification_order=campaign.DEFERRED_VERIFICATION,
                    qualification_sha256=None,
                    final_verification_attestation='final-verification-attestation.json',
                    sampling_readiness={'path': 'ready.json', 'sha256': 'pin'},
                    final_compiler_source='after', implementation_base='before',
                    subject_pins=dict.fromkeys('FIWR', 'pin'))
        ready = dict(schema='mech.fixed-source-sampling-readiness.v1',
                     status='fixed-binaries-ready-final-verification-still-required',
                     performance_qualified=False,
                     final_qualification_requires=sorted(sampling.FINAL_CHECKS),
                     source_commits=dict(F='after', I='before'),
                     subject_pins=plan['subject_pins'])
        with patch.object(sampling, 'evidence', return_value=ready):
            self.assertEqual(sampling.readiness(plan), ready)
        for field, value in [('performance_qualified', True),
                             ('final_qualification_requires', ['correctness']),
                             ('source_commits', dict(F='stale', I='before')),
                             ('subject_pins', dict.fromkeys('FIWR', 'stale'))]:
            with self.subTest(field=field), patch.object(sampling, 'evidence', return_value=dict(ready, **{field:value})):
                with self.assertRaises(AssertionError):
                    sampling.readiness(plan)

    def test_final_attestation_binds_the_unchanged_sampling_plan_and_completed_gate(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(campaign, 'HERE', Path(directory)):
            root = Path(directory)
            plan = dict(verification_order=campaign.DEFERRED_VERIFICATION,
                        qualification_sha256=None,
                        final_verification_attestation='final-verification-attestation.json')
            (root/'plan.json').write_text(json.dumps(plan))
            (root/'qualification.json').write_text(json.dumps({'proceed_to_primary':False}))
            with self.assertRaises(FileNotFoundError):
                campaign.final_gate(plan)
            attestation = dict(schema='mech.final-verification-attestation.v1',
                               sampling_plan_sha256=process.sha(root/'plan.json'),
                               qualification_sha256=process.sha(root/'qualification.json'))
            (root/'final-verification-attestation.json').write_text(json.dumps(attestation))
            self.assertFalse(campaign.final_gate(plan)['proceed_to_primary'])
            (root/'qualification.json').write_text(json.dumps({'proceed_to_primary':True}))
            with self.assertRaises(AssertionError):
                campaign.final_gate(plan)
            (root/'qualification.json').write_text(json.dumps({'proceed_to_primary':False}))
            (root/'plan.json').write_text(json.dumps(dict(plan, changed_after_sampling=True)))
            with self.assertRaises(AssertionError):
                campaign.final_gate(plan)

    def test_final_qualification_still_requires_full_gate_after_collection(self):
        fixed = ({}, {}, {'source':{}}, {'source':{}})
        with patch.object(campaign, 'fixed_prerequisites', return_value=fixed), \
             patch.object(campaign, 'final_gate', side_effect=FileNotFoundError('pending final verification')):
            with self.assertRaisesRegex(FileNotFoundError, 'pending final verification'):
                campaign.prerequisites({'verification_order':campaign.DEFERRED_VERIFICATION})


if __name__ == '__main__':
    unittest.main()
