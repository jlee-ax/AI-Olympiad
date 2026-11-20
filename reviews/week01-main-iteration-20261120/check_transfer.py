"""Replay public Week 1 classroom examples and check that plausible mistakes are observable."""
import argparse
import ast
import json
import re
from contextlib import chdir
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = ROOT / "lessons" / "week01"


def source(cell):
    return "".join(cell["source"])


def literal_inputs(cell):
    result = {}
    for statement in ast.parse(source(cell)).body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = ast.literal_eval(statement.value)
    return result


def load_reference(guide):
    import matplotlib
    matplotlib.use("Agg")
    marker = r"^<!-- teacher-cell: (ref-[a-z-]+) -->\n```python\n(.*?)\n```$"
    parts = re.findall(marker, guide.read_text(encoding="utf-8"), re.MULTILINE | re.DOTALL)
    assert [name for name, _ in parts] == ["ref-gallery", "ref-align", "ref-axes", "ref-plot", "ref-projection",
                                           "ref-digit-lookup", "ref-named-means", "ref-pixel-plot"]
    reference = {}
    for name, body in parts:
        exec(compile(body, f"{guide.name}:{name}", "exec"), reference)
    return reference


def pick_ids(case, best):
    # Independent labeled pairs keep the oracle free of array-position indexing.
    return [best(zip(row, case["ids"]), key=lambda pair: pair[0])[1] for row in case["scores"]]


def visibility(case, records):
    scores, costs = (pick_ids(case, choice) for choice in (max, min))
    features = records["features"][:2]
    means = []
    for field in features:
        observed = [row[field] for row in records["rows"] if row.get(field) is not None]
        means.append(sum(observed) / len(observed))
    return {
        "reversed_queries_expose_stale_score_answers": scores != scores[::-1],
        "reversed_queries_expose_stale_cost_answers": costs != costs[::-1],
        "swapped_features_expose_stale_column_means": means[0] != means[1],
    }


def check_csv_handoff(directions):
    """Open the actual linked CSV section and run its published loading and join cells in order."""
    from ipykernel.inprocess.manager import InProcessKernelManager
    from IPython.utils.capture import capture_output
    from pandas.errors import MergeError

    link = re.search(r"\]\((week01_[a-z_]+\.ipynb)#(tables-csv)\)", directions)
    assert link, "The integrated textbook does not point to the independent CSV exercise"
    companion = LESSON / link.group(1)
    cells = json.loads(companion.read_text(encoding="utf-8"))["cells"]
    match, = (i for i, c in enumerate(cells) if f'id="{link.group(2)}"' in source(c))
    manager = InProcessKernelManager()
    manager.start_kernel()
    try:
        shell = manager.kernel.shell
        executed = []
        with chdir(companion.parent), capture_output():
            for cell in cells[match:]:
                if cell["cell_type"] != "code":
                    continue
                shell.run_cell(source(cell), store_history=False, silent=True).raise_error()
                executed.append(cell["id"])
                if "site_notes" in shell.user_ns and "new_plants" in shell.user_ns:
                    break
        records = shell.user_ns["new_plants"]
        notes = shell.user_ns["site_notes"]
        assert records.shape == (4, 5) and notes.shape == (2, 2)
        def join(lookup):
            return records.merge(lookup, on="site", how="left", validate="many_to_one")
        joined = join(notes)
        assert joined.sample_id.tolist() == records.sample_id.tolist()
        assert joined.equals(join(notes.iloc[::-1])) and joined.note.notna().all()
        partial = join(notes.iloc[:1])
        assert partial.sample_id.tolist() == records.sample_id.tolist() and partial.note.isna().sum() == 2
        try:
            join(notes.iloc[[0, 0]])
        except MergeError:
            pass
        else:
            raise AssertionError("Duplicate lookup keys invalidated the declared many-to-one join")
        return {"executed_cell_ids": executed, "new_csv_shape": list(records.shape),
                "lookup_shape": list(notes.shape), "rows_retained_with_missing_note": len(partial)}
    finally:
        manager.shutdown_kernel()


