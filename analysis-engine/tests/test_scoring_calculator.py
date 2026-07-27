from __future__ import annotations

import unittest
from typing import Any

from app.metrics.registry import (
    MetricDefinition,
    MetricRegistration,
)
from app.scoring.calculator import calculate_swing_score
from app.scoring.profile import (
    DEFAULT_SCORING_PROFILE,
    validate_score_profile,
)
from app.scoring.types import ScoreProfile


def build_unused_metric(
    context: dict[str, Any],
) -> dict[str, Any]:
    del context
    return {}


def build_registration(
    key: str,
    weight: float,
    *,
    enabled: bool = True,
) -> MetricRegistration:
    return MetricRegistration(
        definition=MetricDefinition(
            key=key,
            display_name=key,
            builder=build_unused_metric,
        ),
        enabled=enabled,
        version="1.0.0",
        scoring_weight=weight,
    )


class ScoringCalculatorTests(unittest.TestCase):
    def test_calculates_weighted_overall_score(self) -> None:
        registrations = (
            build_registration("tempo", 15.0),
            build_registration("impactPosition", 20.0),
        )

        metric_results = {
            "tempo": {
                "classification": "balanced",
                "confidence": 0.8,
            },
            "impactPosition": {
                "classification": "needs_attention",
                "confidence": 0.5,
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertEqual(scoring["overallScore"], 74.29)
        self.assertEqual(scoring["weightedTotal"], 74.29)
        self.assertEqual(scoring["availableWeight"], 35.0)
        self.assertEqual(scoring["possibleWeight"], 35.0)
        self.assertEqual(scoring["scoreCoverage"], 100.0)
        self.assertEqual(scoring["scoreConfidence"], 62.86)

        metrics = scoring["metrics"]

        self.assertEqual(
            metrics["tempo"]["weightedContribution"],
            42.86,
        )
        self.assertEqual(
            metrics["impactPosition"][
                "weightedContribution"
            ],
            31.43,
        )

    def test_renormalizes_when_metric_is_incomplete(self) -> None:
        registrations = (
            build_registration("tempo", 15.0),
            build_registration("impactPosition", 20.0),
        )

        metric_results = {
            "tempo": {
                "classification": "balanced",
                "confidence": 0.9,
            },
            "impactPosition": {
                "classification": "incomplete",
                "confidence": 0.4,
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertEqual(scoring["overallScore"], 100.0)
        self.assertEqual(scoring["availableWeight"], 15.0)
        self.assertEqual(scoring["possibleWeight"], 35.0)
        self.assertEqual(scoring["scoreCoverage"], 42.86)
        self.assertEqual(scoring["scoreConfidence"], 90.0)

        impact_score = scoring["metrics"]["impactPosition"]

        self.assertEqual(impact_score["status"], "unscored")
        self.assertEqual(
            impact_score["reason"],
            "classification_not_scorable",
        )
        self.assertIsNone(impact_score["rawScore"])
        self.assertEqual(impact_score["normalizedWeight"], 0.0)

    def test_reports_unmapped_classification(self) -> None:
        registrations = (
            build_registration("rotation", 15.0),
        )

        metric_results = {
            "rotation": {
                "classification": "unexpected_state",
                "confidence": 1.0,
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertIsNone(scoring["overallScore"])
        self.assertIsNone(scoring["scoreConfidence"])
        self.assertEqual(scoring["availableWeight"], 0.0)
        self.assertEqual(scoring["scoreCoverage"], 0.0)

        rotation_score = scoring["metrics"]["rotation"]

        self.assertEqual(rotation_score["status"], "unscored")
        self.assertEqual(
            rotation_score["reason"],
            "unmapped_classification",
        )

    def test_reports_missing_metric_result(self) -> None:
        registrations = (
            build_registration("weightShift", 15.0),
        )

        scoring = calculate_swing_score(
            registrations,
            {},
        )

        metric_score = scoring["metrics"]["weightShift"]

        self.assertIsNone(scoring["overallScore"])
        self.assertEqual(
            metric_score["reason"],
            "missing_metric_result",
        )
        self.assertIsNone(metric_score["classification"])

    def test_excludes_disabled_and_zero_weight_metrics(
        self,
    ) -> None:
        registrations = (
            build_registration("tempo", 15.0),
            build_registration(
                "rotation",
                15.0,
                enabled=False,
            ),
            build_registration("headStability", 0.0),
        )

        metric_results = {
            "tempo": {
                "classification": "balanced",
                "confidence": 1.0,
            },
            "rotation": {
                "classification": "neutral",
                "confidence": 1.0,
            },
            "headStability": {
                "classification": "neutral",
                "confidence": 1.0,
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertEqual(
            set(scoring["metrics"].keys()),
            {"tempo"},
        )
        self.assertEqual(scoring["possibleWeight"], 15.0)

    def test_missing_confidence_does_not_change_performance_score(
        self,
    ) -> None:
        registrations = (
            build_registration("tempo", 15.0),
        )

        metric_results = {
            "tempo": {
                "classification": "balanced",
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertEqual(scoring["overallScore"], 100.0)
        self.assertEqual(scoring["scoreConfidence"], 0.0)
        self.assertIsNone(
            scoring["metrics"]["tempo"]["confidence"]
        )

    def test_clamps_confidence_to_supported_range(self) -> None:
        registrations = (
            build_registration("tempo", 15.0),
        )

        metric_results = {
            "tempo": {
                "classification": "balanced",
                "confidence": 1.4,
            },
        }

        scoring = calculate_swing_score(
            registrations,
            metric_results,
        )

        self.assertEqual(scoring["scoreConfidence"], 100.0)
        self.assertEqual(
            scoring["metrics"]["tempo"]["confidence"],
            1.0,
        )

    def test_default_profile_supports_early_extension_severity(
        self,
    ) -> None:
        registrations = (
            build_registration("earlyExtension", 15.0),
        )

        expected_scores = {
            "neutral": 100.0,
            "mild_early_extension": 80.0,
            "moderate_early_extension": 55.0,
            "severe_early_extension": 25.0,
        }

        for classification, expected_score in (
            expected_scores.items()
        ):
            with self.subTest(classification=classification):
                scoring = calculate_swing_score(
                    registrations,
                    {
                        "earlyExtension": {
                            "classification": classification,
                            "confidence": 1.0,
                        }
                    },
                )

                self.assertEqual(
                    scoring["overallScore"],
                    expected_score,
                )

    def test_rejects_out_of_range_profile_score(self) -> None:
        invalid_profile = ScoreProfile(
            name="invalid",
            version="1.0.0",
            classification_scores={
                "tempo": {
                    "balanced": 101.0,
                }
            },
        )

        with self.assertRaises(ValueError):
            validate_score_profile(invalid_profile)

    def test_default_profile_is_valid(self) -> None:
        validate_score_profile(DEFAULT_SCORING_PROFILE)


if __name__ == "__main__":
    unittest.main()