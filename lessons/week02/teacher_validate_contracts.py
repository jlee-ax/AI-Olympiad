"""Teacher reference checks for the two synthetic contracts; never grade student work.

Reads the actual distributed prompt and computes finite reference cases.
No model accuracy, student performance, or test-set independence is inferred.
"""
import json
import math
from pathlib import Path

notebook_path = Path(__file__).with_name("week02_prediction_evaluation.ipynb")
book = json.loads(notebook_path.read_text(encoding="utf-8"))
prompt = "".join(book["cells"][19]["source"])
rows = {}
for line in prompt.splitlines():
    fields = [part.strip() for part in line.strip().strip("|").split("|")]
    if len(fields) == 5 and fields[0] in {
        "a1", "a2", "b1", "b2", "c6", "c7", "d6", "d7",
        "rX", "rY", "sX", "sY", "tX", "tY", "uX", "uY",
    }:
        rid, group, third, value, label = fields
        assert rid not in rows
        rows[rid] = (group, third, None if value == "결측" else float(value), int(label))
assert len(rows) == 16

practice = {}
for line in prompt.splitlines():
    fields = [part.strip() for part in line.strip().strip("|").split("|")]
    if len(fields) == 5 and fields[0] in {"가", "나"}:
        case, rid, group, slot, value = fields
        assert rid not in practice
        practice[rid] = (case, group, slot, float(value))
assert practice == {
    "w8": ("가", "W", "8", 5.0), "v8": ("가", "V", "8", 1.0),
    "rZ": ("나", "R", "Z", 5.0), "sZ": ("나", "S", "Z", 1.0),
}


def fit_statistics(train):
    observed = [row[2] for row in train if row[2] is not None]
    assert observed
    mean = sum(observed) / len(observed)
    filled = [mean if row[2] is None else row[2] for row in train]
    center = sum(filled) / len(filled)
    variance = sum((x - center) ** 2 for x in filled) / len(filled)
    assert variance > 0
    return mean, center, math.sqrt(variance)


def rule(value, stats):
    mean, center, scale = stats
    value = mean if value is None else value
    return 1 if (value - center) / scale >= 0 else -1


def counts(truth, predictions):
    assert len(truth) == len(predictions) and truth
    assert set(truth) <= {-1, 1} and set(predictions) <= {-1, 1}
    tp = sum(y == 1 and p == 1 for y, p in zip(truth, predictions))
    fp = sum(y == -1 and p == 1 for y, p in zip(truth, predictions))
    tn = sum(y == -1 and p == -1 for y, p in zip(truth, predictions))
    fn = sum(y == 1 and p == -1 for y, p in zip(truth, predictions))
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def metrics(truth, predictions):
    c = counts(truth, predictions)
    return ((c["tp"] + c["tn"]) / len(truth),
            None if c["tp"] + c["fn"] == 0 else c["tp"] / (c["tp"] + c["fn"]))


def evaluate(train_ids, val_ids):
    train = [rows[rid] for rid in train_ids]
    val = [rows[rid] for rid in val_ids]
    stats = fit_statistics(train)
    truth = [row[3] for row in val]
    predictions = {"K": [-1] * len(val), "R": [rule(row[2], stats) for row in val]}
    return stats, predictions, {name: metrics(truth, values) for name, values in predictions.items()}


