from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimaryFocus:
    """
    Highest-priority measured area selected for coaching attention.

    This model intentionally contains only identifying and prioritization
    information. The full coaching guidance remains in Recommendation.
    """

    metric_key: str
    display_name: str
    severity: str

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "displayName": self.display_name,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class Recommendation:
    """
    Deterministic coaching guidance for one improvement finding.

    Recommendation content comes from the curated catalog while
    prioritization data comes from the swing findings.
    """

    metric_key: str
    display_name: str
    severity: str
    priority: int
    title: str
    summary: str
    focus: str
    rationale: str
    practice_cues: tuple[str, ...]
    caution: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "displayName": self.display_name,
            "severity": self.severity,
            "priority": self.priority,
            "title": self.title,
            "summary": self.summary,
            "focus": self.focus,
            "rationale": self.rationale,
            "practiceCues": list(self.practice_cues),
            "caution": self.caution,
        }


@dataclass(frozen=True)
class SwingRecommendations:
    """
    Complete deterministic recommendation output for one swing.

    The Recommendation Engine will produce this model from structured
    findings and the curated recommendation catalog.
    """

    status: str
    primary_focus: PrimaryFocus | None
    recommendations: tuple[Recommendation, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "primaryFocus": (
                self.primary_focus.to_dict()
                if self.primary_focus is not None
                else None
            ),
            "recommendations": [
                recommendation.to_dict()
                for recommendation in self.recommendations
            ],
            "warnings": list(self.warnings),
        }