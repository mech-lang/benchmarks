# Retained native call-cache resource demand

Compiler revision `79a344544c3f023246c7dcee7380f2748029bd9d` adds a read-only demand interface for retained native library-call caches. It combines binding metadata, planning-cache metadata, weak footprint slots and independently admitted String indexes. It does not inspect input/output Values, rebuild a plan, or retain caller payloads.

Fixed binding/planner reservations contain metadata only. Their admitted byte capacities conservatively bound their node populations without walking recursive metadata trees. Separately admitted String indexes may scale with input size, so their existing node witnesses are used directly; large offset buffers are not counted as one node per byte. All sums are checked for overflow.

An empty cache reports zero retained demand. A bound cache requires the original work account and memory account. Each preview charges fixed work on that existing ledger and creates no allowance. It neither authenticates a selected site nor grants execution permission. No stored structure, serialization format or normal execution path changes; native IR30, work policy44 and ABI15 remain current.

All 202 native checks pass, with three pre-existing exclusions. A new original/decoded-source check warms a real selected Unicode String call and verifies that reported bytes equal the retained reservation difference. Repeated previews allocate no backing, retain no snapshot roots and leave metadata unchanged. A zero-work enclosing scope denies preview without renewal; another ledger sharing the same memory account is rejected. Demand remains readable after the caller payload retires, and all claims release when the cache retires.

The subject runs serially under the shared benchmark mutex with bounded process control and a complete cleanup record. There are no quantitative benchmark samples or canonical dataset changes. This completes the call-cache part of future caller geometry. Private builders/native frame state and checked retained-map entry/call/exit routing remain unfinished, followed by full-input qualification and fresh complete-process timings.
