import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from game_comparisons import export_game_comparisons, jit_admission


class GameComparisonsTest(unittest.TestCase):
    def fixture(self):
        files, programs, groups = {}, {}, []
        for language, seconds, suffix in [('mech', .5, 'mec'), ('rust', 1, 'rs')]:
            code = 'measured ' + language + ' source\n'
            digest = hashlib.sha256(code.encode()).hexdigest()
            files[digest] = {'name': 'program.' + suffix, 'code': code}
            key = 'task:' + language
            programs[key] = {'key': key, 'seconds': seconds, 'samples': [seconds] * 3,
                             'files': [digest], 'execution_mode': 'aot', 'report': 'report.json'}
            groups.append({'language': language, 'fast': key})
        return {'protocol': {'hardware': 'Test machine', 'timing': 'Whole process'},
                'benchmarks': [{'key': 'task', 'title': 'Task', 'workload': 'N=10', 'groups': groups}],
                'programs': programs, 'files': files}

    def test_projection_preserves_observations_and_exact_program_bytes(self):
        catalog = self.fixture()
        before = copy.deepcopy(catalog)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            bundle = export_game_comparisons(catalog, output)
            case = bundle['cases'][0]
            for language in ('mech', 'rust'):
                original = catalog['programs']['task:' + language]
                self.assertEqual(case[language]['seconds'], original['seconds'])
                self.assertEqual(case[language]['samples'], original['samples'])
                content = (output/case[language]['source_url'].removeprefix('/benchmarks/')).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), original['files'][0])
                self.assertIn('detail.program=task%3A' + language, case[language]['implementation_url'])
                self.assertTrue(case[language]['implementation_url'].startswith('/benchmarks/#v=1&inspect=1&'))
            self.assertEqual(json.loads((output/'game-comparisons.json').read_text()), bundle)
        self.assertEqual(catalog, before)

    def test_mismatched_source_unqualified_timing_and_jit_are_rejected(self):
        for mutation in ('source', 'eligibility', 'mode', 'recipe'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                catalog = self.fixture(); program = catalog['programs']['task:mech']; recipes = None
                if mutation == 'source': catalog['files'][program['files'][0]]['code'] += 'changed'
                if mutation == 'eligibility': program['eligible_for_chart'] = False
                if mutation == 'mode': program['execution_mode'] = 'jit'
                if mutation == 'recipe': recipes = {'programs': {'task:mech': {'source_sha256': ['wrong']}}}
                with self.assertRaises(ValueError): export_game_comparisons(catalog, directory, recipes)

    def test_jit_selects_fastest_eligible_external_peer_across_inventory(self):
        catalog = self.fixture()
        catalog['languages'] = [{'key': language, 'label': language + ' JIT'} for language in ('csharp', 'fsharp', 'javascript')]
        catalog['program_inventory'] = {}
        def add(language, seconds, name, mode='jit', inventory=False, **extra):
            code = name + '\n'; digest = hashlib.sha256(code.encode()).hexdigest(); key = 'task:' + name
            catalog['files'][digest] = {'name': name + '.txt', 'code': code}
            program = {'key': key, 'benchmark': 'task', 'language': language, 'seconds': seconds,
                       'samples': [seconds] * 3, 'files': [digest], 'execution_mode': mode, **extra}
            catalog['program_inventory' if inventory else 'programs'][key] = program
            return key
        mech = add('mech-jit', .8, 'mech-jit')
        catalog['benchmarks'][0]['groups'].append({'language': 'mech-jit', 'fast': mech})
        add('csharp', 1, 'csharp')
        add('javascript', 2, 'javascript')
        fastest = add('fsharp', .6, 'fsharp', inventory=True)
        add('csharp', .1, 'aot', mode='aot')
        add('csharp', .2, 'excluded', eligible_for_chart=False)
        add('csharp', .3, 'alias', timing_alias_of='other')
        add('rust', .01, 'rust-jit', mode='jit')
        with tempfile.TemporaryDirectory() as directory:
            result = export_game_comparisons(catalog, directory)
            row = result['jit_cases'][0]
            self.assertEqual(row['reference']['program'], fastest)
            self.assertEqual(row['reference']['seconds'], .6)
            self.assertEqual(row['reference']['execution_mode'], 'jit')
            self.assertEqual(row['eligible_external_jit_programs'], 3)
            # JIT reference selection is independent of the presence of Rust.
            catalog['benchmarks'][0]['groups'] = [{'language': 'mech-jit', 'fast': mech}]
            independent = export_game_comparisons(catalog, directory)
            self.assertEqual(independent['cases'], [])
            self.assertEqual(independent['jit_cases'][0]['reference']['program'], fastest)

    def test_unknown_modes_can_use_recorded_jit_launches_but_disabled_jit_cannot(self):
        program={'key':'task:runtime','files':['source-hash'],'seconds':1,'samples':[1,1,1],'execution_mode':'unknown'}
        for executable, disabled in [('java',['-Xint']),('node',['--jitless']),('julia',['--compile=no']),('luajit',['-joff'])]:
            with self.subTest(executable=executable):
                program['language']={'node':'javascript'}.get(executable,executable)
                recipe={'source_sha256':program['files'],'command':['/runtime/'+executable,'source-file']}
                admitted=jit_admission(program,{program['key']:recipe})
                self.assertEqual(admitted['basis'],'recorded-jit-enabled-runtime-launch')
                self.assertEqual(admitted['recorded_execution_mode'],'unknown')
                self.assertFalse(admitted['machine_code_trace_recorded'])
                recipe['command']=['/runtime/'+executable,*disabled,'source-file']
                self.assertIsNone(jit_admission(program,{program['key']:recipe}))
        program['language']='javascript'
        recipe={'source_sha256':program['files'],'command':['/runtime/node','source.js'],'environment':{'NODE_OPTIONS':'--jitless'}}
        self.assertIsNone(jit_admission(program,{program['key']:recipe}))
        program['language']='java'
        recipe={'source_sha256':['different'],'command':['/runtime/java','Main']}
        self.assertIsNone(jit_admission(program,{program['key']:recipe}))
        recipe={'source_sha256':program['files'],'command':['/runtime/java','Main']}
        self.assertIsNone(jit_admission(program|{'execution_mode':'aot'},{program['key']:recipe}))


if __name__ == '__main__':
    unittest.main()
