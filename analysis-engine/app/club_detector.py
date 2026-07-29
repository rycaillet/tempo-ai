from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence, TypedDict

import cv2
import numpy as np

from app.pose_detector import (
    read_frame_at_index,
    rotate_frame,
)


LEFT_WRIST_INDEX = 15
RIGHT_WRIST_INDEX = 16

REFERENCE_PHASES = (
    "address",
    "takeaway",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

MINIMUM_WRIST_VISIBILITY = 0.35
MINIMUM_LINE_LENGTH_RATIO = 0.08
MAXIMUM_HAND_DISTANCE_RATIO = 0.22

CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150
HOUGH_THRESHOLD = 24
HOUGH_MAX_LINE_GAP = 18


class PixelPoint(TypedDict):
    x: float
    y: float


class ShaftLine(TypedDict):
    start: PixelPoint
    end: PixelPoint
    lengthPixels: float
    angleDegrees: float


class ShaftCandidate(TypedDict):
    line: ShaftLine
    handDistancePixels: float
    handDistanceRatio: float
    lengthRatio: float
    score: float


class ClubFrameDetection(TypedDict):
    phase: str
    frameIndex: int
    timestampSeconds: float | None
    detected: bool
    confidence: float
    handAnchor: PixelPoint | None
    shaftLine: ShaftLine | None
    candidateCount: int
    failureReason: str | None


class ClubDetectionSummary(TypedDict):
    requestedFrames: int
    processedFrames: int
    detectedFrames: int
    undetectedFrames: int
    detectionRate: float
    averageConfidence: float
    selectedRotation: str


class ClubDetectionResult(TypedDict):
    sourceVideo: str
    assumptions: dict[str, Any]
    summary: ClubDetectionSummary
    frames: list[ClubFrameDetection]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected a JSON object in {path}."
        )

    return payload


