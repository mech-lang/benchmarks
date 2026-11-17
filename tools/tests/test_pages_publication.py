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


if __name__ == '__main__':
    unittest.main()
