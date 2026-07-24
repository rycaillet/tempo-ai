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
    def build_geometry(frame_index: int) -> dict[str, object]:
        progress = (frame_index - 65) / 52

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
            "spineAngle": 42.0 + (4.0 * progress),
            "shoulderTilt": 5.0 + (12.0 * progress),
            "hipTilt": 2.0 + (6.0 * progress),
            "leftElbowAngle": 165.0 - (28.0 * progress),
            "rightElbowAngle": 150.0 - (35.0 * progress),
        }

    def build_geometry_payload(self) -> dict[str, object]:
        frames = []

        for frame_index, timestamp in self.phase_frames.values():
            frames.append(
                {
                    "frameIndex": frame_index,
                    "timestampSeconds": timestamp,
                    "poseDetected": True,
                    "geometry": self.build_geometry(frame_index),
                }
            )

        return {
            "sourceVideo": "fixtures/integration-swing.mp4",
            "metadata": {
                "width": 1920,
                "height": 1080,
            },
            "orientation": {
                "selectedRotation": "none",
            },
            "frames": frames,
        }

    def build_refined_phases_payload(self) -> dict[str, object]:
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
        with tempfile.TemporaryDirectory() as temporary_directory:
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
                json.dumps(self.build_geometry_payload()),
                encoding="utf-8",
            )

            refined_phases_path.write_text(
                json.dumps(self.build_refined_phases_payload()),
                encoding="utf-8",
            )

            command_result = analyze_golf_metrics(
                geometry_path=geometry_path,
                refined_phases_path=refined_phases_path,
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
                output_path.read_text(encoding="utf-8")
            )

            summary = result["summary"]
            metrics = result["metrics"]
            validation = metrics["phaseValidation"]
            eligibility = metrics["feedbackEligibility"]
            tempo = metrics["tempo"]
            feedback = tempo["feedback"]

            self.assertEqual(summary["referenceFrameCount"], 6)
            self.assertEqual(
                summary["availableReferenceMeasurements"],
                48,
            )
            self.assertEqual(
                summary["totalReferenceMeasurements"],
                48,
            )
            self.assertEqual(
                summary["referenceMeasurementCompleteness"],
                1.0,
            )
            self.assertTrue(summary["allReferenceFramesHavePose"])
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

            self.assertEqual(validation["status"], "valid")
            self.assertEqual(validation["confidence"], 1.0)
            self.assertEqual(validation["passedCheckCount"], 9)
            self.assertEqual(validation["failedChecks"], [])

            self.assertTrue(eligibility["eligible"])
            self.assertEqual(eligibility["mode"], "normal")
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
            self.assertEqual(tempo["classification"], "quick")

            self.assertEqual(
                feedback["status"],
                "below_target",
            )
            self.assertEqual(
                feedback["deliveryStatus"],
                "displayed",
            )
            self.assertIsNone(feedback["disclaimer"])
            self.assertIsNotNone(feedback["message"])

            self.assertEqual(
                result["phaseFrames"]["addressReference"][
                    "frameIndex"
                ],
                65,
            )
            self.assertEqual(
                result["phaseFrames"]["finishReference"][
                    "frameIndex"
                ],
                117,
            )

            self.assertIn("transitions", metrics)
            self.assertIn(
                "maximumMovementFromAddressReference",
                metrics,
            )
            self.assertIn("angleRanges", metrics)
            self.assertIn("armExtension", metrics)


if __name__ == "__main__":
    unittest.main()