a_train = ["a1", "a2", "b1", "b2"]
a_val = ["c6", "c7", "d6", "d7"]
b_train = ["rX", "sX", "tX", "uX"]
b_val = ["rY", "sY", "tY", "uY"]
assert set(rows[i][0] for i in a_train).isdisjoint(rows[i][0] for i in a_val)
assert max(int(rows[i][1]) for i in a_train) <= 5
assert min(int(rows[i][1]) for i in a_val) >= 6
assert {rows[i][0] for i in b_train} == {rows[i][0] for i in b_val}
assert {rows[i][1] for i in b_train} == {"X"}
assert {rows[i][1] for i in b_val} == {"Y"}
a_stats, a_pred, a_scores = evaluate(a_train, a_val)
b_stats, b_pred, b_scores = evaluate(b_train, b_val)
assert a_stats[:2] == (2.5, 2.5) and math.isclose(a_stats[2], math.sqrt(19) / 2)
assert b_stats[:2] == (3, 3) and math.isclose(b_stats[2], math.sqrt(5))
assert a_pred == b_pred == {"K": [-1] * 4, "R": [1] * 4}
assert a_scores == b_scores == {"K": (0.75, 0.0), "R": (0.25, 1.0)}
assert max(a_scores, key=lambda name: a_scores[name][0]) == "K"
assert max(b_scores, key=lambda name: b_scores[name][1]) == "R"
assert [-1, -1] == [-1 for rid in ("w8", "v8") if rid in practice]
assert [rule(practice[rid][3], b_stats) for rid in ("rZ", "sZ")] == [1, -1]

# Same fitted state despite validation change; a fit that sees validation is different.
before = fit_statistics([rows[i] for i in a_train])
assert before == fit_statistics([rows[i] for i in a_train])
leaky = fit_statistics([rows[i] for i in a_train + a_val])
assert leaky[0] != before[0]
assert metrics([-1, -1], [-1, 1])[1] is None
assert not set(rows[i][0] for i in a_train).isdisjoint(
    [rows["a1"][0], rows["c6"][0]])
assert max(int(rows[i][1]) for i in a_val) > min(int(rows[i][1]) for i in a_train)

# Different explicit label contract: 0 is known, None is unknown.
labels = [0, 1, None, 0, 1]
predicted = [0, 1, 1, 1, 1]
known = [(y, p) for y, p in zip(labels, predicted) if y is not None]
assert len(known) == 4 and sum(y == 0 for y, _ in known) == 2
assert sum(y == p for y, p in known) == 3

# This sensor contract allows only observations that have already arrived.
events = [(1, 1, 3), (2, 4, 99)]  # observed_at, arrived_at, value
available = lambda t: [value for observed, arrived, value in events
                       if observed < t and arrived <= t]
assert available(3) == [3] and available(4) == [3, 99]

# Compare the separate arithmetic with a library fit on each training set.
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
for ids, expected, val_ids, predictions in (
    (a_train, a_stats, a_val, a_pred["R"]),
    (b_train, b_stats, b_val, b_pred["R"]),
):
    pipe = Pipeline([("imputer", SimpleImputer()), ("scaler", StandardScaler())])
    x_train = [[float("nan") if rows[i][2] is None else rows[i][2]] for i in ids]
    x_val = [[float("nan") if rows[i][2] is None else rows[i][2]] for i in val_ids]
    pipe.fit(x_train)
    assert math.isclose(pipe["imputer"].statistics_[0], expected[0])
    assert math.isclose(pipe["scaler"].mean_[0], expected[1])
    assert math.isclose(pipe["scaler"].scale_[0], expected[2])
    assert [1 if z[0] >= 0 else -1 for z in pipe.transform(x_val)] == predictions
    prior = (pipe["imputer"].statistics_[0], pipe["scaler"].mean_[0], pipe["scaler"].scale_[0])
    pipe.transform([[1000.0]])
    assert prior == (pipe["imputer"].statistics_[0], pipe["scaler"].mean_[0], pipe["scaler"].scale_[0])

print(json.dumps({
    "result": "passed",
    "a_fit": a_stats, "b_fit": b_stats,
    "a_predictions": a_pred, "b_predictions": b_pred,
    "a_accuracy_selection": "K", "b_recall_selection": "R",
    "a_unlabelled": [["w8", -1], ["v8", -1]],
    "b_unlabelled": [["rZ", 1], ["sZ", -1]],
    "zero_positive_recall": "undefined",
    "known_zero_and_unknown_none": "checked",
    "different_observation_and_arrival_times": "checked",
    "scope": "teacher reference and finite controls; student answers and outcomes not observed",
}, ensure_ascii=False, indent=2))
