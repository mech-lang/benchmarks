"""Only the new byte-copy and invocation delta; no observer/runtime execution."""
from contextlib import nullcontext
import copy
import hashlib
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).with_name('rebol_extension_rebx_load.py')
m=types.ModuleType('rebx_test');m.__file__=str(SOURCE)
exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),m.__dict__)


class Rebx(unittest.TestCase):
    def test_exact_copy_missing_run_alias_and_changed_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();old=root/'old.dylib';alias=root/'new/image.rebx'
            raw=b'unchanged image\x00\x80\xff';old.write_bytes(raw);sha=hashlib.sha256(raw).hexdigest()
            def pin(pins,resolutions,path,expected):
                self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),expected)
                pins[str(path)]=expected;resolutions[str(path)]=str(path)
            e=types.SimpleNamespace(pin=pin,read_bytes=lambda p:Path(p).read_bytes(),
                physical=lambda p:self.assertEqual(p.resolve(),p))
            inspector=types.SimpleNamespace(kb=types.SimpleNamespace(atomic=nullcontext))
            with patch.multiple(m,OLD_IMAGE=old,ALIAS=alias,IMAGE_SHA=sha):
                with self.assertRaisesRegex(AssertionError,'missing'):
                    m.image_alias(e,inspector,{}, {},False)
                pins,resolutions={},{}
                record=m.image_alias(e,inspector,pins,resolutions,True)
                self.assertEqual(alias.read_bytes(),raw);self.assertEqual(old.read_bytes(),raw)
                self.assertEqual(pins,{str(old):sha,str(alias):sha})
                self.assertTrue(record['byte_identical']);self.assertFalse(record['binary_rebuilt'])
                self.assertEqual(m.image_alias(e,inspector,{}, {},False),record)
                alias.write_bytes(b'changed')
                with self.assertRaisesRegex(AssertionError,'every image byte'):
                    m.image_alias(e,inspector,{}, {},True)
                self.assertEqual(alias.read_bytes(),b'changed');self.assertEqual(old.read_bytes(),raw)

    def test_only_image_environment_changes_in_existing_scoped_smoke(self):
        original=dict(id='load-nine-commands-scoped-reads',directory='00-load-nine-commands-scoped-reads',
            command=['runtime','--quiet','--no-color','--do','exact existing two read exceptions','unchanged-smoke.reb'],
            environment=dict(HOME='fresh home',TMPDIR='fresh tmp',MECH_CLBG_REBOL_PRIMITIVES=str(m.OLD_IMAGE)),
            stdin_hex='0080ff',timeout_seconds=30)
        module=types.SimpleNamespace(held=lambda *a:None,build_plan=lambda *a:None,verify=lambda *a:None,
            corrected_slot=lambda *a:copy.deepcopy(original))
        m.attach(module,dict(path=str(SOURCE),sha256='a'*64),False)
        value=module.corrected_slot(None,None,None)
        expected=copy.deepcopy(original);expected['environment']['MECH_CLBG_REBOL_PRIMITIVES']=str(m.ALIAS)
        self.assertEqual(value,expected)
        self.assertEqual(original['environment']['MECH_CLBG_REBOL_PRIMITIVES'],str(m.OLD_IMAGE))


if __name__=='__main__':unittest.main()
