from __future__ import annotations

import copy
import unittest
from typing import Any

from app.golf_metrics import (
    apply_feedback_eligibility,
    build_feedback_eligibility,
)


BASE_TEMPO_METRICS: dict[str, Any] = {
    "backswingDurationSeconds": 1.12,
    "downswingDurationSeconds": 0.56,
    "totalSwingDurationSeconds": 1.68,
    "backswingToDownswingRatio": 2.0,
    "ratioDisplay": "2.00:1",
    "classification": "quick",
    "confidence": 1.0,
    "feedback": {
        "status": "below_target",
        "targetRange": {
            "minimum": 2.7,
            "maximum": 3.3,
            "ratioDisplay": "2.7:1 to 3.3:1",
        },
        "message": (
            "Your downswing is fast relative to your backswing. "
            "A slightly smoother transition or more deliberate "
            "backswing may create a more balanced tempo."
        ),
        "basis": (
            "Heuristic target range used for prototype "
            "swing-tempo feedback."
        ),
    },
}


def make_phase_validation(
    status: str,
    confidence: float,
    failed_checks: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "confidence": confidence,
        "failedChecks": failed_checks or [],
    }


class FeedbackEligibilityTests(unittest.TestCase):
    def test_valid_phases_display_feedback_normally(self) -> None:
        validation = make_phase_validation("valid", 1.0)
        eligibility = build_feedback_eligibility(validation)

        result = apply_feedback_eligibility(
            copy.deepcopy(BASE_TEMPO_METRICS),
            eligibility,
        )
        feedback = result["feedback"]

        self.assertTrue(eligibility["eligible"])
        self.assertEqual(eligibility["status"], "eligible")
        self.assertEqual(eligibility["mode"], "normal")
        self.assertFalse(eligibility["requiresDisclaimer"])

        self.assertEqual(feedback["status"], "below_target")
        self.assertEqual(feedback["deliveryStatus"], "displayed")
        self.assertIsNone(feedback["disclaimer"])
        self.assertIsNotNone(feedback["message"])
        self.assertNotIn("originalStatus", feedback)

    def test_review_phases_display_feedback_with_caution(self) -> None:
        validation = make_phase_validation(
            "review",
            0.888889,
            ["finishTimingPlausible"],
        )
        eligibility = build_feedback_eligibility(validation)

        result = apply_feedback_eligibility(
            copy.deepcopy(BASE_TEMPO_METRICS),
            eligibility,
        )
        feedback = result["feedback"]

        self.assertTrue(eligibility["eligible"])
        self.assertEqual(
            eligibility["status"],
            "eligible_with_caution",
        )
        self.assertEqual(eligibility["mode"], "cautious")
        self.assertTrue(eligibility["requiresDisclaimer"])

        self.assertEqual(feedback["status"], "below_target")
        self.assertEqual(
            feedback["deliveryStatus"],
            "displayed_with_caution",
        )
        self.assertIsNotNone(feedback["message"])
        self.assertIsInstance(feedback["disclaimer"], str)
        self.assertIn(
            "preliminary observation",
            feedback["disclaimer"],
        )

    def test_invalid_phases_suppress_feedback(self) -> None:
        validation = make_phase_validation(
            "invalid",
            0.555556,
            [
                "timestampOrderStrictlyIncreasing",
                "downswingTimingPlausible",
            ],
        )
        eligibility = build_feedback_eligibility(validation)

        result = apply_feedback_eligibility(
            copy.deepcopy(BASE_TEMPO_METRICS),
            eligibility,
        )
        feedback = result["feedback"]

        self.assertFalse(eligibility["eligible"])
        self.assertEqual(eligibility["status"], "suppressed")
        self.assertEqual(eligibility["mode"], "suppressed")
        self.assertTrue(eligibility["requiresDisclaimer"])

        self.assertEqual(feedback["status"], "suppressed")
        self.assertEqual(feedback["originalStatus"], "below_target")
        self.assertEqual(feedback["deliveryStatus"], "suppressed")
        self.assertIsNone(feedback["message"])
        self.assertIsInstance(feedback["disclaimer"], str)
        self.assertIn(
            "did not pass validation",
            feedback["disclaimer"],
        )

    def test_gate_does_not_mutate_original_tempo_metrics(self) -> None:
        original = copy.deepcopy(BASE_TEMPO_METRICS)
        validation = make_phase_validation("invalid", 0.5)
        eligibility = build_feedback_eligibility(validation)

        apply_feedback_eligibility(original, eligibility)

        self.assertEqual(original, BASE_TEMPO_METRICS)

    def test_missing_feedback_object_raises_clear_error(self) -> None:
        validation = make_phase_validation("valid", 1.0)
        eligibility = build_feedback_eligibility(validation)

        with self.assertRaisesRegex(
            ValueError,
            "Tempo metrics are missing a feedback object",
        ):
            apply_feedback_eligibility({}, eligibility)


if __name__ == "__main__":
    unittest.main()