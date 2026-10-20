#!/usr/bin/env python3
"""Separate native-reader-bound Clojure source-owner prototype; never evaluate input.

prepare is source-only. capture launches the pinned read-only helper and must be
scheduled outside benchmark windows. replay never launches a language runtime.
No command changes canonical data, existing v2 reports, or chart coordinates.
"""
import argparse
import collections
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKET = Path('experiments/source-normalization/clojure-v1')
POLICY = 'logical-source-owners.clojure-v1'
SUPPLEMENTAL = [('experiments/clojure/optimization-v1/primitive-v1/sources/clbg/nbody/primitive_updates.clj',
                 '12d61dd8a07254f6ba94652fb30b63cc305ec0145e482f1136044a1dc8c88fe2')]
READER_SHA = '036dc155f3b62548df3da934791aa9d8ec36572a9c664ce2cc7f6551856436be'
JAVA_SHA = '83c9c5310d044e7c4262432854eb1bc5f49763d7c1e9971777a646c91b96c06d'
JAR_PINS = {'clojure-1.12.6.jar': '21b578db389a8e74b286ce79c4a7f86ec641e26d88b12f18d69030916b0e18ca',
    'spec.alpha-0.5.238.jar': '94cd99b6ea639641f37af4860a643b6ed399ee5a8be5d717cff0b663c8d75077',
    'core.specs.alpha-0.4.74.jar': 'eb73ac08cf49ba840c88ba67beef11336ca554333d9408808d78946e0feb9ddb',
    'tools.reader-1.6.0.jar': READER_SHA}


class QualificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise QualificationError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def lex(text):
    """Lossless restricted source segmentation, NOT a native Clojure lexer.

    Every byte is preserved. Native acceptance/events are required separately;
    this scanner alone never qualifies source or supplies a lexical-token metric.
    """
    tokens, i, offsets = [], 0, [0]
    for character in text:
        offsets.append(offsets[-1] + len(character.encode('utf-8')))
    delimiters = set('()[]{}";@^`~\\')
    def emit(kind, a, b, trivia=False):
        tokens.append(dict(kind=kind, start=offsets[a], end=offsets[b],
                           text=text[a:b], trivia=trivia))
    while i < len(text):
        start, ch = i, text[i]
        if ch.isspace() or ch == ',':
            require(ch in ' \t\r\n\v\f,', 'Non-ASCII syntax whitespace needs a native lexer qualification')
            i += 1
            while i < len(text) and (text[i].isspace() or text[i] == ','):
                require(text[i] in ' \t\r\n\v\f,', 'Non-ASCII syntax whitespace needs a native lexer qualification')
                i += 1
            emit('whitespace', start, i, True)
        elif ch == ';':
            while i < len(text) and text[i] not in '\r\n':
                i += 1
            emit('comment', start, i, True)
        elif ch in '()[]{}':
            i += 1; emit(ch, start, i)
        elif ch == '"' or text.startswith('#"', i):
            kind = 'regex' if ch == '#' else 'string'
            i += 2 if ch == '#' else 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1; break
                else:
                    i += 1
            else:
                raise QualificationError('Unterminated restricted reader string')
            require(i <= len(text), 'Unterminated string escape')
            emit(kind, start, i)
        elif ch == '\\':
            i += 1
            require(i < len(text), 'Incomplete character literal')
            # A delimiter itself can be the literal character: \\), \\; etc.
            i += 1
            while i < len(text) and not text[i].isspace() and text[i] != ',' and text[i] not in delimiters:
                i += 1
            emit('character', start, i)
        elif ch in "'@^":
            i += 1; emit(ch, start, i)
        elif ch in '`~':
            raise QualificationError('Syntax quote/unquote is outside the qualified reader subset')
        elif ch == '#':
            pair = text[i:i + 2]
            require(pair in ("#'", '#(', '#{'),
                    'Unsupported reader dispatch (including read-eval/custom tags): ' + pair)
            i += 2; emit(pair, start, i)
        else:
            i += 1
            while i < len(text) and not text[i].isspace() and text[i] != ',' and text[i] not in delimiters:
                i += 1
            spelling = text[start:i]
            require(not spelling.startswith('::'), 'Auto-resolved keywords require a separately qualified namespace resolver')
            emit('atom', start, i)
    require(b''.join(item['text'].encode() for item in tokens) == text.encode(), 'Non-lossless segmentation')
    return tokens


def source_tree(text):
    tokens = lex(text)
    significant = [item for item in tokens if not item['trivia']]
    position, nodes = 0, []
    pairs = {'(': (')', 'list'), '[': (']', 'vector'), '{': ('}', 'map'),
             '#(': (')', 'anonymous-fn'), '#{': ('}', 'set')}
    prefixes = {"'": ('quote', 1), "#'": ('var-quote', 1), '@': ('deref', 1), '^': ('metadata', 2)}
    def read(parent=None):
        nonlocal position
        require(position < len(significant), 'Incomplete reader form')
        token = significant[position]; position += 1
        require(token['kind'] not in (')', ']', '}'), 'Unmatched closing delimiter')
        node = dict(id=len(nodes) + 1, parent=parent, kind=token['kind'], start=token['start'],
                    end=token['end'], children=[])
        nodes.append(node)
        if token['kind'] in pairs:
            closing, node['kind'] = pairs[token['kind']]
            while position < len(significant) and significant[position]['kind'] != closing:
                node['children'].append(read(node['id']))
            require(position < len(significant), 'Unclosed reader collection')
            node['end'] = significant[position]['end']; position += 1
        elif token['kind'] in prefixes:
            node['kind'], count = prefixes[token['kind']]
            node['children'] = [read(node['id']) for _ in range(count)]
            node['end'] = nodes[node['children'][-1] - 1]['end']
        return node['id']
    roots = []
    while position < len(significant):
        roots.append(read())
    return dict(tokens=tokens, nodes=nodes, roots=roots)


