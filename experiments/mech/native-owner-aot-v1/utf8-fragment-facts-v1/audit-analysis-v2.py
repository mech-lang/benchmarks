"""Correct Apple otool SIMD spelling using the retained exact assembly only."""
import fcntl
from pathlib import Path
import re
import sys

STUDY = Path(__file__).resolve().parent
HERE = STUDY.parent
sys.path.insert(0, str(HERE / 'preparation-interactions-v1'))
from measure import PLAN, process, read, source_state

before = source_state()
plan = read(STUDY / 'plan.json')
assert before['commit'] == plan['source_commit'] and not before['status']
with Path(PLAN['common_mutex']).open('a+') as lock:
    assert Path(PLAN['common_mutex']).stat().st_ino == 83858837
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    original = read(STUDY / 'code-audit/results.json')
    path = STUDY / 'code-audit/byte-facts.s'
    assert process.sha(path) == original['retained_sha256']
    instructions = [m[2] for line in path.read_text().splitlines()
                    if (m := re.match(r'^([0-9a-fA-F]{16})\s+(.+)$', line))]
    assert len(instructions) == original['instructions'] == 121
    vector = [line for line in instructions if re.search(r'\bv[0-9]+\b', line)]
    wide_loads = [line for line in instructions if re.match(r'(?:ldp|ldr)\s+q[0-9]+', line)]
    assert vector and wide_loads and any(line.startswith('udot.4s') for line in vector)
    assert source_state() == before
    result = dict(status='retained-assembly-vector-spelling-corrected', source=before,
        source_after=before, driver_sha256=process.sha(Path(__file__)),
        retained_sha256=process.sha(path), original_audit_sha256=process.sha(STUDY / 'code-audit/results.json'),
        instructions=len(instructions), vector_instructions=vector, vector_load_instructions=wide_loads,
        native_processes_launched=0, benchmark_samples=0,
        correction='The initial classifier searched register lane suffixes such as v3.16b. Apple otool prints lanes on mnemonics, such as orr.16b v3. This analysis reads the same retained 121-instruction function, preserving the original report. No executable, raw assembly, profile or timing is changed or repeated.')
    process.save(STUDY / 'code-audit/analysis-v2.json', result)
    print('Retained assembly:', len(vector), 'vector-register instructions;', len(wide_loads), 'wide loads; no native execution', flush=True)
