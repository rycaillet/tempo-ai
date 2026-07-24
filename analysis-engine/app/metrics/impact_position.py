from __future__ import annotations

import math
from typing import Any, Literal


Handedness = Literal["right", "left"]


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def normalize_point_delta(
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

    delta_x_normalized = (
        float(end_x) - float(start_x)
    )
    delta_y_normalized = (
        float(end_y) - float(start_y)
    )

    distance_normalized = math.hypot(
        delta_x_normalized,
        delta_y_normalized,
    )

    delta_x_pixels = (
        delta_x_normalized * frame_width
    )
    delta_y_pixels = (
        delta_y_normalized * frame_height
    )

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
        "deltaXPixels": round_value(
            delta_x_pixels
        ),
        "deltaYPixels": round_value(
            delta_y_pixels
        ),
        "distancePixels": round_value(
            distance_pixels
        ),
    }


def angle_value(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None

    return round_value(float(value))


def angle_delta(
    start_angle: Any,
    end_angle: Any,
) -> float | None:
    if not isinstance(start_angle, (int, float)):
        return None

    if not isinstance(end_angle, (int, float)):
        return None

    return round_value(
        float(end_angle) - float(start_angle)
    )


def get_arm_mapping(
    handedness: Handedness,
) -> dict[str, str]:
    if handedness == "right":
        return {
            "leadArm": "leftElbowAngle",
            "trailArm": "rightElbowAngle",
        }

    return {
        "leadArm": "rightElbowAngle",
        "trailArm": "leftElbowAngle",
    }


def get_required_reference(
    references: dict[str, dict[str, Any]],
    reference_name: str,
) -> dict[str, Any]:
    reference = references.get(reference_name)

    if not isinstance(reference, dict):
        raise ValueError(
            f"{reference_name} is missing."
        )

    geometry = reference.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError(
            f"{reference_name} geometry is missing."
        )

    return reference


def build_reference_metadata(
    reference_name: str,
    reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": reference_name,
        "frameIndex": reference.get(
            "frameIndex"
        ),
        "timestampSeconds": reference.get(
            "timestampSeconds"
        ),
        "poseDetected": bool(
            reference.get("poseDetected")
        ),
    }


def build_impact_position_metrics(
    references: dict[str, dict[str, Any]],
    frame_width: float,
    frame_height: float,
    handedness: Handedness,
) -> dict[str, Any]:
    if frame_width <= 0:
        raise ValueError(
            "Frame width must be greater than zero."
        )

    if frame_height <= 0:
        raise ValueError(
            "Frame height must be greater than zero."
        )

    address_reference = get_required_reference(
        references,
        "addressReference",
    )
    impact_reference = get_required_reference(
        references,
        "impactReference",
    )

    address_geometry = address_reference[
        "geometry"
    ]
    impact_geometry = impact_reference[
        "geometry"
    ]

    arm_mapping = get_arm_mapping(handedness)

    spine_angle_at_address = angle_value(
        address_geometry.get("spineAngle")
    )
    spine_angle_at_impact = angle_value(
        impact_geometry.get("spineAngle")
    )

    head_movement = normalize_point_delta(
        address_geometry.get("headCenter"),
        impact_geometry.get("headCenter"),
        frame_width,
        frame_height,
    )
    shoulder_movement = normalize_point_delta(
        address_geometry.get("shoulderCenter"),
        impact_geometry.get("shoulderCenter"),
        frame_width,
        frame_height,
    )
    hip_movement = normalize_point_delta(
        address_geometry.get("hipCenter"),
        impact_geometry.get("hipCenter"),
        frame_width,
        frame_height,
    )

    measurements = {
        "spineAngleAtAddressDegrees": (
            spine_angle_at_address
        ),
        "spineAngleAtImpactDegrees": (
            spine_angle_at_impact
        ),
        "spineAngleChangeDegrees": angle_delta(
            spine_angle_at_address,
            spine_angle_at_impact,
        ),
        "shoulderTiltAtImpactDegrees": (
            angle_value(
                impact_geometry.get(
                    "shoulderTilt"
                )
            )
        ),
        "hipTiltAtImpactDegrees": (
            angle_value(
                impact_geometry.get("hipTilt")
            )
        ),
        "headMovementFromAddress": (
            head_movement
        ),
        "shoulderMovementFromAddress": (
            shoulder_movement
        ),
        "hipMovementFromAddress": hip_movement,
        "leadArmAngleAtImpactDegrees": (
            angle_value(
                impact_geometry.get(
                    arm_mapping["leadArm"]
                )
            )
        ),
        "trailArmAngleAtImpactDegrees": (
            angle_value(
                impact_geometry.get(
                    arm_mapping["trailArm"]
                )
            )
        ),
    }

    completeness_values = (
        measurements[
            "spineAngleAtImpactDegrees"
        ],
        measurements[
            "spineAngleChangeDegrees"
        ],
        measurements[
            "shoulderTiltAtImpactDegrees"
        ],
        measurements[
            "hipTiltAtImpactDegrees"
        ],
        measurements[
            "headMovementFromAddress"
        ]["distanceNormalized"],
        measurements[
            "shoulderMovementFromAddress"
        ]["distanceNormalized"],
        measurements[
            "hipMovementFromAddress"
        ]["distanceNormalized"],
        measurements[
            "leadArmAngleAtImpactDegrees"
        ],
        measurements[
            "trailArmAngleAtImpactDegrees"
        ],
    )

    available_measurement_count = sum(
        value is not None
        for value in completeness_values
    )
    total_measurement_count = len(
        completeness_values
    )

    completeness = (
        available_measurement_count
        / total_measurement_count
    )

    confidence = completeness

    required_frames_have_pose = all(
        bool(reference.get("poseDetected"))
        for reference in (
            address_reference,
            impact_reference,
        )
    )

    if not required_frames_have_pose:
        confidence *= 0.75

    return {
        "referenceFrames": {
            "start": build_reference_metadata(
                "addressReference",
                address_reference,
            ),
            "end": build_reference_metadata(
                "impactReference",
                impact_reference,
            ),
        },
        "handednessAssumption": handedness,
        "armMapping": arm_mapping,
        "measurements": measurements,
        "measurementCompleteness": {
            "available": (
                available_measurement_count
            ),
            "total": total_measurement_count,
            "ratio": round_value(completeness),
        },
        "confidence": round_value(confidence),
        "classification": "unclassified",
        "feedback": {
            "status": "not_available",
            "message": None,
            "basis": (
                "This milestone extracts impact-position "
                "measurements only. Coaching classification "
                "has not yet been implemented."
            ),
        },
    }