CORE_FUNCTIONS = frozenset('''* + - / < <= = > >= aclone aget alength aset aset-byte aset-char aset-double
 aset-int aset-long assoc! bit-and bit-or bit-shift-left byte-array char char-array conj count dec double
 double-array drop empty? even? first flush get inc int int-array long long-array map mapv max min mod
 next nil? nth object-array peek persistent! pos? print println quot range reduce reductions rem rest
 second seq sort-by str take to-array transient unchecked-byte unsigned-bit-shift-right vals vec zero? zipmap
 comp partial identity constantly apply juxt'''.split())
EXTERNAL_FUNCTIONS = frozenset(('s/argument', 's/input-text', 's/jobs', 's/printf', 'string/split'))
JAVA_CALLS = frozenset(('BigInteger/valueOf', 'BufferedOutputStream.', 'Executors/newFixedThreadPool',
    'HashMap.', 'IllegalArgumentException.', 'IllegalStateException.', 'Long/parseLong', 'Math/sqrt',
    'Pattern/compile', 'String.', 'String/format', 'StringBuilder.'))
JAVA_METHODS = frozenset('''.add .append .awaitTermination .charAt .divide .entrySet .equals .find .flush
 .get .getBytes .getKey .getOrDefault .getValue .intValue .length .matcher .multiply .put .readAllBytes
 .replaceAll .setLength .shutdown .startsWith .submit .substring .subtract .toString .toUpperCase .write'''.split())
CONTROL = frozenset(('let', 'loop', 'if', 'if-let', 'when', 'when-not', 'doseq', 'dotimes', 'for',
                     'cond', 'case', 'try', 'reify', 'do'))
EXPRESSION_MACROS = frozenset(('and', 'or', 'assert'))
SUPPORTED_MACROS = CONTROL | EXPRESSION_MACROS | {'ns', 'defn', 'fn'}
RESERVED = SUPPORTED_MACROS | {'def', 'defmacro', 'catch', 'finally', 'quote', 'var', 'recur', 'throw'}


