"""Pure Kotlin owner tests: synthetic boundaries and actual saved PSI regressions.

Synthetic fixtures are explicitly constructed trees, not native observations.
Saved-PSI tests read the retained v3 artifacts without executing Kotlin or a JVM.
Only Python ownership accounting and bounded source/evidence checks run here;
these tests neither qualify counts nor write a new replay.
"""
from dataclasses import dataclass, field
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock


COUNTER = Path(__file__).with_name('kotlin_source_units_v2.py')
SPEC = importlib.util.spec_from_file_location('synthetic_kotlin_source_units_v2', COUNTER)
COUNTER_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COUNTER_MODULE
SPEC.loader.exec_module(COUNTER_MODULE)
count_source = COUNTER_MODULE.count_source


ELEMENT_TYPES = {
    'KtFile': 'kotlin.FILE', 'KtNamedFunction': 'FUN', 'KtBlockExpression': 'BLOCK',
    'KtProperty': 'PROPERTY', 'KtClass': 'CLASS', 'KtClassBody': 'CLASS_BODY',
    'KtPrimaryConstructor': 'PRIMARY_CONSTRUCTOR', 'KtParameterList': 'VALUE_PARAMETER_LIST',
    'KtParameter': 'VALUE_PARAMETER', 'KtIfExpression': 'IF', 'KtWhileExpression': 'WHILE',
    'KtForExpression': 'FOR', 'KtWhenExpression': 'WHEN', 'KtWhenEntry': 'WHEN_ENTRY',
    'KtLambdaExpression': 'LAMBDA_EXPRESSION', 'KtFunctionLiteral': 'FUNCTION_LITERAL',
    'KtLambdaArgument': 'LAMBDA_ARGUMENT', 'KtReturnExpression': 'RETURN',
    'KtCallExpression': 'CALL_EXPRESSION', 'KtDotQualifiedExpression': 'DOT_QUALIFIED_EXPRESSION',
    'KtBinaryExpression': 'BINARY_EXPRESSION', 'KtNameReferenceExpression': 'REFERENCE_EXPRESSION',
    'KtConstantExpression': 'INTEGER_CONSTANT', 'KtValueArgumentList': 'VALUE_ARGUMENT_LIST',
    'KtDestructuringDeclaration': 'DESTRUCTURING_DECLARATION',
    'KtStringTemplateExpression': 'STRING_TEMPLATE',
    'KtLiteralStringTemplateEntry': 'LITERAL_STRING_TEMPLATE_ENTRY',
    'KtBlockStringTemplateEntry': 'LONG_STRING_TEMPLATE_ENTRY',
    'KtPropertyAccessor': 'PROPERTY_ACCESSOR',
}


@dataclass
class Tree:
    kind: str
    start: int
    end: int
    children: list = field(default_factory=list)
    element_type: str | None = None


def at(source, fragment, occurrence=0):
    start = -1
    for _ in range(occurrence + 1):
        start = source.index(fragment, start + 1)
    return start, start + len(fragment)


def kt(source, kind, fragment, children=(), occurrence=0, element_type=None):
    return Tree(kind, *at(source, fragment, occurrence), list(children), element_type)


def container(source, kind, fragment, child, occurrence=0):
    cls = 'KtContainerNode' if kind in ('CONDITION', 'LOOP_RANGE') else 'KtContainerNodeForControlStructureBody'
    return kt(source, cls, fragment, [child], occurrence, element_type=kind)


def ref(source, fragment, occurrence=0):
    return kt(source, 'KtNameReferenceExpression', fragment, occurrence=occurrence)


def scalar(source, fragment, occurrence=0):
    kind = 'KtConstantExpression' if re.fullmatch(r'[0-9]+', fragment) else 'KtBinaryExpression'
    return kt(source, kind, fragment, occurrence=occurrence)


def call(source, fragment, children=(), occurrence=0):
    return kt(source, 'KtCallExpression', fragment, children, occurrence)


def block(source, fragment, children=(), occurrence=0):
    return kt(source, 'KtBlockExpression', fragment, children, occurrence)


def function(source, children, fragment=None):
    return kt(source, 'KtNamedFunction', fragment or source.strip(), children)


def lambda_tree(source, fragment, bodies, *, parameters=None, occurrence=0):
    begin, finish = at(source, fragment, occurrence)
    arrow = source.find('->', begin, finish)
    body_start = arrow + 2 if arrow >= 0 else begin + 1
    body_end = finish - 1
    while body_start < body_end and source[body_start].isspace():
        body_start += 1
    while body_end > body_start and source[body_end - 1].isspace():
        body_end -= 1
    children = []
    if parameters is not None:
        start = begin + 1
        while source[start].isspace():
            start += 1
        end = arrow
        while source[end - 1].isspace():
            end -= 1
        children.append(Tree('KtParameterList', start, end, list(parameters)))
    children.append(Tree('KtBlockExpression', body_start, body_end, list(bodies)))
    literal = Tree('KtFunctionLiteral', begin, finish, children)
    return Tree('KtLambdaExpression', begin, finish, [literal])


def lambda_call(source, fragment, callback):
    argument = Tree('KtLambdaArgument', callback.start, callback.end, [callback])
    return call(source, fragment, [argument])


def qualified_lambda(source, fragment, receiver, selector, callback):
    return kt(source, 'KtDotQualifiedExpression', fragment,
              [receiver, lambda_call(source, selector, callback)])


def simple_string(source, quoted):
    begin, end = at(source, quoted)
    literal = Tree('KtLiteralStringTemplateEntry', begin + 1, end - 1)
    return Tree('KtStringTemplateExpression', begin, end, [literal])


