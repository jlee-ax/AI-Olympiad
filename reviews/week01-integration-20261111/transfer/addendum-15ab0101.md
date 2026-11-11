# Robot transfer comparison: candidate update

Date: 2026-11-11. Reviewer: `/root/gap_prioritization`.

The current `lessons/week01/week01_integrated.ipynb` was reread and its raw SHA-256 verified as `15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120` (34 cells). This addendum extends, without overwriting, the manual comparison of `e39e609d3354f20ca5518b652be39f3b31ec0b16154d37651e33309b42a39a6b` in `lesson-comparison.json` and `review.md`.

## Relevant changes on manual rereading

- Cell 1 more accurately describes changes to parts of two rows in the synthetic table. The local field roles and prediction-time boundary remain the same.
- Cell 19 now distinguishes consistent rescaling of a single feature, which preserves the nearest centre, from unequal scaling of multiple features. This improves the distance explanation; it does not introduce Robot channels or a Robot policy.
- Cell 33 gives concrete preparation cells and separate-kernel instructions for the older notebooks, restores explicit checks for written work, statistical principles, dtype and dirty data, and explains later-week connections. This improves navigation and prerequisite recovery. It does not add a Robot-specific independent task.

This is a manual comparison of the reviewed cell sources, not a claim that an archived complete raw copy of the previous candidate was byte-diffed here. No Robot-relevant code or new Robot assessment was found in the reread.

## Conclusion

The Robot conclusion is unchanged. Cells 1–4 still provide a local data dictionary/availability foundation, cells 9–12 a two-dimensional axis and same-shape counterexample, and cells 25–29 a local output/order foundation. The new roadmap does not establish transfer to the 8x8x2 row/column/channel contract, separately supplied direction/carrying, meaningless empty/wall colours, independent snapshots without previous observations, or the integer JSON-list output.

The original source remains pinned to IOAI 2026 commit `e1963801aa4cf33a5a03520b39fa6620a7894c54`, statement blob `f45b6bee1620d337eeaded43798df34a8413f2bd`. The earlier 25/25 synthetic expectations remain an independent source-contract run, not execution results for this candidate. They were not rerun because the source fixture, checker and relevant contract did not change.

Learner transfer, answers, assistance, retention and workload remain unobserved. No movement policy, official dataset result or international contest solution is inferred. Only this new addendum was written; the prior five transfer files, lesson files and Git index were not modified by this follow-up.
