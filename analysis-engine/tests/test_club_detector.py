from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from app.club_detector import (
    build_shaft_candidate,
    calculate_hand_anchor,
    create_club_detection_output_path,
    distance_from_point_to_segment,
    get_reference_phases,
    get_rotated_dimensions,
)


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

    def test_candidate_accepts_long_line_near_hands(
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


if __name__ == "__main__":
    unittest.main()