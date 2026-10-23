# Rejected histogram-helper approach

The proposed `map/hash-histogram` operation was discarded before source or
benchmark admission. Although it would have counted every key through a
library table, it moved the source-level counting procedure into a new runtime
primitive. That does not meet the purpose of finding and filling general Mech
compiler/library gaps with the counting algorithm expressed in Mech.

No implementation from this attempt was committed to the compiler. Its tracked
changes and untracked helper were removed, returning the checkout to the tested
batched compiler revision before ordinary map work began. The first build
failed compilation on a tuple type mismatch. The second was explicitly stopped
when the approach was rejected; its owned process and descendants were reaped
and closed. Neither is a passing test result or timing sample. The retained
receipts document the terminal attempts; the replacement work is in
`general-map-counting-v1`.
