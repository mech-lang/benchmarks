#!/usr/bin/env python3
"""Check individual upstream citations against primary-host responses."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import hashlib,html,json,re
ROOT=Path(__file__).resolve().parents[1]

def fetch(url):
    requested=url
    # GitHub's raw endpoint returns the actual pinned source bytes.
    if 'github.com/' in url and '/blob/' in url:
        url=url.replace('https://github.com/','https://raw.githubusercontent.com/',1).replace('/blob/','/',1)
    try:
        with urlopen(Request(url,headers={'User-Agent':'mech-benchmark-source-audit/1'}),timeout=25) as response:
            body=response.read();status=response.status;resolved=response.url
        row=dict(url=requested,retrieved_url=resolved,status=status,body_sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
        if '/program/' in requested:
            blocks=re.findall(r'<pre\b[^>]*>(.*?)</pre>',body.decode('utf-8'),re.S|re.I)
            if blocks:
                code=html.unescape(re.sub(r'<[^>]*>','',blocks[0]))
                row['normalized_source_sha256']=hashlib.sha256(code.replace('\r\n','\n').strip().encode()).hexdigest()
        return row
    except (HTTPError,URLError,TimeoutError,OSError) as error:
        return dict(url=requested,status=getattr(error,'code',None),error=str(error)[:250])

def main():
    data=json.loads((ROOT/'data/benchmarks.json').read_text());catalog={**data['program_inventory'],**data['programs']}
    urls=sorted({s['url'] for p in catalog.values() for s in p['authorship']['sources'] if s['relationship'] in ['implementation','reference implementation']})
    with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(fetch,urls))
    for row in rows:
        if row.get('normalized_source_sha256'):
            row['matching_retained_source_sha256']=[sha for sha,f in data['files'].items() if hashlib.sha256(f['code'].replace('\r\n','\n').strip().encode()).hexdigest()==row['normalized_source_sha256']]
    result=dict(schema='benchmark-source-citation-checks.v1',checked_at=datetime.now(timezone.utc).isoformat(),
                scope='Availability and response-byte checks only. A reachable URL does not by itself establish original authorship or a license grant.',
                summary=dict(citations=len(rows),available=sum(r.get('status')==200 for r in rows),unavailable=sum(r.get('status')!=200 for r in rows)),citations=rows)
    (ROOT/'data/source-citation-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
if __name__=='__main__':main()
