from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


AnalysisSection = Mapping[str, Any]


@dataclass(frozen=True)
class SwingAnalysisReport:
    """
    Complete deterministic output produced by the golf analysis
    pipeline.

    The report acts as the stable aggregate passed to future systems
    such as insights, coaching, comparison, persistence, and API
    serialization.
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
    summary: AnalysisSection

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the report using the existing public JSON structure.

        Top-level sections are copied so callers cannot add or remove
        report fields by mutating the dictionaries returned here.
        """

        return {
            "sourceVideo": self.source_video,
            "inputs": dict(self.inputs),
            "coordinateSystem": dict(self.coordinate_system),
            "assumptions": dict(self.assumptions),
            "phaseFrames": dict(self.phase_frames),
            "referenceGeometry": dict(self.reference_geometry),
            "metrics": dict(self.metrics),
            "scoring": dict(self.scoring),
            "findings": dict(self.findings),
            "summary": dict(self.summary),
        }