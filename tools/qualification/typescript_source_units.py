#!/usr/bin/env python3
"""Candidate canonical units from retained TypeScript 7.0.2 native ASTs.

No parser, compiler, Node process or source evaluation runs here. Native kinds,
roles and exact ranges own executable blocks, declarations and literal segments.
Only comment delimiters outside native literals are read from source text.
Unknown ownership, directives and unsupported syntax produce null counts.
"""
import argparse
from bisect import bisect_right
import fcntl
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/typescript/source-units-v1'
NATIVE = ROOT/'experiments/typescript/native-stage-v1'
READER = ROOT/'tools/qualification/typescript_native_stage.py'
READER_SHA = '4a6cc2484c2e967bd84496958e0b22ac205600a403e0ca41310505c3fc998175'
ENUM = ROOT/'experiments/typescript/toolchain-v1/.build/packages-v1/node_modules/typescript/dist/enums/syntaxKind.js'
ENUM_SHA = 'f5cc780058a86f406358654944bdc0b060eaf0790c0fc81fa7eaa430c2bead07'
PLAN_SHA = '520b14aea813379f036053ce7bc6e7b21ad016775407536ee3195703444412c4'
REPORT_SHA = 'ec6fb9979e5de31cd8496f01e338fef80f322f118def9923d61b8c3b5ca9e83b'
TERMINAL_SHA = '2abf7814b6063b15561af165bed377d77f6616597d555ec7f4d967c421372038'
REVIEW_SHA = 'f5c253d1abe24c3c0f409a3ca1668b1662f9377742976160c7e26392c6dcffd5'
FIXTURES = ROOT/'experiments/typescript/source-counts-v1/fixtures.json'
FIXTURES_SHA = '1bb37feb2effab6984fbcf2895677c2ff79ea69ff01d2de39a9b4d3a360eb867'
RULE = 'canonical-source-units-20261012-approved-rule-v2'
LITERALS = {'StringLiteral','RegularExpressionLiteral','NoSubstitutionTemplateLiteral',
            'TemplateHead','TemplateMiddle','TemplateTail'}
ASSIGNMENTS = {'EqualsToken','PlusEqualsToken','MinusEqualsToken','AsteriskEqualsToken',
               'SlashEqualsToken','PercentEqualsToken','AsteriskAsteriskEqualsToken',
               'LessThanLessThanEqualsToken','GreaterThanGreaterThanEqualsToken',
               'GreaterThanGreaterThanGreaterThanEqualsToken','AmpersandEqualsToken',
               'BarEqualsToken','CaretEqualsToken','AmpersandAmpersandEqualsToken',
               'BarBarEqualsToken','QuestionQuestionEqualsToken'}
UNSUPPORTED = {'TypeLiteral','MappedType','InterfaceDeclaration','DeclareKeyword',
               'Decorator','ModuleDeclaration','ModuleBlock','ConditionalType',
               'ImportType','ExportDeclaration','ExportAssignment','EnumDeclaration',
               'SwitchStatement','CaseBlock','CaseClause','DefaultClause','DoStatement',
               'LabeledStatement','WithStatement','ClassExpression','GetAccessor',
               'SetAccessor','PropertySignature','IndexSignature','MethodSignature'}
