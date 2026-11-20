"""Exercise the Week 1 bridge examples and its published teacher references."""

import contextlib
import io
from itertools import permutations
import json
from pathlib import Path
import re
import unittest

import numpy as np


LESSON = Path(__file__).resolve().parents[2] / "lessons" / "week01"
STEM = "week01_axes_linear_bridge"


class AxesBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        book = json.loads((LESSON / (STEM + ".ipynb")).read_text(encoding="utf-8"))
        cls.cells = book["cells"]
        cls.source = {cell["id"]: "".join(cell["source"]) for cell in book["cells"]}
        cls.ns = {"np": np}
        with contextlib.redirect_stdout(io.StringIO()):
            for cell_id in (
                "ba428b91", "5ebb633b", "ae4dc17f", "cb88ba54", "e9bd32e9", "3950021e", "retrieval-norm-code",
                "d81386f3", "sequence-mean-code", "ec433d3b", "07c93362",
            ):
                exec(compile(cls.source[cell_id], cell_id, "exec"), cls.ns)
        guide = (LESSON / (STEM + "_teacher.md")).read_text(encoding="utf-8")
        for code in re.findall(r"^```python\n(.*?)^```$", guide, flags=re.M | re.S):
            exec(compile(code, STEM + "_teacher.md", "exec"), cls.ns)

    def test_linked_sections_start_in_fresh_namespaces(self):
        for anchor in ("bridge-axes", "bridge-scores"):
            with self.subTest(anchor=anchor), contextlib.redirect_stdout(io.StringIO()):
                start = next(i for i, cell in enumerate(self.cells)
                             if f'<a id="{anchor}">' in self.source[cell["id"]])
                fresh = {}
                for i, cell in enumerate(self.cells[start:], start):
                    source = self.source[cell["id"]]
                    if i > start and cell["cell_type"] == "markdown" and re.search(r"^## ", source, re.M):
                        break
                    if cell["cell_type"] == "code":
                        exec(compile(source, cell["id"], "exec"), fresh)
                if anchor == "bridge-axes":
                    self.assertEqual(fresh["image_ids"][1], 52)
                    self.assertEqual(fresh["X"][1, 0], 60)
                    self.assertEqual(fresh["first_image"] @ fresh["average_weights"], 50)
                else:
                    self.assertEqual(fresh["matched_ids"].tolist(), [19, 7])
                    self.assertEqual(fresh["counts"].ravel().tolist(), [2, 3])

        for cell_id in ("51e17d9e", "ec433d3b", "07c93362"):
            with self.subTest(cell=cell_id), contextlib.redirect_stdout(io.StringIO()):
                fresh = {}
                exec(compile(self.source[cell_id], cell_id, "exec"), fresh)
                self.assertIn("np", fresh)

    def test_choose_a_cell_that_can_distinguish_the_operations(self):
        by_element = self.ns["by_position"]
        by_rule = self.ns["by_rule"]
        np.testing.assert_array_equal(np.diag(by_element), np.diag(by_rule))
        self.assertIn("[1, 0]", self.source["25e2b1ff"])
        self.assertEqual((by_element[1, 0], by_rule[1, 0]), (0, 60))

    def test_grayscale_matrix_uses_named_axes_and_signed_contrast(self):
        image_ids, x, w, y = (self.ns[name] for name in ("image_ids", "X", "W", "Y"))
        np.testing.assert_array_equal(image_ids, [17, 52, 8])
        np.testing.assert_array_equal(x[:, 0], [20, 60, 40])
        np.testing.assert_array_equal(w, [[.5, -1], [.5, 1]])
        np.testing.assert_array_equal(y, [[50, 60], [45, -30], [80, 80]])
        # Equal means alone cannot reveal reversed input columns.
        wrong = x[:, ::-1] @ w
        np.testing.assert_array_equal(wrong[:, 0], y[:, 0])
        np.testing.assert_array_equal(wrong[:, 1], -y[:, 1])
        np.testing.assert_array_equal(x[:, ::-1] @ w[::-1], y)
        with self.assertRaises(ValueError):
            x @ x

    def test_rgb_outputs_follow_the_named_channels_and_image_ids(self):
        transform = self.ns["image_features"]
        ids, names, x = (self.ns[k] for k in ("image_ids_new", "channel_names", "X_new"))
        self.assertEqual(x.dtype, np.uint8)
        expected = [[12, 8], [-9, 7], [5, 5]]
        for order in permutations(range(3)):
            ordered = list(order)
            result = transform(ids, [names[i] for i in ordered], x[:, ordered])
            self.assertEqual([r[0] for r in result], [31, 7, 19])
            np.testing.assert_allclose([r[1:] for r in result], expected)
        reversed_rows = transform(ids[::-1], names, x[::-1])
        np.testing.assert_allclose(reversed_rows, [[19, 5, 5], [7, -9, 7], [31, 12, 8]])
        # Headers kept while the numeric columns move.
        stale = transform(ids, names, x[:, ::-1])
        self.assertAlmostEqual(stale[0][1], 6)
        self.assertAlmostEqual(stale[0][2], 8)

    def test_zero_channel_unsigned_subtraction_and_missing_channel(self):
        transform = self.ns["image_features"]
        fresh = np.array([[0, 0, 255], [1, 3, 0]], dtype=np.uint8)
        result = transform([2, 71], ["G", "R", "B"], fresh)
        np.testing.assert_allclose(result, [[2, -255, 85], [71, 3, 4 / 3]])
        for labels, values in ((["R", "B"], [[0, 255]]),
                               (["R", "B", "B"], [[0, 2, 255]])):
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                transform([2], labels, values)

    def search(self, rule, *, gallery=None, gallery_ids=None, tokens=None,
               stored=None, requested=None):
        v = self.ns
        return v["match_requests"](
            v["token_table_new"], v["query_tokens_new"] if tokens is None else tokens,
            v["q_ids_new"] if stored is None else stored,
            v["gallery_new"] if gallery is None else gallery,
            v["g_ids_new"] if gallery_ids is None else gallery_ids,
            v["requested_query_ids"] if requested is None else requested, rule,
        )

    def test_score_contract_and_external_query_order(self):
        self.assertEqual(self.search("cosine"), [90, 53])
        self.assertEqual(self.search("dot"), [90, 8])
        self.assertEqual(self.search("cosine", requested=[61, 22]), [53, 90])
        self.assertEqual(self.search("dot", tokens=self.ns["query_tokens_new"][::-1],
                                     stored=self.ns["q_ids_new"][::-1]), [90, 8])

        # Read the change students actually see in 6B.
        prompt = self.source["2442117e"]
        added = re.search(r"후보 ID \*\*(\d+)\*\*, 벡터 \*\*(\[[^]]+\])\*\*", prompt)
        self.assertIsNotNone(added)
        ident, coords = int(added[1]), json.loads(added[2])
        ids = np.append(self.ns["g_ids_new"], ident)
        gallery = np.vstack((self.ns["gallery_new"], coords))
        for order in (list(range(len(ids))), list(reversed(range(len(ids))))):
            self.assertEqual(self.search("cosine", gallery=gallery[order], gallery_ids=ids[order]),
                             [90, 6])
            self.assertEqual(self.search("dot", gallery=gallery[order], gallery_ids=ids[order]),
                             [90, 8])

    def test_read_the_declared_score_precision_before_breaking_a_tie(self):
        specification = self.source["2442117e"]
        self.assertIn("원시 내적", specification)
        self.assertIn("코사인 유사도", specification)
        args = {"tokens": [[1]], "stored": [31], "requested": [31], "gallery_ids": [70, 5]}
        self.assertEqual(self.search("cosine", gallery=[[1, 0], [1, .0002]], **args), [5])
        self.assertEqual(self.search("cosine", gallery=[[1, 0], [1, .002]], **args), [70])

    def test_lookup_counts_and_the_average_collision(self):
        pool = self.ns["lookup_and_masked_mean"]
        E = self.ns["token_table_new"]
        _, valid, sums, counts, means = pool(E, self.ns["query_tokens_new"])
        np.testing.assert_array_equal(counts[:, 0], [3, 2])
        self.assertTrue(valid[1, 1])
        np.testing.assert_array_equal(sums, [[6, 9], [6, 4]])
        np.testing.assert_array_equal(means, [[2, 3], [3, 2]])

        token_ids = np.array([[1, 2, 0, 0], [2, 1, 2, 1]])
        _, valid, _, counts, means = pool(E, token_ids)
        self.assertEqual([row[mask][0] for row, mask in zip(token_ids, valid)], [1, 2])
        self.assertEqual(counts.ravel().tolist(), [2, 4])
        np.testing.assert_array_equal(means, [[2, 4.5], [2, 4.5]])

    def test_zero_at_lookup_and_at_search_has_different_consequences(self):
        only_zero = {"tokens": [[4]], "stored": [12], "requested": [12]}
        self.assertEqual(self.search("dot", **only_zero), [8])
        with self.assertRaises(ValueError):
            self.search("cosine", **only_zero)
        for bad_ids in ([[0, 0]], [[-1]], [[5]], [[True, 1]]):
            with self.subTest(bad_ids=bad_ids), self.assertRaises(ValueError):
                self.ns["lookup_and_masked_mean"](self.ns["token_table_new"], bad_ids)
        for invalid in ([[0, 0]], [[np.nan, 1]], [[np.inf, 2]], [["3", "4"]],
                        np.array([[3 + 4j, 0]]), [[True, False]]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.ns["normalize_rows"](invalid)


if __name__ == "__main__":
    unittest.main()
