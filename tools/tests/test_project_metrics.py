import argparse
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('project_metrics', Path(__file__).parents[1] / 'project_metrics.py')
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class ProjectMetrics(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.command('init', '-q')
        files = {
            'Cargo.toml': '[package]\nname="fixture"\nversion="0.1.0"\n[dependencies]\nalpha="1"\nrenamed={package="actual",version="2"}\nlocal={path="src/internal"}\n[workspace.dependencies]\nshared="3"\n[target.\'cfg(unix)\'.dev-dependencies]\nalpha="1"\n[package.metadata.dependencies]\nnot_a_dependency="99"\n',
            'Cargo.lock': 'version=3\n[[package]]\nname="alpha"\nversion="1"\nsource="registry+example"\n[[package]]\nname="alpha"\nversion="2"\nsource="registry+example"\n[[package]]\nname="local"\nversion="1"\n',
            'src/lib.rs': '// comment\n\npub fn value() -> u32 { 1 }\n',
            'src/internal/Cargo.toml': '[package]\nname="internal"\nversion="0.1.0"\n',
            'tests/value.rs': '#[test]\nfn value() {}\n',
            'tests/fixtures/value.mec': 'value := 1\n',
            'tests/fixtures/Cargo.toml': 'intentionally invalid fixture {{',
            'vendor/upstream.rs': 'third party\n',
            'target/generated.rs': 'build output\n',
            'dist/bundle.js': 'generated output\n',
        }
        for name, text in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.command('add', '.')
        self.command('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture')
        self.revision = self.command('rev-parse', 'HEAD').decode().strip()

    def command(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args], stderr=subprocess.PIPE)

    def snapshot(self):
        return metrics.inventory(self.source, self.revision)

    def test_git_objects_ignore_working_and_untracked_changes(self):
        original = self.snapshot()
        (self.source / 'src/lib.rs').write_text('changed\n' * 20)
        (self.source / 'src/untracked.rs').write_text('untracked\n')
        self.assertEqual(original, self.snapshot())

    def test_scope_and_line_definition_are_explicit(self):
        snapshot = self.snapshot()
        paths = {row['path'] for row in snapshot['files']}
        self.assertEqual(paths, {'src/lib.rs', 'tests/value.rs', 'tests/fixtures/value.mec'})
        rust = next(row for row in snapshot['files'] if row['path'] == 'src/lib.rs')
        self.assertEqual((rust['physical_lines'], rust['nonempty_lines']), (3, 2))
        self.assertEqual(snapshot['summary']['rust_test_files'], 1)
        self.assertEqual(snapshot['summary']['mech_test_files'], 1)
        self.assertNotIn('passed_tests', snapshot['summary'])

    def test_declarations_and_lock_resolutions_are_distinct(self):
        dependencies = self.snapshot()['dependencies']
        self.assertEqual(dependencies['declared_external_names'], ['actual', 'alpha', 'shared'])
        self.assertEqual(dependencies['package_count'], 2)
        self.assertEqual(dependencies['resolved_external_count'], 2)
        self.assertEqual(dependencies['multiple_version_names'], ['alpha'])

    def test_missing_lockfile_is_unavailable(self):
        self.command('rm', 'Cargo.lock')
        self.command('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'remove lock')
        self.assertIsNone(metrics.inventory(self.source, 'HEAD')['dependencies']['resolved_external_count'])

    def collect(self):
        output = self.root / 'results/project/fixture-001'
        metrics.collect(argparse.Namespace(mech=self.source, revision=self.revision, repository='example/fixture',
                                          track='main', label='Fixture', github=False, output=output))
        return output

    def test_offline_snapshot_exports_and_retains_downloads(self):
        self.collect()
        output = self.root / 'public'
        output.mkdir()
        rows = metrics.export_project(output, root=self.root)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['github'])
        self.assertNotIn('files', rows[0])
        self.assertTrue((output / 'project-evidence/fixture-001/snapshot.json').is_file())

    def test_changed_evidence_preserves_previous_export(self):
        directory = self.collect()
        output = self.root / 'public'
        output.mkdir()
        metrics.export_project(output, root=self.root)
        before = (output / 'project.json').read_bytes()
        (directory / 'snapshot.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            metrics.export_project(output, root=self.root)
        self.assertEqual((output / 'project.json').read_bytes(), before)
        self.assertTrue((output / 'project-evidence/fixture-001/snapshot.json').is_file())

    def test_recomputed_pin_does_not_hide_inconsistent_summary(self):
        directory = self.collect()
        path = directory / 'snapshot.json'
        snapshot = json.loads(path.read_bytes())
        snapshot['summary']['physical_lines'] += 1
        path.write_bytes(metrics.encoded(snapshot))
        pins = json.loads((directory / 'evidence.json').read_bytes())
        pins['files']['snapshot.json'] = metrics.digest(path.read_bytes())
        (directory / 'evidence.json').write_bytes(metrics.encoded(pins))
        with self.assertRaisesRegex(ValueError, 'summary'):
            metrics.export_project(self.root / 'public', root=self.root)

    def test_snapshot_ids_cannot_escape_public_directory(self):
        directory = self.collect()
        path = directory / 'snapshot.json'
        snapshot = json.loads(path.read_bytes())
        snapshot['id'] = '../outside'
        path.write_bytes(metrics.encoded(snapshot))
        pins = json.loads((directory / 'evidence.json').read_bytes())
        pins['files']['snapshot.json'] = metrics.digest(path.read_bytes())
        (directory / 'evidence.json').write_bytes(metrics.encoded(pins))
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            metrics.export_project(self.root / 'public', root=self.root)

    def test_github_raw_bytes_are_retained_without_request_credentials(self):
        client = metrics.GitHub.__new__(metrics.GitHub)
        client.base = 'https://api.github.com/repos/example/fixture'
        client.headers = {'Authorization': 'Bearer private-credential'}
        client.evidence = []
        raw = b'{  "value": 1, "spacing": "retained" }\n'
        response = io.BytesIO(raw)
        response.headers = {}
        with patch.object(metrics.urllib.request, 'urlopen', return_value=response):
            data, more = client.get('')
        self.assertEqual(data['value'], 1)
        self.assertFalse(more)
        self.assertEqual(client.evidence[0]['raw_json'].encode(), raw)
        self.assertEqual(client.evidence[0]['sha256'], metrics.digest(raw))
        self.assertNotIn('private-credential', json.dumps(client.evidence))


if __name__ == '__main__':
    unittest.main()