FUNCTIONS = {'FunctionDeclaration','MethodDeclaration','Constructor','FunctionExpression'}
LOOPS = {'ForStatement','ForInStatement','ForOfStatement','WhileStatement'}
SCALARS = set('''Identifier NumericLiteral BigIntLiteral NullKeyword TrueKeyword FalseKeyword
ThisKeyword NumberKeyword StringKeyword BigIntKeyword BooleanKeyword VoidKeyword UnknownKeyword
ReadonlyKeyword PrivateKeyword PublicKeyword ProtectedKeyword AsyncKeyword AwaitKeyword
StaticKeyword AbstractKeyword ExportKeyword DefaultKeyword
BinaryExpression CallExpression NewExpression ElementAccessExpression PropertyAccessExpression
ConditionalExpression PrefixUnaryExpression PostfixUnaryExpression ParenthesizedExpression
ArrayLiteralExpression ObjectLiteralExpression PropertyAssignment ShorthandPropertyAssignment
ArrayBindingPattern ObjectBindingPattern BindingElement
ArrayType LiteralType TupleType NamedTupleMember TypeReference TypeParameter UnionType
IntersectionType ParenthesizedType TypeOperator
Parameter VariableDeclaration VariableDeclarationList TemplateExpression TemplateSpan
ImportClause ImportSpecifier NamedImports NamespaceImport ExternalModuleReference
EndOfFile'''.split()) | LITERALS
TOKENS = set('''AmpersandAmpersandToken AmpersandToken AsteriskToken AsteriskAsteriskToken
BarBarToken BarToken CaretToken ColonToken CommaToken EqualsEqualsEqualsToken EqualsEqualsToken
EqualsGreaterThanToken ExclamationEqualsEqualsToken ExclamationEqualsToken GreaterThanEqualsToken
GreaterThanToken LessThanEqualsToken LessThanLessThanToken LessThanToken MinusToken PercentToken
PlusToken QuestionQuestionToken QuestionToken SlashToken InstanceOfKeyword InKeyword
QuestionDotToken DotDotDotToken ExclamationToken TildeToken'''.split()) | ASSIGNMENTS
STATEMENTS = {'SourceFile','Block','VariableStatement','ExpressionStatement','ReturnStatement',
              'ThrowStatement','BreakStatement','ContinueStatement','ClassDeclaration',
              'PropertyDeclaration','TypeAliasDeclaration','ImportDeclaration',
              'ImportEqualsDeclaration','IfStatement','TryStatement','CatchClause','ArrowFunction'} | FUNCTIONS | LOOPS
FALSE_FLAGS = dict(canonical_loc_qualified=False,formatted_loc=None,
                   formatted_loc_qualified=False,chart_admission=False)


class CountError(ValueError): pass


def require(value,message):
    if not value: raise CountError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def substantive(text,punctuation=''):
    return any(not char.isspace() and char not in punctuation for char in text)


@lru_cache(maxsize=1)
def reader_module():
    raw=READER.read_bytes();require(digest(raw)==READER_SHA,'Frozen native validator changed')
    spec=importlib.util.spec_from_file_location('typescript_units_validator',READER)
    module=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(READER),'exec'),module.__dict__)
    return module


def validator(): return reader_module().validate_ast


@lru_cache(maxsize=1)
def native_kinds():
    raw=ENUM.read_bytes();require(digest(raw)==ENUM_SHA,'Retained SyntaxKind definition changed')
    entries=re.findall(r'SyntaxKind\[SyntaxKind\["([A-Za-z0-9_]+)"\] = ([0-9]+)\] = "\1";',raw.decode())
    require(len(entries)>300 and len({name for name,_ in entries})==len(entries),'Unexpected native enum format')
    return {name:int(value) for name,value in entries}


