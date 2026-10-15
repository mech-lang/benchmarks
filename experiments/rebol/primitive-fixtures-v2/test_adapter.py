"""Unrun synthetic tests; no child processes, toolchain intake or runtime replay."""
import importlib.util
import io
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('adapter.py')
SPEC = importlib.util.spec_from_file_location('rebol_fixture_adapter', PATH)
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def cases():
    return json.loads((PATH.parent.parent/'primitive-fixtures-v1/spec.json').read_text())['cases']


def case(name):
    return next(c for c in cases() if c['id'] == name)


def io_sidecar(mode='collect', count=0, chunks=''):
    return ('schema "rebol-primitive-io-observation-v1" mode "'+mode+'" bytes '+str(count)
            +' chunks ['+chunks+'] eof #(true)\n').encode()


class Stream:
    def __init__(self, fd):
        self.fd, self.closed = fd, False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True


class Selector:
    def __init__(self, *, idle=False, output_first=False):
        self.entries = {}; self.idle = idle; self.output_first = output_first

    def __enter__(self): return self
    def __exit__(self, *args): pass
    def register(self, stream, event): self.entries[stream] = event
    def unregister(self, stream): del self.entries[stream]
    def get_map(self): return self.entries

    def select(self, timeout):
        if self.idle: return []
        entries = list(self.entries.items())
        if self.output_first:
            entries.sort(key=lambda p: p[1] != selectors.EVENT_READ)
        return [(SimpleNamespace(fileobj=s), event) for s, event in entries]


