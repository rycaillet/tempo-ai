from __future__ import annotations

from typing import Any


REQUIRED_REFERENCE_NAMES = (
    "addressReference",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

MEASUREMENT_NAMES = (
    "address",
    "topOfBackswing",
    "downswingStart",
    "impact",
    "finish",
)

MINIMUM_BACKSWING_SHOULDER_TURN = 0.04
MINIMUM_BACKSWING_HIP_TURN = 0.015
MAXIMUM_BACKSWING_HIP_TURN = 0.12

MINIMUM_TOP_SEPARATION = 0.02
MAXIMUM_TOP_SEPARATION = 0.12

MINIMUM_IMPACT_RETURN_RATIO = 0.40
MINIMUM_FINISH_SHOULDER_TURN = 0.04


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def validate_references(
    references: dict[str, dict[str, Any]],
) -> None:
    for reference_name in REQUIRED_REFERENCE_NAMES:
        reference = references.get(reference_name)

        if not isinstance(reference, dict):
            raise ValueError(
                f"{reference_name} is missing."
            )


def get_geometry(
    reference: dict[str, Any],
) -> dict[str, Any] | None:
    geometry = reference.get("geometry")

    if not isinstance(geometry, dict):
        return None

    return geometry


def get_point(
    reference: dict[str, Any],
    point_name: str,
) -> dict[str, float] | None:
    geometry = get_geometry(reference)

    if geometry is None:
        return None

    point = geometry.get(point_name)

    if not isinstance(point, dict):
        return None

    x_value = point.get("x")
    y_value = point.get("y")
    z_value = point.get("z")

    if not isinstance(x_value, (int, float)):
        return None

    if not isinstance(y_value, (int, float)):
        return None

    if not isinstance(z_value, (int, float)):
        return None

    return {
        "x": float(x_value),
        "y": float(y_value),
        "z": float(z_value),
    }


def calculate_pair_state(
    left_point: dict[str, float] | None,
    right_point: dict[str, float] | None,
) -> dict[str, float | None]:
    if left_point is None or right_point is None:
        return {
            "imageWidthNormalized": None,
            "depthSeparationNormalized": None,
            "absoluteDepthSeparationNormalized": None,
        }

    image_width = abs(
        right_point["x"] - left_point["x"]
    )

    depth_separation = (
        right_point["z"] - left_point["z"]
    )

    return {
        "imageWidthNormalized": round_value(
            image_width
        ),
        "depthSeparationNormalized": round_value(
            depth_separation
        ),
        "absoluteDepthSeparationNormalized": (
            round_value(abs(depth_separation))
        ),
    }


def calculate_rotation_state(
    reference: dict[str, Any],
) -> dict[str, Any]:
    left_shoulder = get_point(
        reference,
        "leftShoulder",
    )
    right_shoulder = get_point(
        reference,
        "rightShoulder",
    )
    left_hip = get_point(
        reference,
        "leftHip",
    )
    right_hip = get_point(
        reference,
        "rightHip",
    )

    shoulder_state = calculate_pair_state(
        left_shoulder,
        right_shoulder,
    )
    hip_state = calculate_pair_state(
        left_hip,
        right_hip,
    )

    shoulder_depth = shoulder_state[
        "absoluteDepthSeparationNormalized"
    ]
    hip_depth = hip_state[
        "absoluteDepthSeparationNormalized"
    ]

    separation_proxy = None

    if (
        isinstance(shoulder_depth, (int, float))
        and isinstance(hip_depth, (int, float))
    ):
        separation_proxy = max(
            0.0,
            float(shoulder_depth) - float(hip_depth),
        )

    return {
        "shoulders": shoulder_state,
        "hips": hip_state,
        "shoulderHipSeparationProxy": round_value(
            separation_proxy
        ),
    }


def calculate_change_from_address(
    address_state: dict[str, Any],
    phase_state: dict[str, Any],
) -> dict[str, float | None]:
    address_shoulder_depth = address_state[
        "shoulders"
    ].get("depthSeparationNormalized")

    phase_shoulder_depth = phase_state[
        "shoulders"
    ].get("depthSeparationNormalized")

    address_hip_depth = address_state[
        "hips"
    ].get("depthSeparationNormalized")

    phase_hip_depth = phase_state[
        "hips"
    ].get("depthSeparationNormalized")

    shoulder_change = None
    hip_change = None

    if (
        isinstance(address_shoulder_depth, (int, float))
        and isinstance(
            phase_shoulder_depth,
            (int, float),
        )
    ):
        shoulder_change = (
            float(phase_shoulder_depth)
            - float(address_shoulder_depth)
        )

    if (
        isinstance(address_hip_depth, (int, float))
        and isinstance(
            phase_hip_depth,
            (int, float),
        )
    ):
        hip_change = (
            float(phase_hip_depth)
            - float(address_hip_depth)
        )

    absolute_shoulder_change = (
        abs(shoulder_change)
        if shoulder_change is not None
        else None
    )

    absolute_hip_change = (
        abs(hip_change)
        if hip_change is not None
        else None
    )

    rotation_separation = None

    if (
        absolute_shoulder_change is not None
        and absolute_hip_change is not None
    ):
        rotation_separation = max(
            0.0,
            absolute_shoulder_change
            - absolute_hip_change,
        )

    return {
        "shoulderDepthChangeNormalized": round_value(
            shoulder_change
        ),
        "absoluteShoulderDepthChangeNormalized": (
            round_value(absolute_shoulder_change)
        ),
        "hipDepthChangeNormalized": round_value(
            hip_change
        ),
        "absoluteHipDepthChangeNormalized": round_value(
            absolute_hip_change
        ),
        "shoulderHipRotationSeparationProxy": (
            round_value(rotation_separation)
        ),
    }


def calculate_return_ratio(
    top_change: float | None,
    later_change: float | None,
) -> float | None:
    if top_change is None or later_change is None:
        return None

    if top_change <= 0.0:
        return None

    remaining_ratio = later_change / top_change

    return_ratio = 1.0 - remaining_ratio

    return max(
        0.0,
        min(1.0, return_ratio),
    )


def classify_backswing_shoulder_turn(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": MINIMUM_BACKSWING_SHOULDER_TURN,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "message": (
                "Backswing shoulder rotation could not be "
                "estimated from the available shoulder landmarks."
            ),
        }

    if value < MINIMUM_BACKSWING_SHOULDER_TURN:
        status = "limited_turn"
        message = (
            "The shoulder depth-change proxy indicates limited "
            "upper-body rotation from address to the top."
        )
    else:
        status = "within_target"
        message = (
            "The shoulder depth-change proxy indicates a "
            "meaningful upper-body turn during the backswing."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "message": message,
    }


