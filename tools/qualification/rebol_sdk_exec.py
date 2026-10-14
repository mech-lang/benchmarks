"""Exact SDK generator exec with recorded cwd and inherited common lock."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--common-fd',type=int,required=True)
    args=parser.parse_args()
    assert sha(args.plan)==args.plan_sha256
    plan=json.loads(args.plan.read_bytes())
    assert plan['schema']=='rebol-retained-spec-sdk-generation-v1'
    held,named=os.fstat(args.common_fd),Path('/tmp/mech-clbg-timing.lock').stat()
    assert (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino) and held.st_ino==79859134
    fcntl.flock(args.common_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for path,expected in plan['pins'].items():assert sha(path)==expected,('Changed SDK input',path)
    copy=Path(plan['source_copy'])
    assert not any(p.is_symlink() for p in copy.rglob('*'))
    assert {str(p) for p in copy.rglob('*') if p.is_file()}==set(plan['initial_copy_pins'])
    expected=[plan['runtime'],'-q','-s',plan['generator_wrapper'],plan['raw_spec'],plan['source_copy'],plan['output']]
    assert plan['command']==expected
    assert Path(plan['source_copy']).is_dir() and Path(plan['output']).is_dir()
    os.chdir(Path(plan['source_copy'])/'make')
    with (Path(plan['output'])/'generator-startup.json').open('x') as stream:
        json.dump(dict(pid=os.getpid(),actual_cwd=str(Path.cwd()),command=expected,
            inherited_common_mutex=True,common_mutex_inode=held.st_ino,
            kernel_image_after_exec_independently_observed=False),stream,indent=2)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.set_inheritable(args.common_fd,True)
    os.execv(plan['runtime'],expected)


if __name__=='__main__':main()
