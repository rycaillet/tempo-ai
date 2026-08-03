from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence, TypedDict

import cv2
import numpy as np

from app.club_frame_window import (
    build_dense_club_frame_requests,
)
from app.pose_detector import (
    read_frame_at_index,
    rotate_frame,
)
from app.club_visualizer import (
    create_club_visualization_directory,
    create_club_visualization_path,
    draw_club_detection_visualization,
    save_club_detection_visualization,
)
from app.club_search_region import (
    SearchRegion,
    build_pose_guided_corridor_mask,
    build_pose_guided_search_region,
    crop_frame_to_search_region,
    translate_coordinates_to_full_frame,
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

PRIMARY_MINIMUM_LINE_LENGTH_RATIO = 0.08
FALLBACK_MINIMUM_LINE_LENGTH_RATIO = 0.04

MINIMUM_LINE_LENGTH_RATIO = (
    PRIMARY_MINIMUM_LINE_LENGTH_RATIO
)

MAXIMUM_LINE_LENGTH_RATIO = 0.55
MAXIMUM_HAND_DISTANCE_RATIO = 0.22
MAXIMUM_GRIP_ENDPOINT_DISTANCE_RATIO = 0.12

CANNY_LOW_THRESHOLD = 50
CANNY_HIGH_THRESHOLD = 150

ADAPTIVE_CANNY_SIGMA = 0.33
ADAPTIVE_CANNY_MINIMUM_LOW_THRESHOLD = 10
ADAPTIVE_CANNY_MINIMUM_HIGH_THRESHOLD = 30
ADAPTIVE_CANNY_MAXIMUM_HIGH_THRESHOLD = 220

CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)
ENHANCED_EDGE_CLOSE_KERNEL_SIZE = 3

PRIMARY_HOUGH_THRESHOLD = 24
FALLBACK_HOUGH_THRESHOLD = 18

HOUGH_THRESHOLD = PRIMARY_HOUGH_THRESHOLD
HOUGH_MAX_LINE_GAP = 18

MERGE_MAXIMUM_ANGLE_CHANGE_DEGREES = 10.0
MERGE_MAXIMUM_PERPENDICULAR_DISTANCE_RATIO = 0.012
MERGE_MAXIMUM_ENDPOINT_GAP_RATIO = 0.045

MAXIMUM_REFERENCE_ANGLE_CHANGE_DEGREES = 75.0
MAXIMUM_TEMPORAL_ANGLE_CHANGE_DEGREES = 65.0
MAXIMUM_TEMPORAL_DISTAL_SHIFT_RATIO = 0.30
MINIMUM_TEMPORAL_SELECTION_SCORE = 0.48

TEMPORAL_IMAGE_SCORE_WEIGHT = 0.55
TEMPORAL_ANGLE_SCORE_WEIGHT = 0.30
TEMPORAL_DISTAL_SCORE_WEIGHT = 0.15

PROVENANCE_CORRIDOR_PRIMARY_ADJUSTMENT = 0.03
PROVENANCE_CORRIDOR_FALLBACK_ADJUSTMENT = 0.015
PROVENANCE_ENHANCED_PRIMARY_ADJUSTMENT = -0.01
PROVENANCE_ENHANCED_FALLBACK_ADJUSTMENT = -0.02
PROVENANCE_RECTANGULAR_PRIMARY_ADJUSTMENT = -0.02
PROVENANCE_RECTANGULAR_FALLBACK_ADJUSTMENT = -0.04
PROVENANCE_MERGED_SEGMENT_BONUS_PER_EXTRA_SEGMENT = 0.005
PROVENANCE_MAXIMUM_MERGED_SEGMENT_BONUS = 0.02


class PixelPoint(TypedDict):
    x: float
    y: float


class ShaftLine(TypedDict):
    start: PixelPoint
    end: PixelPoint
    lengthPixels: float
    angleDegrees: float


class CandidateProvenance(TypedDict):
    searchRegion: str
    edgeSource: str
    houghPass: str
    segmentSource: str
    sourceSegmentCount: int
    scoreAdjustment: float


class ShaftCandidate(TypedDict):
    line: ShaftLine
    handDistancePixels: float
    handDistanceRatio: float
    nearestEndpointDistancePixels: float
    nearestEndpointDistanceRatio: float
    lengthRatio: float
    baseImageScore: float
    score: float
    provenance: CandidateProvenance


class CandidateEvaluationDiagnostics(TypedDict):
    index: int
    line: ShaftLine
    imageScore: float
    adjustedImageScore: float
    provenance: CandidateProvenance
    temporalScore: float | None
    angleChangeDegrees: float | None
    distalShiftRatio: float | None
    accepted: bool
    selected: bool
    rejectionReasons: list[str]


class CandidateDiagnostics(TypedDict):
    croppedFrameEmpty: bool
    edgePixelCount: int

    corridorMaskAvailable: bool
    corridorMaskPixelCount: int
    corridorEdgePixelCount: int

    enhancedEdgeAttempted: bool
    enhancedEdgePixelCount: int
    adaptiveCannyLowThreshold: int | None
    adaptiveCannyHighThreshold: int | None

    detectionPass: str
    fallbackAttempted: bool

    minimumLineLengthPixels: int
    rawHoughLineCount: int
    mergedHoughLineCount: int
    segmentMergeCount: int

    primaryMinimumLineLengthPixels: int
    primaryRawHoughLineCount: int
    primaryMergedHoughLineCount: int

    fallbackMinimumLineLengthPixels: int
    fallbackRawHoughLineCount: int
    fallbackMergedHoughLineCount: int

    corridorPrimaryRawHoughLineCount: int
    corridorPrimaryMergedHoughLineCount: int
    corridorFallbackRawHoughLineCount: int
    corridorFallbackMergedHoughLineCount: int
    enhancedCorridorPrimaryRawHoughLineCount: int
    enhancedCorridorPrimaryMergedHoughLineCount: int
    enhancedCorridorFallbackRawHoughLineCount: int
    enhancedCorridorFallbackMergedHoughLineCount: int
    rectangularPrimaryRawHoughLineCount: int
    rectangularPrimaryMergedHoughLineCount: int
    rectangularFallbackRawHoughLineCount: int
    rectangularFallbackMergedHoughLineCount: int

    rejectedInvalidCoordinates: int
    rejectedInvalidFrameDimensions: int
    rejectedTooShort: int
    rejectedTooLong: int
    rejectedTooFarFromHands: int
    rejectedGripEndpointTooFar: int

    acceptedCandidateCount: int
    temporalReferenceAvailable: bool
    temporalCandidatesEvaluated: int
    temporalCandidatesRejected: int
    temporalSelectionMode: str
    selectedTemporalScore: float | None
    selectedAngleChangeDegrees: float | None
    selectedDistalShiftRatio: float | None
    candidateEvaluations: list[CandidateEvaluationDiagnostics]


class TemporalCandidateEvaluation(TypedDict):
    candidate: ShaftCandidate
    temporalScore: float
    angleChangeDegrees: float
    distalShiftRatio: float
    accepted: bool


class TemporalComparison(TypedDict):
    previousPhase: str
    previousFrameIndex: int
    angleChangeDegrees: float
    withinThreshold: bool


class ClubFrameDetection(TypedDict):
    phase: str
    referenceFrameIndex: int
    frameIndex: int
    phaseOffsetFrames: int
    isReferenceFrame: bool
    timestampSeconds: float | None
    detected: bool
    confidence: float
    handAnchor: PixelPoint | None
    shaftLine: ShaftLine | None
    candidateCount: int
    candidateDiagnostics: CandidateDiagnostics | None
    failureReason: str | None
    debugImagePath: str | None
    temporalStatus: str
    temporalComparison: TemporalComparison | None


class ClubDetectionSummary(TypedDict):
    requestedFrames: int
    processedFrames: int
    detectedFrames: int
    undetectedFrames: int
    detectionRate: float
    averageConfidence: float
    selectedRotation: str
    visualizationCount: int
    temporalComparisonCount: int
    temporallyConsistentFrames: int
    temporalReviewFrames: int
    maximumAngleChangeDegrees: float | None


class ClubDetectionResult(TypedDict):
    sourceVideo: str
    assumptions: dict[str, Any]
    visualizationDirectory: str
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


def calculate_nearest_endpoint_distance(
    point: PixelPoint,
    start: PixelPoint,
    end: PixelPoint,
) -> float:
    start_distance = math.hypot(
        point["x"] - start["x"],
        point["y"] - start["y"],
    )

    end_distance = math.hypot(
        point["x"] - end["x"],
        point["y"] - end["y"],
    )

    return min(
        start_distance,
        end_distance,
    )


