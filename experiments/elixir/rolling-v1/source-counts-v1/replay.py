"""Replay the unchanged retained counter against native captures; no execution.

Candidate counts remain unapproved. The public application boundary excludes the
same exact generic helper and launcher as the retained parent. Uniform logical
source units are a separate policy and are not certified by this replay.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from qualification import elixir_source_units as counter

PLAN=HERE/'plan-v1.json'
NATIVE=HERE/'run-v1'
REPLAY=HERE/'retained-replay-v1.json'
LEDGER=HERE/'source-ownership-proposed-v1.json'
CONTRACT=ROOT/'experiments/elixir/source-units-v1/fixture-contract.json'
OLD_REPLAY=ROOT/'experiments/elixir/source-units-v1/replay-v2.json'
FRONTEND=ROOT/'experiments/elixir/source-counts-v1/read_sources.exs'
COUNTER=ROOT/'tools/qualification/elixir_source_units.py'
COUNTER_SHA='d1070e8f38fdebdfe2523c918bfb4367958667f34bf3c77efb6d6725544dc07f'


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def ref(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()


def line_ledger(text,result):
    source=counter.Source(text);physical={i for i,row in enumerate(''.join(source.cleaned).splitlines(),1) if row.strip()}
    expansions={r['line']:r for r in result['expansions']};rows=[]
    for i,line in enumerate(text.splitlines(),1):
        expansion=expansions.get(i)
        rows.append(dict(line=i,source_text=line,significant=i in physical,
            retained_rule_units=expansion['units'] if expansion else 1 if i in physical else 0,
            retained_rule_owners=copy.deepcopy(expansion.get('canonical_events',[])) if expansion else [],
            residual_statements=copy.deepcopy(expansion.get('statements',[])) if expansion else [],
            fallback='preserved-significant-physical-row' if i in physical and expansion is None else None))
    require(sum(r['significant'] for r in rows)==result['physical_loc'],'Physical source ledger differs')
    if not result['diagnostics']:require(sum(r['retained_rule_units'] for r in rows)==result['normalized_loc'],'Retained source units do not sum')
    return rows


def make():
    require(sha(COUNTER)==COUNTER_SHA,'Exact retained counter changed')
    plan=load(PLAN);native=load(NATIVE/'report.json');raw=load(NATIVE/'native-process/process.json')
    require(native['status']=='PASSED-NATIVE-READER-AWAITING-OWNER-REVIEW' and native['plan']==ref(PLAN)
        and native['pins_unchanged'] is True and native['process']==raw,'Unclosed native source capture')
    require(raw['exit_code']==0 and not raw['timed_out'] and not raw['remaining_process_group']
        and raw['quantitative_benchmark'] is False and raw['common_mutex_inherited'] is True
        and raw['common_mutex_inode']==native['common_mutex_inode']==plan['common_mutex_inode'],'Unclean or wrong-lock reader process')
    for stream in ['stdout','stderr']:
        item=raw[stream];path=NATIVE/'native-process'/(stream+'.bin')
        require(item['bytes']==path.stat().st_size==0 and item['sha256']==sha(path),'Reader diagnostic drift')
    for path,digest in plan['pins'].items():
        require(not Path(path).is_absolute() and '..' not in Path(path).parts and sha(ROOT/path)==digest,'Changed pinned count/policy artifact: '+path)
    for path,item in native['artifacts'].items():
        p=ROOT/path;require(p.is_file() and sha(p)==item['sha256'] and p.stat().st_size==item['bytes'],'Changed native capture artifact: '+path)
    actual={str(p.relative_to(ROOT)) for p in (NATIVE/'reader').rglob('*') if p.is_file()}
    require(actual==set(native['artifacts']),'Native AST artifact inventory differs')
    frontend=FRONTEND.read_bytes();entry=b'\nSourceCountReader.main(System.argv())\n'
    require(frontend.endswith(entry) and (HERE/'retained-reader-host-v1.exs').read_bytes()
        ==frontend[:-len(entry)]+b'\n'+(HERE/'reader_host.exs').read_bytes(),'Retained reader function prefix changed')
    require(plan['counter']==ref(COUNTER) and plan['frontend']==ref(FRONTEND),'Wrong retained frontend/counter binding')
    result=counter.replay(PLAN,NATIVE/'reader',fixture_contract=CONTRACT)
    require(result['native_fixture_expectations_passed'] is True and len(result['fixture_checks'])==14,'Retained fixture replay differs')
    historical=load(OLD_REPLAY);old_directory=ROOT/'experiments/elixir/source-counts-v1/run-v1/reader'
    controls=[]
    for identity,role in [('parent-main','application'),('support','application-helper'),('runner','application-launcher')]:
        original_id='elixir-knucleotide-optimized--'+role
        observed=result['files'][identity];old=historical['files'][original_id]
        require(observed==old,'Exact parent/helper/launcher ownership replay differs: '+identity)
        current=NATIVE/'reader'/identity;previous=old_directory/original_id
        for name in ['source.exs','ast.json','ast.etf','formatted.exs','formatted-ast.json']:
            require((current/name).read_bytes()==(previous/name).read_bytes(),'Exact retained native source/AST/formatter control differs: '+identity+'/'+name)
        controls.append(dict(id=identity,historical_id=original_id,exact_counter_result=True,exact_native_artifact_bytes=True,
            exact_canonical_events=True,exact_expansions=True,original_normalized_loc=observed['original']['normalized_loc'],
            original_physical_loc=observed['original']['physical_loc'],formatted_physical_loc=observed['formatted']['physical_loc']))
    require([(r['original_normalized_loc'],r['original_physical_loc']) for r in controls]==[(47,39),(61,53),(1,1)],'Historical parent count control differs')
    parent=load(ROOT/'programs/elixir/knucleotide/elixir-knucleotide-optimized/program.json')
    require(parent['loc']==47 and parent['physical_loc']==39 and parent['source_accounting']['previous_loc']==109,'Public parent application boundary differs')
    for r in parent['sources'][1:]:require(r['role']=='runtime-support' and r['role_evidence']['included_in_application_loc'] is False,'Historical generic support is no longer excluded')
    files={}
    for identity in ['parent-main','serial-main','parallel-main','support','runner']:
        observed=result['files'][identity];text=(NATIVE/'reader'/identity/'source.exs').read_bytes().decode()
        files[identity]=dict(source_sha256=observed['source_sha256'],source=ref(NATIVE/'reader'/identity/'source.exs'),
            native_ast=ref(NATIVE/'reader'/identity/'ast.json'),formatted_source=ref(NATIVE/'reader'/identity/'formatted.exs'),
            formatted_ast=ref(NATIVE/'reader'/identity/'formatted-ast.json'),
            role='application' if identity.endswith('-main') else 'runtime-support',
            included_in_application_loc=identity.endswith('-main'),
            observed_retained_rule_loc=observed['original']['normalized_loc'],observed_physical_loc=observed['original']['physical_loc'],
            observed_formatted_physical_loc=observed['formatted']['physical_loc'],diagnostics=copy.deepcopy(observed['original']['diagnostics']),
            formatted_diagnostics=copy.deepcopy(observed['formatted']['diagnostics']),line_ledger=line_ledger(text,observed['original']),
            canonical_events=copy.deepcopy(observed['original']['canonical_events']),
            expression_continuations=copy.deepcopy(observed['original']['expression_continuations']))
    profiles=[]
    for name in ['serial','parallel']:
        f=files[name+'-main'];support=[files['support'],files['runner']]
        proposed=f['observed_retained_rule_loc']
        profiles.append(dict(id=name,source_sha256=f['source_sha256'],source=f['source'],
            application_loc=None,physical_loc=None,formatted_loc=None,independent_review_approved=False,
            retained_rule_proposed_loc=proposed,candidate_physical_loc=f['observed_physical_loc'],
            candidate_formatted_application_loc=f['observed_formatted_physical_loc'],
            application_files=[name+'-main'],excluded_support_files=['support','runner'],
            excluded_support_loc=sum(v['observed_retained_rule_loc'] for v in support),excluded_support_physical_loc=sum(v['observed_physical_loc'] for v in support),
            whole_bundle_retained_rule_loc=proposed+62 if proposed is not None else None,
            whole_bundle_physical_loc=f['observed_physical_loc']+54,
            diagnostics=f['diagnostics'],formatted_diagnostics=f['formatted_diagnostics'],
            uniform_logical_loc=None,uniform_logical_grammar_qualified=False))
    ownership=dict(schema='elixir-rolling-retained-source-review.v1',status='NATIVE-REPLAY-AWAITING-INDEPENDENT-OWNER-REVIEW',
        controller=ref(Path(__file__)),native_capture=ref(NATIVE/'report.json'),plan=ref(PLAN),counter=ref(COUNTER),frontend=ref(FRONTEND),
        qualified_predecessor=ref(ROOT/'experiments/elixir/source-units-v1/qualified-source-counts.json'),
        rule_version=result['rule_version'],grammar=result['grammar'],application_policy='application-loc-v1',
        files=files,profiles=profiles,controls=controls,retained_fixture_expectations_passed=True,
        parser_functions_unchanged=True,counter_constants_unchanged=True,frozen_files_edited=False,
        boundary=dict(parent_current_application=[47,39],parent_historical_whole_bundle=[109,93],excluded_generic_support=[62,54],
            policy=ref(ROOT/'docs/methodology.md'),parent_manifest=ref(ROOT/'programs/elixir/knucleotide/elixir-knucleotide-optimized/program.json'),
            note='The original source-count qualification counted complete bundles. The published application policy subsequently excluded the unchanged general helper61/53 and launcher1/1. Only each rolling main is proposed for application LOC; all benchmark parsing/counting/format construction functions remain inside that main. Existing frozen native/pilot packet prose is clarified here without changing it.'),
        retained_policy_limit='This replays the already-qualified retained Elixir owner policy, including written closers and retained data/expression continuation rows. It does not certify logical-source-owners uniform-axis semantics or claim a newly qualified whole-language frontend.',
        source_evaluations=0,subject_recompilations=0,subject_main_invocations=0,
        canonical_loc_qualified=False,formatted_loc_qualified=False,uniform_logical_axis_qualified=False,chart_admission=False)
    return result,ownership


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    require(args.prepare!=args.check,'Choose one mode');result,ownership=make()
    if args.prepare:
        require(not REPLAY.exists() and not LEDGER.exists(),'Fresh replay/ledger required');REPLAY.write_bytes(encoded(result));LEDGER.write_bytes(encoded(ownership))
    else:require(load(REPLAY)==result and load(LEDGER)==ownership,'Stale replay/source ledger')
    print(json.dumps(dict(status=ownership['status'],proposals=[{k:r[k] for k in ['id','retained_rule_proposed_loc','candidate_physical_loc','candidate_formatted_application_loc']} for r in ownership['profiles']],
        source_count_approved=False,uniform_logical_axis_qualified=False,ledger=ref(LEDGER))))
