# Teacher guide · Partially labeled classification and nearest centroids

The mathematical objective is to derive a class mean vector, explain why it minimizes within-class squared distance, and predict the class of a held-out painting. Section 1 starts with the real IOAI 2025 Antique data. Sections 2–4 use small, explicitly synthetic tables for arithmetic and evaluation. The submission material follows the classification exercise. [Student notebook](week01_problem_pipeline.ipynb)

## Reading the official data

In the pinned public training CSV the header is `feature1,feature2,feature3,feature4,feature5,Authenticated`. The statement describes the first five columns as digital features of a painting. It does not identify physical measurements, units or an ID field. The notebook's row numbers count the first data record as 1 and exclude the header. The three quoted records are rounded to three decimal places.

| Data record | Five published features, rounded | Published label |
|---:|---|---:|
| 1 | [0.600, 0.012, 0.209, 1.088, 4.088] | 0 |
| 47 | [−0.534, 4.897, 0.658, 1.269, 3.627] | −1 |
| 142 | [3.188, −2.940, −0.404, 0.737, 3.842] | 1 |

A count of all 500 published records gives 496 unknown, two replicas (rows 47 and 380), and two authentic (rows 142 and 183). A student should distinguish an unknown target from an absent digital feature or a third class of paintings. Antique explicitly asks contestants to use unlabeled training examples. Fitting class centers only on known labels is a supervised baseline. Its four labeled official examples do not establish accuracy on either leaderboard. [Official training CSV at the cited revision](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Antique/training_set/training_set.csv) · [Official Antique statement, §§1–5](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Antique/Antique.ipynb)

The contest supplies training, validation and test sets of 500 distinct samples each. Contestants could access training during the event. Their submitted notebook reads the validation and test features in the scoring environment and produces predictions. The grader has the targets and evaluates each set's accuracy. In contrast, the pinned 2026 Potato statement explicitly supplies no labeled training split. It supplies a vocabulary, public embeddings and public games for testing a strategy. Output consists of the next word proposed to the interactive judge. The leaderboard games and the judge's representation are hidden. [Potato, Task, Dataset, Output and Metric](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md)

## Working through the theory

**Complete the training vectors.** The two-coordinate teaching table is synthetic. T, V, A and B label groups of classroom records. A row ID identifies the same painting when row order changes. In this supervised example, fit the mean imputer and classifier only on T1–T4. T2's missing second feature becomes (1+3+5)/3=3. The first-feature imputation value is (1+3+7+9)/4=5. T5 has both features but its target is unknown.

**Derive the center.** The replica vectors [1,1], [3,3] average to [2,2]. The authentic vectors [7,3], [9,5] average to [8,4]. In one dimension the sum of squared distances from 1 and 3 to any representative a is 2(a−2)²+2. For arbitrary training values with mean m, expanding (xᵢ−m+m−a)² and summing cancels the cross term because Σ(xᵢ−m)=0. The sum for representative a equals the sum for m plus n(m−a)². Each coordinate contributes its own sum, so choosing the mean in each coordinate minimizes the total within that class. Ask the learner to identify which term changes when a changes. This is a statement about squared distances inside a group. Classification errors still depend on how the two groups overlap.

**Predict and examine the boundary.** For the new vector [6,3], squared distances to replica and authentic centers are 17 and 5. Predict +1. For a general [x,y], subtracting the authentic squared distance from the replica squared distance gives 12x+4y−72. Thus 3x+y=18 at a tie. The example [5.25,3] has squared distances 11.5625 and 8.5625. After refitting a separate model with T4's first feature changed from 9 to 11, the authentic center moves to [9,4], its distance becomes 15.0625, and the prediction switches from +1 to −1. The original model's center remains [8,4]. Multiplying one feature by 10 multiplies its squared-difference contribution by 100, so the assumption about feature scales matters. None of the specified predictions is tied.

**Evaluate with unseen labels.** At `f265b556`, the four synthetic validation rows contain only identifiers and features. V4 receives the training mean 5 for its missing first feature. Predictions for V1,V2,V3,V4 are −1,+1,+1,+1. At `worked-score` the separately ordered key is joined by ID. V3 is the only error, so accuracy is 3/4. Changing a validation feature and calling `predict` leaves training means and centers intact. Including held-out records in the imputation mean leaks information even when their labels are omitted. The worked output is visible. Use Section 4 to collect a student's first independent response.

