# Retrieval prerequisite: source comparison and prioritization

Teacher research record, 2026-11-11, written before editing the retrieval candidate. This records a source-based design decision, not student attainment or a new discovery approval. Only this file was created by this task; lesson files, the Git index and remote refs were not changed.

## Baseline and selected gap

The complete integrated notebook read for this comparison had 38 cells and SHA-256 `ca89cf21b31a82e51f083344f3d156e046ad1356d31c22ffd87607aeeddd4551`. The existing axes/ID bridge had SHA `09efa4d1a8ebf918dab7fc0b30f60f8130e817729d70cfe93cd7c60f15b5767f`; the ten-week plan had SHA `cbe69f862ae76a87cd69233889c7fd6698e38ac34eb4d385f2b825722daeabb5`.

The integrated lesson already connects categorical grids, meaningful feature counts, two-feature class centres, squared distance, actual fitting, a training-data perturbation, validation and physical CSV re-reading. Its new independent panel problem changes channel/code meanings. Repeating that pathway is not the selected improvement. The reference panel solution still reproduces the worked training matrix `[[0,0],[2,1],[2,2],[4,3]]`; this limits the numerical transfer sampled by that reference path, without proving student failure or excluding other legitimate student features/models.

Bridge cells 13–17 already define query/candidate axes, `Q @ G.T`, maximum-score positions, arbitrary candidate IDs, joint row/ID permutations and a same-shape misalignment counterexample. Required B, cells 24–27, asks for a fresh score matrix and ID recovery. Its raw dot product is explicitly a synthetic scoring rule; it is not an incorrectly implemented cosine calculation. The actual missing prerequisite is **computing and comparing raw inner product, Euclidean distance and row-normalized inner product, then recovering the correct IDs on a new input**. A warning that normalization may matter does not provide that practice.

The selected change should replace/extend the existing retrieval B route rather than append two new units. Preserve mandatory bridge A, row/ID alignment and independent attempts, plus the old main notebook's Python, statistics, CSV, plotting, grouping/merging and dot-product tasks. Current discovery demand D05 remains broader than this numerical prerequisite: real encoding, official matching constraints and actual competition performance remain separate.

## Direct primary-source readings

