from __future__ import annotations

from typing import Any, Mapping


MINIMUM_REFERENCE_LINE_LENGTH_RATIO = 0.08


def has_metric_quality_club_evidence(
    detection: Mapping[str, Any],
) -> bool:
    """
    Return whether a detected club line has enough image evidence
    to support customer-facing club metrics.

    Short single-segment fallback detections remain useful to the
    detector for diagnostics, temporal continuity, and tracking, but
    they are not considered strong enough to support reference-phase
    measurements.

    Older or synthetic detection payloads that do not include
    candidate diagnostics remain usable for backward compatibility.
    """

    diagnostics = detection.get(
        "candidateDiagnostics"
    )

    if not isinstance(diagnostics, Mapping):
        return True

    evaluations = diagnostics.get(
        "candidateEvaluations"
    )

    if not isinstance(evaluations, list):
        return True

    selected_evaluation: Mapping[
        str,
        Any,
    ] | None = None

    for evaluation in evaluations:
        if (
            isinstance(evaluation, Mapping)
            and evaluation.get("selected") is True
        ):
            selected_evaluation = evaluation
            break

    if selected_evaluation is None:
        return True

    provenance = selected_evaluation.get(
        "provenance"
    )

    if not isinstance(provenance, Mapping):
        return True

    length_ratio_value = (
        selected_evaluation.get("lengthRatio")
    )

    length_ratio = (
        float(length_ratio_value)
        if isinstance(
            length_ratio_value,
            (int, float),
        )
        and not isinstance(
            length_ratio_value,
            bool,
        )
        else None
    )

    if length_ratio is None:
        return True

    is_short_single_fallback = (
        provenance.get("houghPass")
        == "fallback"
        and provenance.get("segmentSource")
        == "single"
        and length_ratio
        < MINIMUM_REFERENCE_LINE_LENGTH_RATIO
    )

    return not is_short_single_fallback