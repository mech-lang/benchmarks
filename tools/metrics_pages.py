"""Generate static, directly linkable routes for the performance explorer."""
from html import escape
from pathlib import Path
import re

PAGES = {
    '': ('Mech performance', 'Compare Mech with Rust and libdeflate. The reference is always 1×.', 'summary'),
    'deflate': ('DEFLATE compression', 'Native compression calls · libdeflate 1.26, level 12 · Apple M3', 'deflate'),
    'applications': ('Applications', 'Application performance · Rust', 'suite'),
    'runtime': ('Runtime', 'Small runtime tests · Rust', 'suite'),
    'scaling': ('Worker scaling', 'Complete worker groups · Rust', 'suite'),
    'compiler': ('Compiler', 'Source-to-executable build time · Rust', 'suite'),
    'size': ('Code & output size', 'Executable, object, artifact and compressed output bytes', 'suite'),
    'memory': ('Memory & allocations', 'Retained storage, worker peak memory and allocation counts', 'suite'),
    'lifecycle': ('Activation & cleanup', 'Initial turns, activation, snapshots and teardown', 'suite'),
    'compression-history': ('Checked compression · historical', 'Earlier managed program calls · Mech measurements without a matched level-12 timer', 'suite'),
    'knucleotide': ('K-nucleotide', 'Whole-process runtime · full FASTA N=25,000,000 · Rust', 'suite'),
    'nbody': ('N-body', 'Whole-process runtime · 50,000,000 steps · Rust', 'suite'),
    'related-post-gen': ('Related Post Gen', '5,000 posts · post-JSON work and whole-process measurements', 'suite'),
}

def build_metrics_pages(output, catalog=None):
    output = Path(output)
    template_path = output / 'campaigns.html'
    if not template_path.exists():
        return []
    template = template_path.read_text()
    pages = dict(PAGES)
    for case in (catalog or {}).get('cases', []):
        if not re.fullmatch(r'[a-z0-9-]+', case['id']):
            raise ValueError('Invalid metrics task route')
        pages['tasks/' + case['id']] = (case['title'], 'Measurements, matched references and implementation details for this task.', 'suite')
    written = []
    for route, (title, intro, kind) in pages.items():
        if kind == 'suite' and route in PAGES and route not in ('knucleotide','nbody','related-post-gen'):
            kind = 'summary'
        path = output / 'metrics' / route / 'index.html'
        path.parent.mkdir(parents=True, exist_ok=True)
        html = re.sub(r'<title>.*?</title>', '<title>Mech · ' + escape(title) + '</title>', template)
        html = re.sub(r'(<link rel="canonical" href=")[^"]+', r'\g<1>https://mech-lang.org/metrics/' + (route + '/' if route else ''), html)
        html = re.sub(r'(<h1 id="page-title">).*?(</h1>)', lambda m: m[1] + escape(title) + m[2], html)
        html = re.sub(r'(<p class="intro" id="page-intro">).*?(</p>)', lambda m: m[1] + escape(intro) + m[2], html)
        for panel, view in [('summary-panel', 'summary'), ('deflate-m3', 'deflate'), ('suite-panel', 'suite')]:
            html = re.sub(r'(<section id="' + panel + r'"[^>]*?)(?: hidden)?>', lambda m: m[1].removesuffix(' hidden') + ('' if kind == view else ' hidden') + '>', html, count=1)
        html = html.replace('href="/metrics/" aria-current="page">Summary', 'href="/metrics/">Summary')
        current = '/metrics/' + (route + '/' if route else '')
        html = html.replace('href="' + current + '">', 'href="' + current + '" aria-current="page">', 1)
        path.write_text(html)
        written.append(path)
    return written
