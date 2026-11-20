"""Blind answers from an independently implemented interpretation of four public interfaces."""
from itertools import combinations
from math import fsum


def projection(case):
    rows = case["features"]
    labels = case["labels"]
    positions = case["keep"]
    return [
        [first, second]
        for first, second in combinations(range(len(rows)), 2)
        if labels[first] != labels[second]
        and all(rows[first][j] == rows[second][j] for j in positions)
    ]


def lookup(case):
    by_name = dict(case["records"])
    return [by_name.get(name) for name in case["requests"]]


def summarize(case):
    columns = case["columns"]
    rows = case["values"]
    observed = []
    means = []
    for name in case["keep"]:
        position = columns.index(name)
        valid = [row[position] for row in rows if row[position] is not None]
        observed.append(len(valid))
        means.append(fsum(valid) / len(valid) if valid else None)
    return {"shape": [len(rows), len(observed)], "observed": observed, "means": means}


def frequencies(case):
    groups = case["groups"]
    heights = []
    for group in groups:
        values = [value for record_group, value in case["rows"] if record_group == group]
        hits = values.count(case["target"])
        if case["unit"] == "percent":
            heights.append(100 * hits / len(values) if values else 0)
        elif case["unit"] == "count":
            heights.append(hits)
        else:
            raise ValueError("Unknown frequency unit")
    return {"groups": list(groups), "heights": heights}


def solve(questions):
    procedures = {
        "transfer": projection,
        "KOAI-01.practical": lookup,
        "KOAI-02.practical": summarize,
        "KOAI-03.practical": frequencies,
    }
    if set(questions) != set(procedures):
        raise ValueError("The assignment must contain the four registered Week 1 obligations")
    return {
        obligation: [procedures[obligation](case) for case in prompt["inputs"]]
        for obligation, prompt in questions.items()
    }
