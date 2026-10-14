"""Exact canonical owner coverage for six retained R workload sources.

This is a reviewed six-source mapping, not an R parser or a physical-LOC
fallback. Every significant source character is assigned to an explicit owner;
changed bytes need a fresh review. No source, compiler or runtime is executed.
"""
import hashlib
import re

POLICY='r-six-retained-source-owners-v1'
RULE='canonical-source-units-20261012-approved-rule-v2'
BASE='archive/comparisons/r-apl-uiua-comparison/20261011/sources/r/'
# Each entry describes physical source rows 2..EOF. Row 1 is the retained
# attribution/design comment. Header opening braces have their own zero-unit
# spans; written closing braces retain one unit. F and P mark the two reviewed
# packed-control forms, expanded below rather than guessed by a parser.
SOURCES={
 'nbody:nbody-r-compact':dict(path=BASE+'nbody/compact.R',
  sha256='f8fdbaa8a2f7977b8f082610b691160b01f9c6916ec796acfffe0b5318a5f5ff',
  owners=('H:run','B:p','B:v','B:m','B:pair','B:incidence','B:v[1L,]','E:energy','S:initial-energy',
          'H:step','B:delta','B:distance','B:force','B:v','B:p','C:step','S:final-energy','C:run','S:invoke-run')),
 'nbody:nbody-r-optimized':dict(path=BASE+'nbody/optimized.R',
  sha256='2c3969aa76d27160af75bcd4273cb4223de0d6b72282f190b4b5e7095fc76ed7',
  owners=('H:run','B:p','B:v','B:m','B:i','B:j','B:pairs','B:diagonal','B:v[1L,]','E:energy',
          'S:initial-energy','H:step','B:delta','B:d2','B:d2[diagonal]','B:mag','B:v[,1L]',
          'B:v[,2L]','B:v[,3L]','B:p','C:step','S:final-energy','C:run','S:invoke-run')),
 'binarytrees:binarytrees-r-compact':dict(path=BASE+'binarytrees/compact.R',
  sha256='441e3d954b41cc3c1356eba42eed13c1f4ee547b475303f5a822cfd3585493dc',
  owners=('E:make','E:check','H:run','B:depth','S:stretch-output','S:gc','B:long','H:depth-iteration',
          'B:iterations','B:total','S:iteration-output','C:depth-iteration','S:retained-root-output','C:run','S:invoke-run')),
 'binarytrees:binarytrees-r-optimized':dict(path=BASE+'binarytrees/optimized.R',
  sha256='b8ae857e270ab9dc85c816117d912005cd1a159aac2dfb38d565887701a05f66',
  owners=('E:make','E:check','H:task','B:iterations','B:total','F:iteration-total','S:task-result','C:task',
          'H:run','B:depth','S:stretch-output','S:gc','B:long','B:cluster','S:cluster-cleanup',
          'S:export-functions','S:parallel-iteration-output','S:retained-root-output','C:run','S:invoke-run')),
 'fannkuchredux:fannkuchredux-r-array-compact':dict(path=BASE+'fannkuchredux/array-compact.R',
  sha256='8402f39b4815ac28f05a8bf646f43aaa99762c4396bd691060f918733c0d68d6',
  owners=('H:run','B:factorials','B:checksum','B:maximum','H:batch','B:ranks','B:remainder','B:permutation',
          'P:unrank','B:digit','B:remainder','B:gather','B:permutation[seq_len(i),]','C:unrank',
          'B:flips','B:active','H:flip','B:first','B:rows','B:gather','B:permutation[,active]',
          'B:flips[active]','B:active','C:flip','B:checksum','B:maximum','C:batch','S:result-output','C:run','S:invoke-run')),
 'fannkuchredux:fannkuchredux-r-array-batched':dict(path=BASE+'fannkuchredux/array-batched.R',
  sha256='1d87cf59c2081123649117fdaee3957537872eded5e4b8d300701f94aa2796a2',
  owners=('H:run','B:factorials','B:total','B:workers','B:ranges','H:task','B:checksum','B:maximum','H:batch',
          'B:ranks','B:remainder','B:permutation','P:unrank','B:digit','B:remainder','B:gather',
          'B:permutation[seq_len(i),]','C:unrank','B:flips','B:active','H:flip','B:first','B:rows','B:gather',
          'B:permutation[,active]','B:flips[active]','B:active','C:flip','B:checksum','B:maximum','C:batch',
          'S:task-result','C:task','B:result','S:result-output','C:run','S:invoke-run')),
}
KINDS={'H':'explicit-header','B':'independent-binding','E':'expression-function-binding',
       'S':'expression-statement','C':'written-close'}
