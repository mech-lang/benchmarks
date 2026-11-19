"""Publication checks cover the evidence linked from the campaign dashboard."""
import hashlib
import importlib.util
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('verify_pages', Path(__file__).parents[1] / 'verify_pages.py')
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)


class PagesPublication(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.raw = self.root / 'campaign-evidence/run-001/raw/fork-1/supervised.json'
        self.raw.parent.mkdir(parents=True)
        self.raw.write_text('{"outcome":"ok"}\n')
        (self.root / 'index.html').write_text('<html></html>')
        self.manifest = {'version': 'test', 'files': {
            path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in self.root.rglob('*') if path.is_file()}}
        (self.root / 'build.json').write_text(json.dumps(self.manifest))

    def test_nested_evidence_is_pinned(self):
        files = pages.check_local_assets(self.root, self.manifest)
        name = self.raw.relative_to(self.root).as_posix()
        self.assertEqual(files[name]['sha256'], self.manifest['files'][name])
        self.assertEqual(files[name]['bytes'], self.raw.stat().st_size)

    def test_missing_nested_evidence_is_rejected(self):
        self.raw.unlink()
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            pages.check_local_assets(self.root, self.manifest)

    def test_changed_nested_evidence_is_rejected(self):
        self.raw.write_text('{"outcome":"changed"}\n')
        with self.assertRaisesRegex(RuntimeError, 'differs from reviewed manifest'):
            pages.check_local_assets(self.root, self.manifest)

    def test_unlisted_nested_file_is_rejected(self):
        self.raw.with_name('extra.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError, 'inventory'):
            pages.check_local_assets(self.root, self.manifest)

    def test_symlink_to_evidence_is_rejected(self):
        self.raw.with_name('alias.json').symlink_to(self.raw.name)
        with self.assertRaisesRegex(RuntimeError, 'Symlinks'):
            pages.check_local_assets(self.root, self.manifest)

    def test_symlink_directory_is_rejected(self):
        (self.root / 'alias').symlink_to(self.raw.parent, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'Symlinks'):
            pages.check_local_assets(self.root, self.manifest)

    def test_live_entry_point_is_hashed_from_response(self):
        raw = b'<html>Metrics</html>'
        response = io.BytesIO(raw)
        response.status = 200
        with patch.object(pages, 'request', return_value=response):
            actual = pages.check_live_asset('https://mech-lang.org/metrics/', {'bytes': len(raw)})
        self.assertEqual(actual, dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))

    def test_oversized_live_entry_point_is_rejected(self):
        response = io.BytesIO(b'wrong page')
        response.status = 200
        with patch.object(pages, 'request', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'exceeds expected size'):
                pages.check_live_asset('https://mech-lang.org/metrics/', {'bytes': 1})

    def test_external_archives_require_an_immutable_expected_repository(self):
        name='campaign-evidence/run-001/raw.tar.gz'
        pin={'url':'https://raw.githubusercontent.com/mech-lang/benchmarks/'+('a'*40)+'/results/campaigns/run-001/raw.tar.gz',
             'sha256':'b'*64,'bytes':10}
        manifest={**self.manifest,'external_files':{name:pin}}
        self.assertEqual(pages.external_assets(manifest),{name:pin})
        for url in [pin['url'].replace('a'*40,'main'),pin['url'].replace('mech-lang/benchmarks','different/repo'),pin['url'].replace('https:','http:')]:
            with self.subTest(url=url),self.assertRaisesRegex(RuntimeError,'immutable repository'):
                pages.external_assets({**manifest,'external_files':{name:{**pin,'url':url}}})

    def test_archive_redirect_must_reach_its_pinned_commit(self):
        response=io.BytesIO(b'complete archive');response.status=200
        response.geturl=lambda:'https://raw.githubusercontent.com/mech-lang/benchmarks/main/results/campaigns/run-001/raw.tar.gz'
        with patch.object(pages,'request',return_value=response),self.assertRaisesRegex(RuntimeError,'redirect differs'):
            pages.check_live_asset('https://mech-lang.org/benchmarks/campaign-evidence/run-001/raw.tar.gz',{'bytes':16},
                'https://raw.githubusercontent.com/mech-lang/benchmarks/'+('a'*40)+'/results/campaigns/run-001/raw.tar.gz')


if __name__ == '__main__':
    unittest.main()
