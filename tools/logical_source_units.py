#!/usr/bin/env python3
"""Qualify native Python/Julia logical source owners for exact retained sources.

No input is executed, lowered or macro-expanded. This additive v2 qualification
does not change canonical LOC, timing samples, eligibility or chart coordinates.
"""
import argparse
import ast
import collections
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tokenize

ROOT = Path(__file__).resolve().parents[1]
PACKET = Path('experiments/source-normalization/v2')
BUILD = Path('experiments/source-normalization/.build')
POLICY = 'logical-source-owners.v2-python-julia'
JULIA_VERSION = '1.13.1'
JULIA_ARCHIVE_SHA = 'a3e0259d4777c2b776c2cba134d5b6c6c124048dcb913f8881517892c49a0f7f'
LANGUAGES = ('python', 'julia', 'julia-aot')


class QualificationError(ValueError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def pretty(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def require(condition, message):
    if not condition:
        raise QualificationError(message)


def rule_definition():
    return dict(id=POLICY, status='native-qualified-exact-source-subset',
        unit_definition='Independent native statement/binding, definition or control header; pure expression-function binding is one owner.',
        close_and_literal_rows=0, generic_language_certificate=False,
        rules=[
            'Count each independent executable statement, binding, explicit definition and explicit control header once. Chained assignments charge each written assignment target; destructuring with one initializer remains one owner.',
            'Written end/braces, grouping punctuation, else/catch/finally separators, matrix/array row separators and literal continuation rows add no units.',
            'Pure expression functions, lambdas, array primitives, reductions, comprehensions and compositions remain expressions; do not invent scalar operations or implicit loops.',
            'Long/block function declarations own one header and their independent written body statements. Short expression functions own one definition; written multi-statement blocks inside their expression remain visible.',
            'A loop header includes its iterator/binding/control syntax. Its body statements count independently. Native ternary and short-circuit expressions remain single expressions.',
            'Python documentation strings are zero-unit documentation owners; ordinary standalone literal expressions remain statements. Decorators belong to the definition owner.',
            'Julia whitelisted annotation/task macros wrap the written payload without expansion and add no extra owner. Expression macros remain expressions; unsupported macro names fail qualification.',
            'All significant native tokens must be covered by a native owner or explicit zero-unit syntax. Unknown syntax, parse diagnostics, source/evidence drift and contradictory role metadata fail closed.'],
        limitations=[
            'Qualification applies to the exact recorded source hashes and tested native syntax forms, not every Python/Julia grammar construct.',
            'No macro execution/expansion, language lowering, compiler-generated code or installed library implementation is counted.',
            'This policy differs from canonical cohorts that count written closers, literal wrapping or physical rows. No canonical rebase is performed.'])


def program_catalog(data):
    return {**data.get('program_inventory', {}), **data['programs']}


def metadata(row, digest, source):
    override = row.get('file_roles', {}).get(digest, {})
    if isinstance(override, str):
        override = {'role': override}
    value = {**source, **override}
    role = value.get('role', 'application')
    require(role in ('application', 'application-helper', 'runtime-setup', 'runtime-support'), 'Unknown source role')
    included = role != 'runtime-support'
    require(value.get('included_in_application_loc', included) == included, 'Contradictory source role')
    return value, included


def project_application(text, ranges):
    """Mask only reviewed support, retaining native original UTF-8 byte offsets."""
    lines = text.splitlines(keepends=True)
    previous = 0
    excluded = set()
    for span in ranges:
        a, b = span['start'], span['end']
        require(type(a) is int and type(b) is int and previous < a <= b <= len(lines), 'Invalid support range')
        previous = b
        excluded.update(range(a, b + 1))
    # A UTF-8 glyph outside the application becomes the same number of spaces,
    # so native byte positions still address the exact complete original file.
    return b''.join((bytes(c if c in (10, 13) else 32 for c in line.encode('utf-8'))
                     if number in excluded else line.encode('utf-8'))
                    for number, line in enumerate(lines, 1)).decode('utf-8')


def offsets(text):
    starts, current = [], 0
    for line in text.splitlines(keepends=True):
        starts.append(current); current += len(line.encode('utf-8'))
    starts.append(current)
    return starts


PYTHON_STATEMENTS = frozenset(('FunctionDef', 'AsyncFunctionDef', 'ClassDef', 'Return', 'Delete', 'Assign',
    'AugAssign', 'AnnAssign', 'For', 'AsyncFor', 'While', 'If', 'With', 'AsyncWith', 'Raise', 'Try',
    'Assert', 'Import', 'ImportFrom', 'Global', 'Nonlocal', 'Expr', 'Pass', 'Break', 'Continue'))
PYTHON_IGNORED_TOKENS = frozenset((tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
    tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING))


def python_units(text):
    raw = text.encode('utf-8')
    try:
        tree = ast.parse(text, filename='<hash-bound-application>', type_comments=True)
    except (SyntaxError, ValueError) as error:
        raise QualificationError('Native Python parse rejected: ' + str(error)) from error
    require(not any(isinstance(node, ast.NamedExpr) for node in ast.walk(tree)),
            'Python assignment-expression ownership is not qualified in this exact-source subset')
    starts = offsets(text)
    rows = text.splitlines(keepends=True)
    owners = []
    documentation = set()
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = parent.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                documentation.add(id(body[0]))
    def visit(node, path, parent_owner=None):
        current_owner = parent_owner
        if isinstance(node, ast.stmt):
            kind = type(node).__name__
            require(kind in PYTHON_STATEMENTS, 'Unqualified Python statement kind: ' + kind)
            start_line, start_column = node.lineno, node.col_offset
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.decorator_list:
                first = min(node.decorator_list, key=lambda value: (value.lineno, value.col_offset))
                start_line, start_column = first.lineno, max(0, first.col_offset - 1)  # include @
            a = starts[start_line - 1] + start_column
            b = starts[node.end_lineno - 1] + node.end_col_offset
            units = len(node.targets) if isinstance(node, ast.Assign) else 1
            if id(node) in documentation:
                units = 0
            current_owner = len(owners) + 1
            owners.append(dict(id=current_owner, parent_owner=parent_owner, native_path=path, kind=kind,
                units=units, start=a, end=b, line=start_line, end_line=node.end_lineno,
                source_sha256=sha(raw[a:b]), reason='native-docstring' if not units else 'native-statement-owner'))
        for name, child in ast.iter_fields(node):
            if isinstance(child, ast.AST):
                visit(child, path + '.' + name, current_owner)
            elif isinstance(child, list):
                for i, item in enumerate(child):
                    if isinstance(item, ast.AST):
                        visit(item, f'{path}.{name}[{i}]', current_owner)
    visit(tree, 'Module')
    tokens = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in PYTHON_IGNORED_TOKENS:
            continue
        def absolute(position):
            line, column = position
            return starts[line - 1] + len(rows[line - 1][:column].encode('utf-8'))
        a, b = absolute(token.start), absolute(token.end)
        if token.string == ';':
            tokens.append(dict(start=a, end=b, owner=None, zero_unit_reason='statement-separator'))
            continue
        candidates = [owner for owner in owners if owner['start'] <= a and b <= owner['end']]
        require(candidates, 'Significant Python token lacks native owner: ' + repr(token.string))
        owner = min(candidates, key=lambda item: (item['end'] - item['start'], -item['id']))
        tokens.append(dict(start=a, end=b, owner=owner['id']))
    # Every native statement must be counted, including statements sharing a row.
    require(len(owners) == sum(isinstance(n, ast.stmt) for n in ast.walk(tree)), 'Missing Python statement owner')
    normalized_ast = ast.dump(tree, include_attributes=False)
    return dict(parser='CPython ast.parse + tokenize', accepted=True, source_sha256=sha(raw),
        logical_loc=sum(owner['units'] for owner in owners), owners=owners,
        coverage=dict(significant_tokens=len(tokens), unowned_significant_tokens=0,
                      token_ownership_sha256=sha(encoded(tokens))),
        native_ast_sha256=sha(normalized_ast.encode('utf-8')), generic_language_certificate=False)


JULIA_DECORATING_MACROS = frozenset(('@inline', '@inbounds', '@fastmath', '@simd', '@sync',
    'Threads.@threads', 'Threads.@spawn', '@everywhere', '@distributed', 'Base.@propagate_inbounds'))
JULIA_EXPRESSION_MACROS = frozenset(('@ntuple', '@printf', 'Printf.@printf'))
JULIA_LITERAL_MACROS = frozenset(('r', 'b'))  # regex and byte-string literals present in exact sources
JULIA_CONTROL = frozenset(('function', 'for', 'while', 'if', 'elseif', 'let', 'try', 'struct', 'module', 'macro', 'do'))
JULIA_ZERO_BRANCH = frozenset(('finally', 'catch', 'else'))
JULIA_BINDING_WRAPPERS = frozenset(('const', 'global', 'local'))
JULIA_EXPR_KINDS = frozenset(('Identifier', 'Integer', 'String', 'string', 'Float', 'HexInt', 'Bool',
    'char', 'Char', 'macro_name', 'StrMacroName', 'CmdMacroName', 'importpath', '=', 'op=', 'call', 'ref',
    '.', '::', 'tuple', 'iteration', 'in', 'juxtapose', 'curly', 'dotcall', '&&', '||', '?', '->',
    'vect', 'parameters', 'generator', 'where', 'typed_comprehension', 'vcat', ':', 'comprehension',
    'row', '...', '<:', '>:', 'hcat', 'ncat', 'nrow', 'typed_vcat', 'typed_hcat', 'typed_ncat',
    'braces', 'comparison', 'cartesian_iterator', 'using', 'import', 'export', 'public', 'return',
    'break', 'continue', 'abstract', 'primitive', 'inert'))


def julia_units(text, capture):
    raw = text.encode('utf-8')
    require(capture['source_sha256'] == sha(raw), 'Julia native source hash differs')
    require(capture['accepted'] is True, 'Native Julia parse rejected: ' + capture.get('error', 'unknown'))
    nodes = {item['id']: item for item in capture['nodes']}
    require(len(nodes) == len(capture['nodes']) and 1 in nodes, 'Malformed native Julia node identities')
    for node in nodes.values():
        for child_id in node['children']:
            require(child_id in nodes and nodes[child_id]['parent'] == node['id'], 'Broken native Julia tree edge')
            require(node['start'] <= nodes[child_id]['start'] <= nodes[child_id]['end'] <= node['end'],
                    'Native Julia child range outside parent')
    owners = []
    seen = set()
    def children(node):
        return [nodes[i] for i in node['children']]
    def spelling(node):
        return raw[node['start']:node['end']].decode('utf-8')
    def owner(node, kind=None, units=1, span=None):
        require(node['id'] not in seen, 'Duplicate Julia owner')
        seen.add(node['id'])
        a, b = span if span else (node['start'], node['end'])
        require(0 <= a <= b <= len(raw), 'Native Julia owner range outside input')
        owners.append(dict(id=len(owners) + 1, native_node=node['id'], kind=kind or node['kind'],
            units=units, start=a, end=b, line=raw[:a].count(b'\n') + 1,
            end_line=raw[:b].count(b'\n') + 1, source_sha256=sha(raw[a:b])))
    def macro_payload(node):
        cs = children(node)
        require(cs, 'Empty Julia macro call')
        name = spelling(cs[0])
        if cs[0]['kind'] in ('StrMacroName', 'CmdMacroName'):
            require(name in JULIA_LITERAL_MACROS, 'Unqualified Julia literal macro: ' + name)
            return 'literal', cs[1:]
        if name in JULIA_DECORATING_MACROS:
            return 'decoration', cs[1:]
        require(name in JULIA_EXPRESSION_MACROS, 'Unqualified Julia macro: ' + name)
        return 'expression', cs[1:]
    def expression(node, parent_kind=None):
        kind = node['kind']
        if kind == 'quote':
            return  # quoted AST is literal data, not expanded/evaluated source
        if kind in ('toplevel', 'block'):
            owner(node, kind='syntax-block', units=0)
            for child in children(node):
                statement(child)
        elif kind == 'parens':
            for child in children(node):
                expression(child, kind)
        elif kind in JULIA_CONTROL:
            statement(node)
        elif kind == '=' and parent_kind not in ('call', 'parameters', 'tuple', 'iteration', 'in', 'generator'):
            statement(node)
        elif kind == 'macrocall':
            behavior, payload = macro_payload(node)
            if behavior == 'literal':
                return
            for child in payload:
                expression(child, kind)
        elif kind == '->':
            cs = children(node)
            require(len(cs) == 2, 'Unknown Julia lambda shape')
            body = cs[-1]
            if body['kind'] == 'block':
                statements = children(body)
                # A single pure callback expression remains an expression.
                if len(statements) == 1 and statements[0]['kind'] not in JULIA_CONTROL | {'=', 'op='}:
                    expression(statements[0], '->')
                else:
                    expression(body, '->')
            else:
                expression(body, '->')
        else:
            require(kind in JULIA_EXPR_KINDS, 'Unqualified Julia expression kind: ' + kind)
            for child in children(node):
                expression(child, kind)
    def statement(node, span=None):
        kind = node['kind']
        cs = children(node)
        if kind in ('toplevel', 'block', 'parens'):
            owner(node, kind='syntax-block', units=0, span=span)
            for child in cs:
                statement(child)
            return
        if kind == 'macrocall':
            behavior, payload = macro_payload(node)
            if behavior == 'decoration':
                # Nested annotation/task decorators retain the same owner.
                require(payload and (len(payload) == 1 or payload[-1]['kind'] == 'for'),
                        'Unqualified Julia decorating macro argument structure')
                statement(payload[-1], span=span or (node['start'], node['end']))
            else:
                owner(node, kind='macro-expression', span=span)
                if behavior != 'literal':
                    for child in payload:
                        expression(child, 'macrocall')
            return
        owner(node, span=span)
        if kind == 'function':
            require(len(cs) >= 2, 'Unknown Julia function shape')
            for signature in cs[:-1]:
                expression(signature, 'function-signature')
            if node['short_function']:
                # No extra charge for the pure expression body of f(x)=expr.
                expression(cs[-1], 'short-function')
            else:
                require(cs[-1]['kind'] == 'block', 'Long Julia function lacks native block')
                expression(cs[-1], 'function')
        elif kind in JULIA_CONTROL:
            for child in cs:
                if child['kind'] in {'block', 'elseif'} | JULIA_ZERO_BRANCH:
                    if child['kind'] in JULIA_ZERO_BRANCH:
                        owner(child, kind='syntax-branch', units=0)
                        for body in children(child):
                            expression(body, child['kind'])
                    else:
                        expression(child, kind)
                else:
                    # Iterator binders are structural (the native `in` and
                    # `iteration` parent kinds suppress extra binding units),
                    # but their executable expressions must still be checked.
                    expression(child, kind)
        elif kind in JULIA_BINDING_WRAPPERS:
            # const/global/local annotate their binding instead of duplicating it.
            def binding_contents(child):
                if child['kind'] in JULIA_BINDING_WRAPPERS:
                    for value in children(child):
                        binding_contents(value)
                elif child['kind'] == '=':
                    for value in children(child)[1:]:
                        expression(value, '=')
                else:
                    expression(child, kind)
            for child in cs:
                binding_contents(child)
        else:
            require(kind in JULIA_EXPR_KINDS or kind == 'quote', 'Unqualified Julia statement kind: ' + kind)
            if kind != 'quote':
                for child in (cs[1:] if kind == '=' else cs):
                    expression(child, kind)
    statement(nodes[1])
    token_owners = []
    for token in capture['tokens']:
        if token['trivia'] or token['start'] == token['end']:
            continue
        a, b = token['start'], token['end']
        require(0 <= a <= b <= len(raw), 'Native Julia token outside input')
        candidates = [item for item in owners if item['start'] <= a and b <= item['end']]
        require(candidates, 'Significant Julia token lacks owner: ' + repr(raw[a:b]))
        item = min(candidates, key=lambda value: (value['end'] - value['start'], -value['units'], -value['id']))
        token_owners.append(dict(start=a, end=b, owner=item['id']))
    # The native lossless token stream must cover exactly the whole input.
    require(b''.join(raw[t['start']:t['end']] for t in capture['tokens']) == raw,
            'Native Julia token stream is not lossless/full-input')
    return dict(parser='Julia 1.13.1 Base.JuliaSyntax native syntax tree', accepted=True,
        source_sha256=sha(raw), logical_loc=sum(item['units'] for item in owners), owners=owners,
        coverage=dict(significant_tokens=len(token_owners), unowned_significant_tokens=0,
                      token_ownership_sha256=sha(encoded(token_owners))), generic_language_certificate=False)


JULIA_FIXTURES = {
    'semicolon-packed': 'x=1; y=2\n',
    'semicolon-expanded': 'x=1\ny=2\n',
    'matrix-packed': 'x=[1 2; 3 4]\n',
    'matrix-wrapped': 'x=[1 2;\n3 4]\n',
    'keyword-semicolon': 'sort!(counts; lt=freq_isless, rev=true)\n',
    'literal-punctuation': 'x="; # end"\n',
    'expression-function': 'f(x)=x+1\n',
    'block-function': 'function f(x)\n y=x+1\n y\nend\n',
    'loop-packed': 'for i=1:3; x+=i; y+=i; end\n',
    'loop-expanded': 'for i=1:3\n x+=i\n y+=i\nend\n',
    'invalid': 'function f(\n',
    'nested-block': 'a=(x=1; x+1)\n',
    'quoted-code': 'x=:(a=1;b=2)\n',
    'macro-block': '@inbounds for i=1:3\n x[i]+=1\nend\n',
}
JULIA_VARIANTS = (
    ('fannkuchredux:fannkuchredux-julia-1', 'sign = 1; maxflips = sum = 0', 'sign = 1\n    maxflips = sum = 0'),
    ('fannkuchredux:fannkuchredux-julia-2', 'lo = 2; hi = first - 1', 'lo = 2\n                hi = first - 1'),
)
PYTHON_FIXTURE_PAIRS = (
    ('independent-semicolon-statements', 'x=1; y=2\n', 'x=1\ny=2\n', 2),
    ('matrix-literal-wrapping', 'x=[[1,2],[3,4]]\n', 'x=[\n [1,2],\n [3,4]\n]\n', 1),
    ('loop-header-and-packed-body', 'for i in range(3): x+=i; y+=i\n', 'for i in range(3):\n x+=i\n y+=i\n', 3),
    ('literal-punctuation', 'x="; # end"\n', 'x = ("; # end")\n', 1),
    ('chained-assignment', 'x=y=1\n', 'x = y = (1)\n', 2),
    ('pure-expression-lambda', 'f=lambda x:x+1\n', 'f = (lambda x: (x + 1))\n', 1),
)


def application_inputs(data):
    inputs = {}
    for key, row in sorted(program_catalog(data).items()):
        if row['language'] not in LANGUAGES:
            continue
        for digest in row['files']:
            source = data['files'][digest]
            require(sha(source['code'].encode('utf-8')) == digest, 'Canonical source hash differs')
            value, included = metadata(row, digest, source)
            if included:
                text = project_application(source['code'], value.get('support_line_ranges', []))
                identity = key if len(row['files']) == 1 else key + ':' + digest
                inputs[identity] = dict(text=text, program=key, language=row['language'],
                    full_source_sha256=digest, application_projection_sha256=sha(text.encode('utf-8')),
                    support_line_ranges=value.get('support_line_ranges', []))
    return inputs


def julia_input_manifest(data):
    result = {}
    for identity, row in application_inputs(data).items():
        if row['language'] == 'python':
            continue
        result[identity] = dict(row)
        if row['support_line_ranges']:
            result[identity + ':submitted'] = dict(row,
                text=data['files'][row['full_source_sha256']]['code'], scope='submitted')
    for name, text in JULIA_FIXTURES.items():
        result['fixture:' + name] = dict(text=text, fixture=name)
    catalog = program_catalog(data)
    for key, old, new in JULIA_VARIANTS:
        source = data['files'][catalog[key]['files'][0]]['code']
        require(source.count(old) == 1, 'Real-source variant replacement must be unique')
        result['variant:' + key] = dict(text=source.replace(old, new), variant_of=key, old=old, new=new)
    for row in result.values():
        row['sha256'] = sha(row['text'].encode('utf-8'))
        row['input'] = row['sha256'] + '.jl'
    return result


def native_capture(data, julia, root=ROOT):
    """Explicit refresh only: bounded native parser, no workload evaluation."""
    root = Path(root)
    binary = Path(julia).resolve()
    require(binary.is_file(), 'Missing Julia parser runtime')
    manifest = julia_input_manifest(data)
    directory = root / BUILD / 'inputs'
    directory.mkdir(parents=True, exist_ok=True)
    for row in manifest.values():
        (directory / row['input']).write_bytes(row['text'].encode('utf-8'))
    arguments = [str(binary), '--startup-file=no', '--history-file=no', '--threads=1',
                 str(root / 'tools/julia_source_tree.jl')]
    arguments += [str(directory / name) for name in sorted({row['input'] for row in manifest.values()})]
    environment = dict(PATH='/usr/bin:/bin', LC_ALL='C', JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                       JULIA_LOAD_PATH='@stdlib', JULIA_DEPOT_PATH=str(root / BUILD / 'julia-depot'))
    process = subprocess.run(arguments, env=environment, capture_output=True, timeout=30, check=False)
    require(process.returncode == 0 and not process.stderr, 'Julia parser process failed: ' + process.stderr.decode(errors='replace'))
    result = json.loads(process.stdout)
    require(result['version'] == JULIA_VERSION, 'Native Julia runtime version differs')
    require(not result['input_evaluation'] and not result['macro_expansion'] and not result['lowering'], 'Unsafe native evidence mode')
    receipt = dict(schema='logical-source-native-capture.v2', tool='tools/julia_source_tree.jl',
        tool_sha256=sha((root / 'tools/julia_source_tree.jl').read_bytes()),
        executable=dict(path=str(binary), sha256=sha(binary.read_bytes()), version=JULIA_VERSION),
        official_archive_sha256=JULIA_ARCHIVE_SHA, argv=arguments, environment=environment,
        exit_code=process.returncode, stderr_sha256=sha(process.stderr), stdout_sha256=sha(process.stdout),
        canonical_result_sha256=sha(encoded(result)),
        input_evaluation=False, macro_expansion=False, lowering=False, benchmark_executions=0)
    save_native(result, receipt, root)
    return result, receipt


def save_native(result, receipt, root=ROOT):
    directory = Path(root) / PACKET
    directory.mkdir(parents=True, exist_ok=True)
    raw = encoded(result)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, filename='', mode='wb', mtime=0, compresslevel=9) as stream:
        stream.write(raw)
    (directory / 'native-trees.json.gz').write_bytes(buffer.getvalue())
    (directory / 'native-capture.json').write_bytes(pretty(receipt))


def load_native(data, root=ROOT):
    directory = Path(root) / PACKET
    result = json.loads(gzip.decompress((directory / 'native-trees.json.gz').read_bytes()))
    receipt = json.loads((directory / 'native-capture.json').read_bytes())
    require(receipt['canonical_result_sha256'] == sha(encoded(result)), 'Native capture result digest differs')
    require(result['version'] == JULIA_VERSION, 'Captured Julia version differs')
    require(receipt['tool_sha256'] == sha((Path(root) / 'tools/julia_source_tree.jl').read_bytes()), 'Captured Julia tree exporter differs')
    require(receipt['official_archive_sha256'] == JULIA_ARCHIVE_SHA, 'Captured Julia distribution differs')
    require(not result['input_evaluation'] and not result['macro_expansion'] and not result['lowering'], 'Unsafe native capture mode')
    by_input = {row['input']: row for row in result['sources']}
    manifest = julia_input_manifest(data)
    require(set(by_input) == {row['input'] for row in manifest.values()}, 'Native captures do not cover exact expected inputs')
    for row in manifest.values():
        require(by_input[row['input']]['source_sha256'] == row['sha256'], 'Native capture source binding differs')
    return result, receipt


def fixtures(data, native):
    rows = []
    for name, compact, expanded, expected in PYTHON_FIXTURE_PAIRS:
        left, right = python_units(compact), python_units(expanded)
        require(left['logical_loc'] == right['logical_loc'] == expected, 'Python normalization fixture differs: ' + name)
        rows.append(dict(id='python:' + name, language='python', compact=compact, expanded=expanded,
            compact_units=left['logical_loc'], expanded_units=right['logical_loc'], expected_units=expected,
            native_accepted=True, passed=True, native_ast_equivalent=left['native_ast_sha256'] == right['native_ast_sha256']))
    native_rows = {row['input']: row for row in native['sources']}
    manifest = julia_input_manifest(data)
    pairs = [('semicolon-packing', 'semicolon-packed', 'semicolon-expanded', 2),
             ('matrix-literal-wrapping', 'matrix-packed', 'matrix-wrapped', 1),
             ('loop-header-and-body', 'loop-packed', 'loop-expanded', 3)]
    for name, a, b, expected in pairs:
        left = julia_units(JULIA_FIXTURES[a], native_rows[manifest['fixture:' + a]['input']])
        right = julia_units(JULIA_FIXTURES[b], native_rows[manifest['fixture:' + b]['input']])
        require(left['logical_loc'] == right['logical_loc'] == expected, 'Julia normalization fixture differs: ' + name)
        rows.append(dict(id='julia:' + name, language='julia', compact=JULIA_FIXTURES[a], expanded=JULIA_FIXTURES[b],
            compact_units=left['logical_loc'], expanded_units=right['logical_loc'], expected_units=expected,
            native_accepted=True, passed=True))
    for name, expected in [('keyword-semicolon', 1), ('literal-punctuation', 1), ('expression-function', 1),
                           ('block-function', 3), ('nested-block', 3), ('quoted-code', 1), ('macro-block', 2)]:
        result = julia_units(JULIA_FIXTURES[name], native_rows[manifest['fixture:' + name]['input']])
        require(result['logical_loc'] == expected, 'Julia fixture differs: ' + name)
        rows.append(dict(id='julia:' + name, language='julia', source=JULIA_FIXTURES[name],
            logical_units=result['logical_loc'], expected_units=expected, native_accepted=True, passed=True))
    invalid = native_rows[manifest['fixture:invalid']['input']]
    require(invalid['accepted'] is False, 'Invalid Julia fixture unexpectedly accepted')
    rows.append(dict(id='julia:invalid-syntax', language='julia', source=JULIA_FIXTURES['invalid'],
                     native_accepted=False, expected_rejection=True, passed=True))
    for key, old, new in JULIA_VARIANTS:
        left = manifest[key]; right = manifest['variant:' + key]
        a = julia_units(left['text'], native_rows[left['input']])
        b = julia_units(right['text'], native_rows[right['input']])
        require(a['logical_loc'] == b['logical_loc'], 'Real Julia packing invariance failed: ' + key)
        rows.append(dict(id='real-source-packing:' + key, language='julia', program=key,
            original_sha256=left['sha256'], variant_sha256=right['sha256'], old=old, new=new,
            original_units=a['logical_loc'], variant_units=b['logical_loc'], native_accepted=True, passed=True))
    key = 'pidigits:pidigits-julia-3'
    item = manifest[key]
    result = julia_units(item['text'], native_rows[item['input']])
    tuple_owners = [owner for owner in result['owners'] if owner['line'] == 42 and owner['units']]
    require(len(tuple_owners) == 1 and tuple_owners[0]['kind'] == '=' and tuple_owners[0]['units'] == 1,
            'Real Julia destructuring must remain one initialized binding')
    rows.append(dict(id='julia:real-tuple-binding', language='julia', program=key,
        source_sha256=item['full_source_sha256'], line=42,
        source=item['text'].splitlines()[41], expected_units=1, logical_units=1,
        native_accepted=True, passed=True))
    return rows


def priority_audit(data, results):
    catalog = program_catalog(data)
    findings = []
    def finding(identity, start, end, issue, family, evidence):
        row = catalog[identity]
        digest = row['files'][0]
        source = data['files'][digest]['code']
        lines = source.splitlines()
        findings.append(dict(program=identity, language=row['language'], source_sha256=digest,
            lines=dict(start=start, end=end), source_text='\n'.join(lines[start - 1:end]),
            retained_loc=row['loc'], retained_metric=row.get('loc_metric', 'unspecified-legacy'),
            rule_family=family, inconsistency=issue, acceptance_evidence=evidence))
    finding('spectralnorm:spectralnorm-python3-8', 25, 25,
        'Three native independent statements share one retained physical source row.',
        'legacy-significant-physical-lines', 'Current CPython AST acceptance and three statement owners on this exact row.')
    finding('spectralnorm:spectralnorm-python3-8', 34, 34,
        'Native for header plus two AugAssign statements share a physical row; logical owners remain three after unpacking.',
        'legacy-significant-physical-lines', 'Current CPython AST acceptance, owner ranges and source-preserving full-program variants.')
    finding('fannkuchredux:fannkuchredux-julia-1', 14, 14,
        'One physical row contains independent sign binding plus maxflips/sum chained assignments; native ownership separates written bindings.',
        'legacy-significant-physical-lines', 'Julia 1.13.1 native full-source acceptance; original and semicolon-expanded variants have equal new counts.')
    finding('regexredux:regexredux-julia-3', 18, 28,
        'The multiline variants tuple is one native constant binding, not one logical unit per literal row.',
        'legacy-significant-physical-lines', 'Julia 1.13.1 native const/assignment/tuple source ranges; row layout is zero additional units.')
    # Source-bound follow-up cases in other priority families are findings, not
    # new parser certifications or speculative replacement totals.
    mech = next((k for k, r in catalog.items() if r['language'] == 'mech' and r['benchmark'] == 'nbody'
                 and '[0 4.841' in data['files'][r['files'][0]]['code']), None)
    if mech:
        text = data['files'][catalog[mech]['files'][0]]['code'].splitlines()
        start = next(n for n, line in enumerate(text, 1) if '~x :=' in line)
        finding(mech, start, start + 2,
            'One written matrix binding spans three source rows. Physical-row rules retain layout cost; target owner policy charges one expression.',
            'legacy-significant-physical-lines', 'Exact retained scored source. Fresh native Mech owner qualification is outside this Python/Julia packet.')
    for language in ('fsharp', 'kotlin', 'typescript', 'elixir', 'apl'):
        candidates = [(k, r) for k, r in catalog.items() if r['language'] == language]
        if not candidates:
            continue
        if language == 'fsharp':
            chosen = None
            for key, row in candidates:
                lines = data['files'][row['files'][0]]['code'].splitlines()
                for n, line in enumerate(lines, 1):
                    depth = line.count('[|') - line.count('|]')
                    if depth <= 0:
                        continue
                    end = n
                    while depth and end < len(lines):
                        depth += lines[end].count('[|') - lines[end].count('|]')
                        end += 1
                    if not depth and end > n:
                        chosen = (key, n, end)
                        break
                if chosen:
                    break
            if not chosen:
                continue
            key, start, end = chosen
            finding(key, start, end,
                'Retained cohort masks structural array semicolons but starts from physical significant rows; literal wrapping and owner/close choices still require native qualification.',
                'lexical-cohort-plus-packed-statement-heuristics', 'Retained source and counter implementation; no fresh F# compiler/AST acceptance is claimed.')
        else:
            key, row = candidates[0]
            lines = data['files'][row['files'][0]]['code'].splitlines()
            marker = '∇' if language == 'apl' else '}' if language in ('kotlin', 'typescript') else 'end'
            closers = [n for n, line in enumerate(lines, 1) if line.strip() == marker]
            if closers:
                finding(key, closers[0], closers[0],
                    'Written closing syntax is retained by this cohort owner policy; the new Python/Julia policy adds zero units for closers. These cannot be relabeled as the same rule version.',
                    'native-or-exact-source-owners-with-written-closers',
                    'Existing retained native/source-specific qualification; fresh counts in this packet cover Python/Julia only.')
    return findings


def qualify(data, catalog_raw, native, receipt, root=ROOT):
    before = copy.deepcopy(data)
    native_rows = {row['input']: row for row in native['sources']}
    manifest = julia_input_manifest(data)
    catalog = program_catalog(data)
    profiles = {}
    source_cache = {}
    for identity, item in application_inputs(data).items():
        key, language, text = item['program'], item['language'], item['text']
        if language == 'python':
            result = python_units(text)
            # Native unparse supplies a second, source-accepted full-program
            # layout. Exact AST equivalence is checked, not presumed.
            parsed = ast.parse(text, type_comments=True)
            variant = ast.unparse(parsed) + '\n'
            alternate = python_units(variant)
            require(result['native_ast_sha256'] == alternate['native_ast_sha256'], 'Native Python unparse changed AST')
            require(result['logical_loc'] == alternate['logical_loc'], 'Python full-source layout changed logical units')
            result['native_layout_variant'] = dict(tool='CPython ast.unparse',
                source_sha256=sha(variant.encode('utf-8')), accepted=True,
                logical_loc=alternate['logical_loc'], ast_equivalent=True)
        else:
            result = julia_units(text, native_rows[manifest[identity]['input']])
        source_id = item['application_projection_sha256']
        source_cache[source_id] = dict(result, full_source_sha256=item['full_source_sha256'],
                                      support_line_ranges=item['support_line_ranges'])
        row = catalog[key]
        output = profiles.setdefault(key, dict(language=language, benchmark=row['benchmark'],
            authorship_kind=row.get('authorship', {}).get('kind'), selected_for_chart=key in data['programs'],
            retained_loc=row['loc'], retained_metric=row.get('loc_metric', 'unspecified-legacy'),
            logical_loc=0, policy=POLICY, status='qualified-exact-source-native-owners', sources=[]))
        output['logical_loc'] += result['logical_loc']
        output['sources'].append(source_id)
    require(data == before, 'Qualification mutated canonical catalog')
    root = Path(root)
    paths = ['tools/logical_source_units.py', 'tools/julia_source_tree.jl']
    priority_counters = ['archive/workloads/nbody/run.py',
        'archive/comparisons/remaining-languages-comparison/20261011/metrics_final.py',
        'archive/comparisons/array-comparison/all-20261009/audit_sources.py',
        'tools/qualification/kotlin_source_units_v2.py', 'tools/qualification/typescript_source_units.py',
        'tools/qualification/elixir_source_units.py', 'tools/qualification/apl_retained_source_units.py',
        'tools/qualification/r_retained_source_units.py']
    parser_paths = [Path(ast.__file__), Path(tokenize.__file__), Path(sys.executable).resolve()]
    report = dict(schema='benchmark-source-normalization.v2', policy=rule_definition(),
        catalog_sha256=sha(catalog_raw), canonical_fields_changed=False, source_bytes_changed=False,
        benchmark_executions=0, input_evaluation=False, macro_expansion=False, lowering=False,
        tool_pins={path: sha((root / path).read_bytes()) for path in paths},
        priority_counter_pins={path: sha((root / path).read_bytes()) for path in priority_counters},
        python_parser=dict(implementation=sys.implementation.name, version=sys.version,
            pins={str(path): sha(path.read_bytes()) for path in parser_paths}),
        julia_parser=dict(version=native['version'], api=native['parser'],
            native_capture_sha256=sha((root / PACKET / 'native-trees.json.gz').read_bytes()),
            receipt_sha256=sha((root / PACKET / 'native-capture.json').read_bytes()),
            exporter_sha256=receipt['tool_sha256'], official_archive_sha256=JULIA_ARCHIVE_SHA),
        coverage=dict(profiles=len(profiles), unique_application_projections=len(source_cache),
            profiles_by_language=dict(sorted(collections.Counter(row['language'] for row in profiles.values()).items())),
            profiles_by_authorship=dict(sorted(collections.Counter(row['authorship_kind'] or 'unknown' for row in profiles.values()).items())),
            logical_counts_changed=sum(row['logical_loc'] != row['retained_loc'] for row in profiles.values()),
            unowned_significant_tokens=sum(row['coverage']['unowned_significant_tokens'] for row in source_cache.values()),
            complete_for_languages=list(LANGUAGES), all_language_suite_complete=False),
        fixtures=fixtures(data, native), priority_rule_audit=priority_audit(data, profiles),
        profiles=profiles, sources=source_cache)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-julia', action='store_true', help='Start one bounded parse-only native capture process.')
    parser.add_argument('--julia', type=Path, help='Required with --refresh-julia; exact Julia 1.13.1 binary.')
    parser.add_argument('--check', action='store_true', help='Replay captured native trees and compare qualification without writing.')
    args = parser.parse_args()
    raw = (ROOT / 'data/benchmarks.json').read_bytes()
    data = json.loads(raw)
    if args.refresh_julia:
        require(args.julia is not None and not args.check, 'Refresh requires --julia and cannot be combined with --check')
        native, receipt = native_capture(data, args.julia)
    else:
        native, receipt = load_native(data)
    report = qualify(data, raw, native, receipt)
    output = pretty(report)
    path = ROOT / PACKET / 'qualification.json'
    if args.check:
        require(path.read_bytes() == output, 'Source-normalization qualification differs; replay under the pinned Python/parser environment')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(output)
    print(json.dumps(dict(status='verified' if args.check else 'qualified', **report['coverage'], benchmark_executions=0), sort_keys=True))


if __name__ == '__main__':
    main()
