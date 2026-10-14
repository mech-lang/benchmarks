"""Pure byte-row and saved-XML replay checks; no JVM or full pin verification."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

PATH = Path(__file__).with_name('kotlin_single_entry_capture.py')
SPEC = importlib.util.spec_from_file_location('tested_capture_replay',PATH)
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


class CaptureReplayTests(unittest.TestCase):
    def fixture(self):
        return ('main code [0x100,0x110] = 16\n[MachCode]\n'
                '  0x100: 1f20 03d5 | e953 40d1 \n'
                '  0x108: 3f01 00f9 | ff03 02d1 \n[/MachCode]\n')

    def test_consecutive_rows_preserve_every_byte(self):
        start,data,count = m.instruction_bytes(self.fixture(),'0x100')
        self.assertEqual((start,len(data),count),(256,16,2))
        self.assertEqual(data.hex(),'1f2003d5e95340d13f0100f9ff0302d1')

    def test_comments_at_same_address_are_not_extra_bytes(self):
        text = self.fixture().replace('  0x108:', '  0x108: ; ImmutableOopMap {[0]=Oop}\n  0x108:')
        self.assertEqual(m.instruction_bytes(text,'0x100')[2],2)

    def test_crlf_and_tabs_are_horizontal_separators(self):
        text = self.fixture().replace('\n','\r\n').replace('  0x','\t0x')
        self.assertEqual(len(m.instruction_bytes(text,'0x100')[1]),16)

    def test_missing_row_rejected(self):
        text = self.fixture().replace('  0x108: 3f01 00f9 | ff03 02d1 \n','')
        with self.assertRaisesRegex(AssertionError,'cover the main-code range'): m.instruction_bytes(text,'0x100')

    def test_overlap_rejected(self):
        text = self.fixture().replace('[/MachCode]','0x108: aabbccdd\n[/MachCode]')
        with self.assertRaisesRegex(AssertionError,'Overlapping'): m.instruction_bytes(text,'0x100')

    def test_odd_hex_group_rejected(self):
        with self.assertRaisesRegex(AssertionError,'Malformed'): m.instruction_bytes(self.fixture().replace('1f20','1f2'),'0x100')

    def test_outside_entry_rejected(self):
        with self.assertRaisesRegex(AssertionError,'range/entry'): m.instruction_bytes(self.fixture(),'0x110')

    def test_actual_saved_nine_methods_fully_replay(self):
        path = m.stage.PACKET/'run-v1/kotlin-binarytrees-compact/hotspot.xml'
        if not path.exists(): self.skipTest('Saved native capture unavailable')
        value = m.capture_index(path,'binarytrees')
        self.assertEqual([n['compile_id'] for n in value['native_methods']],
                         ['79','81','84','88','126','127','128','157','158'])
        self.assertEqual([n['instruction_coverage']['bytes'] for n in value['native_methods']],
                         [1096,2280,2392,448,13264,12992,3480,18832,3848])
        self.assertTrue(all(n['oopmap_count'] > 0 for n in value['native_methods']))
        self.assertEqual(value['node_allocation_eliminations'],[])
        self.assertFalse(value['source_work_qualified'])
        self.assertFalse(value['optimized_main_allocation_and_lifetime_proved'])


if __name__ == '__main__': unittest.main()