def check_required_assignment(cells):
    """A function that passes the oracle must also be assigned in the learner's required work."""
    prompt = source(cells["4042bdda"])
    headings = list(re.finditer(r"(?m)^\*\*([^*\n]+)\*\*", prompt))
    blocks = [(h.group(1), prompt[h.end():headings[i+1].start() if i+1 < len(headings) else len(prompt)])
              for i, h in enumerate(headings)]

    def required(head, body):
        return (re.match(r"문제\s+\d+\.", head) is not None and "(필수)" in head
                and "indistinguishable_pairs(case)" in body)

    matches = [(head, body) for head, body in blocks if "indistinguishable_pairs(case)" in body]
    assert len(matches) == 1, "The learner must receive the general function assignment exactly once"
    heading, body = matches[0]
    assert required(heading, body), "The Week 1 transfer is not visibly assigned as required"
    assert not required("추가 문제.", body), "Relabeling the same problem optional cannot count as required"
    work = cells["summary-exercise-work"]
    assert work["cell_type"] == "code" and not ast.parse(source(work)).body and not work.get("outputs")
    return {"required_problem": heading, "response_cell": work["id"]}


def check_projection(function):
    """Compare the published reference with equivalence classes of feature signatures."""
    from collections import defaultdict
    from itertools import combinations, permutations

    matrix = [[2,3,5], [2,4,5], [2,3,5], [7,4,5]]
    labels = [1, 0, 1, 1]

    def expected(rows, answers, columns):
        classes = defaultdict(list)
        for index, row in enumerate(rows):
            key = tuple(row[k] for k in columns)
            classes[key].append(index)
        return sorted([i, j] for group in classes.values() for i, j in combinations(group, 2)
                      if answers[i] != answers[j])

    checks = 0
    for order in permutations(range(len(matrix))):
        rows = [matrix[i] for i in order]
        answers = [labels[i] for i in order]
        for count in range(4):
            for columns in combinations(range(3), count):
                case = {"features": rows, "labels": answers, "keep": list(columns)}
                assert function(case) == expected(rows, answers, columns)
                checks += 1
    adversarial = {"features": [[0,0],[0,1]], "labels": [1,2]}
    assert function({**adversarial, "keep": [0]}) == [[0,1]]
    assert function({**adversarial, "keep": [1]}) == []
    assert function({"features": [], "labels": [], "keep": []}) == []
    assert function({"features": [[3]], "labels": [0], "keep": []}) == []
    return checks


def check_practical_references(reference):
    lookup = reference["restore_digit_predictions"]
    predictions = {"records": [["im3", 0], ["im8", 6]], "requests": ["im3", "IM3", "im8", "im3"]}
    assert lookup(predictions) == [0, None, 6, 0]
    assert lookup({**predictions, "records": predictions["records"][::-1]}) == [0, None, 6, 0]
    assert lookup({**predictions, "requests": []}) == []
    reduce_columns = reference["named_feature_means"]
    frame = {"columns": ["left", "right", "absent"], "values": [[0, 5, None], [6, None, None]]}
    assert reduce_columns({**frame, "keep": ["absent", "left", "right"]}) == {
        "shape": [2, 3], "observed": [0, 2, 1], "means": [None, 3, 5]}
    assert reduce_columns({**frame, "values": [], "keep": ["right"]}) == {
        "shape": [0, 1], "observed": [0], "means": [None]}
    assert reduce_columns({**frame, "keep": []}) == {"shape": [2, 0], "observed": [], "means": []}

    plot = reference["plot_pixel_frequency"]
    rows = [[6, 4], [2, 4], [2, 3], [2, 4]]
    for library in ("matplotlib", "seaborn"):
        def render(groups, unit, data):
            return plot({"rows": data, "groups": groups, "target": 4, "unit": unit, "library": library})
        assert render([6, 2, 1], "count", rows) == {"groups": [6, 2, 1], "heights": [1, 2, 0]}
        result = render([2, 6], "percent", rows[::-1])
        assert result["groups"] == [2, 6]
        assert abs(result["heights"][0] - 200/3) < 1e-8 and result["heights"][1] == 100
    return ["digit lookup preserves a measured zero and missing-record status",
            "column means use the named fields and observed denominators",
            "both plotting libraries use the specified group denominator and display order"]


