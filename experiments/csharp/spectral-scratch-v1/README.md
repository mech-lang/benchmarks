# C# spectral-norm scratch reuse

This uncompiled candidate allocates and pins one temporary vector in `Main`
instead of allocating/pinning it in each of twenty A-transpose-A calls. The
coefficient, dot product, forward/transpose multiplication bodies, lane reduction
and all forty dense products remain unchanged in the source. This is a lower
allocation hypothesis, not a measured speedup.

The original is [spectral norm C# #5](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/spectralnorm-csharpcore-5.html),
contributed by Jesper Meyer; the retained ARM adaptation is its immediate local
predecessor. Notices and [BSD terms](LICENSE.benchmarksgame) remain, with
Apache-2.0 applying to local changes. Both JIT and NativeAOT need separate native
qualification and full-size measurements under the common mutex. Source counts
and chart admission are unqualified.
