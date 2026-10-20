"""Restore the exact retained official SWI10.0.2 private ARM64 application."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import urllib.request
from native_process import atom,now,one,sha,success

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PACKET=HERE.parent
CONFIG=ROOT/'archive/languages/prolog/20261013/runtime-qualified/success-halt-v1/runtime-config.json'
URL='https://www.swi-prolog.org/download/stable/bin/swipl-10.0.2-1.fat.dmg'
ARCHIVE_SHA='bf775f0b8d7880f4908dee513316013ef42a73793be392814fde2a0a8e9ddc5d'
ARCHIVE_BYTES=34301763
BINARY_SHA='554814b1da7c0c30595adafb758145e42a6134c696b47c8870d359008246443e'
LOCK='/tmp/mech-clbg-timing.lock'


def require(condition,message):
    if not condition:raise ValueError(message)


def ref(path):
    p=Path(path).resolve();return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def safe_tree(root):
    root=root.resolve()
    for path in root.rglob('*'):
        require(path.resolve().is_relative_to(root),'Escaping application entry: '+str(path))
        require(path.is_file() or path.is_dir(),'Unsupported or dangling application entry: '+str(path))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    require(output.is_relative_to(PACKET/'.build') and not output.exists(),'Exclusive private .build output required')
    environment=dict(PATH='/usr/bin:/bin',LC_ALL='C',LANG='C',TZ='UTC')
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir(parents=True)
        report=dict(schema='prolog-spectral-runtime-restoration.v1',status='RUNNING',started_utc=now(),
            controller=ref(__file__),process_helper=ref(HERE/'native_process.py'),historical_config=ref(CONFIG),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,quantitative_benchmark=False,attempts=[],active=None)
        atom(output/'report.json',report)
        mount=output/'mount';mount.mkdir();mounted=False
        try:
            archive=output/'swipl-10.0.2-1.fat.dmg'
            report['active']='download';atom(output/'report.json',report)
            with urllib.request.urlopen(URL,timeout=60) as incoming,archive.open('xb') as outgoing:
                shutil.copyfileobj(incoming,outgoing)
            require(archive.stat().st_size==ARCHIVE_BYTES and sha(archive)==ARCHIVE_SHA,'Official archive bytes differ')
            report['archive']=dict(url=URL,**ref(archive),bytes=ARCHIVE_BYTES)
            report['active']='readonly-attach';atom(output/'report.json',report)
            row=one(['/usr/bin/hdiutil','attach','-readonly','-nobrowse','-noautoopen','-mountpoint',str(mount),'-plist',str(archive)],
                output/'commands/attach',environment,ROOT,lock.fileno());report['attempts'].append(row);success(row)
            convert=one(['/usr/bin/plutil','-convert','json','-o','-',str(output/'commands/attach/stdout.bin')],output/'commands/mount-plist-json',environment,ROOT,lock.fileno());report['attempts'].append(convert);success(convert)
            inventory=json.loads((output/'commands/mount-plist-json/stdout.bin').read_bytes())
            entities=inventory['system-entities'];observed=[e for e in entities if 'mount-point' in e]
            require(len(observed)==1 and Path(observed[0]['mount-point']).resolve()==mount and os.path.ismount(mount),'Unexpected owned mount inventory')
            mounted=True;report['mount_inventory']=inventory
            apps=[p for p in mount.glob('*.app') if p.is_dir() and not p.is_symlink()]
            require(len(apps)==1,'Ambiguous application layout');safe_tree(apps[0])
            original=output/'original-app'/apps[0].name;original.parent.mkdir();shutil.copytree(apps[0],original,symlinks=True)
            app=output/'arm64-app'/apps[0].name;app.parent.mkdir();shutil.copytree(original,app,symlinks=True);safe_tree(app)
            config=json.loads(CONFIG.read_text());marker='/arm64-app/SWI-Prolog.app/'
            expected={p.split(marker,1)[1]:digest for p,digest in config['pins'].items() if marker in p}
            require(len(expected)==2799,'Historical ARM64 file inventory differs')
            binary=app/'Contents/MacOS/swipl';fat_binary=original/'Contents/MacOS/swipl'
            mode=binary.stat().st_mode;binary.unlink()
            report['active']='historical-arm64-slice';atom(output/'report.json',report)
            row=one(['/usr/bin/lipo',str(fat_binary),'-thin','arm64','-output',str(binary)],output/'commands/slice',environment,ROOT,lock.fileno())
            report['attempts'].append(row);success(row);binary.chmod(mode)
            actual={str(p.relative_to(app)):sha(p) for p in app.rglob('*') if p.is_file()}
            require(actual==expected,'Restored whole application differs from2799 historical file pins')
            require(sha(binary)==BINARY_SHA,'Retained executable differs')
            home=app/str(config['home']).split('/SWI-Prolog.app/',1)[1]
            require(home.is_dir(),'Historical home mapping differs');environment['SWI_HOME_DIR']=str(home)
            report.update(binary=ref(binary),home=str(home),environment=environment,pins={str((app/p).relative_to(ROOT)):d for p,d in actual.items()},
                historical_file_count=len(expected),whole_tree_exact=True,active='version')
            atom(output/'report.json',report)
            row=one([str(binary),'--version'],output/'commands/version',environment,ROOT,lock.fileno());report['attempts'].append(row);success(row)
            require(row['stdout']['sha256']=='17f679c59f5980232090f30158ce6caef61e950a0e5946d48d53e4f8887ec4be' and row['stderr']['bytes']==0,'Exact historical version output differs')
            row=one(['/usr/bin/otool','-L',str(binary)],output/'commands/linked-images',environment,ROOT,lock.fileno());report['attempts'].append(row);success(row)
            report.update(status='PASSED',active=None,finished_utc=now())
        except BaseException as error:
            report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally:
            mounted=mounted or os.path.ismount(mount)
            if mounted:
                try:
                    row=one(['/usr/bin/hdiutil','detach',str(mount)],output/'commands/detach',environment,ROOT,lock.fileno());report['attempts'].append(row);success(row)
                    require(not os.path.ismount(mount),'Owned mount remains');report['owned_mount_detached']=True
                except BaseException as error:
                    report.update(status='FAILED',detach_error=repr(error));raise
                finally:atom(output/'report.json',report)
            else:atom(output/'report.json',report)
        print(json.dumps(dict(status=report['status'],report=ref(output/'report.json'),whole_tree_exact=report['whole_tree_exact'])))


if __name__=='__main__':main()
