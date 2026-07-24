from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

import cv2
import mediapipe as mp
import numpy as np

from app.phase_detector import find_longest_detection_window


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "pose_landmarker_full.task"
)

OUTPUT_DIRECTORY = PROJECT_ROOT / "output"

ROTATIONS = (
    "none",
    "clockwise90",
    "counterclockwise90",
    "rotate180",
)


class VideoMetadata(TypedDict):
    frameCount: int
    fps: float
    durationSeconds: float
    width: int
    height: int


class OrientationCandidate(TypedDict):
    rotation: str
    framesTested: int
    framesDetected: int
    averageVisibility: float
    score: float


class OrientationResult(TypedDict):
    selectedRotation: str
    candidates: list[OrientationCandidate]


class LandmarkData(TypedDict):
    index: int
    x: float
    y: float
    z: float
    visibility: float
    presence: float


class PoseFrameData(TypedDict):
    frameIndex: int
    timestampMs: int
    timestampSeconds: float
    poseDetected: bool
    landmarks: list[LandmarkData]


class PoseDetectionSummary(TypedDict):
    processedFrames: int
    detectedFrames: int
    undetectedFrames: int
    detectionRate: float
    rotation: str


class ActivePoseWindow(TypedDict):
    startFrame: int
    endFrame: int
    frameCount: int
    startTimeSeconds: float
    endTimeSeconds: float
    durationSeconds: float


class VideoAnalysisResult(TypedDict):
    metadata: VideoMetadata
    orientation: OrientationResult
    poseDetection: PoseDetectionSummary
    activePoseWindow: ActivePoseWindow
    timelinePath: str


def rotate_frame(
    frame: np.ndarray,
    rotation: str,
) -> np.ndarray:
    if rotation == "none":
        return frame

    if rotation == "clockwise90":
        return cv2.rotate(
            frame,
            cv2.ROTATE_90_CLOCKWISE,
        )

    if rotation == "counterclockwise90":
        return cv2.rotate(
            frame,
            cv2.ROTATE_90_COUNTERCLOCKWISE,
        )

    if rotation == "rotate180":
        return cv2.rotate(
            frame,
            cv2.ROTATE_180,
        )

    raise ValueError(f"Unsupported rotation: {rotation}")


def read_video_metadata(
    video_path: Path,
) -> VideoMetadata:
    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        raise ValueError(
            f"Unable to open video: {video_path}"
        )

    try:
        frame_count = int(
            video.get(cv2.CAP_PROP_FRAME_COUNT)
        )
        fps = float(
            video.get(cv2.CAP_PROP_FPS)
        )
        width = int(
            video.get(cv2.CAP_PROP_FRAME_WIDTH)
        )
        height = int(
            video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        if frame_count <= 0:
            raise ValueError(
                "Video contains no readable frames."
            )

        if fps <= 0:
            raise ValueError(
                "Video reported an invalid FPS value."
            )

        return {
            "frameCount": frame_count,
            "fps": round(fps, 3),
            "durationSeconds": round(
                frame_count / fps,
                3,
            ),
            "width": width,
            "height": height,
        }
    finally:
        video.release()


def get_orientation_sample_indices(
    frame_count: int,
) -> list[int]:
    percentages = (
        0.10,
        0.30,
        0.50,
        0.70,
        0.90,
    )

    indices = {
        min(
            frame_count - 1,
            max(
                0,
                int(frame_count * percentage),
            ),
        )
        for percentage in percentages
    }

    return sorted(indices)


def read_frame_at_index(
    video: cv2.VideoCapture,
    frame_index: int,
) -> np.ndarray | None:
    video.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame_index,
    )

    success, frame = video.read()

    if not success:
        return None

    return frame


def calculate_average_visibility(
    pose_landmarks: list[object],
) -> float:
    if not pose_landmarks:
        return 0.0

    visibility_values = [
        float(
            getattr(
                landmark,
                "visibility",
                0.0,
            )
        )
        for landmark in pose_landmarks
    ]

    if not visibility_values:
        return 0.0

    return (
        sum(visibility_values)
        / len(visibility_values)
    )


