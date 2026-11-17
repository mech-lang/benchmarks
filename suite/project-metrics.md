# Project metrics

[Project metrics](https://mech-lang.org/metrics/project/) complements the
[benchmark history](https://mech-lang.org/metrics/). The initial snapshots cover
the benchmark candidate `9087b1f0`, comparison revision `fc2b7310`, and default
branch `0bc31018`. These source tracks remain separate. A first observation
does not establish a historical trend.

## Collect another snapshot

```sh
python3 tools/project_metrics.py --mech /path/to/mech --revision EXACT_COMMIT --track compiler-candidate --label 'Benchmarked compiler' --github --output results/project/NEW_UNIQUE_ID
python3 tools/build_site.py
python3 tools/serve.py --port 8766
```

Open <http://127.0.0.1:8766/metrics/project/>. Reuse a track only for revisions
belonging to that same comparison series. The source inventory reads Git blobs,
so working edits and untracked files never enter the count. No compiler files
are changed, no build runs, and no tests are executed by this collector.

`--github` records current repository statistics and workflow observations
associated with the exact commit. It uses the authenticated `gh` session when
available; credentials are never included in saved evidence. Without that flag,
the inventory works offline and GitHub observations remain unavailable.

## Definitions

- Source files use the versioned extension/path policy in each snapshot. Physical
  lines include comments and blanks; nonempty lines are also retained. Vendor,
  dependency and named build-output directories are excluded. Checked-in source
  outside those directories remains counted, including generated source.
- Rust test files follow test-directory and filename conventions. Mech test and
  fixture files are counted separately. Inline/generated test cases are not
  enumerated. These are static inventories, not executed test counts or coverage.
- Cargo packages are first-party package manifests outside fixture folders.
  Unique registry/Git dependency declarations include optional, dev, build and
  target-specific groups. Root Cargo.lock resolutions are a different count;
  neither describes the enabled graph for a particular feature profile.
- CI rows are workflows associated with the revision, limited to the latest 20
  observations. Jobs for the latest completed workflow are retained, with
  pagination and an explicit completeness flag. Job wall times include setup
  and validation. Reusable workflows can validate another requested ref; no
  executed-test count, line coverage or cold compiler-build claim is inferred.
- Stars, forks and open issues plus PRs are observed when collecting, independently
  of the source revision's commit date. They are dated snapshots, not live counters.

Each directory retains `snapshot.json`, the GitHub API evidence in
`github.json.gz`, and SHA-256 pins in `evidence.json`. The builder verifies those
pins and recomputes summaries before exporting. Every source file has a Git blob
identity and SHA-256. Full inventories and API evidence are downloadable.

## Publish and verify

Copy the complete generated `site/public/` tree into the existing GitLab website
repository's `public/benchmarks/`, preserving separately hosted media. Copy
`campaigns.html` to `public/metrics/index.html` and `project.html` to
`public/metrics/project/index.html`. Push the reviewed website change to `main`
to use its existing Pages job. `tools/verify_pages.py` verifies all generated
files and both public entry points against the exact publication receipt.

The collector is repeatable and records observations when invoked. It does not
install a background schedule or publish automatically.
