# Preparing KOAI evaluations with NVIDIA SkillEvaluator

The five skills each have three **public development cases** in `skills/<name>/evals/evals.json`. One asks for ordinary role work, one introduces a fault, and one should leave the role unused. The files include their answer keys. They exercise the integration and can be studied by authors. Reserve different, independently reviewed questions for performance claims.

| Skill | What the two role-specific cases exercise |
|---|---|
| ground | Reconcile the competition year with a syllabus snapshot and correct a double-counted time allocation. |
| recall | Find the active synthetic handoff record and trace the superseded record without deleting history. |
| orchestrate | Return the actual checkpoint and exhausted-budget decisions of the advisory controller. |
| evaluate | Follow a NumPy view, copy and saved sum on a fresh Week 1 input. Correct a Week 2 train/validation leak. |
| reflect | Distinguish repeat incidents across runs from two reports of one incident. |

## Setup and commands

Use Python 3.12–3.14 and the [official NVIDIA source at the tested revision](https://github.com/NVIDIA/SkillEvaluator/tree/e3ede733f4d57578a1630b0579ea236b8cf8a727). In a separate checkout, check out that revision and run `uv sync --frozen --no-dev --no-editable --extra all`. Activate its virtual environment, then run these commands from this KOAI checkout. The adapter verifies the installed Python source fingerprint and reports the package version. Existing KOAI tools and their standard-library tests retain their existing entry points.

```sh
skillevaluator validate skills/koai-evaluate --tiers 1 --no-llm -r json -o /tmp/koai-t1
python tools/skill_evaluation.py check koai-evaluate --pilot
python tools/skill_evaluation.py prepare koai-evaluate /tmp/koai-pilot --pilot
```

Tier 1 uses NVIDIA's configured security scanners. If SkillSpector is installed but its child process cannot locate it, set `SKILLEVALUATOR_SKILLSPECTOR_PATH` to that verified executable. Check the native report's scanner statuses and publication status. Tier 2 uses a configured embedding provider. With that provider available, run `skillevaluator similarity-check skills --save-catalog /tmp/koai-catalog.json`, then `skillevaluator tier2 skills/koai-recall --catalog /tmp/koai-catalog.json`. A similar description is a prompt for investigation. Selection accuracy requires actual trigger observations.

`check` runs the installed NVIDIA strict validator and native coverage policy. The project additionally requires an actual nonempty canonical Agent Skills JSON dataset, distinct IDs and prompts, expected answers, observable assertions, typed answer fields and all three control types. Missing data can produce native exit 0. The project returns nonzero for that case, including with `--pilot`. The public sets have three distinct cases per role. The pinned native coverage subcheck requires ten and at least one non-trigger. `--pilot` permits technically valid provisional inputs and reports `provisional`. Without it those inputs exit nonzero.

`prepare` exclusively creates a new destination outside the working checkout. Its report records the tested skill bundle, native Python sources, cases, grader and common-input hashes. Keep the entire destination private. After a failure it may contain diagnostic inputs. A retry uses a fresh destination. Only `evidence: paired_task_preparation` confirms that both arms were built and checked.

## Inputs and grading

The explicit common file list in `tools/skill_evaluation.py` contains the curriculum snapshot, the Week 1 integrated and Week 2 temporal-preprocessing learner notebooks, a synthetic handoff, public worked-example material, repository tools and the references needed by those tools. Both native tasks receive identical common file bytes. Ground, recall, orchestrate and reflect can follow the evaluation guides they link to. When evaluating the evaluation role itself, its procedure and installed skill appear only in the treatment arm. The two curriculum JSON contracts retain their original paths in both arms. The adapter verifies the exact agent-visible file maps and prompt in each generated task. Teacher notes, validation labels, historic review answers and the published KOAI case sets are outside the common allowlist. A historical graph explicitly discussed in the skill and manuals is a public example and is ineligible as an independent performance question.

The goal of a case is visible in `instruction.md`. The native builder puts `entry.json` and the project grader under the verifier's `tests/`. The agent writes `/workspace/output/answer.json`. The custom metric `koai_case_facts_correct` is 1 when all required fields match, and 0 for an absent, malformed, oversized or incorrect answer. Additional answer fields are tolerated. Finite JSON numbers compare by numeric value. Booleans and strings are distinct. Duplicated JSON keys are rejected. The metric checks recorded fields. NVIDIA's default metrics and independent review cover reasoning, behavior and actual skill use. The official `default_plus_custom` runner retains its default overall and adds the KOAI metric separately.

## Independent comparison

An external `--suite FILE` must use the same documented keys as the public files. Use original IDs and prompts. The project checks exact normalized prompt reuse across the five public sets. A reviewer must also check for paraphrased examples, exposed solutions, incorrect reference answers and overlap with tuning. Supply cases the common inputs can actually support. New weeks or inputs need a reviewed extension of the explicit fixture list before making claims about them.

Run `check --pilot` with the external suite to obtain its `dataset_sha256`, `context_sha256` and `grader_sha256`. An independent reviewer records those three values with `status: reviewed`, `author` and a distinct `reviewer` in an external JSON record. This binds the assessment across compared skill versions. The recorded names are declarations. Verify independence and source quality in the review process. Run the following with the selected skill, suite, receipt and a fresh destination.

```sh
python tools/skill_evaluation.py prepare koai-evaluate /tmp/koai-reviewed \
  --suite /private/cases.json --review /private/review.json
```

`reviewed_inputs` establishes input eligibility. Study the paired preparation report before executing: `prepared_skill` gives the curated source path relative to the destination. Run actual trials against that source with NVIDIA's `tier3` command, Harbor, `--copy-repo`, `--grading-mode default_plus_custom` and a `--results-dir` outside the fixture. For example, use `skillevaluator tier3 --env-mode docker --copy-repo --grading-mode default_plus_custom --agents codex --model "$AGENT_MODEL" --evaluated-source-repository jlee-ax/AI-Olympiad --evaluated-source-revision "sha256:$SKILL_BUNDLE_SHA256" --results-dir "$RESULTS_DIR" "$PREPARED_SKILL"` in a configured environment. Use the exact skill bundle hash from the preparation report for the source revision. The static tests do not install NumPy into the Harbor image or execute notebook cells there. Supply an available isolated runner, explicit agent and judge models, credentials if the provider requires them, and bounded attempts, tokens, judge calls and cost. The native dollar limit covers agent spend with a price file. Account separately for judge and runtime costs. Keep both arms enabled. The evaluator launches the configured evaluation agent. The project's workflow controller continues to give advisory decisions.

Compare current and revised skills on the same held-out cases, controls, fixtures, models, judge basis, budgets and repetitions. Retain native reports and use `skillevaluator tier3 compare-versions "$PREPARED_SKILL" --current "$NEW_RUN" --prior "$OLD_RUN" --results-dir "$RESULTS_DIR"` on retained compatible runs. Define the primary measure before testing as the proportion of held-out tasks whose required defect is detected, correctly repaired and independently verified on a fresh input. Report its paired change, sample size and uncertainty. Track false positives on healthy inputs, missed faults, off-scope invocation, stale or duplicate state after resume, failed critical checks, tokens and elapsed time. Require enough paired observations, review NVIDIA's sufficiency and confidence information and set acceptable margins from the baseline and cost of errors before adopting a revision. Count an incomplete run as incomplete. Measure later student transfer separately with unseen tasks and observed unaided responses.