def check(notebook, guide, sensitivity_only=False):
    cells = {c["id"]: c for c in json.loads(notebook.read_text(encoding="utf-8"))["cells"]}
    case = literal_inputs(cells["gallery-challenge-input"])["matching_case"]
    records = literal_inputs(cells["records-input"])
    signals = visibility(case, records)
    if sensitivity_only:
        return signals
    assert all(signals.values()), signals
    for key in ("gallery-challenge-work", "records-work"):
        assert not ast.parse(source(cells[key])).body and not cells[key].get("outputs")

    required_assignment = check_required_assignment(cells)
    ref = load_reference(guide)
    practical_references = check_practical_references(ref)
    projection_checks = check_projection(ref["indistinguishable_pairs"])
    matching = ref["select_gallery_ids"]
    by_score = pick_ids(case, max)
    by_cost = pick_ids(case, min)
    assert by_cost != by_score and matching(case) == by_score
    assert len(set(by_score)) < len(by_score)
    order = [2, 3, 0, 1]
    relabeled = [case["ids"][i] for i in order]
    moved = [[row[i] for i in order] for row in case["scores"]]
    assert matching({"ids": relabeled, "scores": moved}) == by_score
    assert matching({"ids": relabeled, "scores": case["scores"]}) != by_score
    assert matching({"ids": case["ids"], "scores": case["scores"][::-1]}) == by_score[::-1]
    assert matching({"ids": [503], "scores": [[-9], [0]]}) == [503, 503]
    assert matching({"ids": [80, 0, 101], "scores": [[-1, -9, -3], [1, 7, 4]]}) == [80, 0]

    align = ref["align_painting_labels"]
    keys = {"items": records["items"], "labels": records["labels"]}
    assert align(keys) == [-1, 0, None, 0]
    assert align({**keys, "labels": keys["labels"][::-1]}) == [-1, 0, None, 0]
    assert align({"items": [" a ", "missing", "A", "B"], "labels": [["a", 0], ["B", 1]]}) == [0, None, 0, 1]

    axes = ref["summarize_feature_axes"]
    measurements = {"features": records["features"], "rows": records["rows"]}
    expected = {"shape": [3, 3], "row_means": [2, 8, 2], "column_means": [3, 4, None],
                "missing_by_column": [1, 1, 3]}
    assert axes(measurements) == expected
    features = measurements["features"]
    assert axes({**measurements, "features": [features[1], features[0], features[2]]}) == {
        **expected, "column_means": [4, 3, None]}
    assert axes({"features": ["x", "y"], "rows": [{"x": 0}, {}]}) == {
        "shape": [2, 2], "row_means": [0, None], "column_means": [0, None], "missing_by_column": [1, 2]}

    from matplotlib import pyplot as plt
    plot = ref["plot_known_labels"]
    plot_receipts = {}
    for library in ("matplotlib", "seaborn"):
        for mode, values, label in (("count", [2, 3], "known labels"), ("percent", [100, 60], "known labels (%)")):
            result = plot({"groups": ["B", "A"], "rows": records["label_log"], "measure": mode, "library": library})
            assert result == {"groups": ["B", "A"], "heights": values, "x_label": "group", "y_label": label}
            plot_receipts[f"{library}_{mode}"] = result["heights"]
    assert not plt.get_fignums()
    return {"visible_required_assignment": required_assignment,
            "representation_permutations_and_subsets": projection_checks,
            "practical_references": practical_references,
            "visible_discriminators": signals, "csv_handoff": check_csv_handoff(source(cells["4042bdda"])),
            "classroom_score_ids": by_score, "classroom_cost_ids": by_cost,
            "feature_column_means": expected["column_means"], "rendered_bar_heights": plot_receipts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, default=LESSON / "week01_integrated.ipynb")
    parser.add_argument("--teacher", type=Path, default=LESSON / "week01_integrated_teacher.md")
    parser.add_argument("--sensitivity-only", action="store_true",
                        help="Report whether the public input distinguishes each tempting wrong answer.")
    args = parser.parse_args()
    print(json.dumps(check(args.notebook, args.teacher, args.sensitivity_only), ensure_ascii=False, indent=2))
