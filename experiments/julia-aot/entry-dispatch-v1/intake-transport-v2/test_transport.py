"""Unrun pure transport faults: fake probes and descriptor writes, no LLDB."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('transport.py')
spec = importlib.util.spec_from_file_location('entry_intake_transport', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.probe = Path(self.temporary.name)/'probe.py'

    def fixture(self, body):
        raw = ('def entry(debugger, draft_sha, trace_sha):\n'+body).encode()
        self.probe.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def collector(self, chunk=13, interrupt=True):
        streams, calls = {1: bytearray(), 2: bytearray()}, []
        def write(fd, raw):
            calls.append((fd, len(raw)))
            if interrupt and len(calls) % 5 == 1:
                raise InterruptedError()
            data = bytes(raw[:chunk])
            streams[fd].extend(data)
            return len(data)
        return streams, calls, write

    def test_partial_writes_and_eintr_preserve_both_streams(self):
        streams, calls, writer = self.collector(chunk=3)
        stdout, stderr = 'body:λ😀\n'.encode(), b'failure details\n'
        with patch.object(m.os, 'write', side_effect=writer):
            m.write_all(1, stdout); m.write_all(2, stderr)
        self.assertEqual(bytes(streams[1]), stdout)
        self.assertEqual(bytes(streams[2]), stderr)
        self.assertGreater(len(calls), 4)

    def test_complete_large_json_and_stderr_after_probe_return(self):
        expected = dict(status='complete', payload='x'*300000, final_field='λ😀')
        probe_sha = self.fixture(
            '    import json, sys\n'
            '    assert draft_sha == "draft" and trace_sha == "trace"\n'
            '    print(json.dumps(dict(status="complete", payload="x"*300000, final_field="λ😀"), ensure_ascii=False))\n'
            '    sys.stderr.write("separate diagnostic\\n")\n'
            '    return 0\n')
        streams, _, writer = self.collector(chunk=8191)
        with patch.object(m.os, 'write', side_effect=writer):
            status = m.run(object(), self.probe, probe_sha, 'draft', 'trace')
        self.assertEqual(status, 0)
        self.assertGreater(len(streams[1]), 268124)
        self.assertEqual(json.loads(streams[1]), expected)
        self.assertEqual(bytes(streams[2]), b'separate diagnostic\n')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(streams[1][:-3])

    def test_nonzero_and_exception_keep_output_and_failure(self):
        for ending in ('    return 1\n', '    raise ValueError("probe fault")\n'):
            with self.subTest(ending=ending):
                digest = self.fixture('    import sys\n    print("{\\"partial\\": true}")\n'
                    '    sys.stderr.write("before failure\\n")\n'+ending)
                streams, _, writer = self.collector()
                with patch.object(m.os, 'write', side_effect=writer):
                    status = m.run(object(), self.probe, digest, 'draft', 'trace')
                self.assertEqual(status, 1)
                self.assertEqual(json.loads(streams[1]), {'partial': True})
                self.assertTrue(streams[2].startswith(b'before failure\n'))
                if 'raise' in ending:
                    self.assertIn(b'ValueError: probe fault', streams[2])

    def test_invalid_status_and_wrong_source_pin_fail(self):
        for ending in ('True', '2', 'None'):
            with self.subTest(ending=ending):
                digest = self.fixture('    return '+ending+'\n')
                streams, _, writer = self.collector()
                with patch.object(m.os, 'write', side_effect=writer):
                    self.assertEqual(m.run(object(), self.probe, digest, 'd', 't'), 1)
                self.assertIn(b'Unexpected static probe status', streams[2])
        digest = self.fixture('    print("must not execute")\n    return 0\n')
        streams, _, writer = self.collector()
        with patch.object(m.os, 'write', side_effect=writer):
            self.assertEqual(m.run(object(), self.probe, '0'*64, 'd', 't'), 1)
        self.assertEqual(streams[1], b'')
        self.assertIn(b'Pinned probe changed', streams[2])

    def test_zero_write_and_broken_pipe_are_not_success(self):
        for effect in (lambda fd, data: 0, lambda fd, data: (_ for _ in ()).throw(BrokenPipeError())):
            with self.subTest(effect=effect), patch.object(m.os, 'write', side_effect=effect):
                with self.assertRaises(OSError):
                    m.write_all(1, b'not-complete')

    def test_exact_outer_command_forces_failure_status_on_load_or_write_error(self):
        probe_sha = self.fixture('    print("{\\"complete\\": true}")\n    return 0\n')
        transport_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        for mode in ('complete', 'bad-transport-pin', 'broken-stdout'):
            with self.subTest(mode=mode):
                command = m.command_source(SOURCE, '0'*64 if mode == 'bad-transport-pin' else transport_sha,
                    self.probe, probe_sha, 'draft', 'trace')
                streams, _, normal = self.collector()
                def writer(fd, data):
                    if mode == 'broken-stdout' and fd == 1:
                        raise BrokenPipeError('injected stdout failure')
                    return normal(fd, data)
                with patch.object(m.os, 'write', side_effect=writer), \
                        patch.object(m.os, '_exit', side_effect=SystemExit) as exited:
                    with self.assertRaises(SystemExit):
                        exec(command.removeprefix('script '), {'lldb': types.SimpleNamespace(debugger=object())})
                exited.assert_called_once_with(0 if mode == 'complete' else 1)
                if mode == 'complete':
                    self.assertEqual(json.loads(streams[1]), {'complete': True})
                    self.assertEqual(streams[2], b'')
                else:
                    self.assertTrue(streams[2])


if __name__ == '__main__':
    unittest.main()
