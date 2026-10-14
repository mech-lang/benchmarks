# Deterministic retained publication

`tools/qualification/import_retained_publication_target_v2.py` retains the
separate evidence and publication checkout procedure from
[TARGET-CHECKOUT.md](TARGET-CHECKOUT.md). It uses the same CLI flags, original
evidence consumers, leases, copied-link checks, preview digests and guarded
transaction. Pass the v2 file's SHA-256 as `--adapter-sha256` and retain an exact
copy of that file in the publication checkout.

The original retained transform inserts new `archive_paths` keys by iterating
a Python set. Independent preview and apply processes can therefore serialize
different object-key orders. V2 preserves the existing mapping's key order and
appends only new keys in sorted order after the unchanged transform. Mapping
values, benchmark records, metadata and scientific policy are unchanged.
Missing or changed existing mappings are rejected.

Create a fresh preview and a fresh apply directory for this revision. Use all
six digests from the new preview for application. A previous preview remains
an immutable record and does not authorize different prepared bytes. Previously
successful v1 receipts and normalization-history entries remain unchanged.

The focused test suite replays the existing synthetic transaction failures and
compares the actual retained R transform across three independent Python hash
seeds. These checks execute no benchmark, compiler, runtime closure replay or
publication against a current catalog. Actual preview and application require
the original evidence leases and complete physical verification.