def detect_best_rotation(
    video_path: Path,
    frame_count: int,
) -> OrientationResult:
    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        raise ValueError(
            f"Unable to open video: {video_path}"
        )

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH),
    )

    options = (
        mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=(
                mp.tasks.vision.RunningMode.IMAGE
            ),
            num_poses=1,
            min_pose_detection_confidence=0.4,
            min_pose_presence_confidence=0.4,
            output_segmentation_masks=False,
        )
    )

    sample_indices = (
        get_orientation_sample_indices(
            frame_count
        )
    )

    candidate_results: list[
        OrientationCandidate
    ] = []

    try:
        with (
            mp.tasks.vision.PoseLandmarker
            .create_from_options(options)
        ) as landmarker:
            for rotation in ROTATIONS:
                frames_tested = 0
                frames_detected = 0
                visibility_total = 0.0

                for frame_index in sample_indices:
                    frame = read_frame_at_index(
                        video,
                        frame_index,
                    )

                    if frame is None:
                        continue

                    frames_tested += 1

                    rotated_frame = rotate_frame(
                        frame,
                        rotation,
                    )

                    rgb_frame = cv2.cvtColor(
                        rotated_frame,
                        cv2.COLOR_BGR2RGB,
                    )

                    mediapipe_image = mp.Image(
                        image_format=(
                            mp.ImageFormat.SRGB
                        ),
                        data=rgb_frame,
                    )

                    result = landmarker.detect(
                        mediapipe_image
                    )

                    if not result.pose_landmarks:
                        continue

                    frames_detected += 1

                    visibility_total += (
                        calculate_average_visibility(
                            result.pose_landmarks[0]
                        )
                    )

                average_visibility = (
                    visibility_total
                    / frames_detected
                    if frames_detected > 0
                    else 0.0
                )

                detection_rate = (
                    frames_detected
                    / frames_tested
                    if frames_tested > 0
                    else 0.0
                )

                score = (
                    detection_rate * 0.8
                    + average_visibility * 0.2
                )

                candidate_results.append(
                    {
                        "rotation": rotation,
                        "framesTested": (
                            frames_tested
                        ),
                        "framesDetected": (
                            frames_detected
                        ),
                        "averageVisibility": round(
                            average_visibility,
                            4,
                        ),
                        "score": round(
                            score,
                            4,
                        ),
                    }
                )
    finally:
        video.release()

    if not candidate_results:
        raise RuntimeError(
            "Unable to test video orientation."
        )

    best_candidate = max(
        candidate_results,
        key=lambda candidate: (
            candidate["score"],
            candidate["framesDetected"],
        ),
    )

    if best_candidate["framesDetected"] == 0:
        raise RuntimeError(
            "No pose was detected in any tested "
            "orientation."
        )

    return {
        "selectedRotation": (
            best_candidate["rotation"]
        ),
        "candidates": candidate_results,
    }


def serialize_landmarks(
    pose_landmarks: list[object],
) -> list[LandmarkData]:
    serialized_landmarks: list[
        LandmarkData
    ] = []

    for index, landmark in enumerate(
        pose_landmarks
    ):
        serialized_landmarks.append(
            {
                "index": index,
                "x": round(
                    float(
                        getattr(
                            landmark,
                            "x",
                            0.0,
                        )
                    ),
                    6,
                ),
                "y": round(
                    float(
                        getattr(
                            landmark,
                            "y",
                            0.0,
                        )
                    ),
                    6,
                ),
                "z": round(
                    float(
                        getattr(
                            landmark,
                            "z",
                            0.0,
                        )
                    ),
                    6,
                ),
                "visibility": round(
                    float(
                        getattr(
                            landmark,
                            "visibility",
                            0.0,
                        )
                    ),
                    6,
                ),
                "presence": round(
                    float(
                        getattr(
                            landmark,
                            "presence",
                            0.0,
                        )
                    ),
                    6,
                ),
            }
        )

    return serialized_landmarks


def create_timeline_output_path(
    video_path: Path,
) -> Path:
    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_stem = (
        video_path.stem.replace(" ", "-")
    )

    return (
        OUTPUT_DIRECTORY
        / f"{safe_stem}-pose-timeline.json"
    )


