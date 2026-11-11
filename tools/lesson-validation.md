# Validate current tools with a frozen lesson

`lesson_validation.py` combines the current `tools`, `skills`, `templates`, `examples` and `tests` with a lesson checkout's `lessons`, `reviews` and `curriculum` in a **new external workspace**. It copies no Git state, preserves hashes of every input file, refuses symlinks and existing/in-source destinations, and verifies the copied bytes before execution. Original changes after preparation require a fresh workspace. Post-run checks report original changes and unexpected copy changes.

This is a versioned copy for avoiding accidental source-worktree writes, **not an OS security sandbox**. It does not revoke filesystem/environment/network rights from a child process or undo writes. Only run reviewed, authorized lesson code. The existing host sandbox still applies. Neither worktree is rewritten or merged by this tool.

```sh
python3 -B tools/lesson_validation.py prepare \
  --tool-root /path/to/current-improvement-checkout \
  --lesson-root /path/to/pinned-lesson-checkout \
  --output /path/to/new-validation-workspace
python3 -B tools/lesson_validation.py run --root /path/to/new-validation-workspace
```

The default run evaluates the latest baseline, historical bundle and a new artifact-bound bundle. It does not execute notebook/key snippets. Use explicit `--execute-notebook` only for the reviewed lesson: both its validator and `check_depth.py` execute supplied code and teacher-key snippets. The runner first removes the copied historical receipt, executes a fresh in-process notebook kernel, validates the new receipt's timestamp, current artifact hash, source projection, code-cell counts, zero errors, required assertions and blank/unobserved learner scope, then checks the final notebook/HTML. A zero process exit with a missing/old/mismatched receipt cannot create a passed execution claim.

```sh
python3 -B tools/lesson_validation.py run --root /path/to/new-validation-workspace \
  --python /path/to/python-with-notebook-dependencies --execute-notebook
```

Dependencies for the pinned Week 1 validator are NumPy, pandas, Matplotlib, Seaborn, nbformat, nbclient, nbconvert, ipykernel and jupyterlab metadata. The runner installs nothing. An optional `--dependency-path` adds an explicitly selected installed-package directory. Application caches/runtime files use the validation workspace; no personal-device work is involved.

`validation-current/` contains exact command/stdout/stderr receipts, fresh quality bundle and current evaluator output. `run.json.status: passed` means all requested commands ran successfully and preservation/integrity checks held. The quality report may still be failed, uncertain or not ready. A new artifact/execution binding does not promote historical semantic reviews to current passes. Add actual current reviewer evidence separately; source and learner uncertainties remain visible.

Before/after comparisons of tools/specs and protected lesson files detect unexpected changes. The intentional copied outputs are the executed notebook, rendered HTML, receipt and validation images. No worker, concurrency lock, authenticated ledger or scheduler is added.
