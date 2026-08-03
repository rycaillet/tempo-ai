from __future__ import annotations

import argparse
import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

from app.analysis import build_swing_analysis_report
from app.analysis.api_contract import (
    ANALYSIS_API_VERSION,
)
from app.analysis.versioning import (
    build_analysis_version_manifest,
)
from app.club_analysis_quality import (
    build_club_analysis_quality_summary,
)
from app.coaching import (
    PROMPT_VERSION,
    CoachingProvider,
    build_coach_context,
    build_configured_coaching_provider,
    generate_coaching_response,
)
from app.findings import build_swing_findings
from app.recommendations import build_swing_recommendations
from app.metrics.early_extension import (
    build_early_extension_metrics,
)
from app.metrics.head_stability import (
    build_head_stability_metrics,
)
from app.metrics.impact_position import (
    build_impact_position_metrics,
)
from app.metrics.rotation import (
    build_rotation_metrics,
)
from app.metrics.shaft_lean import (
    build_shaft_lean_metrics,
)
from app.metrics.swing_plane import (
    build_swing_plane_metrics,
)
from app.metrics.weight_shift import (
    build_weight_shift_metrics,
)
from app.metrics.registry import (
    MetricContext,
    MetricDefinition,
    MetricRegistration,
    SummaryField,
    build_registered_metric_summary,
    build_registered_metrics,
    get_metric_versions,
    validate_scoring_weights,
)
from app.scoring import calculate_swing_score

Handedness = Literal["right", "left"]

