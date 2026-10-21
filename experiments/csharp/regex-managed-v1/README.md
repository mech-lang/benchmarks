# C# ordinary managed regex alternative

This uncompiled serial form uses the standard .NET `Regex.Count` and `Replace`
APIs. Latin1 decoding preserves one character per input byte for the reported
lengths. It executes all nine case-sensitive counts and all five dependent
substitutions. No match-object collection, external PCRE binding or custom
benchmark kernel is authored. Runtime regex parsing/execution remains inside
each fresh process.

It is a distinct library/idiom alternative to the retained local
[PCRE2 C# #2](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/regexredux-csharpcore-2.html)
adaptation by Michael Ganss, derived from Josh Goldfoot with Anthony Lloyd's
ordering changes. The protected managed #5 source is unchanged. Notices and
[BSD terms](LICENSE.benchmarksgame) remain, with Apache-2.0 for local changes.
The current serving model is known only as Codex GPT-6; predecessor model
evidence remains as recorded.

This form emphasizes ordinary source expression, not a claim of highest speed.
Default regex-engine behavior, complete outputs, source counts, both execution
modes and full-size observations still require native qualification. All authored
helpers remain counted; the unmodified general regex engine is a dependency.
