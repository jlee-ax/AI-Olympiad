# Teacher guide · Reading a new task and producing its predictions

A student coming from the integrated notebook with an ordering question needs just the three rows in Section 4. A student opening this companion on its own can follow the model in Sections 1–3 or enter the fresh device task in Section 5. Every device table is constructed in its own setup cell. [Student notebook](week01_problem_pipeline.ipynb) · [Integrated Week 1](week01_integrated.ipynb)

## Choose an entry and a stopping point

| Student need | Use | Evidence to bring back |
|---|---|---|
| A position, an identifier and a prediction have become confused. | Section 4, cells `ecb6bc7a` through `3d1ecace`, works in a fresh kernel with Python alone. | Three values in the requested order and the two IDs whose assignments would otherwise change. Return to the integrated matching exercise. |
| A student can read a table and take a mean but wonders what a model learns. | Sections 1–3. Ask for the second center, one prediction and the source of the missing-value replacement before showing the worked output. | The two class representatives and an explanation of why changing training can alter a prediction while calling `predict` leaves the learned quantities intact. |
| A student can fit a small classifier and needs an unfamiliar instruction to interpret. | Section 5, from `bb177697`. Give the device brief and data with earlier examples closed. Collect the student's description, predictions, CSV and changed-order check before giving feedback. | One row and its prediction deadline, a reason to exclude a tempting field, a training-only calculation, first validation predictions, and an actual reopened `audit.csv`. |
| A student asks how a submission checker could miss an error. | The final, optional file experiment uses the model from Sections 1–3. Inspect one damaged archive against the intact one. | Identify whether the failure concerns parsing, number of rows, or which item's prediction occupies a row. |

The Week 1 plan allocates 20 minutes of theory, 20 minutes of noncoding work including 10 written minutes, and 80 coding minutes. Required outside work is estimated at 5–7 hours. Section 4 can occupy the existing order-repair portion of an ID exercise. As planning estimates, allow 3–6 minutes for that detour, 15–25 minutes for the worked model, or 25–45 minutes for a student already able to fit a classifier to attempt the device task. Choose according to need. Assigning all three plus the archive adds workload. The two Week 1 independent model options share subject matter. If the integrated optional device task already provides the evidence required, return to the core. Neither model option supplies the required array, function, new CSV, merge or plotting products. Record actual time, help and unfinished work. These estimates have no classroom timing or learner-outcome data. [Ten-week student plan](../../curriculum/student-plan.html) · [Course contract](../../curriculum/contract.json)

The core Week 1 work uses Python, NumPy, pandas and plotting. A nearest-centroid model is an optional application of means and named columns. The plan places scikit-learn and systematic splitting, preprocessing and evaluation from Week 2, classification models and selection in Week 4, and independent work from a new brief in Week 10. Full semi-supervised optimization and competition readiness exceed the evidence from this companion. [Course contract](../../curriculum/contract.json)

## Worked painting example

- The contest's training label 0 means unknown. Guessing a label for such a painting can change the training target without new evidence about authenticity. The local rule learns both its imputation values and its centers from T1–T4 only. A different procedure could use unlabeled *training features* under the original task's rules. Excluding T5 is a declared simplification of this particular classifier.
- T2 is missing its color measurement. The known training means are [(1+3+7+9)/4, (1+3+5)/3] = [5,3]. After filling T2, the class centers in label order −1,+1 are [2,2] and [8,4]. With this equal-scale Euclidean example, the squared distances from [6,3] are 17 and 5. Predict +1. With a different unit conversion the dimensions can contribute differently.
- Refitting a second model after changing T4's first feature from 9 to 11 gives imputation values [5.5,3] and a positive center [9,4]. The same [5.25,3] receives +1 from the original and −1 from the refitted model. In the separate verification experiment changing V1 and calling `predict` leaves the original imputation values and centers intact.
- At `f265b556`, validation contains only IDs and features. Predictions for V1,V2,V3,V4 are −1,+1,+1,+1. The following `worked-score` cell joins the shuffled classroom key by ID. V3 is wrong, so 3 of 4 match. V4 used the training texture mean 5. The demonstration deliberately reveals the comparison after the first model output. Its published worked output is readable. Use Section 5 for a fresh attempt.
- Section 4 receives pairs A08→1, A02→−1 and A05→−1. The classroom request A05,A08,A02 therefore gets −1,+1,−1. Copying the input column assigns different results to A05 and A08. B04,B09 receive −1,+1. These are comparisons with the model's recorded predictions. A/B have no classroom ground truth. Official Antique has no added ID field or separate request-order list. When a file has only positions, capture original row positions before shuffling and restore them before export.

