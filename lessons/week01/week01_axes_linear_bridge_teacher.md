# Week 1 teacher guide · Array axes, matrix products and retrieval

Students read an indexed numerical array, derive a matrix product from two specified expressions and map a score-table column to a gallery ID. The opening grayscale and independent RGB data are small, synthetic numerical examples. The source task in section 5 is IOAI 2025 *Restroom Icon Matching*. Its original inputs are images. The accompanying exercises supply their own vectors, tokens and scoring rules. [Student notebook](week01_axes_linear_bridge.ipynb)

## Routes and prerequisites

| Student need | Start in a fresh kernel | Evidence to collect |
|---|---|---|
| Identify a row, a column and a coefficient | Start section 1 at `ba428b91` and continue through sections 2–3. Exercise A has its own setup in `ec433d3b`. | Derive one signed output, check a row and feature reordering and distinguish an observed zero from a missing channel. Return to [integrated section 3](week01_integrated.ipynb#week01-axes). |
| Build a query-by-gallery score matrix | Start section 5 at `3950021e`. Open exercise B once the student has worked through row normalization and lookup. | Compare both scoring requests, follow a winning column to its ID, and construct two different token sequences with the same stored mean. Return to [integrated section 6](week01_integrated.ipynb#week01-match). |
| Choose between a new batch dimension and concatenation | Start section 4 at `51e17d9e`. Exercise C supplies its own data. | Describe one output entry by its source vector and ID, including a case of unequal batch sizes. Return to [integrated section 8](week01_integrated.ipynb#week01-check). |

For a short section 5 helper replay, run `3950021e` (NumPy and query/gallery input), `retrieval-norm-code` (row normalization and cosine), `d81386f3` (lookup data) and `sequence-mean-code` (masked mean). Independent data cells `ec433d3b` and `07c93362` import NumPy. Leave the answer cells empty when distributing the student notebook. Students can use NumPy or scalar loops after giving a hand prediction. For A, ask to see the coefficient matrix even if the student's implementation uses named columns directly.

The course allocates a 120-minute Week 1 class and historically estimated 5–7 hours of required self-study. The bridge supplements the relevant part of the integrated class or individual practice. The main route also includes written work, CSV operations and visualization. Count an existing successful new-input demonstration once. Neither time on this revision nor learner performance has been measured. [Week 1 plan](../../curriculum/student-plan.html#week-1) · [Integrated guide](week01_integrated_teacher.md)

## Sections 1–3 · Hand calculations for the grayscale array

An identifier is a persistent name for a particular item in this data contract. The row index is its current position after any sort or reordering. The ID list is `[17,52,8]`. In the separately constructed data matrix `X` of shape `(3,2)`, axis 0 indexes images and axis 1 indexes pixel position in a two-pixel row. `X[1,:]` returns `[60,30]` for ID 52. `X[:,0]` returns the left brightness values `[20,60,40]` in image order. A new order of image rows must carry their IDs. The entries are grayscale codes between 0 and 255.

The mean and signed contrast are defined as `(L+R)/2` and `R−L`. Write each expression's coefficients down its column to obtain `W=[[0.5,-1],[0.5,1]]`. The two rows of W correspond to X's left and right feature columns. In an `(n,d) @ (d,m)` product, fix one input row and one output column and sum the d matched products. In particular `Y[1,1]=60×(−1)+30×1=−30`. The negative value indicates a darker right pixel. The map defined by W acts on real vectors. The grayscale codes supply a bounded set of examples of its inputs. It gives a linear transformation because distributing the products over a sum gives T(u+v)=T(u)+T(v), and factoring a scalar from all terms gives T(au)=aT(u). `Y` has shape `(3,2)` and rows `[50,60]`, `[45,−30]` and `[80,80]`.

`X @ X` fails because the inner lengths are 2 and 3. Reversing X's two columns and leaving W unchanged yields `[50,−60]` instead of `[50,60]` on the first image. The unchanged mean hides that error. Reversing the matching rows of W restores all three outputs. To diagnose elementwise multiplication, take the top two rows as `A=[[20,80],[60,30]]`. Both `A*I` and `A@I` produce the same diagonal entries 20 and 30. Only the latter retains the off-diagonal entry `[1,0]=60`. The former sets it to zero. [NumPy matrix multiplication](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html)

## Exercise A · Select RGB columns by name

The output has two columns, red minus blue and the arithmetic mean of all three channels. These are the exercise's explicitly defined features. The mean is an unweighted code-value mean. All input values lie between 0 and 255, while the signed difference ranges from −255 to 255. For the supplied input order B, R, G, the coefficient rows are `[−1,1/3]`, `[1,1/3]` and `[0,1/3]`. The shapes are `(3,3) @ (3,2) → (3,2)`.

| Image ID | B, R, G | R − B | Channel mean |
|---:|---|---:|---:|
| 31 | 2, 14, 8 | 12 | 8 |
| 7 | 12, 3, 6 | −9 | 7 |
| 19 | 4, 9, 2 | 5 | 5 |

For ID 7, red is at index 1 and blue is at index 0. The signed difference is `3−12=−9`. Arithmetic on unsigned bytes can wrap around during subtraction. Convert values to a signed or floating type **before** subtracting, or use real coefficients in the product. A physically missing G column and a G value of zero carry different information. With G absent one can still compute red minus blue from R and B, but the requested fixed three-channel mean is unknown. With G present at zero both outputs are defined and the denominator is three. A duplicated channel name leaves the mapping ambiguous.

Reverse both the headings and data to G, R, B. Each image retains its two features. Reverse only the numeric columns, retain the old B, R, G headings, and ID 31 falsely gets `14−8=6`. Its reported mean remains 8. That observed value distinguishes a check that inspects only symmetric summaries from a check that inspects the actual channel correspondence. Reordering whole image rows and IDs carries the outputs into that same order.

```python
def image_features(image_ids, channel_names, pixels):
    weights = {"R": (1, 1 / 3), "G": (0, 1 / 3), "B": (-1, 1 / 3)}
    if len(channel_names) != 3 or set(channel_names) != set(weights):
        raise ValueError("Expected R, G and B once each")
    values = np.asarray(pixels, dtype=float)
    if values.shape != (len(image_ids), len(channel_names)):
        raise ValueError("Image IDs and channel names must match the pixel array")
    coefficients = np.array([weights[name] for name in channel_names])
    results = values @ coefficients
    return [(image_id, *row.tolist()) for image_id, row in zip(image_ids, results)]
```

## Section 5 · Scores, positions and stored representations

A query is the input seeking a match. A gallery item is an eligible object to choose by its ID. A raw dot product is evaluated on the two original coordinate vectors before any length normalization. In the first worked query `[1,0]`, gallery items 42, 19 and 35 have raw dots 3, 2 and 1. Their cosines are `3/5`, 1 and `2/√5`. Their squared distances from the query are 20, 1 and 0.25. The fourth candidate, ID 7, has raw dot 0, cosine 0 and squared distance 5. The winning IDs across the entire gallery are therefore 42 by raw dot, 19 by direction and 35 by distance. For the two worked queries, first-maximum cosine positions `[2,1]` map to `[19,7]`. Jointly reordering candidates and IDs to `[19,42,35,7]` produces positions `[0,3]` and the same IDs. The stale header would attach `[42,35]`. `argmax` on the complete score table without an axis instead selects a single flattened position. [NumPy argmax](https://numpy.org/doc/stable/reference/generated/numpy.argmax.html)

A length denominator has shape `(number of rows,1)`. One positive scalar per whole row preserves its direction. Negating one row changes the sign of all its cosines. An arbitrary change of scale for each feature can change direction, and a columnwise denominator can broadcast successfully while scaling the wrong objects. The worked cosine helper rejects zero-length rows, nonfinite coordinates and unsupported array types. The arithmetic is designed for small finite real data whose norms can be computed in the running floating-point format. A zero component is valid whenever the vector as a whole has positive length. In the worked tie fixture the first current maximum wins, as NumPy specifies. Section 6B introduces its own ID-based tie rule. [NumPy norm and keepdims](https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html)

The classroom section 5 token array has shapes `(V,d)=(6,3)`, `(B,T)=(2,4)` and lookup shape `(2,4,3)`. Token ID 0 supplies the PAD convention even though the PAD table row is `[8,8,8]`. ID 5 supplies an actual zero vector and counts as a real token. The counts are `[2,3]`, sums `[[2,2,2],[4,4,0]]` and means `[[1,1,1],[4/3,4/3,0]]`. The locationwise lookup changes if token order changes, while these fixed-vector means survive the reordering. In `d81386f3`, the external ID 41 requires an explicit map to the table's row 3. A negative NumPy index can silently select the last row, so the helper validates IDs before indexing. Empty token arrays, out-of-range and noninteger IDs, and any all-PAD query are rejected by this classroom contract. [PyTorch embedding table and row indices](https://docs.pytorch.org/docs/2.15/generated/torch.nn.Embedding.html)

## Exercise B · What each retrieval request measures

Here `(B,T,d)=(2,4,2)` and the five table rows include PAD. The mask has shape `(2,4)`, the broadcast mask `(2,4,1)`, the sums and means `(2,2)` and the counts `(2,1)`. For query 61, real IDs `[1,1,2]` give sum `[6,9]` and mean `[2,3]`. For query 22, real IDs `[3,4]` give sum `[6,4]` and mean `[3,2]`. Count ID 4 despite its zero vector. The two query and gallery coordinate systems are shared in this exercise.

| Stored query | Raw dots in gallery order 90, 8, 53, 17 | Cosines in that order, to six places | Raw winner | Direction winner |
|---|---|---|---:|---:|
| 61 | 7, 9, 5, 4 | 0.868243, 0.832050, 0.980581, 0.554700 | 8 | 53 |
| 22 | 8, 6, 5, 6 | 0.992278, 0.554700, 0.980581, 0.832050 | 90 | 90 |

The axes on each `(2,4)` score table are stored query rows and current candidate positions. For query 61, column 1 is ID 8, whose long vertical vector contributes 9 in the raw score. Column 2 is ID 53, whose more closely aligned direction wins on the normalized calculation. The integer to submit is the candidate ID. The independent request names query 22 before 61, so the returned cosine list is **`[90,53]`** and the raw-dot list is **`[90,8]`**.

Appending ID 6 with `[0.5,0.5]` leaves each raw dot for the new item at 2.5. It exactly shares the direction of ID 53. After six-decimal score recording, the smaller ID wins their tie for query 61. The new cosine and dot-product outputs are **`[90,6]`** and **`[90,8]`**. Reversing the complete five-row gallery preserves both answers. A first-position tie break chooses 53 before the reversal, which exposes a direct copy of the worked rule. Section 6B names the two numeric score functions from section 5 and asks the student to match them to the requests. Use cosine for condition ① and the raw dot product for ② before rounding. Using negative angle would give an equivalent ordering on unrounded nonzero vectors, but six-place recording can produce different ties.

```python
def match_requests(table, token_ids, query_ids, gallery, gallery_ids, requested_ids, rule):
    _, _, _, _, queries = lookup_and_masked_mean(table, token_ids)
    gallery = np.asarray(gallery)
    gallery_ids = np.asarray(gallery_ids)
    if rule == "cosine":
        scores = cosine_scores(queries, gallery)
    elif rule == "dot":
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

The references assume the input contracts in the handout. The query and gallery ID lists each name unique rows, and each requested query exists. The score function reuses the student's worked section 5 helpers. A named-table or scalar-loop solution is equally admissible. The acceptance evidence is the named result under each rule, a sum and denominator trace, and the response to the changed data.

If the student checks only a winner, compare the means. Zeroing the PAD *vectors* but dividing by all four slots gives `[[1.5,2.25],[1.5,1]]`. Each row is a positive multiple of its correct mean, so cosine cannot expose the denominator error. Using the actual nonzero PAD and dividing by four gives `[[3.25,5],[5,6.5]]`, which would choose ID 53 for both original queries by direction. Looking at the intermediate counts and the actual coordinates distinguishes the three calculations. For the original gallery a single real ID 4 has count 1, sum and mean `[0,0]`. Strength yields four exact zeros and selects ID 8. Direction has no defined cosine. An all-PAD input has count 0 and neither request has a mean to compare. A teacher can check these two rows in separate calls to a helper that rejects an entire invalid batch.

For the archive request, `[1,2,0,0]` and `[2,1,2,1]` both average to `[2,4.5]`. The first real tokens are 1 and 2 and the valid lengths are 2 and 4. A lookup by the mean would receive identical input for either record and would have to return two different correct answers. Saving first real ID and count is sufficient for this request. Saving the sequence and the PAD convention would also suffice. If a student supplies a pair that changes only the length or only the first token, ask whether one can construct a pair that defeats both requested fields. Future contextual representations may include position or neighboring tokens in the vectors before any pooling.

## Exercise C and the final sign question

Stacking the two input arrays of shape `(2,2)` produces `(2,2,2)` with axes input batch, within-batch position, feature. Row concatenation produces `(4,2)` with four candidate rows. Column concatenation produces `(2,4)`. Its first row joins ID 90's values to ID 53's values, so interpreting it as four features of a single candidate would misidentify two coordinates. With one and three rows, stack fails, row concatenation produces `(4,2)`, and column concatenation cannot match the row counts. A feature join for the same candidate would need matching IDs and a shared row order. [NumPy stack](https://numpy.org/doc/stable/reference/generated/numpy.stack.html) · [NumPy concatenate](https://numpy.org/doc/stable/reference/generated/numpy.concatenate.html)

In the small sign example, ID 73 is a male sign at the correct location, ID 18 is a female sign at a different location, and **40** satisfies both conditions. No numeric threshold or choice of the top two enforces either condition. The notes supply facts about locations and the type of sign that a table of numerical scores can discard. The international *Restroom Icon Matching* statement requires the opposite sign from the same restroom, independent query/gallery numbering, a trained model and an output ID per query. Its baseline encodes images, concatenates batches, normalizes each embedding, forms a matrix of pair scores, then uses the second of its ranked candidates and a one-based numeric filename convention. Those last choices are properties of that baseline and file layout. The actual statement defines correctness by the true partner. [IOAI 2025 Restroom, §§2–6 and baseline](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Restroom/Restroom.ipynb)

## Course and source boundaries

The national announcement checked on 2026-11-20 includes written and coding examinations across sections 1–4 for the middle-school division. Its linked domestic syllabus still carries the IOAI 2026 label. Section 1-1 includes NumPy/pandas and array manipulation, and the broader syllabus includes preprocessing, embeddings and pooling. Week 1 uses small supplied vectors to practise named axes, representations and one returned ID. Image encoding, training, and full text or audio models have their own later course placements. The separate international 2027 syllabus establishes its own scope. [National 2027 announcement](https://kitpa.org/koai/2027) · [Linked domestic syllabus](https://kitpa.org/koai/syllabus) · [International 2027 syllabus](https://ioai-official.org/wp-content/uploads/2026/11/IOAI_Syllabus.pdf) · [Registered Week 1 decision](../../curriculum/course-harness.json)

*Potato* supplies one public embedding row per vocabulary word and uses a different private representation for the interactive judge. These exercises supply their own fixed numbers. *Find the Order* asks for the chronological rank of each shuffled audio chunk indexed by that chunk's ID. This motivates retaining order when the output depends on it. The public task uses audio and requires a full permutation. Locally checking the arithmetic, representation collision and file-ID conventions establishes those prerequisites on particular inputs. Actual performance on either contest problem and student outcomes require separate evidence. [IOAI 2026 Potato dataset](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md#dataset) · [IOAI 2026 Find the Order output](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md#output) · [Earlier retrieval evidence](../../reviews/week01-retrieval-20261111/source-prioritization.md) · [Earlier sequence evidence](../../reviews/week01-sequence-20261111/source-prioritization.md)