class Tree:
    def __init__(self,source,evidence):
        require(evidence['schema']=='typescript-native-ast-source-v1'
                and evidence['parser']=='TypeScript 7.0.2 native API','Wrong native AST schema/parser')
        validator()(evidence,dict(id=evidence['id'],source_path=evidence['source_path'],
            sha256=digest(source.encode()),expected_parse='error' if evidence['parse_diagnostics'] else 'ok'),source.encode())
        require(not evidence['parse_diagnostics'],'Native parser rejected source')
        self.source=source;self.starts=[0]+[m.end() for m in re.finditer(r'\r\n|[\r\n\u2028\u2029]',source)]
        offsets={0:0};units=0
        for index,char in enumerate(source):
            units+=2 if ord(char)>0xffff else 1;offsets[units]=index+1
        kinds=native_kinds();self.nodes=[];self.diagnostics=[]
        for raw in evidence['nodes']:
            require(kinds.get(raw['kind'])==raw['native_kind'],'Native kind name/value differs')
            require(all(raw[key] in offsets for key in ('start_utf16','end_utf16','full_start_utf16')),
                    'Native boundary splits a UTF-16 surrogate pair')
            node=dict(raw,start=offsets[raw['start_utf16']],end=offsets[raw['end_utf16']],
                      full_start=offsets[raw['full_start_utf16']])
            self.nodes.append(node)
            if node['kind'] not in SCALARS|TOKENS|STATEMENTS or node['kind'] in UNSUPPORTED:
                self.issue('unsupported-native-owner',node['start'],node['kind'])
        for node in self.nodes:
            children=self.children(node)
            require(all(a['end']<=b['start'] for a,b in zip(children,children[1:])),
                    'Native sibling source ranges overlap or are unordered')
        self.cleaned=list(source);self.literals=[];self.comments=[]
        for node in self.nodes:
            if node['kind'] in LITERALS:
                require(not node['children'],'Native literal segment unexpectedly owns children')
                self.mask(node['start'],node['end'],'S')
                self.literals.append(dict(start=node['start'],end=node['end'],native_node=node['id'],kind=node['kind']))
        self.comments_only()
        self.cleaned=''.join(self.cleaned)
        self.pairs={};stack=[]
        for index,char in enumerate(self.cleaned):
            if char in '([{':stack.append((char,index))
            elif char in ')]}':
                require(stack and stack[-1][0]=={')':'(',']':'[','}':'{'}[char], 'Unowned or unbalanced delimiter')
                _,opening=stack.pop();self.pairs[opening]=index
            elif char in '\'"`':
                self.issue('unowned-string-delimiter',index)
        require(not stack,'Unclosed delimiter outside native literal/comment spans')
        for node in self.nodes:
            if node['kind']=='TemplateExpression' and any(n['kind']=='Block' or self.assignment(n)
                    or n['kind'] in ('PostfixUnaryExpression','PrefixUnaryExpression') and n.get('operator_kind') in ('PlusPlusToken','MinusMinusToken')
                    for n in self.descendants(node)):
                self.issue('interpolation-with-independent-work-needs-review',node['start'])

    def children(self,node): return [self.nodes[i] for i in node['children']]

    def descendants(self,node):
        for child in self.children(node):
            yield child
            yield from self.descendants(child)

    def role(self,node,name,optional=False):
        value=node['roles'].get(name)
        require(type(value) is int or optional and value is None,'Missing/ambiguous native '+name+' role')
        return self.nodes[value] if value is not None else None

    def roles(self,node,name):
        value=node['roles'].get(name,[]);require(type(value) is list,'Expected native '+name+' role list')
        return [self.nodes[i] for i in value]

    def issue(self,kind,offset,detail=None):
        self.diagnostics.append(dict(kind=kind,offset=offset,**({'detail':detail} if detail else {})))

    def line(self,offset):return bisect_right(self.starts,offset)

    def rows(self,text):
        require(len(text)==len(self.source),'Source-preserving projection changed length')
        return [text[a:b] for a,b in zip(self.starts,self.starts[1:]+[len(text)])]

    def mask(self,start,end,value):
        for index in range(start,end):
            if not self.source[index].isspace():self.cleaned[index]=value

    def comments_only(self):
        index=0
        while index<len(self.source):
            pair=''.join(self.cleaned[index:index+2])
            if pair not in ('//','/*'):index+=1;continue
            start=index
            if pair=='//':
                end=index+2
                while end<len(self.source) and self.source[end] not in '\r\n\u2028\u2029':end+=1
            else:
                end=self.source.find('*/',index+2);require(end>=0,'Unterminated comment outside native literal');end+=2
            require(not any(n['start']<end and start<n['end'] for n in self.nodes if not n['children'] and n['end']>n['start']),
                    'Comment range intersects a native semantic leaf')
            text=self.source[start:end]
            if re.search(r'@(?:ts-(?:ignore|expect-error|check|nocheck)|jsx\w*)\b|^///\s*<reference\b|[#@]\s*source(?:Mapping)?URL\s*=',text):
                self.issue('compiler-directive-needs-review',start)
            self.mask(start,end,' ');self.comments.append(dict(start=start,end=end));index=end

    def assignment(self,node):
        if node['kind']!='BinaryExpression':return None
        operator=self.role(node,'operatorToken')
        return operator if operator['kind'] in ASSIGNMENTS else None