def write_json(
    output_path: Path,
    payload: Mapping[str, Any],
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_club_detection_output_path(
    refined_phases_path: Path,
) -> Path:
    file_name = refined_phases_path.name

    suffix = "-refined-phases.json"

    if file_name.endswith(suffix):
        stem = file_name[
            : -len(suffix)
        ]

        return (
            refined_phases_path.parent
            / f"{stem}-club-detection.json"
        )

    return refined_phases_path.with_name(
        f"{refined_phases_path.stem}"
        "-club-detection.json"
    )


def get_rotated_dimensions(
    width: int,
    height: int,
    rotation: str,
) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        raise ValueError(
            "Video dimensions must be positive."
        )

    if rotation in (
        "clockwise90",
        "counterclockwise90",
    ):
        return height, width

    if rotation in (
        "none",
        "rotate180",
    ):
        return width, height

    raise ValueError(
        f"Unsupported rotation: {rotation}"
    )


def get_landmark_map(
    pose_frame: Mapping[str, Any],
) -> dict[int, Mapping[str, Any]]:
    landmarks = pose_frame.get("landmarks")

    if not isinstance(landmarks, list):
        return {}

    result: dict[
        int,
        Mapping[str, Any],
    ] = {}

    for landmark in landmarks:
        if not isinstance(landmark, Mapping):
            continue

        index = landmark.get("index")

        if isinstance(index, int):
            result[index] = landmark

    return result


def landmark_to_pixel_point(
    landmark: Mapping[str, Any],
    *,
    frame_width: int,
    frame_height: int,
) -> PixelPoint | None:
    x = landmark.get("x")
    y = landmark.get("y")
    visibility = landmark.get(
        "visibility",
        0.0,
    )

    if not isinstance(x, (int, float)):
        return None

    if not isinstance(y, (int, float)):
        return None

    if not isinstance(
        visibility,
        (int, float),
    ):
        return None

    if visibility < MINIMUM_WRIST_VISIBILITY:
        return None

    return {
        "x": float(x) * frame_width,
        "y": float(y) * frame_height,
    }


def calculate_hand_anchor(
    pose_frame: Mapping[str, Any],
    *,
    frame_width: int,
    frame_height: int,
) -> PixelPoint | None:
    landmarks = get_landmark_map(
        pose_frame
    )

    wrist_points: list[PixelPoint] = []

    for wrist_index in (
        LEFT_WRIST_INDEX,
        RIGHT_WRIST_INDEX,
    ):
        landmark = landmarks.get(
            wrist_index
        )

        if landmark is None:
            continue

        point = landmark_to_pixel_point(
            landmark,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if point is not None:
            wrist_points.append(point)

    if not wrist_points:
        return None

    return {
        "x": sum(
            point["x"]
            for point in wrist_points
        )
        / len(wrist_points),
        "y": sum(
            point["y"]
            for point in wrist_points
        )
        / len(wrist_points),
    }


def calculate_line_length(
    start: PixelPoint,
    end: PixelPoint,
) -> float:
    return math.hypot(
        end["x"] - start["x"],
        end["y"] - start["y"],
    )


def calculate_line_angle(
    start: PixelPoint,
    end: PixelPoint,
) -> float:
    angle = math.degrees(
        math.atan2(
            end["y"] - start["y"],
            end["x"] - start["x"],
        )
    )

    while angle < 0.0:
        angle += 180.0

    while angle >= 180.0:
        angle -= 180.0

    return angle


def distance_from_point_to_segment(
    point: PixelPoint,
    start: PixelPoint,
    end: PixelPoint,
) -> float:
    segment_x = end["x"] - start["x"]
    segment_y = end["y"] - start["y"]

    segment_length_squared = (
        segment_x * segment_x
        + segment_y * segment_y
    )

    if segment_length_squared <= 0.0:
        return math.hypot(
            point["x"] - start["x"],
            point["y"] - start["y"],
        )

    projection = (
        (
            point["x"] - start["x"]
        )
        * segment_x
        + (
            point["y"] - start["y"]
        )
        * segment_y
    ) / segment_length_squared

    projection = min(
        1.0,
        max(0.0, projection),
    )

    closest_x = (
        start["x"]
        + projection * segment_x
    )
    closest_y = (
        start["y"]
        + projection * segment_y
    )

    return math.hypot(
        point["x"] - closest_x,
        point["y"] - closest_y,
    )


def build_shaft_candidate(
    coordinates: Sequence[int],
    *,
    hand_anchor: PixelPoint,
    frame_width: int,
    frame_height: int,
) -> ShaftCandidate | None:
    if len(coordinates) != 4:
        return None

    start: PixelPoint = {
        "x": float(coordinates[0]),
        "y": float(coordinates[1]),
    }

    end: PixelPoint = {
        "x": float(coordinates[2]),
        "y": float(coordinates[3]),
    }

    diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    if diagonal <= 0.0:
        return None

    length_pixels = calculate_line_length(
        start,
        end,
    )

    length_ratio = (
        length_pixels / diagonal
    )

    if (
        length_ratio
        < MINIMUM_LINE_LENGTH_RATIO
    ):
        return None

    hand_distance_pixels = (
        distance_from_point_to_segment(
            hand_anchor,
            start,
            end,
        )
    )

    hand_distance_ratio = (
        hand_distance_pixels / diagonal
    )

    if (
        hand_distance_ratio
        > MAXIMUM_HAND_DISTANCE_RATIO
    ):
        return None

    length_score = min(
        1.0,
        length_ratio / 0.35,
    )

    proximity_score = max(
        0.0,
        1.0
        - (
            hand_distance_ratio
            / MAXIMUM_HAND_DISTANCE_RATIO
        ),
    )

    score = (
        0.58 * proximity_score
        + 0.42 * length_score
    )

    return {
        "line": {
            "start": start,
            "end": end,
            "lengthPixels": round(
                length_pixels,
                3,
            ),
            "angleDegrees": round(
                calculate_line_angle(
                    start,
                    end,
                ),
                3,
            ),
        },
        "handDistancePixels": round(
            hand_distance_pixels,
            3,
        ),
        "handDistanceRatio": round(
            hand_distance_ratio,
            6,
        ),
        "lengthRatio": round(
            length_ratio,
            6,
        ),
        "score": round(
            score,
            6,
        ),
    }


def detect_shaft_candidates(
    frame: np.ndarray,
    *,
    hand_anchor: PixelPoint,
) -> list[ShaftCandidate]:
    frame_height, frame_width = (
        frame.shape[:2]
    )

    grayscale = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY,
    )

    blurred = cv2.GaussianBlur(
        grayscale,
        (5, 5),
        0,
    )

    edges = cv2.Canny(
        blurred,
        CANNY_LOW_THRESHOLD,
        CANNY_HIGH_THRESHOLD,
    )

    minimum_line_length = max(
        20,
        int(
            math.hypot(
                frame_width,
                frame_height,
            )
            * MINIMUM_LINE_LENGTH_RATIO
        ),
    )

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=HOUGH_THRESHOLD,
        minLineLength=minimum_line_length,
        maxLineGap=HOUGH_MAX_LINE_GAP,
    )

    if lines is None:
        return []

    candidates: list[ShaftCandidate] = []

    for line in lines:
        coordinates = (
            np.asarray(line)
            .reshape(-1)
            .tolist()
        )

        candidate = build_shaft_candidate(
            coordinates,
            hand_anchor=hand_anchor,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if candidate is not None:
            candidates.append(candidate)

    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["score"],
            candidate["line"][
                "lengthPixels"
            ],
        ),
        reverse=True,
    )


