from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoachStrength:
    """
    Compact representation of one measured swing strength.

    Only information useful to a coaching provider is retained.
    """

    metric_key: str
    display_name: str
    score: float | None
    reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "displayName": self.display_name,
            "score": self.score,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CoachPriority:
    """
    One ordered coaching priority supplied to an AI provider.

    Guidance remains grounded in the deterministic recommendation
    catalog rather than being invented from raw pose measurements.
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
    caution: str | None

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
class CoachContext:
    """
    Provider-independent context for generating AI coaching language.

    This model intentionally excludes raw frames, landmarks, geometry,
    and low-level metric measurements. An AI provider receives only
    deterministic conclusions produced by the analysis engine.
    """

    status: str
    overall_score: float | None
    score_confidence: float | None
    score_coverage: float | None
    rating: str | None
    rating_label: str | None
    analysis_summary: str | None
    overall_finding: str | None
    primary_focus_metric_key: str | None
    strengths: tuple[CoachStrength, ...]
    priorities: tuple[CoachPriority, ...]
    warnings: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "overallScore": self.overall_score,
            "scoreConfidence": self.score_confidence,
            "scoreCoverage": self.score_coverage,
            "rating": self.rating,
            "ratingLabel": self.rating_label,
            "analysisSummary": self.analysis_summary,
            "overallFinding": self.overall_finding,
            "primaryFocusMetricKey": (
                self.primary_focus_metric_key
            ),
            "strengths": [
                strength.to_dict()
                for strength in self.strengths
            ],
            "priorities": [
                priority.to_dict()
                for priority in self.priorities
            ],
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class CoachResponse:
    """
    Structured coaching response returned by a future AI provider.

    Defining this model now prevents provider-specific response formats
    from leaking into the rest of the application.
    """

    status: str
    headline: str | None
    overview: str | None
    primary_focus: str | None
    action_steps: tuple[str, ...]
    encouragement: str | None
    disclaimer: str | None
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "headline": self.headline,
            "overview": self.overview,
            "primaryFocus": self.primary_focus,
            "actionSteps": list(self.action_steps),
            "encouragement": self.encouragement,
            "disclaimer": self.disclaimer,
            "warnings": list(self.warnings),
        }