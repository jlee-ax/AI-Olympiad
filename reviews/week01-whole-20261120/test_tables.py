"""Regression checks for the Week 1 foundation's worked examples."""
import json
from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import load_digits


WEEK = Path(__file__).resolve().parents[2] / "lessons" / "week01"


class FoundationExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook = json.loads((WEEK / "week01_python_tables.ipynb").read_text())
        cls.code = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]
                    if cell["cell_type"] == "code"}

    def setUp(self):
        self.namespace = {"pd": pd, "np": np, "plt": plt,
                          "display": lambda *objects: None}
        self.addCleanup(plt.close, "all")

    def run_cell(self, cell_id):
        with redirect_stdout(StringIO()):
            exec(compile(self.code[cell_id], cell_id, "exec"), self.namespace)

    def test_named_table_landing_runs_from_an_empty_namespace(self):
        self.namespace = {}
        self.run_cell("3468f4e4")
        namespace = self.namespace
        source = load_digits(as_frame=True)
        indices = [7, 2, 11]
        names = ["pixel_2_3", "pixel_4_4"]
        expected = source.data.loc[indices, names].to_numpy()
        self.assertEqual(namespace["sample_indices"], indices)
        self.assertEqual(namespace["pixel_features"], names)
        self.assertEqual(namespace["sample_targets"], source.target.loc[indices].tolist())
        np.testing.assert_array_equal(namespace["H"], expected)
        self.assertEqual(namespace["H"][1, 0], source.images[2, 2, 3])
        np.testing.assert_allclose(expected.mean(axis=0), [9, 46/3])
        np.testing.assert_allclose(expected.mean(axis=1), [7.5, 14, 15])

    def test_public_csv_inputs_keep_measured_features_and_shuffled_labels(self):
        self.namespace = {}
        self.run_cell("digits-practice-csv")
        source = load_digits(as_frame=True)
        left = pd.read_csv(StringIO(self.namespace["measure_csv"])).set_index("sample_index")
        labels = pd.read_csv(StringIO(self.namespace["labels_csv"])).set_index("sample_index")
        self.assertEqual(left.index.tolist(), [47, 10, 56, 30, 21, 36])
        self.assertEqual(labels.index.tolist(), left.index.tolist()[::-1])
        np.testing.assert_array_equal(left, source.data.loc[left.index, left.columns])
        np.testing.assert_array_equal(labels["digit"], source.target.loc[labels.index])
        joined = left.join(labels, validate="one_to_one")
        self.assertNotEqual(labels["digit"].tolist(), joined["digit"].tolist())
        np.testing.assert_allclose(joined.groupby("digit")["pixel_2_3"].mean(), [22/3, 14])
        np.testing.assert_array_equal(np.histogram(left["pixel_2_3"], [0, 8, 12, 16])[0],
                                      [1, 2, 3])

    def test_selection_rejects_ambiguous_source_and_request(self):
        self.run_cell("14425637")
        select = self.namespace["require_columns"]
        repeated = pd.DataFrame([["Q1", 8, 3]], columns=["id", "measure", "measure"])
        self.assertEqual(select(repeated, ["id"]).columns.tolist(), ["id"])
        with self.assertRaisesRegex(ValueError, "measure"):
            select(repeated, ["measure"])
        unique = pd.DataFrame([["Q1", 8]], columns=["id", "measure"])
        self.assertEqual(select(unique, ["measure", "id"]).iloc[0].tolist(), [8, "Q1"])
        with self.assertRaisesRegex(ValueError, "measure"):
            select(unique, ["measure", "measure"])
        with self.assertRaisesRegex(KeyError, "missing"):
            select(repeated, ["missing"])

    def test_feature_contrasts_follow_named_inputs_and_source_indices(self):
        self.run_cell("14425637")
        self.run_cell("8e3a1c92")
        self.run_cell("fixed-prediction-matrix-example")
        calculate = self.namespace["pixel_contrasts"]
        source = load_digits(as_frame=True).frame.loc[[14, 0, 7]].copy()
        changed = source.iloc[::-1, ::-1].copy()
        changed.loc[14, "pixel_4_4"] = np.nan
        changed.loc[0, "pixel_2_3"] += 3
        changed["target"] = 99
        for table in (source, changed):
            result = calculate(table)
            self.assertEqual(result.index.tolist(), table.index.tolist())
            expected = table["pixel_2_3"] - table["pixel_4_4"]
            np.testing.assert_allclose(result, expected, equal_nan=True)

    def test_scatterplots_show_correct_pairs_and_equal_marginals(self):
        self.run_cell("48d931b0")
        first, second = self.namespace["fig"].axes
        panels = []
        for axis in (first, second):
            by_id = {label.get_text(): tuple(label.xy) for label in axis.texts}
            plotted = Counter(tuple(xy) for group in axis.collections
                              for xy in group.get_offsets())
            self.assertEqual(plotted, Counter(by_id.values()))
            panels.append(by_id)
        original, alternative = panels
        source = load_digits(as_frame=True)
        expected = {f"i={i}": (source.images[i, 2, 3], source.images[i, 3, 5])
                    for i in (0, 20, 48, 1, 11, 42)}
        self.assertEqual(original, expected)
        self.assertEqual(original.keys(), alternative.keys())
        self.assertEqual({key: point[0] for key, point in original.items()},
                         {key: point[0] for key, point in alternative.items()})
        self.assertEqual(Counter(point[1] for point in original.values()),
                         Counter(point[1] for point in alternative.values()))
        self.assertEqual({key for key in original if original[key] != alternative[key]},
                         {"i=20", "i=1"})
        self.assertEqual(first.get_xlim(), second.get_xlim())
        self.assertEqual(first.get_ylim(), second.get_ylim())


if __name__ == "__main__":
    unittest.main()
