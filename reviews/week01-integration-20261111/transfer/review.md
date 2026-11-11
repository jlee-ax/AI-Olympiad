# Independent transfer probe: Robot Chasing

The source-led synthetic audit matched all 25 frozen expectations. This shows that the reviewer reproduced the selected schema counterexamples; it is not learner achievement, Robot action accuracy, or a pass of the integrated lesson.

## Source and freeze

The official IOAI 2026 international task is [Robot Chasing](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md), not a domestic middle-school past paper. After reading live main, the reviewer resolved and reread commit `e1963801aa4cf33a5a03520b39fa6620a7894c54`, file blob `f45b6bee1620d337eeaded43798df34a8413f2bd`. Full pinned lines 1–134 were read; the web view collapses blank lines. URL, retrieval time and locations are in `source-reading.json`.

The fixture and expected checks were written before reading the new integrated candidate. The scene is newly authored and deliberately asymmetric. No official samples, learned model, movement policy, shortest-path rule or action-correctness labels were used. Output values [0,5,2] are arbitrary format/lineage markers.

## Expected and actual checks

Run from the repository root:

```sh
python3 -B reviews/week01-integration-20261111/transfer/run_robot_contract.py
```

The run used Python 3 and NumPy 2.3.5. All expected and observed values, environment details, fixture and script hashes are saved in `robot-contract-results.json`. Results are written only in this transfer directory.

| Probe | Frozen expectation | Observed |
|---|---|---|
| Valid asymmetric grid | Shape [8,8,2]; cell [2,5] is [10,2]; interior shape [6,6,2] | Matched |
| Row/column exchange | Shape/schema still pass, but cell [2,5] becomes [6,0] and fails the coordinate oracle | Matched |
| Direction as another channel | An appended direction channel fails the original shape contract | Matched |
| Direction overwrites colour | In-range values and shape can pass; the frozen cell oracle detects [10,3] instead of [10,2] | Matched |
| Meaningless colours | Recolouring empty/wall cells preserves the meaningful grid and red-ball location [5,2]; naive red-colour count changes 1→61 | Matched |
| Prediction-time fields | No label/previous-action key; row permutation preserves rowwise probes but changes fabricated previous-row context | Matched |
| Output format | Integer markers round-trip; wrong length/type/range/container are rejected | Matched |
| Output lineage | Reversed markers still pass format but fail the separate order oracle | Matched |

The remaining normal cases verify separately supplied direction/carrying and a joint row permutation. The colour invariant concerns representation semantics, not an assertion that an arbitrary trained policy has invariant predictions. The guard checks a declared subset of possible input constraints.

## Manual comparison with the integrated candidate

The reviewer first read candidate `09da87fd69d9a5c479c8e84e4e48f08b5d878b6830034f976dc0f8ca69f494f8`, then reread all 34 cells at `e39e609d3354f20ca5518b652be39f3b31ec0b16154d37651e33309b42a39a6b` after a concurrent edit. This latter SHA bounds the comparison in `lesson-comparison.json`.

- Cells 1–4 and 17 provide a local data dictionary and availability/target distinction. Robot needs fresh field-role decisions; its robot_id can distinguish robot-specific patterns, so the plant ID rule is not universal.
- Cells 9–12 supply a sound two-dimensional axis prerequisite and a same-shape counterexample. They do not explicitly assess a third semantic channel axis, the square-grid transpose, or channel overwriting.
- Cells 5–9 explain numerical meaning and units. Robot object/colour categories and ignored wall/empty colours require another contract reading, not an unqualified transfer of numerical averages.
- Cells 25–29 teach local output and order checking. Robot's integer JSON list and absent history are different contracts; the current independent exercise remains a table/CSV classification task.

These are limits of explicit transfer evidence, not demonstrated errors in the integrated local example or proof that learners cannot generalize. A short follow-up probe can ask for an axis/field table, one coordinate prediction, a same-shape counterexample and an output-contract comparison. Full Robot policy learning belongs to later work and is not required to use this probe.

No student response, assistance level, retention, classroom time, official dataset result or contest submission was observed. No lesson or Git index was modified by this audit.

