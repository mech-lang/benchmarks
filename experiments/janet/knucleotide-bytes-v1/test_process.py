import fcntl
import json
from pathlib import Path
import tempfile
import time
import unittest
import process

class ProcessTests(unittest.TestCase):
    def test_exit_clock_independent_of_telemetry(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            with (p/'lock').open('w+') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                r=process.execute(['/bin/sleep','.1'],p/'ok',{'PATH':'/usr/bin:/bin'},lock,
                                  monitor=lambda: time.sleep(.5),monitor_interval=.01)
                self.assertEqual(r['exit_status'],0)
                self.assertGreater(r['maximum_rss_bytes'],0)
                self.assertGreater(r['elapsed_seconds'],.09)
                self.assertLess(r['elapsed_seconds'],.45)
                memory=process.execute(['/usr/bin/python3','-c','x=bytearray(32*1024*1024)'],p/'memory',{'PATH':'/usr/bin:/bin'},lock,quantitative=True)
                self.assertGreater(memory['maximum_rss_bytes'],32*1024*1024)
                self.assertTrue(memory['quantitative_benchmark'])
                with self.assertRaises(AssertionError):
                    process.execute(['/bin/sleep','10'],p/'timeout',{'PATH':'/usr/bin:/bin'},lock,deadline=.05)
                r=json.loads((p/'timeout/process.json').read_text())
                self.assertTrue(r['reaped'] and r['group_closed'])
                self.assertEqual(r['cleanup_errors'],[])

if __name__=='__main__':unittest.main()
