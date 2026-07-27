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
    "addressToTop",
    "addressToDownswingStart",
    "addressToImpact",
    "topToImpact",
    "impactToFinish",
)

STATIONARY_THRESHOLD = 0.01

MILD_HIP_SHIFT_THRESHOLD = 0.03
MODERATE_HIP_SHIFT_THRESHOLD = 0.06
SEVERE_HIP_SHIFT_THRESHOLD = 0.10

MILD_SPINE_LOSS_THRESHOLD = 5.0
MODERATE_SPINE_LOSS_THRESHOLD = 10.0
SEVERE_SPINE_LOSS_THRESHOLD = 15.0


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


def get_hip_center(
    reference: dict[str, Any],
) -> dict[str, float] | None:
    geometry = get_geometry(reference)

    if geometry is None:
        return None

    hip_center = geometry.get("hipCenter")

    if not isinstance(hip_center, dict):
        return None

    hip_x = hip_center.get("x")
    hip_y = hip_center.get("y")

    if not isinstance(hip_x, (int, float)):
        return None

    if not isinstance(hip_y, (int, float)):
        return None

    return {
        "x": float(hip_x),
        "y": float(hip_y),
    }


def get_spine_angle(
    reference: dict[str, Any],
) -> float | None:
    geometry = get_geometry(reference)

    if geometry is None:
        return None

    spine_angle = geometry.get("spineAngle")

    if not isinstance(spine_angle, (int, float)):
        return None

    return float(spine_angle)


def classify_vertical_direction(
    delta_y_normalized: float,
) -> str:
    if abs(delta_y_normalized) <= STATIONARY_THRESHOLD:
        return "stationary"

    if delta_y_normalized > 0.0:
        return "down"

    return "up"


def calculate_posture_change(
    start_reference: dict[str, Any],
    end_reference: dict[str, Any],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any] | None:
    start_hip = get_hip_center(start_reference)
    end_hip = get_hip_center(end_reference)

    start_spine_angle = get_spine_angle(
        start_reference
    )
    end_spine_angle = get_spine_angle(
        end_reference
    )

    if start_hip is None or end_hip is None:
        return None

    delta_x_normalized = (
        end_hip["x"] - start_hip["x"]
    )
    delta_y_normalized = (
        end_hip["y"] - start_hip["y"]
    )

    delta_x_pixels = (
        delta_x_normalized * frame_width
    )
    delta_y_pixels = (
        delta_y_normalized * frame_height
    )

    spine_angle_change = None
    posture_loss_degrees = None

    if (
        start_spine_angle is not None
        and end_spine_angle is not None
    ):
        spine_angle_change = (
            end_spine_angle - start_spine_angle
        )

        posture_loss_degrees = max(
            0.0,
            start_spine_angle - end_spine_angle,
        )

    return {
        "deltaXNormalized": round_value(
            delta_x_normalized
        ),
        "absoluteDeltaXNormalized": round_value(
            abs(delta_x_normalized)
        ),
        "deltaYNormalized": round_value(
            delta_y_normalized
        ),
        "absoluteDeltaYNormalized": round_value(
            abs(delta_y_normalized)
        ),
        "deltaXPixels": round_value(
            delta_x_pixels
        ),
        "absoluteDeltaXPixels": round_value(
            abs(delta_x_pixels)
        ),
        "deltaYPixels": round_value(
            delta_y_pixels
        ),
        "absoluteDeltaYPixels": round_value(
            abs(delta_y_pixels)
        ),
        "verticalDirection": (
            classify_vertical_direction(
                delta_y_normalized
            )
        ),
        "startSpineAngleDegrees": round_value(
            start_spine_angle
        ),
        "endSpineAngleDegrees": round_value(
            end_spine_angle
        ),
        "spineAngleChangeDegrees": round_value(
            spine_angle_change
        ),
        "postureLossDegrees": round_value(
            posture_loss_degrees
        ),
    }


def classify_hip_shift(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": 0.0,
        "maximum": MILD_HIP_SHIFT_THRESHOLD,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "severity": None,
            "message": (
                "Hip-center movement could not be measured "
                "for this phase transition."
            ),
        }

    if value <= MILD_HIP_SHIFT_THRESHOLD:
        status = "within_target"
        severity = "none"
        message = (
            "Hip-center vertical movement is within the "
            "current prototype target range."
        )
    elif value <= MODERATE_HIP_SHIFT_THRESHOLD:
        status = "mild_depth_loss"
        severity = "mild"
        message = (
            "The hip center shows a mild image-plane shift "
            "that may indicate some loss of posture."
        )
    elif value <= SEVERE_HIP_SHIFT_THRESHOLD:
        status = "moderate_depth_loss"
        severity = "moderate"
        message = (
            "The hip center shows a moderate image-plane "
            "shift that may indicate early posture loss."
        )
    else:
        status = "severe_depth_loss"
        severity = "severe"
        message = (
            "The hip center shows a large image-plane shift "
            "that may indicate substantial posture loss."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "severity": severity,
        "message": message,
    }


