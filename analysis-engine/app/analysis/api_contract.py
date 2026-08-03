from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.analysis.versioning import (
    build_execution_metadata,
)
from app.coaching.context import build_coach_context


ANALYSIS_API_VERSION = "1.0.0"

METRIC_DISPLAY_NAMES = {
    "tempo": "Tempo",
    "addressPosture": "Address posture",
    "impactPosition": "Impact position",
    "earlyExtension": "Early extension",
    "headStability": "Head stability",
    "weightShift": "Weight shift",
    "rotation": "Rotation",
    "shaftLean": "Shaft lean",
    "swingPlane": "Swing plane",
}


def get_mapping(
    value: Any,
) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value

    return {}


def get_list(
    value: Any,
) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


def normalize_string(
    value: Any,
) -> str | None:
    if isinstance(value, str) and value:
        return value

    return None


def normalize_number(
    value: Any,
) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    return None


def build_metric_card(
    *,
    metric_key: str,
    metric_result: Mapping[str, Any],
    scoring_result: Mapping[str, Any],
) -> dict[str, Any]:
    feedback = get_mapping(
        metric_result.get("feedback")
    )
    completeness = get_mapping(
        metric_result.get("measurementCompleteness")
    )

    return {
        "metricKey": metric_key,
        "displayName": METRIC_DISPLAY_NAMES.get(
            metric_key,
            metric_key,
        ),
        "classification": normalize_string(
            metric_result.get("classification")
        ),
        "confidence": normalize_number(
            metric_result.get("confidence")
        ),
        "measurementCompleteness": normalize_number(
            completeness.get("ratio")
        ),
        "feedbackStatus": normalize_string(
            feedback.get("status")
        ),
        "deliveryStatus": normalize_string(
            feedback.get("deliveryStatus")
        ),
        "scoreStatus": normalize_string(
            scoring_result.get("status")
        ),
        "score": normalize_number(
            scoring_result.get("rawScore")
        ),
        "weightedScore": normalize_number(
            scoring_result.get("weightedScore")
        ),
    }


