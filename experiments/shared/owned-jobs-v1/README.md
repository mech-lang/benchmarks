# Durable qualification jobs

This shared launcher is an exact source copy of the retained
[Kotlin dispatcher](../../kotlin/dispatch-v1/launch_durable.py).
[Source identity](source-identity.json) records both paths, byte counts and
SHA-256 values. No behavior changed. It provides a common location for future
Scala and TypeScript job ownership without placing their jobs under another
language's experiment.

Each fresh job directory retains the command request, detached worker identity,
command start, raw stdout/stderr and terminal exit. A private lease and persisted
one-byte handoff precede command launch. Existing job names cannot be reused;
the launcher never retries or resumes a command. Termination is forwarded only
to the direct command owned by the worker. The target controller remains
responsible for descendant ownership, cleanup and native evidence.

The launcher does not acquire the common timing mutex. Every target must acquire
and retain that mutex itself. A successful worker exit is an observation of the
command's exit status; it does not qualify source counts, correctness, required
work, timings or publication. Do not launch a target until the preceding native
cohort has closed and its process ownership has been checked.

```text
<retained-python> -I -S -B launch_durable.py --job <fresh-job-name> --cwd <physical-checkout> --command-json <exact-reviewed-JSON-argv>
```

The source copy alone starts no job. Launch records remain next to this file in
`owned-jobs/<job-name>/`; benchmark and qualification outputs remain in their
language-specific experiment directories.
