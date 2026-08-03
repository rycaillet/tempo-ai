from __future__ import annotations

import unittest

from app.club_detector import (
    calculate_selected_candidate_confidence,
    create_candidate_diagnostics,
    create_candidate_provenance,
    evaluate_shaft_candidate,
)


class ClubConfidenceCalibrationTests(unittest.TestCase):
    def create_candidate(self):
        provenance = create_candidate_provenance(
            search_region="corridor",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=1,
        )

        candidate, rejection_reason = evaluate_shaft_candidate(
            [100, 100, 500, 300],
            hand_anchor={"x": 105.0, "y": 105.0},
            frame_width=1000,
            frame_height=800,
            provenance=provenance,
        )

        self.assertIsNone(rejection_reason)
        self.assertIsNotNone(candidate)
        assert candidate is not None
        return candidate

    def test_image_only_confidence_uses_adjusted_image_score(self) -> None:
        candidate = self.create_candidate()
        diagnostics = create_candidate_diagnostics()
        diagnostics["temporalSelectionMode"] = "image_only"
        diagnostics["selectedTemporalScore"] = candidate["score"]

        confidence = calculate_selected_candidate_confidence(
            candidate,
            diagnostics=diagnostics,
        )

        expected = round(
            0.95 * candidate["score"] + 0.05 * 0.50,
            6,
        )

        self.assertEqual(confidence, expected)
        self.assertEqual(
            diagnostics["selectedConfidenceMode"],
            "image_only",
        )
        self.assertEqual(
            diagnostics["selectedCalibratedConfidence"],
            expected,
        )
        self.assertIsNone(
            diagnostics["selectedAngleContinuityConfidence"]
        )

    def test_temporal_confidence_combines_all_evidence(self) -> None:
        candidate = self.create_candidate()
        diagnostics = create_candidate_diagnostics()
        diagnostics["temporalSelectionMode"] = "temporal"
        diagnostics["selectedTemporalScore"] = 0.80
        diagnostics["selectedAngleChangeDegrees"] = 13.0
        diagnostics["selectedDistalShiftRatio"] = 0.06

        confidence = calculate_selected_candidate_confidence(
            candidate,
            diagnostics=diagnostics,
        )

        angle_continuity = 1.0 - 13.0 / 65.0
        distal_continuity = 1.0 - 0.06 / 0.30
        expected = round(
            0.45 * candidate["score"]
            + 0.25 * 0.80
            + 0.20 * angle_continuity
            + 0.10 * distal_continuity,
            6,
        )

        self.assertEqual(confidence, expected)
        self.assertEqual(
            diagnostics["selectedConfidenceMode"],
            "temporal",
        )
        self.assertEqual(
            diagnostics["selectedAngleContinuityConfidence"],
            round(angle_continuity, 6),
        )
        self.assertEqual(
            diagnostics["selectedDistalContinuityConfidence"],
            round(distal_continuity, 6),
        )

    def test_temporal_confidence_penalizes_weaker_continuity(self) -> None:
        candidate = self.create_candidate()

        strong = create_candidate_diagnostics()
        strong["temporalSelectionMode"] = "temporal"
        strong["selectedTemporalScore"] = 0.75
        strong["selectedAngleChangeDegrees"] = 5.0
        strong["selectedDistalShiftRatio"] = 0.03

        weak = create_candidate_diagnostics()
        weak["temporalSelectionMode"] = "temporal"
        weak["selectedTemporalScore"] = 0.75
        weak["selectedAngleChangeDegrees"] = 55.0
        weak["selectedDistalShiftRatio"] = 0.27

        strong_confidence = calculate_selected_candidate_confidence(
            candidate,
            diagnostics=strong,
        )
        weak_confidence = calculate_selected_candidate_confidence(
            candidate,
            diagnostics=weak,
        )

        self.assertGreater(strong_confidence, weak_confidence)

    def test_confidence_is_clamped_to_unit_interval(self) -> None:
        candidate = self.create_candidate()
        candidate["score"] = 1.5

        diagnostics = create_candidate_diagnostics()
        diagnostics["temporalSelectionMode"] = "temporal"
        diagnostics["selectedTemporalScore"] = 2.0
        diagnostics["selectedAngleChangeDegrees"] = -10.0
        diagnostics["selectedDistalShiftRatio"] = -1.0

        confidence = calculate_selected_candidate_confidence(
            candidate,
            diagnostics=diagnostics,
        )

        self.assertEqual(confidence, 1.0)


if __name__ == "__main__":
    unittest.main()