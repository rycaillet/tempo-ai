from __future__ import annotations

from typing import Any


REQUIRED_REFERENCE_NAMES = (
    "addressReference",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

MINIMUM_MEANINGFUL_SHIFT = 0.01

MINIMUM_BACKSWING_LOAD = 0.015
MAXIMUM_BACKSWING_LOAD = 0.10

MINIMUM_TRANSITION_TRANSFER = 0.02
MAXIMUM_TRANSITION_TRANSFER = 0.16

MAXIMUM_ADDRESS_TO_IMPACT_SHIFT = 0.16
MAXIMUM_IMPACT_TO_FINISH_SHIFT = 0.20


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


def get_hip_center(
    reference: dict[str, Any],
) -> dict[str, Any] | None:
    geometry = reference.get("geometry")

    if not isinstance(geometry, dict):
        return None

    hip_center = geometry.get("hipCenter")

    if not isinstance(hip_center, dict):
        return None

    return hip_center


def classify_horizontal_direction(
    delta_x_normalized: float | None,
) -> str | None:
    if delta_x_normalized is None:
        return None

    if abs(delta_x_normalized) < MINIMUM_MEANINGFUL_SHIFT:
        return "stationary"

    if delta_x_normalized < 0.0:
        return "left"

    return "right"


def calculate_lateral_shift(
    start_point: dict[str, Any] | None,
    end_point: dict[str, Any] | None,
    frame_width: float,
) -> dict[str, float | str | None]:
    if start_point is None or end_point is None:
        return {
            "deltaXNormalized": None,
            "absoluteDeltaXNormalized": None,
            "deltaXPixels": None,
            "absoluteDeltaXPixels": None,
            "direction": None,
        }

    start_x = start_point.get("x")
    end_x = end_point.get("x")

    if not isinstance(start_x, (int, float)):
        return {
            "deltaXNormalized": None,
            "absoluteDeltaXNormalized": None,
            "deltaXPixels": None,
            "absoluteDeltaXPixels": None,
            "direction": None,
        }

    if not isinstance(end_x, (int, float)):
        return {
            "deltaXNormalized": None,
            "absoluteDeltaXNormalized": None,
            "deltaXPixels": None,
            "absoluteDeltaXPixels": None,
            "direction": None,
        }

    delta_x_normalized = float(end_x) - float(start_x)
    absolute_delta_x_normalized = abs(
        delta_x_normalized
    )

    delta_x_pixels = delta_x_normalized * frame_width
    absolute_delta_x_pixels = abs(delta_x_pixels)

    return {
        "deltaXNormalized": round_value(
            delta_x_normalized
        ),
        "absoluteDeltaXNormalized": round_value(
            absolute_delta_x_normalized
        ),
        "deltaXPixels": round_value(delta_x_pixels),
        "absoluteDeltaXPixels": round_value(
            absolute_delta_x_pixels
        ),
        "direction": classify_horizontal_direction(
            delta_x_normalized
        ),
    }


def classify_backswing_load(
    shift: dict[str, Any],
) -> dict[str, Any]:
    distance = shift.get(
        "absoluteDeltaXNormalized"
    )

    if not isinstance(distance, (int, float)):
        return {
            "status": "not_available",
            "value": None,
            "direction": None,
            "targetRange": {
                "minimum": MINIMUM_BACKSWING_LOAD,
                "maximum": MAXIMUM_BACKSWING_LOAD,
            },
            "message": (
                "Backswing hip movement could not be "
                "measured from the available pose geometry."
            ),
        }

    direction = shift.get("direction")

    if distance < MINIMUM_BACKSWING_LOAD:
        status = "limited_shift"
        message = (
            "Very little lateral hip movement was measured "
            "between address and the top of the backswing."
        )
    elif distance <= MAXIMUM_BACKSWING_LOAD:
        status = "within_target"
        message = (
            "Backswing lateral hip movement is within the "
            "current prototype range."
        )
    else:
        status = "excessive_shift"
        message = (
            "The hips moved substantially away from their "
            "address position during the backswing."
        )

    return {
        "status": status,
        "value": round_value(float(distance)),
        "direction": direction,
        "targetRange": {
            "minimum": MINIMUM_BACKSWING_LOAD,
            "maximum": MAXIMUM_BACKSWING_LOAD,
        },
        "message": message,
    }


def movements_reverse_direction(
    first_delta: float,
    second_delta: float,
) -> bool:
    if abs(first_delta) < MINIMUM_MEANINGFUL_SHIFT:
        return False

    if abs(second_delta) < MINIMUM_MEANINGFUL_SHIFT:
        return False

    return (
        first_delta < 0.0 < second_delta
        or second_delta < 0.0 < first_delta
    )


def classify_transition_transfer(
    address_to_top: dict[str, Any],
    top_to_impact: dict[str, Any],
) -> dict[str, Any]:
    backswing_delta = address_to_top.get(
        "deltaXNormalized"
    )
    transfer_delta = top_to_impact.get(
        "deltaXNormalized"
    )
    transfer_distance = top_to_impact.get(
        "absoluteDeltaXNormalized"
    )

    values = (
        backswing_delta,
        transfer_delta,
        transfer_distance,
    )

    if not all(
        isinstance(value, (int, float))
        for value in values
    ):
        return {
            "status": "not_available",
            "value": None,
            "direction": None,
            "reversedDirection": None,
            "targetRange": {
                "minimum": MINIMUM_TRANSITION_TRANSFER,
                "maximum": MAXIMUM_TRANSITION_TRANSFER,
            },
            "message": (
                "Transition hip movement could not be "
                "measured from the available pose geometry."
            ),
        }

    numeric_backswing_delta = float(backswing_delta)
    numeric_transfer_delta = float(transfer_delta)
    numeric_transfer_distance = float(
        transfer_distance
    )

    reversed_direction = movements_reverse_direction(
        numeric_backswing_delta,
        numeric_transfer_delta,
    )

    if (
        numeric_transfer_distance
        < MINIMUM_TRANSITION_TRANSFER
    ):
        status = "limited_transfer"
        message = (
            "Limited lateral hip transfer was measured from "
            "the top of the backswing through impact."
        )
    elif not reversed_direction:
        status = "no_direction_reversal"
        message = (
            "The measured hip movement did not reverse "
            "direction between the backswing and impact."
        )
    elif (
        numeric_transfer_distance
        <= MAXIMUM_TRANSITION_TRANSFER
    ):
        status = "within_target"
        message = (
            "The hips reversed direction and transferred "
            "laterally through impact within the current "
            "prototype range."
        )
    else:
        status = "excessive_shift"
        message = (
            "A substantial lateral hip transfer was measured "
            "between the top of the backswing and impact."
        )

    return {
        "status": status,
        "value": round_value(
            numeric_transfer_distance
        ),
        "direction": top_to_impact.get("direction"),
        "reversedDirection": reversed_direction,
        "targetRange": {
            "minimum": MINIMUM_TRANSITION_TRANSFER,
            "maximum": MAXIMUM_TRANSITION_TRANSFER,
        },
        "message": message,
    }


def classify_shift_maximum(
    *,
    shift: dict[str, Any],
    maximum: float,
    movement_name: str,
) -> dict[str, Any]:
    distance = shift.get(
        "absoluteDeltaXNormalized"
    )

    if not isinstance(distance, (int, float)):
        return {
            "status": "not_available",
            "value": None,
            "direction": None,
            "targetRange": {
                "maximum": maximum,
            },
            "message": (
                f"{movement_name} could not be measured from "
                "the available pose geometry."
            ),
        }

    if distance <= maximum:
        status = "within_target"
        message = (
            f"{movement_name} is within the current "
            "prototype range."
        )
    else:
        status = "excessive_shift"
        message = (
            f"{movement_name} exceeded the current "
            "prototype range."
        )

    return {
        "status": status,
        "value": round_value(float(distance)),
        "direction": shift.get("direction"),
        "targetRange": {
            "maximum": maximum,
        },
        "message": message,
    }


def build_weight_shift_metrics(
    references: dict[str, dict[str, Any]],
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

    address_reference = references[
        "addressReference"
    ]
    top_reference = references[
        "topOfBackswing"
    ]
    downswing_reference = references[
        "downswingStart"
    ]
    impact_reference = references[
        "impactReference"
    ]
    finish_reference = references[
        "finishReference"
    ]

    address_hip_center = get_hip_center(
        address_reference
    )
    top_hip_center = get_hip_center(
        top_reference
    )
    downswing_hip_center = get_hip_center(
        downswing_reference
    )
    impact_hip_center = get_hip_center(
        impact_reference
    )
    finish_hip_center = get_hip_center(
        finish_reference
    )

    measurements = {
        "addressToTop": calculate_lateral_shift(
            address_hip_center,
            top_hip_center,
            frame_width,
        ),
        "topToDownswingStart": (
            calculate_lateral_shift(
                top_hip_center,
                downswing_hip_center,
                frame_width,
            )
        ),
        "topToImpact": calculate_lateral_shift(
            top_hip_center,
            impact_hip_center,
            frame_width,
        ),
        "addressToImpact": calculate_lateral_shift(
            address_hip_center,
            impact_hip_center,
            frame_width,
        ),
        "impactToFinish": calculate_lateral_shift(
            impact_hip_center,
            finish_hip_center,
            frame_width,
        ),
    }

    measurable_values = (
        measurements["addressToTop"][
            "absoluteDeltaXNormalized"
        ],
        measurements["topToDownswingStart"][
            "absoluteDeltaXNormalized"
        ],
        measurements["topToImpact"][
            "absoluteDeltaXNormalized"
        ],
        measurements["addressToImpact"][
            "absoluteDeltaXNormalized"
        ],
        measurements["impactToFinish"][
            "absoluteDeltaXNormalized"
        ],
    )

    available_measurement_count = sum(
        value is not None
        for value in measurable_values
    )

    total_measurement_count = len(
        measurable_values
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

    backswing_load_finding = (
        classify_backswing_load(
            measurements["addressToTop"]
        )
    )

    transition_transfer_finding = (
        classify_transition_transfer(
            measurements["addressToTop"],
            measurements["topToImpact"],
        )
    )

    impact_shift_finding = (
        classify_shift_maximum(
            shift=measurements[
                "addressToImpact"
            ],
            maximum=(
                MAXIMUM_ADDRESS_TO_IMPACT_SHIFT
            ),
            movement_name=(
                "Address-to-impact lateral hip movement"
            ),
        )
    )

    finish_shift_finding = (
        classify_shift_maximum(
            shift=measurements[
                "impactToFinish"
            ],
            maximum=(
                MAXIMUM_IMPACT_TO_FINISH_SHIFT
            ),
            movement_name=(
                "Impact-to-finish lateral hip movement"
            ),
        )
    )

    findings = {
        "backswingLoad": backswing_load_finding,
        "transitionTransfer": (
            transition_transfer_finding
        ),
        "impactShift": impact_shift_finding,
        "finishShift": finish_shift_finding,
    }

    issue_statuses = {
        "limited_shift",
        "limited_transfer",
        "no_direction_reversal",
        "excessive_shift",
    }

    issue_names = [
        finding_name
        for finding_name, finding in findings.items()
        if finding["status"] in issue_statuses
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
            "Some weight-shift proxy measurements were "
            "unavailable. Review pose visibility and the "
            "selected swing frames before relying on this "
            "result."
        )
    else:
        classification = "neutral"
        feedback_status = "within_target"
        primary_issue = None
        feedback_message = (
            "Measured lateral hip movement follows the "
            "current prototype weight-shift ranges."
        )

    return {
        "referenceFrames": {
            "addressReference": {
                "frameIndex": address_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": (
                    address_reference.get(
                        "timestampSeconds"
                    )
                ),
                "poseDetected": bool(
                    address_reference.get(
                        "poseDetected"
                    )
                ),
            },
            "topOfBackswing": {
                "frameIndex": top_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": (
                    top_reference.get(
                        "timestampSeconds"
                    )
                ),
                "poseDetected": bool(
                    top_reference.get(
                        "poseDetected"
                    )
                ),
            },
            "downswingStart": {
                "frameIndex": downswing_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": (
                    downswing_reference.get(
                        "timestampSeconds"
                    )
                ),
                "poseDetected": bool(
                    downswing_reference.get(
                        "poseDetected"
                    )
                ),
            },
            "impactReference": {
                "frameIndex": impact_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": (
                    impact_reference.get(
                        "timestampSeconds"
                    )
                ),
                "poseDetected": bool(
                    impact_reference.get(
                        "poseDetected"
                    )
                ),
            },
            "finishReference": {
                "frameIndex": finish_reference.get(
                    "frameIndex"
                ),
                "timestampSeconds": (
                    finish_reference.get(
                        "timestampSeconds"
                    )
                ),
                "poseDetected": bool(
                    finish_reference.get(
                        "poseDetected"
                    )
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
                "Prototype 2D image-plane lateral hip-center "
                "movement heuristics. This is a weight-shift "
                "proxy and does not measure pressure beneath "
                "the golfer's feet. Camera position, framing, "
                "perspective, and video mirroring can affect "
                "the result."
            ),
        },
    }