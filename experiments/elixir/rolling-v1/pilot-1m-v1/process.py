"""Complete-process pilot capture derived from the exact untimed native observer."""
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
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atom(path, value):
    path=Path(path); temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n'); temporary.replace(path)


def one(command,directory,environment,cwd,lock_fd,timeout=120,stdin=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    record=dict(command=list(map(str,command)),cwd=str(cwd),environment=environment,
        started_utc=now(),stdin=str(stdin) if stdin is not None else '/dev/null',quantitative_benchmark=True,
        common_mutex_inherited=True,common_mutex_inode=os.fstat(lock_fd).st_ino)
    atom(directory/'active.json',record)
    completed=threading.Event(); timed_out=[False]; child=[None]
    def watchdog():
        if not completed.wait(timeout):
            timed_out[0]=True
            if child[0] is not None:
                try:os.killpg(child[0],signal.SIGKILL)
                except ProcessLookupError:pass
    watcher=threading.Thread(target=watchdog,daemon=True);watcher.start()
    try:
        with open(stdin if stdin is not None else '/dev/null','rb') as inp,(directory/'stdout.bin').open('xb') as out,(directory/'stderr.bin').open('xb') as err:
            started=time.perf_counter_ns()
            process=subprocess.Popen(command,stdin=inp,stdout=out,stderr=err,cwd=cwd,env=environment,
                start_new_session=True,pass_fds=(lock_fd,))
            child[0]=process.pid
            pid,status,usage=os.wait4(process.pid,0)
            process.returncode=os.waitstatus_to_exitcode(status)
            record.update(pid=pid,exit_code=process.returncode,elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
                user_seconds=usage.ru_utime,system_seconds=usage.ru_stime,maximum_rss_bytes=usage.ru_maxrss)
            try:os.killpg(pid,0);remaining=True
            except ProcessLookupError:remaining=False
            if remaining:
                os.killpg(pid,signal.SIGKILL)
            record['remaining_process_group']=remaining
    except BaseException as error:
        record['error']=repr(error)
        if child[0] is not None:
            try:os.killpg(child[0],signal.SIGKILL)
            except ProcessLookupError:pass
        raise
    finally:
        completed.set();watcher.join();record.update(timed_out=timed_out[0],finished_utc=now())
        for stream in ['stdout','stderr']:
            p=directory/(stream+'.bin')
            if p.is_file():record[stream]=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
        atom(directory/'process.json',record)
    return record


def success(record):
    if not(record.get('exit_code')==0 and not record.get('timed_out') and not record.get('remaining_process_group') and 'error' not in record):
        raise ValueError('Native process failed; raw attempt retained: '+repr(record.get('command')))
