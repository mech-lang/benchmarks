"""Pure lossless partition tests using the two closed native stdout captures."""
import copy
import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name('typescript_v8_stdout.py');S=importlib.util.spec_from_file_location('stdout_partition',P)
m=importlib.util.module_from_spec(S);S.loader.exec_module(m)
P=P.with_name('typescript_single_entry_remaining.py');S=importlib.util.spec_from_file_location('capture',P)
b=importlib.util.module_from_spec(S);S.loader.exec_module(b)


class PartitionTests(unittest.TestCase):
    def args(self,bench):
        folder,pid,name=('run-v1/01-binarytrees',175,'mainThread') if bench=='binarytrees' else ('run-pi-v1/00-pidigits',2755,'calculatePi')
        d=b.PACKET/folder
        return [(d/'stdout.bin').read_bytes(),b.s.expected_output(bench),pid,name,b''.join(x.read_bytes() for x in sorted(d.glob('code-*.asm')))]

    def test_actual_full_outputs_lossless(self):
        for bench,count in [('binarytrees',11),('pidigits',1000)]:
            with self.subTest(bench=bench):
                args=self.args(bench);r=m.split(*args)
                self.assertEqual(r['application_lines'],count)
                self.assertEqual(sum(x['bytes'] for x in r['streams'].values()),len(args[0]))
                self.assertEqual(b''.join(args[0][x['start']:x['end']] for x in r['segments']),args[0])
                for x in r['segments']:self.assertEqual(x['sha256'],m.digest(args[0][x['start']:x['end']]))
                self.assertFalse(r['required_work_qualified'])

    def test_missing_changed_duplicate_application_rejected(self):
        for mode in ['missing','changed','duplicate']:
            with self.subTest(mode=mode):
                a=self.args('binarytrees');first=a[1].splitlines(keepends=True)[0]
                replacement={'missing':b'','changed':first.replace(b'8388607',b'8388606'),'duplicate':first+first}[mode]
                a[0]=a[0].replace(first,replacement,1)
                with self.assertRaises(AssertionError):m.split(*a)

    def test_unknown_indented_or_plain_diagnostic_rejected(self):
        for line in [b'unknown\n',b'   unknown\n',b'123456\n',b' - undocumented: 1\n']:
            with self.subTest(line=line):
                a=self.args('binarytrees');a[0]+=line
                with self.assertRaises(AssertionError):m.split(*a)

    def test_wrong_pid_outer_and_truncation_rejected(self):
        for mode in ['pid','outer','truncated']:
            with self.subTest(mode=mode):
                a=self.args('binarytrees')
                if mode=='pid':a[2]=176
                elif mode=='outer':a[3]='another'
                else:a[0]=a[0][:-1]
                with self.assertRaises(AssertionError):m.split(*a)

    def test_incomplete_disassembly_rejected(self):
        a=self.args('binarytrees');a[0]=a[0].replace(b'Source Position Table (size = 11)\n',b'',1)
        with self.assertRaises(AssertionError):m.split(*a)

    def test_split_deoptimization_requires_code_pair(self):
        a=self.args('pidigits');r=m.split(*a)
        self.assertEqual([x['optimization_id'] for x in r['split_deoptimization_records']],[34,24])
        self.assertEqual([x['optimization_id_header_verified'] for x in r['split_deoptimization_records']],[True,False])
        for code in [b'',a[4].replace(b'[marking dependent code',b'[other dependent code',1)]:
            args=a.copy();args[4]=code
            with self.assertRaises(AssertionError):m.split(*args)
        a[0]=a[0].replace(b') (opt id 34)',b') (opt id 35)')
        with self.assertRaises(AssertionError):m.split(*a)


if __name__=='__main__':unittest.main()
