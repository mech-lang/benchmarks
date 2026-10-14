"""Lossless, non-evaluating inspection of the retained Builder spec data.

This reader never creates a replacement SDK spec. The native generator loads
the original Builder bytes; this inspection records selected data and spans.
"""
import hashlib
import re

SPEC_SHA = '960a9e74aa4a0bbdc35f02a8ea18e1cba90dfb7681e04853dff524e0922dba5e'
SOURCE_ROOT = '/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/rebol-comparison/20261013/.build/sdk-builder-spec-v1/source-copy/'
ARRAYS = ('files','clean','includes','core-files','host-files','mezz-base-files','mezz-sys-files',
          'mezz-lib-files','mezz-prot-files','boot-host-files')


def parse(raw):
    text = raw.decode('utf8')
    index = 0

    def space():
        nonlocal index
        while index < len(text):
            if text[index].isspace():
                index += 1
            elif text[index] == ';':
                end = text.find('\n',index)
                index = len(text) if end < 0 else end + 1
            else:
                break

    def value():
        nonlocal index
        space()
        start = index
        assert index < len(text), 'Unexpected end of data'
        if text.startswith('#[', index) or text.startswith('#(',index):
            opening = text[index:index+2];index += 2
        elif text[index] in '[(':
            opening = text[index];index += 1
        else:
            opening = None
        if opening:
            closing = ']' if opening.endswith('[') else ')'
            children=[]
            space()
            while index < len(text) and text[index] != closing:
                children.append(value());space()
            assert index < len(text) and text[index] == closing, 'Unbalanced data'
            index += 1
            return dict(kind=opening,start=start,end=index,children=children)
        if text[index] in '"{':
            opening=text[index];closing='"' if opening=='"' else '}'
            index += 1; depth=1; decoded=[]
            while index < len(text):
                char=text[index];index += 1
                if char=='^':
                    assert index < len(text)
                    escaped=text[index];index += 1
                    assert escaped != '(', 'Unexpected numeric string escape in retained spec'
                    decoded.append({'/':'\n','-':'\t','M':'\r'}.get(escaped,escaped));continue
                if opening=='{' and char=='{':depth += 1
                if char==closing:
                    depth -= 1
                    if depth==0:break
                decoded.append(char)
            assert depth==0,'Unterminated string'
            return dict(kind='string',start=start,end=index,value=''.join(decoded))
        while index < len(text) and not text[index].isspace() and text[index] not in '[](){}";':
            index += 1
        assert index>start, ('Unexpected delimiter',index)
        return dict(kind='atom',start=start,end=index,value=text[start:index])

    root=value();space()
    assert index==len(text) and root['kind']=='#[', 'Expected one complete saved map'
    children=root['children'];assert len(children)%2==0
    fields={}
    for key,val in zip(children[::2],children[1::2]):
        assert key['kind']=='atom' and re.fullmatch(r'[A-Za-z][A-Za-z0-9?_-]*:',key['value'])
        name=key['value'][:-1];assert name not in fields, ('Duplicate map key',name)
        fields[name]=val
    return fields


def canonical(node):
    if node['kind'] in ('atom','string'):
        return [node['kind'],node['value']]
    return [node['kind'],[canonical(child) for child in node['children']]]


def review(raw):
    assert hashlib.sha256(raw).hexdigest()==SPEC_SHA, 'Retained Builder spec changed'
    fields=parse(raw)
    scalars={'name':('string','rebol3-bulk-macos-arm64'),'compiler':('atom','clang'),
        'arch':('atom','arm64'),'root':('atom','%'+SOURCE_ROOT),'source':('atom','%src/'),
        'temp':('atom','%make/tmp/'),'output':('atom','%build/'),
        'objects':('atom','%make/tmp/clang-arm64/rebol3-bulk-macos-arm64/'),
        'version':('atom','3.22.1'),'product':('atom','Bulk'),'os':('atom','macos'),
        'sys':('atom','darwin'),'vendor':('atom','apple'),'platform':('atom','macOS'),
        'stack-size':('atom','4194304'),'remove-docstrings':('atom','off')}
    for key,(kind,val) in scalars.items():
        assert canonical(fields[key])==[kind,val], ('Selected SDK property changed',key)
    for key in ('gits','assembly','post-build','boot-host-files'):
        assert canonical(fields[key])==['[',[]]
    assert canonical(fields['pre-build'])==['[',[['atom','do'],['atom','%make/pre-make.r3'],['string','$NEST_SPEC']]]
    arrays={}
    for key in ARRAYS:
        node=fields[key];assert node['kind']=='['
        values=[]
        for child in node['children']:
            assert child['kind']=='atom' and child['value'].startswith('%'), ('Non-file SDK input',key)
            name=child['value'][1:]
            if name.startswith('/'):
                assert name.startswith(SOURCE_ROOT), ('Uncontained SDK input',name)
                name=name[len(SOURCE_ROOT):]
            else:
                assert not name.startswith('../') and '/..' not in name
                if key not in ('includes',):name='src/'+name
            values.append(name)
        arrays[key]=values
    compiled=set(arrays['files'])
    assert set(arrays['core-files']+arrays['host-files']) <= compiled
    assert 'src/os/host-main.c' in compiled
    config=fields['config'];assert config['kind']=='[' and all(n['kind']=='atom' for n in config['children'])
    definitions=fields['defines'];assert definitions['kind']=='['
    assert {'__LP64__','ENDIAN_LITTLE','TO_MACOS','REB_EXE','TEST_EXTENSIONS'} <= {
        n.get('value') for n in definitions['children']}
    assert not any(key in fields for key in ('target','target-arch','target-abi','abi','os-target','configuration'))
    return dict(schema='retained-Rebol-Builder-spec-source-review-v1', original_spec_sha256=SPEC_SHA,
        resolved_spec_recreated=False, generator_executions=0, extension_builds=0, chart_admission=False,
        selected={key:val for key,(_,val) in scalars.items()}, arrays=arrays,
        array_counts={key:dict(entries=len(values),unique=len(set(values))) for key,values in arrays.items()},
        config_words=[n['value'] for n in config['children']],
        field_spans={key:dict(start=node['start'],end=node['end']) for key,node in fields.items()},
        field_names=list(fields), native_spec_readback_verified=False, generated_headers_verified=False,
        vendor_default_derivations=dict(abi='macho from spec/os=macos',target='arm64-apple-darwin-macho',
            build_date='actual generator clock',git_commit='none in fresh copy with no .git',
            os_version='actual sw_vers -productVersion query',libc='actual attempted ldd --version query'),
        source_file_closure='898 retained source files plus the exact saved Builder spec; whole closure not rehashed by this source review')
