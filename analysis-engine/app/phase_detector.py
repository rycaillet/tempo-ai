from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import TypedDict

LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24

TRACKED_LANDMARK_WEIGHTS = {
    LEFT_SHOULDER: 1.0,
    RIGHT_SHOULDER: 1.0,
    LEFT_ELBOW: 1.5,
    RIGHT_ELBOW: 1.5,
    LEFT_WRIST: 2.0,
    RIGHT_WRIST: 2.0,
    LEFT_HIP: 1.0,
    RIGHT_HIP: 1.0,
}

MINIMUM_VISIBILITY = 0.45
SMOOTHING_WINDOW_SIZE = 7
MINIMUM_VALID_LANDMARKS = 6

PEAK_SEARCH_MARGIN_SECONDS = 0.40
PEAK_SEARCH_MARGIN_RATIO = 0.10
MINIMUM_PEAK_SEARCH_MARGIN_FRAMES = 3
SUSTAINED_MOVEMENT_SECONDS = 0.12
MINIMUM_SUSTAINED_MOVEMENT_FRAMES = 3
IMPACT_ZONE_PEAK_RATIO = 0.70
TOP_SEARCH_LOOKBACK_SECONDS = 1.60
TOP_SEARCH_MINIMUM_GAP_SECONDS = 0.08


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


class DetectionWindow(TypedDict):
    startFrame: int
    endFrame: int
    frameCount: int
    startTimeSeconds: float
    endTimeSeconds: float
    durationSeconds: float


class MotionFrame(TypedDict):
    frameIndex: int
    timestampSeconds: float
    rawMotion: float
    smoothedMotion: float
    validLandmarkCount: int


class MotionSummary(TypedDict):
    analyzedFrames: int
    peakMotionFrame: int
    peakMotionTimeSeconds: float
    peakMotionValue: float
    medianMotionValue: float
    movementThreshold: float
    estimatedFps: float
    peakSearchMarginFrames: int


class PhasePoint(TypedDict):
    frameIndex: int
    timestampSeconds: float
    confidence: float


class ImpactZone(TypedDict):
    startFrame: int
    startTimeSeconds: float
    peakFrame: int
    peakTimeSeconds: float
    endFrame: int
    endTimeSeconds: float
    confidence: float


class PhaseCandidates(TypedDict):
    movementStart: PhasePoint | None
    topOfBackswing: PhasePoint | None
    downswingStart: PhasePoint | None
    impactZone: ImpactZone | None
    movementEnd: PhasePoint | None


class MotionAnalysis(TypedDict):
    activePoseWindow: DetectionWindow
    summary: MotionSummary
    phaseCandidates: PhaseCandidates
    frames: list[MotionFrame]


def find_longest_detection_window(frames: list[PoseFrame]) -> DetectionWindow:
    longest_start: int | None = None
    longest_end: int | None = None
    current_start: int | None = None

    for index, frame in enumerate(frames):
        if frame["poseDetected"]:
            if current_start is None:
                current_start = index
        elif current_start is not None:
            current_end = index - 1
            if (
                longest_start is None
                or longest_end is None
                or current_end - current_start > longest_end - longest_start
            ):
                longest_start = current_start
                longest_end = current_end
            current_start = None

    if current_start is not None:
        current_end = len(frames) - 1
        if (
            longest_start is None
            or longest_end is None
            or current_end - current_start > longest_end - longest_start
        ):
            longest_start = current_start
            longest_end = current_end

    if longest_start is None or longest_end is None:
        raise ValueError("No continuous pose detection window was found.")

    start_frame = frames[longest_start]
    end_frame = frames[longest_end]

    return {
        "startFrame": start_frame["frameIndex"],
        "endFrame": end_frame["frameIndex"],
        "frameCount": end_frame["frameIndex"] - start_frame["frameIndex"] + 1,
        "startTimeSeconds": round(start_frame["timestampSeconds"], 3),
        "endTimeSeconds": round(end_frame["timestampSeconds"], 3),
        "durationSeconds": round(
            end_frame["timestampSeconds"] - start_frame["timestampSeconds"],
            3,
        ),
    }


def get_landmark_map(frame: PoseFrame) -> dict[int, LandmarkData]:
    return {landmark["index"]: landmark for landmark in frame["landmarks"]}


