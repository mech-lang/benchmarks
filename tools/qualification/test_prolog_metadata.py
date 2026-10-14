"""Synthetic metadata fault tests; no runtime execution or full-closure hashes."""
import copy
import gzip
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load('metadata_test_subject', 'prolog_metadata.py')
ledger_tests = load('metadata_synthetic_ledger', 'test_prolog_reconcile.py')
SHA = '1'*64


def success(command):
    return dict(command=command, exit_status=0, final_exit_status=0, inherited_common_mutex=True,
        preparation_only=True, never_chart_eligible=True, pid=101, identity={'pid': 101},
        started_at='2026-10-14T00:00:00+00:00', finished_at='2026-10-14T00:00:01+00:00')


def fixture(failure=None):
    args = ledger_tests.fixture(failure=failure)
    plan = args['plan']
    reconciliation = ledger_tests.audit.reconcile(**args)
    reconciliation.update(status='full90-reconciled-awaiting-runtime-and-publication-review',
        file_integrity_verified=True,
        plan=dict(path='/fixture/experiments/prolog/full90-v1/plan.json', sha256=m.r.PLAN_SHA))
    plan['timing_policy'] = 'Synthetic fresh-process boundary'
    binary='/fixture/app/swipl'; home='/fixture/app/home'
    flags = dict(architecture='arm64-darwin', bounded=False, gc=True, home=home,
        stack_limit=8589934592, version_components=[10, 0, 2], version_data='swi(10,0,2,[])')
    images = {path: SHA for path in [binary, '/fixture/app/libswipl.dylib', '/fixture/app/libgmp.dylib',
        '/fixture/app/libpcre.dylib', '/fixture/app/libz.dylib', '/fixture/app/json.so', '/fixture/app/pcre4pl.so']}
    config = dict(status='qualified-runtime-discovery', chart_admission=False, architecture='arm64',
        runtime_backend='swi-native-bytecode-vm', default_gc_observed=True, bounded_observed=False,
        version_components=[10, 0, 2], environment={'SWI_HOME_DIR':home}, home=home,
        binary=binary, binary_sha256=SHA, actual_feature_probe='/fixture/feature.json',
        actual_feature_probe_sha256=SHA, pcre_version='10.40 2022-04-14',
        source_library_review=dict(path='/fixture/library.json', sha256=SHA),
        closed_review=dict(path='/fixture/closed.json', sha256=SHA), loaded_native_images=list(images))
    documents = {m.CONFIG: config,
        '/fixture/feature.json':dict(runtime=flags,pcre_version=config['pcre_version'],regex_jit_requested=False),
        '/fixture/library.json':dict(status='passed',root_review=True,actual_feature_sha256=SHA,
            native_image_closure_sha256=m.IMAGE_SHA,source_pins={}),
        '/fixture/closed.json':dict(status='corrected-feature-and-private-images-passed',feature_exit=0,
            native_images=7,runtime=flags,images=list(images)),
        m.IMAGES:dict(status='passed-native-image-closure',selected_architecture='arm64',executable=binary,
            chart_admission=False,image_pins=images,contexts=[dict(image=path,selected_architecture='arm64',
                mach_header={'architecture':'arm64'},architectures=['arm64'],dependencies=[
                    dict(scope='OS-image-not-hashed',install_name='/usr/lib/libSystem.B.dylib')]) for path in images])}
    bytes_files = {}
    for field, name, command, output in (
            ('feature_probe_owned_receipt','feature',[binary,*m.PREFIX,'-l','/fixture/probe.pl'],b''),
            ('version_receipt','version',[binary,'--version'],m.VERSION.encode())):
        ref=dict(status='passed',receipt=f'/fixture/{name}-command.json',receipt_sha256=SHA,
                 command=command,stdout=f'/fixture/{name}.stdout',stdout_sha256=SHA)
        config[field]=ref;documents[ref['receipt']]=success(command)
        bytes_files[ref['stdout']]=output;bytes_files[f'/fixture/{name}.stderr']=b''
    outcome=dict(status='qualified-original-Prolog20-work-and-LOC-awaiting-full90',source_work_qualified=True,
        canonical_LOC_admitted=True,chart_admission=False,profiles=20,outputs={})
    plan['pins'].update(images)
    for manifest in plan['manifests'].values():
        for row in manifest['profiles']:
            if row['language'] != 'prolog':continue
            form = 'optimized' if row['id'].endswith('-optimized') else 'compact'
            directory='/fixture/'+row['id']; main=directory+'/main.pl'; helper=directory+'/clbg_io.pl'
            row.update(source=main,measured_source=main,source_sha256=SHA,binary=binary,binary_sha256=SHA,
                variant=form,source_alias_of='prolog-'+row['benchmark']+'-compact' if form=='optimized' else None,
                optimization_claim='synthetic alias' if form=='optimized' else 'synthetic baseline',
                runtime_environment=config['environment'],canonical_loc=3,physical_loc=3,
                source_bundle=[dict(path=main,origin=main,sha256=SHA),dict(path=helper,origin=helper,sha256=SHA)])
            command=[binary,*m.PREFIX,'-l',str(Path(helper).with_suffix('.qlf'))]
            if row['benchmark'] in ('revcomp','knucleotide'):
                records=directory+'/clbg_records.pl'
                row['source_bundle'].append(dict(path=records,origin=records,sha256=SHA))
                command+=['-l',str(Path(records).with_suffix('.qlf'))]
            command+=['-s',str(Path(main).with_suffix('.qlf')),'-g',f'clbg_io:run(clbg_{row["benchmark"]}:main)']
            if row['benchmark'] not in ('regexredux','revcomp','knucleotide'):command+=['--','{n}']
            row['command']=command
            ref=dict(path=directory+'/compiled.json',sha256=SHA)
            row['compiler_bound_input_inventory']=ref;outcome['outputs'][Path(ref['path']).name]=SHA
            artifacts={str(Path(source['path']).with_suffix('.qlf')):SHA for source in row['source_bundle']}
            plan['pins'].update(artifacts)
            retained={k:copy.deepcopy(row[k]) for k in ('id','key','benchmark','variant','source','source_sha256',
                'measured_source','binary','binary_sha256','command','cwd','runtime_environment','source_alias_of')}
            retained.update(application_artifact_pins=artifacts,vendor_libraries=['library(pcre)']
                if row['benchmark']=='regexredux' else [],compile_receipts=[])
            for entry in row['source_bundle']:
                source=entry['path']
                compile_ref=dict(source=source,receipt=source+'.command.json',receipt_sha256=SHA,
                                 command=[binary,'synthetic-compile',source])
                retained['compile_receipts'].append(compile_ref)
                documents[compile_ref['receipt']]=success(compile_ref['command'])
            loaded_ref=dict(receipt=directory+'/loaded.json',receipt_sha256=SHA)
            documents[loaded_ref['receipt']]=dict(mode='inspect',target=str(Path(main).with_suffix('.qlf')),runtime=flags,
                foreign_libraries=[dict(resolved_path='/fixture/app/pcre4pl.so')]
                if row['benchmark']=='regexredux' else [])
            documents[ref['path']]=dict(status='qualified-exact-authored-compiler-inputs',source_sha256=SHA,
                binary_sha256=SHA,independently_retained_compiler_input_evidence=retained,
                original_compiler_input_evidence=loaded_ref,files=row['source_bundle'])
            observed=reconciliation['profiles'][row['key']]
            observed.update({field:row[field] for field in ('key','id','language','benchmark','source',
                                                          'source_sha256','binary_sha256')})
    reconciliation['verified_file_pins']=dict(plan['pins'],**{str(m.RECONCILER.resolve()):m.RECONCILER_SHA,
        str(m.r.HELPER.resolve()):m.r.HELPER_SHA})
    return plan,reconciliation,outcome,documents,bytes_files


