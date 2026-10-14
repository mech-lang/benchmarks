"""Small source/synthetic checks. No LLVM, Julia, preparation or runtime hashes."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('julia_native_inspection.py')
S=importlib.util.spec_from_file_location('julia_offline_tested',P)
m=importlib.util.module_from_spec(S);S.loader.exec_module(m)


def command(code,name):
    prefix=24 if code in (0xc,0x80000018,0x8000001f,0x20,0x80000023) else 12
    raw=name.encode()+b'\0';length=(prefix+len(raw)+7)//8*8
    return struct.pack('<III',code,length,prefix)+b'\0'*(prefix-12)+raw+b'\0'*(length-prefix-len(raw))


def image(path,imports=(),rpaths=(),filetype=6):
    commands=b''.join(command(0xc,n) for n in imports)+b''.join(command(0x8000001c,n) for n in rpaths)
    if not commands: commands=struct.pack('<II',0x1b,24)+b'\0'*16
    count=len(imports)+len(rpaths) or 1
    path.write_bytes(struct.pack('<8I',0xfeedfacf,0x0100000c,0,filetype,count,len(commands),0,0)+commands)
    path.chmod(0o700)


def receipt(directory,slot,pid=42):
    directory.mkdir(exist_ok=True)
    start=dict(status='starting',kind=m.KIND,command=slot['command'],environment=m.environment(directory),cwd=str(directory),
        started_at='2026-10-14T00:00:00+00:00',process_timeout_seconds=30,cleanup_timeout_seconds=5,
        inherited_common_mutex=True,common_mutex_inode=79859134,native_process_started=False,
        stop_signals=[],cleanup_errors=[],benchmark_samples=0,stdin_bytes=0,stdin_sha256=m.EMPTY_SHA,
        observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0,maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,
        native_file_limit_bytes=m.FILE_LIMIT,stdout_capture_limit_bytes=m.FILE_LIMIT+m.kb.PIPE_CHUNK,
        stdout_transport='OS pipe, retained as received',stderr_transport='exclusive artifact',
        source_work_qualified=False,chart_admission=False)
    identity=dict(pid=pid,pgid=pid,ppid=os.getpid(),birth_seconds=123,birth_microseconds=456,status=2)
    active=dict(start,status='running',pid=pid,pgid=pid,native_process_started=True,identity=identity)
    final=dict(active,status='native-passed',leader_identity_before_reap=dict(identity,status=5),
        remaining_process_group=[],exit_status=0,direct_child_reaped=True,kernel_monitor_samples=1,
        observed_peak_process_group_rss_bytes=1024,finished_at='2026-10-14T00:00:01+00:00')
    for name,raw in [('stdout',b'actual offline fixture\n'),('stderr',b'')]:
        (directory/(name+'.bin')).write_bytes(raw)
        final[name+'_bytes']=len(raw);final[name+'_sha256']=hashlib.sha256(raw).hexdigest()
    for name,rec in [('start',start),('active',active),('process',final)]:
        (directory/(name+'.json')).write_text(json.dumps(rec))
    return final


class DraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft=json.loads(m.DRAFT.read_bytes())
        cls.records={name:json.loads(Path(ref['path']).read_bytes()) for name,ref in cls.draft['source_records'].items()
                     if ref['path'].endswith('.json')}

    def test_actual_recorded_eleven_bindings_without_native_or_hashing(self):
        with patch.object(m,'sha',side_effect=AssertionError('No artifact hashing in metadata check')):
            self.assertEqual(len(m.validate_draft(self.draft,self.records)),11)
        self.assertEqual(hashlib.sha256(m.DRAFT.read_bytes()).hexdigest(),m.DRAFT_SHA)

    def test_changed_artifact_or_command_rejected(self):
        for change in ('artifact','argv','order'):
            draft=copy.deepcopy(self.draft)
            if change=='artifact':draft['commands'][0]['artifact_input']['sha256']='0'*64
            elif change=='argv':draft['commands'][0]['argv'][-1]='/tmp/file'
            else:draft['commands'].reverse()
            with self.assertRaises(AssertionError):m.validate_draft(draft,self.records)

    def test_prior_admission_not_invented(self):
        records=copy.deepcopy(self.records);records['link_result']['runtime_aot_proven']=True
        with self.assertRaises(AssertionError):m.validate_draft(self.draft,records)

    def test_observer_policy_and_environment(self):
        self.assertEqual((m.kb.TIMEOUT,m.kb.CLEANUP_TIMEOUT,m.kb.RSS_LIMIT,m.kb.FILE_LIMIT),(30,5,2*1024**3,64*1024**2))
        env=m.environment(Path('/private/tmp/fixture'))
        self.assertFalse(any(k.startswith(('DYLD_','JULIA_')) for k in env))
        self.assertEqual(env['HOME'],'/private/tmp/fixture/home')


class MachOTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()

    def test_recursive_loader_rpath_and_os_boundary(self):
        (self.root/'bin').mkdir();(self.root/'lib').mkdir()
        executable=self.root/'bin/llvm-dis';lib=self.root/'lib/libtest.dylib';dep=self.root/'lib/second.dylib'
        image(executable,['@rpath/libtest.dylib'],['@loader_path/../lib'],2)
        image(lib,['@loader_path/second.dylib','/usr/lib/libSystem.B.dylib'])
        image(dep,['/usr/lib/libc++.1.dylib'])
        pins={};closure=m.tool_closure([executable],pins)
        self.assertEqual(set(closure['images']),{str(p) for p in (executable,lib,dep)})
        self.assertEqual(closure['os_managed_install_names'],['/usr/lib/libSystem.B.dylib','/usr/lib/libc++.1.dylib'])
        self.assertFalse(closure['actual_loaded_images_observed'])
        self.assertEqual(set(pins),{str(p) for p in (executable,lib,dep)})

    def test_missing_or_ambiguous_dependency_fails(self):
        executable=self.root/'tool'
        image(executable,['@rpath/missing.dylib'],['@loader_path'],2)
        with self.assertRaises(AssertionError):m.tool_closure([executable],{})
        for name in ('a','b'):
            (self.root/name).mkdir();image(self.root/name/'same.dylib')
        image(executable,['@rpath/same.dylib'],['@loader_path/a','@loader_path/b'],2)
        with self.assertRaises(AssertionError):m.tool_closure([executable],{})

    def test_rpath_escape_is_not_an_os_image(self):
        executable=self.root/'tool';dependency=self.root/'escaped.dylib'
        image(dependency)
        image(executable,['@rpath/../..'+str(dependency)],['/usr/lib'],2)
        pins={};closure=m.tool_closure([executable],pins)
        self.assertIn(str(dependency),closure['images'])
        self.assertIn(str(dependency),pins)
        self.assertEqual(closure['os_managed_install_names'],[])

    def test_universal_arm64_selection(self):
        thin=self.root/'thin';image(thin,['/usr/lib/libSystem.B.dylib'])
        raw=thin.read_bytes();fat=self.root/'fat';offset=64
        fat.write_bytes(struct.pack('>II',0xcafebabe,1)+struct.pack('>IIIII',0x0100000c,0,offset,len(raw),3)
                        +b'\0'*(offset-28)+raw)
        parsed=m.macho(fat)
        self.assertEqual(parsed['slice_offset'],offset)
        self.assertEqual(parsed['imports'][0]['install_name'],'/usr/lib/libSystem.B.dylib')

    def test_new_earlier_rpath_candidate_is_rejected(self):
        for name in ('early','late'):(self.root/name).mkdir()
        executable=self.root/'tool';library=self.root/'late/lib.dylib';image(library)
        image(executable,['@rpath/lib.dylib'],['@loader_path/early','@loader_path/late'],2)
        pins={};closure=m.tool_closure([executable],pins)
        missing=self.root/'early/lib.dylib'
        self.assertEqual(closure['unavailable_candidates'],[str(missing)])
        resolutions={n:str(Path(n).resolve()) for n in pins}
        m.verify(pins,resolutions,closure['unavailable_candidates'])
        image(missing)
        with self.assertRaises(AssertionError):m.verify(pins,resolutions,closure['unavailable_candidates'])

    def test_non_os_alias_into_os_boundary_rejected(self):
        os_root=self.root/'mock-system';os_root.mkdir()
        library=os_root/'lib.dylib';image(library)
        alias=self.root/'alias.dylib';alias.symlink_to(library)
        executable=self.root/'tool';image(executable,[str(alias)],filetype=2)
        with patch.object(m,'os_image',lambda name:name.startswith(str(os_root)+'/')):
            with self.assertRaisesRegex(AssertionError,'Non-OS loader alias'):
                m.tool_closure([executable],{})

    def test_bad_header_and_embedded_environment(self):
        path=self.root/'bad';path.write_bytes(b'not macho')
        with self.assertRaises(AssertionError):m.macho(path)
        raw=command(0x27,'DYLD_INSERT_LIBRARIES=/tmp/evil')
        path.write_bytes(struct.pack('<8I',0xfeedfacf,0x0100000c,0,2,1,len(raw),0,0)+raw)
        with self.assertRaises(AssertionError):m.macho(path)

    def test_dependency_symlink_retarget_rejected(self):
        a=self.root/'a';b=self.root/'b';image(a);image(b)
        alias=self.root/'alias';alias.symlink_to(a)
        pins={};m.pin(pins,alias);resolutions={str(alias):str(a)}
        alias.unlink();alias.symlink_to(b)
        with self.assertRaises(AssertionError):m.verify(pins,resolutions)

    def test_named_command_extent_rejected(self):
        path=self.root/'bad';raw=struct.pack('<III',0xc,24,24)+b'\0'*12
        path.write_bytes(struct.pack('<8I',0xfeedfacf,0x0100000c,0,2,1,len(raw),0,0)+raw)
        with self.assertRaises(AssertionError):m.macho(path)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.slot=dict(id='decode-00',directory='00-decode-00',command=['/llvm-dis','/artifact.bc','-o','-'])
        self.directory=self.root/self.slot['directory'];self.record=receipt(self.directory,self.slot)

    def test_exact_closed_capture(self):
        capture,snapshot=m.checked_capture(self.slot,self.directory,os.getpid())
        self.assertEqual(capture['pid'],42);self.assertEqual(len(snapshot),5)
        self.assertTrue(all(capture[k] is False for k in m.FALSE_GATES))

    def test_output_mutation_and_extra_artifacts(self):
        (self.directory/'stdout.bin').write_bytes(b'changed')
        with self.assertRaises(AssertionError):m.checked_capture(self.slot,self.directory,os.getpid())
        receipt(self.directory,self.slot);(self.directory/'extra').write_bytes(b'x')
        with self.assertRaises(AssertionError):m.checked_capture(self.slot,self.directory,os.getpid())

    def test_unreaped_wrong_parent_or_signal_rejected(self):
        for key,value in [('direct_child_reaped',False),('remaining_process_group',[{'pid':99}]),
                          ('stop_signals',[9]),('exit_status',1),('exit_status',False),('stdout_transport','unknown')]:
            record=dict(self.record);record[key]=value
            (self.directory/'process.json').write_text(json.dumps(record))
            with self.assertRaises(AssertionError):m.checked_capture(self.slot,self.directory,os.getpid())
        receipt(self.directory,self.slot)
        with self.assertRaises(AssertionError):m.checked_capture(self.slot,self.directory,os.getpid()+1)

    def test_symlink_inventory_rejected(self):
        (self.directory/'link').symlink_to(self.directory/'stdout.bin')
        with self.assertRaises(AssertionError):m.inventory(self.directory)

    def report(self):
        capture,snapshot=m.checked_capture(self.slot,self.directory,os.getpid())
        return dict(status='failed',attempted_commands=[self.slot['directory']],native_processes_started=1,
            registered_commands=[dict(directory=self.slot['directory'],pid=42)],captures=[capture],
            validated_artifacts={self.slot['directory']:snapshot},active=None)

    def test_failed_partial_stage_closes_without_promotion(self):
        report=self.report()
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,dict(schedule=[self.slot]),self.root,{}, {},object())
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],'failed');self.assertEqual(terminal['integrity_errors'],[])
        self.assertTrue(all(terminal[k] is False for k in m.FALSE_GATES))

    def test_incomplete_success_rejected(self):
        report=self.report();report['status']=m.SUCCESS
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,dict(schedule=[self.slot]),self.root,{}, {},object())
        self.assertEqual(report['status'],'failed-integrity')

    def test_complete_eleven_capture_closure(self):
        schedule=[];report=dict(status=m.SUCCESS,attempted_commands=[],registered_commands=[],native_processes_started=11,
                               captures=[],validated_artifacts={},active=None)
        for index in range(11):
            slot=dict(id=f'case{index}',directory=f'{index:02}-decode-00',command=self.slot['command'])
            directory=self.root/slot['directory'];receipt(directory,slot,pid=42+index)
            for name in ('start','active','process'):
                path=directory/(name+'.json');value=json.loads(path.read_bytes())
                value['started_at']=f'2026-10-14T00:00:{index*2:02}+00:00'
                if name=='process':value['finished_at']=f'2026-10-14T00:00:{index*2+1:02}+00:00'
                path.write_text(json.dumps(value))
            capture,snapshot=m.checked_capture(slot,directory,os.getpid())
            schedule.append(slot);report['attempted_commands'].append(slot['directory'])
            report['registered_commands'].append(dict(directory=slot['directory'],pid=42+index))
            report['captures'].append(capture);report['validated_artifacts'][slot['directory']]=snapshot
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,dict(schedule=schedule),self.root,{}, {},object())
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],m.SUCCESS);self.assertEqual(terminal['integrity_errors'],[])
        self.assertEqual(len(terminal['available_evidence']),56)

    def test_final_inventory_cannot_adopt_late_mutation(self):
        report=self.report();original=m.inventory
        def changed(path,exclude=()):
            if path==self.root and exclude==('report.json','terminal.json'):
                (self.directory/'stdout.bin').write_bytes(b'late change')
            return original(path,exclude)
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock'),patch.object(m,'inventory',changed):
            m.finish(report,dict(schedule=[self.slot]),self.root,{}, {},object())
        self.assertEqual(report['status'],'failed-integrity')

    def final_verify_mutation(self,path):
        report=self.report();calls=0
        def verify(pins,resolutions,unavailable=()):
            nonlocal calls
            calls+=1
            if calls==2:path.write_bytes(b'changed during final input replay')
        with patch.object(m,'verify',verify),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,dict(schedule=[self.slot]),self.root,{}, {},object())
        self.assertEqual(report['status'],'failed-integrity')
        self.assertTrue(any('during final input verification' in e for e in report['integrity_errors']))

    def test_output_mutation_during_final_input_replay_rejected(self):
        self.final_verify_mutation(self.directory/'stdout.bin')

    def test_report_mutation_during_final_input_replay_rejected(self):
        self.final_verify_mutation(self.root/'report.json')

    def test_mutex_identity_rechecked_after_last_inventory(self):
        report=self.report();calls=0
        def check(lock):
            nonlocal calls
            calls+=1
            if calls==3:raise AssertionError('Mutex changed during final inventory')
        with patch.object(m,'verify'),patch.object(m.kb.kh,'verify_lock',check):
            m.finish(report,dict(schedule=[self.slot]),self.root,{}, {},object())
        self.assertEqual(calls,3)
        terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(terminal['status'],'failed-integrity')
        self.assertFalse(terminal['common_mutex_held'])


if __name__=='__main__':unittest.main()
