# Kotlin source reader initialization revision

This revision supplies the empty compiler-extension storage required by the
retained Kotlin 2.4.21 PSI environment. It has not been compiled or executed.
The original reader, controller, plan and failed run in `source-counts-v1`
remain unchanged.

The original diagnostic Java compilation passed. Its parser JVM exited 1
before source inspection because `createForProduction` attempted to read an
unregistered extensions storage. The process was reaped without signals or
cleanup errors. This is reader initialization evidence, with no application
source failure established.

Pure class-file inspection of the exact retained compiler found:

- `FrontendConfigurationKeysKt.setExtensionsStorage` is public and static. It
  stores the supplied value in `FrontendConfigurationKeys.EXTENSIONS_STORAGE`.
- `CompilerPluginRegistrar.ExtensionStorage` has a public empty constructor.
  It creates an empty extension map and disposable list; querying an absent
  extension returns an empty list.
- `KotlinCoreEnvironment.configureProjectEnvironment` calls
  `getCompilerExtensions`, which throws the observed exception when that
  configuration entry is absent.

[initialization-review.json](initialization-review.json) binds the class-entry
hashes, public descriptors and observed failure receipts. The full compiler
JAR hash is copied from the prepared original plan, not recomputed during this
source-only diagnosis. No native `javap` or compiler command was used.

`SourceReader.java` adds two imports, creates a `CompilerConfiguration`, sets
its empty extension storage and passes it to `createForProduction`. Parsing,
UTF-16 ranges, source retention, output schemas and the application-class
canary are unchanged. No plugin is installed and no source analysis or
application compilation is added. `fixtures.json` is byte-identical to v1.

`kotlin_loc_v2.py` is the original controller with only its packet directory
changed. It retains the reviewed bounded v2 supervisor, exact runtime/compiler
closure, forty authored inputs, fourteen fixtures, one diagnostic compilation
and one parser JVM. Its 30-second deadline, five-second cleanup, 2 GiB RSS and
8 MiB file limits are unchanged. The fourteen pure PSI/artifact tests pass
against the new controller; native initialization remains unverified.

Prepare under the common timing mutex with the retained Python:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_loc_v2.py prepare \
  --plan experiments/kotlin/source-counts-v2/plan-v1.json \
  --output experiments/kotlin/source-counts-v2/run-v1
```

After reviewing the actual plan, use the same Python invocation with
`tools/qualification/kotlin_loc_v2.py run --plan PATH --plan-sha256 SHA256`.
Existing outputs are rejected; no failed attempt is automatically retried.
Canonical and formatted LOC remain null pending native evidence and owner
review. This stage grants no source-work, timing or chart qualification.
