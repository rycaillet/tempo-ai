from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrengthFinding:
    metric_key: str
    display_name: str
    score: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "displayName": self.display_name,
            "score": self.score,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ImprovementFinding:
    metric_key: str
    display_name: str
    score: float
    severity: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "displayName": self.display_name,
            "score": self.score,
            "severity": self.severity,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SwingFindings:
    status: str
    overall_finding: str
    strengths: tuple[StrengthFinding, ...]
    improvement_priorities: tuple[ImprovementFinding, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "overallFinding": self.overall_finding,
            "strengths": [
                finding.to_dict()
                for finding in self.strengths
            ],
            "improvementPriorities": [
                finding.to_dict()
                for finding in self.improvement_priorities
            ],
            "warnings": list(self.warnings),
        }