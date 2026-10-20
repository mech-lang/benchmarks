"""Tiny synthetic proof binding tests; no native parser or recorded catalog."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import logical_source_payload as binder
import build_site


def fixture(root):
    files, programs = {}, {}
    def file(text):
        digest = binder.sha(text.encode())
        files[digest] = dict(sha256=digest, code=text, name='fixture', path='fixture')
        return digest
    py = file('x=1\n# support\n'); app = file('(def x 1)\n'); support = file('(def helper 1)\n'); other = file('opaque\n')
    def row(key, language, hashes, roles=None):
        programs[key] = dict(key=key,id=key,language=language,benchmark='b',loc=7,files=hashes,
            file_roles=roles or {},samples=[1,2,3],seconds=2,x=1,y=1)
        return programs[key]
    row('b:py','python',[py],{py:dict(role='application',support_line_ranges=[dict(start=2,end=2)])})
    clj = row('b:clj','clojure',[app,support],{support:dict(role='runtime-support')})
    unknown = row('b:unknown','unknown',[other]); programs.pop('b:unknown')
    catalog = dict(programs=programs,program_inventory={unknown['key']:unknown},files=files,languages=[],benchmarks=[])
    raw = binder.encoded(catalog)
    projection = binder.project(files[py]['code'],[dict(start=2,end=2)]); projected = binder.sha(projection)
    tools = {'tools/logical_source_units.py':b'python-julia-tool', 'tools/julia_source_tree.jl':b'julia-helper',
             'tools/clojure_logical_source_units.py':b'clojure-tool',
             (binder.CLOJURE/'capture.clj').as_posix():b'clojure-helper',
             (binder.CLOJURE/'test_replay.py').as_posix():b'clojure-tests',
             (binder.CLOJURE/'native-capture.json.gz').as_posix():b'native-capture'}
    for name, content in tools.items():
        path = root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(content)
    v2 = dict(schema='benchmark-source-normalization.v2',catalog_sha256=binder.sha(raw),
        policy=dict(id=binder.V2_POLICY,status='native-qualified-exact-source-subset'),
        input_evaluation=False,macro_expansion=False,lowering=False,canonical_fields_changed=False,source_bytes_changed=False,
        tool_pins={path:binder.sha(tools[path]) for path in ('tools/logical_source_units.py','tools/julia_source_tree.jl')},
        profiles={'b:py':dict(status='qualified-exact-source-native-owners',policy=binder.V2_POLICY,
            language='python',benchmark='b',retained_loc=7,sources=[projected],logical_loc=1)},
        sources={projected:dict(accepted=True,source_sha256=projected,full_source_sha256=py,
            support_line_ranges=[dict(start=2,end=2)],coverage=dict(unowned_significant_tokens=0),logical_loc=1,
            owners=[dict(start=0,end=3,units=1,source_sha256=binder.sha(projection[:3]))])})
    bindings = [dict(source_sha256=digest,job=digest,role='application' if digest==app else 'runtime-support',
                     included_in_application=digest==app) for digest in clj['files']]
    inputs = dict(catalog_sha256=binder.sha(raw),policy=binder.CLOJURE_POLICY,
        programs={'b:clj':dict(files=bindings)},jobs={digest:dict(source_sha256=digest,text=files[digest]['code']) for digest in (app,support)})
    outcomes = {digest:dict(status='native-qualified-exact-source-subset',logical_units=1,
                          coverage=dict(unowned_significant_tokens=0),source_tree={'not_for_browser':True}) for digest in (app,support)}
    clojure = dict(schema='clojure-logical-source-qualification.v1',policy=binder.CLOJURE_POLICY,
        status='native-qualified-exact-source-subset',canonical_changed=False,inputs_sha256=binder.sha(binder.encoded(inputs)),
        programs={'b:clj':dict(status='native-qualified-exact-source-subset',retained_loc=7,files=bindings,
            application_logical_units=1,submitted_logical_units=2,excluded_support_logical_units=1)},outcomes=outcomes)
    policy = dict(id=binder.CLOJURE_POLICY)
    review = dict(decision='qualified-exact-source-subset',approved_source_scope=dict(policy=binder.CLOJURE_POLICY,
        policy_sha256=binder.sha(binder.encoded(policy)),tool_sha256=binder.sha(tools['tools/clojure_logical_source_units.py']),
        helper_sha256=binder.sha(tools[(binder.CLOJURE/'capture.clj').as_posix()]),
        tests_sha256=binder.sha(tools[(binder.CLOJURE/'test_replay.py').as_posix()]),
        native_capture_sha256=binder.sha(tools[(binder.CLOJURE/'native-capture.json.gz').as_posix()]),
        source_proof_sha256=binder.sha(binder.encoded(outcomes))),
        current_projection=dict(report_sha256=binder.sha(binder.encoded(clojure)),inputs_sha256=binder.sha(binder.encoded(inputs)),programs=['b:clj']))
    reports = {name:binder.encoded(doc) for name,doc in dict(v2=v2,clojure=clojure,inputs=inputs,policy=policy,review=review).items()}
    return catalog, raw, reports


class Binding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.catalog,self.raw,self.reports=fixture(self.root)
    def tearDown(self): self.temp.cleanup()
    def bind(self, reports=None, catalog=None, raw=None):
        return binder.bind(catalog or self.catalog,raw or self.raw,reports or self.reports,self.root)
    def test_compact_partial_scoped_projection_preserves_evidence(self):
        before=copy.deepcopy(self.catalog)
        metadata,profiles=self.bind()
        self.assertEqual(metadata['coverage']['qualified_profiles'],2)
        self.assertEqual(metadata['coverage']['retained_profiles'],3)
        self.assertNotIn('b:unknown',profiles)
        self.assertEqual(profiles['b:clj']['application'],1)
        self.assertEqual(profiles['b:clj']['submitted'],2)
        self.assertEqual(profiles['b:clj']['excluded_support'],1)
        self.assertIsNone(profiles['b:py']['submitted'])
        self.assertNotIn('source_tree',binder.encoded(profiles).decode())
        self.assertNotIn('"owners":',binder.encoded(profiles).decode())
        self.assertEqual(self.catalog,before)
        with patch.object(build_site,'bind_logical_source_units',side_effect=lambda c,r,p:binder.bind(c,r,p,self.root)):
            projected=build_site.browser_data(self.catalog,catalog_raw=self.raw,logical_reports=self.reports)
            self.assertEqual(projected['programs']['b:py']['logical_source_units'],profiles['b:py'])
            self.assertNotIn('logical_source_units',projected['program_inventory']['b:unknown'])
            self.assertEqual(projected['logical_source_units'],metadata)
    def test_report_pin_status_scope_and_proof_mutations_fail_closed(self):
        edits=[('v2',lambda d:d.update(catalog_sha256='0'*64)),
               ('v2',lambda d:d.update(input_evaluation=True)),
               ('v2',lambda d:d['tool_pins'].clear()),
               ('v2',lambda d:d['profiles']['b:py'].update(logical_loc=2)),
               ('v2',lambda d:next(iter(d['sources'].values())).update(accepted=False)),
               ('v2',lambda d:next(iter(d['sources'].values()))['coverage'].update(unowned_significant_tokens=1)),
               ('clojure',lambda d:d['programs']['b:clj'].update(application_logical_units=2)),
               ('inputs',lambda d:d.update(catalog_sha256='0'*64)),
               ('policy',lambda d:d.update(id='unreviewed')),
               ('review',lambda d:d.update(decision='pending')),
               ('review',lambda d:d['approved_source_scope'].update(tests_sha256='0'*64)),
               ('review',lambda d:d['current_projection'].update(programs=[]))]
        for name,edit in edits:
            with self.subTest(name=name,edit=edit):
                reports=copy.deepcopy(self.reports); doc=json.loads(reports[name]);edit(doc);reports[name]=binder.encoded(doc)
                with self.assertRaisesRegex(ValueError,'Invalid qualified logical source units'): self.bind(reports)
    def test_changed_producer_native_capture_or_tests_rejected(self):
        for name in ('tools/logical_source_units.py','tools/julia_source_tree.jl','tools/clojure_logical_source_units.py',
                     (binder.CLOJURE/'native-capture.json.gz').as_posix(),(binder.CLOJURE/'test_replay.py').as_posix()):
            with self.subTest(path=name):
                path=self.root/name; before=path.read_bytes();path.write_bytes(before+b'changed')
                with self.assertRaisesRegex(ValueError,'Invalid qualified logical source units'): self.bind()
                path.write_bytes(before)
    def test_changed_source_roles_or_embedded_projection_rejected(self):
        for mode in ('code','role','range','override'):
            with self.subTest(mode=mode):
                catalog=copy.deepcopy(self.catalog); row=catalog['programs']['b:py'];digest=row['files'][0]
                if mode=='code': catalog['files'][digest]['code']+='drift'
                if mode=='role': row['file_roles'][digest]['role']='runtime-support'
                if mode=='range': row['file_roles'][digest]['support_line_ranges']=[]
                if mode=='override': row['file_roles'][digest]['code']='different displayed source'
                raw=binder.encoded(catalog);reports=copy.deepcopy(self.reports)
                for name in ('v2','inputs'):
                    doc=json.loads(reports[name]);doc['catalog_sha256']=binder.sha(raw);reports[name]=binder.encoded(doc)
                with self.assertRaisesRegex(ValueError,'Invalid qualified logical source units'):self.bind(reports,catalog,raw)


if __name__=='__main__': unittest.main()
