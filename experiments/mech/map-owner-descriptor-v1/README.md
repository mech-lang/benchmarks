# Retained-map layout association in standalone descriptors

Compiler revision `2efe102fad8541261044e65431b68dc94e44814a` carries the complete same-plan retained-map candidate and word layout in build-owned descriptors. The layout includes region/revision/tail associations, native state slots and actions, constants, entry/exit site inventories and frame width. Programs with no owner candidates retain `null` instead of a second copy of their ordinary scalar layout.

The Object identity hashes the complete ordered proof encoding directly into its digest without a second serialized buffer. Typed IR advances from 28 to 29 to distinguish the new association. Work policy42 and ABI15 remain unchanged. Existing identity checks reject preceding IR28 objects.

Proof restoration follows the existing private wire reader and unsafe checked-build confinement contract. The proof types expose no public safe deserializer. Missing and extra descriptor proof fields are rejected. A matching hash or decoded layout does not authenticate supplied code, establish a current visit or grant map mutation authority.

Validation passes 199 native checks and eleven map integration checks: 210 distinct passing checks, with three pre-existing native exclusions. Two new native checks exercise original and bytecode-decoded programs. Layouts preserve every field through descriptor encoding/restoration; fifteen metadata changes per artifact alter the Object identity, including omitted/duplicated candidates, changed frame/state words, tail fields and extra site/slot/action inventories. Existing descriptor inventory checks verify that ordinary programs retain no map-owner layout.

`native-regressions-v1` retains a closed compile failure from an omitted identity argument in a prefix test. `native-regressions-v2` retains a closed compile failure from a missing serializer borrow. Both are fixed. `native-regressions-v3` passes all 199 native checks; `map-contracts-v1` passes all eleven map integration checks. Subjects execute serially under the shared benchmark mutex with bounded process control and complete cleanup receipts.

This change establishes metadata association, not retained-map execution. The normal generated program still uses canonical maps. Complete live caller/frame geometry, actual current-visit routing, entry/call/exit storage handoff, the general source hash contract, full-input qualification and fresh timings remain unfinished. No benchmark samples, new runtime speed claim or canonical dataset change is admitted.
