from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.coaching.models import CoachResponse


AnalysisSection = Mapping[str, Any]


@dataclass(frozen=True)
class SwingAnalysisReport:
    """
    Complete deterministic output produced by the golf analysis
    pipeline, optionally enriched with validated coaching output.

    The deterministic analysis sections remain the source of truth.
    Coaching is generated afterward and attached as a downstream
    result.
    """

    source_video: Any
    inputs: AnalysisSection
    coordinate_system: AnalysisSection
    assumptions: AnalysisSection
    phase_frames: AnalysisSection
    reference_geometry: AnalysisSection
    metrics: AnalysisSection
    scoring: AnalysisSection
    findings: AnalysisSection
    recommendations: AnalysisSection
    summary: AnalysisSection
    coaching: CoachResponse | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the report using the public JSON structure.

        Top-level analysis sections are copied so callers cannot add
        or remove report fields by mutating the returned dictionaries.

        The coaching section is included only when validated coaching
        output has been attached. Deterministic-only reports therefore
        preserve their existing public structure.
        """

        result = {
            "sourceVideo": self.source_video,
            "inputs": dict(self.inputs),
            "coordinateSystem": dict(self.coordinate_system),
            "assumptions": dict(self.assumptions),
            "phaseFrames": dict(self.phase_frames),
            "referenceGeometry": dict(self.reference_geometry),
            "metrics": dict(self.metrics),
            "scoring": dict(self.scoring),
            "findings": dict(self.findings),
            "recommendations": dict(self.recommendations),
            "summary": dict(self.summary),
        }

        if self.coaching is not None:
            result["coaching"] = self.coaching.to_dict()

        return result