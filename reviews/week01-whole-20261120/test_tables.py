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


WEEK = Path(__file__).resolve().parents[2] / "lessons" / "week01"


class FoundationExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook = json.loads((WEEK / "week01_python_tables.ipynb").read_text())
        cls.code = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]
                    if cell["cell_type"] == "code"}

    def setUp(self):
        self.plants = pd.read_csv(WEEK / "data" / "week1_plants.csv")
        self.namespace = {"pd": pd, "np": np, "plt": plt, "plants": self.plants,
                          "display": lambda *objects: None}
        self.addCleanup(plt.close, "all")

    def run_cell(self, cell_id):
        with redirect_stdout(StringIO()):
            exec(compile(self.code[cell_id], cell_id, "exec"), self.namespace)

    def test_named_table_landing_runs_from_an_empty_namespace(self):
        self.namespace = {}
        self.run_cell("3468f4e4")
        namespace = self.namespace
        self.assertEqual(namespace["pot_ids"], ["K8", "K2", "K5"])
        self.assertEqual(namespace["day_columns"], ["mon_cm", "fri_cm"])
        heights = namespace["H"]
        source_row = namespace["height_days"].set_index("pot_id").loc["K2"]
        self.assertEqual(heights[1, 0], source_row["mon_cm"])
        np.testing.assert_allclose(heights.mean(axis=0), [4, 11])
        np.testing.assert_allclose(heights.mean(axis=1), [6, 9, 7.5])

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

    def test_predictions_follow_the_source_rows_columns_and_measurements(self):
        self.run_cell("14425637")
        source = self.plants.iloc[::-1, ::-1].copy()
        source.loc[source.pot_id == "P02", "water_ml"] = 50.0
        source.loc[source.pot_id == "P01", "sunlight_hours"] = np.nan
        source["height_cm"] = 999.0
        for table in (self.plants, source):
            with self.subTest(ids=table["pot_id"].tolist()):
                self.namespace["plants"] = table
                self.run_cell("fixed-prediction-matrix-example")
                rows = [row for row in table.itertuples()
                        if row.pot_id in {"P01", "P02", "P04"}]
                expected = [4.0 + row.sunlight_hours + 0.1 * row.water_ml for row in rows]
                self.assertEqual(self.namespace["model_ids"], [row.pot_id for row in rows])
                np.testing.assert_allclose(self.namespace["fixed_predictions"],
                                           expected, equal_nan=True)

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
        expected = {row.pot_id: (row.sunlight_hours, row.height_cm)
                    for row in self.plants.itertuples()}
        self.assertEqual(original, expected)
        self.assertEqual(original.keys(), alternative.keys())
        self.assertEqual({key: point[0] for key, point in original.items()},
                         {key: point[0] for key, point in alternative.items()})
        self.assertEqual(Counter(point[1] for point in original.values()),
                         Counter(point[1] for point in alternative.values()))
        self.assertEqual({key for key in original if original[key] != alternative[key]},
                         {"P01", "P06"})
        self.assertEqual(first.get_xlim(), second.get_xlim())
        self.assertEqual(first.get_ylim(), second.get_ylim())


if __name__ == "__main__":
    unittest.main()
