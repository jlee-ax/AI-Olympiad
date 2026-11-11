# Joined review preflight

`review_preflight.py` reads the actual artifact, current graph path declaration, recorded contest comparison and workflow state together. It never runs work, records acceptance, changes state or schedules a loop. See [the manual cycle](MANUAL-CYCLE.md) for the external work and recording steps.

```sh
python3 -B tools/review_preflight.py --root ROOT \
  --depth reviews/contest-depth.json --graph reviews/graph.json \
  --paths reviews/paths.json --state reviews/workflow.json
```

All input paths are relative to the explicit root. `--paths` may be omitted to expose a historical missing declaration as a gap. `--quality BUNDLE` additionally evaluates that current bundle using the selected root's criteria, contract and local assets; missing versioned criteria are an error, never an inferred pass. The code and selected root must have the intended compatible specification versions.

The report runs the existing contest inspector, [seven-role graph inspector](graph-paths.md), workflow validation, active-record recall and decision. It also hashes actual artifact bytes; checks the workflow artifact digest against that artifact; hashes recalled local source files; requires every recorded comparison to have a path with its `comparison_id` and provenance bound to the reviewed artifact; and rejects mixed synthetic/real contexts. Remote URIs are not fetched. Source truth, locator meaning and omitted dependencies still need direct review.

`required_inputs` returns three canonical manifests: `review:depth`, `review:graph`, `review:paths`, with revision `review-preflight-v1` and SHA-256 of parsed, sorted, compact, ASCII JSON. Bind them in `state.context.inputs` before an actual fresh aggregate review. This prevents changed judgments, sources or role mappings from reusing an unchanged old review. Copying hashes does not create agreement or a review. Artifact and provenance digests, separately, use raw bytes.

| Report | Exit | Meaning |
|---|---:|---|
| `invalid` | 2 | Invalid inputs or evaluation unavailable. |
| `blocked` | 1 | Missing/stale evidence, unresolved depth findings or noncontinuing workflow decision. |
| `consistent_recorded_context` | 0 | The declared checks agree mechanically with the local context. |

The underlying workflow decision is always reported separately. `continue`, `noop` and `verified_completion_claim` can satisfy its mechanical portion. A checkpoint or pending criteria decision blocks the joined result even if files match. A zero exit is advisory consistency, not authorization, educational adequacy, learner achievement or an instruction to execute work.

The tests use explicit synthetic declarations for independent passes and exercise actual files, subprocess CLI exit codes, missing paths/edges, changed notebook/source bytes, stale aggregate reviews, manifest refresh followed by a fresh review, JSON restart/no-op, mixed or malformed inputs, and read-only behavior. The [real-case reproduction](../reviews/system-improvement-20261111/reproduce_real_cases.py) applies the same code to copies of pinned Week 1 records. Its actual old workflow stays blocked; the harness does not manufacture a review or consent to make the real case green.
