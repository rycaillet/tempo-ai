from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from app.club_detector import (
    ClubFrameDetection,
    apply_temporal_consistency_validation,
    build_shaft_candidate,
    calculate_axial_angle_change,
    calculate_hand_anchor,
    calculate_nearest_endpoint_distance,
    create_club_detection_output_path,
    distance_from_point_to_segment,
    get_reference_phases,
    get_rotated_dimensions,
)


def create_club_frame_detection(
    *,
    phase: str,
    frame_index: int,
    angle_degrees: float | None,
    detected: bool = True,
) -> ClubFrameDetection:
    shaft_line = (
        {
            "start": {
                "x": 100.0,
                "y": 100.0,
            },
            "end": {
                "x": 300.0,
                "y": 300.0,
            },
            "lengthPixels": 282.843,
            "angleDegrees": angle_degrees,
        }
        if detected
        and angle_degrees is not None
        else None
    )

    return {
        "phase": phase,
        "frameIndex": frame_index,
        "timestampSeconds": (
            frame_index / 30.0
        ),
        "detected": detected,
        "confidence": (
            0.8 if detected else 0.0
        ),
        "handAnchor": (
            {
                "x": 100.0,
                "y": 100.0,
            }
            if detected
            else None
        ),
        "shaftLine": shaft_line,
        "candidateCount": (
            3 if detected else 0
        ),
        "failureReason": (
            None
            if detected
            else "No reliable candidate."
        ),
        "debugImagePath": None,
        "temporalStatus": "pending",
        "temporalComparison": None,
    }


