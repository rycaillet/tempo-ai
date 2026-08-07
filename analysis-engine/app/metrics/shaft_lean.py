from __future__ import annotations

import math
from typing import Any, Mapping


IMPACT_PHASE_NAME = "impactReference"

VERTICAL_TOLERANCE_DEGREES = 5.0
MINIMUM_ENDPOINT_SEPARATION_PIXELS = 1.0


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def calculate_point_distance(
    first_point: Mapping[str, Any],
    second_point: Mapping[str, Any],
) -> float | None:
    first_x = first_point.get("x")
    first_y = first_point.get("y")
    second_x = second_point.get("x")
    second_y = second_point.get("y")

    values = (
        first_x,
        first_y,
        second_x,
        second_y,
    )

    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        for value in values
    ):
        return None

    return math.hypot(
        float(second_x) - float(first_x),
        float(second_y) - float(first_y),
    )


def get_club_detection_frames(
    club_detection: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    frames = club_detection.get("frames")

    if not isinstance(frames, list):
        raise ValueError(
            "Club detection data must contain a frames list."
        )

    return [
        frame
        for frame in frames
        if isinstance(frame, Mapping)
    ]


def get_phase_detection(
    club_detection: Mapping[str, Any],
    phase_name: str,
) -> Mapping[str, Any] | None:
    frames = get_club_detection_frames(
        club_detection
    )

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

    if len(phase_frames) == 1:
        return phase_frames[0]

    return None


def get_valid_point(
    value: Any,
) -> dict[str, float] | None:
    if not isinstance(value, Mapping):
        return None

    x_value = value.get("x")
    y_value = value.get("y")

    if (
        isinstance(x_value, bool)
        or not isinstance(x_value, (int, float))
        or not math.isfinite(float(x_value))
    ):
        return None

    if (
        isinstance(y_value, bool)
        or not isinstance(y_value, (int, float))
        or not math.isfinite(float(y_value))
    ):
        return None

    return {
        "x": float(x_value),
        "y": float(y_value),
    }


def orient_shaft_line(
    shaft_line: Mapping[str, Any],
    hand_anchor: Mapping[str, Any],
) -> dict[str, Any] | None:
    start = get_valid_point(
        shaft_line.get("start")
    )
    end = get_valid_point(
        shaft_line.get("end")
    )
    anchor = get_valid_point(hand_anchor)

    if (
        start is None
        or end is None
        or anchor is None
    ):
        return None

    line_length = calculate_point_distance(
        start,
        end,
    )

    if (
        line_length is None
        or line_length
        < MINIMUM_ENDPOINT_SEPARATION_PIXELS
    ):
        return None

    start_distance = calculate_point_distance(
        anchor,
        start,
    )
    end_distance = calculate_point_distance(
        anchor,
        end,
    )

    if (
        start_distance is None
        or end_distance is None
    ):
        return None

    if start_distance <= end_distance:
        grip_endpoint = start
        clubhead_endpoint = end
        grip_distance = start_distance
        clubhead_distance = end_distance
    else:
        grip_endpoint = end
        clubhead_endpoint = start
        grip_distance = end_distance
        clubhead_distance = start_distance

    distance_total = (
        grip_distance + clubhead_distance
    )

    orientation_confidence = (
        abs(
            clubhead_distance - grip_distance
        )
        / distance_total
        if distance_total > 0.0
        else 0.0
    )

    return {
        "gripEndpoint": grip_endpoint,
        "clubheadEndpoint": clubhead_endpoint,
        "lineLengthPixels": round_value(
            line_length,
            3,
        ),
        "gripDistanceFromHandsPixels": (
            round_value(
                grip_distance,
                3,
            )
        ),
        "clubheadDistanceFromHandsPixels": (
            round_value(
                clubhead_distance,
                3,
            )
        ),
        "orientationConfidence": round_value(
            orientation_confidence
        ),
    }


def calculate_signed_lean_from_vertical(
    grip_endpoint: Mapping[str, Any],
    clubhead_endpoint: Mapping[str, Any],
) -> float | None:
    grip = get_valid_point(grip_endpoint)
    clubhead = get_valid_point(
        clubhead_endpoint
    )

    if grip is None or clubhead is None:
        return None

    delta_x = (
        clubhead["x"] - grip["x"]
    )
    delta_y = (
        clubhead["y"] - grip["y"]
    )

    if math.hypot(delta_x, delta_y) <= 0.0:
        return None

    absolute_lean = math.degrees(
        math.atan2(
            abs(delta_x),
            abs(delta_y),
        )
    )

    if abs(delta_x) <= 0.000001:
        return 0.0

    return math.copysign(
        absolute_lean,
        delta_x,
    )


def classify_camera_relative_lean(
    signed_lean_degrees: float | None,
) -> dict[str, Any]:
    target_range = {
        "verticalToleranceDegrees": (
            VERTICAL_TOLERANCE_DEGREES
        ),
    }

    if signed_lean_degrees is None:
        return {
            "status": "not_available",
            "value": None,
            "direction": None,
            "targetRange": target_range,
            "message": (
                "Impact shaft lean could not be measured "
                "from the available club detection."
            ),
        }

    absolute_lean = abs(
        signed_lean_degrees
    )

    if (
        absolute_lean
        <= VERTICAL_TOLERANCE_DEGREES
    ):
        status = "approximately_vertical"
        direction = "vertical"
        message = (
            "The detected shaft is approximately vertical "
            "in the impact reference frame."
        )
    elif signed_lean_degrees < 0.0:
        status = "leans_image_left"
        direction = "image_left"
        message = (
            "The detected clubhead is positioned toward "
            "image-left relative to the grip at impact."
        )
    else:
        status = "leans_image_right"
        direction = "image_right"
        message = (
            "The detected clubhead is positioned toward "
            "image-right relative to the grip at impact."
        )

    return {
        "status": status,
        "value": round_value(
            signed_lean_degrees
        ),
        "absoluteValue": round_value(
            absolute_lean
        ),
        "direction": direction,
        "targetRange": target_range,
        "message": message,
    }



def select_metric_shaft_line(
    impact_detection: Mapping[str, Any],
) -> tuple[Mapping[str, Any] | None, str | None]:
    smoothed_shaft_line = impact_detection.get(
        "smoothedShaftLine"
    )

    if isinstance(smoothed_shaft_line, Mapping):
        return smoothed_shaft_line, "smoothed"

    raw_shaft_line = impact_detection.get(
        "shaftLine"
    )

    if isinstance(raw_shaft_line, Mapping):
        return raw_shaft_line, "raw"

    return None, None


def build_unavailable_result(
    impact_detection: Mapping[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    frame_index = (
        impact_detection.get("frameIndex")
        if impact_detection is not None
        else None
    )
    timestamp_seconds = (
        impact_detection.get(
            "timestampSeconds"
        )
        if impact_detection is not None
        else None
    )
    detection_confidence = (
        impact_detection.get("confidence")
        if impact_detection is not None
        else None
    )

    finding = classify_camera_relative_lean(
        None
    )

    return {
        "referenceFrame": {
            "name": IMPACT_PHASE_NAME,
            "frameIndex": frame_index,
            "timestampSeconds": (
                timestamp_seconds
            ),
            "clubDetected": False,
        },
        "measurements": {
            "signedLeanFromVerticalDegrees": None,
            "absoluteLeanFromVerticalDegrees": None,
            "cameraRelativeDirection": None,
            "gripEndpoint": None,
            "clubheadEndpoint": None,
            "lineLengthPixels": None,
            "gripDistanceFromHandsPixels": None,
            "clubheadDistanceFromHandsPixels": None,
            "orientationConfidence": None,
            "shaftGeometrySource": None,
            "clubDetectionConfidence": (
                round_value(
                    float(detection_confidence)
                )
                if isinstance(
                    detection_confidence,
                    (int, float),
                )
                and not isinstance(
                    detection_confidence,
                    bool,
                )
                else None
            ),
        },
        "measurementCompleteness": {
            "available": 0,
            "total": 1,
            "ratio": 0.0,
        },
        "findings": {
            "impactShaftLean": finding,
        },
        "classification": "incomplete",
        "issueCount": 0,
        "primaryIssue": None,
        "confidence": 0.0,
        "feedback": {
            "status": "insufficient_data",
            "message": reason,
            "basis": (
                "Shaft lean is measured from the detected "
                "club shaft in the two-dimensional impact "
                "reference frame. Image direction is retained "
                "without claiming that it represents forward "
                "or backward lean."
            ),
        },
    }


def build_shaft_lean_metrics(
    club_detection: Mapping[str, Any],
) -> dict[str, Any]:
    impact_detection = get_phase_detection(
        club_detection,
        IMPACT_PHASE_NAME,
    )

    if impact_detection is None:
        return build_unavailable_result(
            None,
            (
                "Club detection did not contain an "
                "impactReference frame."
            ),
        )

    if not bool(
        impact_detection.get("detected")
    ):
        failure_reason = impact_detection.get(
            "failureReason"
        )

        reason = (
            str(failure_reason)
            if isinstance(
                failure_reason,
                str,
            )
            and failure_reason
            else (
                "The golf shaft was not reliably detected "
                "in the impact reference frame."
            )
        )

        return build_unavailable_result(
            impact_detection,
            reason,
        )

    hand_anchor = impact_detection.get(
        "handAnchor"
    )
    shaft_line, shaft_geometry_source = (
        select_metric_shaft_line(
            impact_detection
        )
    )

    if not isinstance(hand_anchor, Mapping):
        return build_unavailable_result(
            impact_detection,
            (
                "The impact club detection is missing "
                "a valid hand anchor."
            ),
        )

    if not isinstance(shaft_line, Mapping):
        return build_unavailable_result(
            impact_detection,
            (
                "The impact club detection is missing "
                "both a valid smoothed shaft line and "
                "a valid raw shaft line."
            ),
        )

    oriented_line = orient_shaft_line(
        shaft_line,
        hand_anchor,
    )

    if oriented_line is None:
        return build_unavailable_result(
            impact_detection,
            (
                "The detected impact shaft line could "
                "not be oriented relative to the hands."
            ),
        )

    signed_lean = (
        calculate_signed_lean_from_vertical(
            oriented_line["gripEndpoint"],
            oriented_line["clubheadEndpoint"],
        )
    )

    if signed_lean is None:
        return build_unavailable_result(
            impact_detection,
            (
                "Impact shaft lean could not be calculated "
                "from the oriented shaft endpoints."
            ),
        )

    finding = classify_camera_relative_lean(
        signed_lean
    )

    detection_confidence_value = (
        impact_detection.get("confidence")
    )

    detection_confidence = (
        max(
            0.0,
            min(
                1.0,
                float(
                    detection_confidence_value
                ),
            ),
        )
        if isinstance(
            detection_confidence_value,
            (int, float),
        )
        and not isinstance(
            detection_confidence_value,
            bool,
        )
        and math.isfinite(
            float(detection_confidence_value)
        )
        else 0.0
    )

    orientation_confidence_value = (
        oriented_line[
            "orientationConfidence"
        ]
    )

    orientation_confidence = (
        float(orientation_confidence_value)
        if isinstance(
            orientation_confidence_value,
            (int, float),
        )
        else 0.0
    )

    confidence = (
        detection_confidence
        * (
            0.5
            + 0.5
            * orientation_confidence
        )
    )

    absolute_lean = abs(signed_lean)

    return {
        "referenceFrame": {
            "name": IMPACT_PHASE_NAME,
            "frameIndex": impact_detection.get(
                "frameIndex"
            ),
            "timestampSeconds": (
                impact_detection.get(
                    "timestampSeconds"
                )
            ),
            "clubDetected": True,
        },
        "measurements": {
            "signedLeanFromVerticalDegrees": (
                round_value(signed_lean)
            ),
            "absoluteLeanFromVerticalDegrees": (
                round_value(absolute_lean)
            ),
            "cameraRelativeDirection": (
                finding["direction"]
            ),
            "gripEndpoint": oriented_line[
                "gripEndpoint"
            ],
            "clubheadEndpoint": oriented_line[
                "clubheadEndpoint"
            ],
            "lineLengthPixels": oriented_line[
                "lineLengthPixels"
            ],
            "gripDistanceFromHandsPixels": (
                oriented_line[
                    "gripDistanceFromHandsPixels"
                ]
            ),
            "clubheadDistanceFromHandsPixels": (
                oriented_line[
                    "clubheadDistanceFromHandsPixels"
                ]
            ),
            "orientationConfidence": (
                orientation_confidence_value
            ),
            "shaftGeometrySource": (
                shaft_geometry_source
            ),
            "clubDetectionConfidence": (
                round_value(
                    detection_confidence
                )
            ),
        },
        "measurementCompleteness": {
            "available": 1,
            "total": 1,
            "ratio": 1.0,
        },
        "findings": {
            "impactShaftLean": finding,
        },
        "classification": "observed",
        "issueCount": 0,
        "primaryIssue": None,
        "confidence": round_value(
            confidence
        ),
        "feedback": {
            "status": "measurement_only",
            "message": finding["message"],
            "basis": (
                "This prototype measures the selected shaft "
                "geometry's two-dimensional direction relative "
                "to image "
                "vertical at impact. Negative values lean toward "
                "image-left and positive values lean toward "
                "image-right. Camera position, video mirroring, "
                "perspective, shaft blur, and line-detection "
                "accuracy can affect the result. The current "
                "measurement does not yet label the direction "
                "as forward or backward shaft lean."
            ),
        },
    }