"""Focused exact-source extension tests. No JVM/compiler/formatter execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import clojure_logical_extensions as tool

ROOT=Path(__file__).resolve().parents[1]
INPUTS=json.loads((ROOT/tool.SUPPLEMENT/'inputs.json').read_bytes())
PARENT='193e26ad8dfd011fd1835d9d67be04bb223d088e6cdd3e2d6302ca8cae2f46d4'


def fixture(root):
    files={digest:dict(code=INPUTS['jobs']['file:'+digest]['text'],sha256=digest) for digest in (PARENT,tool.SOURCE,tool.SUPPORT)}
    parts=lambda digest:[dict(source_sha256=digest,job='file:'+digest,role='application',included_in_application=True),
        dict(source_sha256=tool.SUPPORT,job='file:'+tool.SUPPORT,role='runtime-support',included_in_application=False)]
    profiles={f'nbody:old-{i}':dict(files=parts(PARENT),retained_loc=109,retained_physical_loc=49) for i in range(21)}
    base_inputs=dict(programs=profiles)
    base_report=dict(programs={key:dict(retained_loc=109,application_logical_units=63,submitted_logical_units=81,excluded_support_logical_units=18) for key in profiles})
    programs={key:dict(key=key,language='clojure',benchmark='nbody',files=[PARENT,tool.SUPPORT],loc=109,physical_loc=49,
        file_roles={PARENT:dict(role='application'),tool.SUPPORT:dict(role='runtime-support')}) for key in profiles}
    programs[tool.PROFILE]=dict(key=tool.PROFILE,language='clojure',benchmark='nbody',files=[tool.SOURCE,tool.SUPPORT],loc=109,physical_loc=49,
        file_roles={tool.SOURCE:dict(role='application'),tool.SUPPORT:dict(role='runtime-support')})
    catalog=dict(programs=programs,program_inventory={},files=files)
    for path,value in ((tool.BASE/'inputs.json',base_inputs),(tool.BASE/'qualification.json',base_report),(tool.BASE/'independent-review.json',dict(original=True))):
        (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_bytes(tool.encoded(value))
    proof=dict(source_records=[dict(source_sha256=tool.SOURCE,role='application',included_in_application=True,logical_units=63),
        dict(source_sha256=tool.SUPPORT,role='runtime-support',included_in_application=False,logical_units=18)],
        artifacts={str(path):tool.ref(root,path) for path in (tool.BASE/'inputs.json',tool.BASE/'qualification.json',tool.BASE/'independent-review.json')})
    review=dict(decision='fixture-reviewed')
    for path,value in ((tool.PACKET/'proof.json',proof),(tool.PACKET/'independent-review.json',review)):
        (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_bytes(tool.encoded(value))
    return catalog,proof,review

class Projection(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.catalog,self.proof,self.review=fixture(self.root)
    def tearDown(self):self.tmp.cleanup()
    def project(self,catalog=None):
        catalog=catalog or self.catalog;raw=tool.encoded(catalog)
        (self.root/'data').mkdir(exist_ok=True);(self.root/'data/benchmarks.json').write_bytes(raw)
        with patch.object(tool,'validate',return_value=(self.proof,self.review)):
            return tool.project(catalog,raw,self.root)
    def test_exact_old21_plus_one_source_extension_compact_projection(self):
        before=copy.deepcopy(self.catalog);projection=self.project()
        self.assertEqual(len(projection['base_profiles']),21)
        self.assertEqual(list(projection['profiles']),[tool.PROFILE])
        row=projection['profiles'][tool.PROFILE]
        self.assertEqual([row[k] for k in ('application','submitted','excluded_support')],[63,81,18])
        self.assertEqual(row['sources'][1]['application'],0)
        self.assertIn('report_sha256',row['evidence']);self.assertNotIn('source_tree',tool.encoded(projection).decode())
        self.assertEqual(self.catalog,before)
    def test_source_role_count_and_key_drift_fail_closed(self):
        for edit in (lambda d:d['files'][tool.SOURCE].update(code='changed'),
                     lambda d:d['programs'][tool.PROFILE]['file_roles'][tool.SUPPORT].update(role='application-helper'),
                     lambda d:d['programs'][tool.PROFILE].update(loc=108),
                     lambda d:d['programs']['nbody:old-0'].update(files=[tool.SOURCE,tool.SUPPORT]),
                     lambda d:d['programs']['nbody:old-0']['file_roles'][PARENT].update(support_line_ranges=[dict(start=1,end=1)]),
                     lambda d:d['programs'].update({'nbody:extra':copy.deepcopy(d['programs'][tool.PROFILE])}),
                     lambda d:d['programs'].pop('nbody:old-0')):
            catalog=copy.deepcopy(self.catalog);edit(catalog)
            with self.assertRaises(ValueError):self.project(catalog)
    def test_same_source_matching_count_does_not_admit_another_profile(self):
        catalog=copy.deepcopy(self.catalog);catalog['programs']['nbody:borrowed']=catalog['programs'].pop(tool.PROFILE)
        with self.assertRaisesRegex(ValueError,'inventory'):self.project(catalog)
    def test_unapproved_saved_review_is_rejected(self):
        # This rejection happens before optional artifacts can be consulted.
        (self.root/tool.PACKET/'proof.json').write_bytes(tool.encoded(dict(schema='clojure-exact-source-owner-extension-proof.v1',
            policy=tool.POLICY,profile=tool.PROFILE,status='source-qualified-pending-independent-review',generic_language_certificate=False,
            canonical_changed=False,native_processes_executed=0,native_qualification_sha256=tool.NATIVE_QUAL)))
        with self.assertRaisesRegex(ValueError,'review'):tool.validate(self.root)

class SavedNativeProof(unittest.TestCase):
    def test_saved_four_source_native_owner_proof_replays_without_runtime(self):
        proof=tool.source_proof(ROOT)
        self.assertEqual(proof['application_logical_units'],63)
        self.assertEqual(proof['submitted_logical_units'],81)
        self.assertEqual(proof['excluded_support_logical_units'],18)
        self.assertEqual(proof['native_jobs_replayed'],4)
        self.assertEqual(proof['unowned_significant_tokens'],0)
        self.assertFalse(proof['generic_language_certificate'])
        self.assertEqual(set(r['source_sha256'] for r in proof['source_records']),{tool.SOURCE,tool.SUPPORT})

if __name__=='__main__':unittest.main()
