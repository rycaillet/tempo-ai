from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.findings.models import (
    ImprovementFinding,
    StrengthFinding,
    SwingFindings,
)


HIGH_SEVERITY_SCORE_MAXIMUM = 69.999999
MEDIUM_SEVERITY_SCORE_MAXIMUM = 79.999999


def get_numeric_score(
    metric_result: Mapping[str, Any],
) -> float | None:
    raw_score = metric_result.get("rawScore")

    if not isinstance(raw_score, (int, float)):
        return None

    return float(raw_score)


def determine_improvement_severity(score: float) -> str:
    if score <= HIGH_SEVERITY_SCORE_MAXIMUM:
        return "high"

    if score <= MEDIUM_SEVERITY_SCORE_MAXIMUM:
        return "medium"

    return "low"


def get_display_name(
    metric_key: str,
    metric_display_names: Mapping[str, str],
) -> str:
    display_name = metric_display_names.get(metric_key)

    if isinstance(display_name, str) and display_name:
        return display_name

    return metric_key


def build_strength_findings(
    scoring_metrics: Mapping[str, Any],
    strength_metric_keys: list[str],
    metric_display_names: Mapping[str, str],
) -> tuple[StrengthFinding, ...]:
    findings: list[StrengthFinding] = []

    for metric_key in strength_metric_keys:
        metric_result = scoring_metrics.get(metric_key)

        if not isinstance(metric_result, Mapping):
            continue

        score = get_numeric_score(metric_result)

        if score is None:
            continue

        findings.append(
            StrengthFinding(
                metric_key=metric_key,
                display_name=get_display_name(
                    metric_key,
                    metric_display_names,
                ),
                score=score,
                reason=(
                    f"{get_display_name(metric_key, metric_display_names)} "
                    "was one of the highest-scoring available metrics."
                ),
            )
        )

    return tuple(findings)


def build_improvement_findings(
    scoring_metrics: Mapping[str, Any],
    priority_metric_keys: list[str],
    metric_display_names: Mapping[str, str],
) -> tuple[ImprovementFinding, ...]:
    findings: list[ImprovementFinding] = []

    for metric_key in priority_metric_keys:
        metric_result = scoring_metrics.get(metric_key)

        if not isinstance(metric_result, Mapping):
            continue

        score = get_numeric_score(metric_result)

        if score is None:
            continue

        display_name = get_display_name(
            metric_key,
            metric_display_names,
        )

        findings.append(
            ImprovementFinding(
                metric_key=metric_key,
                display_name=display_name,
                score=score,
                severity=determine_improvement_severity(score),
                reason=(
                    f"{display_name} was one of the lowest-scoring "
                    "available metrics."
                ),
            )
        )

    return tuple(findings)


def build_swing_findings(
    scoring: Mapping[str, Any],
    metric_display_names: Mapping[str, str],
) -> SwingFindings:
    interpretation = scoring.get("interpretation")
    scoring_metrics = scoring.get("metrics")

    if not isinstance(interpretation, Mapping):
        return SwingFindings(
            status="not_available",
            overall_finding=(
                "Swing findings could not be produced because scoring "
                "interpretation was unavailable."
            ),
            strengths=(),
            improvement_priorities=(),
            warnings=("missing_scoring_interpretation",),
        )

    if not isinstance(scoring_metrics, Mapping):
        scoring_metrics = {}

    status = interpretation.get("status")
    summary = interpretation.get("summary")
    strength_keys = interpretation.get("strengths")
    priority_keys = interpretation.get(
        "improvementPriorities"
    )
    warnings = interpretation.get("warnings")

    normalized_status = (
        status
        if isinstance(status, str)
        else "not_available"
    )

    normalized_summary = (
        summary
        if isinstance(summary, str)
        else (
            "Swing findings could not be summarized because the "
            "interpretation summary was unavailable."
        )
    )

    normalized_strength_keys = (
        [
            item
            for item in strength_keys
            if isinstance(item, str)
        ]
        if isinstance(strength_keys, list)
        else []
    )

    normalized_priority_keys = (
        [
            item
            for item in priority_keys
            if isinstance(item, str)
        ]
        if isinstance(priority_keys, list)
        else []
    )

    normalized_warnings = (
        tuple(
            item
            for item in warnings
            if isinstance(item, str)
        )
        if isinstance(warnings, list)
        else ()
    )

    return SwingFindings(
        status=normalized_status,
        overall_finding=normalized_summary,
        strengths=build_strength_findings(
            scoring_metrics=scoring_metrics,
            strength_metric_keys=normalized_strength_keys,
            metric_display_names=metric_display_names,
        ),
        improvement_priorities=build_improvement_findings(
            scoring_metrics=scoring_metrics,
            priority_metric_keys=normalized_priority_keys,
            metric_display_names=metric_display_names,
        ),
        warnings=normalized_warnings,
    )