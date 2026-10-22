"""Read-only release-source inspection; retain only GMP division sources/licenses."""
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
URL='https://gmplib.org/download/gmp/gmp-6.3.0.tar.xz'
out=HERE/'gmp-release-source-v1';out.mkdir(exist_ok=False)
with urlopen(Request(URL,headers={'User-Agent':'mech-benchmark-library-source-audit/1'}),timeout=40) as response:
    body=response.read();status=response.status;resolved=response.url
assert status==200
files={}
with tarfile.open(fileobj=io.BytesIO(body),mode='r:xz') as archive:
    for name in ('mpz/fdiv_q.c','mpz/tdiv_q.c','COPYING.LESSERv3','COPYINGv2','AUTHORS'):
        member=archive.getmember('gmp-6.3.0/'+name);assert member.isfile()
        data=archive.extractfile(member).read();path=out/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        files[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
result=dict(schema='gmp-release-source-inspection.v1',requested_url=URL,retrieved_url=resolved,status=status,captured_at_utc=datetime.now(timezone.utc).isoformat(),archive_sha256=hashlib.sha256(body).hexdigest(),archive_bytes=len(body),files=files,archive_executed=False,runtime_rebuilt=False,scope='Official version-matched release source; this alone does not prove bit-identical build flags or a complete source-to-installed-binary chain.')
(out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print('Captured official GMP 6.3.0 division source and license files')
