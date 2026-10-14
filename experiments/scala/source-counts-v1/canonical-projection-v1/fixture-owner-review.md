# Native fixture ownership review

These decisions use the actual v2 native node roles and physical tokens. The
original proposed count is compared only after projection. Source text, node IDs
and token assignments for each decision are retained in the linked artifact.
All counts remain candidate fixture evidence rather than application admission.

| Fixture | Derived units | Actual owner decision |
| --- | ---: | --- |
| [packed-method](results-v1/owner-packed-method.json) | 5 | `DefDef` header, two `ValDef` statements, final `InfixOp`, written close; semicolons add zero. |
| [expanded-method](results-v1/owner-expanded-method.json) | 5 | Same five owners after executable layout expansion. |
| [expression-method](results-v1/owner-expression-method.json) | 1 | `DefDef` and its scalar expression form one declaration. |
| [generic-expression-method](results-v1/owner-generic-expression-method.json) | 1 | Type parameter and zero-width synthetic `TypeBoundsTree` remain in the method header; neither adds an authored unit. |
| [tuple-type-alias](results-v1/owner-tuple-type-alias.json) | 1 | One `TypeDef`; tuple type punctuation is structural. |
| [constructor-fields-no-body](results-v1/owner-constructor-fields-no-body.json) | 3 | Class header and two native constructor `ValDef` spans beginning with written `val`. |
| [constructor-plain-formals](results-v1/owner-constructor-plain-formals.json) | 1 | Class header; ordinary constructor parameters are not fields. |
| [constructor-fields-packed-body](results-v1/owner-constructor-fields-packed-body.json) | 5 | Class header, two fields, expression method and written class close. |
| [constructor-fields-expanded-body](results-v1/owner-constructor-fields-expanded-body.json) | 5 | Same owners; wrapping the constructor signature adds no units. |
| [explicit-class-fields](results-v1/owner-explicit-class-fields.json) | 4 | Class header, two native body bindings and written close. |
| [object-main](results-v1/owner-object-main.json) | 5 | Object header, method header, call, method close and object close. |
| [tuple-pattern-binding](results-v1/owner-tuple-pattern-binding.json) | 1 | One native `PatDef`; its two pattern identifiers do not become two bindings. |
| [expression-lambda](results-v1/owner-expression-lambda.json) | 1 | Native expression `Function` stays inside its binding. |
| [braced-callback-packed](results-v1/owner-braced-callback-packed.json) | 5 | Enclosing binding/call/lambda header, binding, call, final expression and written callback close. Native synthetic body `Block` adds no extra header or close. |
| [braced-callback-expanded](results-v1/owner-braced-callback-expanded.json) | 5 | Same callback and statement owners after executable expansion. |
| [braced-one-expression-callback](results-v1/owner-braced-one-expression-callback.json) | 3 | Callback header, final expression and written close survive even with one expression. |
| [parenthesized-expression-callback](results-v1/owner-parenthesized-expression-callback.json) | 1 | Native expression `Function` in an ordinary argument list; no written executable close. |
| [while-and-compound-updates](results-v1/owner-while-and-compound-updates.json) | 6 | Method header, while header, two actual update expressions, loop close and method close. |
| [unbraced-if-else](results-v1/owner-unbraced-if-else.json) | 6 | Method header, if header and call, else header and call, method close. No branch close is invented. |
| [scalar-conditional-value](results-v1/owner-scalar-conditional-value.json) | 1 | Native `If` has scalar branches and remains a composed binding value. |
| [try-finally](results-v1/owner-try-finally.json) | 8 | Method, try and finally headers; two body calls; three actual closes. Empty native handler adds nothing. |
| [updates](results-v1/owner-updates.json) | 5 | Method header, two native infix updates, one native indexed `Assign`, close. |
| [indented-method](results-v1/owner-indented-method.json) | 3 | Method header, binding and final expression. Native layout exit has no written close. |
| [braced-layout-counterpart](results-v1/owner-braced-layout-counterpart.json) | 4 | Corresponding three owners plus its actual written close. |
| [written-end-marker](results-v1/owner-written-end-marker.json) | null | Native `DefDef` end-name span proves a written end marker; its canonical rule remains gated. |
| [wrapped-literal-data](results-v1/owner-wrapped-literal-data.json) | 4 | Native literal-only `Array` application preserves four occupied physical data rows. |
| [packed-literal-data](results-v1/owner-packed-literal-data.json) | 1 | The same data on one written row contributes one unit under the physical-data policy. |
| [grouped-import](results-v1/owner-grouped-import.json) | 1 | One native `Import`; selector braces are structural, not executable closes. |
| [nested-comments-and-literal](results-v1/owner-nested-comments-and-literal.json) | 1 | One binding; native comment coverage excludes the nested comment while retaining comment-looking literal text. |
| [protected-character-literals](results-v1/owner-protected-character-literals.json) | 4 | Four bindings; quote, slash, brace and escaped newline stay literal tokens. |
| [scalar-interpolation](results-v1/owner-scalar-interpolation.json) | 1 | Native interpolation expression has no independent statements. Its interpolation delimiter is structural. |
| [executable-interpolation](results-v1/owner-executable-interpolation.json) | null | Native interpolation descendant `Block` contains a binding and call; independent work cannot be hidden inside the literal owner. |
| [match-expression](results-v1/owner-match-expression.json) | null | Native `Match`/`CaseDef` ownership requires explicit case/header/body review. |
| [pattern-callback](results-v1/owner-pattern-callback.json) | null | Native partial-function `Match` has an empty selector; ordinary-function accounting is not silently substituted. |
| [anonymous-runnable](results-v1/owner-anonymous-runnable.json) | 5 | Binding/new-template header, actual method header, call and two written closes; synthetic constructor contributes zero. |
| [unicode-crlf](results-v1/owner-unicode-crlf.json) | 2 | Two owners; native UTF-16 positions map to exact UTF-8 bytes across the supplementary character and CRLF. |
| [comment-only](results-v1/owner-comment-only.json) | 0 | Native empty root and no physical code tokens. |
| [never-evaluate](results-v1/owner-never-evaluate.json) | 1 | One binding containing native `Throw`; the retained source is data and is never executed. |
| [meaningful-directive](results-v1/owner-meaningful-directive.json) | null | The meaningful `//>` directive remains a review gate even though the native scanner calls it a comment. |
| [unclosed-method](results-v1/owner-unclosed-method.json) | null | Actual native parse error; no canonical count. |
| [mismatched-array-delimiter](results-v1/owner-mismatched-array-delimiter.json) | null | Actual native parse error; no canonical count. |

The 34 concrete values agree with the original proposed counts. The five review
contracts and two parser-rejection contracts remain null for their actual
native reasons. Fixture rejection expectations are not used to disable or
suppress a counter error. None of these fixture decisions substitutes for a
manual application owner review.
