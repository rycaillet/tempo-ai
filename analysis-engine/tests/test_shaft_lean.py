from __future__ import annotations

import unittest
from typing import Any

from app.metrics.shaft_lean import (
    build_shaft_lean_metrics,
    calculate_point_distance,
    calculate_signed_lean_from_vertical,
    classify_camera_relative_lean,
    get_phase_detection,
    orient_shaft_line,
)


def create_impact_detection(
    *,
    detected: bool = True,
    confidence: float = 0.8,
    hand_anchor: dict[str, float] | None = None,
    shaft_start: dict[str, float] | None = None,
    shaft_end: dict[str, float] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "phase": "impactReference",
        "frameIndex": 107,
        "timestampSeconds": 4.28,
        "detected": detected,
        "confidence": confidence,
        "handAnchor": (
            hand_anchor
            if hand_anchor is not None
            else {
                "x": 100.0,
                "y": 100.0,
            }
        ),
        "shaftLine": (
            {
                "start": (
                    shaft_start
                    if shaft_start is not None
                    else {
                        "x": 102.0,
                        "y": 103.0,
                    }
                ),
                "end": (
                    shaft_end
                    if shaft_end is not None
                    else {
                        "x": 80.0,
                        "y": 180.0,
                    }
                ),
                "lengthPixels": 80.0,
                "angleDegrees": 105.0,
            }
            if detected
            else None
        ),
        "candidateCount": 3 if detected else 0,
        "failureReason": failure_reason,
        "debugImagePath": None,
    }