def create_candidate_diagnostics() -> CandidateDiagnostics:
    return {
        "croppedFrameEmpty": False,
        "edgePixelCount": 0,

        "corridorMaskAvailable": False,
        "corridorMaskPixelCount": 0,
        "corridorEdgePixelCount": 0,

        "enhancedEdgeAttempted": False,
        "enhancedEdgePixelCount": 0,
        "adaptiveCannyLowThreshold": None,
        "adaptiveCannyHighThreshold": None,

        "detectionPass": "none",
        "fallbackAttempted": False,

        "minimumLineLengthPixels": 0,
        "rawHoughLineCount": 0,
        "mergedHoughLineCount": 0,
        "segmentMergeCount": 0,

        "primaryMinimumLineLengthPixels": 0,
        "primaryRawHoughLineCount": 0,
        "primaryMergedHoughLineCount": 0,

        "fallbackMinimumLineLengthPixels": 0,
        "fallbackRawHoughLineCount": 0,
        "fallbackMergedHoughLineCount": 0,

        "corridorPrimaryRawHoughLineCount": 0,
        "corridorPrimaryMergedHoughLineCount": 0,
        "corridorFallbackRawHoughLineCount": 0,
        "corridorFallbackMergedHoughLineCount": 0,
        "enhancedCorridorPrimaryRawHoughLineCount": 0,
        "enhancedCorridorPrimaryMergedHoughLineCount": 0,
        "enhancedCorridorFallbackRawHoughLineCount": 0,
        "enhancedCorridorFallbackMergedHoughLineCount": 0,
        "rectangularPrimaryRawHoughLineCount": 0,
        "rectangularPrimaryMergedHoughLineCount": 0,
        "rectangularFallbackRawHoughLineCount": 0,
        "rectangularFallbackMergedHoughLineCount": 0,

        "rejectedInvalidCoordinates": 0,
        "rejectedInvalidFrameDimensions": 0,
        "rejectedTooShort": 0,
        "rejectedTooLong": 0,
        "rejectedTooFarFromHands": 0,
        "rejectedGripEndpointTooFar": 0,

        "acceptedCandidateCount": 0,
        "temporalReferenceAvailable": False,
        "temporalCandidatesEvaluated": 0,
        "temporalCandidatesRejected": 0,
        "temporalSelectionMode": "not_attempted",
        "selectedTemporalScore": None,
        "selectedAngleChangeDegrees": None,
        "selectedDistalShiftRatio": None,
        "candidateEvaluations": [],
    }



def create_candidate_provenance(
    *,
    search_region: str,
    edge_source: str,
    hough_pass: str,
    source_segment_count: int,
) -> CandidateProvenance:
    normalized_segment_count = max(1, int(source_segment_count))

    adjustment = 0.0

    if search_region == "corridor":
        if edge_source == "enhanced":
            adjustment = (
                PROVENANCE_ENHANCED_PRIMARY_ADJUSTMENT
                if hough_pass == "primary"
                else PROVENANCE_ENHANCED_FALLBACK_ADJUSTMENT
            )
        else:
            adjustment = (
                PROVENANCE_CORRIDOR_PRIMARY_ADJUSTMENT
                if hough_pass == "primary"
                else PROVENANCE_CORRIDOR_FALLBACK_ADJUSTMENT
            )
    elif search_region == "rectangular":
        adjustment = (
            PROVENANCE_RECTANGULAR_PRIMARY_ADJUSTMENT
            if hough_pass == "primary"
            else PROVENANCE_RECTANGULAR_FALLBACK_ADJUSTMENT
        )

    merged_bonus = min(
        PROVENANCE_MAXIMUM_MERGED_SEGMENT_BONUS,
        (
            normalized_segment_count - 1
        ) * PROVENANCE_MERGED_SEGMENT_BONUS_PER_EXTRA_SEGMENT,
    )

    adjustment += merged_bonus

    return {
        "searchRegion": search_region,
        "edgeSource": edge_source,
        "houghPass": hough_pass,
        "segmentSource": (
            "merged"
            if normalized_segment_count > 1
            else "single"
        ),
        "sourceSegmentCount": normalized_segment_count,
        "scoreAdjustment": round(adjustment, 6),
    }


def evaluate_shaft_candidate(
    coordinates: Sequence[int],
    *,
    hand_anchor: PixelPoint,
    frame_width: int,
    frame_height: int,
    minimum_length_ratio: float = (
        MINIMUM_LINE_LENGTH_RATIO
    ),
    provenance: CandidateProvenance | None = None,
) -> tuple[ShaftCandidate | None, str | None]:
    if len(coordinates) != 4:
        return None, "invalid_coordinates"

    if frame_width <= 0 or frame_height <= 0:
        return None, "invalid_frame_dimensions"

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
        return None, "invalid_frame_dimensions"

    length_pixels = calculate_line_length(
        start,
        end,
    )

    length_ratio = length_pixels / diagonal

    if length_ratio < minimum_length_ratio:
        return None, "too_short"

    if length_ratio > MAXIMUM_LINE_LENGTH_RATIO:
        return None, "too_long"

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

    if hand_distance_ratio > MAXIMUM_HAND_DISTANCE_RATIO:
        return None, "too_far_from_hands"

    nearest_endpoint_distance_pixels = (
        calculate_nearest_endpoint_distance(
            hand_anchor,
            start,
            end,
        )
    )

    nearest_endpoint_distance_ratio = (
        nearest_endpoint_distance_pixels
        / diagonal
    )

    if (
        nearest_endpoint_distance_ratio
        > MAXIMUM_GRIP_ENDPOINT_DISTANCE_RATIO
    ):
        return None, "grip_endpoint_too_far"

    length_score = min(
        1.0,
        length_ratio / 0.35,
    )

    segment_proximity_score = max(
        0.0,
        1.0
        - (
            hand_distance_ratio
            / MAXIMUM_HAND_DISTANCE_RATIO
        ),
    )

    endpoint_proximity_score = max(
        0.0,
        1.0
        - (
            nearest_endpoint_distance_ratio
            / MAXIMUM_GRIP_ENDPOINT_DISTANCE_RATIO
        ),
    )

    base_score = (
        0.42 * endpoint_proximity_score
        + 0.33 * segment_proximity_score
        + 0.25 * length_score
    )

    active_provenance = (
        provenance
        if provenance is not None
        else create_candidate_provenance(
            search_region="unknown",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=1,
        )
    )

    adjusted_score = min(
        1.0,
        max(
            0.0,
            base_score
            + active_provenance["scoreAdjustment"],
        ),
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
        "nearestEndpointDistancePixels": round(
            nearest_endpoint_distance_pixels,
            3,
        ),
        "nearestEndpointDistanceRatio": round(
            nearest_endpoint_distance_ratio,
            6,
        ),
        "lengthRatio": round(
            length_ratio,
            6,
        ),
        "baseImageScore": round(
            base_score,
            6,
        ),
        "score": round(
            adjusted_score,
            6,
        ),
        "provenance": active_provenance,
    }, None


def build_shaft_candidate(
    coordinates: Sequence[int],
    *,
    hand_anchor: PixelPoint,
    frame_width: int,
    frame_height: int,
) -> ShaftCandidate | None:
    candidate, _ = evaluate_shaft_candidate(
        coordinates,
        hand_anchor=hand_anchor,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    return candidate


def record_candidate_rejection(
    diagnostics: CandidateDiagnostics,
    rejection_reason: str | None,
) -> None:
    rejection_key_by_reason = {
        "invalid_coordinates": (
            "rejectedInvalidCoordinates"
        ),
        "invalid_frame_dimensions": (
            "rejectedInvalidFrameDimensions"
        ),
        "too_short": "rejectedTooShort",
        "too_long": "rejectedTooLong",
        "too_far_from_hands": (
            "rejectedTooFarFromHands"
        ),
        "grip_endpoint_too_far": (
            "rejectedGripEndpointTooFar"
        ),
    }

    key = rejection_key_by_reason.get(
        rejection_reason
    )

    if key is not None:
        diagnostics[key] += 1


def sort_shaft_candidates(
    candidates: Sequence[ShaftCandidate],
) -> list[ShaftCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["score"],
            candidate["line"]["lengthPixels"],
        ),
        reverse=True,
    )



