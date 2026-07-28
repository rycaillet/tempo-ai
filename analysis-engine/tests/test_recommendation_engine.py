from __future__ import annotations

import unittest

from app.recommendations import (
    RecommendationTemplate,
    SwingRecommendations,
    build_swing_recommendations,
)


class RecommendationEngineTests(unittest.TestCase):
    @staticmethod
    def build_findings() -> dict[str, object]:
        return {
            "status": "ready",
            "overallFinding": (
                "This swing contains measurable areas for improvement."
            ),
            "strengths": [],
            "improvementPriorities": [
                {
                    "metricKey": "rotation",
                    "displayName": "Rotation",
                    "score": 62.0,
                    "severity": "high",
                    "reason": (
                        "Rotation was one of the lowest-scoring "
                        "available metrics."
                    ),
                },
                {
                    "metricKey": "tempo",
                    "displayName": "Tempo",
                    "score": 75.0,
                    "severity": "medium",
                    "reason": (
                        "Tempo was one of the lowest-scoring "
                        "available metrics."
                    ),
                },
            ],
            "warnings": [],
        }

    def test_builds_prioritized_recommendations(self) -> None:
        result = build_swing_recommendations(
            self.build_findings()
        )

        self.assertIsInstance(result, SwingRecommendations)
        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.recommendations), 2)

        self.assertEqual(
            result.recommendations[0].metric_key,
            "rotation",
        )
        self.assertEqual(
            result.recommendations[0].priority,
            1,
        )
        self.assertEqual(
            result.recommendations[1].metric_key,
            "tempo",
        )
        self.assertEqual(
            result.recommendations[1].priority,
            2,
        )

    def test_first_recommendation_becomes_primary_focus(
        self,
    ) -> None:
        result = build_swing_recommendations(
            self.build_findings()
        )

        self.assertIsNotNone(result.primary_focus)
        self.assertEqual(
            result.primary_focus.metric_key,
            "rotation",
        )
        self.assertEqual(
            result.primary_focus.display_name,
            "Rotation",
        )
        self.assertEqual(
            result.primary_focus.severity,
            "high",
        )

    def test_to_dict_uses_public_json_shape(self) -> None:
        result = build_swing_recommendations(
            self.build_findings()
        ).to_dict()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            result["primaryFocus"],
            {
                "metricKey": "rotation",
                "displayName": "Rotation",
                "severity": "high",
            },
        )
        self.assertEqual(
            result["recommendations"][0]["metricKey"],
            "rotation",
        )
        self.assertEqual(
            result["recommendations"][0]["priority"],
            1,
        )
        self.assertEqual(
            result["recommendations"][0]["title"],
            "Improve rotational sequencing",
        )

    def test_not_ready_findings_return_not_available(
        self,
    ) -> None:
        result = build_swing_recommendations(
            {
                "status": "not_available",
                "improvementPriorities": [],
                "warnings": ["missing_scoring_interpretation"],
            }
        )

        self.assertEqual(result.status, "not_available")
        self.assertIsNone(result.primary_focus)
        self.assertEqual(result.recommendations, ())
        self.assertEqual(
            result.warnings,
            (
                "missing_scoring_interpretation",
                "findings_not_ready",
            ),
        )

    def test_no_priorities_return_not_available(self) -> None:
        result = build_swing_recommendations(
            {
                "status": "ready",
                "improvementPriorities": [],
                "warnings": [],
            }
        )

        self.assertEqual(result.status, "not_available")
        self.assertIsNone(result.primary_focus)
        self.assertEqual(result.recommendations, ())
        self.assertEqual(
            result.warnings,
            ("no_improvement_priorities",),
        )

    def test_missing_catalog_entry_adds_warning(self) -> None:
        findings = {
            "status": "ready",
            "improvementPriorities": [
                {
                    "metricKey": "unknownMetric",
                    "displayName": "Unknown metric",
                    "severity": "high",
                },
                {
                    "metricKey": "rotation",
                    "displayName": "Rotation",
                    "severity": "medium",
                },
            ],
            "warnings": [],
        }

        result = build_swing_recommendations(findings)

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(
            result.recommendations[0].metric_key,
            "rotation",
        )
        self.assertEqual(
            result.recommendations[0].priority,
            1,
        )
        self.assertIn(
            "missing_recommendation_template:unknownMetric",
            result.warnings,
        )

    def test_custom_catalog_keeps_engine_generic(self) -> None:
        custom_catalog = {
            "customMetric": RecommendationTemplate(
                metric_key="customMetric",
                title="Improve the custom metric",
                summary="Practice the custom measured movement.",
                focus="Custom movement",
                rationale=(
                    "This demonstrates that the engine does not contain "
                    "metric-specific logic."
                ),
                practice_cues=(
                    "Practice the custom movement slowly.",
                ),
                caution=None,
            ),
        }

        findings = {
            "status": "ready",
            "improvementPriorities": [
                {
                    "metricKey": "customMetric",
                    "displayName": "Custom metric",
                    "severity": "low",
                },
            ],
            "warnings": [],
        }

        result = build_swing_recommendations(
            findings=findings,
            catalog=custom_catalog,
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(
            result.recommendations[0].metric_key,
            "customMetric",
        )
        self.assertEqual(
            result.recommendations[0].title,
            "Improve the custom metric",
        )

    def test_duplicate_metric_is_skipped(self) -> None:
        findings = self.build_findings()

        priorities = findings["improvementPriorities"]
        self.assertIsInstance(priorities, list)

        priorities.append(
            {
                "metricKey": "rotation",
                "displayName": "Rotation",
                "severity": "high",
            }
        )

        result = build_swing_recommendations(findings)

        self.assertEqual(len(result.recommendations), 2)
        self.assertIn(
            "duplicate_improvement_finding:rotation",
            result.warnings,
        )

    def test_invalid_priority_entry_is_skipped(self) -> None:
        findings = {
            "status": "ready",
            "improvementPriorities": [
                "invalid-entry",
                {
                    "metricKey": "tempo",
                    "displayName": "Tempo",
                    "severity": "medium",
                },
            ],
            "warnings": [],
        }

        result = build_swing_recommendations(findings)

        self.assertEqual(result.status, "ready")
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(
            result.recommendations[0].metric_key,
            "tempo",
        )
        self.assertIn(
            "invalid_improvement_finding",
            result.warnings,
        )


if __name__ == "__main__":
    unittest.main()