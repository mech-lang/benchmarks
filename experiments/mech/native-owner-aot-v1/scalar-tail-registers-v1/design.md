# Entry-local scalar Tail fuel

The current diagnostic identifies 73 ms of main-thread CPU time in the original source scanner. Its closed pure scalar body has three private loan words: ready, remaining compute and remaining comparison. Only the generated Tail emitter writes them, and the host receives remaining credit through explicit leave arguments.

This candidate represents those words with Cranelift frontend variables within a single checked invocation. Each invocation initializes them from the original validated local storage. The same original homes are synchronized at preparation, leave, pause, checkpoint clearing and error boundaries. Source values, borrowed-string words, map fuel and map frames are outside this change. No credit is created, enlarged or renewed; every original header still checks and spends the same two prices. Declined/exhausted loans use the original per-visit callback path.

The differential test compiles actual bytecode both with and without register substitution. It compares carriers, original work, error origins and outputs across repeated empty/growing prefixes, EOF, Unicode and CRLF input, missing markers, empty rows, and compute/comparison exhaustion. Every successful pause must clear its original checkpoint homes and all owned memory must retire. Existing native capture, late-error, resource and map suites remain required.

The change is independent of the unpromoted join/map fusion experiment. IR83 identifies the changed guest emitter; ABI29 and policy68 are unchanged. The source, bytecode, source resource requirements, full seven-map work and seven-worker cap remain pinned. Instrumented probes are excluded from primary timings.
