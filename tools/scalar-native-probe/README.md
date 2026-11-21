# Primary scalar execution comparison

The scalar entry is a primary maintained native capability. This probe compares
it with canonical Program's managed Value interface before any replacement is
accepted. It measures original and decoded versions of 1-, 32- and 256-operation
U64 programs in optimized builds. Five alternating paired rounds measure 2,000
calls per batch after 100 warmup calls. Both paths check the expected value on
every invocation. The counted allocator covers the invocation's setup, execution,
publication and release; it does not count parsing, lowering or JIT compilation.

```sh
python3 tools/scalar-native-probe/run.py \
  --mech /absolute/clean-mech-checkout \
  --revision FULL_CANDIDATE_COMMIT \
  --evidence /absolute/fresh-evidence
```

Commit the probe first and use a clean disposable candidate checkout. The tool
temporarily adds one standalone integration test, runs the exact nonempty
ignored selector and removes only that test file afterward. Production files
are unchanged. The receipt pins candidate and runner commits, probe and lockfile
hashes, compiler, command, platform, every sample and allocation count. The raw
execution log is retained on failure as well as success. Dependencies must be
prefetched for the locked offline build.

The two interfaces have different transport contracts. A faster general native
arithmetic loop does not by itself establish equivalent short-call overhead.
These paired batch means are diagnostic evidence; the tool never automatically
qualifies a replacement. For acceptance, run on an otherwise idle host, retain
the existing semantic/ownership/resource tests and compare a proposed shared
scalar specialization against the maintained scalar entry. Preserve a runtime
path that meets the established latency and allocation behavior.