def calculate_distance(first: LandmarkData, second: LandmarkData) -> float:
    return math.hypot(second["x"] - first["x"], second["y"] - first["y"])


def calculate_midpoint(
    first: LandmarkData,
    second: LandmarkData,
) -> tuple[float, float]:
    return (
        (first["x"] + second["x"]) / 2.0,
        (first["y"] + second["y"]) / 2.0,
    )


def calculate_torso_length(
    landmarks: dict[int, LandmarkData],
) -> float | None:
    required = (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP)

    if any(index not in landmarks for index in required):
        return None

    if any(landmarks[index]["visibility"] < MINIMUM_VISIBILITY for index in required):
        return None

    shoulder_midpoint = calculate_midpoint(
        landmarks[LEFT_SHOULDER],
        landmarks[RIGHT_SHOULDER],
    )
    hip_midpoint = calculate_midpoint(
        landmarks[LEFT_HIP],
        landmarks[RIGHT_HIP],
    )

    torso_length = math.hypot(
        shoulder_midpoint[0] - hip_midpoint[0],
        shoulder_midpoint[1] - hip_midpoint[1],
    )

    return torso_length if torso_length > 0.0001 else None


def calculate_frame_motion(
    previous_frame: PoseFrame,
    current_frame: PoseFrame,
) -> tuple[float, int]:
    previous_landmarks = get_landmark_map(previous_frame)
    current_landmarks = get_landmark_map(current_frame)
    torso_length = calculate_torso_length(current_landmarks)

    if torso_length is None:
        return 0.0, 0

    weighted_motion_total = 0.0
    weight_total = 0.0
    valid_landmark_count = 0

    for landmark_index, landmark_weight in TRACKED_LANDMARK_WEIGHTS.items():
        previous_landmark = previous_landmarks.get(landmark_index)
        current_landmark = current_landmarks.get(landmark_index)

        if previous_landmark is None or current_landmark is None:
            continue

        if (
            previous_landmark["visibility"] < MINIMUM_VISIBILITY
            or current_landmark["visibility"] < MINIMUM_VISIBILITY
        ):
            continue

        normalized_distance = (
            calculate_distance(previous_landmark, current_landmark) / torso_length
        )
        weighted_motion_total += normalized_distance * landmark_weight
        weight_total += landmark_weight
        valid_landmark_count += 1

    if weight_total == 0:
        return 0.0, 0

    return weighted_motion_total / weight_total, valid_landmark_count


def smooth_values(
    values: list[float],
    window_size: int = SMOOTHING_WINDOW_SIZE,
) -> list[float]:
    if not values:
        return []
    if window_size <= 1:
        return values.copy()

    smoothed_values: list[float] = []
    half_window = window_size // 2

    for index in range(len(values)):
        start_index = max(0, index - half_window)
        end_index = min(len(values), index + half_window + 1)
        window_values = values[start_index:end_index]
        smoothed_values.append(sum(window_values) / len(window_values))

    return smoothed_values


def estimate_fps(frames: list[MotionFrame]) -> float:
    differences = [
        frames[index]["timestampSeconds"] - frames[index - 1]["timestampSeconds"]
        for index in range(1, len(frames))
        if frames[index]["timestampSeconds"] > frames[index - 1]["timestampSeconds"]
    ]

    if not differences:
        return 30.0

    median_difference = statistics.median(differences)
    return 1.0 / median_difference if median_difference > 0 else 30.0