class ClubDetectorTests(
    unittest.TestCase
):
    def test_creates_expected_output_path(
        self,
    ) -> None:
        source = Path(
            "output/swing-refined-phases.json"
        )

        result = (
            create_club_detection_output_path(
                source
            )
        )

        self.assertEqual(
            result,
            Path(
                "output/"
                "swing-club-detection.json"
            ),
        )

    def test_rotated_dimensions_swap_for_clockwise_rotation(
        self,
    ) -> None:
        self.assertEqual(
            get_rotated_dimensions(
                444,
                960,
                "clockwise90",
            ),
            (960, 444),
        )

    def test_rotated_dimensions_remain_for_no_rotation(
        self,
    ) -> None:
        self.assertEqual(
            get_rotated_dimensions(
                1920,
                1080,
                "none",
            ),
            (1920, 1080),
        )

    def test_hand_anchor_averages_visible_wrists(
        self,
    ) -> None:
        pose_frame: dict[str, Any] = {
            "landmarks": [
                {
                    "index": 15,
                    "x": 0.40,
                    "y": 0.50,
                    "visibility": 0.90,
                },
                {
                    "index": 16,
                    "x": 0.60,
                    "y": 0.70,
                    "visibility": 0.80,
                },
            ]
        }

        result = calculate_hand_anchor(
            pose_frame,
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertAlmostEqual(
            result["x"],
            500.0,
        )

        self.assertAlmostEqual(
            result["y"],
            300.0,
        )

    def test_hand_anchor_uses_one_reliable_wrist(
        self,
    ) -> None:
        pose_frame: dict[str, Any] = {
            "landmarks": [
                {
                    "index": 15,
                    "x": 0.25,
                    "y": 0.50,
                    "visibility": 0.90,
                },
                {
                    "index": 16,
                    "x": 0.75,
                    "y": 0.50,
                    "visibility": 0.10,
                },
            ]
        }

        result = calculate_hand_anchor(
            pose_frame,
            frame_width=800,
            frame_height=600,
        )

        self.assertEqual(
            result,
            {
                "x": 200.0,
                "y": 300.0,
            },
        )

    def test_hand_anchor_returns_none_without_reliable_wrists(
        self,
    ) -> None:
        pose_frame: dict[str, Any] = {
            "landmarks": [
                {
                    "index": 15,
                    "x": 0.25,
                    "y": 0.50,
                    "visibility": 0.10,
                }
            ]
        }

        result = calculate_hand_anchor(
            pose_frame,
            frame_width=800,
            frame_height=600,
        )

        self.assertIsNone(result)

    def test_point_to_segment_distance_is_zero_on_line(
        self,
    ) -> None:
        distance = (
            distance_from_point_to_segment(
                {
                    "x": 50.0,
                    "y": 50.0,
                },
                {
                    "x": 0.0,
                    "y": 0.0,
                },
                {
                    "x": 100.0,
                    "y": 100.0,
                },
            )
        )

        self.assertAlmostEqual(
            distance,
            0.0,
        )

    def test_nearest_endpoint_distance_uses_closest_endpoint(
        self,
    ) -> None:
        distance = (
            calculate_nearest_endpoint_distance(
                {
                    "x": 12.0,
                    "y": 10.0,
                },
                {
                    "x": 10.0,
                    "y": 10.0,
                },
                {
                    "x": 100.0,
                    "y": 100.0,
                },
            )
        )

        self.assertEqual(
            distance,
            2.0,
        )

    def test_nearest_endpoint_distance_differs_from_segment_distance(
        self,
    ) -> None:
        point = {
            "x": 50.0,
            "y": 50.0,
        }

        start = {
            "x": 0.0,
            "y": 0.0,
        }

        end = {
            "x": 100.0,
            "y": 100.0,
        }

        segment_distance = (
            distance_from_point_to_segment(
                point,
                start,
                end,
            )
        )

        endpoint_distance = (
            calculate_nearest_endpoint_distance(
                point,
                start,
                end,
            )
        )

        self.assertEqual(
            segment_distance,
            0.0,
        )

        self.assertGreater(
            endpoint_distance,
            0.0,
        )

    def test_candidate_accepts_plausible_line_with_endpoint_near_hands(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [100, 100, 500, 500],
            hand_anchor={
                "x": 110.0,
                "y": 110.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNotNone(candidate)

        assert candidate is not None

        self.assertGreater(
            candidate["score"],
            0.5,
        )

        self.assertGreater(
            candidate["line"][
                "lengthPixels"
            ],
            500.0,
        )

        self.assertLess(
            candidate[
                "nearestEndpointDistanceRatio"
            ],
            0.02,
        )

    def test_candidate_rejects_short_line(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [100, 100, 110, 110],
            hand_anchor={
                "x": 100.0,
                "y": 100.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(candidate)

    def test_candidate_rejects_line_far_from_hands(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [700, 500, 950, 700],
            hand_anchor={
                "x": 50.0,
                "y": 50.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(candidate)

    def test_candidate_rejects_line_that_only_passes_near_hands(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [500, 0, 500, 800],
            hand_anchor={
                "x": 500.0,
                "y": 400.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(candidate)

    def test_candidate_rejects_excessively_long_line(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [100, 100, 900, 700],
            hand_anchor={
                "x": 105.0,
                "y": 105.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(candidate)

    def test_candidate_rejects_production_full_height_false_positive(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [604, 443, 604, 0],
            hand_anchor={
                "x": 454.601,
                "y": 115.49,
            },
            frame_width=604,
            frame_height=443,
        )

        self.assertIsNone(candidate)

    def test_candidate_rejects_invalid_frame_dimensions(
        self,
    ) -> None:
        candidate = build_shaft_candidate(
            [10, 10, 100, 100],
            hand_anchor={
                "x": 10.0,
                "y": 10.0,
            },
            frame_width=0,
            frame_height=443,
        )

        self.assertIsNone(candidate)

    def test_reference_phases_follow_expected_order(
        self,
    ) -> None:
        payload = {
            "phases": {
                "impactReference": {
                    "frameIndex": 107,
                },
                "address": {
                    "frameIndex": 65,
                },
                "topOfBackswing": {
                    "frameIndex": 93,
                },
                "takeaway": {
                    "frameIndex": 67,
                },
                "downswingStart": {
                    "frameIndex": 102,
                },
                "finishReference": {
                    "frameIndex": 117,
                },
            }
        }

        result = get_reference_phases(
            payload
        )

        self.assertEqual(
            [
                phase_name
                for phase_name, _ in result
            ],
            [
                "address",
                "takeaway",
                "topOfBackswing",
                "downswingStart",
                "impactReference",
                "finishReference",
            ],
        )

    def test_reference_phases_reject_missing_phase_object(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "phases object",
        ):
            get_reference_phases({})

    def test_axial_angle_change_handles_reversed_line_direction(
        self,
    ) -> None:
        result = calculate_axial_angle_change(
            5.0,
            175.0,
        )

        self.assertEqual(
            result,
            10.0,
        )

    def test_temporal_validation_accepts_small_angle_change(
        self,
    ) -> None:
        frames = [
            create_club_frame_detection(
                phase="address",
                frame_index=65,
                angle_degrees=40.0,
            ),
            create_club_frame_detection(
                phase="takeaway",
                frame_index=70,
                angle_degrees=55.0,
            ),
        ]

        apply_temporal_consistency_validation(
            frames
        )

        self.assertEqual(
            frames[0]["temporalStatus"],
            "not_compared",
        )

        self.assertIsNone(
            frames[0]["temporalComparison"]
        )

        self.assertEqual(
            frames[1]["temporalStatus"],
            "consistent",
        )

        self.assertEqual(
            frames[1]["temporalComparison"],
            {
                "previousPhase": "address",
                "previousFrameIndex": 65,
                "angleChangeDegrees": 15.0,
                "withinThreshold": True,
            },
        )

    def test_temporal_validation_flags_large_angle_change(
        self,
    ) -> None:
        frames = [
            create_club_frame_detection(
                phase="address",
                frame_index=65,
                angle_degrees=5.0,
            ),
            create_club_frame_detection(
                phase="takeaway",
                frame_index=70,
                angle_degrees=90.0,
            ),
        ]

        apply_temporal_consistency_validation(
            frames
        )

        self.assertEqual(
            frames[1]["temporalStatus"],
            "review",
        )

        comparison = frames[1][
            "temporalComparison"
        ]

        self.assertIsNotNone(
            comparison
        )

        assert comparison is not None

        self.assertEqual(
            comparison[
                "angleChangeDegrees"
            ],
            85.0,
        )

        self.assertFalse(
            comparison[
                "withinThreshold"
            ]
        )

    def test_temporal_validation_skips_failed_detection(
        self,
    ) -> None:
        frames = [
            create_club_frame_detection(
                phase="address",
                frame_index=65,
                angle_degrees=40.0,
            ),
            create_club_frame_detection(
                phase="takeaway",
                frame_index=70,
                angle_degrees=None,
                detected=False,
            ),
            create_club_frame_detection(
                phase="topOfBackswing",
                frame_index=90,
                angle_degrees=50.0,
            ),
        ]

        apply_temporal_consistency_validation(
            frames
        )

        self.assertEqual(
            frames[1]["temporalStatus"],
            "unavailable",
        )

        self.assertIsNone(
            frames[1]["temporalComparison"]
        )

        comparison = frames[2][
            "temporalComparison"
        ]

        self.assertIsNotNone(
            comparison
        )

        assert comparison is not None

        self.assertEqual(
            comparison["previousPhase"],
            "address",
        )

        self.assertEqual(
            comparison[
                "previousFrameIndex"
            ],
            65,
        )

        self.assertEqual(
            comparison[
                "angleChangeDegrees"
            ],
            10.0,
        )

    def test_temporal_validation_retains_review_detection_for_next_comparison(
        self,
    ) -> None:
        frames = [
            create_club_frame_detection(
                phase="address",
                frame_index=65,
                angle_degrees=5.0,
            ),
            create_club_frame_detection(
                phase="takeaway",
                frame_index=70,
                angle_degrees=90.0,
            ),
            create_club_frame_detection(
                phase="topOfBackswing",
                frame_index=90,
                angle_degrees=100.0,
            ),
        ]

        apply_temporal_consistency_validation(
            frames
        )

        self.assertEqual(
            frames[1]["temporalStatus"],
            "review",
        )

        self.assertEqual(
            frames[2]["temporalStatus"],
            "consistent",
        )

        comparison = frames[2][
            "temporalComparison"
        ]

        self.assertIsNotNone(
            comparison
        )

        assert comparison is not None

        self.assertEqual(
            comparison["previousPhase"],
            "takeaway",
        )

        self.assertEqual(
            comparison[
                "angleChangeDegrees"
            ],
            10.0,
        )


if __name__ == "__main__":
    unittest.main()