"""Pure counter tests using synthetic terms and separately named saved native ASTs.

Only the Python source-unit counter is exercised. No test invokes Elixir, a
compiler, a formatter, a subprocess, or application code. Synthetic fixtures
remain distinct from the already retained source-reader artifacts consumed by
SavedNativeOwnerRegressions; these tests do not qualify process provenance.
"""
import base64
import importlib.util
import json
from pathlib import Path
import sys
import unittest


COUNTER = Path(__file__).with_name('elixir_source_units.py')
SPEC = importlib.util.spec_from_file_location('synthetic_elixir_source_units', COUNTER)
COUNTER_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COUNTER_MODULE
SPEC.loader.exec_module(COUNTER_MODULE)
count_source = COUNTER_MODULE.count_source


class Atom(str):
    """Distinguish an Erlang atom from a binary before lossless JSON tagging."""


def tagged(value):
    if isinstance(value, Atom):
        return ['atom', str(value)]
    if isinstance(value, str):
        return ['binary', base64.b64encode(value.encode()).decode('ascii')]
    if isinstance(value, int) and not isinstance(value, bool):
        return ['integer', str(value)]
    if isinstance(value, tuple):
        return ['tuple', [tagged(item) for item in value]]
    if isinstance(value, list):
        return ['list', [tagged(item) for item in value]]
    if isinstance(value, dict):
        return ['map', [[tagged(key), tagged(item)] for key, item in value.items()]]
    raise TypeError(type(value).__name__)


def position(source, token, occurrence=0):
    offset = -1
    for _ in range(occurrence + 1):
        offset = source.index(token, offset + 1)
    return [(Atom('line'), source.count('\n', 0, offset) + 1),
            (Atom('column'), offset - source.rfind('\n', 0, offset))]


def node(source, name, lexeme=None, arguments=None, occurrence=0, **extra):
    metadata = [(Atom(key), value) for key, value in extra.items()]
    metadata += position(source, lexeme or name, occurrence)
    return (Atom(name), metadata, Atom('nil') if arguments is None else arguments)


def literal(source, value, lexeme, occurrence=0, **extra):
    return node(source, '__block__', lexeme, [value], occurrence, **extra)


def sequence(*expressions):
    return (Atom('__block__'), [], list(expressions))


def key(source, name, occurrence=0, keyword=False):
    extra = {'format': Atom('keyword')} if keyword else {}
    return literal(source, Atom(name), name, occurrence, **extra)


def payload(ast, comments=()):
    return {'ast': tagged(ast), 'comments': tagged(list(comments))}


def comment(source, text):
    return dict(position(source, text)) | {
        Atom('text'): text, Atom('previous_eol_count'): 0, Atom('next_eol_count'): 1}


def definition(source, body, *, name='f', args=(), do_occurrence=0,
               end_occurrence=0, def_occurrence=0, keyword=False):
    head = node(source, name, name + '(', list(args),
                closing=position(source, ')', def_occurrence))
    extra = {} if keyword else {
        'do': position(source, 'do', do_occurrence),
        'end': position(source, 'end', end_occurrence)}
    return node(source, 'def', 'def',
                [head, [(key(source, 'do', do_occurrence, keyword), body)]],
                def_occurrence, **extra)


def for_value(source):
    generator = node(source, '<-', arguments=[node(source, 'item'), node(source, 'items')])
    return node(source, 'for', arguments=[generator, [
        (key(source, 'do'), node(source, 'item', occurrence=2))]],
        do=position(source, 'do'), end=position(source, 'end'))


