# Remaining preparation and counting work

The newly qualified worker-credit/fragment-fact combination is the next development baseline; the finite-credit checkpoint remains the control for its interaction study. The combination records 0.6046 s / 1.092× Rust and 0.6083 s / 1.082× Rust in its two sessions. The independent register-cache, cold-origin and partial join/map-fusion candidates remain unpromoted.

The measured worker-start delay identifies preparation as the next priority. The scalar scanner is nested inside capture; joining and normalization occur after EOF. These diagnostic spans must not be added as independent contributions to primary elapsed time.

The [plan](plan.json) separates four implementation tracks and defines their qualification requirements. The qualified [fragment-fact interaction](../credit-fragment-facts-v1/) tests one retained input-side factor on the credit baseline. The next scanner experiment changes the accounting algorithm while preserving frame storage and the existing reconciliation callback. Larger fusion must remove real buffer passes and intermediate ownership construction. Counting work targets both long tasks and preserves the prescribed complete maps, default growth and all original updates.

Every candidate requires correctness checks, actual emitted-code inspection, fresh phase/per-width diagnostics and balanced complete-process measurement. Native subjects remain serial under the existing common lock; internal parallel work remains capped at seven workers. The canonical benchmark dataset is unchanged.
