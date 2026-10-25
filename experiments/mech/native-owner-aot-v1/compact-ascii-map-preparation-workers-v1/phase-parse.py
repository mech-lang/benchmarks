"""Parse actual physical phase boundaries for each retained representation."""
COMMON={'borrow_rows','source_scan','selected_join','join_copy','map_prepare','map_kernel','map_finish'}
EXTRA={'source_loan','joined_transform','chunk_receipt'}

def parse(path, subject):
    assert subject in {'candidate','parent','ordinary'}
    direct=subject in {'candidate','parent'};fused=subject!='ordinary'
    phases={};marks=[];rows=None
    for line in path.read_text().splitlines():
        w=line.split()
        if not w:continue
        if w[0].startswith('PPHASE_'):
            assert w[0]==('PPHASE_V2' if direct else 'PPHASE_V1'),w
            assert len(w)==6 and w[1] not in phases
            phases[w[1]]=dict(zip(['calls','cpu_ns','wall_ns','maximum_cpu_ns'],map(int,w[2:])))
        elif w[0]=='PMARK_V1':
            assert len(w)==4;marks.append(dict(name=w[1],cpu_ns=int(w[2]),wall_ns=int(w[3])))
        elif w[0]=='PROWS_V1':
            assert len(w)==5 and rows is None
            rows=dict(zip(['direct_windows','direct_rows','cell_windows','cell_rows'],map(int,w[1:])))
    assert set(phases)==(COMMON|EXTRA if direct else COMMON) and rows is not None
    unused={'join_copy','map_kernel'} if direct else set()
    for name,p in phases.items():
        assert all(v>=0 for v in p.values()) and p['maximum_cpu_ns']<=p['cpu_ns']
        if name in unused:assert not any(p.values()),(name,p)
        else:assert p['calls']>0,(name,p)
    for a,b in zip(marks,marks[1:]):
        assert b['cpu_ns']>=a['cpu_ns'] and b['wall_ns']>=a['wall_ns']
    names=[m['name'] for m in marks]
    assert names[0]=='main_begin' and names[-1]=='main_complete'
    if fused:
        assert names==['main_begin','capture_begin','capture_complete','selected_join_begin','spawn_begin','main_complete'],names
        assert phases['map_prepare']['calls']==1 and phases['map_finish']['calls']==2
        if direct:
            assert phases['source_loan']['calls']==phases['joined_transform']['calls']+1
            assert phases['chunk_receipt']['calls']==phases['joined_transform']['calls']
        else:assert phases['join_copy']['calls']==phases['map_kernel']['calls']+1
    else:
        assert names==['main_begin','capture_begin','capture_complete','selected_join_begin','map_kernel_begin','map_kernel_complete','spawn_begin','main_complete'],names
        assert phases['map_kernel']['calls']==1
        assert phases['join_copy']['cpu_ns']<=phases['selected_join']['cpu_ns']
    assert phases['selected_join']['calls']==1
    assert rows['cell_windows']==rows['cell_rows']==0
    assert rows['direct_windows']==phases['borrow_rows']['calls']
    return dict(phases=phases,marks=marks,rows=rows,representation=subject,
                physical_meanings='plan.json phase_semantics; legacy copy/map phases are unused for candidate')
