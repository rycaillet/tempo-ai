from __future__ import annotations

import unittest
from dataclasses import replace

from app.analysis import (
    SwingAnalysisReport,
    build_swing_analysis_report,
)
from app.coaching import (
    CoachResponse,
    MockCoachingProvider,
    build_coach_context,
    generate_coaching_response,
)


class CoachingPipelineIntegrationTests(unittest.TestCase):
    @staticmethod
    def build_deterministic_report() -> SwingAnalysisReport:
        return build_swing_analysis_report(
            source_video="swing.mp4",
            inputs={
                "geometryAnalysisPath": (
                    "/analysis/geometry.json"
                ),
                "refinedPhasesPath": (
                    "/analysis/phases.json"
                ),
            },
            coordinate_system={
                "space": (
                    "normalized-landmarks-and-rotated-video-pixels"
                ),
                "angleUnits": "degrees",
            },
            assumptions={
                "handedness": "right",
            },
            phase_frames={},
            reference_geometry={},
            metrics={},
            scoring={
                "overallScore": 80.0,
                "scoreConfidence": 90.0,
                "scoreCoverage": 100.0,
                "interpretation": {
                    "status": "ready",
                    "rating": "good",
                    "ratingLabel": "Good",
                    "summary": (
                        "Solid measured swing fundamentals."
                    ),
                },
            },
            findings={
                "status": "ready",
                "overallFinding": (
                    "Address posture is the primary focus."
                ),
                "strengths": [
                    {
                        "metricKey": "tempo",
                        "displayName": "Tempo",
                        "score": 90.0,
                        "reason": (
                            "Tempo was one of the strongest "
                            "measured areas."
                        ),
                    },
                ],
                "improvementPriorities": [
                    {
                        "metricKey": "addressPosture",
                    },
                ],
                "warnings": [],
            },
            recommendations={
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
                        "title": "Improve address posture",
                        "summary": (
                            "Create a more balanced setup."
                        ),
                        "focus": "Balanced setup posture",
                        "rationale": (
                            "Setup influences the motion "
                            "that follows."
                        ),
                        "practiceCues": [
                            "Balance over the middle of the feet.",
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

    def test_pipeline_attaches_validated_coaching(
        self,
    ) -> None:
        deterministic_report = (
            self.build_deterministic_report()
        )
        deterministic_result = (
            deterministic_report.to_dict()
        )

        context = build_coach_context(
            deterministic_result
        )

        coaching_response = generate_coaching_response(
            context=context,
            provider=MockCoachingProvider(),
        )

        final_report = replace(
            deterministic_report,
            coaching=coaching_response,
        )

        final_result = final_report.to_dict()

        self.assertEqual(context.status, "ready")
        self.assertEqual(
            coaching_response.status,
            "ready",
        )
        self.assertIsInstance(
            final_report.coaching,
            CoachResponse,
        )
        self.assertEqual(
            final_result["coaching"]["status"],
            "ready",
        )

    def test_coaching_does_not_change_deterministic_sections(
        self,
    ) -> None:
        deterministic_report = (
            self.build_deterministic_report()
        )
        deterministic_result = (
            deterministic_report.to_dict()
        )

        context = build_coach_context(
            deterministic_result
        )
        coaching_response = generate_coaching_response(
            context=context,
            provider=MockCoachingProvider(),
        )

        final_result = replace(
            deterministic_report,
            coaching=coaching_response,
        ).to_dict()

        deterministic_section_keys = (
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
        )

        for section_key in deterministic_section_keys:
            self.assertEqual(
                final_result[section_key],
                deterministic_result[section_key],
            )

    def test_context_uses_deterministic_recommendation(
        self,
    ) -> None:
        report = self.build_deterministic_report()

        context = build_coach_context(
            report.to_dict()
        )

        self.assertEqual(
            context.primary_focus_metric_key,
            "addressPosture",
        )
        self.assertEqual(
            len(context.priorities),
            1,
        )
        self.assertEqual(
            context.priorities[0].metric_key,
            "addressPosture",
        )
        self.assertEqual(
            context.priorities[0].priority,
            1,
        )


if __name__ == "__main__":
    unittest.main()