from __future__ import annotations

import unittest

from app.analysis.api_contract import (
    ANALYSIS_API_VERSION,
    build_analysis_api_contract,
)


class AnalysisApiContractTests(
    unittest.TestCase
):
    @staticmethod
    def build_report() -> dict[str, object]:
        return {
            "sourceVideo": "fixtures/swing.mp4",
            "metrics": {
                "tempo": {
                    "classification": "balanced",
                    "confidence": 0.9,
                    "measurementCompleteness": {
                        "ratio": 1.0,
                    },
                    "feedback": {
                        "status": "within_target",
                        "deliveryStatus": "displayed",
                    },
                },
                "shaftLean": {
                    "classification": "observed",
                    "confidence": 0.68,
                    "measurements": {
                        "signedLeanFromVerticalDegrees": 12.5,
                        "cameraRelativeDirection": "image_right",
                        "shaftGeometrySource": "smoothed",
                    },
                    "measurementCompleteness": {
                        "ratio": 1.0,
                    },
                    "feedback": {
                        "status": "measurement_only",
                        "deliveryStatus": (
                            "displayed_with_caution"
                        ),
                        "basis": (
                            "Camera-relative shaft measurement."
                        ),
                    },
                },
                "swingPlane": {
                    "classification": "observed",
                    "confidence": 0.71,
                    "measurementCompleteness": {
                        "available": 6,
                        "total": 6,
                        "ratio": 1.0,
                    },
                    "measurements": {
                        "phaseChangesDegrees": {
                            "topToImpactDegrees": 19.3,
                        },
                        "smoothedReferenceCount": 4,
                        "trackedReferenceCount": 1,
                        "averageDetectionConfidence": 0.71,
                        "phaseMeasurements": {
                            "address": {
                                "available": True,
                                "confidence": 0.8,
                            },
                        },
                    },
                    "feedback": {
                        "status": "measurement_only",
                        "deliveryStatus": (
                            "displayed_with_caution"
                        ),
                        "basis": (
                            "Camera-relative 2D trajectory."
                        ),
                    },
                },
            },
            "scoring": {
                "overallScore": 84.0,
                "scoreConfidence": 92.0,
                "scoreCoverage": 100.0,
                "metrics": {
                    "tempo": {
                        "status": "scored",
                        "rawScore": 90.0,
                        "weightedScore": 13.5,
                    },
                    "shaftLean": {
                        "status": "unscored",
                        "reason": "weight_is_zero",
                    },
                    "swingPlane": {
                        "status": "unscored",
                        "reason": "weight_is_zero",
                    },
                },
                "interpretation": {
                    "status": "ready",
                    "rating": "good",
                    "ratingLabel": "Good",
                    "summary": "A solid measured swing.",
                },
            },
            "findings": {
                "status": "ready",
                "overallFinding": (
                    "Address posture is the main priority."
                ),
                "strengths": [
                    {
                        "metricKey": "tempo",
                        "displayName": "Tempo",
                        "score": 90.0,
                        "reason": "Strong timing.",
                    },
                ],
                "improvementPriorities": [
                    {
                        "metricKey": "addressPosture",
                        "displayName": "Address posture",
                        "score": 65.0,
                        "severity": "high",
                        "reason": "Lowest score.",
                    },
                ],
                "warnings": [],
            },
            "recommendations": {
                "status": "ready",
                "primaryFocus": {
                    "metricKey": "addressPosture",
                    "displayName": "Address posture",
                    "severity": "high",
                },
                "recommendations": [
                    {
                        "metricKey": "addressPosture",
                        "displayName": "Address posture",
                        "severity": "high",
                        "priority": 1,
                        "title": "Build a balanced setup",
                        "summary": "Improve setup balance.",
                        "focus": "Posture",
                        "rationale": "Setup influences motion.",
                        "practiceCues": [
                            "Balance over mid-foot.",
                        ],
                        "caution": None,
                    },
                ],
                "warnings": [],
            },
            "summary": {
                "clubAnalysisQuality": {
                    "status": "complete",
                    "referencePhasesAvailable": 6,
                    "referencePhasesTotal": 6,
                },
            },
            "coaching": {
                "status": "ready",
                "headline": "Build a balanced setup",
            },
        }

    def test_builds_versioned_ready_contract(
        self,
    ) -> None:
        result = build_analysis_api_contract(
            report=self.build_report(),
            video_path="/uploads/swing.mp4",
            handedness="right",
            artifacts={
                "golfMetricsPath": (
                    "/output/swing-golf-metrics.json"
                ),
            },
        )

        self.assertEqual(
            result["contractVersion"],
            ANALYSIS_API_VERSION,
        )
        self.assertEqual(
            result["status"],
            "ready",
        )
        self.assertEqual(
            result["source"]["handedness"],
            "right",
        )
        self.assertEqual(
            result["score"]["overallScore"],
            84.0,
        )
        self.assertEqual(
            result["recommendations"][
                "primaryFocus"
            ]["metricKey"],
            "addressPosture",
        )

    def test_builds_compact_metric_cards(
        self,
    ) -> None:
        result = build_analysis_api_contract(
            report=self.build_report(),
            video_path="/uploads/swing.mp4",
            handedness="right",
            artifacts={},
        )

        cards = {
            card["metricKey"]: card
            for card in result["metrics"]
        }

        self.assertEqual(
            cards["tempo"]["score"],
            90.0,
        )
        self.assertEqual(
            cards["shaftLean"]["scoreStatus"],
            "unscored",
        )
        self.assertEqual(
            cards["swingPlane"][
                "feedbackStatus"
            ],
            "measurement_only",
        )

    def test_exposes_club_details_and_quality(
        self,
    ) -> None:
        result = build_analysis_api_contract(
            report=self.build_report(),
            video_path="/uploads/swing.mp4",
            handedness="right",
            artifacts={},
        )

        self.assertEqual(
            result["clubMetrics"]["shaftLean"][
                "geometrySource"
            ],
            "smoothed",
        )
        self.assertEqual(
            result["clubMetrics"]["swingPlane"][
                "phaseChangesDegrees"
            ]["topToImpactDegrees"],
            19.3,
        )
        self.assertEqual(
            result["clubAnalysisQuality"][
                "status"
            ],
            "complete",
        )

    def test_includes_observations_without_raw_geometry(
        self,
    ) -> None:
        result = build_analysis_api_contract(
            report=self.build_report(),
            video_path="/uploads/swing.mp4",
            handedness="right",
            artifacts={},
        )

        observation_keys = [
            item["metricKey"]
            for item in result["observations"]
        ]

        self.assertEqual(
            observation_keys,
            ["shaftLean", "swingPlane"],
        )
        self.assertNotIn(
            "shaftLine",
            str(result),
        )
        self.assertNotIn(
            "landmarks",
            str(result),
        )

    def test_marks_contract_partial_when_layers_not_ready(
        self,
    ) -> None:
        report = self.build_report()
        report["findings"]["status"] = (
            "not_available"
        )

        result = build_analysis_api_contract(
            report=report,
            video_path="/uploads/swing.mp4",
            handedness="right",
            artifacts={},
        )

        self.assertEqual(
            result["status"],
            "partial",
        )


if __name__ == "__main__":
    unittest.main()