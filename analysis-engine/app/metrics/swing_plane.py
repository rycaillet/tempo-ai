from __future__ import annotations

from typing import Any, Mapping, Sequence
from app.metrics.club_evidence import (
    has_metric_quality_club_evidence,
)


REFERENCE_PHASES = (
    "address",
    "takeaway",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

MEASUREMENT_PHASE_NAMES = {
    "address": "address",
    "takeaway": "takeaway",
    "topOfBackswing": "topOfBackswing",
    "downswingStart": "downswingStart",
    "impactReference": "impact",
    "finishReference": "finish",
}


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def calculate_signed_axial_angle_change(
    start_angle: float | None,
    end_angle: float | None,
) -> float | None:
    if start_angle is None or end_angle is None:
        return None

    difference = end_angle - start_angle

    while difference > 90.0:
        difference -= 180.0

    while difference < -90.0:
        difference += 180.0

    return round_value(difference)


def select_reference_detection(
    frames: Sequence[Mapping[str, Any]],
    phase_name: str,
) -> Mapping[str, Any] | None:
    phase_frames = [
        frame
        for frame in frames
        if frame.get("phase") == phase_name
    ]

    if not phase_frames:
        return None

    for frame in phase_frames:
        if frame.get("isReferenceFrame") is True:
            return frame

    detected_frames = [
        frame
        for frame in phase_frames
        if frame.get("detected")
    ]

    if not detected_frames:
        return phase_frames[0]

    return min(
        detected_frames,
        key=lambda frame: (
            abs(
                int(frame.get("phaseOffsetFrames", 0))
            ),
            int(frame.get("frameIndex", 0)),
        ),
    )


def select_shaft_geometry(
    detection: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, str | None]:
    smoothed_line = detection.get(
        "smoothedShaftLine"
    )

    if isinstance(smoothed_line, Mapping):
        return smoothed_line, "smoothed"

    raw_line = detection.get("shaftLine")

    if isinstance(raw_line, Mapping):
        return raw_line, "raw"

    return None, None


def build_phase_measurement(
    detection: Mapping[str, Any] | None,
    *,
    phase_name: str,
) -> dict[str, Any]:
    if detection is None:
        return {
            "phase": phase_name,
            "frameIndex": None,
            "timestampSeconds": None,
            "available": False,
            "shaftAngleDegrees": None,
            "geometrySource": None,
            "detectionSource": "unavailable",
            "confidence": 0.0,
        }

    shaft_line, geometry_source = (
        select_shaft_geometry(detection)
    )

    angle_value = (
        shaft_line.get("angleDegrees")
        if shaft_line is not None
        else None
    )

    angle = (
        float(angle_value)
        if isinstance(angle_value, (int, float))
        else None
    )

    available = (
        bool(detection.get("detected"))
        and angle is not None
        and has_metric_quality_club_evidence(
            detection
        )
    )

    confidence_value = detection.get(
        "confidence",
        0.0,
    )

    confidence = (
        float(confidence_value)
        if isinstance(
            confidence_value,
            (int, float),
        )
        else 0.0
    )

    return {
        "phase": phase_name,
        "frameIndex": detection.get("frameIndex"),
        "timestampSeconds": detection.get(
            "timestampSeconds"
        ),
        "available": available,
        "shaftAngleDegrees": (
            round_value(angle)
            if available
            else None
        ),
        "geometrySource": (
            geometry_source
            if available
            else None
        ),
        "detectionSource": detection.get(
            "detectionSource",
            (
                "image"
                if detection.get("detected")
                else "unavailable"
            ),
        ),
        "confidence": round_value(
            confidence if available else 0.0
        ),
    }


def build_swing_plane_metrics(
    club_detection: Mapping[str, Any],
) -> dict[str, Any]:
    frames_value = club_detection.get("frames")

    frames: list[Mapping[str, Any]] = (
        [
            frame
            for frame in frames_value
            if isinstance(frame, Mapping)
        ]
        if isinstance(frames_value, list)
        else []
    )

    phase_measurements = {
        MEASUREMENT_PHASE_NAMES[phase_name]: (
            build_phase_measurement(
                select_reference_detection(
                    frames,
                    phase_name,
                ),
                phase_name=phase_name,
            )
        )
        for phase_name in REFERENCE_PHASES
    }

    angles = {
        name: measurement["shaftAngleDegrees"]
        for name, measurement
        in phase_measurements.items()
    }

    changes = {
        "addressToTakeawayDegrees": (
            calculate_signed_axial_angle_change(
                angles["address"],
                angles["takeaway"],
            )
        ),
        "takeawayToTopDegrees": (
            calculate_signed_axial_angle_change(
                angles["takeaway"],
                angles["topOfBackswing"],
            )
        ),
        "topToDownswingStartDegrees": (
            calculate_signed_axial_angle_change(
                angles["topOfBackswing"],
                angles["downswingStart"],
            )
        ),
        "downswingStartToImpactDegrees": (
            calculate_signed_axial_angle_change(
                angles["downswingStart"],
                angles["impact"],
            )
        ),
        "impactToFinishDegrees": (
            calculate_signed_axial_angle_change(
                angles["impact"],
                angles["finish"],
            )
        ),
        "topToImpactDegrees": (
            calculate_signed_axial_angle_change(
                angles["topOfBackswing"],
                angles["impact"],
            )
        ),
    }

    available_measurements = [
        measurement
        for measurement
        in phase_measurements.values()
        if measurement["available"]
    ]

    available_count = len(
        available_measurements
    )
    total_count = len(REFERENCE_PHASES)

    completeness = (
        available_count / total_count
    )

    average_detection_confidence = (
        sum(
            float(measurement["confidence"])
            for measurement
            in available_measurements
        )
        / available_count
        if available_count > 0
        else 0.0
    )

    confidence = (
        completeness
        * average_detection_confidence
    )

    smoothed_count = sum(
        measurement["geometrySource"]
        == "smoothed"
        for measurement in available_measurements
    )

    tracked_count = sum(
        measurement["detectionSource"]
        == "tracked"
        for measurement in available_measurements
    )

    if available_count == 0:
        classification = "incomplete"
        feedback_status = "insufficient_data"
        feedback_message = (
            "Swing-plane measurements were unavailable because "
            "no usable shaft geometry was found at the reference "
            "phases."
        )
        finding_status = "not_available"
    else:
        classification = "observed"
        feedback_status = "measurement_only"
        feedback_message = (
            "Camera-relative shaft angles were measured across "
            "the available swing phases."
        )
        finding_status = (
            "complete_trajectory"
            if available_count == total_count
            else "partial_trajectory"
        )

    findings = {
        "cameraRelativeSwingPlane": {
            "status": finding_status,
            "availablePhaseCount": available_count,
            "totalPhaseCount": total_count,
            "message": (
                feedback_message
                if available_count == 0
                else (
                    "The shaft trajectory is available across all "
                    "reference phases."
                    if available_count == total_count
                    else (
                        "The shaft trajectory is available for only "
                        "some reference phases."
                    )
                )
            ),
        }
    }

    return {
        "referenceFrames": {
            name: {
                "frameIndex": measurement[
                    "frameIndex"
                ],
                "timestampSeconds": measurement[
                    "timestampSeconds"
                ],
                "clubDetected": measurement[
                    "available"
                ],
                "detectionSource": measurement[
                    "detectionSource"
                ],
                "shaftGeometrySource": measurement[
                    "geometrySource"
                ],
            }
            for name, measurement
            in phase_measurements.items()
        },
        "measurements": {
            "phaseMeasurements": (
                phase_measurements
            ),
            "phaseChangesDegrees": changes,
            "smoothedReferenceCount": (
                smoothed_count
            ),
            "trackedReferenceCount": (
                tracked_count
            ),
            "averageDetectionConfidence": (
                round_value(
                    average_detection_confidence
                )
            ),
        },
        "measurementCompleteness": {
            "available": available_count,
            "total": total_count,
            "ratio": round_value(completeness),
        },
        "findings": findings,
        "classification": classification,
        "issueCount": 0,
        "primaryIssue": None,
        "confidence": round_value(confidence),
        "feedback": {
            "status": feedback_status,
            "message": feedback_message,
            "basis": (
                "This prototype measures the detected shaft line's "
                "two-dimensional camera-relative angle at selected "
                "swing phases. It prefers smoothed shaft geometry "
                "when available and otherwise uses the raw detected "
                "line. These measurements do not reconstruct a true "
                "three-dimensional swing plane and may vary with "
                "camera position, perspective, mirroring, blur, and "
                "detection accuracy."
            ),
        },
    }