## Independent three-feature classification

Start at `bb177697` and run `f53ccb1f`. This is a second synthetic table of paintings, with changed records, three features, different column orders and a different encoding. Its records do not appear in the official competition files. The `item` string identifies one painting. Prefixes R, V and J distinguish its training, validation and additional inputs. `feature1`, `feature2` and `feature3` are equal-scale numerical coordinates. `label=0` means replica, 1 authentic, and −1 unknown. The training-only `verified_label` contains the result once authentication is complete. At prediction time it is unavailable. Including it would directly disclose the outcome.

Use R1–R4. R5 remains unconfirmed and supplies neither targets nor learned preprocessing under this exercise's stated supervised policy. With columns ordered 1,2,3 the imputation means are [4,4,2]. The second-feature mean uses three observed values, (2+4+6)/3=4. After imputation the two replica vectors [0,2,0] and [2,4,2] have center [1,3,1]. The two authentic vectors [6,4,2] and [8,6,4] have center [7,5,3]. V3 is [5,4,1]. Its squared distances are (5−1)²+(4−3)²+(1−1)²=17 and (5−7)²+(4−5)²+(1−3)²=9. Predict 1 before opening the key. The validation label later identifies it as a replica. Mark the derivation and the diagnosis separately. A classification error on V3 is compatible with a correct centroid calculation.

First validation predictions are V1→0, V2→1, V3→1. The key is intentionally ordered V3→0, V1→0, V2→1. Comparing by ID gives 2/3 and identifies V3 as the error. Comparing by position happens to give the same fraction but incorrectly blames V2. Ask for the error ID as well as the fraction. An alternative trained classifier can be tested as an extension after the student has derived and evaluated the specified nearest-centroid result.

### Reference code for fitting and prediction

The first block runs after the Section 4 setup and before opening any validation key. Use a separate working directory for these teacher examples.

```python
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline

feature_columns = ["feature1", "feature2", "feature3"]
known_paintings = exercise_train.loc[exercise_train["label"].isin([0, 1])]
exercise_model = Pipeline([("fill", SimpleImputer(strategy="mean")),
                         ("classifier", NearestCentroid())])
exercise_model.fit(known_paintings[feature_columns], known_paintings["label"])

def predict_paintings(table, value_column):
    required = ["item"] + feature_columns
    missing = [column for column in required if column not in table]
    if missing:
        raise ValueError("Missing required columns " + ", ".join(missing))
    ids = table["item"]
    if not all(isinstance(item, str) and item.strip() for item in ids) or ids.duplicated().any():
        raise ValueError("Each painting needs one distinct, nonempty item ID")
    values = exercise_model.predict(table[feature_columns])
    return pd.DataFrame({"item": ids.to_numpy(), value_column: values})

first_predictions = predict_paintings(exercise_validation, "prediction")
audit_rows = predict_paintings(exercise_input, "signal")
```

## Optional file exercise

In Antique's actual submission each headerless CSV contains one binary label per original input position. The classroom ordering example adds IDs to show how predictions stay attached to paintings. It can be read and run in isolation at `pipeline-submit` / `order-by-hand`. Original A order is A05,A08,A02. Computation order A08,A02,A05 yields +1,−1,−1, which restores to −1,+1,−1. The B file restores to −1,+1. Swapping unequal predictions changes which painting receives which result, even if every label is legitimate and the row count is correct. Two equal numeric predictions alone cannot reveal that their corresponding rows were exchanged.

The independent exercise uses a **separate classroom format** with a header and two columns. The fitted model gives J3→1, J1→0, J2→0. Row order J1,J2,J3 gives 0,0,1. Changing J1's feature vector to [7,5,3] changes its predicted label to 1. A missing cell uses a training mean. A missing required feature column or duplicated ID is an input error. Use the following second block to write and reopen `audit.csv` in a separate directory. Checking the CSV's records also detects an extra field on every line, an empty record, a missing header, or a valid label assigned to the wrong painting. Quoted IDs and leading zeros are preserved.

