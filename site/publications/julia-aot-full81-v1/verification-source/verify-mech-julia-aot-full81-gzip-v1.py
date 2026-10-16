import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import urllib.request

# Fill these from the exact validated remote build; no prior build is assumed.
BUILD_VERSION = '1b021c21ca65c531'
GZIP_SHA256 = 'd78ae04ce33a057d22e5801ab85e843d2ab414014bbc51a1a34c1cf89df678dc'
DATASET_SHA256 = 'ec3e743dc01ae1508974818155143965b6737596be7400e4c724c5475cdbda5c'
ENCODED_BYTES = 1239655
DECODED_BYTES = 8567799
if not (re.fullmatch('[0-9a-f]{16}', BUILD_VERSION)
        and all(re.fullmatch('[0-9a-f]{64}', value) for value in (GZIP_SHA256, DATASET_SHA256))
        and type(ENCODED_BYTES) is int and 0 < ENCODED_BYTES <= 2 * 1024 * 1024
        and type(DECODED_BYTES) is int and DECODED_BYTES > 0):
    raise RuntimeError('Replace every reviewed build placeholder before live verification')
output = Path('/tmp/mech-julia-aot-full81-pages-20261015/live-gzip.json')
encoded_output = output.parent / 'live-data.json.gz'
assert not output.exists(), 'Preserve prior receipt; choose a fresh output before a retry'
assert not encoded_output.exists(), 'Preserve prior encoded body'
record = {
    'schema': 'benchmark-julia-aot-full81-gzip-verification-v1',
    'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'url': 'https://mech-lang.org/benchmarks/data.json',
    'build': BUILD_VERSION,
    'request_accept_encoding': 'gzip',
}
try:
    request = urllib.request.Request(record['url'], headers={
        'Accept-Encoding': 'gzip', 'Cache-Control': 'no-cache',
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        record['http_status'] = response.status
        record['response_headers'] = dict(response.headers.items())
        assert response.status == 200
        assert response.headers.get('Content-Encoding', '').lower() == 'gzip'
        encoded = response.read(2 * 1024 * 1024 + 1)
    encoded_output.write_bytes(encoded)
    record['encoded_bytes'] = len(encoded)
    record['encoded_sha256'] = hashlib.sha256(encoded).hexdigest()
    assert len(encoded) == ENCODED_BYTES
    assert record['encoded_sha256'] == GZIP_SHA256
    decoded = gzip.decompress(encoded)
    record['decoded_bytes'] = len(decoded)
    record['decoded_sha256'] = hashlib.sha256(decoded).hexdigest()
    assert len(decoded) == DECODED_BYTES
    assert record['decoded_sha256'] == DATASET_SHA256
    record['status'] = 'passed'
except Exception as error:
    record['status'] = 'failed'
    record['error'] = f'{type(error).__name__}: {error}'
output.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record), flush=True)
raise SystemExit(0 if record['status'] == 'passed' else 1)
