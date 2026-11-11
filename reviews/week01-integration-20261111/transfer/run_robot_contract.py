"""Independent, source-led synthetic contract checks; no robot policy is inferred."""
from __future__ import annotations
import copy
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CASES = []
OBJECTS = {1, 2, 5, 6, 7, 10, 11}


def record(name, expected, observed, lines, meaning):
    CASES.append(dict(name=name, expected=expected, observed=observed,
                      passed=expected == observed, source_lines=lines, meaning=meaning))


def validate_observation(obs):
    if not {"robot_id", "image", "direction", "mission", "carrying"}.issubset(obs):
        raise ValueError("missing input field")
    if type(obs["robot_id"]) is not int or obs["robot_id"] not in range(6):
        raise ValueError("robot_id")
    if type(obs["direction"]) is not int or obs["direction"] not in range(4):
        raise ValueError("direction")
    if not isinstance(obs["mission"], str):
        raise ValueError("mission")
    image = np.asarray(obs["image"])
    if image.shape != (8, 8, 2) or not np.issubdtype(image.dtype, np.integer):
        raise ValueError("image shape/dtype")
    if not np.isin(image[..., 0], list(OBJECTS)).all():
        raise ValueError("object channel")
    if not np.isin(image[..., 1], range(6)).all():
        raise ValueError("colour channel")
    carried = obs["carrying"]
    if carried is not None:
        if (not isinstance(carried, list) or len(carried) != 2
                or any(type(value) is not int for value in carried)):
            raise ValueError("carrying pair")
    return image


def rejected(call):
    try:
        call()
    except (ValueError, KeyError) as error:
        return type(error).__name__
    return "accepted"


def cell(obs, row, column):
    return validate_observation(obs)[row, column].tolist()


def meaningful_grid(obs):
    image = validate_observation(obs).copy()
    image[..., 1][np.isin(image[..., 0], [1, 2])] = -1
    return image


def red_balls(obs):
    image = validate_observation(obs)
    return np.argwhere((image[..., 0] == 6) & (image[..., 1] == 0)).tolist()


def validate_output(text, row_count):
    values = json.loads(text)
    if (type(values) is not list or len(values) != row_count
            or any(type(value) is not int or value not in range(6) for value in values)):
        raise ValueError("one integer action 0..5 for every input row")
    return values


def row_features(obs):
    image = validate_observation(obs)
    return [obs["robot_id"], obs["direction"], int((image[..., 0] == 10).sum())]


def fabricated_previous_robot(rows, index):
    return rows[index - 1]["robot_id"] if index else None


