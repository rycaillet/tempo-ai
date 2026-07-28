from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.recommendations.catalog import (
    RECOMMENDATION_CATALOG,
    RecommendationTemplate,
)
from app.recommendations.models import (
    PrimaryFocus,
    Recommendation,
    SwingRecommendations,
)


def normalize_warnings(
    raw_warnings: Any,
) -> list[str]:
    """
    Return only valid warning strings from an upstream findings section.
    """

    if not isinstance(raw_warnings, list):
        return []

    return [
        warning
        for warning in raw_warnings
        if isinstance(warning, str) and warning
    ]


def build_recommendation(
    *,
    finding: Mapping[str, Any],
    template: RecommendationTemplate,
    priority: int,
) -> Recommendation | None:
    """
    Build one recommendation from an improvement finding and template.

    Invalid findings are ignored rather than allowing malformed upstream
    data to break the complete swing analysis.
    """

    metric_key = finding.get("metricKey")
    display_name = finding.get("displayName")
    severity = finding.get("severity")

    if not isinstance(metric_key, str) or not metric_key:
        return None

    normalized_display_name = (
        display_name
        if isinstance(display_name, str) and display_name
        else metric_key
    )

    normalized_severity = (
        severity
        if isinstance(severity, str) and severity
        else "unknown"
    )

    return Recommendation(
        metric_key=metric_key,
        display_name=normalized_display_name,
        severity=normalized_severity,
        priority=priority,
        title=template.title,
        summary=template.summary,
        focus=template.focus,
        rationale=template.rationale,
        practice_cues=template.practice_cues,
        caution=template.caution,
    )


def build_swing_recommendations(
    findings: Mapping[str, Any],
    catalog: Mapping[
        str,
        RecommendationTemplate,
    ] = RECOMMENDATION_CATALOG,
) -> SwingRecommendations:
    """
    Build deterministic coaching recommendations from swing findings.

    Improvement-priority order is preserved. Metric-specific coaching
    content is supplied entirely by the recommendation catalog, keeping
    the engine generic and independent of individual golf metrics.
    """

    findings_status = findings.get("status")
    warnings = normalize_warnings(findings.get("warnings"))

    if findings_status != "ready":
        warnings.append("findings_not_ready")

        return SwingRecommendations(
            status="not_available",
            primary_focus=None,
            recommendations=(),
            warnings=tuple(warnings),
        )

    raw_priorities = findings.get("improvementPriorities")

    if not isinstance(raw_priorities, list) or not raw_priorities:
        warnings.append("no_improvement_priorities")

        return SwingRecommendations(
            status="not_available",
            primary_focus=None,
            recommendations=(),
            warnings=tuple(warnings),
        )

    recommendations: list[Recommendation] = []
    processed_metric_keys: set[str] = set()

    for raw_finding in raw_priorities:
        if not isinstance(raw_finding, Mapping):
            warnings.append("invalid_improvement_finding")
            continue

        metric_key = raw_finding.get("metricKey")

        if not isinstance(metric_key, str) or not metric_key:
            warnings.append("invalid_improvement_finding")
            continue

        if metric_key in processed_metric_keys:
            warnings.append(
                f"duplicate_improvement_finding:{metric_key}"
            )
            continue

        processed_metric_keys.add(metric_key)

        template = catalog.get(metric_key)

        if template is None:
            warnings.append(
                f"missing_recommendation_template:{metric_key}"
            )
            continue

        recommendation = build_recommendation(
            finding=raw_finding,
            template=template,
            priority=len(recommendations) + 1,
        )

        if recommendation is None:
            warnings.append("invalid_improvement_finding")
            continue

        recommendations.append(recommendation)

    if not recommendations:
        warnings.append("no_recommendations_available")

        return SwingRecommendations(
            status="not_available",
            primary_focus=None,
            recommendations=(),
            warnings=tuple(warnings),
        )

    first_recommendation = recommendations[0]

    primary_focus = PrimaryFocus(
        metric_key=first_recommendation.metric_key,
        display_name=first_recommendation.display_name,
        severity=first_recommendation.severity,
    )

    return SwingRecommendations(
        status="ready",
        primary_focus=primary_focus,
        recommendations=tuple(recommendations),
        warnings=tuple(warnings),
    )