def owners(text, tree, native):
    """Apply explicit source owners only after the exact native capture is bound."""
    raw = text.encode(); nodes = {node['id']: node for node in tree['nodes']}
    require(native.get('accepted') is True and native.get('source_sha256') == sha(raw), 'Missing exact native acceptance')
    require(native.get('read_eval') is False and native.get('source_evaluated') is False
            and native.get('macroexpanded') is False and native.get('custom_data_readers') is False,
            'Unsafe/unknown native reader mode')
    events = native['events']
    event_by_id = {event['id']: event for event in events}
    require(len(event_by_id) == len(events), 'Duplicate native reader event ID')
    for event in events:
        parent = event.get('parent')
        require(parent is None or parent in event_by_id and parent < event['id'], 'Broken native reader parent edge')
        if parent is not None:
            outer = event_by_id[parent]
            require(outer['start_utf16'] <= event['start_utf16'] <= event['end_utf16'] <= outer['end_utf16'],
                    'Native reader child span outside parent')
    # Native event positions are UTF-16 indices; source byte offsets are UTF-8.
    utf16_bytes, u16, byte_position = {0: 0}, 0, 0
    for character in text:
        u16 += len(character.encode('utf-16-le')) // 2
        byte_position += len(character.encode())
        utf16_bytes[u16] = byte_position
    event_spans = collections.defaultdict(list)
    source_spans = {(node['start'], node['end']) for node in nodes.values()}
    anonymous_inner_spans = {(node['start'] + 1, node['end']) for node in nodes.values() if node['kind'] == 'anonymous-fn'}
    # The pinned native read-arg implementation delegates the digits in %1/%2
    # to read*. They are reader-internal pieces of one written argument token.
    argument_index_spans = {(token['start'] + 1, token['end']) for token in tree['tokens']
        if re.fullmatch(r'%[1-9][0-9]*', token['text'])
        and any(node['kind'] == 'anonymous-fn' and node['start'] < token['start'] < token['end'] < node['end'] for node in nodes.values())}
    internal_spans = anonymous_inner_spans | argument_index_spans
    source_spans |= internal_spans
    for event in events:
        require(event['start_utf16'] in utf16_bytes and event['end_utf16'] in utf16_bytes,
                'Native reader position is outside complete UTF-16 boundaries')
        a, b = utf16_bytes[event['start_utf16']], utf16_bytes[event['end_utf16']]
        require(0 <= a <= b <= len(raw), 'Native reader event outside source')
        # read* starts before leading trivia, including comments and commas.
        ts = [t for t in tree['tokens'] if a <= t['start'] and t['end'] <= b and not t['trivia']]
        if event.get('kind') not in ('eof', 'delimiter'):
            normalized = (a, b) if (a, b) in internal_spans else (ts[0]['start'], b) if ts else None
            require(normalized in source_spans, 'Native reader form lacks a matching source-form span')
            require(normalized not in argument_index_spans or event['kind'] == 'number', 'Unexpected native reader argument-index kind')
            event_spans[normalized].append(event['id'])
    for node in nodes.values():
        require((node['start'], node['end']) in event_spans,
                'Restricted source form lacks exact native reader span: ' + repr(raw[node['start']:node['end']][:80]))
        node['native_events'] = event_spans[(node['start'], node['end'])]
    out = []
    def cs(node):
        return [nodes[i] for i in node['children']]
    def transparent(node):
        while node['kind'] == 'metadata':
            require(cs(node)[0]['kind'] == 'atom', 'Only written scalar type/flag metadata is qualified')
            flag = raw[cs(node)[0]['start']:cs(node)[0]['end']].decode()
            require(not flag.startswith(':') or flag in (':private', ':const', ':dynamic'), 'Unqualified metadata flag: ' + flag)
            node = cs(node)[1]
        return node
    def spelling(node):
        node = transparent(node)
        return raw[node['start']:node['end']].decode()
    def head(node):
        values = cs(transparent(node))
        return spelling(values[0]) if values else None
    def add(node, kind, units=1, span=None):
        a, b = span or (node['start'], node['end'])
        out.append(dict(id=len(out) + 1, source_node=node['id'], kind=kind, units=units,
                        start=a, end=b, source_sha256=sha(raw[a:b]), native_events=node['native_events']))
    globals_, aliases = set(), {}
    for ident in tree['roots']:
        node = transparent(nodes[ident]); values = cs(node)
        if node['kind'] == 'list' and head(node) == 'ns':
            for clause in values[2:]:
                require(clause['kind'] == 'list', 'Unknown namespace clause')
                fields = cs(clause); directive = head(clause)
                require(directive in (':require', ':import', ':gen-class', ':refer-clojure'), 'Unqualified namespace directive')
                if directive == ':require':
                    for library in fields[1:]:
                        parts = cs(library)
                        require(library['kind'] == 'vector' and len(parts) == 3 and spelling(parts[1]) == ':as', 'Unknown require/alias form')
                        lib, alias = spelling(parts[0]), spelling(parts[2])
                        require((lib, alias) in (('clbg.support', 's'), ('clojure.string', 'string')), 'Unqualified required namespace/alias')
                        aliases[alias] = lib
                elif directive == ':gen-class':
                    require(len(fields) == 1, 'Custom gen-class declarations are not qualified')
                elif directive == ':refer-clojure':
                    require(len(fields) == 3 and spelling(fields[1]) == ':exclude'
                            and spelling(fields[2]) == '[printf]', 'Unknown core namespace remapping')
        if node['kind'] == 'list' and head(node) in ('def', 'defn') and len(values) > 1:
            name = spelling(values[1]); require(name not in RESERVED, 'Reserved syntax is shadowed by local definition')
            globals_.add(name)
    native_macros = set(native['core_macro_names'])
    require(SUPPORTED_MACROS - {'do', 'if', 'try', 'reify'} <= native_macros,
            'Pinned core macro metadata differs from the policy assumptions')
    require(CORE_FUNCTIONS <= set(native['core_function_names']), 'Pinned core function metadata differs from the policy assumptions')

    def binding_names(node):
        node = transparent(node); values = cs(node)
        if node['kind'] == 'atom':
            name = spelling(node)
            require(any(event_by_id[i]['kind'] == 'symbol' for i in node['native_events'])
                    and name not in RESERVED and '/' not in name and not name.startswith(':'),
                    'Unsupported binding target: ' + name)
            return set() if name == '&' else {name}
        if node['kind'] == 'vector':
            result, index = set(), 0
            while index < len(values):
                word = spelling(values[index])
                if word in ('&', ':as'):
                    require(index + 1 < len(values), 'Incomplete vector destructuring')
                    result |= binding_names(values[index + 1]); index += 2
                else:
                    result |= binding_names(values[index]); index += 1
            return result
        if node['kind'] == 'map':
            require(len(values) % 2 == 0, 'Odd destructuring map')
            result = set()
            for key, value in zip(values[::2], values[1::2]):
                word = spelling(key)
                if word in (':keys', ':strs', ':syms'):
                    require(transparent(value)['kind'] == 'vector', 'Unknown destructuring key list')
                    result |= set().union(*(binding_names(n) for n in cs(transparent(value))))
                elif word == ':as':
                    result |= binding_names(value)
                elif word == ':or':
                    require(transparent(value)['kind'] == 'map', 'Unknown destructuring default map')
                else:
                    require(not word.startswith(':'), 'Unsupported destructuring directive')
                    result |= binding_names(key)
            return result
        raise QualificationError('Unsupported binding target kind: ' + node['kind'])

    def bindings(vector, local, charge):
        vector = transparent(vector); values = cs(vector)
        require(vector['kind'] == 'vector' and len(values) % 2 == 0, 'Expected complete binding vector')
        current = set(local)
        for target, value in zip(values[::2], values[1::2]):
            require(not spelling(target).startswith(':'), 'Binding modifiers need a separate qualification')
            if charge:
                add(target, 'independent-binding', span=(target['start'], value['end']))
            expression(value, current)
            binding_defaults(target, current)
            current |= binding_names(target)
        return current

    def binding_defaults(node, local):
        node = transparent(node); values = cs(node)
        if node['kind'] == 'vector':
            for value in values:
                if spelling(value) not in ('&', ':as'):
                    binding_defaults(value, local)
        elif node['kind'] == 'map':
            require(len(values) % 2 == 0, 'Odd destructuring map')
            for key, value in zip(values[::2], values[1::2]):
                word = spelling(key)
                if word == ':or':
                    defaults = cs(transparent(value))
                    require(transparent(value)['kind'] == 'map' and len(defaults) % 2 == 0, 'Unknown destructuring defaults')
                    for default in defaults[1::2]:
                        expression(default, local)
                elif word not in (':keys', ':strs', ':syms', ':as'):
                    require(transparent(value)['kind'] in ('atom', 'string', 'character', 'quote'), 'Computed destructuring lookup key is not qualified')
                    binding_defaults(key, local)

    def body(values, local, expression_body=False):
        if expression_body and len(values) == 1:
            expression(values[0], local)
        else:
            for value in values:
                statement(value, local)

    def function(node, local, definition=False):
        values = cs(node); index = 2 if definition else 1
        if index < len(values) and transparent(values[index])['kind'] == 'atom':
            require(not definition, 'Unsupported defn declaration')
            local = set(local) | binding_names(values[index]); index += 1
        if definition and index < len(values) and transparent(values[index])['kind'] == 'string':
            add(values[index], 'documentation', 0); index += 1
        require(index < len(values) and transparent(values[index])['kind'] == 'vector',
                'Only single-arity function forms are qualified')
        binding_defaults(values[index], local)
        local = set(local) | binding_names(values[index]); index += 1
        require(index < len(values), 'Function body missing')
        body(values[index:], local, expression_body=True)

    def conditional(node, local):
        values, name = cs(node), head(node)
        if name in ('if', 'if-let'):
            require(len(values) in (3, 4), 'Unknown conditional shape')
            add(node, name + '-expression', 0)
            if name == 'if-let':
                require(transparent(values[1])['kind'] == 'vector' and len(cs(transparent(values[1]))) == 2,
                        'Only one conditional binding is qualified')
                inner = bindings(values[1], local, False)
            else:
                inner = set(local); expression(values[1], local)
            expression(values[2], inner)
            if len(values) == 4:
                expression(values[3], local)
        elif name == 'cond':
            require(len(values) % 2 == 1, 'Unknown cond clause shape')
            add(node, 'cond-expression', 0)
            clauses = list(zip(values[1::2], values[2::2]))
            for index, (test, result) in enumerate(clauses):
                default = spelling(test) == ':else'
                require(not default or index == len(clauses) - 1, 'Only a final :else cond default is qualified')
                expression(test, local); expression(result, local)
        else:
            require(name == 'case' and len(values) >= 4, 'Unknown case shape')
            add(node, 'case-expression', 0)
            expression(values[1], local)
            clauses = values[2:]
            for result in clauses[1::2]:
                expression(result, local)
            if len(clauses) % 2:
                expression(clauses[-1], local)
            # Written case constants are data; no implicit dispatch is added.

    def expression(node, local):
        node = transparent(node); kind, values = node['kind'], cs(node)
        if kind in ('quote', 'var-quote'):
            return  # data/source reference, no evaluation/expansion
        if kind == 'deref':
            expression(values[0], local); return
        if kind in ('vector', 'map', 'set'):
            for value in values:
                expression(value, local)
            return
        if kind in ('atom', 'string', 'regex', 'character'):
            return
        require(kind in ('list', 'anonymous-fn'), 'Unknown source expression: ' + kind)
        require(values, 'Empty executable call is not qualified')
        name = head(node)
        if name in ('if', 'if-let', 'cond', 'case'):
            conditional(node, local); return
        if name in CONTROL or name in ('def', 'defn', 'ns'):
            statement(node, local); return
        if name == 'fn':
            function(node, local); return
        require(name not in native_macros or name in EXPRESSION_MACROS, 'Unqualified core macro: ' + str(name))
        if name in EXTERNAL_FUNCTIONS:
            require(name.split('/')[0] in aliases, 'External API used without its reviewed namespace alias')
        require(name in CORE_FUNCTIONS | EXTERNAL_FUNCTIONS | EXPRESSION_MACROS | globals_ | set(local) | {'recur', 'throw'}
                or name in JAVA_CALLS | JAVA_METHODS,
                'Unqualified call head (unknown function/macro): ' + str(name))
        for value in values[1:]:
            expression(value, local)

    def statement(node, local):
        node = transparent(node); values = cs(node); name = head(node) if node['kind'] in ('list', 'anonymous-fn') else None
        if name == 'ns':
            add(node, 'namespace-declaration'); return
        if name == 'def':
            require(len(values) in (2, 3, 4), 'Unsupported def shape')
            add(node, 'definition')
            if len(values) > 2:
                expression(values[-1], local)
            return
        if name == 'defn':
            add(node, 'function-definition'); function(node, local, True); return
        if name == 'do':
            add(node, 'syntax-block', 0); body(values[1:], local); return
        if name in ('let', 'loop', 'doseq', 'for', 'dotimes'):
            require(len(values) >= 3, 'Control/binding body missing')
            add(node, name + '-header')
            if name == 'dotimes':
                vector = transparent(values[1]); parts = cs(vector)
                require(vector['kind'] == 'vector' and len(parts) in (2, 3), 'Unknown dotimes header')
                for part in parts[1:]:
                    expression(part, local)
                inner = set(local) | binding_names(parts[0])
            else:
                inner = bindings(values[1], local, charge=name == 'let')
            body(values[2:], inner); return
        if name in ('if', 'if-let', 'cond', 'case'):
            # These forms have one expression per branch, like native ternary
            # expressions. Statement position adds one carrier, not branch rows.
            add(node, 'conditional-form-statement'); conditional(node, local); return
        if name in ('when', 'when-not'):
            require(len(values) >= 2, 'Missing when test')
            add(node, name + '-header'); expression(values[1], local); body(values[2:], local); return
        if name == 'try':
            add(node, 'try-header')
            for value in values[1:]:
                parts = cs(transparent(value)); clause = head(value) if transparent(value)['kind'] == 'list' else None
                if clause == 'finally':
                    add(value, 'finally-syntax', 0); body(parts[1:], local)
                elif clause == 'catch':
                    require(len(parts) >= 4, 'Unknown catch clause')
                    add(value, 'catch-syntax', 0); body(parts[3:], set(local) | binding_names(parts[2]))
                else:
                    statement(value, local)
            return
        if name == 'reify':
            add(node, 'anonymous-class-definition')
            for value in values[1:]:
                value = transparent(value)
                if value['kind'] == 'atom':
                    continue  # written interface/type name
                parts = cs(value)
                require(value['kind'] == 'list' and len(parts) >= 3 and transparent(parts[1])['kind'] == 'vector', 'Unknown reify method')
                require(all(transparent(parameter)['kind'] == 'atom' for parameter in cs(transparent(parts[1]))),
                        'Reify method parameter destructuring/defaults are outside the qualified subset')
                add(value, 'method-definition'); body(parts[2:], set(local) | binding_names(parts[1]), True)
            return
        add(node, 'form-statement'); expression(node, local)

    for ident in tree['roots']:
        statement(nodes[ident], set())
    token_owners = []
    for token in tree['tokens']:
        if token['trivia']:
            continue
        candidates = [owner for owner in out if owner['start'] <= token['start'] and token['end'] <= owner['end']]
        require(candidates, 'Significant source token has no native-bound owner')
        selected = min(candidates, key=lambda row: (row['end'] - row['start'], -row['id']))
        token_owners.append(dict(start=token['start'], end=token['end'], owner=selected['id']))
    return dict(status='native-qualified-exact-source-subset', logical_units=sum(row['units'] for row in out),
                owners=out, source_tree=tree, coverage=dict(significant_source_tokens=len(token_owners),
                unowned_significant_tokens=0, native_span_bound_forms=len(nodes),
                explicit_reader_internal_spans=[dict(start=a, end=b) for a, b in sorted(internal_spans)],
                token_ownership_sha256=sha(encoded(token_owners))), generic_language_certificate=False)


