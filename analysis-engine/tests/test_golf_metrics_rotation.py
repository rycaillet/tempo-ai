from __future__ import annotations

import unittest
from typing import Any

from app.metrics.rotation import (
    build_rotation_metrics,
    calculate_change_from_address,
    calculate_pair_state,
    calculate_return_ratio,
    calculate_rotation_state,
    classify_backswing_hip_turn,
    classify_backswing_shoulder_turn,
    classify_finish_rotation,
    classify_impact_unwinding,
    classify_top_separation,
    get_point,
)


class RotationMetricTests(unittest.TestCase):
    @staticmethod
    def build_point(
        *,
        x: float,
        y: float,
        z: float,
    ) -> dict[str, float]:
        return {
            "x": x,
            "y": y,
            "z": z,
            "visibility": 0.99,
        }

    def build_reference(
        self,
        *,
        frame_index: int,
        timestamp_seconds: float,
        shoulder_depth: float | None,
        hip_depth: float | None,
        pose_detected: bool = True,
    ) -> dict[str, Any]:
        geometry: dict[str, Any] = {}

        if shoulder_depth is not None:
            geometry["leftShoulder"] = self.build_point(
                x=0.40,
                y=0.30,
                z=-shoulder_depth / 2.0,
            )
            geometry["rightShoulder"] = self.build_point(
                x=0.60,
                y=0.30,
                z=shoulder_depth / 2.0,
            )

        if hip_depth is not None:
            geometry["leftHip"] = self.build_point(
                x=0.44,
                y=0.60,
                z=-hip_depth / 2.0,
            )
            geometry["rightHip"] = self.build_point(
                x=0.56,
                y=0.60,
                z=hip_depth / 2.0,
            )

        return {
            "frameIndex": frame_index,
            "timestampSeconds": timestamp_seconds,
            "poseDetected": pose_detected,
            "geometry": geometry,
        }

    def build_references(
        self,
        *,
        address_shoulder: float = 0.01,
        address_hip: float = 0.01,
        top_shoulder: float = 0.09,
        top_hip: float = 0.04,
        downswing_shoulder: float = 0.07,
        downswing_hip: float = 0.05,
        impact_shoulder: float = 0.04,
        impact_hip: float = 0.04,
        finish_shoulder: float = 0.09,
        finish_hip: float = 0.06,
    ) -> dict[str, dict[str, Any]]:
        return {
            "addressReference": self.build_reference(
                frame_index=10,
                timestamp_seconds=1.0,
                shoulder_depth=address_shoulder,
                hip_depth=address_hip,
            ),
            "topOfBackswing": self.build_reference(
                frame_index=20,
                timestamp_seconds=2.0,
                shoulder_depth=top_shoulder,
                hip_depth=top_hip,
            ),
            "downswingStart": self.build_reference(
                frame_index=24,
                timestamp_seconds=2.2,
                shoulder_depth=downswing_shoulder,
                hip_depth=downswing_hip,
            ),
            "impactReference": self.build_reference(
                frame_index=28,
                timestamp_seconds=2.4,
                shoulder_depth=impact_shoulder,
                hip_depth=impact_hip,
            ),
            "finishReference": self.build_reference(
                frame_index=40,
                timestamp_seconds=3.0,
                shoulder_depth=finish_shoulder,
                hip_depth=finish_hip,
            ),
        }

    def test_get_point_returns_valid_point(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            shoulder_depth=0.10,
            hip_depth=0.05,
        )

        point = get_point(
            reference,
            "leftShoulder",
        )

        self.assertIsNotNone(point)

        assert point is not None

        self.assertEqual(point["x"], 0.40)
        self.assertEqual(point["y"], 0.30)
        self.assertEqual(point["z"], -0.05)

    def test_get_point_returns_none_when_missing(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            shoulder_depth=None,
            hip_depth=0.05,
        )

        self.assertIsNone(
            get_point(reference, "leftShoulder")
        )

    def test_calculate_pair_state_returns_depth_separation(
        self,
    ) -> None:
        left_point = self.build_point(
            x=0.40,
            y=0.30,
            z=-0.05,
        )
        right_point = self.build_point(
            x=0.60,
            y=0.30,
            z=0.05,
        )

        result = calculate_pair_state(
            left_point,
            right_point,
        )

        self.assertEqual(
            result["imageWidthNormalized"],
            0.20,
        )
        self.assertEqual(
            result["depthSeparationNormalized"],
            0.10,
        )
        self.assertEqual(
            result[
                "absoluteDepthSeparationNormalized"
            ],
            0.10,
        )

    def test_calculate_pair_state_handles_missing_point(
        self,
    ) -> None:
        result = calculate_pair_state(
            None,
            self.build_point(
                x=0.60,
                y=0.30,
                z=0.05,
            ),
        )

        self.assertIsNone(
            result["depthSeparationNormalized"]
        )

    def test_calculate_rotation_state_returns_separation(
        self,
    ) -> None:
        reference = self.build_reference(
            frame_index=1,
            timestamp_seconds=0.0,
            shoulder_depth=0.10,
            hip_depth=0.04,
        )

        result = calculate_rotation_state(reference)

        self.assertEqual(
            result["shoulders"][
                "depthSeparationNormalized"
            ],
            0.10,
        )
        self.assertEqual(
            result["hips"][
                "depthSeparationNormalized"
            ],
            0.04,
        )
        self.assertEqual(
            result["shoulderHipSeparationProxy"],
            0.06,
        )

    def test_calculate_change_from_address(
        self,
    ) -> None:
        address = calculate_rotation_state(
            self.build_reference(
                frame_index=1,
                timestamp_seconds=0.0,
                shoulder_depth=0.01,
                hip_depth=0.01,
            )
        )
        top = calculate_rotation_state(
            self.build_reference(
                frame_index=2,
                timestamp_seconds=1.0,
                shoulder_depth=0.09,
                hip_depth=0.04,
            )
        )

        result = calculate_change_from_address(
            address_state=address,
            phase_state=top,
        )

        self.assertEqual(
            result[
                "absoluteShoulderDepthChangeNormalized"
            ],
            0.08,
        )
        self.assertEqual(
            result[
                "absoluteHipDepthChangeNormalized"
            ],
            0.03,
        )
        self.assertEqual(
            result[
                "shoulderHipRotationSeparationProxy"
            ],
            0.05,
        )

    def test_calculate_return_ratio(
        self,
    ) -> None:
        self.assertEqual(
            calculate_return_ratio(0.08, 0.03),
            0.625,
        )

    def test_calculate_return_ratio_clamps_result(
        self,
    ) -> None:
        self.assertEqual(
            calculate_return_ratio(0.08, 0.12),
            0.0,
        )
        self.assertEqual(
            calculate_return_ratio(0.08, 0.0),
            1.0,
        )

    def test_calculate_return_ratio_requires_top_turn(
        self,
    ) -> None:
        self.assertIsNone(
            calculate_return_ratio(0.0, 0.0)
        )

    def test_classify_backswing_shoulder_turn(
        self,
    ) -> None:
        self.assertEqual(
            classify_backswing_shoulder_turn(
                0.03
            )["status"],
            "limited_turn",
        )
        self.assertEqual(
            classify_backswing_shoulder_turn(
                0.08
            )["status"],
            "within_target",
        )

    def test_classify_backswing_hip_turn(
        self,
    ) -> None:
        self.assertEqual(
            classify_backswing_hip_turn(
                0.01
            )["status"],
            "limited_turn",
        )
        self.assertEqual(
            classify_backswing_hip_turn(
                0.05
            )["status"],
            "within_target",
        )
        self.assertEqual(
            classify_backswing_hip_turn(
                0.15
            )["status"],
            "excessive_turn",
        )

    def test_classify_top_separation(
        self,
    ) -> None:
        self.assertEqual(
            classify_top_separation(
                0.01
            )["status"],
            "limited_separation",
        )
        self.assertEqual(
            classify_top_separation(
                0.05
            )["status"],
            "within_target",
        )
        self.assertEqual(
            classify_top_separation(
                0.14
            )["status"],
            "excessive_separation",
        )

    def test_classify_impact_unwinding(
        self,
    ) -> None:
        self.assertEqual(
            classify_impact_unwinding(
                0.25
            )["status"],
            "limited_unwinding",
        )
        self.assertEqual(
            classify_impact_unwinding(
                0.70
            )["status"],
            "within_target",
        )

    def test_classify_finish_rotation(
        self,
    ) -> None:
        self.assertEqual(
            classify_finish_rotation(
                0.02
            )["status"],
            "limited_finish",
        )
        self.assertEqual(
            classify_finish_rotation(
                0.08
            )["status"],
            "within_target",
        )

    def test_build_rotation_metrics_returns_neutral_result(
        self,
    ) -> None:
        result = build_rotation_metrics(
            self.build_references()
        )

        self.assertEqual(
            result["classification"],
            "neutral",
        )
        self.assertEqual(result["issueCount"], 0)
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

    def test_build_rotation_metrics_detects_limited_turn(
        self,
    ) -> None:
        references = self.build_references(
            top_shoulder=0.03,
            top_hip=0.02,
        )

        result = build_rotation_metrics(references)

        self.assertEqual(
            result["classification"],
            "needs_attention",
        )
        self.assertGreater(result["issueCount"], 0)
        self.assertEqual(
            result["primaryIssue"],
            "backswingShoulderTurn",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "outside_target",
        )

    def test_build_rotation_metrics_handles_missing_landmarks(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"] = (
            self.build_reference(
                frame_index=20,
                timestamp_seconds=2.0,
                shoulder_depth=None,
                hip_depth=None,
            )
        )

        result = build_rotation_metrics(references)

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 4,
                "total": 5,
                "ratio": 0.8,
            },
        )
        self.assertEqual(result["confidence"], 0.8)

    def test_build_rotation_metrics_reduces_confidence_without_pose(
        self,
    ) -> None:
        references = self.build_references()

        references["finishReference"][
            "poseDetected"
        ] = False

        result = build_rotation_metrics(references)

        self.assertEqual(
            result["confidence"],
            0.75,
        )

    def test_build_rotation_metrics_validates_references(
        self,
    ) -> None:
        references = self.build_references()

        del references["impactReference"]

        with self.assertRaisesRegex(
            ValueError,
            "impactReference is missing",
        ):
            build_rotation_metrics(references)


if __name__ == "__main__":
    unittest.main()