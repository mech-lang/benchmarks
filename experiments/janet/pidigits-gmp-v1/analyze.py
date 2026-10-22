"""Final-cohort medians and paired round ratios, without pooling the first cohort."""
import json
import statistics
from common import HERE,process

p=HERE/'final-run-v1/results.json';r=json.loads(p.read_bytes());assert r['status']=='56-full-size-complete-process-outputs-pass'
parents={row['sample']:row for row in r['samples'] if row['label']=='parent'}
profiles={}
for label,summary in r['summary'].items():
    rows=[row for row in r['samples'] if row['label']==label];ratios=[parents[row['sample']]['seconds']/row['seconds'] for row in rows]
    profiles[label]=dict(**summary,parent_speedup_from_cohort_medians=r['summary']['parent']['median_seconds']/summary['median_seconds'],paired_parent_speedups=ratios,median_paired_parent_speedup=statistics.median(ratios),rounds_faster_than_parent=sum(value>1 for value in ratios),rounds=len(rows))
result=dict(schema='janet-pidigits-final-cohort-analysis.v1',status='verified-final-eight-way-cohort-only',final_report_sha256=process.sha(p),initial_cohort_retained_separately=True,profiles=profiles,
            limitation='Within-round ratios reduce broad temporal drift but do not prove a pristine host, eliminate source-order effects or establish a globally fastest implementation.')
process.save(HERE/'analysis.json',result)
print(json.dumps(profiles))
