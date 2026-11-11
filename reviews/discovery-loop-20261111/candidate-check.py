#!/usr/bin/env python3
"""Execute the candidate's example and review answer; do not claim learner evidence."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import sys

import numpy as np

here = Path(__file__).resolve().parent
document_path = here / "candidate-bridge.md"
document = document_path.read_text(encoding="utf-8")
checks = []


def extract_code(start, end):
    pattern = rf"<!-- {re.escape(start)} -->\s*~~~python\n(.*?)\n~~~\s*<!-- {re.escape(end)} -->"
    match = re.search(pattern, document, re.DOTALL)
    if not match:
        raise AssertionError(f"missing code section: {start}")
    return match.group(1)


def run_check(name, function):
    try:
        function()
    except Exception as error:
        checks.append({"name": name, "status": "failed", "error": f"{type(error).__name__}: {error}"})
    else:
        checks.append({"name": name, "status": "passed"})


def raises_value_error(function):
    try:
        function()
    except ValueError:
        return True
    return False


sample = {}
exercise = {}
sample_output = io.StringIO()
with contextlib.redirect_stdout(sample_output):
    exec(compile(extract_code("실행 예제 시작", "실행 예제 끝"), str(document_path), "exec"), sample)
exec(compile(extract_code("독립 과제 입력 시작", "독립 과제 입력 끝"), str(document_path), "exec"), exercise)
exec(compile(extract_code("검토 답안 코드 시작", "검토 답안 코드 끝"), str(document_path), "exec"), exercise)

Q, G = sample["Q"], sample["G"]
q, g = exercise["q"], exercise["g"]


def sample_contract():
    assert Q.shape == (2, 3) and G.shape == (4, 3)
    assert G.T.shape == (3, 4) and sample["scores"].shape == (2, 4)
    np.testing.assert_array_equal(sample["scores"], [[2, 2, 1, 4], [0, 3, 1, 2]])
    assert sample["scores"][0, 3] == sum(Q[0, k] * G[3, k] for k in range(3))
    # Ties below the maximum exist; only the maximum in each row is unique.
    maxima = np.max(sample["scores"], axis=1, keepdims=True)
    assert np.all(np.sum(sample["scores"] == maxima, axis=1) == 1)
    assert "이 예제에서 각 행의 최댓값에는 동점이 없습니다." in document


def elementwise_is_not_pairwise():
    incorrect = Q * G[:2]
    assert incorrect.shape == (2, 3)
    np.testing.assert_array_equal(incorrect, [[2, 0, 0], [0, 2, 1]])
    assert (Q @ G[:2].T).shape == (2, 2)
    assert sample["scores"].shape == (2, 4)
    assert (q * g[:2]).shape == (2, 2)
    assert exercise["exercise_scores"].shape == (2, 3)


def contraction_mismatch_is_rejected():
    assert raises_value_error(lambda: Q @ G)
    assert raises_value_error(lambda: q @ g)


def joins_use_expected_axes():
    assert sample["stacked"].shape == (2, 2, 3)
    assert sample["joined_rows"].shape == (4, 3)
    assert sample["joined_columns"].shape == (2, 6)
    np.testing.assert_array_equal(sample["joined_rows"], G)
    np.testing.assert_array_equal(sample["joined_columns"][0], [2, 0, 0, 1, 1, 0])
    assert raises_value_error(lambda: np.stack([G[:1], G[1:]], axis=0))
    assert np.concatenate([G[:1], G[1:]], axis=0).shape == (4, 3)


def mapping(queries, query_ids, gallery, gallery_ids):
    positions = np.argmax(queries @ gallery.T, axis=1)
    return {int(qid): int(gid) for qid, gid in zip(query_ids, gallery_ids[positions])}


def reorder_tracks_actual_ids():
    qids, gids = sample["query_ids"], sample["gallery_ids"]
    original = mapping(Q, qids, G, gids)
    assert original == {103: 35, 109: 7}
    qorder, gorder = [1, 0], [2, 0, 3, 1]
    assert mapping(Q[qorder], qids[qorder], G[gorder], gids[gorder]) == original
    assert mapping(Q[qorder], qids, G, gids) != original
    assert mapping(Q, qids, G[gorder], gids) != original
    assert list(sample["positions"] + 1) != list(sample["matched_ids"])


def independent_exercise_answer():
    np.testing.assert_array_equal(exercise["exercise_scores"], [[4, 2, 3], [2, 4, 3]])
    np.testing.assert_array_equal(exercise["exercise_positions"], [0, 1])
    np.testing.assert_array_equal(exercise["exercise_ids"], [81, 6])
    assert int(np.dot(q[0], g[2])) == 3
    np.testing.assert_array_equal(exercise["shuffled_scores"], [[3, 2, 4], [3, 4, 2]])
    np.testing.assert_array_equal(exercise["shuffled_positions"], [2, 1])
    np.testing.assert_array_equal(exercise["shuffled_ids"], [6, 81])
    assert mapping(q, exercise["q_ids"], g, exercise["g_ids"]) == {12: 81, 27: 6}
    assert mapping(q[[1, 0]], exercise["q_ids"][[1, 0]], g[[2, 0, 1]],
                   exercise["g_ids"][[2, 0, 1]]) == {12: 81, 27: 6}


def independent_exercise_joins():
    np.testing.assert_array_equal(exercise["stacked_vectors"], [[0, 2], [2, 0]])
    np.testing.assert_array_equal(exercise["joined_vectors"], [0, 2, 2, 0])
    np.testing.assert_array_equal(exercise["joined_features"], [[0, 2, 2, 0]])
    assert exercise["stacked_vectors"].shape == (2, 2)
    assert exercise["joined_vectors"].shape == (4,)
    assert exercise["joined_features"].shape == (1, 4)


def document_scope():
    for heading in ["## 학습 범위와 선수 지식", "## 기초에서 원리로", "## shape 추적",
                    "## 작은 코드", "## 새 독립 과제", "## 별도 검토: 과제 예시 답안",
                    "## 기존 교안과의 대조 및 배치 제안", "## 근거와 검증 범위"]:
        assert heading in document
    assert document.index("## 새 독립 과제") < document.index("## 별도 검토: 과제 예시 답안")
    assert "실제 학습자 응답이나 독립 수행은 아직 관찰하지 않았습니다" in document


for name, function in [
    ("sample_rectangular_pairwise_matrix_and_one_cell", sample_contract),
    ("elementwise_multiplication_counterexample", elementwise_is_not_pairwise),
    ("contraction_mismatch_raises", contraction_mismatch_is_rejected),
    ("stack_and_concatenate_axes_and_shape_constraints", joins_use_expected_axes),
    ("query_gallery_reorder_id_alignment_and_wrong_controls", reorder_tracks_actual_ids),
    ("independent_exercise_review_answer_and_reordering", independent_exercise_answer),
    ("independent_exercise_stack_and_concatenate_answers", independent_exercise_joins),
    ("lesson_scope_headings_and_no_learner_claim", document_scope),
]:
    run_check(name, function)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


result = {
    "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
    "checks": checks,
    "test_scope": "Executes the draft's sample, independent task input, and teacher review answer, plus negative controls; does not execute learner responses.",
    "learner_evidence": "No learner response or independent performance observed.",
    "versions": {"python": sys.version.split()[0], "numpy": np.__version__},
    "executed_example_stdout": sample_output.getvalue(),
    "artifacts_sha256": {
        "candidate-bridge.md": sha256(document_path),
        "candidate-check.py": sha256(Path(__file__).resolve()),
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if result["status"] != "passed":
    raise SystemExit(1)
