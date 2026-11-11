# Manual workflow cycle

`workflow.py` reads a saved JSON state and returns advice. An operator performs
work, reviews it, and saves the next state. Restarting the CLI reconstructs its
queries from that file; it does not resume a worker or recover unsaved work.
Use [the state contract](README.md#state-contract-version-1) for exact fields.

## Read the saved context

Run from the repository root, substituting your actual saved paths:

```sh
python3 -B tools/workflow.py validate path/to/state.json
python3 -B tools/workflow.py fingerprint path/to/state.json
python3 -B tools/workflow.py recall path/to/state.json --query 'relevant terms'
python3 -B tools/workflow.py decide path/to/state.json
```

For lesson-production or recurring scope, the decision also needs the current
quality bundle. A design task may supply one:

```sh
python3 -B tools/quality.py evaluate path/to/quality.json
python3 -B tools/workflow.py decide path/to/state.json --quality path/to/quality.json
```

To join depth comparisons, graph paths, recorded path content judgments, actual
local files, the full declared source catalog and workflow review, use the optional
preflight (add `--quality` when applicable):

```sh
python3 -B tools/review_preflight.py --root . \
  --depth path/to/depth.json --graph path/to/graph.json --paths path/to/paths.json \
  --semantic-review path/to/path-content-review.json --state path/to/state.json
```

Its `required_inputs` lists canonical depth, graph, path, content-review and full
source-catalog manifests that must be bound into workflow inputs before obtaining
a fresh aggregate review. The content review is required even for synthetic
fixtures. It records scoped judgments about the problem-specific key, feedback
and independent assessment; connected role labels do not supply those judgments.
A binding mismatch or stale review blocks the joined result; copying the hashes
does not supply that review. All submitted declarations still need actual human
or agent judgment. See [the preflight contract](review-preflight.md) for the
manifest IDs, local URI policy and separate limits on learner claims.

Preflight checks all declared local sources, including context-only references,
unused catalog entries and sources of superseded records. Preserve historical
source files at immutable paths with their recorded hashes. A changed or missing
local source blocks even if no active record recalls it. Changing a catalog URI,
revision or digest also requires a new catalog binding and aggregate review.
External sources remain explicitly unverified and are never fetched; pathless
manifests are not inferred as filesystem locations.

Read `status`, `reason`, findings and errors, not just the exit code. All commands
above are read-only. `continue` is an advisory candidate within recorded limits;
it does not grant permission, execute work, or prove the recorded claims true.

## Perform and record a bounded attempt

1. Preserve the previous state before editing. Resolve the first decision reason
   using actual evidence and existing authorization. Record only real agreements
   and agreed finite limits; copying fingerprints or toggling flags cannot create
   consent. Changed criteria need an explicit new comparison/baseline, preserving
   the earlier state. Synthetic fixtures demonstrate format, not real approvals.
2. An authorized operator performs one bounded task and records what actually
   happened. Update actual artifact/input manifests and source versions. Append
   source-linked `records` with distinct IDs; use `supersedes` for a reviewed
   correction of earlier records. Preserve original records and source versions.
   Unsuperseding alternatives can remain observations until one resolution exists.
3. Update actual cumulative `usage`, including elapsed time and checkpoint time.
   A completed attempt increments attempts; reading the state or waiting for an
   agreement does not. Preserve total usage across restarts. Neither the CLI nor
   the counters measure elapsed time for you.
4. Validate the updated state and calculate its current fingerprint. Context
   changes normally make earlier aggregate reviews stale. Obtain a real separate
   review of that current candidate. When using joined preflight, first record
   the actual scoped path content review and bind all returned `required_inputs`;
   append the aggregate `reviews` entry, required checks,
   current evidence record IDs, conclusion and reason. Different identity strings
   alone do not establish independence. Never change an old review fingerprint
   to pretend its evidence was rechecked.
5. For quality-gated work, update and evaluate the actual quality bundle and bind
   the three exact quality manifests described in
   [the quality binding contract](README.md#binding-quality-into-the-existing-workflow).
   Changes to these manifests also require a current aggregate workflow review.
   Repeat `validate`, `fingerprint`, and `decide` after these updates.
6. Append a `history` receipt for each actually completed attempt: a distinct ID,
   the context fingerprint of the resulting candidate/evidence, its real
   `accepted`, `rejected`, or `no_progress` outcome, and a reason. Preserve prior
   reviews and receipts. Recalculate subsequent decisions from the saved state;
   receipts themselves do not change the context fingerprint.

Exact payload duplicates with new IDs or timestamps do not create new evidence.
With current passing verification, a receipt for the same context yields
`noop / no_new_evidence`. Changed evidence yields a new context and requires
current verification. A newer failure for the current context blocks reuse even
when a previous receipt exists. These checks rely on the supplied history; there
is no append-only enforcement or authenticated execution ledger.

## Checkpoints, stop, and restart

At the reported checkpoint boundary, `decide` returns `pause / checkpoint_due`
before verification or completion. Record a useful handoff: current artifact and
state paths, actual work and tests, unresolved questions, totals, and next bounded
step. After the actual checkpoint, an authorized operator may reset only
`minutes_since_checkpoint`; keep cumulative time, attempts and history. Finite
budget exhaustion returns `stop` and takes precedence over a checkpoint.

Save state after actual updates, then rerun validation and the decision on that
saved file. After a restart, reread it and recall relevant records before working.
A caller must provide safe persistence and coordination: the tool supplies no
state writer, atomic update, concurrent lock, scheduler, background worker,
external-action retry, or elapsed-time timer. Inspect actual external outcomes
before recording or retrying an uncertain action.

Set a completion claim only when its actual condition has been checked. A current
accepted review of every required check is also necessary for
`stop / verified_completion_claim`. An explicit requested stop is honored before
quality and review gates. Preserve the saved state and report remaining blockers.