def create_pose_frame_lookup(
    pose_payload: Mapping[str, Any],
) -> dict[int, Mapping[str, Any]]:
    frames = pose_payload.get("frames")

    if not isinstance(frames, list):
        raise ValueError(
            "Pose timeline does not contain "
            "a frames list."
        )

    lookup: dict[
        int,
        Mapping[str, Any],
    ] = {}

    for frame in frames:
        if not isinstance(frame, Mapping):
            continue

        frame_index = frame.get(
            "frameIndex"
        )

        if isinstance(frame_index, int):
            lookup[frame_index] = frame

    return lookup


def get_reference_phases(
    refined_phases: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    phases = refined_phases.get("phases")

    if not isinstance(phases, Mapping):
        raise ValueError(
            "Refined phase analysis does not "
            "contain a phases object."
        )

    references: list[
        tuple[str, Mapping[str, Any]]
    ] = []

    for phase_name in REFERENCE_PHASES:
        phase = phases.get(phase_name)

        if not isinstance(phase, Mapping):
            continue

        frame_index = phase.get(
            "frameIndex"
        )

        if not isinstance(frame_index, int):
            continue

        references.append(
            (
                phase_name,
                phase,
            )
        )

    if not references:
        raise ValueError(
            "Refined phase analysis contains "
            "no usable reference frames."
        )

    return references


def analyze_club_detection(
    *,
    video_path: Path,
    pose_timeline_path: Path,
    refined_phases_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    resolved_video_path = (
        video_path.expanduser().resolve()
    )

    if not resolved_video_path.is_file():
        raise FileNotFoundError(
            f"Video file not found: "
            f"{resolved_video_path}"
        )

    pose_payload = load_json(
        pose_timeline_path
    )

    refined_phases = load_json(
        refined_phases_path
    )

    metadata = pose_payload.get("metadata")
    orientation = pose_payload.get(
        "orientation"
    )

    if not isinstance(metadata, Mapping):
        raise ValueError(
            "Pose timeline does not contain "
            "video metadata."
        )

    if not isinstance(
        orientation,
        Mapping,
    ):
        raise ValueError(
            "Pose timeline does not contain "
            "orientation metadata."
        )

    width = metadata.get("width")
    height = metadata.get("height")
    selected_rotation = orientation.get(
        "selectedRotation"
    )

    if not isinstance(width, int):
        raise ValueError(
            "Video metadata width is invalid."
        )

    if not isinstance(height, int):
        raise ValueError(
            "Video metadata height is invalid."
        )

    if not isinstance(
        selected_rotation,
        str,
    ):
        raise ValueError(
            "Selected video rotation is invalid."
        )

    rotated_width, rotated_height = (
        get_rotated_dimensions(
            width,
            height,
            selected_rotation,
        )
    )

    pose_frame_lookup = (
        create_pose_frame_lookup(
            pose_payload
        )
    )

    reference_phases = (
        get_reference_phases(
            refined_phases
        )
    )

    video = cv2.VideoCapture(
        str(resolved_video_path)
    )

    if not video.isOpened():
        raise ValueError(
            f"Unable to open video: "
            f"{resolved_video_path}"
        )

    frame_results: list[
        ClubFrameDetection
    ] = []

    try:
        for phase_name, phase in (
            reference_phases
        ):
            frame_index = int(
                phase["frameIndex"]
            )

            timestamp_value = phase.get(
                "timestampSeconds"
            )

            timestamp_seconds = (
                float(timestamp_value)
                if isinstance(
                    timestamp_value,
                    (int, float),
                )
                else None
            )

            pose_frame = (
                pose_frame_lookup.get(
                    frame_index
                )
            )

            if pose_frame is None:
                frame_results.append(
                    {
                        "phase": phase_name,
                        "frameIndex": (
                            frame_index
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": None,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "failureReason": (
                            "Pose timeline did not "
                            "contain the requested "
                            "reference frame."
                        ),
                    }
                )
                continue

            hand_anchor = (
                calculate_hand_anchor(
                    pose_frame,
                    frame_width=(
                        rotated_width
                    ),
                    frame_height=(
                        rotated_height
                    ),
                )
            )

            if hand_anchor is None:
                frame_results.append(
                    {
                        "phase": phase_name,
                        "frameIndex": (
                            frame_index
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": None,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "failureReason": (
                            "Reliable wrist "
                            "landmarks were not "
                            "available."
                        ),
                    }
                )
                continue

            raw_frame = read_frame_at_index(
                video,
                frame_index,
            )

            if raw_frame is None:
                frame_results.append(
                    {
                        "phase": phase_name,
                        "frameIndex": (
                            frame_index
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": hand_anchor,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "failureReason": (
                            "The reference video "
                            "frame could not be read."
                        ),
                    }
                )
                continue

            rotated_frame = rotate_frame(
                raw_frame,
                selected_rotation,
            )

            candidates = (
                detect_shaft_candidates(
                    rotated_frame,
                    hand_anchor=hand_anchor,
                )
            )

            if not candidates:
                frame_results.append(
                    {
                        "phase": phase_name,
                        "frameIndex": (
                            frame_index
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": hand_anchor,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "failureReason": (
                            "No reliable shaft-line "
                            "candidate was found near "
                            "the detected hands."
                        ),
                    }
                )
                continue

            best_candidate = candidates[0]

            frame_results.append(
                {
                    "phase": phase_name,
                    "frameIndex": frame_index,
                    "timestampSeconds": (
                        timestamp_seconds
                    ),
                    "detected": True,
                    "confidence": round(
                        best_candidate["score"],
                        3,
                    ),
                    "handAnchor": {
                        "x": round(
                            hand_anchor["x"],
                            3,
                        ),
                        "y": round(
                            hand_anchor["y"],
                            3,
                        ),
                    },
                    "shaftLine": (
                        best_candidate["line"]
                    ),
                    "candidateCount": len(
                        candidates
                    ),
                    "failureReason": None,
                }
            )
    finally:
        video.release()

    detected_results = [
        frame
        for frame in frame_results
        if frame["detected"]
    ]

    detected_count = len(
        detected_results
    )

    processed_count = len(
        frame_results
    )

    average_confidence = (
        sum(
            frame["confidence"]
            for frame in detected_results
        )
        / detected_count
        if detected_count > 0
        else 0.0
    )

    result: ClubDetectionResult = {
        "sourceVideo": str(
            resolved_video_path
        ),
        "assumptions": {
            "detectedObject": (
                "probable-golf-shaft-line"
            ),
            "coordinateSystem": (
                "rotated-video-pixels"
            ),
            "referenceFrameSource": (
                "golf-phase-refiner"
            ),
            "limitations": [
                (
                    "Line detection does not "
                    "identify the club model or "
                    "club type."
                ),
                (
                    "Body edges, clothing, shadows, "
                    "and background objects can "
                    "produce competing line "
                    "candidates."
                ),
                (
                    "A missing detection is retained "
                    "as an explicit failure state "
                    "instead of being inferred."
                ),
            ],
        },
        "summary": {
            "requestedFrames": len(
                reference_phases
            ),
            "processedFrames": (
                processed_count
            ),
            "detectedFrames": (
                detected_count
            ),
            "undetectedFrames": (
                processed_count
                - detected_count
            ),
            "detectionRate": round(
                (
                    detected_count
                    / processed_count
                )
                if processed_count > 0
                else 0.0,
                3,
            ),
            "averageConfidence": round(
                average_confidence,
                3,
            ),
            "selectedRotation": (
                selected_rotation
            ),
        },
        "frames": frame_results,
    }

    resolved_output_path = (
        output_path
        if output_path is not None
        else create_club_detection_output_path(
            refined_phases_path
        )
    )

    resolved_output_path = (
        resolved_output_path
        .expanduser()
        .resolve()
    )

    write_json(
        resolved_output_path,
        result,
    )

    return {
        "clubDetectionPath": str(
            resolved_output_path
        ),
        "clubDetection": result,
    }