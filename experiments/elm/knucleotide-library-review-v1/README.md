# Elm nucleotide map and input review

The retained core-Dict source has a full median of301.240s (586.27× the
retained Mech AOT median of0.513828s). Its observations remain historical data.
Source inspection finds a required-work conflict: core Dict uses a red-black
tree, while this workload prescribes hash tables. A guarded eligibility decision
and independent evidence join remain pending; no catalog entry has changed.

[The review](source-review-v1.json) binds the application, dependency manifest,
workload description and official exact-version library sources. HashDict stores
original keys and compares them separately from the hash. A narrow hash alone
does not prove that distinct36-bit keys are merged.

[The uncompiled candidate](proposal.json) uses the existing HashDict library,
standard integer equality and a standard string-hash projection. All seven maps
still count every overlapping occurrence. Decimal-key hashing has an allocation
cost; it is a correctness/idiom alternative, not a measured speed winner. The
first exact THREE record and comment/line boundaries are handled explicitly in
Elm. New code and inherited authored helpers require complete ownership counts.

Compilation, native work/output probes, independent count approval and isolated
measurements remain pending. Official library files are retained as cited review
evidence; historical compiler-input identity needs its own manifest join.
