import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from game_comparisons import export_game_comparisons


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


if __name__ == '__main__':
    unittest.main()
