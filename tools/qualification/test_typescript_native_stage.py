"""Pure TypeScript stage admission tests; no Node, compiler or runtime hash."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('typescript_native_stage.py')
SPEC = importlib.util.spec_from_file_location('tested_typescript_native_stage', PATH)
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


def digest(data): return hashlib.sha256(data).hexdigest()


def ast_fixture():
    text = 'const s = "😀";\n'; raw = text.encode(); count = len(text.encode('utf-16-le'))//2
    item = dict(id='unicode',source_path='/synthetic/unicode.ts',sha256=digest(raw),expected_parse='ok')
    root = dict(id=0,parent=-1,kind='SourceFile',native_kind=300,flags=0,full_start_utf16=0,start_utf16=0,
                end_utf16=count,text_sha256=digest(raw),children=[1],roles={'statements':[1]})
    child = dict(id=1,parent=0,kind='VariableStatement',native_kind=200,flags=0,full_start_utf16=0,start_utf16=0,
                 end_utf16=count-1,text_sha256=digest(text[:-1].encode()),children=[],roles={})
    evidence = dict(id='unicode',source_path=item['source_path'],source_sha256=digest(raw),source_text=text,
                    source_bytes=len(raw),source_utf16_length=count,offset_units='UTF-16 code units',
                    native_transport_verified=False,canonical_loc=None,formatted_loc=None,chart_admission=False,
                    parse_diagnostics=[],nodes=[root,child])
    return evidence,item,raw


class TypeScriptStage(unittest.TestCase):
    def test_physical_absolute_path_required(self):
        with self.assertRaises(AssertionError):m.physical_path(Path('relative.json'))
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp).resolve();m.physical_path(directory/'future.json')
            (directory/'alias').symlink_to(directory,target_is_directory=True)
            with self.assertRaises(AssertionError):m.physical_path(directory/'alias/future.json')

    def test_actual_metadata_draft_does_not_hash_runtime_or_create_paths(self):
        original = m.sha
        def small_only(path):
            value = str(Path(path).resolve())
            if value in (str(m.NODE),str(m.kb.kh.PYTHON.resolve())) or value.endswith('/lib/tsc'):
                raise AssertionError('Runtime hash attempted during metadata-only draft')
            return original(path)
        with tempfile.TemporaryDirectory() as tmp, patch.object(m,'sha',side_effect=small_only):
            output=Path(tmp).resolve()/'not-created'; plan=m.draft(output)
            self.assertFalse(output.exists()); self.assertEqual(len(plan['inputs']),40)
            self.assertEqual(sum(i['expected_parse']=='error' for i in plan['inputs']),2)
            self.assertEqual(plan['owned_commands'],2);self.assertEqual(plan['expected_api_children'],1)
            self.assertFalse(plan['pins_verified']);self.assertFalse(plan['chart_admission'])
            self.assertEqual(plan['compiler_command'][1:3],['--project',str(output/'compile/project/tsconfig.json')])
            self.assertEqual(plan['compiler_command'][-2:],['--incremental','false'])

    def child_fixture(self, code=None, signal='SIGTERM'):
        plan=dict(compiler='/synthetic/tsc',reader_plan={'output':'/synthetic/evidence'})
        receipt=dict(pid=41,cwd='/synthetic/reader')
        start=dict(pid=42,parent_pid=41,executable=plan['compiler'],cwd=receipt['cwd'],language_cwd=plan['reader_plan']['output'],
                   argv=[plan['compiler'],'--api','--cwd',plan['reader_plan']['output'],
                         '--callbacks=readFile,fileExists,directoryExists,getAccessibleEntries,realpath'])
        terminal=dict(pid=42,parent_pid=41,close_requested=True,close_observed=True,child_error=None,close_error=None,
                      exit_code=code,signal_code=signal,events=[dict(event=e,code=code,signal=signal) for e in ('exit','close')])
        return start,terminal,receipt,plan

    def test_api_child_expected_sigterm_or_clean_exit(self):
        for code,signal in ((None,'SIGTERM'),(0,None)):
            m.validate_child(*self.child_fixture(code,signal))

    def test_api_child_wrong_executable_parent_or_argv_fails(self):
        for change in (lambda s:s.update(pid=True),lambda s:s.update(parent_pid=1),lambda s:s.update(executable='/other/tsc'),
                       lambda s:s['argv'].append('--fallback'),lambda s:s.update(cwd='/other')):
            start,terminal,receipt,plan=self.child_fixture();change(start)
            with self.subTest(change=change),self.assertRaises(AssertionError):m.validate_child(start,terminal,receipt,plan)

    def test_api_child_signal_error_or_missing_close_fails(self):
        for code,signal in ((1,None),(None,'SIGKILL'),(False,None)):
            with self.assertRaises(AssertionError):m.validate_child(*self.child_fixture(code,signal))
        for change in (lambda t:t.update(close_observed=False),lambda t:t.update(child_error='spawn failed'),
                       lambda t:t['events'].pop(),lambda t:t['events'].reverse()):
            start,terminal,receipt,plan=self.child_fixture();change(terminal)
            with self.assertRaises(AssertionError):m.validate_child(start,terminal,receipt,plan)

    def test_utf16_non_bmp_source_slices(self):
        evidence,item,raw=ast_fixture();m.validate_ast(evidence,item,raw)
        self.assertNotEqual(evidence['source_bytes'],evidence['source_utf16_length'])

    def test_ast_source_span_role_or_disconnected_tree_fails(self):
        changes=[lambda e:e.update(source_text='different'),lambda e:e['nodes'][1].update(end_utf16=1000),
                 lambda e:e['nodes'][1].update(text_sha256='0'*64),lambda e:e['nodes'][0].update(children=[]),
                 lambda e:e['nodes'][1].update(parent=-1),lambda e:e['nodes'][0].update(roles={'name':99}),
                 lambda e:e['nodes'][0].update(children=[1,1])]
        for change in changes:
            evidence,item,raw=ast_fixture();change(evidence)
            with self.subTest(change=change),self.assertRaises(AssertionError):m.validate_ast(evidence,item,raw)

    def test_parse_rejections_keep_diagnostics_without_owner_tree(self):
        evidence,item,raw=ast_fixture();item['expected_parse']='error';evidence['parse_diagnostics']=[{'code':1005}];evidence['nodes']=[]
        m.validate_ast(evidence,item,raw)
        item['expected_parse']='ok'
        with self.assertRaises(AssertionError):m.validate_ast(evidence,item,raw)

    def test_source_capture_cannot_grant_transport_or_counts(self):
        for field,value in [('canonical_loc',3),('formatted_loc',4),('native_transport_verified',True),('chart_admission',True)]:
            evidence,item,raw=ast_fixture();evidence[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):m.validate_ast(evidence,item,raw)

    def make_compile(self, directory):
        project=directory/'project';project.mkdir();emitted=project/'emitted';emitted.mkdir();files=[];lines=[];pins={}
        for bench in m.BENCHES:
            source=project/(bench+'.ts');source.write_text('const value: number = 1;\n');files.append(str(source))
            pins[str(m.SOURCES/source.name)]=m.sha(source)
            js=emitted/(bench+'.js');js.write_text('const value = 1;\n')
            sm=emitted/(bench+'.js.map');sm.write_text(json.dumps(dict(version=3,file=js.name,sourceRoot='',
                sources=['../'+source.name],sourcesContent=[source.read_text()],mappings='AAAA')))
            lines.extend(['TSFILE: '+str(js),'TSFILE: '+str(sm)])
        for filename in ('tsconfig.json','package.json'):
            source=project/filename;source.write_text('{}');pins[str(m.SOURCES/filename)]=m.sha(source)
        return {'pins':pins}, ('\n'.join(files+lines)+'\n').encode()

    def test_exact_ten_emit_pairs_and_typed_source_map_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);plan,stdout=self.make_compile(directory);result=m.validate_compile(plan,directory,stdout)
            self.assertEqual(len(result['profiles']),10);self.assertEqual(len(result['emitted_file_inventory']),20)

    def test_compiler_diagnostics_or_unpinned_dependency_fail(self):
        for extra in (b'error TS1234: bad option\n',b'/unretained/library.d.ts\n'):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);plan,stdout=self.make_compile(directory)
                with self.assertRaises(AssertionError):m.validate_compile(plan,directory,stdout+extra)

    def test_missing_emit_or_wrong_source_map_fails(self):
        for missing in (True,False):
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);plan,stdout=self.make_compile(directory);p=directory/'project/emitted/binarytrees.js.map'
                if missing:p.unlink()
                else:
                    sm=json.loads(p.read_bytes());sm['sourcesContent']=['const value = 1;'];p.write_text(json.dumps(sm))
                with self.assertRaises(AssertionError):m.validate_compile(plan,directory,stdout)

    def test_changed_staged_source_config_or_package_fails_even_with_matching_map(self):
        for filename in ('binarytrees.ts','tsconfig.json','package.json'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);plan,stdout=self.make_compile(directory);source=directory/'project'/filename
                source.write_text('const value: number = 2;\n' if filename.endswith('.ts') else '{"changed":true}')
                if filename.endswith('.ts'):
                    mapping=directory/'project/emitted/binarytrees.js.map';value=json.loads(mapping.read_bytes())
                    value['sourcesContent']=[source.read_text()];mapping.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.validate_compile(plan,directory,stdout)

    def test_package_extra_file_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);file=directory/'entry.js';file.write_text('x')
            packages=[dict(installation_directory=str(directory),files={'entry.js':dict(bytes=1)})]
            m.package_inventory(packages);(directory/'extra').write_text('x')
            with self.assertRaises(AssertionError):m.package_inventory(packages)
            (directory/'extra').unlink();(directory/'alias').symlink_to(file)
            with self.assertRaises(AssertionError):m.package_inventory(packages)

    def test_native_receipt_inventory_and_unreaped_process_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);directory=output/'compile';directory.mkdir()
            report=dict(status='failed',owned_commands_started=1,registered_commands=[dict(stage='compile',pid=42,pgid=42)])
            self.assertTrue(m.process_closure(report,output))
            receipt=dict(pid=42,pgid=42,native_process_started=True,direct_child_reaped=True,remaining_process_group=[],cleanup_errors=[])
            p=directory/'process.json';p.write_text(json.dumps(receipt));self.assertEqual(m.process_closure(report,output),[])
            receipt['direct_child_reaped']=False;p.write_text(json.dumps(receipt));self.assertTrue(m.process_closure(report,output))

    def test_package_and_native_inventory_reject_unlisted_fifo(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);file=directory/'entry.js';file.write_text('x')
            packages=[dict(installation_directory=str(directory),files={'entry.js':dict(bytes=1)})]
            os.mkfifo(directory/'unlisted-pipe')
            with self.assertRaises(AssertionError):m.package_inventory(packages)
            with self.assertRaises(AssertionError):m.inventory(directory)

    def test_owned_receipt_identity_output_and_resource_faults_fail(self):
        # Adapt a retained generic version receipt into a synthetic directory;
        # no saved producer file is changed and no PID is inspected or signalled.
        original=json.loads((m.TOOLS/'native-versions-v1/node/process.json').read_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'reader';directory.mkdir();command=['/synthetic/node','/synthetic/reader.mjs'];env=m.environment(directory)
            receipt=copy.deepcopy(original);receipt.update(command=command,environment=env,cwd=str(directory),kind='typescript-reader')
            receipt['identity']['ppid']=os.getpid();receipt['leader_identity_before_reap']['ppid']=os.getpid()
            for name in ('stdout','stderr'):
                (directory/(name+'.bin')).write_bytes(b'');receipt[name+'_bytes']=0;receipt[name+'_sha256']=digest(b'')
            for name in ('start.json','active.json'):(directory/name).write_text(json.dumps(receipt))
            m.validate_receipt(receipt,command,env,directory)
            for change in (lambda r:r.update(direct_child_reaped=False),lambda r:r.update(exit_status=1),
                           lambda r:r.update(maximum_process_group_rss_bytes=1),lambda r:r['identity'].update(ppid=1),
                           lambda r:r['leader_identity_before_reap'].update(birth_seconds=0),lambda r:r.update(stdout_sha256='0'*64)):
                fault=copy.deepcopy(receipt);change(fault)
                with self.subTest(change=change),self.assertRaises(AssertionError):m.validate_receipt(fault,command,env,directory)

    def test_inventory_retains_nested_terminal_and_detects_late_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);nested=directory/'nested';nested.mkdir();p=nested/'terminal.json';p.write_text('{}')
            before=m.inventory(directory);self.assertIn('nested/terminal.json',before)
            p.write_text('{ }');self.assertNotEqual(before,m.inventory(directory))
            (directory/'alias').symlink_to(p)
            with self.assertRaises(AssertionError):m.inventory(directory)

    def final_fixture(self, directory):
        output=directory/'output';output.mkdir();prerequisite=directory/'prerequisite';prerequisite.write_text('pinned')
        generated=output/'fixture.ts';generated.write_text('const n = 1;')
        report=dict(status='compile-and-AST-captures-recorded-awaiting-independent-review',owned_commands_started=2,
                    registered_commands=[],stages=dict(compile={},reader={}),observed_api_children=[],
                    validated_stage_artifacts={},generated_input_pins={str(generated):m.sha(generated)})
        for index,stage in enumerate(('compile','reader')):
            child=output/stage;child.mkdir();pid=40+index
            report['registered_commands'].append(dict(stage=stage,pid=pid,pgid=pid))
            receipt=dict(pid=pid,pgid=pid,native_process_started=True,direct_child_reaped=True,
                         remaining_process_group=[],cleanup_errors=[],status='native-passed')
            (child/'process.json').write_text(json.dumps(receipt))
            (child/'terminal.json').write_text('{}')
            report['validated_stage_artifacts'][stage]=m.inventory(child)
        return report,{'packages':[]},output,{str(prerequisite):m.sha(prerequisite)}

    def test_final_closure_preserves_validated_stage_bytes_and_report(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.kb.kh,'verify_lock'):
            report,plan,output,pins=self.final_fixture(Path(tmp));m.finish(report,plan,output,pins,object())
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'compile-and-AST-captures-recorded-awaiting-independent-review')
            self.assertEqual(terminal['integrity_errors'],[]);self.assertTrue(terminal['common_mutex_held'])
            self.assertEqual(terminal['report_sha256'],m.sha(output/'report.json'))
            self.assertEqual(terminal['available_evidence'],m.inventory(output,('terminal.json',)))

    def test_final_inventory_cannot_adopt_late_stage_or_input_mutation(self):
        for fault in ('stage-before-inventory','stage-after-first','prerequisite-after-second','generated-after-second'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp,patch.object(m.kb.kh,'verify_lock'):
                report,plan,output,pins=self.final_fixture(Path(tmp));original=m.inventory;calls=0
                stage=output/'compile/terminal.json'
                if fault=='stage-before-inventory':stage.write_text('{"changed":true}')
                def injected(path,excluded=()):
                    nonlocal calls
                    result=original(path,excluded);calls+=1
                    if fault=='stage-after-first' and calls==1:stage.write_text('{"changed":true}')
                    if fault=='prerequisite-after-second' and calls==2:Path(next(iter(pins))).write_text('changed')
                    if fault=='generated-after-second' and calls==2:(output/'fixture.ts').write_text('changed')
                    return result
                with patch.object(m,'inventory',side_effect=injected):m.finish(report,plan,output,pins,object())
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertTrue(terminal['integrity_errors'])
                self.assertEqual(set(terminal['available_evidence']),{'report.json'})

    def test_final_mutex_mismatch_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.kb.kh,'verify_lock',side_effect=AssertionError('lock changed')):
            report,plan,output,pins=self.final_fixture(Path(tmp));m.finish(report,plan,output,pins,object())
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity');self.assertFalse(terminal['common_mutex_held'])
            self.assertTrue(any(e['path']=='<common-mutex>' for e in terminal['integrity_errors']))

    def test_main_converts_termination_to_supervisor_interruption(self):
        installed={}
        def execute(args):
            self.assertEqual(set(installed),m.kb.kh.SIGNALS)
            for sig,handler in installed.items():
                with self.assertRaises(KeyboardInterrupt):handler(sig,None)
            return 17
        with patch.object(m.sys,'argv',['stage','run','--plan','/synthetic/plan.json','--plan-sha256','0'*64]),\
             patch.object(m.signal,'signal',side_effect=lambda sig,handler:installed.__setitem__(sig,handler)),\
             patch.object(m,'run',side_effect=execute):
            self.assertEqual(m.main(),17)


if __name__ == '__main__':unittest.main()
