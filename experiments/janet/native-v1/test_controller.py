import fcntl
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('janet_native', Path(__file__).with_name('run.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class ControllerTests(unittest.TestCase):
    def test_normal_nonzero_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root/'lock').open('w+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                env = {'PATH':'/usr/bin:/bin'}
                ok = m.execute(['/bin/echo','complete'], root/'ok', env, lock)
                self.assertEqual(ok['exit_status'], 0)
                self.assertEqual((root/'ok/stdout.bin').read_bytes(), b'complete\n')
                bad = m.execute(['/usr/bin/false'], root/'bad', env, lock)
                self.assertNotEqual(bad['exit_status'], 0)
                with self.assertRaises(AssertionError):
                    m.execute(['/bin/sleep','10'], root/'timeout', env, lock, deadline=.1)
                import json
                receipt = json.loads((root/'timeout/process.json').read_bytes())
                self.assertTrue(receipt['reaped'] and receipt['group_closed'])
                self.assertEqual(receipt['cleanup_errors'], [])

if __name__ == '__main__': unittest.main()
