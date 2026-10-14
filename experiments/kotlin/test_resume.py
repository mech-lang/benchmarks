"""Small synthetic receipt/artifact fixtures; no JVM or benchmark execution."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[2]/'tools/qualification/kotlin_resume.py'
spec = importlib.util.spec_from_file_location('kotlin_resume', MODULE)
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


class QualificationFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root/'migration').mkdir()
        (self.root/'migration/reorganization-paths.tsv').write_text('original_path\tcurrent_path\n')
        self.overrides = dict(schema='kotlin-retired-orchestration-substitutions-v1', substitutions=[])

    def tearDown(self):
        self.temp.cleanup()

    def evidence(self):
        return resume.Evidence(self.root, self.overrides)

    def test_archive_relocation_preserves_bytes(self):
        (self.root/'archived.json').write_text('{"compiler_commands":3}')
        (self.root/'migration/reorganization-paths.tsv').write_text(
            'original_path\tcurrent_path\nbenchmarks/clbg/example.json\tarchived.json\n')
        e = self.evidence()
        logical = resume.OLD/'benchmarks/clbg/example.json'
        self.assertEqual(e.read(logical, resume.sha(self.root/'archived.json')), {'compiler_commands': 3})
        self.assertEqual(e.path(logical), self.root/'archived.json')

    def test_mapping_cannot_escape_archive(self):
        (self.root/'migration/reorganization-paths.tsv').write_text(
            'original_path\tcurrent_path\nbenchmarks/clbg/example.json\t../escape.json\n')
        with self.assertRaisesRegex(AssertionError, 'Migration escape'):
            self.evidence().path(resume.OLD/'benchmarks/clbg/example.json')

    def test_changed_source_rejected(self):
        source = self.root/'Main.kt'; source.write_text('fun main() {}')
        e = self.evidence(); expected = resume.sha(source)
        e.bind(source, expected)
        source.write_text('fun main() { println(1) }')
        with self.assertRaisesRegex(AssertionError, 'Changed pinned bytes'):
            e.bind(source, expected)

    def test_runtime_cannot_receive_editorial_waiver(self):
        self.overrides['substitutions'] = [dict(current_path='runtime.py', historical_sha256='0'*64)]
        with self.assertRaisesRegex(AssertionError, 'Unexpected editorial substitution'):
            self.evidence()

    def test_retained_command_failure_rejected(self):
        detail = dict(exit_status=0, final_exit_status=0, inherited_common_mutex=True,
                      preparation_only=True, never_chart_eligible=True, pid=42, identity={'pid': 42})
        resume.successful(detail)
        for changes in [dict(exit_status=1), dict(final_exit_status=None), dict(inherited_common_mutex=False),
                        dict(stop_signals=[15]), dict(identity=None), dict(timeout=True)]:
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                resume.successful(dict(detail, **changes))

    def classes(self):
        folder = self.root/'classes'
        for owner in ['clbg/Support.class', 'clbg/nbody/MainKt.class']:
            p = folder/owner; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'\xca\xfe\xba\xbe\x00\x00\x00\x3d'+b'fixture')
        return folder

    def test_exact_retained_class_set(self):
        folder = self.classes()
        pins = {str(p): resume.sha(p) for p in folder.rglob('*.class')}
        _, owners = resume.class_artifacts(folder, 'nbody', pins)
        self.assertEqual(owners, ['clbg.Support', 'clbg.nbody.MainKt'])
        (folder/'clbg/nbody/Extra.class').write_bytes(b'\xca\xfe\xba\xbe\x00\x00\x00\x3d'+b'fixture')
        with self.assertRaisesRegex(AssertionError, 'Unpinned retained class'):
            resume.class_artifacts(folder, 'nbody', pins)

    def test_missing_and_wrong_target_classes_rejected(self):
        folder = self.classes()
        pins = {str(p): resume.sha(p) for p in folder.rglob('*.class')}
        path = folder/'clbg/nbody/MainKt.class'
        path.write_bytes(b'\xca\xfe\xba\xbe\x00\x00\x00\x3c')
        with self.assertRaisesRegex(AssertionError, 'Wrong class target'):
            resume.class_artifacts(folder, 'nbody', pins)
        path.unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing application/helper owner'):
            resume.class_artifacts(folder, 'nbody', pins)

    def test_retained_form_prefix_and_source_flags(self):
        compiler = '/compiler/kotlinc'
        benchmarks = ['binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
                      'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm']
        rows = []
        for benchmark in benchmarks:
            for variant in ['compact', 'optimized']:
                identifier = 'kotlin-'+benchmark+'-'+variant
                main, helper = '/source/'+identifier+'/Main.kt', '/source/'+identifier+'/Support.kt'
                rows.append(dict(id=identifier, benchmark=benchmark,
                    authored_inputs=[dict(path=main, role='application', counted=True),
                                     dict(path=helper, role='application-helper', counted=True)],
                    compile_command_proposed=[compiler, helper, main, '-jvm-target', '17', '-no-reflect', '-d', str(Path(main).parent/'classes')]))
        resume.validate_inventory({'forms': rows}, compiler)
        self.assertEqual(len([r for r in rows if r['id'] not in resume.COMPILED]), 17)
        self.assertEqual(len([r for r in rows if r['id'] not in resume.DECODED]), 18)
        rows[2]['compile_command_proposed'][4] = '21'
        with self.assertRaisesRegex(AssertionError, 'Compilation flags'):
            resume.validate_inventory({'forms': rows}, compiler)


if __name__ == '__main__':
    unittest.main()