def classify_backswing_hip_turn(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": MINIMUM_BACKSWING_HIP_TURN,
        "maximum": MAXIMUM_BACKSWING_HIP_TURN,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "message": (
                "Backswing hip rotation could not be estimated "
                "from the available hip landmarks."
            ),
        }

    if value < MINIMUM_BACKSWING_HIP_TURN:
        status = "limited_turn"
        message = (
            "The hip depth-change proxy indicates limited lower-body "
            "rotation during the backswing."
        )
    elif value <= MAXIMUM_BACKSWING_HIP_TURN:
        status = "within_target"
        message = (
            "The hip depth-change proxy is within the current "
            "prototype backswing range."
        )
    else:
        status = "excessive_turn"
        message = (
            "The hip depth-change proxy exceeds the current "
            "prototype backswing range."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "message": message,
    }


def classify_top_separation(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": MINIMUM_TOP_SEPARATION,
        "maximum": MAXIMUM_TOP_SEPARATION,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "message": (
                "Shoulder-to-hip rotational separation could "
                "not be estimated at the top."
            ),
        }

    if value < MINIMUM_TOP_SEPARATION:
        status = "limited_separation"
        message = (
            "The shoulders and hips show limited relative "
            "depth change at the top of the backswing."
        )
    elif value <= MAXIMUM_TOP_SEPARATION:
        status = "within_target"
        message = (
            "Shoulder-to-hip rotational separation is within "
            "the current prototype range at the top."
        )
    else:
        status = "excessive_separation"
        message = (
            "The shoulder-to-hip depth-change difference exceeds "
            "the current prototype range at the top."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "message": message,
    }


def classify_impact_unwinding(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": MINIMUM_IMPACT_RETURN_RATIO,
        "maximum": 1.0,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "message": (
                "Rotation return through impact could not be "
                "estimated from the available landmarks."
            ),
        }

    if value < MINIMUM_IMPACT_RETURN_RATIO:
        status = "limited_unwinding"
        message = (
            "A large portion of the backswing shoulder-depth "
            "change remains at impact."
        )
    else:
        status = "within_target"
        message = (
            "The shoulder-depth proxy shows meaningful rotation "
            "back toward the address relationship by impact."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "message": message,
    }


def classify_finish_rotation(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": MINIMUM_FINISH_SHOULDER_TURN,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "message": (
                "Finish rotation could not be estimated from "
                "the available shoulder landmarks."
            ),
        }

    if value < MINIMUM_FINISH_SHOULDER_TURN:
        status = "limited_finish"
        message = (
            "The finish frame shows limited shoulder-depth change "
            "relative to address."
        )
    else:
        status = "within_target"
        message = (
            "The finish frame shows continued upper-body rotation "
            "relative to address."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "message": message,
    }


