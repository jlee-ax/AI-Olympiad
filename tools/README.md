# Workflow tools

`workflow.py` validates recorded state and recommends a next step. It does not execute work or authenticate recorded claims. It is independent of the older graph-format validator, `validate.py`.

Read the [working procedure](../skills/references/workflow.md), [evaluation protocol](../skills/koai-evaluate/references/evaluation.md), and [research evidence](../skills/references/evidence.md) for the judgments that sit outside this tool. Attribution is retained in [third-party notices](../THIRD_PARTY_NOTICES.md).

## Commands

Run from the repository root with Python 3.10+; only the standard library is required.

```sh
python3 -B tools/workflow.py validate templates/workflow.json
python3 -B tools/workflow.py decide templates/workflow.json
python3 -B tools/workflow.py fingerprint examples/workflow.json
python3 -B tools/workflow.py recall examples/workflow.json --query 'synthetic evidence'
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

Each command reads one JSON file and prints JSON. It does not write state, contact services, launch commands or workers, generate lessons, schedule runs, create PRs, or merge changes. Repeated reads leave the input unchanged.

| Command | Result |
|---|---|
| `validate STATE` | Structural and reference checks. |
| `fingerprint STATE` | Context, criteria, and budget fingerprints after validation. |
| `recall STATE [--query TEXT]` | Active records, excluding superseded content and exact duplicates, with source details. |
| `decide STATE` | `pause`, `blocked`, `continue`, `noop`, or `stop`, with a reason code. |

Every result has `authority: advisory_only`. Structurally valid inputs exit 0 regardless of the decision; unreadable or invalid inputs exit 2. Exit 0 therefore does not mean that checks passed or work is authorized. CLI usage errors follow argparse's error output and exit 2. A nonempty `--query` applies only to `recall`.

The [template](../templates/workflow.json) is structurally valid but lacks agreements, configured criteria, and finite budgets: it returns `pause / operator_agreement_required`. That is the first unmet condition, not the only one.

The [example](../examples/workflow.json) is explicitly `synthetic: true`. Its approvals, hashes, reviewers, checks, and budgets are fixture declarations, not actual authority or execution history. Its digests were generated from synthetic identifying strings.

## State contract: version 1

| Field | Meaning |
|---|---|
| `schema_version`, `synthetic` | Integer version 1 and a boolean identifying synthetic state. |
| `scope` | `task_kind`: `design`, `lesson_production`, or `recurring`; boolean `lesson_production_allowed` and `recurring_allowed`. The latter two task kinds require their corresponding flag before a continue recommendation. Both flags default to false in the template; enabling them creates no execution capability. |
| `agreement` | `operator_agreed`, `operator_id`, `criteria_agreed`, `criteria_fingerprint`, `budget_fingerprint`. Record actual user decisions; strings and booleans do not authenticate consent. |
| `context` | `inputs`, `skills`, `rubric`, `evaluator`, `references`, `artifact`, `author`, `required_checks`, `finish_condition`. The template permits empty or null values; the decision procedure checks configuration before proceeding. |
| `frozen` | A baseline containing `rubric`, `evaluator`, `references`, `required_checks`, and `finish_condition`, or null before configuration. Changes require an explicit new comparison/baseline. |
| `limits` | `checkpoint_minutes` defaults to 30 in the template. `max_iterations`, `max_elapsed_minutes`, and `max_no_progress` remain null until agreed and must be positive integers before proceeding. The example's 3 attempts, 90 minutes, and 2 non-progress attempts are not recommended defaults or validated optima. |
| `usage` | Caller-reported nonnegative integers: `iterations_used`, `elapsed_minutes`, `no_progress_count`, `minutes_since_checkpoint`. The tool does not measure elapsed time or external work. |
| `stop` | `requested`, `reason`, `goal_claimed`. An explicit stop requires a reason. A goal claim can support completion only with current required checks and a separate accepted review. |
| `sources` | Source catalog entries: `id`, `uri`, `revision`, `sha256`. The tool does not open links or fetch source material. Use a new ID for a new source version so earlier records remain interpretable. |
| `records` | `id`, `kind`, `text`, `created_at`, `source_refs`, `supersedes`. Kinds: `evidence`, `decision`, `observation`, `skill`. Each record needs at least one source reference with a location. |
| `reviews` | `id`, `context_fingerprint`, `author_id`, `reviewer`, `checks`, `conclusion`, `reason`. Conclusions: `accepted`, `changes_requested`, `abstain`. Of reviews matching the current fingerprint, the last in array order applies. |
| `history` | Completed attempts: `id`, `context_fingerprint`, `outcome`, `reason`. Outcomes: `accepted`, `rejected`, `no_progress`. Merely reading state or waiting for agreement is not a completed attempt. |

A manifest contains `id`, a nonempty `revision`, and a lowercase 64-character hexadecimal `sha256`. `inputs`, `skills`, and `references` are manifest lists; `rubric`, `evaluator`, and `artifact` are individual manifests. Each `context.references` entry must match its catalog ID, revision, and digest. For real work, the caller must calculate digests from actual content. The tool checks declared formats and references, not whether those bytes exist or match.

Both `author` and `reviewer` have `id` and `model_family`. Each source reference has `source_id` and a nonempty `locator`. Each check has `id`, `status`, and `evidence_record_ids`; permitted recorded statuses are `passed`, `failed`, and `not_run`.

Passing checks must cite current records of **kind `evidence`**. Decisions, observations, and skills alone cannot justify a pass. A claimed pass with superseded support becomes `stale`; missing support or the wrong record kind becomes `unsupported`. A missing required check becomes `not_run`. Referential integrity does not establish that a claim is true.

## Fingerprints and reuse

`context_fingerprint(state)` hashes the declared scope and permission flags; input, skill, and artifact identities/revisions/digests; author; measurement configuration; active record kinds/text/source locations; and the referenced source catalog. Canonical ordering makes manifest-list order irrelevant. Changing a skill version, artifact, scope, or relevant evidence changes the fingerprint.

Exact duplicate record payloads—kind, text, and source locations—count once even when record IDs or timestamps differ. Repeated identical source references and undeclared decorative metadata do not create new evidence. This is exact deduplication, not semantic equivalence or contradiction detection. Paraphrases, distinct source IDs, and omitted dependencies still require review; selected state does not guarantee comprehensive retrieval.

Reviews, completed-attempt receipts, and usage counters do not enter the context fingerprint, so recording a result does not invalidate itself. The latest matching review is checked again. A new failed check or rejected review takes precedence over an old completion receipt. With valid verification and an existing completed attempt at the same fingerprint, the result is `noop / no_new_evidence`. Changed context cannot reuse old reviews or attempts.

`criteria_fingerprint(state)` hashes the measurement configuration. `budget_fingerprint(state)` hashes the declared scope and limits. If the values recorded in `agreement` do not match, the planner pauses for the corresponding agreement. Copying calculated hashes into agreement fields does not create consent.

When official scope, evaluator, rubric, required checks, or completion criteria change, preserve the earlier experiment and set up the new context, frozen baseline, agreements, and reviews in a new state file/baseline. The CLI cannot authenticate historical changes or prevent someone from silently rewriting `frozen`.

## Supersession and recall

`supersedes` may reference only earlier record IDs. Preserve original records. Two successors replacing the same predecessor form an invalid branch; v1 cannot repair that branch by appending a reconciliation record. Keep alternatives as observations without `supersedes`, then have one reviewed successor explicitly replace the current record and applicable alternatives.

Recall excludes superseded records and exact copies of their retired content. To reverse a correction deliberately, add a record that supersedes the current correction lineage. Superseding an unrelated record to revive corrected content is invalid.

Recall splits the query on whitespace and returns active records whose text contains every term, using case-insensitive substring matching. An empty query returns all active, deduplicated records. Source details accompany each result. There is no vector search, semantic search, summarization, or automatic deletion.

## Decision precedence

The first applicable condition wins; later checks may not yet have been evaluated.

1. Validate structure and references. Unreadable JSON, non-finite numbers, and lone Unicode surrogates are rejected.
2. Honor an explicit stop request. Then require operator agreement, criteria agreement, the relevant scope flag, and configured context. Inputs, skills, and required checks must be nonempty; artifact, rubric, evaluator, author, and finish condition must be configured.
3. Require a frozen baseline matching the current measurement configuration and a matching criteria-agreement fingerprint.
4. Require finite budgets and a matching budget-agreement fingerprint. Completed receipts set a lower bound on iterations; trailing rejected/non-progress receipts since the last accepted attempt set a lower bound on stagnation. Reaching an iteration, elapsed-time, or non-progress limit returns `stop`, in that order.
5. When reported time since checkpoint reaches `checkpoint_minutes`, return `pause / checkpoint_due`. This precedes verification and completion. Thirty minutes is the requested default checkpoint, not an optimality claim, timer, or forced process-kill boundary.
6. Check the last review matching the current context. Its author ID must match the artifact's author, and its reviewer ID must differ. A reported same-family model generates a warning. Different identity strings do not prove independent people, executions, models, or reasoning.
7. If verification passes and the goal is claimed, return `stop / verified_completion_claim`. Otherwise failed, missing, stale, or unaccepted verification returns `blocked`. With valid verification, a matching completed receipt returns `noop / no_new_evidence`; otherwise return `continue / verified_candidate_within_budget`.

Verification passes only when every required check has current evidence, the review is accepted, and the recorded author/reviewer identity conditions hold. A goal boolean alone cannot establish completion.

A continue recommendation proposes a bounded next step; it neither grants authority nor schedules it. After a checkpoint, an authorized operator may update actual usage and reset `minutes_since_checkpoint`, preserving total time, attempts, and history. State persistence and handoff are external responsibilities: this tool supplies no writer, append-only enforcement, authentication, or concurrent locking.

## Python API and verification limits

`validate_state(state)` returns structural errors and warnings; `decide(state)` returns structural errors in its decision result. `context_fingerprint`, `criteria_fingerprint`, `budget_fingerprint`, `measurement`, and `recall_records` are pure queries that expect previously validated state. The public CLI validates before querying.

Synthetic tests cover fingerprint changes, stale reviews, evidence kinds, failed/unrun checks, reviewer IDs, frozen baselines, duplicate no-ops, supersession, budgets, checkpoints, malformed JSON, and read-only behavior. They do not establish source truth, actual execution, authentic consent, immutable history, elapsed time, independent judgment, learner outcomes, or the effectiveness of repeated improvement.

## Host runtime notes

The following observations come from an inspected unofficial Codex port at revision `7f3b75256df824ca84a9b76b6bc202b967a221c2` (2026-11-09). That port was neither installed nor executed for this project.

- **File parity is not behavioral parity.** Its [parity contract][parity] and [checker][parity-code] concern file correspondence, existence, and blob hashes. They do not demonstrate instruction following, recovery, or production reliability. The inspected [integration report][integration] records an earlier version, so it is not current-version validation.
- **Persistent records are not persistent workers.** The [runtime contract][runtime] and [orchestration procedure][orchestrate] reconstruct workers and check current branch/PR state after a restart. A saved agent ID is not a durable worker handle. Local files do not create a cloud VM or independent security boundary.
- **Scheduling belongs to the host.** Verify available automation capabilities and saved schedules; detached sleep is not durable scheduling. The inspected [polling contract][polling] distinguishes a 30-minute triage budget and an in-run read interval from recurrence. The host available during the 2026-11-10 review supported schedules no more frequently than hourly; importing files could not supply a 30-minute scheduler. A paused heartbeat's creation/read/deletion is not evidence of timed delivery.
- **Watchers report observed conditions.** The inspected [watcher CLI][watch] and [policy][watch-policy] classify PR conflicts, reviews, and CI. `--status-only` exit 0 means reporting succeeded; read the JSON decision separately. Default timeout 0 is unbounded. Suppressing repeated reports is not external-action deduplication, scheduling, merging, or educational evaluation.
- **A ledger is not exactly-once execution.** The inspected [ledger][ledger] records intent and unresolved outcomes and uses locks; it does not automatically expire stale locks or authenticate external success. Check the actual service before resolving an uncertain result or retrying. No such external-action ledger or executor is implemented here.

[parity]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/PARITY.md
[parity-code]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/scripts/parity.py
[runtime]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/CODEX.md
[orchestrate]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md
[watch]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts
[watch-policy]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.ts
[ledger]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/automations/benny/scripts/ledger.mjs
[polling]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/plugins/pstack/automations/benny/POLLING.md
[integration]: https://github.com/ScriptedAlchemy/pstack-codex/blob/7f3b75256df824ca84a9b76b6bc202b967a221c2/INTEGRATION-TESTS.md

## Concrete quality assessment

The [quality specification](../skills/references/quality-specification.md), [criterion catalog](../skills/references/criteria.json), and [unit specifications](../skills/koai-evaluate/references/unit-specifications.json) define concrete objects, observations, severity, pass/fail/uncertainty and pending choices. The confirmed course is ten 120-minute classes; its [existing HTML](../curriculum/student-plan.html) and [60-topic contract](../curriculum/contract.json) are version-bound.

Run these read-only commands from the repository root:

    python3 -B tools/quality.py baseline
    python3 -B tools/quality.py evaluate templates/quality.json
    python3 -B tools/quality.py plan templates/quality.json
    python3 -B tools/quality.py agreement-context templates/quality.json
    python3 -B tools/quality.py impact BUNDLE --changed SOURCE_ID
    python3 -B tools/quality.py review-context BUNDLE --criterion K10 --object CLAIM_ID
    python3 -B tools/workflow.py decide STATE --quality BUNDLE

Use the quality bundle contract in the specification. For real objects, populate actual artifacts, diagnoses, activity links, claims, source reads, execution receipts and independent reviews; do not copy synthetic passes.

The default quality bundle remains incomplete. A baseline pass verifies pinned schedule/scope consistency, not current material readiness. The evaluate output lists K01–K15 measurements and findings. Plan suppresses exact earlier attempts, gives a reproduced defect a priority floor, and pauses for missing agreement, finite limits, an unscoped higher-priority blocker or the reported 30-minute checkpoint. It cannot execute the recommendation.

Quality commands return structured JSON with authority advisory_only. Exit 2 means unreadable/invalid input or baseline errors; other decisions can exit 0. Inspect status and ready_for_review. A zero exit alone does not establish readiness.

### Binding quality into the existing workflow

Lesson-production and recurring decisions now require a quality report. Existing design decisions can still use the earlier state contract without one. An optional quality bundle on a design decision is also checked.

The API accepts decide(state, quality_report=None). A supplied report must come from evaluating the actual current bundle/root. Public CLI --quality performs that evaluation itself. The report is a recorded preflight, not authenticated truth.

Bind these exact manifests in context.inputs:

| Manifest ID | Revision | SHA256 |
|---|---|---|
| quality:bundle | The quality bundle revision | Report bundle_sha256: canonical JSON, not pretty-printed raw file bytes |
| quality:criteria | Report specification_revision | Actual criterion-catalog file bytes |
| quality:evaluator | quality-v1 | Actual quality.py file bytes |

The workflow artifact digest must match the quality report's actual artifact digest. A synthetic quality report cannot validate non-synthetic workflow state. Every K01–K15 check must pass and ready_for_review must be true. The existing independent current-context verification and completion predicate still apply.

Quality is checked after scope, agreement, frozen baseline, finite budgets and checkpoint conditions, before the existing verification step. Missing quality pauses; missing bindings, artifact mismatch, failed/uncertain/unrun checks or a synthetic/real mismatch block. Adding the manifests changes the workflow context, so refresh the aggregate review explicitly. Current unit content reviews may be reused only according to their own actual region/dependency bindings.

The workflow input validation/fingerprint/recall commands keep their structural meanings. Only the decision gate gains this concrete preflight. No scheduler, Jupyter executor, web source reader, state writer or publisher is added.

### Synthetic end-to-end example

    python3 -B tools/quality.py evaluate examples/quality.json
    python3 -B tools/workflow.py decide examples/quality-workflow.json --quality examples/quality.json

The first reports a synthetic passed fixture; the second reports an advisory synthetic continue decision. No actual lesson execution, learner result or user approval is established. The real template remains incomplete, and a synthetic report cannot validate real state.