class AdapterTests(unittest.TestCase):
    def test_original_inventory_and_all_bytes(self):
        self.assertEqual(tuple(c['id'] for c in cases()), a.CASE_IDS)
        for c in cases():
            incoming, outgoing = a.case_bytes(c)
            if c['stdin']['kind'] == 'byte-cycle':
                self.assertEqual(incoming, bytes(i % 256 for i in range(c['stdin']['length'])))
                self.assertEqual(outgoing, (a.MARKER if 'fault_sidecar' in c else b'') + incoming)
        self.assertEqual(set(a.byte_cycle(256)), set(range(256)))

    def test_save_flat_shape_logic_and_chunks(self):
        c = case('file-32769'); incoming, _ = a.case_bytes(c)
        result = a.check_case(c, incoming, b'', 0,
            sidecar=io_sidecar(count=32769, chunks='32768 1'))
        self.assertEqual(result['observation']['chunks'], [32768, 1])
        for raw in (b'[schema "x"]', b'schema "x" schema "x"', b'eof true',
                    b'chunks [[1]]', b'count -1', b'count 1.0', b'count 1 ; comment',
                    b'count (do %some-file)', b'schema {x}'):
            with self.subTest(raw=raw), self.assertRaises((AssertionError, ValueError)):
                a.observation(raw)

    def test_gc_is_observed_not_predicted(self):
        raw = (b'schema "rebol-primitive-gc-observation-v1" before 7 after 9 '
               b'discarded-buffer-count 65536 discarded-buffer-capacity 1024 '
               b'manual-gc #(false) policy-changed #(false)\n')
        c = case('gc-ownership')
        a.check_case(c, b'ok gc-ownership\n', b'', 0, sidecar=raw)
        for changed in (raw.replace(b'after 9', b'after 7'),
                        raw.replace(b'manual-gc #(false)', b'manual-gc #(true)'),
                        raw.replace(b'65536', b'65537')):
            with self.assertRaises(AssertionError):
                a.check_case(c, b'ok gc-ownership\n', b'', 0, sidecar=changed)

    def test_sidecars_cannot_replace_raw_output_or_successful_exit(self):
        c = case('file-0'); sidecar = io_sidecar()
        for output, stderr, code, saved in ((b'x', b'', 0, sidecar), (b'', b'x', 0, sidecar),
                (b'', b'', 1, sidecar), (b'', b'', 0, None),
                (b'', b'', 0, io_sidecar(count=1, chunks='1'))):
            with self.assertRaises(AssertionError):
                a.check_case(c, output, stderr, code, sidecar=saved)

    def test_fault_counters_marker_and_duplicate_keys(self):
        c = case('pipe-injected-short-io'); _, output = a.case_bytes(c)
        saved = io_sidecar('faults', 65537, '32768 32768 1')
        fault = dict(schema=c['fault_sidecar']['schema'], armed=1, read_calls=10000,
            write_calls=6000, read_eintr=2, write_eintr=2, read_short=9997,
            write_short=5997, read_bytes=65537, write_bytes=65554)
        a.check_case(c, output, b'', 0, sidecar=saved, fault_sidecar=json.dumps(fault).encode())
        for key, value in (('armed', 0), ('read_eintr', 1), ('write_short', 0),
                           ('write_bytes', 65537), ('read_calls', True), ('read_calls', 3)):
            changed = dict(fault); changed[key] = value
            with self.assertRaises(AssertionError):
                a.check_case(c, output, b'', 0, sidecar=saved, fault_sidecar=json.dumps(changed).encode())
        duplicate = json.dumps(fault).replace('"armed": 1', '"armed": 1, "armed": 1').encode()
        with self.assertRaises(AssertionError):
            a.check_case(c, output, b'', 0, sidecar=saved, fault_sidecar=duplicate)
        with self.assertRaises(AssertionError):
            a.check_case(c, output[len(a.MARKER):], b'', 0, sidecar=saved,
                         fault_sidecar=json.dumps(fault).encode())

    def test_regular_launch_inherits_actual_zero_offset_and_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'stdin.bin'; payload = a.byte_cycle(32769)
            path.write_bytes(payload)
            with a.regular_input(path, payload) as stream:
                def fake_launch(*args, **kwargs):
                    self.assertIs(kwargs['stdin'], stream)
                    self.assertTrue(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
                    self.assertEqual(os.lseek(stream.fileno(), 0, os.SEEK_CUR), 0)
                    return 'owned-child-placeholder'
                transport = a.Transport(case('file-32769'), regular=stream, popen=fake_launch)
                self.assertEqual(transport.launch(['placeholder'], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE), 'owned-child-placeholder')
                self.assertEqual(transport.record['spawn_stdin_descriptor']['size'], len(payload))
                with self.assertRaises(AssertionError):
                    transport.launch(['placeholder'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def test_regular_file_mutation_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'stdin.bin'; path.write_bytes(b'')
            with self.assertRaises(AssertionError):
                with a.regular_input(path, b''):
                    path.write_bytes(b'x')

    def transfer(self, *, epipe=False, idle=False, output_first=False, regular=False):
        c = case('file-256' if regular else 'pipe-indexed-65537')
        payload, _ = a.case_bytes(c)
        regular_stream = Stream(72) if regular else None
        clock = [0.0]; ticks = []
        transport = a.Transport(c, regular=regular_stream, clock=lambda: clock[0],
            selector_factory=lambda: Selector(idle=idle, output_first=output_first))
        process = SimpleNamespace(args=['fixture-placeholder'],
                                  stdin=None if regular else Stream(70), stdout=Stream(71))
        reads = [b'observed output', b'']; writes = []
        output = io.BytesIO()

        def tick():
            ticks.append(True)
            if idle: clock[0] += 0.25

        def read(fd, amount):
            self.assertEqual(fd, 71)
            data = reads[0][:amount]; reads[0] = reads[0][amount:]
            if not reads[0] and data: reads.pop(0)
            return data

        def write(fd, data):
            self.assertEqual(fd, 70)
            if epipe: raise BrokenPipeError()
            count = min(2, len(data)); writes.append(bytes(data[:count])); return count

        try:
            with patch.object(a.os, 'fstat', side_effect=lambda fd: SimpleNamespace(
                    st_mode=stat.S_IFREG if fd == 72 else stat.S_IFIFO)), \
                 patch.object(a.os, 'set_blocking'), patch.object(a.os, 'read', side_effect=read), \
                 patch.object(a.os, 'write', side_effect=write):
                transport.transfer(process, payload, output, 1.0 if idle else 100.0, tick)
        except BaseException as error:
            return transport, writes, output.getvalue(), ticks, error
        return transport, writes, output.getvalue(), ticks, None

    def test_partial_pipe_writes_use_actual_counts_and_poll_resources(self):
        transport, writes, output, ticks, error = self.transfer()
        self.assertIsNone(error)
        self.assertEqual(b''.join(writes), a.byte_cycle(65537))
        self.assertEqual(transport.record['parent_write_bytes'], 65537)
        self.assertEqual(transport.record['parent_write_calls'], len(writes))
        self.assertGreater(transport.record['parent_partial_writes'], 0)
        self.assertLessEqual(transport.record['largest_parent_read'], 13)
        self.assertEqual(output, b'observed output')
        self.assertGreater(len(ticks), len(writes))
        self.assertTrue(transport.record['transfer_completed'])

    def test_empty_output_eof_does_not_skip_remaining_feed(self):
        transport, writes, _, _, error = self.transfer(output_first=True)
        self.assertIsNone(error)
        self.assertTrue(transport.record['stdout_eof'])
        self.assertEqual(b''.join(writes), a.byte_cycle(65537))

    def test_regular_input_has_no_fake_parent_write_observations(self):
        transport, writes, _, _, error = self.transfer(regular=True)
        self.assertIsNone(error)
        self.assertEqual(writes, [])
        self.assertEqual(transport.record['observed_parent_stdin_type'], 'regular-file')
        self.assertEqual(transport.record['parent_write_bytes'], 0)

    def test_stall_polls_and_deadline_rejects(self):
        transport, _, _, ticks, error = self.transfer(idle=True)
        self.assertIsInstance(error, subprocess.TimeoutExpired)
        self.assertGreater(len(ticks), 1)
        self.assertFalse(transport.record['transfer_completed'])

    def test_epipe_preserves_partial_transport_without_success(self):
        transport, _, output, _, error = self.transfer(epipe=True)
        self.assertIsInstance(error, AssertionError)
        self.assertTrue(transport.record['parent_epipe'])
        self.assertTrue(transport.record['stdin_closed'])
        self.assertFalse(transport.record['transfer_completed'])
        self.assertEqual(output, b'observed outp')


if __name__ == '__main__':
    unittest.main()
