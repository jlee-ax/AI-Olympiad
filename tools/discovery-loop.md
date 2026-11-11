# External requirement discovery loop

`discovery_loop.py` manages a finite, replayable review of an explicitly sampled external frontier. It fixes a narrower failure mode: `quality.py` K11 follows already registered claims, `contest_depth.py` follows registered goals/comparisons, and the older joined preflight connects those comparisons to paths. A sound record for those objects cannot discover an absent concept or a deeper external problem demand. The new frontier is seeded before the program permits lesson comparison; later reading can append new questions and demands.

The program executes local source and lesson reads, validates transitions, retains exact excerpts and byte hashes, computes the next action, queues unreviewed/gap/uncertain demands, tracks declared changes and finite usage, suppresses exact duplicates, and replays saved JSON. A human or model executes searches with available tools, reads the primary material, extracts and judges meaning, and performs any authorized lesson edits. The program does not browse, invoke a model, transform a PDF, edit a lesson, authenticate reviewers, or establish source truth. A source snapshot and its attribution must retain the connection to the original primary source; a text projection does not authenticate that connection.

## Commands and persistence

All commands print JSON to stdout and leave inputs unchanged. Python 3.10+ and the standard library suffice.

```sh
python3 -B tools/discovery_loop.py init config.json > session-00.json
python3 -B tools/discovery_loop.py step session-00.json --event event-01.json --root . > session-01.json
python3 -B tools/discovery_loop.py next session-01.json --root .
python3 -B tools/discovery_loop.py report session-01.json --root .
python3 -B tools/discovery_loop.py manifest session-01.json
```

Write a next state to a different file; redirecting stdout onto the input would truncate it before the command reads it. Keep earlier states/events as review history. A caller may deliberately replace a state after checking the new output. Invalid input exits 2. Valid report/next commands exit 0 even when `needs_work`, `paused`, or `stopped`; inspect `ready_for_review` and `status`. A zero exit is never a completion or authorization signal.

The equivalent Python functions are `initialize(config)`, `step(state, event, root)`, `inspect(state, root)` and `manifest(state)`. `step` returns a new session and reads files only for read/compare events. `inspect` reopens recorded spans and checks current bytes. Both replay the full event chain. Root-relative regular files are required; absolute paths, escapes and symlink escapes are rejected. Readers need UTF-8 text snapshots; retain primary files and conversion provenance separately.

## Seed a review boundary

A minimal config is:

```json
{
  "schema_version": 1,
  "synthetic": true,
  "scope": {
    "id": "unit:foundation",
    "lesson_path": "lesson.txt",
    "lesson_revision": "fixture-v1",
    "readiness": "scoped_foundation",
    "boundary": "One introductory unit; later course demands need accountable placement."
  },
  "frontier": [{
    "id": "probe:external",
    "question": "What observable operations and reasoning do primary external tasks require?",
    "required_kinds": ["official_scope", "official_problem", "research"]
  }],
  "policy": {
    "max_events": 80,
    "max_rounds": 12,
    "max_no_progress": 4,
    "max_elapsed_minutes": 180
  }
}
```

These numbers are fixture examples, not recommended budgets or user agreements. Use `synthetic:false` for real work. `readiness` is `scoped_foundation` or `course`; it does not change the official target. When `lesson_path` is a text projection of an actual notebook, additionally set `scope.artifact_path` and `scope.artifact_sha256` to the original artifact's root-relative path and raw SHA-256. The tool checks the original bytes and projection independently, but their semantic correspondence still requires review.

Each frontier probe has a unique immutable ID, an external question and nonempty `required_kinds` from `official_scope`, `official_problem`, `research`, `background`. Select questions and relevant source families independently of lesson claims. Distinguish governing national scope, newer international material of uncertain applicability, examples, actual past problems, research and local teaching hypotheses. A newer source does not silently supersede the governing national target.

The session contains the seed, its digest and an append-only hash chain. Changing/removing a seed obligation or historical event breaks replay unless a caller explicitly constructs and rebinds a different baseline. The chain is integrity bookkeeping, not authenticated history. Review manifests prevent an existing aggregate review from silently accepting the changed universe.

## Event contract