NAMED_ARGUMENTS=frozenset(('byrow','each','by','envir','sep','mc.cores','mc.preschedule'))


def count_source(source,identity):
    if type(source) is not bytes or identity not in SOURCES:
        raise ValueError('Exact registered source bytes and profile identity required')
    spec=SOURCES[identity];digest=hashlib.sha256(source).hexdigest()
    if digest!=spec['sha256']:
        raise ValueError('Source is outside the six retained R owner decisions')
    text=source.decode('utf-8');lines=text.splitlines(keepends=True)
    if not text.isascii() or not text.endswith('\n') or len(lines)!=len(spec['owners'])+1:
        raise ValueError('Reviewed source layout differs')
    if not lines[0].startswith('#') or any(not line.strip() or line.lstrip().startswith('#') for line in lines[1:]):
        raise ValueError('Reviewed comment/code coverage differs')
    owners=[];offset=len(lines[0]);named=[]
    def add(kind,name,line,start,end,units):
        if end<=start:raise ValueError('Empty reviewed owner')
        owners.append(dict(kind=kind,name=name,line=line,start=start,end=end,canonical_units=units,text=text[start:end]))
    for number,(line,decision) in enumerate(zip(lines[1:],spec['owners']),2):
        body=line.rstrip('\n');left=offset+len(body)-len(body.lstrip());right=offset+len(body.rstrip())
        tag,name=decision.split(':',1);spelling=text[left:right]
        if tag=='H':
            if not spelling.endswith(' {'):raise ValueError('Reviewed header opener differs')
            add(KINDS[tag],name,number,left,right-2,1)
            add('written-open',name,number,right-1,right,0)
        elif tag=='C':
            if spelling!='}':raise ValueError('Reviewed close differs')
            add(KINDS[tag],name,number,left,right,1)
        elif tag=='F':
            prefix='for (i in seq_len(iterations))'
            if spelling!=prefix+' total <- total+check(make(d))':raise ValueError('Reviewed unbraced loop differs')
            add('explicit-header','iteration',number,left,left+len(prefix),1)
            add('independent-binding','total',number,left+len(prefix)+1,right,1)
        elif tag=='P':
            prefix='if (n >= 2L)'
            if spelling!=prefix+' for (i in seq.int(n,2L,by=-1L)) {':raise ValueError('Reviewed nested control headers differ')
            add('explicit-header','rank-width-condition',number,left,left+len(prefix),1)
            add('explicit-header','unrank-loop',number,left+len(prefix)+1,right-2,1)
            add('written-open','unrank-loop',number,right-1,right,0)
        else:
            if tag in ('B','E') and not spelling.startswith(name+' <- '):
                raise ValueError('Reviewed binding owner differs')
            if tag=='E' and ('function(' not in spelling or '{' in spelling):
                raise ValueError('Reviewed expression-only function differs')
            add(KINDS[tag],name,number,left,right,1)
        for match in re.finditer(r'\b([A-Za-z][A-Za-z0-9.]*)=(?!=)',body):
            if match[1] not in NAMED_ARGUMENTS:raise ValueError('Unreviewed named argument')
            named.append(dict(line=number,name=match[1],start=offset+match.start(),end=offset+match.end(),
                              independent_binding=False))
        offset+=len(line)
    owned=set()
    for owner in owners:
        span=set(range(owner['start'],owner['end']))
        if owned&span:raise ValueError('Overlapping source owners')
        owned.update(span)
    unowned=[i for i in range(len(lines[0]),len(text)) if not text[i].isspace() and i not in owned]
    if unowned:raise ValueError('Unowned significant source characters')
    by_line={line:sum(o['canonical_units'] for o in owners if o['line']==line) for line in range(2,len(lines)+1)}
    return dict(schema='r-exact-retained-source-unit-count-v1',policy=POLICY,rule_version=RULE,identity=identity,
        source_path=spec['path'],source_sha256=digest,canonical_loc=sum(by_line.values()),
        physical_loc=len(lines)-1,original_physical_loc=len(lines)-1,formatted_loc=None,formatted_loc_qualified=False,
        source_owners=owners,packed_owner_lines=[dict(line=line,canonical_units=n) for line,n in by_line.items() if n!=1],
        named_arguments=named,comment_spans=[dict(start=0,end=len(lines[0]),canonical_units=0)],
        unowned_significant_characters=[],generic_language_certificate=False,native_execution=False,
        chart_admission=False)
