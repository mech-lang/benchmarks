"""Reproduction records must describe the measured source and actual cohort."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import build_reproducibility as audit

class Reproduction(unittest.TestCase):
    def fixture(self,report):
        return dict(languages=[dict(key='rust')],benchmarks=[dict(key='nbody',workload='N = 50,000,000 steps')],
            programs={'nbody:test':dict(key='nbody:test',id='test',language='rust',benchmark='nbody',files=['a'*64],
                samples=[1,2,3],seconds=2,report=report,execution_mode='aot')})
    def test_uses_actual_local_version_not_upstream_notes(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            report=dict(toolchains={'rust':{'version':'rustc 1.96.0'}},hardware={'cpu':'Apple M3'},os='macOS 26.2',
                protocol={'timed_region':'Fresh process through exit','environment':{'RAYON_NUM_THREADS':'8'}},
                programs=[dict(id='test',samples_seconds=[1,2,3],command=['./app','{n}'],compile_command=['rustc','-O','app.rs'],
                    upstream_notes='rustc 1.84.1 on Linux')])
            Path(temp,'report.json').write_text(json.dumps(report));data=self.fixture('report.json');before=copy.deepcopy(data)
            r=audit.build(data)['programs']['nbody:test']
            self.assertEqual(r['version_label'],'rustc 1.96.0');self.assertNotIn('1.84',json.dumps(r))
            self.assertEqual(r['command'],['./app','{n}']);self.assertEqual(r['environment']['RAYON_NUM_THREADS'],'8')
            self.assertEqual(r['status'],'recorded-recipe');self.assertFalse(r['replay_verified']);self.assertEqual(data,before)
    def test_wrong_sample_array_cannot_supply_command_or_build(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            Path(temp,'report.json').write_text(json.dumps({'programs':[dict(id='test',samples_seconds=[9,9,9],command=['wrong'],compile_command=['wrong'])]}))
            r=audit.build(self.fixture('report.json'))['programs']['nbody:test']
            self.assertIsNone(r['command']);self.assertEqual(r['build_commands'],[]);self.assertEqual(r['status'],'gaps')
    def test_every_retained_profile_has_source_bound_recipe_or_explicit_gaps(self):
        data=json.loads((audit.ROOT/'data/benchmarks.json').read_text());catalog={**data['program_inventory'],**data['programs']}
        index=json.loads((audit.ROOT/'data/reproducibility.json').read_text())
        self.assertEqual(set(index['programs']),set(catalog))
        for key,r in index['programs'].items():
            self.assertEqual(r['source_sha256'],catalog[key]['files']);self.assertFalse(r['replay_verified'])
            self.assertEqual(r['status']=='gaps',bool(r['missing']))
            for e in r['evidence']:self.assertTrue((audit.ROOT/e['path']).is_file())
        lean=index['programs']['nbody:lean4-nbody-native-v1'];self.assertTrue(lean['versions'])
        ts=index['programs']['nbody:typescript-nbody-v1'];self.assertIn('24.19.0',ts['version_label'])

    def test_chart_projection_keeps_full_recipes_in_lazy_sidecar(self):
        browser=json.loads((audit.ROOT/'site/public/data.json').read_text())
        full=json.loads((audit.ROOT/'site/public/reproduction.json').read_text())
        self.assertEqual(set(browser['reproducibility']),set(full['programs']))
        for key,summary in browser['reproducibility'].items():
            self.assertNotIn('build_commands',summary);self.assertNotIn('dependencies',summary)
            self.assertEqual(summary['version_label'],full['programs'][key]['version_label'])

if __name__=='__main__':unittest.main()
