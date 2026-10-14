#!/usr/bin/env python3
"""Unqualified canonical source-unit candidates from retained native Kotlin PSI.

No Kotlin lexer, compiler, JVM, source evaluation, or runtime preflight runs here.
The native PSI partition, classes, parent relationships and ranges supply syntax
ownership. Unsupported or inconsistent ownership produces diagnostics and a null
normalized_loc. Actual reader completion and final owner review remain separate.
"""
import argparse
from bisect import bisect_right
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'experiments/kotlin/source-units-v1'
RULE_VERSION = 'canonical-source-units-20261012-approved-rule-v2'
GRAMMAR = 'kotlin-native-psi-owners-v1'
READER_VALIDATOR_SHA256 = '7e7bf707e96651559c53ea67909547adce9a6a05d30da07dca266d89d6d4e63f'
FALSE_FLAGS = dict(canonical_loc_qualified=False, formatted_loc_qualified=False,
                   chart_admission=False)
ASSIGNMENTS = {'=', '+=', '-=', '*=', '/=', '%='}
LOOPS = {'KtForExpression', 'KtWhileExpression'}
UNSUPPORTED = {'KtDoWhileExpression', 'KtTryExpression', 'KtCatchClause',
               'KtFinallySection', 'KtClassInitializer', 'KtSecondaryConstructor',
               'KtPropertyAccessor', 'KtObjectLiteralExpression', 'KtAnnotationEntry',
               'KtFileAnnotationList'}
STRUCTURAL_SUFFIX_PARENTS = {'KtValueArgumentList', 'KtParenthesizedExpression',
                             'KtCollectionLiteralExpression', 'KtContainerNode',
                             'KtParameterList'}


class CountError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CountError(message)


