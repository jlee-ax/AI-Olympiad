# Week 1 competition-depth candidate review

## Exact revisions and scope

- Baseline: remote lesson branch commit `8d341af794165da77c3b4d1545c9d0d651882dea`; notebook SHA-256 `602c0c4e04e7208b0b082d9e4e7d4be384e1371f67c5f211d931911367d02eb0`.
- Candidate notebook SHA-256 `2506059c43a95f3e00e1fe868650bda1462afbfe277b18fb633e61d260f0b5d8`; teacher notes SHA-256 `56705451b759c5812d6987bfaa76765c165a8a3b299062c575dc0dca03d2b5bc`. The exact executed notebook, environment, code-cell count and outputs are in `lessons/week01/validation.json`.
- Supplementary skill and inspector: `codex/koai-contest-depth-20261110` commit `64f24aabdad2b1976740d88d4a0ba74a4ed89766`. The [baseline review](baseline-review.md), [baseline comparison](baseline-depth.json), [candidate comparison](candidate-depth.json) and their inspector outputs are separate records.

## Sources and status

Directly consulted [KOAI 2027 rules](https://kitpa.org/koai/2027), the [linked syllabus](https://kitpa.org/koai/syllabus), the [2026 sample notice](https://kitpa.org/files/36) and [sample PDF](https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf): multiple-choice questions 2, 6 and 24 and written question 2. The sample is an official high-school-standard learning example, not a verified 2027 middle-school past paper; a complete official answer key is not published. The 2027 page links a syllabus labeled IOAI 2026. [StandardScaler documentation](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) was read for training statistics and the handling of zero variance.

## Findings and response

1. The prior notebook's four written prompts differed from the course plan's two multiple-choice items and one short response. `cell:71068cea` now uses that format; teacher notes contain keys and explanations. The tool compares manually recorded counts, not an automatically parsed notebook.
2. Existing reshape/transpose exposure did not ask learners to distinguish two same-shape outputs. `cell:depth-reshape-compare` asks for predictions, a counterexample and axis mapping. New variable names preserve earlier `A` and `B`. This is a NumPy foundation, not a claim that the PyTorch sample is mastered.
3. Existing code work mainly modified supplied procedures. `cell:depth-function-spec` asks for a small implementation from an input/output contract, with zero, missingness, empty input and input immutability. Its numerical domain is bounded; the teacher solution and cases are separate from the notebook but the repository itself does not make them secret.
4. `cell:9ce91662` relates translation, scale, variance, units and standard deviation to later preprocessing; the learner must reason about changed values. The graph's range and unit/legend instructions were clarified.

The `candidate-inspection.json` result is `uncertain`, not an aggregate pass: revised homework duration and actual classroom timing are not estimated or observed, and learner independence or learning is not observed. The prior K01–K16 review was bound to the old notebook; this supplementary review does not rebind or pass those stale checks.

## Independent review and tests

A separate GPT-6.1 Terra Max reviewer inspected the exact notebook and teacher notes, recomputed the changed quiz, array outputs, function cases and variance claims, and verified the source/attachment projection and the saved execution receipt. The reviewer identified and the author corrected: variable collisions with prior cells; unbounded finite inputs that could overflow the teacher function; ambiguity about which data to rescale; an imprecise square-root explanation; chart-boundary and unit-label risks; and the outdated homework-scope description. Different reviewer identity/model does not prove calibrated or independent educational judgment.

`check_depth.py` recomputes the actual quiz snippet and array mapping, checks the teacher function on edge cases and 150 seeded inputs against an independent reference, checks variance transformations with exact fractions, and confirms the teacher key is absent from notebook and HTML text. It does not establish that a learner solved anything. `tools/validate.py` reports the candidate graph structurally valid; it cannot establish semantic completeness.

The fresh in-process Jupyter kernel executed all 27 code cells without error, including two empty student exercise cells, and the generated HTML was refreshed. A separate-process kernel attempt failed before cell execution because local network interface/ZMQ operations were not permitted; it is not reported as a pass. All five saved plot images and two embedded diagrams were viewed, including the changed graph. HTML text was checked for new content and teacher-key absence. A browser screenshot of the local HTML was not obtained because the browser security policy disallowed the `file:` URL; visual HTML layout remains unverified. The source and attachment projection was unchanged by the successful execution.

The class ledger still totals 120 minutes, but this is planning arithmetic rather than observed feasibility. The earlier 5–7-hour self-study range predates the new tasks and cannot be treated as a current estimate. No real learner responses, educator calibration, outcome improvement, full contest readiness, main merge or recurring schedule are asserted.
