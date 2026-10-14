"""Pure Scala bounded-controller tests; no JVM, runtime hashes, or plan preparation."""
import copy
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH=Path(__file__).with_name('scala_bounded.py')
SPEC=importlib.util.spec_from_file_location('tested_scala149',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


def digest(raw):return hashlib.sha256(raw).hexdigest()


class ScalaBounded(unittest.TestCase):
    def receipt_fixture(self,directory,code=0):
        command=['/synthetic/java',*m.c.FLAGS,'-cp','/synthetic/classes:/synthetic/runtime.jar','Main']
        env=m.environment(directory,command[0]);payload=b'input';parent=os.getpid()
        common=dict(kind='scala-bounded-main',command=command,environment=env,cwd=str(directory),
            started_at='2026-10-14T00:00:00+00:00',stdin_bytes=len(payload),stdin_sha256=digest(payload),
            inherited_common_mutex=True,common_mutex_inode=79859134,process_timeout_seconds=30,cleanup_timeout_seconds=5,
            maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,native_file_limit_bytes=m.kb.FILE_LIMIT,
            stdout_capture_limit_bytes=m.kb.FILE_LIMIT+m.kb.PIPE_CHUNK,stdout_transport='OS pipe, retained as received',
            stderr_transport='exclusive artifact',benchmark_samples=0,source_work_qualified=False,chart_admission=False)
        identity=dict(pid=42,pgid=42,ppid=parent,birth_seconds=100,birth_microseconds=3,status=2)
        start=dict(common,status='starting',native_process_started=False)
        active=dict(common,status='running',native_process_started=True,pid=42,pgid=42,identity=identity)
        final=dict(common,status='failed' if code else 'native-passed',native_process_started=True,pid=42,pgid=42,
            identity=identity,leader_identity_before_reap=dict(identity,status=5),direct_child_reaped=True,
            remaining_process_group=[],cleanup_errors=[],stop_signals=[],exit_status=code,
            kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=100,
            finished_at='2026-10-14T00:00:01+00:00')
        if code:final.update(error_type='AssertionError',error='Native command exited unsuccessfully',timed_out=False)
        for name,raw in (('stdout',b''),('stderr',b'rejection' if code else b'')):
            (directory/(name+'.bin')).write_bytes(raw);final[name+'_bytes']=len(raw);final[name+'_sha256']=digest(raw)
        for name,value in (('start',start),('active',active),('process',final)):(directory/(name+'.json')).write_text(json.dumps(value))
        return command,env,payload,parent,'scala-bounded-main',code

    def test_native_success_and_exact_expected_exit1_envelopes(self):
        for code in (0,1):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,code)
                receipt,stdout,stderr=m.native_receipt(directory,*args)
                self.assertEqual(receipt['exit_status'],code)
                self.assertEqual(receipt['status'],'failed' if code else 'native-passed')

    def test_exit1_unrelated_failure_timeout_signal_and_cleanup_rejected(self):
        changes=[lambda r:r.update(error='Unexpected stderr; raw bytes retained'),lambda r:r.update(error_type='RuntimeError'),
                 lambda r:r.update(exit_status=-15),lambda r:r.update(timed_out=True),lambda r:r.update(stop_signals=[9]),
                 lambda r:r.update(cleanup_errors=['failed']),lambda r:r.update(artifact_errors=['failed']),
                 lambda r:r.update(direct_child_reaped=False),lambda r:r.update(remaining_process_group=[41]),
                 lambda r:r.update(status='native-passed')]
        for change in changes:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,1);path=directory/'process.json'
                value=json.loads(path.read_bytes());change(value);path.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_missing_unowned_or_changed_birth_and_policy_rejected(self):
        changes=[('active',lambda r:r.update(native_process_started=False)),
                 ('process',lambda r:r['identity'].update(ppid=1)),
                 ('process',lambda r:r['leader_identity_before_reap'].update(birth_seconds=999)),
                 ('start',lambda r:r.update(stdin_sha256='0'*64)),('process',lambda r:r.update(exit_status=True)),
                 ('active',lambda r:r['command'].append('--other')),('process',lambda r:r.update(maximum_process_group_rss_bytes=1))]
        for name,change in changes:
            with self.subTest(name=name,change=change),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);args=self.receipt_fixture(directory,1);path=directory/(name+'.json')
                value=json.loads(path.read_bytes());change(value);path.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_raw_stream_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);args=self.receipt_fixture(directory);(directory/'stdout.bin').write_bytes(b'new')
            with self.assertRaises(AssertionError):m.native_receipt(directory,*args)

    def test_actual_corpus149_input_and_expected_pins_without_runtime_hash(self):
        pins={};schedule=m.corpus(pins)
        self.assertEqual(len(schedule),149);self.assertEqual(len({s['directory'] for s in schedule}),149)
        self.assertEqual(sum(s['case']['expected_exit']=='nonzero' for s in schedule),7)
        self.assertEqual(set(s['case']['benchmark'] for s in schedule),m.c.BENCHES)
        self.assertTrue(all(str(m.CORPUS.parent/s['case']['stdin']['path']) in pins for s in schedule))
        self.assertEqual(pins[str(m.CORPUS)],m.CORPUS_SHA)

    def test_commands_use_direct_main_and_original_argument_contract(self):
        plan={'compiled':{'java':'/synthetic/jdk/bin/java'}};profile={'runtime_classpath':'/classes:/scala3.jar:/scala.jar'}
        directory=Path('/synthetic/case')
        command,env=m.command_for(plan,profile,{'input_kind':'integer-argument','n':0},directory)
        self.assertEqual(command[-2:],['Main','0']);self.assertEqual(command[1:5],m.c.FLAGS)
        self.assertNotIn('JAVA_TOOL_OPTIONS',env);self.assertEqual(env['JAVA_HOME'],'/synthetic/jdk')
        command,_=m.command_for(plan,profile,{'input_kind':'stdin','n':0},directory)
        self.assertEqual(command[-1],'Main');self.assertNotIn('dotty.tools.dotc.Main',command)

    def test_rejection_contract_is_strict_and_does_not_promote_work(self):
        case=next(s['case'] for s in m.corpus({}) if s['case']['expected_exit']=='nonzero')
        stderr=(b'Exception in thread "main" java.lang.IllegalArgumentException: requirement failed: Invalid IUPAC byte: '
            +str(case['expected_invalid_byte']).encode()+b'\n\tat Main$.main(Main.scala:1)\n\tat Main.main(Main.scala)\n')
        value=m.check.validate(case,'scala',b'',stderr,1,None)
        self.assertTrue(value['output_contract_satisfied']);self.assertFalse(value['source_work_qualified'])
        for stdout,error,code in ((b'>r\n',stderr,1),(b'',stderr+b'extra\n',1),(b'',stderr,0),(b'',stderr,-15)):
            with self.assertRaises(ValueError):m.check.validate(case,'scala',stdout,error,code,None)

    def test_all142_success_reference_contracts(self):
        checked=0
        for slot in m.corpus({}):
            case=slot['case']
            if case['expected_exit']!=0:continue
            expected=(m.CORPUS.parent/case['expected']['path']).read_bytes()
            self.assertTrue(m.check.validate(case,'scala',expected,b'',0,expected)['output_contract_satisfied']);checked+=1
        self.assertEqual(checked,142)

    def test_missing_or_failed_future_compile_receipt_blocks_before_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);path=directory/'report.json'
            with patch.object(m.c,'PACKET',directory):
                with self.assertRaises(AssertionError):m.compiled_prerequisite(path,'0'*64,'0'*64,{})
            output=directory/'run';output.mkdir();path=output/'report.json';path.write_text('{"status":"failed"}')
            (output/'terminal.json').write_text('{}')
            with patch.object(m.c,'PACKET',directory),self.assertRaises((KeyError,AssertionError)):
                m.compiled_prerequisite(path,m.sha(path),m.sha(output/'terminal.json'),{})

    @contextmanager
    def compiled_fixture(self):
        # Entirely synthetic closed future compilation in a disposable directory.
        # Artifact headers/receipts exercise bindings, not actual Scala execution.
        with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
            root=Path(tmp).resolve();packet=root/'compiled';output=packet/'run';output.mkdir(parents=True)
            sources_path=root/'sources.json';toolchain_path=root/'toolchain.json';rows=[];profiles=[]
            java=str(root/'jdk/bin/java');javap=str(root/'jdk/bin/javap')
            libraries=[str(root/name) for name in ('scala3-library_3-3.10.0.jar','scala-library-3.10.0.jar')]
            pins={name:'0'*64 for name in (java,javap,*libraries)}
            for path,sha in ((m.COMPILE,m.COMPILE_SHA),(m.c.HELPER,m.c.HELPER_SHA),
                (Path(m.kb.__file__),m.helper.OBSERVER_SHA),(Path(m.kb.kh.__file__),m.kb.HELPER_CONTROLLER_SHA),
                (Path(m.kb.eb.__file__),m.kb.REFERENCE_CONTROLLER_SHA),(m.kb.kh.PYTHON,m.kb.kh.PYTHON_SHA)):
                pins[str(path)]=sha
            toolchain=dict(status='versions-and-readers-compiled-awaiting-parser-execution',native_processes_started=4,
                integrity_errors=[],pins=dict(pins),java=java,compiler_dependencies=libraries,compiler_classpath='/synthetic/compiler')
            toolchain_path.write_text(json.dumps(toolchain));pins[str(toolchain_path)]=m.sha(toolchain_path)
            instant=datetime(2026,10,14,tzinfo=timezone.utc)
            for index,bench in enumerate(sorted(m.c.BENCHES)):
                original='experiments/scala/source-v1/'+bench+'/Main.scala';authored=root/original
                authored.parent.mkdir(parents=True);authored.write_text('object Main { def main(args: Array[String]): Unit = () }\n')
                src=dict(path=original,role='application',bytes=authored.stat().st_size,sha256=m.sha(authored))
                rows.append(dict(id='scala-'+bench+'-jvm-v1',language='scala',variant='jvm',benchmark=bench,sources=[src]))
                directory=output/bench;directory.mkdir();source=directory/'Main.scala';source.write_bytes(authored.read_bytes())
                pins[str(authored)]=pins[str(source)]=src['sha256'];classes=directory/'classes';classes.mkdir()
                for name in ('Main.class','Main$.class'):(classes/name).write_bytes(b'\xca\xfe\xba\xbe'+b'\0'*6)
                (classes/'Main.tasty').write_bytes(b'synthetic')
                artifacts=m.c.class_inventory(classes)
                for item in artifacts:pins[item['path']]=item['sha256']
                cp=str(classes)+os.pathsep+os.pathsep.join(libraries);env=m.environment(directory,java)
                command=[java]+m.c.FLAGS+['-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
                    '-cp','/synthetic/compiler','dotty.tools.dotc.Main','-classpath',os.pathsep.join(libraries),
                    '-encoding','UTF-8','-color:never','-d',str(classes),str(source)]
                profile=dict(id=rows[-1]['id'],benchmark=bench,source=str(source),original_source=original,
                    source_sha256=src['sha256'],main_owner='Main',runtime_classpath=cp,compile_command=command,
                    artifacts=artifacts,source_work_qualified=False,chart_admission=False)
                for offset,stage in enumerate(('compile','bytecode')):
                    where=directory/stage;where.mkdir();self.receipt_fixture(where)
                    owners=[a['relative_path'][:-6] for a in artifacts if a['relative_path'].endswith('.class')]
                    argv=command if stage=='compile' else [javap,'-J-XX:ActiveProcessorCount=8','-J-Xms64m','-J-Xmx1g',
                        '-J-XX:+UseG1GC','-p','-c','-s','-l','-verbose','-classpath',cp]+owners
                    stdout=b'' if stage=='compile' else b'public static void main(java.lang.String[]);\n    descriptor: ([Ljava/lang/String;)V\n'
                    (where/'stdout.bin').write_bytes(stdout);pid=100+2*index+offset
                    started=(instant+timedelta(seconds=2*(2*index+offset))).isoformat()
                    ended=(instant+timedelta(seconds=2*(2*index+offset)+1)).isoformat()
                    for name in ('start','active','process'):
                        path=where/(name+'.json');record=json.loads(path.read_bytes())
                        record.update(command=argv,environment=env,stdin_bytes=0,stdin_sha256=digest(b''),started_at=started,
                                      kind='diagnostic-compile' if stage=='compile' else 'bytecode-inspection')
                        if name!='start':record.update(pid=pid,pgid=pid);record['identity'].update(pid=pid,pgid=pid)
                        if name=='process':
                            record['leader_identity_before_reap'].update(pid=pid,pgid=pid)
                            record.update(stdout_bytes=len(stdout),stdout_sha256=digest(stdout),finished_at=ended)
                        path.write_text(json.dumps(record))
                    profile[stage+'_process']=dict(path=str(where/'process.json'),sha256=m.sha(where/'process.json'))
                profiles.append(profile)
            sources_path.write_text(json.dumps(dict(schema='scala-source-draft-manifest-v1',programs=rows)))
            pins[str(sources_path)]=m.sha(sources_path)
            report=dict(schema='scala-ten-applications-compile-v1',status=m.COMPILED,integrity_errors=[],active=None,
                native_processes_started=20,compiler_processes_started=10,bytecode_reader_processes_started=10,
                subject_main_executions=0,benchmark_samples=0,bounded_outputs_qualified=False,source_work_qualified=False,
                full_timings_qualified=False,chart_admission=False,canonical_loc=None,formatted_loc=None,
                pins=pins,profiles=profiles,runtime_libraries=libraries,artifacts=m.inventory(output),
                started_at=instant.isoformat(),finished_at=(instant+timedelta(seconds=40)).isoformat())
            report_path=output/'report.json';report_path.write_text(json.dumps(report))
            terminal=dict(status=m.COMPILED,report_sha256=m.sha(report_path),native_processes_started=20,
                          subject_main_executions=0,benchmark_samples=0,chart_admission=False)
            terminal_path=output/'terminal.json';terminal_path.write_text(json.dumps(terminal))
            for target,name,value in ((m,'ROOT',root),(m.c,'PACKET',packet),(m.c,'SOURCES',sources_path),
                    (m.c,'SOURCES_SHA',m.sha(sources_path)),(m.c,'TOOLCHAIN',toolchain_path),
                    (m.c,'TOOLCHAIN_SHA',m.sha(toolchain_path))):stack.enter_context(patch.object(target,name,value))
            yield report_path,terminal_path,report,terminal

    def test_synthetic_closed10_profiles_and20_receipts_admit_only_prerequisite(self):
        with self.compiled_fixture() as (path,terminal,report,_):
            pins={};value=m.compiled_prerequisite(path,m.sha(path),m.sha(terminal),pins)
            self.assertEqual(len(value['profiles']),10);self.assertEqual(len(value['runtime_libraries']),2)
            self.assertEqual(value['report_sha256'],m.sha(path));self.assertEqual(value['artifacts'],report['artifacts'])
            self.assertTrue(all(x['main_owner']=='Main' for x in value['profiles']))

    def test_changed_class_pin_entrypoint_command_or_compile_count_rejected(self):
        changes=[lambda r:r['pins'].pop(r['profiles'][0]['artifacts'][0]['path']),
                 lambda r:r['profiles'][0].update(main_owner='Other'),
                 lambda r:r['profiles'][0]['compile_command'].append('-unchecked'),
                 lambda r:r.update(compiler_processes_started=9)]
        for change in changes:
            with self.subTest(change=change),self.compiled_fixture() as (path,terminal,report,end):
                change(report);path.write_text(json.dumps(report));end['report_sha256']=m.sha(path);terminal.write_text(json.dumps(end))
                with self.assertRaises(AssertionError):m.compiled_prerequisite(path,m.sha(path),m.sha(terminal),{})

    def test_compiled_native_artifact_late_mutation_rejected(self):
        with self.compiled_fixture() as (path,terminal,report,_):
            artifact=Path(report['profiles'][0]['artifacts'][0]['path']);artifact.write_bytes(artifact.read_bytes()+b'changed')
            with self.assertRaises(AssertionError):m.compiled_prerequisite(path,m.sha(path),m.sha(terminal),{})

    def test_additional_compiled_process_receipt_rejected_even_if_report_binds_it(self):
        with self.compiled_fixture() as (path,terminal,report,end):
            extra=path.parent/'extra';extra.mkdir();(extra/'process.json').write_text('{}')
            report['artifacts']=m.inventory(path.parent,('report.json','terminal.json'));path.write_text(json.dumps(report))
            end['report_sha256']=m.sha(path);terminal.write_text(json.dumps(end))
            with self.assertRaisesRegex(AssertionError,'process receipt inventory'):
                m.compiled_prerequisite(path,m.sha(path),m.sha(terminal),{})

    def final_fixture(self,directory):
        output=directory/'bounded';output.mkdir();compiled=directory/'compiled';compiled.mkdir()
        prerequisite=directory/'pin';prerequisite.write_text('retained')
        stage=output/'001-one';stage.mkdir()
        receipt=dict(pid=42,pgid=42,native_process_started=True,direct_child_reaped=True,remaining_process_group=[],cleanup_errors=[])
        (stage/'process.json').write_text(json.dumps(receipt));(stage/'terminal.json').write_text('{}')
        report=dict(status='failed',native_processes_started=1,registered_commands=[dict(slot=1,directory=stage.name,pid=42)],
            qualified_cases=1,cases=[],successful_cases=1,rejected_cases=0,bounded_outputs_qualified=False,
            validated_case_artifacts={stage.name:m.inventory(stage)})
        plan=dict(schedule=[dict(slot=1,directory=stage.name)],compiled=dict(report=str(compiled/'report.json'),artifacts={}))
        return report,plan,output,{str(prerequisite):m.sha(prerequisite)}

    def test_final_closure_retains_partial_failure_without_rewriting_receipt(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'),patch.object(m.kb.kh,'verify_lock'):
            report,plan,output,pins=self.final_fixture(Path(tmp));before=(output/'001-one/process.json').read_bytes()
            m.finish(report,plan,output,pins,object());terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed');self.assertFalse(terminal['bounded_outputs_qualified'])
            self.assertEqual(terminal['integrity_errors'],[]);self.assertEqual(before,(output/'001-one/process.json').read_bytes())
            self.assertIn('001-one/terminal.json',terminal['available_evidence'])

    def test_snapshot_late_mutation_and_pin_change_fail_closed(self):
        for fault in ('stage-before','stage-during','pin-after'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'),patch.object(m.kb.kh,'verify_lock'):
                report,plan,output,pins=self.final_fixture(Path(tmp));path=output/'001-one/terminal.json'
                if fault=='stage-before':path.write_text('{"changed":true}')
                original=m.inventory;calls=0
                def inject(directory,exclude=()):
                    nonlocal calls
                    value=original(directory,exclude);calls+=1
                    if fault=='stage-during' and calls==1:path.write_text('{"changed":true}')
                    if fault=='pin-after' and calls==2:Path(next(iter(pins))).write_text('changed')
                    return value
                with patch.object(m,'inventory',side_effect=inject):m.finish(report,plan,output,pins,object())
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertTrue(terminal['integrity_errors'])

    def test_unreaped_native_or_changed_mutex_cannot_claim_success(self):
        for fault in ('unreaped','mutex'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp,patch.object(m,'execution_inputs'):
                report,plan,output,pins=self.final_fixture(Path(tmp))
                if fault=='unreaped':
                    path=output/'001-one/process.json';r=json.loads(path.read_bytes());r['direct_child_reaped']=False;path.write_text(json.dumps(r))
                with patch.object(m.kb.kh,'verify_lock',side_effect=AssertionError('wrong mutex') if fault=='mutex' else None):
                    m.finish(report,plan,output,pins,object())
                terminal=json.loads((output/'terminal.json').read_bytes());self.assertEqual(terminal['status'],'failed-integrity')
                if fault=='mutex':self.assertFalse(terminal['common_mutex_held'])

    def test_fifo_and_symlink_artifacts_rejected_without_opening(self):
        for kind in ('fifo','symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                output=Path(tmp);path=output/'unexpected'
                if kind=='fifo':os.mkfifo(path)
                else:path.symlink_to(output)
                with self.assertRaises(AssertionError):m.inventory(output)

    def test_plan_pin_conflicts_and_nonphysical_paths_rejected(self):
        with self.assertRaises(AssertionError):m.bind({},'relative','0'*64)
        pins={};m.bind(pins,'/synthetic/one','0'*64)
        with self.assertRaises(AssertionError):m.bind(pins,'/synthetic/one','1'*64)
        with self.assertRaises(AssertionError):m.bind(pins,'/synthetic/two','bad')

    def test_signals_enter_owned_supervisor_cleanup(self):
        handlers={}
        def run(args):
            self.assertEqual(set(handlers),m.kb.kh.SIGNALS)
            for sig,handler in handlers.items():
                with self.assertRaises(KeyboardInterrupt):handler(sig,None)
            return 19
        with patch.object(m.sys,'argv',['stage','run','--plan','/synthetic/plan','--plan-sha256','0'*64]),\
             patch.object(m.signal,'signal',side_effect=lambda sig,handler:handlers.__setitem__(sig,handler)),\
             patch.object(m,'run',side_effect=run):self.assertEqual(m.main(),19)


if __name__=='__main__':unittest.main()
