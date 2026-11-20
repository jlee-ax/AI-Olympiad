# Week 1 teacher guide · From aligned columns to a gallery ID

The bridge is a return visit for a student who can already read one record and its ID. The choice in sections 1–3 is which inner dimension has the same meaning in two arrays. The choice in section 5 is which information a score should preserve. Use the relevant exercise in section 6 to see whether the student can make that choice on new data. [Student notebook](week01_axes_linear_bridge.ipynb)

## Where to enter and when to return

| Starting question | Route in a fresh kernel | Student evidence and exit |
|---|---|---|
| Which feature goes with each coefficient? | Start with section 1's first code cell and work through sections 1–3. Use 6A when a new example is needed. | Take one named result and its units through the student's calculation, including a changed column order. Return to [integrated section 3](week01_integrated.ipynb#week01-axes). |
| Where could a query-by-gallery score table come from? | Start at section 5's first code cell and work through that section in order. Then reveal only 6B and its input. | Collect the two ordered ID lists, a joint candidate permutation and the response to the archive request. Return to [integrated section 6](week01_integrated.ipynb#week01-match). |
| When does combining arrays preserve an identity? | Start at section 4's first code cell. Section 6C supplies its own data. | Check the meaning of one concatenated row and the unequal-batch example. Return to [integrated section 8](week01_integrated.ipynb#week01-check). |

For a direct section 5 helper replay in a fresh kernel, run `3950021e` (NumPy and query/gallery data), `retrieval-norm-code` (row normalization and cosine), `d81386f3` (lookup data) and `sequence-mean-code` (masked mean). Section 6A's `ec433d3b` and section 6B's `07c93362` are self-contained data cells that import NumPy. They allow a fresh attempt with the worked helpers closed. Keep the worked examples and this key closed while the student makes the first predictions. Read the student's explanation, code, changed input and any help received before attributing a result to independent work.

The registered middle-school Week 1 plan has a 120-minute class and an earlier estimate of 5–7 hours of required independent work. The integrated route already includes the Python diagnosis, written work, array practice, actual CSV and plotting tasks. Credit a student’s existing evidence once. Choose a bridge question within the applicable practice or support route. Time spent, amount of help and transfer to an unaided examination have yet to be observed. [Week 1 plan](../../curriculum/student-plan.html#week-1) · [Integrated guide](week01_integrated_teacher.md)

## Sections 1–3 · What one matrix entry counts

The photography rule supplies the coefficients. A small leaf is photographed on one side, a large leaf on both sides. In P24's record `[1,3]`, multiply leaves by photos per leaf to obtain photos. The third column of W gives `1×1 + 3×2 = 7` photos. The columns of `X @ W` are small-leaf count, large-leaf count and photos. Its rows are `[2,1,4]`, `[1,3,7]` and `[3,2,7]` in P11, P24, P38 order. The first two output columns count leaves and the third counts photos. A row sum across all three has no requested physical interpretation.

If a student says only that the inner dimensions match, label one shared leaf type on both tables. In `(n,d) @ (d,m)`, one multiplication counts the contribution of feature k to output j on row i. Summing across the d aligned features leaves n objects and m requested outputs. In `W @ X`, output categories happen to be as numerous as pots, so NumPy can perform the operation. Reassigning the first pot to the first output category has no basis in the recording rule. `X @ X` fails the size check as well.

The identity-matrix example makes a particularly short diagnostic. With A=`[[2,1],[1,3]]`, the two diagonal entries are 2 and 3 under both operations. At `[1,0]`, the elementwise product gives 0 and the requested small-leaf count under matrix multiplication is 1. Ask the student to pick a cell whose value can disprove the proposed operation. [NumPy matrix multiplication](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)

## Exercise A · From the order sheet to the packing quantities

Rows of `X_new` are classes, columns are kits. For each kit, look up its recipe by name, then its per-kit quantities in the packing slip’s requested item order. With order columns `["기본","확장"]` and output columns `["유리판","시험관"]` the resulting W is `[[2,0],[1,3]]`. The product has shape `(3,2)`. Its named rows are

| Class | Glass plates | Test tubes |
|---|---:|---:|
| 솔반 | 6 | 12 |
| 별반 | 5 | 3 |
| 달반 | 3 | 9 |

For 별반, `2 basic kits × 2 plates/basic kit + 1 extension kit × 1 plate/extension kit = 5 plates`. Reversing the named order columns makes the first row `[4,1]` and the two matching coefficient rows `[[1,3],[2,0]]`. The slip still says 6 plates and 12 tubes. Reversing just the values and leaving the old names gives 9 plates and 3 tubes for 솔반. Both products have shape `(3,2)`. Reordering the recipe records themselves also preserves the answer. An ordered lookup for an unfamiliar kit needs its item quantities, including any explicit measured zero. The task gives one recipe per kit and one order row per class.

The earlier square-array check remains available with these numbers. `X_new[:2] * W` yields `[[2,0],[2,3]]`, whereas the two packing rows are `[[6,12],[5,3]]`. A coefficient array with three rows cannot multiply this two-kit order matrix. Ask which object or unit is lost in the first error before discussing shape in the second. A loop that matches the labels and sums item quantities earns the same mathematical credit as matrix multiplication.

```python
def shipping_manifest(class_ids, order_columns, orders, recipe_rows, item_columns):
    recipe = dict(recipe_rows)
    coefficients = np.array([
        [recipe[kit][item] for item in item_columns]
        for kit in order_columns
    ])
    packed = np.asarray(orders) @ coefficients
    return [(class_id, *row.tolist()) for class_id, row in zip(class_ids, packed)]
```

## Section 5 · Scores, positions and stored representations

In the first worked query `[1,0]`, gallery items 42, 19 and 35 have raw dots 3, 2 and 1. Their cosines are `3/5`, 1 and `2/√5`. Their squared distances from the query are 20, 1 and 0.25. The fourth candidate, ID 7, has raw dot 0, cosine 0 and squared distance 5. The winning IDs across the entire gallery are therefore 42 by raw dot, 19 by direction and 35 by distance. For the two worked queries, first-maximum cosine positions `[2,1]` map to `[19,7]`. Jointly reordering candidates and IDs to `[19,42,35,7]` produces positions `[0,3]` and the same IDs. The stale header would attach `[42,35]`. `argmax` on the complete score table without an axis instead selects a single flattened position. [NumPy argmax](https://numpy.org/doc/stable/reference/generated/numpy.argmax.html)

A length denominator has shape `(number of rows,1)`. One positive scalar per whole row preserves its direction. Negating one row changes the sign of all its cosines. An arbitrary change of scale for each feature can change direction, and a columnwise denominator can broadcast successfully while scaling the wrong objects. The worked cosine helper rejects zero-length rows, nonfinite coordinates and unsupported array types. The arithmetic is designed for small finite real data whose norms can be computed in the running floating-point format. A measured zero in the plant classification exercise has its ordinary meaning. In the worked tie fixture the first current maximum wins, as NumPy specifies. Section 6B introduces its own ID-based tie rule. [NumPy norm and keepdims](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)

The section 5 token array has shapes `(V,d)=(6,3)`, `(B,T)=(2,4)` and lookup shape `(2,4,3)`. Token ID 0 supplies the PAD convention even though the PAD table row is `[8,8,8]`. ID 5 supplies an actual zero vector and counts as a real token. The counts are `[2,3]`, sums `[[2,2,2],[4,4,0]]` and means `[[1,1,1],[4/3,4/3,0]]`. The locationwise lookup changes if token order changes, while these fixed-vector means survive the reordering. In `d81386f3`, the external ID 41 requires an explicit map to the table's row 3. A negative NumPy index can silently select the last row, so the helper validates IDs before indexing. Empty token arrays, out-of-range and noninteger IDs, and any all-PAD query are rejected by this classroom contract. [PyTorch embedding table and row indices](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html)

## Exercise B · What each retrieval request measures

Here `(B,T,d)=(2,4,2)` and the five table rows include PAD. The mask has shape `(2,4)`, the broadcast mask `(2,4,1)`, the sums and means `(2,2)` and the counts `(2,1)`. For query 61, real IDs `[1,1,2]` give sum `[6,9]` and mean `[2,3]`. For query 22, real IDs `[3,4]` give sum `[6,4]` and mean `[3,2]`. Count ID 4 despite its zero vector. The two query and gallery coordinate systems are shared in this exercise.

| Stored query | Raw dots in gallery order 90, 8, 53, 17 | Cosines in that order, to six places | Raw winner | Direction winner |
|---|---|---|---:|---:|
| 61 | 7, 9, 5, 4 | 0.868243, 0.832050, 0.980581, 0.554700 | 8 | 53 |
| 22 | 8, 6, 5, 6 | 0.992278, 0.554700, 0.980581, 0.832050 | 90 | 90 |

The axes on each `(2,4)` score table are stored query rows and current candidate positions. For query 61, column 1 is ID 8, whose long vertical vector contributes 9 in the raw score. Column 2 is ID 53, whose more closely aligned direction wins on the normalized calculation. The integer to submit is the candidate ID. The independent request names query 22 before 61, so the returned direction list is **`[90,53]`** and the strength list is **`[90,8]`**.

Appending ID 6 with `[0.5,0.5]` leaves each raw dot for the new item at 2.5. It exactly shares the direction of ID 53. After six-decimal score recording, the smaller ID wins their tie for query 61. The new direction and strength outputs are **`[90,6]`** and **`[90,8]`**. Reversing the complete five-row gallery preserves both answers. A first-position tie break chooses 53 before the reversal, which exposes a direct copy of the worked rule. Section 6B names the two numeric score functions from section 5 and asks the student to match them to the requests. Use the cosine value for direction and the raw dot product for strength before rounding. Using negative angle would give an equivalent ordering on unrounded nonzero vectors, but six-place recording can produce different ties.

```python
def match_requests(table, token_ids, query_ids, gallery, gallery_ids, requested_ids, rule):
    _, _, _, _, queries = lookup_and_masked_mean(table, token_ids)
    gallery = np.asarray(gallery)
    gallery_ids = np.asarray(gallery_ids)
    if rule == "direction":
        scores = cosine_scores(queries, gallery)
    elif rule == "strength":
        scores = queries @ gallery.T
    else:
        raise ValueError("unknown search request")

    recorded = np.round(scores, 6)
    selected = {}
    for query_id, row in zip(query_ids, recorded):
        tied_ids = gallery_ids[row == row.max()]
        selected[query_id] = int(tied_ids.min())
    return [selected[query_id] for query_id in requested_ids]
```

These two teacher references use the data contract in the handout. The ID lists are unique names of the supplied rows, and the requested queries and items exist. The score function reuses the student's worked section 5 helpers. A named-table or scalar-loop solution is equally admissible. The acceptance evidence is the named result under each rule, a sum and denominator trace, and the response to the changed data.

If the student checks only a winner, compare the means. Zeroing the PAD *vectors* but dividing by all four slots gives `[[1.5,2.25],[1.5,1]]`. Each row is a positive multiple of its correct mean, so cosine cannot expose the denominator error. Using the actual nonzero PAD and dividing by four gives `[[3.25,5],[5,6.5]]`, which would choose ID 53 for both original queries by direction. Looking at the intermediate counts and the actual coordinates distinguishes the three calculations. For the original gallery a single real ID 4 has count 1, sum and mean `[0,0]`. Strength yields four exact zeros and selects ID 8. Direction has no defined cosine. An all-PAD input has count 0 and neither request has a mean to compare. A teacher can check these two rows in separate calls to a helper that rejects an entire invalid batch.

For the archive request, `[1,2,0,0]` and `[2,1,2,1]` both average to `[2,4.5]`. The first real tokens are 1 and 2 and the valid lengths are 2 and 4. A lookup by the mean would receive identical input for either record and would have to return two different correct answers. Saving first real ID and count is sufficient for this request. Saving the sequence and the PAD convention would also suffice. If a student supplies a pair that changes only the length or only the first token, ask whether one can construct a pair that defeats both requested fields. Future contextual representations may include position or neighboring tokens in the vectors before any pooling.

## Exercise C and the final sign question

Stacking the two input arrays of shape `(2,2)` produces `(2,2,2)` with axes input batch, within-batch position, feature. Row concatenation produces `(4,2)` with four candidate rows. Column concatenation produces `(2,4)`. Its first row joins ID 90's values to ID 53's values, so interpreting it as four features of a single candidate would misidentify two coordinates. With one and three rows, stack fails, row concatenation produces `(4,2)`, and column concatenation cannot match the row counts. A feature join for the same candidate would need matching IDs and a shared row order. [NumPy stack](https://numpy.org/doc/stable/reference/generated/numpy.stack.html) · [NumPy concatenate](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html)

In the small sign example, ID 73 is a male sign at the correct location, ID 18 is a female sign at a different location, and **40** satisfies both conditions. No numeric threshold or choice of the top two enforces either condition. The notes supply facts about locations and the type of sign that a table of numerical scores can discard. The international *Restroom Icon Matching* statement requires the opposite sign from the same restroom, independent query/gallery numbering, a trained model and an output ID per query. Its baseline encodes images, concatenates batches, normalizes each embedding, forms a matrix of pair scores, then uses the second of its ranked candidates and a one-based numeric filename convention. Those last choices are properties of that baseline and file layout. The actual statement defines correctness by the true partner. [IOAI 2025 Restroom, §§2–6 and baseline](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Restroom/Restroom.ipynb)

## Course and source boundaries

The national announcement checked on 2026-11-20 includes written and coding examinations across sections 1–4 for the middle-school division. Its linked domestic syllabus still carries the IOAI 2026 label. Section 1-1 includes NumPy/pandas and array manipulation, and the broader syllabus includes preprocessing, embeddings and pooling. Week 1 uses small supplied vectors to practise named axes, representations and one returned ID. Image encoding, training, and full text or audio models have their own later course placements. The separate international 2027 syllabus establishes its own scope. [National 2027 announcement](https://kitpa.org/koai/2027) · [Linked domestic syllabus](https://kitpa.org/koai/syllabus) · [International 2027 syllabus](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf) · [Registered Week 1 decision](../../curriculum/course-harness.json)

*Potato* supplies one public embedding row per vocabulary word and uses a different private representation for the interactive judge. These exercises supply their own fixed numbers. *Find the Order* asks for the chronological rank of each shuffled audio chunk indexed by that chunk's ID. This motivates retaining order when the output depends on it. The public task uses audio and requires a full permutation. Locally checking the arithmetic, representation collision and file-ID conventions establishes those prerequisites on particular inputs. Actual performance on either contest problem and student outcomes require separate evidence. [IOAI 2026 Potato dataset](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md#dataset) · [IOAI 2026 Find the Order output](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md#output) · [Earlier retrieval evidence](../../reviews/week01-retrieval-20261111/source-prioritization.md) · [Earlier sequence evidence](../../reviews/week01-sequence-20261111/source-prioritization.md)
