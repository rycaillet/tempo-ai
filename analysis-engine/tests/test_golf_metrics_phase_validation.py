from __future__ import annotations

import unittest

from app.golf_metrics import build_phase_validation


class PhaseValidationTests(unittest.TestCase):
    def build_references(self) -> dict[str, dict[str, object]]:
        return {
            "addressReference": {
                "frameIndex": 65,
                "timestampSeconds": 2.60,
                "poseDetected": True,
            },
            "takeawayReference": {
                "frameIndex": 67,
                "timestampSeconds": 2.68,
                "poseDetected": True,
            },
            "topOfBackswing": {
                "frameIndex": 93,
                "timestampSeconds": 3.72,
                "poseDetected": True,
            },
            "downswingStart": {
                "frameIndex": 102,
                "timestampSeconds": 4.08,
                "poseDetected": True,
            },
            "impactReference": {
                "frameIndex": 107,
                "timestampSeconds": 4.28,
                "poseDetected": True,
            },
            "finishReference": {
                "frameIndex": 117,
                "timestampSeconds": 4.68,
                "poseDetected": True,
            },
        }

    def test_plausible_phases_are_valid(self) -> None:
        result = build_phase_validation(
            self.build_references()
        )

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["passedCheckCount"], 9)
        self.assertEqual(result["totalCheckCount"], 9)
        self.assertEqual(result["failedChecks"], [])
        self.assertTrue(all(result["checks"].values()))

    def test_noncritical_timing_failure_requires_review(self) -> None:
        references = self.build_references()
        references["takeawayReference"][
            "timestampSeconds"
        ] = 3.40

        result = build_phase_validation(references)

        self.assertEqual(result["status"], "review")
        self.assertEqual(result["confidence"], 0.888889)
        self.assertEqual(result["passedCheckCount"], 8)
        self.assertEqual(
            result["failedChecks"],
            ["takeawayTimingPlausible"],
        )
        self.assertFalse(
            result["checks"]["takeawayTimingPlausible"]
        )

    def test_missing_pose_marks_validation_invalid(self) -> None:
        references = self.build_references()
        references["impactReference"]["poseDetected"] = False

        result = build_phase_validation(references)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["confidence"], 0.888889)
        self.assertIn(
            "allReferenceFramesHavePose",
            result["failedChecks"],
        )
        self.assertFalse(
            result["checks"]["allReferenceFramesHavePose"]
        )

    def test_reversed_frame_order_marks_validation_invalid(
        self,
    ) -> None:
        references = self.build_references()
        references["downswingStart"]["frameIndex"] = 90

        result = build_phase_validation(references)

        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "frameOrderStrictlyIncreasing",
            result["failedChecks"],
        )
        self.assertFalse(
            result["checks"]["frameOrderStrictlyIncreasing"]
        )
        self.assertTrue(
            result["checks"]["timestampOrderStrictlyIncreasing"]
        )

    def test_reversed_timestamp_order_reports_all_failures(
        self,
    ) -> None:
        references = self.build_references()
        references["downswingStart"][
            "timestampSeconds"
        ] = 3.60

        result = build_phase_validation(references)

        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "timestampOrderStrictlyIncreasing",
            result["failedChecks"],
        )
        self.assertIn(
            "transitionTimingPlausible",
            result["failedChecks"],
        )
        self.assertFalse(
            result["checks"]["timestampOrderStrictlyIncreasing"]
        )
        self.assertFalse(
            result["checks"]["transitionTimingPlausible"]
        )

    def test_missing_timestamp_raises_clear_error(self) -> None:
        references = self.build_references()
        del references["finishReference"]["timestampSeconds"]

        with self.assertRaisesRegex(
            ValueError,
            "finishReference is missing a valid timestampSeconds value",
        ):
            build_phase_validation(references)


if __name__ == "__main__":
    unittest.main()