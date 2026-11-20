# Week 1 teacher guide · From a score row to a gallery ID

A query asks for one gallery object. In a query-by-gallery score table, read the query's row, find the winning column under the stated rule, then use that column's header to identify the object. A student's answer should survive moving the candidate and its scores together. The same student should be able to explain why moving query rows changes the order of the answer list. [Student notebook](week01_integrated.ipynb)

## Classroom route and stopping point

Use sections 1–8 as the main route. Move from one pot per row to one query per row, then change the data contract and ask for an ordered lookup, numerical summaries and figures. Students first write a hand prediction and reason, then run their own solution on the supplied and changed inputs. The three items to collect are the matching answer and function, the painting-ID lookup and measurement summary, and the two plots with their source counts. Section 8 includes a fresh CSV, a new array and a clean-kernel rerun as checks on those items.

| Existing class allocation | Work to place in that block | Check one concrete result |
|---|---|---|
| 20 min, theory | Read a pot record, distinguish what is available at prediction time, and name the objects on each axis. Connect mean and variance to units. | A student identifies P03's unrecorded water, the later height, and the objects represented by the rows and columns of a score table. |
| 20 min, noncoding | Spend 10 min calculating axis means by hand. For the 10 min written block, follow the link in integrated section 3 to section 5 of *Python and tables* (cell `71068cea`). Have students answer both selected-response items and the constructed-response item on paper, then return to section 3. | Collect each original choice or calculation and its reason before revealing the key. The answers are 13, shape `(3,)` with two values per mean, and 6 ml over two measured values. The missing third value leaves the actual three-pot mean undetermined. |
| 20 min, Python | Follow the link in integrated section 2 to section 6 of *Python and tables* (cell `7208718e`). Have students predict all five diagnostic items before running the checks. Locate the first line that differs from the prediction, inspect the traceback and return to section 2. | Keep the first prediction and the correction. Check a returned value against printed output. The last-element repair for a nonempty list is `values[-1]`. |
| 40 min, CSV and pandas | Read the class plant table with its dictionary. Select records, check measured zeros and missing values, then demonstrate grouping by location and a left join to one description per location. | Trace one pot ID through the join. Compare the total rows for its location with the number of measured values. Students apply the same operations independently to the fresh CSV in section 8. |
| 20 min, NumPy and Matplotlib | Reduce a same-unit array along each axis and read a plotted mark against a source record or group. Use the section 5 score table as a short worked example of following a position to its ID. | The student identifies the source and unit of a point or bar, then follows one winning column to the gallery header. The paper exercises stay in the noncoding block. |

