# Week 1 teaching guide · Data representation and descriptive statistics

[Student textbook](week01_integrated.ipynb)

The principal learning objective is to decide what a numerical representation preserves and whether it is sufficient for classification or retrieval. A learner should be able to identify the unit of analysis, justify a numerical operation and use it on a different input. Ask for the intermediate calculation and its interpretation. A correct file produced by a supplied example establishes only that it executed.

## Teaching the required material

Use the established 120-minute allocation as a planning constraint. The first 20 minutes introduce samples, features, labels, loss of information and descriptive moments. Use the noncoding 20 minutes for an axis reduction by hand and the foundation's two selected-response items and one written calculation. The Python 20 minutes cover the loop for a mean with missing values, including empty input, and the companion's five short tracing tasks. In the 40-minute pandas/CSV block, select labeled columns in the real digits data, distinguish a measured zero from a masked value, build a group summary and perform the CSV left join in the companion if needed. In the final 20 minutes, form a small NumPy matrix, read the actual scatterplot, and connect its coordinates or an inner product to a classification or retrieval decision. The larger independent exercises and conditional sections can use the existing 5–7 hour independent-study allowance. These are allocations. No learner time was observed.

Use the integrated material for the main explanations and choose companion sections for a specific difficulty. The foundation develops labeled tables, NumPy, visualization and the optional synthetic CSV lab. The axes companion develops matrix operations, similarity and information lost through pooling. The classification companion derives a supervised baseline from partially labeled data and separates training, validation and submission. Later weeks own training design, model selection and higher-dimensional domain models. An image-matching problem supplies a reason to learn matrix products here without requiring a full image encoder in Week 1.

## Worked explanations and answer keys

**Representation.** The scikit-learn digits subset has 1,797 images, 64 integer-valued features and one class value per image. Each feature counts foreground pixels in one nonoverlapping 4×4 region of an original 32×32 binary image. The 64 counts form an 8×8 map. Original image index 0 has class 0 and value 15 at region (2,2), flattened offset 18. Flattening in a fixed order is reversible here. Replacing 16 binary positions by one count is not reversible. For instance, moving a single foreground pixel inside a block preserves the count. Basing an interpretation on grey-level sensor readings would misdescribe this source. The source index names a record in this ordered dataset. It is not the digit label or an intrinsic number written on the image. [scikit-learn digits](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_digits.html) · [UCI construction](https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits)

**Missing data and moments.** The real digits feature matrix is complete. In a private copy of feature pixel_2_2 for indices 11, 56 and 10, the class example masks the last of the original values 0, 10 and 16. The observed subset mean is 5. Filling the third slot with zero gives 10/3. The actual mean before masking was 26/3, which cannot be inferred from the two visible values alone. For [2,4,6] and [4,4,4], both means are 4. Their signed deviations are [-2,0,2] and [0,0,0]. The variances using denominator n are 8/3 and zero, with standard deviations approximately 1.633 and zero. A length variance is measured in squared length units, and the standard deviation in the original unit. Distinguish a descriptive variance from an estimator using n−1. Missing all data yields an undefined mean, represented in the lesson function as None.

**Axes and broadcasting.** For image indices [0,1,11] and named features [pixel_2_2,pixel_4_2], the array contains [15,8], [3,1], [0,12] in that order. Axis-zero reduction leaves [6,7], and axis-one reduction leaves [11.5,2,6]. The entry X[2,1] has value 12 and comes from original image 11 at (4,2). Transposition yields first row [15,3,0]; reshaping in C order gives first row [15,8,3]. A two-element vector of column means broadcasts across rows. A row mean needs shape (3,1) to broadcast down this (3,2) matrix. A square matrix can give a numerically legal but semantically wrong broadcast. Test one index against an explicit subtraction when dimensions coincide.

**Figures.** The scatterplot puts pixel_2_2 on the horizontal axis and pixel_4_2 on the vertical. Images 10 and 20 have class 0, image 26 has class 6, and all three occupy (16,16). No deterministic classifier using only these two coordinates can get all three correct. Inspecting other coordinates distinguishes the particular 10/26 pair. This establishes information loss for those examples and does not establish that a third coordinate suffices globally. The bar chart summarizes the same eight selected cases. Classes 0, 1 and 6 have respective totals 4, 3 and 1. Both coordinates equal 16 for 2, 0 and 1 images. The conditional proportions are 50%, 0% and 100%. The group's sample size matters, and the chosen rows do not estimate population rates.

