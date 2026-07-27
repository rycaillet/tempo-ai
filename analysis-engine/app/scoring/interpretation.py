from __future__ import annotations

from dataclasses import dataclass

from app.scoring.types import SwingScore


EXCELLENT_SCORE_MINIMUM = 90.0
GOOD_SCORE_MINIMUM = 80.0
FAIR_SCORE_MINIMUM = 70.0
NEEDS_IMPROVEMENT_SCORE_MINIMUM = 55.0

READY_CONFIDENCE_MINIMUM = 70.0
READY_COVERAGE_MINIMUM = 75.0

REVIEW_CONFIDENCE_MINIMUM = 50.0
REVIEW_COVERAGE_MINIMUM = 50.0

STRENGTH_SCORE_MINIMUM = 85.0
IMPROVEMENT_PRIORITY_SCORE_MAXIMUM = 80.0

MAX_STRENGTHS = 2
MAX_IMPROVEMENT_PRIORITIES = 2


@dataclass(frozen=True)
class SwingInterpretation:
    rating: str
    rating_label: str
    status: str
    summary: str
    strengths: tuple[str, ...]
    improvement_priorities: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "rating": self.rating,
            "ratingLabel": self.rating_label,
            "status": self.status,
            "summary": self.summary,
            "strengths": list(self.strengths),
            "improvementPriorities": list(
                self.improvement_priorities
            ),
            "warnings": list(self.warnings),
        }


def classify_overall_score(
    overall_score: float | None,
) -> tuple[str, str]:
    if overall_score is None:
        return "not_available", "Not Available"

    if overall_score >= EXCELLENT_SCORE_MINIMUM:
        return "excellent", "Excellent"

    if overall_score >= GOOD_SCORE_MINIMUM:
        return "good", "Good"

    if overall_score >= FAIR_SCORE_MINIMUM:
        return "fair", "Fair"

    if overall_score >= NEEDS_IMPROVEMENT_SCORE_MINIMUM:
        return "needs_improvement", "Needs Improvement"

    return "poor", "Poor"


def determine_interpretation_status(
    overall_score: float | None,
    score_confidence: float | None,
    score_coverage: float,
) -> str:
    if overall_score is None:
        return "not_available"

    normalized_confidence = (
        score_confidence
        if score_confidence is not None
        else 0.0
    )

    if (
        normalized_confidence < REVIEW_CONFIDENCE_MINIMUM
        or score_coverage < REVIEW_COVERAGE_MINIMUM
    ):
        return "insufficient_data"

    if (
        normalized_confidence < READY_CONFIDENCE_MINIMUM
        or score_coverage < READY_COVERAGE_MINIMUM
    ):
        return "review"

    return "ready"


def build_interpretation_warnings(
    score_confidence: float | None,
    score_coverage: float,
) -> tuple[str, ...]:
    warnings: list[str] = []

    normalized_confidence = (
        score_confidence
        if score_confidence is not None
        else 0.0
    )

    if normalized_confidence < READY_CONFIDENCE_MINIMUM:
        warnings.append("low_score_confidence")

    if score_coverage < READY_COVERAGE_MINIMUM:
        warnings.append("limited_score_coverage")

    return tuple(warnings)


def identify_strengths(
    swing_score: SwingScore,
) -> tuple[str, ...]:
    scored_metrics = [
        metric_score
        for metric_score in swing_score.metrics.values()
        if (
            metric_score.status == "scored"
            and metric_score.raw_score is not None
            and metric_score.raw_score
            >= STRENGTH_SCORE_MINIMUM
        )
    ]

    scored_metrics.sort(
        key=lambda metric_score: (
            -float(metric_score.raw_score),
            metric_score.metric_key,
        )
    )

    return tuple(
        metric_score.metric_key
        for metric_score in scored_metrics[:MAX_STRENGTHS]
    )


def identify_improvement_priorities(
    swing_score: SwingScore,
) -> tuple[str, ...]:
    scored_metrics = [
        metric_score
        for metric_score in swing_score.metrics.values()
        if (
            metric_score.status == "scored"
            and metric_score.raw_score is not None
            and metric_score.raw_score
            < IMPROVEMENT_PRIORITY_SCORE_MAXIMUM
        )
    ]

    scored_metrics.sort(
        key=lambda metric_score: (
            float(metric_score.raw_score),
            metric_score.metric_key,
        )
    )

    return tuple(
        metric_score.metric_key
        for metric_score in scored_metrics[
            :MAX_IMPROVEMENT_PRIORITIES
        ]
    )


def build_interpretation_summary(
    rating: str,
    status: str,
) -> str:
    if status == "not_available":
        return (
            "A swing rating could not be produced because no "
            "score-weighted metrics were available."
        )

    rating_summaries = {
        "excellent": (
            "This swing demonstrates excellent measured fundamentals "
            "across the available metrics."
        ),
        "good": (
            "This swing demonstrates solid measured fundamentals with "
            "a few improvement opportunities."
        ),
        "fair": (
            "This swing shows a mix of solid fundamentals and "
            "measurable areas for improvement."
        ),
        "needs_improvement": (
            "This swing contains several measurable areas that would "
            "benefit from focused improvement."
        ),
        "poor": (
            "The available metrics identify significant opportunities "
            "to improve this swing."
        ),
    }

    summary = rating_summaries[rating]

    if status == "insufficient_data":
        return (
            f"{summary} The current interpretation is limited because "
            "the analysis does not contain enough reliable data."
        )

    if status == "review":
        return (
            f"{summary} Review the confidence and coverage before "
            "relying fully on this interpretation."
        )

    return summary


def interpret_swing_score(
    swing_score: SwingScore,
) -> SwingInterpretation:
    rating, rating_label = classify_overall_score(
        swing_score.overall_score
    )

    status = determine_interpretation_status(
        overall_score=swing_score.overall_score,
        score_confidence=swing_score.score_confidence,
        score_coverage=swing_score.score_coverage,
    )

    return SwingInterpretation(
        rating=rating,
        rating_label=rating_label,
        status=status,
        summary=build_interpretation_summary(
            rating=rating,
            status=status,
        ),
        strengths=identify_strengths(swing_score),
        improvement_priorities=(
            identify_improvement_priorities(swing_score)
        ),
        warnings=build_interpretation_warnings(
            score_confidence=swing_score.score_confidence,
            score_coverage=swing_score.score_coverage,
        ),
    )