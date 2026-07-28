from __future__ import annotations

import unittest

from app.coaching import build_coach_context


class CoachingContextTests(unittest.TestCase):
    @staticmethod
    def build_report() -> dict[str, object]:
        return {
            "scoring": {
                "overallScore": 85.06,
                "scoreConfidence": 100.0,
                "scoreCoverage": 85.0,
                "metrics": {
                    "rotation": {
                        "status": "unscored",
                        "reason": (
                            "classification_not_scorable"
                        ),
                    },
                },
                "interpretation": {
                    "rating": "good",
                    "ratingLabel": "Good",
                    "status": "ready",
                    "summary": (
                        "This swing demonstrates solid "
                        "measured fundamentals."
                    ),
                },
            },
            "findings": {
                "status": "ready",
                "overallFinding": (
                    "The swing has strong fundamentals with "
                    "two improvement opportunities."
                ),
                "strengths": [
                    {
                        "metricKey": "headStability",
                        "displayName": "Head stability",
                        "score": 100.0,
                        "reason": (
                            "Head stability was one of the "
                            "highest-scoring metrics."
                        ),
                    },
                ],
                "improvementPriorities": [
                    {
                        "metricKey": "addressPosture",
                        "displayName": "Address posture",
                        "severity": "high",
                    },
                    {
                        "metricKey": "weightShift",
                        "displayName": "Weight shift",
                        "severity": "high",
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
                        "title": (
                            "Create a balanced address posture"
                        ),
                        "summary": (
                            "Establish a stable setup."
                        ),
                        "focus": (
                            "Balance, alignment, and posture"
                        ),
                        "rationale": (
                            "Setup influences movement."
                        ),
                        "practiceCues": [
                            "Balance over the middle of the feet.",
                        ],
                        "caution": (
                            "Address posture varies with body "
                            "proportions."
                        ),
                    },
                    {
                        "metricKey": "weightShift",
                        "displayName": "Weight shift",
                        "severity": "high",
                        "priority": 2,
                        "title": "Improve pressure transfer",
                        "summary": (
                            "Coordinate movement toward the "
                            "lead side."
                        ),
                        "focus": "Lower-body pressure transfer",
                        "rationale": (
                            "Transfer supports sequencing."
                        ),
                        "practiceCues": [
                            "Finish supported on the lead side.",
                        ],
                        "caution": (
                            "Pose landmarks do not directly "
                            "measure pressure."
                        ),
                    },
                ],
                "warnings": [],
            },
        }

    def test_builds_ready_context_from_report(
        self,
    ) -> None:
        context = build_coach_context(
            self.build_report()
        )

        self.assertEqual(context.status, "ready")
        self.assertEqual(context.overall_score, 85.06)
        self.assertEqual(
            context.score_confidence,
            100.0,
        )
        self.assertEqual(context.score_coverage, 85.0)
        self.assertEqual(context.rating, "good")
        self.assertEqual(context.rating_label, "Good")
        self.assertEqual(
            context.primary_focus_metric_key,
            "addressPosture",
        )

    def test_preserves_strengths_and_priority_order(
        self,
    ) -> None:
        context = build_coach_context(
            self.build_report()
        )

        self.assertEqual(
            [
                strength.metric_key
                for strength in context.strengths
            ],
            ["headStability"],
        )

        self.assertEqual(
            [
                priority.metric_key
                for priority in context.priorities
            ],
            [
                "addressPosture",
                "weightShift",
            ],
        )

        self.assertEqual(
            [
                priority.priority
                for priority in context.priorities
            ],
            [1, 2],
        )

    def test_builds_analysis_limitations(
        self,
    ) -> None:
        context = build_coach_context(
            self.build_report()
        )

        self.assertIn(
            (
                "The overall score does not include every "
                "configured metric because one or more "
                "measurements were unavailable."
            ),
            context.limitations,
        )

        self.assertIn(
            (
                "Metric rotation was not scored: "
                "classification_not_scorable."
            ),
            context.limitations,
        )

        self.assertIn(
            (
                "Address posture varies with body "
                "proportions."
            ),
            context.limitations,
        )

        self.assertIn(
            (
                "Pose landmarks do not directly measure "
                "pressure."
            ),
            context.limitations,
        )

    def test_detects_recommendation_order_mismatch(
        self,
    ) -> None:
        report = self.build_report()

        recommendations = report["recommendations"]
        self.assertIsInstance(recommendations, dict)

        recommendation_items = recommendations[
            "recommendations"
        ]
        self.assertIsInstance(
            recommendation_items,
            list,
        )

        recommendation_items.reverse()

        context = build_coach_context(report)

        self.assertIn(
            "recommendation_order_mismatch",
            context.warnings,
        )
        self.assertIn(
            "recommendation_priority_mismatch",
            context.warnings,
        )
        self.assertIn(
            "primary_focus_mismatch",
            context.warnings,
        )

    def test_returns_not_available_when_layers_not_ready(
        self,
    ) -> None:
        report = self.build_report()

        findings = report["findings"]
        recommendations = report["recommendations"]

        self.assertIsInstance(findings, dict)
        self.assertIsInstance(recommendations, dict)

        findings["status"] = "not_available"
        recommendations["status"] = "not_available"
        recommendations["primaryFocus"] = None
        recommendations["recommendations"] = []

        context = build_coach_context(report)

        self.assertEqual(
            context.status,
            "not_available",
        )
        self.assertIn(
            "findings_not_ready",
            context.warnings,
        )
        self.assertIn(
            "recommendations_not_ready",
            context.warnings,
        )
        self.assertIsNone(
            context.primary_focus_metric_key
        )
        self.assertEqual(context.priorities, ())

    def test_propagates_upstream_warnings(
        self,
    ) -> None:
        report = self.build_report()

        findings = report["findings"]
        recommendations = report["recommendations"]

        self.assertIsInstance(findings, dict)
        self.assertIsInstance(recommendations, dict)

        findings["warnings"] = [
            "limited_metric_coverage",
        ]
        recommendations["warnings"] = [
            "missing_recommendation_template:rotation",
        ]

        context = build_coach_context(report)

        self.assertIn(
            "findings:limited_metric_coverage",
            context.warnings,
        )
        self.assertIn(
            (
                "recommendations:"
                "missing_recommendation_template:rotation"
            ),
            context.warnings,
        )

    def test_serialized_context_excludes_raw_analysis_data(
        self,
    ) -> None:
        report = self.build_report()
        report["metrics"] = {
            "rawMetric": {
                "landmarks": [1, 2, 3],
            },
        }
        report["referenceGeometry"] = {
            "addressReference": {
                "headCenter": {
                    "x": 0.5,
                    "y": 0.2,
                },
            },
        }

        result = build_coach_context(
            report
        ).to_dict()

        self.assertNotIn("metrics", result)
        self.assertNotIn(
            "referenceGeometry",
            result,
        )
        self.assertNotIn("landmarks", result)


if __name__ == "__main__":
    unittest.main()