def calculate_peak_search_margin(frame_count: int, estimated_fps: float) -> int:
    margin = max(
        MINIMUM_PEAK_SEARCH_MARGIN_FRAMES,
        round(estimated_fps * PEAK_SEARCH_MARGIN_SECONDS),
        round(frame_count * PEAK_SEARCH_MARGIN_RATIO),
    )
    return min(margin, max(0, (frame_count - 1) // 2))


def calculate_sustained_frame_count(estimated_fps: float) -> int:
    return max(
        MINIMUM_SUSTAINED_MOVEMENT_FRAMES,
        round(estimated_fps * SUSTAINED_MOVEMENT_SECONDS),
    )


def find_true_runs(values: list[bool]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    run_start: int | None = None

    for index, value in enumerate(values):
        if value and run_start is None:
            run_start = index
        elif not value and run_start is not None:
            runs.append((run_start, index - 1))
            run_start = None

    if run_start is not None:
        runs.append((run_start, len(values) - 1))

    return runs


def clamp_confidence(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 3)


def landmark_confidence(frame: MotionFrame) -> float:
    return frame["validLandmarkCount"] / len(TRACKED_LANDMARK_WEIGHTS)


def create_phase_point(frame: MotionFrame, confidence: float) -> PhasePoint:
    return {
        "frameIndex": frame["frameIndex"],
        "timestampSeconds": frame["timestampSeconds"],
        "confidence": clamp_confidence(confidence),
    }


def find_phase_candidates(
    motion_frames: list[MotionFrame],
    peak_index: int,
    movement_threshold: float,
    peak_motion_value: float,
    estimated_fps: float,
    peak_search_margin: int,
) -> PhaseCandidates:
    reliable_and_moving = [
        frame["validLandmarkCount"] >= MINIMUM_VALID_LANDMARKS
        and frame["smoothedMotion"] >= movement_threshold
        for frame in motion_frames
    ]

    sustained_frames = calculate_sustained_frame_count(estimated_fps)
    movement_runs = [
        run
        for run in find_true_runs(reliable_and_moving)
        if run[1] - run[0] + 1 >= sustained_frames
    ]

    primary_run = next(
        (run for run in movement_runs if run[0] <= peak_index <= run[1]),
        None,
    )

    if primary_run is None and movement_runs:
        primary_run = min(
            movement_runs,
            key=lambda run: min(abs(peak_index - run[0]), abs(peak_index - run[1])),
        )

    if primary_run is None:
        primary_run = (
            max(0, peak_index - 1),
            min(len(motion_frames) - 1, peak_index + 1),
        )

    movement_start_index, movement_end_index = primary_run

    impact_threshold = max(
        movement_threshold,
        peak_motion_value * IMPACT_ZONE_PEAK_RATIO,
    )

    impact_start_index = peak_index
    impact_end_index = peak_index

    while impact_start_index > 0:
        candidate = motion_frames[impact_start_index - 1]
        if (
            candidate["validLandmarkCount"] < MINIMUM_VALID_LANDMARKS
            or candidate["smoothedMotion"] < impact_threshold
        ):
            break
        impact_start_index -= 1

    while impact_end_index < len(motion_frames) - 1:
        candidate = motion_frames[impact_end_index + 1]
        if (
            candidate["validLandmarkCount"] < MINIMUM_VALID_LANDMARKS
            or candidate["smoothedMotion"] < impact_threshold
        ):
            break
        impact_end_index += 1

    minimum_top_gap = max(
        1,
        round(estimated_fps * TOP_SEARCH_MINIMUM_GAP_SECONDS),
    )
    top_search_end = max(
        movement_start_index,
        impact_start_index - minimum_top_gap,
    )
    top_search_start = max(
        peak_search_margin,
        top_search_end - round(estimated_fps * TOP_SEARCH_LOOKBACK_SECONDS),
    )

    top_index: int | None = None
    if top_search_start <= top_search_end:
        top_index = min(
            range(top_search_start, top_search_end + 1),
            key=lambda index: (
                motion_frames[index]["smoothedMotion"],
                -motion_frames[index]["validLandmarkCount"],
            ),
        )

    downswing_index: int | None = None
    if top_index is not None:
        for index in range(top_index + 1, peak_index + 1):
            frame = motion_frames[index]
            if (
                frame["validLandmarkCount"] >= MINIMUM_VALID_LANDMARKS
                and frame["smoothedMotion"] >= movement_threshold
            ):
                downswing_index = index
                break

        if downswing_index is None:
            downswing_index = min(peak_index, top_index + 1)

    movement_start_frame = motion_frames[movement_start_index]
    movement_end_frame = motion_frames[movement_end_index]
    peak_frame = motion_frames[peak_index]

    run_strength = min(
        1.0,
        (movement_end_index - movement_start_index + 1)
        / max(sustained_frames * 2, 1),
    )

    movement_start_confidence = (
        0.55 * landmark_confidence(movement_start_frame) + 0.45 * run_strength
    )
    movement_end_confidence = (
        0.55 * landmark_confidence(movement_end_frame) + 0.45 * run_strength
    )

    peak_prominence = peak_motion_value / max(movement_threshold, 0.000001)
    impact_confidence = (
        0.45 * landmark_confidence(peak_frame)
        + 0.35 * min(1.0, peak_prominence / 2.0)
        + 0.20
        * min(
            1.0,
            (impact_end_index - impact_start_index + 1)
            / max(sustained_frames, 1),
        )
    )

    top_point: PhasePoint | None = None
    if top_index is not None:
        top_frame = motion_frames[top_index]
        separation = impact_start_index - top_index
        top_confidence = (
            0.50 * landmark_confidence(top_frame)
            + 0.30
            * min(1.0, separation / max(round(estimated_fps * 0.40), 1))
            + 0.20
            * min(
                1.0,
                movement_threshold / max(top_frame["smoothedMotion"], 0.000001) / 3.0,
            )
        )
        top_point = create_phase_point(top_frame, top_confidence)

    downswing_point: PhasePoint | None = None
    if downswing_index is not None:
        downswing_frame = motion_frames[downswing_index]
        downswing_confidence = (
            0.55 * landmark_confidence(downswing_frame)
            + 0.45
            * min(
                1.0,
                downswing_frame["smoothedMotion"]
                / max(movement_threshold, 0.000001)
                / 1.5,
            )
        )
        downswing_point = create_phase_point(
            downswing_frame,
            downswing_confidence,
        )

    impact_start_frame = motion_frames[impact_start_index]
    impact_end_frame = motion_frames[impact_end_index]

    return {
        "movementStart": create_phase_point(
            movement_start_frame,
            movement_start_confidence,
        ),
        "topOfBackswing": top_point,
        "downswingStart": downswing_point,
        "impactZone": {
            "startFrame": impact_start_frame["frameIndex"],
            "startTimeSeconds": impact_start_frame["timestampSeconds"],
            "peakFrame": peak_frame["frameIndex"],
            "peakTimeSeconds": peak_frame["timestampSeconds"],
            "endFrame": impact_end_frame["frameIndex"],
            "endTimeSeconds": impact_end_frame["timestampSeconds"],
            "confidence": clamp_confidence(impact_confidence),
        },
        "movementEnd": create_phase_point(
            movement_end_frame,
            movement_end_confidence,
        ),
    }


def analyze_motion_signal(
    frames: list[PoseFrame],
    active_pose_window: DetectionWindow | None = None,
) -> MotionAnalysis:
    if not frames:
        raise ValueError("Pose timeline contains no frames.")

    if active_pose_window is None:
        active_pose_window = find_longest_detection_window(frames)

    active_frames = [
        frame
        for frame in frames
        if (
            active_pose_window["startFrame"]
            <= frame["frameIndex"]
            <= active_pose_window["endFrame"]
            and frame["poseDetected"]
        )
    ]

    if len(active_frames) < 2:
        raise ValueError(
            "At least two detected frames are required for movement analysis."
        )

    raw_motion_values: list[float] = [0.0]
    valid_landmark_counts: list[int] = [len(TRACKED_LANDMARK_WEIGHTS)]

    for index in range(1, len(active_frames)):
        motion_value, valid_landmark_count = calculate_frame_motion(
            active_frames[index - 1],
            active_frames[index],
        )
        raw_motion_values.append(motion_value)
        valid_landmark_counts.append(valid_landmark_count)

    smoothed_motion_values = smooth_values(raw_motion_values)

    motion_frames: list[MotionFrame] = [
        {
            "frameIndex": frame["frameIndex"],
            "timestampSeconds": frame["timestampSeconds"],
            "rawMotion": round(raw_motion_values[index], 6),
            "smoothedMotion": round(smoothed_motion_values[index], 6),
            "validLandmarkCount": valid_landmark_counts[index],
        }
        for index, frame in enumerate(active_frames)
    ]

    estimated_fps = estimate_fps(motion_frames)
    peak_search_margin = calculate_peak_search_margin(
        len(motion_frames),
        estimated_fps,
    )

    eligible_peak_frames = [
        (index, frame)
        for index, frame in enumerate(motion_frames)
        if (
            peak_search_margin <= index < len(motion_frames) - peak_search_margin
            and frame["validLandmarkCount"] >= MINIMUM_VALID_LANDMARKS
        )
    ]

    if not eligible_peak_frames:
        eligible_peak_frames = [
            (index, frame)
            for index, frame in enumerate(motion_frames)
            if frame["validLandmarkCount"] >= MINIMUM_VALID_LANDMARKS
        ]

    if not eligible_peak_frames:
        raise ValueError(
            "Not enough reliable landmark data to identify peak motion."
        )

    peak_index, peak_motion_frame = max(
        eligible_peak_frames,
        key=lambda item: item[1]["smoothedMotion"],
    )

    reliable_motion_values = [
        frame["smoothedMotion"]
        for frame in motion_frames
        if (
            frame["smoothedMotion"] > 0
            and frame["validLandmarkCount"] >= MINIMUM_VALID_LANDMARKS
        )
    ]

    median_motion_value = (
        statistics.median(reliable_motion_values)
        if reliable_motion_values
        else 0.0
    )

    movement_threshold = max(
        median_motion_value * 1.5,
        peak_motion_frame["smoothedMotion"] * 0.12,
    )

    phase_candidates = find_phase_candidates(
        motion_frames=motion_frames,
        peak_index=peak_index,
        movement_threshold=movement_threshold,
        peak_motion_value=peak_motion_frame["smoothedMotion"],
        estimated_fps=estimated_fps,
        peak_search_margin=peak_search_margin,
    )

    summary: MotionSummary = {
        "analyzedFrames": len(motion_frames),
        "peakMotionFrame": peak_motion_frame["frameIndex"],
        "peakMotionTimeSeconds": peak_motion_frame["timestampSeconds"],
        "peakMotionValue": round(peak_motion_frame["smoothedMotion"], 6),
        "medianMotionValue": round(median_motion_value, 6),
        "movementThreshold": round(movement_threshold, 6),
        "estimatedFps": round(estimated_fps, 3),
        "peakSearchMarginFrames": peak_search_margin,
    }

    return {
        "activePoseWindow": active_pose_window,
        "summary": summary,
        "phaseCandidates": phase_candidates,
        "frames": motion_frames,
    }


def load_pose_timeline(
    timeline_path: Path,
) -> tuple[list[PoseFrame], DetectionWindow | None]:
    try:
        payload = json.loads(timeline_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Unable to read pose timeline: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Pose timeline contains invalid JSON: {error}"
        ) from error

    frames = payload.get("frames")
    if not isinstance(frames, list):
        raise ValueError("Pose timeline does not contain a frames list.")

    return frames, payload.get("activePoseWindow")


def create_motion_output_path(timeline_path: Path) -> Path:
    filename = timeline_path.name

    if filename.endswith("-pose-timeline.json"):
        filename = filename.replace(
            "-pose-timeline.json",
            "-motion-analysis.json",
        )
    else:
        filename = f"{timeline_path.stem}-motion-analysis.json"

    return timeline_path.parent / filename


def save_motion_analysis(output_path: Path, analysis: MotionAnalysis) -> None:
    try:
        output_path.write_text(
            json.dumps(analysis, indent=2),
            encoding="utf-8",
        )
    except OSError as error:
        raise RuntimeError(
            f"Unable to save motion analysis: {error}"
        ) from error


def print_result(payload: dict[str, object]) -> None:
    print(json.dumps(payload))


def main() -> None:
    if len(sys.argv) != 2:
        print_result(
            {
                "success": False,
                "error": (
                    "Usage: python -m app.phase_detector "
                    "<pose-timeline-path>"
                ),
            }
        )
        raise SystemExit(1)

    timeline_path = Path(sys.argv[1]).expanduser().resolve()

    if not timeline_path.is_file():
        print_result(
            {
                "success": False,
                "error": f"Pose timeline file not found: {timeline_path}",
            }
        )
        raise SystemExit(1)

    try:
        frames, active_pose_window = load_pose_timeline(timeline_path)
        analysis = analyze_motion_signal(frames, active_pose_window)
        output_path = create_motion_output_path(timeline_path)
        save_motion_analysis(output_path, analysis)
    except (ValueError, RuntimeError) as error:
        print_result({"success": False, "error": str(error)})
        raise SystemExit(1) from error

    print_result(
        {
            "success": True,
            "activePoseWindow": analysis["activePoseWindow"],
            "motionSummary": analysis["summary"],
            "phaseCandidates": analysis["phaseCandidates"],
            "motionAnalysisPath": str(output_path),
        }
    )


if __name__ == "__main__":
    main()