"""Full-input observer policy using the immutable Kotlin v2 lifecycle.

Only the observer RSS ceiling changes: 10 GiB matches the retained full-study
sampler policy and accommodates the unchanged 8 GiB JVM heap plus native memory.
Load a separate module so prerequisite receipts still use the original 2 GiB
validator. No native work, preflight, or runtime hashing occurs at import.
"""
import hashlib
import importlib.util
from pathlib import Path

SOURCE_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
OBSERVED_RSS_LIMIT = 10*1024*1024*1024


def load():
    path = Path(__file__).with_name('kotlin_bounded_v2.py')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise AssertionError('Immutable Kotlin v2 supervisor changed')
    spec = importlib.util.spec_from_file_location('kotlin_single_entry_lifecycle',path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    if (module.RSS_LIMIT != 2*1024*1024*1024 or module.TIMEOUT != 30 or
            module.CLEANUP_TIMEOUT != 5 or module.FILE_LIMIT != 8*1024*1024 or
            module.FLAGS != ['-XX:ActiveProcessorCount=8','-Xms64m','-Xmx8g','-XX:+UseG1GC']):
        raise AssertionError('Original supervisor policy differs')
    module.RSS_LIMIT = OBSERVED_RSS_LIMIT
    return module


supervisor = load()
