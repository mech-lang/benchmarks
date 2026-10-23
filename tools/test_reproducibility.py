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
    def test_direct_rustc_capture_requires_the_matching_timed_profile(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            report=dict(rustc={'version':'rustc 1.96.0-nightly'},programs=[dict(id='test',samples_seconds=[1,2,3])])
            Path(temp,'report.json').write_text(json.dumps(report));data=self.fixture('report.json')
            r=audit.build(data)['programs']['nbody:test'];self.assertEqual(r['version_label'],'rustc 1.96.0-nightly')
            report['programs'][0]['samples_seconds']=[9,9,9]
            Path(temp,'report.json').write_text(json.dumps(report))
            self.assertEqual(audit.build(data)['programs']['nbody:test']['versions'],[])
    def test_native_compiler_is_not_inferred_from_library_or_source_names(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            report=dict(toolchains={'c':'gcc-16 16.2.0','llvm':['Homebrew clang version 22.1.8','Target: arm64-apple-darwin25.2.0']},
                programs=[dict(id='test',samples_seconds=[1,2,3],command=['./app'],
                    compile_command=['/opt/llvm/bin/clang-22','-I/opt/gcc/include','nbody-gcc-3.c','-o','app'])])
            Path(temp,'report.json').write_text(json.dumps(report));data=self.fixture('report.json');data['programs']['nbody:test']['language']='c'
            r=audit.build(data)['programs']['nbody:test'];self.assertEqual(r['version_label'],'Homebrew clang version 22.1.8')
            self.assertNotIn('gcc-16',json.dumps(r['versions']))
    def test_native_gcc_and_gpp_historical_aliases_are_supported(self):
        self.assertEqual(audit.native_compiler_keys('c',[dict(command=['gcc-16','-include','clang-sdk-compat.h'])]),['gcc','c'])
        self.assertEqual(audit.native_compiler_keys('cpp',[dict(command=['g++-16','clang-port.cpp'])]),['gpp','cpp','gcc'])
    def test_cpp_prefers_its_recorded_frontend_to_an_unrelated_gcc_entry(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            report=dict(toolchains={'gpp':'g++-15 15.2.0','gcc':'gcc-16 16.2.0'},
                programs=[dict(id='test',samples_seconds=[1,2,3],command=['./app'],compile_command=['g++-15','app.cpp','-o','app'])])
            Path(temp,'report.json').write_text(json.dumps(report));data=self.fixture('report.json');data['programs']['nbody:test']['language']='cpp'
            r=audit.build(data)['programs']['nbody:test'];self.assertEqual(r['version_label'],'g++-15 15.2.0')
            self.assertEqual(len(r['versions']),1)
    def test_mixed_report_does_not_assign_mech_compiler_to_competitors(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            snapshot=dict(base_commit='b'*40,path='mech-compiler.tar.gz',sha256='c'*64)
            report=dict(compiler_snapshot=snapshot,programs=[dict(id='test',samples_seconds=[1,2,3])])
            Path(temp,'report.json').write_text(json.dumps(report));data=self.fixture('report.json')
            r=audit.build(data)['programs']['nbody:test']
            self.assertEqual(r['compiler_identity'],{});self.assertEqual(r['versions'],[])
            self.assertEqual(r['report_compiler_context']['metadata']['compiler_snapshot'],snapshot)
            data['programs']['nbody:test']['language']='mech'
            r=audit.build(data)['programs']['nbody:test']
            self.assertEqual(r['compiler_identity']['compiler_snapshot'],snapshot)
            self.assertNotIn('report_compiler_context',r)
    def test_earlier_version_requires_both_executable_and_source_identity(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)),patch.object(audit,'BINARY_BUILD_REPORTS',('earlier.json',)):
            Path(temp,'report.json').write_text(json.dumps({'programs':[dict(id='test',samples_seconds=[1,2,3])]}))
            prior=dict(id='test',language='rust',binary_sha256='b'*64,source={'sha256':{'app.rs':'a'*64}},compile_command=['rustc','-O','app.rs'])
            Path(temp,'earlier.json').write_text(json.dumps(dict(toolchain_versions={'rust':'rustc 1.96.0'},programs=[prior])))
            data=self.fixture('report.json');data['programs']['nbody:test']['binary_sha256']='b'*64
            r=audit.build(data)['programs']['nbody:test']
            self.assertEqual(r['version_label'],'rustc 1.96.0')
            self.assertIn('binary-matched build provenance',r['versions'][0]['scope'])
            self.assertEqual(r['build_commands'][0]['command'],prior['compile_command'])
            self.assertIn('not recaptured',r['missing'][0])
            for field,value in [('binary_sha256','c'*64),('files',['c'*64])]:
                wrong=copy.deepcopy(data);wrong['programs']['nbody:test'][field]=value
                r=audit.build(wrong)['programs']['nbody:test']
                self.assertEqual(r['versions'],[]);self.assertEqual(r['build_commands'],[])
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

class MechRuntimeIdentity(unittest.TestCase):
    def test_emitter_and_linked_runtime_commits_remain_distinct(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(audit,'ROOT',Path(temp)):
            key='nbody:test';emitter='a'*40;runtime='b'*40
            version='Mech 0.3.6 development (emitter '+emitter[:9]+', runtime '+runtime[:9]+')'
            row=dict(key=key,id='test',source_sha256='c'*64,samples_seconds=[1,2,3],runtime_commit=runtime,runtime_source=dict(path='runtime.rs',sha256='d'*64),runtime_version=version)
            report=dict(compiler_source_commit=emitter,programs={key:row},hardware='Apple M3',os='macOS')
            Path(temp,'report.json').write_text(json.dumps(report))
            data=dict(languages=[dict(key='mech')],benchmarks=[dict(key='nbody',workload='N = 1')],programs={key:dict(key=key,id='test',language='mech',benchmark='nbody',files=['c'*64],samples=[1,2,3],seconds=2,report='report.json',execution_mode='aot',measured_backend=dict(evidence=dict(runtime_receipt=dict(report='report.json',field='/programs/'+key+'/runtime_version',value=version))))})
            result=audit.build(data)['programs'][key]
            self.assertEqual(result['compiler_identity']['compiler_source_commit'],emitter)
            self.assertEqual(result['compiler_identity']['runtime_source_commit'],runtime)
            self.assertEqual(result['compiler_identity']['runtime_source'],row['runtime_source'])
            self.assertEqual(result['version_label'],version)

if __name__=='__main__':unittest.main()