| Source and reading extent | Evidence and applicability limit |
|---|---|
| [KOAI 2027 notice](https://kitpa.org/koai/2027), syllabus link and middle-school section; [linked domestic syllabus](https://kitpa.org/koai/syllabus), introduction and programming/ML/data-science/CV tables | The notice links a syllabus still headed **IOAI 2026**. It includes practical NumPy/tensors, feature engineering and CLIP, and distinguishes understanding from implementation. It does not prescribe cosine as a separate Week 1 topic. The domestic applicability of international 2027 changes is still unresolved. |
| [IOAI 2025 Restroom Icon Matching](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb), statement L19–114, path sorting L153–162, embedding/matching code L210–277 | International individual contest, not domestic middle-school past paper. The task requires the same restroom and opposite-gender counterpart, with independently shuffled query/gallery filenames. The supplied baseline normalizes embedding rows, multiplies query/gallery matrices, and reconnects positions to ordered paths/output. This supports a numerical prerequisite; the baseline is not a mandated or guaranteed optimal algorithm. The statement requires a trained model, while the shown encoder example is labelled zero-shot: this record does not claim that a toy matrix or that baseline alone fulfils every task requirement. |
| [CMU 36-462/662, Spring 2020, Lecture 24](https://stat.cmu.edu/~cshalizi/dm/20/lectures/24/lecture-24.html), representation §3 and distance/normalization §4–4.1.3, abstraction §5 | Gives Euclidean distance, norm, row length normalization and normalized inner product. It also requires reconnecting vector results to underlying items to assess whether a representation works. Use only small numerical principles here; its complete document-retrieval pipeline and statistical course are not Week 1 requirements. |
| [MIT 6.0001, Fall 2016, Lecture 7](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/resources/mit6_0001f16_lec7/), PDF pp.3–11 and 17 | Undergraduate introductory programming notes connect specifications, expected input/output pairs, boundary cases, independent black-box checks and integration. Supports hand expectations and counterexamples alongside executable code; tests do not prove all inputs correct or demonstrate learning. |
| [Cornell CS1110, Fall 2019 definitions](https://www.cs.cornell.edu/courses/cs1110/2019fa/materials/definitions/), function specification, sequence, test-case/unit-test entries; [Fall 2026 course description](https://www.cs.cornell.edu/courses/cs1110/2026fa/info/CS1110.pdf), p.1 | Separates a function's meaning/preconditions from its implementation and defines a test case by inputs plus expected output. These are college programming sources adapted to a small middle-school exercise, not evidence that the full college course fits this lesson. |
| [IOAI 2026 Find the Order, pinned statement](https://raw.githubusercontent.com/IOAI-official/IOAI-2026/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md), full 106 lines, especially L55–79 | `P[i]` is chunk_i's chronological rank, not the list of chunk IDs in playback order. The official illustration's playback order `[1,2,0]` requires `[2,0,1]`. Filenames encode shuffled IDs; hidden evaluation removes answers. This is an international individual task, not a domestic middle-school past paper. Real audio reconstruction is deferred. |

The Stanford IR-book pages attempted in this round timed out and were not used as newly verified evidence. The Restroom `main` URL is mutable; Find the Order is pinned to commit `e1963801aa4cf33a5a03520b39fa6620a7894c54`.

## Minimal mathematical and code chain

Start with provided finite, dimensionless feature vectors whose coordinate meanings and order match. Distinguish three rules before executing them:

- Inner product: `sum_j q[j]*g[j]`, choose the largest score. Magnitude can affect the result.
- Squared L2 distance: `sum_j (q[j]-g[j])**2`, choose the smallest distance. Taking its square root preserves the ordering.
- Norm: `||v|| = sqrt(sum_j v[j]**2)`. For nonzero rows use `v_hat = v/||v||`; normalized inner product is `q_hat @ g_hat`, also called cosine similarity. No trigonometric derivation is needed for this small calculation.

Relate each sum to one query/candidate pair, then reuse `Q_hat @ G_hat.T` and the candidate-ID lookup. Explain why row lengths have shape `(n,1)` when broadcasting over features. These are different scoring choices, not a universal claim that normalization improves accuracy; cosine is not a calibrated probability. Positive rescaling of a nonzero row leaves its direction/cosine unchanged. Define a zero-vector policy before division.

Independent synthetic arithmetic was executed in memory with NumPy, without running/writing lesson notebooks:

| Given inputs | Raw inner product | Squared L2 distance | Row-normalized inner product and resulting IDs |
|---|---|---|---|
| `Q=[[1,0],[0,1]]`, `G=[[3,4],[1,0]]`, candidate IDs `[42,7]` | `[[3,1],[4,0]]`, IDs `[42,42]` | `[[20,0],[18,2]]`, IDs `[7,7]` | `[[0.6,1],[0.8,0]]`, IDs `[7,42]` |
| New input `Q=[[3,4],[0,3]]`, `G=[[4,3],[1,0],[0,2]]`, IDs `[90,8,53]` | `[[24,3,8],[9,0,6]]` | `[[2,20,13],[16,10,1]]` | `[[0.96,0.6,0.8],[0.6,0,1]]`, IDs `[90,53]` |

The first example has different winners under the three rules. Multiplying its second candidate by positive 10 preserved all cosine scores. Jointly permuting the second example's candidates and IDs preserved the matched IDs. A zero row was explicitly rejected in the audit helper. These are finite synthetic design checks, not an official-data benchmark or student results. Candidate exercises should not reuse the displayed expected answers as their independent assessment.

Require an independent attempt to predict norms, every score, the selected position and actual ID before code. Then change candidate lengths/order and include a zero row or an explicit nonzero precondition. A helpful error diagnosis is to contrast normalization over each row with division by one global scalar or by columns. Give feedback on the first wrong correspondence or denominator, then use another new input. Keep exact matches for IDs and appropriate floating comparison for calculated scores.

## Zero vectors and Week 2 boundaries

**Do not insert unit normalization indiscriminately into the existing plant classifier.** Its P01 input is `[0,0]`, so its Euclidean norm is zero and it has no unit direction. Also, dividing water by a fixed 10ml reference, changing a feature's relative scale and dividing each whole vector by its norm are different operations. Keep the retrieval example's nonzero, dimensionless vector contract separate from that classifier.

Week 2 already teaches train-only mean/standard-deviation standardization, min/max scaling and categorical handling. Standardization uses a training column's centre and spread; min/max uses training column extrema. Row normalization uses one currently available row's own length and does not itself estimate training population statistics. A new validation row's norm is not automatically information leakage. Reuse the Week 2 distinction instead of teaching another full preprocessing pipeline in Week 1.

## Comparison with inverse-rank transfer and later placement

Inverse rank remains a valuable new output-contract assessment. In a separate synthetic illustration, playback order `Q=[2,0,3,1]` corresponds to ranks `P=[1,3,0,2]`, satisfying `P[Q[r]]=r`. Both arrays pass length/range/uniqueness checks, so format alone cannot detect the wrong meaning. Class-position-to-label decoding, ID alignment and inverse permutations share the need to preserve a declared relationship but are not the same conversion algorithm.

For this iteration, retrieval normalization has the clearer missing principle/practice within an already mandatory bridge route. Inverse rank introduces another task/output definition; adding both as full new units would increase load. Defer the full inverse-rank exercise to audio/new-contract work, or retain it only as a short uncompleted transfer diagnostic. Do not claim the normalized search exercise has fulfilled it. Actual Whisper/audio ordering belongs in Week 9 and new-specification submission in Week 10.

The numerical retrieval prerequisite connects to Week 3 losses/distances, Week 4 neighbours and metric choices, Week 5 geometric representations, Week 6 tensor/matrix operations, and Weeks 7–9 actual encoders/CLIP/retrieval. It does not bring model training, normalized embedding quality, identity/gender constraints, matching optimisation, masks, softmax or all deep-learning topics into Week 1. Existing broad D05 and other discovery demands must remain open where unfulfilled; the new lesson bytes will need their own review rather than inheriting the old candidate's approval.

## Burden and unobserved evidence

This is a replacement/extension of search B, not two new units. Even so, vector length, three selection rules, axis-specific division and zero-vector policy add conceptual work. The old 120-minute class and 5–7-hour self-study allocation do not measure this version. Student time, help, independent answers, retention and transfer are unobserved; no new time-saving or mastery claim is justified. Observe prediction/hand-calculation/code/debugging/retest time and assistance separately before deciding whether the remaining work fits Week 1 or needs later scheduling. At the inspected state Weeks 3–10 were planned rather than actual lesson notebooks; a prerequisite link is not evidence those later lessons or outcomes are complete.
