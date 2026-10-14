"""Saved native AST and small synthetic integrity regressions; no native work."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

PATH=Path(__file__).with_name('typescript_source_units.py')
SPEC=importlib.util.spec_from_file_location('tested_typescript_units',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
EVIDENCE=m.NATIVE/'run-v1/reader/evidence'
CONTRACT=json.loads(m.FIXTURES.read_bytes())['fixtures']


def saved(identity):
    directory=EVIDENCE/identity
    return (directory/'source.ts').read_bytes().decode(),json.loads((directory/'ast.json').read_bytes())


def retarget_same_width(source,evidence):
    """Synthetic line-ending variant; native shape is retained, not re-parsed."""
    value=copy.deepcopy(evidence);raw=source.encode();u16=source.encode('utf-16-le')
    value.update(source_text=source,source_bytes=len(raw),source_sha256=m.digest(raw),source_utf16_length=len(u16)//2)
    for node in value['nodes']:
        node['text_sha256']=m.digest(u16[node['start_utf16']*2:node['end_utf16']*2].decode('utf-16-le').encode())
    return value


class TypeScriptUnits(unittest.TestCase):
    def test_all21_actual_positive_fixture_contracts(self):
        checked=0
        for fixture in CONTRACT:
            if fixture['expected_owner_status']!='candidate':continue
            with self.subTest(id=fixture['id']):
                result=m.count_source(*saved(fixture['id']))
                self.assertEqual(result['status'],'candidate-native-owner-pass',result['diagnostics'])
                self.assertEqual(result['normalized_loc'],fixture['proposed_normalized_loc'])
                self.assertFalse(result['canonical_loc_qualified']);self.assertIsNone(result['formatted_loc'])
                self.assertFalse(result['chart_admission']);self.assertTrue(result['complete_source_owner_coverage'])
                checked+=1
        self.assertEqual(checked,21)

    def test_seven_explicit_review_gates_stay_null(self):
        checked=0
        for fixture in CONTRACT:
            if fixture['expected_owner_status']!='review':continue
            with self.subTest(id=fixture['id']):
                result=m.count_source(*saved(fixture['id']))
                self.assertEqual(result['status'],'needs-review');self.assertIsNone(result['normalized_loc'])
                self.assertTrue(result['diagnostics']);checked+=1
        self.assertEqual(checked,7)

    def test_two_actual_parser_rejections_have_no_count_or_recovery_owners(self):
        for identity in ('unclosed-body','mismatched-delimiter'):
            result=m.count_source(*saved(identity))
            self.assertEqual(result['status'],'native-parser-rejection');self.assertIsNone(result['normalized_loc'])

    def test_parameter_properties_add_fields_without_overlapping_header_events(self):
        result=m.count_source(*saved('parameter-properties-expanded'))
        self.assertEqual(len(result['parameter_properties']),2)
        self.assertEqual(sum(x['units'] for x in result['parameter_properties']),2)
        self.assertEqual(result['normalized_loc'],6)
        events=result['canonical_events']
        self.assertTrue(all(a['end']<=b['start'] for a,b in zip(events,events[1:])))

    def test_data_wrapping_is_preserved_and_not_promoted_into_statements(self):
        wrapped=m.count_source(*saved('wrapped-data'));packed=m.count_source(*saved('packed-data'))
        self.assertEqual((wrapped['physical_loc'],wrapped['normalized_loc']),(4,4))
        self.assertEqual((packed['physical_loc'],packed['normalized_loc']),(1,1))
        self.assertFalse(wrapped['canonical_events']);self.assertFalse(packed['canonical_events'])

    def test_nested_callbacks_preserve_body_work_and_only_structural_suffix(self):
        nested=m.count_source(*saved('nested-block-callback'))
        self.assertEqual(nested['normalized_loc'],7)
        continued=m.count_source(*saved('callback-continuation-review'))
        self.assertIn('callback-continuation-needs-review',[d['kind'] for d in continued['diagnostics']])

    def test_literals_protect_comment_spelling_without_hiding_interpolation_work(self):
        value=m.count_source(*saved('comments-and-regex'))
        self.assertEqual(value['normalized_loc'],2);self.assertEqual(len(value['comment_spans']),2)
        work=m.count_source(*saved('interpolation-work-review'))
        self.assertIn('interpolation-with-independent-work-needs-review',[d['kind'] for d in work['diagnostics']])

    def test_unicode_crlf_and_synthetic_cr_only_row_boundaries(self):
        self.assertEqual(m.count_source(*saved('unicode-crlf'))['normalized_loc'],4)
        source,evidence=saved('expanded-bindings')
        for newline in ('\r','\u2028','\u2029'):
            altered=source.replace('\n',newline)
            result=m.count_source(altered,retarget_same_width(altered,evidence))
            self.assertEqual(result['normalized_loc'],7,result['diagnostics'])
            self.assertEqual(result['physical_loc'],7)

    def test_changed_source_kind_or_role_cannot_produce_a_count(self):
        source,evidence=saved('packed-bindings')
        mutations=[lambda e:e['nodes'][1].update(native_kind=0),
                   lambda e:e['nodes'][1].update(kind='UnreviewedSyntax'),
                   lambda e:e['nodes'][0]['roles'].update(statements=[]),
                   lambda e:e['nodes'][0]['children'].append(e['nodes'][0]['children'][0]),
                   lambda e:e['nodes'][1].update(parent=-1)]
        for mutate in mutations:
            value=copy.deepcopy(evidence);mutate(value)
            self.assertIsNone(m.count_source(source,value)['normalized_loc'])
        self.assertIsNone(m.count_source(source+' ',evidence)['normalized_loc'])

    def test_missing_native_literal_owner_cannot_hide_comment_like_source(self):
        source,evidence=saved('comments-and-regex');value=copy.deepcopy(evidence)
        literal=next(n for n in value['nodes'] if n['kind']=='StringLiteral')
        literal.update(kind='Identifier',native_kind=m.native_kinds()['Identifier'])
        self.assertIsNone(m.count_source(source,value)['normalized_loc'])

    def test_surrogate_split_source_span_is_rejected(self):
        source,evidence=saved('unicode-crlf');value=copy.deepcopy(evidence)
        literal=next(n for n in value['nodes'] if n['kind']=='StringLiteral')
        literal['end_utf16']=source.encode('utf-16-le').index('😀'.encode('utf-16-le'))//2+1
        self.assertIsNone(m.count_source(source,value)['normalized_loc'])

    def test_all_ten_saved_application_projections_cover_exact_source(self):
        # This larger saved-data replay is separate from the small fixture tests.
        # It starts no native process and never hashes runtime executables.
        directories=sorted(EVIDENCE.glob('typescript-*-v1'))
        self.assertEqual(len(directories),10)
        for directory in directories:
            with self.subTest(id=directory.name):
                source,evidence=saved(directory.name);value=m.count_source(source,evidence)
                self.assertEqual(value['status'],'candidate-native-owner-pass',value['diagnostics'])
                self.assertIsInstance(value['normalized_loc'],int);coverage=value['source_coverage']
                self.assertEqual((coverage[0]['start'],coverage[-1]['end']),(0,len(source)))
                self.assertTrue(all(a['end']==b['start'] for a,b in zip(coverage,coverage[1:])))
                self.assertFalse(any(item['kind']=='unowned' for item in coverage))


if __name__=='__main__':unittest.main()