class Owners:
    def __init__(self,tree):
        self.tree=tree;self.events=[];self.regions=[];self.boundaries=set();self.declarations=[];self.assignments=[]
        self.blocks=set();self.braces=set();self.parameter_properties=[];self.diagnostics=list(tree.diagnostics)
        self.coverage=[]
        self.sequence(tree.nodes[0]);self.finish()

    def issue(self,kind,node,detail=None):
        self.diagnostics.append(dict(kind=kind,offset=node['start'] if isinstance(node,dict) else node,
                                     **({'detail':detail} if detail else {})))

    def event(self,kind,start,end,units,node,**extra):
        while start<end and self.tree.cleaned[start].isspace():start+=1
        require(0<=start<end<=len(self.tree.source),'Empty or escaping owner event')
        self.events.append(dict(kind=kind,start=start,end=end,units=units,native_node=node['id'],**extra))

    def sequence(self,node):
        for child in self.tree.roles(node,'statements'):self.statement(child)

    def block(self,node,start=None,owner=None,units=1):
        require(node['kind']=='Block','Native executable body must be Block')
        a,b=node['start'],node['end']-1
        require(self.tree.cleaned[a]=='{' and self.tree.cleaned[b]=='}' and self.tree.pairs.get(a)==b,
                'Native Block does not own exact written delimiters')
        self.blocks.add(node['id']);self.braces.update((a,b));owner=owner or node
        self.event('header' if start is not None else 'open',a if start is None else start,a+1,0 if start is None else units,owner)
        self.event('close',b,b+1,1,owner);self.sequence(node)

    def body(self,body,start,owner):
        if body['kind']=='Block':self.block(body,start,owner)
        else:self.event('header',start,body['start'],1,owner);self.statement(body)

    def statement(self,node,start=None):
        t=self.tree;kind=node['kind'];start=node['start'] if start is None else start
        self.boundaries.update((start,node['end']))
        if kind=='Block':self.block(node);return
        if kind in ('ImportDeclaration','ImportEqualsDeclaration','TypeAliasDeclaration'):
            self.event('declaration',start,node['end'],1,node);return
        if kind=='ClassDeclaration':
            close=node['end']-1
            openings=[a for a,b in t.pairs.items() if b==close and t.cleaned[a]=='{']
            require(len(openings)==1,'Class body delimiters are ambiguous');opening=openings[0]
            self.braces.update((opening,close));self.event('header',start,opening+1,1,node)
            self.event('close',close,close+1,1,node)
            for member in t.roles(node,'members'):self.statement(member)
            return
        if kind in FUNCTIONS:
            body=t.role(node,'body',True)
            if body is None:self.issue('bodyless-function-needs-review',node);return
            properties=[]
            if kind=='Constructor':
                for param in t.roles(node,'parameters'):
                    modifiers=t.roles(param,'modifiers')
                    if any(m['kind'] in ('ReadonlyKeyword','PublicKeyword','PrivateKeyword','ProtectedKeyword') for m in modifiers):
                        properties.append(param['id']);self.parameter_properties.append(dict(native_node=param['id'],start=param['start'],end=param['end'],units=1))
            self.block(body,start,node,1+len(properties));return
        if kind in LOOPS:
            self.body(t.role(node,'statement'),start,node);return
        if kind=='IfStatement':
            body=t.role(node,'thenStatement');self.body(body,start,node)
            otherwise=t.role(node,'elseStatement',True)
            if otherwise:
                prefix=body['end'];gap=t.cleaned[prefix:otherwise['start']].strip()
                require(gap=='else','Native else boundary differs')
                if otherwise['kind']=='IfStatement':self.statement(otherwise,prefix)
                else:self.body(otherwise,prefix,node)
            return
        if kind=='TryStatement':
            body=t.role(node,'tryBlock');self.block(body,start,node);last=body['end']
            catch=t.role(node,'catchClause',True)
            if catch:self.block(t.role(catch,'block'),catch['start'],catch);last=catch['end']
            final=t.role(node,'finallyBlock',True)
            if final:
                require(t.cleaned[last:final['start']].strip()=='finally','Native finally boundary differs')
                self.block(final,last,node)
            return
        if kind=='VariableStatement':
            declarations=t.roles(t.role(node,'declarationList'),'declarations')
            require(declarations,'Variable statement has no declaration')
            for index,decl in enumerate(declarations):
                begin=start if index==0 else decl['start']
                self.boundaries.add(begin);self.declarations.append(decl['start'])
                self.expression(decl,begin,decl['end'])
            return
        if kind in ('PropertyDeclaration','ExpressionStatement','ReturnStatement','ThrowStatement','BreakStatement','ContinueStatement'):
            if kind=='PropertyDeclaration':self.declarations.append(node['start'])
            self.expression(node,start,node['end']);return
        self.issue('unsupported-statement-owner',node,kind)

    def expression(self,node,start,end):
        t=self.tree;region=dict(start=start,end=end,native_node=node['id']);self.regions.append(region)
        callbacks=[]
        def inspect(current,data=False):
            kind=current['kind']
            if kind in ('ArrowFunction','FunctionExpression') and t.role(current,'body',True) and t.role(current,'body')['kind']=='Block':
                callbacks.append(current);return
            data=data or kind in ('ArrayLiteralExpression','ObjectLiteralExpression','ArrayBindingPattern','ObjectBindingPattern')
            assignment=t.assignment(current)
            if assignment and not data:self.assignments.append(assignment['start'])
            for child in t.children(current):inspect(child,data)
        inspect(node)
        cursor=start
        for index,callback in enumerate(callbacks):
            body=t.role(callback,'body')
            prefix=t.cleaned[cursor:callback['start']]
            if index and substantive(prefix,',()[];'):
                self.issue('callback-composition-needs-review',callback)
            header_start=cursor if index==0 else callback['start']
            if index and prefix.strip():self.event('structural-suffix',cursor,callback['start'],0,node)
            prefix_units=sum(header_start<=p<body['start'] for p in self.assignments+self.declarations)
            self.block(body,header_start,callback,max(1,prefix_units));cursor=body['end']
        if callbacks:
            suffix=t.cleaned[cursor:end]
            if substantive(suffix,'()[],;'):
                self.issue('callback-continuation-needs-review',cursor)
            elif suffix.strip():self.event('structural-suffix',cursor,end,0,node)

    def finish(self):
        t=self.tree
        for node in t.nodes:
            if node['kind']=='Block' and node['id'] not in self.blocks:self.issue('unowned-executable-block',node)
            if node['kind'] in ('ObjectLiteralExpression','ObjectBindingPattern','NamedImports'):
                a,b=node['start'],node['end']-1
                if t.cleaned[a]=='{' and t.pairs.get(a)==b:self.braces.update((a,b))
        for index,char in enumerate(t.cleaned):
            if char in '{}' and index not in self.braces and not any(e['start']<=index<e['end'] for e in self.events):
                self.issue('unowned-written-brace',index)
        self.events.sort(key=lambda e:(e['start'],e['end']))
        for a,b in zip(self.events,self.events[1:]):
            if a['end']>b['start']:self.issue('overlapping-owner-events',b['start'])
        statements=t.roles(t.nodes[0],'statements');cursor=0
        for node in statements:
            if t.cleaned[cursor:node['start']].strip():self.issue('unowned-top-level-source',cursor)
            cursor=node['end']
        if t.cleaned[cursor:].strip():self.issue('unowned-top-level-source',cursor)
        # Every nonwhitespace character must have an explicit source owner.
        # Comments and literal segments come first; the native expression owner
        # supplies physical remainder without flattening data or expression rows.
        intervals=[dict(item,coverage='comment',native_node=None) for item in t.comments]
        intervals += [dict(item,coverage='native-literal') for item in t.literals]
        intervals += [dict(item,coverage='canonical-event') for item in self.events]
        intervals += [dict(item,coverage='native-expression') for item in sorted(self.regions,key=lambda r:r['end']-r['start'])]
        for index,char in enumerate(t.source):
            if char.isspace():key=('whitespace',None)
            else:
                owner=next((r for r in intervals if r['start']<=index<r['end']),None)
                if owner:key=(owner['coverage'],owner.get('native_node'))
                elif char in ',;':key=('structural-separator',None)
                else:key=('unowned',None);self.issue('unowned-source-character',index,char)
            if self.coverage and self.coverage[-1]['end']==index and (self.coverage[-1]['kind'],self.coverage[-1]['native_node'])==key:
                self.coverage[-1]['end']=index+1
            else:self.coverage.append(dict(start=index,end=index+1,kind=key[0],native_node=key[1]))


