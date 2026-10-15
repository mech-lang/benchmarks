"""Synthetic qualification joins only; no actual runtime or evidence replay."""
import importlib.util
from contextlib import contextmanager
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('rebol_qualification',Path(__file__).with_name('rebol_qualification.py'))
q=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(q)
SHA='a'*64


def ref(path):return dict(path=str(path),sha256=SHA)


def manifest():
    stages={}
    for key in ('bounded','work'):
        job=q.ROOT/'experiments/shared/owned-jobs-v1/owned-jobs'/key
        stages[key]=dict(plan=ref(q.PACKET/(key+'-plan.json')),report=ref(q.PACKET/key/'report.json'),
            terminal=ref(q.PACKET/key/'terminal.json'),durable=dict(directory=str(job),artifacts={},
                lease=dict(path=str(job/'owner.lock'),device=1,inode=2 if key=='bounded' else 3)))
    return dict(schema='rebol-exact-bounded-source-qualification-v1',
        status='independently-qualified-exact-inputs-for-full-timing',independent_review=True,
        scope=dict.fromkeys(q.TRUE_SCOPE,True)|dict.fromkeys(q.FALSE_SCOPE,False),stages=stages,
        references={key:ref(q.PACKET/(key+'.json')) for key in ('source_review','primitive_review',
            'bounded_source_review','work_source_review','count_review','work_review')})


class Evidence:
    PYTHON=Path('/retained/python')
    def __init__(self):self.documents={};self.raw={};self.inventories={};self.events=[]
    def physical(self,path):return Path(path)
    def pin(self,pins,resolutions,path,expected=None):
        path=str(path);pins[path]=expected or SHA;resolutions[path]=path;return Path(path)
    def document(self,reference,pins,resolutions):
        self.pin(pins,resolutions,reference['path'],reference['sha256'])
        return q.clone(self.documents[reference['path']])
    def read_bytes(self,path):return self.raw[str(path)]
    def inventory(self,path,exclude=()):
        return {k:v for k,v in self.inventories[str(path)].items() if k not in exclude},[]
    def verify(self,pins,resolutions,absent,closures):self.events.append(('verify',q.clone(pins),q.clone(closures)))
    def check_leases(self,leases):self.events.append(('leases',tuple(leases)))


