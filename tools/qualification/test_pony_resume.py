"""Adversarial metadata fixtures for Pony recovery; no native process is started."""
import ast
import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pony_resume_under_test', HERE / 'pony_resume.py')
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)
ROOT = HERE.parents[1]


def pure_functions(relative, names, namespace):
    """Load the saved pure qualification functions, without importing the harness."""
    tree = ast.parse((ROOT / relative).read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError('Missing saved qualification function')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), relative, 'exec'), namespace)
    return types.SimpleNamespace(**{name: namespace[name] for name in names})


class ArchivedEvidence:
    def __init__(self):
        with (ROOT / 'migration/reorganization-paths.tsv').open(newline='') as stream:
            self.mapping = {r['original_path']: r['current_path'] for r in csv.DictReader(stream, delimiter='\t')}
        self.cache = {}
        self.overrides = {}

    def path(self, logical):
        path = Path(logical)
        if path.is_relative_to(resume.OLD_ROOT):
            return ROOT / self.mapping[str(path.relative_to(resume.OLD_ROOT))]
        return path

    def read(self, logical, expected=None):
        key = str(logical)
        if key in self.overrides:
            return copy.deepcopy(self.overrides[key])
        if key not in self.cache:
            self.cache[key] = json.loads(self.path(logical).read_text())
        return copy.deepcopy(self.cache[key])

    def bind(self, logical, expected):
        return self.path(logical)

    def absorb(self, values):
        pass


class RetainedSampleMutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = ArchivedEvidence()
        cls.terminal = cls.evidence.read(resume.RETAINED_STUDY / 'terminal.json')
        guard_rel = 'archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/remaining_owner.py'
        cls.guard = pure_functions(guard_rel, ['qualification_checks', 'benchmark_failure'], {})
        prepare_rel = 'archive/comparisons/r-apl-uiua-comparison/20261011/prepare.py'
        fingerprint = pure_functions(prepare_rel, ['support_pins', 'execution_fingerprint'],
                                     dict(json=json, Path=Path, compact=types.SimpleNamespace(ROOT=resume.HOST)))
        cls.harness = types.SimpleNamespace(execution_fingerprint=fingerprint.execution_fingerprint, group_members=lambda pgid: [])

    def setUp(self):
        self.evidence.overrides = {}
        self.before = self.evidence.read(resume.RETAINED_STUDY / 'report.json')
        self.end = copy.deepcopy(self.terminal)
        self.no_process = patch.object(resume.subprocess, 'run', return_value=types.SimpleNamespace(stdout='', returncode=0))
        self.no_process.start()
        self.addCleanup(self.no_process.stop)

    def validate(self):
        self.evidence.overrides[str(resume.RETAINED_STUDY / 'report.json')] = self.before
        return resume.validate_retained(self.evidence, self.end, self.guard, self.harness)

    def test_exact_archived_54_have_36_unrepeated_slots(self):
        _, _, schedule, before = self.validate()
        self.assertEqual(len(before['attempts']), 54)
        self.assertEqual(len(schedule[54:]), 36)
        self.assertEqual(schedule[54][:2], ('knucleotide', 1))

    def test_altered_sample_duration_is_rejected(self):
        self.before['attempts'][40]['seconds'] += 0.01
        with self.assertRaisesRegex(AssertionError, 'Raw and supervised'):
            self.validate()

    def test_missing_supervisor_receipt_is_rejected(self):
        name = self.before['attempts'][40]['supervisor_result_path']
        self.evidence.overrides[name] = {}
        with self.assertRaisesRegex(AssertionError, 'Raw and supervised'):
            self.validate()

    def test_reordered_saved_slot_is_rejected(self):
        self.before['attempts'][40], self.before['attempts'][41] = self.before['attempts'][41], self.before['attempts'][40]
        with self.assertRaisesRegex(AssertionError, 'schedule'):
            self.validate()

    def test_mutated_retained_prefix_is_rejected(self):
        self.before['attempts'][0]['seconds'] += 1
        with self.assertRaisesRegex(AssertionError, 'First 22'):
            self.validate()

    def test_interrupted_inflight_sample_is_not_reused(self):
        self.before['active'] = {'attempt': 55, 'sampler_pid': 1}
        with self.assertRaisesRegex(AssertionError, 'relocation stop'):
            self.validate()

    def test_other_integrity_failure_cannot_be_relocated(self):
        self.end['integrity_errors'][0]['error'] = 'Pinned input changed'
        with self.assertRaisesRegex(AssertionError, 'Non-relocation'):
            self.validate()

    def test_wrong_saved_aggregate_is_rejected(self):
        row = next(row for row in self.before['programs'].values() if row['samples_seconds'])
        row['samples_seconds'][0] += 1
        with self.assertRaisesRegex(AssertionError, 'aggregate'):
            self.validate()

    def test_changed_saved_loc_is_rejected(self):
        next(iter(self.before['programs'].values()))['loc'] += 1
        with self.assertRaisesRegex(AssertionError, 'source evidence'):
            self.validate()

    def test_changed_execution_command_is_rejected(self):
        next(iter(self.before['programs'].values()))['command'].append('--different-workers')
        with self.assertRaisesRegex(AssertionError, 'Saved program changed'):
            self.validate()

    def test_claimed_complete_output_cannot_override_wrong_hash(self):
        attempt = self.before['attempts'][40]
        attempt['stdout_sha256'] = '0' * 64
        raw = self.evidence.read(attempt['result_path'])
        raw['stdout_sha256'] = '0' * 64
        self.evidence.overrides[attempt['result_path']] = raw
        self.evidence.overrides[attempt['supervisor_result_path']] = copy.deepcopy(attempt)
        with self.assertRaisesRegex(AssertionError, 'frozen qualification'):
            self.validate()

    def test_supervisor_claim_cannot_waive_an_unsafe_gate(self):
        attempt = self.before['attempts'][40]
        attempt['pins_unchanged_at_end'] = False
        # Mutate both persistence layers; independently recomputed qualification
        # must still reject the internally consistent forged success claim.
        raw = self.evidence.read(attempt['result_path'])
        raw['pins_unchanged_at_end'] = False
        self.evidence.overrides[attempt['result_path']] = raw
        self.evidence.overrides[attempt['supervisor_result_path']] = copy.deepcopy(attempt)
        with self.assertRaisesRegex(AssertionError, 'frozen qualification'):
            self.validate()

    def test_real_source_failure_requires_literal_safe_gates(self):
        attempt = copy.deepcopy(self.before['attempts'][40])
        attempt.update(error='wrong output', error_type='OutputValidationError')
        self.assertTrue(resume.isolated_failure(self.guard, attempt))
        for name in ('pins_unchanged', 'valid_environment', 'no_wrapper_integrity_error', 'exact_command_and_group'):
            for unsafe in (False, None, 1):
                with self.subTest(gate=name, value=unsafe):
                    changed = copy.deepcopy(attempt)
                    changed['qualification_checks'][name] = unsafe
                    self.assertFalse(resume.isolated_failure(self.guard, changed))