def build_metric_cards(
    report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    metrics = get_mapping(report.get("metrics"))
    scoring = get_mapping(report.get("scoring"))
    scoring_metrics = get_mapping(
        scoring.get("metrics")
    )

    cards: list[dict[str, Any]] = []

    for metric_key in METRIC_DISPLAY_NAMES:
        metric_result = get_mapping(
            metrics.get(metric_key)
        )

        if not metric_result:
            continue

        cards.append(
            build_metric_card(
                metric_key=metric_key,
                metric_result=metric_result,
                scoring_result=get_mapping(
                    scoring_metrics.get(metric_key)
                ),
            )
        )

    return cards


def build_source_summary(
    *,
    report: Mapping[str, Any],
    video_path: str,
    handedness: str,
) -> dict[str, Any]:
    return {
        "videoPath": video_path,
        "sourceVideo": report.get("sourceVideo"),
        "handedness": handedness,
    }


def build_score_summary(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    scoring = get_mapping(report.get("scoring"))
    interpretation = get_mapping(
        scoring.get("interpretation")
    )

    return {
        "overallScore": normalize_number(
            scoring.get("overallScore")
        ),
        "confidence": normalize_number(
            scoring.get("scoreConfidence")
        ),
        "coverage": normalize_number(
            scoring.get("scoreCoverage")
        ),
        "rating": normalize_string(
            interpretation.get("rating")
        ),
        "ratingLabel": normalize_string(
            interpretation.get("ratingLabel")
        ),
        "status": normalize_string(
            interpretation.get("status")
        ),
        "summary": normalize_string(
            interpretation.get("summary")
        ),
    }


def build_findings_summary(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    findings = get_mapping(report.get("findings"))

    return {
        "status": normalize_string(
            findings.get("status")
        ),
        "overallFinding": normalize_string(
            findings.get("overallFinding")
        ),
        "strengths": [
            dict(item)
            for item in get_list(
                findings.get("strengths")
            )
            if isinstance(item, Mapping)
        ],
        "improvementPriorities": [
            dict(item)
            for item in get_list(
                findings.get(
                    "improvementPriorities"
                )
            )
            if isinstance(item, Mapping)
        ],
        "warnings": [
            item
            for item in get_list(
                findings.get("warnings")
            )
            if isinstance(item, str)
        ],
    }


def build_recommendation_summary(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    recommendations = get_mapping(
        report.get("recommendations")
    )
    primary_focus = recommendations.get(
        "primaryFocus"
    )

    return {
        "status": normalize_string(
            recommendations.get("status")
        ),
        "primaryFocus": (
            dict(primary_focus)
            if isinstance(primary_focus, Mapping)
            else None
        ),
        "items": [
            dict(item)
            for item in get_list(
                recommendations.get(
                    "recommendations"
                )
            )
            if isinstance(item, Mapping)
        ],
        "warnings": [
            item
            for item in get_list(
                recommendations.get("warnings")
            )
            if isinstance(item, str)
        ],
    }


def build_club_metric_details(
    report: Mapping[str, Any],
) -> dict[str, Any]:
    metrics = get_mapping(report.get("metrics"))
    shaft_lean = get_mapping(
        metrics.get("shaftLean")
    )
    swing_plane = get_mapping(
        metrics.get("swingPlane")
    )

    shaft_measurements = get_mapping(
        shaft_lean.get("measurements")
    )
    swing_measurements = get_mapping(
        swing_plane.get("measurements")
    )

    return {
        "shaftLean": {
            "classification": normalize_string(
                shaft_lean.get("classification")
            ),
            "confidence": normalize_number(
                shaft_lean.get("confidence")
            ),
            "signedLeanFromVerticalDegrees": (
                normalize_number(
                    shaft_measurements.get(
                        "signedLeanFromVerticalDegrees"
                    )
                )
            ),
            "cameraRelativeDirection": (
                normalize_string(
                    shaft_measurements.get(
                        "cameraRelativeDirection"
                    )
                )
            ),
            "geometrySource": normalize_string(
                shaft_measurements.get(
                    "shaftGeometrySource"
                )
            ),
        },
        "swingPlane": {
            "classification": normalize_string(
                swing_plane.get("classification")
            ),
            "confidence": normalize_number(
                swing_plane.get("confidence")
            ),
            "measurementCompleteness": (
                normalize_number(
                    get_mapping(
                        swing_plane.get(
                            "measurementCompleteness"
                        )
                    ).get("ratio")
                )
            ),
            "phaseChangesDegrees": dict(
                get_mapping(
                    swing_measurements.get(
                        "phaseChangesDegrees"
                    )
                )
            ),
            "smoothedReferenceCount": (
                swing_measurements.get(
                    "smoothedReferenceCount"
                )
            ),
            "trackedReferenceCount": (
                swing_measurements.get(
                    "trackedReferenceCount"
                )
            ),
        },
    }


def build_analysis_api_contract(
    *,
    report: Mapping[str, Any],
    video_path: str,
    handedness: str,
    artifacts: Mapping[str, Any],
    processed_at: str | None = None,
    duration_milliseconds: float | None = None,
) -> dict[str, Any]:
    """
    Build the stable backend-facing TempoAI analysis contract.

    The detailed deterministic report remains the internal source of
    truth. This payload intentionally exposes only fields expected by
    backend persistence and frontend presentation layers.
    """

    scoring = get_mapping(report.get("scoring"))
    interpretation = get_mapping(
        scoring.get("interpretation")
    )
    findings = get_mapping(report.get("findings"))
    recommendations = get_mapping(
        report.get("recommendations")
    )
    summary = get_mapping(report.get("summary"))

    coach_context = build_coach_context(report)
    coach_context_payload = coach_context.to_dict()

    coaching = report.get("coaching")

    engine = dict(
        get_mapping(
            summary.get("analysisEngine")
        )
    )

    if (
        processed_at is not None
        and duration_milliseconds is not None
    ):
        engine.update(
            build_execution_metadata(
                processed_at=processed_at,
                duration_milliseconds=(
                    duration_milliseconds
                ),
            )
        )

    status = (
        "ready"
        if (
            interpretation.get("status") == "ready"
            and findings.get("status") == "ready"
            and recommendations.get("status")
            == "ready"
        )
        else "partial"
    )

    return {
        "contractVersion": ANALYSIS_API_VERSION,
        "engine": engine,
        "status": status,
        "source": build_source_summary(
            report=report,
            video_path=video_path,
            handedness=handedness,
        ),
        "score": build_score_summary(report),
        "findings": build_findings_summary(report),
        "recommendations": (
            build_recommendation_summary(report)
        ),
        "metrics": build_metric_cards(report),
        "clubMetrics": build_club_metric_details(
            report
        ),
        "clubAnalysisQuality": dict(
            get_mapping(
                summary.get(
                    "clubAnalysisQuality"
                )
            )
        ),
        "observations": get_list(
            coach_context_payload.get(
                "observations"
            )
        ),
        "warnings": get_list(
            coach_context_payload.get("warnings")
        ),
        "limitations": get_list(
            coach_context_payload.get(
                "limitations"
            )
        ),
        "coaching": (
            dict(coaching)
            if isinstance(coaching, Mapping)
            else None
        ),
        "artifacts": {
            key: value
            for key, value in artifacts.items()
            if isinstance(value, str)
        },
    }