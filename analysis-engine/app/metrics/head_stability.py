from __future__ import annotations

import math
from typing import Any


REQUIRED_REFERENCE_NAMES = (
    "addressReference",
    "topOfBackswing",
    "impactReference",
    "finishReference",
)

STABLE_IMPACT_MOVEMENT_MAXIMUM = 0.08
MODERATE_IMPACT_MOVEMENT_MAXIMUM = 0.14

STABLE_MAXIMUM_MOVEMENT_MAXIMUM = 0.12
MODERATE_MAXIMUM_MOVEMENT_MAXIMUM = 0.20


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def validate_frame_dimensions(
    frame_width: float,
    frame_height: float,
) -> None:
    if frame_width <= 0.0:
        raise ValueError(
            "Frame width must be greater than zero."
        )

    if frame_height <= 0.0:
        raise ValueError(
            "Frame height must be greater than zero."
        )


def get_head_center(
    reference: dict[str, Any],
) -> dict[str, Any] | None:
    geometry = reference.get("geometry")

    if not isinstance(geometry, dict):
        return None

    head_center = geometry.get("headCenter")

    if not isinstance(head_center, dict):
        return None

    return head_center


def calculate_head_movement(
    start_point: dict[str, Any] | None,
    end_point: dict[str, Any] | None,
    frame_width: float,
    frame_height: float,
) -> dict[str, float | None]:
    if start_point is None or end_point is None:
        return {
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    start_x = start_point.get("x")
    start_y = start_point.get("y")
    end_x = end_point.get("x")
    end_y = end_point.get("y")

    values = (
        start_x,
        start_y,
        end_x,
        end_y,
    )

    if not all(
        isinstance(value, (int, float))
        for value in values
    ):
        return {
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    delta_x_normalized = float(end_x) - float(start_x)
    delta_y_normalized = float(end_y) - float(start_y)

    distance_normalized = math.hypot(
        delta_x_normalized,
        delta_y_normalized,
    )

    delta_x_pixels = delta_x_normalized * frame_width
    delta_y_pixels = delta_y_normalized * frame_height

    distance_pixels = math.hypot(
        delta_x_pixels,
        delta_y_pixels,
    )

    return {
        "deltaXNormalized": round_value(
            delta_x_normalized
        ),
        "deltaYNormalized": round_value(
            delta_y_normalized
        ),
        "distanceNormalized": round_value(
            distance_normalized
        ),
        "deltaXPixels": round_value(delta_x_pixels),
        "deltaYPixels": round_value(delta_y_pixels),
        "distancePixels": round_value(distance_pixels),
    }


def calculate_maximum_head_movement(
    frames: list[dict[str, Any]],
    address_head_center: dict[str, Any] | None,
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    maximum_distance = -1.0
    maximum_result: dict[str, Any] | None = None

    for frame in frames:
        if not frame.get("poseDetected"):
            continue

        geometry = frame.get("geometry")

        if not isinstance(geometry, dict):
            continue

        current_head_center = geometry.get("headCenter")

        if not isinstance(current_head_center, dict):
            continue

        movement = calculate_head_movement(
            address_head_center,
            current_head_center,
            frame_width,
            frame_height,
        )

        distance_normalized = movement.get(
            "distanceNormalized"
        )

        if not isinstance(
            distance_normalized,
            (int, float),
        ):
            continue

        if distance_normalized > maximum_distance:
            maximum_distance = float(distance_normalized)

            maximum_result = {
                "frameIndex": frame.get("frameIndex"),
                "timestampSeconds": frame.get(
                    "timestampSeconds"
                ),
                **movement,
            }

    if maximum_result is None:
        return {
            "frameIndex": None,
            "timestampSeconds": None,
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    return maximum_result


def classify_movement(
    *,
    distance: float | None,
    stable_maximum: float,
    moderate_maximum: float,
    stable_message: str,
    moderate_message: str,
    excessive_message: str,
) -> dict[str, Any]:
    if distance is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": {
                "stableMaximum": stable_maximum,
                "moderateMaximum": moderate_maximum,
            },
            "message": (
                "Head movement could not be measured from "
                "the available pose geometry."
            ),
        }

    if distance <= stable_maximum:
        status = "within_target"
        message = stable_message
    elif distance <= moderate_maximum:
        status = "moderate_movement"
        message = moderate_message
    else:
        status = "excessive_movement"
        message = excessive_message

    return {
        "status": status,
        "value": round_value(distance),
        "targetRange": {
            "stableMaximum": stable_maximum,
            "moderateMaximum": moderate_maximum,
        },
        "message": message,
    }


def build_head_stability_metrics(
    references: dict[str, dict[str, Any]],
    frames: list[dict[str, Any]],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    validate_frame_dimensions(
        frame_width,
        frame_height,
    )

    for reference_name in REQUIRED_REFERENCE_NAMES:
        if reference_name not in references:
            raise ValueError(
                f"{reference_name} is missing."
            )

    address_reference = references["addressReference"]
    top_reference = references["topOfBackswing"]
    impact_reference = references["impactReference"]
    finish_reference = references["finishReference"]

    address_head_center = get_head_center(
        address_reference
    )

    measurements = {
        "addressToTop": calculate_head_movement(
            address_head_center,
            get_head_center(top_reference),
            frame_width,
            frame_height,
        ),
        "addressToImpact": calculate_head_movement(
            address_head_center,
            get_head_center(impact_reference),
            frame_width,
            frame_height,
        ),
        "addressToFinish": calculate_head_movement(
            address_head_center,
            get_head_center(finish_reference),
            frame_width,
            frame_height,
        ),
        "maximumMovement": (
            calculate_maximum_head_movement(
                frames=frames,
                address_head_center=address_head_center,
                frame_width=frame_width,
                frame_height=frame_height,
            )
        ),
    }

    measurable_distances = (
        measurements["addressToTop"][
            "distanceNormalized"
        ],
        measurements["addressToImpact"][
            "distanceNormalized"
        ],
        measurements["addressToFinish"][
            "distanceNormalized"
        ],
        measurements["maximumMovement"][
            "distanceNormalized"
        ],
    )

    available_measurement_count = sum(
        value is not None
        for value in measurable_distances
    )

    total_measurement_count = len(
        measurable_distances
    )

    completeness = (
        available_measurement_count
        / total_measurement_count
    )

    confidence = completeness

    required_references_have_pose = all(
        bool(references[name].get("poseDetected"))
        for name in REQUIRED_REFERENCE_NAMES
    )

    if not required_references_have_pose:
        confidence *= 0.75

    impact_finding = classify_movement(
        distance=measurements["addressToImpact"][
            "distanceNormalized"
        ],
        stable_maximum=(
            STABLE_IMPACT_MOVEMENT_MAXIMUM
        ),
        moderate_maximum=(
            MODERATE_IMPACT_MOVEMENT_MAXIMUM
        ),
        stable_message=(
            "Your head position remained stable from "
            "address through impact within the current "
            "prototype range."
        ),
        moderate_message=(
            "Your head moved moderately between address "
            "and impact. Review the movement direction and "
            "camera angle before treating it as a swing issue."
        ),
        excessive_message=(
            "Your head moved substantially between address "
            "and impact. Excessive movement may make it more "
            "difficult to return the club consistently."
        ),
    )

    maximum_finding = classify_movement(
        distance=measurements["maximumMovement"][
            "distanceNormalized"
        ],
        stable_maximum=(
            STABLE_MAXIMUM_MOVEMENT_MAXIMUM
        ),
        moderate_maximum=(
            MODERATE_MAXIMUM_MOVEMENT_MAXIMUM
        ),
        stable_message=(
            "Maximum measured head movement remained "
            "within the current prototype range."
        ),
        moderate_message=(
            "The swing contains moderate overall head "
            "movement. Review when the maximum movement "
            "occurs before drawing a coaching conclusion."
        ),
        excessive_message=(
            "The swing contains substantial head movement "
            "relative to the address position."
        ),
    )

    findings = {
        "impactStability": impact_finding,
        "maximumStability": maximum_finding,
    }

    issue_names = [
        finding_name
        for finding_name, finding in findings.items()
        if finding["status"]
        in {
            "moderate_movement",
            "excessive_movement",
        }
    ]

    unavailable_count = sum(
        finding["status"] == "not_available"
        for finding in findings.values()
    )

    if issue_names:
        classification = "needs_attention"
        feedback_status = "outside_target"
        primary_issue = issue_names[0]
        feedback_message = findings[
            primary_issue
        ]["message"]
    elif unavailable_count > 0:
        classification = "incomplete"
        feedback_status = "insufficient_data"
        primary_issue = None
        feedback_message = (
            "Some head-stability measurements were "
            "unavailable. Review pose visibility and the "
            "selected swing frames before relying on this "
            "result."
        )
    else:
        classification = "neutral"
        feedback_status = "within_target"
        primary_issue = None
        feedback_message = (
            "Measured head movement is within the current "
            "prototype stability ranges."
        )

    return {
        "referenceFrames": {
            "addressReference": {
                "frameIndex": address_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": address_reference.get(
                    "timestampSeconds"
                ),
                "poseDetected": bool(
                    address_reference.get("poseDetected")
                ),
            },
            "topOfBackswing": {
                "frameIndex": top_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": top_reference.get(
                    "timestampSeconds"
                ),
                "poseDetected": bool(
                    top_reference.get("poseDetected")
                ),
            },
            "impactReference": {
                "frameIndex": impact_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": impact_reference.get(
                    "timestampSeconds"
                ),
                "poseDetected": bool(
                    impact_reference.get("poseDetected")
                ),
            },
            "finishReference": {
                "frameIndex": finish_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": finish_reference.get(
                    "timestampSeconds"
                ),
                "poseDetected": bool(
                    finish_reference.get("poseDetected")
                ),
            },
        },
        "measurements": measurements,
        "measurementCompleteness": {
            "available": available_measurement_count,
            "total": total_measurement_count,
            "ratio": round_value(completeness),
        },
        "findings": findings,
        "classification": classification,
        "issueCount": len(issue_names),
        "primaryIssue": primary_issue,
        "confidence": round_value(confidence),
        "feedback": {
            "status": feedback_status,
            "message": feedback_message,
            "basis": (
                "Prototype 2D image-plane head-movement "
                "heuristics. Camera position, framing, and "
                "perspective can affect these measurements."
            ),
        },
    }