def stage_fixture(kind):
    e=Evidence();stage=manifest()['stages'][kind];output=Path(stage['report']['path']).parent
    controller=q.ROOT/'tools/qualification'/('rebol_bounded.py' if kind=='bounded' else 'rebol_work_observations.py')
    count=149 if kind=='bounded' else 3;prefix='rebol149-bounded' if kind=='bounded' else 'rebol-three-work-observations'
    files={'start.json','active.json','process.json','stdout.bin','stderr.bin'}
    module=SimpleNamespace(__file__=str(controller),PACKET=output.parent,GATES=q.FALSE_SCOPE,
                           CAPTURE_FILES=files,SUCCESS='retained-not-qualified')
    schedule=[];captures=[];artifacts={};snapshots={};base=datetime(2026,1,1,tzinfo=timezone.utc)
    for index in range(count):
        name=f'{index:03d}';slot=dict(id=name,directory=name)
        if kind=='work':slot['sidecar']=str(output/name/'observation.tsv')
        schedule.append(slot)
        captures.append(dict(id=name,pid=100+index,started_at=(base+timedelta(seconds=2*index)).isoformat(),
                             finished_at=(base+timedelta(seconds=2*index+1)).isoformat(),observer_status='failed' if kind=='work' and index==2 else 'native-passed'))
        snapshot={f:dict(bytes=1,sha256=SHA) for f in files|({'observation.tsv'} if kind=='work' else set())}
        snapshots[name]=snapshot;artifacts.update({name+'/'+f:v for f,v in snapshot.items()})
    plan=dict(schema=prefix+'-plan-v1',repository=str(q.ROOT),controller=str(controller),controller_sha256=SHA,
        output=str(output),automatic_retry=False,benchmark_samples=0,common_mutex_inode=79859134,
        cleanup_timeout_seconds=5,pins={str(controller):SHA},input_resolutions={str(controller):str(controller)},
        schedule=schedule,**dict.fromkeys(module.GATES,False))
    report=dict(schema=prefix+'-results-v1',status=module.SUCCESS,plan=stage['plan']['path'],plan_sha256=SHA,
        pins=dict(plan['pins'],**{stage['plan']['path']:SHA}),input_resolutions=dict(plan['input_resolutions'],**{stage['plan']['path']:stage['plan']['path']}),
        attempts=[s['id'] for s in schedule],registered=[dict(id=c['id'],pid=c['pid']) for c in captures],
        captures=captures,active=None,integrity_errors=[],artifact_errors=[],validated_files=artifacts,artifacts=artifacts,
        benchmark_samples=0,**dict.fromkeys(module.GATES,False))
    e.raw[stage['report']['path']]=b'report';e.raw[stage['terminal']['path']]=b'terminal'
    available=dict(artifacts,**{'report.json':dict(bytes=6,sha256=SHA)})
    terminal=dict(schema=prefix+'-terminal-v1',status=module.SUCCESS,integrity_errors=[],artifact_errors=[],report_sha256=SHA,
        expected_report_sha256=SHA,common_mutex_held=True,common_mutex_inode=79859134,native_processes_started=count,
        available_evidence=available,benchmark_samples=0,**dict.fromkeys(module.GATES,False))
    terminal['validated_cases' if kind=='bounded' else 'validated_observations']=count
    e.documents.update({stage['plan']['path']:plan,stage['report']['path']:report,stage['terminal']['path']:terminal})
    e.inventories[str(output)]=dict(available,**{'terminal.json':dict(bytes=8,sha256=SHA)})
    job=Path(stage['durable']['directory']);jobfiles={name:dict(bytes=1,sha256=SHA) for name in ('launch.json','command-started.json','terminal.json')}
    stage['durable']['artifacts']=jobfiles;e.inventories[str(job)]=jobfiles
    argv=[str(e.PYTHON),'-I','-S','-B',str(controller),'run','--plan',stage['plan']['path'],'--plan-sha256',SHA]
    identity=dict(pid=55,birth_seconds=100,birth_microseconds=5)
    start=dict(command=argv,cwd=str(q.ROOT),command_identity_observation_missing=False,command_pid=55,command_identity=identity)
    end=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,automatic_retry=False,stop_signals=[],
             command_identity_observation_missing=False,command_pid=55,command_identity=identity)
    for name,value in [('launch.json',start),('command-started.json',start),('terminal.json',end)]:e.raw[str(job/name)]=q.encoded(value)
    def checker(slot,directory,parent):
        if parent!=55:raise AssertionError('Wrong parent passed to existing checker')
        index=int(slot['id']);return q.clone(captures[index]),q.clone(snapshots[slot['id']])
    return e,module,stage,dict(_kind=kind,schedule=q.clone(schedule)),checker,{str(controller):SHA},{str(controller):str(controller)}