def inspect(data):
    plan,reconciliation,outcome,documents,bytes_files=data
    return m.inspect(plan,reconciliation,outcome,lambda path,sha=None:documents[path],
                     lambda path,sha=None:bytes_files[path])


class MetadataSemantics(unittest.TestCase):
    def test_all_forms_preserve_aliases_without_claiming_native_aot(self):
        result=inspect(fixture())
        self.assertEqual(len(result['profiles']),20)
        self.assertEqual(sum(p['source_alias_of'] is not None for p in result['profiles']),10)
        self.assertEqual(result['application_execution'],'bytecode/QLF')
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['runtime_publication_metadata_qualified'])
        self.assertFalse(result['file_integrity_verified'])
        self.assertEqual(sum(len(p['qlf_artifact_pins']) for p in result['profiles']),44)

    def test_record_helper_cannot_be_omitted_from_measured_command(self):
        data=fixture();row=data[0]['manifests']['revcomp']['profiles'][0]
        row['command'][8:10]=[]
        data[3][row['compiler_bound_input_inventory']['path']]['independently_retained_compiler_input_evidence']['command']=list(row['command'])
        with self.assertRaises(ValueError):inspect(data)

    def test_failed_form_is_excluded_without_substituting_its_alias(self):
        key='regexredux:prolog-regexredux-compact'
        result=inspect(fixture(failure=key))
        self.assertEqual(len(result['profiles']),19)
        self.assertEqual(result['excluded_profiles'][0]['key'],key)
        alias=next(p for p in result['profiles'] if p['id']=='prolog-regexredux-optimized')
        self.assertEqual(alias['source_alias_of'],'prolog-regexredux-compact')

    def test_incomplete_or_unhashed_reconciliation_cannot_grant_runtime_metadata(self):
        for field,value in [('status','running'),('file_integrity_verified',False),
                            ('chart_admission',True),('runtime_publication_metadata_qualified',True)]:
            data=fixture();data[1][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):inspect(data)

    def test_missing_reconciliation_input_pin_is_rejected(self):
        data=fixture();data[1]['verified_file_pins'].pop(next(iter(data[0]['pins'])))
        with self.assertRaises(ValueError):inspect(data)

    def test_source_seal_is_required(self):
        data=fixture();data[2]['canonical_LOC_admitted']=False
        with self.assertRaises(ValueError):inspect(data)

    def test_runtime_flags_are_type_sensitive(self):
        for field,value in [('gc',1),('bounded',0),('stack_limit',8589934592.0),
                            ('architecture','x86_64-darwin')]:
            data=fixture();data[3]['/fixture/feature.json']['runtime'][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):inspect(data)

    def test_compile_receipt_nonzero_exit_is_rejected(self):
        data=fixture();d=data[3]
        compile_path=next(path for path in d if path.endswith('.pl.command.json'))
        d[compile_path]['exit_status']=1
        with self.assertRaises(ValueError):inspect(data)

    def test_changed_qlf_argument_is_rejected(self):
        data=fixture();row=data[0]['manifests']['regexredux']['profiles'][0]
        row['command'][9]='/fixture/replacement.qlf'
        with self.assertRaises(ValueError):inspect(data)

    def test_alias_cannot_claim_an_unrelated_source(self):
        data=fixture();row=data[0]['manifests']['regexredux']['profiles'][1]
        row['source_alias_of']='prolog-revcomp-compact'
        data[3][row['compiler_bound_input_inventory']['path']]['independently_retained_compiler_input_evidence']['source_alias_of']=row['source_alias_of']
        with self.assertRaises(ValueError):inspect(data)

    def test_foreign_library_outside_retained_closure_is_rejected(self):
        data=fixture();data[3]['/fixture/prolog-regexredux-compact/loaded.json']['foreign_libraries'][0]['resolved_path']='/unbound/foreign.so'
        with self.assertRaises(ValueError):inspect(data)

    def test_non_os_unhashed_library_is_rejected(self):
        data=fixture();data[3][m.IMAGES]['contexts'][0]['dependencies'][0]['install_name']='/opt/homebrew/lib/unknown.dylib'
        with self.assertRaises(ValueError):inspect(data)

    def test_probe_failure_cannot_be_hidden_by_config_summary(self):
        data=fixture();data[3]['/fixture/feature-command.json']['timed_out']=True
        with self.assertRaises(ValueError):inspect(data)