def _coordinates_to_points(
    coordinates: Sequence[int],
) -> tuple[PixelPoint, PixelPoint]:
    if len(coordinates) != 4:
        raise ValueError(
            "A shaft segment must contain exactly "
            "four coordinates."
        )

    return (
        {
            "x": float(coordinates[0]),
            "y": float(coordinates[1]),
        },
        {
            "x": float(coordinates[2]),
            "y": float(coordinates[3]),
        },
    )


def _point_to_infinite_line_distance(
    point: PixelPoint,
    line_start: PixelPoint,
    line_end: PixelPoint,
) -> float:
    line_x = line_end["x"] - line_start["x"]
    line_y = line_end["y"] - line_start["y"]
    line_length = math.hypot(line_x, line_y)

    if line_length <= 0.0:
        return calculate_line_length(
            point,
            line_start,
        )

    return abs(
        line_y * point["x"]
        - line_x * point["y"]
        + line_end["x"] * line_start["y"]
        - line_end["y"] * line_start["x"]
    ) / line_length


def _minimum_endpoint_gap(
    first_start: PixelPoint,
    first_end: PixelPoint,
    second_start: PixelPoint,
    second_end: PixelPoint,
) -> float:
    return min(
        calculate_line_length(first_start, second_start),
        calculate_line_length(first_start, second_end),
        calculate_line_length(first_end, second_start),
        calculate_line_length(first_end, second_end),
    )


def _segments_are_mergeable(
    first_coordinates: Sequence[int],
    second_coordinates: Sequence[int],
    *,
    frame_diagonal: float,
) -> bool:
    if frame_diagonal <= 0.0:
        return False

    first_start, first_end = _coordinates_to_points(
        first_coordinates
    )
    second_start, second_end = _coordinates_to_points(
        second_coordinates
    )

    angle_change = calculate_axial_angle_change(
        calculate_line_angle(first_start, first_end),
        calculate_line_angle(second_start, second_end),
    )

    if angle_change > MERGE_MAXIMUM_ANGLE_CHANGE_DEGREES:
        return False

    maximum_perpendicular_distance = (
        frame_diagonal
        * MERGE_MAXIMUM_PERPENDICULAR_DISTANCE_RATIO
    )

    perpendicular_distance = min(
        max(
            _point_to_infinite_line_distance(
                second_start,
                first_start,
                first_end,
            ),
            _point_to_infinite_line_distance(
                second_end,
                first_start,
                first_end,
            ),
        ),
        max(
            _point_to_infinite_line_distance(
                first_start,
                second_start,
                second_end,
            ),
            _point_to_infinite_line_distance(
                first_end,
                second_start,
                second_end,
            ),
        ),
    )

    if perpendicular_distance > maximum_perpendicular_distance:
        return False

    endpoint_gap = _minimum_endpoint_gap(
        first_start,
        first_end,
        second_start,
        second_end,
    )

    return endpoint_gap <= (
        frame_diagonal
        * MERGE_MAXIMUM_ENDPOINT_GAP_RATIO
    )


def _merge_segment_group(
    segment_group: Sequence[Sequence[int]],
) -> list[int]:
    if not segment_group:
        raise ValueError(
            "Cannot merge an empty segment group."
        )

    points: list[PixelPoint] = []

    for coordinates in segment_group:
        start, end = _coordinates_to_points(
            coordinates
        )
        points.extend((start, end))

    reference_start, reference_end = (
        _coordinates_to_points(segment_group[0])
    )

    direction_x = (
        reference_end["x"] - reference_start["x"]
    )
    direction_y = (
        reference_end["y"] - reference_start["y"]
    )
    direction_length = math.hypot(
        direction_x,
        direction_y,
    )

    if direction_length <= 0.0:
        return [
            int(round(reference_start["x"])),
            int(round(reference_start["y"])),
            int(round(reference_end["x"])),
            int(round(reference_end["y"])),
        ]

    unit_x = direction_x / direction_length
    unit_y = direction_y / direction_length

    projections = [
        (
            (
                point["x"] - reference_start["x"]
            ) * unit_x
            + (
                point["y"] - reference_start["y"]
            ) * unit_y
        )
        for point in points
    ]

    minimum_projection = min(projections)
    maximum_projection = max(projections)

    return [
        int(round(
            reference_start["x"]
            + minimum_projection * unit_x
        )),
        int(round(
            reference_start["y"]
            + minimum_projection * unit_y
        )),
        int(round(
            reference_start["x"]
            + maximum_projection * unit_x
        )),
        int(round(
            reference_start["y"]
            + maximum_projection * unit_y
        )),
    ]


def group_collinear_segments(
    coordinates: Sequence[Sequence[int]],
    *,
    frame_width: int,
    frame_height: int,
) -> list[list[int]]:
    if not coordinates:
        return []

    frame_diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    groups: list[list[list[int]]] = []

    for segment in coordinates:
        normalized_segment = [
            int(value)
            for value in segment
        ]

        for group in groups:
            if _segments_are_mergeable(
                _merge_segment_group(group),
                normalized_segment,
                frame_diagonal=frame_diagonal,
            ):
                group.append(normalized_segment)
                break
        else:
            groups.append([normalized_segment])

    return groups


def merge_collinear_segments(
    coordinates: Sequence[Sequence[int]],
    *,
    frame_width: int,
    frame_height: int,
) -> list[list[int]]:
    groups = group_collinear_segments(
        coordinates,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    return [
        _merge_segment_group(group)
        for group in groups
    ]


def calculate_adaptive_canny_thresholds(
    grayscale: np.ndarray,
    *,
    mask: np.ndarray | None = None,
) -> tuple[int, int]:
    """Derive stable Canny thresholds from local image intensity."""

    if grayscale.size == 0:
        return (
            ADAPTIVE_CANNY_MINIMUM_LOW_THRESHOLD,
            ADAPTIVE_CANNY_MINIMUM_HIGH_THRESHOLD,
        )

    if (
        mask is not None
        and mask.shape == grayscale.shape
        and mask.dtype == np.uint8
        and bool(np.any(mask))
    ):
        samples = grayscale[mask > 0]
    else:
        samples = grayscale.reshape(-1)

    if samples.size == 0:
        return (
            ADAPTIVE_CANNY_MINIMUM_LOW_THRESHOLD,
            ADAPTIVE_CANNY_MINIMUM_HIGH_THRESHOLD,
        )

    median_intensity = float(np.median(samples))

    low_threshold = int(round(
        (1.0 - ADAPTIVE_CANNY_SIGMA)
        * median_intensity
    ))
    high_threshold = int(round(
        (1.0 + ADAPTIVE_CANNY_SIGMA)
        * median_intensity
    ))

    low_threshold = max(
        ADAPTIVE_CANNY_MINIMUM_LOW_THRESHOLD,
        min(254, low_threshold),
    )
    high_threshold = max(
        ADAPTIVE_CANNY_MINIMUM_HIGH_THRESHOLD,
        min(
            ADAPTIVE_CANNY_MAXIMUM_HIGH_THRESHOLD,
            high_threshold,
        ),
    )

    if high_threshold <= low_threshold:
        high_threshold = min(
            ADAPTIVE_CANNY_MAXIMUM_HIGH_THRESHOLD,
            low_threshold + 20,
        )

    if high_threshold <= low_threshold:
        low_threshold = max(
            ADAPTIVE_CANNY_MINIMUM_LOW_THRESHOLD,
            high_threshold - 1,
        )

    return low_threshold, high_threshold


def build_enhanced_corridor_edges(
    grayscale: np.ndarray,
    *,
    corridor_mask: np.ndarray,
) -> tuple[np.ndarray, int, int]:
    """Recover weak, locally blended line evidence inside the corridor."""

    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=CLAHE_TILE_GRID_SIZE,
    )

    enhanced = clahe.apply(grayscale)

    enhanced_blurred = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0,
    )

    low_threshold, high_threshold = (
        calculate_adaptive_canny_thresholds(
            enhanced_blurred,
            mask=corridor_mask,
        )
    )

    enhanced_edges = cv2.Canny(
        enhanced_blurred,
        low_threshold,
        high_threshold,
    )

    enhanced_edges = cv2.bitwise_and(
        enhanced_edges,
        enhanced_edges,
        mask=corridor_mask,
    )

    closing_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (
            ENHANCED_EDGE_CLOSE_KERNEL_SIZE,
            ENHANCED_EDGE_CLOSE_KERNEL_SIZE,
        ),
    )

    enhanced_edges = cv2.morphologyEx(
        enhanced_edges,
        cv2.MORPH_CLOSE,
        closing_kernel,
    )

    enhanced_edges = cv2.bitwise_and(
        enhanced_edges,
        enhanced_edges,
        mask=corridor_mask,
    )

    return (
        enhanced_edges,
        low_threshold,
        high_threshold,
    )


