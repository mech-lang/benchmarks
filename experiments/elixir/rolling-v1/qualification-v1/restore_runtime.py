"""Restore only the official pinned Elixir ZIP; verify the retained local OTP.

No global installation, package-manager change or benchmark execution. Every
external attempt has a fresh raw receipt. --prepare performs metadata reads only.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import zipfile

from native_process import atom,now,one,sha,success

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
BUILD=BASE/'.build/runtime-v1'
ELIXIR=BUILD/'elixir'
OTP=Path('/opt/homebrew/Cellar/erlang/29.1.1_2')
HIST=ROOT/'archive/languages/elixir/20261013/jobs/retained-otp-probes-v1/intake-result.json'
HIST_SHA='ad8aca223866b085ba3e823538298b948bd427748909bff1913d874d608519d0'
PLAN=HERE/'runtime-plan-v1.json'
OUTPUT=HERE/'runtime-v1'
LOCK=Path('/tmp/mech-clbg-timing.lock')
URL='https://github.com/elixir-lang/elixir/releases/download/v1.20.4/elixir-otp-29.zip'
ZIP_SHA='7863c546cda13fecc949e562e326042451dacf8fd8698a36783cb71eeb223b46'


def require(value,message):
    if not value:raise ValueError(message)


def ref(path):
    path=Path(path);return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),sha256=sha(path))


def environment():
    return dict(PATH=str(OTP/'bin')+':'+str(ELIXIR/'bin')+':/usr/bin:/bin:/usr/sbin:/sbin',
        HOME=str(BUILD/'home'),XDG_CONFIG_HOME=str(BUILD/'config'),TMPDIR=str(BUILD/'tmp')+'/',LC_ALL='C',LANG='C',
        ERL_FLAGS='',ERL_AFLAGS='',ERL_ZFLAGS='',ERL_LIBS='',ERL_COMPILER_OPTIONS='',
        ELIXIR_ERL_OPTIONS='+S 8:8 +A 1 +SDcpu 1:1 +SDio 1',ERL_CRASH_DUMP=str(BUILD/'erl-crash.dump'),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')


def make_plan():
    require(sha(HIST)==HIST_SHA,'Historical native distribution receipt changed')
    historical=json.loads(HIST.read_bytes());pins=historical['pins']
    old='/retained-otp-toolchain-v1/elixir/'
    elixir={str(ELIXIR/k.split(old,1)[1]):v for k,v in pins.items() if old in k}
    otp={k:v for k,v in pins.items() if k.startswith(str(OTP)+'/')}
    require(len(elixir)==723 and len(otp)==4243,'Historical distribution inventory changed')
    return dict(schema='elixir-rolling-runtime-restoration-plan.v1',status='PREPARED',
        controller=ref(__file__),process_helper=ref(HERE/'native_process.py'),historical_manifest=ref(HIST),
        archive=dict(url=URL,sha256=ZIP_SHA,path=str(BUILD/'elixir-otp-29.zip')),
        expected_elixir_files=elixir,expected_otp_files=otp,
        expected_version=historical['actual_version_stdout'],environment=environment(),
        common_mutex=str(LOCK),output=str(OUTPUT),quantitative_benchmark=False,chart_admission=False)


def run():
    plan=json.loads(PLAN.read_bytes());require(plan==make_plan(),'Restoration plan/controller changed')
    require(not OUTPUT.exists() and not BUILD.exists(),'Fresh restoration attempt required')
    with LOCK.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(os.fstat(lock.fileno()).st_ino==LOCK.stat().st_ino,'Common lock identity changed')
        OUTPUT.mkdir();BUILD.mkdir(parents=True)
        for name in ['home','config','tmp']:(BUILD/name).mkdir()
        report=dict(schema='elixir-rolling-runtime-restoration.v1',status='RUNNING',started_utc=now(),plan=ref(PLAN),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,attempts=[],active=None,quantitative_benchmark=False,chart_admission=False)
        def command(label,argv):
            report['active']=label;atom(OUTPUT/'report.json',report)
            row=one(argv,OUTPUT/label,plan['environment'],ROOT,lock.fileno(),timeout=180)
            report['attempts'].append(row);atom(OUTPUT/'report.json',report);success(row);return row
        try:
            archive=BUILD/'elixir-otp-29.zip'
            command('official-archive-download',['/usr/bin/curl','--fail','--location','--retry','0','--max-time','120','--output',str(archive),URL])
            require(sha(archive)==ZIP_SHA,'Official archive SHA differs')
            ELIXIR.mkdir()
            with zipfile.ZipFile(archive) as package:
                entries=package.infolist();require(len({i.filename for i in entries})==len(entries),'Duplicate ZIP entry')
                for entry in entries:
                    name=Path(entry.filename);mode=entry.external_attr>>16
                    require(not name.is_absolute() and '..' not in name.parts and not stat.S_ISLNK(mode),'Unsafe archive member')
                    target=ELIXIR/name
                    if entry.is_dir():target.mkdir(parents=True,exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(package.read(entry))
                        if mode&0o777:target.chmod(mode&0o777)
            observed_elixir={str(p):sha(p) for p in ELIXIR.rglob('*') if p.is_file()}
            require(observed_elixir==plan['expected_elixir_files'],'Elixir tree differs from exact historical723-file manifest')
            observed_otp={p:sha(p) for p in plan['expected_otp_files']}
            require(observed_otp==plan['expected_otp_files'],'Installed OTP differs from exact historical4243-file manifest')
            report.update(archive=ref(archive),archive_bytes=archive.stat().st_size,elixir_files=observed_elixir,otp_files=observed_otp)
            version=command('compiler-runtime-version',[str(ELIXIR/'bin/elixir'),'--version'])
            require(Path(version['stdout']['path']).read_text()==plan['expected_version'],'Restored native versions/configuration differ')
            require(Path(version['stderr']['path']).read_bytes()==b'','Unexpected version diagnostic')
            report.update(status='PASSED',active=None,finished_utc=now())
        except BaseException as error:
            report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:atom(OUTPUT/'report.json',report)
    print(report['status'],len(report.get('elixir_files',{})),len(report.get('otp_files',{})))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.run,'Choose one mode')
    if args.prepare:require(not PLAN.exists(),'Fresh plan required');atom(PLAN,make_plan())
    else:run()
