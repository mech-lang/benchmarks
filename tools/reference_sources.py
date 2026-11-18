"""Publish a reference's original citation or its exact measured source."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


def source_link(record, campaign, output, root):
    if record.get('backend') != 'rust':
        return None
    source = record.get('source', '').encode()
    digest = record.get('source_sha256')
    if not source or hashlib.sha256(source).hexdigest() != digest:
        raise ValueError('Reference source does not match its recorded hash')
    origin = campaign.get('origin', {})
    if (record.get('case_id') == 'related-post-gen'
            and origin.get('upstream') == 'https://github.com/zupat/related_post_gen'
            and origin.get('upstream_revision') == record.get('revision')):
        return origin['upstream'] + '/tree/' + record['revision'] + '/rust_con'
    authorship = record.get('implementation', {}).get('authorship', {})
    choices = [authorship]
    for path in sorted((Path(root)/'programs/rust'/record['case_id']).glob('**/program.json')):
        choices.append(json.loads(path.read_text()).get('authorship', {}))
    for author in choices:
        if digest not in author.get('source_sha256', []):
            continue
        for citation in author.get('sources', []):
            url = citation.get('url', '')
            if citation.get('relationship') == 'implementation' and urlsplit(url).scheme in ('http', 'https'):
                return url
    target = Path(output)/'reference-sources'/f'{digest}.rs.txt'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source)
    return '/benchmarks/reference-sources/' + target.name