**Weighted sums and retrieval.** With ordered coefficients [1,−1], image 0 has contrast 7. That statistic loses absolute pixel count. In the supplied pairwise score table, Q4 chooses candidate 14 at column position 1 (score 0.90) and Q9 chooses candidate 81 at position 0 (score 0.80). For the separately given feature vectors, the unnormalized score matrix is [[4,2,2],[0,1,2]]. Its cosine counterpart is [[1/√2,1,1/√2],[0,1/√2,1]]. Candidate 81 wins by raw dot product on the first query and candidate 14 wins with normalized vectors. Scores arise from the representational choice. A published task on visual matching provided images and its own pairing criterion. Neither classroom scoring rule is an official required algorithm. [Original IOAI 2025 task](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Restroom/Restroom.ipynb)

**Section 6.** For Q8, Q5 and Q2, maximizing the supplied similarities returns [63,63,17]. Minimizing the same numbers interpreted as costs returns [17,17,41]. The first maxima/minima occur at column positions 2 and 1, with values 0.65 and 0.05. Simultaneously permuting headers and columns preserves each chosen candidate. Relabeling unchanged scores generally changes the candidate. Moving queries moves the output slots, although exchanging two queries with the same winning candidate is invisible in the ID list. On the new vectors, q=(1,0) has dot products 2 and 1 but cosine similarities 1/√2 and 1. The raw and normalized rules choose different candidates. A zero vector has no cosine direction. It should not silently be assigned a best match under this definition.

**Section 7.** The exercise codes 1 and −1 label the two known classes and 0 means unknown. A missing search key is distinct. The real Antique competition uses those label meanings. The case-insensitive names, missing-record policy and per-region lookup are practice inputs. The answer in requested order is [-1,0,None,0]. With region order [region_b,region_a,region_c], the row means are [2,8,2], column means [3,4,None] and counts of missing values [1,1,3]. Group B has 2/2 known labels and group A has 3/5. B then A gives count heights [2,3] and percentage heights [100,60]. A repeated request adds no underlying observation to the separate label log. [Original IOAI 2025 task](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Antique/Antique.ipynb)

## Independent problems

1. The row means of (2,6), (4,4), (6,2) are all 4. The contrast x₁−x₂ is −4, 0 and 4. Its sign answers the stated question. An indicator of x₁>x₂ is also sufficient. Accept any justified statistic that distinguishes the cases required by the question.
2. The true digit is unavailable for the new image when predicting. Supplying it as an input would leak the answer. Real images 10 and 26 differ at region (0,3), which has counts 9 and 13. Their squared distance in the full 64-element representation is 1,756. A single successful separation is evidence about this pair only.
3. In the specified order the dot-product score matrix is [[2,1],[1,3]]. The candidates chosen are [23,71]. A joint permutation interchanges columns and displayed positions while preserving those two candidate identifiers. The first query uses the first coordinate and the second query the second coordinate.

## Conditional extensions

**A. Nearest-centroid classification.** Use training indices [0,1,10,11] and validation indices [21,70,72]. Artificially mask image 10's first coordinate only in the training copy. The first-coordinate replacement is (15+3+0)/3 = 6. Training vectors after this operation are (15,8), (3,1), (6,16), (0,12) with labels 0,1,0,1. Taking coordinate-wise class means gives (10.5,12) and (1.5,6.5). Expanding the sum of squared deviations about the mean shows that the arithmetic mean minimizes the squared error coordinate by coordinate. This is the mathematical property used by this particular classifier.

Validation image 21 is (4,3); its squared distances are 123.25 and 18.5. For image 70 at (10,5) they are 49.25 and 74.5, giving a wrong prediction of 0 for true class 1. For image 72 at (16,15) they are 39.25 and 282.5. Predictions [1,0,0] match two of [1,1,0]. In the perturbation, increasing image 0's second coordinate to 12 makes the class-0 center (10.5,14); the other center is unchanged. For probe (7,9), squared distances change from (21.25,36.5) to (37.25,36.5) and the class changes from 0 to 1. This perturbation is a numerical counterfactual. Changing only a held-out label could change measured accuracy, but has no effect on the fitted means or predictions. The CSV preserves the physical pair for each requested image after reordering. [Nearest-centroid estimator](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestCentroid.html)

**B. Masked binary arrays.** Use the rows T1–T4, exclude unknown-label T5, and include measured zero when fitting the scalar mean (0+3+9)/3 = 4. The second feature is the sum of I×M over all four spatial cells. Patterns A, B, C, D have respective counts 0, 1, 2, 3. T2's unmasked ones are at (0,0) and (0,1) but only (0,1) is valid and on. With a copy of T2's stacked array, the basic view into the image channel shares storage with that copied stack. Changing its valid (0,1) entry from 1 to 0 changes the view and the copied stack. A separately copied view, original table array and an integer calculated before the change retain their previous values. Two single-pixel images with different locations under an all-ones mask have the same valid count and cannot be distinguished by that statistic alone.

