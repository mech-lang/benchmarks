#!/usr/bin/env python3
"""Candidate canonical source units from the retained Elixir reader's tagged AST.

This module never invokes Elixir, evaluates source, or supplies chart admission.
It preserves physical nonblank/noncomment rows, expands independent statements
and matches, and replaces explicit executable headers/closers with owned units.
Parser positions must agree with the source. Unsupported or ambiguous ownership
produces diagnostics and a null normalized_loc, not an invented qualified count.
Synthetic AST tests are distinct from actual native-reader replay and review.
"""
import argparse
import base64
from bisect import bisect_right
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


RULE_VERSION = 'canonical-source-units-20261012-approved-rule-v2'
GRAMMAR = 'elixir-native-position-owners-v1'
FIXTURE_CONTRACT = Path(__file__).resolve().parents[2] / 'experiments/elixir/source-units-v1/fixture-contract.json'
EXPLICIT = {'defmodule', 'def', 'defp', 'defmacro', 'defmacrop', 'if', 'unless',
            'case', 'cond', 'for', 'with', 'try', 'receive'}
BRANCHES = {'do', 'else', 'rescue', 'catch', 'after'}
FALSE_FLAGS = dict(canonical_loc_qualified=False, formatted_loc_qualified=False,
                   chart_admission=False)


class CountError(ValueError):
    pass


class Atom(str):
    """An Erlang atom remains distinguishable from binary literal bytes."""


@dataclass(frozen=True)
class TermMap:
    pairs: tuple


def decode(value, depth=0):
    if depth > 512 or not isinstance(value, list) or len(value) != 2:
        raise CountError('Malformed or excessively deep tagged term')
    kind, raw = value
    if kind == 'atom' and isinstance(raw, str):
        return Atom(raw)
    if kind == 'binary' and isinstance(raw, str):
        try:
            return base64.b64decode(raw, validate=True)
        except ValueError as error:
            raise CountError('Malformed binary literal') from error
    if kind == 'integer' and isinstance(raw, str) and re.fullmatch(r'-?(0|[1-9][0-9]*)', raw):
        return int(raw)
    if kind == 'float' and isinstance(raw, str):
        # No numeric operation is needed; preserve the exact printed token.
        return ('__float_literal__', raw)
    if kind in ('tuple', 'list') and isinstance(raw, list):
        items = [decode(v, depth + 1) for v in raw]
        return tuple(items) if kind == 'tuple' else items
    if kind == 'map' and isinstance(raw, list):
        if not all(isinstance(pair, list) and len(pair) == 2 for pair in raw):
            raise CountError('Malformed tagged map')
        return TermMap(tuple((decode(k, depth + 1), decode(v, depth + 1)) for k, v in raw))
    raise CountError('Unknown or malformed tagged term: ' + str(kind))


def metadata(value):
    if not isinstance(value, list) or not all(isinstance(p, tuple) and len(p) == 2
                                             and isinstance(p[0], Atom) for p in value):
        raise CountError('AST metadata is not an atom-keyed keyword list')
    # Macro metadata is a keyword list, not a map: repeated :parens and
    # :end_of_expression entries are documented native parser output. Preserve
    # Keyword.get/2's first-value semantics. Conflicting ownership coordinates
    # cannot describe an unambiguous source span and remain a rejection.
    result = {}
    for key, item in value:
        if key in result and key in {'line', 'column', 'do', 'end', 'closing'} and result[key] != item:
            raise CountError('Conflicting native ownership metadata: ' + key)
        result.setdefault(key, item)
    return result


def node(value):
    if isinstance(value, tuple) and len(value) == 3 and isinstance(value[1], list):
        if isinstance(value[0], Atom) or isinstance(value[0], tuple):
            return value[0], metadata(value[1]), value[2]
    return None


def literal(value):
    part = node(value)
    if part and part[0] == '__block__' and isinstance(part[2], list) and len(part[2]) == 1:
        return part[2][0]
    return value


