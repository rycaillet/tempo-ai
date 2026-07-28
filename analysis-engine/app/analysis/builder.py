from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.analysis.report import SwingAnalysisReport


def require_analysis_section(
    section_name: str,
    section: Mapping[str, Any],
) -> Mapping[str, Any]:
    """
    Validate a required report section before constructing the
    aggregate report.
    """

    if not isinstance(section, Mapping):
        raise TypeError(
            f"Analysis report section must be a mapping: "
            f"{section_name}"
        )

    return section


def build_swing_analysis_report(
    *,
    source_video: Any,
    inputs: Mapping[str, Any],
    coordinate_system: Mapping[str, Any],
    assumptions: Mapping[str, Any],
    phase_frames: Mapping[str, Any],
    reference_geometry: Mapping[str, Any],
    metrics: Mapping[str, Any],
    scoring: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> SwingAnalysisReport:
    """
    Build the complete domain report for one analyzed golf swing.

    This builder intentionally does not calculate metrics or alter
    analysis values. It establishes the stable boundary between the
    deterministic pipeline and downstream consumers.
    """

    return SwingAnalysisReport(
        source_video=source_video,
        inputs=require_analysis_section("inputs", inputs),
        coordinate_system=require_analysis_section(
            "coordinate_system",
            coordinate_system,
        ),
        assumptions=require_analysis_section(
            "assumptions",
            assumptions,
        ),
        phase_frames=require_analysis_section(
            "phase_frames",
            phase_frames,
        ),
        reference_geometry=require_analysis_section(
            "reference_geometry",
            reference_geometry,
        ),
        metrics=require_analysis_section("metrics", metrics),
        scoring=require_analysis_section("scoring", scoring),
        summary=require_analysis_section("summary", summary),
    )