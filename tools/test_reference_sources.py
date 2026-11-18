import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from reference_sources import source_link

class ReferenceSourcesTest(unittest.TestCase):
    def record(self):
        source='fn main() { println!("result"); }\n'
        return {'case_id':'scalar','backend':'rust','source':source,'source_sha256':hashlib.sha256(source.encode()).hexdigest()}
    def test_generated_reference_links_to_exact_retained_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);record=self.record()
            url=source_link(record,{},root/'public',root)
            self.assertEqual((root/'public/reference-sources'/url.rsplit('/',1)[1]).read_text(),record['source'])
            self.assertTrue(url.endswith('.rs.txt'))
            record['source']='changed'
            with self.assertRaises(ValueError):source_link(record,{},root/'public',root)
    def test_original_citation_is_bound_to_measured_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);record=self.record()
            folder=root/'programs/rust/scalar/published';folder.mkdir(parents=True)
            metadata={'authorship':{'source_sha256':[record['source_sha256']],'sources':[{'url':'https://example.org/original','relationship':'implementation'}]}}
            (folder/'program.json').write_text(json.dumps(metadata))
            self.assertEqual(source_link(record,{},root/'public',root),'https://example.org/original')
            record['case_id']='related-post-gen';record['revision']='abc'
            campaign={'origin':{'upstream':'https://github.com/zupat/related_post_gen','upstream_revision':'abc'}}
            self.assertEqual(source_link(record,campaign,root/'public',root),'https://github.com/zupat/related_post_gen/tree/abc/rust_con')

if __name__=='__main__':unittest.main()
