# Trimmed N-body with code generation disabled

The unchanged safe-trim executable completed the bounded 1,000-step N-body case
with the exact reference output and exit status zero. Its SHA-256 remained
`86260f83a90db739e82729ce869d21bb8aa747282c9bb8da0ad41a3210770187`.

This observation sets `JULIA_LOAD_CODEGEN_LIB=0` before process startup.
Julia 1.13.1's [loader](https://github.com/JuliaLang/julia/blob/v1.13.1/cli/loader_lib.c)
uses this control in its library constructor to skip the optional codegen
library. The captured dyld image list contains no `libjulia-codegen` image.
The earlier default-loader observation remains separately preserved.

This result does not establish AOT qualification: Julia's
[codegen stubs](https://github.com/JuliaLang/julia/blob/v1.13.1/src/codegen-stubs.c)
retain an interpreter fallback. Native coverage and calibrated observation of
interpreter entry paths remain required. The report admits zero timing samples.

```sh
python3 tools/qualification/julia_pilot.py --disable-codegen-library \
  --output /absolute/path/to/new-observation
```