def count_fixture():
    e=Evidence();benches=('binarytrees','fannkuchredux','fasta','knucleotide','mandelbrot','nbody','pidigits','regexredux','revcomp','spectralnorm')
    ids=benches+('io','loader','extension','big','regex')
    ledger=SimpleNamespace(RULE='rule-v2',KINDS={},ORIGINAL_C='old.c',CORRECTED_C='new.c',ORIGINAL_FANN='old.reb',CORRECTED_FANN='new.reb',DECISIONS=[])
    ledger.SOURCES={i:dict(path='synthetic/'+i,reviewed_source_sha256=SHA) for i in ids}
    ledger.BUNDLES={b:(b,'io','loader','extension')+(('big',) if b=='pidigits' else ('regex',) if b=='regexredux' else ()) for b in benches}
    results={i:dict(source_path=ledger.SOURCES[i]['path'],source_sha256=SHA,canonical_loc=2,physical_loc=3,
                   formatted_loc=None,identity=i,rule_version=ledger.RULE,source_identity_reviewed=True,
                   source_owners=[dict(start=0,end=1,canonical_units=2)],unowned_significant_characters=[]) for i in ids}
    units=SimpleNamespace(ROOT=q.ROOT,LEDGER=q.LEDGER,count_source=lambda raw,i,ledger:q.clone(results[i]))
    summaries={i:dict(path=str(q.ROOT/ledger.SOURCES[i]['path']),sha256=SHA,canonical_loc=2,physical_loc=3) for i in ids}
    for i in ids:e.raw[summaries[i]['path']]=b'x'
    source=dict(dependencies={str(p.relative_to(q.ROOT)):SHA for p in (q.COUNTER,q.LEDGER)})
    proposal=dict(schema='rebol-fifteen-source-count-proposal-v1',status='unreviewed-projection',rule_version=ledger.RULE,
        source_files=15,workloads=10,four_file_bundles=8,five_file_bundles=2,
        sources={i:dict(q.clone(value),source_identity_reviewed=False) for i,value in results.items()},bundles={},
        decisions=[],source_identity_reviewed=False,
        canonical_LOC_admitted=False,native_execution=False,compiler_input_qualified=False,required_work_qualified=False,
        full_timing_qualified=False,chart_admission=False,
        corrected_c_substitution=dict(original=ledger.ORIGINAL_C,counted=ledger.CORRECTED_C,original_modified=False,count_both_revisions=False),
        corrected_fannkuch_substitution=dict(original=ledger.ORIGINAL_FANN,counted=ledger.CORRECTED_FANN,original_modified=False,count_both_revisions=False))
    review=dict(schema='rebol15-independent-source-count-review-v1',status='qualified-exact-fifteen-source-owner-counts',
        independent_review=True,canonical_LOC_admitted=True,full_timing_qualified=False,chart_admission=False,rule_version=ledger.RULE,
        references=dict(proposal=ref(q.PACKET/'proposal.json'),rule=ref(q.RULE)),sources=summaries,bundles={})
    for b,members in ledger.BUNDLES.items():
        files=[dict(identity=i,path=ledger.SOURCES[i]['path'],sha256=SHA,canonical_loc=2,physical_loc=3) for i in members]
        proposal['bundles'][b]=dict(files=files,canonical_loc=2*len(members),physical_loc=3*len(members),source_forms=1,native_samples=0,canonical_LOC_admitted=False)
        review['bundles'][b]=dict(members=list(members),canonical_loc=2*len(members),physical_loc=3*len(members))
    reviewref=ref(q.PACKET/'count-review.json');e.documents[reviewref['path']]=review;e.documents[review['references']['proposal']['path']]=proposal
    sources={b:{k:summaries[b][k] for k in ('path','sha256')} for b in benches}
    extension=dict(corrected_source={k:summaries['extension'][k] for k in ('path','sha256')},
        unchanged_facades={summaries[i]['path']:SHA for i in ('io','loader','big','regex')})
    return e,reviewref,source,{}, {},sources,extension,units,ledger


