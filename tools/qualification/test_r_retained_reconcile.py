"""Saved R report boundaries and provenance faults, without native work."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('r_retained_tests',Path(__file__).with_name('r_retained_reconcile.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def fixture():
    def read(relative):return json.loads((r.BASE/relative).read_text())
    report=read('results/timings-r.json')
    counts=json.loads(r.COUNTS.read_text())
    return dict(report=report,audit=read('source-audit-r.json'),manifest=read(r.CONTINUATION+'/manifest.json'),
        before=read(r.CONTINUATION+'/r-before.json'),counts=counts,
        sources={c['key']:(r.ROOT/c['source']['path']).read_bytes() for c in counts['profiles']},
        raw={n:read(r.CONTINUATION+'/attempts/'+Path(report['attempts'][n-1]['result_path']).name) for n in range(88,94)},
        supervised={n:read(r.CONTINUATION+'/attempts/'+Path(report['attempts'][n-1]['supervisor_result_path']).name) for n in range(88,94)})


class Retained(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values=fixture();cls.consumer=r.load_policy('consumer');cls.owners=r.load_policy('owners')

    def check(self,values):return r.reconcile(**values,consumer=self.consumer,owners=self.owners)

    def test_all_27_saved_observations_with_original_schema_boundaries(self):
        result=self.check(copy.deepcopy(self.values))
        self.assertEqual((result['subject_observations'],result['control_observations']),(18,9))
        self.assertEqual((result['report_only_observations'],result['separate_sampler_supervisor_observations']),(21,6))
        self.assertEqual(result['preserved_prior_observations'],87)
        self.assertFalse(result['physical_file_integrity_verified']);self.assertFalse(result['chart_admission'])
        self.assertEqual(result['native_processes_started'],0)

    def test_rewriting_original_prefix_is_rejected(self):
        values=copy.deepcopy(self.values);values['before']['attempts'][66]['seconds']+=1
        with self.assertRaisesRegex(ValueError,'rewritten'):self.check(values)

    def test_raw_and_supervisor_receipts_must_match_without_retrofilled_fields(self):
        for which,field,value in [('raw','seconds',1),('raw','qualified',True),('supervised','seconds',1)]:
            values=copy.deepcopy(self.values);values[which][88][field]=value
            with self.subTest(which=which,field=field),self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_invented_report_only_lifecycle_is_rejected(self):
        values=copy.deepcopy(self.values)
        for report in ('report','before'):values[report]['attempts'][67]['qualified']=True
        with self.assertRaisesRegex(ValueError,'original schema'):self.check(values)

    def test_group_cleanup_and_bad_reference_are_not_admitted(self):
        for field,value in [('remaining_group_members',[123]),('stdout_sha256','0'*64),('cleanup_error','failed')]:
            values=copy.deepcopy(self.values)
            for report in ('report','before'):values[report]['attempts'][67][field]=value
            with self.subTest(field=field),self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_changed_source_count_or_identity_is_rejected(self):
        for mutation in ('count','bytes','identity'):
            values=copy.deepcopy(self.values);key=values['counts']['profiles'][0]['key']
            if mutation=='count':values['counts']['profiles'][0]['canonical_loc']-=1
            elif mutation=='bytes':values['sources'][key]+=b'\n'
            else:values['counts']['profiles'][0]['source']['path']='archive/other.R'
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_recorded_order_and_native_registration_are_required(self):
        for mutation in ('order','group','check'):
            values=copy.deepcopy(self.values)
            if mutation=='order':values['report']['orders']['binarytrees'][0].reverse()
            else:
                for attempt in (values['report']['attempts'][87],values['supervised'][88]):
                    if mutation=='group':attempt['supervised_native_group']['inherited_common_mutex']=False
                    else:attempt['qualification_checks'].pop('pins_unchanged')
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,AssertionError)):self.check(values)

    def test_late_lease_replacement_fails_before_consumer_under_original_locks(self):
        original_loader=r.load_policy;core=original_loader('files')
        for replace_name in ('owner','common'):
            with tempfile.TemporaryDirectory() as directory:
                common=Path(directory)/'common';common.touch()
                owner=Path(directory)/'owner';owner.touch()
                replaced=owner if replace_name=='owner' else common
                retained=Path(directory)/'retained-original-lock'
                events=[]
                class Files:
                    def __init__(self):self.pins={}
                    def verify(self,path,digest):self.pins[str(path)]=digest
                    def read(self,path,digest):
                        self.verify(path,digest);raw=Path(path).read_bytes()
                        if str(path).endswith(r.CONTINUATION+'/manifest.json'):
                            d=json.loads(raw);d['owner_leases']=[str(owner)];return json.dumps(d).encode()
                        if str(path).endswith(('results/timings-r.json','source-audit-r.json')):
                            d=json.loads(raw);d['shared_timing_lock']=str(common);return json.dumps(d).encode()
                        return raw
                    def final_check(self,original_pins=()):
                        if not original_pins:raise AssertionError('Missing immutable input pins')
                        events.append('pins');replaced.rename(retained);replaced.touch()
                substitute=SimpleNamespace(**core.__dict__);substitute.Files=Files
                def cleanup():
                    with retained.open('r+') as other:
                        with self.assertRaises(BlockingIOError):r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
                    events.append('cleanup')
                with patch.object(r,'LOCK',common),patch.object(r,'LOCK_INODE',common.stat().st_ino),\
                     patch.object(r,'load_policy',side_effect=lambda name:substitute if name=='files' else original_loader(name)):
                    with self.assertRaisesRegex(ValueError,'lease pathname replaced'):
                        with r.review_files('0'*64,on_exit_failure=cleanup,final_consumer_check=lambda:events.append('consumer')):
                            events.append('body')
                self.assertEqual(events,['body','pins','cleanup'])


if __name__=='__main__':unittest.main()
