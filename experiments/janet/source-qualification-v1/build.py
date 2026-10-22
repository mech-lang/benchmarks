"""Reconcile exact Janet source measures; never infer missing logical LOC."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
JANET=HERE.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    inputs=[]
    catalog=ROOT/'data/benchmarks.json'
    assert sha(catalog)=='99db1ecdd4f8a20fc6aabfc13d493728a4a36d94cdc6778235376ebb60983d1c'
    inputs.append(dict(path='data/benchmarks.json',sha256=sha(catalog)))
    def load(p):
        inputs.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
        return json.loads(p.read_bytes())
    original=load(JANET/'source-measures-v1.json')
    overlays=load(JANET/'source-overlay-measures-v1.json')
    core=load(JANET/'source-count-v1/run-v1/results.json')
    published=load(JANET/'source-count-v2/run-v1/results.json')
    lexical=load(JANET/'lexical-v1/run-v1/results.json')
    for folder,report in [('source-count-v1',core),('source-count-v2',published)]:
        assert sha(JANET/folder/'run.py')==report['controller_sha256']
        assert sha(JANET/folder/'format.janet')==report['formatter_sha256']
    assert sha(JANET/'lexical-v1/count.janet')==lexical['counter_sha256']
    assert sha(JANET/'lexical-v1/run.py')==lexical['controller_sha256']
    assert sha(JANET/'dependencies-v2/spork-format/snapshot.json')==lexical['grammar_snapshot_sha256']
    grammar=json.loads((JANET/'dependencies-v2/spork-format/snapshot.json').read_bytes())
    for name,pin in grammar['files'].items():
        assert sha(JANET/'dependencies-v2/spork-format'/name)==pin['sha256']
    assert core['status']=='native-reader-format-roundtrip-compile-and-149-contracts-pass'
    assert published['status']=='published-formatter-roundtrip-compile-and-149-contracts-pass'
    assert len(core['bounded_outputs'])==len(published['bounded_outputs'])==149
    assert len(core['sources'])==len(published['sources'])==len(lexical['profiles'])==13
    assert lexical['status']=='13-source-grammar-counts-and-eight-hand-counted-layout-probes-pass'
    assert len(lexical['probes'])==8
    assert all(p['packed']==p['wrapped']==p['hand_count'] for p in lexical['probes'])
    assert all(not p['identical_formatted_bytes'] for p in published['probes'][:8])
    raw={r['source']:r for r in original['profiles'].values()}
    raw.update(overlays['profiles'])
    rows=[]
    for index,row in enumerate(lexical['profiles']):
        name=row['source']; source=ROOT/name
        assert sha(source)==row['source_sha256']==raw[name]['sha256']
        a=next(r for r in core['sources'] if r['source']==name)
        b=next(r for r in published['sources'] if r['source']==name)
        assert a['source_sha256']==b['source_sha256']==row['source_sha256']
        for f in (a,b):
            assert f['native_reader_roundtrip_verified'] and f['independent_process_idempotence_verified'] and f['native_compile_clean']
            assert sha(ROOT/f['formatted_source'])==f['formatted_sha256']
        for label in ('source','reader','published'):
            capture=JANET/'lexical-v1/run-v1'/f'{index:02d}-{label}'
            assert (capture/'stderr.bin').read_bytes()==b''
            assert (capture/'stdout.bin').read_bytes()==f"{row['language_lexical_tokens']}\n".encode()
        assert a['reader_formatted_loc']==len([line for line in (ROOT/a['formatted_source']).read_bytes().splitlines() if line.strip()])
        assert b['published_formatted_loc']==len([line for line in (ROOT/b['formatted_source']).read_bytes().splitlines() if line.strip()])
        metric={k:raw[name][k] for k in ['physical_lines','utf8_bytes','unicode_codepoints','gzip_bytes','gzip_sha256','cl100k_base_tokens']}
        rows.append(dict(source=name,source_sha256=row['source_sha256'],**metric,
            language_lexical_tokens=row['language_lexical_tokens'],lexical_count_qualified_for_exact_source=True,
            reader_formatted_nonblank_rows=a['reader_formatted_loc'],
            published_formatter_nonblank_rows=b['published_formatted_loc'],
            published_formatter_retains_input_layout=True,
            canonical_formatted_loc=None,logical_normalized_loc=None,
            normalization_status='Native grammar lexical count qualified; neither formatter row measure establishes input-layout-independent logical LOC.',
            application_boundary='All authored application text and helpers; unchanged general libraries and runtime excluded.'))
    # Every recorded native invocation must have complete owned cleanup evidence.
    receipt_count=0
    for folder in ['source-count-v1','source-count-v2','lexical-v1']:
        for p in (JANET/folder).rglob('process.json'):
            r=json.loads(p.read_bytes())
            assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],str(p)
            receipt_count+=1
    return dict(schema='janet-source-qualification.v1',inputs=inputs,
        profiles=rows,native_process_receipts_verified=receipt_count,
        formatted_corpus_executions=298,lexical_hand_count_probes=8,
        historical_field_reconciliation='The two raw formatter reports use names ending _formatted_loc for all nonblank output rows, including preserved comments. Here those fields are explicitly nonblank_rows, not noncomment application LOC.',
        lexical_bias='Language-specific grammar tokens are not language-neutral complexity, logical statements or minimum expressiveness. Reader abbreviations, strings and compound delimiters affect the count.',
        chart_admission=False,canonical_catalog_changed=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=build();output=HERE/'results.json'
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status='checked' if args.check else 'written',sources=len(result['profiles']),native_process_receipts_verified=result['native_process_receipts_verified'])))
