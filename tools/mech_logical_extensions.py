"""Bind the frozen native Mech owner proof to exact complete application bundles."""
import hashlib,json
from pathlib import Path
from source_metrics import metadata_for
PACKET=Path('experiments/source-normalization/mech-v1')
POLICY='logical-source-owners.mech-v1-definitions-bindings'
REPORT_SHA='78963bf84de96dda70be7b454eb145e9214d2266e59e63d53c3ea062e8948adf'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError('Invalid Mech logical extension: '+message)
def bind(catalog,root):
    root=Path(root);p=root/PACKET/'qualification.json'
    if not p.exists():return None
    raw=p.read_bytes();require(sha(raw)==REPORT_SHA,'frozen proof differs');proof=json.loads(raw)
    require(proof['status']=='native-qualified-exact-source-subset' and proof['policy']==POLICY and proof['input_programs_executed'] is False,'proof scope differs')
    for name,field in [('owners.py','policy_source_sha256'),('helper/src/main.rs','helper_source_sha256')]:require(sha((root/PACKET/name).read_bytes())==proof[field],'producer differs')
    by_sha={r['source_sha256']:r for r in proof['sources'].values()};profiles={}
    require(len(by_sha)==3,'source inventory differs')
    for r in by_sha.values():
        require(type(r['logical_units']) is int and r['logical_units']>0 and r['logical_units']==len(r['owners']) and r['unowned_significant_tokens']==0,'owner totals differ')
    for key,row in {**catalog.get('program_inventory',{}),**catalog['programs']}.items():
        if row['language'] not in ('mech','mech-jit','mech-resident'):continue
        parts=[];total=0
        for digest in row['files']:
            source=catalog['files'][digest];require(sha(source['code'].encode())==digest,'source bytes differ')
            meta,role,included=metadata_for(row,digest,source)
            if not included or meta.get('support_line_ranges') or digest not in by_sha:break
            require(meta.get('code',source['code'])==source['code'] and meta.get('sha256',digest)==digest,'source override differs')
            count=by_sha[digest]['logical_units'];total+=count
            parts.append(dict(source_sha256=digest,application_projection_sha256=digest,application=count,submitted=count,excluded_support=0,role=role,support_line_ranges=[]))
        else:
            if parts:profiles[key]=dict(status='qualified',application=total,submitted=total,excluded_support=0,policy=POLICY,sources=parts)
    metadata=dict(id=POLICY,report_path=(PACKET/'qualification.json').as_posix(),report_sha256=REPORT_SHA,
        definition='Native Mech definitions and written binding owners; matrices, comprehensions and expression matches remain expressions.',
        native_parsers='Mech retained-document parser at 6de19875e; source parsing only.',scope='Exact complete application source bundles; no generic language certificate or formatted LOC claim.',evidence_path=(PACKET/'README.md').as_posix())
    return dict(profiles=profiles,policy=metadata)
