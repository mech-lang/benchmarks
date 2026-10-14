# Kotlin native source inspection

The retained Kotlin 2.4.21 compiler supplies this stage's parser. A new Java
diagnostic uses `KotlinCoreEnvironment`, `KtPsiFactory`, and PSI node ranges to
inspect the forty physical authored inputs from twenty compiled forms. Each
form includes its main and the complete `Support.kt`. The reader performs
syntax parsing without compiling, evaluating, or loading application classes.

Each result preserves original source bytes, the exact PSI text, every node's
parent/children and UTF-16 range, leaf text, comments, whitespace and native
syntax errors. All leaf ranges must cover the PSI text exactly once. Any
observed CRLF/CR normalization is explicit and limited to newline replacement;
the original source copy remains unchanged. Fourteen fixtures cover packed
statements, callback bodies, control flow, fields and destructuring, literals,
nested comments, interpolation, data wrapping, Unicode, and rejected syntax.

The preparation controller pins the closed helper/compiler evidence, source
inputs, retained JVM, compiler manifest classpath and reader source. One
diagnostic `javac` command builds only `SourceReader.java`; one JVM reads the
forty inputs and fourteen fixtures. Both run sequentially under the unchanged
common timing mutex and the reviewed bounded supervisor. The reader classpath
contains the diagnostic and the retained compiler libraries, with no benchmark
class directories.

Native parser results are evidence for the subsequent canonical owner review.
They do not themselves define the source-unit rule. Packed header/body/close
boundaries, independent assignments, callback bodies, constructor properties,
and wrapped literal/data lines must follow the suite's existing counting rule.
Canonical and formatted LOC remain null until the required review succeeds.
No Kotlin formatter is substituted or inferred from the PSI tree.

The diagnostic uses the original retained JVM options plus explicit headless
mode. Each native command has a 30-second deadline and five seconds for
cleanup, with 2 GiB observed process-group RSS and an 8 MiB per-file limit.
The compiler manifest and all five of its declared library dependencies are
pinned. Annotation processing is disabled for the Java diagnostic build.

From the repository root, prepare a fresh plan while the timing mutex is free:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_loc.py prepare \
  --plan experiments/kotlin/source-counts-v1/plan-v1.json \
  --output experiments/kotlin/source-counts-v1/run-v1
```

After reviewing the emitted plan and its SHA-256, execute the exact plan with
`kotlin_loc.py run --plan PATH --plan-sha256 SHA256` using the same Python
invocation. Existing output directories are rejected; failed observations
remain available and are not automatically retried.

The source reader has not yet been compiled or executed. Fourteen pure Python
fixtures currently check UTF-16 offsets, newline preservation, empty nodes,
tree structure, native-error inventories, artifact retention and process
receipts. They do not replace the actual native parser observations.
