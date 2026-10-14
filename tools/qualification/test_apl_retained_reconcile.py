"""Small saved-metadata and injected closure faults; no native/runtime replay."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH=Path(__file__).with_name('apl_retained_reconcile.py')
spec=importlib.util.spec_from_file_location('apl_retained_under_test',PATH)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
INDEX,DOCUMENTS,RECEIPTS,SOURCES=a.metadata()


def check(documents=DOCUMENTS,receipts=RECEIPTS,sources=SOURCES,index=INDEX):
    return a.reconcile(index,documents,receipts,sources)


class Retained(unittest.TestCase):
    def changed(self,name,operation):
        documents=dict(DOCUMENTS);documents[name]=copy.deepcopy(DOCUMENTS[name]);operation(documents[name])
        with self.assertRaises((ValueError,KeyError)):check(documents)

    def test_actual_saved_metadata_joins_preserve_exact_scope(self):
        r=check()
        self.assertEqual((r['accepted_native_observations'],r['apl_native_observations'],r['matched_control_observations']),(42,27,15))
        self.assertEqual((len(r['profiles']),r['selected_source_identities'],r['timing_alias_labels']),(16,9,2))
        self.assertEqual(r['report_only_native_attempts'],[44]);self.assertEqual(r['preserved_failed_attempts'],[58,75])
        self.assertEqual(r['original_report_status'],'partial');self.assertEqual(r['recovery_owner_status'],'complete')
        self.assertFalse(r['chart_admission']);self.assertFalse(r['file_integrity_verified']);self.assertFalse(r['full_suite_qualified'])

    def test_prefix_and_failed_dispositions_cannot_be_rewritten(self):
        self.changed('old_report',lambda r:r['attempts'][81].update(seconds=1))
        self.changed('report',lambda r:r.update(status='complete'))
        self.changed('report',lambda r:r['programs'][a.TREE].update(samples_seconds=[1,2,3],measurement_status='measured'))

    def test_missing_only_recovery_cannot_repeat_or_reorder(self):
        self.changed('manifest',lambda m:m['planned_slots'].reverse())
        self.changed('admission',lambda d:d.update(already_running_sample_restarted=True))
        self.changed('report',lambda d:d['sample84_recovery'].update(fresh_attempts=4))

    def test_raw_and_supervisor_remain_distinct_exact_artifacts(self):
        records=dict(RECEIPTS);records[87]=copy.deepcopy(RECEIPTS[87]);records[87]['raw']['seconds']=1
        with self.assertRaisesRegex(ValueError,'sampler fields'):check(receipts=records)
        records=dict(RECEIPTS);records.pop(84)
        with self.assertRaises(KeyError):check(receipts=records)

    def test_kernel_event_pid_birth_flags_and_exit_status_fail_closed(self):
        self.changed('event1',lambda v:v.update(data=256))
        self.changed('exit68666',lambda v:v.update(pid=1))
        self.changed('registered',lambda v:v['identities'].update({'68666':'another process'}))
        self.changed('observer',lambda v:v.update(exit_status_origin='synthetic waitpid'))

    def test_recovery84_requires_exact_additive_enrichment(self):
        records=dict(RECEIPTS);records[84]=copy.deepcopy(RECEIPTS[84]);records[84]['supervisor']['sampler_wait_status']=1
        with self.assertRaisesRegex(ValueError,'additive reconstruction'):check(receipts=records)
        self.changed('admission',lambda v:v['recovered84_checks'].update(sampler_exited_normally=False))

    def test_fasta_command_repair_does_not_erase_failure58(self):
        self.changed('report',lambda r:r['argv_revision']['new_command'].append('--other'))
        self.changed('argv_qualification',lambda r:r.update(status='failed'))
        self.changed('report',lambda r:r['attempts'][57].update(qualified=True))

    def test_old_report_only_control_cannot_gain_new_lifecycle_claim(self):
        row=DOCUMENTS['report']['programs']['mandelbrot:mech-control-for-apl-medium-v3']
        record=copy.deepcopy(DOCUMENTS['report']['attempts'][43]);record['sampler_wait_status']=0
        with self.assertRaisesRegex(ValueError,'invented supervisor'):a.receipt(record,row,RECEIPTS,a.consumer(INDEX)._execution_fingerprint)

    def test_output_and_process_ownership_are_replayed_not_trusted_flags(self):
        row=DOCUMENTS['report']['programs'][a.KEY]
        original=DOCUMENTS['report']['attempts'][86]
        for field,value in [('stdout_sha256','0'*64),('sampler_wait_status',1),('valid_environment',False),('seconds',float('nan'))]:
            record=copy.deepcopy(original);record[field]=value
            with self.assertRaises(ValueError):a.receipt(record,row,RECEIPTS,a.consumer(INDEX)._execution_fingerprint)

    def test_exact_counts_source_bytes_and_alias_ownership_required(self):
        self.changed('counts',lambda v:v.update(canonical_loc_qualified=False))
        self.changed('report',lambda v:v['programs']['nbody:nbody-apl-optimized-canonical-v2']['attempts'].append(76))
        sources=dict(SOURCES);identity=DOCUMENTS['counts']['profiles'][0]['source_identity'];sources[identity]+=b'\n'
        with self.assertRaisesRegex(ValueError,'Counted bytes'):check(sources=sources)

    def test_inherited_pins_and_native_receipt_route_cannot_be_removed(self):
        key=next(iter(DOCUMENTS['manifest']['pins']))
        self.changed('status',lambda v:v['retained_input_and_actual_result_pins'].pop(key))
        index=copy.deepcopy(INDEX);index['receipts']['87']['raw']['recorded_path']='/wrong/path'
        with self.assertRaisesRegex(ValueError,'route or pin'):check(index=index)

    def test_audited_work_correctness_and_serial_primitive_policy_bound(self):
        row=DOCUMENTS['report']['programs'][a.KEY];origin=next(r for r in DOCUMENTS['audit']['programs'] if r['key']==a.KEY)
        for field,value in [('algorithm',dict(strict=True,native_benchmark_kernel=True)),
                            ('adversarial_validation_status','pending'),('small_validation',dict(reference_match=False))]:
            changed=copy.deepcopy(row);changed[field]=value
            with self.assertRaises(ValueError):a.source_work(changed,origin,DOCUMENTS,
                DOCUMENTS['status']['retained_input_and_actual_result_pins'],INDEX)
        self.changed('work_knucleotide',lambda v:v.update(all_map_cases_per_variant=0))
        self.changed('work_mandelbrot',lambda v:v['rows'][0]['work_trace'].update(reference_match=False))
        self.changed('work_fasta',lambda v:v['rows'][0].update(passed=False))


class Closure(unittest.TestCase):
    def test_immutable_original_pins_survive_consumer_map_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'evidence';path.write_bytes(b'original');files=a.Files();files.verify(path,hashlib.sha256(b'original').hexdigest())
            frozen=tuple(files.pins.items());files.pins.clear();path.write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError,'Physical evidence'):files.final(frozen)

    def test_final_consumer_and_restoration_execute_before_lease_release(self):
        events=[]
        class FakeFiles:
            def __init__(self):self.pins={}
            def verify(self,path,digest):self.pins[str(path)]=digest
            def final(self,original):events.append('physical-final');self.test_original=original
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.write_bytes(b'')
            def consumer_check():
                events.append('consumer-final')
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):a.fcntl.flock(other,a.fcntl.LOCK_EX|a.fcntl.LOCK_NB)
                raise ValueError('injected output mutation')
            def restore():
                events.append('restore')
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):a.fcntl.flock(other,a.fcntl.LOCK_EX|a.fcntl.LOCK_NB)
            with patch.object(a,'LOCK',lock),patch.object(a,'LOCK_INODE',lock.stat().st_ino),patch.object(a,'Files',FakeFiles),\
                 patch.object(a,'metadata',return_value=(INDEX,DOCUMENTS,RECEIPTS,SOURCES)),patch.object(a,'reconcile',return_value={}):
                with self.assertRaisesRegex(ValueError,'injected output'):
                    with a.review_context('1'*64,on_exit_failure=restore,final_consumer_check=consumer_check):events.append('body')
            self.assertEqual(events,['body','physical-final','consumer-final','restore'])
            with lock.open('r+') as other:a.fcntl.flock(other,a.fcntl.LOCK_EX|a.fcntl.LOCK_NB)

    def test_mutex_replacement_during_final_pins_is_detected(self):
        events=[]
        with tempfile.TemporaryDirectory() as directory:
            lock=Path(directory)/'lock';lock.write_bytes(b'')
            class FakeFiles:
                def __init__(self):self.pins={}
                def verify(self,path,digest):self.pins[str(path)]=digest
                def final(self,original):lock.rename(lock.with_suffix('.original'));lock.write_bytes(b'')
            with patch.object(a,'LOCK',lock),patch.object(a,'LOCK_INODE',lock.stat().st_ino),patch.object(a,'Files',FakeFiles),\
                 patch.object(a,'metadata',return_value=(INDEX,DOCUMENTS,RECEIPTS,SOURCES)),patch.object(a,'reconcile',return_value={}):
                with self.assertRaisesRegex(ValueError,'lease identity'):
                    with a.review_context('1'*64,on_exit_failure=lambda:events.append('restore'),
                            final_consumer_check=lambda:events.append('consumer')):pass
            self.assertEqual(events,['restore'])


if __name__=='__main__':unittest.main()
