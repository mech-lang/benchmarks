"""Parse diagnostic phase totals without treating nested spans as additive."""
PHASES={'borrow_rows','source_scan','selected_join','join_copy','map_prepare','map_kernel','map_finish'}
def parse(path, *, fused=False):
 phases={};marks=[];rows=None
 for line in path.read_text().splitlines():
  w=line.split()
  if not w:continue
  if w[0]=='PPHASE_V1':
   assert len(w)==6 and w[1] not in phases
   phases[w[1]]=dict(zip(['calls','cpu_ns','wall_ns','maximum_cpu_ns'],map(int,w[2:])))
  elif w[0]=='PMARK_V1':
   assert len(w)==4;marks.append(dict(name=w[1],cpu_ns=int(w[2]),wall_ns=int(w[3])))
  elif w[0]=='PROWS_V1':
   assert len(w)==5 and rows is None
   rows=dict(zip(['direct_windows','direct_rows','cell_windows','cell_rows'],map(int,w[1:])))
 assert set(phases)==PHASES and rows is not None
 assert all(p['calls']>0 and p['cpu_ns']>=0 and p['wall_ns']>=0 for p in phases.values())
 for a,b in zip(marks,marks[1:]):
  assert b['cpu_ns']>=a['cpu_ns'] and b['wall_ns']>=a['wall_ns']
 names=[m['name'] for m in marks]
 assert names[0]=='main_begin' and names[-1]=='main_complete'
 if fused:
  # The map now executes per physical join chunk, before the original logical
  # map header. It has no single unfused begin/end marker interval.
  assert names==['main_begin','capture_begin','capture_complete','selected_join_begin','spawn_begin','main_complete'],names
  assert phases['selected_join']['calls']==1
  assert phases['map_kernel']['calls']>0
  assert phases['join_copy']['calls']==phases['map_kernel']['calls']+1
  assert phases['map_prepare']['calls']==1 and phases['map_finish']['calls']==2
 else:
  for label in ['capture_begin','capture_complete','selected_join_begin','map_kernel_begin','map_kernel_complete','spawn_begin']:
   assert names.count(label)==1,(label,names)
  assert [names.index(n) for n in ['capture_begin','capture_complete','selected_join_begin','map_kernel_begin','map_kernel_complete','spawn_begin']]==sorted(names.index(n) for n in ['capture_begin','capture_complete','selected_join_begin','map_kernel_begin','map_kernel_complete','spawn_begin'])
  assert phases['map_kernel']['calls']==1 and phases['selected_join']['calls']==1
  assert phases['join_copy']['cpu_ns']<=phases['selected_join']['cpu_ns']
 assert rows['cell_windows']==rows['cell_rows']==0
 assert rows['direct_windows']==phases['borrow_rows']['calls']
 return dict(phases=phases,marks=marks,rows=rows,representation="fused-chunks" if fused else "ordinary")
