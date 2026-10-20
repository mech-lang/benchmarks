"""Focused synthetic formatter-only proposal tests; no native execution."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nim_formatter_overlay',ROOT/'tools/qualification/nim_formatted_overlay.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
REPORT=json.loads((ROOT/'experiments/source-formatting/v1/nim-run-v1/replay-v1/qualification.json').read_bytes())
SOURCE=(ROOT/'experiments/source-formatting/v1/nim-run-v1/input.nim').read_text()

def fixture():
    target=dict(key=tool.PROFILE,language='nim',benchmark='knucleotide',id='new',files=[tool.SOURCE],
        file_roles={tool.SOURCE:dict(role='application',included_in_application_loc=True)},
        loc=72,physical_loc=64,x=72/37,y=2,seconds=2,samples=[1.9,2,2.1],timing_alias_of=None,
        formatted_loc=None,formatted_loc_status='pending',formatted_loc_complete=False,formatted_x=None)
    parent=dict(key='knucleotide:parent',language='nim',benchmark='knucleotide',id='old',files=['parent'],
        loc=37,physical_loc=39,x=1,y=3,seconds=3,samples=[2.9,3,3.1],
        formatted_loc=34,formatted_loc_status='qualified',formatted_loc_complete=True,formatted_x=1)
    return dict(programs={target['key']:target,parent['key']:parent},program_inventory={target['key']:copy.deepcopy(target)},
        files={tool.SOURCE:dict(code=SOURCE), 'parent':dict(code='old source')},
        benchmarks=[dict(key='knucleotide',baseline_loc=37,baseline_seconds=1,baseline_formatted_loc=34,
            groups=[dict(language='nim',programs=[target['key'],parent['key']],fast=target['key'],small=parent['key'],
                         formatted_fast=parent['key'],formatted_small=parent['key'])])],
        reference_summary=[dict(lang='nim',fast=dict(x=72/37,y=2),small=dict(x=1,y=3))],
        formatted_reference_summary=[dict(lang='nim',fast=dict(x=1,y=3),small=dict(x=1,y=3))])

class Overlay(unittest.TestCase):
    def test_only_exact_formatter_projection_changes(self):
        before=fixture();saved=copy.deepcopy(before);after=tool.transform(before,REPORT)
        self.assertEqual(before,saved)
        self.assertEqual(tool.immutable_projection(after),tool.immutable_projection(before))
        for pool in ('programs','program_inventory'):
            row=after[pool][tool.PROFILE]
            self.assertEqual(row['formatted_loc'],66);self.assertTrue(row['formatted_loc_complete'])
            self.assertEqual(row['formatted_x'],66/34);self.assertEqual(row['samples'],[1.9,2,2.1])
        group=after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['formatted_fast'],tool.PROFILE);self.assertEqual(group['formatted_small'],'knucleotide:parent')
        self.assertEqual(after['formatted_reference_summary'][0]['fast'],dict(x=66/34,y=2))
        self.assertEqual(after['reference_summary'],before['reference_summary'])
    def test_source_partition_status_and_duplicate_drift_fail(self):
        for edit in (lambda d:d['files'][tool.SOURCE].update(code=SOURCE+'changed'),
                     lambda d:d['programs'][tool.PROFILE]['file_roles'][tool.SOURCE].update(role='runtime-support'),
                     lambda d:d['programs'][tool.PROFILE].update(formatted_loc_complete=True),
                     lambda d:d['program_inventory'][tool.PROFILE].update(seconds=999)):
            before=fixture();edit(before)
            with self.assertRaises(ValueError):tool.transform(before,REPORT)
    def test_qualification_scope_and_value_cannot_be_borrowed(self):
        for field,value in [('formatted_loc',67),('source_sha256','0'*64),('provider','community-project'),('status','pending')]:
            report=copy.deepcopy(REPORT);report[field]=value
            with self.assertRaises(ValueError):tool.transform(fixture(),report)
    def test_second_application_is_not_silent(self):
        after=tool.transform(fixture(),REPORT)
        with self.assertRaisesRegex(ValueError,'no longer'):tool.transform(after,REPORT)

if __name__=='__main__':unittest.main()
