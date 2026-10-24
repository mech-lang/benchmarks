"""Regression coverage for actual macOS startup/queue trace phase headers."""
from analyze_profile import stack_threads
from profile_hotspots import leaves, category

trace = """Call graph:
    4 Thread_1: Main Thread
    + 4 _dyld_start
    2 Thread_1 DispatchQueue_1: com.apple.main-thread
    + 2 start
    3 Thread_2
    + 3 mech_canonical_program_entry_v1
    1 Thread_2 different phase
    + 1 leaf
Total number in stack"""
threads = stack_threads(trace, {'generated_program_entry': ['mech_canonical_program_entry_v1']})
assert len(threads) == 2
assert threads[0]['thread'] == 'Thread_1' and threads[0]['samples'] == 6 and threads[0]['main_thread']
assert threads[1]['samples'] == 4 and threads[1]['observed_native_worker']
assert threads[1]['inclusive_samples']['generated_program_entry'] == 3
assert sum(row[2] for row in leaves(trace)) == 10
assert sum(row['samples'] for row in threads) == 10
print('Thread-phase parsing: 10 observations preserved, two threads, one main thread.')

for helper in ['_ZN11mech_engine8resident6budget7workers11lock_escrow17habcE',
               'mech_engine::resident::budget::workers::lock_escrow']:
    assert category('core::hint::spin_loop', (helper, 'core::hint::spin_loop'), 'mech') == 'work_budget_active'
    assert category('__ulock_wait', (helper, '__ulock_wait'), 'mech') == 'work_budget_wait'
print('Escrow helper accounting classification covers both spins and blocked fallback.')