class MigrationPinMutations(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'migration').mkdir()
        self.table = self.root / 'migration/reorganization-paths.tsv'
        self.table.write_text('original_path\tcurrent_path\tgit_blob\tmode\n'
                              'benchmarks/clbg/example.txt\tarchive/example.txt\tunused\t100644\n')
        (self.root / 'archive').mkdir()
        self.source = self.root / 'archive/example.txt'
        self.source.write_text('exact evidence\n')
        self.config = self.root / 'replacements.json'
        artifacts = []
        for name, digest in resume.CONTROL_PINS.items():
            if name.startswith('full90-'):
                path = str(resume.ARCHIVE_REL / 'revisions' / name)
                artifacts.append(dict(revision_path=name, historical_sha256=digest, archive_path=path,
                                      archive_sha256='0' * 64, executed=False, source_or_runtime_evidence=False))
        self.configuration = dict(schema='pony-orchestration-supersessions-v1', artifacts=artifacts)
        self.config.write_text(json.dumps(self.configuration))

    def resolver(self):
        return resume.Resolver(self.root, self.root / 'retained', self.config)

    def test_moved_evidence_keeps_exact_original_digest(self):
        logical = str(resume.OLD_ROOT / 'benchmarks/clbg/example.txt')
        resolver = self.resolver()
        self.assertEqual(resolver.bind(logical, resume.sha(self.source)), self.source.resolve())
        self.assertFalse(resolver.relocations[logical]['superseded_orchestration'])

    def test_changed_evidence_cannot_be_accepted_as_relocation(self):
        expected = resume.sha(self.source)
        self.source.write_text('different evidence\n')
        with self.assertRaisesRegex(AssertionError, 'Pinned bytes changed'):
            self.resolver().bind(str(resume.OLD_ROOT / 'benchmarks/clbg/example.txt'), expected)

    def test_unknown_historical_path_has_no_fallback(self):
        with self.assertRaisesRegex(AssertionError, 'no migration entry'):
            self.resolver().resolve(resume.OLD_ROOT / 'benchmarks/clbg/unlisted.txt')

    def test_migration_cannot_escape_checkout(self):
        self.table.write_text('original_path\tcurrent_path\tgit_blob\tmode\n'
                             'benchmarks/clbg/example.txt\t../../escape.txt\tunused\t100644\n')
        with self.assertRaisesRegex(AssertionError, 'escapes'):
            self.resolver().resolve(resume.OLD_ROOT / 'benchmarks/clbg/example.txt')

    def test_runtime_or_source_cannot_be_declared_superseded(self):
        self.configuration['artifacts'][0]['revision_path'] = 'sources/nbody/main.pony'
        self.config.write_text(json.dumps(self.configuration))
        with self.assertRaisesRegex(AssertionError, 'Only named historical orchestration'):
            self.resolver()

    def test_old_host_path_is_never_relocated(self):
        path = resume.HOST_COHORT / '.build/program'
        self.assertEqual(self.resolver().resolve(path), path)

    def test_duplicate_migration_rows_are_rejected(self):
        self.table.write_text(self.table.read_text() + self.table.read_text().splitlines()[1] + '\n')
        with self.assertRaisesRegex(AssertionError, 'Duplicate migration'):
            self.resolver()


class ManifestEditorialParity(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / resume.ARCHIVE_REL / 'full-studies/pony-retained20-full-v1/manifest.json'
        self.raw = self.path.read_bytes()
        self.document = json.loads(self.raw)
        self.expected = resume.manifest_technical_digest(self.raw)

    def test_only_narrative_field_is_omitted_from_technical_digest(self):
        self.document['chart_policy'] = 'Different narrative text for a separate review.'
        changed = json.dumps(self.document).encode()
        self.assertEqual(resume.manifest_technical_digest(changed), self.expected)

    def test_source_runtime_workload_and_command_changes_are_detected(self):
        for mutate in (
            lambda d: d.update(timeout_seconds=1),
            lambda d: d.update(maximum_rss_mib=1),
            lambda d: d['profiles'][0].update(source_sha256='0' * 64),
            lambda d: d['profiles'][0].update(binary_sha256='0' * 64),
            lambda d: d['profiles'][0]['command'].append('--different-runtime'),
            lambda d: d.update(samples=1),
        ):
            changed = copy.deepcopy(self.document)
            mutate(changed)
            self.assertNotEqual(resume.manifest_technical_digest(json.dumps(changed).encode()), self.expected)

    def test_actual_manifest_requires_exact_historical_and_archive_hashes(self):
        resolver = resume.Resolver(ROOT, ROOT / resume.ARCHIVE_REL / 'full-studies/pony-retained20-resumed-v1',
                                   ROOT / 'experiments/pony/migration-resume-v1/orchestration-supersessions.json')
        self.assertEqual(resolver.bind(resume.OLD_STUDY / 'manifest.json', resume.SUITE_SHA), self.path.resolve())
        with self.assertRaisesRegex(AssertionError, 'historical pin changed'):
            resolver.bind(resume.OLD_STUDY / 'manifest.json', '0' * 64)

    def test_narrative_field_cannot_be_removed_or_retyped(self):
        self.document.pop('chart_policy')
        with self.assertRaisesRegex(AssertionError, 'narrative text'):
            resume.manifest_technical_digest(json.dumps(self.document).encode())


if __name__ == '__main__':
    unittest.main(verbosity=2)
