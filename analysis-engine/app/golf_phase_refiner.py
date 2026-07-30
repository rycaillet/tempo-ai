from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, TypedDict


LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24

MINIMUM_VISIBILITY = 0.45
MINIMUM_PRESENCE = 0.45

MINIMUM_ADDRESS_TOP_GAP_SECONDS = 0.70
MAXIMUM_ADDRESS_SEARCH_SECONDS = 2.00

ADDRESS_STABILITY_WINDOW_SECONDS = 0.16
ADDRESS_STABLE_RUN_SECONDS = 0.12

ADDRESS_WRIST_SEPARATION_TARGET = 0.20
ADDRESS_MAXIMUM_WRIST_SEPARATION = 0.45

ADDRESS_MINIMUM_WRIST_HEIGHT = -0.20
ADDRESS_MAXIMUM_WRIST_HEIGHT = 0.40

ADDRESS_MAXIMUM_LOCAL_MOTION = 0.12

TAKEAWAY_DISPLACEMENT_THRESHOLD = 0.10
TAKEAWAY_SUSTAINED_SECONDS = 0.12

TOP_HAND_HEIGHT_MARGIN = 0.05
TOP_MAXIMUM_WRIST_SEPARATION = 0.50


class LandmarkData(TypedDict):
    index: int
    x: float
    y: float
    z: float
    visibility: float
    presence: float


class PoseFrame(TypedDict):
    frameIndex: int
    timestampMs: int
    timestampSeconds: float
    poseDetected: bool
    landmarks: list[LandmarkData]


class MotionFrame(TypedDict):
    frameIndex: int
    timestampSeconds: float
    rawMotion: float
    smoothedMotion: float
    validLandmarkCount: int


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(float(value), digits)


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(minimum, min(maximum, value))


def clamp_confidence(value: float) -> float:
    return round(clamp(value), 3)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(
            f"Unable to read JSON file {path}: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path}: {error}"
        ) from error

    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected a JSON object in {path}."
        )

    return payload


def build_landmark_map(
    frame: PoseFrame,
) -> dict[int, LandmarkData]:
    return {
        landmark["index"]: landmark
        for landmark in frame.get("landmarks", [])
    }


def visible_landmark(
    landmarks: dict[int, LandmarkData],
    index: int,
) -> LandmarkData | None:
    landmark = landmarks.get(index)

    if landmark is None:
        return None

    if landmark.get("visibility", 0.0) < MINIMUM_VISIBILITY:
        return None

    return landmark


def midpoint(
    first: LandmarkData,
    second: LandmarkData,
) -> tuple[float, float]:
    return (
        (first["x"] + second["x"]) / 2.0,
        (first["y"] + second["y"]) / 2.0,
    )


