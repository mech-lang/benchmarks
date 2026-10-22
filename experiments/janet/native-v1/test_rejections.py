import json
from pathlib import Path
import unittest
from rejections import validate

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'experiments/janet/source-v3/revcomp.janet'
CORPUS=ROOT/'experiments/shared/bounded-corpus-v1/cases'

class RejectionTests(unittest.TestCase):
    def test_captures_and_corruptions(self):
        manifest=json.loads((CORPUS/'manifest.json').read_bytes())
        for case in manifest['cases']:
            if case['expected_exit']==0: continue
            directory=Path(__file__).parent/'revcomp-run-v1'/case['case']
            raw=(CORPUS/case['stdin']['path']).read_bytes()
            stdout=(directory/'stdout.bin').read_bytes(); stderr=(directory/'stderr.bin').read_bytes()
            result=validate(case,raw,stdout,stderr,1,SOURCE)
            self.assertTrue(result['janet_rejection_contract_pass'])
            for out,err,code in [(stdout,stderr,0),(stdout,b'',1),(stdout,stderr[:-1],1),
                                 (stdout+b'x',stderr,1),(stdout,b'error: unrelated\n',1),
                                 (stdout,stderr.replace(b'record offset',b'file offset'),1)]:
                with self.assertRaises(AssertionError): validate(case,raw,out,err,code,SOURCE)

if __name__=='__main__':unittest.main()
