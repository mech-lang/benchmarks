"""Parse complete in-process boundary records; never infer thread retirement."""
from collections import defaultdict

FIELDS=('slot','region','index','width','thread_id','label','wall_ns','cpu_ns',
        'p_instructions','p_cycles','p_user_mach','p_system_mach',
        'e_instructions','e_cycles','e_user_mach','e_system_mach')
WIDTHS=[1,2,3,4,6,12,18]

def parse(path, subject):
    groups=defaultdict(list)
    for line in path.read_text().splitlines():
        if not line.startswith('WCPU_TRACE_V1 '): continue
        words=line.split(); assert len(words)==17,words
        row={k:(v if k=='label' else int(v)) for k,v in zip(FIELDS,words[1:])}
        groups[row['slot']].append(row)
    assert len(groups)==8 and 31 in groups, list(groups)
    for slot,rows in groups.items():
        assert rows[-1]['label']=='body_complete'
        assert len({r['thread_id'] for r in rows})==1
        for a,b in zip(rows,rows[1:]):
            for key in FIELDS:
                if key in ('label','region','index','width','slot','thread_id'):continue
                assert b[key]>=a[key],(subject,slot,key,a,b)
        for row in rows:
            mach=sum(row[k] for k in ('p_user_mach','p_system_mach','e_user_mach','e_system_mach'))
            assert abs(mach*125//3-row['cpu_ns'])<2_000_000,(subject,row)
        if slot!=31:
            labels=[r['label'] for r in rows]
            assert labels[0]=='worker_begin' and 'count_begin' in labels and 'count_complete' in labels
            assert labels.index('count_begin')<labels.index('count_complete')<labels.index('body_complete')
            if subject!='rust':
                assert {'worker_setup_ready','map_publication_complete','generated_body_complete','worker_storage_retired'}<=set(labels)
    workers=[rows for slot,rows in groups.items() if slot!=31]
    assert sorted(rows[0]['width'] for rows in workers)==WIDTHS
    if subject!='rust': assert len({rows[0]['thread_id'] for rows in workers})==7
    return dict(main=groups[31],workers=sorted(workers,key=lambda rows:rows[0]['width']))