```python
import csv
from tempfile import TemporaryDirectory

def verify_audit(path, input_items, predictions):
    input_items = list(input_items)
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            header = next(reader, None)
            records = list(reader)
        except csv.Error as error:
            raise ValueError("Invalid CSV quoting") from error
    if header != ["item", "signal"]:
        raise ValueError("Wrong header")
    if len(records) != len(input_items) or any(len(row) != 2 for row in records):
        raise ValueError("Expected one record with two fields for each painting")
    saved = pd.DataFrame(records, columns=header)
    if saved["item"].tolist() != input_items:
        raise ValueError("Wrong order of items")
    if not saved["signal"].isin(["0", "1"]).all():
        raise ValueError("Signals must be 0 or 1")
    expected = predictions.set_index("item")["signal"].astype(str)
    if saved["signal"].tolist() != [expected.at[item] for item in saved["item"]]:
        raise ValueError("A prediction was attached to the wrong painting")
    return saved

audit_path = Path("audit.csv")
audit_rows.to_csv(audit_path, index=False)
verify_audit(audit_path, exercise_input["item"], audit_rows)

reordered = exercise_input.iloc[[1, 2, 0]]
reordered_rows = predict_paintings(reordered, "signal")
with TemporaryDirectory() as folder:
    second_path = Path(folder) / "audit.csv"
    reordered_rows.to_csv(second_path, index=False)
    verify_audit(second_path, reordered["item"], audit_rows)
```

A valid `audit.csv` for the unaltered three J records contains the following text.

```csv
item,signal
J3,1
J1,0
J2,0
```

The A/B ZIP extension writes two actual one-column CSVs into a temporary `submission.zip`, reopens the file, checks predictions against the recorded associations, and removes the temporary folder. No official data or leaderboard submission is executed by that demonstration.

## Releasing the independent validation key

The comment-only student cells `06ceb97e` and `device-score-work` separate first predictions from scoring. Running the unchanged notebook does not open the independent key, populate predictions or create `audit.csv`. The student supplies `first_predictions` with exactly `item,prediction` columns, all three distinct validation IDs and integer values in {0,1}. The feedback cell copies these to `recorded_first_predictions` before opening the key. If the local file is absent, the first attempt remains available for a later retry. Reordering a prediction table preserves its associations. Replacing a recorded prediction on rerun raises an error.

The public key has columns `item,label`. It contains only the three independent validation labels. The learner can set `validation_key_path` to an explicitly supplied file. The check matches IDs before displaying `validation_comparison`. This public file and the teacher guide are accessible before an attempt. For an independent assessment, use unseen equivalent records and collect the calculation and initial predictions before releasing the corresponding key. The notebook snapshot lasts for the current kernel session. There are no final test labels for J3,J1,J2. [Published self-check file](data/pipeline_device_validation.csv)

## Place in the course

A learner who can average a short list and read two columns can enter at Section 1. For new classifiers work through the two-coordinate derivation and held-out error before assigning Section 4. A learner already familiar with fitting a classifier may enter directly at the independent exercise. Use the optional filing section only when row correspondence needs practice. A three-feature exercise cannot replace the core array, function, new CSV, merge or plotting tasks.

The plan allocates 20 minutes of theory, 20 minutes of noncoding work including 10 written minutes, and 80 minutes of coding in Week 1. Its required outside-work estimate is 5–7 hours. Treat the worked classifier or independent transfer as selected practice. Assigning every route increases workload. Additional time for new notation, programming help and feedback, and real learner outcomes are unmeasured. Week 2 develops splits, preprocessing and evaluation more fully, Week 4 develops classification and model selection, and Week 10 applies these skills to an unfamiliar problem. [Ten-week plan](../../curriculum/student-plan.html) · [Course contract](../../curriculum/contract.json)

KOAI 2027 covers sections 1–4 of the linked syllabus, labeled IOAI 2026, for both divisions. The 2025 Antique and 2026 Potato tasks are past international individual problems. The source review on 2026-11-20 establishes their published constraints. [Official 2027 rules, §§11–12](https://kitpa.org/storage/6df0e67a-48d7-4255-ba4f-7d86b2bd2824.pdf) · [Official syllabus](https://kitpa.org/koai/syllabus)

Scikit-learn's semi-supervised interface uses −1 for unknown targets. Encoding Antique replica −1→0, authentic 1→1 and unknown 0→−1 avoids the collision. The predicted class codes must be decoded for the competition file. Actually learning from the unlabeled feature distribution is a separate modeling task. [Semi-supervised learning](https://scikit-learn.org/stable/modules/semi_supervised.html) · [NearestCentroid](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestCentroid.html) · [Train-only preprocessing](https://scikit-learn.org/stable/common_pitfalls.html)
