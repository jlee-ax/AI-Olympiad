# Week 02 expansion: source and prerequisite prioritization

Date: 2026-11-11. Reviewer: `/root/gap_prioritization`.

This is a teacher-facing design record, not a student lesson, assessment, execution receipt, or finding of learner achievement. It records the pre-expansion materials read during this investigation; concurrent edits require a fresh comparison. All duration estimates below are unmeasured planning estimates and belong only in this teacher record, not in student materials.

## Existing content and actual gaps

The reviewer directly read:

- `reviews/course-reconstruction-20261111/independent-ten-week-source-audit.md`, including the ten-week prerequisite map and its original proposal to author Week 02 first.
- `reviews/course-discovery-20261111/review.md`, `new-demands.json`, and the original D/H demand payloads and comparison summaries in the discovery reports.
- All 25 cells of `lessons/week02/week02_prediction_evaluation.ipynb`, all 29 cells of `lessons/week01/week01_axes_linear_bridge.ipynb`, `lessons/week02/teacher-notes.md`, and the relevant weekly and topic requirements in `curriculum/student-plan.html`.

Week 02 already teaches prediction-time availability, group splitting, known-label training, train-only imputation and standardization, unknown versus negative labels, confusion matrices, undefined denominators, row versus group averages, and a new-input independent task (cells 2–21). Recreating that flow is not the next priority. Week 01 already supplies dot products, matrix multiplication, position-to-ID recovery, and lookup examples.

The concrete omissions in the pre-expansion Week 02 are in cell 22: median imputation, one-hot encoding, MinMax scaling, forward-fill, and sliding-window features are instructions to perform work, without a connected worked explanation, implementation, independent task, and feedback. Cells 22–24 state F1 and print ROC coordinates, but do not draw the curve or provide a separate independent ROC task. Existing group averaging does not fulfill H01's truth-dependent weights, full denominator, and metric-dependent ranking. D06's remaining assessment dimension is leakage versus overfitting; its existing train-only-fit teaching need not be repeated.

## Original sources directly checked in this investigation

Web locations are the ranges returned during the 2026-11-11 reads, not immutable upstream revisions. `stable` and GitHub `main` may change. These readings support bounded claims, not completeness of the external syllabus.

