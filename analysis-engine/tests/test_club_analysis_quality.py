from __future__ import annotations

import unittest

from app.club_analysis_quality import (
    build_club_analysis_quality_summary,
)


class ClubAnalysisQualitySummaryTests(
    unittest.TestCase
):
    def test_returns_complete_summary(
        self,
    ) -> None:
        club_detection = {
            "summary": {
                "requestedFrames": 30,
                "processedFrames": 30,
                "detectedFrames": 25,
                "imageDetectedFrames": 24,
                "trackedFrames": 1,
                "smoothedFrames": 9,
                "detectionRate": 0.833,
                "averageConfidence": 0.736,
            },
            "frames": [{}],
        }

        phase_measurements = {
            phase_name: {
                "available": True,
                "confidence": confidence,
            }
            for phase_name, confidence in (
                ("address", 0.868),
                ("takeaway", 0.887),
                ("topOfBackswing", 0.690),
                ("downswingStart", 0.485),
                ("impact", 0.522),
                ("finish", 0.806),
            )
        }

        swing_plane = {
            "measurementCompleteness": {
                "available": 6,
                "total": 6,
                "ratio": 1.0,
            },
            "measurements": {
                "phaseMeasurements": (
                    phase_measurements
                ),
                "smoothedReferenceCount": 4,
                "trackedReferenceCount": 1,
            },
        }

        result = (
            build_club_analysis_quality_summary(
                club_detection=club_detection,
                swing_plane=swing_plane,
            )
        )

        self.assertEqual(
            result["status"],
            "complete",
        )
        self.assertEqual(
            result["referencePhasesAvailable"],
            6,
        )
        self.assertEqual(
            result["minimumReferenceConfidence"],
            0.485,
        )
        self.assertTrue(
            result["usesTrackedGeometry"]
        )
        self.assertTrue(
            result["usesSmoothedGeometry"]
        )
        self.assertEqual(
            result["unavailableReferencePhases"],
            [],
        )
        self.assertIn(
            "tracked_reference_geometry_used",
            result["warnings"],
        )
        self.assertIn(
            "low_reference_confidence",
            result["warnings"],
        )

    def test_returns_partial_summary(
        self,
    ) -> None:
        result = (
            build_club_analysis_quality_summary(
                club_detection={
                    "summary": {
                        "requestedFrames": 10,
                        "processedFrames": 10,
                        "detectedFrames": 5,
                        "detectionRate": 0.5,
                    },
                    "frames": [{}],
                },
                swing_plane={
                    "measurementCompleteness": {
                        "available": 2,
                        "total": 6,
                    },
                    "measurements": {
                        "phaseMeasurements": {
                            "address": {
                                "available": True,
                                "confidence": 0.8,
                            },
                            "takeaway": {
                                "available": True,
                                "confidence": 0.7,
                            },
                        },
                        "smoothedReferenceCount": 0,
                        "trackedReferenceCount": 0,
                    },
                },
            )
        )

        self.assertEqual(
            result["status"],
            "partial",
        )
        self.assertEqual(
            result["referencePhaseCompleteness"],
            0.333333,
        )
        self.assertEqual(
            result["unavailableReferencePhases"],
            [
                "topOfBackswing",
                "downswingStart",
                "impact",
                "finish",
            ],
        )
        self.assertIn(
            "missing_reference_phase_geometry",
            result["warnings"],
        )
        self.assertIn(
            "limited_frame_detection_rate",
            result["warnings"],
        )

    def test_returns_not_available_without_detector_input(
        self,
    ) -> None:
        result = (
            build_club_analysis_quality_summary(
                club_detection={"frames": []},
                swing_plane={
                    "measurementCompleteness": {
                        "available": 0,
                        "total": 6,
                    },
                    "measurements": {
                        "phaseMeasurements": {},
                        "smoothedReferenceCount": 0,
                        "trackedReferenceCount": 0,
                    },
                },
            )
        )

        self.assertEqual(
            result["status"],
            "not_available",
        )
        self.assertEqual(
            result["detectedFrames"],
            0,
        )
        self.assertEqual(
            result["referencePhasesAvailable"],
            0,
        )
        self.assertFalse(
            result["usesTrackedGeometry"]
        )
        self.assertFalse(
            result["usesSmoothedGeometry"]
        )
        self.assertIn(
            "club_detection_not_provided",
            result["warnings"],
        )


if __name__ == "__main__":
    unittest.main()