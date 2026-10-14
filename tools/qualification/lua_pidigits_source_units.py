"""Exact authored-owner mapping for four retained Lua pi-digit applications.

This source whitelist is not a Lua parser. It covers the complete measured
application bytes, including written end/else tokens and the control label.
The separately counted C compatibility module is an additional bundle member.
"""
import hashlib

RULE = 'canonical-source-units-20261012-approved-rule-v2'
BASE = 'experiments/lua/retained-pidigits-v1/sources/'
SPECS = {
 1: dict(sha256='e2e0139198ef7b00dd616fdd82d756e079a96db64702c72c4f9bed0a2d9d1e82',
         rows='7-13 15-19 21-26 28-32 34-40 42-56 58-61 63-74 76',
         functions=(21,28,34,42), controls=(51,54,59,65,71), closes=(26,32,40,56,61,67,70,73,74),
         branches=(), labels=(69,), declarations=(15,16,17,18,19)),
 5: dict(sha256='00734d693c0968a606b8aef2cfeffa15da58e7f4ac81731c19fb7f1dde7a0c36',
         rows='6-13 15-21 24-35 38-49 52-58 61-89 91-92',
         functions=(24,38,52,61), controls=(72,74,77,86), closes=(35,49,58,79,84,85,88,89),
         branches=(81,), labels=(), declarations=(15,16,17,18,19,20,21)),
 6: dict(sha256='ce34fae5e45f842c8b414b18fa368e90809165fda0781b8a00da2bc29d50d930',
         rows='7-14 16-18 20-28 30-36 38-43 46-73 75-76',
         functions=(20,30,38,46), controls=(40,56,58,61,70), closes=(28,36,42,43,63,68,69,72,73),
         branches=(65,), labels=(), declarations=(16,17,18)),
 7: dict(sha256='cca5f009f82162b0bdd50d839add97ef21859b5d8ddd047b3db9f286973c9c2c',
         rows='9-19 27-33 41-45 53-58 61-86 88-89',
         functions=(27,41,53,61), controls=(69,71,75,83), closes=(33,45,58,77,81,82,85,86),
         branches=(78,), labels=(), declarations=()),
}


def count_source(raw, variant):
    if type(raw) is not bytes or type(variant) is not int or variant not in SPECS:
        raise ValueError('Exact registered Lua source required')
    spec=SPECS[variant]
    if hashlib.sha256(raw).hexdigest()!=spec['sha256']:
        raise ValueError('Unreviewed Lua source bytes')
    text=raw.decode('utf-8');rows=set()
    for token in spec['rows'].split():
        ends=[int(x) for x in token.split('-')]
        rows.update(range(ends[0],ends[-1]+1))
    owners=[];comments=[];offset=0
    for number,line in enumerate(text.splitlines(keepends=True),1):
        value=line.strip();left=offset+len(line)-len(line.lstrip());right=offset+len(line.rstrip())
        if number not in rows:
            if value and not value.startswith('--'):
                raise ValueError('Significant row outside exact owner mapping')
            if value:comments.append(dict(start=left,end=right,canonical_units=0))
        else:
            if not value or value.startswith('--'):
                raise ValueError('Missing reviewed source owner')
            kind='statement-or-binding'
            if number in spec['functions']:
                if not value.startswith('local function ') or not value.endswith(')'):
                    raise ValueError('Function header differs')
                kind='function-header'
            elif number in spec['controls']:
                if not ((value.startswith('while ') and value.endswith(' do')) or
                        (value.startswith('if ') and value.endswith(' then'))):
                    raise ValueError('Control header differs')
                kind='control-header'
            elif number in spec['closes']:
                if value!='end':raise ValueError('Written close differs')
                kind='written-close'
            elif number in spec['branches']:
                if value!='else':raise ValueError('Branch differs')
                kind='branch'
            elif number in spec['labels']:
                if value!='::continue::':raise ValueError('Control label differs')
                kind='control-label'
            elif number in spec['declarations']:
                if not value.startswith('local ') or '=' in value:raise ValueError('Bare declaration differs')
                kind='independent-uninitialized-binding'
            owners.append(dict(line=number,start=left,end=right,kind=kind,
                               canonical_units=1,text=text[left:right]))
        offset+=len(line)
    if {x['line'] for x in owners}!=rows:raise ValueError('Incomplete owner coverage')
    covered=set()
    for owner in owners+comments:
        span=set(range(owner['start'],owner['end']))
        if covered&span:raise ValueError('Overlapping owner spans')
        covered.update(span)
    if any(not c.isspace() and i not in covered for i,c in enumerate(text)):
        raise ValueError('Unowned significant source character')
    return dict(schema='lua-pidigits-application-owner-count-v1',rule_version=RULE,
                variant=variant,source_path=BASE+f'pidigits-lua-{variant}-normalized.lua',
                source_sha256=spec['sha256'],canonical_loc=len(owners),physical_loc=len(rows),
                formatted_loc=None,formatted_loc_qualified=False,source_owners=owners,
                comment_spans=comments,unowned_significant_characters=[],
                generic_language_certificate=False,native_processes_started=0,
                canonical_loc_qualified=False,chart_admission=False)
