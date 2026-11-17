#!/usr/bin/env python3
"""Import the frozen Related Post Gen cohorts without rerunning or renaming their timers."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from benchmark_suite import ROOT, SCHEMA, archive_evidence, digest, save, seal_evidence, summarize, validate_campaign

VARIANTS = {'related-managed':'mech-ir355-managed-guarded-u16-4',
            'related-compact':'mech-ir353-compact-guarded-u16-4', 'rust':'rust-preinitialized'}
REVISION = 'c18d910c9dfd56d988a7c4e75a94b90ef8fb2b1a'
RUST_REVISION = 'fc2982b0c929b1b701209d401a1dc30c773ef4ab'


def retained_metrics(sample, cohort, rust=False):
    if cohort == 'confirmation':
        return {'native_process_seconds':sample['whole_process_seconds'],
                ('reported_processing_seconds' if rust else 'post_json_seconds'):
                    sample['reported_processing_seconds' if rust else 'post_json_seconds']}
    return {'native_process_seconds':sample['wall_seconds'],
            ('reported_processing_seconds' if rust else 'post_json_seconds'):
                sample['seconds'] if rust else sample['post_json_seconds']}


def import_cohorts(source, output):
    source=Path(source);output=Path(output)
    packet=source/'integration/fixed-benchmark-target-20261112'
    provenance=packet/'provenance'
    manifest=json.loads((provenance/'manifest.json').read_text())
    for name,pin in manifest['files'].items():
        raw=(provenance/name).read_bytes()
        if len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
            raise ValueError('retained provenance changed: '+name)
    reports={cohort:json.loads(gzip.decompress((provenance/'reports'/name).read_bytes())) for cohort,name in
             [('primary','primary_31_round_report.json.gz'),('confirmation','independent_13_round_report.json.gz')]}
    primary=reports['primary']
    source_text=(source/'mech/related_guarded_u16.mec').read_text()
    if hashlib.sha256(source_text.encode()).hexdigest()!='6a3022a0385efd1bf3dcdc9a76409607d20237260b21bf6745416d84da3d027a':
        raise ValueError('qualified Mech source changed')
    task={'outputs':['related_posts'],'input_posts':5000,'input_sha256':primary['input']['sha256'],
          'arithmetic':'Checked unsigned integer scores; exact complete ordered related-post JSON.',
          'ownership':'All 5000 posts processed; complete output equals the unchanged standard Rust oracle.',
          'absolute_tolerance':0,'relative_tolerance':0}
    host={'cpu':primary['machine'],'system':'Darwin','release':primary['platform']}
    note=('Fixed unchanged upstream rust_con example. Its eight-thread Rayon pool is initialized before its reported processing timer; '
          'Mech creates and joins four workers inside its larger continuous post-JSON interval. This conservative comparison preserves that Rust advantage; '
          'it does not claim identical timer boundaries or a win over every custom Rust experiment. Whole-process comparison includes setup on both sides.')
    contract=digest({'task':task,'reference':RUST_REVISION,'policy':note})
    output.mkdir(parents=True,exist_ok=True)
    for cohort,report in reports.items():
        directory=output/f'2026-11-12-related-post-{cohort}-001'
        if directory.exists():raise ValueError('choose a new import destination')
        directory.mkdir()
        shutil.copytree(packet,directory/'retained')
        raw_report=directory/'raw/retained/report.json.gz';raw_report.parent.mkdir(parents=True)
        name='primary_31_round_report.json.gz' if cohort=='primary' else 'independent_13_round_report.json.gz'
        shutil.copyfile(provenance/'reports'/name,raw_report)
        campaign={'schema':SCHEMA,'id':directory.name,'started_at':'2026-11-12' if cohort=='primary' else min(x['started_utc'] for x in report['samples']),
                  'environment':host,'environment_hash':digest(host),'workers':{'candidate':{'revision':REVISION}},
                  'profile':'retained-related-post-gen','sampling':{'forks':31 if cohort=='primary' else 13,'order':'Retained seeded randomized fresh processes; no observations removed.'},
                  'origin':{'kind':'imported_measurements','imported_at':datetime.now(timezone.utc).isoformat(),'original_date':'2026-11-12','time_precision':'date' if cohort=='primary' else 'recorded process timestamp','upstream':'https://github.com/zupat/related_post_gen','upstream_revision':RUST_REVISION},
                  'performance_gate':False,'results':[],'comparisons':[],'complete':True}
        for backend,variant in VARIANTS.items():
            rust=backend=='rust'
            implementation=next(x for x in primary['implementations'] if x['name']==variant)
            text=(provenance/'sources'/f"{implementation['source_sha256']}.rs").read_text() if rust else source_text
            if hashlib.sha256(text.encode()).hexdigest()!=implementation['source_sha256']:raise ValueError('implementation source mismatch')
            measurement={'boundary':implementation['processing_boundary'],'primary_metric':'reported_processing_seconds' if rust else 'post_json_seconds',
                         'schedule':[[]],'reset':'One fresh process per round','threads':8 if rust else 4,
                         'comparison_note':note,'metric_mapping':{'post_json_seconds':'reported_processing_seconds'} if rust else {},
                         'contract_note':'Compact entry omits ordinary managed admission/resource/recovery; arithmetic and indexing remain checked.' if backend=='related-compact' else 'Ordinary managed checks retained.' if not rust else note}
            record={'case_id':'related-post-gen','title':'Rust · unchanged rust_con' if rust else 'Related Post Gen · 5,000 posts',
                    'family':'applications','backend':backend,'lane':'control' if rust else 'candidate','revision':RUST_REVISION if rust else REVISION,
                    'progress':'measured','outcome':'ok','capability':'supported','task':task,'task_hash':digest(task),
                    'measurement':measurement,'measurement_hash':digest(measurement),'source':text,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'environment_hash':digest(host),'feature_profile':{'backend':backend,'managed':backend=='related-managed'},'control_contract':contract,
                    'implementation':{'binary_sha256':implementation['executable_sha256'],'adapter_sha256':implementation.get('receipt_sha256'),
                                      'rustc':'Frozen original build; exact receipts and source pins retained in the report packet.'},'samples':[]}
            if backend=='related-compact':
                record['revision']='IR353 · compiler build '+implementation['compiler_build_sha256']
            record['implementation'].update(compiler_build_sha256=implementation.get('compiler_build_sha256'),
                                            source_publication_revision=REVISION if not rust else RUST_REVISION)
            observed=[x for x in report['samples'] if x['variant']==variant]
            if len(observed)!=(31 if cohort=='primary' else 13):raise ValueError('incomplete retained cohort')
            for x in observed:
                index=x['sample' if cohort=='primary' else 'round']
                if x['exit']!=0 or not x['exact_rust_output' if cohort=='primary' else 'exact_output']:raise ValueError('unqualified retained output')
                metrics=retained_metrics(x,cohort,rust)
                # The parent report owns the observations. The small receipts only
                # expose their original values through the common evidence viewer.
                relative=f'raw/{backend}/fork-{index+1}'
                save(directory/relative/'supervised.json',{'outcome':'ok','metrics':metrics,'retained_observation':{
                    'path':'raw/retained/report.json.gz','sha256':hashlib.sha256(raw_report.read_bytes()).hexdigest(),
                    'cohort':cohort,'variant':variant,'round':index}})
                record['samples'].append({'fork':index,'raw':relative,'metrics':metrics})
            record['samples'].sort(key=lambda x:x['fork'])
            record['summary']=summarize(record['samples'])
            record['verification']={'outcome':'ok','raw':record['samples'][0]['raw'],
                                    'reason':f'All {len(observed)} full 5000-post JSON outputs equal the unchanged standard Rust result. Original output hashes, orders and all other variants remain in the retained report.',
                                    'outputs':[{'kind':'sha256','value':observed[0]['output_sha256'] if cohort=='primary' else observed[0]['gold_sha256']}]}
            campaign['results'].append(record)
        save(directory/'campaign.json',campaign)
        (directory/'report.md').write_text((packet/'REPORT.md').read_text())
        seal_evidence(directory);archive_evidence(directory);validate_campaign(directory,campaign)
        print(directory)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'results/campaigns');a=p.parse_args();import_cohorts(a.source,a.output)
