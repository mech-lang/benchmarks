"""Pure adapter and saved-reader regression checks; no native execution."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).with_name('prolog_revcomp_source_units.py')
SPEC=importlib.util.spec_from_file_location('tested_linear_source_units',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


class SourceUnitAdapterTests(unittest.TestCase):
    def metadata(self):
        return dict(schema='prolog-linear-loc-builtin-metadata-v1',version=[10,0,2],
            version_data='swi(10,0,2,[])',architecture='arm64-darwin',home='/retained/swipl',
            selected_target=dict(module='system',name='string_codes',arity=2,
                                 built_in=True,foreign=True,defined=True,meta_predicate=False))

    def packet(self):
        path=m.GRAMMAR/'jobs/reader31-v1/projections/32/packet.json'
        return json.loads(path.read_bytes())

    def test_addition_is_exact_and_original_counter_is_unchanged(self):
        context=m.BuiltinContext([self.packet()],self.metadata(),'/retained/swipl')
        self.assertEqual(context.resolve('m','string_codes/2'),('system','string_codes/2'))
        self.assertEqual(context.resolve('system','string_codes/2'),('system','string_codes/2'))
        self.assertIsNone(context.resolve('other','string_codes/2'))
        self.assertIsNone(context.resolve('m','string_codes/1'))
        self.assertIsNone(context.resolve('m','string_chars/2'))
        self.assertEqual(context.slots(('system','string_codes/2')), {})
        self.assertNotIn('string_codes/2',m.original.BUILTINS)

    def test_written_local_definition_wins(self):
        context=m.BuiltinContext([self.packet()],self.metadata(),'/retained/swipl')
        context.definitions[('m','string_codes/2')]=[]
        self.assertEqual(context.resolve('m','string_codes/2'),('m','string_codes/2'))

    def test_wrong_runtime_or_nonordinary_builtin_fails_before_projection(self):
        changes=[lambda x:x.update(version=[10,0,1]),lambda x:x.update(home='/other'),
                 lambda x:x.update(architecture='x86_64-linux'),
                 lambda x:x['selected_target'].update(meta_predicate=True),
                 lambda x:x['selected_target'].update(built_in=False),
                 lambda x:x['selected_target'].update(foreign=False),
                 lambda x:x['selected_target'].update(defined=False),
                 lambda x:x['selected_target'].update(arity=True),
                 lambda x:x['selected_target'].update(name='call'),
                 lambda x:x['selected_target'].update(module='candidate'),
                 lambda x:x['selected_target'].update(unreviewed=True)]
        for change in changes:
            metadata=self.metadata();change(metadata)
            with self.subTest(metadata=metadata),self.assertRaises(AssertionError):
                m.BuiltinContext([self.packet()],metadata,'/retained/swipl')

    def test_all22_saved_original_source_projections_are_unchanged(self):
        # Build the same main/helper bundle context for each selected source;
        # this is saved AST replay, not another native reader fixture run.
        root=m.ROOT/'archive/languages/prolog/20261013/source-counts/original22-replay-v1/sources'
        packets=[json.loads(p.read_bytes()) for p in sorted(root.glob('*/original-reader.stdout'))]
        self.assertEqual(len(packets),22)
        helpers={}
        mains=[]
        for packet in packets:
            if Path(packet['source']).name in ('clbg_io.pl','clbg_records.pl'):
                helpers[Path(packet['source']).name]=packet
            else:mains.append(packet)
        self.assertEqual(len(mains),20)
        compared=set()
        for main in mains:
            bundle=[main,helpers['clbg_io.pl']]
            if '/revcomp/' in main['source'] or '/knucleotide/' in main['source']:
                bundle.append(helpers['clbg_records.pl'])
            base=m.original.BundleContext(bundle)
            additive=m.BuiltinContext(bundle,self.metadata(),'/retained/swipl')
            for packet in bundle:
                raw=packet['source_text'].encode('utf8')
                before=m.original.count_prolog(raw,packet,language='prolog',context=base)
                after=m.original.count_prolog(raw,packet,language='prolog',context=additive)
                self.assertEqual(before,after,packet['source'])
                self.assertEqual(after['diagnostics'],[],packet['source'])
                compared.add(packet['source'])
        self.assertEqual(len(compared),22)

    def test_projection_never_grants_admission(self):
        packet=self.packet()
        result=m.project(packet['source_text'].encode(),packet,self.metadata(),'/retained/swipl')
        self.assertEqual(result['projection']['diagnostics'],[])
        for key in ('canonical_LOC_admitted','source_work_qualified','chart_admission'):
            self.assertIs(result[key],False)
        self.assertIsNone(result['formatted_loc'])

    def test_candidate_projection_rejects_unbound_original_or_compiler_bytes(self):
        packet=self.packet();raw=packet['source_text'].encode()
        for original,compiled in ((raw,raw),(b'wrong',raw)):
            with self.assertRaisesRegex(AssertionError,'Candidate and actual compiler input differ'):
                m.project_candidate(original,compiled,packet,self.metadata(),'/retained/swipl','')

    def test_native_commands_read_source_without_loading_candidate(self):
        command=m.reader_command('/retained/swipl','/retained/candidate.pl')
        self.assertEqual(command[-3:],['prolog_source_scan_v1:main','--','/retained/candidate.pl'])
        self.assertEqual(command[command.index('-l')+1],str(m.GRAMMAR/'scan_source.pl'))
        self.assertNotIn('-s',command)
        self.assertNotIn('clbg_revcomp_linear:run',command)
        for binary,source in (('swipl','/retained/candidate.pl'),('/retained/swipl','candidate.pl')):
            with self.assertRaises(AssertionError):m.reader_command(binary,source)

    def test_seven_fixtures_are_fresh_source_only_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/'fixtures'
            manifest=m.write_fixtures(directory)
            self.assertEqual(len(manifest['fixtures']),7)
            self.assertEqual(sum(row['expected_canonical_loc'] is None for row in manifest['fixtures']),3)
            self.assertEqual(manifest['native_executions'],0)
            self.assertIs(manifest['fixtures_qualified'],False)
            for row in manifest['fixtures']:
                self.assertEqual(Path(row['source']).read_text(),row['source_text'])
            with self.assertRaises(FileExistsError):m.write_fixtures(directory)


if __name__=='__main__':unittest.main()