def key_name(value):
    value = literal(value)
    return str(value) if isinstance(value, Atom) else None


@dataclass
class Token:
    text: str
    start: int
    end: int
    context: tuple


class Source:
    def __init__(self, text):
        self.text = text
        self.starts = [0] + [m.end() for m in re.finditer('\n', text)]
        self.cleaned = list(text)
        self.tokens = []
        self.comments = []
        self.literals = []
        self.interpolations = []
        self.stack = []
        self.diagnostics = []
        self._code(0)
        if self.stack:
            self.issue('unclosed-data-delimiter', self.stack[-1][2])

    def issue(self, kind, offset, detail=None):
        result = dict(kind=kind, offset=max(0, offset))
        if detail:
            result['detail'] = detail
        self.diagnostics.append(result)

    def offset(self, location):
        values = metadata(location)
        line, column = values.get('line'), values.get('column')
        if type(line) is not int or type(column) is not int or not 1 <= line <= len(self.starts) or column < 1:
            raise CountError('Missing or invalid native line/column position')
        start = self.starts[line - 1]
        end = self.text.find('\n', start)
        end = len(self.text) if end == -1 else end
        offset = start + column - 1
        if offset > end:
            raise CountError('Native column is outside its source row')
        return offset

    def mask(self, start, end, replacement='S'):
        for i in range(start, end):
            if not self.text[i].isspace():
                self.cleaned[i] = replacement

    def emit(self, text, start, end):
        self.tokens.append(Token(text, start, end, tuple(self.stack)))

    def _literal(self, start, delimiter_start, opener, closer, interpolate, sigil=False):
        text, cursor, segment, depth = self.text, delimiter_start + len(opener), start, 1
        while cursor < len(text):
            if text[cursor] == '\\':
                cursor += 2
                continue
            if interpolate and text.startswith('#{', cursor):
                self.mask(segment, cursor + 2)
                inside = cursor + 2
                cursor = self._code(inside, interpolation=True)
                self.interpolations.append((inside, cursor - 1))
                self.mask(cursor - 1, cursor)
                segment = cursor
                continue
            if opener != closer and text.startswith(opener, cursor):
                depth += 1
                cursor += len(opener)
                continue
            if text.startswith(closer, cursor):
                depth -= 1
                cursor += len(closer)
                if depth == 0:
                    if sigil:
                        while cursor < len(text) and text[cursor].isalpha():
                            cursor += 1
                    self.mask(segment, cursor)
                    self.literals.append((start, cursor))
                    return cursor
                continue
            cursor += 1
        self.issue('unterminated-literal', start)
        self.mask(segment, len(text))
        return len(text)

    def _code(self, cursor, interpolation=False):
        text, base = self.text, len(self.stack)
        while cursor < len(text):
            char = text[cursor]
            if interpolation and char == '}' and len(self.stack) == base:
                return cursor + 1
            if char.isspace():
                cursor += 1
                continue
            if char == '#':
                end = text.find('\n', cursor)
                end = len(text) if end == -1 else end
                # CR belongs to the line ending, not the comment's text.
                if end > cursor and text[end - 1] == '\r':
                    end -= 1
                self.comments.append((cursor, end))
                self.mask(cursor, end, ' ')
                cursor = end
                continue
            if char in '\"\'' or (char == ':' and cursor + 1 < len(text) and text[cursor + 1] in '\"\''):
                at = cursor + (char == ':')
                quote = text[at]
                delimiter = quote * 3 if text.startswith(quote * 3, at) else quote
                cursor = self._literal(cursor, at, delimiter, delimiter, True)
                continue
            sigil = re.match(r'~([A-Za-z])([/|\"\'\[({<])', text[cursor:])
            if sigil:
                at, opener = cursor + 2, sigil[2]
                if opener in '\"\'' and text.startswith(opener * 3, at):
                    opener *= 3
                closer = {'[': ']', '(': ')', '{': '}', '<': '>'}.get(opener, opener)
                cursor = self._literal(cursor, at, opener, closer, sigil[1].islower(), True)
                continue
            if char == '?':
                end = cursor + 2
                if end <= len(text) and text[cursor + 1:cursor + 2] == '\\':
                    end += 1
                    if text[cursor + 2:cursor + 3] in ('x', 'u'):
                        self.issue('unsupported-character-escape', cursor)
                if end > len(text):
                    self.issue('truncated-character-literal', cursor)
                    end = len(text)
                self.mask(cursor, end); self.literals.append((cursor, end)); cursor = end
                continue
            atom = re.match(r':(?:[^\W\d]\w*[!?]?)', text[cursor:], re.UNICODE)
            if atom:
                end = cursor + len(atom[0]); self.mask(cursor, end)
                self.literals.append((cursor, end)); cursor = end
                continue
            word = re.match(r'(?:[^\W\d]\w*[!?]?|[0-9][A-Za-z_0-9.]*)', text[cursor:], re.UNICODE)
            if word:
                end = cursor + len(word[0]); self.emit(word[0], cursor, end); cursor = end
                continue
            symbol = next((v for v in ('<<<', '>>>', '===', '!==', '<<', '>>', '->', '<-', '::',
                                       '|>', '==', '!=', '<=', '>=', '=~', '=>', '&&', '||', '\\\\')
                           if text.startswith(v, cursor)), char)
            end = cursor + len(symbol)
            self.emit(symbol, cursor, end)
            if symbol in ('(', '[', '{', '<<'):
                self.stack.append((symbol, 'args' if symbol == '(' else 'data', cursor))
            elif symbol in (')', ']', '}', '>>'):
                wanted = {')': '(', ']': '[', '}': '{', '>>': '<<'}[symbol]
                if not self.stack or self.stack[-1][0] != wanted:
                    self.issue('unbalanced-data-delimiter', cursor)
                else:
                    self.stack.pop()
            elif symbol == '~':
                self.issue('unsupported-sigil-form', cursor)
            elif symbol == '\ufeff':
                self.issue('unsupported-source-marker', cursor)
            cursor = end
        if interpolation:
            self.issue('unterminated-interpolation', cursor)
        return cursor


