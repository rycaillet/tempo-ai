from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.golf_metrics import analyze_golf_metrics


class GolfMetricsIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.phase_frames = {
            "address": (65, 2.60),
            "takeaway": (67, 2.68),
            "topOfBackswing": (93, 3.72),
            "downswingStart": (102, 4.08),
            "impactReference": (107, 4.28),
            "finishReference": (117, 4.68),
        }

    @staticmethod
    def build_geometry(
        frame_index: int,
    ) -> dict[str, object]:
        progress = (frame_index - 65) / 52

        rotation_depths = {
            65: {
                "shoulder": 0.02,
                "hip": 0.01,
            },
            67: {
                "shoulder": 0.10,
                "hip": 0.04,
            },
            93: {
                "shoulder": 0.28,
                "hip": 0.12,
            },
            102: {
                "shoulder": 0.20,
                "hip": 0.10,
            },
            107: {
                "shoulder": 0.06,
                "hip": 0.04,
            },
            117: {
                "shoulder": -0.20,
                "hip": -0.10,
            },
        }

        depth = rotation_depths[frame_index]
        shoulder_depth = depth["shoulder"]
        hip_depth = depth["hip"]

        return {
            "headCenter": {
                "x": 0.50 + (0.01 * progress),
                "y": 0.20,
            },
            "shoulderCenter": {
                "x": 0.50 + (0.02 * progress),
                "y": 0.38,
            },
            "hipCenter": {
                "x": 0.50 + (0.015 * progress),
                "y": 0.58,
            },
            "leftShoulder": {
                "x": 0.42 + (0.02 * progress),
                "y": 0.38,
                "z": -(shoulder_depth / 2.0),
                "visibility": 0.99,
            },
            "rightShoulder": {
                "x": 0.58 + (0.02 * progress),
                "y": 0.38,
                "z": shoulder_depth / 2.0,
                "visibility": 0.99,
            },
            "leftHip": {
                "x": 0.45 + (0.015 * progress),
                "y": 0.58,
                "z": -(hip_depth / 2.0),
                "visibility": 0.99,
            },
            "rightHip": {
                "x": 0.55 + (0.015 * progress),
                "y": 0.58,
                "z": hip_depth / 2.0,
                "visibility": 0.99,
            },
            "spineAngle": 42.0 + (4.0 * progress),
            "shoulderTilt": 5.0 + (12.0 * progress),
            "hipTilt": 2.0 + (6.0 * progress),
            "leftElbowAngle": (
                165.0 - (28.0 * progress)
            ),
            "rightElbowAngle": (
                150.0 - (35.0 * progress)
            ),
        }

    def build_geometry_payload(
        self,
    ) -> dict[str, object]:
        frames = []

        for frame_index, timestamp in (
            self.phase_frames.values()
        ):
            frames.append(
                {
                    "frameIndex": frame_index,
                    "timestampSeconds": timestamp,
                    "poseDetected": True,
                    "geometry": self.build_geometry(
                        frame_index
                    ),
                }
            )

        return {
            "sourceVideo": (
                "fixtures/integration-swing.mp4"
            ),
            "metadata": {
                "width": 1920,
                "height": 1080,
            },
            "orientation": {
                "selectedRotation": "none",
            },
            "frames": frames,
        }

    def build_refined_phases_payload(
        self,
    ) -> dict[str, object]:
        return {
            "phases": {
                phase_name: {
                    "frameIndex": frame_index,
                    "timestampSeconds": timestamp,
                }
                for phase_name, (
                    frame_index,
                    timestamp,
                ) in self.phase_frames.items()
            }
        }

    def test_analyze_golf_metrics_writes_complete_valid_result(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as (
            temporary_directory
        ):
            temp_path = Path(temporary_directory)

            geometry_path = temp_path / (
                "integration-swing-geometry-analysis.json"
            )
            refined_phases_path = temp_path / (
                "integration-swing-refined-phases.json"
            )
            output_path = temp_path / (
                "integration-swing-golf-metrics.json"
            )

            geometry_path.write_text(
                json.dumps(
                    self.build_geometry_payload()
                ),
                encoding="utf-8",
            )

            refined_phases_path.write_text(
                json.dumps(
                    self.build_refined_phases_payload()
                ),
                encoding="utf-8",
            )

            command_result = analyze_golf_metrics(
                geometry_path=geometry_path,
                refined_phases_path=(
                    refined_phases_path
                ),
                output_path=output_path,
                handedness="right",
            )

            self.assertTrue(command_result["success"])
            self.assertEqual(
                command_result["golfMetricsPath"],
                str(output_path.resolve()),
            )
            self.assertTrue(output_path.exists())

            result = json.loads(
                output_path.read_text(
                    encoding="utf-8"
                )
            )

            summary = result["summary"]
            metrics = result["metrics"]
            scoring = result["scoring"]
            findings_report = result["findings"]
            recommendations = result["recommendations"]
            validation = metrics["phaseValidation"]
            eligibility = metrics[
                "feedbackEligibility"
            ]
            tempo = metrics["tempo"]
            tempo_feedback = tempo["feedback"]
            address_posture = metrics[
                "addressPosture"
            ]
            posture_feedback = address_posture[
                "feedback"
            ]
            head_stability = metrics[
                "headStability"
            ]
            head_stability_feedback = head_stability[
                "feedback"
            ]
            weight_shift = metrics["weightShift"]
            weight_shift_feedback = weight_shift[
                "feedback"
            ]
            rotation = metrics["rotation"]
            rotation_feedback = rotation["feedback"]
            swing_plane = metrics["swingPlane"]
            swing_plane_feedback = swing_plane[
                "feedback"
            ]

            self.assertEqual(
                summary["referenceFrameCount"],
                6,
            )
            self.assertEqual(
                summary[
                    "availableReferenceMeasurements"
                ],
                48,
            )
            self.assertEqual(
                summary["totalReferenceMeasurements"],
                48,
            )
            self.assertEqual(
                summary[
                    "referenceMeasurementCompleteness"
                ],
                1.0,
            )
            self.assertTrue(
                summary["allReferenceFramesHavePose"]
            )
            self.assertEqual(
                summary["handednessAssumption"],
                "right",
            )

            self.assertEqual(
                summary["phaseValidationStatus"],
                "valid",
            )
            self.assertEqual(
                summary["phaseValidationConfidence"],
                1.0,
            )
            self.assertEqual(
                summary["feedbackEligibilityStatus"],
                "eligible",
            )
            self.assertTrue(
                summary["coachingFeedbackEligible"]
            )

            self.assertEqual(
                validation["status"],
                "valid",
            )
            self.assertEqual(
                validation["confidence"],
                1.0,
            )
            self.assertEqual(
                validation["passedCheckCount"],
                9,
            )
            self.assertEqual(
                validation["failedChecks"],
                [],
            )

            self.assertTrue(
                eligibility["eligible"]
            )
            self.assertEqual(
                eligibility["mode"],
                "normal",
            )
            self.assertFalse(
                eligibility["requiresDisclaimer"]
            )

            self.assertEqual(
                tempo["backswingDurationSeconds"],
                1.12,
            )
            self.assertEqual(
                tempo["downswingDurationSeconds"],
                0.56,
            )
            self.assertEqual(
                tempo["backswingToDownswingRatio"],
                2.0,
            )
            self.assertEqual(
                tempo["classification"],
                "quick",
            )

            self.assertEqual(
                tempo_feedback["status"],
                "below_target",
            )
            self.assertEqual(
                tempo_feedback["deliveryStatus"],
                "displayed",
            )
            self.assertIsNone(
                tempo_feedback["disclaimer"]
            )
            self.assertIsNotNone(
                tempo_feedback["message"]
            )

            self.assertEqual(
                address_posture["classification"],
                "neutral",
            )
            self.assertEqual(
                address_posture["issueCount"],
                0,
            )
            self.assertIsNone(
                address_posture["primaryIssue"]
            )
            self.assertEqual(
                address_posture["confidence"],
                1.0,
            )

            self.assertEqual(
                address_posture[
                    "measurementCompleteness"
                ],
                {
                    "available": 5,
                    "total": 5,
                    "ratio": 1.0,
                },
            )

            measurements = address_posture[
                "measurements"
            ]

            self.assertEqual(
                measurements[
                    "spineAngleDegrees"
                ],
                42.0,
            )
            self.assertEqual(
                measurements[
                    "shoulderTiltDegrees"
                ],
                5.0,
            )
            self.assertEqual(
                measurements[
                    "hipTiltDegrees"
                ],
                2.0,
            )

            self.assertEqual(
                measurements[
                    "headToHipOffset"
                ]["deltaXNormalized"],
                0.0,
            )
            self.assertEqual(
                measurements[
                    "shoulderToHipOffset"
                ]["deltaXNormalized"],
                0.0,
            )

            findings = address_posture["findings"]

            self.assertEqual(
                findings["spineAngle"]["status"],
                "within_target",
            )
            self.assertEqual(
                findings["shoulderTilt"]["status"],
                "within_target",
            )
            self.assertEqual(
                findings["hipTilt"]["status"],
                "within_target",
            )
            self.assertIn(
                findings["headPosition"]["status"],
                {
                    "within_target",
                    "centered",
                },
            )
            self.assertIn(
                findings[
                    "shoulderPosition"
                ]["status"],
                {
                    "within_target",
                    "centered",
                },
            )

            self.assertEqual(
                posture_feedback["status"],
                "within_target",
            )
            self.assertEqual(
                posture_feedback[
                    "deliveryStatus"
                ],
                "displayed",
            )
            self.assertIsNone(
                posture_feedback["disclaimer"]
            )
            self.assertIsNotNone(
                posture_feedback["message"]
            )
            self.assertEqual(
                posture_feedback[
                    "eligibilityReason"
                ],
                eligibility["reason"],
            )

            self.assertEqual(
                summary[
                    "addressPostureClassification"
                ],
                "neutral",
            )
            self.assertEqual(
                summary[
                    "addressPostureConfidence"
                ],
                1.0,
            )
            self.assertEqual(
                summary["addressPostureIssueCount"],
                0,
            )
            self.assertIsNone(
                summary[
                    "addressPosturePrimaryIssue"
                ]
            )
            self.assertEqual(
                summary[
                    "addressPostureFeedbackStatus"
                ],
                "within_target",
            )
            self.assertEqual(
                summary[
                    "addressPostureFeedbackDeliveryStatus"
                ],
                "displayed",
            )

            self.assertIsInstance(
                head_stability,
                dict,
            )
            self.assertIn(
                "classification",
                head_stability,
            )
            self.assertIn(
                "confidence",
                head_stability,
            )
            self.assertIn(
                "measurementCompleteness",
                head_stability,
            )
            self.assertIn(
                "issueCount",
                head_stability,
            )
            self.assertIn(
                "primaryIssue",
                head_stability,
            )
            self.assertIn(
                "measurements",
                head_stability,
            )
            self.assertIn(
                "findings",
                head_stability,
            )
            self.assertIn(
                "feedback",
                head_stability,
            )

            self.assertEqual(
                head_stability_feedback[
                    "deliveryStatus"
                ],
                "displayed",
            )
            self.assertIsNone(
                head_stability_feedback["disclaimer"]
            )
            self.assertIsNotNone(
                head_stability_feedback["message"]
            )
            self.assertEqual(
                head_stability_feedback[
                    "eligibilityReason"
                ],
                eligibility["reason"],
            )

            self.assertEqual(
                summary[
                    "headStabilityClassification"
                ],
                head_stability["classification"],
            )
            self.assertEqual(
                summary["headStabilityConfidence"],
                head_stability["confidence"],
            )
            self.assertEqual(
                summary[
                    "headStabilityMeasurementCompleteness"
                ],
                head_stability[
                    "measurementCompleteness"
                ]["ratio"],
            )
            self.assertEqual(
                summary["headStabilityIssueCount"],
                head_stability["issueCount"],
            )
            self.assertEqual(
                summary[
                    "headStabilityPrimaryIssue"
                ],
                head_stability["primaryIssue"],
            )
            self.assertEqual(
                summary[
                    "headStabilityFeedbackStatus"
                ],
                head_stability_feedback["status"],
            )
            self.assertEqual(
                summary[
                    "headStabilityFeedbackDeliveryStatus"
                ],
                head_stability_feedback[
                    "deliveryStatus"
                ],
            )

            self.assertIsInstance(
                weight_shift,
                dict,
            )
            self.assertIn(
                "classification",
                weight_shift,
            )
            self.assertIn(
                "confidence",
                weight_shift,
            )
            self.assertIn(
                "measurementCompleteness",
                weight_shift,
            )
            self.assertIn(
                "issueCount",
                weight_shift,
            )
            self.assertIn(
                "primaryIssue",
                weight_shift,
            )
            self.assertIn(
                "referenceFrames",
                weight_shift,
            )
            self.assertIn(
                "measurements",
                weight_shift,
            )
            self.assertIn(
                "findings",
                weight_shift,
            )
            self.assertIn(
                "feedback",
                weight_shift,
            )

            self.assertEqual(
                weight_shift[
                    "measurementCompleteness"
                ],
                {
                    "available": 5,
                    "total": 5,
                    "ratio": 1.0,
                },
            )
            self.assertEqual(
                weight_shift["confidence"],
                1.0,
            )

            self.assertIn(
                weight_shift["classification"],
                {
                    "neutral",
                    "needs_attention",
                },
            )
            self.assertGreaterEqual(
                weight_shift["issueCount"],
                0,
            )

            weight_shift_measurements = weight_shift[
                "measurements"
            ]

            self.assertIn(
                "addressToTop",
                weight_shift_measurements,
            )
            self.assertIn(
                "topToDownswingStart",
                weight_shift_measurements,
            )
            self.assertIn(
                "topToImpact",
                weight_shift_measurements,
            )
            self.assertIn(
                "addressToImpact",
                weight_shift_measurements,
            )
            self.assertIn(
                "impactToFinish",
                weight_shift_measurements,
            )

            self.assertEqual(
                weight_shift_feedback[
                    "deliveryStatus"
                ],
                "displayed",
            )
            self.assertIsNone(
                weight_shift_feedback["disclaimer"]
            )
            self.assertIsNotNone(
                weight_shift_feedback["message"]
            )
            self.assertEqual(
                weight_shift_feedback[
                    "eligibilityReason"
                ],
                eligibility["reason"],
            )

            self.assertEqual(
                summary[
                    "weightShiftClassification"
                ],
                weight_shift["classification"],
            )
            self.assertEqual(
                summary["weightShiftConfidence"],
                weight_shift["confidence"],
            )
            self.assertEqual(
                summary[
                    "weightShiftMeasurementCompleteness"
                ],
                weight_shift[
                    "measurementCompleteness"
                ]["ratio"],
            )
            self.assertEqual(
                summary["weightShiftIssueCount"],
                weight_shift["issueCount"],
            )
            self.assertEqual(
                summary["weightShiftPrimaryIssue"],
                weight_shift["primaryIssue"],
            )
            self.assertEqual(
                summary["weightShiftFeedbackStatus"],
                weight_shift_feedback["status"],
            )
            self.assertEqual(
                summary[
                    "weightShiftFeedbackDeliveryStatus"
                ],
                weight_shift_feedback[
                    "deliveryStatus"
                ],
            )

            self.assertIsInstance(
                rotation,
                dict,
            )
            self.assertIn(
                "classification",
                rotation,
            )
            self.assertIn(
                "confidence",
                rotation,
            )
            self.assertIn(
                "measurementCompleteness",
                rotation,
            )
            self.assertIn(
                "issueCount",
                rotation,
            )
            self.assertIn(
                "primaryIssue",
                rotation,
            )
            self.assertIn(
                "referenceFrames",
                rotation,
            )
            self.assertIn(
                "measurements",
                rotation,
            )
            self.assertIn(
                "findings",
                rotation,
            )
            self.assertIn(
                "feedback",
                rotation,
            )

            self.assertEqual(
                rotation[
                    "measurementCompleteness"
                ]["ratio"],
                1.0,
            )
            self.assertGreater(
                rotation["confidence"],
                0.0,
            )
            self.assertLessEqual(
                rotation["confidence"],
                1.0,
            )
            self.assertIn(
                rotation["classification"],
                {
                    "neutral",
                    "needs_attention",
                    "incomplete",
                },
            )
            self.assertGreaterEqual(
                rotation["issueCount"],
                0,
            )

            rotation_measurements = rotation[
                "measurements"
            ]

            self.assertIn(
                "states",
                rotation_measurements,
            )
            self.assertIn(
                "changesFromAddress",
                rotation_measurements,
            )
            self.assertIn(
                "impactShoulderReturnRatio",
                rotation_measurements,
            )

            rotation_states = rotation_measurements[
                "states"
            ]
            rotation_changes = rotation_measurements[
                "changesFromAddress"
            ]

            self.assertEqual(
                set(rotation_states),
                {
                    "address",
                    "topOfBackswing",
                    "downswingStart",
                    "impact",
                    "finish",
                },
            )
            self.assertEqual(
                set(rotation_changes),
                {
                    "topOfBackswing",
                    "downswingStart",
                    "impact",
                    "finish",
                },
            )

            for state_name in (
                "address",
                "topOfBackswing",
                "downswingStart",
                "impact",
                "finish",
            ):
                state = rotation_states[state_name]

                self.assertIn(
                    "shoulders",
                    state,
                )
                self.assertIn(
                    "hips",
                    state,
                )
                self.assertIn(
                    "shoulderHipSeparationProxy",
                    state,
                )

                self.assertIn(
                    "depthSeparationNormalized",
                    state["shoulders"],
                )
                self.assertIn(
                    "depthSeparationNormalized",
                    state["hips"],
                )

            for change_name in (
                "topOfBackswing",
                "downswingStart",
                "impact",
                "finish",
            ):
                change = rotation_changes[change_name]

                self.assertIn(
                    "shoulderDepthChangeNormalized",
                    change,
                )
                self.assertIn(
                    "hipDepthChangeNormalized",
                    change,
                )
                self.assertIn(
                    "shoulderHipRotationSeparationProxy",
                    change,
                )

            self.assertAlmostEqual(
                rotation_measurements[
                    "impactShoulderReturnRatio"
                ],
                0.846154,
            )

            self.assertEqual(
                rotation_feedback["deliveryStatus"],
                "displayed",
            )
            self.assertIsNone(
                rotation_feedback["disclaimer"]
            )
            self.assertIsNotNone(
                rotation_feedback["message"]
            )
            self.assertEqual(
                rotation_feedback["eligibilityReason"],
                eligibility["reason"],
            )

            self.assertEqual(
                summary["rotationClassification"],
                rotation["classification"],
            )
            self.assertEqual(
                summary["rotationConfidence"],
                rotation["confidence"],
            )
            self.assertEqual(
                summary[
                    "rotationMeasurementCompleteness"
                ],
                rotation[
                    "measurementCompleteness"
                ]["ratio"],
            )
            self.assertEqual(
                summary["rotationIssueCount"],
                rotation["issueCount"],
            )
            self.assertEqual(
                summary["rotationPrimaryIssue"],
                rotation["primaryIssue"],
            )
            self.assertEqual(
                summary["rotationFeedbackStatus"],
                rotation_feedback["status"],
            )
            self.assertEqual(
                summary[
                    "rotationFeedbackDeliveryStatus"
                ],
                rotation_feedback[
                    "deliveryStatus"
                ],
            )

            self.assertEqual(
                swing_plane["classification"],
                "incomplete",
            )
            self.assertEqual(
                swing_plane["measurementCompleteness"],
                {
                    "available": 0,
                    "total": 6,
                    "ratio": 0.0,
                },
            )
            self.assertEqual(
                swing_plane["confidence"],
                0.0,
            )
            self.assertEqual(
                swing_plane_feedback["status"],
                "insufficient_data",
            )
            self.assertEqual(
                swing_plane_feedback[
                    "deliveryStatus"
                ],
                "displayed",
            )
            self.assertEqual(
                summary["swingPlaneClassification"],
                "incomplete",
            )
            self.assertEqual(
                summary["swingPlaneConfidence"],
                0.0,
            )
            self.assertEqual(
                summary[
                    "swingPlaneMeasurementCompleteness"
                ],
                0.0,
            )
            self.assertEqual(
                summary["swingPlaneFeedbackStatus"],
                "insufficient_data",
            )
            self.assertEqual(
                summary[
                    "swingPlaneFeedbackDeliveryStatus"
                ],
                "displayed",
            )

            self.assertEqual(
                result["phaseFrames"][
                    "addressReference"
                ]["frameIndex"],
                65,
            )
            self.assertEqual(
                result["phaseFrames"][
                    "finishReference"
                ]["frameIndex"],
                117,
            )

            self.assertIn(
                "transitions",
                metrics,
            )
            self.assertIn(
                "maximumMovementFromAddressReference",
                metrics,
            )
            self.assertIn(
                "angleRanges",
                metrics,
            )
            self.assertIn(
                "armExtension",
                metrics,
            )
            self.assertIn(
                "addressPosture",
                metrics,
            )
            self.assertIn(
                "headStability",
                metrics,
            )
            self.assertIn(
                "weightShift",
                metrics,
            )
            self.assertIsInstance(scoring, dict)
            self.assertIsInstance(findings_report, dict)
            self.assertIsInstance(recommendations, dict)

            self.assertEqual(
                scoring["interpretation"]["status"],
                findings_report["status"],
            )

            self.assertEqual(
                findings_report["status"],
                recommendations["status"],
            )

            improvement_priorities = findings_report[
                "improvementPriorities"
            ]
            generated_recommendations = recommendations[
                "recommendations"
            ]

            self.assertEqual(
                len(generated_recommendations),
                len(improvement_priorities),
            )

            expected_metric_keys = [
                priority["metricKey"]
                for priority in improvement_priorities
            ]

            recommendation_metric_keys = [
                recommendation["metricKey"]
                for recommendation in generated_recommendations
            ]

            self.assertEqual(
                recommendation_metric_keys,
                expected_metric_keys,
            )

            expected_priorities = list(
                range(
                    1,
                    len(generated_recommendations) + 1,
                )
            )

            actual_priorities = [
                recommendation["priority"]
                for recommendation in generated_recommendations
            ]

            self.assertEqual(
                actual_priorities,
                expected_priorities,
            )

            if improvement_priorities:
                primary_focus = recommendations[
                    "primaryFocus"
                ]

                self.assertIsNotNone(primary_focus)
                self.assertEqual(
                    primary_focus["metricKey"],
                    improvement_priorities[0]["metricKey"],
                )
                self.assertEqual(
                    primary_focus["displayName"],
                    improvement_priorities[0]["displayName"],
                )
                self.assertEqual(
                    primary_focus["severity"],
                    improvement_priorities[0]["severity"],
                )
            else:
                self.assertIsNone(
                    recommendations["primaryFocus"]
                )

            self.assertEqual(
                command_result["summary"],
                summary,
            )


if __name__ == "__main__":
    unittest.main()