REFERENCE_NAMES = (
    "addressReference",
    "takeawayReference",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

CENTER_NAMES = (
    "headCenter",
    "shoulderCenter",
    "hipCenter",
)

ANGLE_NAMES = (
    "spineAngle",
    "shoulderTilt",
    "hipTilt",
    "leftElbowAngle",
    "rightElbowAngle",
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def get_rotated_dimensions(
    metadata: dict[str, Any],
    orientation: dict[str, Any],
) -> tuple[float, float]:
    width = float(metadata["width"])
    height = float(metadata["height"])

    selected_rotation = orientation.get(
        "selectedRotation",
        "none",
    )

    if selected_rotation in {
        "clockwise90",
        "counterclockwise90",
    }:
        return height, width

    return width, height


def create_frame_lookup(
    geometry_data: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    frames = geometry_data.get("frames")

    if not isinstance(frames, list):
        raise ValueError(
            "Geometry analysis must contain a frames array."
        )

    lookup: dict[int, dict[str, Any]] = {}

    for frame in frames:
        frame_index = frame.get("frameIndex")

        if isinstance(frame_index, int):
            lookup[frame_index] = frame

    return lookup


def get_reference_frame_indices(
    refined_phases_data: dict[str, Any],
) -> dict[str, int]:
    phases = refined_phases_data.get("phases")

    if not isinstance(phases, dict):
        raise ValueError(
            "Refined phase analysis is missing phases."
        )

    phase_mapping = {
        "addressReference": "address",
        "takeawayReference": "takeaway",
        "topOfBackswing": "topOfBackswing",
        "downswingStart": "downswingStart",
        "impactReference": "impactReference",
        "finishReference": "finishReference",
    }

    reference_indices: dict[str, int] = {}

    for reference_name, phase_name in phase_mapping.items():
        phase = phases.get(phase_name)

        if not isinstance(phase, dict):
            raise ValueError(
                "Refined phase analysis is missing "
                f"{phase_name}."
            )

        frame_index = phase.get("frameIndex")

        if not isinstance(frame_index, int):
            raise ValueError(
                f"Refined phase {phase_name} is missing "
                "a valid frameIndex."
            )

        reference_indices[reference_name] = frame_index

    frame_indices = list(reference_indices.values())

    if frame_indices != sorted(frame_indices):
        raise ValueError(
            "Refined golf phases are not chronological."
        )

    return reference_indices


def extract_reference_frames(
    reference_indices: dict[str, int],
    frame_lookup: dict[int, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    references: dict[str, dict[str, Any]] = {}

    for reference_name, frame_index in reference_indices.items():
        frame = frame_lookup.get(frame_index)

        if frame is None:
            raise ValueError(
                f"Geometry frame {frame_index} was not found "
                f"for {reference_name}."
            )

        geometry = frame.get("geometry")

        if not isinstance(geometry, dict):
            raise ValueError(
                f"Geometry is missing for frame {frame_index}."
            )

        references[reference_name] = {
            "frameIndex": frame_index,
            "timestampSeconds": frame.get(
                "timestampSeconds"
            ),
            "poseDetected": frame.get("poseDetected"),
            "geometry": geometry,
        }

    return references


def normalized_point_delta(
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

def axial_angle_delta(
    start_angle: Any,
    end_angle: Any,
) -> float | None:
    """
    Calculate the shortest signed change between two undirected
    line angles.

    Shoulder and hip tilt represent axes rather than directional
    vectors, so angles separated by 180 degrees describe the same
    physical line.

    The returned change is normalized to -90 through 90 degrees.
    """

    if not isinstance(start_angle, (int, float)):
        return None

    if not isinstance(end_angle, (int, float)):
        return None

    difference = float(end_angle) - float(start_angle)

    while difference > 90.0:
        difference -= 180.0

    while difference < -90.0:
        difference += 180.0

    return round_value(difference)

def build_transition_metrics(
    start_reference: dict[str, Any],
    end_reference: dict[str, Any],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    start_geometry = start_reference["geometry"]
    end_geometry = end_reference["geometry"]

    center_movements: dict[str, Any] = {}

    for center_name in CENTER_NAMES:
        center_movements[center_name] = normalized_point_delta(
            start_geometry.get(center_name),
            end_geometry.get(center_name),
            frame_width,
            frame_height,
        )

    angle_changes: dict[str, float | None] = {}

    for angle_name in ANGLE_NAMES:
        start_angle = start_geometry.get(angle_name)
        end_angle = end_geometry.get(angle_name)

        if angle_name in {
            "shoulderTilt",
            "hipTilt",
        }:
            angle_changes[angle_name] = axial_angle_delta(
                start_angle,
                end_angle,
            )
        else:
            angle_changes[angle_name] = angle_delta(
                start_angle,
                end_angle,
            )

    return {
        "fromFrame": start_reference["frameIndex"],
        "toFrame": end_reference["frameIndex"],
        "durationSeconds": round_value(
            float(end_reference["timestampSeconds"])
            - float(start_reference["timestampSeconds"])
        ),
        "centerMovement": center_movements,
        "angleChangesDegrees": angle_changes,
    }


def build_tempo_metrics(
    references: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    required_references = (
        "addressReference",
        "topOfBackswing",
        "impactReference",
    )

    timestamps: dict[str, float] = {}

    for reference_name in required_references:
        timestamp = references[reference_name].get(
            "timestampSeconds"
        )

        if not isinstance(timestamp, (int, float)):
            raise ValueError(
                f"{reference_name} is missing a valid "
                "timestampSeconds value."
            )

        timestamps[reference_name] = float(timestamp)

    address_time = timestamps["addressReference"]
    top_time = timestamps["topOfBackswing"]
    impact_time = timestamps["impactReference"]

    backswing_duration = top_time - address_time
    downswing_duration = impact_time - top_time
    total_swing_duration = impact_time - address_time

    if backswing_duration <= 0.0:
        raise ValueError(
            "Backswing duration must be greater than zero."
        )

    if downswing_duration <= 0.0:
        raise ValueError(
            "Downswing duration must be greater than zero."
        )

    tempo_ratio = backswing_duration / downswing_duration

    target_minimum = 2.7
    target_maximum = 3.3

    if tempo_ratio < target_minimum:
        classification = "quick"
        status = "below_target"
        feedback = (
            "Your downswing is fast relative to your "
            "backswing. A slightly smoother transition or "
            "more deliberate backswing may create a more "
            "balanced tempo."
        )
    elif tempo_ratio <= target_maximum:
        classification = "balanced"
        status = "within_target"
        feedback = (
            "Your backswing-to-downswing timing is within "
            "the target range. Focus on repeating this rhythm "
            "consistently."
        )
    else:
        classification = "deliberate"
        status = "above_target"
        feedback = (
            "Your backswing is long relative to your "
            "downswing. A more continuous transition may help "
            "create a more balanced tempo."
        )

    required_frames_have_pose = all(
        bool(references[reference_name].get("poseDetected"))
        for reference_name in required_references
    )

    confidence = 1.0 if required_frames_have_pose else 0.75

    return {
        "backswingDurationSeconds": round_value(
            backswing_duration
        ),
        "downswingDurationSeconds": round_value(
            downswing_duration
        ),
        "totalSwingDurationSeconds": round_value(
            total_swing_duration
        ),
        "backswingToDownswingRatio": round_value(
            tempo_ratio
        ),
        "ratioDisplay": f"{tempo_ratio:.2f}:1",
        "classification": classification,
        "confidence": confidence,
        "feedback": {
            "status": status,
            "targetRange": {
                "minimum": target_minimum,
                "maximum": target_maximum,
                "ratioDisplay": (
                    f"{target_minimum:.1f}:1 to "
                    f"{target_maximum:.1f}:1"
                ),
            },
            "message": feedback,
            "basis": (
                "Heuristic target range used for prototype "
                "swing-tempo feedback."
            ),
        },
        "referenceFrames": {
            "backswingStart": "addressReference",
            "backswingEnd": "topOfBackswing",
            "downswingStart": "topOfBackswing",
            "downswingEnd": "impactReference",
        },
    }


def build_phase_validation(
    references: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ordered_reference_names = (
        "addressReference",
        "takeawayReference",
        "topOfBackswing",
        "downswingStart",
        "impactReference",
        "finishReference",
    )

    frame_indices: dict[str, int] = {}
    timestamps: dict[str, float] = {}

    for reference_name in ordered_reference_names:
        reference = references[reference_name]
        frame_index = reference.get("frameIndex")
        timestamp = reference.get("timestampSeconds")

        if not isinstance(frame_index, int):
            raise ValueError(
                f"{reference_name} is missing a valid "
                "frameIndex."
            )

        if not isinstance(timestamp, (int, float)):
            raise ValueError(
                f"{reference_name} is missing a valid "
                "timestampSeconds value."
            )

        frame_indices[reference_name] = frame_index
        timestamps[reference_name] = float(timestamp)

    ordered_frames = [
        frame_indices[name]
        for name in ordered_reference_names
    ]
    ordered_times = [
        timestamps[name]
        for name in ordered_reference_names
    ]

    durations = {
        "addressToTakeawaySeconds": (
            timestamps["takeawayReference"]
            - timestamps["addressReference"]
        ),
        "backswingSeconds": (
            timestamps["topOfBackswing"]
            - timestamps["addressReference"]
        ),
        "topToDownswingStartSeconds": (
            timestamps["downswingStart"]
            - timestamps["topOfBackswing"]
        ),
        "downswingSeconds": (
            timestamps["impactReference"]
            - timestamps["topOfBackswing"]
        ),
        "downswingStartToImpactSeconds": (
            timestamps["impactReference"]
            - timestamps["downswingStart"]
        ),
        "impactToFinishSeconds": (
            timestamps["finishReference"]
            - timestamps["impactReference"]
        ),
    }

    checks = {
        "frameOrderStrictlyIncreasing": all(
            earlier < later
            for earlier, later in zip(
                ordered_frames,
                ordered_frames[1:],
            )
        ),
        "timestampOrderStrictlyIncreasing": all(
            earlier < later
            for earlier, later in zip(
                ordered_times,
                ordered_times[1:],
            )
        ),
        "allReferenceFramesHavePose": all(
            bool(references[name].get("poseDetected"))
            for name in ordered_reference_names
        ),
        "takeawayTimingPlausible": (
            0.02
            <= durations["addressToTakeawaySeconds"]
            <= 0.75
        ),
        "backswingTimingPlausible": (
            0.30
            <= durations["backswingSeconds"]
            <= 3.00
        ),
        "transitionTimingPlausible": (
            0.00
            < durations["topToDownswingStartSeconds"]
            <= 0.75
        ),
        "downswingTimingPlausible": (
            0.10
            <= durations["downswingSeconds"]
            <= 1.50
        ),
        "impactTimingPlausible": (
            0.02
            <= durations[
                "downswingStartToImpactSeconds"
            ]
            <= 0.75
        ),
        "finishTimingPlausible": (
            0.10
            <= durations["impactToFinishSeconds"]
            <= 3.00
        ),
    }

    passed_check_count = sum(checks.values())
    total_check_count = len(checks)
    confidence = passed_check_count / total_check_count

    critical_checks = (
        checks["frameOrderStrictlyIncreasing"],
        checks["timestampOrderStrictlyIncreasing"],
        checks["allReferenceFramesHavePose"],
        checks["backswingTimingPlausible"],
        checks["downswingTimingPlausible"],
    )

    if all(checks.values()):
        status = "valid"
    elif all(critical_checks) and confidence >= 0.75:
        status = "review"
    else:
        status = "invalid"

    failed_checks = [
        check_name
        for check_name, passed in checks.items()
        if not passed
    ]

    return {
        "status": status,
        "confidence": round_value(confidence),
        "passedCheckCount": passed_check_count,
        "totalCheckCount": total_check_count,
        "failedChecks": failed_checks,
        "checks": checks,
        "durationsSeconds": {
            name: round_value(value)
            for name, value in durations.items()
        },
        "thresholds": {
            "addressToTakeawaySeconds": {
                "minimum": 0.02,
                "maximum": 0.75,
            },
            "backswingSeconds": {
                "minimum": 0.30,
                "maximum": 3.00,
            },
            "topToDownswingStartSeconds": {
                "exclusiveMinimum": 0.00,
                "maximum": 0.75,
            },
            "downswingSeconds": {
                "minimum": 0.10,
                "maximum": 1.50,
            },
            "downswingStartToImpactSeconds": {
                "minimum": 0.02,
                "maximum": 0.75,
            },
            "impactToFinishSeconds": {
                "minimum": 0.10,
                "maximum": 3.00,
            },
        },
        "basis": (
            "Prototype phase-quality checks used to identify "
            "obviously invalid or questionable phase timing "
            "before downstream coaching feedback is displayed."
        ),
    }



def build_feedback_eligibility(
    phase_validation: dict[str, Any],
) -> dict[str, Any]:
    validation_status = phase_validation.get("status")
    validation_confidence = phase_validation.get("confidence")
    failed_checks = phase_validation.get("failedChecks", [])

    if validation_status == "valid":
        return {
            "eligible": True,
            "status": "eligible",
            "mode": "normal",
            "requiresDisclaimer": False,
            "reason": (
                "Phase validation passed. Coaching feedback "
                "may be displayed normally."
            ),
            "validationStatus": validation_status,
            "validationConfidence": validation_confidence,
            "failedChecks": failed_checks,
        }

    if validation_status == "review":
        return {
            "eligible": True,
            "status": "eligible_with_caution",
            "mode": "cautious",
            "requiresDisclaimer": True,
            "reason": (
                "Most phase checks passed, but one or more "
                "noncritical checks require review. Coaching "
                "feedback should be displayed with a "
                "low-confidence disclaimer."
            ),
            "validationStatus": validation_status,
            "validationConfidence": validation_confidence,
            "failedChecks": failed_checks,
        }

    return {
        "eligible": False,
        "status": "suppressed",
        "mode": "suppressed",
        "requiresDisclaimer": True,
        "reason": (
            "Phase validation failed. Coaching feedback "
            "should be hidden until a reliable swing analysis "
            "is available."
        ),
        "validationStatus": validation_status,
        "validationConfidence": validation_confidence,
        "failedChecks": failed_checks,
    }


def apply_feedback_eligibility(
    metrics: dict[str, Any],
    feedback_eligibility: dict[str, Any],
    metric_name: str = "Tempo",
) -> dict[str, Any]:
    feedback = metrics.get("feedback")

    if not isinstance(feedback, dict):
        raise ValueError(
            f"{metric_name} metrics are missing a feedback object."
        )

    gated_metrics = dict(metrics)
    gated_feedback = dict(feedback)

    mode = feedback_eligibility.get("mode")
    eligibility_reason = feedback_eligibility.get("reason")

    metric_label = metric_name.lower()

    if mode == "normal":
        gated_feedback["deliveryStatus"] = "displayed"
        gated_feedback["disclaimer"] = None

    elif mode == "cautious":
        gated_feedback["deliveryStatus"] = (
            "displayed_with_caution"
        )
        gated_feedback["disclaimer"] = (
            "Phase detection confidence is limited. Treat this "
            f"{metric_label} feedback as a preliminary observation "
            "and review the detected phase frames before relying "
            "on it."
        )

    else:
        original_status = gated_feedback.get("status")

        gated_feedback["status"] = "suppressed"
        gated_feedback["originalStatus"] = original_status
        gated_feedback["deliveryStatus"] = "suppressed"
        gated_feedback["message"] = None
        gated_feedback["disclaimer"] = (
            f"{metric_name} coaching feedback was suppressed "
            "because the detected swing phases did not pass "
            "validation."
        )

    gated_feedback["eligibilityReason"] = eligibility_reason
    gated_metrics["feedback"] = gated_feedback

    return gated_metrics


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


def build_arm_metrics(
    references: dict[str, dict[str, Any]],
    handedness: Handedness,
) -> dict[str, Any]:
    mapping = get_arm_mapping(handedness)

    arm_metrics: dict[str, Any] = {
        "handednessAssumption": handedness,
        "mapping": mapping,
    }

    for arm_name, geometry_key in mapping.items():
        values: dict[str, float | None] = {}

        for reference_name in REFERENCE_NAMES:
            geometry = references[reference_name]["geometry"]
            value = geometry.get(geometry_key)

            values[reference_name] = (
                round_value(float(value))
                if isinstance(value, (int, float))
                else None
            )

        arm_metrics[arm_name] = {
            "measurement": geometry_key,
            "anglesDegrees": values,
            "addressToTopChange": angle_delta(
                values["addressReference"],
                values["topOfBackswing"],
            ),
            "addressToImpactChange": angle_delta(
                values["addressReference"],
                values["impactReference"],
            ),
            "topToImpactChange": angle_delta(
                values["topOfBackswing"],
                values["impactReference"],
            ),
        }

    return arm_metrics

def build_address_posture_metrics(
    references: dict[str, dict[str, Any]],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    address_reference = references.get("addressReference")

    if not isinstance(address_reference, dict):
        raise ValueError("Address reference is missing.")

    geometry = address_reference.get("geometry")

    if not isinstance(geometry, dict):
        raise ValueError(
            "Address reference geometry is missing."
        )

    spine_angle = geometry.get("spineAngle")
    shoulder_tilt = geometry.get("shoulderTilt")
    hip_tilt = geometry.get("hipTilt")

    head_center = geometry.get("headCenter")
    shoulder_center = geometry.get("shoulderCenter")
    hip_center = geometry.get("hipCenter")

    measurements = {
        "spineAngleDegrees": (
            round_value(float(spine_angle))
            if isinstance(spine_angle, (int, float))
            else None
        ),
        "shoulderTiltDegrees": (
            round_value(float(shoulder_tilt))
            if isinstance(shoulder_tilt, (int, float))
            else None
        ),
        "hipTiltDegrees": (
            round_value(float(hip_tilt))
            if isinstance(hip_tilt, (int, float))
            else None
        ),
        "headToHipOffset": normalized_point_delta(
            hip_center,
            head_center,
            frame_width,
            frame_height,
        ),
        "shoulderToHipOffset": normalized_point_delta(
            hip_center,
            shoulder_center,
            frame_width,
            frame_height,
        ),
    }

    available_measurements = (
        measurements["spineAngleDegrees"],
        measurements["shoulderTiltDegrees"],
        measurements["hipTiltDegrees"],
        measurements["headToHipOffset"][
            "distanceNormalized"
        ],
        measurements["shoulderToHipOffset"][
            "distanceNormalized"
        ],
    )

    available_measurement_count = sum(
        measurement is not None
        for measurement in available_measurements
    )

    total_measurement_count = len(available_measurements)

    completeness = (
        available_measurement_count
        / total_measurement_count
    )

    confidence = completeness

    if not address_reference.get("poseDetected"):
        confidence *= 0.75

    def classify_range(
        *,
        value: float | None,
        minimum: float,
        maximum: float,
        below_status: str,
        above_status: str,
        within_message: str,
        below_message: str,
        above_message: str,
    ) -> dict[str, Any]:
        if value is None:
            return {
                "status": "not_available",
                "value": None,
                "targetRange": {
                    "minimum": minimum,
                    "maximum": maximum,
                },
                "message": (
                    "This posture measurement was not available "
                    "for the address frame."
                ),
            }

        if value < minimum:
            status = below_status
            message = below_message
        elif value > maximum:
            status = above_status
            message = above_message
        else:
            status = "within_target"
            message = within_message

        return {
            "status": status,
            "value": round_value(value),
            "targetRange": {
                "minimum": minimum,
                "maximum": maximum,
            },
            "message": message,
        }

    spine_finding = classify_range(
        value=measurements["spineAngleDegrees"],
        minimum=35.0,
        maximum=50.0,
        below_status="too_upright",
        above_status="too_bent",
        within_message=(
            "Your measured spine angle is within the prototype "
            "address-posture target range."
        ),
        below_message=(
            "Your measured spine angle appears relatively upright. "
            "Additional forward bend from the hips may create a "
            "more athletic address posture."
        ),
        above_message=(
            "Your measured spine angle shows substantial forward "
            "bend. Reducing excessive bend may help you maintain "
            "balance and space during the swing."
        ),
    )

    shoulder_tilt_finding = classify_range(
        value=(
            abs(measurements["shoulderTiltDegrees"])
            if measurements["shoulderTiltDegrees"] is not None
            else None
        ),
        minimum=0.0,
        maximum=15.0,
        below_status="too_level",
        above_status="excessive_tilt",
        within_message=(
            "Your measured shoulder tilt is within the prototype "
            "address-posture target range."
        ),
        below_message=(
            "Your shoulders appear nearly level at address."
        ),
        above_message=(
            "Your measured shoulder tilt appears pronounced at "
            "address. Confirm that the setup is balanced and not "
            "excessively tilted."
        ),
    )

    hip_tilt_finding = classify_range(
        value=(
            abs(measurements["hipTiltDegrees"])
            if measurements["hipTiltDegrees"] is not None
            else None
        ),
        minimum=0.0,
        maximum=10.0,
        below_status="too_level",
        above_status="excessive_tilt",
        within_message=(
            "Your measured hip tilt is within the prototype "
            "address-posture target range."
        ),
        below_message=(
            "Your hips appear nearly level at address."
        ),
        above_message=(
            "Your measured hip tilt appears pronounced at address. "
            "Confirm that your lower-body setup remains balanced."
        ),
    )

    head_horizontal_offset = measurements[
        "headToHipOffset"
    ]["deltaXNormalized"]

    head_position_finding = classify_range(
        value=(
            abs(head_horizontal_offset)
            if isinstance(
                head_horizontal_offset,
                (int, float),
            )
            else None
        ),
        minimum=0.0,
        maximum=0.12,
        below_status="centered",
        above_status="excessive_horizontal_offset",
        within_message=(
            "Your head is positioned within the prototype "
            "horizontal alignment range relative to your hips."
        ),
        below_message=(
            "Your head is centered relative to your hips."
        ),
        above_message=(
            "Your head appears significantly offset from your hip "
            "center at address. Check your balance and lateral setup."
        ),
    )

    shoulder_horizontal_offset = measurements[
        "shoulderToHipOffset"
    ]["deltaXNormalized"]

    shoulder_position_finding = classify_range(
        value=(
            abs(shoulder_horizontal_offset)
            if isinstance(
                shoulder_horizontal_offset,
                (int, float),
            )
            else None
        ),
        minimum=0.0,
        maximum=0.10,
        below_status="centered",
        above_status="excessive_horizontal_offset",
        within_message=(
            "Your shoulders are horizontally aligned within the "
            "prototype range relative to your hips."
        ),
        below_message=(
            "Your shoulders are centered relative to your hips."
        ),
        above_message=(
            "Your shoulder center appears significantly offset from "
            "your hip center. Check for excessive lateral lean."
        ),
    )

    findings = {
        "spineAngle": spine_finding,
        "shoulderTilt": shoulder_tilt_finding,
        "hipTilt": hip_tilt_finding,
        "headPosition": head_position_finding,
        "shoulderPosition": shoulder_position_finding,
    }

    issue_names = [
        finding_name
        for finding_name, finding in findings.items()
        if finding["status"]
        not in {
            "within_target",
            "centered",
            "not_available",
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
        feedback_message = findings[primary_issue]["message"]
    elif unavailable_count > 0:
        classification = "incomplete"
        feedback_status = "insufficient_data"
        primary_issue = None
        feedback_message = (
            "Some address-posture measurements were unavailable. "
            "Review the address frame before relying on this result."
        )
    else:
        classification = "neutral"
        feedback_status = "within_target"
        primary_issue = None
        feedback_message = (
            "Your measured address posture is within the current "
            "prototype target ranges."
        )

    return {
        "referenceFrame": {
            "name": "addressReference",
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
                "Prototype heuristic ranges used to organize "
                "address-posture observations. These ranges are "
                "not universal golf instruction standards."
            ),
        },
    }

def calculate_maximum_center_movement(
    frames: list[dict[str, Any]],
    reference_geometry: dict[str, Any],
    center_name: str,
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    reference_point = reference_geometry.get(center_name)

    maximum_distance = -1.0
    maximum_result: dict[str, Any] | None = None

    for frame in frames:
        if not frame.get("poseDetected"):
            continue

        geometry = frame.get("geometry")

        if not isinstance(geometry, dict):
            continue

        current_point = geometry.get(center_name)

        movement = normalized_point_delta(
            reference_point,
            current_point,
            frame_width,
            frame_height,
        )

        distance_pixels = movement["distancePixels"]

        if not isinstance(distance_pixels, (int, float)):
            continue

        if distance_pixels > maximum_distance:
            maximum_distance = float(distance_pixels)

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


def calculate_angle_ranges(
    frames: list[dict[str, Any]],
) -> dict[str, Any]:
    ranges: dict[str, Any] = {}

    for angle_name in ANGLE_NAMES:
        values: list[tuple[int, float, float | None]] = []

        for frame in frames:
            geometry = frame.get("geometry")

            if not isinstance(geometry, dict):
                continue

            value = geometry.get(angle_name)

            if not isinstance(value, (int, float)):
                continue

            values.append(
                (
                    int(frame["frameIndex"]),
                    float(value),
                    frame.get("timestampSeconds"),
                )
            )

        if not values:
            ranges[angle_name] = {
                "minimum": None,
                "minimumFrame": None,
                "maximum": None,
                "maximumFrame": None,
                "range": None,
            }
            continue

        minimum = min(values, key=lambda item: item[1])
        maximum = max(values, key=lambda item: item[1])

        ranges[angle_name] = {
            "minimum": round_value(minimum[1]),
            "minimumFrame": minimum[0],
            "minimumTimeSeconds": minimum[2],
            "maximum": round_value(maximum[1]),
            "maximumFrame": maximum[0],
            "maximumTimeSeconds": maximum[2],
            "range": round_value(
                maximum[1] - minimum[1]
            ),
        }

    return ranges


def count_available_reference_measurements(
    references: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    available = 0
    total = 0

    for reference in references.values():
        geometry = reference["geometry"]

        for center_name in CENTER_NAMES:
            total += 1

            if geometry.get(center_name) is not None:
                available += 1

        for angle_name in ANGLE_NAMES:
            total += 1

            if geometry.get(angle_name) is not None:
                available += 1

    return available, total


def derive_output_path(
    geometry_path: Path,
) -> Path:
    filename = geometry_path.name

    suffix = "-geometry-analysis.json"

    if filename.endswith(suffix):
        prefix = filename[: -len(suffix)]
        output_name = f"{prefix}-golf-metrics.json"
    else:
        output_name = (
            f"{geometry_path.stem}-golf-metrics.json"
        )

    return geometry_path.with_name(output_name)

def build_registered_tempo(
    context: MetricContext,
) -> dict[str, Any]:
    return build_tempo_metrics(
        context["references"]
    )


def build_registered_address_posture(
    context: MetricContext,
) -> dict[str, Any]:
    return build_address_posture_metrics(
        references=context["references"],
        frame_width=context["frame_width"],
        frame_height=context["frame_height"],
    )


def build_registered_impact_position(
    context: MetricContext,
) -> dict[str, Any]:
    return build_impact_position_metrics(
        references=context["references"],
        frame_width=context["frame_width"],
        frame_height=context["frame_height"],
        handedness=context["handedness"],
    )


def build_registered_early_extension(
    context: MetricContext,
) -> dict[str, Any]:
    return build_early_extension_metrics(
        references=context["references"],
        frame_width=context["frame_width"],
        frame_height=context["frame_height"],
    )


def build_registered_head_stability(
    context: MetricContext,
) -> dict[str, Any]:
    return build_head_stability_metrics(
        references=context["references"],
        frames=context["frames"],
        frame_width=context["frame_width"],
        frame_height=context["frame_height"],
    )


def build_registered_weight_shift(
    context: MetricContext,
) -> dict[str, Any]:
    return build_weight_shift_metrics(
        references=context["references"],
        frame_width=context["frame_width"],
        frame_height=context["frame_height"],
    )


def build_registered_rotation(
    context: MetricContext,
) -> dict[str, Any]:
    return build_rotation_metrics(
        references=context["references"],
    )

def build_registered_shaft_lean(
    context: MetricContext,
) -> dict[str, Any]:
    return build_shaft_lean_metrics(
        club_detection=context[
            "club_detection"
        ],
    )


def build_registered_swing_plane(
    context: MetricContext,
) -> dict[str, Any]:
    return build_swing_plane_metrics(
        club_detection=context[
            "club_detection"
        ],
    )


METRIC_DEFINITIONS = (
    MetricDefinition(
        key="tempo",
        display_name="Tempo",
        builder=build_registered_tempo,
        summary_fields=(
            SummaryField(
                output_key="tempoRatio",
                value_path=(
                    "backswingToDownswingRatio",
                ),
            ),
            SummaryField(
                output_key="tempoClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="tempoConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key="tempoStatus",
                value_path=("feedback", "status"),
            ),
        ),
    ),
    MetricDefinition(
        key="addressPosture",
        display_name="Address posture",
        builder=build_registered_address_posture,
        summary_fields=(
            SummaryField(
                output_key="addressPostureClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="addressPostureConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key="addressPostureIssueCount",
                value_path=("issueCount",),
            ),
            SummaryField(
                output_key="addressPosturePrimaryIssue",
                value_path=("primaryIssue",),
            ),
            SummaryField(
                output_key="addressPostureFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "addressPostureFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="impactPosition",
        display_name="Impact position",
        builder=build_registered_impact_position,
        summary_fields=(
            SummaryField(
                output_key="impactPositionClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="impactPositionConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "impactPositionMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="impactPositionFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "impactPositionFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="earlyExtension",
        display_name="Early extension",
        builder=build_registered_early_extension,
        summary_fields=(
            SummaryField(
                output_key="earlyExtensionClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="earlyExtensionConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "earlyExtensionMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="earlyExtensionIssueCount",
                value_path=("issueCount",),
            ),
            SummaryField(
                output_key="earlyExtensionPrimaryIssue",
                value_path=("primaryIssue",),
            ),
            SummaryField(
                output_key="earlyExtensionFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "earlyExtensionFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="headStability",
        display_name="Head stability",
        builder=build_registered_head_stability,
        summary_fields=(
            SummaryField(
                output_key="headStabilityClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="headStabilityConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "headStabilityMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="headStabilityIssueCount",
                value_path=("issueCount",),
            ),
            SummaryField(
                output_key="headStabilityPrimaryIssue",
                value_path=("primaryIssue",),
            ),
            SummaryField(
                output_key="headStabilityFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "headStabilityFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="weightShift",
        display_name="Weight shift",
        builder=build_registered_weight_shift,
        summary_fields=(
            SummaryField(
                output_key="weightShiftClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="weightShiftConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "weightShiftMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="weightShiftIssueCount",
                value_path=("issueCount",),
            ),
            SummaryField(
                output_key="weightShiftPrimaryIssue",
                value_path=("primaryIssue",),
            ),
            SummaryField(
                output_key="weightShiftFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "weightShiftFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="rotation",
        display_name="Rotation",
        builder=build_registered_rotation,
        summary_fields=(
            SummaryField(
                output_key="rotationClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="rotationConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key="rotationMeasurementCompleteness",
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="rotationIssueCount",
                value_path=("issueCount",),
            ),
            SummaryField(
                output_key="rotationPrimaryIssue",
                value_path=("primaryIssue",),
            ),
            SummaryField(
                output_key="rotationFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key="rotationFeedbackDeliveryStatus",
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="shaftLean",
        display_name="Shaft lean",
        builder=build_registered_shaft_lean,
        summary_fields=(
            SummaryField(
                output_key="shaftLeanClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="shaftLeanConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "shaftLeanMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key=(
                    "shaftLeanDegreesFromVertical"
                ),
                value_path=(
                    "measurements",
                    "signedLeanFromVerticalDegrees",
                ),
            ),
            SummaryField(
                output_key=(
                    "shaftLeanCameraRelativeDirection"
                ),
                value_path=(
                    "measurements",
                    "cameraRelativeDirection",
                ),
            ),
            SummaryField(
                output_key="shaftLeanFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "shaftLeanFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
    MetricDefinition(
        key="swingPlane",
        display_name="Swing plane",
        builder=build_registered_swing_plane,
        summary_fields=(
            SummaryField(
                output_key="swingPlaneClassification",
                value_path=("classification",),
            ),
            SummaryField(
                output_key="swingPlaneConfidence",
                value_path=("confidence",),
            ),
            SummaryField(
                output_key=(
                    "swingPlaneMeasurementCompleteness"
                ),
                value_path=(
                    "measurementCompleteness",
                    "ratio",
                ),
            ),
            SummaryField(
                output_key="swingPlaneFeedbackStatus",
                value_path=("feedback", "status"),
            ),
            SummaryField(
                output_key=(
                    "swingPlaneFeedbackDeliveryStatus"
                ),
                value_path=(
                    "feedback",
                    "deliveryStatus",
                ),
            ),
        ),
    ),
)

METRIC_SCORING_WEIGHTS = {
    "tempo": 15.0,
    "addressPosture": 10.0,
    "impactPosition": 20.0,
    "earlyExtension": 15.0,
    "headStability": 10.0,
    "weightShift": 15.0,
    "rotation": 15.0,
    "shaftLean": 0.0,
    "swingPlane": 0.0,
}


METRIC_REGISTRY = tuple(
    MetricRegistration(
        definition=definition,
        enabled=True,
        version="1.0.0",
        scoring_weight=METRIC_SCORING_WEIGHTS[
            definition.key
        ],
    )
    for definition in METRIC_DEFINITIONS
)


validate_scoring_weights(METRIC_REGISTRY)

def analyze_golf_metrics(
    geometry_path: Path,
    refined_phases_path: Path,
    club_detection_path: Path | None = None,
    output_path: Path | None = None,
    handedness: Handedness = "right",
    coaching_provider: CoachingProvider | None = None,
) -> dict[str, Any]:
    geometry_data = load_json(geometry_path)
    refined_phases_data = load_json(
        refined_phases_path
    )

    club_detection_data = (
        load_json(club_detection_path)
        if club_detection_path is not None
        else {
            "frames": [],
        }
    )

    metadata = geometry_data.get("metadata")
    orientation = geometry_data.get("orientation")

    if not isinstance(metadata, dict):
        raise ValueError(
            "Geometry analysis is missing metadata."
        )

    if not isinstance(orientation, dict):
        raise ValueError(
            "Geometry analysis is missing orientation."
        )

    frame_width, frame_height = get_rotated_dimensions(
        metadata,
        orientation,
    )

    frame_lookup = create_frame_lookup(geometry_data)

    reference_indices = get_reference_frame_indices(
        refined_phases_data
    )

    references = extract_reference_frames(
        reference_indices,
        frame_lookup,
    )

    address_reference = references["addressReference"]
    takeaway_reference = references["takeawayReference"]

    transitions = {
        "addressToTakeaway": build_transition_metrics(
            address_reference,
            takeaway_reference,
            frame_width,
            frame_height,
        ),
        "takeawayToTop": build_transition_metrics(
            takeaway_reference,
            references["topOfBackswing"],
            frame_width,
            frame_height,
        ),
        "addressToTop": build_transition_metrics(
            address_reference,
            references["topOfBackswing"],
            frame_width,
            frame_height,
        ),
        "addressToDownswingStart": (
            build_transition_metrics(
                address_reference,
                references["downswingStart"],
                frame_width,
                frame_height,
            )
        ),
        "addressToImpact": build_transition_metrics(
            address_reference,
            references["impactReference"],
            frame_width,
            frame_height,
        ),
        "addressToFinish": build_transition_metrics(
            address_reference,
            references["finishReference"],
            frame_width,
            frame_height,
        ),
        "topToImpact": build_transition_metrics(
            references["topOfBackswing"],
            references["impactReference"],
            frame_width,
            frame_height,
        ),
    }

    frames = geometry_data["frames"]

    maximum_center_movements = {
        center_name: calculate_maximum_center_movement(
            frames,
            address_reference["geometry"],
            center_name,
            frame_width,
            frame_height,
        )
        for center_name in CENTER_NAMES
    }

    available_measurements, total_measurements = (
        count_available_reference_measurements(
            references
        )
    )

    phase_validation = build_phase_validation(references)

    feedback_eligibility = build_feedback_eligibility(
        phase_validation
    )

    metric_context: MetricContext = {
        "references": references,
        "frames": frames,
        "frame_width": frame_width,
        "frame_height": frame_height,
        "handedness": handedness,
        "club_detection": (
            club_detection_data
        ),
    }

    registered_metrics = build_registered_metrics(
        registrations=METRIC_REGISTRY,
        context=metric_context,
        feedback_eligibility=feedback_eligibility,
        apply_feedback=apply_feedback_eligibility,
    )

    club_analysis_quality = (
        build_club_analysis_quality_summary(
            club_detection=club_detection_data,
            swing_plane=registered_metrics[
                "swingPlane"
            ],
        )
    )

    scoring = calculate_swing_score(
        registrations=METRIC_REGISTRY,
        metric_results=registered_metrics,
    )

    findings = build_swing_findings(
        scoring=scoring,
        metric_display_names={
            registration.definition.key: (
                registration.definition.display_name
            )
            for registration in METRIC_REGISTRY
        },
    )

    findings_data = findings.to_dict()

    recommendations = build_swing_recommendations(
        findings=findings_data,
    ).to_dict()

    report = build_swing_analysis_report(
        source_video=geometry_data.get("sourceVideo"),
        inputs={
            "geometryAnalysisPath": str(
                geometry_path.resolve()
            ),
            "refinedPhasesPath": str(
                refined_phases_path.resolve()
            ),
            "clubDetectionPath": (
                str(
                    club_detection_path.resolve()
                )
                if club_detection_path is not None
                else None
            ),
        },
        coordinate_system={
            "space": (
                "normalized-landmarks-and-rotated-video-pixels"
            ),
            "rotatedFrameWidth": frame_width,
            "rotatedFrameHeight": frame_height,
            "positiveXDirection": "image-right",
            "positiveYDirection": "image-down",
            "angleUnits": "degrees",
        },
        assumptions={
            "handedness": handedness,
            "phaseReferences": (
                "Reference frames come from the golf-specific "
                "refined phase analysis."
            ),
            "addressReference": (
                "Golf address frame selected from a sustained, "
                "plausible setup posture."
            ),
            "impactReference": (
                "Peak-motion impact reference from the refined "
                "golf phase analysis."
            ),
            "finishReference": (
                "Movement-end finish reference from the refined "
                "golf phase analysis. Finish posture validation "
                "is not yet implemented."
            ),
            "rotationMeasurements": (
                "Shoulder and hip tilt are 2D image-plane "
                "measurements, not true 3D body rotation."
            ),
            "shaftLeanMeasurement": (
                "Shaft lean is measured in the two-dimensional "
                "rotated video frame relative to image vertical. "
                "The current metric reports image-left or "
                "image-right direction and does not yet claim "
                "forward or backward shaft lean."
            ),
            "addressPostureFeedback": (
                "Address posture classifications use prototype "
                "heuristic ranges and are not universal golf "
                "instruction standards."
            ),
        },
        phase_frames={
            reference_name: {
                "frameIndex": reference["frameIndex"],
                "timestampSeconds": reference[
                    "timestampSeconds"
                ],
                "poseDetected": reference["poseDetected"],
            }
            for reference_name, reference in references.items()
        },
        reference_geometry={
            reference_name: reference["geometry"]
            for reference_name, reference in references.items()
        },
        metrics={
            "phaseValidation": phase_validation,
            "feedbackEligibility": feedback_eligibility,
            **registered_metrics,
            "transitions": transitions,
            "maximumMovementFromAddressReference": (
                maximum_center_movements
            ),
            "angleRanges": calculate_angle_ranges(frames),
            "armExtension": build_arm_metrics(
                references,
                handedness,
            ),
        },
        scoring=scoring,
        findings=findings.to_dict(),
        recommendations=recommendations,
        summary={
            "referenceFrameCount": len(references),
            "availableReferenceMeasurements": (
                available_measurements
            ),
            "totalReferenceMeasurements": total_measurements,
            "referenceMeasurementCompleteness": (
                round_value(
                    available_measurements
                    / total_measurements
                )
                if total_measurements > 0
                else None
            ),
            "allReferenceFramesHavePose": all(
                bool(reference["poseDetected"])
                for reference in references.values()
            ),
            "handednessAssumption": handedness,
            "phaseValidationStatus": phase_validation[
                "status"
            ],
            "phaseValidationConfidence": phase_validation[
                "confidence"
            ],
            "feedbackEligibilityStatus": (
                feedback_eligibility["status"]
            ),
            "coachingFeedbackEligible": (
                feedback_eligibility["eligible"]
            ),
            "clubAnalysisQuality": (
                club_analysis_quality
            ),
            "analysisEngine": (
                build_analysis_version_manifest(
                    contract_version=(
                        ANALYSIS_API_VERSION
                    ),
                    metric_versions=(
                        get_metric_versions(
                            METRIC_REGISTRY
                        )
                    ),
                    coaching_prompt_version=(
                        PROMPT_VERSION
                    ),
                )
            ),
            **build_registered_metric_summary(
                registrations=METRIC_REGISTRY,
                metric_results=registered_metrics,
            ),
        },
    )

    deterministic_result = report.to_dict()

    coach_context = build_coach_context(
        deterministic_result
    )

    provider = (
        coaching_provider
        if coaching_provider is not None
        else build_configured_coaching_provider()
    )

    coaching_response = generate_coaching_response(
        context=coach_context,
        provider=provider,
    )

    report = replace(
        report,
        coaching=coaching_response,
    )

    result = report.to_dict()

    resolved_output_path = (
        output_path
        if output_path is not None
        else derive_output_path(geometry_path)
    )

    write_json(resolved_output_path, result)

    return {
        "success": True,
        "summary": result["summary"],
        "scoring": result["scoring"],
        "phaseFrames": result["phaseFrames"],
        "coaching": result["coaching"],
        "golfMetricsPath": str(
            resolved_output_path.resolve()
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate golf-specific metrics from geometry "
            "and refined golf phase analysis files."
        )
    )

    parser.add_argument(
        "geometry_path",
        type=Path,
        help="Path to the geometry-analysis JSON file.",
    )

    parser.add_argument(
        "refined_phases_path",
        type=Path,
        help="Path to the refined-phases JSON file.",
    )

    parser.add_argument(
        "--club-detection",
        type=Path,
        default=None,
        help=(
            "Optional path to the club-detection JSON "
            "artifact used for Shaft Lean."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional output path. By default, the output "
            "is written beside the geometry-analysis file."
        ),
    )

    parser.add_argument(
        "--handedness",
        choices=("right", "left"),
        default="right",
        help=(
            "Golfer handedness used to identify lead and "
            "trail arms. Defaults to right."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        result = analyze_golf_metrics(
            geometry_path=args.geometry_path,
            refined_phases_path=args.refined_phases_path,
            club_detection_path=args.club_detection,
            output_path=args.output,
            handedness=args.handedness,
        )

        print(json.dumps(result))
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(error),
                }
            )
        )

        raise SystemExit(1) from error


if __name__ == "__main__":
    main()