Every event has `id`, `op`, and `data`. Every `data` requires a nonempty `reason`; `minutes` is an optional nonnegative integer, accumulated from the caller's report. The program is not a timer. Event IDs are immutable; exact retries of the same ID are idempotent.

| Operation | Additional data | Effect |
|---|---|---|
| `discover` | `frontier_id`, `query`, `actor`, `outcome`, `candidates` | Records external search results, including no-result/access failures. `outcome` is `found`, `no_results` or `unavailable`; only `found` has nonempty candidates. Each candidate needs `id`, `uri`, `path`, `revision`, `kind`, `attribution`. |
| `read` | `source_id`, `actor`, `start_line`, `end_line` | Opens actual discovered local bytes and stores an automatically generated receipt. Supplied receipt text cannot replace this read. |
| `trace` | `frontier_id`, `read_ids`, `actor`, `rationale`, `counterevidence`, `uninvestigated`, `demands` | Traces observable requirements back to that frontier's direct readings. Preserves contrary evidence and new questions. |
| `compare` | `demand_id`, `reviewer`, `judgment`, `rationale`, `start_line`, `end_line`, `dimensions` | Opens the selected actual lesson and compares every applicable demand axis. The declared reviewer must differ from the demand extractor. |
| `frontier` | `probe`, optional `resolves` question IDs | Adds another external question; never removes an existing probe. `resolves` transfers persistent open questions to the new probe, whose own investigation must still finish. |
| `supersede_source` | `old_source_id`, `new_source_id`, `reviewer` | Explicitly transfers current source-version obligations. Historical reads remain visible; active demands using old/stale reads still need retracing and explicit replacement. |
| `supersede` | `old_demand_id`, `new_demand_id`, `reviewer`, `dimension_dispositions` | Retains an explicit before/after mapping for every old demand dimension, including the prior gap. It does not establish semantic equivalence. |
| `review_supersession` | Same old/new mapping and review fields | Rechecks an unresolved retirement after further evidence. Earlier judgments remain history. |
| `pause`, `resume` | Common `reason`/`minutes` | Stops/resumes the session without resetting counters or discarding obligations. An exhausted budget requires a new explicit baseline. |

A trace demand requires `id`, `statement`, `prerequisites` (string array), `learning_demand`, `assessment_demand`. There are no domain-specific keyword rules. Extract the inputs, representations, assumptions, decisions, implementation obligations, reasoning and unaided evaluation depth the source actually requires. Optional `dimensions:[{id,required_behavior}]` adds finer checks; it cannot remove the default `learning`, `assessment`, and (when nonempty) `prerequisites` axes. Add mathematical or technical dimensions only when the demand and stage actually need them.

`uninvestigated` is a string array. Each new string becomes a persistent named question. A subsequent empty trace cannot erase it. Read `report.open_questions`, then add a frontier probe with `resolves:[question_id]`. Even a background-source question blocks readiness. A frontier with no extracted demands stays unresolved; recording “nothing applies” alone cannot close an external universe. Explicit scoped/out-of-scope demands allow a reviewer to retain what was considered and why it does not belong in the selected lesson.

For a `covered`, `gap` or `uncertain` comparison, `dimensions` must contain exactly every required dimension ID. Each item requires `id`, `judgment` (`met`, `gap`, `uncertain`), `observed_behavior`, `rationale`, `start_line`, `end_line`. `step` opens each exact span and stores a receipt. Overall `covered` cannot override a gap/uncertain dimension. A term appearing in a lesson does not by itself support derivation, debugging, transfer or independent assessment: the content reviewer must make and justify that distinction. False but structurally complete semantic assertions remain possible and are disclosed as declarations.

A `deferred` or `out_of_scope` comparison requires `scope_basis`; dimension results may be omitted. `deferred` additionally needs `placement:{unit_id,path,start_line,end_line,owner,rationale}`, with a live read receipt generated from the actual placement document. Scoped foundational readiness may retain accountable later placement. Deferred teaching cannot satisfy course readiness, and planned placement establishes neither later delivery nor learner mastery. Changed placement bytes reopen the review.