def account(tree,owners):
    body=list(tree.cleaned);by_line={};owned=set()
    for event in owners.events:
        for index in range(event['start'],event['end']):
            if not body[index].isspace():body[index]=' '
        line=tree.line(event['start']);by_line.setdefault(line,[]).append(event)
        owned.update(range(line,tree.line(event['end']-1)+1))
    body=''.join(body);rows=tree.rows(body)
    physical=[i for i,row in enumerate(tree.rows(tree.cleaned),1) if row.strip()]
    boundaries=owners.boundaries|{p for e in owners.events for p in (e['start'],e['end'])}
    total=0;details=[]
    for line in physical:
        offset=tree.starts[line-1];row=rows[line-1]
        bounds=sorted({0,len(row),*(p-offset for p in boundaries if offset<p<offset+len(row))})
        pieces=[]
        for a,b in zip(bounds,bounds[1:]):
            if not substantive(row[a:b],'{};,'):continue
            assignments=[p for p in owners.assignments if offset+a<=p<offset+b and body[p]!=' ']
            declarations=[p for p in owners.declarations if offset+a<=p<offset+b and body[p]!=' ']
            units=max(1,len(assignments)+len(declarations))
            pieces.append(dict(start=offset+a,end=offset+b,units=units,assignments=assignments,declarations=declarations))
        events=by_line.get(line,[]);units=sum(e['units'] for e in events)+sum(p['units'] for p in pieces)
        if not units and line not in owned:units=1
        total+=units;details.append(dict(line=line,units=units,events=events,remainder=pieces))
    return len(physical),total,details