class ExactMetadataStorage(unittest.TestCase):
    def test_declared_gzip_decodes_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);data=b'{"status":"test-fixture"}';packed=gzip.compress(data,mtime=0)
            physical=root/'data.json.gz';physical.write_bytes(packed)
            plain_sha=hashlib.sha256(data).hexdigest();stored_sha=hashlib.sha256(packed).hexdigest()
            storage=dict(artifacts=[dict(logical_path='data.json',stored_path='data.json.gz',storage_encoding='gzip',
                original_sha256=plain_sha,stored_sha256=stored_sha,original_bytes=len(data),stored_bytes=len(packed))])
            reader=m.Evidence(dict(repository=directory,pins={str(physical):stored_sha}),storage)
            self.assertEqual(reader.raw(str(root/'data.json'),plain_sha),data)
            with self.assertRaises(ValueError):reader.raw(str(root/'data.json'),'0'*64)

    def test_editorial_substitution_cannot_change_runtime_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'new.json';path.write_bytes(b'{}');sha=hashlib.sha256(b'{}').hexdigest()
            relocation=dict(historical_path='/old.json',resolved_path=str(path),storage_encoding='identity',
                expected_sha256=sha,actual_content_sha256=sha,editorial_substitution={'changed':True})
            reader=m.Evidence(dict(repository=directory,pins={str(path):sha},path_reconciliation={'/old.json':relocation}),{'artifacts':[]})
            with self.assertRaises(ValueError):reader.raw('/old.json',sha)


if __name__ == '__main__':
    unittest.main()