FIXTURES = {
    'packed-definitions': '(def x 1)(def y 2)\n',
    'expanded-definitions': '(def x 1)\n(def y 2)\n',
    'semicolon-comments': '(def x 1) ; (def fake 9)\n(def y 2)\n',
    'matrix-packed': '(def matrix [[1 2] [3 4]])\n',
    'matrix-wrapped': '(def matrix [\n [1 2]\n [3 4]\n])\n',
    'multi-bindings-packed': '(let [x 1 y 2] (+ x y))\n',
    'multi-bindings-wrapped': '(let [x 1\n y 2]\n (+ x y))\n',
    'pure-definition': '(defn f [x] (+ x 1))\n',
    'single-effectful-expression': '(defn emit [x] (println x))\n',
    'block-definition': '(defn f [x] (println x) (+ x 1))\n',
    'explicit-do-block': '(defn f [x] (do (println x) (+ x 1)))\n',
    'conditional-definition': '(defn f [x] (if x 1 2))\n',
    'conditional-lambda-binding': '(def f (fn [x] (if x 1 2)))\n',
    'conditional-cond-definition': '(defn f [x] (cond (pos? x) 1 :else 2))\n',
    'conditional-case-definition': '(defn f [x] (case x 0 1 1 2 3))\n',
    'conditional-let-initializer': '(let [x (if true 1 2)] x)\n',
    'conditional-do-branch': '(defn f [x] (if x (do (println x) 1) 2))\n',
    'conditional-let-branch': '(defn f [x] (if x (let [y 1] y) 2))\n',
    'conditional-multiform-body': '(defn f [x] (if x 1 2) (println x))\n',
    'conditional-in-argument': '(defn f [x] (+ (if x 1 2) 3))\n',
    'if-let-expression': '(defn f [x] (if-let [y x] y 0))\n',
    'conditional-top-level': '(if true 1 2)\n',
    'conditional-loop-body': '(dotimes [i 3] (if (pos? i) (println i) (println 0)))\n',
    'conditional-block-branch-top-level': '(if true (do (println 1) (println 2)) 0)\n',
    'when-multiform-body': '(when true (println 1) (println 2))\n',
    'destructuring': '(let [[x y] [1 2]] (+ x y))\n',
    'map-destructuring': '(let [{:keys [x y] :or {x 0}} {:x 1 :y 2}] (+ x y))\n',
    'literal-punctuation': '(def text "; ^ #= (not-code)")\n',
    'unicode-symbol-and-string': '(def β "🌱")\n',
    'anonymous-reduction': '(def result (reduce #(+ %1 %2) 0 [1 2 3]))\n',
    'function-composition': '(def f (comp inc first))\n',
    'loop-packed': '(loop [x 0 total 0] (if (< x 3) (recur (inc x) (+ total x)) total))\n',
    'loop-wrapped': '(loop [x 0 total 0]\n (if (< x 3)\n (recur (inc x) (+ total x))\n total))\n',
    'unknown-macro': '(unqualified-macro [x 1] (println x))\n',
    'unsupported-core-macro': '(with-open [stream nil] (println stream))\n',
    'unknown-default-macro': '(let [{:keys [x] :or {x (unknown-macro)}} {}] x)\n',
    'unknown-conditional-macro': '(defn f [x] (if x 1 (unknown-macro)))\n',
    'macro-flag-definition': '(defn ^:macro f [x] x) (f 1)\n',
    'unknown-java-method': '(.unknown-method value)\n',
    'unsupported-threading-macro': '(-> x inc inc)\n',
    'disabled-read-eval': '#=(throw (Exception. "must not run"))\n',
    'disabled-tag-reader': '#custom/tag {:x 1}\n',
    'disabled-constructor-reader': '#java.util.Date []\n',
    'invalid-reader': '(def x [1 2)\n',
}
PAIRS = [('packed-definitions', 'expanded-definitions'), ('packed-definitions', 'semicolon-comments'),
         ('matrix-packed', 'matrix-wrapped'), ('multi-bindings-packed', 'multi-bindings-wrapped'),
         ('block-definition', 'explicit-do-block'), ('loop-packed', 'loop-wrapped')]
