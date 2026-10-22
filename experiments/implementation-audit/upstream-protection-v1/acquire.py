"""Capture direct published source bytes for protection conflicts, never language execution."""
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from audit_owned_implementations import classify,application_shas

def sha(raw):return hashlib.sha256(raw).hexdigest()
def normalized(raw):return raw.decode('utf-8').replace('\r\n','\n').strip().encode('utf-8')

def main():
    path=ROOT/'data/benchmarks.json';data=json.loads(path.read_bytes());catalog={**data.get('program_inventory',{}),**data['programs']}
    conflicts={k:p for k,p in catalog.items() if (q:=classify(p))['upstream_identity']=='normalized-source-match' and not q['preserve_upstream_source']}
    out=HERE/'capture-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',catalog_sha256=sha(path.read_bytes()),controller_sha256=sha(Path(__file__).read_bytes()),sources={},profiles={},native_processes_started=0,new_timing_samples=0,canonical_changes=False)
    for key,p in conflicts.items():
        app=application_shas(p);matches={}
        for ref in p.get('authorship',{}).get('sources',[]):
            if ref.get('relationship') not in ('implementation','reference implementation'):continue
            url=ref.get('url','')
            if not url.startswith('https://') or any(x in url for x in ('github.com/mech-lang/','raw.githubusercontent.com/mech-lang/')):continue
            check=ref.get('citation_check',{});known=set(check.get('matching_retained_source_sha256',[]))|{check.get('body_sha256'),ref.get('upstream_sha256')}
            wanted=set(app)&known
            if not wanted:continue
            if url not in report['sources']:
                requested=url
                if url.startswith('https://github.com/') and '/blob/' in url:url=url.replace('https://github.com/','https://raw.githubusercontent.com/',1).replace('/blob/','/',1)
                with urlopen(Request(url,headers={'User-Agent':'mech-benchmark-source-protection-audit/1'}),timeout=30) as response:
                    body=response.read();status=response.status;resolved=response.url
                assert status==200
                digest=sha(body);body_path=out/(digest+'.response');body_path.write_bytes(body)
                if '/benchmarksgame/program/' in requested:
                    blocks=re.findall(r'<pre\b[^>]*>(.*?)</pre>',body.decode('utf-8'),re.S|re.I);assert blocks
                    code=html.unescape(re.sub(r'<[^>]*>','',blocks[0])).encode('utf-8');kind='Benchmarks Game HTML first pre; tags removed then HTML entities decoded'
                else:code=body;kind='Direct raw pinned upstream source'
                code_path=out/(sha(code)+'.source');code_path.write_bytes(code)
                report['sources'][requested]=dict(requested_url=requested,retrieved_url=resolved,status=status,response=str(body_path.relative_to(ROOT)),response_sha256=digest,source=str(code_path.relative_to(ROOT)),source_sha256=sha(code),normalized_source_sha256=sha(normalized(code)),extraction=kind)
            captured=report['sources'][requested]
            for digest in wanted:
                local=data['files'][digest]['code'].encode('utf-8');assert sha(local)==digest
                if captured['normalized_source_sha256']==sha(normalized(local)):
                    matches.setdefault(digest,[]).append(requested)
        assert set(app)<=set(matches),(key,app,matches)
        report['profiles'][key]=dict(application_source_sha256=app,verified_external_sources=matches,existing_authorship_kind=p.get('authorship',{}).get('kind'),existing_local_adaptation=p.get('local_adaptation'),proposed_preserve_upstream_source=True,ai_authorship_inferred=False)
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    report['status']='all-conflicting-profiles-match-captured-published-source';(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],profiles=len(report['profiles']),captured_urls=len(report['sources']))))

if __name__=='__main__':main()
