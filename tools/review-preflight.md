# Joined review preflight

`review_preflight.py` reads the actual artifact, current graph path declaration, recorded contest comparison, path content review and workflow state together. It never runs work, records acceptance, changes state or schedules a loop. See [the manual cycle](MANUAL-CYCLE.md) for the external work and recording steps.

```sh
python3 -B tools/review_preflight.py --root ROOT \
  --depth reviews/contest-depth.json --graph reviews/graph.json \
  --paths reviews/paths.json --semantic-review reviews/path-content-review.json \
  --state reviews/workflow.json
```

All input paths are relative to the explicit root. `--paths` may be omitted to expose a historical missing declaration as a gap. `--semantic-review` supplies the separate recorded content judgment for each path; omitting it always blocks the joined result, including synthetic fixtures. `--quality BUNDLE` additionally evaluates that current bundle using the selected root's criteria, contract and local assets; missing versioned criteria are an error, never an inferred pass. The code and selected root must have the intended compatible specification versions.

The report runs the existing contest inspector, [seven-role graph inspector and recorded content-review gate](graph-paths.md), workflow validation, active-record recall and decision. It also hashes actual artifact bytes; checks the workflow artifact digest against that artifact; checks every declared local source catalog entry; requires every recorded comparison to have a path with its `comparison_id` and provenance bound to the reviewed artifact; and rejects mixed synthetic/real contexts. Role names and connected edges alone cannot satisfy the separate content-review gate. That gate records judgments about the problem-specific key, feedback and independent assessment, with current local evidence for each declared comparison. It preserves a reviewer's content judgment; it does not automatically judge correctness or establish learner performance.

Local source checks include `context.references` entries with no active recalled record, unused catalog entries and sources of superseded records. Matching historical versions remain valid when their declared paths preserve the pinned bytes. Changed or missing historical files block; preserve immutable source versions rather than rewriting old records to match a current file. Bare source paths must be root-relative and may contain colons or spaces. `file:` URIs may use a root-relative path or an absolute path inside the selected root, with percent-encoded spaces. File authorities, queries, fragments, malformed escapes and root escapes (including symlinks) block. Explicit external `scheme://` declarations are listed under `unverified_sources` and are never fetched. Pathless input, skill, rubric and evaluator manifests are not guessed into file paths. Source truth, locator meaning and omitted dependencies still need direct review.

A complete joined check requires five canonical `required_inputs`: `review:depth`, `review:graph`, `review:paths`, `review:semantic-review` and `review:source-catalog`. All use revision `review-preflight-v1` and SHA-256 of parsed, sorted-key, compact, ASCII JSON; the source catalog is the complete `state.sources` array. Bind them in `state.context.inputs` before an actual fresh aggregate review. This prevents changed judgments, role mappings or an unused catalog entry's URI/version/digest from reusing an unchanged old review. Refreshing manifests makes the previous workflow review stale; copying hashes creates no agreement or acceptance. Artifact, source and provenance digests separately use raw bytes. The Python helper accepts the content review and catalog as `context_manifests(depth, graph, paths, semantic_review, sources)`.

| Report | Exit | Meaning |
|---|---:|---|
| `invalid` | 2 | Invalid inputs or evaluation unavailable. |
| `blocked` | 1 | Missing/stale evidence or content review, unresolved judgments or noncontinuing workflow decision. |
| `consistent_recorded_context` | 0 | The declared checks agree mechanically with the local context. |

The underlying workflow decision is always reported separately. `continue`, `noop` and `verified_completion_claim` can satisfy its mechanical portion. A checkpoint or pending criteria decision blocks the joined result even if files match. A zero exit is advisory consistency, not authorization, educational adequacy, learner achievement or an instruction to execute work.

The tests use explicit synthetic declarations and content reviews for passing controls. They exercise actual files, subprocess CLI exit codes, missing paths/edges/content reviews, changed or missing recalled and unrecalled local sources, unused catalog rebinding, immutable historical versions, file URI confinement, stale aggregate reviews, manifest refresh followed by a fresh review, JSON restart/no-op, mixed or malformed inputs, and read-only behavior. The [real-case reproduction](../reviews/system-improvement-20261111/reproduce_real_cases.py) applies the same code to copies of pinned Week 1 records. Its actual old workflow stays blocked; the harness does not manufacture a review or consent to make the real case green.