def character(source, quoted, occurrence=0):
    return kt(source, 'KtConstantExpression', quoted, occurrence=occurrence,
              element_type='CHARACTER_CONSTANT')


def payload(source, roots, parsed=None):
    parsed = source if parsed is None else parsed
    nodes = []
    offsets = [0]
    for char in parsed:
        offsets.append(offsets[-1] + (2 if ord(char) > 0xffff else 1))

    def leaf(start, end, parent, *, comment=False, whitespace=False):
        index = len(nodes)
        cls = ('PsiCommentImpl' if comment else 'PsiWhiteSpaceImpl' if whitespace else 'LeafPsiElement')
        nodes.append(dict(id=index, parent=parent, start_utf16=offsets[start], end_utf16=offsets[end],
                          psi_class='com.intellij.psi.impl.source.tree.' + cls,
                          element_type='EOL_COMMENT' if comment else 'WHITE_SPACE' if whitespace else 'TOKEN',
                          comment=comment, whitespace=whitespace, children=[], text=parsed[start:end]))
        return index

    def gaps(start, end, parent):
        result, cursor = [], start
        while cursor < end:
            begin = cursor
            if parsed[cursor].isspace():
                while cursor < end and parsed[cursor].isspace():
                    cursor += 1
                result.append(leaf(begin, cursor, parent, whitespace=True))
            elif parsed.startswith('//', cursor):
                newline = parsed.find('\n', cursor, end)
                cursor = end if newline < 0 else newline
                result.append(leaf(begin, cursor, parent, comment=True))
            elif parsed.startswith('/*', cursor):
                cursor, depth = cursor + 2, 1
                while cursor < end and depth:
                    if parsed.startswith('/*', cursor):
                        cursor += 2; depth += 1
                    elif parsed.startswith('*/', cursor):
                        cursor += 2; depth -= 1
                    else:
                        cursor += 1
                if depth:
                    raise AssertionError('Synthetic fixture has unclosed comment')
                result.append(leaf(begin, cursor, parent, comment=True))
            else:
                token = re.match(r'(?:[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|->|\+=|-=|\+\+|--|==|!=|<=|>=|&&|\|\|)', parsed[cursor:end])
                cursor += len(token[0]) if token else 1
                result.append(leaf(begin, cursor, parent))
        return result

    def visit(tree, parent):
        index = len(nodes)
        row = dict(id=index, parent=parent, start_utf16=offsets[tree.start], end_utf16=offsets[tree.end],
                   psi_class='org.jetbrains.kotlin.psi.' + tree.kind,
                   element_type=tree.element_type or ELEMENT_TYPES.get(tree.kind, tree.kind),
                   comment=False, whitespace=False, children=[])
        nodes.append(row)
        if tree.kind == 'KtLiteralStringTemplateEntry':
            row['children'].append(leaf(tree.start, tree.end, index))
            return index
        cursor = tree.start
        for child in sorted(tree.children, key=lambda child: (child.start, child.end)):
            if not cursor <= child.start <= child.end <= tree.end:
                raise AssertionError('Synthetic children do not nest: ' + tree.kind)
            row['children'].extend(gaps(cursor, child.start, index))
            row['children'].append(visit(child, index))
            cursor = child.end
        row['children'].extend(gaps(cursor, tree.end, index))
        if not row['children']:
            row['text'] = parsed[tree.start:tree.end]
        return index

    visit(Tree('KtFile', 0, len(parsed), list(roots)), -1)
    evidence = dict(schema='kotlin-native-psi-source-v1', id='fixture-synthetic',
                    source_path='fixture:synthetic', source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                    psi_source_sha256=hashlib.sha256(parsed.encode()).hexdigest(),
                    offset_units='UTF-16 code units', source_utf16_length=offsets[-1],
                    newline_normalization_observed=parsed != source, nodes=nodes,
                    parse_errors=[], leaf_coverage_complete=True)
    return {'psi': evidence, 'psi_source': parsed}


