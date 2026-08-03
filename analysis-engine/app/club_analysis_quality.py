from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REFERENCE_PHASE_NAMES = (
    "address",
    "takeaway",
    "topOfBackswing",
    "downswingStart",
    "impact",
    "finish",
)

LOW_REFERENCE_CONFIDENCE_THRESHOLD = 0.50
LIMITED_DETECTION_RATE_THRESHOLD = 0.75


def normalize_integer(
    value: Any,
) -> int:
    if isinstance(value, bool):
        return 0

    if isinstance(value, int):
        return max(0, value)

    return 0


def normalize_number(
    value: Any,
) -> float | None:
    if isinstance(value, bool):
        return None

    if not isinstance(value, (int, float)):
        return None

    return float(value)


def get_mapping(
    value: Any,
) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value

    return {}


def build_club_analysis_quality_summary(
    *,
    club_detection: Mapping[str, Any],
    swing_plane: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a compact quality summary for downstream UI and API use.

    The summary combines existing detector counts with the reference
    phase coverage and provenance already calculated by Swing Plane.
    It does not rerun detection or reinterpret club geometry.
    """

    detector_summary = get_mapping(
        club_detection.get("summary")
    )
    detector_frames = club_detection.get("frames")

    requested_frames = normalize_integer(
        detector_summary.get("requestedFrames")
    )
    processed_frames = normalize_integer(
        detector_summary.get("processedFrames")
    )
    detected_frames = normalize_integer(
        detector_summary.get("detectedFrames")
    )
    image_detected_frames = normalize_integer(
        detector_summary.get("imageDetectedFrames")
    )
    tracked_frames = normalize_integer(
        detector_summary.get("trackedFrames")
    )
    smoothed_frames = normalize_integer(
        detector_summary.get("smoothedFrames")
    )

    if (
        image_detected_frames == 0
        and detected_frames > 0
    ):
        image_detected_frames = max(
            0,
            detected_frames - tracked_frames,
        )

    detection_rate = normalize_number(
        detector_summary.get("detectionRate")
    )
    average_confidence = normalize_number(
        detector_summary.get("averageConfidence")
    )

    completeness = get_mapping(
        swing_plane.get("measurementCompleteness")
    )
    reference_available = normalize_integer(
        completeness.get("available")
    )
    reference_total = normalize_integer(
        completeness.get("total")
    )

    if reference_total == 0:
        reference_total = len(
            REFERENCE_PHASE_NAMES
        )

    measurements = get_mapping(
        swing_plane.get("measurements")
    )
    phase_measurements = get_mapping(
        measurements.get("phaseMeasurements")
    )

    unavailable_reference_phases: list[str] = []
    reference_confidences: list[float] = []

    for phase_name in REFERENCE_PHASE_NAMES:
        phase_measurement = get_mapping(
            phase_measurements.get(phase_name)
        )

        if not phase_measurement.get("available"):
            unavailable_reference_phases.append(
                phase_name
            )
            continue

        confidence = normalize_number(
            phase_measurement.get("confidence")
        )

        if confidence is not None:
            reference_confidences.append(
                confidence
            )

    minimum_reference_confidence = (
        min(reference_confidences)
        if reference_confidences
        else None
    )

    smoothed_reference_count = normalize_integer(
        measurements.get(
            "smoothedReferenceCount"
        )
    )
    tracked_reference_count = normalize_integer(
        measurements.get(
            "trackedReferenceCount"
        )
    )

    has_detector_input = (
        requested_frames > 0
        or processed_frames > 0
        or (
            isinstance(detector_frames, list)
            and bool(detector_frames)
        )
    )

    if not has_detector_input:
        status = "not_available"
    elif (
        reference_total > 0
        and reference_available
        == reference_total
    ):
        status = "complete"
    elif reference_available > 0:
        status = "partial"
    else:
        status = "insufficient"

    warnings: list[str] = []

    if status == "not_available":
        warnings.append(
            "club_detection_not_provided"
        )

    if unavailable_reference_phases:
        warnings.append(
            "missing_reference_phase_geometry"
        )

    if tracked_reference_count > 0:
        warnings.append(
            "tracked_reference_geometry_used"
        )

    if (
        minimum_reference_confidence
        is not None
        and minimum_reference_confidence
        < LOW_REFERENCE_CONFIDENCE_THRESHOLD
    ):
        warnings.append(
            "low_reference_confidence"
        )

    if (
        detection_rate is not None
        and detection_rate
        < LIMITED_DETECTION_RATE_THRESHOLD
    ):
        warnings.append(
            "limited_frame_detection_rate"
        )

    return {
        "status": status,
        "requestedFrames": requested_frames,
        "processedFrames": processed_frames,
        "detectedFrames": detected_frames,
        "imageDetectedFrames": (
            image_detected_frames
        ),
        "trackedFrames": tracked_frames,
        "smoothedFrames": smoothed_frames,
        "detectionRate": detection_rate,
        "averageConfidence": average_confidence,
        "referencePhasesAvailable": (
            reference_available
        ),
        "referencePhasesTotal": reference_total,
        "referencePhaseCompleteness": (
            round(
                reference_available
                / reference_total,
                6,
            )
            if reference_total > 0
            else 0.0
        ),
        "minimumReferenceConfidence": (
            round(
                minimum_reference_confidence,
                6,
            )
            if minimum_reference_confidence
            is not None
            else None
        ),
        "usesTrackedGeometry": (
            tracked_reference_count > 0
        ),
        "usesSmoothedGeometry": (
            smoothed_reference_count > 0
        ),
        "trackedReferenceCount": (
            tracked_reference_count
        ),
        "smoothedReferenceCount": (
            smoothed_reference_count
        ),
        "unavailableReferencePhases": (
            unavailable_reference_phases
        ),
        "warnings": warnings,
    }