The short Potato prompt asks for a decision before choosing a method. Antique supplies known authentication targets in its training rows and also asks for the use of unknown-label examples. Potato supplies a vocabulary, public word representations and public test games with answers for self-scoring. Its statement explicitly supplies no training split of labeled rows. A player's next proposal is a vocabulary word informed by the judge's comparisons. The leaderboard words and judge's representation are hidden. A public self-check can guide strategy but does not supply an official held-out result. Accept an answer that cites this distinction without implementing the game or making a blanket claim that all learning is forbidden. [IOAI 2026 Potato, Task, Dataset, Output and How to submit](https://github.com/IOAI-official/IOAI-2026/blob/e1963801aa4cf33a5a03520b39fa6620a7894c54/Individual-Contest/3_Potato/statement.md)

## Independent device task

A defensible reading explains that one observation is one device and the decision is made on arrival, before inspection or service. A historical receipt number can track the eventual outcome closely. Its future availability rules it out. The model can use vibration, sound and heat. The item identifies the row, while the later label supplies the training target. Learning with `label != 0` would discard the genuine normal devices and admit R5 as if “unconfirmed” were a class. The delivered J rows never include the receipt or target.

For the supervised policy in this brief, use R1,R2,R3,R4. Exclude R5 from both learned preprocessing and the target. In feature order vibration, sound, heat the known means are [4,4,2]. The sound mean has three observed terms (2+4+6)/3, even though there are four known training items. With nearest centroids the centers are [1,3,1] and [7,5,3]. Other legitimate learned classifiers may give different predictions. Evaluate the available features, actual fit, named order, validation denominator and serialization against the student's chosen model.

The delivery tables have deliberately different column orders. A positional slice can select the target or receipt from the history or present the wrong quantities to the model at prediction. A missing required column calls for a clear error or a corrected file. A missing sensor cell uses that sensor's training mean. A repeated or empty item ID prevents a one-to-one file check.

### A runnable reference solution

Use this example in a separate working directory containing the exercise's setup data. The first block fits the model and produces a prediction-only validation table before any key is opened. It also produces the predictions that will be written to disk.

```python
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline

sensor_columns = ["vibration", "sound", "heat"]
known_device = exercise_train.loc[exercise_train["label"].isin([0, 1])]
device_model = Pipeline([("fill", SimpleImputer(strategy="mean")),
                         ("classifier", NearestCentroid())])
device_model.fit(known_device[sensor_columns], known_device["label"])

def predict_devices(table, value_column):
    required = ["item"] + sensor_columns
    missing = [column for column in required if column not in table]
    if missing:
        raise ValueError("Missing required columns " + ", ".join(missing))
    ids = table["item"]
    if not all(isinstance(item, str) and item.strip() for item in ids) or ids.duplicated().any():
        raise ValueError("Each device needs one distinct, nonempty item ID")
    values = device_model.predict(table[sensor_columns])
    return pd.DataFrame({"item": ids.to_numpy(), value_column: values})

first_device_predictions = predict_devices(exercise_validation, "prediction")
audit_rows = predict_devices(exercise_input, "signal")
```

The second block tests the actual file after reading it back and checks a second input order. Parsing CSV records before constructing the table preserves identifiers with leading zeros and quoted commas, rejects extra fields and blank records, and catches changes such as `1.0` where the specification requires the integer text `1`. Each saved value is compared with the prediction recorded for that item.

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
        raise ValueError("Expected one record with two fields for each device")
    saved = pd.DataFrame(records, columns=header)
    if saved["item"].tolist() != input_items:
        raise ValueError("Wrong order of items")
    if not saved["signal"].isin(["0", "1"]).all():
        raise ValueError("Signals must be 0 or 1")
    expected = predictions.set_index("item")["signal"].astype(str)
    if saved["signal"].tolist() != [expected.at[item] for item in saved["item"]]:
        raise ValueError("A prediction was attached to the wrong device")
    return saved

audit_path = Path("audit.csv")
audit_rows.to_csv(audit_path, index=False)
verify_audit(audit_path, exercise_input["item"], audit_rows)

reordered = exercise_input.iloc[[1, 2, 0]]
reordered_rows = predict_devices(reordered, "signal")
with TemporaryDirectory() as folder:
    second_path = Path(folder) / "audit.csv"
    reordered_rows.to_csv(second_path, index=False)
    verify_audit(second_path, reordered["item"], audit_rows)
