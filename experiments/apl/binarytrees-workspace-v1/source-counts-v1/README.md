# APL binary-trees source counts

The measured source bundle contains **41 canonical units and 41 physical code
lines**: the unchanged tree program contributes 40 and the workspace-scale
assignment contributes one. The setup executes inside the measured process and
is included in the source count. Formatted source has not been qualified.

The complete tree source contains three function headers, three written function
closers and 34 statement rows. Labels belong to their following statements;
function-local names are part of the header declaration. Its comment and blank
row are excluded. Nested array expressions and function calls are contents of
their statement, without additional independent source owners. The setup has one
indexed assignment. Neither file packs independent statements on a line.

The compact and optimized labels use one identical tree source and command.
They do not represent separate authored implementations or additional native
observations. Each label receives the same complete 41-unit bundle count.

[The source-owner review](source-owner-review.json) records every written owner
and excluded row, exact source identities and the independently reviewed count.
[The qualified two-file count](qualified-source-counts-v1.json) admits 41 canonical
units and 41 physical code lines. The checker reuses the pinned APL
owner reader in a private module with these two exact source identities; it does
not change the original nine-source reader or admit unknown sources.

The separate [bounded work review](../whole-subject-v1/actual-bounded-work-review-v1.json)
binds the same tree and setup to the completed N=4 and N=10 captures. This packet
does not replay native execution or qualify full-size work, timings or chart
admission. Those gates remain separate from canonical source-count review.

The 5 focused pure test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). The test command from the
repository root is:

```sh
python3 -I -S -B tools/qualification/test_apl_workspace_source_units.py
```
