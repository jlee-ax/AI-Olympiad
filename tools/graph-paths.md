# Explicit learning-path inspection

`graph_paths.py` adds an opt-in, read-only check of a declared learning route. The existing `validate.py` API, CLI, exit codes and structural scope remain unchanged. A structurally valid graph may still lack the teaching and assessment connections needed for a review.

```sh
python3 -B tools/validate.py tests/fixtures/candidate-graph-missing-path.json
python3 -B tools/graph_paths.py tests/fixtures/candidate-graph-missing-path.json
python3 -B tools/graph_paths.py examples/graph-path.json --root .
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_graph_paths.py' -v
```

The first command exits 0 with no structural errors or warnings. The second exits 1 with a `gap`: that historical candidate has no explicit learning-path declarations. The third exits 0 with `declared_path_complete` for an explicitly fictional fixture. Its sources, task and assessment conditions are synthetic; it demonstrates the format and local byte checks only.

The historical fixture is an exact copy of `ai-olympiad-week01-reference/reviews/week01/contest-depth/candidate-graph.json` inspected during the 2026-11-11 workflow review. Its raw-file SHA-256 is `b28289fd2bee5e5255cd01a00492fe247f86b807e9f6d0b406c5b7d4cd7818a3`. Its 12 nodes and 21 edges record source/artifact/review relationships, without a seven-role route. The absence finding does not establish which lesson ideas or activities exist outside the graph.

## CLI and API

```sh
python3 -B tools/graph_paths.py GRAPH.json --spec PATHS.json --root LOCAL_ROOT
```

`--spec` supplies a separate path specification; when omitted, the checker uses `graph.path_spec`, or an empty object if it is absent. `--root` is the local provenance root; its default is the graph file's parent directory. Use `--root .` when provenance paths start at the repository root. Files are never fetched from the network or changed. JSON duplicate keys, non-finite numbers and lone Unicode surrogates are invalid.

`inspect_paths(graph, path_spec, root)` returns the same report as the CLI; `inspect` is an alias. It first calls the legacy structural validator. Both input objects are left unchanged. `graph_sha256` is the SHA-256 of canonical parsed graph JSON with sorted keys, compact separators and ASCII escaping, **not** its raw file digest. Provenance digests, by contrast, are calculated from actual raw file bytes.

| Status | CLI exit | Meaning |
|---|---:|---|
| `invalid` | 2 | Malformed input, unsupported contract, invalid graph, or unsafe file path. |
| `stale` | 1 | At least one declared local digest differs from current file bytes. |
| `gap` | 1 | Missing scope, role, direct connection, provenance, readable file or assessment conditions. |
| `declared_path_complete` | 0 | Every declared route and local binding passed these mechanical checks. |

Precedence is `invalid`, then `stale`, then `gap`, then `declared_path_complete`. Mixed findings remain visible. Each path has its own status; `bindings` reports the path ID, role, node ID, declared local path, expected digest, observed digest and `current`, `stale` or `unavailable` status. Missing provenance has a finding without a fabricated binding receipt. Every result has `authority: advisory_only`.

## Specification version 1

Use the complete [synthetic graph and embedded specification](../examples/graph-path.json) as a format reference. For real work, supply actual observations, locators and computed byte digests.

- `schema_version`: integer `1`; `synthetic`: explicit boolean.
- `required_demands`: a nonempty array of distinct graph node IDs. Each must have at least one declared route. Empty scope and missing/empty `paths` never pass.
- `paths`: nonempty array of route objects with a distinct nonempty `id`. All submitted routes are requirements: a second passing route does not cancel a gap in the first. An optional nonempty `comparison_id` can link a route to another inspector; this standalone checker does not resolve that external identifier.
- `roles`: an object mapping **each of the seven exact role names below** to a distinct graph node ID. Unknown role keys are invalid. Missing nodes or roles, a collapsed pair of roles, or a `blocked`/`superseded` participating node produces a gap. Other declared statuses are permitted because this is a route check, not a completion claim.
- `assessment`: `{ "independent": true, "allowed_support": "...", "answer_conditions": "..." }`. Both strings must be nonempty. Missing conditions produce a gap; an explicit `false` does not supply the independent-assessment role. These are task-design declarations; no unaided learner result is inferred.
- `provenance`: an object keyed by all seven roles. Each entry contains nonempty `path`, `sha256`, `locator`, `revision` and `origin` strings. `sha256` must be 64 lowercase hexadecimal characters. The local file must be a regular readable file beneath `root`, with matching actual bytes. Absolute paths, parent traversal and symlink escapes are invalid. Missing files, directories, FIFOs or unreadable files cannot pass. `origin` records the claimed source/author location; it is not authenticated. Different role nodes may use different locators within the same file.

The exact role order is:

```text
source → demand → prerequisite → theory_explanation → coding_practice
       → independent_assessment → feedback
```

Each adjacent pair requires a **direct** edge in the current graph. `supports` and `informs` go from the earlier role to the later role. `depends_on` goes from the later consumer to its earlier prerequisite, preserving its stored dependency orientation. The report includes the actual edge direction, type and graph-array index. A reverse `supports`/`informs`, a forward `depends_on`, a `revises` edge, or an arbitrary transitive route does not satisfy the connection. Extra feedback cycles retain the legacy structural behavior and do not replace missing required connections. This rule specifies the new inspection contract; it does not relabel historical edges.

## Evidence boundary and controls

Role assignment and provenance are explicit reviewer declarations. The checker does not infer roles from a node's label, ID prefix or generic type; parse the file locator; verify the origin or revision; authenticate official sources; assess theory correctness, coding adequacy or difficulty; confirm reviewer independence; execute a notebook; observe learner work; measure timing; or discover omitted demands and dependencies. A new binding recorded with a new digest says which bytes are now being claimed; it does not approve the change. Obtain an actual current review separately.

The tests include the historical negative graph, an explicit specification whose required nodes are absent from that graph, a complete fictional route, removal of each role and adjacent edge, direction/type controls, an unrelated transitive route, an uncovered second demand, collapsed/inactive roles, missing assessment/provenance, stale/restored bytes, an unchanged neighboring file, invalid and unsafe bindings, malformed JSON/API inputs, and legacy structural/feedback-cycle compatibility. These finite controls establish the reported mechanical behaviors, not educational effectiveness.
