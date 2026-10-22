#!/usr/bin/env python3
"""Owned Janet process execution with independent exit time and macOS wait4 resource usage."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import threading

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/qualification'))
from prolog_supervisor import Owner, lifecycle_atomic
sys.path.insert(0, str(ROOT / 'experiments/janet/bounded-v1'))
from outputs import validate_success


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, obj):
    p.write_text(json.dumps(obj, indent=2) + '\n')


def execute(command, directory, environment, lock, stdin=None, deadline=30, monitor=None, monitor_interval=10, quantitative=False):
    directory.mkdir()
    owner = Owner()
    gate_r, gate_w = os.pipe()
    record = dict(command=command, inherited_common_mutex=True, deadline_seconds=deadline,
                  quantitative_benchmark=quantitative, controller_sha256=sha(Path(__file__)))
    with open(stdin or '/dev/null', 'rb') as inp, (directory/'stdout.bin').open('wb') as out, (directory/'stderr.bin').open('wb') as err:
        os.set_inheritable(lock.fileno(), True)
        started = time.monotonic_ns()
        pid = owner.fork()
        if pid == 0:
            try:
                os.close(gate_w)
                if os.read(gate_r, 1) != b'G':
                    os._exit(125)
                os.close(gate_r)
                os.setsid()
                os.dup2(inp.fileno(), 0); os.dup2(out.fileno(), 1); os.dup2(err.fileno(), 2)
                os.chdir(ROOT)
                os.execve(command[0], command, environment)
            except BaseException:
                os._exit(126)
        os.close(gate_r)
        record['birth_identity'] = owner.children[pid]['identity']
        assert record['birth_identity'], 'No kernel birth identity before exec'
        os.write(gate_w, b'G'); os.close(gate_w)
        end = time.monotonic() + deadline
        next_monitor = time.monotonic() + monitor_interval
        exited = threading.Event()
        wait_errors = []
        def observe_exit():
            try:
                while True:
                    with lifecycle_atomic():
                        reaped, status, usage = os.wait4(pid, os.WNOHANG)
                        if reaped:
                            owner.children[pid]['reaped'] = True
                    if reaped:
                        record['elapsed_seconds'] = (time.monotonic_ns() - started) / 1e9
                        record['exit_status'] = os.waitstatus_to_exitcode(status)
                        assert sys.platform == 'darwin', 'This receipt uses macOS ru_maxrss byte units'
                        record['maximum_rss_bytes'] = usage.ru_maxrss
                        record['user_cpu_seconds'] = usage.ru_utime
                        record['system_cpu_seconds'] = usage.ru_stime
                        return
                    time.sleep(.001)
            except BaseException as error:
                wait_errors.append(error)
            finally:
                exited.set()
        waiter = threading.Thread(target=observe_exit, daemon=True)
        waiter.start()
        try:
            while not exited.wait(.01):
                if time.monotonic() >= end:
                    raise TimeoutError('Owned process deadline')
                if monitor is not None and time.monotonic() >= next_monitor:
                    monitor()
                    next_monitor = time.monotonic() + monitor_interval
            waiter.join()
            if wait_errors:
                raise wait_errors[0]
        except BaseException as error:
            record['error'] = str(error)
        finally:
            if waiter.is_alive():
                owner.kill(pid, signal.SIGKILL)
                waiter.join(timeout=3)
                if waiter.is_alive():
                    record['observer_still_waiting'] = True
                    save(directory/'process.json', record)
                    raise RuntimeError('Owned child remains unreaped; inherited mutex retained')
            errors = owner.cleanup()
            record['cleanup_errors'] = errors
            record['group_closed'] = not owner.group_members(pid)
            record['reaped'] = owner.children[pid]['reaped']
            record['signals'] = owner.signals
            save(directory/'process.json', record)
        assert not errors and record['group_closed'] and record['reaped'], 'Owned cleanup incomplete'
        assert 'error' not in record, record.get('error')
    return record