class KotlinSourceUnitFixtures(unittest.TestCase):
    def counted(self, source, roots, expected, *, physical=None, parsed=None):
        result = count_source(source, payload(source, roots, parsed))
        self.assertEqual(result['diagnostics'], [], result)
        self.assertEqual(result['normalized_loc'], expected, result)
        self.assertEqual(result['candidate_normalized_loc'], expected, result)
        if physical is not None:
            self.assertEqual(result['physical_loc'], physical, result)
        self.flags(result)
        return result

    def flags(self, result):
        for flag in ('canonical_loc_qualified', 'formatted_loc_qualified', 'chart_admission'):
            self.assertIs(result[flag], False, result)

    def gated(self, source, evidence):
        result = count_source(source, evidence)
        self.assertTrue(result['diagnostics'], result)
        self.assertIsNone(result['normalized_loc'], result)
        self.flags(result)
        return result

    def test_packed_and_expanded_independent_statements(self):
        for source in ('fun f() { val x = 1; val y = 2; show(x + y) }\n',
                       'fun f() {\n val x = 1\n val y = 2\n show(x + y)\n}\n'):
            with self.subTest(source=source):
                children = [kt(source, 'KtProperty', 'val x = 1'), kt(source, 'KtProperty', 'val y = 2'),
                            call(source, 'show(x + y)')]
                body = block(source, source[source.index('{'):source.rindex('}') + 1], children)
                self.counted(source, [function(source, [body])], 5)

    def test_expression_function_does_not_gain_header_or_close(self):
        source = 'fun f(x: Int) = x + 1\n'
        parameters = kt(source, 'KtParameterList', '(x: Int)', [kt(source, 'KtParameter', 'x: Int')])
        self.counted(source, [function(source, [parameters, scalar(source, 'x + 1')])], 1, physical=1)

    def test_wrapped_explicit_function_header_counts_once(self):
        source = 'fun f(\n x: Int\n): Int\n{\n return x\n}\n'
        parameters = kt(source, 'KtParameterList', '(\n x: Int\n)', [kt(source, 'KtParameter', 'x: Int')])
        body = block(source, '{\n return x\n}', [kt(source, 'KtReturnExpression', 'return x')])
        self.counted(source, [function(source, [parameters, body])], 3, physical=6)

    def test_scalar_if_in_expression_function_remains_one_unit(self):
        source = 'fun f(c: Boolean) = if (c) 1 else 2\n'
        control = kt(source, 'KtIfExpression', 'if (c) 1 else 2', [
            container(source, 'CONDITION', 'c', ref(source, 'c', 1), 1),
            container(source, 'THEN', '1', scalar(source, '1')),
            container(source, 'ELSE', '2', scalar(source, '2'))])
        self.counted(source, [function(source, [control])], 1, physical=1)

    def test_scalar_if_in_property_initializer_remains_one_unit(self):
        source = 'val value = if (ready) 1 else 2\n'
        control = kt(source, 'KtIfExpression', 'if (ready) 1 else 2', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '1', scalar(source, '1')),
            container(source, 'ELSE', '2', scalar(source, '2'))])
        self.counted(source, [kt(source, 'KtProperty', source.strip(), [control])], 1)

    def test_scalar_if_return_value_remains_one_body_statement(self):
        source = 'fun f(): Int { return if (ready) 1 else 2 }\n'
        control = kt(source, 'KtIfExpression', 'if (ready) 1 else 2', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '1', scalar(source, '1')),
            container(source, 'ELSE', '2', scalar(source, '2'))])
        returned = kt(source, 'KtReturnExpression', 'return if (ready) 1 else 2', [control])
        body = block(source, '{ return if (ready) 1 else 2 }', [returned])
        self.counted(source, [function(source, [body])], 3)

    def test_unbraced_statement_if_has_header_and_branch_body_units(self):
        source = 'fun f() { if (ready) go() else halt() }\n'
        control = kt(source, 'KtIfExpression', 'if (ready) go() else halt()', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', 'go()', call(source, 'go()')),
            container(source, 'ELSE', 'halt()', call(source, 'halt()'))])
        self.counted(source, [function(source, [block(source, '{ if (ready) go() else halt() }', [control])])], 6)

    def test_scalar_if_literal_bodies_remain_one_expression(self):
        for yes, no, literal in (('"yes; }"', '"no; {"', simple_string),
                                 ("';'", "'}'", character)):
            with self.subTest(yes=yes, no=no):
                source = f'fun f() = if (ready) {yes} else {no}\n'
                control = kt(source, 'KtIfExpression', source[source.index('if'):].strip(), [
                    container(source, 'CONDITION', 'ready', ref(source, 'ready')),
                    container(source, 'THEN', yes, literal(source, yes)),
                    container(source, 'ELSE', no, literal(source, no))])
                result = self.counted(source, [function(source, [control])], 1)
                self.assertEqual(result['canonical_events'], [])

    def test_statement_if_literal_bodies_keep_header_and_body_units(self):
        source = 'fun f() { if (ready) "yes; }" else \'}\' }\n'
        control_text = 'if (ready) "yes; }" else \'}\''
        control = kt(source, 'KtIfExpression', control_text, [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '"yes; }"', simple_string(source, '"yes; }"')),
            container(source, 'ELSE', "'}'", character(source, "'}'"))])
        outer = block(source, '{ ' + control_text + ' }', [control])
        result = self.counted(source, [function(source, [outer])], 6)
        self.assertEqual([event['kind'] for event in result['canonical_events']],
                         ['header', 'header', 'header', 'close'])

    def test_braced_branch_with_literal_else_preserves_only_written_closes(self):
        source = 'fun f() { if (ready) { go() } else "no; }" }\n'
        control_text = 'if (ready) { go() } else "no; }"'
        control = kt(source, 'KtIfExpression', control_text, [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '{ go() }', block(source, '{ go() }', [call(source, 'go()')])),
            container(source, 'ELSE', '"no; }"', simple_string(source, '"no; }"'))])
        outer = block(source, '{ ' + control_text + ' }', [control])
        result = self.counted(source, [function(source, [outer])], 7)
        self.assertEqual(sum(event['kind'] == 'close' for event in result['canonical_events']), 2)

    def test_unbraced_loop_literal_bodies_keep_separate_body_units(self):
        for control_text, kind, role, condition, value, literal in (
                ('while (ready) \'}\'', 'KtWhileExpression', 'CONDITION', 'ready', "'}'", character),
                ('for (x in items) "};"', 'KtForExpression', 'LOOP_RANGE', 'items', '"};"', simple_string)):
            with self.subTest(control=control_text):
                source = 'fun f() { ' + control_text + ' }\n'
                loop = kt(source, kind, control_text, [
                    container(source, role, condition, ref(source, condition)),
                    container(source, 'BODY', value, literal(source, value))])
                outer = block(source, '{ ' + control_text + ' }', [loop])
                self.counted(source, [function(source, [outer])], 4)

    def test_control_body_selection_rejects_missing_or_multiple_native_expressions(self):
        for body_text, kinds in [('go()', ()), ('"first"; go()', ('string', 'call')),
                                 ('"first"; \'}\'', ('string', 'character'))]:
            with self.subTest(body=body_text):
                source = 'fun f() { if (ready) ' + body_text + ' }\n'
                choices = {'string': lambda: simple_string(source, '"first"'),
                           'call': lambda: call(source, 'go()'),
                           'character': lambda: character(source, "'}'")}
                body = kt(source, 'KtContainerNodeForControlStructureBody', body_text,
                          [choices[kind]() for kind in kinds], element_type='THEN')
                control_text = 'if (ready) ' + body_text
                control = kt(source, 'KtIfExpression', control_text, [
                    container(source, 'CONDITION', 'ready', ref(source, 'ready')), body])
                outer = block(source, '{ ' + control_text + ' }', [control])
                result = self.gated(source, payload(source, [function(source, [outer])]))
                self.assertIn('must own exactly one expression', result['diagnostics'][0]['detail'])

    def test_braced_statement_if_has_written_closes(self):
        source = 'fun f() { if (ready) { go() } else { halt() } }\n'
        yes = block(source, '{ go() }', [call(source, 'go()')])
        no = block(source, '{ halt() }', [call(source, 'halt()')])
        control = kt(source, 'KtIfExpression', 'if (ready) { go() } else { halt() }', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '{ go() }', yes), container(source, 'ELSE', '{ halt() }', no)])
        self.counted(source, [function(source, [block(source, '{ if (ready) { go() } else { halt() } }', [control])])], 8)

    def test_unbraced_while_has_no_invented_close(self):
        source = 'fun f() { while (ready) go() }\n'
        loop = kt(source, 'KtWhileExpression', 'while (ready) go()', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'BODY', 'go()', call(source, 'go()'))])
        self.counted(source, [function(source, [block(source, '{ while (ready) go() }', [loop])])], 4)

    def test_braced_for_with_packed_body(self):
        source = 'fun f() { for (x in items) { show(x); next(x) } }\n'
        body = block(source, '{ show(x); next(x) }', [call(source, 'show(x)'), call(source, 'next(x)')])
        loop = kt(source, 'KtForExpression', 'for (x in items) { show(x); next(x) }', [
            kt(source, 'KtParameter', 'x'), container(source, 'LOOP_RANGE', 'items', ref(source, 'items')),
            container(source, 'BODY', '{ show(x); next(x) }', body)])
        self.counted(source, [function(source, [block(source, '{ for (x in items) { show(x); next(x) } }', [loop])])], 6)

    def test_when_expression_owns_entry_headers_and_written_closes(self):
        source = 'fun f(x: Int) = when (x) { 0 -> 1; else -> { val y = 2; y } }\n'
        first = kt(source, 'KtWhenEntry', '0 -> 1', [
            kt(source, 'KtWhenConditionWithExpression', '0', [scalar(source, '0')],
               element_type='WHEN_CONDITION_WITH_EXPRESSION'), scalar(source, '1')])
        second_body = block(source, '{ val y = 2; y }', [kt(source, 'KtProperty', 'val y = 2'), ref(source, 'y', 1)])
        second = kt(source, 'KtWhenEntry', 'else -> { val y = 2; y }', [second_body])
        when = kt(source, 'KtWhenExpression', 'when (x) { 0 -> 1; else -> { val y = 2; y } }', [first, second])
        self.counted(source, [function(source, [when])], 8)

    def test_when_literal_conditions_and_bodies_keep_explicit_branch_units(self):
        source = 'fun f(x: Char) = when (x) { \'A\', \'C\' -> \'}\'; else -> "}; ->" }\n'
        first = kt(source, 'KtWhenEntry', "'A', 'C' -> '}'", [
            kt(source, 'KtWhenConditionWithExpression', quoted, [character(source, quoted)],
               element_type='WHEN_CONDITION_WITH_EXPRESSION') for quoted in ("'A'", "'C'")
        ] + [character(source, "'}'")])
        second = kt(source, 'KtWhenEntry', 'else -> "}; ->"', [simple_string(source, '"}; ->"')])
        when = kt(source, 'KtWhenExpression', source[source.index('when'):].strip(), [first, second])
        result = self.counted(source, [function(source, [when])], 6)
        self.assertEqual([event['kind'] for event in result['canonical_events']],
                         ['header', 'header', 'header', 'close'])

    def test_when_body_selection_rejects_missing_or_multiple_native_expressions(self):
        for body_text, kinds in [('go()', ()), ('\'}\'; go()', ('character', 'call')),
                                 ('\'}\'; "second"', ('character', 'string'))]:
            with self.subTest(body=body_text):
                source = 'fun f() = when (x) { else -> ' + body_text + ' }\n'
                choices = {'character': lambda: character(source, "'}'"),
                           'call': lambda: call(source, 'go()'),
                           'string': lambda: simple_string(source, '"second"')}
                entry = kt(source, 'KtWhenEntry', 'else -> ' + body_text,
                           [choices[kind]() for kind in kinds])
                when = kt(source, 'KtWhenExpression', source[source.index('when'):].strip(), [entry])
                result = self.gated(source, payload(source, [function(source, [when])]))
                self.assertIn('lacks exactly one body', result['diagnostics'][0]['detail'])

    def test_masked_control_and_when_bodies_do_not_hide_interpolation_work(self):
        for prefix, suffix in [('fun f() = if (ready) ', ' else "plain"\n'),
                               ('fun f() = when (x) { else -> ', ' }\n')]:
            with self.subTest(prefix=prefix):
                quoted = '"${run { val y = 1; y }}"'
                source = prefix + quoted + suffix
                final_y = source.index('; y') + 2
                callback = lambda_tree(source, '{ val y = 1; y }',
                                       [kt(source, 'KtProperty', 'val y = 1'),
                                        Tree('KtNameReferenceExpression', final_y, final_y + 1)])
                work = lambda_call(source, 'run { val y = 1; y }', callback)
                entry = kt(source, 'KtBlockStringTemplateEntry', '${run { val y = 1; y }}', [work])
                template = kt(source, 'KtStringTemplateExpression', quoted, [entry])
                if 'if' in prefix:
                    expression = kt(source, 'KtIfExpression', source[source.index('if'):].strip(), [
                        container(source, 'CONDITION', 'ready', ref(source, 'ready')),
                        container(source, 'THEN', quoted, template),
                        container(source, 'ELSE', '"plain"', simple_string(source, '"plain"'))])
                else:
                    branch = kt(source, 'KtWhenEntry', 'else -> ' + quoted, [template])
                    expression = kt(source, 'KtWhenExpression', source[source.index('when'):].strip(), [branch])
                result = self.gated(source, payload(source, [function(source, [expression])]))
                self.assertIn('interpolation-with-independent-work-needs-review',
                              [issue['kind'] for issue in result['diagnostics']])

    def test_implicit_parameter_lambda_has_header_body_close(self):
        source = 'fun f() = items.map { it }\n'
        callback = lambda_tree(source, '{ it }', [ref(source, 'it', 1)])
        body = qualified_lambda(source, 'items.map { it }', ref(source, 'items'), 'map { it }', callback)
        self.counted(source, [function(source, [body])], 3)

    def test_explicit_lambda_parameters_and_packed_body(self):
        source = 'fun f() = items.map { x -> val y = x + 1; y }\n'
        callback = lambda_tree(source, '{ x -> val y = x + 1; y }',
                               [kt(source, 'KtProperty', 'val y = x + 1'), ref(source, 'y', 1)],
                               parameters=[kt(source, 'KtParameter', 'x')])
        body = qualified_lambda(source, 'items.map { x -> val y = x + 1; y }', ref(source, 'items'),
                                'map { x -> val y = x + 1; y }', callback)
        self.counted(source, [function(source, [body])], 4)

    def test_final_scalar_if_is_the_lambda_value(self):
        source = 'fun f() = items.map { if (ready) 1 else 2 }\n'
        control = kt(source, 'KtIfExpression', 'if (ready) 1 else 2', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', '1', scalar(source, '1')),
            container(source, 'ELSE', '2', scalar(source, '2'))])
        callback = lambda_tree(source, '{ if (ready) 1 else 2 }', [control])
        body = qualified_lambda(source, 'items.map { if (ready) 1 else 2 }', ref(source, 'items'),
                                'map { if (ready) 1 else 2 }', callback)
        self.counted(source, [function(source, [body])], 3)

    def test_prior_packed_if_in_lambda_is_a_statement(self):
        source = 'fun f() = items.map { if (ready) go() else halt(); 1 }\n'
        control = kt(source, 'KtIfExpression', 'if (ready) go() else halt()', [
            container(source, 'CONDITION', 'ready', ref(source, 'ready')),
            container(source, 'THEN', 'go()', call(source, 'go()')),
            container(source, 'ELSE', 'halt()', call(source, 'halt()'))])
        callback = lambda_tree(source, '{ if (ready) go() else halt(); 1 }', [control, scalar(source, '1')])
        body = qualified_lambda(source, 'items.map { if (ready) go() else halt(); 1 }', ref(source, 'items'),
                                'map { if (ready) go() else halt(); 1 }', callback)
        self.counted(source, [function(source, [body])], 7)

    def test_chained_callbacks_have_disjoint_headers(self):
        source = 'fun f() = items.map { it }.filter { it > 0 }\n'
        first = lambda_tree(source, '{ it }', [ref(source, 'it', 1)])
        second = lambda_tree(source, '{ it > 0 }', [scalar(source, 'it > 0')])
        mapped = qualified_lambda(source, 'items.map { it }', ref(source, 'items'), 'map { it }', first)
        body = qualified_lambda(source, 'items.map { it }.filter { it > 0 }', mapped,
                                'filter { it > 0 }', second)
        self.counted(source, [function(source, [body])], 6)

    def test_parenthesized_callback_then_chained_callback(self):
        source = 'fun f() = use({ it }).map { it }\n'
        first = lambda_tree(source, '{ it }', [ref(source, 'it')])
        arguments = kt(source, 'KtValueArgumentList', '({ it })', [
            kt(source, 'KtValueArgument', '{ it }', [first])])
        used = call(source, 'use({ it })', [arguments])
        second = lambda_tree(source, '{ it }', [ref(source, 'it', 1)], occurrence=1)
        body = qualified_lambda(source, 'use({ it }).map { it }', used, 'map { it }', second)
        self.counted(source, [function(source, [body])], 6)

    def test_scalar_lambda_continuation_preserves_wrapped_rows(self):
        for separator, expected in (('', 3), ('\n', 4)):
            source = 'fun f() = items.map { it }' + separator + '.size\n'
            callback = lambda_tree(source, '{ it }', [ref(source, 'it', 1)])
            mapped = qualified_lambda(source, 'items.map { it }', ref(source, 'items'), 'map { it }', callback)
            body = kt(source, 'KtDotQualifiedExpression', 'items.map { it }' + separator + '.size',
                      [mapped, ref(source, 'size')])
            self.counted(source, [function(source, [body])], expected)

    def test_primary_constructor_fields_are_independent_declarations(self):
        source = 'class Node(val left: Node?, val right: Node?)\n'
        params = kt(source, 'KtParameterList', '(val left: Node?, val right: Node?)', [
            kt(source, 'KtParameter', 'val left: Node?'), kt(source, 'KtParameter', 'val right: Node?')])
        constructor = kt(source, 'KtPrimaryConstructor', '(val left: Node?, val right: Node?)', [params])
        self.counted(source, [kt(source, 'KtClass', source.strip(), [constructor])], 2)

    def test_ordinary_constructor_parameters_are_structural(self):
        source = 'class Plain(left: Int, right: Int)\n'
        params = kt(source, 'KtParameterList', '(left: Int, right: Int)', [
            kt(source, 'KtParameter', 'left: Int'), kt(source, 'KtParameter', 'right: Int')])
        constructor = kt(source, 'KtPrimaryConstructor', '(left: Int, right: Int)', [params])
        self.counted(source, [kt(source, 'KtClass', source.strip(), [constructor])], 1)

    def test_promoted_fields_and_explicit_class_body_have_separate_units(self):
        source = 'class Node(val left: Node?, val right: Node?) {}\n'
        params = kt(source, 'KtParameterList', '(val left: Node?, val right: Node?)', [
            kt(source, 'KtParameter', 'val left: Node?'), kt(source, 'KtParameter', 'val right: Node?')])
        constructor = kt(source, 'KtPrimaryConstructor', '(val left: Node?, val right: Node?)', [params])
        body = kt(source, 'KtClassBody', '{}')
        self.counted(source, [kt(source, 'KtClass', source.strip(), [constructor, body])], 4)

    def test_destructuring_is_one_body_declaration(self):
        source = 'fun f() { val (a, b) = pair(); show(a) }\n'
        body = block(source, '{ val (a, b) = pair(); show(a) }', [
            kt(source, 'KtDestructuringDeclaration', 'val (a, b) = pair()'), call(source, 'show(a)')])
        self.counted(source, [function(source, [body])], 4)

    def test_wrapped_data_is_not_collapsed(self):
        source = 'val values = intArrayOf(\n 1,\n 2\n)\n'
        self.counted(source, [kt(source, 'KtProperty', source.strip())], 4, physical=4)

    def test_comments_and_literal_punctuation(self):
        source = '// whole\nval value = "//; }" /* tail */\nval other = /* outer /* nested */ comment */ 1\n'
        first = kt(source, 'KtProperty', 'val value = "//; }"', [simple_string(source, '"//; }"')])
        second = kt(source, 'KtProperty', 'val other = /* outer /* nested */ comment */ 1')
        self.counted(source, [first, second], 2, physical=2)

    def test_utf16_offsets_and_explicit_newline_normalization(self):
        source = 'val value = "λ😀" // tail\r\nfun f() = value\r\n'
        parsed = source.replace('\r\n', '\n')
        first = kt(parsed, 'KtProperty', 'val value = "λ😀"', [simple_string(parsed, '"λ😀"')])
        second = function(parsed, [ref(parsed, 'value', 1)], 'fun f() = value')
        self.counted(source, [first, second], 2, physical=2, parsed=parsed)

    def test_scalar_string_template_is_one_expression(self):
        source = 'fun f() = "value: ${x + 1}"\n'
        entry = kt(source, 'KtBlockStringTemplateEntry', '${x + 1}', [scalar(source, 'x + 1')])
        template = kt(source, 'KtStringTemplateExpression', '"value: ${x + 1}"', [
            kt(source, 'KtLiteralStringTemplateEntry', 'value: '), entry])
        self.counted(source, [function(source, [template])], 1)

    def test_template_with_independent_work_remains_gated(self):
        source = 'fun f() = "${run { val y = 1; y }}"\n'
        callback = lambda_tree(source, '{ val y = 1; y }', [kt(source, 'KtProperty', 'val y = 1'), ref(source, 'y', 1)])
        work = lambda_call(source, 'run { val y = 1; y }', callback)
        entry = kt(source, 'KtBlockStringTemplateEntry', '${run { val y = 1; y }}', [work])
        template = kt(source, 'KtStringTemplateExpression', '"${run { val y = 1; y }}"', [entry])
        self.gated(source, payload(source, [function(source, [template])]))

    def test_unreviewed_property_accessor_is_gated(self):
        source = 'val x: Int get() = 1\n'
        accessor = kt(source, 'KtPropertyAccessor', 'get() = 1')
        self.gated(source, payload(source, [kt(source, 'KtProperty', source.strip(), [accessor])]))

    def test_annotation_cannot_disappear_inside_function_header(self):
        source = '@JvmStatic fun f() { go() }\n'
        annotation = kt(source, 'KtAnnotationEntry', '@JvmStatic')
        modifiers = kt(source, 'KtModifierList', '@JvmStatic', [annotation])
        body = block(source, '{ go() }', [call(source, 'go()')])
        self.gated(source, payload(source, [function(source, [modifiers, body])]))

    def test_leading_comment_does_not_absorb_header_unit(self):
        source = '/* documentation */\nfun f() { go() }\n'
        body = block(source, '{ go() }', [call(source, 'go()')])
        self.counted(source, [function(source, [body])], 3, physical=1)

    def test_rejects_psi_boundary_inside_surrogate_pair(self):
        source = '😀'
        evidence = payload(source, [])
        nodes = evidence['psi']['nodes']
        self.assertEqual(len(nodes), 2)
        second = dict(nodes[1], id=2, start_utf16=1, text='\ude00')
        nodes[1].update(end_utf16=1, text='\ud83d')
        nodes.append(second)
        nodes[0]['children'] = [1, 2]
        result = count_source(source, evidence)
        self.assertIsNone(result['normalized_loc'])
        self.assertIn('surrogate pair', result['diagnostics'][0]['detail'])

    def test_rejects_non_newline_parser_source_change(self):
        source = 'val x = 1\n'
        parsed = 'val x = 2\n'
        self.gated(source, payload(source, [kt(parsed, 'KtProperty', parsed.strip())], parsed=parsed))

    def test_changed_validator_definition_is_rejected_before_execution(self):
        COUNTER_MODULE.reader_validator.cache_clear()
        try:
            with mock.patch.object(COUNTER_MODULE.Path, 'read_bytes',
                                   return_value=b'raise AssertionError("must never execute")'):
                with self.assertRaisesRegex(COUNTER_MODULE.CountError, 'Frozen native PSI validator bytes differ'):
                    COUNTER_MODULE.reader_validator()
        finally:
            COUNTER_MODULE.reader_validator.cache_clear()

    def test_unowned_executable_braces_are_gated(self):
        source = 'fun f() { go() }\n'
        unknown = kt(source, 'KtUnreviewedExpression', '{ go() }')
        self.gated(source, payload(source, [function(source, [unknown])]))

    def test_rejects_inconsistent_native_offsets_text_and_errors(self):
        source = 'val value = 1\n'
        roots = [kt(source, 'KtProperty', source.strip())]
        for change in ('text', 'overlap', 'parse-error', 'wrong-hash'):
            with self.subTest(change=change):
                evidence = payload(source, roots)
                nodes = evidence['psi']['nodes']
                leaf = next(node for node in nodes if 'text' in node and node['text'] == 'value')
                if change == 'text':
                    leaf['text'] = 'wrong'
                elif change == 'overlap':
                    leaf['start_utf16'] -= 1
                elif change == 'parse-error':
                    evidence['psi']['parse_errors'].append(dict(node=leaf['id'], start_utf16=leaf['start_utf16'],
                                                               end_utf16=leaf['end_utf16'], message='synthetic parse error'))
                else:
                    evidence['psi']['source_sha256'] = '0' * 64
                self.gated(source, evidence)

    def test_replay_uses_completed_controller_reader_paths_and_keeps_counts_unqualified(self):
        # This tree is generated solely in a temporary test directory. It is
        # synthetic report data, never a retained native execution receipt.
        source = 'val value = 1\n'
        source_hash = hashlib.sha256(source.encode()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='kotlin-psi-unit-fixture-') as temporary:
            root = Path(temporary)
            native = root / 'native'; native.mkdir()
            plan_path, controller_path, fixture_path = root / 'plan.json', root / 'controller.json', root / 'fixtures.json'
            inputs = [dict(id='application', kind='application', path='/synthetic/Main.kt',
                           sha256=source_hash, role='application', expected_parse='ok'),
                      dict(id='fixture--one', kind='fixture', path='fixture:one', text=source,
                           sha256=source_hash, expected_parse='ok')]
            plan = dict(schema='kotlin-native-source-reader-plan-v1', inputs=inputs,
                        profiles=[dict(id='synthetic-profile', inputs=['application'])], output=str(root))
            def write(path, value):
                path.write_text(json.dumps(value))
                return hashlib.sha256(path.read_bytes()).hexdigest()
            plan_hash = write(plan_path, plan)
            records, completed = [], []
            for item in inputs:
                folder = native / item['id']; folder.mkdir()
                reader_path = '/synthetic/' + item['id'] + '.kt'
                evidence = payload(source, [kt(source, 'KtProperty', source.strip())])['psi']
                evidence.update(id=item['id'], source_path=reader_path)
                (folder / 'source.kt').write_text(source)
                (folder / 'psi-source.kt').write_text(source)
                psi_hash = write(folder / 'psi.json', evidence)
                records.append(dict(id=item['id'], source_sha256=source_hash, psi_source_sha256=source_hash,
                                    psi_sha256=psi_hash, nodes=len(evidence['nodes']), parse_errors=0,
                                    status='parsed', canonical_loc=None, formatted_loc=None))
                completed.append(dict(item, reader_path=reader_path))
            native_hash = write(native / 'report.json', dict(schema='kotlin-native-source-reader-v1',
                status='read-awaiting-canonical-owner-review', items=records, source_evaluations=0,
                subject_recompilations=0, subject_main_invocations=0, canonical_loc=None,
                formatted_loc=None, chart_admission=False))
            write(controller_path, dict(schema='kotlin-native-source-reader-results-v1',
                status='read-awaiting-canonical-owner-review', reader_evidence_validated=True,
                plan_sha256=plan_hash, native_reader_report_sha256=native_hash, inputs=completed))
            write(fixture_path, dict(schema='kotlin-source-unit-fixture-contract-v1',
                rule_version=COUNTER_MODULE.RULE_VERSION,
                fixtures=[dict(id='fixture--one', outcome='candidate-count', canonical_units=1)]))
            result = COUNTER_MODULE.replay(plan_path, native, fixture_path, controller_path)
            self.assertEqual(result['profiles'][0]['candidate_canonical_loc'], 1)
            self.assertIsNone(result['profiles'][0]['canonical_loc'])
            self.assertTrue(result['native_fixture_expectations_passed'])
            self.assertFalse(result['native_reader_terminal_verified'])
            for flag in ('canonical_loc_qualified', 'formatted_loc_qualified', 'chart_admission'):
                self.assertIs(result[flag], False)


