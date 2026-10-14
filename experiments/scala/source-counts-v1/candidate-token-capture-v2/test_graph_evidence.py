"""Pure saved-graph and additive-source checks; no Scala invocation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('scala_v2_graph_audit', HERE/'audit_graph_evidence.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


class GraphEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = m.audit()
        cls.raw = json.loads((m.V1/'native/parser-output/0030.json').read_bytes())['observed_parser']
        cls.nodes = {node['id']: node for node in cls.raw['nodes']}
        cls.sources = {source['id']: source for source in cls.raw['sources']}
        cls.thicket = cls.nodes[5]

    def shape(self, node=None, nodes=None, edges=None):
        return m.node_shape(node or self.thicket, nodes or self.nodes,
            self.raw['structural_edges'] if edges is None else edges, self.sources)

    def test_all_80_cases_accounted_without_native_qualification(self):
        self.assertEqual(len(self.result['cases']), 80)
        self.assertEqual(self.result['original_incomplete'], 53)
        self.assertEqual(self.result['graph_problem_cases'], 47)
        self.assertEqual(self.result['graph_problem_nodes'], 71)
        self.assertEqual(self.result['expected_v2_positive_cases'], 72)
        self.assertEqual(self.result['expected_v2_rejected_cases'], 8)
        self.assertIs(self.result['native_v2_coverage_qualified'], False)
        self.assertIs(self.result['canonical_loc'], None)

    def test_nonempty_thicket_preserves_literal_and_expression_children(self):
        result = self.shape()
        self.assertEqual([n['native_class'] for n in result['children']],
            ['dotty.tools.dotc.ast.Trees$Literal', 'dotty.tools.dotc.ast.Trees$Block'])
        self.assertEqual(self.result['thicket_child_classes']['dotty.tools.dotc.ast.Trees$Literal'], 30)
        self.assertIs(result['native_NoType_identity_observed_in_v1'], False)

    def test_unknown_typed_tree_not_classified_as_native_container(self):
        node = deepcopy(self.thicket); node['class'] = 'dotty.tools.dotc.ast.Trees$Literal'
        with self.assertRaisesRegex(AssertionError, 'Unexpected typed class'): self.shape(node=node)

    def test_missing_thicket_child_reference_fails(self):
        node = deepcopy(self.thicket); node['fields'][0]['value'][0]['node'] = 99999
        with self.assertRaisesRegex(AssertionError, 'child references'): self.shape(node=node)

    def test_missing_or_duplicate_thicket_edge_fails(self):
        edges = deepcopy(self.raw['structural_edges'])
        edge = next(e for e in edges if e['parent'] == self.thicket['id'])
        edges.remove(edge)
        with self.assertRaisesRegex(AssertionError, 'child/edge inventory'): self.shape(edges=edges)
        edges.extend([edge, edge])
        with self.assertRaisesRegex(AssertionError, 'child/edge inventory'): self.shape(edges=edges)

    def test_v2_preserves_complete_scanner_and_graph_field_traversal(self):
        v1 = (m.ROOT/'candidate-token-capture-v1/SourceReader.scala').read_text()
        v2 = (HERE/'SourceReader.scala').read_text()
        start = '  // Installed before constructing ObservedScanner:'
        end = '  private def read(path: Path'
        self.assertEqual(v1.split(start, 1)[1].split(end, 1)[0], v2.split(start, 1)[1].split(end, 1)[0])
        start = '    private def value(v: Any, parent: Int, role: String): String = v match'
        end = '        val treeState = p match'
        self.assertEqual(v1.split(start, 1)[1].split(end, 1)[0], v2.split(start, 1)[1].split(end, 1)[0])
        self.assertIn('t.hasType && (t.typeOpt eq NoType)', v2)
        self.assertIn('if t.hasType && !nativeNoTypeContainer then', v2)

    def test_v2_fixture_change_is_only_source_supported_xml_expectation(self):
        v1 = json.loads((m.ROOT/'candidate-token-capture-v1/fixtures.json').read_bytes())
        v2 = json.loads((HERE/'fixtures.json').read_bytes())
        self.assertEqual(len(v1['fixtures']), len(v2['fixtures']))
        for before, after in zip(v1['fixtures'], v2['fixtures']):
            if before['id'] != 'xml-direct-reader-handoff': self.assertEqual(before, after)
            else:
                self.assertEqual(after['text'], before['text'])
                self.assertEqual(after['expected_capture'], before['expected_capture'])
                self.assertEqual(after['expected_capture'], 'reject-xml')
                self.assertEqual(after['expected_parse'], 'ok')
                self.assertEqual(after['required_raw_lexemes'], before['required_raw_lexemes'])
                self.assertEqual(after['checks'][1:], before['checks'][1:])
        for key in ('native_token_constants', 'parity_contract', 'coverage_contract'):
            self.assertEqual(v1[key], v2[key])


if __name__ == '__main__': unittest.main()