def point_distance(
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    return math.hypot(
        second[0] - first[0],
        second[1] - first[1],
    )


def calculate_body_features(
    frame: PoseFrame,
    *,
    allow_single_wrist_fallback: bool = False,
) -> dict[str, Any] | None:
    if not frame.get("poseDetected"):
        return None

    landmarks = build_landmark_map(frame)

    left_shoulder = visible_landmark(
        landmarks,
        LEFT_SHOULDER,
    )
    right_shoulder = visible_landmark(
        landmarks,
        RIGHT_SHOULDER,
    )
    left_hip = visible_landmark(
        landmarks,
        LEFT_HIP,
    )
    right_hip = visible_landmark(
        landmarks,
        RIGHT_HIP,
    )

    required_body_landmarks = (
        left_shoulder,
        right_shoulder,
        left_hip,
        right_hip,
    )

    if any(
        landmark is None
        for landmark in required_body_landmarks
    ):
        return None

    assert left_shoulder is not None
    assert right_shoulder is not None
    assert left_hip is not None
    assert right_hip is not None

    left_wrist_raw = landmarks.get(LEFT_WRIST)
    right_wrist_raw = landmarks.get(RIGHT_WRIST)

    left_wrist_visible = visible_landmark(
        landmarks,
        LEFT_WRIST,
    )
    right_wrist_visible = visible_landmark(
        landmarks,
        RIGHT_WRIST,
    )

    wrist_tracking_mode = "both-visible"

    if (
        left_wrist_visible is not None
        and right_wrist_visible is not None
    ):
        wrist_center = midpoint(
            left_wrist_visible,
            right_wrist_visible,
        )
        wrist_separation = point_distance(
            (
                left_wrist_visible["x"],
                left_wrist_visible["y"],
            ),
            (
                right_wrist_visible["x"],
                right_wrist_visible["y"],
            ),
        )
        wrist_visibility = min(
            left_wrist_visible["visibility"],
            right_wrist_visible["visibility"],
        )
    elif allow_single_wrist_fallback:
        visible_wrist = (
            left_wrist_visible
            if left_wrist_visible is not None
            else right_wrist_visible
        )
        occluded_wrist = (
            right_wrist_raw
            if left_wrist_visible is not None
            else left_wrist_raw
        )

        if visible_wrist is None or occluded_wrist is None:
            return None

        if (
            occluded_wrist.get("presence", 0.0)
            < MINIMUM_PRESENCE
        ):
            return None

        wrist_center = (
            visible_wrist["x"],
            visible_wrist["y"],
        )
        wrist_separation = point_distance(
            (
                visible_wrist["x"],
                visible_wrist["y"],
            ),
            (
                occluded_wrist["x"],
                occluded_wrist["y"],
            ),
        )
        wrist_visibility = visible_wrist["visibility"]
        wrist_tracking_mode = (
            "left-visible-single-wrist"
            if left_wrist_visible is not None
            else "right-visible-single-wrist"
        )
    else:
        return None

    shoulder_center = midpoint(
        left_shoulder,
        right_shoulder,
    )
    hip_center = midpoint(
        left_hip,
        right_hip,
    )

    torso_length = point_distance(
        shoulder_center,
        hip_center,
    )

    if torso_length <= 0.0001:
        return None

    minimum_visibility = min(
        left_shoulder["visibility"],
        right_shoulder["visibility"],
        left_hip["visibility"],
        right_hip["visibility"],
        wrist_visibility,
    )

    return {
        "shoulderCenter": shoulder_center,
        "hipCenter": hip_center,
        "wristCenter": wrist_center,
        "torsoLength": torso_length,
        "wristSeparationNormalized": (
            wrist_separation / torso_length
        ),
        "wristHeightFromShouldersNormalized": (
            wrist_center[1] - shoulder_center[1]
        )
        / torso_length,
        "wristHeightFromHipsNormalized": (
            wrist_center[1] - hip_center[1]
        )
        / torso_length,
        "minimumVisibility": minimum_visibility,
        "wristTrackingMode": wrist_tracking_mode,
    }

def estimate_fps(
    motion_frames: list[MotionFrame],
) -> float:
    differences = [
        motion_frames[index]["timestampSeconds"]
        - motion_frames[index - 1]["timestampSeconds"]
        for index in range(1, len(motion_frames))
        if (
            motion_frames[index]["timestampSeconds"]
            > motion_frames[index - 1]["timestampSeconds"]
        )
    ]

    if not differences:
        return 30.0

    differences.sort()
    midpoint_index = len(differences) // 2

    if len(differences) % 2 == 1:
        median_difference = differences[midpoint_index]
    else:
        median_difference = (
            differences[midpoint_index - 1]
            + differences[midpoint_index]
        ) / 2.0

    if median_difference <= 0:
        return 30.0

    return 1.0 / median_difference


def create_phase_point(
    pose_frame: PoseFrame,
    confidence: float,
    method: str,
) -> dict[str, Any]:
    return {
        "frameIndex": pose_frame["frameIndex"],
        "timestampSeconds": round(
            pose_frame["timestampSeconds"],
            3,
        ),
        "confidence": clamp_confidence(confidence),
        "method": method,
    }


def calculate_local_raw_motion(
    motion_frames: list[MotionFrame],
    center_index: int,
    radius: int,
) -> float:
    start_index = max(0, center_index - radius)
    end_index = min(
        len(motion_frames),
        center_index + radius + 1,
    )

    values = [
        frame["rawMotion"]
        for frame in motion_frames[start_index:end_index]
        if frame["validLandmarkCount"] > 0
    ]

    if not values:
        return float("inf")

    return sum(values) / len(values)

def calculate_wrist_displacement(
    first_features: dict[str, Any],
    second_features: dict[str, Any],
) -> float:
    torso_length = first_features["torsoLength"]

    if torso_length <= 0.0001:
        return 0.0

    return (
        point_distance(
            first_features["wristCenter"],
            second_features["wristCenter"],
        )
        / torso_length
    )

def address_position_score(
    features: dict[str, Any],
) -> float:
    wrist_separation = features[
        "wristSeparationNormalized"
    ]

    separation_error = abs(
        wrist_separation
        - ADDRESS_WRIST_SEPARATION_TARGET
    )

    separation_score = 1.0 - clamp(
        separation_error
        / ADDRESS_MAXIMUM_WRIST_SEPARATION
    )

    wrist_below_shoulders = (
        features["wristHeightFromShouldersNormalized"]
        > -0.05
    )
    wrist_near_or_above_hips = (
        features["wristHeightFromHipsNormalized"]
        < 0.35
    )

    vertical_score = (
        float(wrist_below_shoulders)
        + float(wrist_near_or_above_hips)
    ) / 2.0

    visibility_score = clamp(
        (
            features["minimumVisibility"]
            - MINIMUM_VISIBILITY
        )
        / (1.0 - MINIMUM_VISIBILITY)
    )

    return (
        0.45 * separation_score
        + 0.35 * vertical_score
        + 0.20 * visibility_score
    )

def find_true_runs(
    values: list[bool],
) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    run_start: int | None = None

    for index, value in enumerate(values):
        if value and run_start is None:
            run_start = index

        elif not value and run_start is not None:
            runs.append(
                (run_start, index - 1)
            )
            run_start = None

    if run_start is not None:
        runs.append(
            (run_start, len(values) - 1)
        )

    return runs

def find_address_reference(
    pose_frames: list[PoseFrame],
    motion_frames: list[MotionFrame],
    top_frame_index: int,
    estimated_fps: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pose_by_frame = {
        frame["frameIndex"]: frame
        for frame in pose_frames
    }

    top_motion_index = next(
        (
            index
            for index, frame in enumerate(motion_frames)
            if frame["frameIndex"] == top_frame_index
        ),
        None,
    )

    if top_motion_index is None:
        raise ValueError(
            "Top-of-backswing frame was not found "
            "in the motion timeline."
        )

    minimum_top_gap_frames = max(
        1,
        round(
            estimated_fps
            * MINIMUM_ADDRESS_TOP_GAP_SECONDS
        ),
    )

    maximum_search_frames = max(
        1,
        round(
            estimated_fps
            * MAXIMUM_ADDRESS_SEARCH_SECONDS
        ),
    )

    stable_run_frames = max(
        2,
        round(
            estimated_fps
            * ADDRESS_STABLE_RUN_SECONDS
        ),
    )

    stability_radius = max(
        1,
        round(
            estimated_fps
            * ADDRESS_STABILITY_WINDOW_SECONDS
            / 2.0
        ),
    )

    search_end_index = max(
        0,
        top_motion_index - minimum_top_gap_frames,
    )

    search_start_index = max(
        0,
        search_end_index - maximum_search_frames,
    )

    candidate_data: dict[int, dict[str, Any]] = {}
    plausible_address_flags: list[bool] = []

    missing_pose_frame_count = 0
    unreliable_feature_frame_count = 0
    posture_valid_frame_count = 0
    stability_valid_frame_count = 0

    wrist_separation_values: list[float] = []
    wrist_height_values: list[float] = []
    local_motion_values: list[float] = []

    for motion_index in range(
        search_start_index,
        search_end_index + 1,
    ):
        motion_frame = motion_frames[motion_index]
        pose_frame = pose_by_frame.get(
            motion_frame["frameIndex"]
        )

        if pose_frame is None:
            missing_pose_frame_count += 1
            plausible_address_flags.append(False)
            continue

        features = calculate_body_features(
            pose_frame,
            allow_single_wrist_fallback=True,
        )

        if features is None:
            unreliable_feature_frame_count += 1
            plausible_address_flags.append(False)
            continue

        local_motion = calculate_local_raw_motion(
            motion_frames,
            motion_index,
            stability_radius,
        )

        wrist_separation = features[
            "wristSeparationNormalized"
        ]
        wrist_height = features[
            "wristHeightFromShouldersNormalized"
        ]

        wrist_separation_values.append(
            wrist_separation
        )
        wrist_height_values.append(
            wrist_height
        )

        if math.isfinite(local_motion):
            local_motion_values.append(local_motion)

        plausible_posture = (
            wrist_separation
            <= ADDRESS_MAXIMUM_WRIST_SEPARATION
            and ADDRESS_MINIMUM_WRIST_HEIGHT
            <= wrist_height
            <= ADDRESS_MAXIMUM_WRIST_HEIGHT
        )

        stable_enough = (
            local_motion
            <= ADDRESS_MAXIMUM_LOCAL_MOTION
        )

        if plausible_posture:
            posture_valid_frame_count += 1

        if stable_enough:
            stability_valid_frame_count += 1

        is_plausible = (
            plausible_posture
            and stable_enough
        )

        plausible_address_flags.append(is_plausible)

        candidate_data[motion_index] = {
            "poseFrame": pose_frame,
            "features": features,
            "localRawMotion": local_motion,
            "positionScore": address_position_score(
                features
            ),
            "isPlausible": is_plausible,
        }

    all_plausible_runs = find_true_runs(
        plausible_address_flags
    )

    stable_runs = [
        run
        for run in all_plausible_runs
        if run[1] - run[0] + 1 >= stable_run_frames
    ]

    if not stable_runs:
        longest_plausible_run = max(
            (
                run_end - run_start + 1
                for run_start, run_end
                in all_plausible_runs
            ),
            default=0,
        )

        failure_diagnostics = {
            "estimatedFps": round_value(
                estimated_fps
            ),
            "searchStartFrame": (
                motion_frames[
                    search_start_index
                ]["frameIndex"]
            ),
            "searchEndFrame": (
                motion_frames[
                    search_end_index
                ]["frameIndex"]
            ),
            "searchedFrameCount": (
                search_end_index
                - search_start_index
                + 1
            ),
            "requiredStableFrames": (
                stable_run_frames
            ),
            "longestPlausibleRunFrames": (
                longest_plausible_run
            ),
            "missingPoseFrameCount": (
                missing_pose_frame_count
            ),
            "unreliableFeatureFrameCount": (
                unreliable_feature_frame_count
            ),
            "reliableFeatureFrameCount": len(
                candidate_data
            ),
            "postureValidFrameCount": (
                posture_valid_frame_count
            ),
            "stabilityValidFrameCount": (
                stability_valid_frame_count
            ),
            "fullyPlausibleFrameCount": sum(
                plausible_address_flags
            ),
            "wristSeparationRange": {
                "minimum": round_value(
                    min(wrist_separation_values)
                )
                if wrist_separation_values
                else None,
                "maximum": round_value(
                    max(wrist_separation_values)
                )
                if wrist_separation_values
                else None,
                "allowedMaximum": (
                    ADDRESS_MAXIMUM_WRIST_SEPARATION
                ),
            },
            "wristHeightFromShouldersRange": {
                "minimum": round_value(
                    min(wrist_height_values)
                )
                if wrist_height_values
                else None,
                "maximum": round_value(
                    max(wrist_height_values)
                )
                if wrist_height_values
                else None,
                "allowedMinimum": (
                    ADDRESS_MINIMUM_WRIST_HEIGHT
                ),
                "allowedMaximum": (
                    ADDRESS_MAXIMUM_WRIST_HEIGHT
                ),
            },
            "localRawMotionRange": {
                "minimum": round_value(
                    min(local_motion_values)
                )
                if local_motion_values
                else None,
                "maximum": round_value(
                    max(local_motion_values)
                )
                if local_motion_values
                else None,
                "allowedMaximum": (
                    ADDRESS_MAXIMUM_LOCAL_MOTION
                ),
            },
        }

        diagnostic_text = json.dumps(
            failure_diagnostics,
            sort_keys=True,
        )

        raise ValueError(
            "No sustained, plausible address posture "
            "was found before the backswing. "
            f"Diagnostics: {diagnostic_text}"
        )

    absolute_runs = [
        (
            search_start_index + run_start,
            search_start_index + run_end,
        )
        for run_start, run_end in stable_runs
    ]

    selected_run = absolute_runs[0]

    address_index = selected_run[0]
    selected_candidate = candidate_data.get(
        address_index
    )

    if selected_candidate is None:
        raise ValueError(
            "Selected address frame did not contain "
            "reliable pose data."
        )

    pose_frame = selected_candidate["poseFrame"]
    features = selected_candidate["features"]
    local_motion = selected_candidate[
        "localRawMotion"
    ]
    position_score = selected_candidate[
        "positionScore"
    ]

    stability_score = 1.0 - clamp(
        local_motion
        / ADDRESS_MAXIMUM_LOCAL_MOTION
    )

    run_length = (
        selected_run[1] - selected_run[0] + 1
    )

    run_score = clamp(
        run_length
        / max(stable_run_frames * 2, 1)
    )

    confidence = (
        0.50 * position_score
        + 0.30 * stability_score
        + 0.20 * run_score
    )

    phase_point = create_phase_point(
        pose_frame,
        confidence,
        "first-frame-of-stable-address-posture-run",
    )

    diagnostics = {
        "addressRunStartFrame": (
            motion_frames[
                selected_run[0]
            ]["frameIndex"]
        ),
        "addressRunEndFrame": (
            motion_frames[
                selected_run[1]
            ]["frameIndex"]
        ),
        "addressRunFrameCount": run_length,
        "requiredStableFrames": stable_run_frames,
        "searchStartFrame": (
            motion_frames[
                search_start_index
            ]["frameIndex"]
        ),
        "searchEndFrame": (
            motion_frames[
                search_end_index
            ]["frameIndex"]
        ),
        "localRawMotion": round_value(
            local_motion
        ),
        "positionScore": round_value(
            position_score
        ),
        "stabilityScore": round_value(
            stability_score
        ),
        "runScore": round_value(
            run_score
        ),
        "wristSeparationNormalized": round_value(
            features[
                "wristSeparationNormalized"
            ]
        ),
        "wristHeightFromShouldersNormalized": (
            round_value(
                features[
                    "wristHeightFromShouldersNormalized"
                ]
            )
        ),
        "wristHeightFromHipsNormalized": round_value(
            features[
                "wristHeightFromHipsNormalized"
            ]
        ),
        "minimumLandmarkVisibility": round_value(
            features["minimumVisibility"]
        ),
        "plausibleRunCount": len(
            absolute_runs
        ),
    }

    return phase_point, diagnostics


def find_takeaway_reference(
    pose_frames: list[PoseFrame],
    motion_frames: list[MotionFrame],
    address_frame_index: int,
    top_frame_index: int,
    estimated_fps: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    pose_by_frame = {
        frame["frameIndex"]: frame
        for frame in pose_frames
    }

    motion_index_by_frame = {
        frame["frameIndex"]: index
        for index, frame in enumerate(motion_frames)
    }

    address_pose = pose_by_frame.get(
        address_frame_index
    )
    address_motion_index = motion_index_by_frame.get(
        address_frame_index
    )
    top_motion_index = motion_index_by_frame.get(
        top_frame_index
    )

    if (
        address_pose is None
        or address_motion_index is None
        or top_motion_index is None
    ):
        return None, {
            "reason": (
                "Address or top frame was unavailable."
            )
        }

    address_features = calculate_body_features(
        address_pose,
        allow_single_wrist_fallback=True,
    )

    if address_features is None:
        return None, {
            "reason": (
                "Address frame did not contain reliable "
                "body landmarks."
            )
        }

    address_wrist_center = address_features[
        "wristCenter"
    ]
    address_torso_length = address_features[
        "torsoLength"
    ]

    sustained_frames = max(
        2,
        round(
            estimated_fps
            * TAKEAWAY_SUSTAINED_SECONDS
        ),
    )

    qualifying: list[bool] = []
    candidate_data: list[dict[str, Any] | None] = []

    for motion_index in range(
        address_motion_index + 1,
        top_motion_index,
    ):
        motion_frame = motion_frames[motion_index]
        pose_frame = pose_by_frame.get(
            motion_frame["frameIndex"]
        )

        if pose_frame is None:
            qualifying.append(False)
            candidate_data.append(None)
            continue

        features = calculate_body_features(
            pose_frame,
            allow_single_wrist_fallback=True,
        )

        if features is None:
            qualifying.append(False)
            candidate_data.append(None)
            continue

        displacement = (
            point_distance(
                address_wrist_center,
                features["wristCenter"],
            )
            / address_torso_length
        )

        qualifies = (
            displacement
            >= TAKEAWAY_DISPLACEMENT_THRESHOLD
            and motion_frame["rawMotion"] > 0
        )

        qualifying.append(qualifies)
        candidate_data.append({
            "poseFrame": pose_frame,
            "features": features,
            "displacement": displacement,
            "rawMotion": motion_frame["rawMotion"],
        })

    for index in range(
        0,
        len(qualifying) - sustained_frames + 1,
    ):
        window = qualifying[
            index:index + sustained_frames
        ]

        if not all(window):
            continue

        candidate = candidate_data[index]

        if candidate is None:
            continue

        displacement_score = clamp(
            candidate["displacement"]
            / (
                TAKEAWAY_DISPLACEMENT_THRESHOLD
                * 2.0
            )
        )

        visibility_score = clamp(
            candidate["features"][
                "minimumVisibility"
            ]
        )

        confidence = (
            0.65 * displacement_score
            + 0.35 * visibility_score
        )

        phase_point = create_phase_point(
            candidate["poseFrame"],
            confidence,
            "sustained-wrist-displacement-from-address",
        )

        diagnostics = {
            "wristDisplacementNormalized": round_value(
                candidate["displacement"]
            ),
            "rawMotion": round_value(
                candidate["rawMotion"]
            ),
            "sustainedFrames": sustained_frames,
            "minimumLandmarkVisibility": round_value(
                candidate["features"][
                    "minimumVisibility"
                ]
            ),
        }

        return phase_point, diagnostics

    return None, {
        "reason": (
            "No sustained takeaway displacement "
            "was detected."
        ),
        "sustainedFramesRequired": sustained_frames,
        "displacementThreshold": (
            TAKEAWAY_DISPLACEMENT_THRESHOLD
        ),
    }


def validate_top_reference(
    pose_frames: list[PoseFrame],
    motion_frames: list[MotionFrame],
    top_candidate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    frame_index = int(
        top_candidate["frameIndex"]
    )

    pose_frame = next(
        (
            frame
            for frame in pose_frames
            if frame["frameIndex"] == frame_index
        ),
        None,
    )

    motion_frame = next(
        (
            frame
            for frame in motion_frames
            if frame["frameIndex"] == frame_index
        ),
        None,
    )

    if pose_frame is None or motion_frame is None:
        return top_candidate, {
            "validated": False,
            "reason": (
                "Top candidate frame was unavailable."
            ),
        }

    features = calculate_body_features(pose_frame)

    if features is None:
        return top_candidate, {
            "validated": False,
            "reason": (
                "Top candidate lacked reliable landmarks."
            ),
        }

    hands_above_shoulders = (
        features[
            "wristHeightFromShouldersNormalized"
        ]
        <= TOP_HAND_HEIGHT_MARGIN
    )

    wrists_close = (
        features["wristSeparationNormalized"]
        <= TOP_MAXIMUM_WRIST_SEPARATION
    )

    low_motion = (
        motion_frame["smoothedMotion"]
        <= 0.02
    )

    validation_score = (
        0.40 * float(hands_above_shoulders)
        + 0.30 * float(wrists_close)
        + 0.30 * float(low_motion)
    )

    original_confidence = float(
        top_candidate.get("confidence", 0.5)
    )

    confidence = (
        0.50 * original_confidence
        + 0.50 * validation_score
    )

    refined_point = {
        **top_candidate,
        "confidence": clamp_confidence(confidence),
        "method": (
            "motion-minimum-with-golf-posture-validation"
        ),
    }

    diagnostics = {
        "validated": (
            hands_above_shoulders
            and wrists_close
            and low_motion
        ),
        "handsAboveShoulders": hands_above_shoulders,
        "wristsClose": wrists_close,
        "lowMotion": low_motion,
        "wristSeparationNormalized": round_value(
            features["wristSeparationNormalized"]
        ),
        "wristHeightFromShouldersNormalized": round_value(
            features[
                "wristHeightFromShouldersNormalized"
            ]
        ),
        "rawMotion": round_value(
            motion_frame["rawMotion"]
        ),
        "smoothedMotion": round_value(
            motion_frame["smoothedMotion"]
        ),
        "validationScore": round_value(
            validation_score
        ),
    }

    return refined_point, diagnostics


def create_output_path(
    motion_path: Path,
) -> Path:
    filename = motion_path.name

    if filename.endswith("-motion-analysis.json"):
        filename = filename.replace(
            "-motion-analysis.json",
            "-refined-phases.json",
        )
    else:
        filename = (
            f"{motion_path.stem}-refined-phases.json"
        )

    return motion_path.parent / filename


def refine_golf_phases(
    pose_payload: dict[str, Any],
    motion_payload: dict[str, Any],
) -> dict[str, Any]:
    pose_frames = pose_payload.get("frames")
    motion_frames = motion_payload.get("frames")
    phase_candidates = motion_payload.get(
        "phaseCandidates"
    )

    if not isinstance(pose_frames, list):
        raise ValueError(
            "Pose timeline does not contain frames."
        )

    if not isinstance(motion_frames, list):
        raise ValueError(
            "Motion analysis does not contain frames."
        )

    if not isinstance(phase_candidates, dict):
        raise ValueError(
            "Motion analysis does not contain "
            "phase candidates."
        )

    top_candidate = phase_candidates.get(
        "topOfBackswing"
    )

    if not isinstance(top_candidate, dict):
        raise ValueError(
            "Motion analysis does not contain a "
            "top-of-backswing candidate."
        )

    estimated_fps = estimate_fps(motion_frames)

    refined_top, top_diagnostics = (
        validate_top_reference(
            pose_frames,
            motion_frames,
            top_candidate,
        )
    )

    address, address_diagnostics = (
        find_address_reference(
            pose_frames,
            motion_frames,
            int(refined_top["frameIndex"]),
            estimated_fps,
        )
    )

    takeaway, takeaway_diagnostics = (
        find_takeaway_reference(
            pose_frames,
            motion_frames,
            int(address["frameIndex"]),
            int(refined_top["frameIndex"]),
            estimated_fps,
        )
    )

    downswing_start = phase_candidates.get(
        "downswingStart"
    )
    impact_zone = phase_candidates.get(
        "impactZone"
    )
    movement_end = phase_candidates.get(
        "movementEnd"
    )

    refined_phases = {
        "address": address,
        "takeaway": takeaway,
        "topOfBackswing": refined_top,
        "downswingStart": downswing_start,
        "impactReference": (
            {
                "frameIndex": impact_zone[
                    "peakFrame"
                ],
                "timestampSeconds": impact_zone[
                    "peakTimeSeconds"
                ],
                "confidence": impact_zone[
                    "confidence"
                ],
                "method": (
                    "peak-of-motion-impact-zone"
                ),
            }
            if isinstance(impact_zone, dict)
            else None
        ),
        "finishReference": (
            {
                **movement_end,
                "method": (
                    "motion-run-end-unvalidated"
                ),
            }
            if isinstance(movement_end, dict)
            else None
        ),
    }

    phase_sequence = [
        phase
        for phase in (
            refined_phases["address"],
            refined_phases["takeaway"],
            refined_phases["topOfBackswing"],
            refined_phases["downswingStart"],
            refined_phases["impactReference"],
            refined_phases["finishReference"],
        )
        if isinstance(phase, dict)
    ]

    sequence_is_chronological = all(
        phase_sequence[index]["frameIndex"]
        < phase_sequence[index + 1]["frameIndex"]
        for index in range(
            len(phase_sequence) - 1
        )
    )

    return {
        "sourceVideo": pose_payload.get(
            "sourceVideo"
        ),
        "assumptions": {
            "cameraView": (
                "Golf posture rules currently assume a "
                "single visible golfer and a stable camera."
            ),
            "address": (
                "Selected from pre-top posture, hand "
                "position, wrist separation, and local "
                "raw-motion stability."
            ),
            "takeaway": (
                "First sustained wrist-center displacement "
                "from the selected address frame."
            ),
            "topOfBackswing": (
                "Existing motion minimum validated with "
                "hand height, wrist separation, and motion."
            ),
            "impactReference": (
                "Still based on the peak-motion impact zone."
            ),
            "finishReference": (
                "Still based on movement end and remains "
                "unvalidated."
            ),
        },
        "summary": {
            "estimatedFps": round(
                estimated_fps,
                3,
            ),
            "phaseCount": sum(
                phase is not None
                for phase in refined_phases.values()
            ),
            "sequenceIsChronological": (
                sequence_is_chronological
            ),
            "topValidated": top_diagnostics.get(
                "validated",
                False,
            ),
            "addressConfidence": address[
                "confidence"
            ],
            "takeawayDetected": (
                takeaway is not None
            ),
        },
        "phases": refined_phases,
        "diagnostics": {
            "address": address_diagnostics,
            "takeaway": takeaway_diagnostics,
            "topOfBackswing": top_diagnostics,
        },
        "originalMotionCandidates": (
            phase_candidates
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refine general motion candidates into "
            "golf-specific swing phase references."
        )
    )

    parser.add_argument(
        "pose_timeline",
        type=Path,
        help="Path to the pose timeline JSON file.",
    )

    parser.add_argument(
        "motion_analysis",
        type=Path,
        help="Path to the motion analysis JSON file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output path. Defaults beside the "
            "motion analysis file."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    arguments = parser.parse_args()

    pose_path = (
        arguments.pose_timeline
        .expanduser()
        .resolve()
    )
    motion_path = (
        arguments.motion_analysis
        .expanduser()
        .resolve()
    )

    if not pose_path.is_file():
        parser.error(
            f"Pose timeline not found: {pose_path}"
        )

    if not motion_path.is_file():
        parser.error(
            f"Motion analysis not found: {motion_path}"
        )

    output_path = (
        arguments.output.expanduser().resolve()
        if arguments.output
        else create_output_path(motion_path)
    )

    try:
        pose_payload = load_json(pose_path)
        motion_payload = load_json(motion_path)

        result = refine_golf_phases(
            pose_payload,
            motion_payload,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
    except (ValueError, OSError) as error:
        print(json.dumps({
            "success": False,
            "error": str(error),
        }))
        raise SystemExit(1) from error

    print(json.dumps({
        "success": True,
        "summary": result["summary"],
        "phases": result["phases"],
        "refinedPhasesPath": str(output_path),
    }))


if __name__ == "__main__":
    main()