def extract_pose_timeline(
    video_path: Path,
    metadata: VideoMetadata,
    rotation: str,
) -> tuple[
    list[PoseFrameData],
    PoseDetectionSummary,
]:
    video = cv2.VideoCapture(str(video_path))

    if not video.isOpened():
        raise ValueError(
            f"Unable to open video: {video_path}"
        )

    base_options = mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH),
    )

    options = (
        mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=(
                mp.tasks.vision.RunningMode.VIDEO
            ),
            num_poses=1,
            min_pose_detection_confidence=0.4,
            min_pose_presence_confidence=0.4,
            min_tracking_confidence=0.4,
            output_segmentation_masks=False,
        )
    )

    timeline: list[PoseFrameData] = []

    processed_frames = 0
    detected_frames = 0
    frame_index = 0

    fps = metadata["fps"]

    try:
        with (
            mp.tasks.vision.PoseLandmarker
            .create_from_options(options)
        ) as landmarker:
            while True:
                success, frame = video.read()

                if not success:
                    break

                rotated_frame = rotate_frame(
                    frame,
                    rotation,
                )

                rgb_frame = cv2.cvtColor(
                    rotated_frame,
                    cv2.COLOR_BGR2RGB,
                )

                mediapipe_image = mp.Image(
                    image_format=(
                        mp.ImageFormat.SRGB
                    ),
                    data=rgb_frame,
                )

                timestamp_ms = int(
                    round(
                        (
                            frame_index
                            / fps
                        )
                        * 1000
                    )
                )

                result = (
                    landmarker.detect_for_video(
                        mediapipe_image,
                        timestamp_ms,
                    )
                )

                pose_detected = bool(
                    result.pose_landmarks
                )

                landmarks: list[
                    LandmarkData
                ] = []

                if pose_detected:
                    detected_frames += 1

                    landmarks = (
                        serialize_landmarks(
                            result.pose_landmarks[0]
                        )
                    )

                timeline.append(
                    {
                        "frameIndex": frame_index,
                        "timestampMs": timestamp_ms,
                        "timestampSeconds": round(
                            frame_index / fps,
                            3,
                        ),
                        "poseDetected": (
                            pose_detected
                        ),
                        "landmarks": landmarks,
                    }
                )

                processed_frames += 1
                frame_index += 1
    finally:
        video.release()

    undetected_frames = (
        processed_frames - detected_frames
    )

    detection_rate = (
        detected_frames / processed_frames
        if processed_frames > 0
        else 0.0
    )

    summary: PoseDetectionSummary = {
        "processedFrames": processed_frames,
        "detectedFrames": detected_frames,
        "undetectedFrames": (
            undetected_frames
        ),
        "detectionRate": round(
            detection_rate,
            3,
        ),
        "rotation": rotation,
    }

    return timeline, summary


def save_pose_timeline(
    output_path: Path,
    video_path: Path,
    metadata: VideoMetadata,
    orientation: OrientationResult,
    pose_detection: PoseDetectionSummary,
    active_pose_window: ActivePoseWindow,
    frames: list[PoseFrameData],
) -> None:
    payload = {
        "sourceVideo": str(video_path),
        "metadata": metadata,
        "orientation": orientation,
        "poseDetection": pose_detection,
        "activePoseWindow": (
            active_pose_window
        ),
        "frames": frames,
    }

    try:
        output_path.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as error:
        raise RuntimeError(
            "Unable to save pose timeline: "
            f"{error}"
        ) from error


def analyze_video_pose(
    video_path: Path,
) -> VideoAnalysisResult:
    if not MODEL_PATH.is_file():
        raise ValueError(
            f"Pose model not found: {MODEL_PATH}"
        )

    metadata = read_video_metadata(
        video_path
    )

    orientation = detect_best_rotation(
        video_path,
        metadata["frameCount"],
    )

    selected_rotation = (
        orientation["selectedRotation"]
    )

    timeline, pose_detection = (
        extract_pose_timeline(
            video_path,
            metadata,
            selected_rotation,
        )
    )

    active_pose_window = (
        find_longest_detection_window(
            timeline
        )
    )

    output_path = (
        create_timeline_output_path(
            video_path
        )
    )

    save_pose_timeline(
        output_path=output_path,
        video_path=video_path,
        metadata=metadata,
        orientation=orientation,
        pose_detection=pose_detection,
        active_pose_window=(
            active_pose_window
        ),
        frames=timeline,
    )

    return {
        "metadata": metadata,
        "orientation": orientation,
        "poseDetection": pose_detection,
        "activePoseWindow": (
            active_pose_window
        ),
        "timelinePath": str(output_path),
    }