class Owners:
    def __init__(self, source, ast, comments):
        self.source, self.ast = source, ast
        self.events, self.regions, self.assignments, self.boundaries = [], [], [], set()
        self.continuations, self.sequence_starts = [], set()
        self.positions = set()
        self.diagnostics = list(source.diagnostics)
        self._collect_positions(ast)
        self._comments(comments)
        for start, _end in source.literals:
            if start not in self.positions:
                self.issue('literal-not-bound-to-native-position', start)
        self.walk(ast)
        self._finish()

    def issue(self, kind, offset=0, detail=None):
        item = dict(kind=kind, offset=max(offset, 0))
        if detail:
            item['detail'] = detail
        self.diagnostics.append(item)

    def _position(self, part):
        meta = part[1]
        if 'line' not in meta and 'column' not in meta:
            return None
        return self.source.offset(list(meta.items()))

    def _collect_positions(self, term):
        part = node(term)
        if part:
            position = self._position(part)
            if position is not None:
                self.positions.add(position)
            self._collect_positions(part[0])
            self._collect_positions(part[2])
        elif isinstance(term, (list, tuple)):
            for child in term:
                self._collect_positions(child)

    def start(self, term):
        positions = []
        def visit(value):
            part = node(value)
            if part:
                at = self._position(part)
                if at is not None:
                    positions.append(at)
                visit(part[0]); visit(part[2])
            elif isinstance(value, (list, tuple)):
                for child in value:
                    visit(child)
        visit(term)
        return min(positions) if positions else None

    def _comments(self, comments):
        if not isinstance(comments, list):
            raise CountError('Native comments must be a list')
        actual = []
        for term in comments:
            if not isinstance(term, TermMap):
                raise CountError('Native comment must be a tagged map')
            row = dict(term.pairs)
            start = self.source.offset([(Atom('line'), row.get(Atom('line'))),
                                        (Atom('column'), row.get(Atom('column')))])
            text = row.get(Atom('text'))
            if not isinstance(text, bytes):
                raise CountError('Native comment lacks binary text')
            text = text.decode('utf-8')
            if not text.startswith('#') or self.source.text[start:start + len(text)] != text:
                self.issue('native-comment-source-mismatch', start)
            actual.append((start, start + len(text)))
        if sorted(actual) != sorted(self.source.comments):
            self.issue('native-comment-coverage-mismatch')

    def event(self, kind, start, end, units=1, owner=None):
        if start is None or not 0 <= start < end <= len(self.source.text):
            raise CountError('Owner span outside native source positions')
        self.events.append(dict(kind=kind, start=start, end=end, units=units, owner=owner))

    def require_token(self, at, word):
        if at is None or self.source.text[at:at + len(word)] != word:
            raise CountError('Native ' + word + ' position does not match source')
        if not any(t.start == at and t.text == word for t in self.source.tokens):
            raise CountError('Native executable token falls in a literal/comment')

    def keyword_pairs(self, arguments):
        if not isinstance(arguments, list) or not arguments:
            return None
        final = literal(arguments[-1])
        if not isinstance(final, list) or not final:
            return None
        if all(isinstance(p, tuple) and len(p) == 2 and key_name(p[0]) in BRANCHES for p in final):
            return final
        return None

    def body(self, value, limit):
        # Stab clause lists occur in case/cond/receive and are executable, not
        # ordinary list data. Each written pattern/guard and arrow owns a header.
        clauses = literal(value)
        if isinstance(clauses, list) and clauses and all(node(c) and node(c)[0] == '->' for c in clauses):
            for index, clause in enumerate(clauses):
                stop = self.start(clauses[index + 1]) if index + 1 < len(clauses) else limit
                self.arrow(clause, None, stop)
        else:
            self.walk(value, limit=limit)

    def arrow(self, value, header_start, limit):
        name, meta, arguments = node(value)
        if name != '->' or not isinstance(arguments, list) or len(arguments) != 2:
            raise CountError('Malformed native arrow clause')
        at = self.source.offset(list(meta.items())); self.require_token(at, '->')
        start = header_start if header_start is not None else self.start(arguments[0])
        if start is None:
            # Zero-arity fn clauses have an empty pattern list.
            start = at
        self.event('header', start, at + 2, owner='arrow-clause')
        if limit is not None:
            self.regions.append((at + 2, limit))
        self.walk(arguments[1], limit=limit)

    def walk(self, term, statement_start=None, limit=None):
        if limit is None:
            limit = len(self.source.text)
        part = node(term)
        if not part:
            if isinstance(term, (list, tuple)):
                for child in term:
                    self.walk(child, statement_start, limit)
            return
        name, meta, arguments = part
        here = self.start(term)
        first = here if statement_start is None else statement_start
        if name == '__block__' and isinstance(arguments, list) and len(arguments) > 1:
            for index, child in enumerate(arguments):
                at = self.start(child)
                if at is None:
                    raise CountError('Native independent expression lacks a source position')
                self.sequence_starts.add(at)
                if index:
                    self.boundaries.add(at)
                stop = self.start(arguments[index + 1]) if index + 1 < len(arguments) else limit
                self.walk(child, at, stop)
            return
        if name == '=':
            at = self.source.offset(list(meta.items())); self.require_token(at, '=')
            self.assignments.append(at)
        if name == 'fn':
            self.require_token(self._position(part), 'fn')
            closer = meta.get('closing', meta.get('end'))
            if closer is None:
                raise CountError('Anonymous function lacks native closing position')
            end = self.source.offset(closer); self.require_token(end, 'end')
            if not isinstance(arguments, list) or not arguments:
                raise CountError('Anonymous function lacks clauses')
            for index, clause in enumerate(arguments):
                stop = self.start(arguments[index + 1]) if index + 1 < len(arguments) else end
                self.arrow(clause, first if index == 0 else None, stop)
            self.event('close', end, end + 3, owner='fn')
            # Ordinary AST descent preserves the enclosing independent
            # expression's [first, limit) span. Only native sequence siblings
            # and executable bodies establish a new span. This is stronger
            # evidence than a textual `end)` suffix: a following pipeline or
            # data/call value can belong to this very same expression.
            if end + 3 < limit:
                self.continuations.append(dict(start=end + 3, end=limit,
                                               expression_start=first, close=end))
                self.boundaries.add(limit)
            return
        if 'do' in meta or 'end' in meta:
            if name not in EXPLICIT:
                self.issue('unsupported-explicit-macro-owner', here or 0, str(name))
            if 'do' not in meta or 'end' not in meta:
                raise CountError('Explicit block lacks paired native do/end metadata')
            opening, end = self.source.offset(meta['do']), self.source.offset(meta['end'])
            self.require_token(opening, 'do'); self.require_token(end, 'end')
            self.event('header', first, opening + 2, owner=str(name))
            self.event('close', end, end + 3, owner=str(name))
            self.regions.append((opening + 2, end))
            pairs = self.keyword_pairs(arguments)
            if not pairs or key_name(pairs[0][0]) != 'do':
                raise CountError('Explicit block lacks native do-keyword body')
            for argument in arguments[:-1]:
                self.walk(argument, first, opening)
            for index, (key, value) in enumerate(pairs):
                branch = key_name(key)
                if branch != 'do':
                    branch_start = self.start(key)
                    self.require_token(branch_start, branch)
                    self.event('branch', branch_start, branch_start + len(branch), owner=str(name))
                stop = self.start(pairs[index + 1][0]) if index + 1 < len(pairs) else end
                self.body(value, stop)
            return
        if name == '->':
            self.issue('arrow-without-executable-owner', here or 0)
            return
        if name in ('def', 'defp', 'defmacro', 'defmacrop'):
            pairs = self.keyword_pairs(arguments)
            if not pairs or key_name(pairs[0][0]) != 'do':
                raise CountError('Expression-only definition lacks native do-keyword body')
            # Parameter matches belong to the named function's signature, not
            # to independent assignments in its expression body. The written
            # expression-only definition still gains no header/closer units.
            # An executable callback hidden in the signature remains unowned
            # and is rejected by the lexical ownership coverage check.
            for _key, value in pairs:
                self.walk(value, first, limit)
            return
        # Colon keyword functions/conditionals remain ordinary expressions.
        # Their written callbacks, if any, still supply real fn/end owners.
        self.walk(name, first, limit)
        if isinstance(arguments, list):
            for child in arguments:
                self.walk(child, first, limit)

    def _finish(self):
        cleaned = ''.join(self.source.cleaned)
        self.events.sort(key=lambda e: (e['start'], e['end']))
        for event in list(self.events):
            if event['kind'] != 'close':
                continue
            end = event['end']
            for token in self.source.tokens:
                if token.start < end:
                    continue
                if cleaned[end:token.start].strip():
                    break
                if token.text in (')', ']') and token.context:
                    opening, kind, _at = token.context[-1]
                    if opening == {')': '(', ']': '['}[token.text] and kind in ('args', 'data'):
                        end = token.end
                        continue
                if token.text == ',' and token.context:
                    end = token.end
                break
            if end > event['end']:
                self.event('structural-suffix', event['end'], end, 0, 'argument-or-data-suffix')
        self.events.sort(key=lambda e: (e['start'], e['end']))
        for left, right in zip(self.events, self.events[1:]):
            if left['end'] > right['start']:
                self.issue('overlapping-native-owner-spans', right['start'])
        for token in self.source.tokens:
            if token.text in {'do', 'end', 'fn', '->', 'else', 'rescue', 'catch', 'after'}:
                if self.source.text[token.end:token.end + 1] == ':':
                    continue
                if not any(e['start'] <= token.start < e['end'] for e in self.events):
                    self.issue('unowned-executable-token', token.start, token.text)
        for start, end in self.source.interpolations:
            if any(start <= at < end for at in self.assignments) or any(
                    t.text == ';' and start <= t.start < end for t in self.source.tokens):
                self.issue('interpolation-with-independent-work-needs-review', start)
        for tail in self.continuations:
            start, end = tail['start'], tail['end']
            if (any(start <= at < end for at in self.assignments) or
                    any(start <= at < end for at in self.sequence_starts) or
                    any(start <= e['start'] < end and e['units'] for e in self.events)):
                self.issue('non-scalar-expression-continuation-needs-review', start)


