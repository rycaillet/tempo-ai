from __future__ import annotations

import unittest

from app.metrics.impact_position import (
    build_impact_position_metrics,
)


class ImpactPositionMetricsTests(
    unittest.TestCase
):
    @staticmethod
    def build_references(
        *,
        address_pose_detected: bool = True,
        impact_pose_detected: bool = True,
    ) -> dict[str, dict[str, object]]:
        return {
            "addressReference": {
                "frameIndex": 65,
                "timestampSeconds": 2.60,
                "poseDetected": (
                    address_pose_detected
                ),
                "geometry": {
                    "headCenter": {
                        "x": 0.50,
                        "y": 0.20,
                    },
                    "shoulderCenter": {
                        "x": 0.50,
                        "y": 0.38,
                    },
                    "hipCenter": {
                        "x": 0.50,
                        "y": 0.58,
                    },
                    "spineAngle": 42.0,
                    "shoulderTilt": 5.0,
                    "hipTilt": 2.0,
                    "leftElbowAngle": 165.0,
                    "rightElbowAngle": 150.0,
                },
            },
            "impactReference": {
                "frameIndex": 107,
                "timestampSeconds": 4.28,
                "poseDetected": (
                    impact_pose_detected
                ),
                "geometry": {
                    "headCenter": {
                        "x": 0.52,
                        "y": 0.21,
                    },
                    "shoulderCenter": {
                        "x": 0.54,
                        "y": 0.39,
                    },
                    "hipCenter": {
                        "x": 0.53,
                        "y": 0.57,
                    },
                    "spineAngle": 45.5,
                    "shoulderTilt": 14.0,
                    "hipTilt": 7.0,
                    "leftElbowAngle": 142.0,
                    "rightElbowAngle": 121.0,
                },
            },
        }

    def test_extracts_complete_impact_measurements(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        measurements = result["measurements"]

        self.assertEqual(
            measurements[
                "spineAngleAtAddressDegrees"
            ],
            42.0,
        )
        self.assertEqual(
            measurements[
                "spineAngleAtImpactDegrees"
            ],
            45.5,
        )
        self.assertEqual(
            measurements[
                "spineAngleChangeDegrees"
            ],
            3.5,
        )
        self.assertEqual(
            measurements[
                "shoulderTiltAtImpactDegrees"
            ],
            14.0,
        )
        self.assertEqual(
            measurements[
                "hipTiltAtImpactDegrees"
            ],
            7.0,
        )
        self.assertEqual(
            measurements[
                "leadArmAngleAtImpactDegrees"
            ],
            142.0,
        )
        self.assertEqual(
            measurements[
                "trailArmAngleAtImpactDegrees"
            ],
            121.0,
        )

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 9,
                "total": 9,
                "ratio": 1.0,
            },
        )
        self.assertEqual(
            result["confidence"],
            1.0,
        )

    def test_records_reference_metadata(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["referenceFrames"]["start"],
            {
                "name": "addressReference",
                "frameIndex": 65,
                "timestampSeconds": 2.60,
                "poseDetected": True,
            },
        )
        self.assertEqual(
            result["referenceFrames"]["end"],
            {
                "name": "impactReference",
                "frameIndex": 107,
                "timestampSeconds": 4.28,
                "poseDetected": True,
            },
        )

    def test_calculates_center_movements(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        measurements = result["measurements"]

        head_movement = measurements[
            "headMovementFromAddress"
        ]
        shoulder_movement = measurements[
            "shoulderMovementFromAddress"
        ]
        hip_movement = measurements[
            "hipMovementFromAddress"
        ]

        self.assertEqual(
            head_movement[
                "deltaXNormalized"
            ],
            0.02,
        )
        self.assertEqual(
            head_movement[
                "deltaYNormalized"
            ],
            0.01,
        )
        self.assertEqual(
            head_movement["deltaXPixels"],
            38.4,
        )
        self.assertEqual(
            head_movement["deltaYPixels"],
            10.8,
        )

        self.assertEqual(
            shoulder_movement[
                "deltaXNormalized"
            ],
            0.04,
        )
        self.assertEqual(
            hip_movement[
                "deltaXNormalized"
            ],
            0.03,
        )
        self.assertEqual(
            hip_movement[
                "deltaYNormalized"
            ],
            -0.01,
        )

    def test_left_handed_mapping_is_supported(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
            handedness="left",
        )

        measurements = result["measurements"]

        self.assertEqual(
            result["armMapping"],
            {
                "leadArm": "rightElbowAngle",
                "trailArm": "leftElbowAngle",
            },
        )
        self.assertEqual(
            measurements[
                "leadArmAngleAtImpactDegrees"
            ],
            121.0,
        )
        self.assertEqual(
            measurements[
                "trailArmAngleAtImpactDegrees"
            ],
            142.0,
        )

    def test_missing_measurements_reduce_completeness(
        self,
    ) -> None:
        references = self.build_references()

        impact_geometry = references[
            "impactReference"
        ]["geometry"]

        del impact_geometry["spineAngle"]
        del impact_geometry["headCenter"]
        del impact_geometry["leftElbowAngle"]

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 5,
                "total": 9,
                "ratio": 0.555556,
            },
        )
        self.assertEqual(
            result["confidence"],
            0.555556,
        )

    def test_missing_pose_reduces_confidence(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(
                impact_pose_detected=False
            ),
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["measurementCompleteness"][
                "ratio"
            ],
            1.0,
        )
        self.assertEqual(
            result["confidence"],
            0.75,
        )

    def test_missing_address_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["addressReference"]

        with self.assertRaisesRegex(
            ValueError,
            "addressReference is missing",
        ):
            build_impact_position_metrics(
                references=references,
                frame_width=1920,
                frame_height=1080,
                handedness="right",
            )

    def test_missing_impact_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["impactReference"]

        with self.assertRaisesRegex(
            ValueError,
            "impactReference is missing",
        ):
            build_impact_position_metrics(
                references=references,
                frame_width=1920,
                frame_height=1080,
                handedness="right",
            )

    def test_invalid_frame_dimensions_raise_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Frame width must be greater than zero",
        ):
            build_impact_position_metrics(
                references=self.build_references(),
                frame_width=0,
                frame_height=1080,
                handedness="right",
            )

        with self.assertRaisesRegex(
            ValueError,
            "Frame height must be greater than zero",
        ):
            build_impact_position_metrics(
                references=self.build_references(),
                frame_width=1920,
                frame_height=0,
                handedness="right",
            )

    def test_collapsed_lead_arm_needs_attention(
        self,
    ) -> None:
        result = build_impact_position_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["leadArm"]["status"],
            "collapsed",
        )
        self.assertEqual(
            result["classification"],
            "needs_attention",
        )
        self.assertEqual(
            result["issueCount"],
            1,
        )
        self.assertEqual(
            result["primaryIssue"],
            "leadArm",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "outside_target",
        )
        self.assertIsNotNone(
            result["feedback"]["message"]
        )

    def test_neutral_impact_position_is_within_target(
        self,
    ) -> None:
        references = self.build_references()

        references[
            "impactReference"
        ]["geometry"]["leftElbowAngle"] = 165.0

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["spineAngle"][
                "status"
            ],
            "maintained",
        )
        self.assertEqual(
            result["findings"]["headMovement"][
                "status"
            ],
            "stable",
        )
        self.assertEqual(
            result["findings"]["shoulderMovement"][
                "status"
            ],
            "stable",
        )
        self.assertEqual(
            result["findings"]["hipMovement"][
                "status"
            ],
            "stable",
        )
        self.assertEqual(
            result["findings"]["leadArm"][
                "status"
            ],
            "extended",
        )
        self.assertEqual(
            result["findings"]["trailArm"][
                "status"
            ],
            "within_target",
        )
        self.assertEqual(
            result["classification"],
            "neutral",
        )
        self.assertEqual(
            result["issueCount"],
            0,
        )
        self.assertIsNone(
            result["primaryIssue"]
        )
        self.assertEqual(
            result["feedback"]["status"],
            "within_target",
        )

    def test_excessive_spine_angle_loss_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        impact_geometry = references[
            "impactReference"
        ]["geometry"]

        impact_geometry["spineAngle"] = 15.0
        impact_geometry["leftElbowAngle"] = 165.0

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["spineAngle"][
                "status"
            ],
            "excessive_loss",
        )
        self.assertEqual(
            result["classification"],
            "needs_attention",
        )
        self.assertEqual(
            result["primaryIssue"],
            "spineAngle",
        )

    def test_excessive_center_movements_are_identified(
        self,
    ) -> None:
        references = self.build_references()

        impact_geometry = references[
            "impactReference"
        ]["geometry"]

        impact_geometry["headCenter"] = {
            "x": 0.80,
            "y": 0.20,
        }
        impact_geometry["shoulderCenter"] = {
            "x": 0.80,
            "y": 0.38,
        }
        impact_geometry["hipCenter"] = {
            "x": 0.80,
            "y": 0.58,
        }
        impact_geometry["leftElbowAngle"] = 165.0

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["headMovement"][
                "status"
            ],
            "excessive",
        )
        self.assertEqual(
            result["findings"]["shoulderMovement"][
                "status"
            ],
            "excessive",
        )
        self.assertEqual(
            result["findings"]["hipMovement"][
                "status"
            ],
            "excessive",
        )
        self.assertEqual(
            result["classification"],
            "needs_attention",
        )
        self.assertEqual(
            result["issueCount"],
            3,
        )
        self.assertEqual(
            result["primaryIssue"],
            "headMovement",
        )

    def test_trail_arm_issues_are_identified(
        self,
    ) -> None:
        references = self.build_references()

        impact_geometry = references[
            "impactReference"
        ]["geometry"]

        impact_geometry["leftElbowAngle"] = 165.0
        impact_geometry["rightElbowAngle"] = 95.0

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["trailArm"][
                "status"
            ],
            "excessively_bent",
        )
        self.assertEqual(
            result["classification"],
            "needs_attention",
        )
        self.assertEqual(
            result["primaryIssue"],
            "trailArm",
        )

        impact_geometry["rightElbowAngle"] = 175.0

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["trailArm"][
                "status"
            ],
            "overextended",
        )
        self.assertEqual(
            result["classification"],
            "needs_attention",
        )

    def test_missing_findings_produce_incomplete_result(
        self,
    ) -> None:
        references = self.build_references()

        impact_geometry = references[
            "impactReference"
        ]["geometry"]

        del impact_geometry["spineAngle"]
        del impact_geometry["headCenter"]
        del impact_geometry["leftElbowAngle"]

        result = build_impact_position_metrics(
            references=references,
            frame_width=1920,
            frame_height=1080,
            handedness="right",
        )

        self.assertEqual(
            result["findings"]["spineAngle"][
                "status"
            ],
            "not_available",
        )
        self.assertEqual(
            result["findings"]["headMovement"][
                "status"
            ],
            "not_available",
        )
        self.assertEqual(
            result["findings"]["leadArm"][
                "status"
            ],
            "not_available",
        )
        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(
            result["issueCount"],
            0,
        )
        self.assertIsNone(
            result["primaryIssue"]
        )
        self.assertEqual(
            result["feedback"]["status"],
            "insufficient_data",
        )


if __name__ == "__main__":
    unittest.main()