PAIRS += [('conditional-definition', 'conditional-lambda-binding'),
          ('conditional-definition', 'conditional-cond-definition'),
          ('conditional-definition', 'conditional-case-definition')]
EXPECTED_UNITS = {'packed-definitions': 2, 'expanded-definitions': 2, 'semicolon-comments': 2,
    'matrix-packed': 1, 'matrix-wrapped': 1, 'multi-bindings-packed': 4, 'multi-bindings-wrapped': 4,
    'pure-definition': 1, 'single-effectful-expression': 1, 'block-definition': 3, 'explicit-do-block': 3, 'destructuring': 3,
    'conditional-definition': 1, 'conditional-lambda-binding': 1, 'conditional-cond-definition': 1,
    'conditional-case-definition': 1, 'conditional-let-initializer': 3, 'conditional-do-branch': 3,
    'conditional-let-branch': 4, 'conditional-multiform-body': 3, 'conditional-in-argument': 1,
    'if-let-expression': 1, 'conditional-top-level': 1, 'conditional-loop-body': 2,
    'conditional-block-branch-top-level': 3, 'when-multiform-body': 3,
    'map-destructuring': 3, 'literal-punctuation': 1, 'unicode-symbol-and-string': 1, 'anonymous-reduction': 1,
    'function-composition': 1,
    'loop-packed': 2, 'loop-wrapped': 2}


