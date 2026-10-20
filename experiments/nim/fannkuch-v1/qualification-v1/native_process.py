"""Exclusive untimed native attempts with a continuously held common mutex."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def atom(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def one(command, directory, environment, cwd, lock_fd, timeout=180):
    """Capture one fresh process group; retain every failure and raw stream."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    record = dict(command=list(map(str, command)), cwd=str(cwd),
        environment=environment, stdin='/dev/null', started_utc=now(),
        timeout_seconds=timeout, quantitative_benchmark=False,
        common_mutex_inherited=True, common_mutex_fd=lock_fd,
        common_mutex_inode=os.fstat(lock_fd).st_ino)
    atom(directory / 'active.json', record)
    completed = threading.Event()
    child = [None]
    timed_out = [False]

    def watchdog():
        if not completed.wait(timeout):
            timed_out[0] = True
            if child[0] is not None:
                try:
                    os.killpg(child[0].pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    watcher = threading.Thread(target=watchdog, daemon=True)
    watcher.start()
    try:
        with open('/dev/null', 'rb') as inp, (directory / 'stdout.bin').open('xb') as out, (directory / 'stderr.bin').open('xb') as err:
            started = time.perf_counter_ns()
            process = subprocess.Popen(record['command'], cwd=cwd, env=environment,
                stdin=inp, stdout=out, stderr=err, start_new_session=True,
                pass_fds=(lock_fd,))
            child[0] = process
            record.update(pid=process.pid, pgid=process.pid)
            atom(directory / 'active.json', record)
            pid, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            if pid != process.pid:
                raise ValueError('Waited for an unexpected process')
            record.update(exit_code=process.returncode,
                elapsed_seconds=(time.perf_counter_ns() - started) / 1e9,
                user_seconds=usage.ru_utime, system_seconds=usage.ru_stime,
                maximum_rss_bytes=usage.ru_maxrss)
    except BaseException as error:
        record['error'] = repr(error)
        raise
    finally:
        completed.set()
        watcher.join()
        process = child[0]
        if process is not None:
            remaining = group_exists(process.pid)
            record['remaining_process_group_before_cleanup'] = remaining
            if remaining:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if process.returncode is None:
                process.wait()
            deadline = time.monotonic() + 5
            while group_exists(process.pid) and time.monotonic() < deadline:
                time.sleep(0.01)
            record['remaining_process_group'] = group_exists(process.pid)
        record.update(timed_out=timed_out[0], finished_utc=now())
        for stream in ['stdout', 'stderr']:
            path = directory / (stream + '.bin')
            if path.is_file():
                record[stream] = dict(path=str(path), bytes=path.stat().st_size,
                    sha256=sha(path))
        atom(directory / 'process.json', record)
    return record


def success(record):
    if not (record.get('exit_code') == 0 and not record.get('timed_out')
            and not record.get('remaining_process_group_before_cleanup')
            and not record.get('remaining_process_group') and 'error' not in record):
        raise ValueError('Native attempt failed; exclusive raw evidence retained')
