# Single-process complete-map continuation

This additive controller preserves the [closed three-process attempt](../failed-stage-review-v1.json):
the N4 tree and N27 Pi observation contracts passed; the subsequent global map
dump exceeded its 512 MiB RSS limit. Neither successful observation is repeated,
and the failed process and interrupted dump retain their original status.

`tools/qualification/rebol_work_map.py` loads the frozen final work adapter and
holds its 15 inherited leases plus the closed work3 job lease. It binds the
independent failed-stage review, exact prior inputs, full artifact inventory and
durable command identity. The two accepted captures remain separate retained
evidence; they are never represented as new attempts.

The original constructor first reconstructs all three original slots. The new
plan then selects only the map slot and substitutes the independently reviewed
[complete-map diagnostic and consumer](../../../complete-maps-v1/README.md).
The native process loads the same main and existing bounded input; only the
post-main global dump is removed. Normal exit zero and empty stderr are now
required. The 180-second timeout, 512 MiB RSS ceiling, stream/sidecar limits,
owned observer and complete-output checks are unchanged. No compiler, control,
tree or Pi process is launched by this continuation.

Plan, results and terminal schemas explicitly identify a single map process.
The results retain two earlier observation references and one new capture at
most. Any unexpected failure stops without retry. Finalization validates exact
capture membership, prior evidence, serialized report and named leases. All
producer admission flags stay false; final map capacity, backing addresses,
hash-bucket capacity and growth trajectory are unobserved.

The entrypoint accepts `--adapter-sha256 SHA` followed by the frozen `prepare`
or `run` interface. Place the new plan inside this packet; the frozen CLI enforces
the enclosing original work packet for plan files. Fresh outputs are restricted
to a child directory of this packet. Preparation requires the existing primitive/final8 source references and the
new single-map controller source review. Eight focused pure tests cover the
actual failed-review shape, mixed JSON/Markdown source references, source identity, one-slot policy, lease lifetime,
one-process result accounting and failure preservation. All eight passed in
the [final focused run](validation-v2/result.json); the earlier failed fixture
run is retained separately. This packet contains no new native result.