class SourceUnitFixtures(unittest.TestCase):
    def counted(self, source, ast, expected, *, physical=None, comments=()):
        result = count_source(source, payload(ast, comments))
        self.assertEqual(result['diagnostics'], [], result)
        self.assertEqual(result['normalized_loc'], expected, result)
        self.assertEqual(result['candidate_normalized_loc'], expected, result)
        if physical is not None:
            self.assertEqual(result['physical_loc'], physical, result)
        for name in ('canonical_loc_qualified', 'formatted_loc_qualified', 'chart_admission'):
            self.assertIs(result[name], False, result)
        return result

    def gated(self, source, ast, *, comments=()):
        result = count_source(source, payload(ast, comments))
        self.assertTrue(result['diagnostics'], result)
        self.assertIsNone(result['normalized_loc'], result)
        for name in ('canonical_loc_qualified', 'formatted_loc_qualified', 'chart_admission'):
            self.assertIs(result[name], False, result)
        return result

    def test_packed_independent_statements(self):
        source = 'x = 1; y = 2; show(x)\n'
        left = node(source, '=', arguments=[node(source, 'x'), literal(source, 1, '1')])
        right = node(source, '=', occurrence=1,
                     arguments=[node(source, 'y'), literal(source, 2, '2')])
        call = node(source, 'show', arguments=[node(source, 'x', occurrence=1)],
                    closing=position(source, ')'))
        self.counted(source, sequence(left, right, call), 3, physical=1)

    def test_chained_matches_expand_but_destructuring_does_not(self):
        source = 'x = y = 1\n'
        inner = node(source, '=', occurrence=1,
                     arguments=[node(source, 'y'), literal(source, 1, '1')])
        outer = node(source, '=', arguments=[node(source, 'x'), inner])
        self.counted(source, outer, 2, physical=1)
        source = '{left, right} = {1, 2}\n'
        left = literal(source, (node(source, 'left'), node(source, 'right')), '{',
                       closing=position(source, '}'))
        right = literal(source, (literal(source, 1, '1'), literal(source, 2, '2')), '{', 1,
                        closing=position(source, '}', 1))
        self.counted(source, node(source, '=', arguments=[left, right]), 1, physical=1)

    def test_keyword_definition_has_no_invented_header_or_close(self):
        source = 'def f(x), do: x + 1\n'
        body = node(source, '+', arguments=[node(source, 'x', occurrence=1), literal(source, 1, '1')])
        ast = definition(source, body, args=[node(source, 'x')], keyword=True)
        self.counted(source, ast, 1, physical=1)

    def test_keyword_definition_parameter_pattern_is_not_body_assignment(self):
        source = 'def f(x = y), do: z = 1\n'
        pattern = node(source, '=', arguments=[node(source, 'x'), node(source, 'y')])
        body = node(source, '=', occurrence=1,
                    arguments=[node(source, 'z'), literal(source, 1, '1')])
        # This first match belongs to the formal pattern. The definition is an
        # expression-only form with one executable body match, hence one unit.
        ast = definition(source, body, args=[pattern], keyword=True)
        self.counted(source, ast, 1, physical=1)

    def test_explicit_definition_has_header_body_close(self):
        source = 'def f(x) do x end\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        self.counted(source, ast, 3, physical=1)

    def test_wrapped_explicit_header_is_one_unit(self):
        source = 'def f(\n  x\n) do\n  x\nend\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        self.counted(source, ast, 3, physical=5)

    def test_explicit_callback_owns_surrounding_call_prefix(self):
        source = 'map(items, fn x -> x end)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        ast = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        self.counted(source, ast, 3, physical=1)

    def test_callback_packed_body_and_wrapped_structural_suffix(self):
        source = 'map(items, fn x -> y = x; y end\n)\n'
        bind = node(source, '=', arguments=[node(source, 'y'), node(source, 'x', occurrence=1)])
        clause = node(source, '->', arguments=[[node(source, 'x')], sequence(bind, node(source, 'y', occurrence=1))])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        ast = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        self.counted(source, ast, 4, physical=2)

    def test_comment_between_callback_and_wrapped_suffix_is_ignored(self):
        source = 'map(items, fn x -> x end # comment\n)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        ast = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        self.counted(source, ast, 3, physical=2, comments=[comment(source, '# comment')])

    def test_callback_followed_by_scalar_pipeline_shares_expression_unit(self):
        # The native AST-backed rule resolves the archived lexical review gate:
        # scalar continuation belongs to this same independent expression.
        source = 'map(items, fn x -> x end) |> finish()\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')', 1))
        self.counted(source, node(source, '|>', arguments=[call, finish]), 3, physical=1)

    def test_explicit_control_scalar_pipeline_shares_expression_unit(self):
        source = 'for item <- items do item end |> finish()\n'
        finish = node(source, 'finish', arguments=[], closing=position(source, ')'))
        result = self.counted(source, node(source, '|>', arguments=[for_value(source), finish]), 3, physical=1)
        self.assertEqual(len(result['expression_continuations']), 1)

    def test_explicit_control_wrapped_pipeline_preserves_physical_row(self):
        source = 'for item <- items do item end\n|> finish()\n'
        finish = node(source, 'finish', arguments=[], closing=position(source, ')'))
        self.counted(source, node(source, '|>', arguments=[for_value(source), finish]), 4, physical=2)

    def test_explicit_control_pipeline_stops_before_packed_next_statement(self):
        source = 'for item <- items do item end |> finish(); next()\n'
        finish = node(source, 'finish', arguments=[], closing=position(source, ')'))
        following = node(source, 'next', arguments=[], closing=position(source, ')', 1))
        pipe = node(source, '|>', arguments=[for_value(source), finish])
        self.counted(source, sequence(pipe, following), 4, physical=1)

    def test_explicit_control_following_match_is_not_scalar_tail(self):
        source = 'use((for item <- items do item end), following = 1)\n'
        following = node(source, '=', arguments=[node(source, 'following'), literal(source, 1, '1')])
        ast = node(source, 'use', arguments=[for_value(source), following], closing=position(source, ')', 1))
        result = self.gated(source, ast)
        self.assertIn('non-scalar-expression-continuation-needs-review',
                      [d['kind'] for d in result['diagnostics']])

    def test_explicit_control_following_sequence_is_not_scalar_tail(self):
        source = 'use((for item <- items do item end), (first(); second()))\n'
        first = node(source, 'first', arguments=[], closing=position(source, ')', 1))
        second = node(source, 'second', arguments=[], closing=position(source, ')', 2))
        ast = node(source, 'use', arguments=[for_value(source), sequence(first, second)],
                   closing=position(source, ')', 4))
        result = self.gated(source, ast)
        self.assertIn('non-scalar-expression-continuation-needs-review',
                      [d['kind'] for d in result['diagnostics']])

    def test_explicit_control_following_callback_is_not_scalar_tail(self):
        source = 'use((for item <- items do item end), fn x -> x end)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end', 1))
        ast = node(source, 'use', arguments=[for_value(source), callback], closing=position(source, ')', 1))
        result = self.gated(source, ast)
        self.assertIn('non-scalar-expression-continuation-needs-review',
                      [d['kind'] for d in result['diagnostics']])

    def test_explicit_if_pipeline_preserves_both_branch_bodies(self):
        source = 'if ready do yes else no end |> finish()\n'
        control = node(source, 'if', arguments=[node(source, 'ready'), [
            (key(source, 'do'), node(source, 'yes')), (key(source, 'else'), node(source, 'no'))]],
            do=position(source, 'do'), end=position(source, 'end'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')'))
        self.counted(source, node(source, '|>', arguments=[control, finish]), 5, physical=1)

    def test_explicit_case_pipeline_preserves_pattern_and_body(self):
        source = 'case value do :ok -> 1 end |> finish()\n'
        clause = node(source, '->', arguments=[[literal(source, Atom('ok'), ':ok')], literal(source, 1, '1')])
        control = node(source, 'case', arguments=[node(source, 'value'), [(key(source, 'do'), [clause])]],
                       do=position(source, 'do'), end=position(source, 'end'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')'))
        self.counted(source, node(source, '|>', arguments=[control, finish]), 4, physical=1)

    def test_callback_followed_by_scalar_list_value_shares_expression_unit(self):
        source = '[map(items, fn x -> x end), "\\n"]\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        # The reader uses unescape:false, so the encoded binary has two bytes.
        value = literal(source, '\\n', '"', delimiter='"')
        self.counted(source, literal(source, [call, value], '[', closing=position(source, ']')), 3, physical=1)

    def test_callback_followed_by_scalar_call_argument_shares_expression_unit(self):
        source = 'map(items, fn x -> x end, another)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        ast = node(source, 'map', arguments=[node(source, 'items'), callback, node(source, 'another')],
                   closing=position(source, ')'))
        self.counted(source, ast, 3, physical=1)

    def test_wrapped_scalar_pipeline_preserves_physical_row(self):
        source = 'map(items, fn x -> x end)\n|> finish()\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')', 1))
        self.counted(source, node(source, '|>', arguments=[call, finish]), 4, physical=2)

    def test_wrapped_scalar_list_tail_preserves_physical_row(self):
        source = '[map(items, fn x -> x end),\n "\\n"]\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        value = literal(source, '\\n', '"', delimiter='"')
        self.counted(source, literal(source, [call, value], '[', closing=position(source, ']')), 4, physical=2)

    def test_packed_statement_after_scalar_continuation_is_independent(self):
        source = 'map(items, fn x -> x end) |> finish(); next()\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')', 1))
        following = node(source, 'next', arguments=[], closing=position(source, ')', 2))
        ast = sequence(node(source, '|>', arguments=[call, finish]), following)
        self.counted(source, ast, 4, physical=1)

    def test_assignment_in_following_argument_is_not_scalar_continuation(self):
        source = 'map(items, fn x -> x end, following = 1)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        following = node(source, '=', arguments=[node(source, 'following'), literal(source, 1, '1')])
        ast = node(source, 'map', arguments=[node(source, 'items'), callback, following],
                   closing=position(source, ')'))
        self.gated(source, ast)

    def test_chained_matches_in_following_argument_are_not_scalar_continuation(self):
        source = 'map(items, fn x -> x end, following = another = 1)\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        inner = node(source, '=', occurrence=1,
                     arguments=[node(source, 'another'), literal(source, 1, '1')])
        following = node(source, '=', arguments=[node(source, 'following'), inner])
        ast = node(source, 'map', arguments=[node(source, 'items'), callback, following],
                   closing=position(source, ')'))
        self.gated(source, ast)

    def test_sequence_in_following_argument_is_not_scalar_continuation(self):
        source = 'map(items, fn x -> x end, (first(); second()))\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        first = node(source, 'first', arguments=[], closing=position(source, ')'))
        second = node(source, 'second', arguments=[], closing=position(source, ')', 1))
        following = sequence(first, second)
        ast = node(source, 'map', arguments=[node(source, 'items'), callback, following],
                   closing=position(source, ')', 3))
        self.gated(source, ast)

    def test_second_callback_is_not_scalar_continuation(self):
        source = 'map(items, fn x -> x end, fn y -> y end)\n'
        first_clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        first = node(source, 'fn', arguments=[first_clause], closing=position(source, 'end'))
        second_clause = node(source, '->', occurrence=1,
                             arguments=[[node(source, 'y')], node(source, 'y', occurrence=1)])
        second = node(source, 'fn', occurrence=1, arguments=[second_clause], closing=position(source, 'end', 1))
        ast = node(source, 'map', arguments=[node(source, 'items'), first, second],
                   closing=position(source, ')'))
        self.gated(source, ast)

    def test_nested_callback_stops_before_packed_sibling_body_expression(self):
        source = 'map(items, fn x -> map(items, fn y -> y end); x end)\n'
        inner_clause = node(source, '->', occurrence=1,
                            arguments=[[node(source, 'y')], node(source, 'y', occurrence=1)])
        inner_callback = node(source, 'fn', occurrence=1, arguments=[inner_clause],
                              closing=position(source, 'end'))
        inner_call = node(source, 'map', occurrence=1,
                          arguments=[node(source, 'items', occurrence=1), inner_callback],
                          closing=position(source, ')'))
        outer_clause = node(source, '->', arguments=[
            [node(source, 'x')], sequence(inner_call, node(source, 'x', occurrence=1))])
        outer_callback = node(source, 'fn', arguments=[outer_clause], closing=position(source, 'end', 1))
        ast = node(source, 'map', arguments=[node(source, 'items'), outer_callback],
                   closing=position(source, ')', 1))
        self.counted(source, ast, 6, physical=1)

    def test_scalar_continuation_stops_at_next_case_clause(self):
        source = 'case value do :a -> map(items, fn x -> x end) |> finish(); :b -> 0 end\n'
        callback_clause = node(source, '->', occurrence=1,
                               arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[callback_clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')', 1))
        first = node(source, '->', arguments=[
            [literal(source, Atom('a'), ':a')], node(source, '|>', arguments=[call, finish])])
        second = node(source, '->', occurrence=2,
                      arguments=[[literal(source, Atom('b'), ':b')], literal(source, 0, '0')])
        ast = node(source, 'case', arguments=[node(source, 'value'), [(key(source, 'do'), [first, second])]],
                   do=position(source, 'do'), end=position(source, 'end', 1))
        self.counted(source, ast, 8, physical=1)

    def test_scalar_continuation_stops_at_else_branch(self):
        source = 'if ready do map(items, fn x -> x end) |> finish() else fallback end\n'
        clause = node(source, '->', arguments=[[node(source, 'x')], node(source, 'x', occurrence=1)])
        callback = node(source, 'fn', arguments=[clause], closing=position(source, 'end'))
        call = node(source, 'map', arguments=[node(source, 'items'), callback], closing=position(source, ')'))
        finish = node(source, 'finish', arguments=[], closing=position(source, ')', 1))
        branch = node(source, '|>', arguments=[call, finish])
        ast = node(source, 'if', arguments=[node(source, 'ready'), [
            (key(source, 'do'), branch), (key(source, 'else'), node(source, 'fallback'))]],
                   do=position(source, 'do'), end=position(source, 'end', 1))
        self.counted(source, ast, 7, physical=1)

    def test_case_patterns_are_branch_headers(self):
        source = 'case value do :ok -> 1; :error -> 0 end\n'
        first = node(source, '->', arguments=[[literal(source, Atom('ok'), ':ok')], literal(source, 1, '1')])
        second = node(source, '->', occurrence=1,
                      arguments=[[literal(source, Atom('error'), ':error')], literal(source, 0, '0')])
        ast = node(source, 'case', arguments=[node(source, 'value'), [(key(source, 'do'), [first, second])]],
                   do=position(source, 'do'), end=position(source, 'end'))
        self.counted(source, ast, 6, physical=1)

    def test_assignment_valued_case_joins_first_header(self):
        source = 'result = case value do :ok -> 1 end\n'
        clause = node(source, '->', arguments=[[literal(source, Atom('ok'), ':ok')], literal(source, 1, '1')])
        control = node(source, 'case', arguments=[node(source, 'value'), [(key(source, 'do'), [clause])]],
                       do=position(source, 'do'), end=position(source, 'end'))
        self.counted(source, node(source, '=', arguments=[node(source, 'result'), control]), 4, physical=1)

    def test_keyword_conditional_remains_expression(self):
        source = 'value = if ready, do: 1, else: 2\n'
        control = node(source, 'if', arguments=[node(source, 'ready'), [
            (key(source, 'do', keyword=True), literal(source, 1, '1')),
            (key(source, 'else', keyword=True), literal(source, 2, '2'))]])
        self.counted(source, node(source, '=', arguments=[node(source, 'value'), control]), 1, physical=1)

    def test_literal_data_wrapping_is_not_collapsed_to_ast_count(self):
        source = 'data = [\n  1,\n  2\n]\ncount(data)\n'
        data = literal(source, [literal(source, 1, '1'), literal(source, 2, '2')], '[',
                       closing=position(source, ']'))
        bind = node(source, '=', arguments=[node(source, 'data'), data])
        call = node(source, 'count', arguments=[node(source, 'data', occurrence=1)], closing=position(source, ')'))
        self.counted(source, sequence(bind, call), 5, physical=5)

    def test_comments_do_not_hide_literal_punctuation(self):
        source = '# whole\nvalue = "#;end" # tail\nvalue\n'
        bind = node(source, '=', arguments=[node(source, 'value'), literal(source, '#;end', '"', delimiter='"')])
        ast = sequence(bind, node(source, 'value', occurrence=1))
        self.counted(source, ast, 2, physical=2,
                     comments=[comment(source, '# whole'), comment(source, '# tail')])

    def test_unicode_columns_and_crlf(self):
        source = 'value = "λ" # tail\r\nshow(value)\r\n'
        bind = node(source, '=', arguments=[node(source, 'value'), literal(source, 'λ', '"', delimiter='"')])
        call = node(source, 'show', arguments=[node(source, 'value', occurrence=1)], closing=position(source, ')'))
        self.counted(source, sequence(bind, call), 2, physical=2, comments=[comment(source, '# tail')])

    def test_character_semicolon_is_not_a_statement_separator(self):
        source = 'code = ?;\n'
        value = literal(source, 59, '?;', token='?;')
        self.counted(source, node(source, '=', arguments=[node(source, 'code'), value]), 1, physical=1)

    def test_missing_explicit_block_metadata_is_gated(self):
        source = 'def f(x) do x end\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        ast = (ast[0], [(k, v) for k, v in ast[1] if k not in (Atom('do'), Atom('end'))], ast[2])
        self.gated(source, ast)

    def test_repeated_grouping_and_expression_metadata_are_legitimate(self):
        # Macro documents repeated :parens and :end_of_expression entries.
        # These values model nested grouping; they are synthetic positions,
        # not evidence that the retained native reader emitted this exact AST.
        source = '((value)); value\n'
        outer = [(Atom('closing'), position(source, ')', 1))] + position(source, '(')
        inner = [(Atom('closing'), position(source, ')'))] + position(source, '(', 1)
        end_first = [(Atom('newlines'), 0)] + position(source, ';')
        end_second = [(Atom('newlines'), 1)] + position(source, '\n')
        first = node(source, 'value')
        repeated = [(Atom('parens'), outer), (Atom('parens'), inner),
                    (Atom('end_of_expression'), end_first), (Atom('end_of_expression'), end_second)]
        first = (first[0], repeated + first[1], first[2])
        self.counted(source, sequence(first, node(source, 'value', occurrence=1)), 2, physical=1)
        # Counting ignores grouping metadata. Assert the keyword-list helper's
        # first-value behavior separately so this regression cannot pass after
        # an accidental list-to-last-value-map conversion.
        decoded = COUNTER_MODULE.decode(tagged(first))[1]
        meta = COUNTER_MODULE.metadata(decoded)
        self.assertEqual(meta['parens'], COUNTER_MODULE.decode(tagged(outer)))
        self.assertEqual(meta['end_of_expression'], COUNTER_MODULE.decode(tagged(end_first)))

    def test_identical_duplicate_ownership_metadata_is_consistent(self):
        source = 'def f(x) do x end\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        ast = (ast[0], ast[1] + [(Atom('end'), position(source, 'end'))], ast[2])
        self.counted(source, ast, 3, physical=1)

    def test_conflicting_duplicate_ownership_metadata_is_gated(self):
        source = 'def f(x) do x end\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        for field, conflicting in [('line', 2), ('column', 2),
                                   ('do', position(source, 'x')),
                                   ('end', position(source, 'x', 1))]:
            with self.subTest(field=field):
                ambiguous = (ast[0], ast[1] + [(Atom(field), conflicting)], ast[2])
                self.gated(source, ambiguous)

        call_source = 'map(items, fn x -> x end)\n'
        clause = node(call_source, '->', arguments=[
            [node(call_source, 'x')], node(call_source, 'x', occurrence=1)])
        callback = node(call_source, 'fn', arguments=[clause], closing=position(call_source, 'end'))
        callback = (callback[0], callback[1] + [(Atom('closing'), position(call_source, 'x', 1))], callback[2])
        call = node(call_source, 'map', arguments=[node(call_source, 'items'), callback],
                    closing=position(call_source, ')'))
        self.gated(call_source, call)

    def test_contradictory_closer_position_is_gated(self):
        source = 'def f(x) do x end\n'
        ast = definition(source, node(source, 'x', occurrence=1), args=[node(source, 'x')])
        ast = (ast[0], [(k, position(source, 'x', 1) if k == Atom('end') else v) for k, v in ast[1]], ast[2])
        self.gated(source, ast)

    def test_overlapping_sibling_owners_are_gated(self):
        source = 'def a() do 1 end; def b() do 2 end\n'
        first = definition(source, literal(source, 1, '1'), name='a', end_occurrence=1)
        second = definition(source, literal(source, 2, '2'), name='b',
                            do_occurrence=1, end_occurrence=1, def_occurrence=1)
        self.gated(source, sequence(first, second))

    def test_unknown_macro_block_is_gated(self):
        source = 'custom do value end\n'
        ast = node(source, 'custom', arguments=[[(key(source, 'do'), node(source, 'value'))]],
                   do=position(source, 'do'), end=position(source, 'end'))
        self.gated(source, ast)

    def test_comment_metadata_must_match_exact_source(self):
        source = 'value = 1 # tail\n'
        ast = node(source, '=', arguments=[node(source, 'value'), literal(source, 1, '1')])
        bad = comment(source, '# tail')
        bad[Atom('column')] = 1
        self.gated(source, ast, comments=[bad])

    def test_interpolation_independent_work_remains_unqualified(self):
        source = '"value: #{(x = 1; x + 1)}"\n'
        bind = node(source, '=', arguments=[node(source, 'x'), literal(source, 1, '1')])
        addition = node(source, '+', arguments=[node(source, 'x', occurrence=1), literal(source, 1, '1', 1)])
        place = position(source, '#{')
        conversion = ((Atom('.'), place, [Atom('Elixir.Kernel'), Atom('to_string')]),
                      place, [sequence(bind, addition)])
        interpolated = (Atom('::'), place, [conversion, (Atom('binary'), place, Atom('nil'))])
        ast = node(source, '<<>>', '"', ['value: ', interpolated], delimiter='"')
        self.gated(source, ast)


