"""Reject plausible stale or unrelated artifact evidence before a timing run."""
import copy
import gzip
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import artifact_equivalence as equivalence
import wide_slot
from study import process


class ArtifactEvidenceTests(unittest.TestCase):
    def test_wide_geometry_comes_from_actual_range_and_emitted_addresses(self):
        root = Path(__file__).parent / 'test-fixtures/wide-slot'
        descriptor = json.loads(gzip.decompress((root / 'descriptor.json.gz').read_bytes()))['descriptor']
        assembly = gzip.decompress((root / 'disassembly.txt.gz').read_bytes()).decode()
        expected = dict(packing_bits=4, selected_width=17, selected_key_bits=68, payload_bytes=24)
        self.assertEqual(wide_slot.geometry(descriptor, assembly), expected)
        # Leave the distracting width17 constant in the descriptor, but route
        # the selected range through another width: presence alone is no proof.
        wrong_width = copy.deepcopy(descriptor)
        wrong_width['plan']['constants'].append(dict(value=999, constant=dict(data=dict(U64=16))))
        range_site = descriptor['closed_tails']['regions'][0]['packed']['range_site']
        end = descriptor['plan']['blocks'][range_site]['action']['LibraryCall']['operands'][1]
        for block in wrong_width['plan']['blocks']:
            scalar = block['action'].get('Scalar')
            primitive = scalar.get('Primitive') if isinstance(scalar, dict) else None
            if primitive and primitive['output'] == end:
                primitive['operands'][1] = 999
        variants = [(wrong_width, assembly),
                    (descriptor, assembly.replace('#24\n', '#16\n')),
                    (descriptor, assembly.replace('#8\n', '#7\n')),
                    (descriptor, assembly.replace('_packed_loop_5_funded', '_unrelated_loop')),
                    (descriptor, 'unrelated nonempty disassembly')]
        for image, text in variants:
            with self.subTest(text=text[:70]), self.assertRaises((AssertionError, KeyError)):
                wide_slot.geometry(image, text)

    def test_missing_baseline_harness_is_a_pinned_removable_overlay(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            harness = workspace / equivalence.HARNESS
            harness.parent.mkdir(parents=True)
            installed = equivalence.install_harness(workspace)
            self.assertTrue(installed)
            self.assertEqual(harness.read_bytes(), (equivalence.BASELINE / 'snapshot-harness.rs').read_bytes())
            # This is also the cleanup path after a terminated failing stage.
            equivalence.remove_overlay(workspace, installed)
            self.assertFalse(harness.exists())
            installed = equivalence.install_harness(workspace)
            harness.write_text('unexpected edits')
            with self.assertRaises(ValueError):
                equivalence.remove_overlay(workspace, installed)
            self.assertTrue(harness.exists())

    def test_snapshot_receipt_must_prove_the_exact_command_controller_and_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = dict(commit='a' * 40, tree='b' * 40, status='')
            target = str(root / 'cargo-target')
            authorities = {'driver': Path(equivalence.__file__), 'study': equivalence.CODE / 'study.py',
                           'process': equivalence.ROOT / 'experiments/janet/knucleotide-bytes-v1/process.py',
                           'supervisor': equivalence.ROOT / 'tools/qualification/prolog_supervisor.py',
                           'baseline-driver': equivalence.BASELINE / 'executed-driver.py',
                           'harness': equivalence.BASELINE / 'snapshot-harness.rs',
                           'baseline-manifest': equivalence.BASELINE / 'archive-manifest.json'}
            inputs = []
            (root / 'execution-inputs').mkdir()
            for name, original in authorities.items():
                archived = root / 'execution-inputs' / name
                shutil.copyfile(original, archived)
                inputs.append(dict(name=name, path=str(original), archive=str(archived.relative_to(root)), sha256=process.sha(archived)))
            for name, value in [('plan', dict(study_id=equivalence.STUDY_ID, final_compiler_source=source['commit'])),
                                ('target-provenance', dict(source=source, target_dir=target))]:
                archived = root / 'execution-inputs' / name
                archived.write_text(json.dumps(value))
                inputs.append(dict(name=name, path=str(archived), archive=str(archived.relative_to(root)), sha256=process.sha(archived)))
            shutil.copyfile(equivalence.__file__, root / 'executed-driver.py')
            shutil.copyfile(equivalence.BASELINE / 'snapshot-harness.rs', root / 'snapshot-harness.rs')
            shutil.copytree(equivalence.BASELINE / 'snapshots', root / 'snapshots')
            report = dict(schema='mech.representative-snapshot-run.v1', status='passed', study_id=equivalence.STUDY_ID,
                          source=source, source_after=source, source_during=source, harness_overlay=False, overlay_removed=False,
                          subject='F', workspace='/exact/source', primary_timing_samples=0, performance_qualified=False,
                          target_dir=target, execution_inputs=inputs, python=sys.executable,
                          python_sha256=process.sha(Path(sys.executable)), command=equivalence.snapshot_command(),
                          snapshots=equivalence.snapshots(root / 'snapshots'))
            raw = dict(exit_status=0, cleanup_errors=[], signals=[], group_closed=True, reaped=True,
                       inherited_common_mutex=True, quantitative_benchmark=False, deadline_seconds=1800,
                       controller_sha256=process.sha(authorities['process']),
                       command=[sys.executable, '-c', equivalence.WRAPPER, report['workspace'], *equivalence.snapshot_command()])
            stdout = f'test {equivalence.TEST} ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1s\n'
            process_dir = root / 'representative-objects'
            process_dir.mkdir()

            def validate(current, receipt, output):
                (process_dir / 'process.json').write_text(json.dumps(receipt))
                (process_dir / 'stdout.bin').write_text(output)
                (process_dir / 'stderr.bin').write_text('')
                current['process_evidence'] = {name: equivalence.pin(process_dir / name) for name in ('process.json', 'stdout.bin', 'stderr.bin')}
                (root / 'result.json').write_text(json.dumps(current))
                with patch.object(equivalence, 'build_receipt_path', return_value=root / 'result.json'), \
                     patch.object(equivalence, 'source_state', return_value=source):
                    return equivalence.snapshot_receipt({})

            self.assertEqual(validate(copy.deepcopy(report), raw, stdout)[0], source)
            variants = [(report, dict(raw, command=['/bin/true']), stdout),
                        (report, dict(raw, controller_sha256='unrelated'), stdout),
                        (report, raw, ''), (report, raw, stdout.replace(equivalence.TEST, 'unrelated_test')),
                        (dict(report, command=['/bin/true']), raw, stdout),
                        (dict(report, source_during=dict(source, status='?? unreported.rs')), raw, stdout),
                        (dict(report, harness_overlay=True, source_during=dict(source, status='?? ' + equivalence.HARNESS)), raw, stdout),
                        (dict(report, execution_inputs=inputs[:-1]), raw, stdout)]
            for current, receipt, output in variants:
                with self.subTest(command=receipt['command'][:2], output=output[:30]), self.assertRaises((ValueError, KeyError)):
                    validate(copy.deepcopy(current), receipt, output)
            (root / inputs[0]['archive']).write_text('unrelated controller')
            with self.assertRaises(ValueError):
                validate(copy.deepcopy(report), raw, stdout)


if __name__ == '__main__':
    unittest.main()
