"""Pure temporary-catalog regressions; no real dataset, archive or native work."""
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1]/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog = load('catalog_publication_export', 'export_catalog.py')
verifier = load('catalog_publication_verify', 'verify_repository.py')


def fixture():
    files, roles = {}, {}
    for name, role, code in (('main.ex', 'application', 'IO.puts(1)\n'),
                             ('support.ex', 'application-helper', 'defmodule Support do\nend\n'),
                             ('runner.exs', 'application-launcher', 'Main.main()\n')):
        digest = hashlib.sha256(code.encode()).hexdigest()
        files[digest] = dict(name=name, path='authored/'+name, archive_path='retained/'+name,
                             sha256=digest, code=code)
        roles[digest] = dict(role=role, source_path='retained/'+name,
                             normalized_loc=1, physical_loc=len(code.splitlines()), formatted_loc=2)
    rows = {}
    for identity in ('legacy', 'complete', 'partial', 'control-failed'):
        key = 'bench:'+identity
        row = dict(key=key, id=identity, benchmark='bench', language='example',
                   loc=3, physical_loc=4, files=list(files), file_roles=copy.deepcopy(roles),
                   seconds=2, samples=[1, 2, 3], timing_sd=1, report='saved/report.json')
        if identity != 'legacy':
            row.update(formatted_loc=6, measurement_status='measured', full_workload_qualified=True,
                       matched_control_qualified=identity != 'control-failed',
                       eligible_for_chart=identity == 'complete', failed_attempt=None,
                       source_alias_note='Distinct receipt with the same retained source.',
                       evidence={'canonical_loc': {'path': 'saved/loc.json', 'sha256': 'a'*64},
                                 'compiled_work': {'path': 'saved/work.json', 'sha256': 'b'*64}})
            if identity == 'partial':
                row.update(seconds=None, timing_sd=None, samples=[1, 3], failed_attempt=9,
                           measurement_status='failed', full_workload_qualified=False)
            row['publication_record'] = copy.deepcopy(row)
        rows[key] = row
    return dict(languages=[dict(key='example', label='Example')],
                benchmarks=[dict(key='bench', title='Benchmark', workload='synthetic fixture',
                                 baseline_loc=1, baseline_seconds=1)],
                files=files, programs={key: row for key, row in rows.items() if row['id'] in ('legacy', 'complete')},
                program_inventory=rows, archive_paths={'saved/report.json': 'saved/report.json'})


class PublicationCatalog(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root/'data').mkdir()
        self.data = fixture()

    def export(self):
        (self.root/'data/benchmarks.json').write_text(json.dumps(self.data))
        with contextlib.redirect_stdout(io.StringIO()):
            catalog.export(self.root)

    def record(self, identity):
        return self.root/'programs/example/bench'/identity/'program.json'

    def verify(self):
        # These three legacy/archive-specific audits are outside this isolated
        # fixture. Exercise the actual generic manifests, sources, CSVs and totals.
        with patch.object(verifier, 'check_migration', return_value=[]), \
             patch.object(verifier, 'check_previous', return_value=0), \
             patch.object(verifier, 'check_v', return_value={}):
            return verifier.verify(self.root)

    def test_legacy_record_remains_exact_existing_schema(self):
        self.export()
        row = json.loads(self.record('legacy').read_text())
        self.assertEqual(set(row), {'key', 'language', 'benchmark', 'program', 'loc', 'loc_metric',
            'physical_loc', 'seconds', 'samples', 'standard_deviation', 'selected_for_chart',
            'original_timing_report', 'archive_timing_report', 'sources'})
        self.assertEqual(row['standard_deviation'], 1)
        self.assertEqual(row['sources'][2]['file'], 'runner.exs')
        self.assertEqual(row['sources'][2]['role'], 'application-launcher')
        self.assertEqual(self.verify()['status'], 'passed')

    def test_partial_cohort_preserves_null_statistics_and_samples(self):
        self.export()
        row = json.loads(self.record('partial').read_text())
        self.assertIsNone(row['seconds'])
        self.assertIsNone(row['standard_deviation'])
        self.assertEqual(row['samples'], [1, 3])
        self.assertFalse(row['selected_for_chart'])
        self.assertEqual(row['publication_record'], self.data['program_inventory']['bench:partial']['publication_record'])
        with (self.root/'results/current/programs.csv').open() as stream:
            partial = next(row for row in csv.DictReader(stream) if row['program'] == 'partial')
        self.assertEqual((partial['median_seconds'], partial['sample_sd_seconds'], partial['sample_count']), ('', '', '2'))
        with (self.root/'results/current/samples.csv').open() as stream:
            samples = [row for row in csv.DictReader(stream) if row['program'] == 'partial']
        self.assertEqual([row['seconds'] for row in samples], ['1', '3'])
        self.assertEqual(self.verify()['status'], 'passed')

    def test_failed_control_does_not_erase_successful_subject_observations(self):
        self.export()
        row = json.loads(self.record('control-failed').read_text())
        self.assertEqual((row['seconds'], row['samples'], row['standard_deviation']), (2, [1, 2, 3], 1))
        self.assertFalse(row['selected_for_chart'])
        self.assertFalse(row['publication_record']['eligible_for_chart'])
        self.assertFalse(row['publication_record']['matched_control_qualified'])
        self.assertEqual(self.verify()['status'], 'passed')

    def test_verifier_detects_lost_evidence_and_fabricated_partial_sd(self):
        self.export()
        original = json.loads(self.record('partial').read_text())
        for mutation in ('evidence', 'sd'):
            row = copy.deepcopy(original)
            if mutation == 'evidence':
                del row['publication_record']['evidence']['compiled_work']
            else:
                row['standard_deviation'] = 1.4142135623730951
            self.record('partial').write_text(json.dumps(row))
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'Exported program manifest changed'):
                self.verify()

    def test_malformed_publication_rejected_before_catalog_writes(self):
        for value in (None, [], {}):
            self.data['program_inventory']['bench:partial']['publication_record'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Invalid publication record'):
                self.export()
            self.assertFalse((self.root/'programs').exists())


if __name__ == '__main__':
    unittest.main()
