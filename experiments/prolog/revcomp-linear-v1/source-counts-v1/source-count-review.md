# Linear reverse-complement canonical source count

The compiled replacement has **242 canonical source units and 146 physical
source lines**. The [review record](source-count-review.json) binds the exact
source, native reader outputs, projections and compiled artifact bridge.
Formatted LOC remains unavailable. This count applies only to source SHA
`bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322`.

The nine native reader receipts were replayed with their actual controller
parent PID 59675. All commands exited successfully, retained complete stdout
and empty stderr, and closed their owned process groups. The seven fixture
projections and the candidate projection reproduce the saved JSON exactly.
The closed reader artifact inventory also matches its terminal receipt.
The earlier 31-fixture qualification and original reader/counter are unchanged.

The actual builtin metadata identifies `system:string_codes/2` as a defined,
foreign, ordinary builtin in SWI-Prolog 10.0.2 on arm64 Darwin. The adapter adds
only that target. Native fixtures preserve local-definition precedence and
reject another module, another unselected builtin, and goal-valued data.

All 253 candidate owner events were reviewed against their complete written
source fragments. Their source intervals, line positions and UTF-8 byte
boundaries were independently checked. The 22 written predicate identities
match the inspected compiled WAM. Original source bytes and the compiler's
retained input bytes are identical.

| Written source owners | Canonical units |
| --- | ---: |
| Directives | 2 |
| Clause and fact dispatch headers | 52 |
| Ordinary calls | 58 |
| Meta-call headers and written closes | 11 |
| Clause closes | 47 |
| Control and branch headers, control closes | 25 |
| Independent comparisons | 2 |
| Cuts | 26 |
| Unifications | 16 |
| Arithmetic bindings | 3 |
| **Total** | **242** |

The eleven zero-unit events preserve structure without double counting: seven
first condition comparisons and one first condition call merge into their
control headers; the initialization meta-call header merges into its directive;
two forwarded formal goal references add no new written executable body.
The written `main` and `main_with_capacity` arguments to `execute/1` are counted
at their call sites. The formal flow through `execute/1`, `run_checked/1`,
`catch/3` and `call/1` does not hide a dynamically constructed goal. List/state
data and the exception terms remain data; comments and blank lines contribute
no units.

The producer reports and projections retain their original pending-admission
flags. This separate review admits the candidate's canonical count. The
[compiled-work review](../compiled-work-review.md) covers the actual algorithm
and QLF/WAM evidence; full-input measurements and chart admission remain separate.
