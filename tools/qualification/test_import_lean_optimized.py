"""Pure catalog admission checks; no compiler or benchmark execution."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import import_lean_optimized as admission


class Admission(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope = patch.object(admission, 'ROOT', self.root)
        self.scope.start()
        self.addCleanup(self.scope.stop)
        oldkey = 'nbody:lean4-nbody-native-v1'
        old = dict(key=oldkey, id='lean4-nbody-native-v1', benchmark='nbody', language='lean4',
            loc=20, seconds=5, samples=[4,5,6], timing_sd=1, files=['old'], x=2, y=5,
            measured_backend=dict(evidence=dict(command=['old'],source_sha256=['old'])),
            publication_record=dict(timing_sd=1))
        self.data = dict(programs={oldkey:copy.deepcopy(old)},program_inventory={oldkey:copy.deepcopy(old)},
            files={'old':dict(code='retained\n')},archive_paths={'old':'old'},repository=dict(url='https://example.test/repo'),
            languages=[dict(key='lean4'),dict(key='other',coverage_note='unchanged')],
            benchmarks=[dict(key='nbody',baseline_seconds=1,baseline_loc=10,
                groups=[dict(language='lean4',programs=[oldkey],fast=oldkey,small=oldkey),dict(language='other',programs=[])])],
            reference_summary=[dict(lang='lean4',fast={},small={}),dict(lang='other',fast=dict(x=1,y=1))],protocol=dict(lean4='old'))
        self.metadata = dict(languages=dict(lean4=dict(displayed_program_count=1,measurement_basis=[]),other=dict(note='unchanged')))
        profiles = []
        hashes = {}
        for variant, code, loc, samples in [('fast','def main := pure ()\n',11,[2,3,4]),('concise','def main := pure () -- shorter fixture\n',7,[6,7,8])]:
            folder = self.root / variant
            folder.mkdir()
            source = folder/'nbody.lean'; source.write_text(code)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            counts = dict(profiles=dict(nbody=dict(canonical_loc=loc,files=['nbody.lean'])),
                units={'nbody.lean':dict(sha256=digest,canonical_loc=loc,physical_loc=1,expansions=[])})
            full = dict(cases=[dict(benchmark='nbody',elapsed_seconds=value,command=['fixture',str(value)]) for value in samples])
            for name,value in [('counts',counts),('full',full),('build',{}),('work',{})]:
                file = folder/(name+'.json');file.write_text(json.dumps(value));hashes[str(file.relative_to(self.root))]=hashlib.sha256(file.read_bytes()).hexdigest()
            profiles.append(dict(benchmark='nbody',variant=variant,counts_report=f'{variant}/counts.json',
                full_report=f'{variant}/full.json',work_report=f'{variant}/work.json',build_report=f'{variant}/build.json',
                source_directory=str(folder),files=['nbody.lean'],normalized_loc=loc,physical_loc=1,
                samples=samples,median_seconds=samples[1],sample_sd_seconds=1,binary_sha256=variant))
        self.results = dict(status='FULL_SIZE_SAMPLES_AND_NORMALIZED_LOC_RECONCILED',timing_processes_serial=True,
            saved_stream_hashes_recomputed=True,source_counts_independently_replayed=True,global_optimality_claimed=False,
            benchmark_samples=6,profiles=profiles,cohorts=[dict(hashes=hashes)])
        self.path = self.root/'results.json'

    def run_transform(self):
        self.path.write_text(json.dumps(self.results))
        return admission.transform(copy.deepcopy(self.data),copy.deepcopy(self.metadata),self.path)

    def test_measured_endpoints_and_history(self):
        data,metadata,receipt = self.run_transform()
        group = data['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'],'nbody:lean4-nbody-optimized-v1')
        self.assertEqual(group['small'],'nbody:lean4-nbody-compact-v1')
        for section in ('programs','program_inventory','files','archive_paths'):
            for key,value in self.data[section].items():
                self.assertEqual(data[section][key],value)
        self.assertEqual(data['benchmarks'][0]['baseline_loc'],10)
        self.assertEqual(metadata['languages']['other'],self.metadata['languages']['other'])
        self.assertEqual(len(receipt['new_minimum_review']),1)
        self.assertFalse(receipt['baseline_changed'])

    def test_optimized_label_does_not_force_speed_winner(self):
        self.results['profiles'][0]['samples']=[8,9,10]
        self.results['profiles'][0]['median_seconds']=9
        f=self.root/'fast/full.json';r=json.loads(f.read_text())
        for row,value in zip(r['cases'],[8,9,10]):row['elapsed_seconds']=value
        f.write_text(json.dumps(r));self.results['cohorts'][0]['hashes']['fast/full.json']=hashlib.sha256(f.read_bytes()).hexdigest()
        data,_,_=self.run_transform()
        self.assertEqual(data['benchmarks'][0]['groups'][0]['fast'],'nbody:lean4-nbody-native-v1')

    def test_reject_changed_evidence(self):
        (self.root/'fast/work.json').write_text('{"changed":true}')
        with self.assertRaises(AssertionError):self.run_transform()

    def test_reject_mismatched_normalized_loc(self):
        self.results['profiles'][0]['normalized_loc']=1
        with self.assertRaises(AssertionError):self.run_transform()

    def test_reject_missing_sample(self):
        self.results['profiles'][0]['samples'].pop()
        with self.assertRaises(AssertionError):self.run_transform()

    def test_reject_reused_program_identity(self):
        self.data['program_inventory']['nbody:lean4-nbody-optimized-v1']={}
        with self.assertRaises(AssertionError):self.run_transform()


if __name__ == '__main__':
    unittest.main()
