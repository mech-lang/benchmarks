"""Exact Mech CST owner policy; not a whole-language normalization certificate."""
import hashlib
POLICY='logical-source-owners.mech-v1-definitions-bindings'
class QualificationError(ValueError):pass
def require(value,message):
    if not value:raise QualificationError(message)
def qualify(capture):
    require(capture['diagnostics']=='DiagnosticStore { revision: Revision(0), diagnostics: [] }','Native parser diagnostic')
    raw=capture['source'].encode();owners=[];tokens=[]
    def visit(n,owner=None):
        require(0<=n['start']<=n['end']<=len(raw),'Invalid byte range')
        kind=n['kind']
        if n['token']:
            text=raw[n['start']:n['end']].decode();require(text==n['text'],'Native token text differs')
            tokens.append(dict(start=n['start'],end=n['end'],kind=kind,text=text,owner=owner));return
        children=n['children']
        if kind=='Statement':
            semantic=[c for c in children if not c['token'] and c['kind']!='Comment']
            require(len(semantic)==1 and semantic[0]['kind'] in ('VariableDefine','KindDefine'),'Unqualified written statement kind')
        if kind=='FunctionDefine':
            bodies=[c for c in children if c['kind'] in ('FunctionDefineExpression','FunctionDefineStatements')]
            require(len(bodies)==1,'Unqualified function body')
        if kind in ('VariableDefine','KindDefine','FunctionDefine'):
            owner=len(owners);owners.append(dict(id=owner,kind=kind,start=n['start'],end=n['end']))
        require(not kind.startswith(('Fsm','ForLoop','WhileLoop')),'Control-owner policy not qualified for this source kind')
        if kind=='Comment':
            def comments(c):
                if c['token']:
                    text=raw[c['start']:c['end']].decode();require(text==c['text'],'Comment token differs');tokens.append(dict(start=c['start'],end=c['end'],kind='Comment',text=text,owner=None))
                else:
                    for a in c['children']:comments(a)
            comments(n);return
        for child in children:visit(child,owner)
    visit(capture['syntax'])
    position=0;significant=0
    for t in tokens:
        require(t['start']==position,'Gap or overlap in native token stream');position=t['end']
        if t['kind'] not in ('Comment','CommentToken') and t['text'].strip():
            require(t['owner'] is not None,'Unowned significant native token');significant+=1
    require(position==len(raw),'Native token stream does not cover complete source')
    return dict(policy=POLICY,source_sha256=hashlib.sha256(raw).hexdigest(),logical_units=len(owners),owners=owners,significant_tokens=significant,unowned_significant_tokens=0,canonical_formatted_loc=None,generic_language_certificate=False)
