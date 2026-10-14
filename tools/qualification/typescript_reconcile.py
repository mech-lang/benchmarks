"""Independently reconcile completed retained TypeScript full60 evidence.

No producer, sampler, runtime or benchmark is imported or executed. The pure
ledger validates every planned slot, receipt, outer supervisor and matched
control; the file phase requires completed durable/private/common leases and
rechecks the complete physical closure. Failed forms keep their real evidence
and never receive a median or ratio from partial samples. This is not a dataset
importer and grants no chart admission or a new runtime observation.
"""
import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(__file__).with_name('prolog_reconcile.py')
HELPER_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
raw_helper = HELPER.read_bytes()
if hashlib.sha256(raw_helper).hexdigest() != HELPER_SHA:
    raise ValueError('Independent receipt reconciliation helper changed')
spec = importlib.util.spec_from_file_location('typescript_independent_receipt_primitives', HELPER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw_helper, str(HELPER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
BENCHES, SIZES, LOCK, POWER = r.BENCHES, r.SIZES, r.LOCK, r.POWER
AGGREGATE, check_attempt, check_outer = r.AGGREGATE, r.check_attempt, r.check_outer
Files, inventory = r.Files, r.inventory
PACKET = ROOT/'experiments/typescript/full60-v1'
CONTROLLER_SHA = '5e1b5583e372f103696ca4d8908e6db7b950e7dee0ba139c77400d2d092a425d'
WORK_SHA = 'b4c48ede5c375e3f2f1ab37fe4975199ba539bcd06fc4ab3dd93677525ec02f2'
LOC_SHA = 'c8e3461eebdfd73f6052debad012345e4ef4206bdaa2f1e916b8cfbb0d00ebef'
QUALIFICATION_REFS = {'work': ('experiments/typescript/required-work-v1/qualified-work-v1.json',
          'b4c48ede5c375e3f2f1ab37fe4975199ba539bcd06fc4ab3dd93677525ec02f2'),
 'runtime': ('experiments/typescript/runtime-metadata-v1/qualified-runtime-metadata-v1.json',
             '4678a7e7ce8cf63834f5e224b5b488a6b914c374f31d87917cd36dcaa4695aa2'),
 'loc': ('experiments/typescript/source-units-v1/qualified-source-counts-v1.json',
         'c8e3461eebdfd73f6052debad012345e4ef4206bdaa2f1e916b8cfbb0d00ebef'),
 'static': ('experiments/typescript/required-work-v1/static-review-v1.json',
            '454b93f894b4dba6edae697efa69fbe7b7e966c02a8e68e5d3a750da5d1fa71c'),
 'bounded_review': ('experiments/typescript/bounded-v1/independent-results-review-v1.json',
                    '7aa31fae40150228f1023b1cf8932feca3c8599d708f82189b8bdaf55c98609c'),
 'outputs': ('experiments/typescript/single-entry-work-v1/reconciliation-v1/output-review.json',
             'db88a1640b9a4e7b68bb1f0d07a82ae1f054483149761882d3dfa619554b98c8'),
 'tree': ('experiments/typescript/single-entry-work-v1/reconciliation-v1/tree-native-review.json',
          '0fda71f703b53e3aad0e16c9c9d4c07b7d0af31b106aba9674c114a2e3053091'),
 'pi': ('experiments/typescript/single-entry-work-v1/pi-peer-review-v1.json',
        '190cf64172650264858b173a9bdd4068fd25b62bbc853fd392e539ad43d868fe'),
 'loc_replay': ('experiments/typescript/source-units-v1/replay-v1/replay.json',
                '320899df10d4b9ba3e7729354008db8e02771d50a047f41bed01f47c98fba8f0'),
 'compiled_plan': ('experiments/typescript/native-stage-v1/plan-v1.json',
                   '520b14aea813379f036053ce7bc6e7b21ad016775407536ee3195703444412c4'),
 'compiled_report': ('experiments/typescript/native-stage-v1/run-v1/report.json',
                     'ec6fb9979e5de31cd8496f01e338fef80f322f118def9923d61b8c3b5ca9e83b'),
 'compiled_terminal': ('experiments/typescript/native-stage-v1/run-v1/terminal.json',
                       '2abf7814b6063b15561af165bed377d77f6616597d555ec7f4d967c421372038'),
 'bounded_plan': ('experiments/typescript/bounded-v1/plan-v1.json',
                  '5156050046a006d2b1aa0068bc7b24302bd8fc3dd6d796d4b7dca7e4acf58c8a'),
 'bounded_report': ('experiments/typescript/bounded-v1/run-v1/report.json',
                    'd11f66e11071934d4bc7b27312c9d2b38adca7b045a9b490db6d16775c05ce29'),
 'bounded_terminal': ('experiments/typescript/bounded-v1/run-v1/terminal.json',
                      '7b42777781781726488415999c7600e79afb92a0bc863cb3f0a326a9c4737662'),
 'capture_plan': ('experiments/typescript/single-entry-work-v1/plan-v1.json',
                  '6e5d6b72f86dcb46e2e759b70b9dd0e3a11f898472686bd9e33dccbd7e10f4ca'),
 'capture_report': ('experiments/typescript/single-entry-work-v1/run-v1/report.json',
                    '4c23b5feb3d79812659d7e6d0c212467cd970294bf2264880de13bfd1a6dbf12'),
 'capture_terminal': ('experiments/typescript/single-entry-work-v1/run-v1/terminal.json',
                      'd8fa860d2c1bb2e4a8d7788dc4197355b7755f727da0d1cc6443abddc799d8a1'),
 'pi_plan': ('experiments/typescript/single-entry-work-v1/plan-pi-v1.json',
             '96a0ce9449982d5039ca0ac8ec48379339cb7e5a53db67adb3b3a7ac95d7fb87'),
 'pi_report': ('experiments/typescript/single-entry-work-v1/run-pi-v1/report.json',
               'fd8f59f43a65a7d2e04b8bff9d9a39b3f3b38ec02f81b237714f4c1558015d73'),
 'pi_terminal': ('experiments/typescript/single-entry-work-v1/run-pi-v1/terminal.json',
                 '4a5e138b0725c91e759300438a9e150c7827becf345481ea5951bfb1bba02c4a')}
SCHEMA = 'typescript-independent-full60-reconciliation-v1'
NODE = '/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
NODE_SHA = '27db838bb204ef7c21df2931f5656e4c8fb32e6e947f363a402b49714d32b5b1'
CLBG=Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
CONTROL_REFS={
    'control_audit':(str(CLBG/'r-apl-uiua-comparison/20261011/source-audit-r.json'),'d76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'),
    'control_mandel':(str(CLBG/'mandelbrot/experiments/20261011-array-state/source-modes-study/full-study/manifest.json'),'fbffba7b5674e889ac9e5088bbb2e2d8499df41f5d9b4c677be38d831091680f'),
}
TIMING_POLICY=('Fresh direct Node process including startup, retained JavaScript loading, tiered JIT, full input, '
               'all work, complete output and shutdown; subject compilation, pin hashing and output validation excluded')
SUPPORT_PINS={
    str(ROOT/'tools/qualification/elixir_full.py'):'5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703',
    str(ROOT/'tools/qualification/prolog_full.py'):'0d75d33bb77d3715ca7adcd8c07fcf3b659be472c2ef84c063dec57ee4b8eb94',
    str(ROOT/'tools/qualification/prolog_supervisor.py'):'5458bdf5e58465cb21156a2140657066b4706aa2a0941fe3efde8758207574b4',
    str(HELPER):HELPER_SHA,str(r.HELPER):r.HELPER_SHA,
    p.PYTHON:'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e',
    str(PACKET/'README.md'):'ef93a2e8cd44a3193f92507979633caa4549a2955595923a55f6a1964e345b41',
}
SUPPORT_PINS.update({str(CLBG/path):digest for path,digest in {
    'r-apl-uiua-comparison/20261011/run.py':'5b2a038cfae4112e9e2eee79c3cd57ccc6a1521812828c47bf28986d6a8e139b',
    'r-apl-uiua-comparison/20261011/prepare.py':'27fcf050ed21db40e747f2e8801ca6f227d82f1ea98f8592bba7b10a768109e5',
    'array-comparison/all-20261009/run.py':'8b7f1b408fb5838dc6adc2404bcfa6146e48e770e602fbe78255454f3cacb8c7',
    'compact/run.py':'6926e288a7b9b59b030c9226227df967aa1d92b3e395789467706e2241d987ae',
    'nbody/run.py':'e907f71b3fdf8fc6f65adc76aab6dfc424811875388c14f0eb2f31e14e9cffcf',
    'r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/remaining_owner.py':'55581d56609803243b3be264e6a2e37229be06789c22788bbf8cdb6ff6828544',
}.items()})
FULL_REFERENCES = {'regexredux': {'bytes': 298, 'sha256': 'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'},
 'revcomp': {'bytes': 254166745,
             'sha256': 'e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'},
 'pidigits': {'bytes': 16893, 'sha256': 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'},
 'spectralnorm': {'bytes': 12, 'sha256': 'f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'},
 'mandelbrot': {'bytes': 32000015,
                'sha256': '609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'},
 'fasta': {'bytes': 254166745, 'sha256': '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'},
 'knucleotide': {'bytes': 259, 'sha256': 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'},
 'binarytrees': {'bytes': 455, 'sha256': '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'},
 'nbody': None,
 'fannkuchredux': {'bytes': 29, 'sha256': '4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'}}

def absolute_ref(value):
    path=Path(value['path']);path=path if path.is_absolute() else ROOT/path
    require(path.is_absolute() and '..' not in path.parts and p.digest(value['sha256']),'Unsafe source evidence reference')
    return dict(path=str(path),sha256=value['sha256'])


def recorded_pins(value):
    """Path/digest references are evidence inputs, never substituted by aliases."""
    result={}
    def add(path,digest):
        require(path not in result or result[path]==digest,'Conflicting qualification reference')
        result[path]=digest
    def visit(item):
        if isinstance(item,dict):
            if 'path' in item and 'sha256' in item:
                ref=absolute_ref(item);add(ref['path'],ref['sha256'])
            for key,child in item.items():
                if isinstance(child,dict) and 'sha256' in child and 'bytes' in child and 'path' not in child and '/' in key:
                    ref=absolute_ref(dict(path=key,sha256=child['sha256']));add(ref['path'],ref['sha256'])
                visit(child)
        elif isinstance(item,list):
            for child in item:visit(child)
    visit(value);return result


def validate_typescript_row(row,pins):
    sources,env=row['physical_inputs'],row['runtime_environment']
    require(len(sources)==1 and sources[0]['role']=='application' and sources[0]['counted'] is True,
            'Exactly one counted authored TypeScript source required')
    require(sources[0]['path']==row['source'] and sources[0]['sha256']==row['source_sha256']
        and pins.get(row['compiled_source'])==pins.get(row['source'])==row['source_sha256'],'Authored/compiled bytes differ')
    project=Path(row['compiled_source']).parent;native=project.parent
    expected=dict(PATH='/usr/bin:/bin',HOME=str(native/'home'),TMPDIR=str(native/'tmp'),LC_ALL='C',LANG='C',TZ='UTC',UV_THREADPOOL_SIZE='8')
    same(env,expected,'Unqualified Node environment, preload or compile cache')
    require(row['cwd']==str(project) and row['binary']==NODE and row['binary_sha256']==NODE_SHA,
        'Retained Node or working directory differs')
    for name in ('javascript','source_map'):
        ref=row[name];require(set(ref)=={'path','sha256'} and pins.get(ref['path'])==ref['sha256'],'Unbound generated application')
    require(row['javascript']['path']==str(project/'emitted'/(row['benchmark']+'.js'))
        and row['source_map']['path']==row['javascript']['path']+'.map','Emitted main/map ownership differs')
    command=[NODE,row['javascript']['path']]
    if row['benchmark'] not in ('regexredux','knucleotide','revcomp'):command.append('{n}')
    same(row['command'],command,'Direct Node command changed flags, main or argument')
    require(row['variant']=='v1' and row['id']=='typescript-'+row['benchmark']+'-v1'
        and row['source_alias_of'] is None and row['optimization_claim'] is False
        and row['runtime_policy_changes']==row['diagnostic_flags']==[],'Source identity or default timing policy differs')
    require(row['source_work_qualified'] is row['canonical_loc_qualified'] is True
        and row['formatted_loc_qualified'] is False and row['formatted_loc'] is None and row['loc']==row['canonical_loc']
        and all(p.integer(row[name]) and row[name]>0 for name in ('canonical_loc','physical_loc')),'Canonical-only count policy differs')
    require(pins.get(row['source_count_projection']['path'])==row['source_count_projection']['sha256'],'Unbound count projection')
    require(row['memory_policy']=='Retained Node/V8 defaults; no custom heap or collector; UV_THREADPOOL_SIZE=8',
        'Runtime memory policy differs')


def prerequisite_inventory(plan,verify_files=False):
    closures=plan['prerequisite_artifact_closures']
    expected_directories={str(ROOT/'experiments/typescript'/path) for path in
        ('native-stage-v1/run-v1','bounded-v1/run-v1','single-entry-work-v1/run-v1',
         'single-entry-work-v1/run-pi-v1','source-units-v1/replay-v1')}
    require(len(closures)==5 and {item['directory'] for item in closures}==expected_directories,'Five exact qualification closures required')
    for item in closures:
        directory=Path(item['directory']);expected=set()
        for name,record in item['artifacts'].items():
            part=Path(name);path=str(directory/part)
            require(not part.is_absolute() and '..' not in part.parts and p.integer(record['bytes']) and record['bytes']>=0
                and p.digest(record['sha256']) and plan['pins'].get(path)==record['sha256'],'Unsafe or unbound prerequisite artifact')
            expected.add(path)
            if verify_files:require(Path(path).stat().st_size==record['bytes'],'Prerequisite artifact size differs')
        require(str(directory/'report.json') in expected or str(directory/'replay.json') in expected,'Qualification summary omitted')
        if verify_files:same(sorted(inventory(directory)),sorted(expected),'Closed prerequisite inventory differs')


def qualified_bindings(plan,documents,metadata_sizes):
    """Independently join reviewed native, authored, emitted and counted inputs."""
    d,pins=documents,plan['pins']
    def reference(actual,name):
        relative,digest=QUALIFICATION_REFS[name]
        same(absolute_ref(actual),dict(path=str(ROOT/relative),sha256=digest),'Qualification link differs: '+name)
    def keyed(rows):
        values={row['id']:row for row in rows}
        require(len(rows)==len(values)==10 and set(values)=={'typescript-'+b+'-v1' for b in BENCHES},
            'Exactly ten distinct authored implementations required')
        return values
    work,counts,runtime=d['work'],d['loc'],d['runtime']
    require(work['schema']=='typescript-qualified-required-work-v1'
        and work['status']=='ten-retained-required-work-contracts-qualified'
        and work['source_work_qualified'] is work['required_work_qualified'] is True
        and work['qualified_contracts']==27 and work['bounded_total_cases']==149
        and work['bounded_successful_cases']==142 and work['bounded_expected_rejections']==7
        and work['required_work_diagnostic_subject_invocations']==2 and work['capability_listing_invocations']==1,
        'Incomplete ten-workload admission')
    require(all(work[k] is True for k in ('original_producer_receipts_unchanged','original_three_command_stage_preserved_failed',
        'first_tree_capture_reused_without_rerun','missing_pi_captured_once','old_producer_flags_preserved')),
        'Original failed capture or missing-only continuation was rewritten')
    for key,name in [('static','static'),('bounded','bounded_review'),('outputs','outputs'),('tree','tree'),('pi','pi'),
                     ('runtime','runtime'),('source_counts','loc')]:reference(work['evidence'][key],name)
    require(d['tree']['tree_required_work_supported'] is True and d['tree']['argument']==21
        and d['pi']['both_divisions_dominate_comparison'] is True and d['pi']['profile']=='typescript-pidigits-v1'
        and d['outputs']['application_outputs_qualified'] is d['outputs']['previous_stage_preserved_failed'] is True,
        'Required-work or lossless output decision incomplete')
    bounded=d['bounded_review']
    require(bounded['actual_native_processes']==149 and bounded['successful_output_cases']==142 and bounded['expected_rejection_cases']==7
        and all(bounded[k] is True for k in ('all_output_contracts_satisfied','all_birth_parent_reap_and_empty_group_receipts_passed',
            'all_native_intervals_serial','all_expected_failures_retained_verbatim','all_validated_snapshots_equal_final_inventory')),
        'Independent bounded review incomplete')
    for kind in ('plan','report','terminal'):reference(bounded[kind],'bounded_'+kind)
    require(runtime['runtime_publication_metadata_qualified'] is runtime['runtime_dependency_closure_qualified'] is
        runtime['declared_runtime_dependency_closure_qualified'] is True
        and runtime['actual_loaded_image_inventory_observed'] is runtime['observed_in_each_timed_process'] is False
        and runtime['node']['path']==NODE and runtime['node']['expected_full_sha256']==NODE_SHA,
        'Static declared runtime scope differs')
    policy=runtime['default_runtime_policy']
    require(policy['external_runtime_packages']==[] and policy['node_options_or_preloads'] is policy['forced_optimization'] is
        policy['custom_heap_or_gc_flags'] is False,'Qualified default runtime policy differs')
    require(counts['canonical_loc_qualified'] is counts['fixture_expectations_all_passed'] is True
        and counts['formatted_loc_qualified'] is False and counts['formatted_loc'] is None,'Canonical-only count decision differs')
    for doc in (work,counts,runtime):
        require(doc['full_timings_qualified'] is doc['chart_admission'] is False and doc['benchmark_samples']==0,
            'Pre-timing evidence cannot become a timing producer')
    same(plan['runtime_dependency_scope'],runtime['qualification_scope'],'Plan overstates runtime dependency observation')
    reference(plan['qualified_runtime'],'runtime')
    compiled=d['pi_plan']['compiled']
    same(compiled,d['bounded_plan']['compiled'],'Bounded and required-work emitted inputs differ')
    same(compiled,d['capture_plan']['compiled'],'Original tree capture used different emitted inputs')
    require(compiled['node']==NODE,'Another Node runtime')
    reference(dict(path=compiled['report'],sha256=compiled['report_sha256']),'compiled_report')
    reference(dict(path=compiled['terminal'],sha256=compiled['terminal_sha256']),'compiled_terminal')
    original,counted,reviewed=keyed(compiled['profiles']),keyed(counts['profiles']),keyed(work['profiles'])
    same(sorted(work['qualified_profiles']),sorted(original),'Work decision omits or aliases an implementation')
    for identity,source in original.items():
        row=plan['manifests'][source['benchmark']]['profiles'][0];owner,proof=counted[identity],reviewed[identity]
        require(row['id']==identity and row['benchmark']==source['benchmark']==owner['workload']==proof['benchmark'],
            'Timed row aliases another authored workload')
        same(row['binary'],compiled['node'],'Timed Node differs from required-work execution')
        same(row['binary_sha256'],NODE_SHA,'Timed Node bytes differ')
        for field in ('source','source_sha256','compiled_source','javascript','source_map'):
            same(row[field],source[field],'Timed emitted/source identity differs: '+field)
        same(row['source'],absolute_ref(owner['source'])['path'],'Counted source differs')
        same(row['source'],absolute_ref(proof['source'])['path'],'Required-work source differs')
        require(row['source_sha256']==owner['source']['sha256']==proof['source']['sha256']==proof['staged_source']['sha256'],
            'Typed or staged source bytes differ')
        same(row['compiled_source'],absolute_ref(proof['staged_source'])['path'],'Staged compiler input differs')
        same(row['javascript'],absolute_ref(proof['emitted_javascript']),'Required-work emitted code differs')
        same(row['source_map'],absolute_ref(proof['source_map']),'Required-work source map differs')
        same(owner['native_ast'],proof['native_ast'],'Native authored AST differs')
        same(row['runtime_dependency_scope'],runtime['qualification_scope'],'Per-profile dependency scope differs')
        require(owner['complete_nonoverlapping_source_owner_coverage'] is owner['manual_expectation_matches'] is True
            and owner['canonical_loc_qualified'] is True and owner['formatted_loc_qualified'] is False and owner['formatted_loc'] is None
            and proof['source_work_qualified'] is proof['required_work_qualified'] is True
            and all(contract['qualified'] is True for contract in proof['contracts']),'Incomplete source work or owner coverage')
        for field in ('canonical_loc','physical_loc'):same(row[field],owner[field],'Count differs: '+field)
        same(row['source_count_projection'],absolute_ref(owner['projection']),'Count projection differs')
    require(sum(len(v['contracts']) for v in reviewed.values())==27,'Required-work contract coverage changed')
    for name in ('compiled_plan','compiled_report','bounded_plan','bounded_report','capture_plan','capture_report','pi_plan','pi_report'):
        for path,digest in d[name]['pins'].items():require(pins.get(path)==digest,'Inherited qualification pin omitted: '+path)
    for mapping in (counts['native_prerequisite_pins'],d['loc_replay']['prerequisite_pins']):
        for path,digest in mapping.items():require(pins.get(path)==digest,'Owner/parser evidence omitted')
    for name in ('work','loc','runtime','static','bounded_review','outputs','tree','pi'):
        for path,digest in recorded_pins(d[name]).items():require(pins.get(path)==digest,'Reviewed evidence reference omitted: '+path)
    expected_closures={}
    for name,expected_status in [('compiled','compile-and-AST-captures-recorded-awaiting-independent-review'),
            ('bounded','all149-bounded-output-contracts-passed-awaiting-required-work-review'),('capture','failed'),
            ('pi','missing-pi-raw-capture-retained-awaiting-output-and-work-review')]:
        report,terminal=d[name+'_report'],d[name+'_terminal']
        require(report['status']==terminal['status']==expected_status and report['active'] is None
            and report['integrity_errors']==terminal['integrity_errors']==[]
            and terminal['report_sha256']==QUALIFICATION_REFS[name+'_report'][1],'Qualification closure changed: '+name)
        artifacts=dict(terminal['available_evidence'])
        for kind in ('report','terminal'):
            key=name+'_'+kind;relative,digest=QUALIFICATION_REFS[key]
            record=dict(bytes=metadata_sizes[key],sha256=digest)
            require(Path(relative).name not in artifacts or artifacts[Path(relative).name]==record,'Conflicting closed metadata bytes')
            artifacts[Path(relative).name]=record
        expected_closures[str((ROOT/QUALIFICATION_REFS[name+'_report'][0]).parent)]=artifacts
    require(d['capture_report']['error']=='Complete prescribed stdout absent after native diagnostics'
        and d['capture_report']['native_processes_started']==2 and d['pi_report']['native_processes_started']==1,
        'Retained diagnostic history changed')
    replay=d['loc_replay'];reference(counts['replay'],'loc_replay')
    require(len(replay['result_files'])==40 and len(replay['fixture_checks'])==30 and len(replay['applications'])==10
        and replay['native_reader_artifact_files']==160,'Canonical replay coverage differs')
    artifacts=dict(replay['result_files']);artifacts['replay.json']=dict(bytes=metadata_sizes['loc_replay'],sha256=QUALIFICATION_REFS['loc_replay'][1])
    expected_closures[str((ROOT/QUALIFICATION_REFS['loc_replay'][0]).parent)]=artifacts
    same({item['directory']:item['artifacts'] for item in plan['prerequisite_artifact_closures']},expected_closures,
        'Prerequisite inventory differs from actual retained closure')
    audit, special = d['control_audit'], d['control_mandel']
    require(audit['status']=='reviewed' and {row['benchmark'] for row in audit['controls']}==set(BENCHES),
            'Original control review differs')
    for bench in BENCHES:
        name='control_mandel' if bench=='mandelbrot' else 'control_audit'
        origin=(next(row for row in special['profiles'] if row['id']=='row16-aot-control') if bench=='mandelbrot'
                else next(row for row in audit['controls'] if row['benchmark']==bench))
        row=plan['manifests'][bench]['profiles'][1]
        for field in ('benchmark','language','source','source_sha256','binary','binary_sha256','command','cwd','runtime_environment'):
            same(row[field],origin[field],'Matched control execution differs: '+field)
        same(row['control_provenance'],dict(path=CONTROL_REFS[name][0],sha256=CONTROL_REFS[name][1],original_id=origin['id']),
             'Control provenance differs')
        for path,digest in origin.get('support',{}).items():
            require(pins.get(path)==digest,'Matched control support pin omitted')
    for relative in ('knucleotide/.build/knucleotide-input25000000.txt','regexredux/.build/input5000000.txt',
                     'pidigits/inputs/output-full.txt','regexredux/inputs/output-full.txt'):
        path=str(CLBG/relative)
        require(pins.get(path)==audit['pins'][path],'Full input/reference bytes omitted')
    return dict(qualified_sources=10, canonical_counts=10, formatted_counts=0,
                bounded_cases=149, reused_native_work_captures=2, fresh_qualification_executions=0,
                runtime_publication_metadata_qualified=True, runtime_dependency_scope=runtime['qualification_scope'],
                actual_loaded_image_inventory_observed=False, observed_in_each_timed_process=False)


def check_durable(durable, plan_path, plan_sha, plan):
    """Validate the exact retained Python -I -S -B -u durable launch."""
    request, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    command = [p.PYTHON, '-I', '-S', '-B', '-u', plan['controller'], 'run',
               '--plan', plan_path, '--plan-sha256', plan_sha]
    same(request['command'], command, 'Durable command is not the exact prepared TypeScript run')
    require(p.digest(plan['pins'].get(p.PYTHON)), 'Unpinned TypeScript interpreter')
    for item in (launch, worker, started):
        same(item['command'], command, 'Durable argv disagreement')
        require(item['cwd'] == request['cwd'] == plan['repository'], 'Durable cwd disagreement')
    require(p.integer(request['schema_version'], 1) and request['common_mutex_owned_by_target_command'] is True,
            'Wrong durable ownership request')
    for item in (request, launch, ended):
        require(item['automatic_retry'] is False and item['qualification_granted'] is False, 'Durable policy changed')
    require(worker['qualification_granted'] is False and worker['inherited_private_lease'] is True
            and worker['detached_session'] is True and worker['common_mutex_owned_by_target_command'] is True,
            'Worker ownership incomplete')
    require(ended['status'] == 'command-exited-zero-awaiting-report-review'
            and p.integer(ended['exit_code'], 0) and ended['actual_command_started'] is True
            and ended['command_identity_observation_missing'] is False
            and started['command_identity_observation_missing'] is False, 'Durable process did not finish normally')
    same(ended['stop_signals'], [], 'Durable stop signal recorded')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Durable terminal contains a failure')
    first_identity, final_identity = [p.process_identity(item['command_identity']) for item in (started, ended)]
    same(final_identity, first_identity, 'Command identity differs at terminal')
    same(first_identity[2], ' '.join(command), 'Observed controller command differs from durable argv')
    worker_identity = p.process_identity(worker['worker_identity'])
    same(p.process_identity(ended['worker_identity']), worker_identity, 'Worker identity differs at terminal')
    same(p.process_identity(launch['worker_identity']), worker_identity, 'Launch worker identity differs')
    require(p.integer(started['command_pid']) and started['command_pid'] > 0
            and p.integer(ended['command_pid'], started['command_pid'])
            and p.integer(first_identity[0], started['command_pid']), 'Missing command PID/identity')
    require(all(item['command_identity']['listing'].split(None, 7)[1] == str(worker_identity[0])
                for item in (started, ended)), 'Controller parent differs from durable worker')
    require(p.timestamp(request['created_at']) <= p.timestamp(worker['started_at'])
            <= p.timestamp(started['started_at']) <= p.timestamp(ended['finished_at']),
            'Durable times are inconsistent')


def schedule(plan):
    require(plan['schema'] == 'typescript-qualified-retained-full60-v1'
            and plan['status'] == 'prepared-awaiting-independent-review'
            and plan['pins_verified'] is True, 'Unprepared or wrong TypeScript plan')
    require(plan['controller_sha256'] == CONTROLLER_SHA
            and plan['pins'][plan['controller']] == CONTROLLER_SHA, 'Changed frozen controller')
    require(plan['controller']==str(ROOT/'tools/qualification/typescript_full.py')
            and plan['formatted_loc_qualified'] is False,'Changed TypeScript timing implementation')
    for name, expected in (('source_work_profiles', 10), ('canonical_loc_profiles', 10),
            ('formatted_loc_profiles', 0), ('retained_bounded_cases', 149), ('samples', 3),
            ('full_processes', 60), ('typescript_samples', 30), ('matched_mech_samples', 30),
            ('new_native_probes', 0), ('compiler_invocations', 0), ('fixture_reexecutions', 0),
            ('bounded_reexecutions', 0), ('count_replays', 0)):
        require(p.integer(plan[name], expected), 'Changed plan count: '+name)
    require(plan['original_files_mutated'] is False and plan['chart_admission'] is False
            and plan['full_timings_qualified'] is False and plan['no_automatic_retry'] is True
            and plan['continuous_common_mutex'] is True and plan['shared_timing_lock'] == str(LOCK)
            and p.integer(plan['common_mutex_inode'], p.LOCK_INODE), 'Changed plan policy')
    for name, expected in (('qualified_work', WORK_SHA), ('qualified_source_counts', LOC_SHA), ('qualified_runtime', QUALIFICATION_REFS['runtime'][1])):
        binding = plan[name]
        reference_name={'qualified_work':'work','qualified_source_counts':'loc','qualified_runtime':'runtime'}[name]
        require(binding['path']==str(ROOT/QUALIFICATION_REFS[reference_name][0])
                and binding['sha256'] == expected and plan['pins'][binding['path']] == expected,
                'Changed qualification prerequisite')
    require(plan['repository']==str(ROOT) and plan['timing_policy']==TIMING_POLICY,'Repository or timer scope differs')
    for path,digest in SUPPORT_PINS.items():
        require(plan['pins'].get(path)==digest,'Measurement support omitted or changed: '+path)
    for path,digest in CONTROL_REFS.values():
        require(plan['pins'].get(path)==digest,'Control provenance omitted or changed')
    for name,(relative,digest) in QUALIFICATION_REFS.items():
        require(plan['pins'].get(str(ROOT/relative))==digest,'Required qualification input omitted: '+name)
    prerequisite_inventory(plan)
    require(set(plan['manifests']) == set(BENCHES), 'Ten manifests required')
    slots, profiles = [], {}
    for bench in BENCHES:
        manifest = plan['manifests'][bench]
        require(manifest['benchmark'] == bench and p.integer(manifest['size'], SIZES[bench])
                and p.integer(manifest['samples'], 3) and p.integer(manifest['timeout_seconds'], 21600)
                and p.integer(manifest['supervisor_timeout_seconds'], 22200)
                and p.integer(manifest['maximum_rss_mib'], 10240), 'Changed workload or bounds')
        require(manifest['canonical_full_workload'] is True and manifest['chart_admission'] is False
                and manifest['no_automatic_retry'] is True and manifest['shared_timing_lock'] == str(LOCK)
                and manifest['retained_subject_compilation_outside_timer'] is True
                and manifest['runtime_and_script_loading_inside_timer'] is True
                and manifest['runtime_JIT_inside_timer'] is True
                and p.integer(manifest['direct_main_invocations_per_sample'], 1), 'Changed timing policy')
        same(manifest['full_output_reference'],FULL_REFERENCES[bench],'Canonical complete-output reference differs')
        ids = [f'typescript-{bench}-v1', 'mech-aot-control']
        rows = manifest['profiles']
        same([row['id'] for row in rows], ids, 'Changed retained cohort')
        same([row['language'] for row in rows], ['typescript', 'mech'], 'Changed language cohort')
        offset=list(BENCHES).index(bench)%2
        orders = [dict(round=i+1, profiles=ids[(i+offset)%2:]+ids[:(i+offset)%2]) for i in range(3)]
        same(manifest['orders'], orders, 'Changed rotation')
        for row in rows:
            key = row['id'] if row['language'] == 'typescript' else bench+':typescript-full-study:mech-control'
            require(row['key'] == key and row['benchmark'] == bench and key not in profiles,
                    'Duplicate or changed profile identity')
            for field in ('source', 'binary'):
                require(p.digest(row[field+'_sha256']) and plan['pins'].get(row[field]) == row[field+'_sha256'],
                        'Unpinned measured source/runtime')
            require(row['chart_admission'] is False and p.integer(row['maximum_workers'], 8), 'Changed row policy')
            if row['language'] == 'typescript':
                validate_typescript_row(row, plan['pins'])
            profiles[key] = row
        keys = {row['id']: row['key'] for row in rows}
        slots.extend([bench, order['round'], identity, keys[identity]] for order in orders for identity in order['profiles'])
    require(len(slots) == len({tuple(s) for s in slots}) == 60 and len(profiles) == 20, 'Incomplete rotation')
    same(plan['schedule'], slots, 'Changed complete schedule')
    return slots, profiles


def execution_support_pins(plan):
    """TypeScript fingerprint paths already name the measured physical files."""
    return dict(plan['pins'])


def reconcile(plan, report, terminal, raw, supervised, outer, durable, plan_path, plan_sha):
    """Pure validation; file hashes and completed leases must be bound separately."""
    require(p.digest(plan_sha),'Reviewed plan digest required')
    slots, originals = schedule(plan)
    check_durable(durable, plan_path, plan_sha, plan)
    controller_pid = durable['command-started']['command_pid']
    supervisor = report['supervisor']
    require(p.integer(supervisor['pid'], controller_pid), 'Report names another controller process')
    same(p.process_identity(dict(pid=supervisor['pid'],
         listing=str(supervisor['pid'])+' 0 '+supervisor['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']), 'Controller birth/command identity differs')
    require(report['schema']=='typescript-full60-results-v1' and terminal['schema']=='typescript-full60-terminal-v1', 'Wrong result schema')
    require(report['status'] in ('complete', 'complete-with-unqualified-profiles')
            and terminal['status'] == report['status'] and report['active'] is None, 'Study is not terminal')
    require(not any(report.get(k) for k in ('error', 'error_type', 'terminal_integrity_errors')),
            'Study has integrity or execution error')
    require(report['plan'] == plan_path and report['plan_sha256'] == plan_sha, 'Report belongs to another plan')
    require(report['pins_unchanged_at_end'] is True and terminal['common_mutex_held'] is True,
            'Unverified final pin/lock state')
    same(terminal['integrity_errors'], [], 'Final integrity failure')
    expected_pins = dict(plan['pins']); expected_pins[plan_path] = plan_sha
    same(terminal['prerequisite_pins'], expected_pins, 'Terminal closure differs')
    for item in (report, terminal):
        require(item['chart_admission'] is False, 'Measurement cannot grant chart admission')
        same(item['native_launch_unconfirmed_attempts'], [], 'Unconfirmed native launch')
    for name in ('compiler_invocations', 'fixture_reexecutions', 'bounded_reexecutions',
                 'count_replays', 'repeated_completed_samples'):
        require(p.integer(terminal[name], 0), 'Unexpected repeated/preparation work')
    require(terminal['original_files_mutated'] is False and report['no_automatic_retry'] is True
            and report['shared_timing_lock'] == str(LOCK) and p.integer(report['sample_count'], 3)
            and p.integer(report['source_work_profiles'], 10) and p.integer(report['canonical_loc_profiles'], 10)
            and p.integer(report['formatted_loc_profiles'], 0) and p.integer(report['planned_typescript_samples'], 30)
            and p.integer(report['planned_matched_mech_samples'], 30) and report['full_timings_qualified'] is False
            and terminal['full_timings_qualified'] is False,
            'Changed report policy')
    same(report['benchmark_order'], list(BENCHES), 'Changed benchmark order')
    same(report['completed_benchmarks'], list(BENCHES), 'Incomplete workload accounting')
    require(set(report['programs']) == set(originals), 'Changed profile inventory')
    attempts, failed, skipped, provenance, gaps = report['attempts'], {}, [], [], []
    grouped = {key: [] for key in originals}
    all_pins = execution_support_pins(plan); all_pins.update(expected_pins)
    index = 0; previous_end = None
    require(len(report['independent_supervisors']) == len(attempts), 'Outer receipt count differs')
    used_raw, used_supervised, used_outer = set(), set(), set()
    for slot in slots:
        bench, round_number, identifier, key = slot
        if key in failed:
            skipped.append(dict(benchmark=bench, round=round_number, id=identifier, key=key))
            continue
        require(index < len(attempts), 'Missing scheduled attempt')
        a = attempts[index]; index += 1
        require(p.integer(a['attempt'], index), 'Repeated or missing attempt index')
        base = plan['output']+'/attempts/'+f'{index:03d}-{identifier}'
        require(a['result_path'] == base+'.json' and a['supervisor_result_path'] == base+'.supervisor.json',
                'Attempt artifact path differs')
        outer_path = plan['output']+'/outer-supervisor/'+f'{index:03d}-{identifier}.json'
        ref = report['independent_supervisors'][index-1]
        require(ref['path'] == outer_path and ref['status'] == 'returned' and p.digest(ref['sha256'])
                and terminal['available_evidence_pins'][outer_path] == ref['sha256'], 'Outer receipt binding differs')
        begin, end = check_attempt(a, raw[a['result_path']], supervised[a['supervisor_result_path']], slot,
            originals[key], plan['manifests'][bench], all_pins, provenance)
        require(previous_end is None or previous_end <= begin, 'Native timing intervals overlap')
        previous_end = end
        gaps.extend(check_outer(outer[outer_path], a, controller_pid))
        used_raw.add(a['result_path']); used_supervised.add(a['supervisor_result_path']); used_outer.add(outer_path)
        grouped[key].append(a)
        if not a['qualified']:
            failed[key] = a
    require(index == len(attempts) and index+len(skipped) == 60, 'Unaccounted attempts or schedule slots')
    require(set(raw) == used_raw, 'Raw receipt inventory differs')
    require(set(supervised) == used_supervised and set(outer) == used_outer, 'Supervisor receipt inventory differs')
    require(set(terminal['available_evidence_pins']) ==
            used_raw | used_supervised | used_outer | {plan['output']+'/report.json'},
            'Closed inventory contains unregistered or missing evidence')
    expected_snapshots={path:terminal['available_evidence_pins'][path] for path in used_raw|used_supervised|used_outer}
    same(report['validated_attempt_artifacts'],expected_snapshots,'Report validation snapshots differ')
    same(terminal['validated_attempt_artifacts'],expected_snapshots,'Terminal validation snapshots differ')
    require(terminal['common_mutex_held_continuously'] is True and p.integer(terminal['common_mutex_inode'],p.LOCK_INODE),'Timing mutex boundary differs')
    same(report['isolated_failed_profiles'], list(failed), 'Failed profile inventory differs')
    same(report['skipped_failed_profile_slots'], skipped, 'Skipped slots are not explained by prior failure')
    same(terminal['skipped_failed_profile_slots'], skipped, 'Terminal skipped slots differ')
    require(report['status'] == ('complete-with-unqualified-profiles' if failed else 'complete'), 'Status hides failures')
    qualified = sum(a['qualified'] for a in attempts)
    for item in (report, terminal):
        for name, value in (('saved_attempts', index), ('full_performance_runs', index), ('qualified_samples', qualified)):
            require(p.integer(item[name], value), 'Wrong actual execution accounting: '+name)
        same(item['registered_native_attempts'], list(range(1,index+1)), 'Registration ledger differs')
    summaries = {}
    for key, original in originals.items():
        row, observations = report['programs'][key], grouped[key]
        same({k:v for k,v in row.items() if k not in AGGREGATE}, original, 'Measured source/profile metadata changed')
        same(row['attempts'], [a['attempt'] for a in observations], 'Profile attempt membership differs')
        good = [a for a in observations if a['qualified']]
        values = [a['seconds'] for a in good]
        same(row['samples_seconds'], values, 'Profile sample values differ')
        same(row['sample_validation'], [a['validation'] for a in good], 'Profile validations differ')
        if key in failed:
            require(row['measurement_status'] == 'failed-full-workload'
                    and len(values) < 3 and row.get('median_seconds') is None
                    and row.get('sample_stdev_seconds') is None and row['time_x_mech'] is None,
                    'Failed profile promoted partial timings')
            same(row['full_failure'], failed[key], 'Profile failure differs from attempt')
            median = sd = None
        else:
            require(row['measurement_status'] == 'measured' and not row.get('full_failure'), 'Incomplete measured profile')
            median, sd = p.three_statistics(values)
            require(p.finite(row['median_seconds'], True) and row['median_seconds'] == median, 'Median differs')
            require(p.finite(row['sample_stdev_seconds']) and row['sample_stdev_seconds'] >= 0
                    and math.isclose(row['sample_stdev_seconds'], sd,
                    rel_tol=1e-12, abs_tol=1e-12), 'Sample SD differs from independent calculation')
        summaries[key] = dict(key=key, id=row['id'], language=row['language'], benchmark=row['benchmark'],
            source=row['source'], source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
            attempts=row['attempts'], samples_seconds=values, median_seconds=median, sample_stdev_seconds=sd,
            full_workload_qualified=key not in failed, failed_attempt=failed.get(key, {}).get('attempt'))
    for key, row in report['programs'].items():
        control_key = row['benchmark']+':typescript-full-study:mech-control'
        control = summaries[control_key]
        require(row['matched_mech_control'] == control_key
                and row['matched_mech_source_sha256'] == originals[control_key]['source_sha256'], 'Wrong matched control')
        ratio = (summaries[key]['median_seconds']/control['median_seconds']
                 if key not in failed and control_key not in failed else None)
        same(row['time_x_mech'], ratio, 'Matched Mech ratio differs')
        summaries[key]['time_x_mech'] = ratio
    require(p.timestamp(report['started_at']) <= p.timestamp(attempts[0]['started_at'])
            and previous_end <= p.timestamp(report['finished_at']), 'Study times exclude native intervals')
    require(p.timestamp(durable['command-started']['started_at']) <= p.timestamp(report['started_at'])
            and p.timestamp(report['finished_at']) <= p.timestamp(durable['terminal']['finished_at']),
            'Study extends outside durable controller lifetime')
    return dict(schema=SCHEMA, status='ledger-reconciled-awaiting-file-runtime-and-publication-review',
        actual_full_native_processes=index, qualified_samples=qualified, skipped_slots=skipped,
        failed_profiles=list(failed), profiles=summaries, repeated_completed_samples=0,
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance})],
        kernel_identity_observation_gaps=gaps, file_integrity_verified=False, chart_admission=False,
        runtime_publication_metadata_qualified=False, full_timings_qualified=False, complete_stdout_retained=False,
        planned_typescript_samples=30, planned_matched_mech_samples=30,
        actual_typescript_processes=sum(a['language']=='typescript' for a in attempts),
        actual_matched_mech_processes=sum(a['language']=='mech' for a in attempts),
        full_output_evidence='sampler byte counts/hashes and frozen validation receipts',
        resource_evidence='sampled process-group RSS; not an unsampled maximum',
        admission_requirements=['source-work and canonical LOC semantic review', 'runtime metadata review',
            'explicit publication excluding failed profiles', 'catalog and website validation'])


def verify_leases(leases):
    for path, handle, device, inode in leases:
        held, named = os.fstat(handle.fileno()), path.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) == (device, inode),
                'Lease identity changed during result review')


