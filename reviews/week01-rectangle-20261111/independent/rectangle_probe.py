"""Frozen reviewer oracle, prepared before candidate. Importing does not run a test.

The future harness calls check_case once per fresh subprocess/in-process kernel.
An adapter invokes either actual candidate code or a separately labelled reviewer
sample solution. It normalizes only the declared API; it must not clip, correct,
recompute or otherwise repair the submitted mask/coordinates. A mask assembled
by a reviewer is reviewer-solution evidence, never actual-candidate evidence.
"""
from pathlib import Path
import json
import traceback

ROOT = Path(__file__).resolve().parent
SCOPES = {"actual_candidate_callable", "reviewer_sample_solution_from_student_instructions"}


class ProbeMismatch(AssertionError):
    pass


def check_case(adapter, case_id, *, execution_scope, require_masked_image=True,
               fixtures_path=None):
    """Call one adapter(image, box, budget_policy) without prescribing lesson API.

    Canonical return is {'mask': spatial_binary_HxW,
    'masked_image': original_shape_array}. A documented rejection may instead
    return {'accepted': False, 'reason': nonempty_string}. If a candidate only
    provides a mask helper, require_masked_image=False must be recorded and the
    separate displayed/student masking path tested separately. Raw API/shape
    normalization belongs in an explicit, reviewed adapter, not in this oracle.
    An exception for invalid input is recorded for manual traceback adjudication;
    arbitrary crashes must not be automatically counted as semantic rejection.
    """
    import numpy as np

    if execution_scope not in SCOPES:
        raise ValueError("must label actual candidate versus reviewer solution")
    source = Path(fixtures_path) if fixtures_path else ROOT / "frozen-inputs-v2.json"
    fixture = json.loads(source.read_text())
    matches = [x for x in fixture["cases"] if x["id"] == case_id]
    if len(matches) != 1:
        raise ValueError("unknown or duplicated frozen case")
    case = matches[0]
    height, width, channels = case["image_shape"]
    if case["image_mode"] == "zeros":
        image = np.zeros((height, width, channels), dtype=np.int64)
    else:
        image = np.array([[[1 + 1000*r + 10*c + k for k in range(channels)]
                           for c in range(width)] for r in range(height)], dtype=np.int64)
    before = image.copy()
    report = {
        "case_id": case_id, "execution_scope": execution_scope,
        "fixture_file": source.name, "expected_valid": case["expected_valid"],
        "expected_nominal_area": case["nominal_area"],
        "expected_coordinates": case.get("expected_spatial_coordinates"),
        "student_achievement": "not_observed", "actual_student_time": "not_observed",
        "require_masked_image": require_masked_image,
        "status": "running",
    }

    def emit():
        print(json.dumps(report, ensure_ascii=False, indent=2))

    def fail(message):
        report.update(status="mismatch", mismatch=message)
        emit()
        raise ProbeMismatch(message)

    result = None
    caught = None
    try:
        result = adapter(image, tuple(tuple(x) for x in case["box"]),
                         dict(case["budget_policy"]))
    except Exception as error:
        caught = error
        report["raw_exception"] = {"type": type(error).__name__, "message": str(error),
                                   "traceback": traceback.format_exc()}
    report["original_unchanged"] = bool(np.array_equal(image, before))
    if not report["original_unchanged"]:
        fail("adapter/solution modified original image, including on rejected input")

    if not case["expected_valid"]:
        if caught is not None:
            # Intentionally not passed: inspect guard/message/traceback first.
            report.update(status="rejection_observed_pending_manual_traceback_review",
                          expected_rejection_reason=case["invalid_reason"])
            emit()
            return report
        if isinstance(result, dict) and result.get("accepted") is False and result.get("reason"):
            report.update(status="declared_rejection_observed_pending_manual_reason_review",
                          actual_rejection_reason=str(result["reason"]))
            emit()
            return report
        fail("invalid contract accepted; small/clipped/zero-valued slice is insufficient")

    if caught is not None:
        fail("valid declared input raised an exception")
    if not isinstance(result, dict) or "mask" not in result:
        fail("adapter must expose the actual produced mask, not repair/reconstruct it")
    mask = np.asarray(result["mask"])
    report["actual_mask_shape"] = list(mask.shape)
    if mask.shape != (height, width):
        fail("canonical spatial mask shape does not match original spatial shape")
    if not np.isin(mask, [0, 1]).all():
        fail("mask is not binary under the declared educational contract")
    coordinates = np.argwhere(mask != 0).tolist()
    area = len(coordinates)
    report.update(actual_coordinates=coordinates, actual_spatial_area=area,
                  channel_value_count_for_comparison_only=area*channels)
    if coordinates != case["expected_spatial_coordinates"]:
        fail("same shape/area is insufficient: selected coordinate set differs")
    if area != case["nominal_area"]:
        fail("coordinate count differs from independently frozen rectangle area")
    policy = case["budget_policy"]
    if policy["type"] == "official_fraction":
        within = policy["denominator"]*area <= policy["numerator"]*height*width
        report["budget_check"] = "exact integer spatial-area inequality"
    elif policy["type"] == "educational_max_pixels":
        within = area <= policy["maximum"]
        report["budget_check"] = "separate educational absolute spatial-pixel maximum"
    else:
        fail("unknown frozen budget policy")
    if not within:
        fail("produced spatial mask exceeds frozen budget")

    if require_masked_image:
        if "masked_image" not in result:
            fail("masking path required but actual produced masked image is absent")
        masked = np.asarray(result["masked_image"])
        expected_masked = np.where(mask.astype(bool)[:, :, None], before, 0)
        report["actual_masked_image_shape"] = list(masked.shape)
        if masked.shape != before.shape or not np.array_equal(masked, expected_masked):
            fail("masked image lost coordinates/channels or retained wrong values")
        report["masked_image_checked"] = True
    else:
        report["masked_image_checked"] = False
        report["masked_image_limit"] = "separate displayed/student transform path remains untested"
    report["status"] = "passed"
    emit()
    return report
