from __future__ import annotations

import unittest

from app.scoring.interpretation import (
    classify_overall_score,
    determine_interpretation_status,
    interpret_swing_score,
)
from app.scoring.types import MetricScore, SwingScore


def build_metric_score(
    metric_key: str,
    raw_score: float | None,
    *,
    status: str = "scored",
) -> MetricScore:
    return MetricScore(
        metric_key=metric_key,
        classification=(
            "neutral"
            if raw_score is not None
            else "incomplete"
        ),
        status=status,
        reason=(
            None
            if status == "scored"
            else "classification_not_scorable"
        ),
        raw_score=raw_score,
        confidence=1.0,
        configured_weight=20.0,
        normalized_weight=20.0,
        weighted_contribution=(
            raw_score * 0.2
            if raw_score is not None
            else 0.0
        ),
    )


def build_swing_score(
    overall_score: float | None,
    *,
    score_confidence: float | None = 100.0,
    score_coverage: float = 100.0,
    metrics: dict[str, MetricScore] | None = None,
) -> SwingScore:
    return SwingScore(
        profile_name="default",
        profile_version="1.0.0",
        overall_score=overall_score,
        score_confidence=score_confidence,
        score_coverage=score_coverage,
        weighted_total=overall_score,
        available_weight=100.0,
        possible_weight=100.0,
        metrics=metrics or {},
    )


class ScoringInterpretationTests(unittest.TestCase):
    def test_classifies_score_rating_boundaries(self) -> None:
        cases = (
            (100.0, "excellent"),
            (90.0, "excellent"),
            (89.99, "good"),
            (80.0, "good"),
            (79.99, "fair"),
            (70.0, "fair"),
            (69.99, "needs_improvement"),
            (55.0, "needs_improvement"),
            (54.99, "poor"),
            (0.0, "poor"),
            (None, "not_available"),
        )

        for overall_score, expected_rating in cases:
            with self.subTest(overall_score=overall_score):
                rating, _ = classify_overall_score(
                    overall_score
                )

                self.assertEqual(rating, expected_rating)

    def test_ready_status_requires_good_confidence_and_coverage(
        self,
    ) -> None:
        status = determine_interpretation_status(
            overall_score=85.0,
            score_confidence=90.0,
            score_coverage=100.0,
        )

        self.assertEqual(status, "ready")

    def test_review_status_handles_moderate_confidence(
        self,
    ) -> None:
        status = determine_interpretation_status(
            overall_score=85.0,
            score_confidence=65.0,
            score_coverage=100.0,
        )

        self.assertEqual(status, "review")

    def test_review_status_handles_moderate_coverage(
        self,
    ) -> None:
        status = determine_interpretation_status(
            overall_score=85.0,
            score_confidence=90.0,
            score_coverage=70.0,
        )

        self.assertEqual(status, "review")

    def test_insufficient_data_status_handles_low_confidence(
        self,
    ) -> None:
        status = determine_interpretation_status(
            overall_score=85.0,
            score_confidence=49.99,
            score_coverage=100.0,
        )

        self.assertEqual(status, "insufficient_data")

    def test_insufficient_data_status_handles_low_coverage(
        self,
    ) -> None:
        status = determine_interpretation_status(
            overall_score=85.0,
            score_confidence=90.0,
            score_coverage=49.99,
        )

        self.assertEqual(status, "insufficient_data")

    def test_missing_score_is_not_available(self) -> None:
        interpretation = interpret_swing_score(
            build_swing_score(
                overall_score=None,
                score_confidence=None,
                score_coverage=0.0,
            )
        )

        self.assertEqual(
            interpretation.rating,
            "not_available",
        )
        self.assertEqual(
            interpretation.status,
            "not_available",
        )
        self.assertEqual(interpretation.strengths, ())
        self.assertEqual(
            interpretation.improvement_priorities,
            (),
        )

    def test_identifies_top_scoring_strengths(self) -> None:
        swing_score = build_swing_score(
            overall_score=88.0,
            metrics={
                "tempo": build_metric_score(
                    "tempo",
                    100.0,
                ),
                "rotation": build_metric_score(
                    "rotation",
                    90.0,
                ),
                "headStability": build_metric_score(
                    "headStability",
                    85.0,
                ),
            },
        )

        interpretation = interpret_swing_score(swing_score)

        self.assertEqual(
            interpretation.strengths,
            ("tempo", "rotation"),
        )

    def test_identifies_lowest_improvement_priorities(
        self,
    ) -> None:
        swing_score = build_swing_score(
            overall_score=70.0,
            metrics={
                "tempo": build_metric_score(
                    "tempo",
                    100.0,
                ),
                "rotation": build_metric_score(
                    "rotation",
                    60.0,
                ),
                "impactPosition": build_metric_score(
                    "impactPosition",
                    55.0,
                ),
                "weightShift": build_metric_score(
                    "weightShift",
                    75.0,
                ),
            },
        )

        interpretation = interpret_swing_score(swing_score)

        self.assertEqual(
            interpretation.improvement_priorities,
            ("impactPosition", "rotation"),
        )

    def test_excludes_unscored_metrics_from_priorities(
        self,
    ) -> None:
        swing_score = build_swing_score(
            overall_score=100.0,
            metrics={
                "tempo": build_metric_score(
                    "tempo",
                    100.0,
                ),
                "impactPosition": build_metric_score(
                    "impactPosition",
                    None,
                    status="unscored",
                ),
            },
        )

        interpretation = interpret_swing_score(swing_score)

        self.assertEqual(
            interpretation.improvement_priorities,
            (),
        )

    def test_reports_confidence_and_coverage_warnings(
        self,
    ) -> None:
        interpretation = interpret_swing_score(
            build_swing_score(
                overall_score=80.0,
                score_confidence=60.0,
                score_coverage=65.0,
            )
        )

        self.assertEqual(
            interpretation.warnings,
            (
                "low_score_confidence",
                "limited_score_coverage",
            ),
        )

    def test_ready_interpretation_has_no_warnings(
        self,
    ) -> None:
        interpretation = interpret_swing_score(
            build_swing_score(
                overall_score=80.0,
                score_confidence=90.0,
                score_coverage=100.0,
            )
        )

        self.assertEqual(interpretation.warnings, ())


if __name__ == "__main__":
    unittest.main()