Using the prescribed feature order, the class centers are (1.5,2) and (6.5,1). For V9 at (3,3), squared distances are 3.25 and 16.25. V4 at (8,0) is class 1 and V7 at (4,3) is predicted class 0. The public key yields [0,1,1] for V9,V4,V7 and accuracy 2/3. Predictions in N7,N3,N1 order are [1,1,0]. Keep learner-written work blank in the released notebook. The public key is available for self-study; the sequence of displays does not authenticate independent human work.

**C. Rectangular masks.** On the worked rectangle, rows [2,4) and columns [4,7) cover 6 of 96 positions. One selected entry is zero, so the nonzero count is 5. On T=[[1,4,7],[2,5,8]], rows [0,2), columns [1,3) give [[4,7],[5,8]], and columns [0,2) give [[1,4],[2,5]]. Their areas coincide but their masks differ. Bottom-right [1,2)×[2,3) is valid and contains 8. A request for all six positions violates the exercise limit of four, row end 3 exceeds height 2, and equal start/end is empty. A robust solution checks these conditions before slicing. The official 224×224 Pixel budget and its performance objective are separate from these small numerical exercises. [Original task](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Pixel/Pixel.ipynb)

## Executable teacher references

The function names below preserve the public interfaces for testing unseen inputs. The plotting reference reads actual bar heights. The label lookup keeps the external request order. The same numerical tests apply to different record names.

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

### Align known and unknown labels by record name

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

### Projection and class ambiguity

All four problems in section 8 are required. For problem 4, collect both the hand calculation and the general function from the student response cell. A correct gallery lookup or a hand calculation on one example does not complete this assignment. In the worked case, keeping only the first column of [(2,6),(2,8),(4,6)] produces exactly one differently labeled equal-input pair at row positions (0,1). Keeping both columns eliminates it. Adding a coordinate cannot turn an already unequal projected pair into an equal one. If the projection and labels contradict for one pair, no deterministic function of those selected features can correctly label both. An empty collision set on these cases is not a generalization result. This is the registered Week 1 transfer interface. The existing gallery lookup is also assessed in section 6.

<!-- teacher-cell: ref-projection -->
```python
def indistinguishable_pairs(case):
    rows = case["features"]
    labels = case["labels"]
    keep = case["keep"]
    projected = [tuple(row[column] for column in keep) for row in rows]
    pairs = []
    for first in range(len(rows)):
        for second in range(first + 1, len(rows)):
            if labels[first] != labels[second] and projected[first] == projected[second]:
                pairs.append([first, second])
    return pairs
```

## Practical reference on a different input

A digit label of zero is valid. Use exact image identifiers in this exercise. The different case/whitespace convention for the separate Antique-inspired example is stated there.

<!-- teacher-cell: ref-digit-lookup -->
```python
def restore_digit_predictions(case):
    by_id = dict(case["records"])
    return [by_id.get(identifier) for identifier in case["requests"]]
```

Reindex by the requested names before reducing. A measured zero contributes one to its column's observed count. A column with no observations has no mean.

<!-- teacher-cell: ref-named-means -->
```python
import pandas as pd


def named_feature_means(case):
    frame = pd.DataFrame(case["values"], columns=case["columns"], dtype=float)
    selected = frame.loc[:, case["keep"]]
    counts = selected.count()
    means = selected.mean()
    return {
        "shape": list(selected.shape),
        "observed": [int(n) for n in counts],
        "means": [None if pd.isna(value) else float(value) for value in means],
    }
```

The denominator is the number of records in the corresponding class. Tick labels and patch heights come directly from the figure. Count mode admits a class with no records.

<!-- teacher-cell: ref-pixel-plot -->
```python
import matplotlib.pyplot as plt
import seaborn as sns


def plot_pixel_frequency(case):
    groups = case["groups"]
    totals = dict.fromkeys(groups, 0)
    hits = dict.fromkeys(groups, 0)
    for group, value in case["rows"]:
        totals[group] += 1
        hits[group] += int(value == case["target"])
    heights = [hits[group] for group in groups]
    if case["unit"] == "percent":
        heights = [100 * hits[group] / totals[group] for group in groups]
    names = [str(group) for group in groups]
    fig, ax = plt.subplots()
    try:
        if case["library"] == "matplotlib":
            ax.bar(names, heights)
        else:
            sns.barplot(x=names, y=heights, order=names, errorbar=None, ax=ax)
        ax.set_xlabel("Digit")
        ax.set_ylabel("Count" if case["unit"] == "count" else "Percent of this class")
        return {
            "groups": [int(label.get_text()) for label in ax.get_xticklabels()] if groups else [],
            "heights": [float(bar.get_height()) for bar in ax.patches],
        }
    finally:
        plt.close(fig)
```