def build_rotation_metrics(
    references: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    validate_references(references)

    reference_mapping = {
        "address": "addressReference",
        "topOfBackswing": "topOfBackswing",
        "downswingStart": "downswingStart",
        "impact": "impactReference",
        "finish": "finishReference",
    }

    states = {
        measurement_name: calculate_rotation_state(
            references[reference_name]
        )
        for measurement_name, reference_name
        in reference_mapping.items()
    }

    address_state = states["address"]

    changes_from_address = {
        measurement_name: calculate_change_from_address(
            address_state=address_state,
            phase_state=states[measurement_name],
        )
        for measurement_name in (
            "topOfBackswing",
            "downswingStart",
            "impact",
            "finish",
        )
    }

    top_change = changes_from_address[
        "topOfBackswing"
    ]

    impact_change = changes_from_address["impact"]

    top_shoulder_turn = top_change[
        "absoluteShoulderDepthChangeNormalized"
    ]
    top_hip_turn = top_change[
        "absoluteHipDepthChangeNormalized"
    ]
    top_separation = top_change[
        "shoulderHipRotationSeparationProxy"
    ]

    impact_shoulder_turn = impact_change[
        "absoluteShoulderDepthChangeNormalized"
    ]

    finish_shoulder_turn = changes_from_address[
        "finish"
    ]["absoluteShoulderDepthChangeNormalized"]

    impact_return_ratio = calculate_return_ratio(
        (
            float(top_shoulder_turn)
            if isinstance(top_shoulder_turn, (int, float))
            else None
        ),
        (
            float(impact_shoulder_turn)
            if isinstance(
                impact_shoulder_turn,
                (int, float),
            )
            else None
        ),
    )

    findings = {
        "backswingShoulderTurn": (
            classify_backswing_shoulder_turn(
                (
                    float(top_shoulder_turn)
                    if isinstance(
                        top_shoulder_turn,
                        (int, float),
                    )
                    else None
                )
            )
        ),
        "backswingHipTurn": classify_backswing_hip_turn(
            (
                float(top_hip_turn)
                if isinstance(top_hip_turn, (int, float))
                else None
            )
        ),
        "topRotationSeparation": classify_top_separation(
            (
                float(top_separation)
                if isinstance(top_separation, (int, float))
                else None
            )
        ),
        "impactUnwinding": classify_impact_unwinding(
            impact_return_ratio
        ),
        "finishRotation": classify_finish_rotation(
            (
                float(finish_shoulder_turn)
                if isinstance(
                    finish_shoulder_turn,
                    (int, float),
                )
                else None
            )
        ),
    }

    available_findings = [
        finding
        for finding in findings.values()
        if finding["status"] != "not_available"
    ]

    issue_names = [
        finding_name
        for finding_name, finding in findings.items()
        if finding["status"]
        not in {
            "within_target",
            "not_available",
        }
    ]

    total_measurement_count = len(MEASUREMENT_NAMES)

    available_measurement_count = sum(
        (
            states[name]["shoulders"][
                "depthSeparationNormalized"
            ]
            is not None
            and states[name]["hips"][
                "depthSeparationNormalized"
            ]
            is not None
        )
        for name in MEASUREMENT_NAMES
    )

    completeness = (
        available_measurement_count
        / total_measurement_count
    )

    required_frames_have_pose = all(
        bool(references[name].get("poseDetected"))
        for name in REQUIRED_REFERENCE_NAMES
    )

    confidence = completeness

    if not required_frames_have_pose:
        confidence *= 0.75

    if not available_findings:
        classification = "incomplete"
        primary_issue = None
        feedback_status = "insufficient_data"
        feedback_message = (
            "Rotation proxy measurements were unavailable. "
            "Review the detected shoulder and hip landmarks."
        )
    elif issue_names:
        classification = "needs_attention"
        primary_issue = issue_names[0]
        feedback_status = "outside_target"
        feedback_message = findings[
            primary_issue
        ]["message"]
    else:
        classification = "neutral"
        primary_issue = None
        feedback_status = "within_target"
        feedback_message = (
            "The current shoulder and hip rotation proxies are "
            "within their prototype target ranges."
        )

    reference_frames = {
        reference_name: {
            "frameIndex": references[
                reference_name
            ].get("frameIndex"),
            "timestampSeconds": references[
                reference_name
            ].get("timestampSeconds"),
            "poseDetected": bool(
                references[
                    reference_name
                ].get("poseDetected")
            ),
        }
        for reference_name in REQUIRED_REFERENCE_NAMES
    }

    return {
        "referenceFrames": reference_frames,
        "measurements": {
            "states": states,
            "changesFromAddress": changes_from_address,
            "impactShoulderReturnRatio": round_value(
                impact_return_ratio
            ),
        },
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
                "This prototype estimates camera-relative body "
                "rotation using left-to-right shoulder and hip "
                "landmark depth differences. These values are "
                "rotation proxies, not biomechanical turn angles. "
                "They may vary with camera position, perspective, "
                "clothing, landmark accuracy, and MediaPipe depth "
                "estimation."
            ),
        },
    }