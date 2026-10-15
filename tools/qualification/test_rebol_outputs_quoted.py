"""Exact diagnostic correction tests; no native process or lease acquisition."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

old=load('quoted_frozen_outputs',HERE/'rebol_outputs.py')
new=load('quoted_corrected_outputs',HERE/'rebol_outputs_quoted.py')
RAW=b'\n** User error: "Unsupported revcomp sequence byte"\n\n'
CASES=[('extended-invalid-space',32),('extended-invalid-tab',9),('extended-invalid-nul',0),
       ('extended-invalid-high-byte',255),('extended-inline-header-marker',62),
       ('extended-inline-comment-marker',59),('extended-invalid-reverse-order',63)]

def rejection(name='extended-invalid-space',code=32):
    return dict(benchmark='revcomp',case=name,expected_exit='nonzero',
                validation='language-specific-invalid-iupac',expected_invalid_byte=code)

def success(benchmark,raw,method='exact-complete-bytes'):
    return dict(benchmark=benchmark,case='fixture',validation=method,expected_exit=0,
                expected=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))

class QuotedRejectionTests(unittest.TestCase):
    def test_actual_retained_capture_is_exact_and_original_checker_stays_failed(self):
        directory=ROOT/'experiments/rebol/bounded-v1/tree-continuation-v1/run-v1/140-revcomp-extended-invalid-space'
        stdout=(directory/'stdout.bin').read_bytes();stderr=(directory/'stderr.bin').read_bytes()
        process=json.loads((directory/'process.json').read_bytes())
        self.assertEqual(stdout,b'');self.assertEqual(stderr,RAW);self.assertEqual(len(stderr),53)
        self.assertEqual(process['status'],'failed');self.assertEqual(process['exit_status'],1)
        self.assertEqual(process['error'],'Native command exited unsuccessfully')
        with self.assertRaises(ValueError):old.validate(rejection(),stdout,stderr,1,None)
        record=new.validate(rejection(),stdout,stderr,1,None)
        self.assertTrue(record['output_contract_satisfied'])
        self.assertFalse(record['native_process_verified']);self.assertFalse(record['chart_admission'])
        self.assertFalse(record['source_work_qualified']);self.assertFalse(record['native_rejection_prequalified'])

    def test_seven_contracts_keep_oracle_metadata_and_one_exact_message(self):
        for name,code in CASES:
            result=new.validate(rejection(name,code),b'',RAW,1,None)
            self.assertEqual(result['expected_invalid_byte'],code)
            self.assertFalse(result['invalid_byte_emitted'])
            self.assertEqual(result['language'],'rebol')
            self.assertEqual(result['stderr_sha256'],hashlib.sha256(RAW).hexdigest())

    def test_unquoted_generic_extra_and_altered_diagnostics_are_rejected(self):
        for stderr in (old.NEGATIVE_STDERR,b'',RAW.replace(b'"',b''),RAW.replace(b'User',b'user'),
                       RAW.replace(b'Unsupported revcomp sequence byte',b'Unknown error'),
                       RAW[:-1],RAW+b'\n',b'warning\n'+RAW,RAW.replace(b'\n',b'\r\n'),
                       RAW+b'** Where: emit-record\n',RAW+b'** Near: do make error! message\n',
                       RAW.replace(b'byte"',b'byte 32"')):
            with self.subTest(stderr=stderr),self.assertRaises(ValueError):
                new.validate(rejection(),b'',stderr,1,None)

    def test_wrong_exit_partial_stdout_and_nonbyte_streams_are_rejected(self):
        for status,stdout,stderr in ((0,b'',RAW),(2,b'',RAW),(-9,b'',RAW),(True,b'',RAW),
                                    (1,b'>r\n',RAW),(1,b'\n',RAW),(1,'',RAW),(1,b'',RAW.decode())):
            with self.subTest(status=status,stdout=stdout),self.assertRaises(ValueError):
                new.validate(rejection(),stdout,stderr,status,None)

    def test_rejection_cannot_change_corpus_or_expected_output_contract(self):
        for change in (dict(benchmark='fasta'),dict(expected_exit=1),dict(expected_invalid_byte=True),
                       dict(expected_invalid_byte=-1),dict(expected_invalid_byte=256),dict(expected={})):
            case=dict(rejection(),**change)
            with self.subTest(change=change),self.assertRaises(ValueError):new.validate(case,b'',RAW,1,None)
        with self.assertRaises(ValueError):new.validate(rejection(),b'',RAW,1,b'')

    def test_success_results_and_signed_nanounit_boundaries_are_unchanged(self):
        energy=b'-0.169075164\n-0.000000005\n'
        cases=[(success('mandelbrot',b'P4\n9 1\n\xff\x80\x00'),b'P4\n9 1\n\xff\x80\x00',b'P4\n9 1\n\xff\x80\x00'),
               (success('fasta',b'>r\nACTG\n'),b'>r\nACTG\n',b'>r\nACTG\n'),
               (success('nbody',energy,'finite-two-energy-lines-within-1e-8'),b'-0.169075164\n0.000000005\n',energy)]
        for case,stdout,expected in cases:
            self.assertEqual(new.validate(case,stdout,b'',0,expected),old.validate(case,stdout,b'',0,expected))
        bad=[(cases[0][0],cases[0][1][:-1],b'',0,cases[0][2]),
             (cases[1][0],cases[1][1],b'warning\n',0,cases[1][2]),
             (cases[1][0],cases[1][1],b'',False,cases[1][2]),
             (cases[2][0],b'-0.169075164\n0.000000006\n',b'',0,energy),
             (cases[2][0],b'nan\n0.000000005\n',b'',0,energy)]
        for args in bad:
            for module in (old,new):
                with self.subTest(args=args,module=module.__name__),self.assertRaises(ValueError):module.validate(*args)

    def test_expected_pin_and_validation_method_guards_are_unchanged(self):
        raw=b'abc\n';base=success('fasta',raw)
        variants=[dict(base,validation='unknown'),dict(base,benchmark='nbody'),dict(base,expected_exit=False)]
        changed=copy.deepcopy(base);changed['expected']['sha256']='0'*64;variants.append(changed)
        changed=copy.deepcopy(base);changed['expected']['bytes']=True;variants.append(changed)
        for case in variants:
            for module in (old,new):
                with self.subTest(case=case,module=module.__name__),self.assertRaises(ValueError):module.validate(case,raw,b'',0,raw)

    def test_code_difference_is_only_exact_stderr_literal_and_explanation(self):
        self.assertEqual(hashlib.sha256((HERE/'rebol_outputs.py').read_bytes()).hexdigest(),
                         'c4b6e7f7ac9974d27e29db2c8159c0324f6a020fd081800bdf4b6cd090833974')
        def normalized(path):
            tree=ast.parse(path.read_bytes())
            for node in ast.walk(tree):
                if isinstance(node,(ast.Module,ast.FunctionDef)) and node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):
                    node.body.pop(0)
                if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='NEGATIVE_STDERR':
                    node.value=ast.Constant(value=b'normalized exact diagnostic')
            return ast.dump(tree,include_attributes=False)
        self.assertEqual(normalized(HERE/'rebol_outputs.py'),normalized(HERE/'rebol_outputs_quoted.py'))
        self.assertEqual(new.NEGATIVE_STDERR,RAW)
        self.assertEqual((new.CORPUS_SHA256,new.SUCCESS_CASES,new.REJECTION_CASES,new.NEGATIVE_EXIT_STATUS),
                         (old.CORPUS_SHA256,142,7,1))

if __name__=='__main__':unittest.main()