For demand replacement, `dimension_dispositions` must map every old required dimension with `{old_dimension_id,new_dimension_id,judgment,rationale}` to an existing successor dimension. Judgments are `preserved` or `unresolved`; `unresolved` blocks readiness until `review_supersession` records a current preservation review. The reviewer must differ from the old/new extractors. Reports retain before/after required behaviors, the old comparison and every retirement review. These declarations make narrowing reviewable; they do not prove preservation of meaning.

## Iteration, changes and stop conditions

The sequence is external discovery → actual source read → requirement tracing → actual lesson comparison. A gap/uncertainty produces a queue entry and affected demand/frontier/scope IDs. The next actor investigates the gap, reads additional primary evidence, adds questions/demands where needed, makes an authorized revision if warranted, and records a fresh comparison. The program does not execute that actor's work.

Every discovered source must be read and traced. Newly discovered sources and newly traced demands invalidate a prior `recorded_ready` result; they are not ignored because an older source of the same kind already passed. Changed source bytes invalidate dependent demands; changed lesson or placement bytes invalidate their comparisons. Use a new source version, read it, trace a successor demand and explicitly supersede old source/demand obligations. Source-reading timestamps or cosmetic IDs do not substitute for new evidence.

Source progress identity uses URI/path/revision/kind, excluding ID and attribution. Demand deduplication uses exact demand content and source/receipt identity, excluding event/read/demand IDs. Duplicate demands report aliases so later comparisons can resolve their IDs. This is exact deduplication; paraphrases and semantic equivalence remain reviewer work. Repeated same-source searches or same-demand traces increment no-progress; meaningful new evidence can reset it. The event and round caps remain cumulative. Repeated operator pauses and earlier judgments reapplied after a later change remain valid transitions rather than disappearing under global deduplication.

Finite limits apply at every replay prefix, not only the final counters. A valid hash appended after a budget stop cannot reset no-progress and revive readiness. JSON restart preserves counters, open questions, source versions and prior gaps. Reports return `needs_work`, `paused`, `stopped` or `recorded_ready`. The last means only that the sampled declared frontier has current recorded judgments and no unresolved mechanical obligations. It never means complete coverage of the external world, contest sufficiency or measured learning benefit.

## Joined readiness

Real joined preflight requires `--discovery SESSION` by default. `--legacy-scope` permits historical inspection but always returns `legacy_inspection_not_ready`; it cannot support readiness/completion. Synthetic historical fixtures keep their narrower behavior. Bind `discovery_loop.manifest(session)` in `state.context.inputs`; its ID is `review:discovery`, revision `discovery-loop-v1`. The helper `context_manifests(depth,graph,paths,semantic_review,sources,discovery_state)` includes it. A changed frontier, source, demand, judgment or counter changes this binding and requires a fresh aggregate review; copying manifests creates no agreement or acceptance.

Each active `covered` discovery demand additionally needs a graph path with `discovery_demand_id`. Existing seven-role path/semantic-review checks still apply. Deferred/out-of-scope placements remain visible without inventing a current lesson path. The discovery artifact must match the artifact reviewed by preflight; a projection needs the original-artifact pair described above.

A quality bundle may set `discovery:{"path":"reviews/session.json"}`. Real quality readiness requires a current ready session for the same artifact. The discovery gate is supplemental: it does not add a K17, alter K01–K16, or rewrite frozen criteria. `quality.plan_work` exposes `next_discovery_action` and preserves nested pause/stop. Real `lesson_production`/`recurring` workflow decisions also require discovery even when called directly, and bind the manifest before any continue/noop/completion claim. Design/synthetic compatibility does not make a broad lesson-readiness claim.

```sh
python3 -B tools/workflow.py decide state.json --quality quality.json --discovery session.json --root .
python3 -B tools/review_preflight.py --root . --depth depth.json --graph graph.json \
  --paths paths.json --semantic-review semantic.json --state state.json --discovery session.json
```

The synthetic regression suite uses unrelated opaque demands and real temporary files, plus neighboring good/fault cases. It covers new obligations, semantic judgment limits, depth mismatches, legitimate deferral, changed bytes, source replacement, question expansion, duplicate aliases, budget prefixes, pause/resume and direct production/readiness integration. These are finite software tests, not a study of educational quality or proof that an external search was comprehensive.