def classify_spine_posture_loss(
    value: float | None,
) -> dict[str, Any]:
    target_range = {
        "minimum": 0.0,
        "maximum": MILD_SPINE_LOSS_THRESHOLD,
    }

    if value is None:
        return {
            "status": "not_available",
            "value": None,
            "targetRange": target_range,
            "severity": None,
            "message": (
                "Spine-angle posture loss could not be "
                "measured for this phase transition."
            ),
        }

    if value <= MILD_SPINE_LOSS_THRESHOLD:
        status = "within_target"
        severity = "none"
        message = (
            "Measured spine-angle retention is within the "
            "current prototype target range."
        )
    elif value <= MODERATE_SPINE_LOSS_THRESHOLD:
        status = "mild_posture_loss"
        severity = "mild"
        message = (
            "The measured spine angle becomes slightly more "
            "upright before impact."
        )
    elif value <= SEVERE_SPINE_LOSS_THRESHOLD:
        status = "moderate_posture_loss"
        severity = "moderate"
        message = (
            "The measured spine angle becomes noticeably more "
            "upright before impact."
        )
    else:
        status = "severe_posture_loss"
        severity = "severe"
        message = (
            "The measured spine angle becomes substantially "
            "more upright before impact."
        )

    return {
        "status": status,
        "value": round_value(value),
        "targetRange": target_range,
        "severity": severity,
        "message": message,
    }


def severity_rank(
    severity: str | None,
) -> int:
    rankings = {
        None: 0,
        "none": 0,
        "mild": 1,
        "moderate": 2,
        "severe": 3,
    }

    return rankings.get(severity, 0)


def build_early_extension_metrics(
    references: dict[str, dict[str, Any]],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    validate_frame_dimensions(
        frame_width=frame_width,
        frame_height=frame_height,
    )
    validate_references(references)

    reference_pairs = {
        "addressToTop": (
            "addressReference",
            "topOfBackswing",
        ),
        "addressToDownswingStart": (
            "addressReference",
            "downswingStart",
        ),
        "addressToImpact": (
            "addressReference",
            "impactReference",
        ),
        "topToImpact": (
            "topOfBackswing",
            "impactReference",
        ),
        "impactToFinish": (
            "impactReference",
            "finishReference",
        ),
    }

    measurements: dict[str, Any] = {}

    for measurement_name, (
        start_name,
        end_name,
    ) in reference_pairs.items():
        measurements[measurement_name] = (
            calculate_posture_change(
                start_reference=references[start_name],
                end_reference=references[end_name],
                frame_width=frame_width,
                frame_height=frame_height,
            )
        )

    available_measurement_count = sum(
        measurements[name] is not None
        for name in MEASUREMENT_NAMES
    )

    total_measurement_count = len(
        MEASUREMENT_NAMES
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

    address_to_impact = measurements[
        "addressToImpact"
    ]

    impact_hip_shift = (
        address_to_impact[
            "absoluteDeltaYNormalized"
        ]
        if isinstance(address_to_impact, dict)
        else None
    )

    impact_posture_loss = (
        address_to_impact["postureLossDegrees"]
        if isinstance(address_to_impact, dict)
        else None
    )

    hip_shift_finding = classify_hip_shift(
        impact_hip_shift
    )

    spine_posture_finding = (
        classify_spine_posture_loss(
            impact_posture_loss
        )
    )

    findings = {
        "impactHipDepthProxy": hip_shift_finding,
        "impactSpinePosture": spine_posture_finding,
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

    if not available_findings:
        classification = "incomplete"
        primary_issue = None
        feedback_status = "insufficient_data"
        feedback_message = (
            "Early-extension proxy measurements were not "
            "available. Review the detected hip center and "
            "spine angle at the selected phase frames."
        )
    elif issue_names:
        primary_issue = max(
            issue_names,
            key=lambda name: severity_rank(
                findings[name]["severity"]
            ),
        )

        primary_severity = findings[
            primary_issue
        ]["severity"]

        classification_mapping = {
            "mild": "mild_early_extension",
            "moderate": "moderate_early_extension",
            "severe": "severe_early_extension",
        }

        classification = (
            classification_mapping.get(
                primary_severity,
                "needs_attention",
            )
        )

        feedback_status = "outside_target"
        feedback_message = findings[
            primary_issue
        ]["message"]
    else:
        classification = "neutral"
        primary_issue = None
        feedback_status = "within_target"
        feedback_message = (
            "The current 2D posture-loss indicators remain "
            "within their prototype target ranges through "
            "impact."
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
                "This prototype uses vertical image-plane hip-center "
                "movement and measured spine-angle retention as a "
                "2D posture-loss proxy. It does not directly measure "
                "pelvis movement toward the golf ball, true hip depth, "
                "ground pressure, or three-dimensional early extension. "
                "Results can also vary with camera position, framing, "
                "perspective, and video rotation."
            ),
        },
    }