| Source and read extent | Supported claim and limit |
|---|---|
| [KOAI 2027 announcement](https://kitpa.org/koai/2027), lines 94–100, 147–165, 218–234; [linked domestic syllabus](https://kitpa.org/koai/syllabus), lines 74–85 and 119–132 | The domestic page remains labelled IOAI 2026; the 2027 announcement links it and specifies written and coding coverage for middle-school entrants. Feature engineering and preprocessing include windows, statistical features, one-hot, imputation, splitting, and scaling. Their practical O does not create a separate official theory O; explanatory principles are a teaching prerequisite. This does not establish domestic adoption of every international 2027 change. |
| [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), opened page and returned section 12.2 excerpt on learned preprocessing | Learned transformations use training data; Pipeline helps preserve the boundary. A finite code example or high score does not establish absence of leakage or learner understanding. |
| [Lagged features official example](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html), lines 390–405, 481–509, 719–721 | The example shifts past observations before rolling statistics and compares shuffled with time-based evaluation. It does not prove that every use of context across a chronological boundary is forbidden. Availability of past context, learned fit state, and the declared evaluation unit are separate decisions. |
| [Preprocessing guide](https://scikit-learn.org/stable/modules/preprocessing.html), lines 75–132 and 305–355 | Feature-wise standardization differs from sample-wise unit-norm normalization. Arbitrary category codes can introduce an unintended order. Unit-norm normalization is a later bridge to similarity, not an immediate requirement to implement all of D05 in Week 02. |
| [MinMaxScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html), lines 635–751; [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html), lines 692–734 and 803–821 | With default `clip=False`, held-out values may transform outside the training range. Unknown categories raise by default; `ignore` produces zero entries for that feature. These are explicit policies, not evidence that an unseen category is a known class or a missing target. |
| [ROC API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html), lines 648–685 | ROC accepts positive-class probability estimates or unthresholded decision scores. Predictions use score >= threshold. A value between zero and one is not, by itself, evidence of probability calibration. |
| [IOAI 2025 Radar](https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Radar/Radar.ipynb), lines 69–159, especially section 5 | Background truth has weight 1 and other truth has weight 50; normalization uses the maximum possible weighted score. This is a past international task contract, not a forecast of KOAI 2027 middle-school questions or a model-selection recipe. |
| [Stanford CS229 model-selection notes](https://cs229.stanford.edu/notes2020spring/cs229-notes5.pdf), PDF pages 1–3 | Selecting by training error can favor excessive complexity; hold-out and CV compare candidates on held-out examples. The notes' random split and example percentages are not prescriptions for repeated entities or time series. The university treatment supplies principles, not a validated workload for this audience. |

## Production priorities

Preserve the existing main-lesson flow. Turn the existing self-study scope into teachable units rather than adding unrelated model families or only appending another example. The estimates below describe possible replacements for the existing task lists, not demonstrated additional capacity within the class or the planned self-study hours.

| Priority | Connected learning and independent evidence | Placement and estimated burden |
|---|---|---|
| 1. Causal time features | Define prediction time and available history; sort within entity; explain past-only fill; construct a window; calculate mean/std; retain row IDs and source dependencies. Explain, predict by hand, implement, and compare. An independent input changes row order, entity boundaries, leading missing values, and future observations. Require evidence that changing unavailable future values cannot change an earlier feature. | Week 02 feature/preprocessing self-study, about 60–100 minutes; then Week 03 regression and Week 09 segment features. |
| 2. Stable feature representation | Explain median, MinMax versus standardization, training state, category vocabulary, output feature names/order, and unseen-category policy. Use hand calculations and explicit library outputs. Independent inputs include a training-range violation, a new category, and a same-shape feature-order error. Distinguish feature categories from unknown target labels. | Week 02 preprocessing self-study, about 70–110 minutes; supports Week 04 distances/SVM, Week 05 PCA, and Week 08 vocabulary fit. |
| 3. Score to decision to metric | Distinguish a real-valued score from a hard prediction; connect thresholds to the confusion matrix, F1, TPR/FPR, and an actual ROC plot. Use a new independent score table with ties and an explicit positive label. Require both intermediate counts and the plot, not copied coordinates. | Week 02 metric self-study, about 45–75 minutes; continue with Week 04 logistic outputs and validation-based threshold selection. |
| 4. Weighted evaluation contract | Develop weighted averages from the correctness indicator, truth-dependent weight, and the full possible denominator. Compare two predictions whose accuracy and official weighted-score rankings differ. Use new inputs for independent calculation and code, followed by denominator-specific feedback. Existing row/group averages are prerequisites, not substitutes. | Week 02 evaluation extension or Week 10 contract reading, about 25–40 minutes. Preserve original H01 breadth. |

For D06, add a compact independent diagnostic contrasting (a) fitting a scaler on validation inputs, (b) fitting only on training data but generalizing poorly, and (c) legitimate validation-based candidate selection. Ask which evidence or code path supports each conclusion; scores alone do not identify the cause. Full under/overfitting curves remain in Week 03, and fold-specific Pipeline fitting remains in Week 04.

Every unit should retain a pre-execution explanation and intermediate values, the learner's code, the first differing stage, help received, targeted feedback, and a different input for rechecking. Teacher answers must not be treated as independently hidden merely because they are in another public-repository file. No student performance, time, or mastery was observed in this investigation.

## Remaining ten-week work and scope boundaries

- D01: preserve existing axis work; assess model input/target and higher-dimensional transfer in Weeks 06–09.
- D02: complete distance, feature-axis reduction, neighbor selection, nonconsecutive labels, ties, and invalid k in Week 04.
- D04: label/index round-trip in Weeks 04 and 06. D05: norm, cosine, ID recovery, and task-specific matching constraints in Week 09.
- D07–D09: embedding vocabulary versus sequence axes, masking participation, softmax, and loss need the planned prerequisites in Weeks 06 and 08; do not force them into introductory Week 02.
- D10: preserve small-input reasoning throughout; numerical gradient verification follows differentiation. D12 remains a separate Python diagnostic.
- H02: teach and assess inference without development-only APIs using local artifacts in Weeks 08 and 10; public/hidden labels alone do not resolve it.
- N02: image coordinate, area-budget, and output contracts belong in Week 07 and later transfer. N03: preserve introductory unknown-label semantics; a PU constant-alpha derivation is not justified as an immediate Week 02 addition. Its observation-model assumptions remain separate.
- D11: continue checking domestic/international version applicability. This investigation did not re-establish the full international 2027 PDF or its domestic adoption.

The original broad D/H/N requirements remain open unless a later comparison supplies evidence at their declared breadth. A source-backed design, executable teacher code, structural validation, independent learner work, and demonstrated transfer are different evidence levels. No actual hidden final test or subsequent Weeks 03–10 lesson was established by this review.