The earlier course plan sets a 120-minute class and a 5–7 hour historical self-study estimate. Its historical self-study ranges are 2–3 hours for Python/arrays, 1–1.5 hours for visualization, 1–1.5 hours for a new CSV and 1 hour for mathematics/fresh execution. Place the section 6 and 7 independent work in those categories where they exercise the same skill. Credit an existing new-input solution once after checking its reasoning and code. The class allocation is a plan. Actual student time, help needed and independent outcomes for this revision have not been observed. Record incomplete work and its next check. [Course plan](../../curriculum/student-plan.html#week-1) · [Week 1 allocation](lesson-manifest.json)

For **KOAI-01**, collect student-written code that traces the supplied order and returns the right object, including a repeated request. For **KOAI-02**, inspect the pandas selection, NumPy axis decisions and the evidence from a changed feature order. For **KOAI-03**, inspect actual Matplotlib and Seaborn figures, tick text, measured bar heights, units and the records behind them. The separate-kernel CSV and array checks below preserve the course's basic Python, plotting and data obligations. The leaf classifier, device exercise, rectangle, vector retrieval and ZIP checks have keys later in this guide for use when their specific questions arise.

## Matching key for sections 5 and 6

The supplied row index selects the query. A column position starts at zero and identifies a slot in the current arrangement. The value in the slot measures this pair. The gallery ID in its header names the candidate. A row maximum returns a *value*, `argmax(axis=1)` returns *positions*, and indexing the gallery ID sequence with those positions returns the requested *IDs*. With IDs attached as column labels, `score_table.idxmax(axis="columns")` returns those labels directly. Reducing over query rows instead would ask which query scores highest for each candidate.

| Worked query | Winning value | Zero-based column | Gallery ID |
|---|---:|---:|---:|
| Q4 | 0.90 | 1 | 14 |
| Q9 | 0.80 | 0 | 81 |

Move candidate 14 and its two scores to the first column. In gallery order `[14,81,57]` the winning positions are `[0,1]`. The answers remain `[14,81]` for Q4, Q9. If only the headers move, the numerical winners still occupy slots 1 and 0, which now falsely report `[81,14]`. Reading a row aloud as “Q4, score 0.90, column 1, file 14” makes the point of a mismatch visible. [Student matching example](week01_integrated.ipynb)

In the independent task, A rewards larger matches and B charges a smaller editing cost. For the supplied column order `[92,17,63,41]` and query order `[Q8,Q5,Q2]` the keys are

| Query | A value | A column | A ID | B cost | B column | B ID |
|---|---:|---:|---:|---:|---:|---:|
| Q8 | 0.65 | 2 | 63 | 0.05 | 1 | 17 |
| Q5 | 0.92 | 2 | 63 | 0.12 | 1 | 17 |
| Q2 | 0.80 | 1 | 17 | 0.10 | 3 | 41 |

A returns `[63,63,17]`. B returns `[17,17,41]`. Reusing a gallery ID is valid because each query receives its own decision. A classifier would return a class for each query. For example, two different gallery images could share the same class but have different file IDs.

Students choose their own rearrangements. The following choices give one answer key.

| Change to the input | A winning columns → returned IDs | B winning columns → returned IDs |
|---|---|---|
| Move the four columns together in old-position order `[2,3,0,1]`. The new headers are `[63,41,92,17]`. | `[0,0,3] → [63,63,17]` | `[3,3,1] → [17,17,41]` |
| Reverse only the original query rows to `[Q2,Q5,Q8]`, keeping their names and values together. | `[1,2,2] → [17,63,63]` | `[3,1,1] → [41,17,17]` |
| Apply only the new headers `[63,41,92,17]` to the *original* score columns. This intentionally breaks the pairs. | `[2,2,1] → [92,92,41]` | `[1,1,3] → [41,41,17]` |

In the first row, Q8's score 0.65 travels with gallery 63 from position 2 to position 0. In the second row, `Q2 → 17` under A moves to the first output slot, and Q8's own match still follows Q8. The third table has the correct shape and the wrong provenance. Accept any simultaneous candidate permutation and any query permutation that preserve these pairings. Swapping Q8 and Q5 leaves both numerical output lists identical because these two queries pick the same ID under each rule. Compare their names and score rows to see the swap. Reversing all three rows moves Q2 and visibly changes both lists. The general gallery interface assumes a unique maximum in each nonempty row of a finite rectangular table with one column per distinct ID. The separate cost question is answered using its stated objective. [Student matching exercise](week01_integrated.ipynb)

## Records and plots key for sections 4 and 7

**Worked plant bars.** The windowside pots are P03, P04 and P06. P04 and P06 have measured water, so the windowside numerator is 2 and the denominator is 3, or about 66.7%. Indoors, P01, P02 and P05 all have records, giving 3/3 = 100%. P01's 0 ml counts as observed. The scatterplot's point at `(5 h, 12 cm)` identifies P03. A bar groups several pots and has a percentage as its height. [Student plant plots](week01_integrated.ipynb)

**Painting lookup.** Normalize the requested name and each label key by trimming ASCII whitespace and matching ASCII case. Then walk the requests in their supplied order. For `[" F8 ", "f2", "F7", "f2"]` the result is `[-1, 0, None, 0]`. F8 is a known class. F2 occurs twice and has a real label record containing the unknown code 0. F7 lacks a matching record. F9 is present in the registry but unrequested. An empty request returns `[]`. An empty registry yields one `None` per requested item. Looking up truthiness would conflate the recorded zero with an absent key. Accept a loop or a mapping-based plain Python implementation that preserves each request slot.

**Measurement axes.** Only `scan_2`, `scan_1` and `scan_3` belong in the numerical array. The order of those names determines its columns. Each scan measures the same quantity in the same unit. Both an explicit null and an absent requested measurement represent missing observations. F8's `scan_1=0` is measured.

| Source record | scan_2 | scan_1 | scan_3 | Row calculation |
|---|---:|---:|---:|---|
| F8 | 4 | 0 | missing | `(4+0)/2 = 2` |
| F2 | missing | 8 | missing | `8/1 = 8` |
| F7 | 2 | missing | missing | `2/1 = 2` |

The shape is `[3,3]`. Row means are `[2,8,2]`. Column means are `[3,4,None]`, using measured counts `[2,2,0]`. Missing counts are `[1,1,3]`. Moving `scan_3` first, to `[scan_3,scan_2,scan_1]`, produces column means `[None,3,4]` and missing counts `[3,1,1]`. The records and their row means keep their order. Swapping only the first two features changes the column means to `[4,3,None]` while their missing counts happen to be equal. A named cell or a move of the all-missing feature exposes the change in column identity. An entirely missing row contributes `None` for that row's mean. The required record identifier and the optional measurement fields have separate presence rules.

**Known-label plots.** Use the independent `label_log` for these figures. Each row of that log counts once. Repeated requests in `items` change the length of the ordered lookup and do not add observations to this log.

| Display order | Known labels (−1 or 1) | All log records (including 0) | Count bar / percentage bar |
|---|---:|---:|---|
| B | 2 | 2 | 2 / 100% |
| A | 3 | 5 | 3 / 60% |

A has one more known label. B has a higher fraction known. For the public plotting interface, the figure's left-to-right tick text is `["B","A"]`, with x-axis `group`. The count y-axis is `known labels` with heights `[2,3]`, and the percent y-axis is `known labels (%)` with heights `[100,60]`. A signed sum of the labels, the mean of the signed labels, and dividing each group by the seven records in the entire log all answer different questions. Adding an unknown B record leaves its count at 2 and lowers its percentage to `2/3 × 100`. Inspect what the plotted bars actually encode. A table of intended numbers on its own does not verify the rendering. Accept either assignment of Matplotlib and Seaborn to the two student plots. [Student records exercise](week01_integrated.ipynb)

## One fresh-data check for section 8

At section 8, credit the saved section 2 Python diagnostic and section 3 paper responses from class once. If an item is unfinished, return to that item and record the correction and any help. In self-study, have the student bring their three outputs to a new kernel, open the fresh CSV with its data dictionary and trace one new record before running the code. Use the original answer key when a student needs feedback on a particular question, including return values, slicing, paths and required-column errors. [Original teacher key](teacher-notes.txt)

The fresh CSV's short data dictionary should identify `sample_id` as a string naming one pot, `site` as a categorical location shared by pots and used to join the notes, and `final_height_cm` as a numeric height measured in cm. `light_hours` (h) and `water_amount_ml` (ml) are separate quantities. Q01 has measured water 0, Q02 has missing water, and the other two rows have 20 and 40 ml. The three measured values average 20 ml. `light_hours >= 4` selects Q03 and Q04 with heights 12 and 14 cm. Ask for the inferred data types, including a numeric water column that can hold missing values. A lookup for the old required height column `height_cm` fails because this CSV calls it `final_height_cm`. The contract for the painting scans explicitly allows a wholly absent named measurement.

Group `new_plants` by `site` and compute the count and mean of `final_height_cm`. The indoor and windowside mean heights are 8 and 13 cm, based on two heights each. On a copy with Q02's height made missing, the indoor group still has two rows, one measured height and a mean of 7 cm. For water, the indoor and windowside measured counts are 1 and 2, out of two pots per site. A `site` left join to the two unique rows of `site_notes` keeps four pot records with their original IDs. Changing Q02 to an unlisted site leaves four rows and a missing note for Q02. On this same changed copy, duplicating the indoor lookup key makes `validate="many_to_one"` raise an error. Without the cardinality check, Q01 appears twice and the merged table grows to five rows. A height histogram with edges `[6,10,14,18]` cm has frequencies `[2,1,1]`. Use the same four heights and bin edges in Matplotlib's `ax.hist` and Seaborn's `histplot`. A bar for a named site can show its mean height. Pass the same two-row site summary to `ax.bar` and `sns.barplot`, with the same group order and vertical units (cm). The indoor bar then reads 8 and the windowside bar 13 in both plots. A histogram bar counts records in a numerical interval. Have the student identify which source records contribute to a selected bar and check the plotted values in both libraries. [Original fresh input and exercise C](week01_python_tables.ipynb)

For a single new-array check, the original companion supplies `B = [[1,5,9],[3,7,11]]` cm. Mean over the two rows gives `[2,6,10]` cm. Mean over the three columns gives `[5,7]` cm. The first row's population variance is `32/3` cm². Reshaping to `(3,2)` puts 5 at `[0,1]`, while transposing puts 3 there. Adding column corrections `[10,20,30]` gives 41 at the last cell. Row corrections `[[100],[200]]` give 211 there. Using shape `(2,)` fails against the trailing dimension 3. With ordered coefficients `[1,0,2]`, the two row dot products are 19 and 25 cm. Reversing only the features of the first row gives 11 cm, revealing a wrong pairing even though dimensions match. Accept other valid student-selected arrays, corrections, units and coefficients. Have the student restart the kernel, run their saved code in dependency order, and explain any discrepancy between hand and program results.

## Executable teacher references

These four functions implement public interfaces on new inputs. The gallery function uses a numerical row and its current header. The label function keeps a registry keyed by normalized identifier. The feature function constructs the requested columns in pandas, then uses NumPy to identify observed entries and summarize each axis. The plotting function renders one bar per ordered group through the selected library, reads the labels and bar artists back from the axes, and closes the figure. The user-facing lesson leaves its answer cells open for the student's own implementation.

### Select a gallery ID in query order

<!-- teacher-cell: ref-gallery -->
```python
def select_gallery_ids(case):
    gallery_ids = case["ids"]
    selected_ids = []
    for row in case["scores"]:
        winning_value = max(row)
        winning_column = row.index(winning_value)
        selected_ids.append(gallery_ids[winning_column])
    return selected_ids
```

### Align painting labels to requests

<!-- teacher-cell: ref-align -->
```python
from string import ascii_lowercase, ascii_uppercase, whitespace


def align_painting_labels(request):
    to_lowercase = str.maketrans(ascii_uppercase, ascii_lowercase)

    def normalized(identifier):
        return identifier.strip(whitespace).translate(to_lowercase)

    labels_by_id = {}
    for identifier, label in request["labels"]:
        labels_by_id[normalized(identifier)] = label
    return [labels_by_id.get(normalized(item)) for item in request["items"]]
```

### Summarize measurements along both axes

<!-- teacher-cell: ref-axes -->
```python
import numpy as np
import pandas as pd


def summarize_feature_axes(request):
    table = pd.DataFrame.from_records(request["rows"], columns=request["features"])
    values = table.to_numpy(dtype=float, na_value=np.nan)

    def measured_mean(vector):
        measured = vector[~np.isnan(vector)]
        if measured.size == 0:
            return None
        return float(measured.mean(dtype=np.longdouble))

    return {
        "shape": list(values.shape),
        "row_means": [measured_mean(row) for row in values],
        "column_means": [measured_mean(column) for column in values.T],
        "missing_by_column": np.isnan(values).sum(axis=0).tolist(),
    }
```

### Draw and read the requested known-label plot

<!-- teacher-cell: ref-plot -->
```python
import matplotlib.pyplot as plt
import seaborn as sns


def plot_known_labels(request):
    groups = request["groups"]
    totals = dict.fromkeys(groups, 0)
    known = dict.fromkeys(groups, 0)
    for group, label in request["rows"]:
        totals[group] += 1
        if label in (-1, 1):
            known[group] += 1

    if request["measure"] == "count":
        heights = [known[group] for group in groups]
        y_label = "known labels"
    else:
        heights = [100 * known[group] / totals[group] for group in groups]
        y_label = "known labels (%)"

    fig, ax = plt.subplots()
    try:
        if request["library"] == "matplotlib":
            ax.bar(range(len(groups)), heights)
        else:
            sns.barplot(x=groups, y=heights, order=groups, ax=ax, errorbar=None)
        ax.set_xticks(range(len(groups)), labels=groups)
        ax.set_xlabel("group")
        ax.set_ylabel(y_label)

        bars = sorted(ax.patches, key=lambda bar: bar.get_x())
        return {
            "groups": [tick.get_text() for tick in ax.get_xticklabels()],
            "heights": [float(bar.get_height()) for bar in bars],
            "x_label": ax.get_xlabel(),
            "y_label": ax.get_ylabel(),
        }
    finally:
        plt.close(fig)
```

## Worked keys for the plant example

**A record and its time.** One row describes one pot. The complete week's light, water and leaf observations are available just before the height measurement. On planting day the actual future records are unavailable. Height and a label derived from height become available afterward. P01 has a measured 0 ml. P03 has missing water. The six rows yield a two-feature table of shape `(6, 2)` and a height Series of shape `(6,)`. The light filter of at least 5 h selects P03, P04 and P06. The integrated example changes P05's water from 20 to 10 ml and height from 10 to 14 cm and P06's water from 60 to 50 ml relative to the original table.

**Averages and units.** The observed water values sum to 120 ml over five pots, giving 24 ml. The actual six-pot average depends on P03. For `observed_mean`, the stated inputs are lists of length 0–10,000 with finite Python integers or floats from −1,000,000 to 1,000,000 and missing values `None` or NaN. Booleans are outside the contract. `[0, None, NaN, 6]` has two measurements and mean 3. Empty and all-missing lists return `None`. The original table exercise D asks for *both* count and mean, with `(0, None)` for no observations. The heights `[8, 10, 12]` cm have mean 10 cm, deviations `[−2, 0, 2]` cm and population variance `8/3` cm². Three heights of 10 cm have variance 0. Use `ddof=0` in both NumPy and pandas when comparing the population calculation.

**Array axes.** On the two-day table for P01, P02 and P04, reducing axis 0 yields one mean per day, `[11/3, 11/3]` h, shape `(2,)`. Reducing axis 1 yields one mean per pot, `[2, 3, 6]` h, shape `(3,)`. Reshaping the values to `(2, 3)` puts `[2, 2, 3]` in the first row. Transposing puts `[2, 3, 6]` there. Adding a vector of shape `(2,)` adjusts the two days across every pot. A vector of shape `(3,)` mismatches the trailing dimension of size two. A row average needs commensurate quantities.

**Graph and fixed formula.** In the Matplotlib scatterplot P03 is the point `(5 h, 12 cm)`. Pot ID links the point to the original row. Light, location and watering vary together, so the data do not isolate the causal effect of light. The font search includes Noto Sans CJK JP. When the environment reports a missing font, install a Korean-capable font and restart that kernel. For the fixed formula `4 + L + 0.1W`, P02 gives `4 + 3 + 2 = 9` cm and the residual, measured minus predicted, is `+1` cm. The coefficients have units cm/h and cm/ml and the intercept has units cm. The formula is an assigned weighted sum with an intercept. P03 requires an explicit missing-water policy before evaluation. Model fitting and a biological causal effect are separate claims.

### Optional leaf observations and fitted model

Each leaf grid has shape `(2, 2, 2)` in row, column, channel order. Channel 0 is the object (0 background, 1 leaf). For a leaf, channel 1 is its color (0 green, 1 yellow). Background color is immaterial. Numerals here name categories. In P02, `[0,1] = [1,1]` and `[1,0] = [1,0]`. After transposing the spatial axes the shape is identical but the new `[0,1]` contains `[1,0]`. Three cells have color code 1. Only one has both leaf and yellow. Changing only the background colors preserves the count of one. The lesson function assumes a valid grid with this encoding.

Read each grid using its pot ID. The counts in P01–P06 order are `[0, 1, 2, 3, 2, 3]`. The observation *column* is a one-dimensional Series of arrays. A single observation is three-dimensional. An array of the correct shape attached to the wrong ID describes another pot. The count discards spatial position. Basic slicing makes a view. A copied numeric grid can be changed independently. Recompute a previously stored integer to see the effect of an edit.

The worked split names training pots P01–P04 and validation pots P05–P06 from the integrated table. Shuffle the rows with P06 first. The same named pots, training water mean and class centers must survive. A repeated pot ID makes lookup ambiguous, and a missing required pot prevents the declared split. A row outside the two named lists contributes to neither group. This small fixed protocol gives the next week's evaluation discussion an example whose membership can be audited. [pandas label-based indexing](https://pandas.pydata.org/docs/user_guide/indexing.html#selection-by-label) · [Training and validation separation](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)

For the separate target “height at least 12 cm,” P01–P04 have training labels `[0, 0, 1, 1]`. The training water values 0, 20 and 40 ml give an imputation mean of 20 ml. Including the validation records would change that statistic to 24 ml. In the preset 10 ml units, the training rows for `[water/10, yellow leaf count]` are `[[0,0],[2,1],[2,2],[4,3]]`. Each label belongs to the pot in that row. The class means are `[1,0.5]` and `[3,2.5]`.

For class 0's water values 0 and 20 ml, trial centers 0, 10 and 20 ml yield squared-deviation sums 400, 200 and 400 ml². In general the sum is `2(m−10)²+200`, minimized at `m=10`. Dividing 200 by two gives population variance 100 ml². Within-class squared error motivates the mean center. Classification accuracy is a different objective. Groups `[0,4]` and `[1,3]` both have center 2 with variances 4 and 1.

P05 is `[1,2]`. Its squared distances are 2.25 and 4.25, so it receives class 0. P06 receives class 1. Predictions `[0,1]` against `[1,1]` give 1/2. Two positive validation cases offer little information about performance, especially for class 0. The preset scale affects relative distances. Changing training P04's water to 60 ml in a copy gives a new imputation mean of `80/3` ml and class-1 center `[13/3,2.5]`. The same query `[2,2]` moves from predicted class 1 to 0. This experiment varies training data and refits both steps.

Keep P05 and P06 paired with their predictions. Reordering one sequence alone can keep the right length and assign a value to the wrong pot. The integrated example reads a headered `pot_id,prediction` CSV from memory and again from a temporary disk file. That file disappears at block exit. An actual submission requires its designated destination and format.

### Optional rectangle and mask

The worked rectangle `((2,4),(4,7))` on the 8×12 grid keeps rows 2–3 and columns 4–6. Its crop is `[[0,29,30],[40,41,42]]`, shape `(2,3)`. Both the mask and the zeroed-out result are `(8,12)`. Six true mask cells cover 1/16 of the 96 spatial cells. Only five selected numeric values are nonzero. For RGB the region still contains six pixels, or eighteen channel values.

For the separate 2×3 input `T = [[1,4,7],[2,5,8]]` the limit is four cells.

| Coordinates | Crop | Boolean mask shown as 0/1 | Values in full grid |
|---|---|---|---|
| `((0,1),(2,3))` | `[[4,7],[5,8]]` | `[[0,1,1],[0,1,1]]` | `[[0,4,7],[0,5,8]]` |
| `((0,0),(2,2))` | `[[1,4],[2,5]]` | `[[1,1,0],[1,1,0]]` | `[[1,4,0],[2,5,0]]` |
| `((1,2),(2,3))` | `[[8]]` | `[[0,0,0],[0,0,1]]` | `[[0,0,0],[0,0,8]]` |

Both 2×2 crops use four cells at different coordinates. The exclusive bottom/right limits may equal H/W. The fully in-bounds rectangle `((0,0),(2,3))` uses six cells and exceeds the limit. For `((1,1),(3,3))`, bottom 3 exceeds H=2. Without a bounds check, NumPy silently returns `[[5,8]]`. The equal row boundaries in `((1,1),(1,2))` create an empty region, which this exercise rejects.

A reference implementation first unpacks `(top,left),(bottom,right)` and `H,W = grid.shape`. Raise `ValueError` unless `0 <= top < bottom <= H` and `0 <= left < right <= W`. Then raise `ValueError` if `(bottom-top)*(right-left) > max_cells`. Return a copy of `grid[top:bottom,left:right]`, an initially false `np.zeros((H,W), dtype=bool)` with that rectangle set true, and an initially zero `np.zeros_like(grid)` with the crop copied into that rectangle. The copy makes later crop edits independent of the original. The supplied inputs are nonempty 2-D numeric arrays, four non-boolean Python integer coordinates and a positive integer limit. The function only needs to check the geometry and the area.

As a feedback example, cut `((1,1),(3,3))` out of `[[1,2,3,4],[5,0,7,8],[9,10,11,12]]` with limit four. The crop is `[[0,7],[10,11]]`. Its four exact positions include one measured zero. Inspect the full mask, the inside/outside values and the input after the call. A spatial region mask has a different role from a sequence padding mask.

### Optional device classification

Give the student validation features first. Have them record their features, fitted model and first prediction for each validation `unit`. Release the `unit,label` file after that record. Check that each side has one row per required ID, with no missing or unexpected IDs, before a one-to-one join. Missing truth leaves the comparison pending. Public repository files can be read in advance. When administering an independent exercise, control access to the key and record the help actually given. Subsequent validation-based choices need a separate untouched final test to estimate the chosen model's performance. This exercise supplies no final-test truth. [Validation labels](week01_integrated_validation_labels.csv)

Channel 0 now gives state (0 off, 1 on). Channel 1 gives object (0 background, 2 sensor). T2 at `[0,1]` holds `[1,2]` and at `[1,0]` holds `[0,2]`. The number of on sensors is one. Lit background cells do not count. After a spatial transpose the shape stays `(2,2,2)` and the new `[0,1]` contains `[0,2]`. A count discards the location of the sensor. The numeric code 2 identifies an object class.

Each `panel` starts as an `ndarray.copy()`. On a copy of T2, take the basic slice `[:, :, 0]` for a view of the state channel and make an independent copy of that view. Save the initial count as an integer. Changing background `[0,0]` from 1 to 0 keeps the recomputed count at 1. Then turn off the sensor at `[0,1]` through the view. At that position the untouched input still reads 1, the experiment and view read 0, and the saved view copy reads 1. The saved integer is 1 and the recomputed integer is 0. A pandas deep copy of a frame with an object column does not recursively copy each stored array. After copying the frame, `experiment["panel"] = experiment["panel"].map(lambda panel: panel.copy())` separates these numeric arrays. Independent storage and statistical independence are distinct properties. [NumPy copies and views](https://numpy.org/doc/stable/user/basics.copies.html) · [pandas DataFrame.copy](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.copy.html)

T1–T4 carry known labels. T5 has label `?`. The observed training signals `[0,3,9]` give a fill value of 4. T3 gets 4. Including T5's signal of 100 would give 28 under this supervised exercise's policy. Fit preprocessing and the model only on the designated known training rows. Use IDs to restore the output order. The label is a target.

With columns `[signal, on-sensor count]`, training inputs are `[[0,3],[3,1],[4,2],[9,0]]`. The centers for `정상` and `점검` are `[1.5,2]` and `[6.5,1]`. In V9, V4, V7 order this model predicts `[정상, 점검, 정상]` against `[정상, 점검, 점검]` for 2/3. New predictions in N3, N1, N7 order are `[점검, 정상, 점검]`. In the requested output order the CSV reads

```csv
sample_id,prediction
N7,점검
N3,점검
N1,정상
```

A depth-two decision tree using these features can instead predict all three validation labels correctly. Accept a justified model or panel feature with a different output. Inspect the fitted state, available inputs, feature order, split, per-ID comparison and header/rows/allowed values after rereading the file. A missing signal cell takes the training fill value. A missing required column or duplicate ID makes the contract ambiguous and should raise an error before inference or output. Equal predictions can conceal an ID swap. [scikit-learn guidance on preprocessing and leakage](https://scikit-learn.org/stable/common_pitfalls.html)

## Existing notebooks and source boundaries

The plant identifiers belong to their local data source. The foundation CSV uses `sunlight_hours` and records P05 at 20 ml and 10 cm. The integrated table uses `light_h` and records P05 at 10 ml and 14 cm. Both tables have six rows and the same IDs. The threshold of 12 cm gives P05 different classes. Check the data source, observation and units before importing a label or combining rows. The fresh CSV in the foundation lesson uses Q identifiers. For the independent join, execute the original setup `d2be9ce3`, loader `eb304b96`, fresh input `5c37fc90` and lookup `02c6cde1` in that order in its own kernel. [Python and tables notebook](week01_python_tables.ipynb) · [Foundation teacher key](teacher-notes.txt)

| Need | Where to look and what to check |
|---|---|
| Python, mean and variance | Original `71068cea`, `7208718e`, `c6d01f13` and `depth-function-spec` contain written decisions, state, failure line and repair, and a function returning both count and mean. `409e1675`, `82e8a039`, `08bf506c` and `ea9aba74` link hand calculations, units and the variance denominator. The teacher notes give a keyed example for each. |
| NumPy axes and broadcasting | Original A at `145c6754`, `depth-reshape-compare`, `df2802a3` and `practice-broadcast-code` checks placement at one coordinate, axis alignment and a failing rightmost dimension. A change in shape alone cannot demonstrate the intended operation. |
| Graphs | Foundation section 12 puts the same six heights into two different sets of paired observations. Exchanging the heights recorded for P01 and P06 leaves the height histogram unchanged, but moves the two scatter points and changes the indoor mean from 28/3 to 38/3 cm. Ask which source rows support a student's explanation. Exercise B uses Matplotlib and Seaborn to check distributions and categories. |
| Data dictionary, CSV and join | `b38de2c6`/`d7c7b7c4` cover the measured string `20ml`. Check its documented unit before converting and retain P03's missing value. Original C at `0fd965eb`, `02c6cde1` and `13559279` compares per-site means, measurement counts and left joins. Unknown keys retain the left row with a missing note. A duplicated lookup key breaks the many-to-one relationship. |
| Dot products and a fresh run | Original E at `d0ddef13`, `fixed-prediction-matrix-practice`, `fixed-prediction-matrix-practice-code` and `1e511556` checks named feature order and the student's saved solution in a new session. Original quantities `[1,4,2]` and matching prices `[800,500,1200]` give 5,200. A mismatched supplier order gives 6,900. |

When a named array is missing its meaning, use the bridge's axis section and return to integrated section 3. Bridge section 3 distinguishes elementwise multiplication from a matrix product at an off-diagonal entry. Exercise A asks students to align kit and item coefficients, preserve the units and keep the correct result when records move. When the question concerns constructing the scores, the worked retrieval uses supplied vectors, masks by token ID and rejects zero-length vectors for cosine similarity. The worked tie convention chooses the first current candidate. In the independent retrieval specification a tied recorded score selects the smallest candidate ID and results follow the requested query IDs. Integrated section 6 separately supplies unique extrema. Check the rule in the actual statement before accepting deliberate tie-handling differences. [Axes and retrieval notebook](week01_axes_linear_bridge.ipynb#bridge-scores) · [Bridge teacher key](week01_axes_linear_bridge_teacher.md)

If a learner has the correct per-ID predictions but cannot produce the requested row order, open section 4 of the problem-pipeline companion directly and return to the original task after one round trip. Use its independent exercise when the learner needs to decide what can enter a fit and when a held-out label is available. Have the learner preserve a complete per-ID prediction before opening the public self-study key. A structurally valid file may still assign the wrong class to a particular ID. The device exercise in the integrated notebook and the companion have different inputs and answer keys. Assign the branch that checks the missing decision and count completed work once. [Problem-pipeline submission exercise](week01_problem_pipeline.ipynb#pipeline-submit) · [Pipeline teacher key](week01_problem_pipeline_teacher.md)

The national 2027 announcement links a syllabus page headed IOAI 2026. The page names Python, NumPy/pandas and Matplotlib/Seaborn as practical topics. The registered Week 1 decision is to interpret the rows and axes, then map a computed position to the identifier required by the problem. [KOAI 2027 announcement](https://kitpa.org/koai/2027) · [Linked syllabus](https://kitpa.org/koai/syllabus) · [Week 1 course specification](../../curriculum/course-harness.json)

- **Restroom Icon Matching.** The international contest independently shuffles query and gallery files. A trained model must choose the opposite icon from the same restroom. Each output entry identifies a gallery image, and accuracy divides the number of correct matches by the total number of queries. The lesson supplies a score table so the student can work on the final lookup. [Official IOAI 2025 task, sections 2–5](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Restroom/Restroom.ipynb)
- **Antique Painting Authentication.** Five features and labels 1 (authentic), −1 (replica), and 0 (unknown) come from the contest. Entrants use unlabeled samples as well and produce a ZIP containing two headerless CSV files. The classroom painting table isolates label lookup and missing data. The plant and device examples use their own supervised policies and headered output. [Official IOAI 2025 task, sections 2–4](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Antique/Antique.ipynb)
- **Find the Order.** The numerical part of a shuffled audio filename identifies a chunk. `P[i]` gives the zero-based chronological position of that file. If the chronological file IDs are `[2,0,3,1]`, file 0 occupies position 1, file 1 position 3, file 2 position 0 and file 3 position 2. The array indexed by file ID is `[1,3,0,2]`. The lesson's matching output instead holds a gallery ID for each query. Reconstructing chronology from audio belongs to later work. [Official IOAI 2026 problem and output definition](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/1_Find_the_Order/statement.md)
- **Pixel Efficiency.** An official 224×224 image has 50,176 spatial cells. At most 6.25%, or 3,136 cells, may be retained. The contest submits image IDs and coordinates in `submission.jsonl` and is scored on classification accuracy. A full mask helps inspect a classroom rectangle. An admissible area alone supplies no evidence of classification value. The nonempty-rectangle rule is part of the synthetic task. [Official IOAI 2025 task](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Pixel/Pixel.ipynb)
- **Robot Chasing.** The official randomly ordered independent snapshots include an `(8,8,2)` object/color array, robot ID, direction, mission and carrying. The robot ID can help because robots differ. The prediction uses the available snapshot without earlier observations or actions. It returns an action code in input order in JSON, with evaluation truth withheld. The synthetic 2×2 grids isolate axis and category reading. [Official IOAI 2026 task](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/2_Robot_Chasing/statement.md)

These are past international tasks. The classroom examples practice selected decisions for a middle-school preparatory course. Weeks 2–5 develop splits, preprocessing, evaluation, loss and model choices. Week 6 develops tensor operations. Weeks 7–9 revisit identity and axes in image, text and audio tasks, and Week 10 uses unfamiliar specifications. Evidence for those outcomes requires work in their own settings.
