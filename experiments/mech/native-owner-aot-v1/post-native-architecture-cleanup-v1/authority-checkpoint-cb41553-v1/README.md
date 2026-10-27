# Private identity encoding checkpoint

The six library profiles and four runtime dependency closures pass at
cb41553b6a8b9a6b0432b4015ca22b9368ddbab6. The new shared owner preserves
the private byte encoding used by scalar, Match, Iteration and Program
identities; this is unrelated to the Mech source grammar.

PR939 at a68fb2e60d7afbc59bc146f8878b17181e275645 preserves the complete
Rust cleanup patch byte for byte, directly on published935. The only
checkpoint-source differences are the two base test-repair files and the
cleanup handoff documentation. These profile receipts remain qualified
only at their recorded checkpoint; new exact-head correctness, artifact,
process and timing evidence remains required.
