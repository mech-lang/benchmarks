# Timing-boundary audit

The audit traces the 857 selected program profiles to their saved observations
and timing producers. Of these, 814 are non-Mech profiles and 29 are Mech AOT or
JIT profiles; their retained producers time process launch through exit. The
remaining fourteen selected Mech interpreted profiles used internal execution
time, excluding preparation, and require replacement by fresh whole-process
measurements.

- `aot-jit-review.json` covers all 29 selected Mech AOT/JIT profiles and 103 samples.
- `non-mech-review.json` covers all 814 selected non-Mech profiles and 88 reports.

The records distinguish source-inspected historical timing boundaries from
execution-time cryptographic provenance. Where historical runner hashes,
expanded arguments or ambient environments were not retained, those limitations
remain explicit. The audit does not recreate missing historical evidence.

The fresh interpreted cohort is documented in
[`../interpreted-whole-process-v1/`](../interpreted-whole-process-v1/).