class SavedKotlinPsiRegressions(unittest.TestCase):
    """Consume immutable native v3 evidence; never create a replay artifact."""

    @classmethod
    def setUpClass(cls):
        cls.root = COUNTER_MODULE.ROOT
        cls.run_directory = cls.root / 'experiments/kotlin/source-counts-v3/run-v1'
        cls.native = cls.run_directory / 'native-reader/sources'
        cls.replayed = COUNTER_MODULE.replay(
            cls.root / 'experiments/kotlin/source-counts-v3/plan-v1.json', cls.native,
            controller_report=cls.run_directory / 'report.json')

    def saved(self, identity):
        folder = self.native / identity
        return ((folder / 'source.kt').read_bytes().decode(),
                dict(psi=json.loads((folder / 'psi.json').read_bytes()),
                     psi_source=(folder / 'psi-source.kt').read_bytes().decode()))

    def test_all_twenty_helpers_retain_the_scalar_template_return(self):
        helpers = {key: value for key, value in self.replayed['files'].items()
                   if key.endswith('--application-helper')}
        self.assertEqual(len(helpers), 20)
        for identity, result in helpers.items():
            with self.subTest(identity=identity):
                source, evidence = self.saved(identity)
                tree = COUNTER_MODULE.Tree(source, evidence)
                template = next(n for n in tree.nodes
                                if n['kind'] == 'KtStringTemplateExpression' and
                                tree.text[n['start']:n['end']] == '"-$rounded"')
                wrapper = tree.nodes[template['parent']]
                self.assertEqual(wrapper['element_type'], 'THEN')
                self.assertEqual(wrapper['children'], [template['id']])
                self.assertIn(template['id'], tree.hidden)
                selected = tree.role(tree.nodes[wrapper['parent']], 'THEN')
                self.assertEqual(selected['id'], template['id'])
                self.assertEqual(result['diagnostics'], [])
                # Four package/import units; object header/close; size=6;
                # input/text/bytes=3; write overloads=4+1; fixed=5; lines=1.
                self.assertEqual(result['normalized_loc'], 26)
                begin = source.index('return if ')
                end = source.index('\n', begin)
                self.assertFalse(any(begin <= event['start'] < end
                                     for event in result['canonical_events']))

    def test_both_revcomp_forms_keep_all_sixteen_when_branches(self):
        for form in ('compact', 'optimized'):
            identity = 'kotlin-revcomp-' + form + '--application'
            with self.subTest(identity=identity):
                source, evidence = self.saved(identity)
                tree = COUNTER_MODULE.Tree(source, evidence)
                entries = [n for n in tree.nodes if n['kind'] == 'KtWhenEntry']
                self.assertEqual(len(entries), 16)
                result = self.replayed['files'][identity]
                self.assertEqual(result['diagnostics'], [])
                # Package/import=2; complement when=34; record=16; main=18.
                self.assertEqual(result['normalized_loc'], 70)
                literal_bodies = 0
                for entry in entries:
                    arrow = tree.direct_leaf(entry, '->')
                    bodies = [node for node in tree.semantic(entry, include_masked=True)
                              if node['start'] >= arrow['end']]
                    self.assertEqual(len(bodies), 1)
                    if bodies[0]['element_type'] == 'CHARACTER_CONSTANT':
                        literal_bodies += 1
                        self.assertIn(bodies[0]['id'], tree.hidden)
                    events = [event for event in result['canonical_events']
                              if event['native_node'] == entry['id']]
                    self.assertEqual([(event['kind'], event['units']) for event in events], [('header', 1)])
                self.assertEqual(literal_bodies, 15)

    def test_previously_passing_authored_counts_and_owners_are_unchanged(self):
        previous = json.loads((self.root / 'experiments/kotlin/source-units-v1/replay-v1.json').read_bytes())
        passing = {key: value for key, value in previous['files'].items()
                   if key.startswith('kotlin-') and value['normalized_loc'] is not None}
        self.assertEqual(len(passing), 18)
        for identity, old in passing.items():
            with self.subTest(identity=identity):
                current = dict(self.replayed['files'][identity])
                current['grammar'] = old['grammar']
                self.assertEqual(current, old)

    def test_actual_replay_has_all_authored_candidates_and_preserves_every_gate(self):
        replayed = self.replayed
        authored = [value for key, value in replayed['files'].items() if key.startswith('kotlin-')]
        self.assertEqual(len(authored), 40)
        self.assertTrue(all(value['normalized_loc'] is not None and not value['diagnostics'] for value in authored))
        self.assertEqual(len(replayed['fixture_checks']), 14)
        self.assertTrue(all(check['passed'] for check in replayed['fixture_checks']))
        self.assertEqual(len(replayed['profiles']), 20)
        self.assertTrue(all(row['candidate_canonical_loc'] is not None for row in replayed['profiles']))
        for item in [replayed, *replayed['files'].values(), *replayed['profiles']]:
            for flag in COUNTER_MODULE.FALSE_FLAGS:
                self.assertIs(item[flag], False)
        self.assertFalse(replayed['native_reader_terminal_verified'])
        self.assertFalse(replayed['formatter_evidence_available'])
        self.assertIsNone(replayed['formatted_loc'])
        self.assertTrue(all(row['canonical_loc'] is None and row['formatted_loc'] is None
                            for row in replayed['profiles']))


if __name__ == '__main__':
    unittest.main()
