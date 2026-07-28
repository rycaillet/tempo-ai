from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.coaching.models import (
    CoachContext,
    CoachPriority,
    CoachStrength,
)


def normalize_string(
    value: Any,
) -> str | None:
    """
    Return a nonempty string or None.
    """

    if not isinstance(value, str) or not value:
        return None

    return value


def normalize_number(
    value: Any,
) -> float | None:
    """
    Return a numeric value as a float while rejecting booleans.
    """

    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    return float(value)


def normalize_string_list(
    value: Any,
) -> list[str]:
    """
    Return only valid, nonempty strings from an upstream collection.
    """

    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, str) and item
    ]


def append_unique(
    values: list[str],
    value: str,
) -> None:
    """
    Append a string only when it is not already present.
    """

    if value not in values:
        values.append(value)


def get_mapping(
    value: Any,
) -> Mapping[str, Any]:
    """
    Normalize an arbitrary value into a readable mapping.
    """

    if isinstance(value, Mapping):
        return value

    return {}


def build_coach_strength(
    raw_strength: Any,
) -> CoachStrength | None:
    """
    Build one compact strength from a deterministic finding.
    """

    if not isinstance(raw_strength, Mapping):
        return None

    metric_key = normalize_string(
        raw_strength.get("metricKey")
    )

    if metric_key is None:
        return None

    display_name = (
        normalize_string(
            raw_strength.get("displayName")
        )
        or metric_key
    )

    return CoachStrength(
        metric_key=metric_key,
        display_name=display_name,
        score=normalize_number(
            raw_strength.get("score")
        ),
        reason=normalize_string(
            raw_strength.get("reason")
        ),
    )


def build_coach_priority(
    raw_recommendation: Any,
) -> CoachPriority | None:
    """
    Build one provider-safe coaching priority.

    The function accepts only complete catalog-backed recommendation
    objects. Invalid entries are skipped and reported by the context
    builder.
    """

    if not isinstance(raw_recommendation, Mapping):
        return None

    metric_key = normalize_string(
        raw_recommendation.get("metricKey")
    )
    title = normalize_string(
        raw_recommendation.get("title")
    )
    summary = normalize_string(
        raw_recommendation.get("summary")
    )
    focus = normalize_string(
        raw_recommendation.get("focus")
    )
    rationale = normalize_string(
        raw_recommendation.get("rationale")
    )

    priority_value = raw_recommendation.get("priority")

    if (
        metric_key is None
        or title is None
        or summary is None
        or focus is None
        or rationale is None
        or not isinstance(priority_value, int)
        or isinstance(priority_value, bool)
        or priority_value < 1
    ):
        return None

    display_name = (
        normalize_string(
            raw_recommendation.get("displayName")
        )
        or metric_key
    )

    severity = (
        normalize_string(
            raw_recommendation.get("severity")
        )
        or "unknown"
    )

    return CoachPriority(
        metric_key=metric_key,
        display_name=display_name,
        severity=severity,
        priority=priority_value,
        title=title,
        summary=summary,
        focus=focus,
        rationale=rationale,
        practice_cues=tuple(
            normalize_string_list(
                raw_recommendation.get(
                    "practiceCues"
                )
            )
        ),
        caution=normalize_string(
            raw_recommendation.get("caution")
        ),
    )


def extract_metric_keys(
    raw_items: Any,
) -> list[str]:
    """
    Extract valid metric keys while preserving source order.
    """

    if not isinstance(raw_items, list):
        return []

    metric_keys: list[str] = []

    for raw_item in raw_items:
        if not isinstance(raw_item, Mapping):
            continue

        metric_key = normalize_string(
            raw_item.get("metricKey")
        )

        if metric_key is not None:
            metric_keys.append(metric_key)

    return metric_keys


def build_analysis_limitations(
    *,
    scoring: Mapping[str, Any],
    priorities: tuple[CoachPriority, ...],
) -> list[str]:
    """
    Build compact limitations relevant to AI-generated coaching.

    Limitations are factual constraints already represented by the
    deterministic report. They are not new swing conclusions.
    """

    limitations: list[str] = []

    score_coverage = normalize_number(
        scoring.get("scoreCoverage")
    )

    if (
        score_coverage is not None
        and score_coverage < 100.0
    ):
        limitations.append(
            "The overall score does not include every configured "
            "metric because one or more measurements were unavailable."
        )

    scoring_metrics = scoring.get("metrics")

    if isinstance(scoring_metrics, Mapping):
        for metric_key, raw_metric in scoring_metrics.items():
            if not isinstance(raw_metric, Mapping):
                continue

            if raw_metric.get("status") != "unscored":
                continue

            reason = (
                normalize_string(raw_metric.get("reason"))
                or "unknown_reason"
            )

            limitations.append(
                f"Metric {metric_key} was not scored: {reason}."
            )

    for priority in priorities:
        if priority.caution is not None:
            append_unique(
                limitations,
                priority.caution,
            )

    return limitations


