"""Reuse the retained host-phase diagnostic on the compact metadata revision."""
import importlib.util
import json
from pathlib import Path

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
driver = HERE / 'host-startup-audit-v1.py'
spec = importlib.util.spec_from_file_location('retained_host_startup_driver', driver)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
plan = module.read(STUDY / 'plan.json')
module.HEAD = plan['source_commit']
module.OUT = HERE / 'host-startup-audit-v2'
module.PROJECT = HERE / '.build/host-startup-audit-v2.project'
module.ORIGINAL = HERE / '.build' / (plan['binary'] + '.project')
module.PACKAGE = 'owner-counting-host-metadata-trim'
module.main()
path = module.OUT / 'results.json'
result = module.read(path)
result['wrapper_sha256'] = module.process.sha(Path(__file__))
result['wrapper_configuration'] = dict(source_commit=module.HEAD, project=str(module.PROJECT),
    original=str(module.ORIGINAL), package=module.PACKAGE)
module.process.save(path, result)
