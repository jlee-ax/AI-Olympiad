import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from course_tool_prerequisites import inspect


RULE = {"topic":"sample-tools", "modules":["drawing.features"], "data_only":["drawing.features.read_*"],
        "mentions":["FeatureModel"], "introduced_in":[37], "available":False}


def examine(cells, order=None, rules=None, demonstrations=None):
    notebook = {"cells":[{"id":name, "cell_type":kind, "source":source} for name, kind, source, _ in cells]}
    route = {"units":[{"tier":tier, "cells":["main/" + name]}
                       for name, _, _, tier in (order if order is not None else cells)]}
    if demonstrations:
        route["provided_examples"] = demonstrations
    return inspect({"week":11, "rules":rules if rules is not None else [RULE],
                    "notebooks":{"main":notebook}, "route":route})


class RoutedTools(unittest.TestCase):
    def test_data_loader_alias_and_unrelated_hand_calculation_serve_as_controls(self):
        result = examine([("read","code","from drawing.features import read_rows as example\nrows = example()", "class"),
                          ("compare","code","import samplemath as m\nmean=m.mean(rows)\nprint(mean)", "homework"),
                          ("unused","code","from drawing.features import FeatureModel as Spare\n# Spare().fit(rows)", "class")])
        self.assertEqual(result["blocked"], [])
        self.assertEqual(result["review_cells"], [])
        self.assertEqual([(r["kind"],r["api"]) for r in result["findings"]],
                         [("data_only","drawing.features.read_rows")])

    def test_optional_factory_is_not_a_prerequisite_until_a_required_cell_uses_it(self):
        inputs=[("example","code","from drawing.features import FeatureModel as F\nfactory = F\ndef build():\n    return factory()\nmodel = build()", "conditional")]
        sample=examine(inputs)
        self.assertEqual(sample["blocked"], [])
        self.assertTrue(any(r["kind"] == "conditional" for r in sample["findings"]))
        sample=examine(inputs + [("exercise","code","scores = model.predict([[1], [2]])", "homework")])
        self.assertTrue(any(r["cell"] == "main/exercise" and r["origin"] == "main/example" for r in sample["blocked"]))

    def test_stored_factories_are_traced_without_charging_other_fields(self):
        setup = ("examples", "code", """from drawing.features import FeatureModel
from types import SimpleNamespace
registry = {}
choice = registry
registry['factory'] = FeatureModel
registry['ordinary'] = lambda values: sum(values)
holder = SimpleNamespace()
holder.factory = FeatureModel
holder.ordinary = lambda values: sum(values)""", "conditional")
        for expression in ("choice['factory']()", "holder.factory()"):
            case = examine([setup, ("work", "code", "answer = " + expression, "homework")])
            self.assertEqual([(item["cell"], item["api"]) for item in case["blocked"]],
                             [("main/work", "drawing.features.FeatureModel")])
        for expression in ("choice['ordinary']([1, 2])", "holder.ordinary([1, 2])"):
            case = examine([setup, ("work", "code", "answer = " + expression, "class")])
            self.assertEqual(case["blocked"], [])
            self.assertEqual(case["review_cells"], [])
        changed = ("reset", "code", "registry['factory'] = lambda: 0", "class")
        self.assertEqual(examine([setup, changed, ("work", "code", "choice['factory']()", "class")])["blocked"], [])
        unknown = examine([setup, ("work", "code", "choice[selected_name]()", "class")])
        self.assertEqual(unknown["blocked"], [])
        self.assertEqual(unknown["review_cells"], ["main/work"])

    def test_literal_fields_keep_selected_values_and_stored_results_separate(self):
        given = ("worked", "code", """from drawing.features import FeatureModel
given = {'prediction': FeatureModel().predict([[2]]), 'counts': [1, 2]}""", "conditional")
        counts = examine([given, ("work", "code", "sum(given['counts'])", "class")])
        self.assertEqual(counts["blocked"], [])
        selected = examine([given, ("work", "code", "print(given['prediction'])", "class")])
        self.assertTrue(any(item["origin"] == "main/worked" for item in selected["blocked"]))
        whole = examine([given, ("work", "code", "print(given)", "class")])
        self.assertTrue(whole["blocked"])

    def test_route_can_call_a_helper_printed_later_in_the_book(self):
        task=("work","code","answer = make_model()", "class")
        helper=("setup","code","import drawing.features as features\ndef make_model():\n    return features.FeatureModel()", "conditional")
        result=examine([task,helper], order=[helper,task])
        self.assertTrue(any(r["cell"] == "main/work" and r["api"] == "drawing.features.FeatureModel"
                            for r in result["blocked"]))

    def test_required_only_order_catches_optional_rebinding(self):
        source=("setup","code","from drawing.features import FeatureModel as operation", "class")
        replacement=("optional","code","operation = lambda: 0", "conditional")
        work=("work","code","result = operation()", "homework")
        self.assertTrue(examine([source,replacement,work])["blocked"])

    def test_learner_prompt_and_unresolved_dynamic_selection_need_independent_review(self):
        data = examine([("reference","markdown","[See the data](https://example.org/FeatureModel)", "class"),
                        ("prompt","markdown","Choose whether to call FeatureModel here.", "class"),
                        ("indirect","code","import importlib as il\nchosen = il.import_module(module_name)", "homework")])
        self.assertEqual(data["review_cells"],["main/indirect","main/prompt"])
        self.assertEqual(data["blocked"],[])
        literal = examine([("indirect","code","import importlib\nm=importlib.import_module('drawing.features')\ngetattr(m, 'FeatureModel')()", "class")])
        self.assertTrue(literal["blocked"])

    def test_required_function_body_and_bound_default_do_not_disappear(self):
        base=("setup","code","from drawing.features import FeatureModel as F\ndef build(factory=F):\n    return factory()","class")
        unused=examine([base])
        self.assertEqual(unused["blocked"],[])
        self.assertEqual(unused["review_cells"],["main/setup"])
        self.assertIn("definition", {r["kind"] for r in unused["findings"]})
        result=examine([base,("require","code","make = lambda f: f()\nmodel = make(build)", "class")])
        self.assertTrue(any(r["cell"]=="main/require" for r in result["blocked"]))

    def test_known_display_magic_preserves_following_code_and_original_line_numbers(self):
        base = "# figure\n%matplotlib inline\nx = [1, 3]\n"
        self.assertEqual(examine([("display","code",base,"class")])["findings"], [])
        source = base + "from drawing.features import FeatureModel as F\nvalue = F()"
        result = examine([("display","code",source,"class")])
        self.assertEqual([(r["cell"],r["line"]) for r in result["blocked"]],[("main/display",5)])
        for raw in ("%run unexamined.py\nx = 1", "%%time\nx = 1"):
            self.assertEqual(examine([("dynamic","code",raw,"class")])["review_cells"],["main/dynamic"])

    def test_wildcard_or_dynamic_attribute_on_unrelated_math_is_not_a_model_prerequisite(self):
        data = examine([("math","code","from math import *\nimport samplemath as m\nfunc = getattr(m, operator)", "class")])
        self.assertEqual(data["findings"],[])
        future = examine([("future","code","from drawing.features import *", "class")])
        self.assertEqual(future["review_cells"],["main/future"])

    def test_changing_week_or_course_registration_changes_the_disposition(self):
        rows=[("apply","code","import drawing.features as f\nC = f.FeatureModel\nmodel = C()", "class")]
        for rule in ([RULE], [{**RULE,"available":True}], []):
            check=examine(rows,rules=rule)
            self.assertEqual(bool(check["blocked"]),bool(rule) and not rule[0]["available"])
        # A method can have a later introduction than the parent library.
        result=examine(rows,rules=[{**RULE,"available":True},
            {"topic":"analysis", "modules":["drawing.features.FeatureModel"], "data_only":[],
             "mentions":["FeatureModel"], "introduced_in":[42], "available":False}])
        self.assertEqual({r["topic"] for r in result["blocked"]},{"analysis"})

    def test_notebook_kernels_and_teacher_helpers_do_not_leak_names(self):
        sample={"rules":[RULE],"notebooks":{"main":{"cells":[{"id":"work","cell_type":"code",
                    "source":"from my_basic_math import compare\ncompare([1,2])"}]},
                "extra":{"cells":[{"id":"example","cell_type":"code","source":"from drawing.features import FeatureModel as compare\ncompare()"}]}},
                "teacher":{"cells":[{"id":"reference","cell_type":"code","source":"from drawing.features import FeatureModel\nFeatureModel()"}]},
                "route":{"units":[{"tier":"conditional","cells":["extra/example"]},{"tier":"class","cells":["main/work"]}]}}
        result=inspect(sample)
        self.assertEqual(result["blocked"],[])
        self.assertEqual({r["cell"] for r in result["findings"]},{"extra/example"})


if __name__ == "__main__":
    unittest.main()
