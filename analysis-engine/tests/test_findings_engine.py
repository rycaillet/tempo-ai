from __future__ import annotations

import unittest

from app.findings import (
    SwingFindings,
    build_swing_findings,
    determine_improvement_severity,
)


class FindingsEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.display_names = {
            "tempo": "Tempo",
            "rotation": "Rotation",
            "headStability": "Head stability",
        }

    def test_builds_structured_swing_findings(self) -> None:
        scoring = {
            "metrics": {
                "tempo": {
                    "status": "scored",
                    "rawScore": 92.0,
                },
                "rotation": {
                    "status": "scored",
                    "rawScore": 62.0,
                },
            },
            "interpretation": {
                "status": "ready",
                "summary": (
                    "This swing demonstrates solid measured "
                    "fundamentals."
                ),
                "strengths": ["tempo"],
                "improvementPriorities": ["rotation"],
                "warnings": [],
            },
        }

        findings = build_swing_findings(
            scoring=scoring,
            metric_display_names=self.display_names,
        )

        self.assertIsInstance(findings, SwingFindings)
        self.assertEqual(findings.status, "ready")
        self.assertEqual(len(findings.strengths), 1)
        self.assertEqual(
            findings.strengths[0].metric_key,
            "tempo",
        )
        self.assertEqual(
            findings.strengths[0].display_name,
            "Tempo",
        )
        self.assertEqual(
            findings.improvement_priorities[0].metric_key,
            "rotation",
        )
        self.assertEqual(
            findings.improvement_priorities[0].severity,
            "high",
        )

    def test_to_dict_uses_public_json_names(self) -> None:
        scoring = {
            "metrics": {
                "tempo": {
                    "status": "scored",
                    "rawScore": 90.0,
                },
            },
            "interpretation": {
                "status": "ready",
                "summary": "Strong measured swing.",
                "strengths": ["tempo"],
                "improvementPriorities": [],
                "warnings": [],
            },
        }

        result = build_swing_findings(
            scoring=scoring,
            metric_display_names=self.display_names,
        ).to_dict()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            result["overallFinding"],
            "Strong measured swing.",
        )
        self.assertEqual(
            result["strengths"][0]["metricKey"],
            "tempo",
        )
        self.assertEqual(
            result["strengths"][0]["displayName"],
            "Tempo",
        )

    def test_missing_interpretation_returns_not_available(self) -> None:
        findings = build_swing_findings(
            scoring={
                "metrics": {},
            },
            metric_display_names=self.display_names,
        )

        self.assertEqual(findings.status, "not_available")
        self.assertEqual(findings.strengths, ())
        self.assertEqual(
            findings.warnings,
            ("missing_scoring_interpretation",),
        )

    def test_missing_metric_score_skips_finding(self) -> None:
        scoring = {
            "metrics": {},
            "interpretation": {
                "status": "ready",
                "summary": "Analysis complete.",
                "strengths": ["tempo"],
                "improvementPriorities": ["rotation"],
                "warnings": [],
            },
        }

        findings = build_swing_findings(
            scoring=scoring,
            metric_display_names=self.display_names,
        )

        self.assertEqual(findings.strengths, ())
        self.assertEqual(
            findings.improvement_priorities,
            (),
        )

    def test_severity_thresholds(self) -> None:
        self.assertEqual(
            determine_improvement_severity(45.0),
            "high",
        )
        self.assertEqual(
            determine_improvement_severity(69.0),
            "high",
        )
        self.assertEqual(
            determine_improvement_severity(70.0),
            "medium",
        )
        self.assertEqual(
            determine_improvement_severity(79.0),
            "medium",
        )
        self.assertEqual(
            determine_improvement_severity(80.0),
            "low",
        )


if __name__ == "__main__":
    unittest.main()