def inputs(root):
    catalog_path = root / 'data/benchmarks.json'; catalog = json.loads(catalog_path.read_bytes())
    programs = {**catalog.get('program_inventory', {}), **catalog['programs']}
    jobs, profiles = {}, {}
    for key, row in sorted(programs.items()):
        if row['language'] != 'clojure':
            continue
        parts = []
        for digest in row['files']:
            file = catalog['files'][digest]; require(sha(file['code'].encode()) == digest, 'Changed catalog source')
            override = row.get('file_roles', {}).get(digest, {})
            if isinstance(override, str):
                override = {'role': override}
            meta = {**file, **override}; role = meta.get('role', 'application')
            require(role in ('application', 'application-helper', 'runtime-setup', 'runtime-support'), 'Unknown role')
            included = role != 'runtime-support'
            require(meta.get('included_in_application_loc', included) == included, 'Contradictory role')
            # Current exact cohort uses complete excluded units. A partial range
            # requires a separately qualified projection, never a guessed reparse.
            require(not meta.get('support_line_ranges'), 'Embedded support ranges are not yet qualified for this Clojure subset')
            ident = 'file:' + digest
            jobs[ident] = dict(text=file['code'], source_sha256=digest, scope='submitted-source-unit')
            parts.append(dict(source_sha256=digest, role=role, included_in_application=included,
                              included_ranges='whole-file' if included else [], excluded_ranges=[] if included else 'whole-file', job=ident))
        profiles[key] = dict(files=parts, retained_loc=row['loc'], retained_physical_loc=row.get('physical_loc'))
    variants = []
    source_key = 'nbody:clojure-nbody-compact'
    if source_key in profiles:
        part = next(part for part in profiles[source_key]['files'] if part['included_in_application'])
        original = jobs[part['job']]['text']
        changes = [('source-matrix-wrapping',
            '(double-array [0.0 0.0 0.0 0.0 0.0 0.0 solar-mass])',
            '(double-array [\n0.0 0.0 0.0\n0.0 0.0 0.0 solar-mass])'),
            ('source-definition-packing',
             '(def solar-mass (* 4.0 Math/PI Math/PI))\n(def days-per-year 365.24)',
             '(def solar-mass (* 4.0 Math/PI Math/PI))(def days-per-year 365.24)'),
            ('source-binding-wrapping',
             '[n (s/argument arguments 1000) system (bodies)]',
             '[n (s/argument arguments 1000)\n system (bodies)]')]
        for name, before, after in changes:
            require(original.count(before) == 1, 'Source-qualified fixture anchor differs')
            text = original.replace(before, after, 1); ident = 'variant:' + name
            jobs[ident] = dict(text=text, source_sha256=sha(text.encode()), scope='exact-source-derived-fixture')
            variants.append(dict(name=name, base_job=part['job'], variant_job=ident,
                                 program=source_key, before=before, after=after,
                                 original_source_sha256=part['source_sha256'], variant_sha256=sha(text.encode())))
    for name, text in FIXTURES.items():
        jobs['fixture:' + name] = dict(text=text, source_sha256=sha(text.encode()), scope='synthetic-fixture')
    supplemental = []
    for path, digest in SUPPLEMENTAL:
        raw = (root / path).read_bytes(); require(sha(raw) == digest, 'Changed supplemental source')
        ident = 'file:' + digest
        if ident not in jobs:
            jobs[ident] = dict(text=raw.decode(), source_sha256=digest, scope='supplemental-unadmitted-source')
        supplemental.append(dict(path=path, source_sha256=digest, job=ident,
            retained_profile_keys=[key for key, row in profiles.items() if any(part['job'] == ident for part in row['files'])]))
    return dict(schema='clojure-logical-source-inputs.v1', policy=POLICY,
                catalog_sha256=sha(catalog_path.read_bytes()), programs=profiles, jobs=jobs, source_variants=variants,
                supplemental_sources=supplemental,
                qualification_status='source-manifest-prepared-native-evidence-separate',
                prepared_without_native_execution=True, canonical_changed=False)


