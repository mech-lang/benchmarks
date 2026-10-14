# Retained TypeScript compiler and declarations

The [package receipt](retained-packages-v1.json) records four official npm
archives, their published SHA-512 integrity values, local archive hashes and
every extracted file. The installed package identities match their retained
manifests. Extraction ran no installation scripts.

| Package | Version | Retained files |
| --- | --- | ---: |
| TypeScript | 7.0.2 | 416 |
| Apple arm64 compiler | 7.0.2 | 113 |
| Node declarations | 24.19.2 | 75 |
| undici declarations | 7.24.6 | 47 |

Node declarations were selected from the stable 24.x series. Their sole declared
dependency is `undici-types >=7.24.0 <7.24.7`; the selected 7.24.6 satisfies that
range and has no further dependencies. Other optional compiler platforms were
not installed. All archives were checked against the exact registry integrity
values before extraction.

Two serial native [version checks](native-versions-v1/report.json) observed
Node `v24.19.0` and compiler `Version 7.0.2`. Both exited zero with complete
expected stdout, empty stderr and no remaining owned process-group members.
All package and executable pins were checked before and after the commands.
The existing common mutex, 30-second deadline, five-second cleanup deadline and
2 GiB observed process-group RSS limit were used. Go concurrency was capped at
eight with `GOMAXPROCS=8`.

These checks establish the retained executable versions. The complete Node
runtime dependency closure, compiler API/source reader, emitted application
JavaScript, source counts, correctness, required work and timing measurements
remain to be qualified. The original [selection record](selection.json)
preserves its earlier pre-installation state.
