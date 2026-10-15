# Rebol bounded intake after the linker correction

`rebol_bounded_linker.py` consumes the actual successful primitive run through
`rebol_primitive_fixtures_linker.py`. It retains the original fixed19 controller
and combined intake identities, separately records the linker entrypoint, and
carries the failed diagnostic compilation as an additional prerequisite.

The three extension jobs, failed diagnostic job and successful primitive job
remain separate. Their artifacts and leases pass through to later consumers.
The supplemental Apple header remains a diagnostic input. The frozen bounded
schedule, output contracts, observer and finalizer remain unchanged.

The earlier combined-intake source review is retained as a preparatory version;
no bounded native process was launched through that entrypoint. This successor
requires actual independent primitive approval before preparation or execution.