def update_merged_hough_diagnostics(
    diagnostics: CandidateDiagnostics,
) -> None:
    diagnostics[
        "primaryMergedHoughLineCount"
    ] = (
        diagnostics[
            "corridorPrimaryMergedHoughLineCount"
        ]
        + diagnostics[
            "enhancedCorridorPrimaryMergedHoughLineCount"
        ]
        + diagnostics[
            "rectangularPrimaryMergedHoughLineCount"
        ]
    )

    diagnostics[
        "fallbackMergedHoughLineCount"
    ] = (
        diagnostics[
            "corridorFallbackMergedHoughLineCount"
        ]
        + diagnostics[
            "enhancedCorridorFallbackMergedHoughLineCount"
        ]
        + diagnostics[
            "rectangularFallbackMergedHoughLineCount"
        ]
    )

    diagnostics[
        "mergedHoughLineCount"
    ] = (
        diagnostics[
            "primaryMergedHoughLineCount"
        ]
        + diagnostics[
            "fallbackMergedHoughLineCount"
        ]
    )


def run_hough_candidate_pass(
    edges: np.ndarray,
    *,
    hand_anchor: PixelPoint,
    search_region: SearchRegion,
    frame_width: int,
    frame_height: int,
    minimum_line_length_pixels: int,
    minimum_candidate_length_ratio: float,
    hough_threshold: int,
    diagnostics: CandidateDiagnostics,
    raw_count_key: str,
    merged_count_key: str,
    search_region_type: str,
    edge_source: str,
    hough_pass: str,
) -> list[ShaftCandidate]:
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=hough_threshold,
        minLineLength=minimum_line_length_pixels,
        maxLineGap=HOUGH_MAX_LINE_GAP,
    )

    if lines is None:
        diagnostics[raw_count_key] = 0
        diagnostics[merged_count_key] = 0
        update_merged_hough_diagnostics(
            diagnostics
        )
        return []

    diagnostics[raw_count_key] = len(lines)

    full_frame_coordinates = [
        translate_coordinates_to_full_frame(
            np.asarray(line).reshape(-1).tolist(),
            search_region=search_region,
        )
        for line in lines
    ]

    segment_groups = group_collinear_segments(
        full_frame_coordinates,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    merged_coordinates = [
        _merge_segment_group(group)
        for group in segment_groups
    ]

    diagnostics[merged_count_key] = len(
        merged_coordinates
    )

    update_merged_hough_diagnostics(
        diagnostics
    )

    diagnostics["segmentMergeCount"] += max(
        0,
        len(full_frame_coordinates)
        - len(merged_coordinates),
    )

    candidates: list[ShaftCandidate] = []

    for coordinates, segment_group in zip(
        merged_coordinates,
        segment_groups,
    ):
        candidate, rejection_reason = (
            evaluate_shaft_candidate(
                coordinates,
                hand_anchor=hand_anchor,
                frame_width=frame_width,
                frame_height=frame_height,
                minimum_length_ratio=(
                    minimum_candidate_length_ratio
                ),
                provenance=create_candidate_provenance(
                    search_region=search_region_type,
                    edge_source=edge_source,
                    hough_pass=hough_pass,
                    source_segment_count=len(segment_group),
                ),
            )
        )

        if candidate is not None:
            candidates.append(candidate)
        else:
            record_candidate_rejection(
                diagnostics,
                rejection_reason,
            )

    return sort_shaft_candidates(candidates)


def detect_shaft_candidates(
    frame: np.ndarray,
    *,
    hand_anchor: PixelPoint,
    search_region: SearchRegion,
    corridor_mask: np.ndarray | None = None,
    diagnostics: CandidateDiagnostics | None = None,
) -> list[ShaftCandidate]:
    """
    Generate shaft candidates using geometry-guided and broad passes.

    When a valid directional corridor is available, Hough detection
    first searches standard edges inside that corridor. If both
    standard corridor passes fail, a locally contrast-enhanced edge
    map with adaptive Canny thresholds gets one focused recovery pass.
    The broader rectangular pose-guided crop remains the final fallback
    because forearm direction and shaft direction can diverge during
    wrist hinge, transition, impact, and release.
    """

    frame_height, frame_width = frame.shape[:2]

    active_diagnostics = (
        diagnostics
        if diagnostics is not None
        else create_candidate_diagnostics()
    )

    cropped_frame = crop_frame_to_search_region(
        frame,
        search_region,
    )

    if cropped_frame.size == 0:
        active_diagnostics[
            "croppedFrameEmpty"
        ] = True

        return []

    grayscale = cv2.cvtColor(
        cropped_frame,
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

    active_diagnostics["edgePixelCount"] = int(
        np.count_nonzero(edges)
    )

    full_frame_diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    primary_minimum_line_length = max(
        20,
        int(
            full_frame_diagonal
            * PRIMARY_MINIMUM_LINE_LENGTH_RATIO
        ),
    )

    fallback_minimum_line_length = max(
        20,
        int(
            full_frame_diagonal
            * FALLBACK_MINIMUM_LINE_LENGTH_RATIO
        ),
    )

    active_diagnostics[
        "primaryMinimumLineLengthPixels"
    ] = primary_minimum_line_length

    active_diagnostics[
        "fallbackMinimumLineLengthPixels"
    ] = fallback_minimum_line_length

    valid_corridor_mask = (
        corridor_mask is not None
        and corridor_mask.shape == edges.shape
        and corridor_mask.dtype == np.uint8
        and bool(np.any(corridor_mask))
    )

    if valid_corridor_mask:
        assert corridor_mask is not None

        active_diagnostics[
            "corridorMaskAvailable"
        ] = True

        active_diagnostics[
            "corridorMaskPixelCount"
        ] = int(np.count_nonzero(corridor_mask))

        corridor_edges = cv2.bitwise_and(
            edges,
            edges,
            mask=corridor_mask,
        )

        active_diagnostics[
            "corridorEdgePixelCount"
        ] = int(np.count_nonzero(corridor_edges))

        corridor_primary_candidates = (
            run_hough_candidate_pass(
                corridor_edges,
                hand_anchor=hand_anchor,
                search_region=search_region,
                frame_width=frame_width,
                frame_height=frame_height,
                minimum_line_length_pixels=(
                    primary_minimum_line_length
                ),
                minimum_candidate_length_ratio=(
                    PRIMARY_MINIMUM_LINE_LENGTH_RATIO
                ),
                hough_threshold=(
                    PRIMARY_HOUGH_THRESHOLD
                ),
                diagnostics=active_diagnostics,
                raw_count_key=(
                    "corridorPrimaryRawHoughLineCount"
                ),
                merged_count_key=(
                    "corridorPrimaryMergedHoughLineCount"
                ),
                search_region_type="corridor",
                edge_source="standard",
                hough_pass="primary",
            )
        )

        if corridor_primary_candidates:
            active_diagnostics[
                "detectionPass"
            ] = "corridor_primary"

            active_diagnostics[
                "minimumLineLengthPixels"
            ] = primary_minimum_line_length

            active_diagnostics[
                "primaryRawHoughLineCount"
            ] = active_diagnostics[
                "corridorPrimaryRawHoughLineCount"
            ]

            active_diagnostics[
                "rawHoughLineCount"
            ] = active_diagnostics[
                "corridorPrimaryRawHoughLineCount"
            ]

            active_diagnostics[
                "acceptedCandidateCount"
            ] = len(corridor_primary_candidates)

            return corridor_primary_candidates

        active_diagnostics[
            "fallbackAttempted"
        ] = True

        corridor_fallback_candidates = (
            run_hough_candidate_pass(
                corridor_edges,
                hand_anchor=hand_anchor,
                search_region=search_region,
                frame_width=frame_width,
                frame_height=frame_height,
                minimum_line_length_pixels=(
                    fallback_minimum_line_length
                ),
                minimum_candidate_length_ratio=(
                    FALLBACK_MINIMUM_LINE_LENGTH_RATIO
                ),
                hough_threshold=(
                    FALLBACK_HOUGH_THRESHOLD
                ),
                diagnostics=active_diagnostics,
                raw_count_key=(
                    "corridorFallbackRawHoughLineCount"
                ),
                merged_count_key=(
                    "corridorFallbackMergedHoughLineCount"
                ),
                search_region_type="corridor",
                edge_source="standard",
                hough_pass="fallback",
            )
        )

        if corridor_fallback_candidates:
            active_diagnostics[
                "detectionPass"
            ] = "corridor_fallback"

            active_diagnostics[
                "minimumLineLengthPixels"
            ] = fallback_minimum_line_length

            active_diagnostics[
                "primaryRawHoughLineCount"
            ] = active_diagnostics[
                "corridorPrimaryRawHoughLineCount"
            ]

            active_diagnostics[
                "fallbackRawHoughLineCount"
            ] = active_diagnostics[
                "corridorFallbackRawHoughLineCount"
            ]

            active_diagnostics[
                "rawHoughLineCount"
            ] = (
                active_diagnostics[
                    "corridorPrimaryRawHoughLineCount"
                ]
                + active_diagnostics[
                    "corridorFallbackRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "acceptedCandidateCount"
            ] = len(corridor_fallback_candidates)

            return corridor_fallback_candidates

        active_diagnostics[
            "enhancedEdgeAttempted"
        ] = True

        (
            enhanced_corridor_edges,
            adaptive_low_threshold,
            adaptive_high_threshold,
        ) = build_enhanced_corridor_edges(
            grayscale,
            corridor_mask=corridor_mask,
        )

        active_diagnostics[
            "adaptiveCannyLowThreshold"
        ] = adaptive_low_threshold

        active_diagnostics[
            "adaptiveCannyHighThreshold"
        ] = adaptive_high_threshold

        active_diagnostics[
            "enhancedEdgePixelCount"
        ] = int(np.count_nonzero(
            enhanced_corridor_edges
        ))

        enhanced_primary_candidates = (
            run_hough_candidate_pass(
                enhanced_corridor_edges,
                hand_anchor=hand_anchor,
                search_region=search_region,
                frame_width=frame_width,
                frame_height=frame_height,
                minimum_line_length_pixels=(
                    primary_minimum_line_length
                ),
                minimum_candidate_length_ratio=(
                    PRIMARY_MINIMUM_LINE_LENGTH_RATIO
                ),
                hough_threshold=(
                    PRIMARY_HOUGH_THRESHOLD
                ),
                diagnostics=active_diagnostics,
                raw_count_key=(
                    "enhancedCorridorPrimaryRawHoughLineCount"
                ),
                merged_count_key=(
                    "enhancedCorridorPrimaryMergedHoughLineCount"
                ),
                search_region_type="corridor",
                edge_source="enhanced",
                hough_pass="primary",
            )
        )

        if enhanced_primary_candidates:
            active_diagnostics[
                "detectionPass"
            ] = "corridor_enhanced_primary"

            active_diagnostics[
                "minimumLineLengthPixels"
            ] = primary_minimum_line_length

            active_diagnostics[
                "primaryRawHoughLineCount"
            ] = (
                active_diagnostics[
                    "corridorPrimaryRawHoughLineCount"
                ]
                + active_diagnostics[
                    "enhancedCorridorPrimaryRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "fallbackRawHoughLineCount"
            ] = active_diagnostics[
                "corridorFallbackRawHoughLineCount"
            ]

            active_diagnostics[
                "rawHoughLineCount"
            ] = (
                active_diagnostics[
                    "primaryRawHoughLineCount"
                ]
                + active_diagnostics[
                    "fallbackRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "acceptedCandidateCount"
            ] = len(enhanced_primary_candidates)

            return enhanced_primary_candidates

        enhanced_fallback_candidates = (
            run_hough_candidate_pass(
                enhanced_corridor_edges,
                hand_anchor=hand_anchor,
                search_region=search_region,
                frame_width=frame_width,
                frame_height=frame_height,
                minimum_line_length_pixels=(
                    fallback_minimum_line_length
                ),
                minimum_candidate_length_ratio=(
                    FALLBACK_MINIMUM_LINE_LENGTH_RATIO
                ),
                hough_threshold=(
                    FALLBACK_HOUGH_THRESHOLD
                ),
                diagnostics=active_diagnostics,
                raw_count_key=(
                    "enhancedCorridorFallbackRawHoughLineCount"
                ),
                merged_count_key=(
                    "enhancedCorridorFallbackMergedHoughLineCount"
                ),
                search_region_type="corridor",
                edge_source="enhanced",
                hough_pass="fallback",
            )
        )

        if enhanced_fallback_candidates:
            active_diagnostics[
                "detectionPass"
            ] = "corridor_enhanced_fallback"

            active_diagnostics[
                "minimumLineLengthPixels"
            ] = fallback_minimum_line_length

            active_diagnostics[
                "primaryRawHoughLineCount"
            ] = (
                active_diagnostics[
                    "corridorPrimaryRawHoughLineCount"
                ]
                + active_diagnostics[
                    "enhancedCorridorPrimaryRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "fallbackRawHoughLineCount"
            ] = (
                active_diagnostics[
                    "corridorFallbackRawHoughLineCount"
                ]
                + active_diagnostics[
                    "enhancedCorridorFallbackRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "rawHoughLineCount"
            ] = (
                active_diagnostics[
                    "primaryRawHoughLineCount"
                ]
                + active_diagnostics[
                    "fallbackRawHoughLineCount"
                ]
            )

            active_diagnostics[
                "acceptedCandidateCount"
            ] = len(enhanced_fallback_candidates)

            return enhanced_fallback_candidates

    rectangular_primary_candidates = (
        run_hough_candidate_pass(
            edges,
            hand_anchor=hand_anchor,
            search_region=search_region,
            frame_width=frame_width,
            frame_height=frame_height,
            minimum_line_length_pixels=(
                primary_minimum_line_length
            ),
            minimum_candidate_length_ratio=(
                PRIMARY_MINIMUM_LINE_LENGTH_RATIO
            ),
            hough_threshold=(
                PRIMARY_HOUGH_THRESHOLD
            ),
            diagnostics=active_diagnostics,
            raw_count_key=(
                "rectangularPrimaryRawHoughLineCount"
            ),
            merged_count_key=(
                "rectangularPrimaryMergedHoughLineCount"
            ),
            search_region_type="rectangular",
            edge_source="standard",
            hough_pass="primary",
        )
    )

    active_diagnostics[
        "primaryRawHoughLineCount"
    ] = (
        active_diagnostics[
            "corridorPrimaryRawHoughLineCount"
        ]
        + active_diagnostics[
            "enhancedCorridorPrimaryRawHoughLineCount"
        ]
        + active_diagnostics[
            "rectangularPrimaryRawHoughLineCount"
        ]
    )

    if rectangular_primary_candidates:
        active_diagnostics[
            "detectionPass"
        ] = "rectangular_primary"

        active_diagnostics[
            "minimumLineLengthPixels"
        ] = primary_minimum_line_length

        active_diagnostics[
            "rawHoughLineCount"
        ] = (
            active_diagnostics[
                "corridorPrimaryRawHoughLineCount"
            ]
            + active_diagnostics[
                "corridorFallbackRawHoughLineCount"
            ]
            + active_diagnostics[
                "enhancedCorridorPrimaryRawHoughLineCount"
            ]
            + active_diagnostics[
                "enhancedCorridorFallbackRawHoughLineCount"
            ]
            + active_diagnostics[
                "rectangularPrimaryRawHoughLineCount"
            ]
        )

        active_diagnostics[
            "acceptedCandidateCount"
        ] = len(rectangular_primary_candidates)

        return rectangular_primary_candidates

    active_diagnostics[
        "fallbackAttempted"
    ] = True

    rectangular_fallback_candidates = (
        run_hough_candidate_pass(
            edges,
            hand_anchor=hand_anchor,
            search_region=search_region,
            frame_width=frame_width,
            frame_height=frame_height,
            minimum_line_length_pixels=(
                fallback_minimum_line_length
            ),
            minimum_candidate_length_ratio=(
                FALLBACK_MINIMUM_LINE_LENGTH_RATIO
            ),
            hough_threshold=(
                FALLBACK_HOUGH_THRESHOLD
            ),
            diagnostics=active_diagnostics,
            raw_count_key=(
                "rectangularFallbackRawHoughLineCount"
            ),
            merged_count_key=(
                "rectangularFallbackMergedHoughLineCount"
            ),
            search_region_type="rectangular",
            edge_source="standard",
            hough_pass="fallback",
        )
    )

    active_diagnostics[
        "fallbackRawHoughLineCount"
    ] = (
        active_diagnostics[
            "corridorFallbackRawHoughLineCount"
        ]
        + active_diagnostics[
            "enhancedCorridorFallbackRawHoughLineCount"
        ]
        + active_diagnostics[
            "rectangularFallbackRawHoughLineCount"
        ]
    )

    active_diagnostics[
        "rawHoughLineCount"
    ] = (
        active_diagnostics[
            "corridorPrimaryRawHoughLineCount"
        ]
        + active_diagnostics[
            "corridorFallbackRawHoughLineCount"
        ]
        + active_diagnostics[
            "enhancedCorridorPrimaryRawHoughLineCount"
        ]
        + active_diagnostics[
            "enhancedCorridorFallbackRawHoughLineCount"
        ]
        + active_diagnostics[
            "rectangularPrimaryRawHoughLineCount"
        ]
        + active_diagnostics[
            "rectangularFallbackRawHoughLineCount"
        ]
    )

    active_diagnostics[
        "minimumLineLengthPixels"
    ] = fallback_minimum_line_length

    if rectangular_fallback_candidates:
        active_diagnostics[
            "detectionPass"
        ] = "rectangular_fallback"

        active_diagnostics[
            "acceptedCandidateCount"
        ] = len(rectangular_fallback_candidates)

        return rectangular_fallback_candidates

    active_diagnostics[
        "detectionPass"
    ] = "none"

    active_diagnostics[
        "acceptedCandidateCount"
    ] = 0

    return []


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


def calculate_axial_angle_change(
    first_angle: float,
    second_angle: float,
) -> float:
    difference = abs(
        second_angle - first_angle
    ) % 180.0

    if difference > 90.0:
        difference = 180.0 - difference

    return difference


def get_grip_and_distal_endpoints(
    shaft_line: ShaftLine,
    hand_anchor: PixelPoint,
) -> tuple[PixelPoint, PixelPoint]:
    start = shaft_line["start"]
    end = shaft_line["end"]

    start_distance = math.hypot(
        hand_anchor["x"] - start["x"],
        hand_anchor["y"] - start["y"],
    )

    end_distance = math.hypot(
        hand_anchor["x"] - end["x"],
        hand_anchor["y"] - end["y"],
    )

    if start_distance <= end_distance:
        return start, end

    return end, start


def calculate_temporal_candidate_evaluation(
    candidate: ShaftCandidate,
    *,
    current_hand_anchor: PixelPoint,
    previous_shaft_line: ShaftLine,
    previous_hand_anchor: PixelPoint,
    frame_width: int,
    frame_height: int,
) -> TemporalCandidateEvaluation:
    diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    if diagonal <= 0.0:
        return {
            "candidate": candidate,
            "temporalScore": 0.0,
            "angleChangeDegrees": 90.0,
            "distalShiftRatio": 1.0,
            "accepted": False,
        }

    _, current_distal_endpoint = (
        get_grip_and_distal_endpoints(
            candidate["line"],
            current_hand_anchor,
        )
    )

    _, previous_distal_endpoint = (
        get_grip_and_distal_endpoints(
            previous_shaft_line,
            previous_hand_anchor,
        )
    )

    angle_change = calculate_axial_angle_change(
        previous_shaft_line["angleDegrees"],
        candidate["line"]["angleDegrees"],
    )

    distal_shift_pixels = math.hypot(
        current_distal_endpoint["x"]
        - previous_distal_endpoint["x"],
        current_distal_endpoint["y"]
        - previous_distal_endpoint["y"],
    )

    distal_shift_ratio = (
        distal_shift_pixels / diagonal
    )

    angle_score = max(
        0.0,
        1.0 - (
            angle_change
            / MAXIMUM_TEMPORAL_ANGLE_CHANGE_DEGREES
        ),
    )

    distal_score = max(
        0.0,
        1.0 - (
            distal_shift_ratio
            / MAXIMUM_TEMPORAL_DISTAL_SHIFT_RATIO
        ),
    )

    temporal_score = (
        TEMPORAL_IMAGE_SCORE_WEIGHT
        * candidate["score"]
        + TEMPORAL_ANGLE_SCORE_WEIGHT
        * angle_score
        + TEMPORAL_DISTAL_SCORE_WEIGHT
        * distal_score
    )

    accepted = (
        angle_change
        <= MAXIMUM_TEMPORAL_ANGLE_CHANGE_DEGREES
        and temporal_score
        >= MINIMUM_TEMPORAL_SELECTION_SCORE
    )

    return {
        "candidate": candidate,
        "temporalScore": round(
            temporal_score,
            6,
        ),
        "angleChangeDegrees": round(
            angle_change,
            3,
        ),
        "distalShiftRatio": round(
            distal_shift_ratio,
            6,
        ),
        "accepted": accepted,
    }


def build_candidate_evaluation_diagnostics(
    candidate: ShaftCandidate,
    *,
    index: int,
    temporal_score: float | None,
    angle_change_degrees: float | None,
    distal_shift_ratio: float | None,
    accepted: bool,
    selected: bool,
) -> CandidateEvaluationDiagnostics:
    rejection_reasons: list[str] = []

    if not accepted:
        if (
            angle_change_degrees is not None
            and angle_change_degrees
            > MAXIMUM_TEMPORAL_ANGLE_CHANGE_DEGREES
        ):
            rejection_reasons.append(
                "angle_change_exceeds_threshold"
            )

        if (
            temporal_score is not None
            and temporal_score
            < MINIMUM_TEMPORAL_SELECTION_SCORE
        ):
            rejection_reasons.append(
                "temporal_score_below_minimum"
            )

        if not rejection_reasons:
            rejection_reasons.append(
                "temporal_candidate_rejected"
            )

    return {
        "index": index,
        "line": candidate["line"],
        "imageScore": candidate["baseImageScore"],
        "adjustedImageScore": candidate["score"],
        "provenance": candidate["provenance"],
        "temporalScore": temporal_score,
        "angleChangeDegrees": (
            angle_change_degrees
        ),
        "distalShiftRatio": distal_shift_ratio,
        "accepted": accepted,
        "selected": selected,
        "rejectionReasons": rejection_reasons,
    }


def select_shaft_candidate(
    candidates: Sequence[ShaftCandidate],
    *,
    current_hand_anchor: PixelPoint,
    previous_shaft_line: ShaftLine | None,
    previous_hand_anchor: PixelPoint | None,
    frame_width: int,
    frame_height: int,
    diagnostics: CandidateDiagnostics,
) -> ShaftCandidate | None:
    diagnostics["candidateEvaluations"] = []

    if not candidates:
        diagnostics[
            "temporalSelectionMode"
        ] = "no_candidates"

        return None

    if (
        previous_shaft_line is None
        or previous_hand_anchor is None
    ):
        selected = candidates[0]

        diagnostics[
            "temporalSelectionMode"
        ] = "image_only"

        diagnostics[
            "selectedTemporalScore"
        ] = selected["score"]

        diagnostics["candidateEvaluations"] = [
            build_candidate_evaluation_diagnostics(
                candidate,
                index=index,
                temporal_score=None,
                angle_change_degrees=None,
                distal_shift_ratio=None,
                accepted=True,
                selected=(candidate is selected),
            )
            for index, candidate in enumerate(candidates)
        ]

        return selected

    diagnostics[
        "temporalReferenceAvailable"
    ] = True

    evaluations = [
        calculate_temporal_candidate_evaluation(
            candidate,
            current_hand_anchor=(
                current_hand_anchor
            ),
            previous_shaft_line=(
                previous_shaft_line
            ),
            previous_hand_anchor=(
                previous_hand_anchor
            ),
            frame_width=frame_width,
            frame_height=frame_height,
        )
        for candidate in candidates
    ]

    diagnostics[
        "temporalCandidatesEvaluated"
    ] = len(evaluations)

    accepted_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation["accepted"]
    ]

    diagnostics[
        "temporalCandidatesRejected"
    ] = (
        len(evaluations)
        - len(accepted_evaluations)
    )

    if not accepted_evaluations:
        diagnostics[
            "temporalSelectionMode"
        ] = "rejected"

        diagnostics["candidateEvaluations"] = [
            build_candidate_evaluation_diagnostics(
                evaluation["candidate"],
                index=index,
                temporal_score=(
                    evaluation["temporalScore"]
                ),
                angle_change_degrees=(
                    evaluation["angleChangeDegrees"]
                ),
                distal_shift_ratio=(
                    evaluation["distalShiftRatio"]
                ),
                accepted=evaluation["accepted"],
                selected=False,
            )
            for index, evaluation in enumerate(evaluations)
        ]

        return None

    accepted_evaluations.sort(
        key=lambda evaluation: (
            evaluation["temporalScore"],
            evaluation["candidate"]["score"],
            evaluation["candidate"][
                "line"
            ]["lengthPixels"],
        ),
        reverse=True,
    )

    selected_evaluation = (
        accepted_evaluations[0]
    )

    diagnostics[
        "temporalSelectionMode"
    ] = "temporal"

    diagnostics[
        "selectedTemporalScore"
    ] = selected_evaluation[
        "temporalScore"
    ]

    diagnostics[
        "selectedAngleChangeDegrees"
    ] = selected_evaluation[
        "angleChangeDegrees"
    ]

    diagnostics[
        "selectedDistalShiftRatio"
    ] = selected_evaluation[
        "distalShiftRatio"
    ]

    selected_candidate = selected_evaluation[
        "candidate"
    ]

    diagnostics["candidateEvaluations"] = [
        build_candidate_evaluation_diagnostics(
            evaluation["candidate"],
            index=index,
            temporal_score=(
                evaluation["temporalScore"]
            ),
            angle_change_degrees=(
                evaluation["angleChangeDegrees"]
            ),
            distal_shift_ratio=(
                evaluation["distalShiftRatio"]
            ),
            accepted=evaluation["accepted"],
            selected=(
                evaluation["candidate"]
                is selected_candidate
            ),
        )
        for index, evaluation in enumerate(evaluations)
    ]

    return selected_candidate


def apply_temporal_consistency_validation(
    frame_results: list[ClubFrameDetection],
) -> None:
    previous_detection: ClubFrameDetection | None = None

    for frame_result in frame_results:
        frame_result["temporalComparison"] = None

        if not frame_result["detected"]:
            frame_result["temporalStatus"] = "unavailable"
            continue

        shaft_line = frame_result["shaftLine"]

        if shaft_line is None:
            frame_result["temporalStatus"] = "unavailable"
            continue

        if previous_detection is None:
            frame_result["temporalStatus"] = "not_compared"
            previous_detection = frame_result
            continue

        previous_shaft_line = previous_detection["shaftLine"]

        if previous_shaft_line is None:
            frame_result["temporalStatus"] = "not_compared"
            previous_detection = frame_result
            continue

        angle_change = calculate_axial_angle_change(
            previous_shaft_line["angleDegrees"],
            shaft_line["angleDegrees"],
        )

        within_threshold = (
            angle_change
            <= MAXIMUM_REFERENCE_ANGLE_CHANGE_DEGREES
        )

        frame_result["temporalComparison"] = {
            "previousPhase": previous_detection["phase"],
            "previousFrameIndex": previous_detection[
                "frameIndex"
            ],
            "angleChangeDegrees": round(
                angle_change,
                3,
            ),
            "withinThreshold": within_threshold,
        }

        frame_result["temporalStatus"] = (
            "consistent"
            if within_threshold
            else "review"
        )

        previous_detection = frame_result


def analyze_club_detection(
    *,
    video_path: Path,
    pose_timeline_path: Path,
    refined_phases_path: Path,
    output_path: Path | None = None,
    visualization_directory: Path | None = None,
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

    if not pose_frame_lookup:
        raise ValueError(
            "Pose timeline does not contain any "
            "usable indexed frames."
        )

    frame_requests = (
        build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=min(
                pose_frame_lookup
            ),
            maximum_frame_index=max(
                pose_frame_lookup
            ),
        )
    )

    resolved_visualization_directory = (
        visualization_directory
        if visualization_directory is not None
        else create_club_visualization_directory(
            refined_phases_path
        )
    )

    resolved_visualization_directory = (
        resolved_visualization_directory
        .expanduser()
        .resolve()
    )

    resolved_visualization_directory.mkdir(
        parents=True,
        exist_ok=True,
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

    previous_trusted_shaft_line: (
        ShaftLine | None
    ) = None

    previous_trusted_hand_anchor: (
        PixelPoint | None
    ) = None

    try:
        for frame_request in frame_requests:
            phase_name = frame_request[
                "phase"
            ]
            reference_frame_index = (
                frame_request[
                    "referenceFrameIndex"
                ]
            )
            frame_index = frame_request[
                "frameIndex"
            ]
            phase_offset_frames = (
                frame_request[
                    "phaseOffsetFrames"
                ]
            )
            is_reference_frame = (
                frame_request[
                    "isReferenceFrame"
                ]
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
                        "referenceFrameIndex": (
                            reference_frame_index
                        ),
                        "frameIndex": frame_index,
                        "phaseOffsetFrames": (
                            phase_offset_frames
                        ),
                        "isReferenceFrame": (
                            is_reference_frame
                        ),
                        "timestampSeconds": None,
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": None,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "candidateDiagnostics": None,
                        "failureReason": (
                            "Pose timeline did not "
                            "contain the requested "
                            "club-tracking frame."
                        ),
                        "debugImagePath": None,
                        "temporalStatus": "pending",
                        "temporalComparison": None,
                    }
                )
                continue

            timestamp_value = pose_frame.get(
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

            hand_anchor = calculate_hand_anchor(
                pose_frame,
                frame_width=rotated_width,
                frame_height=rotated_height,
            )

            if hand_anchor is None:
                frame_results.append(
                    {
                        "phase": phase_name,
                        "referenceFrameIndex": (
                            reference_frame_index
                        ),
                        "frameIndex": frame_index,
                        "phaseOffsetFrames": (
                            phase_offset_frames
                        ),
                        "isReferenceFrame": (
                            is_reference_frame
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": None,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "candidateDiagnostics": None,
                        "failureReason": (
                            "Reliable wrist "
                            "landmarks were not "
                            "available."
                        ),
                        "debugImagePath": None,
                        "temporalStatus": "pending",
                        "temporalComparison": None,
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
                        "referenceFrameIndex": (
                            reference_frame_index
                        ),
                        "frameIndex": frame_index,
                        "phaseOffsetFrames": (
                            phase_offset_frames
                        ),
                        "isReferenceFrame": (
                            is_reference_frame
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": hand_anchor,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "candidateDiagnostics": None,
                        "failureReason": (
                            "The requested club-tracking "
                            "video frame could not be read."
                        ),
                        "debugImagePath": None,
                        "temporalStatus": "pending",
                        "temporalComparison": None,
                    }
                )
                continue

            rotated_frame = rotate_frame(
                raw_frame,
                selected_rotation,
            )

            search_region = (
                build_pose_guided_search_region(
                    pose_frame,
                    hand_anchor=hand_anchor,
                    frame_width=rotated_width,
                    frame_height=rotated_height,
                )
            )

            corridor_mask = (
                build_pose_guided_corridor_mask(
                    pose_frame,
                    search_region=search_region,
                    hand_anchor=hand_anchor,
                    frame_width=rotated_width,
                    frame_height=rotated_height,
                )
                if search_region is not None
                else None
            )

            candidate_diagnostics = (
                create_candidate_diagnostics()
                if search_region is not None
                else None
            )

            candidates = (
                detect_shaft_candidates(
                    rotated_frame,
                    hand_anchor=hand_anchor,
                    search_region=search_region,
                    corridor_mask=corridor_mask,
                    diagnostics=(
                        candidate_diagnostics
                    ),
                )
                if (
                    search_region is not None
                    and candidate_diagnostics is not None
                )
                else []
            )

            debug_image_path = (
                create_club_visualization_path(
                    resolved_visualization_directory,
                    phase_name=phase_name,
                    frame_index=frame_index,
                )
            )

            if not candidates:
                failure_reason = (
                    (
                        "A pose-guided club search "
                        "region could not be created."
                    )
                    if search_region is None
                    else (
                        "No reliable shaft-line "
                        "candidate was found inside "
                        "the geometry-guided corridor "
                        "or rectangular fallback region."
                    )
                )

                visualization = (
                    draw_club_detection_visualization(
                        rotated_frame,
                        phase_name=phase_name,
                        frame_index=frame_index,
                        hand_anchor=hand_anchor,
                        search_region=search_region,
                        shaft_line=None,
                        confidence=0.0,
                        candidate_count=0,
                        candidate_diagnostics=(
                            candidate_diagnostics
                        ),
                        detected=False,
                        failure_reason=(
                            failure_reason
                        ),
                    )
                )

                save_club_detection_visualization(
                    debug_image_path,
                    visualization,
                )

                frame_results.append(
                    {
                        "phase": phase_name,
                        "referenceFrameIndex": (
                            reference_frame_index
                        ),
                        "frameIndex": frame_index,
                        "phaseOffsetFrames": (
                            phase_offset_frames
                        ),
                        "isReferenceFrame": (
                            is_reference_frame
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
                        "handAnchor": hand_anchor,
                        "shaftLine": None,
                        "candidateCount": 0,
                        "candidateDiagnostics": (
                            candidate_diagnostics
                        ),
                        "failureReason": failure_reason,
                        "debugImagePath": str(
                            debug_image_path
                        ),
                        "temporalStatus": "pending",
                        "temporalComparison": None,
                    }
                )

                continue

            assert candidate_diagnostics is not None

            best_candidate = select_shaft_candidate(
                candidates,
                current_hand_anchor=hand_anchor,
                previous_shaft_line=(
                    previous_trusted_shaft_line
                ),
                previous_hand_anchor=(
                    previous_trusted_hand_anchor
                ),
                frame_width=rotated_width,
                frame_height=rotated_height,
                diagnostics=candidate_diagnostics,
            )

            if best_candidate is None:
                failure_reason = (
                    "Shaft candidates were found, but "
                    "none were temporally believable "
                    "relative to the previous trusted "
                    "club detection."
                )

                visualization = (
                    draw_club_detection_visualization(
                        rotated_frame,
                        phase_name=phase_name,
                        frame_index=frame_index,
                        hand_anchor=hand_anchor,
                        search_region=search_region,
                        shaft_line=None,
                        confidence=0.0,
                        candidate_count=len(candidates),
                        candidate_diagnostics=(
                            candidate_diagnostics
                        ),
                        detected=False,
                        failure_reason=(
                            failure_reason
                        ),
                    )
                )

                save_club_detection_visualization(
                    debug_image_path,
                    visualization,
                )

                frame_results.append(
                    {
                        "phase": phase_name,
                        "referenceFrameIndex": (
                            reference_frame_index
                        ),
                        "frameIndex": frame_index,
                        "phaseOffsetFrames": (
                            phase_offset_frames
                        ),
                        "isReferenceFrame": (
                            is_reference_frame
                        ),
                        "timestampSeconds": (
                            timestamp_seconds
                        ),
                        "detected": False,
                        "confidence": 0.0,
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
                        "shaftLine": None,
                        "candidateCount": len(candidates),
                        "candidateDiagnostics": (
                            candidate_diagnostics
                        ),
                        "failureReason": failure_reason,
                        "debugImagePath": str(
                            debug_image_path
                        ),
                        "temporalStatus": "pending",
                        "temporalComparison": None,
                    }
                )

                continue

            confidence = round(
                (
                    candidate_diagnostics[
                        "selectedTemporalScore"
                    ]
                    if candidate_diagnostics[
                        "selectedTemporalScore"
                    ]
                    is not None
                    else best_candidate["score"]
                ),
                3,
            )

            shaft_line = best_candidate["line"]

            previous_trusted_shaft_line = shaft_line

            previous_trusted_hand_anchor = {
                "x": hand_anchor["x"],
                "y": hand_anchor["y"],
            }

            visualization = (
                draw_club_detection_visualization(
                    rotated_frame,
                    phase_name=phase_name,
                    frame_index=frame_index,
                    hand_anchor=hand_anchor,
                    search_region=search_region,
                    shaft_line=shaft_line,
                    confidence=confidence,
                    candidate_count=len(candidates),
                    candidate_diagnostics=(
                        candidate_diagnostics
                    ),
                    detected=True,
                    failure_reason=None,
                )
            )

            save_club_detection_visualization(
                debug_image_path,
                visualization,
            )

            frame_results.append(
                {
                    "phase": phase_name,
                    "referenceFrameIndex": (
                        reference_frame_index
                    ),
                    "frameIndex": frame_index,
                    "phaseOffsetFrames": (
                        phase_offset_frames
                    ),
                    "isReferenceFrame": (
                        is_reference_frame
                    ),
                    "timestampSeconds": (
                        timestamp_seconds
                    ),
                    "detected": True,
                    "confidence": confidence,
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
                    "shaftLine": shaft_line,
                    "candidateCount": len(candidates),
                    "candidateDiagnostics": (
                        candidate_diagnostics
                    ),
                    "failureReason": None,
                    "debugImagePath": str(
                        debug_image_path
                    ),
                    "temporalStatus": "pending",
                    "temporalComparison": None,
                }
            )
    finally:
        video.release()

    apply_temporal_consistency_validation(
        frame_results
    )

    detected_results = [
        frame
        for frame in frame_results
        if frame["detected"]
    ]

    visualized_results = [
        frame
        for frame in frame_results
        if frame["debugImagePath"] is not None
    ]

    temporal_comparisons = [
        comparison
        for frame in frame_results
        if (
            comparison
            := frame["temporalComparison"]
        )
        is not None
    ]

    temporally_consistent_results = [
        frame
        for frame in frame_results
        if frame["temporalStatus"] == "consistent"
    ]

    temporal_review_results = [
        frame
        for frame in frame_results
        if frame["temporalStatus"] == "review"
    ]

    maximum_angle_change = (
        max(
            comparison["angleChangeDegrees"]
            for comparison in temporal_comparisons
        )
        if temporal_comparisons
        else None
    )

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
        "visualizationDirectory": str(
            resolved_visualization_directory
        ),
        "assumptions": {
            "detectedObject": (
                "probable-golf-shaft-line"
            ),
            "coordinateSystem": (
                "rotated-video-pixels"
            ),
            "candidateSearch": (
                "Standard Canny edge detection and dual-pass "
                "probabilistic Hough detection first run inside "
                "a rotated geometry-guided corridor estimated "
                "from the golfer's forearms and hands. If both "
                "standard corridor passes fail, CLAHE-enhanced "
                "grayscale data and locally adaptive Canny "
                "thresholds receive one additional corridor-only "
                "primary and short-line fallback attempt. The "
                "broader pose-guided rectangle remains the final "
                "fallback."
            ),
            "referenceFrameSource": (
                "golf-phase-refiner"
            ),
            "frameSampling": (
                "Each golf reference phase is expanded "
                "into a bounded dense frame window. "
                "Overlapping frames are processed once "
                "and assigned to the nearest reference "
                "phase."
            ),
            "temporalValidation": (
                "Successful dense-frame detections are "
                "compared chronologically using the "
                "smallest undirected shaft-angle change. "
                "Large changes are retained and marked "
                "for review rather than rejected."
            ),
            "candidateDiagnostics": (
                "Each processed search region records full "
                "and corridor edge density, per-pass raw "
                "and merged Hough line counts, segment merge "
                "totals, accepted candidate "
                "count, image-filter rejection totals, and "
                "a serializable record for every candidate "
                "evaluated during image-only or temporal "
                "selection. Candidate records also preserve "
                "search-region, edge-source, Hough-pass, and "
                "segment-merging provenance."
            ),
            "visualizations": (
                "Debug images show the selected "
                "shaft candidate and detected hand "
                "anchor for inspection. They are "
                "diagnostic artifacts and are not "
                "part of the final coaching report."
            ),
            "limitations": [
                (
                    "Line detection does not "
                    "identify the club model or "
                    "club type."
                ),
                (
                    "Forearm direction is only an estimate "
                    "of shaft direction. Wrist hinge and "
                    "release can cause the shaft to diverge "
                    "from the focused corridor, so a broader "
                    "rectangular fallback remains necessary."
                ),
                (
                    "Body edges, clothing, shadows, "
                    "and background objects can "
                    "produce competing line "
                    "candidates."
                ),
                (
                    "A temporal review status identifies "
                    "an unusually large shaft-angle change "
                    "between successful dense-frame "
                    "detections, but does not by itself "
                    "prove that either detection is wrong."
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
                frame_requests
            ),
            "processedFrames": processed_count,
            "detectedFrames": detected_count,
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
            "selectedRotation": selected_rotation,
            "visualizationCount": len(
                visualized_results
            ),
            "temporalComparisonCount": len(
                temporal_comparisons
            ),
            "temporallyConsistentFrames": len(
                temporally_consistent_results
            ),
            "temporalReviewFrames": len(
                temporal_review_results
            ),
            "maximumAngleChangeDegrees": (
                round(
                    maximum_angle_change,
                    3,
                )
                if maximum_angle_change is not None
                else None
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
        "clubVisualizationDirectory": str(
            resolved_visualization_directory
        ),
        "clubDetection": result,
    }