class ShaftLeanTests(unittest.TestCase):
    def test_calculate_point_distance(self) -> None:
        distance = calculate_point_distance(
            {
                "x": 0.0,
                "y": 0.0,
            },
            {
                "x": 3.0,
                "y": 4.0,
            },
        )

        self.assertEqual(distance, 5.0)

    def test_calculate_point_distance_rejects_invalid_point(
        self,
    ) -> None:
        distance = calculate_point_distance(
            {
                "x": "invalid",
                "y": 0.0,
            },
            {
                "x": 3.0,
                "y": 4.0,
            },
        )

        self.assertIsNone(distance)

    def test_get_phase_detection_returns_impact_frame(
        self,
    ) -> None:
        impact = create_impact_detection()

        result = get_phase_detection(
            {
                "frames": [
                    {
                        "phase": "address",
                    },
                    impact,
                ],
            },
            "impactReference",
        )

        self.assertIs(result, impact)

    def test_get_phase_detection_returns_none_when_missing(
        self,
    ) -> None:
        result = get_phase_detection(
            {
                "frames": [],
            },
            "impactReference",
        )

        self.assertIsNone(result)

    def test_get_phase_detection_requires_frames_list(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "frames list",
        ):
            get_phase_detection(
                {},
                "impactReference",
            )

    def test_orient_shaft_line_selects_endpoint_nearest_hands(
        self,
    ) -> None:
        result = orient_shaft_line(
            {
                "start": {
                    "x": 102.0,
                    "y": 103.0,
                },
                "end": {
                    "x": 80.0,
                    "y": 180.0,
                },
            },
            {
                "x": 100.0,
                "y": 100.0,
            },
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertEqual(
            result["gripEndpoint"],
            {
                "x": 102.0,
                "y": 103.0,
            },
        )
        self.assertEqual(
            result["clubheadEndpoint"],
            {
                "x": 80.0,
                "y": 180.0,
            },
        )
        self.assertGreater(
            result["orientationConfidence"],
            0.0,
        )

    def test_orient_shaft_line_handles_reversed_endpoints(
        self,
    ) -> None:
        result = orient_shaft_line(
            {
                "start": {
                    "x": 80.0,
                    "y": 180.0,
                },
                "end": {
                    "x": 102.0,
                    "y": 103.0,
                },
            },
            {
                "x": 100.0,
                "y": 100.0,
            },
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertEqual(
            result["gripEndpoint"],
            {
                "x": 102.0,
                "y": 103.0,
            },
        )
        self.assertEqual(
            result["clubheadEndpoint"],
            {
                "x": 80.0,
                "y": 180.0,
            },
        )

    def test_orient_shaft_line_rejects_zero_length_line(
        self,
    ) -> None:
        result = orient_shaft_line(
            {
                "start": {
                    "x": 10.0,
                    "y": 10.0,
                },
                "end": {
                    "x": 10.0,
                    "y": 10.0,
                },
            },
            {
                "x": 10.0,
                "y": 10.0,
            },
        )

        self.assertIsNone(result)

    def test_signed_lean_is_negative_toward_image_left(
        self,
    ) -> None:
        result = (
            calculate_signed_lean_from_vertical(
                {
                    "x": 100.0,
                    "y": 100.0,
                },
                {
                    "x": 80.0,
                    "y": 180.0,
                },
            )
        )

        self.assertIsNotNone(result)
        self.assertLess(result, 0.0)

    def test_signed_lean_is_positive_toward_image_right(
        self,
    ) -> None:
        result = (
            calculate_signed_lean_from_vertical(
                {
                    "x": 100.0,
                    "y": 100.0,
                },
                {
                    "x": 120.0,
                    "y": 180.0,
                },
            )
        )

        self.assertIsNotNone(result)
        self.assertGreater(result, 0.0)

    def test_vertical_shaft_has_zero_lean(self) -> None:
        result = (
            calculate_signed_lean_from_vertical(
                {
                    "x": 100.0,
                    "y": 100.0,
                },
                {
                    "x": 100.0,
                    "y": 180.0,
                },
            )
        )

        self.assertEqual(result, 0.0)

    def test_classifies_image_left_lean(self) -> None:
        result = classify_camera_relative_lean(
            -15.0
        )

        self.assertEqual(
            result["status"],
            "leans_image_left",
        )
        self.assertEqual(
            result["direction"],
            "image_left",
        )

    def test_classifies_image_right_lean(self) -> None:
        result = classify_camera_relative_lean(
            15.0
        )

        self.assertEqual(
            result["status"],
            "leans_image_right",
        )
        self.assertEqual(
            result["direction"],
            "image_right",
        )

    def test_classifies_nearly_vertical_shaft(self) -> None:
        result = classify_camera_relative_lean(
            4.0
        )

        self.assertEqual(
            result["status"],
            "approximately_vertical",
        )
        self.assertEqual(
            result["direction"],
            "vertical",
        )

    def test_builds_available_shaft_lean_metrics(
        self,
    ) -> None:
        result = build_shaft_lean_metrics(
            {
                "frames": [
                    create_impact_detection(),
                ],
            }
        )

        self.assertEqual(
            result["classification"],
            "observed",
        )
        self.assertEqual(
            result["measurementCompleteness"][
                "ratio"
            ],
            1.0,
        )
        self.assertEqual(
            result["referenceFrame"][
                "frameIndex"
            ],
            107,
        )
        self.assertEqual(
            result["measurements"][
                "cameraRelativeDirection"
            ],
            "image_left",
        )
        self.assertLess(
            result["measurements"][
                "signedLeanFromVerticalDegrees"
            ],
            0.0,
        )
        self.assertGreater(
            result["confidence"],
            0.0,
        )

    def test_builds_incomplete_result_when_impact_missing(
        self,
    ) -> None:
        result = build_shaft_lean_metrics(
            {
                "frames": [],
            }
        )

        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "insufficient_data",
        )
        self.assertEqual(
            result["confidence"],
            0.0,
        )

    def test_builds_incomplete_result_when_detection_failed(
        self,
    ) -> None:
        result = build_shaft_lean_metrics(
            {
                "frames": [
                    create_impact_detection(
                        detected=False,
                        failure_reason=(
                            "No shaft candidate."
                        ),
                    ),
                ],
            }
        )

        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(
            result["feedback"]["message"],
            "No shaft candidate.",
        )
        self.assertEqual(
            result["referenceFrame"][
                "clubDetected"
            ],
            False,
        )

    def test_builds_incomplete_result_without_hand_anchor(
        self,
    ) -> None:
        impact = create_impact_detection()
        impact["handAnchor"] = None

        result = build_shaft_lean_metrics(
            {
                "frames": [impact],
            }
        )

        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertIn(
            "hand anchor",
            result["feedback"]["message"],
        )

    def test_metric_is_independent_of_detector_endpoint_order(
        self,
    ) -> None:
        normal_result = build_shaft_lean_metrics(
            {
                "frames": [
                    create_impact_detection(),
                ],
            }
        )

        reversed_result = build_shaft_lean_metrics(
            {
                "frames": [
                    create_impact_detection(
                        shaft_start={
                            "x": 80.0,
                            "y": 180.0,
                        },
                        shaft_end={
                            "x": 102.0,
                            "y": 103.0,
                        },
                    ),
                ],
            }
        )

        self.assertEqual(
            normal_result["measurements"][
                "signedLeanFromVerticalDegrees"
            ],
            reversed_result["measurements"][
                "signedLeanFromVerticalDegrees"
            ],
        )


if __name__ == "__main__":
    unittest.main()