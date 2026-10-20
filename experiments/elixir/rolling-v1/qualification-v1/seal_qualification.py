"""Bind completed bounded native records and lossless raw-byte evidence only."""
import argparse
import json
from pathlib import Path

from native_process import atom,sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUTPUT=HERE/'qualification.json'
ARCHIVE=HERE/'lossless-archive-v1/manifest.json'


def require(value,message):
    if not value:raise ValueError(message)


def ref(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))


def make():
    archive=json.loads(ARCHIVE.read_bytes());require(archive['status']=='LOSSLESS-VERIFIED','Lossless raw evidence unsealed')
    omitted={r['raw']['path']:r for r in archive['entries']}
    runtime=json.loads((HERE/'runtime-v2/report.json').read_bytes());builds=json.loads((HERE/'bounded-v2/report.json').read_bytes())
    work=json.loads((HERE/'work-v3/report.json').read_bytes());failure=json.loads((HERE/'failure-v1/report.json').read_bytes())
    require(all(r['status']=='PASSED' for r in [runtime,builds,work,failure]),'Incomplete native gates')
    require(builds['complete_output_observations']==42 and len(builds['programs'])==3 and work['observations']==117
        and work['whole_histograms']==819 and work['total_traced_updates']==222597,'Completed native inventory differs')
    attempts=['runtime-v1','runtime-v2','bounded-v1','bounded-v2','work-v1','work-v2','work-v3','failure-v1']
    require([json.loads((HERE/p/'report.json').read_bytes())['status'] for p in attempts]
        ==['FAILED','PASSED','FAILED','PASSED','FAILED','FAILED','PASSED','PASSED'],'Failed/successful attempts relabeled')
    pins={}
    files=[p for p in HERE.rglob('*') if p.is_file() and p!=OUTPUT and '__pycache__' not in p.parts and not p.name.endswith('.tmp')]
    files.extend([HERE.parent/'plan.json',HERE.parent/'README.md',HERE.parent/'sources/serial.ex',HERE.parent/'sources/parallel.ex'])
    for p in sorted(files):
        relative=str(p.relative_to(ROOT))
        if relative in omitted:continue
        pins[relative]=sha(p)
    sourcebundles={name:dict(source=p['source'],support=p['support'],runner=p['runner'],production_beams=p['beams']) for name,p in builds['programs'].items()}
    for p in sourcebundles.values():
        for key in ['source','support','runner']:pins[p[key]['path']]=p[key]['sha256']
    return dict(schema='elixir-rolling-bounded-qualification.v1',status='QUALIFIED-BOUNDED-NOT-TIMED',
        controller=ref(Path(__file__)),pins=pins,source_bundles=sourcebundles,
        completed_reports={p:ref(HERE/p/'report.json') for p in attempts},
        runtime=dict(official_archive_sha256='7863c546cda13fecc949e562e326042451dacf8fd8698a36783cb71eeb223b46',
            elixir_files_verified=723,otp_files_verified=4243,restored_version='Elixir 1.20.4; OTP 29.1.1_2 / ERTS 17.1; ARM64 JIT',
            environment=builds['programs']['parent']['compiler_command']['environment'],
            archived_distribution_limit='Ignored official ZIP/restored Elixir/local OTP bytes are not rehashed when absent; exact whole-distribution manifests and raw native restoration/version receipts remain retained.'),
        complete_output=dict(shared_cases=14,sources=3,observations=42,exact_independent_and_parent_bytes=True),
        work_witness=dict(observations=117,fixtures=39,whole_histograms=819,actual_map_update_calls=222597,
            production_source_rewritten=False,small_fixture_processes_with_each_returned_map_traced=114,
            compact_large_fixture_processes=3,
            compact_trace_limit='Actual per-call key/old-value/pre-update size and complete final maps retained; no per-step returned-map copy on DNA longer than256. Standard production Map.update remains source/BEAM pinned.',
            actual_default_empty_growth=True,actual_flatmap_to_hashmap_observed=True,
            full_size_updates_source_formula_only=874999961,full_size_work_executed=False),
        parallel_failure_cleanup=dict(passed=True,evidence=ref(HERE/'failure-v1/result.json'),
            source_twin_only=True,production_source_changed=False,all_traced_application_descendants_dead=True),
        large_raw_archive=dict(manifest=ref(ARCHIVE),entries=len(omitted),raw_bytes=archive['raw_bytes'],gzip_bytes=archive['gzip_bytes'],
            local_originals_retained=True,omitted_raw_paths=omitted,
            archived_replay='Every original raw byte is losslessly retained through gzip and exact decompressed SHA/length; no claim that an absent original path was freshly rehashed.'),
        source_count=None,source_formatting=None,required_work_qualified_bounded=True,
        quantitative_benchmark_processes=0,pilot_run=False,full_run=False,chart_admission=False,
        authorship='Codex GPT-6-family local adaptations; exact model and inherited predecessor origin/terms remain unresolved. Unchanged helper/runner remain counted application source.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.check,'Choose one mode')
    if args.prepare:require(not OUTPUT.exists(),'Fresh qualification seal required');atom(OUTPUT,make())
    require(json.loads(OUTPUT.read_bytes())==make(),'Qualification seal or evidence changed')
    print(json.dumps(dict(status='PASSED-OFFLINE-SEAL',qualification=ref(OUTPUT),durable_pins=len(json.loads(OUTPUT.read_bytes())['pins']))))