def account(source, owners):
    cleaned = ''.join(source.cleaned)
    body = list(cleaned)
    starts, by_line, owned_lines = source.starts, {}, set()
    line_of = lambda at: bisect_right(starts, at)
    for event in owners.events:
        for at in range(event['start'], event['end']):
            if not body[at].isspace():
                body[at] = ' '
        line = line_of(event['start'])
        by_line.setdefault(line, []).append(event)
        owned_lines.update(range(line, line_of(event['end'] - 1) + 1))
    body = ''.join(body)
    physical = [i for i, row in enumerate(cleaned.splitlines(keepends=True), 1) if row.strip()]
    body_rows, source_rows = body.splitlines(keepends=True), source.text.splitlines()
    boundaries = owners.boundaries | {at for e in owners.events for at in (e['start'], e['end'])}
    tokens = {t.start: t for t in source.tokens}
    def structural(at, assignment=False):
        region = max((start for start, end in owners.regions if start <= at < end), default=-1)
        token = tokens.get(at)
        context = token.context if token else ()
        return any(opened >= region and (kind == 'data' or not assignment)
                   for _symbol, kind, opened in context)
    expansions, total = [], 0
    for line in physical:
        offset, row = starts[line - 1], body_rows[line - 1]
        separators = [t.end - offset for t in source.tokens if t.text == ';'
                      and offset <= t.start < offset + len(row) and not structural(t.start)]
        bounds = sorted({0, len(row), *separators,
                         *(at - offset for at in boundaries if offset < at < offset + len(row))})
        residual = []
        for left, right in zip(bounds, bounds[1:]):
            text = row[left:right].rstrip().removesuffix(';').rstrip()
            if not text.strip('{}; \t\r\n'):
                continue
            assignments = [at for at in owners.assignments if offset + left <= at < offset + left + len(text)
                           and body[at] == '=']
            for at in assignments:
                if structural(at, assignment=True):
                    owners.issue('assignment-in-data-needs-review', at)
            begin = offset + left + len(text) - len(text.lstrip())
            finish = offset + left + len(text)
            same_expression_tail = next((tail for tail in owners.continuations
                if tail['start'] <= begin < finish <= tail['end'] and
                line_of(tail['close']) == line), None)
            units = 0 if same_expression_tail and not assignments else max(1, len(assignments))
            residual.append(dict(start=offset + left, end=offset + right, units=units,
                                 assignments=assignments,
                                 reason='same-native-expression-scalar-continuation' if units == 0
                                 else 'independent-statement-or-preserved-physical-row'))
        events = by_line.get(line, [])
        units = sum(e['units'] for e in events) + sum(e['units'] for e in residual)
        if not units and line not in owned_lines:
            units = 1
        total += units
        if units != 1 or events or any(e['units'] > 1 for e in residual):
            expansions.append(dict(line=line, original=source_rows[line - 1], units=units,
                                   extra_lines=units - 1, canonical_events=events, statements=residual))
    return len(physical), total, expansions


