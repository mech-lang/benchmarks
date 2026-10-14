"""Pure protocol, oracle and failure-closure checks; no native subject runs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


def imported(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result);return result


m=imported(Path(__file__).with_name('prolog_knucleotide_bounded.py'),'knucleotide_test_controller')
u=imported(Path(__file__).with_name('prolog_knucleotide_source_units.py'),'knucleotide_test_units')
o=imported(m.Q/'fixtures.py','knucleotide_test_oracle')


def metadata():
    return dict(schema='prolog-knucleotide-loc-builtin-metadata-v1',version=[10,0,2],
        version_data='swi(10,0,2,[])',architecture='arm64-darwin',home='/retained/swipl',
        selected_target=dict(module='system',name='atom_string',arity=2,
                             built_in=True,foreign=True,defined=True,meta_predicate=False))


class OracleTests(unittest.TestCase):
    def test_handwritten_oracle_checks(self):
        o.self_check()

    def test_exact_header_parser_and_stop(self):
        raw=b'ACGT\n>THREEISH\nNO\n>THREE\tchosen\r\naCg\rT\n;skip\n\n>FOUR\nN'
        self.assertEqual(o.sequence(raw),b'ACGT')
        self.assertEqual(o.sequence(b'>THREE\vwrong\nN'),b'')
        self.assertEqual(o.sequence(b'>THREE'),b'')

    def test_invalid_code_is_original_byte(self):
        for code in (9,32,33,78,110,255):
            with self.subTest(code=code),self.assertRaises(o.InvalidBase) as caught:
                o.reference(b'>THREE\nAC'+bytes([code]))
            self.assertEqual(caught.exception.code,code)

    def test_all_maps_use_every_overlapping_window(self):
        value=o.complete_maps(b'>THREE\nGGTGGT')
        self.assertEqual(value['widths'],[1,2,3,4,6,12,18])
        for row in value['maps']:
            self.assertEqual(sum(pair[1] for pair in row['pairs']),max(0,6-row['width']+1))
        self.assertIn([43,2],value['maps'][2]['pairs'])

    def test_frequency_ties_sort_lexically(self):
        self.assertTrue(o.reference(b'>THREE\nTGCA').startswith(b'A 25.000\nC 25.000\nG 25.000\nT 25.000\n\n'))

    def test_old_expected_output_cannot_be_silently_replaced(self):
        known=[(name,b'',o.reference(b'')) for name in o.RETAINED_CASES]
        known[0]=(known[0][0],known[0][1],b'wrong')
        with self.assertRaises(AssertionError):o.manifest_rows(known)


class ProtocolTests(unittest.TestCase):
    def manifest(self):
        known=[(name,b'',o.reference(b'')) for name in o.RETAINED_CASES]
        rows=[]
        for name,raw,expected in o.manifest_rows(known):
            rows.append(dict(id=name,expected_status='invalid-acgt' if type(expected) is int else 'success'))
        return dict(schema='prolog-knucleotide-linear-fixtures-v1',cases=rows,
            complete_map_cases=['empty','all-four-base-words','query-overlaps','lowercase-long-line'])

    def test_exact_88_process_schedule(self):
        rows=m.schedule(self.manifest(),u)
        self.assertEqual(len(rows),88)
        for kind,number in [('compile',4),('inspect',2),('case',62),('maps',8),('metadata',1),('reader-fixture',7),('reader',4)]:
            self.assertEqual(sum(r['kind']==kind for r in rows),number)
        self.assertEqual([r['name'] for r in rows[:4]],['clbg_io','clbg_records','compact','optimized'])

    def test_retained_control_is_validated_but_not_selected_for_qualification(self):
        rows=[dict(id='prolog-knucleotide-'+v,language='prolog',binary='/swipl',runtime_environment={})
              for v in ('compact','optimized')]
        rows.append(dict(id='mech-aot-control',language='mech',key='knucleotide:prolog-full-study:mech-control'))
        self.assertEqual(m.runtime_profiles(rows),rows[:2])
        for change in (lambda r:r.pop(),lambda r:r[2].update(key='another-control'),
                       lambda r:r[1].update(binary='/other')):
            value=copy.deepcopy(rows);change(value)
            with self.assertRaises(AssertionError):m.runtime_profiles(value)

    def test_missing_alias_case_or_full_map_scope_is_rejected(self):
        for mutate in (lambda x:x['cases'].pop(),lambda x:x['cases'].__setitem__(0,x['cases'][1]),
                       lambda x:x['complete_map_cases'].pop()):
            manifest=self.manifest();mutate(manifest)
            with self.assertRaises(AssertionError):m.schedule(manifest,u)

    def test_direct_main_command_preloads_only_retained_compiled_helpers(self):
        root=Path('/fresh/input');argv=m.command('/retained/swipl',root,'optimized')
        self.assertEqual(argv,['/retained/swipl','-q','-O','-f','none','--stack-limit=8g',
            '-l','/fresh/input/support/clbg_io.qlf','-l','/fresh/input/support/clbg_records.qlf',
            '-s','/fresh/input/sources/knucleotide/optimized.qlf','-g','clbg_io:run(clbg_knucleotide:main)'])
        with self.assertRaises(AssertionError):m.command('/retained/swipl',root,'pilot')

    def test_exact_invalid_output_requires_empty_stdout_and_specific_code(self):
        case=dict(expected_status='invalid-acgt',expected_invalid_code=78)
        error=b"ERROR: [Thread main] Domain error: `acgt_nucleotide' expected, found `78'\n"
        m.check_output(case,b'',error)
        for stdout,stderr in [(b'partial',error),(b'',error+b'other'),(b'',error.replace(b'78',b'79'))]:
            with self.assertRaises(AssertionError):m.check_output(case,stdout,stderr)

    def test_success_checks_complete_bytes(self):
        expected=b'whole output\n';case=dict(expected_status='success',output_bytes=len(expected),
                                           output_sha256=hashlib.sha256(expected).hexdigest())
        m.check_output(case,expected,b'')
        for stdout,stderr in [(expected[:-1],b''),(expected+b'x',b''),(expected,b'warning')]:
            with self.assertRaises(AssertionError):m.check_output(case,stdout,stderr)

    def test_loader_checks_reviewed_bytes_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.py';path.write_text('raise RuntimeError("must not execute")\n')
            with self.assertRaisesRegex(AssertionError,'Pinned executable source changed'):
                m.load(path,'0'*64,'not_executed')

    def test_compiler_inventory_rejects_missing_helper_and_unpinned_library(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);authored=folder/'input';target=authored/'sources/knucleotide/compact.qlf'
            loaded=['sources/knucleotide/compact.pl','support/clbg_io.pl','support/clbg_records.pl']
            runtime=dict(version_components=[10,0,2],version_data='swi(10,0,2,[])',architecture='arm64-darwin',
                home='/retained/swipl',bounded=False,gc=True,stack_limit=8*1024**3)
            data=dict(mode='inspect',target=str(target),wam=str(folder/'candidate.wam'),runtime=runtime,
                      loaded_sources=[str(authored/name) for name in loaded],foreign_libraries=[])
            plan=dict(environment={'SWI_HOME_DIR':'/retained/swipl'},pins={})
            path=folder/'loaded-inputs.json';path.write_text(json.dumps(data))
            m.compiler_metadata(folder,'inspect',target,authored,loaded,plan)
            for change in (lambda x:x['loaded_sources'].pop(),
                           lambda x:x['foreign_libraries'].append(dict(resolved_path='/unreviewed/native.so')),
                           lambda x:x['runtime'].update(gc=False)):
                value=copy.deepcopy(data);change(value);path.write_text(json.dumps(value))
                with self.assertRaises(AssertionError):m.compiler_metadata(folder,'inspect',target,authored,loaded,plan)

    def test_incomplete_success_is_retained_as_failed_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            report=dict(status=m.COMPLETE,commands=[],native_processes_started=0,active=None,projections={})
            with patch.object(m.b,'verify_pins',return_value=[]),patch.object(m.kb.kh,'verify_lock'):
                with self.assertRaisesRegex(AssertionError,'closure failed'):
                    m.finish(report,dict(schedule=[dict(id='missing')]),{},output,{},object())
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity')
            self.assertFalse(terminal['source_work_qualified'])

    def test_late_artifact_or_input_mutation_cannot_keep_success(self):
        for changed_pin in (False,True):
            with self.subTest(changed_pin=changed_pin),tempfile.TemporaryDirectory() as directory:
                output=Path(directory);child=output/'done';child.mkdir();(child/'stdout.bin').write_bytes(b'old')
                snapshots={'done':m.b.inventory(child)}
                if not changed_pin:(child/'stdout.bin').write_bytes(b'changed')
                report=dict(status='failed',commands=[],native_processes_started=1,active=None,projections={})
                errors=[dict(path='input',error='changed')] if changed_pin else []
                with patch.object(m.b,'verify_pins',return_value=errors),patch.object(m.kb.kh,'verify_lock'):
                    with self.assertRaises(AssertionError):m.finish(report,{}, {},output,snapshots,object())
                self.assertEqual(json.loads((output/'terminal.json').read_bytes())['status'],'failed-integrity')

    def test_report_mutation_at_initial_snapshot_or_late_pin_replay_cannot_be_adopted(self):
        for phase in ('snapshot','pin-replay'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as directory:
                output=Path(directory);commands=[dict(id=str(i),pid=1000+i) for i in range(88)]
                report=dict(status=m.COMPLETE,commands=commands,native_processes_started=88,active=None,
                            projections={'compact':{},'optimized':{}})
                real_inventory=m.b.inventory;seen=[0];pin_reads=[0]
                def inventory(path):
                    if Path(path)==output:
                        seen[0]+=1
                        if phase=='snapshot' and seen[0]==1:
                            (output/'report.json').write_bytes(b'{"externally_changed":true}\n')
                    return real_inventory(path)
                def verify(pins):
                    pin_reads[0]+=1
                    if phase=='pin-replay' and pin_reads[0]==2:
                        (output/'report.json').write_bytes(b'{"externally_changed":true}\n')
                    return []
                with patch.object(m.b,'verify_pins',side_effect=verify),patch.object(m.b,'inventory',side_effect=inventory),\
                     patch.object(m.kb.kh,'verify_lock'):
                    with self.assertRaises(AssertionError):m.finish(report,dict(schedule=commands),{},output,{},object())
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')
                self.assertNotEqual(terminal['report_sha256'],terminal['expected_report_sha256'])
                self.assertEqual((output/'report.json').read_bytes(),b'{"externally_changed":true}\n')


class SourceOwnerTests(unittest.TestCase):
    def packet(self):
        return json.loads((u.GRAMMAR/'jobs/reader31-v1/projections/32/packet.json').read_bytes())

    def test_exact_new_builtin_and_original_counter_unchanged(self):
        context=u.BuiltinContext([self.packet()],metadata(),'/retained/swipl')
        self.assertEqual(context.resolve('m','atom_string/2'),('system','atom_string/2'))
        self.assertEqual(context.resolve('system','atom_string/2'),('system','atom_string/2'))
        self.assertIsNone(context.resolve('other','atom_string/2'))
        self.assertIsNone(context.resolve('m','atom_string/1'))
        self.assertNotIn('atom_string/2',u.original.BUILTINS)

    def test_local_definition_wins(self):
        context=u.BuiltinContext([self.packet()],metadata(),'/retained/swipl')
        context.definitions[('m','atom_string/2')]=[]
        self.assertEqual(context.resolve('m','atom_string/2'),('m','atom_string/2'))

    def test_builtin_metadata_rejects_other_runtime_and_meta_or_nonforeign_target(self):
        mutations=[lambda x:x.update(version=[10,0,1]),lambda x:x.update(home='/other'),
            lambda x:x['selected_target'].update(meta_predicate=True),lambda x:x['selected_target'].update(foreign=False),
            lambda x:x['selected_target'].update(arity=True),lambda x:x['selected_target'].update(name='atom_chars')]
        for change in mutations:
            value=metadata();change(value)
            with self.assertRaises(AssertionError):u.validate_metadata(value,'/retained/swipl')

    def test_fixture_scope_covers_shadowing_and_hidden_goals(self):
        rows=u.fixtures();self.assertEqual(len(rows),7)
        self.assertEqual([r['id'] for r in rows if r['expected_canonical_loc'] is None],
                         ['other-module','other-builtin','hidden-control'])
        self.assertEqual(next(r for r in rows if r['id']=='local-definition')['expected_canonical_loc'],5)


if __name__=='__main__':unittest.main()
