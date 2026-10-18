"""Build the pinned official Luau runtime and retained generic hosts."""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/luau'
REVISION = '9d7748a4f324213a18cb8283fa2a77c330225fa0'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--toolchain', type=Path, default=Path('/private/tmp/mech-luau-toolchain-0.743'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assert subprocess.check_output(['git', '-C', args.toolchain, 'rev-parse', 'HEAD'], text=True).strip() == REVISION
    assert not subprocess.check_output(['git', '-C', args.toolchain, 'status', '--porcelain'], text=True).strip()
    build = HERE / '.build/native-v1'
    report = dict(schema='luau-runtime-build.v1', status='RUNNING', release='0.743', revision=REVISION,
                  started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), commands=[],
                  sources={str(p.relative_to(ROOT)):sha(p) for p in (HERE/'source-v1').iterdir() if p.is_file()},
                  compiler_version=subprocess.check_output(['/usr/bin/clang++','--version'],text=True),
                  benchmark_samples=0)

    def save():
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')

    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['common_mutex_inode']=__import__('os').fstat(lock.fileno()).st_ino
        commands=[['/opt/homebrew/bin/cmake','-S',HERE/'source-v1','-B',build,
                   '-DCMAKE_BUILD_TYPE=Release','-DLUAU_SOURCE='+str(args.toolchain),
                   '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG -fno-fast-math -ffp-contract=off'],
                  ['/opt/homebrew/bin/cmake','--build',build,'--parallel','4','--target',
                   'luau-host','luau-regex','luau-bigint','luau-source-reader','Luau.Repl.CLI','Luau.Compile.CLI']]
        for i,command in enumerate(commands):
            command=list(map(str,command))
            with (args.output/f'{i}.stdout').open('wb') as out,(args.output/f'{i}.stderr').open('wb') as err:
                result=subprocess.run(command,stdout=out,stderr=err,timeout=900)
            report['commands'].append(dict(command=command,exit_code=result.returncode))
            save()
            if result.returncode:
                print((args.output/f'{i}.stderr').read_text()[-6000:],flush=True)
                report['status']='FAILED';save();raise SystemExit(result.returncode)
        report['artifacts']={name:dict(path=str(build/name),sha256=sha(build/name)) for name in
                             ('luau-host','luau-regex','luau-bigint','luau-source-reader','luau/luau','luau/luau-compile')}
        report['version_capture']=subprocess.check_output([build/'luau-host','--version'],text=True)
        report['dependencies']={name:dict(path=str(path),sha256=sha(path)) for name,path in
                                [('gmp',Path('/opt/homebrew/opt/gmp/lib/libgmp.a')),
                                 ('pcre2',Path('/opt/homebrew/opt/pcre2/lib/libpcre2-8.a'))]}
        report['status']='BUILT_AWAITING_CORRECTNESS'
        save()
    print(json.dumps(dict(status=report['status'],release=report['release'],artifacts=report['artifacts']),indent=2))


if __name__=='__main__':
    main()
