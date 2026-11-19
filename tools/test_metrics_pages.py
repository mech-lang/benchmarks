import json
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
from metrics_pages import build_metrics_pages, PAGES

ROOT = Path(__file__).resolve().parents[1]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = []
        self.panels = {}
        self.canonical = None
    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        identity = attributes.get('id')
        if identity:
            if identity in self.ids:
                self.duplicates.append(identity)
            self.ids.add(identity)
        if tag == 'section' and identity in ('summary-panel','deflate-m3','suite-panel'):
            self.panels[identity] = 'hidden' not in attributes
        if tag == 'link' and attributes.get('rel') == 'canonical':
            self.canonical = attributes['href']

class MetricsPagesTest(unittest.TestCase):
    def test_pages_and_individual_tasks_have_stable_routes(self):
        catalog = json.loads((ROOT/'suite/catalog.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output/'campaigns.html').write_text((ROOT/'site/src/campaigns.html').read_text())
            paths = build_metrics_pages(output,catalog)
            self.assertEqual(len(paths),len(PAGES)+len(catalog['cases']))
            for path in paths:
                with self.subTest(path=path.relative_to(output)):
                    parser = PageParser()
                    html = path.read_text()
                    parser.feed(html)
                    self.assertFalse(parser.duplicates)
                    self.assertEqual(sum(parser.panels.values()),1)
                    self.assertEqual(parser.canonical,'https://mech-lang.org/'+path.parent.relative_to(output).as_posix()+'/')
                    self.assertIn('/benchmarks/metrics-page.mjs',html)
            root = PageParser();root.feed((output/'metrics/index.html').read_text())
            self.assertTrue(root.panels['summary-panel'])
            compiler = PageParser();compiler.feed((output/'metrics/compiler/index.html').read_text())
            self.assertTrue(compiler.panels['summary-panel'])
            for route in ['runtime','scaling','memory','lifecycle']:
                measurements = PageParser();measurements.feed((output/f'metrics/{route}/index.html').read_text())
                self.assertTrue(measurements.panels['suite-panel'],'standalone resident measurements must stay accessible')
            deflate = PageParser();deflate.feed((output/'metrics/deflate/index.html').read_text())
            self.assertTrue(deflate.panels['deflate-m3'])
            task = PageParser();task.feed((output/'metrics/tasks/knucleotide/index.html').read_text())
            self.assertTrue(task.panels['suite-panel'])
    def test_missing_template_and_invalid_task_route(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(build_metrics_pages(directory),[])
            (Path(directory)/'campaigns.html').write_text('template')
            with self.assertRaises(ValueError):
                build_metrics_pages(directory,{'cases':[{'id':'../elsewhere','title':'Invalid'}]})

if __name__ == '__main__':
    unittest.main()
