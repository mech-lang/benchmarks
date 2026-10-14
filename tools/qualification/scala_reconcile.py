"""Independently reconcile completed retained Scala full60 evidence.

No producer, sampler, runtime or benchmark is imported or executed. The pure
ledger validates every planned slot, receipt, outer supervisor and matched
control; the file phase requires completed durable/private/common leases and
rechecks the complete physical closure. Failed forms keep their real evidence
and never receive a median or ratio from partial samples. This is not a dataset
importer and grants no chart admission or runtime-publication approval.
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
spec = importlib.util.spec_from_file_location('scala_independent_receipt_primitives', HELPER)
r = importlib.util.module_from_spec(spec)
exec(compile(raw_helper, str(HELPER), 'exec'), r.__dict__)
p, require, same = r.p, r.require, r.same
BENCHES, SIZES, LOCK, POWER = r.BENCHES, r.SIZES, r.LOCK, r.POWER
AGGREGATE, check_attempt, check_outer = r.AGGREGATE, r.check_attempt, r.check_outer
Files, inventory = r.Files, r.inventory
PACKET = ROOT/'experiments/scala/full60-v1'
CONTROLLER_SHA = 'b9462a71eddd6fbc6ae5eb7a7098995f2184c54178ebc176c187cd9e49d10d13'
WORK_SHA = '32540d68a39aaeac3676ea5573cb48d7df2dbcdaea80e865ab30e7ef7c6c0cfc'
LOC_SHA = 'f5c706f72cdae4bf31cc5f19ff7fec2ea0ddeba2f05ec16571868c343028c0d0'
QUALIFICATION_REFS = {'work': ('experiments/scala/single-entry-work-v1/actual-instruction-review-v1.json',
          '32540d68a39aaeac3676ea5573cb48d7df2dbcdaea80e865ab30e7ef7c6c0cfc'),
 'tree_peer': ('experiments/scala/single-entry-work-v1/tree-peer-review-v1.json',
               '8f554b4cf43c801daacc790779948f67bdbc00f07487f873e61733d7d0a974e3'),
 'pi_peer': ('experiments/scala/single-entry-work-v1/pi-peer-review-v1.json',
             '2a32bc0a078f204657daea99afbb0b89ae9a40efbb483a9308cfeda5398b5c98'),
 'static': ('experiments/scala/compiled-applications-v1/required-work-review-v1.json',
            'c71af7c1070e2c17df3e5c00148edc550bddfefba4a0d27b76084367e6574510'),
 'compiled_report': ('experiments/scala/compiled-applications-v1/run-v1/report.json',
                     '55e266372bf64595430fc83aeb47dd68149075ff53d9d0d8b9627bf21c14f782'),
 'compiled_terminal': ('experiments/scala/compiled-applications-v1/run-v1/terminal.json',
                       'ccd911b9e313c085e86466ff9cd6bdf5e7c5a1fdf4617b54efc0a21edb3f2522'),
 'compiled_review': ('experiments/scala/compiled-applications-v1/independent-compilation-plan-review-v1.json',
                     '4688c8180e3149515ef0cdfdcc3f6b0373c7cf8f717001e075708d735b2108c3'),
 'bounded_plan': ('experiments/scala/bounded-v1/plan-v1.json',
                  '8dcc5342826524ef290ee0ed55e3d77fec89d50642fb82f51ece405ba67bacbc'),
 'bounded_report': ('experiments/scala/bounded-v1/run-v1/report.json',
                    'a5d794e06c554f2d89fe4430f55eefc9ebfa03e3a35f55c512ff5816d7c774b8'),
 'bounded_terminal': ('experiments/scala/bounded-v1/run-v1/terminal.json',
                      'e85b8306e290deb148f41a02ae6ad4e3ed516ba0d364d249720406b8ac807161'),
 'bounded_review': ('experiments/scala/bounded-v1/independent-closed-artifact-review-v1.json',
                    'feef20e589c177bab59999e94539d2283ce3ba49d52837b69f6175b3130585f8'),
 'capture_plan': ('experiments/scala/single-entry-work-v1/plan-v1.json',
                  'f508fb2a0aef9a06a69219e322847a152142b0a8f5ea4b9a2fe3c8abc96dd1a2'),
 'capture_report': ('experiments/scala/single-entry-work-v1/run-v1/report.json',
                    '0fc2ed6759ee95bb2ff375e83ffe6be57b1fce745cb83cd3d212ae6a09d3507a'),
 'capture_terminal': ('experiments/scala/single-entry-work-v1/run-v1/terminal.json',
                      '06aed95539f79eae8d3188494820268526d34612325b5fed43849b22a52da1c6'),
 'loc': ('experiments/scala/source-counts-v1/canonical-owner-review-v1/qualified-source-counts-v1.json',
         'f5c706f72cdae4bf31cc5f19ff7fec2ea0ddeba2f05ec16571868c343028c0d0'),
 'projection_review': ('experiments/scala/source-counts-v1/canonical-owner-review-v1/results-v1/review.json',
                       '25fde663cc9a774fd0d6668434919c1014a8984478c180b3a9bed00f42c69869'),
 'parser_report': ('experiments/scala/source-counts-v1/native-token-capture-v2/report.json',
                   'a2b5a96c833d7c16e73c6a070e863d832d051048b4d87611543b4dbc17c97287'),
 'parser_terminal': ('experiments/scala/source-counts-v1/native-token-capture-v2/terminal.json',
                     '7b336f1138cffe20047cd438f84621f4635904c19fec3d68d1a12b25f12f6b4f')}
SCHEMA = 'scala-independent-full60-reconciliation-v1'
JVM_FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
ENVIRONMENT_FIELDS = frozenset(('PATH','JAVA_HOME','CLASSPATH','LC_ALL','LANG','HOME','TMPDIR','TZ'))


CLBG=Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg')
CONTROL_REFS={
    'control_audit':(str(CLBG/'r-apl-uiua-comparison/20261011/source-audit-r.json'),'d76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'),
    'control_mandel':(str(CLBG/'mandelbrot/experiments/20261011-array-state/source-modes-study/full-study/manifest.json'),'fbffba7b5674e889ac9e5088bbb2e2d8499df41f5d9b4c677be38d831091680f'),
}
TIMING_POLICY=('Fresh direct JVM process including startup, retained class loading, tiered JIT, full input, '
               'all work, complete output and shutdown; subject compilation, pin hashing and output validation excluded')
SUPPORT_PINS={
    str(ROOT/'tools/qualification/elixir_full.py'):'5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703',
    str(ROOT/'tools/qualification/prolog_full.py'):'0d75d33bb77d3715ca7adcd8c07fcf3b659be472c2ef84c063dec57ee4b8eb94',
    str(ROOT/'tools/qualification/prolog_supervisor.py'):'5458bdf5e58465cb21156a2140657066b4706aa2a0941fe3efde8758207574b4',
    str(HELPER):HELPER_SHA,str(r.HELPER):r.HELPER_SHA,
    p.PYTHON:'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e',
    str(PACKET/'README.md'):'3e0626527ac39519f6d5dc602b2ba2572804bbb00cf2b6421a676699a3b41099',
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

def validate_scala_row(row,pins):
    sources,artifacts,env=row['physical_inputs'],row['class_artifacts'],row['runtime_environment']
    require(len(sources)==1 and sources[0]['role']=='application' and sources[0]['counted'] is True,
            'Exactly one counted authored Scala source required')
    require(sources[0]['path']==row['source'] and sources[0]['sha256']==row['source_sha256']
            and pins.get(row['compiled_source'])==pins.get(row['source'])==row['source_sha256'],'Authored/compiled bytes differ')
    require(set(env)==ENVIRONMENT_FIELDS and env['PATH']=='/usr/bin:/bin' and env['CLASSPATH']==''
            and env['LC_ALL']==env['LANG']=='C' and env['TZ']=='UTC'
            and env['JAVA_HOME']==str(Path(row['binary']).parent.parent),'Unqualified JVM environment')
    classes=Path(row['classes']);directory=classes.parent
    require(classes.is_absolute() and '..' not in classes.parts and row['cwd']==str(directory)
            and row['compiled_source']==str(directory/'Main.scala') and env['HOME']==str(directory/'home')
            and env['TMPDIR']==str(directory/'tmp')+'/','Retained classpath/cwd policy differs')
    libraries=row['runtime_libraries']
    require(len(libraries)==2 and [Path(name).name for name in libraries]==
            ['scala3-library_3-3.10.0.jar','scala-library-3.10.0.jar']
            and all(p.digest(pins.get(name)) for name in libraries),'Retained runtime libraries differ')
    command=[row['binary'],*JVM_FLAGS,'-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
             '-cp',':'.join([str(classes),*libraries]),'Main']
    if row['benchmark'] not in ('regexredux','knucleotide','revcomp'):command.append('{n}')
    same(row['command'],command,'Scored command changes main, classpath, flags or arguments')
    require(artifacts and len({item['relative_path'] for item in artifacts})==len(artifacts),'Missing/duplicate generated classes')
    for item in artifacts:
        part=Path(item['relative_path'])
        require(not part.is_absolute() and '..' not in part.parts and item['path']==str(classes/part)
                and p.digest(item['sha256']) and pins.get(item['path'])==item['sha256']
                and p.integer(item['bytes']) and item['bytes']>0,'Generated class artifact escaped its byte closure')
    require({'Main.class','Main$.class','Main.tasty'}<={item['relative_path'] for item in artifacts},'Direct Scala Main class missing')
    require(row['variant']=='jvm-v1' and row['id']=='scala-'+row['benchmark']+'-jvm-v1'
            and row['main_owner']=='Main' and row['source_alias_of'] is None and row['optimization_claim'] is False
            and row['runtime_policy_changes']==row['diagnostic_flags']==[],'Real source identity or timing policy differs')
    require(row['source_work_qualified'] is row['canonical_loc_qualified'] is True
            and row['formatted_loc_qualified'] is False and row['formatted_loc'] is None and row['loc']==row['canonical_loc']
            and all(p.integer(row[name]) and row[name]>0 for name in ('canonical_loc','physical_loc')),'Canonical-only count policy differs')
    require(pins.get(row['source_count_projection']['path'])==row['source_count_projection']['sha256'], 'Source count projection unbound')
    require(row['memory_policy']=='Retained -Xms64m -Xmx8g G1; ActiveProcessorCount=8; default tiered compilation',
            'Memory/JIT policy differs')


def prerequisite_inventory(plan,verify_files=False):
    closures=plan['prerequisite_artifact_closures']
    expected_directories={str(ROOT/'experiments/scala'/path) for path in
        ('compiled-applications-v1/run-v1','bounded-v1/run-v1','single-entry-work-v1/run-v1',
         'source-counts-v1/native-token-capture-v2','source-counts-v1/canonical-owner-review-v1/results-v1')}
    require(len(closures)==5 and {item['directory'] for item in closures}==expected_directories,'Five exact qualification closures required')
    for item in closures:
        directory=Path(item['directory']);expected=set()
        for name,record in item['artifacts'].items():
            part=Path(name);path=str(directory/part)
            require(not part.is_absolute() and '..' not in part.parts and p.integer(record['bytes']) and record['bytes']>=0
                    and p.digest(record['sha256']) and plan['pins'].get(path)==record['sha256'],'Unbound or unsafe prerequisite artifact')
            expected.add(path)
            if verify_files:require(Path(path).stat().st_size==record['bytes'],'Prerequisite artifact size differs')
        require(str(directory/'report.json') in expected or str(directory/'review.json') in expected,'Qualification summary omitted')
        if verify_files:same(sorted(inventory(directory)),sorted(expected),'Closed prerequisite inventory differs')
    if verify_files:
        for manifest in plan['manifests'].values():
            row=manifest['profiles'][0]
            same(sorted(inventory(row['classes'])),sorted(a['path'] for a in row['class_artifacts']),'Executable class inventory differs')


def qualified_bindings(plan, documents, metadata_sizes):
    """Join immutable qualification identities to the actual timed rows.

    The reviewed decisions are retained inputs, not decisions inferred from
    producer success flags. File mode authenticates every document before this
    join, including the original compiler and parser inventories.
    """
    d, pins = documents, plan['pins']
    def keyed(rows):
        values = {row['id']: row for row in rows}
        require(len(rows) == len(values) == 10 and set(values) ==
                {'scala-'+bench+'-jvm-v1' for bench in BENCHES}, 'Qualified implementation inventory differs')
        return values
    def reference(actual, name):
        relative, digest = QUALIFICATION_REFS[name]
        same(dict(path=str(ROOT/actual['path']), sha256=actual['sha256']),
             dict(path=str(ROOT/relative), sha256=digest), 'Qualification link differs: '+name)
    work, counts = d['work'], d['loc']
    require(work['source_work_qualified'] is True and work['full_timings_qualified'] is False
            and work['chart_admission'] is False and work['producer_artifacts_unchanged'] is True
            and work['closed_artifact_inventory_exact'] is True, 'Required-work admission is incomplete')
    require(counts['canonical_loc_qualified'] is counts['canonical_LOC_admitted'] is
            counts['manual_owner_review_replayed'] is True and counts['formatted_loc_qualified'] is False
            and counts['formatted_loc'] is None, 'Canonical-only count decision differs')
    for field, name in [('producer_plan','capture_plan'), ('producer_report','capture_report'),
            ('producer_terminal','capture_terminal'), ('pidigits_peer_review','pi_peer'),
            ('prior_static_required_work_review','static'), ('prior_149_case_closed_artifact_review','bounded_review')]:
        reference(work[field], name)
    reference(d['tree_peer']['review'], 'work')
    require(d['tree_peer']['status'] == 'no-concrete-tree-evidence-blocker'
            and d['pi_peer']['both_division_calls_dominate_comparison'] is True
            and d['pi_peer']['complete_hotspot_log'] is True
            and d['pi_peer']['caller_execution_path'] == 'interpreted-main', 'Tree/pi review differs')
    runtime = d['capture_plan']['compiled']
    same(runtime, d['bounded_plan']['compiled'], 'Bounded and required-work compiled inputs differ')
    same(d['capture_plan']['runtime_flags'], JVM_FLAGS, 'Qualified JVM policy differs')
    original, counted = keyed(runtime['profiles']), keyed(counts['profiles'])
    compiled, static = keyed(d['compiled_report']['profiles']), keyed(d['static']['profiles'])
    same(sorted(work['qualified_profiles']), sorted(original), 'Work decision omits or aliases an implementation')
    require(d['bounded_review']['cases_verified'] == 149 and d['bounded_review']['successful_outputs_verified'] == 142
            and d['bounded_review']['expected_rejections_verified'] == 7
            and all(d['bounded_review'][name] is True for name in ('exact_case_order_preserved',
                'serial_lifetimes_verified','all_original_process_receipts_preserved','all_native_children_reaped',
                'all_process_groups_closed','all_output_bytes_rechecked')), 'Independent bounded review incomplete')
    for kind in ('plan','report','terminal'): reference(d['bounded_review']['bounded_'+kind], 'bounded_'+kind)
    for identity, source in original.items():
        row = plan['manifests'][source['benchmark']]['profiles'][0]
        count, built, reviewed = counted[identity], compiled[identity], static[identity]
        same(row['id'], identity, 'Timed row aliases another qualified source')
        for field in ('benchmark','source','source_sha256','compiled_source','classes','main_owner'):
            same(row[field], source[field], 'Timed qualified identity differs: '+field)
        same(row['class_artifacts'], source['artifacts'], 'Timed class artifacts differ')
        same(row['class_artifacts'], built['artifacts'], 'Timed classes differ from actual compiler output')
        same(row['runtime_libraries'], runtime['runtime_libraries'], 'Runtime jars differ from qualification')
        same(row['binary'], runtime['java'], 'JVM differs from qualified execution')
        same(row['source_sha256'], built['source_sha256'], 'Compiler source bytes differ')
        same(row['compiled_source'], built['source'], 'Compiler source path differs')
        same(source['runtime_classpath'], built['runtime_classpath'], 'Compiler classpath differs')
        same(source['runtime_classpath'], ':'.join([row['classes'], *row['runtime_libraries']]), 'Timed classpath differs')
        same(row['source'], str(ROOT/reviewed['source']['path']), 'Required-work source differs')
        same(row['source_sha256'], reviewed['source']['sha256'], 'Required-work source bytes differ')
        same({a['path']:a['sha256'] for a in row['class_artifacts']},
             {str(ROOT/a['path']):a['sha256'] for a in reviewed['class_artifacts']}, 'Required-work classes differ')
        require(reviewed['static_workload_contracts_passed'] is True
                and all(item['static_result']=='passed' for item in reviewed['contracts']), 'Static work review incomplete')
        for field in ('benchmark','source','source_sha256','canonical_loc','physical_loc'):
            same(row[field], count[field], 'Counted source identity/value differs: '+field)
        same(row['source_count_projection'], dict(path=count['projection'], sha256=count['projection_sha256']),
             'Canonical projection differs')
        require(count['canonical_loc_qualified'] is True and count['formatted_loc_qualified'] is False
                and count['formatted_loc'] is None, 'Profile count admission differs')
    for name in ('compiled_report','bounded_plan','bounded_report','capture_plan','capture_report','parser_report'):
        for path, digest in d[name]['pins'].items():
            require(pins.get(path)==digest, 'Inherited prerequisite pin omitted or changed: '+path)
    for path, digest in counts['evidence_pins'].items():
        require(pins.get(path)==digest, 'Canonical owner evidence omitted or changed')
    expected_closures = {}
    for name in ('compiled','bounded','capture','parser'):
        report, terminal = d[name+'_report'], d[name+'_terminal']
        require(report['status']==terminal['status'] and report['active'] is None
                and report['integrity_errors']==[] and terminal['report_sha256']==QUALIFICATION_REFS[name+'_report'][1],
                'Qualification producer is not closed: '+name)
        directory = ROOT/QUALIFICATION_REFS[name+'_report'][0]
        artifacts = dict(terminal['available_evidence'] if name in ('bounded','capture') else report['artifacts'])
        for kind in ('report','terminal'):
            key=name+'_'+kind; relative,digest=QUALIFICATION_REFS[key]
            record=dict(bytes=metadata_sizes[key],sha256=digest)
            require(Path(relative).name not in artifacts or artifacts[Path(relative).name]==record,
                    'Conflicting qualification summary bytes')
            artifacts[Path(relative).name]=record
        expected_closures[str(directory.parent)] = artifacts
    projection=d['projection_review']
    require(projection['input_replay']['report_sha256']==QUALIFICATION_REFS['parser_report'][1]
            and projection['input_replay']['native_pairs']==80 and len(projection['artifacts'])==51,
            'Canonical parser/projection dependency differs')
    artifacts=dict(projection['artifacts'])
    artifacts['review.json']=dict(bytes=metadata_sizes['projection_review'],sha256=QUALIFICATION_REFS['projection_review'][1])
    expected_closures[str((ROOT/QUALIFICATION_REFS['projection_review'][0]).parent)] = artifacts
    same({item['directory']:item['artifacts'] for item in plan['prerequisite_artifact_closures']}, expected_closures,
         'Prerequisite inventory differs from closed original evidence')
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
                bounded_cases=149, reused_native_work_captures=2, fresh_qualification_executions=0)


def check_durable(durable, plan_path, plan_sha, plan):
    """Validate the exact retained Python -I -S -B -u durable launch."""
    request, launch, worker, started, ended = [durable[k] for k in
        ('request', 'launch', 'worker-started', 'command-started', 'terminal')]
    command = [p.PYTHON, '-I', '-S', '-B', '-u', plan['controller'], 'run',
               '--plan', plan_path, '--plan-sha256', plan_sha]
    same(request['command'], command, 'Durable command is not the exact prepared Scala run')
    require(p.digest(plan['pins'].get(p.PYTHON)), 'Unpinned Scala interpreter')
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
    require(plan['schema'] == 'scala-qualified-retained-full60-v1'
            and plan['status'] == 'prepared-awaiting-independent-review'
            and plan['pins_verified'] is True, 'Unprepared or wrong Scala plan')
    require(plan['controller_sha256'] == CONTROLLER_SHA
            and plan['pins'][plan['controller']] == CONTROLLER_SHA, 'Changed frozen controller')
    require(plan['controller']==str(ROOT/'tools/qualification/scala_full.py')
            and plan['formatted_loc_qualified'] is False,'Changed Scala timing implementation')
    for name, expected in (('source_work_profiles', 10), ('canonical_loc_profiles', 10),
            ('formatted_loc_profiles', 0), ('retained_bounded_cases', 149), ('samples', 3),
            ('full_processes', 60), ('scala_samples', 30), ('matched_mech_samples', 30),
            ('new_native_probes', 0), ('compiler_invocations', 0), ('fixture_reexecutions', 0),
            ('bounded_reexecutions', 0), ('count_replays', 0)):
        require(p.integer(plan[name], expected), 'Changed plan count: '+name)
    require(plan['original_files_mutated'] is False and plan['chart_admission'] is False
            and plan['full_timings_qualified'] is False and plan['no_automatic_retry'] is True
            and plan['continuous_common_mutex'] is True and plan['shared_timing_lock'] == str(LOCK)
            and p.integer(plan['common_mutex_inode'], p.LOCK_INODE), 'Changed plan policy')
    for name, expected in (('qualified_work', WORK_SHA), ('qualified_source_counts', LOC_SHA)):
        binding = plan[name]
        reference_name='work' if name=='qualified_work' else 'loc'
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
                and manifest['runtime_and_class_loading_inside_timer'] is True
                and manifest['runtime_JIT_inside_timer'] is True
                and p.integer(manifest['direct_main_invocations_per_sample'], 1), 'Changed timing policy')
        same(manifest['full_output_reference'],FULL_REFERENCES[bench],'Canonical complete-output reference differs')
        ids = [f'scala-{bench}-jvm-v1', 'mech-aot-control']
        rows = manifest['profiles']
        same([row['id'] for row in rows], ids, 'Changed retained cohort')
        same([row['language'] for row in rows], ['scala', 'mech'], 'Changed language cohort')
        offset=list(BENCHES).index(bench)%2
        orders = [dict(round=i+1, profiles=ids[(i+offset)%2:]+ids[:(i+offset)%2]) for i in range(3)]
        same(manifest['orders'], orders, 'Changed rotation')
        for row in rows:
            key = row['id'] if row['language'] == 'scala' else bench+':scala-full-study:mech-control'
            require(row['key'] == key and row['benchmark'] == bench and key not in profiles,
                    'Duplicate or changed profile identity')
            for field in ('source', 'binary'):
                require(p.digest(row[field+'_sha256']) and plan['pins'].get(row[field]) == row[field+'_sha256'],
                        'Unpinned measured source/runtime')
            require(row['chart_admission'] is False and p.integer(row['maximum_workers'], 8), 'Changed row policy')
            if row['language'] == 'scala':
                validate_scala_row(row, plan['pins'])
            profiles[key] = row
        keys = {row['id']: row['key'] for row in rows}
        slots.extend([bench, order['round'], identity, keys[identity]] for order in orders for identity in order['profiles'])
    require(len(slots) == len({tuple(s) for s in slots}) == 60 and len(profiles) == 20, 'Incomplete rotation')
    same(plan['schedule'], slots, 'Changed complete schedule')
    return slots, profiles


def execution_support_pins(plan):
    """Scala fingerprint paths already name the measured physical files."""
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
    require(report['schema']=='scala-full60-results-v1' and terminal['schema']=='scala-full60-terminal-v1', 'Wrong result schema')
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
            and p.integer(report['formatted_loc_profiles'], 0) and p.integer(report['planned_scala_samples'], 30)
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
        control_key = row['benchmark']+':scala-full-study:mech-control'
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
        planned_scala_samples=30, planned_matched_mech_samples=30,
        actual_scala_processes=sum(a['language']=='scala' for a in attempts),
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
            'Wrong independently retained Scala plan')
    plan = p.strict_json(plan_bytes)
    require(plan_path.is_relative_to(PACKET) and Path(plan['output']).is_relative_to(PACKET)
            and job==ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/scala-full60-v1','Wrong retained full60 paths')
    cohort = Path(plan['repository'])/'experiments/scala/scala-full60.owner.lock'
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
        result.update(status='full60-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True, common_mutex_held=True, common_mutex_inode=p.LOCK_INODE,
            plan=dict(path=str(plan_path), sha256=expected_sha),
            report=dict(path=terminal['report'], sha256=terminal['report_sha256']),
            terminal=dict(path=str(terminal_path), sha256=terminal_sha), verified_file_pins=dict(verified_pins),
            source_evidence=dict(work=plan['qualified_work'], counts=plan['qualified_source_counts'], binding_review=source_review),
            compiler_owner_fingerprint_policy='Exact physical source, class and retained provenance paths; no alias substitution')
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