def count_source(text, payload):
    diagnostics, source, owners = [], None, None
    try:
        if not isinstance(text, str) or not isinstance(payload, dict) or set(payload) != {'ast', 'comments'}:
            raise CountError('Expected exact source text and native ast/comments envelope')
        source = Source(text)
        owners = Owners(source, decode(payload['ast']), decode(payload['comments']))
        physical, candidate, expansions = account(source, owners)
        diagnostics = owners.diagnostics
    except (CountError, UnicodeError, TypeError, KeyError, IndexError, RecursionError) as error:
        diagnostics.append(dict(kind='native-owner-input-rejected', offset=0, detail=str(error)))
        if source is not None:
            diagnostics = source.diagnostics + diagnostics
            physical = sum(bool(row.strip()) for row in ''.join(source.cleaned).splitlines())
        else:
            physical = None
        candidate, expansions = None, []
    starts = source.starts if source is not None else [0]
    for issue in diagnostics:
        at = issue.get('offset', 0)
        line = bisect_right(starts, at)
        issue.update(line=line, column=at - starts[line - 1] + 1)
    return dict(rule_version=RULE_VERSION, grammar=GRAMMAR, language='elixir',
                physical_loc=physical, normalized_loc=None if diagnostics else candidate,
                candidate_normalized_loc=candidate, expansions=expansions,
                canonical_events=owners.events if owners else [], diagnostics=diagnostics,
                expression_continuations=owners.continuations if owners else [],
                review_status='needs-review' if diagnostics else 'candidate-native-owner-pass',
                evidence='Caller-supplied tagged AST; actual reader/replay and semantic review are separate',
                **FALSE_FLAGS)


