from __future__ import annotations

import unittest
from typing import Any

from app.analysis import (
    SwingAnalysisReport,
    build_swing_analysis_report,
)


class SwingAnalysisReportTests(unittest.TestCase):
    @staticmethod
    def build_report() -> SwingAnalysisReport:
        return build_swing_analysis_report(
            source_video="swing.mp4",
            inputs={
                "geometryAnalysisPath": "/analysis/geometry.json",
                "refinedPhasesPath": "/analysis/phases.json",
            },
            coordinate_system={
                "space": (
                    "normalized-landmarks-and-rotated-video-pixels"
                ),
                "rotatedFrameWidth": 1920.0,
                "rotatedFrameHeight": 1080.0,
                "positiveXDirection": "image-right",
                "positiveYDirection": "image-down",
                "angleUnits": "degrees",
            },
            assumptions={
                "handedness": "right",
            },
            phase_frames={
                "addressReference": {
                    "frameIndex": 10,
                    "timestampSeconds": 0.333,
                    "poseDetected": True,
                },
            },
            reference_geometry={
                "addressReference": {
                    "headCenter": {
                        "x": 0.5,
                        "y": 0.2,
                    },
                },
            },
            metrics={
                "tempo": {
                    "classification": "balanced",
                    "confidence": 0.9,
                },
            },
            scoring={
                "overallScore": 92.0,
                "scoreConfidence": 90.0,
                "scoreCoverage": 100.0,
                "interpretation": {
                    "rating": "excellent",
                    "status": "ready",
                },
            },
            findings={
                "status": "ready",
                "overallFinding": "Strong measured swing.",
                "strengths": [
                    {
                        "metricKey": "tempo",
                        "displayName": "Tempo",
                        "score": 92.0,
                        "reason": (
                            "Tempo was one of the highest-scoring "
                            "available metrics."
                        ),
                    },
                ],
                "improvementPriorities": [],
                "warnings": [],
            },
            recommendations={
                "status": "ready",
                "primaryFocus": {
                    "metricKey": "rotation",
                    "displayName": "Rotation",
                    "severity": "high",
                },
                "recommendations": [
                    {
                        "metricKey": "rotation",
                        "displayName": "Rotation",
                        "severity": "high",
                        "priority": 1,
                        "title": "Improve rotational sequencing",
                        "summary": (
                            "Coordinate the shoulder and hip turn."
                        ),
                        "focus": (
                            "Body turn and rotational sequence"
                        ),
                        "rationale": (
                            "Coordinated rotation supports balance."
                        ),
                        "practiceCues": [
                            "Create a comfortable shoulder turn.",
                        ],
                        "caution": None,
                    },
                ],
                "warnings": [],
            },
            summary={
                "referenceFrameCount": 6,
                "handednessAssumption": "right",
            },
        )

    def test_builder_returns_swing_analysis_report(self) -> None:
        report = self.build_report()

        self.assertIsInstance(report, SwingAnalysisReport)

    def test_to_dict_preserves_public_output_shape(self) -> None:
        report = self.build_report()

        result = report.to_dict()

        self.assertEqual(
            tuple(result.keys()),
            (
                "sourceVideo",
                "inputs",
                "coordinateSystem",
                "assumptions",
                "phaseFrames",
                "referenceGeometry",
                "metrics",
                "scoring",
                "findings",
                "recommendations",
                "summary",
            ),
        )

    def test_to_dict_serializes_all_report_sections(self) -> None:
        report = self.build_report()

        result = report.to_dict()

        self.assertEqual(result["sourceVideo"], "swing.mp4")
        self.assertEqual(
            result["inputs"]["geometryAnalysisPath"],
            "/analysis/geometry.json",
        )
        self.assertEqual(
            result["coordinateSystem"]["angleUnits"],
            "degrees",
        )
        self.assertEqual(
            result["assumptions"]["handedness"],
            "right",
        )
        self.assertEqual(
            result["phaseFrames"]["addressReference"][
                "frameIndex"
            ],
            10,
        )
        self.assertEqual(
            result["referenceGeometry"]["addressReference"][
                "headCenter"
            ]["x"],
            0.5,
        )
        self.assertEqual(
            result["metrics"]["tempo"]["classification"],
            "balanced",
        )
        self.assertEqual(
            result["scoring"]["overallScore"],
            92.0,
        )
        self.assertEqual(
            result["findings"]["status"],
            "ready",
        )
        self.assertEqual(
            result["findings"]["overallFinding"],
            "Strong measured swing.",
        )
        self.assertEqual(
            result["findings"]["strengths"][0]["metricKey"],
            "tempo",
        )
        self.assertEqual(
            result["recommendations"]["status"],
            "ready",
        )
        self.assertEqual(
            result["recommendations"]["primaryFocus"][
                "metricKey"
            ],
            "rotation",
        )
        self.assertEqual(
            result["recommendations"]["recommendations"][0][
                "priority"
            ],
            1,
        )
        self.assertEqual(
            result["summary"]["referenceFrameCount"],
            6,
        )

    def test_to_dict_returns_new_top_level_section_dicts(
        self,
    ) -> None:
        report = self.build_report()

        first_result = report.to_dict()
        second_result = report.to_dict()

        section_keys = (
            "inputs",
            "coordinateSystem",
            "assumptions",
            "phaseFrames",
            "referenceGeometry",
            "metrics",
            "scoring",
            "findings",
            "recommendations",
            "summary",
        )

        for section_key in section_keys:
            self.assertIsNot(
                first_result[section_key],
                second_result[section_key],
            )

    def test_builder_rejects_invalid_required_section(
        self,
    ) -> None:
        invalid_metrics: Any = ["not", "a", "mapping"]

        with self.assertRaisesRegex(
            TypeError,
            "metrics",
        ):
            build_swing_analysis_report(
                source_video="swing.mp4",
                inputs={},
                coordinate_system={},
                assumptions={},
                phase_frames={},
                reference_geometry={},
                metrics=invalid_metrics,
                scoring={},
                findings={},
                recommendations={},
                summary={},
            )


if __name__ == "__main__":
    unittest.main()