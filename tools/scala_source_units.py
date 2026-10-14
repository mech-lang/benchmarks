"""Pure, inspectable source-unit projection from retained Scala 3.10 parser JSON.

No source is parsed or evaluated here. Native nodes supply statement/child roles;
the retained physical tokens prove written boundaries. Unknown ownership returns
diagnostics and a null count. Application admission always needs manual review.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'experiments/scala/source-counts-v1'
PACKET = BASE / 'canonical-projection-v1'
RULE = 'canonical-source-units-20261012-approved-rule-v2'
REPORT_SHA = 'a2b5a96c833d7c16e73c6a070e863d832d051048b4d87611543b4dbc17c97287'
REVIEW_SHA = 'd6154d35fbc7f8f5a25b82a0e1d7a98fb8188e1c8a0fe9ada1ceb59e7ce3a18f'
TOKEN_AUDIT_SHA = 'faed374a1f5fafc657cb62662397668e261e382352bb5035ac54ea25263c6d48'
MARKERS = ('native_empty_tree_sentinel', 'native_thicket_container', 'native_no_type_marker')
FIELD_ROLES = {
    'AppliedTypeTree': 'tpt args', 'Apply': 'fun args', 'Assign': 'lhs rhs',
    'Block': 'stats expr', 'CaseDef': 'pat guard body', 'DefDef': 'name paramss tpt preRhs',
    'Final': '', 'Function': 'args body', 'Ident': 'name', 'If': 'cond thenp elsep',
    'Import': 'expr selectors', 'ImportSelector': 'imported renamed bound',
    'InfixOp': 'left op right', 'InterpolatedString': 'id segments', 'Literal': 'const',
    'Match': 'selector cases', 'ModuleDef': 'name impl', 'New': 'tpt', 'Number': 'digits kind',
    'PackageDef': 'pid stats', 'Parens': 't', 'ParsedTry': 'expr handler finalizer',
    'PatDef': 'mods pats tpt rhs', 'PrefixOp': 'op od', 'Private': '', 'Return': 'expr from',
    'Select': 'qualifier name', 'Template': 'constr preParentsOrDerived self preBody',
    'Thicket': 'trees', 'This': 'qual', 'Throw': 'expr', 'Tuple': 'trees',
    'TypeApply': 'fun args', 'TypeBoundsTree': 'lo hi alias', 'TypeDef': 'name rhs',
    'TypeTree': '', 'Typed': 'expr tpt', 'ValDef': 'name tpt preRhs', 'Var': '',
    'WhileDo': 'cond body',
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    raw = Path(path).read_bytes()
    require(len(raw) <= 16 * 1024 * 1024, 'Oversized retained JSON')
    require(expected is None or digest(raw) == expected, 'Changed retained evidence: '+str(path))
    return json.loads(raw)


def pinned_token_audit():
    path = BASE / 'candidate-token-capture-v2/audit_token_evidence.py'
    raw = path.read_bytes()
    require(digest(raw) == TOKEN_AUDIT_SHA, 'Changed frozen token auditor')
    module = types.ModuleType('scala_frozen_token_audit')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module.audit()


def replay_native():
    """Independently replay the exact delta and token/source evidence, no runtime hashes."""
    old_audit = pinned_token_audit()
    report = read(BASE/'native-token-capture-v2/report.json', REPORT_SHA)
    review = read(BASE/'native-token-capture-v2-review.json', REVIEW_SHA)
    previous = read(BASE/'native-token-capture-v1/report.json', old_audit['original_report_sha256'])
    require(report['inputs'] == previous['inputs'] and len(report['results']) == 80, 'Changed 80-input cohort')
    require(report['native_processes_started'] == 2 and report['subject_main_executions'] == 0
            and report['benchmark_samples'] == 0 and report['integrity_errors'] == []
            and report['active'] is None, 'Native revision did not close successfully')
    cases, records, types_seen = [], [], Counter()
    for i, (item, entry) in enumerate(zip(report['inputs'], report['results'])):
        path = BASE/'native-token-capture-v2/reader/parser-output'/f'{i:04d}.json'
        require(Path(entry['path']) == path and entry['id'] == item['id'], 'Result identity mismatch')
        new = read(path, entry['sha256'])
        old_entry = previous['results'][i]
        old = read(old_entry['path'], old_entry['sha256'])
        require(new['stock_parser'] == new['observed_parser'] and new['stock_parser_parity'] is True,
                'Stock/observed native AST disagreement')
        graph = copy.deepcopy(new['observed_parser'])
        require(graph['graph_problems'] == [], 'Unexpected revised graph problem')
        for node in graph['nodes']:
            state = node['tree_state']
            if state is not None:
                for key in MARKERS:
                    require(type(state[key]) is bool, 'Missing native NoType marker')
                allowed = state['native_no_type_marker'] and any(state[k] for k in
                    ('native_empty_valdef_sentinel', 'native_empty_tree_sentinel', 'native_thicket_container'))
                require(not state['has_type'] or allowed, 'Unexpected typed parse node')
                if allowed:
                    types_seen[node['class']] += 1
                for key in MARKERS:
                    del state[key]
        graph['graph_problems'] = old['observed_parser']['graph_problems']
        require(graph == old['observed_parser'], 'Revision altered pre-existing AST evidence')
        for key in ('source_path', 'source_sha256', 'source_byte_count', 'source_bytes_base64',
                    'decoded_text', 'utf16_length', 'utf16_to_utf8_byte_boundaries', 'offset_unit'):
            require(new[key] == old[key], 'Revision altered source evidence: '+key)
        old_tokens, new_tokens = copy.deepcopy(old['token_capture']), copy.deepcopy(new['token_capture'])
        old_tokens['issues'] = [v for v in old_tokens['issues'] if v['kind'] != 'native_graph_not_complete']
        # Only the aggregate completeness booleans change after graph classification.
        for value in (old_tokens, new_tokens):
            value.pop('candidate_coverage_complete', None)
        require(old_tokens == new_tokens, 'Revision altered native tokens, comments or scanner events')
        complete = i not in (39, 40, 44, 47, 48, 67, 68, 69)
        require(new['candidate_coverage_complete'] is complete and entry['candidate_coverage_complete'] is complete,
                'Unexpected native coverage result')
        cases.append(dict(index=i, id=item['id'], source_sha256=item['source_sha256'],
            capture_sha256=entry['sha256'], exact_native_pair=True, original_graph_preserved=True,
            original_tokens_and_source_preserved=True, complete=complete))
        records.append((item, new))
    require(dict(types_seen) == review['native_no_type_classes'], 'NoType inventory differs from independent review')
    return dict(schema='scala-canonical-input-replay-v1', report_sha256=REPORT_SHA,
        prior_review_sha256=REVIEW_SHA, native_pairs=80, complete_cases=72, expected_rejections=8,
        native_no_type_classes=dict(types_seen), token_audit_summary=old_audit['summary'], cases=cases,
        native_executions=0, canonical_LOC_admitted=False, chart_admission=False), records


def references(value):
    if isinstance(value, dict):
        if set(value) == {'node'}:
            yield value['node']
        else:
            for item in value.values():
                yield from references(item)
    elif isinstance(value, list):
        for item in value:
            yield from references(item)


def edge_roles(value, role):
    if isinstance(value, dict):
        if set(value) == {'node'}:
            yield role, value['node']
        else:
            for key, item in value.items():
                yield from edge_roles(item, role+'.'+key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from edge_roles(item, role+f'[{index}]')


class Projection:
    def __init__(self, record):
        self.record = record
        self.text = record['decoded_text']
        self.raw = self.text.encode('utf-8')
        self.bounds = record['utf16_to_utf8_byte_boundaries']
        self.length = record['utf16_length']
        self.nodes = {node['id']: node for node in record['observed_parser']['nodes']}
        self.tokens = [p for p in record['token_capture']['physical_pieces'] if p['kind'] == 'token']
        self.events, self.claimed, self.diagnostics = [], {}, []
        self.active = set()
        self.validate()

    def validate(self):
        require(base64.b64decode(self.record['source_bytes_base64'], validate=True) == self.raw
                and digest(self.raw) == self.record['source_sha256']
                and len(self.raw) == self.record['source_byte_count'], 'Source identity mismatch')
        boundaries, offset = [0], 0
        for char in self.text:
            offset += len(char.encode('utf-8'))
            if ord(char) > 0xffff:
                boundaries.append(-1)
            boundaries.append(offset)
        require(self.bounds == boundaries and self.length == len(boundaries)-1, 'Invalid native offset map')
        require(list(self.nodes) == list(range(len(self.nodes))) and
                len(self.nodes) == len(self.record['observed_parser']['nodes']), 'Native node identity gap/duplicate')
        edges = []
        for node in self.nodes.values():
            require(all(ref in self.nodes for ref in references(node)), 'Dangling native node reference')
            span = node['span']
            if span['exists']:
                require(0 <= span['start'] <= span['end'] <= self.length, 'Native span outside source')
                require(self.bounds[span['start']] >= 0 and self.bounds[span['end']] >= 0,
                        'Native owner cuts a supplementary character')
            if node['product'] not in FIELD_ROLES:
                self.problem('unsupported-native-node', node['id'], node['product'])
            elif [f['role'] for f in node['fields']] != FIELD_ROLES[node['product']].split():
                self.problem('unexpected-native-field-roles', node['id'])
            state = node['tree_state']
            if state and state['has_type']:
                suffix = node['class'].rsplit('$', 1)[-1]
                permitted = ((suffix == 'EmptyTree' and node['product'] == 'Thicket' and
                              state['native_empty_tree_sentinel']) or
                             (suffix == 'EmptyValDef' and node['product'] == 'ValDef' and
                              state['native_empty_valdef_sentinel']) or
                             (suffix == 'Thicket' and node['product'] == 'Thicket' and
                              state['native_thicket_container']))
                if not (permitted and state['native_no_type_marker']):
                    self.problem('unexpected-typed-native-node', node['id'])
            for field in node['fields']:
                edges.extend((node['id'], role, child) for role, child in edge_roles(field['value'], field['role']))
            for key, role in (('extra_modifiers', '@modifiers'), ('native_derived', '@derived')):
                edges.extend((node['id'], label, child) for label, child in edge_roles(node[key], role))
            end_marker = node['native_definition_end_name_span']
            if end_marker and end_marker['exists']:
                self.problem('written-end-marker-owner-review', node['id'],
                             [end_marker['start'], end_marker['end']])
            if node['product'] == 'TypeBoundsTree' and not (span['synthetic'] and span['zero_extent']):
                self.problem('explicit-type-bound-owner-review', node['id'])
            if node['native_derived']:
                self.problem('derives-owner-review', node['id'])
            mods = node['extra_modifiers']
            if isinstance(mods, dict) and mods.get('annotations'):
                self.problem('annotation-owner-review', node['id'])
        retained_edges = [(e['parent'], e['role'], e['child'])
                          for e in self.record['observed_parser']['structural_edges']]
        require(Counter(edges) == Counter(retained_edges), 'Native fields/edge inventory disagreement')
        graph = self.record['observed_parser']
        reachable, pending = set(), [graph['root']]
        adjacency = {}
        for parent, role, child in edges:
            adjacency.setdefault(parent, []).append(child)
        while pending:
            current = pending.pop()
            if current not in reachable:
                reachable.add(current); pending.extend(adjacency.get(current, ()))
        require(reachable == set(self.nodes), 'Detached native node')
        visiting, visited = set(), set()
        def acyclic(current):
            require(current not in visiting, 'Cycle in native ownership graph')
            if current not in visited:
                visiting.add(current)
                for child in adjacency.get(current, ()):
                    acyclic(child)
                visiting.remove(current); visited.add(current)
        acyclic(graph['root'])
        require(len({p['id'] for p in self.tokens}) == len(self.tokens), 'Duplicate physical token ID')
        for piece in self.record['token_capture']['physical_pieces']:
            require(self.slice(piece['start'], piece['end']) == piece['source_text'], 'Physical piece/source mismatch')
            require(piece['kind'] in ('token', 'comment'), 'Unknown physical piece kind')
        for space in self.record['token_capture']['whitespace_intervals']:
            value = self.slice(space['start'], space['end'])
            require(value == space['text'] and value.isspace(), 'Invalid whitespace interval')
        # Coverage is recomputed from all physical pieces and retained whitespace.
        intervals = sorted((p['start'], p['end']) for p in self.record['token_capture']['physical_pieces'])
        intervals += [(p['start'], p['end']) for p in self.record['token_capture']['whitespace_intervals']]
        cursor = 0
        for start, end in sorted(intervals):
            if start != cursor:
                self.problem('physical-coverage-gap-or-overlap', None, [cursor, start])
            cursor = end
        if cursor != self.length:
            self.problem('physical-coverage-tail', None, [cursor, self.length])
        for piece in self.record['token_capture']['physical_pieces']:
            if piece['kind'] == 'comment' and piece['source_text'].lstrip().startswith('//>'):
                self.problem('meaningful-directive-owner-review', None, [piece['start'], piece['end']])

    def slice(self, start, end):
        require(0 <= start <= end <= self.length and self.bounds[start] >= 0 and self.bounds[end] >= 0,
                'Invalid ownership interval')
        return self.raw[self.bounds[start]:self.bounds[end]].decode('utf-8')

    def problem(self, kind, node=None, detail=None):
        value = dict(kind=kind, node=node, detail=detail)
        if value not in self.diagnostics:
            self.diagnostics.append(value)

    def fields(self, node):
        return {field['role']: field['value'] for field in self.nodes[node]['fields']}

    def child(self, node, role):
        value = self.fields(node).get(role)
        return value.get('node') if isinstance(value, dict) else None

    def children(self, node, role):
        return list(references(self.fields(node).get(role, [])))

    def span(self, node):
        s = self.nodes[node]['span']
        return (s['start'], s['end']) if s['exists'] else (None, None)

    def product(self, node):
        return self.nodes[node]['product'] if node is not None else None

    def empty(self, node):
        state = self.nodes[node]['tree_state'] if node is not None else None
        return node is None or bool(state and state['empty'])

    def descendants(self, node):
        pending, seen = [node], set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            yield current
            pending.extend(references(self.fields(current)))

    def within(self, start, end, word=None):
        return [p for p in self.tokens if start <= p['start'] and p['end'] <= end
                and (word is None or p['source_text'] == word)]

    def emit(self, kind, node, start, end, units=1, reason=None):
        selected = [p for p in self.within(start, end) if p['id'] not in self.claimed]
        if units and not selected:
            self.problem('unit-has-no-written-token', node, kind)
            return
        if not selected:
            return
        event = dict(id=len(self.events), kind=kind, node=node, units=units,
            utf16_span=[start, end], utf8_span=[self.bounds[start], self.bounds[end]],
            source_text=self.slice(start, end), token_ids=[p['id'] for p in selected], reason=reason)
        self.events.append(event)
        for p in selected:
            self.claimed[p['id']] = event['id']

    def braces(self, start, end):
        # The scanner already protects string/comment punctuation. Match only real tokens.
        stack, pairs = [], {}
        for p in self.within(start, end):
            word = p['source_text']
            if word in ('(', '[', '{'):
                stack.append(p)
            elif word in (')', ']', '}'):
                if not stack or stack[-1]['source_text'] != {')':'(', ']':'[', '}':'{'}[word]:
                    continue  # An enclosing source range may omit an outer delimiter.
                opening = stack.pop()
                pairs[opening['start']] = p
        return pairs

    def block(self, node, header_start=None, header_kind='block-header', owner=None):
        start, end = self.span(node)
        owner = node if owner is None else owner
        if start is None:
            self.problem('missing-block-span', node)
            return
        body = self.children(node, 'stats')
        expr = self.child(node, 'expr')
        if not self.empty(expr):
            body.append(expr)
        tokens = self.within(start, end)
        written = bool(tokens and tokens[0]['source_text'] == '{')
        close = self.braces(start, end).get(start) if written else None
        if written and (close is None or close['end'] != end):
            self.problem('ambiguous-written-block-close', node)
            return
        if header_start is not None:
            boundary = tokens[0]['end'] if written else start
            self.emit(header_kind, owner, header_start, boundary)
        elif written:
            self.emit('block-opener', owner, start, tokens[0]['end'], 0)
        for item in body:
            self.unit(item)
        if close:
            self.emit('written-close', owner, close['start'], close['end'])
        # Only semicolons may remain between proven statements; they add no unit.
        self.structural(node, start, end, allowed={';'})

    def structural(self, node, start, end, allowed):
        left = [p for p in self.within(start, end) if p['id'] not in self.claimed]
        unexpected = [p for p in left if p['source_text'] not in allowed]
        if unexpected:
            self.problem('unowned-meaningful-tokens', node,
                [[p['id'], p['source_text'], p['start'], p['end']] for p in unexpected])
        for p in left:
            self.emit('structural-separator' if p not in unexpected else 'unresolved-token', node,
                p['start'], p['end'], 0)

    def template(self, node, template, start, end):
        members = self.children(template, 'preBody')
        constructor = self.child(template, 'constr')
        params = self.children(constructor, 'paramss') if constructor is not None else []
        # First brace after the constructor and parents belongs to the authored body;
        # use the enclosing node's matched outer brace, never a member method's brace.
        pairs = self.braces(start, end)
        opens = [p for p in self.within(start, end, '{') if p['start'] in pairs
                 and pairs[p['start']]['end'] == end]
        opening = opens[0] if len(opens) == 1 else None
        if len(opens) > 1 or (members and opening is None):
            self.problem('template-body-boundary-review', node)
            return
        header_end = opening['end'] if opening else end
        for param in params:
            a, b = self.span(param)
            first = self.within(a, b) if a is not None else []
            if first and first[0]['source_text'] in ('val', 'var'):
                self.emit('constructor-field', param, a, b)
        self.emit('type-or-object-header', node, start, header_end)
        for member in members:
            self.unit(member)
        if opening:
            close = pairs[opening['start']]
            self.emit('written-close', node, close['start'], close['end'])
            self.structural(node, header_end, close['start'], {';'})

    def special_roots(self, node):
        """Return maximal executable children; expression-only functions stay composed."""
        if node is None or self.empty(node):
            return []
        product = self.product(node)
        if product == 'InterpolatedString':
            for inner in self.descendants(node):
                if self.product(inner) == 'Block' and (self.children(inner, 'stats') or
                        self.product(self.child(inner, 'expr')) in ('Block', 'WhileDo', 'If', 'ParsedTry')):
                    self.problem('executable-interpolation-owner-review', inner)
            return []
        if product in ('Match', 'CaseDef'):
            self.problem('pattern-owner-review', node)
            return []
        if product == 'New' and self.product(self.child(node, 'tpt')) == 'Template':
            return [node]
        if product == 'Block':
            return [node]
        if product in ('WhileDo', 'ParsedTry'):
            return [node]
        if product == 'If':
            descendants = list(self.descendants(node))[1:]
            if any(self.product(n) in ('Block', 'WhileDo', 'ParsedTry', 'Match') for n in descendants):
                return [node]
            return []
        found = []
        for child in references(self.fields(node)):
            found.extend(self.special_roots(child))
        return list(dict.fromkeys(found))

    def expand(self, expr, owner, start, end):
        roots = self.special_roots(expr)
        if not roots:
            return False
        if len(roots) != 1:
            self.problem('multiple-embedded-owner-review', owner, roots)
            return False
        root = roots[0]
        kind = self.product(root)
        if kind == 'New':
            _, root_end = self.span(root)
            self.template(owner, self.child(root, 'tpt'), start, root_end)
            self.structural(owner, root_end, end, {')', ']', ','})
        elif kind == 'Block':
            block_expr = self.child(root, 'expr')
            if not self.children(root, 'stats') and self.product(block_expr) == 'Function':
                body = self.child(block_expr, 'body')
                a, b = self.span(root)
                closing = self.braces(a, b).get(a)
                if closing is None:
                    self.problem('callback-written-boundary-review', root)
                    return True
                body_start, _ = self.span(body)
                self.emit('braced-callback-header', owner, start, body_start)
                if self.product(body) == 'Block':
                    self.block(body)
                else:
                    self.unit(body)
                self.emit('written-close', root, closing['start'], closing['end'])
                self.structural(owner, start, end, {';', ')', ']', ','})
            else:
                self.block(root, start, 'embedded-block-header', owner)
                self.structural(owner, start, end, {')', ']', ','})
        else:
            # Keeping the enclosing declaration and embedded control distinct
            # needs an explicit common-rule decision outside this narrow subset.
            self.problem('embedded-control-owner-review', owner, kind)
        return True

    def literal_data(self, node, allow_names=False):
        product = self.product(node)
        if product in ('Number', 'Literal'):
            return True
        if allow_names and product in ('Ident', 'Select'):
            return all(self.literal_data(c, True) for c in references(self.fields(node)))
        if product in ('Tuple', 'Parens'):
            children = list(references(self.fields(node)))
            return bool(children) and all(self.literal_data(c, allow_names) for c in children)
        if product == 'PrefixOp':
            return self.literal_data(self.child(node, 'od'), allow_names)
        if product == 'InfixOp':
            operator = self.fields(self.child(node, 'op')).get('name', {}).get('text')
            return operator in ('+', '-', '*', '/', '%', '<<', '>>', '&', '|', '^') and all(
                self.literal_data(self.child(node, key), allow_names) for key in ('left', 'right'))
        return False

    def array_data(self, node):
        if self.product(node) != 'Apply':
            return False
        target = self.child(node, 'fun')
        if self.product(target) == 'TypeApply':
            target = self.child(target, 'fun')
        return (self.product(target) == 'Ident' and self.fields(target)['name']['text'] == 'Array'
                and all(self.literal_data(arg, True) for arg in self.children(node, 'args')))

    def data_rows(self, node, expr, start, end):
        selected = self.within(start, end)
        rows = {}
        for token in selected:
            # Literal token internal newlines remain physical rows too.
            a, b = token['start'], token['end']
            prefix = self.slice(0, a)
            first = prefix.count('\n')
            last = first + token['source_text'].count('\n')
            for line in range(first, last+1):
                rows.setdefault(line, []).append(token)
        if len(rows) <= 1:
            return False
        descendants = list(self.descendants(expr)) if expr is not None else []
        array = any(self.array_data(n) for n in descendants)
        literals = self.literal_data(expr) and any(self.product(n) == 'Literal' for n in descendants)
        args = self.children(expr, 'args') if self.product(expr) == 'Apply' else []
        literal_call = bool(args) and all(self.literal_data(arg) for arg in args)
        if not (array or literals or literal_call):
            self.problem('multiline-composed-value-owner-review', node)
            return False
        # A token may span multiple data rows: one owner carries the retained row
        # weight, avoiding duplicated literal ownership.
        self.emit('physical-data-rows', node, start, end, len(rows),
                  dict(policy='Preserve written data/argument wrapping',
                       physical_rows=[line+1 for line in sorted(rows)],
                       native_array_nodes=[n for n in descendants if self.array_data(n)],
                       literal_composition=literals, literal_call_arguments=literal_call))
        return True

    def unit(self, node):
        if self.empty(node):
            return
        if node in self.active:
            self.problem('native-owner-cycle', node)
            return
        self.active.add(node)
        try:
            self._unit(node)
        finally:
            self.active.remove(node)

    def _unit(self, node):
        product = self.product(node)
        start, end = self.span(node)
        if start is None:
            self.problem('missing-authored-unit-span', node)
            return
        if product == 'DefDef':
            name = self.fields(node)['name']['text']
            if name == '<init>':
                self.problem('constructor-scaffolding-in-statement-list', node)
                return
            rhs = self.child(node, 'preRhs')
            if self.product(rhs) == 'Block':
                self.block(rhs, start, 'method-header', node)
            elif not self.expand(rhs, node, start, end):
                self.emit('expression-method', node, start, end)
        elif product in ('ValDef', 'PatDef', 'Assign', 'Return', 'Throw'):
            role = 'preRhs' if product == 'ValDef' else 'rhs' if product in ('PatDef', 'Assign') else 'expr'
            rhs = self.child(node, role)
            if not self.expand(rhs, node, start, end):
                if not self.data_rows(node, rhs, start, end):
                    self.emit('binding' if product in ('ValDef', 'PatDef') else 'statement', node, start, end)
        elif product in ('ModuleDef', 'TypeDef'):
            child = self.child(node, 'impl' if product == 'ModuleDef' else 'rhs')
            if self.product(child) == 'Template':
                self.template(node, child, start, end)
            else:
                self.emit('type-alias', node, start, end)
        elif product == 'Block':
            self.block(node, start)
        elif product == 'WhileDo':
            body = self.child(node, 'body')
            if self.product(body) == 'Block':
                self.block(body, start, 'while-header', node)
            else:
                self.emit('while-header', node, start, self.span(body)[0])
                self.unit(body)
        elif product == 'If':
            thenp, elsep = self.child(node, 'thenp'), self.child(node, 'elsep')
            if self.product(thenp) == 'Block':
                self.block(thenp, start, 'if-header', node)
            else:
                self.emit('if-header', node, start, self.span(thenp)[0])
                self.unit(thenp)
            if not self.empty(elsep):
                a, _ = self.span(elsep)
                keywords = self.within(self.span(thenp)[1], a, 'else')
                if len(keywords) != 1:
                    self.problem('else-keyword-owner-review', node)
                elif self.product(elsep) == 'Block':
                    self.block(elsep, keywords[0]['start'], 'else-header', node)
                else:
                    self.emit('else-header', node, keywords[0]['start'], a)
                    self.unit(elsep)
        elif product == 'ParsedTry':
            body, handler, finalizer = (self.child(node, key) for key in ('expr', 'handler', 'finalizer'))
            if self.product(body) == 'Block':
                self.block(body, start, 'try-header', node)
            else:
                self.emit('try-header', node, start, self.span(body)[0]); self.unit(body)
            if not self.empty(handler):
                self.problem('catch-owner-review', node)
            if not self.empty(finalizer):
                a, _ = self.span(finalizer)
                keywords = self.within(self.span(body)[1], a, 'finally')
                if len(keywords) != 1:
                    self.problem('finally-keyword-owner-review', node)
                elif self.product(finalizer) == 'Block':
                    self.block(finalizer, keywords[0]['start'], 'finally-header', node)
                else:
                    self.emit('finally-header', node, keywords[0]['start'], a); self.unit(finalizer)
        elif product in ('Match', 'CaseDef'):
            self.problem('pattern-owner-review', node)
        elif product == 'Import':
            self.emit('import', node, start, end)
        else:
            if not self.expand(node, node, start, end):
                if not self.data_rows(node, node, start, end):
                    self.emit('expression-statement', node, start, end)

    def result(self, application=False):
        graph = self.record['observed_parser']
        if (self.record['candidate_coverage_complete'] is not True or graph['parse_has_errors'] or graph['failure']
                or graph['graph_problems'] or self.record['stock_parser'] != graph
                or self.record['token_capture']['issues']):
            self.problem('native-parse-or-token-coverage-rejected')
        else:
            root = graph['root']
            if self.product(root) == 'PackageDef':
                pid = self.child(root, 'pid')
                if self.fields(pid).get('name', {}).get('text') != '<empty>':
                    self.problem('written-package-owner-review', root)
                for node in self.children(root, 'stats'):
                    self.unit(node)
            elif self.product(root) != 'Thicket' or not self.empty(root):
                self.problem('unsupported-native-root', root)
        missing = [p for p in self.tokens if p['id'] not in self.claimed]
        for p in missing:
            if p['source_text'] == ';':
                self.emit('structural-separator', graph['root'], p['start'], p['end'], 0)
            else:
                self.problem('unowned-token', None, [p['id'], p['source_text'], p['start'], p['end']])
        # Source lines are counted from physical code tokens, not comment masking.
        occupied = set()
        for token in self.tokens:
            line = self.slice(0, token['start']).count('\n')
            occupied.update(range(line, line+token['source_text'].count('\n')+1))
        candidate = sum(e['units'] for e in self.events) if not self.diagnostics else None
        return dict(schema='scala-native-owner-projection-v1', rule=RULE,
            source_sha256=self.record['source_sha256'], source_bytes=len(self.raw),
            physical_loc=len(occupied), candidate_normalized_loc=candidate,
            normalized_loc=None if application else candidate, formatted_loc=None,
            application_manual_owner_review_required=application, canonical_LOC_admitted=False,
            chart_admission=False, diagnostics=self.diagnostics, canonical_events=self.events,
            token_ownership=[dict(token_id=p['id'], owner_event=self.claimed.get(p['id']),
                utf16_span=[p['start'], p['end']], utf8_span=[self.bounds[p['start']], self.bounds[p['end']]],
                source_text=p['source_text']) for p in self.tokens],
            all_meaningful_tokens_owned=all(p['id'] in self.claimed for p in self.tokens),
            native_nodes_preserved=len(self.nodes), literal_and_comment_evidence_preserved=True)


def project(record, *, application=False):
    return Projection(record).result(application)


def build_packet(output):
    require(not output.exists(), 'Fresh additive output directory required')
    review, records = replay_native()
    projections, checks = [], []
    for item, record in records:
        if item['group'] == 'capture':
            continue  # Capture contracts test transport, not a canonical owner count.
        value = project(record, application=item['group'] == 'application')
        value.update(id=item['id'], native_capture_sha256=review['cases'][item['index']]['capture_sha256'])
        projections.append(value)
        if item['group'] == 'owner':
            fixture = item['fixture']
            expected = fixture['proposed_normalized_loc']
            actual = value['normalized_loc']
            checks.append(dict(id=item['id'], proposed=expected, projected=actual,
                expectation_matches=(actual == expected), status=fixture['expected_owner_status'],
                diagnostic_kinds=sorted({d['kind'] for d in value['diagnostics']})))
    artifacts = {value['id']+'.json': (json.dumps(value, indent=2, ensure_ascii=True)+'\n').encode()
                 for value in projections}
    source_pins = {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in
                  (Path(__file__).resolve(), ROOT/'tools/test_scala_source_units.py',
                   ROOT/'archive/validation/loc-normalization/20261012/canonical.py',
                   ROOT/'archive/validation/loc-normalization/20261012/normalizer.py',
                   BASE/'fixtures.json')}
    summary = dict(schema='scala-canonical-projection-review-v1', rule=RULE, source_pins=source_pins,
        native_input_replay=review, fixture_checks=checks,
        fixture_count=len(checks), candidate_fixture_matches=sum(c['expectation_matches'] for c in checks),
        application_count=10, application_counts_admitted=0,
        all_application_counts_require_manual_owner_review=True,
        native_executions=0, canonical_LOC_admitted=False, chart_admission=False,
        projection_artifacts={name: dict(sha256=digest(raw), bytes=len(raw)) for name, raw in artifacts.items()})
    output.mkdir(parents=True)
    for name, raw in artifacts.items():
        (output/name).write_bytes(raw)
    (output/'review.json').write_text(json.dumps(summary, indent=2, ensure_ascii=True)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_packet(args.output.resolve())
    print(json.dumps({k: result[k] for k in ('fixture_count', 'candidate_fixture_matches',
        'application_count', 'application_counts_admitted', 'native_executions')}))
