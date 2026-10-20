"""Restore exact retained Clojure/JDK payloads and build three isolated sources."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request

import run_serial as run

ROOT, HERE = run.ROOT, run.HERE
BUILD = HERE/'.build'
RESTORATION = HERE/'runtime-restoration.json'
SUPPORT_SHA = 'ae37ffdcbfe8d1fa34632e1151d4098b5747f71ce2ad074d326043be3d289446'


def fetch(url, destination, limit):
    run.require(not destination.exists(), 'Download already exists; preserve prior attempts')
    with urllib.request.urlopen(url, timeout=120) as response, destination.open('xb') as stream:
        total = 0
        while True:
            block = response.read(1024*1024)
            if not block: break
            total += len(block); run.require(total <= limit, 'Download exceeds declared size limit')
            stream.write(block)


def safe_extract(archive, output):
    output.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        for member in members:
            path = Path(member.name)
            run.require(not path.is_absolute() and '..' not in path.parts and not member.isdev() and not member.isfifo(), 'Unsafe JDK archive member')
            if member.issym() or member.islnk():
                target = Path(member.linkname)
                run.require(not target.is_absolute(), 'Absolute archive link')
                candidate = (output/path.parent/target) if member.issym() else (output/target)
                run.require(candidate.resolve().is_relative_to(output.resolve()), 'Archive link escapes destination')
        # Names/links are checked above; the additional data filter is available
        # in supported modern Python and rejects unsafe ownership/permissions.
        if hasattr(tarfile, 'data_filter'): stream.extractall(output, members=members, filter='data')
        else: stream.extractall(output, members=members)


def checked(record, notes=True):
    stderr=Path(record['stderr']['path']).read_bytes()
    run.require(record['exit_code']==0 and not record['timed_out'] and not record['remaining_process_group'], 'Native preparation failed; attempt retained')
    if notes: run.require(stderr in [b'',run.EXPECTED_NOTES], 'Unexpected compiler/diagnostic stderr; retain and review')


def prepare(output):
    run.require(output.is_relative_to(HERE) and not output.exists() and not BUILD.exists(), 'Use a fresh preparation directory/build tree')
    run.require(not (HERE/'runtime-build.json').exists() and not (HERE/'builds.json').exists(), 'Do not overwrite qualified receipts')
    with open(run.LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run.competition();output.mkdir(parents=True);BUILD.mkdir()
        report=dict(schema='clojure-nbody-preparation.v1',status='RUNNING',started_utc=run.now(),
            controller=run.ref(__file__),process_controller=run.ref(HERE/'run_serial.py'),restoration=run.ref(RESTORATION),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,active=None,steps=[],native_subject_timings=False,chart_admission=False)
        run.atom(output/'report.json',report)
        try:
            restoration=run.load(RESTORATION)
            for value in restoration['historical_receipts']:run.check_ref(value)
            proposal=run.load(HERE/'plan.json')
            for value in [proposal['parent']['source'],proposal['parent']['support']]+[row['source'] for row in proposal['candidates']]:run.check_ref(value)
            archive=BUILD/Path(restoration['jdk']['archive_url']).name
            report['active']='download-jdk';run.atom(output/'report.json',report)
            fetch(restoration['jdk']['archive_url'],archive,512*1024*1024)
            run.require(run.sha(archive)==restoration['jdk']['archive_sha256'],'Exact JDK archive checksum mismatch')
            safe_extract(archive,BUILD/'jdk')
            expected=restoration['jdk']['extracted_tree_sha256'];tree={}
            for relative,digest in expected.items():
                path=BUILD/'jdk'/relative
                run.require(path.is_file() and run.sha(path)==digest,'Restored JDK file differs: '+relative);tree[run.ref(path)['path']]=digest
            actual={str(path.relative_to(BUILD/'jdk')) for path in (BUILD/'jdk').rglob('*') if path.is_file()}
            run.require(actual==set(expected),'Missing or extra extracted JDK files')
            home=BUILD/'jdk'/'jdk-25.0.4.1+1'/'Contents/Home';java=home/'bin/java';env=run.environment(home)
            jars=[];(BUILD/'vendor').mkdir()
            for row in restoration['jars']:
                path=BUILD/'vendor'/(row['name']+'-'+row['version']+'.jar');fetch(row['url'],path,32*1024*1024)
                run.require(run.sha(path)==row['sha256'],'Pinned vendor JAR differs');jars.append(path);tree[run.ref(path)['path']]=row['sha256']
            identity=[]
            for name in ['java','javac','javap']:
                record=run.one([home/'bin'/name,'-version'],output/('identity-'+name),30,env,lock.fileno())
                checked(record,notes=False);identity.append(run.ref(output/('identity-'+name)/'process.json'))
                raw=Path(record['stdout']['path']).read_bytes()+Path(record['stderr']['path']).read_bytes()
                run.require(b'25.0.4.1' in raw,'Wrong actual JDK version')
            record=run.one([java,*run.FLAGS,'-XshowSettings:properties','-version'],output/'identity-properties',30,env,lock.fileno())
            checked(record,notes=False);properties=Path(record['stdout']['path']).read_text()+Path(record['stderr']['path']).read_text()
            run.require('os.arch = aarch64' in properties and 'java.runtime.version = 25.0.4.1+1' in properties,'Wrong actual platform/version')
            identity.append(run.ref(output/'identity-properties/process.json'))
            record=run.one([java,*run.FLAGS,'-cp',':'.join(map(str,jars)),'clojure.main','-e',
                '(assert (= "1.12.6" (clojure-version))) (assert (= 8 (.availableProcessors (Runtime/getRuntime)))) (println (clojure-version)) (doseq [g (java.lang.management.ManagementFactory/getGarbageCollectorMXBeans)] (println (.getName g)))'],
                output/'identity-clojure',30,env,lock.fileno());checked(record)
            identity.append(run.ref(output/'identity-clojure/process.json'))
            linked=[]
            for name,path in [('java',java),('libjvm',home/'lib/server/libjvm.dylib')]:
                for label,command in [('architecture',['/usr/bin/lipo','-archs',path]),('linked',['/usr/bin/otool','-L',path])]:
                    record=run.one(command,output/(name+'-'+label),30,env,lock.fileno());checked(record)
                    linked.append(run.ref(output/(name+'-'+label)/'process.json'))
                    if label=='architecture':run.require(Path(record['stdout']['path']).read_text().split()==['arm64'],'Expected native ARM64 image')
            runtime=dict(schema='clojure-runtime-build.v1',status='PASSED',java=run.ref(java),java_home=str(home),
                archive=run.ref(archive),jars=[run.ref(path) for path in jars],pins=tree,environment=env,flags=run.FLAGS,
                compiler_version='1.12.6',runtime_version='25.0.4.1+1',architecture='arm64',backend='JVM bytecode then HotSpot JIT',
                restoration=run.ref(RESTORATION),identity=identity,linked_image_evidence=linked,controller=run.ref(__file__),
                common_mutex_inode=os.fstat(lock.fileno()).st_ino,finished_utc=run.now())
            run.atom(HERE/'runtime-build.json',runtime)
            builds=dict(schema='clojure-nbody-builds.v1',status='RUNNING',active=None,runtime=run.ref(HERE/'runtime-build.json'),
                controller=run.ref(__file__),process_controller=run.ref(HERE/'run_serial.py'),programs={},started_utc=run.now())
            run.atom(output/'builds-progress.json',builds)
            for name in run.NAMES:
                builds['active']=name;run.atom(output/'builds-progress.json',builds)
                source=proposal['parent']['source'] if name=='parent' else next(row['source'] for row in proposal['candidates'] if row['id']==name)
                namespace='clbg.nbody.compact' if name=='parent' else next(row['namespace'] for row in proposal['candidates'] if row['id']==name)
                package=BUILD/'packages'/name;mainroot=package/'sources';supportroot=package/'support'
                target=mainroot/Path(*namespace.replace('-','_').split('.')).with_suffix('.clj');target.parent.mkdir(parents=True)
                shutil.copyfile(ROOT/source['path'],target)
                helper=supportroot/'clbg/support.clj';helper.parent.mkdir(parents=True);shutil.copyfile(ROOT/proposal['parent']['support']['path'],helper)
                run.require(run.sha(target)==source['sha256'] and run.sha(helper)==SUPPORT_SHA,'Compiled source copies differ')
                classes=BUILD/'classes'/name;classes.mkdir(parents=True)
                expression='(binding [*compile-path* '+json.dumps(str(classes))+' *compiler-options* {:direct-linking true} *warn-on-reflection* true] (compile \'clbg.support) (compile \''+namespace+'))'
                command=[java,*run.FLAGS,'-cp',':'.join(map(str,[mainroot,supportroot,*jars])),'clojure.main','-e',expression]
                record=run.one(command,output/('compile-'+name),180,env,lock.fileno());checked(record)
                class_pins={run.ref(path)['path']:run.sha(path) for path in sorted(classes.rglob('*.class'))}
                run.require(bool(class_pins),'Compiler produced no classes')
                mainclass=namespace.replace('-','_');classpath=':'.join(map(str,[classes,*jars]));evidence=[run.ref(output/('compile-'+name)/'process.json')]
                record=run.one([home/'bin/javap','-c','-p','-s','-classpath',classpath,mainclass+'$advance'],output/('javap-'+name),30,env,lock.fileno());checked(record)
                evidence.extend([run.ref(output/('javap-'+name)/'process.json'),run.ref(output/('javap-'+name)/'stdout.bin')])
                builds['programs'][name]=dict(source=source,support=proposal['parent']['support'],namespace=namespace,main_class=mainclass,
                    flags=run.FLAGS,compile_command=list(map(str,command)),compile_options=dict(direct_linking=True,warn_on_reflection=True),
                    run_argv=list(map(str,[java,*run.FLAGS,'-cp',classpath,mainclass])),classes=str(classes),class_pins=class_pins,
                    input_files=[run.ref(target),run.ref(helper)],evidence=evidence)
                builds['active']=None;run.atom(output/'builds-progress.json',builds)
            builds.update(status='PASSED',finished_utc=run.now());run.atom(HERE/'builds.json',builds)
            report.update(status='PASSED',active=None,finished_utc=run.now(),runtime=run.ref(HERE/'runtime-build.json'),builds=run.ref(HERE/'builds.json'))
        except BaseException as error:
            report.update(status='FAILED',error=repr(error),finished_utc=run.now());raise
        finally:run.atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.output.resolve())


if __name__=='__main__':main()