def read_json(path):
    return json.loads(Path(path).read_text())


def replay(plan_path, reader_directory, fixture_contract=FIXTURE_CONTRACT):
    plan, directory = read_json(plan_path), Path(reader_directory)
    report = read_json(directory / 'report.json')
    if plan['schema'] != 'elixir-source-reader-plan-v1' or report['schema'] != 'elixir-native-source-reader-v1':
        raise CountError('Wrong native reader plan/results schema')
    if (report['status'] != 'read-awaiting-canonical-owner-review' or
            any(report[k] != 0 for k in ('source_evaluations', 'subject_recompilations', 'subject_main_invocations'))):
        raise CountError('Reader execution does not satisfy source-only contract')
    inputs = {item['id']: item for item in plan['inputs']}
    if (len(inputs) != len(plan['inputs']) or len(report['items']) != len(inputs) or
            {item['id'] for item in report['items']} != set(inputs)):
        raise CountError('Reader input inventory differs')
    if any(item['expected_parse'] not in ('ok', 'error') or item['kind'] not in ('application', 'fixture')
           for item in inputs.values()):
        raise CountError('Unexpected source-reader input role or parse contract')
    results = {}
    for item in report['items']:
        identity = item['id']
        if re.fullmatch(r'[a-z0-9-]+', identity) is None:
            raise CountError('Unsafe source artifact identifier')
        folder, expected = directory / identity, inputs[identity]
        source_bytes = (folder / 'source.exs').read_bytes()
        digest = hashlib.sha256(source_bytes).hexdigest()
        if digest != expected['sha256'] or digest != item['source_sha256']:
            raise CountError('Native source identity differs: ' + identity)
        if expected['expected_parse'] == 'error':
            if item['status'] != 'expected-parse-rejection' or not (folder / 'parse-error.json').is_file():
                raise CountError('Missing expected native rejection')
            results[identity] = dict(status='native-parser-rejected-as-expected', normalized_loc=None, **FALSE_FLAGS)
            continue
        if item['status'] != 'parsed-and-formatted' or item['semantic_ast_preserved'] is not True:
            raise CountError('Native parser/formatter did not complete')
        formatted = (folder / 'formatted.exs').read_bytes()
        if hashlib.sha256(formatted).hexdigest() != item['formatted_sha256']:
            raise CountError('Formatted source identity differs')
        original_count = count_source(source_bytes.decode('utf-8'), read_json(folder / 'ast.json'))
        formatted_count = count_source(formatted.decode('utf-8'), read_json(folder / 'formatted-ast.json'))
        results[identity] = dict(source_sha256=digest, original=original_count, formatted=formatted_count,
                                 candidate_formatted_loc=formatted_count['physical_loc'], **FALSE_FLAGS)
    contract = read_json(fixture_contract)
    if contract['schema'] != 'elixir-source-unit-fixture-contract-v1' or contract['rule_version'] != RULE_VERSION:
        raise CountError('Wrong source-unit fixture contract')
    expectations = {row['id']: row for row in contract['fixtures']}
    fixture_ids = {key for key, item in inputs.items() if item['kind'] == 'fixture'}
    if len(expectations) != len(contract['fixtures']) or set(expectations) != fixture_ids:
        raise CountError('Native fixture inventory differs from reviewed fixture contract')
    checks = []
    for identity, expected in expectations.items():
        result = results[identity]
        if expected['outcome'] == 'parse-rejected':
            passed = result.get('status') == 'native-parser-rejected-as-expected'
        elif expected['outcome'] == 'needs-review':
            counted = result.get('original', {})
            passed = (counted.get('normalized_loc') is None and
                      any(d['kind'] == expected['diagnostic'] for d in counted.get('diagnostics', [])))
        elif expected['outcome'] == 'candidate-count':
            counted = result.get('original', {})
            passed = counted.get('normalized_loc') == expected['canonical_units'] and not counted.get('diagnostics')
        else:
            raise CountError('Unknown fixture expectation')
        checks.append(dict(id=identity, passed=passed, expectation=expected))
    bundles, seen = [], set()
    for bundle in plan['profiles']:
        if bundle['id'] in seen or len(bundle['inputs']) != len(set(bundle['inputs'])):
            raise CountError('Duplicate profile or repeated source input within profile')
        seen.add(bundle['id'])
        if any(inputs[key]['kind'] != 'application' for key in bundle['inputs']):
            raise CountError('A source profile includes a non-application input')
        files = [results[key] for key in bundle['inputs']]
        counts = [f.get('original', {}).get('normalized_loc') for f in files]
        bundle_count = sum(counts) if all(type(n) is int for n in counts) else None
        bundles.append(dict(id=bundle['id'], inputs=bundle['inputs'], candidate_canonical_loc=bundle_count,
                            canonical_loc=None, formatted_loc=None, **FALSE_FLAGS))
    clean = all(check['passed'] for check in checks) and all(b['candidate_canonical_loc'] is not None for b in bundles)
    return dict(schema='elixir-source-unit-replay-v1',
                status='candidate-replay-awaiting-owner-review' if clean else 'candidate-replay-needs-review',
                rule_version=RULE_VERSION, grammar=GRAMMAR, reader_directory=str(directory.resolve()),
                plan=str(Path(plan_path).resolve()), files=results, profiles=bundles,
                fixture_contract=str(Path(fixture_contract).resolve()), fixture_checks=checks,
                native_fixture_expectations_passed=all(check['passed'] for check in checks),
                native_reader_metadata_consumed=True, native_reader_terminal_verified=False,
                source_evaluations=0, subject_recompilations=0, **FALSE_FLAGS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    single = commands.add_parser('count', help='Count one exact source/tagged-AST pair as an unqualified candidate')
    single.add_argument('--source', type=Path, required=True)
    single.add_argument('--ast', type=Path, required=True)
    collection = commands.add_parser('replay', help='Consume the completed native source-reader tree')
    collection.add_argument('--plan', type=Path, required=True)
    collection.add_argument('--reader-directory', type=Path, required=True)
    collection.add_argument('--fixture-contract', type=Path, default=FIXTURE_CONTRACT)
    for command in (single, collection):
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = (count_source(args.source.read_bytes().decode('utf-8'), read_json(args.ast))
              if args.action == 'count' else replay(args.plan, args.reader_directory, args.fixture_contract))
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(args.output), status=result.get('status', result.get('review_status')), **FALSE_FLAGS)))


if __name__ == '__main__':
    main()