def count_source(source,evidence):
    tree=owners=None;physical=candidate=None;details=[];diagnostics=[]
    try:
        if evidence.get('parse_diagnostics'):
            validator()(evidence,dict(id=evidence['id'],source_path=evidence['source_path'],sha256=digest(source.encode()),expected_parse='error'),source.encode())
            return dict(rule_version=RULE,status='native-parser-rejection',physical_loc=None,normalized_loc=None,
                        diagnostics=evidence['parse_diagnostics'],**FALSE_FLAGS)
        tree=Tree(source,evidence);owners=Owners(tree);physical,candidate,details=account(tree,owners);diagnostics=owners.diagnostics
    except (AssertionError,CountError,KeyError,IndexError,TypeError,UnicodeError,RecursionError) as error:
        diagnostics=[dict(kind='native-owner-input-rejected',offset=0,detail=str(error))]
    for issue in diagnostics:
        line=tree.line(issue['offset']) if tree else 1
        issue.update(line=line,column=issue['offset']-(tree.starts[line-1] if tree else 0)+1)
    return dict(rule_version=RULE,grammar='typescript-7.0.2-native-owner-projection-v1',language='typescript',
        source_sha256=digest(source.encode()),status='needs-review' if diagnostics else 'candidate-native-owner-pass',
        physical_loc=physical,normalized_loc=None if diagnostics else candidate,candidate_normalized_loc=candidate,
        diagnostics=diagnostics,canonical_events=owners.events if owners else [],
        parameter_properties=owners.parameter_properties if owners else [],line_accounting=details,
        source_coverage=owners.coverage if owners else [],complete_source_owner_coverage=bool(owners) and not any(
            item['kind']=='unowned' for item in owners.coverage),
        comment_spans=tree.comments if tree else [],native_literal_spans=tree.literals if tree else [],
        ownership_offset_units='Python Unicode character offsets into exact original source',**FALSE_FLAGS)


