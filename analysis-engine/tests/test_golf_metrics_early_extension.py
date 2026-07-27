from __future__ import annotations

import unittest
from typing import Any

from app.metrics.early_extension import (
    build_early_extension_metrics,
    calculate_posture_change,
    classify_hip_shift,
    classify_spine_posture_loss,
    classify_vertical_direction,
    get_hip_center,
    get_spine_angle,
    severity_rank,
)


class EarlyExtensionMetricTests(unittest.TestCase):
    def build_reference(
        self,
        *,
        frame_index: int,
        timestamp_seconds: float,
        hip_x: float | None = 0.50,
        hip_y: float | None = 0.58,
        spine_angle: float | None = 42.0,
        pose_detected: bool = True,
    ) -> dict[str, Any]:
        geometry: dict[str, Any] = {}

        if hip_x is not None and hip_y is not None:
            geometry["hipCenter"] = {
                "x": hip_x,
                "y": hip_y,
            }

        if spine_angle is not None:
            geometry["spineAngle"] = spine_angle

        return {
            "frameIndex": frame_index,
            "timestampSeconds": timestamp_seconds,
            "poseDetected": pose_detected,
            "geometry": geometry,
        }

    def build_references(
        self,
        *,
        address_hip_y: float = 0.58,
        top_hip_y: float = 0.59,
        downswing_hip_y: float = 0.60,
        impact_hip_y: float = 0.60,
        finish_hip_y: float = 0.59,
        address_spine: float = 42.0,
        top_spine: float = 43.0,
        downswing_spine: float = 41.0,
        impact_spine: float = 40.0,
        finish_spine: float = 41.0,
    ) -> dict[str, dict[str, Any]]:
        return {
            "addressReference": self.build_reference(
                frame_index=10,
                timestamp_seconds=1.0,
                hip_y=address_hip_y,
                spine_angle=address_spine,
            ),
            "topOfBackswing": self.build_reference(
                frame_index=20,
                timestamp_seconds=2.0,
                hip_y=top_hip_y,
                spine_angle=top_spine,
            ),
            "downswingStart": self.build_reference(
                frame_index=24,
                timestamp_seconds=2.2,
                hip_y=downswing_hip_y,
                spine_angle=downswing_spine,
            ),
            "impactReference": self.build_reference(
                frame_index=28,
                timestamp_seconds=2.4,
                hip_y=impact_hip_y,
                spine_angle=impact_spine,
            ),
            "finishReference": self.build_reference(
                frame_index=40,
                timestamp_seconds=3.0,
                hip_y=finish_hip_y,
                spine_angle=finish_spine,
            ),
        }

    def test_get_hip_center_returns_valid_point(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            hip_x=0.45,
            hip_y=0.62,
        )

        self.assertEqual(
            get_hip_center(reference),
            {
                "x": 0.45,
                "y": 0.62,
            },
        )

    def test_get_hip_center_returns_none_when_missing(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            hip_x=None,
            hip_y=None,
        )

        self.assertIsNone(get_hip_center(reference))

    def test_get_spine_angle_returns_value(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            spine_angle=44.5,
        )

        self.assertEqual(
            get_spine_angle(reference),
            44.5,
        )

    def test_get_spine_angle_returns_none_when_missing(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            spine_angle=None,
        )

        self.assertIsNone(get_spine_angle(reference))

    def test_classify_vertical_direction_stationary(
        self,
    ) -> None:
        self.assertEqual(
            classify_vertical_direction(0.005),
            "stationary",
        )

    def test_classify_vertical_direction_down(
        self,
    ) -> None:
        self.assertEqual(
            classify_vertical_direction(0.03),
            "down",
        )

    def test_classify_vertical_direction_up(
        self,
    ) -> None:
        self.assertEqual(
            classify_vertical_direction(-0.03),
            "up",
        )

    def test_calculate_posture_change_returns_expected_values(
        self,
    ) -> None:
        start = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            hip_x=0.50,
            hip_y=0.58,
            spine_angle=42.0,
        )
        end = self.build_reference(
            frame_index=2,
            timestamp_seconds=0.1,
            hip_x=0.53,
            hip_y=0.64,
            spine_angle=34.0,
        )

        result = calculate_posture_change(
            start_reference=start,
            end_reference=end,
            frame_width=1000.0,
            frame_height=500.0,
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertEqual(
            result["deltaXNormalized"],
            0.03,
        )
        self.assertEqual(
            result["deltaYNormalized"],
            0.06,
        )
        self.assertEqual(
            result["deltaXPixels"],
            30.0,
        )
        self.assertEqual(
            result["deltaYPixels"],
            30.0,
        )
        self.assertEqual(
            result["verticalDirection"],
            "down",
        )
        self.assertEqual(
            result["spineAngleChangeDegrees"],
            -8.0,
        )
        self.assertEqual(
            result["postureLossDegrees"],
            8.0,
        )

    def test_calculate_posture_change_returns_none_without_hips(
        self,
    ) -> None:
        start = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            hip_x=None,
            hip_y=None,
        )
        end = self.build_reference(
            frame_index=2,
            timestamp_seconds=0.1,
        )

        result = calculate_posture_change(
            start_reference=start,
            end_reference=end,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertIsNone(result)

    def test_classify_hip_shift_within_target(
        self,
    ) -> None:
        result = classify_hip_shift(0.02)

        self.assertEqual(
            result["status"],
            "within_target",
        )
        self.assertEqual(
            result["severity"],
            "none",
        )

    def test_classify_hip_shift_mild(
        self,
    ) -> None:
        result = classify_hip_shift(0.05)

        self.assertEqual(
            result["status"],
            "mild_depth_loss",
        )
        self.assertEqual(
            result["severity"],
            "mild",
        )

    def test_classify_hip_shift_moderate(
        self,
    ) -> None:
        result = classify_hip_shift(0.08)

        self.assertEqual(
            result["status"],
            "moderate_depth_loss",
        )
        self.assertEqual(
            result["severity"],
            "moderate",
        )

    def test_classify_hip_shift_severe(
        self,
    ) -> None:
        result = classify_hip_shift(0.12)

        self.assertEqual(
            result["status"],
            "severe_depth_loss",
        )
        self.assertEqual(
            result["severity"],
            "severe",
        )

    def test_classify_hip_shift_not_available(
        self,
    ) -> None:
        result = classify_hip_shift(None)

        self.assertEqual(
            result["status"],
            "not_available",
        )
        self.assertIsNone(result["severity"])

    def test_classify_spine_posture_loss_within_target(
        self,
    ) -> None:
        result = classify_spine_posture_loss(4.0)

        self.assertEqual(
            result["status"],
            "within_target",
        )
        self.assertEqual(
            result["severity"],
            "none",
        )

    def test_classify_spine_posture_loss_mild(
        self,
    ) -> None:
        result = classify_spine_posture_loss(8.0)

        self.assertEqual(
            result["status"],
            "mild_posture_loss",
        )
        self.assertEqual(
            result["severity"],
            "mild",
        )

    def test_classify_spine_posture_loss_moderate(
        self,
    ) -> None:
        result = classify_spine_posture_loss(12.0)

        self.assertEqual(
            result["status"],
            "moderate_posture_loss",
        )
        self.assertEqual(
            result["severity"],
            "moderate",
        )

    def test_classify_spine_posture_loss_severe(
        self,
    ) -> None:
        result = classify_spine_posture_loss(18.0)

        self.assertEqual(
            result["status"],
            "severe_posture_loss",
        )
        self.assertEqual(
            result["severity"],
            "severe",
        )

    def test_severity_rank_orders_levels(
        self,
    ) -> None:
        self.assertLess(
            severity_rank("none"),
            severity_rank("mild"),
        )
        self.assertLess(
            severity_rank("mild"),
            severity_rank("moderate"),
        )
        self.assertLess(
            severity_rank("moderate"),
            severity_rank("severe"),
        )

    def test_build_metrics_returns_complete_neutral_result(
        self,
    ) -> None:
        result = build_early_extension_metrics(
            references=self.build_references(),
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "neutral",
        )
        self.assertEqual(
            result["issueCount"],
            0,
        )
        self.assertIsNone(result["primaryIssue"])
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 5,
                "total": 5,
                "ratio": 1.0,
            },
        )
        self.assertEqual(
            result["feedback"]["status"],
            "within_target",
        )

    def test_build_metrics_detects_mild_early_extension(
        self,
    ) -> None:
        references = self.build_references(
            impact_hip_y=0.63,
            impact_spine=35.0,
        )

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "mild_early_extension",
        )
        self.assertGreaterEqual(
            result["issueCount"],
            1,
        )

    def test_build_metrics_detects_moderate_early_extension(
        self,
    ) -> None:
        references = self.build_references(
            impact_hip_y=0.66,
            impact_spine=30.0,
        )

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "moderate_early_extension",
        )

    def test_build_metrics_detects_severe_early_extension(
        self,
    ) -> None:
        references = self.build_references(
            impact_hip_y=0.70,
            impact_spine=20.0,
        )

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "severe_early_extension",
        )

    def test_build_metrics_uses_most_severe_issue(
        self,
    ) -> None:
        references = self.build_references(
            impact_hip_y=0.63,
            impact_spine=25.0,
        )

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "severe_early_extension",
        )
        self.assertEqual(
            result["primaryIssue"],
            "impactSpinePosture",
        )

    def test_build_metrics_returns_incomplete_without_impact_hips(
        self,
    ) -> None:
        references = self.build_references()

        references["impactReference"] = (
            self.build_reference(
                frame_index=28,
                timestamp_seconds=2.4,
                hip_x=None,
                hip_y=None,
                spine_angle=None,
            )
        )

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "insufficient_data",
        )
        self.assertLess(
            result[
                "measurementCompleteness"
            ]["ratio"],
            1.0,
        )

    def test_confidence_reduces_when_pose_is_missing(
        self,
    ) -> None:
        references = self.build_references()

        references["impactReference"][
            "poseDetected"
        ] = False

        result = build_early_extension_metrics(
            references=references,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["confidence"],
            0.75,
        )

    def test_reference_frame_metadata_is_returned(
        self,
    ) -> None:
        result = build_early_extension_metrics(
            references=self.build_references(),
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            result["referenceFrames"][
                "addressReference"
            ]["frameIndex"],
            10,
        )
        self.assertEqual(
            result["referenceFrames"][
                "impactReference"
            ]["frameIndex"],
            28,
        )

    def test_feedback_basis_explains_proxy_limitations(
        self,
    ) -> None:
        result = build_early_extension_metrics(
            references=self.build_references(),
            frame_width=1920.0,
            frame_height=1080.0,
        )

        basis = result["feedback"]["basis"]

        self.assertIn("2D posture-loss proxy", basis)
        self.assertIn(
            "does not directly measure",
            basis,
        )
        self.assertIn("camera position", basis)

    def test_missing_required_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        references.pop("impactReference")

        with self.assertRaisesRegex(
            ValueError,
            "impactReference is missing",
        ):
            build_early_extension_metrics(
                references=references,
                frame_width=1920.0,
                frame_height=1080.0,
            )

    def test_invalid_frame_width_raises_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Frame width must be greater than zero",
        ):
            build_early_extension_metrics(
                references=self.build_references(),
                frame_width=0.0,
                frame_height=1080.0,
            )

    def test_invalid_frame_height_raises_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Frame height must be greater than zero",
        ):
            build_early_extension_metrics(
                references=self.build_references(),
                frame_width=1920.0,
                frame_height=0.0,
            )


if __name__ == "__main__":
    unittest.main()