@lru_cache(maxsize=1)
def reader_validator():
    """Load definitions only; invoke solely the frozen reader's pure validator.

    The reviewed module has no top-level native work. Its prepare/run/main and
    runtime pin functions are never called. compile/exec avoids writing pyc files.
    validate_psi hashes only the supplied source text, never runtime artifacts.
    """
    path = Path(__file__).with_name('kotlin_loc_v3.py')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == READER_VALIDATOR_SHA256,
            'Frozen native PSI validator bytes differ from the reviewed definition')
    spec = importlib.util.spec_from_file_location('kotlin_source_units_psi_validator', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module.validate_psi


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Tree:
    def __init__(self, original, payload):
        require(isinstance(original, str) and isinstance(payload, dict) and
                set(payload) == {'psi', 'psi_source'}, 'Expected exact source and psi/psi_source envelope')
        self.text, evidence = payload['psi_source'], payload['psi']
        require(isinstance(self.text, str) and isinstance(evidence, dict), 'Missing native PSI source')
        expected = dict(id=evidence['id'], sha256=digest(original.encode('utf-8')),
                        expected_parse='error' if evidence['parse_errors'] else 'ok')
        reader_validator()(evidence, original, self.text, expected)
        require(not evidence['parse_errors'], 'Native parser rejected this source')
        self.normalized = original != self.text
        self.starts = [0] + [m.end() for m in re.finditer('\n', self.text)]
        # Python indexes Unicode scalar values; IntelliJ indexes UTF-16 units.
        # Every node boundary must map to a full source character boundary.
        offsets, units = {0: 0}, 0
        for index, char in enumerate(self.text):
            units += 2 if ord(char) > 0xffff else 1
            offsets[units] = index + 1
        self.nodes = []
        for raw in evidence['nodes']:
            require(raw['start_utf16'] in offsets and raw['end_utf16'] in offsets,
                    'Native PSI boundary splits a UTF-16 surrogate pair')
            node = dict(raw, start=offsets[raw['start_utf16']], end=offsets[raw['end_utf16']])
            node['kind'] = raw['psi_class'].rsplit('.', 1)[-1]
            if node['kind'].startswith('Kt'):
                require(raw['psi_class'].startswith('org.jetbrains.kotlin.psi.'),
                        'Kotlin PSI class has an unexpected native package')
            self.nodes.append(node)
        require(self.nodes[0]['kind'] == 'KtFile', 'Native PSI root is not a Kotlin file')
        self.cleaned = list(self.text)
        self.hidden, self.diagnostics = set(), []
        for node in self.nodes:
            if node['comment']:
                self.mask(node, ' ')
        for node in self.nodes:
            if node['kind'] == 'KtStringTemplateExpression':
                work = [child for child in self.descendants(node)
                        if child['kind'] in ({'KtLambdaExpression', 'KtFunctionLiteral', 'KtBlockExpression',
                                              'KtWhenExpression', 'KtProperty', 'KtDestructuringDeclaration'} |
                                             LOOPS | UNSUPPORTED) or self.assignment(child)]
                if work:
                    self.issue('interpolation-with-independent-work-needs-review', node['start'])
                self.mask(node, 'S')
            elif node['element_type'] == 'CHARACTER_CONSTANT':
                self.mask(node, 'S')
        self.cleaned = ''.join(self.cleaned)
        self.leaves = [n for n in self.nodes if not n['children'] and n['id'] not in self.hidden
                       and not n['whitespace'] and not n['comment'] and n['end'] > n['start']]

    def issue(self, kind, offset, detail=None):
        item = dict(kind=kind, offset=offset)
        if detail:
            item['detail'] = detail
        self.diagnostics.append(item)

    def children(self, node):
        return [self.nodes[i] for i in node['children']]

    def descendants(self, node):
        for child in self.children(node):
            yield child
            yield from self.descendants(child)

    def semantic(self, node):
        return [c for c in self.children(node) if c['kind'].startswith('Kt') and
                c['id'] not in self.hidden and not c['comment'] and c['end'] > c['start']]

    def mask(self, node, replacement):
        for index in range(node['start'], node['end']):
            if not self.text[index].isspace():
                self.cleaned[index] = replacement
        self.hidden.add(node['id'])
        self.hidden.update(child['id'] for child in self.descendants(node))

    def direct_leaf(self, node, text, optional=False):
        matches = [c for c in self.children(node) if not c['children'] and
                   not c['comment'] and not c['whitespace'] and c.get('text') == text]
        require(len(matches) == 1 or optional and not matches,
                'Missing/ambiguous native ' + repr(text) + ' under ' + node['kind'])
        return matches[0] if matches else None

    def role(self, node, role, optional=False):
        matches = [c for c in self.children(node) if c['element_type'] == role]
        require(len(matches) == 1 or optional and not matches,
                'Missing/ambiguous native ' + role + ' body under ' + node['kind'])
        if not matches:
            return None
        children = self.semantic(matches[0])
        require(len(children) == 1, 'Native body container must own exactly one expression')
        return children[0]

    def assignment(self, node):
        if node['kind'] != 'KtBinaryExpression':
            return None
        operators = [c for c in self.children(node) if c['kind'] == 'KtOperationReferenceExpression']
        if len(operators) != 1:
            return None
        operator = operators[0]
        return operator if self.text[operator['start']:operator['end']] in ASSIGNMENTS else None

    def line(self, offset):
        return bisect_right(self.starts, offset)


class Owners:
    def __init__(self, tree):
        self.tree = tree
        self.events, self.continuations = [], []
        self.expressions = []
        self.assignments, self.declarations = [], []
        self.boundaries, self.owned_blocks, self.visited = set(), set(), set()
        self.diagnostics = list(tree.diagnostics)
        self.sequence(tree.nodes[0])
        self.finish()

    def issue(self, kind, node, detail=None):
        item = dict(kind=kind, offset=node['start'] if isinstance(node, dict) else node)
        if detail:
            item['detail'] = detail
        self.diagnostics.append(item)

    def event(self, kind, start, end, units=1, node=None, **details):
        while start < end and self.tree.cleaned[start].isspace():
            start += 1
        require(0 <= start < end <= len(self.tree.text), 'Native owner span is empty or outside source')
        self.events.append(dict(kind=kind, start=start, end=end, units=units,
                                native_node=node['id'] if node else None, **details))

    def sequence(self, node, final_value=False):
        self.visited.add(node['id'])
        children = self.tree.semantic(node)
        for index, child in enumerate(children):
            self.boundaries.add(child['start'])
            self.walk(child, role='value' if final_value and index == len(children) - 1 else 'statement')

    def block(self, node, *, header_start=None, header_units=1, owner=None, braces=True):
        require(node['kind'] in ('KtBlockExpression', 'KtClassBody'), 'Expected a native executable body')
        self.owned_blocks.add(node['id'])
        if braces:
            opening, closing = self.tree.direct_leaf(node, '{'), self.tree.direct_leaf(node, '}')
            require(opening['start'] < closing['start'], 'Native block delimiters are reversed')
            if header_start is None:
                self.event('open', opening['start'], opening['end'], 0, node)
            else:
                self.event('header', header_start, opening['end'], header_units, owner or node)
            self.event('close', closing['start'], closing['end'], 1, owner or node)
        self.sequence(node, final_value=not braces)

    def body(self, body, header_start, owner, *, units=1):
        if body['kind'] == 'KtBlockExpression':
            self.block(body, header_start=header_start, header_units=units, owner=owner)
        else:
            self.event('header', header_start, body['start'], units, owner)
            self.walk(body, role='statement')

    def expression(self, node):
        return dict(start=node['start'], end=node['end'], cursor=node['start'], id=node['id'])

    def promoted(self, node):
        constructors = [c for c in self.tree.children(node) if c['kind'] == 'KtPrimaryConstructor']
        result = []
        for constructor in constructors:
            for parameter in self.tree.descendants(constructor):
                if parameter['kind'] == 'KtParameter' and any(
                        self.tree.direct_leaf(parameter, word, optional=True) for word in ('val', 'var')):
                    result.append(parameter)
        return result

    def walk(self, node, expression=None, role='value', header_start=None):
        if node['id'] in self.tree.hidden:
            return
        self.visited.add(node['id'])
        kind = node['kind']
        if expression is None:
            expression = self.expression(node)
            self.expressions.append(dict(start=node['start'], end=node['end'], owner=node['id'], role=role))
        if kind in UNSUPPORTED:
            self.issue('unsupported-native-executable-owner', node, kind)
            return
        if kind in ('KtImportList', 'KtClassBody'):
            if kind == 'KtClassBody':
                self.issue('class-body-without-native-declaration-owner', node)
            else:
                self.sequence(node)
            return
        if kind in ('KtClass', 'KtObjectDeclaration'):
            bodies = [c for c in self.tree.children(node) if c['kind'] == 'KtClassBody']
            require(len(bodies) <= 1, 'Native class has multiple bodies')
            fields = self.promoted(node)
            if bodies:
                self.block(bodies[0], header_start=node['start'], header_units=1 + len(fields), owner=node)
            else:
                self.declarations.extend(p['start'] for p in fields)
            return
        if kind == 'KtNamedFunction':
            blocks = [c for c in self.tree.children(node) if c['kind'] == 'KtBlockExpression']
            require(len(blocks) <= 1, 'Native function has multiple block bodies')
            if blocks:
                self.block(blocks[0], header_start=node['start'], owner=node)
            else:
                equals = self.tree.direct_leaf(node, '=', optional=True)
                if equals:
                    for child in self.tree.semantic(node):
                        if child['start'] >= equals['end']:
                            self.walk(child, expression, 'value')
            return
        if kind == 'KtLambdaExpression':
            literals = [c for c in self.tree.children(node) if c['kind'] == 'KtFunctionLiteral']
            require(len(literals) == 1, 'Native lambda lacks exactly one function literal')
            self.walk(literals[0], expression)
            return
        if kind == 'KtFunctionLiteral':
            opening, closing = self.tree.direct_leaf(node, '{'), self.tree.direct_leaf(node, '}')
            arrow = self.tree.direct_leaf(node, '->', optional=True)
            bodies = [c for c in self.tree.children(node) if c['kind'] == 'KtBlockExpression']
            require(len(bodies) == 1, 'Native lambda lacks exactly one body')
            # A later callback in this same composed expression starts a new
            # executable header/body/close. Its body must never be suppressed
            # as scalar continuation of an earlier callback.
            for tail in self.continuations:
                if tail['expression_owner'] == expression['id']:
                    tail['end'] = min(tail['end'], expression['cursor'])
            self.event('header', expression['cursor'], (arrow or opening)['end'], node=node,
                       expression_owner=expression['id'])
            self.event('close', closing['start'], closing['end'], node=node,
                       expression_owner=expression['id'])
            self.block(bodies[0], braces=False)
            if closing['end'] < expression['end']:
                self.continuations.append(dict(start=closing['end'], end=expression['end'],
                                               close=closing['start'], expression_owner=expression['id']))
            expression['cursor'] = closing['end']
            return
        if kind in LOOPS:
            body = self.tree.role(node, 'BODY')
            self.body(body, node['start'], node)
            return
        if kind == 'KtIfExpression':
            then = self.tree.role(node, 'THEN')
            otherwise = self.tree.role(node, 'ELSE', optional=True)
            explicit = then['kind'] == 'KtBlockExpression' or otherwise and otherwise['kind'] == 'KtBlockExpression'
            if role == 'statement' or explicit:
                start = node['start'] if header_start is None else header_start
                self.body(then, start, node)
                if otherwise:
                    token = self.tree.direct_leaf(node, 'else')
                    if otherwise['kind'] == 'KtIfExpression':
                        self.walk(otherwise, role='statement', header_start=token['start'])
                    else:
                        self.body(otherwise, token['start'], node)
                return
            # Scalar if/else expressions in initializers, operands, returns or
            # expression-bodied functions gain no invented control boundaries.
        if kind == 'KtWhenExpression':
            opening, closing = self.tree.direct_leaf(node, '{'), self.tree.direct_leaf(node, '}')
            self.event('header', expression['cursor'], opening['end'], node=node)
            self.event('close', closing['start'], closing['end'], node=node)
            for entry in self.tree.children(node):
                if entry['kind'] != 'KtWhenEntry':
                    continue
                self.visited.add(entry['id'])
                arrow = self.tree.direct_leaf(entry, '->')
                bodies = [c for c in self.tree.semantic(entry) if c['start'] >= arrow['end']]
                require(len(bodies) == 1, 'Native when entry lacks exactly one body')
                body = bodies[0]
                if body['kind'] == 'KtBlockExpression':
                    self.block(body, header_start=entry['start'], owner=entry)
                else:
                    self.event('header', entry['start'], arrow['end'], node=entry)
                    self.walk(body, role='statement')
            if closing['end'] < expression['end']:
                self.continuations.append(dict(start=closing['end'], end=expression['end'],
                                               close=closing['start'], expression_owner=expression['id']))
            expression['cursor'] = closing['end']
            return
        if kind == 'KtBlockExpression':
            self.issue('block-without-native-executable-owner', node)
            return
        if kind in ('KtProperty', 'KtDestructuringDeclaration'):
            self.declarations.append(node['start'])
        operator = self.tree.assignment(node)
        if operator:
            self.assignments.append(operator['start'])
        for child in self.tree.semantic(node):
            self.walk(child, expression, 'value')

    def finish(self):
        for node in self.tree.nodes:
            if node['id'] in self.tree.hidden:
                continue
            if node['kind'] in ('KtBlockExpression', 'KtClassBody') and node['id'] not in self.owned_blocks:
                self.issue('unowned-native-executable-body', node, node['kind'])
            if node['kind'] in UNSUPPORTED and node['id'] not in self.visited:
                self.issue('unsupported-native-executable-owner', node, node['kind'])
        for close in list(self.events):
            if close['kind'] != 'close':
                continue
            end = close['end']
            for leaf in self.tree.leaves:
                if leaf['start'] < end:
                    continue
                if self.tree.cleaned[end:leaf['start']].strip():
                    break
                parent = self.tree.nodes[leaf['parent']] if leaf['parent'] >= 0 else None
                if leaf.get('text') in (')', ']', ',') and parent and parent['kind'] in STRUCTURAL_SUFFIX_PARENTS:
                    end = leaf['end']
                    if leaf['text'] == ',':
                        break
                    continue
                break
            if end > close['end'] and not any(event['start'] <= close['end'] and end <= event['end']
                                              for event in self.events):
                self.event('structural-suffix', close['end'], end, 0)
        self.events.sort(key=lambda e: (e['start'], e['end']))
        for left, right in zip(self.events, self.events[1:]):
            if left['end'] > right['start']:
                self.issue('overlapping-native-owner-spans', right['start'])
        for leaf in self.tree.leaves:
            if leaf.get('text') in ('{', '}') and not any(
                    event['start'] <= leaf['start'] and leaf['end'] <= event['end'] for event in self.events):
                self.issue('unowned-native-brace', leaf)


def account(tree, owners):
    body = list(tree.cleaned)
    by_line, owned_lines = {}, set()
    for event in owners.events:
        for offset in range(event['start'], event['end']):
            if not body[offset].isspace():
                body[offset] = ' '
        line = tree.line(event['start'])
        by_line.setdefault(line, []).append(event)
        owned_lines.update(range(line, tree.line(event['end'] - 1) + 1))
    body = ''.join(body)
    rows, original_rows = body.splitlines(keepends=True), tree.text.splitlines()
    physical = [i for i, row in enumerate(tree.cleaned.splitlines(keepends=True), 1) if row.strip()]
    boundaries = owners.boundaries | {at for event in owners.events for at in (event['start'], event['end'])}
    # These semicolons are native PSI leaves outside masked literal/comment data.
    separators = [leaf['end'] for leaf in tree.leaves if leaf.get('text') == ';']
    total, expansions = 0, []
    for line in physical:
        offset, row = tree.starts[line - 1], rows[line - 1]
        bounds = sorted({0, len(row), *(at - offset for at in boundaries | set(separators)
                                       if offset < at < offset + len(row))})
        statements = []
        for left, right in zip(bounds, bounds[1:]):
            text = row[left:right].rstrip().removesuffix(';').rstrip()
            if not text.strip('{}; \t\r\n'):
                continue
            begin = offset + left + len(text) - len(text.lstrip())
            end = offset + left + len(text)
            matches = [at for at in owners.assignments if offset + left <= at < end and body[at] != ' ']
            declarations = [at for at in owners.declarations if offset + left <= at < end and body[at] != ' ']
            owning_expression = min((region for region in owners.expressions
                                     if region['start'] <= begin < end <= region['end']),
                                    key=lambda region: region['end'] - region['start'], default=None)
            tail = next((tail for tail in owners.continuations if tail['start'] <= begin < end <= tail['end']
                         and tree.line(tail['close']) == line and owning_expression and
                         owning_expression['owner'] == tail['expression_owner']), None)
            if tail and (matches or declarations):
                owners.issue('non-scalar-expression-continuation-needs-review', begin)
            units = 0 if tail and not matches and not declarations else max(1, len(matches), len(declarations))
            statements.append(dict(start=offset + left, end=offset + right, units=units,
                                   assignments=matches, declarations=declarations,
                                   reason='same-native-expression-scalar-continuation' if not units
                                   else 'independent-source-unit-or-preserved-physical-row'))
        events = by_line.get(line, [])
        units = sum(e['units'] for e in events) + sum(s['units'] for s in statements)
        if not units and line not in owned_lines:
            units = 1
        total += units
        if units != 1 or events or any(s['units'] != 1 for s in statements):
            expansions.append(dict(line=line, original=original_rows[line - 1], units=units,
                                   extra_lines=units - 1, canonical_events=events, statements=statements))
    return len(physical), total, expansions


def count_source(source, payload):
    tree, owners, diagnostics = None, None, []
    try:
        tree = Tree(source, payload)
        owners = Owners(tree)
        physical, candidate, expansions = account(tree, owners)
        diagnostics = owners.diagnostics
    except (AssertionError, CountError, UnicodeError, TypeError, KeyError, IndexError, RecursionError) as error:
        diagnostics = [dict(kind='native-owner-input-rejected', offset=0, detail=str(error))]
        physical, candidate, expansions = None, None, []
    starts = tree.starts if tree else [0]
    for issue in diagnostics:
        offset = issue['offset']
        line = bisect_right(starts, offset)
        issue.update(line=line, column=offset - starts[line - 1] + 1)
    return dict(rule_version=RULE_VERSION, grammar=GRAMMAR, language='kotlin',
                physical_loc=physical, normalized_loc=None if diagnostics else candidate,
                candidate_normalized_loc=candidate, expansions=expansions, diagnostics=diagnostics,
                canonical_events=owners.events if owners else [],
                expression_continuations=owners.continuations if owners else [],
                independent_expression_owners=owners.expressions if owners else [],
                newline_normalization_observed=tree.normalized if tree else None,
                ownership_offset_units='Python Unicode character offsets into psi_source',
                review_status='needs-review' if diagnostics else 'candidate-native-owner-pass',
                evidence='Caller-supplied native PSI; actual reader completion and owner review remain separate',
                **FALSE_FLAGS)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def replay(plan_path, reader_directory, fixture_contract=PACKET / 'fixture-contract.json', controller_report=None):
    plan, directory = read_json(plan_path), Path(reader_directory)
    native_raw = (directory / 'report.json').read_bytes()
    report, contract = json.loads(native_raw), read_json(fixture_contract)
    require(plan['schema'] == 'kotlin-native-source-reader-plan-v1' and
            report['schema'] == 'kotlin-native-source-reader-v1', 'Wrong Kotlin reader schema')
    require(report['status'] == 'read-awaiting-canonical-owner-review' and
            all(report[key] == 0 for key in ('source_evaluations', 'subject_recompilations', 'subject_main_invocations')) and
            report['canonical_loc'] is report['formatted_loc'] is None and report['chart_admission'] is False,
            'Reader report does not satisfy source-only contract')
    controller_path = Path(controller_report) if controller_report else Path(plan['output']) / 'report.json'
    controller = read_json(controller_path)
    require(controller['schema'] == 'kotlin-native-source-reader-results-v1' and
            controller['status'] == 'read-awaiting-canonical-owner-review' and
            controller['reader_evidence_validated'] is True and
            controller['plan_sha256'] == digest(Path(plan_path).read_bytes()) and
            controller['native_reader_report_sha256'] == digest(native_raw),
            'Saved native reader/controller/plan binding differs')
    planned = {item['id']: item for item in plan['inputs']}
    inputs = {item['id']: item for item in controller['inputs']}
    require(len(planned) == len(plan['inputs']) == len(inputs) == len(controller['inputs']) == len(report['items']) and
            {item['id'] for item in report['items']} == set(inputs) == set(planned), 'Native reader inventory differs')
    for identity, item in inputs.items():
        require({key: value for key, value in item.items() if key != 'reader_path'} == planned[identity] and
                isinstance(item.get('reader_path'), str), 'Runtime reader input differs from reviewed source plan')
    results = {}
    for item in report['items']:
        identity, expected = item['id'], inputs[item['id']]
        require(re.fullmatch(r'[a-z0-9-]+', identity), 'Unsafe source artifact ID')
        folder = directory / identity
        source, parsed, raw = ((folder / name).read_bytes() for name in ('source.kt', 'psi-source.kt', 'psi.json'))
        require(digest(source) == item['source_sha256'] == expected['sha256'] and
                digest(parsed) == item['psi_source_sha256'] and digest(raw) == item['psi_sha256'],
                'Retained native PSI/source artifact identity differs')
        evidence = json.loads(raw)
        reader_validator()(evidence, source.decode(), parsed.decode(), expected)
        require(evidence['source_path'] == expected['reader_path'] and
                item['nodes'] == len(evidence['nodes']) and item['parse_errors'] == len(evidence['parse_errors']),
                'Native PSI summary differs from artifacts')
        if expected['expected_parse'] == 'error':
            require(item['status'] == 'expected-parse-rejection', 'Missing expected native parser rejection')
            results[identity] = dict(status='native-parser-rejected-as-expected', normalized_loc=None, **FALSE_FLAGS)
        else:
            require(item['status'] == 'parsed', 'Native reader did not parse expected valid source')
            results[identity] = count_source(source.decode(), dict(psi=evidence, psi_source=parsed.decode()))
    require(contract['schema'] == 'kotlin-source-unit-fixture-contract-v1' and
            contract['rule_version'] == RULE_VERSION, 'Wrong source-unit fixture contract')
    expectations = {row['id']: row for row in contract['fixtures']}
    require(len(expectations) == len(contract['fixtures']) and set(expectations) ==
            {key for key, value in inputs.items() if value['kind'] == 'fixture'}, 'Native fixture inventory differs')
    checks = []
    for identity, expected in expectations.items():
        counted = results[identity]
        if expected['outcome'] == 'parse-rejected':
            passed = counted.get('status') == 'native-parser-rejected-as-expected'
        elif expected['outcome'] == 'needs-review':
            passed = counted['normalized_loc'] is None and any(
                d['kind'] == expected['diagnostic'] for d in counted.get('diagnostics', []))
        elif expected['outcome'] == 'candidate-count':
            passed = counted['normalized_loc'] == expected['canonical_units'] and not counted['diagnostics']
        else:
            raise CountError('Unknown fixture expectation')
        checks.append(dict(id=identity, passed=passed, expectation=expected))
    profiles, seen = [], set()
    for row in plan['profiles']:
        require(row['id'] not in seen and len(row['inputs']) == len(set(row['inputs'])) and
                all(inputs[key]['kind'] == 'application' for key in row['inputs']), 'Invalid application source bundle')
        seen.add(row['id'])
        counts = [results[key]['normalized_loc'] for key in row['inputs']]
        value = sum(counts) if all(type(n) is int for n in counts) else None
        profiles.append(dict(id=row['id'], inputs=row['inputs'], candidate_canonical_loc=value,
                             canonical_loc=None, formatted_loc=None, **FALSE_FLAGS))
    clean = all(row['passed'] for row in checks) and all(row['candidate_canonical_loc'] is not None for row in profiles)
    return dict(schema='kotlin-source-unit-replay-v1',
                status='candidate-replay-awaiting-owner-review' if clean else 'candidate-replay-needs-review',
                rule_version=RULE_VERSION, grammar=GRAMMAR, files=results, profiles=profiles,
                plan=str(Path(plan_path).resolve()), reader_directory=str(directory.resolve()),
                controller_report=str(controller_path.resolve()),
                fixture_checks=checks, native_fixture_expectations_passed=all(row['passed'] for row in checks),
                native_reader_metadata_consumed=True, native_reader_terminal_verified=False,
                formatter_evidence_available=False, formatted_loc=None, source_evaluations=0,
                subject_recompilations=0, **FALSE_FLAGS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    single = commands.add_parser('count', help='Count a saved exact source/native PSI pair as a candidate')
    single.add_argument('--source', type=Path, required=True)
    single.add_argument('--psi-source', type=Path, required=True)
    single.add_argument('--psi', type=Path, required=True)
    collection = commands.add_parser('replay', help='Consume completed saved native reader artifacts')
    collection.add_argument('--plan', type=Path, required=True)
    collection.add_argument('--reader-directory', type=Path, required=True)
    collection.add_argument('--fixture-contract', type=Path, default=PACKET / 'fixture-contract.json')
    collection.add_argument('--controller-report', type=Path)
    for command in (single, collection):
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = (count_source(args.source.read_bytes().decode(),
                          dict(psi=read_json(args.psi), psi_source=args.psi_source.read_bytes().decode()))
              if args.action == 'count' else replay(args.plan, args.reader_directory, args.fixture_contract,
                                                    args.controller_report))
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(args.output), status=result.get('status', result.get('review_status')), **FALSE_FLAGS)))


if __name__ == '__main__':
    main()
