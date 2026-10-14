#!/usr/bin/env python3
"""Pure diagnosis of frozen Scala v1 graph transport; not v2 native validation."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT/'native-token-capture-v1'
REPORT_SHA = 'a72690ad68a0b2b1d0947cbe010811411739789584f18a4040e6e2a6fb293ac9'
TERMINAL_SHA = '832dbad46e40a9ce682f003567784d3f460447cd465dcf04495ed532234370fc'
READER_SHA = 'b786fb092aa62ed0df3d7bd5e32c3a55aa555eee07cd66fb963fb2ea39560bce'
COMMIT = '25c18aaa21b6be202945e024cd5180d9d62d650f'
UPSTREAM = dict(path='compiler/src/dotty/tools/dotc/ast/Trees.scala',
    url=f'https://github.com/scala/scala3/blob/{COMMIT}/compiler/src/dotty/tools/dotc/ast/Trees.scala',
    commit=COMMIT, git_blob_sha='02077aed374ad3ac5aa1b0292af283e06fbc077a',
    source_bytes=90528, source_sha256='7724f5302bd575e27f796b23e294abed3806492d9a241644e605ddf68a76bf69',
    facts=[dict(lines='132-141', fact='hasType tests a non-null type slot; typeOpt is a final direct slot read.'),
           dict(lines='1057-1059', fact='Thicket initializes its type slot to the NoType singleton.'),
           dict(lines='1086-1094', fact='EmptyTree inherits Thicket; EmptyValDef also initializes NoType.'),
           dict(lines='1099-1102,1233-1240', fact='Shared empty sentinels and Thicket constructors retain native trees.')])


def require(value, message):
    if not value: raise AssertionError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 16*1024*1024,
            'Missing/nonregular/oversized frozen evidence: '+str(path))
    raw = path.read_bytes()
    require(len(raw) <= 16*1024*1024 and digest(raw) == expected, 'Frozen evidence changed: '+str(path))
    return json.loads(raw)


def node_shape(node, nodes, edges, sources):
    """Recognize structural evidence only; v1 did not record typeOpt identity."""
    require(node['tree_state'] is not None and node['tree_state']['has_type'] is True and
            node['tree_state']['native_empty_valdef_sentinel'] is False and node['product'] == 'Thicket',
            'Unexpected reported typed node state')
    require([field['role'] for field in node['fields']] == ['trees'] and
            node['extra_modifiers'] is None and node['native_derived'] is None,
            'Native Thicket structural fields differ')
    children = node['fields'][0]['value']
    require(isinstance(children, list) and all(isinstance(child, dict) and set(child) == {'node'} and
            child['node'] in nodes for child in children), 'Thicket child references incomplete')
    expected_edges = {(node['id'], f'trees[{index}]', child['node']) for index, child in enumerate(children)}
    actual_edges = {(edge['parent'], edge['role'], edge['child']) for edge in edges if edge['parent'] == node['id']}
    require(actual_edges == expected_edges and len([e for e in edges if e['parent'] == node['id']]) == len(children),
            'Thicket child/edge inventory differs')
    cls = node['class']
    if cls == 'dotty.tools.dotc.ast.Trees$EmptyTree':
        require(children == [] and node['tree_state']['empty'] is True and node['span']['exists'] is False and
                sources[node['source_id']]['exists'] is False, 'Native EmptyTree shape differs')
        kind = 'shared-empty-tree-NoType-constructor'
    else:
        require(cls == 'dotty.tools.dotc.ast.Trees$Thicket' and children and
                node['tree_state']['empty'] is False, 'Unexpected typed class or empty Thicket shape')
        kind = 'Thicket-NoType-constructor'
    return dict(node_id=node['id'], native_class=cls, constructor_semantics=kind,
        span=node['span'], source_id=node['source_id'], node_transport_sha256=digest(json.dumps(node, sort_keys=True).encode()),
        children=[dict(node_id=child['node'], native_class=nodes[child['node']]['class'],
            span=nodes[child['node']]['span'], transport_sha256=digest(json.dumps(nodes[child['node']], sort_keys=True).encode()))
            for child in children], native_NoType_identity_observed_in_v1=False)


def audit():
    report = read(V1/'report.json', REPORT_SHA); terminal = read(V1/'terminal.json', TERMINAL_SHA)
    require(report['status'] == terminal['status'] == 'eighty-source-transports-retained-awaiting-independent-review' and
            terminal['report_sha256'] == REPORT_SHA and report['native_processes_started'] == terminal['native_processes_started'] == 1 and
            report['subject_main_executions'] == report['benchmark_samples'] == 0 and report['integrity_errors'] == [],
            'Unexpected frozen capture scope')
    require(digest((ROOT/'candidate-token-capture-v1/SourceReader.scala').read_bytes()) == READER_SHA,
            'Frozen v1 reader changed')
    require(len(report['inputs']) == len(report['results']) == 80, 'Expected all 80 source results')
    cases = []; classes = Counter(); children = Counter(); groups = Counter(); old_empty_valdefs = 0
    for index, (source, result) in enumerate(zip(report['inputs'], report['results'])):
        require(source['index'] == index and source['id'] == result['id'], 'Source/result ordering differs')
        raw = read(result['path'], result['sha256'])
        require(raw['stock_parser'] == raw['observed_parser'] and raw['stock_parser_parity'] is True and
                result['stock_parser_parity'] is True and raw['source_sha256'] == source['source_sha256'],
                'Frozen source/parity evidence differs')
        graph = raw['observed_parser']; nodes = {n['id']: n for n in graph['nodes']}
        sources = {s['id']: s for s in graph['sources']}
        require(len(nodes) == len(graph['nodes']) and set(nodes) == set(range(len(nodes))), 'Graph node IDs differ')
        require(all(e['parent'] in nodes and e['child'] in nodes for e in graph['structural_edges']),
                'Graph edge references a missing node')
        old_empty_valdefs += sum(bool(n['tree_state'] and n['tree_state']['native_empty_valdef_sentinel']) for n in nodes.values())
        diagnosed = []
        for problem in graph['graph_problems']:
            require(set(problem) == {'kind', 'node'} and problem['kind'] == 'typed_tree_in_parse_output',
                    'Unexpected graph problem requires separate review')
            node = nodes[problem['node']]
            diagnosis = node_shape(node, nodes, graph['structural_edges'], sources)
            diagnosed.append(diagnosis); classes[node['class']] += 1
            children.update(child['native_class'] for child in diagnosis['children'])
        require(len({d['node_id'] for d in diagnosed}) == len(diagnosed), 'Duplicate graph problem node')
        non_graph = [issue for issue in raw['token_capture']['issues'] if issue['kind'] != 'native_graph_not_complete']
        graph_issues = [issue for issue in raw['token_capture']['issues'] if issue['kind'] == 'native_graph_not_complete']
        require(len(graph_issues) == int(bool(diagnosed)), 'Graph problem/coverage issue linkage differs')
        require(raw['candidate_coverage_complete'] is (not graph['graph_problems'] and not non_graph) and
                result['candidate_coverage_complete'] == raw['candidate_coverage_complete'], 'V1 completeness differs')
        category = 'intentional-token-or-parse-rejection' if non_graph else (
                    'native-NoType-container-false-rejection' if diagnosed else 'already-complete-v1')
        groups[category] += 1
        cases.append(dict(index=index, id=source['id'], group=source['group'], raw_result=result['path'],
            raw_result_sha256=result['sha256'], source_sha256=source['source_sha256'], category=category,
            original_graph_problems=graph['graph_problems'], diagnosed_nodes=diagnosed,
            retained_non_graph_issues=non_graph, original_candidate_coverage_complete=raw['candidate_coverage_complete'],
            v2_native_result=None))
    require(dict(classes) == {'dotty.tools.dotc.ast.Trees$EmptyTree': 41, 'dotty.tools.dotc.ast.Trees$Thicket': 30} and
            dict(groups) == {'already-complete-v1': 27, 'native-NoType-container-false-rejection': 45,
                             'intentional-token-or-parse-rejection': 8}, 'Actual failure cohort differs')
    require(children == Counter({'dotty.tools.dotc.ast.Trees$Literal': 30, 'dotty.tools.dotc.ast.Trees$Ident': 18,
                                 'dotty.tools.dotc.ast.Trees$Block': 11, 'dotty.tools.dotc.ast.Trees$This': 1}),
            'Thicket child/literal cohort differs')
    require(old_empty_valdefs == 22, 'Previously handled EmptyValDef cohort differs')
    return dict(schema='scala-v1-native-graph-diagnosis-v2', status='saved-v1-evidence-diagnosed-v2-not-executed',
        report_sha256=REPORT_SHA, terminal_sha256=TERMINAL_SHA, frozen_reader_sha256=READER_SHA,
        upstream=UPSTREAM, inputs=80, exact_parity_cases=80, original_complete=27, original_incomplete=53,
        graph_problem_cases=sum(bool(c['diagnosed_nodes']) for c in cases), graph_problem_nodes=71,
        native_problem_classes=dict(classes), thicket_child_classes=dict(children), old_empty_valdef_sentinels=22,
        categories=dict(groups), expected_v2_positive_cases=72, expected_v2_rejected_cases=8, cases=cases,
        native_v2_executions=0, native_v2_coverage_qualified=False, native_fixture_transport_verified=False,
        canonical_loc=None, formatted_loc=None, chart_admission=False)


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2, ensure_ascii=True))
