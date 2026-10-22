#!/usr/bin/env python3
"""Serialized, untimed Janet conformance; fork ownership precedes exec."""
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/qualification'))
from prolog_supervisor import Owner
sys.path.insert(0, str(ROOT / 'experiments/janet/bounded-v1'))
from outputs import validate_success


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, obj):
    p.write_text(json.dumps(obj, indent=2) + '\n')


def execute(command, directory, environment, lock, stdin=None, deadline=30):
    directory.mkdir()
    owner = Owner()
    gate_r, gate_w = os.pipe()
    record = dict(command=command, inherited_common_mutex=True, deadline_seconds=deadline,
                  quantitative_benchmark=False, controller_sha256=sha(Path(__file__)))
    with open(stdin or '/dev/null', 'rb') as inp, (directory/'stdout.bin').open('wb') as out, (directory/'stderr.bin').open('wb') as err:
        os.set_inheritable(lock.fileno(), True)
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
        try:
            while True:
                reaped, status = owner.waitpid(pid, os.WNOHANG)
                if reaped:
                    record['exit_status'] = os.waitstatus_to_exitcode(status)
                    break
                if time.monotonic() >= end:
                    raise TimeoutError('Owned process deadline')
                time.sleep(.01)
        except BaseException as error:
            record['error'] = str(error)
        finally:
            errors = owner.cleanup()
            record['cleanup_errors'] = errors
            record['group_closed'] = not owner.group_members(pid)
            record['reaped'] = owner.children[pid]['reaped']
            record['signals'] = owner.signals
            save(directory/'process.json', record)
        assert not errors and record['group_closed'] and record['reaped'], 'Owned cleanup incomplete'
        assert 'error' not in record, record.get('error')
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', required=True)
    args = parser.parse_args()
    plan_path = ROOT/'experiments/janet/bounded-v1/plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    for name, pin in plan['pins'].items():
        p = Path(name) if name.startswith('/') else ROOT/name
        assert sha(p) == pin['sha256'], name
    output = Path(__file__).parent/'run-v1'
    output.mkdir(exist_ok=False)
    report = dict(status='running', plan_sha256=sha(plan_path), observations=[],
                  benchmark_samples=0, chart_admission=False, required_work_qualified=False)
    corpus = json.loads((ROOT/plan['corpus']).read_bytes())
    lock_path = Path(plan['common_mutex'])
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['mutex_inode'] = os.fstat(lock.fileno()).st_ino
        assert report['mutex_inode'] == lock_path.stat().st_ino
        save(output/'results.json', report)
        version = execute([plan['runtime'], '--version'], output/'version', plan['environment'], lock)
        assert version['exit_status'] == 0
        assert (output/'version/stdout.bin').read_bytes() == plan['expected_version_stdout'].encode()
        assert not (output/'version/stderr.bin').read_bytes()
        for row in plan['schedule']:
            directory = output/f"{row['slot']:03d}-{row['benchmark']}-{row['case']}"
            process = execute(row['command'], directory, plan['environment'], lock, ROOT/row['stdin'])
            case = corpus['cases'][row['corpus_index']]
            obs = dict(slot=row['slot'], benchmark=row['benchmark'], case=row['case'])
            if case['expected_exit'] == 0:
                expected = (ROOT/plan['corpus']).parent.joinpath(case['expected']['path']).read_bytes()
                try:
                    validate_success(case, (directory/'stdout.bin').read_bytes(), (directory/'stderr.bin').read_bytes(), process['exit_status'], expected)
                    obs['status'] = 'bounded-output-pass'
                except ValueError as error:
                    obs.update(status='bounded-output-fail', error=str(error))
            else:
                obs['status'] = 'rejection-captured-unqualified'
            report['observations'].append(obs)
            save(output/'results.json', report)
            print(json.dumps(obs), flush=True)
        report['status'] = 'bounded-capture-complete'
        save(output/'results.json', report)


if __name__ == '__main__':
    main()
