# Evidence review

Reviewed 2026-11-10. This document distinguishes published observations from proposed transfers and local tests.
The starting point is Lauren Tan's pstack at the revision recorded in [pstack traceability](pstack-traceability.md).
No local experiment has established improved agent performance, better teaching, or an effective recurring cadence.
Repository validation checks structure and decision records; it does not validate research claims or educational quality.
Real lesson production and recurring execution remain outside the current implementation scope.
Official KOAI 2027 scope and learner prerequisites require separate confirmation.

## How to read the evidence

- **Claim** names the proposition under investigation, not an accepted conclusion.
- **Source result** reports a particular version, population, model, task and metric.
- **Limit** states what that result does not establish.
- **Proposed transfer** is a hypothesis for this repository.
- **Local test needed** identifies evidence required before claiming that transfer works.

## E01 — Curated skills can help; skill creation is not itself learning

**Claim:** Reusable procedural packages can improve task completion.
**Source result:** [SkillsBench v4, 2026-06-14](https://arxiv.org/html/2602.12670v4) evaluates 87 tasks across 18 model–harness configurations.
Curated skills raise mean task-macro pass rate from 33.9% to 50.5% (+16.6 percentage points), with configuration gains from +4.1 to +25.7 points.
A separate self-generated condition scores 8.1–11.5 points below no-skills baselines on three configurations.
**Limit:** This is an optimistic, high-quality curated sample; low-signal tasks were filtered during construction.
The self-generated audit identifies discovery failures, creator/solver interference and incorrect assumptions; it does not isolate experience-derived skill quality.
The association between smaller bundles and better results is not a universal causal limit on skill count.
**Proposed transfer:** Preserve pstack's curated workflows and evaluate additions individually; do not reward the number of new skill files.
**Local test needed:** Compare pinned pstack with and without each candidate skill on matched unseen tasks; verify actual skill use in traces and include authoring cost.

## E02 — More repository instructions can add effort without useful improvement

**Claim:** Adding remembered instructions improves future work.
**Source result:** [Evaluating AGENTS.md v2, 2026-06-23](https://arxiv.org/html/2602.11988v2) studies four model configurations on 300 SWE-bench Lite and 138 CTXbench tasks.
Generated context files change success by -0.5 and -2 percentage points on average, neither statistically significant, while increasing cost by 20% and 23%.
Developer files average +2.4 points versus no context (p = .21), but outperform generated files.
**Limit:** Single completion per agent/task and coding-focused benchmarks; this is not evidence that every instruction is harmful.
The revised paper is more qualified than the earlier claim that context files generally reduce performance.
**Proposed transfer:** Keep only useful, non-redundant guidance; favor pstack's enforcement-first approach for mechanically checkable mistakes.
**Local test needed:** Compare a reminder, a reusable procedure and an executable check on a real prior failure plus neighboring valid cases.

## E03 — Reflection needs task-specific evidence and a fair comparator

**Claim:** Another critique-and-rewrite cycle improves the answer.
**Source result:** [Self-Refine v2, 2023-05-25](https://arxiv.org/html/2303.17651v2) studies seven tasks; GPT-4 code optimization rises from 27.3 to 36.0, while math accuracy changes only from 92.9 to 93.1.
It also reports competing quality dimensions and non-monotonic revision quality.
[Huang et al. v2, ICLR 2024](https://arxiv.org/html/2310.01798v2) find GPT-4 GSM8K accuracy falls from 95.5 to 89.0 after two intrinsic correction rounds; an oracle stopping signal instead yields 97.5.
They identify unequal inference budgets and stronger revision prompts as evaluation confounds.
[CRITIC v3, ICLR 2024](https://arxiv.org/html/2305.11738v3) reports improvements using search/execution feedback across question answering, mathematical program synthesis and toxicity reduction, with task-dependent outcomes and added latency.
[SCoRe v2, ICLR 2025](https://arxiv.org/abs/2409.12917v2) reports improved self-correction after multi-turn reinforcement learning on Gemini models.
**Limit:** Huang's older-model results do not establish a permanent inability of current models to self-correct.
SCoRe changes training; its results cannot be attributed to adding a reflection prompt or memory file.
**Proposed transfer:** Keep pstack's evidence-led critique; distinguish an improved artifact from a reusable lesson.
**Local test needed:** Compare reflection with equal-budget fresh attempts and tool-grounded correction, measuring regressions as well as fixes.

## E04 — Executable reuse and feedback can help in observable environments

**Claim:** Verified procedures and failure memories transfer beyond their original attempt.
**Source result:** [Voyager v2, 2023-10-19](https://arxiv.org/html/2305.16291v2) stores executable Minecraft skills; it discovers 63 unique items within 160 prompting iterations and its no-library ablation plateaus later.
The experiments use three runs, an automatic curriculum and environment feedback.
[Reflexion v4, NeurIPS 2023](https://arxiv.org/html/2303.11366v4) improves HumanEval Python from 80.1% to 91.0% but reduces MBPP Python from 80.1% to 77.1%.
On 50 difficult HumanEval Rust problems, reflection without test generation scores 52%, versus 60% baseline and 68% for the full method.
**Limit:** Final submitted accuracy after iterative work is not single-call accuracy; faulty self-generated tests can select incorrect answers.
Neither study establishes learner understanding or indefinite improvement across a teaching skill library.
**Proposed transfer:** Investigate reusable production/checking procedures separately from pedagogical judgments.
**Local test needed:** Require successful application to a new related task and test a case where reuse should be rejected.

## E05 — Incremental context updates are promising, not self-validating

**Claim:** A maintained playbook can accumulate useful experience without losing earlier knowledge.
**Source result:** [Agentic Context Engineering v3, 2026-03-29](https://arxiv.org/html/2510.04618v3) uses identified entries, incremental updates and deduplication.
With DeepSeek-V3.1 in all roles, offline AppWorld adaptation raises the paper's aggregate metric from 42.4 to 59.4.
A full-rewriting case collapses from 18,282 context tokens to 122 and loses accuracy; harmful updates every iteration also drive a FiNER experiment below baseline.
**Limit:** Reported deduplication sensitivity is on FiNER; it does not establish a universal merge threshold or safe automatic deletion policy.
**Proposed transfer:** Test small, source-linked revisions to pstack knowledge instead of repeatedly replacing the entire record.
**Local test needed:** Measure lost evidence, false merges, stale guidance, negative transfer and maintenance cost under successive corrections.

## E06 — Memory has accuracy, efficiency and maintenance tradeoffs

**Claim:** An evolving memory store is better than searchable original evidence.
**Source result:** [LongMemEval v2, ICLR 2025](https://arxiv.org/html/2410.10813v2) contains 500 questions covering extraction, multiple sessions, time, updates and abstention.
In one large-history, round-level setting, raw text plus fact keys improves Recall@10 from .692 to .784 and GPT-4o QA from .670 to .720.
Replacing raw content with compressed representations can lose information.
[Mem0 v1](https://arxiv.org/html/2504.19413v1) reports LoCoMo judge scores of 66.88 for memory, 68.44 for graph memory and 72.90 for full context.
Corresponding response p95 latency is 1.440s, 2.590s and 17.117s; its headline relative improvement uses a different baseline.
[A-Mem v11](https://arxiv.org/html/2502.12110v11) improves some temporal results, but GPT-4o single-hop F1 is 48.43 versus 61.56 for its LoCoMo baseline.
**Limit:** Benchmarks, models and metrics differ; these numbers cannot rank all stores.
Mem0 uses ten conversations and excludes adversarial/unanswerable questions; answering-context savings do not establish whole-lifecycle savings.
Correct retrieval does not prove correct physical deletion, deduplication or procedural improvement.
**Proposed transfer:** Retain raw evidence and scoped live-state recall; compare simple search, derived notes and linked memory.
**Local test needed:** Use paraphrased duplicates, changed facts, conflicting sources and similarly named concepts; score obsolete answers and false merges.

## E07 — Evaluation is a measurement problem

**Claim:** A positive model review or passing test proves the intended improvement.
**Source result:** [MT-Bench/Chatbot Arena v4, NeurIPS 2023](https://arxiv.org/html/2306.05685v4) reports over 80% agreement with human preferences in its setting, alongside position, verbosity and self-enhancement biases.
[Are “Solved Issues” Really Solved? v2, 2025-09-09](https://arxiv.org/abs/2503.15223v2) finds 7.8% of evaluated patches counted as correct while failing developer-written tests.
Of plausible patches, 29.6% behave differently from references; 28.6% of that divergent subset were certainly incorrect on manual inspection.
[The Reusable Holdout, 2015](https://www.cis.upenn.edu/~aaroth/reusable.html) explains the statistical risk of adaptively reusing evaluation data.
**Limit:** Different behavior alone is not incorrectness; different model families do not guarantee independent judgments.
A rubric hidden from candidates can still become an optimization target through repeated feedback.
**Proposed transfer:** Extend pstack's existing blinded evaluation with calibrated judgments and fresh transfer cases.
**Local test needed:** Reverse output order, seed known errors, compare educator ratings, record evaluator versions and reserve untouched assessment cases.

## E08 — Self-modification is demonstrated under bounded conditions

**Claim:** An agent can improve its own implementation through evaluated changes.
**Source result:** [Darwin Gödel Machine v3, 2026-03-12](https://arxiv.org/html/2505.22954v3) runs 80 iterations with a frozen foundation model and an archive of agents.
Its SWE-bench improvement from 20% to 50% concerns a 200-task Verified subset with staged evaluation; the reported run cost is about USD 22,000.
Full Polyglot improves from 14.2% to 30.7%, and cross-benchmark transfer provides additional evidence.
**Limit:** The outer exploration machinery stays fixed; execution is sandboxed and monitored.
A separate hallucination experiment finds an agent bypassing the detector through logging changes.
**Proposed transfer:** Treat proposed skill/code changes as experimental candidates, with inspectable lineage and evaluation outside their editable scope.
**Local test needed:** Measure unseen-task improvement, evaluator integrity, regressions, compute and human review cost; no 30-minute guarantee follows.

## E09 — Long-running research exposes repetition and stagnation

**Claim:** Durable records and autonomous critique prevent wasted cycles.
**Source result:** [AutoResearch at Production Scale v1, 2026-09-24](https://arxiv.org/html/2609.30541v1) reports 12 weeks and 220+ experiments on two book-recommendation systems.
Observed failures include repeated rejected ideas, stagnation, infrastructure faults, unequal iteration costs and metric fixation.
**Limit:** One organization/domain, observational sequential interventions and offline metrics; System B's strategic redirects and memory maintenance were human-led.
The reported gains do not isolate a general causal advantage of its architecture.
**Proposed transfer:** Preserve rejected hypotheses and revisit reasons; count an evidence-backed no-change outcome as informative.
**Local test needed:** Check whether a restarted session avoids a known failed idea, and whether additional cycles improve outcomes beyond noise and cost.

## E10 — A graph is a hypothesis about retrieval and impact, not a quality guarantee

**Claim:** Graph structure improves synthesis and identifies all affected work.
**Source result:** [GraphRAG v2, 2025-02-19](https://arxiv.org/html/2404.16130v2) studies 125 global questions per corpus over roughly 1.0M/1.7M tokens.
Global methods outperform conventional vector retrieval on comprehensiveness/diversity; claim-based comparisons find no significant difference among global methods and text map-reduce.
One reported indexing run takes 281 minutes.
**Limit:** LLM-based evaluation, specific corpora and global questions; no proof that a graph removes hallucination or captures every dependency.
**Proposed transfer:** Use explicit relationships for traceability while comparing retrieval and impact analysis with simpler records.
**Local test needed:** Evaluate missed dependencies, unnecessary rechecks, source fidelity and indexing/maintenance cost.

## E11 — Provenance and incremental builds provide formal analogies

**Claim:** Versioned dependencies and evidence links improve the reliability of handoffs.
**Source result:** [Build Systems à la Carte: Theory and Practice, JFP 2020](https://simon.peytonjones.org/assets/pdfs/build-systems-jfp.pdf) models dependency/rebuilding choices.
[Why and Where, ICDT 2001](https://doi.org/10.1007/3-540-44503-X_20) distinguishes source influence from source location.
**Limit:** These are software/data-provenance results, not educational-agent efficacy studies.
**Proposed transfer:** Record input, skill and artifact versions; distinguish supporting evidence from a location link.
**Local test needed:** Change an input and verify the correct downstream records become review candidates without claiming complete dependency discovery.

## E12 — Teaching evidence does not establish agent-cycle effectiveness

**Claim:** Interleaved practice may benefit future course design.
**Source result:** [Rohrer et al., JEP 2020](https://doi.org/10.1037/edu0000367) compares interleaved/blocked practice in 54 seventh-grade classes over four months.
One month later, unannounced-test scores are 61% versus 38%; an accessible [paper copy](https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf) preserves the original study.
**Limit:** Mathematics instruction, not KOAI lessons or agent scheduling; learner level and task selection matter.
**Proposed transfer:** Consider mixed retrieval practice and delayed assessment when lesson work is separately authorized.
**Local test needed:** Confirm learner prerequisites and competition scope, then measure learning rather than treating artifact scores or simulated students as learner outcomes.

## Local investigation priorities

| Question | Comparator and observation needed |
| --- | --- |
| Does a change help? | Pinned pstack versus pstack plus one candidate; same model, inputs, tools and resource allowance. |
| Is the benefit durable? | Original failure plus unseen related and unrelated tasks; retain regressions and inconclusive results. |
| Does memory earn its cost? | Raw search versus notes versus linked notes; include writing, retrieval, review and recovery costs. |
| Is “no change” valid? | Seed duplicate/rejected proposals; check that existing evidence can justify no new edit or PR. |
| When should work stop or pause? | Compare bounded campaigns; record completion, missing evidence, budget and repeated failure by cause. |
| Is evaluation trustworthy? | Blinded order reversal, known-error detection, educator calibration and fresh holdouts. |

The requested 30-minute interval is a preference for future investigation, not a demonstrated optimum or an active schedule.
Quality thresholds, stagnation counts, retention periods and promotion rules remain unset until justified for local use.
A decision record is a recommendation about work; it does not execute work or grant authority.