def prepare(root):
    manifest = inputs(root); packet = root / PACKET
    write(packet / 'inputs.json', manifest)
    # EDN input is a trusted manifest container, not evaluated application text.
    strings = lambda value: json.dumps(value, ensure_ascii=True)
    edn = '[\n' + '\n'.join('[' + ' '.join(strings(value) for value in (key, job['text'], job['source_sha256'])) + ']'
                           for key, job in sorted(manifest['jobs'].items())) + '\n]\n'
    (packet / 'inputs.edn').write_text(edn)
    return manifest


def reader_jobs(manifest):
    return {key: {name: row[name] for name in ('text', 'source_sha256')} for key, row in manifest['jobs'].items()}


def capture_locked(root, java, jars, mutex):
    manifest = prepare(root); packet = root / PACKET
    jars = [Path(path).resolve() for path in jars]
    require(len(jars) == 4 and {path.name: sha(path.read_bytes()) for path in jars} == JAR_PINS, 'Changed pinned native classpath')
    require(sha(Path(java).read_bytes()) == JAVA_SHA, 'Changed pinned Java launcher')
    helper = packet / 'capture.clj'
    command = [str(Path(java).resolve()), '-Xms32m', '-Xmx256m', '-cp', ':'.join(map(str, jars)),
               'clojure.main', str(helper), str(packet / 'inputs.edn')]
    environment = dict(PATH='/usr/bin:/bin', LANG='C', LC_ALL='C', TZ='UTC')
    run = subprocess.run(command, cwd=root, env=environment, capture_output=True, check=False, timeout=90)
    require(run.returncode == 0 and not run.stderr, 'Native reader helper failed: ' + run.stderr.decode(errors='replace')[:1000])
    native = json.loads(run.stdout)
    require(native['clojure_version'] == '1.12.6' and set(native['jobs']) == set(manifest['jobs']), 'Wrong native capture inventory/version')
    native['capture_binding'] = dict(jobs_sha256=sha(encoded(reader_jobs(manifest))),
        captured_catalog_sha256=manifest['catalog_sha256'], native_input_edn_sha256=sha((packet / 'inputs.edn').read_bytes()),
        helper_sha256=sha(helper.read_bytes()),
        producer_tool_sha256=sha(Path(__file__).read_bytes()), executable_sha256=sha(Path(java).read_bytes()),
        jars=[dict(name=path.name, sha256=sha(path.read_bytes())) for path in jars], command=command,
        common_mutex=mutex, controlled_environment=environment)
    with (packet / 'native-capture.json.gz').open('wb') as target:
        with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=0) as stream:
            stream.write(encoded(native))
    return native


def capture(root, java, jars):
    lock_path = Path('/tmp/mech-clbg-timing.lock')
    require(lock_path.exists(), 'The common native-work timing mutex must already exist')
    with lock_path.open('r+b') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise QualificationError('Native capture is blocked by another timing-window owner') from error
        return capture_locked(root, java, jars, dict(path=str(lock_path), inode=lock_path.stat().st_ino,
            exclusive_nonblocking_lock=True))


