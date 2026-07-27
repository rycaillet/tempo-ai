from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.metrics.registry import (
    MetricRegistration,
    get_score_enabled_metric_registrations,
)
from app.scoring.interpretation import interpret_swing_score
from app.scoring.normalization import (
    calculate_normalized_weight,
    calculate_percentage,
    calculate_weighted_average,
    calculate_weighted_contribution,
    normalize_confidence,
    round_score,
)
from app.scoring.profile import (
    DEFAULT_SCORING_PROFILE,
    validate_score_profile,
)
from app.scoring.types import (
    MetricScore,
    ScoreProfile,
    SwingScore,
)


MetricResults = Mapping[str, Mapping[str, Any]]


def calculate_swing_score(
    registrations: Iterable[MetricRegistration],
    metric_results: MetricResults,
    profile: ScoreProfile = DEFAULT_SCORING_PROFILE,
) -> dict[str, object]:
    validate_score_profile(profile)

    score_registrations = get_score_enabled_metric_registrations(
        registrations
    )

    possible_weight = sum(
        float(registration.scoring_weight)
        for registration in score_registrations
    )

    score_candidates: list[
        tuple[
            MetricRegistration,
            str | None,
            float | None,
            float | None,
            str,
            str | None,
        ]
    ] = []

    available_weight = 0.0
    weighted_score_total = 0.0
    weighted_confidence_total = 0.0

    for registration in score_registrations:
        metric_key = registration.definition.key
        configured_weight = float(registration.scoring_weight)
        metric_result = metric_results.get(metric_key)

        if metric_result is None:
            score_candidates.append(
                (
                    registration,
                    None,
                    None,
                    None,
                    "unscored",
                    "missing_metric_result",
                )
            )
            continue

        classification_value = metric_result.get("classification")

        if not isinstance(classification_value, str):
            score_candidates.append(
                (
                    registration,
                    None,
                    None,
                    normalize_confidence(
                        metric_result.get("confidence")
                    ),
                    "unscored",
                    "missing_classification",
                )
            )
            continue

        classification = classification_value
        metric_profile = profile.classification_scores.get(metric_key)

        if metric_profile is None:
            score_candidates.append(
                (
                    registration,
                    classification,
                    None,
                    normalize_confidence(
                        metric_result.get("confidence")
                    ),
                    "unscored",
                    "missing_profile_mapping",
                )
            )
            continue

        if classification not in metric_profile:
            score_candidates.append(
                (
                    registration,
                    classification,
                    None,
                    normalize_confidence(
                        metric_result.get("confidence")
                    ),
                    "unscored",
                    "unmapped_classification",
                )
            )
            continue

        raw_score = metric_profile[classification]
        confidence = normalize_confidence(
            metric_result.get("confidence")
        )

        if raw_score is None:
            score_candidates.append(
                (
                    registration,
                    classification,
                    None,
                    confidence,
                    "unscored",
                    "classification_not_scorable",
                )
            )
            continue

        normalized_raw_score = float(raw_score)

        available_weight += configured_weight
        weighted_score_total += (
            normalized_raw_score * configured_weight
        )

        weighted_confidence_total += (
            (confidence if confidence is not None else 0.0)
            * configured_weight
        )

        score_candidates.append(
            (
                registration,
                classification,
                normalized_raw_score,
                confidence,
                "scored",
                None,
            )
        )

    metric_scores: dict[str, MetricScore] = {}

    for (
        registration,
        classification,
        raw_score,
        confidence,
        status,
        reason,
    ) in score_candidates:
        metric_key = registration.definition.key
        configured_weight = float(registration.scoring_weight)

        normalized_weight = (
            calculate_normalized_weight(
                configured_weight,
                available_weight,
            )
            if status == "scored"
            else 0.0
        )

        weighted_contribution = (
            calculate_weighted_contribution(
                raw_score,
                configured_weight,
                available_weight,
            )
            if status == "scored" and raw_score is not None
            else 0.0
        )

        metric_scores[metric_key] = MetricScore(
            metric_key=metric_key,
            classification=classification,
            status=status,
            reason=reason,
            raw_score=(
                round_score(raw_score)
                if raw_score is not None
                else None
            ),
            confidence=(
                round_score(confidence)
                if confidence is not None
                else None
            ),
            configured_weight=round_score(configured_weight),
            normalized_weight=round_score(normalized_weight),
            weighted_contribution=round_score(
                weighted_contribution
            ),
        )

    overall_score = calculate_weighted_average(
        weighted_score_total,
        available_weight,
    )

    score_confidence = calculate_weighted_average(
        weighted_confidence_total,
        available_weight,
    )

    score_coverage = calculate_percentage(
        available_weight,
        possible_weight,
    )

    swing_score = SwingScore(
        profile_name=profile.name,
        profile_version=profile.version,
        overall_score=(
            round_score(overall_score)
            if overall_score is not None
            else None
        ),
        score_confidence=(
            round_score(score_confidence * 100.0)
            if score_confidence is not None
            else None
        ),
        score_coverage=round_score(score_coverage),
        weighted_total=(
            round_score(
                sum(
                    metric_score.weighted_contribution
                    for metric_score in metric_scores.values()
                )
            )
            if overall_score is not None
            else None
        ),
        available_weight=round_score(available_weight),
        possible_weight=round_score(possible_weight),
        metrics=metric_scores,
    )

    result = swing_score.to_dict()
    result["interpretation"] = interpret_swing_score(
        swing_score
    ).to_dict()

    return result