def document(path,expected):
    raw=path.read_bytes();require(digest(raw)==expected,'Pinned metadata changed: '+str(path))
    return json.loads(raw)


def write_new(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def replay(output):
    """Saved AST/source replay only. The CLI holds the common mutex throughout."""
    require(output.is_absolute() and output.resolve()==output and output.is_relative_to(PACKET)
            and output!=PACKET and not output.exists(),'Fresh physical output under this packet required')
    c=reader_module();directory=NATIVE/'run-v1'
    pins={NATIVE/'plan-v1.json':PLAN_SHA,directory/'report.json':REPORT_SHA,
          directory/'terminal.json':TERMINAL_SHA,NATIVE/'independent-native-review-v1.json':REVIEW_SHA,
          FIXTURES:FIXTURES_SHA,READER:READER_SHA,ENUM:ENUM_SHA}
    plan=document(NATIVE/'plan-v1.json',PLAN_SHA);report=document(directory/'report.json',REPORT_SHA)
    terminal=document(directory/'terminal.json',TERMINAL_SHA)
    reviewed=document(NATIVE/'independent-native-review-v1.json',REVIEW_SHA);fixtures=document(FIXTURES,FIXTURES_SHA)
    require(report['status']==terminal['status']=='compile-and-AST-captures-recorded-awaiting-independent-review'
            and terminal['report_sha256']==REPORT_SHA and report['plan_sha256']==PLAN_SHA
            and report['integrity_errors']==report['process_receipt_errors']==terminal['integrity_errors']==[]
            and report['active'] is None and terminal['common_mutex_held'] is True
            and reviewed['status']=='actual-compile-and-AST-artifact-replay-passed'
            and reviewed['report']['sha256']==REPORT_SHA and reviewed['terminal']['sha256']==TERMINAL_SHA,
            'Actual native source receipt/review is not closed')
    inventory=c.inventory(directory,('terminal.json',))
    require(inventory==terminal['available_evidence'] and {k:v for k,v in inventory.items() if k!='report.json'}==report['artifacts'],
            'Actual source artifact closure changed')
    c.check_snapshot(report,directory,inventory)
    require(c.process_closure(report,directory)==[],'Actual native process ledger changed')
    require(plan['pins'][str(ENUM)]==ENUM_SHA,'Native SyntaxKind source not bound to reader toolchain')
    results={};source_bindings=[]
    for item in plan['inputs']:
        where=directory/'reader/evidence'/item['id'];source=(where/'source.ts').read_bytes()
        ast_raw=(where/'ast.json').read_bytes();evidence=json.loads(ast_raw)
        require(digest(source)==item['sha256'] and evidence['source_path']==item['source_path']
                and (bool(evidence['parse_diagnostics'])==(item['expected_parse']=='error')),'Native input/source expectation differs')
        require(Path(item['source_path']).read_bytes()==source,'Original source differs from native source copy')
        results[item['id']]=count_source(source.decode('utf-8'),evidence)
        source_bindings.append(dict(id=item['id'],role=item['role'],source_path=item['source_path'],source_sha256=item['sha256'],
            ast_path=str(where/'ast.json'),ast_sha256=digest(ast_raw),native_nodes=len(evidence['nodes'])))
    checks=[]
    for fixture in fixtures['fixtures']:
        result=results[fixture['id']];expected=fixture['expected_owner_status']
        if expected=='parse-rejection':passed=result['status']=='native-parser-rejection' and result['normalized_loc'] is None
        elif expected=='review':passed=result['status']=='needs-review' and result['normalized_loc'] is None and bool(result['diagnostics'])
        else:passed=result['status']=='candidate-native-owner-pass' and result['normalized_loc']==fixture['proposed_normalized_loc']
        if fixture.get('equivalent_to'):passed=passed and result['normalized_loc']==results[fixture['equivalent_to']]['normalized_loc']
        checks.append(dict(id=fixture['id'],expected=expected,expected_units=fixture['proposed_normalized_loc'],
                           actual_units=result['normalized_loc'],passed=bool(passed)))
    applications=[dict(id=item['id'],physical_loc=results[item['id']]['physical_loc'],
        candidate_canonical_loc=results[item['id']]['normalized_loc'],formatted_loc=None,
        diagnostics=results[item['id']]['diagnostics']) for item in plan['inputs'] if item['role']=='application']
    success=len(checks)==30 and all(c['passed'] for c in checks) and len(applications)==10 and all(
        type(a['candidate_canonical_loc']) is int for a in applications)
    require(c.inventory(directory,('terminal.json',))==inventory,'Native artifacts changed during source replay')
    for path,expected in pins.items():require(digest(path.read_bytes())==expected,'Source replay prerequisite changed')
    output.mkdir(parents=True,exist_ok=False)
    files={}
    for identity,value in results.items():
        path=output/(identity+'.json');write_new(path,value);files[path.name]=dict(bytes=path.stat().st_size,sha256=digest(path.read_bytes()))
    value=dict(schema='typescript-canonical-owner-replay-v1',status='candidate-replay-passed-awaiting-owner-review' if success else 'candidate-replay-needs-review',
        rule_version=RULE,counter=dict(path=str(Path(__file__).resolve()),sha256=digest(Path(__file__).read_bytes())),
        prerequisite_pins={str(path):value for path,value in pins.items()},source_bindings=source_bindings,
        fixture_checks=checks,applications=applications,result_files=files,native_reader_artifact_files=len(inventory),
        source_evaluations=0,new_parser_invocations=0,benchmark_samples=0,required_work_qualified=False,
        runtime_dependency_closure_qualified=False,**FALSE_FLAGS)
    write_new(output/'replay.json',value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    single=sub.add_parser('count');single.add_argument('--source',type=Path,required=True)
    single.add_argument('--ast',type=Path,required=True);single.add_argument('--output',type=Path,required=True)
    batch=sub.add_parser('replay');batch.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='count':
        value=count_source(args.source.read_bytes().decode('utf-8'),json.loads(args.ast.read_bytes()))
        write_new(args.output,value);return 0 if value['status']=='candidate-native-owner-pass' else 1
    c=reader_module()
    with c.kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);c.kb.kh.verify_lock(lock);c.checked_runtime()
        value=replay(args.output);c.kb.kh.verify_lock(lock)
    print(json.dumps(dict(status=value['status'],replay=str(args.output/'replay.json'))))
    return 0 if value['status']=='candidate-replay-passed-awaiting-owner-review' else 1


if __name__=='__main__':raise SystemExit(main())