```

For this model the first validation predictions are V1→0, V2→1, V3→1. Compare with the shuffled key V3→0, V1→0, V2→1 by item. Two of three are correct, and the missed item is V3. Pairing by row position also happens to give 2/3 with these first predictions, but it falsely blames V2. A student should identify the device as well as the fraction. In the original input order the file reads as follows.

```csv
item,signal
J3,1
J1,0
J2,0
```

The changed order J1,J2,J3 gives 0,0,1. For a new-value check, keep J1's ID and give it the sensor vector [7,5,3] in model feature order. The fitted centroid model now predicts 1 for J1. The duplicate-ID test and the missing-column test check different conditions. A candidate with valid 0/1 values but reversed predictions fails the recorded ID/value comparison on J3 and J2. If all observed outputs happen to agree, a swap of equal labels cannot establish or refute row correspondence. Inspect where IDs and model outputs were bound or try inputs giving different labels.

### Releasing validation feedback

The student answer cell `06ceb97e` starts empty. In a fresh kernel, an unchanged Run All does not read the device key or produce device predictions, a score, or `audit.csv`. The setup `f53ccb1f` and the raw tables support an entry directly at Section 5. The student supplies a DataFrame named `first_device_predictions` with exactly `item,prediction`. Row order is free. The release cell `device-score-release` requires the three distinct, expected IDs and integer labels in {0,1}. A full first table is copied to the immutable `recorded_device_predictions` tuple before any key file is opened. A missing file leaves that snapshot available for a later retry. Reordering the submitted table leaves the recorded associations intact. Changing a recorded value causes an error on rerun.

The key has columns `item,label` and is intentionally ordered V3,V1,V2. By default it goes in `data/` relative to the notebook's working directory. The student can set `device_key_path` to a teacher-supplied file. The comparison checks the key's complete ID set and joins the frozen predictions by ID. The student counts the matching devices, names an error, and distinguishes first-attempt evidence from later model changes. A smaller or duplicated table must not quietly change the denominator. [Public validation CSV](data/pipeline_device_validation.csv)

The public self-check and this guide are readable ahead of time. For independent assessment distribute an unseen equivalent, hold its key outside the student materials, and collect the first prediction file and rationale before releasing it. Record any help already seen and whether the work was independent, prompted, or copied from an example. In a self-study notebook the snapshot lasts for the current kernel. A reset or direct access to the public key remains possible. No final J labels are distributed. Student performance and workload have not been observed.

## File extension and primary sources

The optional extension packs two actual headerless files and reopens a temporary `submission.zip`. It rejects a missing feature, missing or duplicated ID, an unknown-label output, a swapped sequence of differing labels of the same length, an extra header and a short file. Inspecting a headerless CSV verifies the recorded mapping only if that mapping was trustworthy in the first place. No official dataset is run or submitted in this lesson.

Source check on 2026-11-20. The KOAI 2027 rules cover sections 1–4 for both divisions of the online written and coding examination. The linked syllabus is headed IOAI 2026 and places Python, NumPy/pandas and plotting in its practical programming foundations. Sections 1–3 of this companion are an instructional choice within the ten-week plan. [Official rules, §§11–12, pp. 7–8](https://kitpa.org/storage/6df0e67a-48d7-4255-ba4f-7d86b2bd2824.pdf) · [Official syllabus, §§1-1 and 1-4](https://kitpa.org/koai/syllabus)

In the 2025 international individual problem, training, validation and test each comprise 500 independent paintings. The first five training columns contain features. The sixth holds 1, −1 or 0. The task expressly asks contestants to leverage unknown-label samples. Validation and test feature files are unavailable directly to contestants during the contest. The submitted notebook loads them in the scoring environment. It generates a ZIP with headerless `submissionA.csv` and `submissionB.csv` in the corresponding input-row order. Each entry is −1 or 1. Accuracy is computed separately for the two sets. The published baseline randomly assigns signs to unknown targets before fitting an SVM. That supplies a runnable comparison and cannot turn a guess into an observed authentication. This is a past international problem and does not predict the 2027 Korean middle-school questions. [Pinned IOAI Antique notebook, §§1–6 and baseline](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Antique/Antique.ipynb)

In scikit-learn's semi-supervised interface −1 denotes an unlabeled target. One explicit inbound mapping is replica −1→0, authentic +1→1 and unknown 0→−1. Predicted classes 0 and 1 must be decoded to −1 and +1 for Antique. The mapping addresses a representational collision. Choice of algorithm and the assumptions that allow an unlabeled feature distribution to help are further work. [Semi-supervised learning](https://scikit-learn.org/stable/modules/semi_supervised.html) · [NearestCentroid](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestCentroid.html) · [Train-only preprocessing](https://scikit-learn.org/stable/common_pitfalls.html)
