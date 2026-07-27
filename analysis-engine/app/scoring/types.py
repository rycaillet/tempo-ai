from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ClassificationScore = float | None


@dataclass(frozen=True)
class ScoreProfile:
    name: str
    version: str
    classification_scores: Mapping[
        str,
        Mapping[str, ClassificationScore],
    ]

    def get_classification_score(
        self,
        metric_key: str,
        classification: str,
    ) -> ClassificationScore:
        metric_scores = self.classification_scores.get(metric_key)

        if metric_scores is None:
            return None

        return metric_scores.get(classification)


@dataclass(frozen=True)
class MetricScore:
    metric_key: str
    classification: str | None
    status: str
    reason: str | None
    raw_score: float | None
    confidence: float | None
    configured_weight: float
    normalized_weight: float
    weighted_contribution: float

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "status": self.status,
            "reason": self.reason,
            "rawScore": self.raw_score,
            "confidence": self.confidence,
            "configuredWeight": self.configured_weight,
            "normalizedWeight": self.normalized_weight,
            "weightedContribution": self.weighted_contribution,
        }


@dataclass(frozen=True)
class SwingScore:
    profile_name: str
    profile_version: str
    overall_score: float | None
    score_confidence: float | None
    score_coverage: float
    weighted_total: float | None
    available_weight: float
    possible_weight: float
    metrics: Mapping[str, MetricScore]

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": {
                "name": self.profile_name,
                "version": self.profile_version,
            },
            "overallScore": self.overall_score,
            "scoreConfidence": self.score_confidence,
            "scoreCoverage": self.score_coverage,
            "weightedTotal": self.weighted_total,
            "availableWeight": self.available_weight,
            "possibleWeight": self.possible_weight,
            "metrics": {
                metric_key: metric_score.to_dict()
                for metric_key, metric_score in self.metrics.items()
            },
        }