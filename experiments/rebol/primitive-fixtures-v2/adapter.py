"""Unexecuted adapters for the unchanged eighteen general primitive fixtures.

No module import starts a process, reads evidence, or grants qualification. The
caller must supply the reviewed frozen observer, actual pinned case, explicit
environment, owned output directory and held mutex. This module only supplies
its launch/transfer hooks and independently decodes the small fixture sidecars.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import time


MAX_INPUT = 131089
FILE_LIMIT = 1048576
TIMEOUT_SECONDS = 180
FRAGMENTS = (1, 2, 255, 32767, 3, 4096)
MARKER = bytes.fromhex('4d4543482d494f2d4641554c542d563100')
FILE_LENGTHS = (0, 1, 255, 256, 32767, 32768, 32769, 65537, 131089)
CASE_IDS = ('arithmetic', 'formatting', 'regex', 'gc-ownership') + tuple(
    'file-'+str(n) for n in FILE_LENGTHS) + (
    'pipe-collect-65537', 'pipe-stream-65537', 'pipe-indexed-65537',
    'pipe-indexed-0', 'pipe-injected-short-io')


def require(value, message):
    if not value:
        raise AssertionError(message)


def natural(value):
    return type(value) is int and value >= 0


def byte_cycle(length):
    require(natural(length) and length <= MAX_INPUT, 'Bounded byte-cycle length required')
    return (bytes(range(256)) * ((length + 255)//256))[:length]


def case_bytes(case):
    """Expand only the original deterministic input/output recipes."""
    require(case['id'] in CASE_IDS, 'Unknown primitive case')
    recipe = case['stdin']
    if recipe['kind'] == 'empty':
        require(recipe == {'kind': 'empty'}, 'Unexpected empty-input fields')
        payload = b''
    else:
        require(recipe['kind'] == 'byte-cycle'
                and recipe['formula'] == 'byte[i] = i % 256, i in [0,length)'
                and recipe['transport'] in ('regular-file', 'pipe'), 'Unknown input recipe')
        payload = byte_cycle(recipe['length'])
    expected = case['stdout']
    if expected['kind'] == 'exact-ascii':
        stdout = expected['text'].encode('ascii')
    else:
        require(expected['kind'] == 'byte-cycle'
                and expected['formula'] == 'byte[i] = i % 256, i in [0,length)',
                'Unknown output recipe')
        prefix = bytes.fromhex(expected['prefix_hex'])
        require(prefix == (MARKER if case['id'] == 'pipe-injected-short-io' else b''),
                'Fault activation marker must remain real stdout')
        stdout = prefix + byte_cycle(expected['length'])
    return payload, stdout


# Retained mezz-save.reb uses mold/only and a trailing newline: there is no
# enclosing block or REBOL header. s-mold.c emits logic as #(true)/#(false).
# This accepts only the literal vocabulary these two fixtures actually save;
# it never loads/evaluates Rebol and is not a general Rebol parser.
TOKEN = re.compile(r'\s+|#\((?:true|false)\)|"[a-z0-9-]+"|[a-z][a-z0-9-]*|[0-9]+|\[|\]')


def observation(raw):
    require(type(raw) is bytes and len(raw) <= FILE_LIMIT, 'Bounded observation bytes required')
    text = raw.decode('ascii')
    tokens, position = [], 0
    while position < len(text):
        match = TOKEN.match(text, position)
        require(match is not None, 'Unsupported observation syntax')
        token = match.group(); position = match.end()
        if not token.isspace():
            tokens.append(token)
    values, index = {}, 0
    while index < len(tokens):
        key = tokens[index]; index += 1
        require(re.fullmatch('[a-z][a-z0-9-]*', key) and key not in values,
                'Unique observation word key required')
        require(index < len(tokens), 'Missing observation value')
        token = tokens[index]; index += 1
        if token == '[':
            value = []
            while index < len(tokens) and tokens[index] != ']':
                require(tokens[index].isdigit(), 'Only integer chunk entries allowed')
                value.append(int(tokens[index])); index += 1
                require(len(value) <= MAX_INPUT, 'Too many chunk observations')
            require(index < len(tokens), 'Unclosed chunk block')
            index += 1
        elif token.startswith('"'):
            value = token[1:-1]
        elif token in ('#(true)', '#(false)'):
            value = token == '#(true)'
        else:
            require(token.isdigit(), 'Unsupported observation value')
            value = int(token)
        values[key] = value
    return values


def unique_object(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate fault-sidecar key')
        result[key] = value
    return result


def check_case(case, stdout, stderr, exit_status, *, sidecar=None, fault_sidecar=None):
    """Validate retained bytes only; owned lifecycle and file closure are external."""
    _, expected = case_bytes(case)
    require(type(exit_status) is int and exit_status == case['exit'] == 0, 'Fixture exit failed')
    require(stderr == b'' and case['stderr'] == {'kind': 'empty'}, 'Fixture stderr is not empty')
    require(stdout == expected, 'Fixture stdout differs; preserve original raw bytes')
    decoded = None
    require((sidecar is not None) == ('sidecar' in case), 'Missing or unexpected observation sidecar')
    if sidecar is not None:
        decoded = observation(sidecar)
        expected_sidecar = case['sidecar']
        require(decoded.get('schema') == expected_sidecar['schema'], 'Observation schema differs')
        if case['id'] == 'gc-ownership':
            require(set(decoded) == {'schema', 'before', 'after', 'discarded-buffer-count',
                'discarded-buffer-capacity', 'manual-gc', 'policy-changed'}, 'GC observation fields differ')
            require(natural(decoded['before']) and natural(decoded['after'])
                    and decoded['after'] > decoded['before'], 'Automatic collection was not observed')
            require(type(decoded['discarded-buffer-count']) is int and decoded['discarded-buffer-count'] == 65536
                    and type(decoded['discarded-buffer-capacity']) is int and decoded['discarded-buffer-capacity'] == 1024
                    and decoded['manual-gc'] is False and decoded['policy-changed'] is False,
                    'GC churn/policy differs from the frozen fixture')
        else:
            require(set(decoded) == {'schema', 'mode', 'bytes', 'chunks', 'eof'}, 'IO observation fields differ')
            require(decoded['mode'] == expected_sidecar['mode'] and natural(decoded['bytes'])
                    and decoded['bytes'] == expected_sidecar['bytes'] and decoded['eof'] is True,
                    'IO mode, byte count or EOF differs')
            chunks = decoded['chunks']
            require(type(chunks) is list and all(natural(n) and 0 < n <= 32768 for n in chunks)
                    and sum(chunks) == decoded['bytes'], 'Invalid native read-chunk observations')
    require((fault_sidecar is not None) == ('fault_sidecar' in case), 'Missing or unexpected fault sidecar')
    fault = None
    if fault_sidecar is not None:
        require(type(fault_sidecar) is bytes and len(fault_sidecar) <= 4096, 'Bounded fault JSON required')
        fault = json.loads(fault_sidecar, object_pairs_hook=unique_object)
        keys = {'armed', 'read_calls', 'write_calls', 'read_eintr', 'write_eintr',
                'read_short', 'write_short', 'read_bytes', 'write_bytes'}
        require(type(fault) is dict and set(fault) == keys | {'schema'}, 'Fault observation fields differ')
        require(fault['schema'] == case['fault_sidecar']['schema'] and all(natural(fault[k]) for k in keys),
                'Invalid fault counters')
        require(all(fault[k] == v for k, v in case['fault_sidecar']['exact'].items()),
                'Fault activation/EINTR/byte counts differ')
        require(fault['read_short'] > 0 and fault['write_short'] > 0
                and fault['read_calls'] > fault['read_eintr']
                and fault['write_calls'] > fault['write_eintr'], 'Actual short IO was not observed')
        require(fault['read_short'] <= fault['read_calls'] - fault['read_eintr']
                and fault['write_short'] <= fault['write_calls'] - fault['write_eintr'],
                'Short IO counters exceed completed-call opportunities')
    return {'observation': decoded, 'fault_observation': fault,
            'raw_outputs_match': True, 'lifecycle_qualified_here': False,
            'primitive_qualification_granted_here': False}


@contextmanager
def regular_input(path, payload):
    """Keep the exact regular descriptor open through observer cleanup and replay."""
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'Physical absolute input required')
    before = path.lstat(); require(stat.S_ISREG(before.st_mode), 'Regular stdin file required')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    # Popen inherits the OS descriptor offset, not a BufferedReader's logical
    # position. Keep this handle unbuffered so a rewind really reaches fd 0.
    with os.fdopen(descriptor, 'rb', buffering=0) as stream:
        held = os.fstat(stream.fileno())
        require(stat.S_ISREG(held.st_mode) and (held.st_dev, held.st_ino) == (before.st_dev, before.st_ino),
                'Regular input changed before open')
        require(held.st_size == len(payload) <= MAX_INPUT
                and stream.read(MAX_INPUT + 1) == payload, 'Regular stdin bytes differ')
        stream.seek(0)
        try:
            yield stream
        finally:
            after = path.lstat()
            require(stat.S_ISREG(after.st_mode) and (after.st_dev, after.st_ino) == (held.st_dev, held.st_ino)
                    and stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Regular stdin identity changed')
            stream.seek(0)
            require(stream.read(MAX_INPUT + 1) == payload, 'Regular stdin changed during observation')


class Transport:
    """Hooks only: the frozen observer retains native ownership and cleanup.

    Save record in the caller's finally block, even when observe raises. The
    caller must retain independent sidecars and raw captures on every outcome.
    Neither hook catches or replaces the observer's process/lifecycle outcome.
    """
    def __init__(self, case, *, regular=None, popen=subprocess.Popen,
                 clock=time.monotonic, selector_factory=selectors.DefaultSelector):
        self.payload, _ = case_bytes(case)
        self.mode = case['stdin'].get('transport', 'pipe')
        require((regular is not None) == (self.mode == 'regular-file'), 'Regular descriptor/transport mismatch')
        self.regular, self.popen, self.clock, self.selector_factory = regular, popen, clock, selector_factory
        self.policy = case.get('pipe_policy')
        if self.policy is not None:
            require(self.mode == 'pipe' and self.policy == dict(concurrent_feeder_and_reader=True,
                feed_fragment_cycle=list(FRAGMENTS), stdout_read_cap=13, short_syscall_claim=False),
                'Frozen pipe policy differs')
        require(not case['id'].startswith('pipe-') or self.policy is not None, 'Pipe case lost its policy')
        self.record = dict(schema='rebol-fixture-observed-transport-v1', case=case['id'],
            requested_transport=self.mode, spawn_hook_called=False, transfer_started=False,
            input_bytes=len(self.payload), parent_write_attempts=0, parent_write_calls=0,
            parent_write_bytes=0, parent_partial_writes=0, parent_write_would_block=0,
            parent_write_interrupted=0, completed_fragments_by_cycle_slot=[0]*len(FRAGMENTS),
            parent_read_attempts=0, parent_read_calls=0, parent_read_bytes=0,
            parent_read_would_block=0, parent_read_interrupted=0, largest_parent_read=0,
            stdin_closed=False, stdout_eof=False, parent_epipe=False, transfer_completed=False,
            extension_short_syscall_claim=False)

    def launch(self, *args, **kwargs):
        require(not self.record['spawn_hook_called'], 'Transport hook cannot launch twice')
        require(kwargs.get('stdin') == subprocess.PIPE and kwargs.get('stdout') == subprocess.PIPE,
                'Unexpected observer stdio contract')
        if self.regular is not None:
            held = os.fstat(self.regular.fileno())
            require(stat.S_ISREG(held.st_mode) and held.st_size == len(self.payload)
                    and os.lseek(self.regular.fileno(), 0, os.SEEK_CUR) == 0,
                    'Prepared regular stdin descriptor differs')
            self.record['spawn_stdin_descriptor'] = dict(type='regular-file', device=held.st_dev,
                inode=held.st_ino, size=held.st_size, offset=0)
            kwargs['stdin'] = self.regular
        self.record['spawn_hook_called'] = True
        # Never add fallible work after Popen returns: the frozen observer must
        # receive the child immediately and register it inside its signal mask.
        return self.popen(*args, **kwargs)

    def transfer(self, process, payload, output, deadline, tick):
        require(payload == self.payload and not self.record['transfer_started'], 'Transfer input/reentry differs')
        self.record['transfer_started'] = True
        require(stat.S_ISFIFO(os.fstat(process.stdout.fileno()).st_mode), 'Actual stdout is not a pipe')
        self.record['observed_stdout_type'] = 'fifo'
        if self.regular is None:
            require(process.stdin is not None and stat.S_ISFIFO(os.fstat(process.stdin.fileno()).st_mode),
                    'Actual parent stdin endpoint is not a pipe')
            self.record['observed_parent_stdin_type'] = 'fifo'
        else:
            require(process.stdin is None and stat.S_ISREG(os.fstat(self.regular.fileno()).st_mode),
                    'Regular file was not supplied as native stdin')
            self.record['observed_parent_stdin_type'] = 'regular-file'
        offset, fragment, remaining_fragment = 0, 0, 0
        read_cap = 13 if self.policy else 65536
        self.record['stdout_read_cap'] = read_cap

        def progress():
            if self.clock() >= deadline:
                # Preserve the frozen observer's timed_out classification.
                raise subprocess.TimeoutExpired(process.args, TIMEOUT_SECONDS)
            tick()  # Existing kernel identity, process-group RSS and file guards.

        with self.selector_factory() as selector:
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            if self.regular is None:
                if payload:
                    os.set_blocking(process.stdin.fileno(), False)
                    selector.register(process.stdin, selectors.EVENT_WRITE)
                else:
                    process.stdin.close(); self.record['stdin_closed'] = True
            while selector.get_map():
                progress()
                for key, _ in selector.select(min(0.05, max(0, deadline-self.clock()))):
                    progress()
                    if key.fileobj is process.stdout:
                        self.record['parent_read_attempts'] += 1
                        try:
                            data = os.read(process.stdout.fileno(), read_cap)
                        except BlockingIOError:
                            self.record['parent_read_would_block'] += 1; continue
                        except InterruptedError:
                            self.record['parent_read_interrupted'] += 1; continue
                        self.record['parent_read_calls'] += 1
                        if data:
                            output.write(data); output.flush()
                            self.record['parent_read_bytes'] += len(data)
                            self.record['largest_parent_read'] = max(self.record['largest_parent_read'], len(data))
                            require(output.tell() <= FILE_LIMIT, 'Fixture stdout exceeded capture limit')
                        else:
                            selector.unregister(process.stdout); process.stdout.close()
                            self.record['stdout_eof'] = True
                    else:
                        require(key.fileobj is process.stdin, 'Unknown transfer endpoint')
                        if remaining_fragment == 0:
                            remaining_fragment = min(FRAGMENTS[fragment % len(FRAGMENTS)] if self.policy else 65536,
                                                     len(payload)-offset)
                        self.record['parent_write_attempts'] += 1
                        try:
                            written = os.write(process.stdin.fileno(), payload[offset:offset+remaining_fragment])
                        except BlockingIOError:
                            self.record['parent_write_would_block'] += 1; continue
                        except InterruptedError:
                            self.record['parent_write_interrupted'] += 1; continue
                        except BrokenPipeError:
                            self.record['parent_epipe'] = True
                            selector.unregister(process.stdin); process.stdin.close()
                            self.record['stdin_closed'] = True
                            raise AssertionError('Child closed stdin before the complete payload')
                        require(0 < written <= remaining_fragment, 'Invalid successful parent write count')
                        self.record['parent_write_calls'] += 1
                        self.record['parent_write_bytes'] += written
                        self.record['parent_partial_writes'] += int(written < remaining_fragment)
                        offset += written; remaining_fragment -= written
                        if remaining_fragment == 0:
                            if self.policy:
                                self.record['completed_fragments_by_cycle_slot'][fragment % len(FRAGMENTS)] += 1
                            fragment += 1
                        if offset == len(payload):
                            selector.unregister(process.stdin); process.stdin.close()
                            self.record['stdin_closed'] = True
                    progress()
        require(self.record['stdout_eof'] and (self.regular is not None or offset == len(payload)),
                'Incomplete input/output transport')
        self.record['transfer_completed'] = True