def build_coach_context(
    report: Mapping[str, Any],
) -> CoachContext:
    """
    Convert a complete deterministic analysis report into compact,
    provider-independent AI coaching context.

    Cross-layer inconsistencies are exposed as warnings rather than
    silently corrected. The AI layer therefore cannot hide disagreement
    between findings and recommendations.
    """

    scoring = get_mapping(report.get("scoring"))
    interpretation = get_mapping(
        scoring.get("interpretation")
    )
    findings = get_mapping(report.get("findings"))
    recommendations_section = get_mapping(
        report.get("recommendations")
    )

    warnings: list[str] = []

    for warning in normalize_string_list(
        findings.get("warnings")
    ):
        append_unique(
            warnings,
            f"findings:{warning}",
        )

    for warning in normalize_string_list(
        recommendations_section.get("warnings")
    ):
        append_unique(
            warnings,
            f"recommendations:{warning}",
        )

    interpretation_status = normalize_string(
        interpretation.get("status")
    )
    findings_status = normalize_string(
        findings.get("status")
    )
    recommendations_status = normalize_string(
        recommendations_section.get("status")
    )

    if interpretation_status != "ready":
        append_unique(
            warnings,
            "scoring_interpretation_not_ready",
        )

    if findings_status != "ready":
        append_unique(
            warnings,
            "findings_not_ready",
        )

    if recommendations_status != "ready":
        append_unique(
            warnings,
            "recommendations_not_ready",
        )

    raw_strengths = findings.get("strengths")
    strengths: list[CoachStrength] = []

    if isinstance(raw_strengths, list):
        for raw_strength in raw_strengths:
            strength = build_coach_strength(
                raw_strength
            )

            if strength is None:
                append_unique(
                    warnings,
                    "invalid_strength",
                )
                continue

            strengths.append(strength)

    raw_recommendations = recommendations_section.get(
        "recommendations"
    )
    priorities: list[CoachPriority] = []

    if isinstance(raw_recommendations, list):
        for raw_recommendation in raw_recommendations:
            priority = build_coach_priority(
                raw_recommendation
            )

            if priority is None:
                append_unique(
                    warnings,
                    "invalid_recommendation",
                )
                continue

            priorities.append(priority)

    finding_metric_keys = extract_metric_keys(
        findings.get("improvementPriorities")
    )
    recommendation_metric_keys = [
        priority.metric_key
        for priority in priorities
    ]

    if (
        finding_metric_keys
        != recommendation_metric_keys
    ):
        append_unique(
            warnings,
            "recommendation_order_mismatch",
        )

    actual_priorities = [
        priority.priority
        for priority in priorities
    ]
    expected_priorities = list(
        range(1, len(priorities) + 1)
    )

    if actual_priorities != expected_priorities:
        append_unique(
            warnings,
            "recommendation_priority_mismatch",
        )

    primary_focus = get_mapping(
        recommendations_section.get(
            "primaryFocus"
        )
    )
    primary_focus_metric_key = normalize_string(
        primary_focus.get("metricKey")
    )

    expected_primary_focus = (
        priorities[0].metric_key
        if priorities
        else None
    )

    if (
        primary_focus_metric_key
        != expected_primary_focus
    ):
        append_unique(
            warnings,
            "primary_focus_mismatch",
        )

    normalized_priorities = tuple(priorities)

    limitations = build_analysis_limitations(
        scoring=scoring,
        priorities=normalized_priorities,
    )

    ready = (
        interpretation_status == "ready"
        and findings_status == "ready"
        and recommendations_status == "ready"
        and bool(normalized_priorities)
    )

    return CoachContext(
        status="ready" if ready else "not_available",
        overall_score=normalize_number(
            scoring.get("overallScore")
        ),
        score_confidence=normalize_number(
            scoring.get("scoreConfidence")
        ),
        score_coverage=normalize_number(
            scoring.get("scoreCoverage")
        ),
        rating=normalize_string(
            interpretation.get("rating")
        ),
        rating_label=normalize_string(
            interpretation.get("ratingLabel")
        ),
        analysis_summary=normalize_string(
            interpretation.get("summary")
        ),
        overall_finding=normalize_string(
            findings.get("overallFinding")
        ),
        primary_focus_metric_key=(
            primary_focus_metric_key
        ),
        strengths=tuple(strengths),
        priorities=normalized_priorities,
        warnings=tuple(warnings),
        limitations=tuple(limitations),
    )