@contextmanager
def _yield_verified(result, recheck, on_exit_failure, final_consumer_check=None):
    """Keep a final closure check and optional restoration inside outer leases."""
    recheck()
    try:
        yield result
    finally:
        try:
            recheck()
            if final_consumer_check is not None:final_consumer_check()
        except BaseException as closure_error:
            if on_exit_failure is not None:
                try:
                    on_exit_failure()
                except BaseException as restoration_error:
                    raise BaseExceptionGroup('Closure validation and publication restoration failed',
                        [closure_error, restoration_error])
            raise


@contextmanager
def review_files(plan_path, expected_sha, durable_directory, on_exit_failure=None, final_consumer_check=None):
    """Yield only after completed-job and physical-file verification.

    All three live descriptors remain held through the caller's exclusive
    output write and a final closure check, including on a failing body. A
    guarded publication consumer may supply restoration on exit-check failure;
    restoration runs before releasing any lease. Never call during a live run.
    """
    plan_path, job = Path(plan_path).resolve(), Path(durable_directory).resolve()
    plan_bytes = plan_path.read_bytes()
    require(p.digest(expected_sha) and hashlib.sha256(plan_bytes).hexdigest() == expected_sha,
            'Wrong independently retained TypeScript plan')
    plan = p.strict_json(plan_bytes)
    require(plan_path.is_relative_to(PACKET) and Path(plan['output']).is_relative_to(PACKET)
            and job==ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/typescript-full60-v1','Wrong retained full60 paths')
    cohort = Path(plan['repository'])/'experiments/typescript/typescript-full60.owner.lock'
    files = Files()
    with ExitStack() as stack:
        leases = []
        for path in (job/'owner.lock', cohort, LOCK):
            handle = stack.enter_context(path.open('rb'))
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held, named = os.fstat(handle.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino), 'Lease replaced')
            if path == LOCK:
                require(held.st_ino == p.LOCK_INODE, 'Original common mutex replaced')
            leases.append((path, handle, held.st_dev, held.st_ino))
        files.verify(str(plan_path), expected_sha)
        schedule(plan)
        for path, digest in ((Path(__file__).resolve(), hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                             (HELPER.resolve(), HELPER_SHA), (r.HELPER.resolve(), r.HELPER_SHA)):
            files.verify(str(path), digest)
        durable = {}
        job_inventory = {str(job/name) for name in ('owner.lock','request.json','launch.json','worker-started.json',
            'command-started.json','terminal.json','command.stdout','command.stderr','worker.log')}
        require(inventory(job) == job_inventory, 'Durable job contains missing or unregistered artifacts')
        for name in ('request', 'launch', 'worker-started', 'command-started', 'terminal'):
            path = job/(name+'.json')
            durable[name] = files.document(str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        check_durable(durable, str(plan_path), expected_sha, plan)
        require((job/'command.stderr').read_bytes() == b'', 'Durable controller emitted errors')
        for name in ('command.stdout', 'command.stderr', 'worker.log', 'owner.lock'):
            path = job/name
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            files.verify(str(path), digest)
        output = Path(plan['output'])
        terminal_path = output/'terminal.json'
        terminal_sha = hashlib.sha256(terminal_path.read_bytes()).hexdigest()
        terminal = files.document(str(terminal_path), terminal_sha)
        require(terminal['report'] == str(output/'report.json'), 'Terminal report path changed')
        report = files.document(terminal['report'], terminal['report_sha256'])
        available = terminal['available_evidence_pins']
        expected_inventory = set(available) | {str(terminal_path)}
        require(inventory(output) == expected_inventory, 'Closed full60 artifact inventory differs')
        for path, digest in available.items():
            require(Path(path).is_relative_to(output), 'Output artifact escapes retained run')
            files.verify(path, digest)
        for path, digest in plan['pins'].items():
            files.verify(path, digest)
        qualification_documents, metadata_sizes = {}, {}
        for name,(relative,digest) in {**QUALIFICATION_REFS,**CONTROL_REFS}.items():
            path=str(ROOT/relative)
            qualification_documents[name]=files.document(path,digest)
            metadata_sizes[name]=Path(path).stat().st_size
        source_review=qualified_bindings(plan,qualification_documents,metadata_sizes)
        prerequisite_inventory(plan, verify_files=True)
        def documents(paths):
            return {path: files.document(path, available[path]) for path in paths}
        raw = documents(a['result_path'] for a in report['attempts'])
        supervised = documents(a['supervisor_result_path'] for a in report['attempts'])
        outer = documents(a['path'] for a in report['independent_supervisors'])
        result = reconcile(plan, report, terminal, raw, supervised, outer, durable, str(plan_path), expected_sha)
        verified_pins = tuple(files.verified.items())
        def recheck():
            for path, digest in verified_pins:
                files.verify(path, digest)
            require(inventory(output) == expected_inventory, 'Closed artifact inventory changed during review')
            require(inventory(job) == job_inventory, 'Durable artifact inventory changed during review')
            prerequisite_inventory(plan, verify_files=True)
            verify_leases(leases)
        result.update(status='full60-reconciled-awaiting-publication-review',
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=p.LOCK_INODE,
            plan=dict(path=str(plan_path), sha256=expected_sha),
            report=dict(path=terminal['report'], sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path), sha256=terminal_sha), verified_file_pins=dict(verified_pins),
            source_evidence=dict(work=plan['qualified_work'], counts=plan['qualified_source_counts'], binding_review=source_review),
            runtime_evidence=plan['qualified_runtime'],runtime_publication_metadata_qualified=True,
            runtime_dependency_scope=plan['runtime_dependency_scope'],actual_loaded_image_inventory_observed=False,
            observed_in_each_timed_process=False,
            compiler_owner_fingerprint_policy='Exact physical TypeScript, JavaScript, map and retained provenance paths; no alias substitution')
        with _yield_verified(result, recheck, on_exit_failure, final_consumer_check) as verified:
            yield verified


def save_review_result(path, plan_path, plan_sha, durable_directory):
    """Keep only a receipt whose surrounding closure check completed successfully."""
    path, owned = Path(path), {}
    def remove_owned():
        if not owned:
            return
        identity = path.lstat()
        require((identity.st_dev, identity.st_ino) == owned['identity'] and not path.is_symlink(),
                'Refusing to remove a replaced result path')
        actual = path.read_bytes()
        require(owned['bytes'].startswith(actual), 'Refusing to remove altered result bytes')
        path.unlink()
        owned.clear()
    def verify_owned():
        require(bool(owned), 'Result ownership was not recorded')
        identity = path.lstat()
        require(not path.is_symlink() and (identity.st_dev, identity.st_ino) == owned['identity'],
                'Result path changed before closure')
        require(path.read_bytes() == owned['bytes'], 'Result bytes changed before closure')
        identity = path.lstat()
        require((identity.st_dev, identity.st_ino) == owned['identity'] and not path.is_symlink(),
                'Result path changed during closure')
    with review_files(plan_path, plan_sha, durable_directory, on_exit_failure=remove_owned,
                      final_consumer_check=verify_owned) as result:
        raw = (json.dumps(result, indent=2, allow_nan=False)+'\n').encode('utf-8')
        try:
            with path.open('xb') as stream:
                identity = os.fstat(stream.fileno())
                owned.update(identity=(identity.st_dev, identity.st_ino), bytes=raw)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as write_error:
            try:
                remove_owned()
            except BaseException as restoration_error:
                raise BaseExceptionGroup('Result write and restoration failed', [write_error, restoration_error])
            raise
    return result, hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--durable-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize
            and Path(sys.executable).resolve() == Path(p.PYTHON).resolve(), 'Use retained Python -I -S -B')
    require(not args.output.exists() and args.output.parent.is_dir(), 'Result review requires a new file')
    plan = p.strict_json(args.plan.read_bytes())
    require(args.output.resolve().is_relative_to(PACKET)
            and not args.output.resolve().is_relative_to(Path(plan['output']).resolve()),
            'Result review cannot alter original measurement artifacts')
    result, digest = save_review_result(args.output, args.plan, args.plan_sha256, args.durable_directory)
    print(json.dumps(dict(output=str(args.output), sha256=digest,
                          actual_native_processes=result['actual_full_native_processes'],
                          failed_profiles=result['failed_profiles'], chart_admission=False)), flush=True)


if __name__ == '__main__':
    main()