class SavedNativeOwnerRegressions(unittest.TestCase):
    """Read the completed native reader; never generate ASTs or rewrite replay-v1."""

    @classmethod
    def setUpClass(cls):
        root = COUNTER.resolve().parents[2]
        cls.reader = root/'experiments/elixir/source-counts-v1/run-v1/reader'
        cls.previous = json.loads((root/'experiments/elixir/source-units-v1/replay-v1.json').read_bytes())
        cls.native = json.loads((cls.reader/'report.json').read_bytes())

    def saved_count(self, identity, formatted=False):
        directory = self.reader/identity
        source = directory/('formatted.exs' if formatted else 'source.exs')
        ast = directory/('formatted-ast.json' if formatted else 'ast.json')
        return count_source(source.read_bytes().decode('utf-8'), json.loads(ast.read_bytes()))

    def test_actual_control_and_callback_continuations(self):
        for benchmark, original, formatted in [('spectralnorm', 28, 29), ('nbody', 68, 112),
                                               ('knucleotide', 47, 52)]:
            identity = 'elixir-'+benchmark+'-compact--application'
            with self.subTest(benchmark=benchmark):
                result = self.saved_count(identity)
                self.assertEqual(result['diagnostics'], [])
                self.assertEqual(result['normalized_loc'], original)
                self.assertEqual(self.saved_count(identity, True)['normalized_loc'], formatted)
                if benchmark == 'spectralnorm':
                    row = next(e for e in result['expansions'] if e['line'] == 12)
                    self.assertEqual(row['original'].strip(), 'end |> List.to_tuple()')
                    self.assertEqual(row['units'], 1)
                    self.assertEqual([e['kind'] for e in row['canonical_events']], ['close'])
                    self.assertEqual(row['statements'][0]['reason'], 'same-native-expression-scalar-continuation')

    def test_all_retained_sources_change_only_original_spectralnorm_unit(self):
        reviewed = 0
        for identity, previous in self.previous['files'].items():
            if not identity.startswith('elixir-'):
                continue
            for variant, formatted in [('original', False), ('formatted', True)]:
                with self.subTest(identity=identity, variant=variant):
                    result = self.saved_count(identity, formatted)
                    expected = previous[variant]['normalized_loc']
                    if not formatted and identity in {
                            'elixir-spectralnorm-compact--application',
                            'elixir-spectralnorm-optimized--application'}:
                        expected -= 1
                    self.assertEqual(result['diagnostics'], [])
                    self.assertEqual(result['normalized_loc'], expected)
                    self.assertEqual(result['physical_loc'], previous[variant]['physical_loc'])
                    self.assertIs(result['canonical_loc_qualified'], False)
                    reviewed += 1
        self.assertEqual(reviewed, 120)

    def test_original_fourteen_native_fixture_contracts_are_preserved(self):
        actual = {item['id']: item for item in self.native['items']}
        checks = self.previous['fixture_checks']
        self.assertEqual(len(checks), 14)
        for check in checks:
            expected = check['expectation']
            with self.subTest(identity=check['id']):
                if expected['outcome'] == 'parse-rejected':
                    self.assertEqual(actual[check['id']]['status'], 'expected-parse-rejection')
                    self.assertTrue((self.reader/check['id']/'parse-error.json').is_file())
                    continue
                result = self.saved_count(check['id'])
                if expected['outcome'] == 'candidate-count':
                    self.assertEqual(result['diagnostics'], [])
                    self.assertEqual(result['normalized_loc'], expected['canonical_units'])
                else:
                    self.assertEqual(expected['outcome'], 'needs-review')
                    self.assertIsNone(result['normalized_loc'])
                    self.assertIn(expected['diagnostic'], [d['kind'] for d in result['diagnostics']])


if __name__ == '__main__':
    unittest.main()
