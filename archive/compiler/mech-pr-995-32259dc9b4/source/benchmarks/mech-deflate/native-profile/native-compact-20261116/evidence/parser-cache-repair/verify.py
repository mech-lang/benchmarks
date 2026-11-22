"""Verify parser-repair provenance, matched builds and actual deployed streams."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
from statistics import median
import io,json,math,tarfile,zlib

HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
sha=lambda b:sha256(b).hexdigest()

def close(a,b):
    assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)

def main():
    summary=read(HERE/'summary.json');archive=read(HERE/'archive.json')
    blob=HERE/archive['file'];assert sha(blob.read_bytes())==archive['sha256']
    with tarfile.open(blob,'r:gz') as t:
        members=t.getmembers();assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
        data={m.name:t.extractfile(m).read() for m in members}
    mapping=json.loads(data['files.json'])
    for logical,record in mapping.items():
        actual=data[record['blob']];assert len(actual)==record['bytes'] and sha(actual)==record['sha256'],logical
    get=lambda p:data[mapping[p]['blob']]
    js=lambda p:json.loads(get(p))
    assert summary['codec_source_changed'] is False and summary['runtime_score']=={'roc':81,'libdeflate':63}
    for path,pin in summary['source_inputs_sha256'].items():assert sha(get('source/inputs/'+path))==pin
    source=get('source/program.mec');assert len(source)==243209 and sha(source)==summary['codec_sha256']
    old=get('parser/failed-source.log').decode();assert 'syntax/recovery-limit' in old and '239584' in old and '243209' in old
    for name in ['prefix-repaired','cache-repaired']:
        proof=js('parser/'+name+'.json');assert proof['clean'];stats=proof['stats']
        assert stats['parser_steps']==3967302 and stats['events_emitted']==718353 and stats['new_node_count']==160696
    initial=get('tests/cache-repair-initial-failure.log').decode();assert '549 passed; 1 failed;' in initial and 'one_shot_lexical_replay_preserves_identities_limits_and_work' in initial
    tests=get('tests/cache-repair.log').decode();counts=[int(line.split('ok. ')[1].split(' passed')[0]) for line in tests.splitlines() if 'test result: ok.' in line]
    assert counts==[550,16,13,2,5] and sum(counts)==586
    assert 'one_shot_lexical_replay_preserves_identities_limits_and_work ... ok' in tests
    recipes=read(HERE.parent/'arm64-byte-extensions/recipes.json')['roles']
    for generation in ['prefix','cache']:
        records=js('replays/'+generation+'/standard.json');assert records['all_three_exact'] and len(records['records'])==2
        for record in records['records']:
            assert record['artifacts']==recipes[record['role']]['artifacts'] and record['full_integrated_source_identity']
        checks=js('replays/'+generation+'/checked.json');assert checks['all_pass'] and len(checks['records'])==3
        default=checks['records'][0];assert default['default_invocation'] and default['full_integrated_source_identity']
        assert default['checked_failure_probe']['cases']==6 and default['checked_failure_probe']['observations']==12 and default['checked_failure_probe']['exact_recoveries']==12
        outputs=js('replays/'+generation+'/correctness.json');assert len(outputs)==default['verified_exact_calls']
        assert all(r['exact_reference'] and r['independent_inflation'] and r['input_alias_unchanged'] and r['borrowed_output_alias_unchanged'] for r in outputs)
        for record in checks['records'][1:]:assert record['all_three_exact'] and record['checked'] and record['artifacts']==recipes[record['role']]['artifacts']
    public=read(HERE/'public-replay.json');assert public['all_three_exact'] and len(public['records'])==2
    assert public['script_sha256']==sha((HERE/'replay.py').read_bytes())
    for record in public['records']:assert record['artifacts']==recipes[record['role']]['artifacts'] and record['source_commit']==summary['source_commit'] and record['full_integrated_source_identity']
    fixtures=js('deployments/fixtures.json');fixture={r['case']:r for r in fixtures};assert len(fixture)==81
    total=0
    for generation in ['regressed','repaired']:
        base='builds/'+generation+'/'
        plan=js(base+'plan.json');comparison=js(base+'comparison.json');recorded=js(base+'summary.json')
        assert sha(get(base+'plan.json'))==comparison['plan_sha256']==recorded['plan_sha256']
        assert sha(get('controllers/timing-driver-as-run.py'))==plan['timer_sha256']
        actors=tuple(plan['actors']);orders=plan['orders'];rows=comparison['observations'];assert len(actors)==6 and len(rows)==len(orders)==12
        for position in range(6):assert Counter(order[position] for order in orders)==dict.fromkeys(actors,2)
        assert recorded['medians']==comparison['medians'] and recorded['paired_ratios']==comparison['paired_ratios'] and recorded['phases']==comparison['phases']
        for actor in actors:
            job=plan['actors'][actor];warm=comparison['warmup'][actor]
            assert sha(get(base+'warmup/'+actor+'/compressor'))==warm['stripped_executable']['sha256']
            assert len(get(base+'warmup/'+actor+'/compressor'))==warm['stripped_executable']['bytes']
            for i,row in enumerate(rows,1):
                result=row[actor];assert result['generated_artifacts']==job['artifact_sha256'];assert result['stripped_executable']==warm['stripped_executable']
                for artifact,pin in result['generated_artifacts'].items():
                    name={'encoder':'program.o','metadata':'metadata.json','bytecode':'program.mecb'}[artifact]
                    assert sha(get(base+f'order-{i}/'+actor+'/artifacts/'+name))==pin
                for step in ['source','link','strip']:assert result['seconds'][step]>=0 and result['commands'][step]
                assert result['seconds']['source_through_link']>=result['seconds']['source']
            for cut,value in comparison['medians'][actor].items():close(value,median(r[actor]['seconds'][cut] for r in rows))
            if actor.startswith('mech-'):
                for peer,value in comparison['paired_ratios'][actor].items():close(value,median(r[actor]['seconds']['source_through_link']/r[peer]['seconds']['source_through_link'] for r in rows))
                for phase,value in comparison['phases'][actor].items():close(value,median(next(p['seconds'] for p in r[actor]['compiler_phases'] if p['phase']==phase) for r in rows))
        if generation=='repaired':
            for role,value in recorded['paired_regressed_control'].items():close(value,median(r[role]['seconds']['source_through_link']/r['mech-regressed-selected']['seconds']['source_through_link'] for r in rows))
        deployed=js(base+'deployment-smokes.json');assert deployed['checked_executions']==len(deployed['records'])==486
        for actor,pin in deployed['actors_sha256'].items():assert pin==sha(get(base+'warmup/'+actor+'/compressor'))
        for record in deployed['records']:
            raw=get('deployments/'+record['output_sha256']+'.deflate');assert sha(raw)==record['output_sha256'];assert len(raw)==record['output_bytes']
            inp=zlib.decompress(raw,-15);assert sha(inp)==fixture[record['case']]['input_sha256']==record['input_sha256']
            assert record['independent_inflation'] and (record['matches_selected_bytes'] or record['actor']=='libdeflate')
            if record['actor']!='libdeflate':assert sha(raw)==fixture[record['case']]['raw_reference_sha256']
            total+=1
    result={'parser_tests':586,'standard_source_replays':6,'checked_source_replays':4,'default_executable_builds':2,'complete_build_orders':24,'actors_each':6,'verified_deployed_outputs':total,'runtime_score_unchanged':True}
    assert total==972
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
