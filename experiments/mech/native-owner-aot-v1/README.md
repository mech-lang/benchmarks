# Source-map standalone timing diagnostic

The newest available source-written standalone executable, compiler revision `f6fb76f5f284b8731368a5d30028cc1663c2bb03`, was measured on a deterministic 1,000-base FASTA input. Three fresh secured processes took 5.7253, 5.4542 and 5.4684 seconds: median 5.4684 seconds (1.00× this Mech AOT diagnostic). Median peak RSS was 12,795,904 bytes. All three complete outputs match an independent reference.

This is a bounded diagnostic of the preserved canonical-map executable. It is not the full 125-million-base workload, and does not measure the new retained-map compiler revision `9e2d1a29cdeee612dcae850c32eb326755e14d8a`. The new CLI build was interrupted before artifact publication; its process receipt retains complete owned-group cleanup. No candidate speedup or canonical benchmark dataset change is claimed.

The input, launch policy, executable hash, compiler revision, timing/resource receipts and complete outputs are retained under `available-timing-v1`. Timed processes run serially under the existing shared mutex, include startup and shutdown, and exclude build and reference checking.
