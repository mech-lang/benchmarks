# Paired Rust task controls

Source to linked executable, with a fresh source/project per fork and warmed support dependencies. Mech includes its compiler worker, dependency resolution, checked runtime support build and link; Rust includes rustc and final link with prebuilt standard library. Both produce a complete scalar CLI checked against all scheduled inputs. This compares deployment paths, including their different support machinery.

| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |
| --- | ---: | ---: | ---: |
| native-build / native | 7.15742992 | 0.160854208 | 44.496 |
