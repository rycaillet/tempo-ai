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


def build_spine_angle_finding(
    spine_angle_change: float | None,
) -> dict[str, Any]:
    if spine_angle_change is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": {
                "minimum": -10.0,
                "maximum": 10.0,
            },
            "message": (
                "Spine-angle change could not be measured "
                "between address and impact."
            ),
        }

    if spine_angle_change < -20.0:
        status = "excessive_loss"
        message = (
            "Your measured spine angle decreased substantially "
            "between address and impact. This may indicate a "
            "significant loss of posture."
        )
    elif spine_angle_change < -10.0:
        status = "moderate_loss"
        message = (
            "Your measured spine angle decreased moderately "
            "between address and impact."
        )
    elif spine_angle_change > 20.0:
        status = "excessive_gain"
        message = (
            "Your measured spine angle increased substantially "
            "between address and impact. This may indicate "
            "excessive forward bend."
        )
    elif spine_angle_change > 10.0:
        status = "moderate_gain"
        message = (
            "Your measured spine angle increased moderately "
            "between address and impact."
        )
    else:
        status = "maintained"
        message = (
            "Your measured spine angle remained relatively "
            "stable from address through impact."
        )

    return {
        "status": status,
        "value": round_value(spine_angle_change),
        "targetRange": {
            "minimum": -10.0,
            "maximum": 10.0,
        },
        "message": message,
    }


def build_movement_finding(
    *,
    value: float | None,
    stable_maximum: float,
    moderate_maximum: float,
    body_part_name: str,
) -> dict[str, Any]:
    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": {
                "stableMaximum": stable_maximum,
                "moderateMaximum": moderate_maximum,
            },
            "message": (
                f"{body_part_name} movement from address "
                "could not be measured."
            ),
        }

    if value <= stable_maximum:
        status = "stable"
        message = (
            f"{body_part_name} movement remained within the "
            "current prototype stability range."
        )
    elif value <= moderate_maximum:
        status = "moderate"
        message = (
            f"{body_part_name} movement was moderate between "
            "address and impact."
        )
    else:
        status = "excessive"
        message = (
            f"{body_part_name} movement was substantial between "
            "address and impact. Review the swing for excessive "
            "body displacement."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": {
            "stableMaximum": stable_maximum,
            "moderateMaximum": moderate_maximum,
        },
        "message": message,
    }


def build_lead_arm_finding(
    lead_arm_angle: float | None,
) -> dict[str, Any]:
    if lead_arm_angle is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": {
                "minimumExtended": 160.0,
                "minimumSlightlyBent": 145.0,
            },
            "message": (
                "Lead-arm angle at impact could not be measured."
            ),
        }

    if lead_arm_angle >= 160.0:
        status = "extended"
        message = (
            "The lead arm remained extended at the measured "
            "impact reference."
        )
    elif lead_arm_angle >= 145.0:
        status = "slightly_bent"
        message = (
            "The lead arm was slightly bent at the measured "
            "impact reference."
        )
    else:
        status = "collapsed"
        message = (
            "The lead arm appeared significantly bent at the "
            "measured impact reference."
        )

    return {
        "status": status,
        "value": round_value(lead_arm_angle),
        "targetRange": {
            "minimumExtended": 160.0,
            "minimumSlightlyBent": 145.0,
        },
        "message": message,
    }


def build_trail_arm_finding(
    trail_arm_angle: float | None,
) -> dict[str, Any]:
    if trail_arm_angle is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": {
                "minimum": 110.0,
                "maximum": 170.0,
            },
            "message": (
                "Trail-arm angle at impact could not be measured."
            ),
        }

    if trail_arm_angle < 110.0:
        status = "excessively_bent"
        message = (
            "The trail arm appeared heavily bent at the measured "
            "impact reference."
        )
    elif trail_arm_angle > 170.0:
        status = "overextended"
        message = (
            "The trail arm appeared nearly fully extended at the "
            "measured impact reference."
        )
    else:
        status = "within_target"
        message = (
            "The trail-arm angle was within the current "
            "prototype impact range."
        )

    return {
        "status": status,
        "value": round_value(trail_arm_angle),
        "targetRange": {
            "minimum": 110.0,
            "maximum": 170.0,
        },
        "message": message,
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

    findings = {
        "spineAngle": build_spine_angle_finding(
            measurements[
                "spineAngleChangeDegrees"
            ]
        ),
        "headMovement": build_movement_finding(
            value=measurements[
                "headMovementFromAddress"
            ]["distanceNormalized"],
            stable_maximum=0.08,
            moderate_maximum=0.14,
            body_part_name="Head",
        ),
        "shoulderMovement": build_movement_finding(
            value=measurements[
                "shoulderMovementFromAddress"
            ]["distanceNormalized"],
            stable_maximum=0.12,
            moderate_maximum=0.20,
            body_part_name="Shoulder-center",
        ),
        "hipMovement": build_movement_finding(
            value=measurements[
                "hipMovementFromAddress"
            ]["distanceNormalized"],
            stable_maximum=0.10,
            moderate_maximum=0.18,
            body_part_name="Hip-center",
        ),
        "leadArm": build_lead_arm_finding(
            measurements[
                "leadArmAngleAtImpactDegrees"
            ]
        ),
        "trailArm": build_trail_arm_finding(
            measurements[
                "trailArmAngleAtImpactDegrees"
            ]
        ),
    }

    issue_statuses = {
        "excessive_loss",
        "excessive_gain",
        "excessive",
        "collapsed",
        "excessively_bent",
        "overextended",
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
            "Some impact-position measurements were unavailable. "
            "Review the impact reference before relying on this "
            "classification."
        )
    else:
        classification = "neutral"
        feedback_status = "within_target"
        primary_issue = None
        feedback_message = (
            "Your measured impact position is within the current "
            "prototype target ranges."
        )

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
        "findings": findings,
        "classification": classification,
        "issueCount": len(issue_names),
        "primaryIssue": primary_issue,
        "confidence": round_value(confidence),
        "feedback": {
            "status": feedback_status,
            "message": feedback_message,
            "basis": (
                "Prototype heuristic ranges used to organize "
                "2D impact-position observations. These ranges "
                "are not universal golf instruction standards."
            ),
        },
    }