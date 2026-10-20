"""Isolated compact typed-aset builds; inspect real generated code before performance claims."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil

import run_serial as run

ROOT,HERE=run.ROOT,run.HERE
SUPPORT_WARNING=b"Reflection warning, clbg/support.clj:19:16 - reference to field get can't be resolved.\n"
TOOL_NOTES=b'Picked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \n'


def check(record,compiler=False):
    err=Path(record['stderr']['path']).read_bytes()
    allowed=[b'',run.EXPECTED_NOTES,TOOL_NOTES]
    if compiler:allowed+=[SUPPORT_WARNING,run.EXPECTED_NOTES+SUPPORT_WARNING]
    run.require(record['exit_code']==0 and not record['timed_out'] and not record['remaining_process_group'] and err in allowed,
        'Build/diagnostic failed or has an unreviewed warning; preserve attempt')


def build(output):
    run.require(output.is_relative_to(HERE) and not output.exists() and not (HERE/'builds.json').exists(),'Use fresh output; do not overwrite admitted build receipt')
    with open(run.LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run.competition();output.mkdir(parents=True)
        runtime=run.load(HERE/'runtime-build.json');proposal=run.load(HERE/'plan.json')
        run.check_ref(proposal['runtime']['copy']);run.check_ref(proposal['runtime']['receipt'])
        run.require(proposal['runtime']['copy']['sha256']==proposal['runtime']['receipt']['sha256'],
            'Runtime receipt copy differs from the retained exact toolchain')
        controllers=output/'controllers';controllers.mkdir()
        for name in ['build_candidates.py','run_serial.py']:
            shutil.copyfile(HERE/name,controllers/name)
        run.require(runtime['status']=='PASSED','Verified restored runtime required')
        for path,digest in runtime['pins'].items():run.check_ref(dict(path=path,sha256=digest))
        java=ROOT/runtime['java']['path'];home=Path(runtime['java_home']);jars=[ROOT/row['path'] for row in runtime['jars']];env=runtime['environment']
        report=dict(schema='clojure-nbody-builds.v1',status='RUNNING',active=None,runtime=run.ref(HERE/'runtime-build.json'),
            controller=run.ref(__file__),process_controller=run.ref(HERE/'run_serial.py'),programs={},started_utc=run.now(),
            common_mutex_inode=os.fstat(lock.fileno()).st_ino,
            inherited_runtime=proposal['runtime']['receipt'], proposal=run.ref(HERE/'plan.json'),
            accepted_warning=dict(text=SUPPORT_WARNING.decode(),scope='Byte-identical generic support jobs helper, unused by n-body; no application warning accepted.'))
        run.atom(output/'report.json',report)
        try:
            for name in run.NAMES:
                report['active']=name;run.atom(output/'report.json',report)
                descriptor=next(row for row in proposal['programs'] if row['id']==name)
                source=descriptor['source']; namespace=descriptor['namespace']
                run.check_ref(source);run.check_ref(proposal['parent']['support'])
                package=HERE/'.build'/('packages-'+output.name)/name;mainroot=package/'sources';supportroot=package/'support'
                target=mainroot/Path(*namespace.replace('-','_').split('.')).with_suffix('.clj');target.parent.mkdir(parents=True)
                shutil.copyfile(ROOT/source['path'],target)
                helper=supportroot/'clbg/support.clj';helper.parent.mkdir(parents=True);shutil.copyfile(ROOT/proposal['parent']['support']['path'],helper)
                run.require(run.sha(target)==source['sha256'] and run.sha(helper)==proposal['parent']['support']['sha256'],'Source copy differs')
                classes=HERE/'.build'/('classes-'+output.name)/name;classes.mkdir(parents=True)
                expression='(binding [*compile-path* '+json.dumps(str(classes))+' *compiler-options* {:direct-linking true} *warn-on-reflection* true] (compile \'clbg.support) (compile \''+namespace+'))'
                command=[java,*run.FLAGS,'-cp',':'.join(map(str,[mainroot,supportroot,*jars])),'clojure.main','-e',expression]
                record=run.one(command,output/('compile-'+name),180,env,lock.fileno());check(record,compiler=True)
                class_pins={run.ref(path)['path']:run.sha(path) for path in sorted(classes.rglob('*.class'))};run.require(bool(class_pins),'Missing class files')
                mainclass=namespace.replace('-','_');classpath=':'.join(map(str,[classes,*jars]));evidence=[run.ref(output/('compile-'+name)/'process.json'),run.ref(output/('compile-'+name)/'stderr.bin'),run.ref(output/('compile-'+name)/'stdout.bin'),
                    run.ref(controllers/'build_candidates.py'),run.ref(controllers/'run_serial.py')]
                for method,suffix in [('advance','$advance'),('momentum','$offset_momentum')]:
                    diagnostic=output/('javap-'+method+'-'+name)
                    record=run.one([home/'bin/javap','-c','-p','-s','-classpath',classpath,mainclass+suffix],diagnostic,30,env,lock.fileno());check(record)
                    evidence.extend([run.ref(diagnostic/'process.json'),run.ref(diagnostic/'stdout.bin')])
                report['programs'][name]=dict(source=source,support=proposal['parent']['support'],namespace=namespace,main_class=mainclass,
                    flags=run.FLAGS,compile_command=list(map(str,command)),compile_options=dict(direct_linking=True,warn_on_reflection=True),
                    run_argv=list(map(str,[java,*run.FLAGS,'-cp',classpath,mainclass])),classes=str(classes),class_pins=class_pins,
                    input_files=[run.ref(target),run.ref(helper)],evidence=evidence)
                report['active']=None;run.atom(output/'report.json',report)
            report.update(status='PASSED',finished_utc=run.now());run.atom(HERE/'builds.json',report)
        except BaseException as error:
            report.update(status='FAILED',error=repr(error),finished_utc=run.now());raise
        finally:run.atom(output/'report.json',report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();build(args.output.resolve())