def replay(root):
    packet = root / PACKET; expected = inputs(root)
    require(json.loads((packet / 'inputs.json').read_bytes()) == expected, 'Source/catalog input manifest drift')
    native = json.loads(gzip.decompress((packet / 'native-capture.json.gz').read_bytes()))
    binding = native['capture_binding']
    require(binding['jobs_sha256'] == sha(encoded(reader_jobs(expected)))
            and binding['native_input_edn_sha256'] == sha((packet / 'inputs.edn').read_bytes())
            and binding['helper_sha256'] == sha((packet / 'capture.clj').read_bytes())
            and binding['executable_sha256'] == JAVA_SHA
            and {row['name']: row['sha256'] for row in binding['jars']} == JAR_PINS, 'Native capture producer/input/runtime drift')
    outcomes = {}
    for key, job in expected['jobs'].items():
        try:
            result = owners(job['text'], source_tree(job['text']), native['jobs'][key])
        except QualificationError as error:
            result = dict(status='unqualified', reason=str(error))
        outcomes[key] = result
    profiles = {}
    for key, row in expected['programs'].items():
        results = [outcomes[part['job']] for part in row['files']]
        ok = all(result['status'] != 'unqualified' for result in results)
        profile = dict(status='native-qualified-exact-source-subset' if ok else 'unqualified', files=row['files'],
                       retained_loc=row['retained_loc'], retained_physical_loc=row['retained_physical_loc'])
        if ok:
            profile.update(application_logical_units=sum(result['logical_units'] for part, result in zip(row['files'], results) if part['included_in_application']),
                           submitted_logical_units=sum(result['logical_units'] for result in results),
                           excluded_support_logical_units=sum(result['logical_units'] for part, result in zip(row['files'], results) if not part['included_in_application']))
        profiles[key] = profile
    pairs = []
    for a, b in PAIRS:
        left, right = outcomes['fixture:' + a], outcomes['fixture:' + b]
        pairs.append(dict(left=a, right=b, left_units=left.get('logical_units'), right_units=right.get('logical_units'),
                          passed=left.get('logical_units') is not None and left.get('logical_units') == right.get('logical_units')))
    source_variants = []
    for variant in expected['source_variants']:
        a, b = outcomes[variant['base_job']], outcomes[variant['variant_job']]
        source_variants.append(dict(**variant, base_units=a.get('logical_units'), variant_units=b.get('logical_units'),
            passed=a.get('logical_units') is not None and a.get('logical_units') == b.get('logical_units')))
    fixture_expectations = []
    for name in FIXTURES:
        result = outcomes['fixture:' + name]; value = EXPECTED_UNITS.get(name)
        fixture_expectations.append(dict(name=name, expected_units=value, actual_units=result.get('logical_units'),
            expected_status='unqualified' if value is None else 'native-qualified-exact-source-subset',
            passed=(result['status'] == 'unqualified') if value is None else result.get('logical_units') == value))
    report = dict(schema='clojure-logical-source-qualification.v1', policy=POLICY,
        status='native-qualified-exact-source-subset', canonical_changed=False,
        native_capture_sha256=sha((packet / 'native-capture.json.gz').read_bytes()), inputs_sha256=sha(encoded(expected)),
        analysis_tool_sha256=sha(Path(__file__).read_bytes()), programs=profiles, outcomes=outcomes,
        supplemental_sources=expected['supplemental_sources'],
        paired_fixtures=pairs, fixture_expectations=fixture_expectations, source_variants=source_variants,
        generic_language_certificate=False,
        summary=dict(profiles=len(profiles), source_units=sum(k.startswith('file:') for k in expected['jobs']),
                     retained_source_units=len({part['job'] for profile in expected['programs'].values() for part in profile['files']}),
                     supplemental_source_units=len({row['job'] for row in expected['supplemental_sources']} - {part['job'] for profile in expected['programs'].values() for part in profile['files']}),
                     source_units_native_bound=sum(k.startswith('file:') and v['status'] != 'unqualified' for k, v in outcomes.items()),
                     all_pairs_pass=all(pair['passed'] for pair in pairs),
                     all_source_variants_pass=all(row['passed'] for row in source_variants),
                     all_fixture_expectations_pass=all(row['passed'] for row in fixture_expectations)))
    write(packet / 'qualification.json', report)
    return report


def review_receipt(root):
    """Bind the completed independent review; refresh projections only if unchanged.

    Approval applies to this source proof. A new policy/tool/native capture or
    per-source outcome fails refresh rather than borrowing the previous review.
    """
    packet = root / PACKET; report = json.loads((packet / 'qualification.json').read_bytes())
    require(report['summary']['all_pairs_pass'] and report['summary']['all_source_variants_pass']
            and report['summary']['all_fixture_expectations_pass']
            and report['summary']['source_units'] == report['summary']['source_units_native_bound'], 'Incomplete qualification')
    scope = dict(policy=POLICY, tool_sha256=sha(Path(__file__).read_bytes()),
        policy_sha256=sha((packet / 'policy.json').read_bytes()), helper_sha256=sha((packet / 'capture.clj').read_bytes()),
        native_capture_sha256=report['native_capture_sha256'], source_proof_sha256=sha(encoded(report['outcomes'])),
        tests_sha256=sha((packet / 'test_replay.py').read_bytes()))
    target = packet / 'independent-review.json'
    if target.exists():
        require(json.loads(target.read_bytes())['approved_source_scope'] == scope, 'Independent source review invalidated by code/policy/proof drift')
    receipt = dict(schema='clojure-logical-owner-independent-review.v1', decision='qualified-exact-source-subset',
        review_basis='Independent static review of native-bound walker, source scopes, expression/loop decisions and explicit fixture expectations; native parse-only capture and offline regression checks.',
        approved_source_scope=scope, current_projection=dict(report_sha256=sha((packet / 'qualification.json').read_bytes()),
            inputs_sha256=report['inputs_sha256'], programs=sorted(report['programs'])),
        source_policy_limits=['No whole-language certificate or universal fairness claim.',
            'Clojure fixed-shape conditionals remain expressions; explicit blocks remain visible.',
            'Loop state/iterator binders belong to one header; independent let pairs count separately.',
            'Reify methods permit scalar parameter symbols only; destructuring/defaults fail.',
            'New catalog projections can reuse only unchanged, already reviewed exact source proofs.'])
    write(target, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'capture', 'replay', 'review')); parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--java'); parser.add_argument('--jar', action='append', default=[])
    args = parser.parse_args(); root = args.root.resolve()
    if args.mode == 'prepare':
        value = prepare(root); print(dict(status=value['qualification_status'], profiles=len(value['programs']), jobs=len(value['jobs'])))
    elif args.mode == 'capture':
        require(args.java and args.jar, 'Capture needs explicit pinned java and jars; schedule outside benchmark windows')
        value = capture(root, args.java, args.jar); print(dict(native_jobs=len(value['jobs']), input_evaluated=False))
    elif args.mode == 'replay':
        print(replay(root)['summary'])
    else:
        print(review_receipt(root)['decision'])


if __name__ == '__main__':
    main()