class QualificationTests(unittest.TestCase):
    def test_manifest_requires_actual_scope_and_both_stages(self):
        q.manifest_contract(manifest())
        for mutate in (lambda m:m.update(status='source-only'),lambda m:m['scope'].update(runtime_source_equivalence_proven=True),
                       lambda m:m['scope'].update(bounded_output_qualified=False),lambda m:m['stages'].pop('work')):
            value=manifest();mutate(value)
            with self.assertRaises(AssertionError):q.manifest_contract(value)

    def test_reference_root_and_digest_not_guessed(self):
        for value in (ref('/other/receipt.json'),dict(path=str(q.PACKET/'x'),sha256=None),dict(ref(q.PACKET/'x'),extra=True)):
            with self.assertRaises((AssertionError,TypeError)):q.ref(value)

    def test_fifo_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as directory:
            # Resolve macOS /var before isolating the later regular-file gate.
            path=Path(directory).resolve()/'input';path.touch()
            with patch.object(Path,'lstat',return_value=SimpleNamespace(st_mode=0o010600)),patch.object(q.os,'open',side_effect=AssertionError('must not open')):
                with self.assertRaisesRegex(AssertionError,'Regular'):q.read_small(path)

    def test_exact149_and_work3_replay_preserves_raw_failure(self):
        for kind in ('bounded','work'):
            args=stage_fixture(kind);result=q.closed_stage(*args)
            self.assertEqual(len(result[1]),149 if kind=='bounded' else 3)
            if kind=='work':self.assertEqual(result[1][-1]['observer_status'],'failed')

    def test_durable_wrong_command_birth_or_pid_rejected(self):
        for field in ('command','birth','pid'):
            args=stage_fixture('work');e,_,stage,*_=args
            path=str(Path(stage['durable']['directory'])/'command-started.json');value=json.loads(e.raw[path])
            if field=='command':value['command'].insert(1,'-u')
            elif field=='birth':value['command_identity']['birth_microseconds']+=1
            else:value['command_pid']+=1
            e.raw[path]=q.encoded(value)
            with self.assertRaisesRegex(AssertionError,'Durable'):q.closed_stage(*args)

    def test_durable_zero_exit_keeps_awaiting_review_status(self):
        args=stage_fixture('work');e,module,stage,_,_,pins,resolutions=args
        terminal=str(Path(stage['durable']['directory'])/'terminal.json')
        original=e.raw[terminal]
        self.assertEqual(q.durable_inputs(e,stage,Path(module.__file__),pins,resolutions)[0],55)
        self.assertEqual(e.raw[terminal],original)
        # Successful worker exit does not replace the independent report gates.
        e.documents[stage['report']['path']]['status']='failed'
        with self.assertRaises(AssertionError):q.closed_stage(*args)
        self.assertEqual(e.raw[terminal],original)
        for status in ('command-succeeded','command-failed'):
            changed=json.loads(original);changed['status']=status;e.raw[terminal]=q.encoded(changed)
            with self.assertRaisesRegex(AssertionError,'Durable'):
                q.durable_inputs(e,stage,Path(module.__file__),pins,resolutions)

    def test_plan_capture_and_complete_membership_faults(self):
        for fault in ('plan','pin','capture','extra','missing','raw'):
            args=stage_fixture('work');e,module,stage,expected,checker,pins,resolutions=args
            if fault=='plan':e.documents[stage['plan']['path']]['schedule'].reverse()
            elif fault=='pin':e.documents[stage['report']['path']]['pins'].clear()
            elif fault=='capture':e.documents[stage['report']['path']]['captures'][0]['pid']+=1
            elif fault=='extra':e.inventories[str(Path(stage['report']['path']).parent)]['surprise']=dict(bytes=1,sha256=SHA)
            elif fault=='missing':e.inventories[str(Path(stage['report']['path']).parent)].pop('000/stdout.bin')
            else:
                def changed(slot,directory,parent):
                    value,snapshot=checker(slot,directory,parent);snapshot['stdout.bin']['sha256']='b'*64;return value,snapshot
                args=(e,module,stage,expected,changed,pins,resolutions)
            with self.assertRaises(AssertionError):q.closed_stage(*args)

    def test_count_complete_fifteen_and_four_five_bundle_roles(self):
        args=count_fixture();units,ledger=args[-2:]
        with patch.object(q,'pinned_module',side_effect=[units,ledger]):bundles,identities,_=q.counts(*args[:-2])
        self.assertEqual(len(identities),15);self.assertEqual(sorted(len(v['physical_inputs']) for v in bundles.values()),[4]*8+[5]*2)
        self.assertEqual(bundles['pidigits']['canonical_loc'],10)
        self.assertEqual(bundles['pidigits']['physical_inputs'][3]['role'],'general-library-helper')
        self.assertIsNone(bundles['pidigits']['formatted_loc'])

    def test_count_wrong_owner_sum_source_image_or_duplicate_rejected(self):
        for fault in ('owner','sum','main','image','duplicate','draft','formatted'):
            args=count_fixture();e,reference,_,_,_,sources,extension,units,ledger=args
            review=e.documents[reference['path']];proposal=e.documents[review['references']['proposal']['path']]
            if fault=='owner':proposal['sources']['io']['source_owners'][0]['end']=2
            elif fault=='sum':review['bundles']['pidigits']['canonical_loc']+=1
            elif fault=='main':sources['fannkuchredux']['path']=str(q.ROOT/'old.reb')
            elif fault=='image':extension['corrected_source']['sha256']='b'*64
            elif fault=='duplicate':ledger.BUNDLES['pidigits']=ledger.BUNDLES['pidigits']+('extension',)
            elif fault=='draft':review['canonical_LOC_admitted']=False
            else:proposal['sources']['io']['formatted_loc']=3
            with patch.object(q,'pinned_module',side_effect=[units,ledger]),self.assertRaises(AssertionError):q.counts(*args[:-2])

    def test_ten_bases_keep_fresh_environment_and_one_authored_form(self):
        args=count_fixture();e,_,_,_,_,sources,image,units,ledger=args
        with patch.object(q,'pinned_module',side_effect=[units,ledger]):bundles,_,_=q.counts(*args[:-2])
        e.RUNTIME=Path('/retained/rebol')
        e.environment=lambda out:dict(PATH='/usr/bin',LC_ALL='C',HOME=str(out/'home'),REBOL_HOME=str(out/'home'),TMPDIR=str(out/'tmp'))
        rows=[]
        for b in ledger.BUNDLES:
            sources[b].update(historical_path=str(q.PROFILES.parent/'sources'/b/'main.reb'),historical_sha256=SHA,substitution=None)
            rows.append(dict(id='baseline-'+b,benchmark=b,source='sources/'+b+'/main.reb',stdin=b=='knucleotide',maximum_workers=1))
        bases=q.make_bases(e,SimpleNamespace(BENCHES=tuple(ledger.BUNDLES)),dict(profiles=rows),sources,bundles,image,{})
        self.assertEqual(len(bases),10)
        for base in bases:
            policy=base['runtime_environment_policy'];self.assertNotIn('HOME',policy['fixed'])
            self.assertEqual(policy['fresh_directories'],dict(HOME='home',REBOL_HOME='home',TMPDIR='tmp'))
            self.assertEqual(policy['diagnostic_flags'],[]);self.assertFalse(policy['ambient_loader_overrides'])
            self.assertEqual(base['alias_policy']['authored_source_forms'],1)
            self.assertFalse(base['alias_policy']['copied_timing_allowed'])
        self.assertEqual(next(b for b in bases if b['benchmark']=='knucleotide')['input_kind'],'stdin')
        self.assertEqual(next(b for b in bases if b['benchmark']=='pidigits')['input_kind'],'integer-argument')

    def test_actual_work_review_binds_every_source_and_scoped_observation(self):
        count_args=count_fixture();e,_,_,_,_,sources,extension,_,_=count_args
        m=manifest();runtime=dict(path='/retained/rebol',sha256=SHA);image=dict(path='/approved/image',sha256=SHA)
        identities={i:dict(path=str(q.ROOT/'synthetic'/i),sha256=SHA) for i in (*sources,'io','loader','extension','big','regex')}
        bounded=[dict(id='bounded',observer_status='failed',expected_rejection=True)]
        work=[dict(id='map',observer_status='failed',accepted_map_stderr_failure=True)]
        review=dict(schema='rebol-independent-bounded-work-review-v1',status='qualified-exact-bounded-outputs-and-source-work',
            independent_review=True,bounded_output_qualified=True,required_work_qualified=True,
            **dict.fromkeys(q.FALSE_SCOPE,False),runtime=runtime,extension_image=image,sources=identities,
            stages={key:{name:m['stages'][key][name] for name in ('plan','report','terminal')} for key in ('bounded','work')},
            bounded_validations=bounded,work_observations=work,limitations=q.clone(q.LIMITATIONS),
            map_growth_source_review=ref(q.PACKET/'map-source-review.json'),source_work={b:dict(main=main,
                required_work_qualified=True,scope='exact-source-and-bounded-evidence',evidence=[ref(q.PACKET/(b+'-source-review.json'))])
                for b,main in sources.items()})
        e.documents[m['references']['work_review']['path']]=review
        result=q.work_approval(e,m,{}, {},sources,identities,runtime,image,bounded,work)
        self.assertEqual(result['work_observations'][0]['observer_status'],'failed')
        for fault in ('runtime','map-growth','pi-scope','observed','missing-source'):
            bad=q.clone(review)
            if fault=='runtime':bad['runtime_source_equivalence_proven']=True
            elif fault=='map-growth':bad['limitations']['maps']['capacity_growth_trajectory_observed']=True
            elif fault=='pi-scope':bad['limitations']['pi']['uninstrumented_full_size_trace']=True
            elif fault=='observed':bad['work_observations'][0]['observer_status']='native-passed'
            else:bad['source_work'].pop('fasta')
            e.documents[m['references']['work_review']['path']]=bad
            with self.assertRaises(AssertionError):q.work_approval(e,m,{}, {},sources,identities,runtime,image,bounded,work)

    def test_immutable_qualification_closure_allows_only_additions(self):
        e=Evidence();pins={'original':SHA};resolutions={'original':'physical'};admission={'bases':[1]}
        check=q.guarded_recheck(e,pins,resolutions,admission,[],[],[],[])
        pins['new']=SHA;resolutions['new']='new';check()
        self.assertEqual(e.events[-1][0],'leases')
        pins.pop('original')
        with self.assertRaisesRegex(AssertionError,'removed'):check()
        pins['original']=SHA;resolutions['original']='other'
        with self.assertRaisesRegex(AssertionError,'rebound'):check()
        resolutions['original']='physical';admission['bases'].append(2)
        with self.assertRaisesRegex(AssertionError,'content changed'):check()

    def test_closure_snapshot_cannot_be_shrunk_through_alias(self):
        e=Evidence();closures=[dict(directory='evidence',artifacts={'x':dict(bytes=1,sha256=SHA)})]
        check=q.guarded_recheck(e,{}, {},{},[],[],closures,[]);closures.clear();check()
        self.assertEqual(e.events[0][2][0]['directory'],'evidence')

    def test_body_failure_finalization_cleanup_before_unlock(self):
        events=[];held=SimpleNamespace(recheck=lambda:events.append('recheck'))
        with self.assertRaisesRegex(ValueError,'body'):
            with q._yield_verified({},held,lambda:events.append('cleanup'),lambda:events.append('final')):
                events.append('body');raise ValueError('body')
        events.append('unlock');self.assertEqual(events,['body','recheck','final','cleanup','unlock'])

    def test_recheck_failure_skips_success_terminal_and_retains_cleanup_error(self):
        events=[]
        def fail():events.append('recheck');raise ValueError('pin drift')
        def cleanup():events.append('failed terminal');raise OSError('cleanup')
        with self.assertRaises(BaseExceptionGroup) as caught:
            with q._yield_verified({},SimpleNamespace(recheck=fail),cleanup,lambda:events.append('success')):pass
        self.assertEqual(events,['recheck','failed terminal'])
        self.assertEqual([str(x) for x in caught.exception.exceptions],['pin drift','cleanup'])

    def test_final_consumer_failure_is_not_success(self):
        events=[]
        def final():events.append('final');raise RuntimeError('changed output')
        with self.assertRaisesRegex(RuntimeError,'changed output'):
            with q._yield_verified({},SimpleNamespace(recheck=lambda:events.append('recheck')),
                                   lambda:events.append('cleanup'),final):pass
        self.assertEqual(events,['recheck','final','cleanup'])

    def test_late_inherited_exit_downgrades_after_stream_closes(self):
        events=[];common=SimpleNamespace(closed=False)
        @contextmanager
        def inherited(*args):
            yield {},SimpleNamespace(common=common)
            events.append('success callback returned');common.closed=True
            raise OSError('late inherited lease check')
        def cleanup():events.append(('failed terminal',common.closed))
        with patch.object(q,'_held_review',inherited),self.assertRaisesRegex(OSError,'late inherited'):
            with q.review_context(q.PACKET/'manifest.json',SHA,cleanup):pass
        self.assertEqual(events,['success callback returned',('failed terminal',True)])


if __name__=='__main__':unittest.main()
