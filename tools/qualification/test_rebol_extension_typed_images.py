"""Synthetic files only: no compiler, loader, runtime or observer is executed."""
import ast
import copy
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
source = HERE/'rebol_extension_typed_images.py'
a = types.ModuleType('typed_images'); a.__file__ = str(source)
exec(compile(source.read_bytes(),str(source),'exec'),a.__dict__)
FROZEN = a.ROOT/'tools/qualification/julia_native_inspection.py'


def inspector():
    raw = FROZEN.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == a.INSPECTOR_SHA
    names = {'require','sha','physical','pin','macho','os_image','expand','tool_closure'}
    tree = ast.parse(raw)
    selected = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == names
    module = types.ModuleType('frozen_static_reader')
    module.__dict__.update(os=os,Path=Path,struct=struct,hashlib=hashlib)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(FROZEN),'exec'),module.__dict__)
    return module


def named(command, name, minimum):
    encoded = name.encode()+b'\0'
    length = (minimum+len(encoded)+7)//8*8
    return struct.pack('<III',command,length,minimum)+bytes(minimum-12)+encoded+bytes(length-minimum-len(encoded))


def image(path, kind=6, imports=('/usr/lib/libSystem.B.dylib',), rpaths=(), mode=0o444):
    commands = [named(0xc,n,24) for n in imports]+[named(0x8000001c,n,12) for n in rpaths]
    body = b''.join(commands)
    path.write_bytes(struct.pack('<8I',0xfeedfacf,0x0100000c,0,kind,len(commands),len(body),0,0)+body)
    path.chmod(mode)
    return path


class TypedRoots(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.i = inspector()

    def test_readonly_dylib_retains_exact_frozen_graph(self):
        library = image(self.root/'library')
        with self.assertRaisesRegex(AssertionError,'not executable'):
            self.i.tool_closure([library],{})
        pins = {}; actual = a.tool_closure(self.i,[library],pins)
        library.chmod(0o555)
        expected_pins = {}; expected = self.i.tool_closure([library],expected_pins)
        self.assertEqual(actual,expected)
        self.assertEqual(pins,expected_pins)
        self.assertIs(actual['actual_loaded_images_observed'],False)

    def test_executable_mode_is_still_required(self):
        program = image(self.root/'program',kind=2)
        with self.assertRaisesRegex(AssertionError,'executable root is not executable'):
            a.tool_closure(self.i,[program],{})
        program.chmod(0o555)
        one, two = {}, {}
        self.assertEqual(a.tool_closure(self.i,[program],one),self.i.tool_closure([program],two))
        self.assertEqual(one,two)

    def test_transitive_named_paths_and_absent_candidates_preserved(self):
        early, late = self.root/'early',self.root/'late'
        early.mkdir(); late.mkdir()
        library = image(late/'lib')
        program = image(self.root/'program',2,('@rpath/lib',),(str(early),str(late)),0o555)
        one,two = {},{}
        actual = a.tool_closure(self.i,[program],one)
        self.assertEqual(actual,self.i.tool_closure([program],two))
        self.assertEqual(one,two)
        self.assertEqual(actual['unavailable_candidates'],[str(early/'lib')])
        self.assertEqual(set(actual['images']),{str(program),str(library)})
        self.assertEqual(actual['named_path_resolutions'],{str(library):str(library)})

    def test_ambiguous_and_missing_imports_reject(self):
        dirs = [self.root/'a',self.root/'b']
        for d in dirs: d.mkdir(); image(d/'lib')
        program = image(self.root/'program',2,('@rpath/lib',),tuple(map(str,dirs)),0o555)
        with self.assertRaisesRegex(AssertionError,'ambiguous'):
            a.tool_closure(self.i,[program],{})
        for d in dirs: (d/'lib').unlink()
        with self.assertRaisesRegex(AssertionError,'Missing'):
            a.tool_closure(self.i,[program],{})

    def test_root_symlink_fifo_and_unsupported_type_reject_before_walk(self):
        target = image(self.root/'target')
        link = self.root/'link'; link.symlink_to(target)
        with self.assertRaisesRegex(AssertionError,'Physical'):
            a.tool_closure(self.i,[link],{})
        fifo = self.root/'fifo'; os.mkfifo(fifo)
        with self.assertRaisesRegex(AssertionError,'Regular'):
            a.tool_closure(self.i,[fifo],{})
        bad = image(self.root/'object',kind=1)
        with self.assertRaisesRegex(AssertionError,'Unsupported'):
            a.tool_closure(self.i,[bad],{})

    def test_non_os_alias_crossing_remains_rejected(self):
        system = self.root/'system'; system.mkdir()
        library = image(system/'lib')
        alias = self.root/'alias'; alias.symlink_to(library)
        program = image(self.root/'program',2,(str(alias),),mode=0o555)
        old = self.i.os_image
        self.i.os_image = lambda name: name.startswith(str(system)+'/') or old(name)
        with self.assertRaisesRegex(AssertionError,'Non-OS loader alias'):
            a.tool_closure(self.i,[program],{})

    def test_checked_source_requires_exact_bytes_and_regular_physical_file(self):
        path = self.root/'source'; path.write_bytes(b'original')
        digest = hashlib.sha256(b'original').hexdigest()
        self.assertEqual(a.checked(path,digest),b'original')
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'digest'):
            a.checked(path,digest)
        fifo = self.root/'fifo'; os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError,'Regular'):
            a.checked(fifo,digest)

    def test_private_attachment_binds_adapter_and_preserves_original_plan(self):
        adapter = dict(path=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        calls = []
        def pin(pins,resolutions,path,digest):
            a.checked(path,digest); pins[path]=digest;resolutions[path]=path
        def plan(output,intake_ref,source_ref,intake,pins,resolutions,reader):
            return dict(controller=str(a.ORIGINAL),controller_sha256=a.ORIGINAL_SHA,
                        pins=dict(pins),schedule=['same four commands'])
        controller = types.SimpleNamespace(load_support=lambda pins,res: self.i,build_plan=plan,
            pin=pin,require=self.i.require,INSPECTOR_SHA=a.INSPECTOR_SHA)
        a.attach(controller,adapter)
        pins,res = {},{}
        reader = controller.load_support(pins,res)
        library = image(self.root/'library')
        self.assertIn(str(library),reader.tool_closure([library],{})['images'])
        intake = dict(typed_image_adapter=adapter)
        prepared = controller.build_plan(None,None,None,intake,pins,res,reader)
        self.assertEqual(prepared,controller.build_plan(None,None,None,intake,pins,res,reader))
        self.assertEqual(prepared['controller'],str(a.ORIGINAL))
        self.assertEqual(prepared['controller_sha256'],a.ORIGINAL_SHA)
        self.assertEqual(prepared['entrypoint'],str(source))
        self.assertEqual(prepared['typed_image_adapter'],adapter)
        self.assertEqual(prepared['pins'][str(source)],adapter['sha256'])
        with self.assertRaisesRegex(AssertionError,'Intake must bind'):
            controller.build_plan(None,None,None,{},pins,res,reader)
        changed = copy.deepcopy(intake);changed['typed_image_adapter']['sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'Intake must bind'):
            controller.build_plan(None,None,None,changed,pins,res,reader)


if __name__ == '__main__': unittest.main()
