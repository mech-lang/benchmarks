"""Small snapshot fixtures; no current catalog, native process or runtime hashes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('normalization_under_test', HERE/'normalization_history.py')
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


def fixture(workload='fannkuchredux', before=31, after=20, lang='uiua'):
    old_key, new_key = workload+':old', workload+':new'
    old = dict(key=old_key, benchmark=workload, language='old', loc=before, x=1,
               seconds=2, samples=[1,2,3], y=2, source_sha256='old-source')
    old['publication_record'] = copy.deepcopy(old)
    reference = dict(lang='old', fast=dict(x=1,y=2), small=dict(x=1,y=2))
    group = dict(language='old', programs=[old_key], fast=old_key, small=old_key)
    original = dict(benchmarks=[dict(key=workload, baseline_loc=before, baseline_seconds=1,
        baseline_formatted_loc=99, groups=[group])], programs={old_key:old},
        program_inventory={old_key:copy.deepcopy(old)}, files={'old':{'code':'unchanged'}},
        reference_summary=[reference], formatted_reference_summary=[dict(lang='old', fast={'x':1,'y':2})])
    current = copy.deepcopy(original)
    row = dict(key=new_key, benchmark=workload, language=lang, loc=after, x=1,
               seconds=3, samples=[2,3,4], y=3, eligible_for_chart=True)
    row['publication_record'] = copy.deepcopy(row)
    endpoint = dict(language=lang, programs=[new_key], fast=new_key, small=new_key)
    current['benchmarks'][0]['groups'].append(endpoint)
    current['benchmarks'][0]['baseline_loc'] = after
    changes=[]
    for pool in ('programs','program_inventory'):
        current[pool][new_key] = copy.deepcopy(row)
        for key, value in current[pool].items():
            prior=value['loc']/before
            value['x']=value['loc']/after
            value['publication_record']['x']=value['x']
            changes.append(dict(pool=pool,key=key,before=prior,after=value['x']))
    refs=[]
    for kind in ('fast','small'):
        current['reference_summary'][0][kind]['x']=before/after
        refs.append(dict(language='old',kind=kind,before=1,after=before/after))
    current['reference_summary'].append(dict(lang=lang,fast=dict(x=1,y=3),small=dict(x=1,y=3)))
    audit=dict(endpoint=endpoint,normalization=dict(benchmark=workload,axis='canonical-loc',
        before=before,after=after,changed_program_coordinates=changes,changed_aggregate_coordinates=refs,
        timing_baseline_changed=False,formatted_baselines_changed=False,raw_source_counts_changed=False,
        timing_samples_changed=False,source_or_receipt_bytes_changed=False))
    return original,current,audit,{new_key},{lang}


def encode(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def write(root,path,value):
    raw=encode(value)
    destination=root/path
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(raw)
    return dict(path=path,sha256=hashlib.sha256(raw).hexdigest())


def saved(root,original,current,audit,key='fixture_admission',folder='admission'):
    current[key]=copy.deepcopy(audit)
    original_ref=write(root,folder+'/before/'+n.CATALOG,original)
    current_ref=write(root,folder+'/after/'+n.CATALOG,current)
    lang_before=write(root,folder+'/before/'+n.LANGUAGES,{'unchanged':'languages'})
    lang_after=write(root,folder+'/after/'+n.LANGUAGES,{'unchanged':'languages'})
    success=dict(status='applied',catalog_changed=True,audit=audit,
        originals={n.CATALOG:original_ref['sha256'],n.LANGUAGES:lang_before['sha256']},
        prepared={n.CATALOG:current_ref['sha256'],n.LANGUAGES:lang_after['sha256']})
    success_ref=write(root,folder+'/SUCCESS.json',success)
    return dict(audit_key=key,success=success_ref)


def multi_fixture():
    original=dict(benchmarks=[],programs={},program_inventory={},files={},reference_summary=[],
                  formatted_reference_summary=[])
    for workload,baseline in [('nbody',20),('binarytrees',16),('fannkuchredux',20)]:
        key=workload+':old'
        row=dict(key=key,benchmark=workload,language='old',loc=baseline,x=1,seconds=2,y=2)
        row['publication_record']=copy.deepcopy(row)
        for pool in ('programs','program_inventory'):original[pool][key]=copy.deepcopy(row)
        original['benchmarks'].append(dict(key=workload,baseline_loc=baseline,baseline_seconds=1,
            groups=[dict(language='old',programs=[key],fast=key,small=key)]))
    # Existing partial language: its later coverage expansion must not be
    # mistaken for a change to its raw timing or original normalization audit.
    for workload,loc in [('nbody',21),('fannkuchredux',20)]:
        key=workload+':uiua';bench=next(b for b in original['benchmarks'] if b['key']==workload)
        row=dict(key=key,benchmark=workload,language='uiua',loc=loc,x=loc/bench['baseline_loc'],seconds=3,y=3)
        row['publication_record']=copy.deepcopy(row)
        for pool in ('programs','program_inventory'):original[pool][key]=copy.deepcopy(row)
        bench['groups'].append(dict(language='uiua',programs=[key],fast=key,small=key))
    for language,coverage in [('old',None),('uiua',['nbody','fannkuchredux'])]:
        ref=dict(lang=language,fast=dict(x=1,y=2 if language=='old' else 3),small=dict(x=1,y=2 if language=='old' else 3))
        if coverage is not None:ref['measured_benchmarks']=coverage
        for kind in ('fast','small'):ref[kind]['x']=n.aggregate(original,ref,kind)
        original['reference_summary'].append(ref)
    after=copy.deepcopy(original);endpoints={};added={pool:set() for pool in ('programs','program_inventory')}
    for workload,loc in [('nbody',19),('binarytrees',15),('fannkuchredux',21)]:
        key=workload+':r';bench=next(b for b in after['benchmarks'] if b['key']==workload)
        row=dict(key=key,benchmark=workload,language='r',loc=loc,x=loc/bench['baseline_loc'],seconds=4,y=4)
        row['publication_record']=copy.deepcopy(row)
        for pool in added:after[pool][key]=copy.deepcopy(row);added[pool].add(key)
        endpoints[workload]=dict(language='r',programs=[key],fast=key,small=key)
        bench['groups'].append(endpoints[workload])
    extra=copy.deepcopy(after['program_inventory']['nbody:r']);extra['key']='nbody:r-not-selected';extra['publication_record']['key']=extra['key']
    after['program_inventory'][extra['key']]=extra;added['program_inventory'].add(extra['key'])
    normalizations=[]
    for workload,low in [('nbody',19),('binarytrees',15)]:
        bench=next(b for b in after['benchmarks'] if b['key']==workload);high=bench['baseline_loc'];bench['baseline_loc']=low
        changes=[]
        for pool in added:
            for key,row in after[pool].items():
                if row['benchmark']!=workload:continue
                old=row['x'];row['x']=row['loc']/low;row['publication_record']['x']=row['x']
                changes.append(dict(pool=pool,key=key,before=old,after=row['x']))
        aggregates=[];affected={g['language'] for g in bench['groups']}
        for ref in after['reference_summary']:
            if ref['lang'] not in affected:continue
            for kind in ('fast','small'):
                old=ref[kind]['x'];ref[kind]['x']=n.aggregate(after,ref,kind)
                aggregates.append(dict(language=ref['lang'],kind=kind,before=old,after=ref[kind]['x']))
        normalizations.append(dict(benchmark=workload,axis='canonical-loc',before=high,after=low,
            changed_program_coordinates=changes,changed_aggregate_coordinates=aggregates,
            timing_baseline_changed=False,formatted_baselines_changed=False,raw_source_counts_changed=False,
            timing_samples_changed=False,source_or_receipt_bytes_changed=False))
    newref=dict(lang='r',measured_benchmarks=[b['key'] for b in after['benchmarks']],
                fast=dict(x=1,y=4),small=dict(x=1,y=4))
    for kind in ('fast','small'):newref[kind]['x']=n.aggregate(after,newref,kind)
    after['reference_summary'].append(newref)
    audit=dict(endpoints=endpoints,normalizations=normalizations,aggregate_change=dict(before=None,after=newref))
    return original,after,audit,added,{'r'}


class Normalization(unittest.TestCase):
    def test_three_explicit_workload_minima_use_same_engine(self):
        for workload,before,after in [('fannkuchredux',31,20),('nbody',20,19),('binarytrees',16,15)]:
            with self.subTest(workload=workload):
                original,current,audit,added,refs=fixture(workload,before,after)
                n.validate_transition(original,current,audit,added,refs)
                reverse=copy.deepcopy(current)
                n.reverse_transition(reverse,original,current,audit)
                for pool in ('programs','program_inventory'):
                    for key,row in original[pool].items():self.assertEqual(reverse[pool][key],row)
                self.assertEqual(reverse['benchmarks'][0]['baseline_loc'],before)
                self.assertEqual(reverse['reference_summary'][0],original['reference_summary'][0])
                self.assertEqual(current['benchmarks'][0]['baseline_loc'],after)

    def test_every_program_and_aggregate_change_must_be_listed(self):
        for field in ('changed_program_coordinates','changed_aggregate_coordinates'):
            original,current,audit,added,refs=fixture()
            audit['normalization'][field].pop()
            with self.assertRaisesRegex(ValueError,'Incomplete'):
                n.validate_transition(original,current,audit,added,refs)

    def test_duplicate_and_forged_audit_entries_rejected(self):
        for mode in ('duplicate','before','after'):
            original,current,audit,added,refs=fixture()
            rows=audit['normalization']['changed_program_coordinates']
            if mode=='duplicate':rows.append(copy.deepcopy(rows[0]))
            else:rows[0][mode]+=1
            with self.assertRaises(ValueError):n.validate_transition(original,current,audit,added,refs)

    def test_raw_time_source_and_formatted_changes_are_never_excused(self):
        for mode in ('samples','seconds','source_sha256','y','publication_raw','formatted','timebase'):
            original,current,audit,added,refs=fixture()
            row=current['programs']['fannkuchredux:old']
            if mode=='publication_raw':row['publication_record']['seconds']=100
            elif mode=='formatted':current['formatted_reference_summary'][0]['fast']['x']=9
            elif mode=='timebase':current['benchmarks'][0]['baseline_seconds']=.5
            else:row[mode]=['changed'] if mode=='samples' else 100
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                n.validate_transition(original,current,audit,added,refs)

    def test_wrong_current_or_publication_x_rejected(self):
        for mode in ('x','publication','aggregate'):
            original,current,audit,added,refs=fixture()
            if mode=='x':current['programs']['fannkuchredux:old']['x']=99
            elif mode=='publication':current['programs']['fannkuchredux:old']['publication_record']['x']=99
            else:current['reference_summary'][0]['fast']['x']=99
            with self.assertRaises(ValueError):n.reverse_transition(current,original,current,audit)

    def test_unlisted_later_language_reverses_derived_coordinates_only(self):
        original,current,audit,added,refs=fixture()
        later=copy.deepcopy(current)
        key='fannkuchredux:later'
        row=dict(key=key,benchmark='fannkuchredux',language='later',loc=40,x=2,seconds=4,y=4,samples=[4]*3)
        row['publication_record']=copy.deepcopy(row)
        for pool in ('programs','program_inventory'):later[pool][key]=copy.deepcopy(row)
        later['benchmarks'][0]['groups'].append(dict(language='later',programs=[key],fast=key,small=key))
        later['reference_summary'].append(dict(lang='later',fast=dict(x=2,y=4),small=dict(x=2,y=4)))
        n.reverse_transition(later,original,current,audit)
        self.assertEqual(later['programs'][key]['x'],40/31)
        self.assertEqual(n.raw_row(later['programs'][key]),n.raw_row(row))

    def test_ordered_rebases_compose_and_reverse_to_original_values(self):
        first_before,first_after,first_audit,first_added,first_refs=fixture('binarytrees',16,15,'uiua')
        second_before=copy.deepcopy(first_after)
        second_after=copy.deepcopy(second_before)
        key='binarytrees:r'
        row=dict(key=key,benchmark='binarytrees',language='r',loc=14,x=1,seconds=4,y=4)
        row['publication_record']=copy.deepcopy(row)
        endpoint=dict(language='r',programs=[key],fast=key,small=key)
        second_after['benchmarks'][0]['groups'].append(endpoint)
        second_after['benchmarks'][0]['baseline_loc']=14
        changed=[]
        for pool in ('programs','program_inventory'):
            second_after[pool][key]=copy.deepcopy(row)
            for identity,value in second_after[pool].items():
                prior=second_before[pool][identity]['x'] if identity in second_before[pool] else 14/15
                value['x']=value['loc']/14;value['publication_record']['x']=value['x']
                changed.append(dict(pool=pool,key=identity,before=prior,after=value['x']))
        aggregates=[]
        for ref in second_after['reference_summary']:
            for kind in ('fast','small'):
                old=ref[kind]['x'];ref[kind]['x']=n.aggregate(second_after,ref,kind)
                aggregates.append(dict(language=ref['lang'],kind=kind,before=old,after=ref[kind]['x']))
        second_after['reference_summary'].append(dict(lang='r',fast=dict(x=1,y=4),small=dict(x=1,y=4)))
        second_audit=copy.deepcopy(first_audit)
        second_audit['endpoint']=endpoint
        second_audit['normalization'].update(before=15,after=14,changed_program_coordinates=changed,
            changed_aggregate_coordinates=aggregates)
        n.validate_transition(second_before,second_after,second_audit,{key},{'r'})
        n.reverse_transition(second_after,second_before,second_after,second_audit)
        n.reverse_transition(second_after,first_before,first_after,first_audit)
        self.assertEqual(second_after['programs']['binarytrees:old'],first_before['programs']['binarytrees:old'])
        self.assertEqual(second_after['benchmarks'][0]['baseline_loc'],16)

    def test_saved_success_pins_snapshots_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);original,current,audit,added,refs=fixture()
            entry=saved(root,original,current,audit)
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry]))
            untouched=copy.deepcopy(current)
            with patch.dict(n.ADAPTERS,{'fixture_admission':lambda *_:(added,refs)},clear=True):
                result=n.historical_view(root,current)
            self.assertEqual(current,untouched)
            self.assertEqual(result['programs']['fannkuchredux:old'],original['programs']['fannkuchredux:old'])

    def test_current_admitted_raw_samples_cannot_hide_behind_saved_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);original,current,audit,added,refs=fixture()
            entry=saved(root,original,current,audit)
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry]))
            current['programs']['fannkuchredux:new']['samples'][0]=99
            current['programs']['fannkuchredux:new']['publication_record']['samples'][0]=99
            with patch.dict(n.ADAPTERS,{'fixture_admission':lambda *_:(added,refs)},clear=True),self.assertRaisesRegex(ValueError,'Admitted raw'):
                n.historical_view(root,current)

    def test_current_exact_endpoint_group_is_bound_even_when_ratios_equal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);before,current,audit,added,refs=fixture()
            entry=saved(root,before,current,audit)
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry]))
            current['benchmarks'][0]['groups'][-1]['programs'].append('fannkuchredux:new')
            with patch.dict(n.ADAPTERS,{'fixture_admission':lambda *_:(added,refs)},clear=True),self.assertRaisesRegex(ValueError,'endpoint group'):
                n.historical_view(root,current)

    def test_saved_preview_missing_history_and_changed_snapshot_rejected(self):
        for mode in ('preview','missing','bytes','unknown','missingentry'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);original,current,audit,added,refs=fixture()
                entry=saved(root,original,current,audit)
                if mode=='preview':
                    receipt=json.loads((root/entry['success']['path']).read_bytes());receipt['status']='preview-ready'
                    entry['success']=write(root,entry['success']['path'],receipt)
                if mode=='bytes':(root/'admission/before/data/benchmarks.json').write_text('{}')
                if mode=='unknown':entry['audit_key']='unregistered'
                if mode!='missing':write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',
                    admissions=[] if mode=='missingentry' else [entry]))
                with patch.dict(n.ADAPTERS,{'fixture_admission':lambda *_:(added,refs)},clear=True),self.assertRaises(ValueError):
                    n.historical_view(root,current)

    def test_current_minimum_and_history_order_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);original,current,audit,added,refs=fixture()
            entry=saved(root,original,current,audit)
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry]))
            current['benchmarks'][0]['baseline_loc']=19
            with patch.dict(n.ADAPTERS,{'fixture_admission':lambda *_:(added,refs)},clear=True),self.assertRaises(ValueError):
                n.historical_view(root,current)

    def test_unchanged_catalog_needs_no_history_or_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            data={'fixture':'no normalization'}
            self.assertIs(n.historical_view(Path(directory),data),data)

    def test_one_snapshot_pair_covers_two_rebases_and_distinct_pool_additions(self):
        original,current,audit,added,refs=multi_fixture()
        boundaries=n.validate_transition(original,current,audit,added,refs)
        self.assertEqual(len(boundaries),2)
        self.assertEqual(len(added['programs']),3)
        self.assertEqual(len(added['program_inventory']),4)
        result=copy.deepcopy(current)
        for boundary in reversed(boundaries):n.reverse_boundary(result,boundary)
        for pool in ('programs','program_inventory'):
            for key,row in original[pool].items():self.assertEqual(result[pool][key],row)
        self.assertEqual(result['reference_summary'][:2],original['reference_summary'])

    def test_later_recorded_existing_language_coverage_expansion_composes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);before,first,audit,added,refs=multi_fixture()
            entry1=saved(root,before,first,audit,key='r_admission',folder='r')
            second_before=copy.deepcopy(first);second=copy.deepcopy(first)
            key='binarytrees:uiua';row=dict(key=key,benchmark='binarytrees',language='uiua',loc=15,x=1,seconds=3,y=3)
            row['publication_record']=copy.deepcopy(row)
            for pool in ('programs','program_inventory'):second[pool][key]=copy.deepcopy(row)
            endpoint=dict(language='uiua',programs=[key],fast=key,small=key)
            next(b for b in second['benchmarks'] if b['key']=='binarytrees')['groups'].append(endpoint)
            ref=next(r for r in second['reference_summary'] if r['lang']=='uiua');old_ref=copy.deepcopy(ref)
            ref['measured_benchmarks']=[b['key'] for b in second['benchmarks']]
            for kind in ('fast','small'):ref[kind]['x']=n.aggregate(second,ref,kind)
            second_audit=dict(endpoints={'binarytrees':endpoint},normalizations=[],aggregate_change=dict(before=old_ref,after=ref))
            entry2=saved(root,second_before,second,second_audit,key='uiua_admission',folder='uiua')
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry1,entry2]))
            adapters={'r_admission':lambda *_:(added,refs),'uiua_admission':lambda *_:({key},set())}
            with patch.dict(n.ADAPTERS,adapters,clear=True):result=n.historical_view(root,second)
            new_ref=next(r for r in result['reference_summary'] if r['lang']=='uiua')
            self.assertEqual(new_ref['measured_benchmarks'],['nbody','binarytrees','fannkuchredux'])
            self.assertAlmostEqual(new_ref['fast']['x'],statistics.geometric_mean([21/20,15/16,1]))
            self.assertEqual(result['programs']['nbody:uiua']['seconds'],3)
            # The same coverage edit with no bound admission is rejected.
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry1]))
            unbound=copy.deepcopy(second);unbound.pop('uiua_admission')
            with patch.dict(n.ADAPTERS,{'r_admission':adapters['r_admission']},clear=True),self.assertRaisesRegex(ValueError,'coverage/timing'):
                n.historical_view(root,unbound)

    def test_actual_four_retained_candidates_bind_counts_reports_and_transform(self):
        spec=importlib.util.spec_from_file_location('retained_saved_fixture',HERE/'qualification/test_retained_catalog_publication.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        candidates=module.candidates();real_checked=n.checked
        for language,candidate in candidates.items():
            with self.subTest(language=language):
                raw=encode(candidate);ref=dict(path='experiments/fixture/candidate.json',sha256=hashlib.sha256(raw).hexdigest())
                before,metadata=module.catalog(candidate,expanded_reference=language in ('uiua','lua'))
                after,_,audit=module.p.build_publication(before,metadata,candidate,ref,
                    runtime_scope_ref=module.p.APL_RUNTIME_REVIEW if language=='apl' else None)
                def evidence(root,reference):
                    if reference==ref:return raw
                    return real_checked(HERE.parent,reference)
                with patch.object(n,'checked',side_effect=evidence):
                    adapter=n.ADAPTERS[language+'_retained_publication_audit']
                    added,refs=adapter(HERE.parent,audit,before,after)
                    boundaries=n.validate_transition(before,after,audit,added,refs)
                    self.assertEqual(len(boundaries),2 if language=='r' else 1 if language=='uiua' else 0)
                    for mutation in (('count','source_pin','native_sample','runtime_scope','runtime_flag','runtime_command')
                                     if language=='apl' else ('count','source_pin','native_sample')):
                        broken=copy.deepcopy(candidate);bad_audit=copy.deepcopy(audit)
                        key=next(iter(broken['program_inventory']))
                        if mutation=='count':broken['program_inventory'][key]['loc']-=1
                        elif mutation=='native_sample':broken['program_inventory'][key]['seconds']+=1
                        elif mutation=='runtime_scope':bad_audit.pop('runtime_publication_scope_review')
                        elif mutation=='runtime_flag':broken['runtime_publication_metadata_qualified']=True
                        elif mutation=='runtime_command':broken['program_inventory'][key]['runtime_arguments'].append('changed')
                        else:bad_audit['source_counts']['sha256']='0'*64
                        raw=encode(broken);ref['sha256']=hashlib.sha256(raw).hexdigest()
                        bad_audit['candidate']=copy.deepcopy(ref)
                        with self.assertRaises(ValueError):adapter(HERE.parent,bad_audit,before,after)

    def lua_fixture(self, existing_helper=False):
        spec=importlib.util.spec_from_file_location('lua_saved_fixture',HERE/'qualification/test_retained_catalog_publication.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        candidate=module.candidates()['lua'];before,metadata=module.catalog(candidate,expanded_reference=True)
        if existing_helper:
            before['files'][n.LUA_HELPER]=dict(code=candidate['files'][n.LUA_HELPER]['code'],
                name='previously retained helper.c',path='sources/previous/gmp.c',retained_metadata=True)
        # Include an existing LuaJIT row/reference: Lua admission must leave it exact.
        old=copy.deepcopy(before['programs']['pidigits:old-c'])
        old.update(key='pidigits:old-luajit',language='luajit')
        old['publication_record']={k:copy.deepcopy(v) for k,v in old.items() if k!='publication_record'}
        for pool in ('programs','program_inventory'):before[pool][old['key']]=copy.deepcopy(old)
        before['benchmarks'][-1]['groups'].append(dict(language='luajit',label='LuaJIT',
            fast=old['key'],small=old['key'],programs=[old['key']]))
        before['reference_summary'].append(dict(lang='luajit',label='LuaJIT',measured_benchmarks=['pidigits'],
            fast=dict(x=1,y=2),small=dict(x=1,y=2)))
        raw=encode(candidate);ref=dict(path='experiments/lua-fixture/candidate.json',sha256=hashlib.sha256(raw).hexdigest())
        after,_,audit=module.p.build_publication(before,metadata,candidate,ref)
        return candidate,before,after,audit

    def test_lua_existing_identical_helper_preserves_prior_source_metadata(self):
        candidate,before,after,audit=self.lua_fixture(existing_helper=True)
        raw=encode(candidate);real_checked=n.checked
        def evidence(root,reference):
            return raw if reference==audit['candidate'] else real_checked(HERE.parent,reference)
        with patch.object(n,'checked',side_effect=evidence):
            added,refs=n.validate_lua(HERE.parent,audit,before,after)
            n.validate_transition(before,after,audit,added,refs)
            self.assertEqual(after['files'][n.LUA_HELPER],before['files'][n.LUA_HELPER])
            broken=copy.deepcopy(after);broken['files'][n.LUA_HELPER]=copy.deepcopy(candidate['files'][n.LUA_HELPER])
            with self.assertRaises(ValueError):n.validate_lua(HERE.parent,audit,before,broken)

    def test_lua_complete_bundle_controls_and_raw_metadata_are_independently_bound(self):
        candidate,before,after,audit=self.lua_fixture();real_checked=n.checked
        for fault in ('helper_source','helper_count','helper_omitted','role','raw_attempt','raw_routing',
                      'control_samples','control_source','control_omitted','runtime','runtime_scope','boundary',
                      'algorithm','old_count','alias'):
            broken=copy.deepcopy(candidate);current=copy.deepcopy(after);record=copy.deepcopy(audit)
            row=broken['program_inventory']['pidigits:lua-interpreted-gmp-listed-1']
            if fault=='helper_source':broken['files'][n.LUA_HELPER]['code']+='changed'
            elif fault=='helper_count':row['file_roles'][n.LUA_HELPER]['normalized_loc']-=1
            elif fault=='helper_omitted':row['files'].pop()
            elif fault=='role':row['file_roles'][n.LUA_HELPER]['role']='application'
            elif fault=='raw_attempt':row['sample_execution_metadata'][0]['command'][-1]='9999'
            elif fault=='raw_routing':row['sample_evidence']['receipts'][0]['path']='other.json'
            elif fault=='control_samples':broken['matched_mech_controls']['mech-small-control']['samples'][0]+=1
            elif fault=='control_source':broken['matched_mech_controls']['mech-fast-control']['source_sha256']='0'*64
            elif fault=='control_omitted':broken['matched_mech_controls'].pop('mech-small-control')
            elif fault=='runtime':row['runtime_arguments'][0]='luajit'
            elif fault=='runtime_scope':row['runtime_policy']='JIT compiler'
            elif fault=='boundary':row['timing_measurement']['kind']='kernel-only'
            elif fault=='algorithm':row['algorithm']['native_benchmark_kernel']=True
            elif fault=='old_count':row['original_producer_loc']+=1
            else:row['timing_alias_of']='pidigits:lua-interpreted-gmp-listed-6'
            raw=encode(broken);record['candidate']['sha256']=hashlib.sha256(raw).hexdigest()
            # Reflect the forgery in both saved data and candidate; rejection
            # must come from retained source/report evidence, not their mismatch.
            current['files'].update(copy.deepcopy(broken['files']))
            for pool in ('programs','program_inventory'):
                for key,value in broken['program_inventory'].items():
                    if key not in current[pool]:continue
                    admitted=current[pool][key]
                    admitted.update({k:copy.deepcopy(v) for k,v in value.items()
                                     if k not in ('eligible_for_chart','chart_admission')})
                    admitted['chart_admission']['candidate']=copy.deepcopy(record['candidate'])
                    admitted['publication_record']={k:copy.deepcopy(v) for k,v in admitted.items() if k!='publication_record'}
            def evidence(root,reference):
                return raw if reference==record['candidate'] else real_checked(HERE.parent,reference)
            with self.subTest(fault=fault),patch.object(n,'checked',side_effect=evidence),self.assertRaises(ValueError):
                n.validate_lua(HERE.parent,record,before,current)

    def test_lua_only_nine_to_ten_no_rebase_and_luajit_preservation(self):
        candidate,before,after,audit=self.lua_fixture();raw=encode(candidate);real_checked=n.checked
        def evidence(root,reference):
            return raw if reference==audit['candidate'] else real_checked(HERE.parent,reference)
        with patch.object(n,'checked',side_effect=evidence):
            added,refs=n.validate_lua(HERE.parent,audit,before,after)
            self.assertEqual(n.validate_transition(before,after,audit,added,refs),[])
            self.assertEqual((len(added['programs']),len(added['program_inventory'])),(2,4))
            self.assertEqual(audit['aggregate_change']['after']['measured_benchmarks'],[b['key'] for b in before['benchmarks']])
            for fault in ('minimum','time_minimum','rebase','coverage','duplicate_coverage','luajit','other_row',
                          'baseline','language_metadata','source_inventory','scalar_type'):
                old=copy.deepcopy(before);new=copy.deepcopy(after);record=copy.deepcopy(audit)
                if fault=='minimum':old['benchmarks'][-1]['baseline_loc']=300
                elif fault=='time_minimum':old['benchmarks'][-1]['baseline_seconds']=1
                elif fault=='rebase':record['normalizations']=[dict(benchmark='pidigits',before=300,after=275)]
                elif fault=='coverage':next(r for r in old['reference_summary'] if r['lang']=='lua')['measured_benchmarks'].pop()
                elif fault=='duplicate_coverage':next(r for r in old['reference_summary'] if r['lang']=='lua')['measured_benchmarks'][-1]='nbody'
                elif fault=='luajit':new['programs']['pidigits:old-luajit']['seconds']+=1
                elif fault=='other_row':new['programs']['nbody:old-c']['loc']+=1
                elif fault=='language_metadata':new['languages'][0]['timed_benchmarks'].pop()
                elif fault=='source_inventory':new['files']['unrelated']=dict(code='changed')
                elif fault=='scalar_type':record['native_runs']=False
                else:new['benchmarks'][0]['baseline_loc']-=1
                with self.subTest(fault=fault),self.assertRaises(ValueError):
                    added,refs=n.validate_lua(HERE.parent,record,old,new)
                    n.validate_transition(old,new,record,added,refs)

    def test_lua_saved_no_rebase_admission_keeps_expanded_coverage_in_historical_view(self):
        candidate,before,after,audit=self.lua_fixture();raw=encode(candidate);real_checked=n.checked
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            entry=saved(root,before,after,audit,key='lua_retained_publication_audit',folder='lua')
            write(root,n.HISTORY,dict(schema='canonical-loc-normalization-history-v1',admissions=[entry]))
            def evidence(target,reference):
                if reference==audit['candidate']:return raw
                if reference in [dict(path=p,sha256=d) for p,d in n.LUA_PINS.values()]:
                    return real_checked(HERE.parent,reference)
                return real_checked(target,reference)
            with patch.object(n,'checked',side_effect=evidence):
                result=n.historical_view(root,after)
                self.assertEqual(result,after)
                self.assertEqual(len(next(r for r in result['reference_summary'] if r['lang']=='lua')['measured_benchmarks']),10)
                altered=copy.deepcopy(after);altered['program_inventory']['pidigits:lua-interpreted-gmp-listed-1']['samples'][0]+=1
                with self.assertRaises(ValueError):n.historical_view(root,altered)

    def test_new_coordinates_publication_and_own_metadata_are_checked(self):
        for mode in ('x','y','publication','aggregate_y','aggregate_label','missing_rebase'):
            before,after,audit,added,refs=multi_fixture()
            key='fannkuchredux:r'
            if mode in ('x','y'):after['programs'][key][mode]=99
            elif mode=='publication':after['programs'][key]['publication_record']['seconds']=99
            elif mode=='aggregate_y':
                after['reference_summary'][-1]['fast']['y']=99
                audit['aggregate_change']['after']=copy.deepcopy(after['reference_summary'][-1])
            elif mode=='aggregate_label':
                # An existing own aggregate may expand coverage, but cannot
                # rewrite unrelated metadata such as its label.
                before=copy.deepcopy(after);audit=dict(endpoints={},normalizations=[],
                    aggregate_change=dict(before=copy.deepcopy(after['reference_summary'][-1]),
                                          after=copy.deepcopy(after['reference_summary'][-1])))
                audit['aggregate_change']['after']['label']='changed'
                after['reference_summary'][-1]['label']='changed';added={pool:set() for pool in ('programs','program_inventory')};refs=set()
            else:
                # Independent normalization audit absence cannot authorize a
                # lower newly admitted minimum, even with self-consistent x.
                before,after,audit,added,refs=fixture('nbody',20,19,'r')
                audit=dict(endpoints={'nbody':audit['endpoint']},normalizations=[])
                after['benchmarks'][0]['baseline_loc']=20
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                n.validate_transition(before,after,audit,added,refs)

    def test_old_positive_nonselected_inventory_cannot_disappear_from_rebase(self):
        before,after,audit,added,refs=fixture()
        key='fannkuchredux:old-nonselected'
        row=copy.deepcopy(before['program_inventory']['fannkuchredux:old'])
        row['key']=row['publication_record']['key']=key
        before['program_inventory'][key]=copy.deepcopy(row)
        row['x']=row['publication_record']['x']=None
        after['program_inventory'][key]=row
        with self.assertRaisesRegex(ValueError,'positive coordinate availability'):
            n.validate_transition(before,after,audit,added,refs)

    def test_old_null_coordinate_cannot_be_promoted_by_normalization(self):
        before,after,audit,added,refs=fixture()
        key='fannkuchredux:old-null'
        row=copy.deepcopy(before['program_inventory']['fannkuchredux:old'])
        row['key']=row['publication_record']['key']=key;row['x']=row['publication_record']['x']=None
        before['program_inventory'][key]=copy.deepcopy(row)
        row['x']=row['publication_record']['x']=31/20
        after['program_inventory'][key]=row
        audit['normalization']['changed_program_coordinates'].append(
            dict(pool='program_inventory',key=key,before=None,after=31/20))
        with self.assertRaisesRegex(ValueError,'positive coordinate availability'):
            n.validate_transition(before,after,audit,added,refs)

    def test_old_null_or_absent_x_field_membership_is_preserved(self):
        for missing in (False,True):
            for publication in (False,True):
                before,after,audit,added,refs=fixture()
                key='fannkuchredux:old-unqualified'
                row=copy.deepcopy(before['program_inventory']['fannkuchredux:old'])
                row['key']=row['publication_record']['key']=key
                row['x']=row['publication_record']['x']=None
                if missing:
                    row.pop('x');row['publication_record'].pop('x')
                before['program_inventory'][key]=copy.deepcopy(row)
                after['program_inventory'][key]=copy.deepcopy(row)
                n.validate_transition(before,after,audit,added,refs)
                target=after['program_inventory'][key]['publication_record'] if publication else after['program_inventory'][key]
                if missing:target['x']=None
                else:target.pop('x')
                with self.subTest(missing=missing,publication=publication),self.assertRaisesRegex(ValueError,'field availability'):
                    n.validate_transition(before,after,audit,added,refs)

    def test_missing_original_null_metadata_field_is_rejected(self):
        original,current,audit,added,refs=fixture()
        original['benchmarks'][0]['optional']=None
        with self.assertRaisesRegex(ValueError,'metadata'):n.validate_transition(original,current,audit,added,refs)

    def test_actual_uiua_candidate_counts_report_and_small_snapshot_replay(self):
        spec=importlib.util.spec_from_file_location('uiua_saved_fixture',HERE/'qualification/test_uiua_fann_publication.py')
        fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
        candidate=fixture_module.candidate()
        raw=encode(candidate)
        candidate_ref=dict(path='experiments/uiua/fann-v5-publication-v1/fixture/candidate.json',
                           sha256=hashlib.sha256(raw).hexdigest())
        original,languages=fixture_module.catalog()
        current,_,audit=fixture_module.p.build_publication(original,languages,candidate,candidate_ref)
        real_checked=n.checked
        def evidence(root,ref):
            if ref==candidate_ref:
                self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['sha256'])
                return raw
            return real_checked(HERE.parent,ref)
        with patch.object(n,'checked',side_effect=evidence):
            added,refs=n.validate_uiua(HERE.parent,audit,original,current)
            n.validate_transition(original,current,audit,added,refs)
            for mutation in ('source','count','report_pin','candidate_time'):
                broken=copy.deepcopy(candidate);bad_audit=copy.deepcopy(audit)
                key='fannkuchredux:parallel-study:uiua-compact'
                if mutation=='source':broken['files'][broken['program_inventory'][key]['source_sha256']]['code']+='changed'
                elif mutation=='count':broken['program_inventory'][key]['loc']=19
                elif mutation=='candidate_time':broken['program_inventory'][key]['seconds']=1
                else:bad_audit['report']['sha256']='0'*64
                raw=encode(broken);candidate_ref['sha256']=hashlib.sha256(raw).hexdigest()
                bad_audit['candidate']=copy.deepcopy(candidate_ref)
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                    n.validate_uiua(HERE.parent,bad_audit,original,current)

    def test_strict_json_and_safe_regular_evidence(self):
        with self.assertRaises(ValueError):n.strict_json(b'{"x":1,"x":2}')
        with self.assertRaises(ValueError):n.safe_path('../outside')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'actual').write_text('x');(root/'linked').symlink_to(root/'actual')
            with self.assertRaises(ValueError):n.read_bytes(root,'linked')


if __name__=='__main__':unittest.main()