def main():
    image = np.empty((8, 8, 2), dtype=np.int64)
    image[:] = [1, 4]
    image[[0, 7], :, :] = [2, 5]
    image[:, [0, 7], :] = [2, 5]
    image[2, 5], image[5, 2] = [10, 2], [6, 0]
    image[1, 4], image[4, 6] = [5, 1], [11, 3]
    base = dict(robot_id=4, image=image.tolist(), direction=3,
                mission="approach the red ball", carrying=None)

    record("valid_schema_and_axis_roles", [8, 8, 2], list(validate_observation(base).shape),
           "27-43", "Asymmetric fixture: rows, columns, then object/colour.")
    record("known_row_column_cell", [10, 2], cell(base, 2, 5), "43-61",
           "The two cell values are categorical channels, not spatial positions.")
    record("wall_border_and_interior", [[2, 5], [6, 6, 2]],
           [cell(base, 0, 3), list(validate_observation(base)[1:7, 1:7].shape)],
           "10,43", "The full grid includes walls; the interior slice is smaller.")

    transposed = copy.deepcopy(base)
    transposed["image"] = image.transpose(1, 0, 2).tolist()
    record("transpose_passes_shape_schema", "accepted",
           rejected(lambda: validate_observation(transposed)), "32,43",
           "A square-grid transpose preserves shape; the guard cannot certify meaning.")
    record("transpose_fails_frozen_spatial_oracle", [[6, 0], False],
           [cell(transposed, 2, 5), cell(transposed, 2, 5) == [10, 2]], "43",
           "The frozen coordinate oracle reveals the row/column exchange.")

    direction_only = copy.deepcopy(base)
    direction_only["direction"] = 0
    record("direction_changes_without_image_change", [True, 3, 0],
           [base["image"] == direction_only["image"], base["direction"],
            direction_only["direction"]], "32-35,61",
           "Facing is separately available; the next action is not inferred.")
    record("reading_direction_from_colour_is_wrong", [2, False],
           [cell(base, 2, 5)[1], cell(base, 2, 5)[1] == base["direction"]], "59-61",
           "The colour at the robot cell is not top-level facing.")

    third_channel = copy.deepcopy(base)
    third_channel["image"] = np.dstack([image, np.full((8, 8), base["direction"])]).tolist()
    record("appended_direction_channel_rejected", "ValueError",
           rejected(lambda: validate_observation(third_channel)), "32,61",
           "Adding facing creates 8x8x3, outside the image contract.")
    overwritten = copy.deepcopy(base)
    overwritten_image = image.copy()
    overwritten_image[..., 1] = base["direction"]
    overwritten["image"] = overwritten_image.tolist()
    record("direction_overwrite_can_pass_schema", "accepted",
           rejected(lambda: validate_observation(overwritten)), "32,59-61",
           "In-range values and matching shape still cannot certify channel meaning.")
    record("direction_overwrite_fails_cell_oracle", [[10, 3], False],
           [cell(overwritten, 2, 5), cell(overwritten, 2, 5) == [10, 2]], "59-61",
           "A channel overwrite changes the independently specified fixture cell.")

    recoloured = copy.deepcopy(base)
    recoloured_image = image.copy()
    recoloured_image[..., 1][np.isin(image[..., 0], [1, 2])] = 0
    recoloured["image"] = recoloured_image.tolist()
    record("wall_empty_colour_semantics_invariant", True,
           np.array_equal(meaningful_grid(base), meaningful_grid(recoloured)), "59",
           "Declared meaningless colours changed; no action invariance is claimed.")
    record("red_ball_query_ignores_wall_colours", [[[5, 2]], [[5, 2]], 1, 61],
           [red_balls(base), red_balls(recoloured), int((image[..., 1] == 0).sum()),
            int((recoloured_image[..., 1] == 0).sum())], "43-59",
           "Colour-only counting spuriously includes empty cells and walls.")

    carrying_only = copy.deepcopy(base)
    carrying_only["carrying"] = [5, 2]
    record("carrying_is_separate_available_input", [True, [5, 2]],
           [np.array_equal(validate_observation(base), validate_observation(carrying_only)),
            carrying_only["carrying"]], "27-37",
           "Carrying is available separately and need not add an image channel.")
    record("no_label_or_previous_action_available", ["KeyError", "KeyError"],
           [rejected(lambda: base["label"]), rejected(lambda: base["previous_action"])],
           "37,97-101", "The evaluation observation has neither hidden action nor history.")

    other = copy.deepcopy(base)
    other["robot_id"], other["direction"] = 1, 0
    batch = [base, other]
    forward = [row_features(obs) for obs in batch]
    reversed_restored = [row_features(obs) for obs in batch[::-1]][::-1]
    record("rowwise_probe_survives_order_change", forward, reversed_restored, "37,105-107",
           "Per-row schema probes retain observation identity under a joint permutation.")
    record("previous_row_is_not_observed_history", [None, 1],
           [fabricated_previous_robot(batch, 0),
            fabricated_previous_robot(batch[::-1], 1)], "37",
           "Reordering rows changes fabricated history for the same observation.")

    markers = [0, 5, 2]  # Arbitrary format/lineage markers, NOT ground-truth action labels.
    record("normal_output_json_roundtrip", markers, validate_output(json.dumps(markers), 3),
           "105-114", "Format only: the values are not a guessed movement policy.")
    bad_outputs = [
        ("wrong_count", [0, 5]), ("float_action", [0, 5, 2.0]),
        ("boolean_action", [0, 5, True]), ("out_of_range", [0, 5, 6]),
        ("negative_action", [0, 5, -1]), ("object_instead_of_list", {"actions": markers}),
    ]
    for name, value in bad_outputs:
        record("output_reject_" + name, "ValueError",
               rejected(lambda value=value: validate_output(json.dumps(value), 3)), "105-114",
               "This contract differs from labels and containers in the first toy classifier.")
    record("reversed_output_can_pass_format", markers[::-1],
           validate_output(json.dumps(markers[::-1]), 3), "105-107",
           "Format validity alone cannot certify row correspondence.")
    record("reversed_output_fails_external_order_oracle", False, markers[::-1] == markers,
           "105-107", "Arbitrary-marker lineage check, not an action-correctness score.")

    report = dict(
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        purpose="Independent synthetic contract transfer and counterexamples only",
        source=json.loads((HERE / "source-reading.json").read_text()),
        environment=dict(python=sys.version, executable=sys.executable,
                         numpy=np.__version__, platform=platform.platform()),
        fixture=base,
        fixture_sha256=hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cases=CASES,
        summary=dict(cases=len(CASES), passed=sum(case["passed"] for case in CASES),
                     failed=sum(not case["passed"] for case in CASES)),
        limits=["No official data or robot policy was used, learned, guessed, or scored.",
                "Output actions are arbitrary format markers, not policy labels.",
                "No learner answer, mastery, classroom timing, or contest solution was observed.",
                "The observation guard checks this declared subset, not all official input constraints.",
                "These tests check source semantics, not execution of the integrated lesson."])
    (HERE / "robot-contract-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["summary"], ensure_ascii=False))
    if report["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

