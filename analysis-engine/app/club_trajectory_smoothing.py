from __future__ import annotations

import math
from typing import Any, MutableMapping, Sequence


MAXIMUM_SMOOTHING_FRAME_GAP = 4
MAXIMUM_SMOOTHING_NEIGHBOR_ANGLE_CHANGE_DEGREES = 45.0
MAXIMUM_SMOOTHING_ANGLE_ADJUSTMENT_DEGREES = 5.0

CURRENT_FRAME_WEIGHT = 0.50
PREVIOUS_FRAME_WEIGHT = 0.25
NEXT_FRAME_WEIGHT = 0.25

MINIMUM_SMOOTHED_LINE_LENGTH_RATIO = 0.04
MAXIMUM_SMOOTHED_LINE_LENGTH_RATIO = 0.55


FrameRecord = MutableMapping[str, Any]
PointRecord = MutableMapping[str, float]
LineRecord = MutableMapping[str, Any]


def calculate_line_length(
    first_point: PointRecord,
    second_point: PointRecord,
) -> float:
    return math.hypot(
        second_point["x"] - first_point["x"],
        second_point["y"] - first_point["y"],
    )


def calculate_line_angle(
    first_point: PointRecord,
    second_point: PointRecord,
) -> float:
    angle = math.degrees(
        math.atan2(
            second_point["y"] - first_point["y"],
            second_point["x"] - first_point["x"],
        )
    )

    while angle < 0.0:
        angle += 180.0

    while angle >= 180.0:
        angle -= 180.0

    return angle


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
    shaft_line: LineRecord,
    hand_anchor: PointRecord,
) -> tuple[PointRecord, PointRecord]:
    start = shaft_line["start"]
    end = shaft_line["end"]

    start_distance = calculate_line_length(
        hand_anchor,
        start,
    )

    end_distance = calculate_line_length(
        hand_anchor,
        end,
    )

    if start_distance <= end_distance:
        return start, end

    return end, start


def translate_point_to_anchor(
    point: PointRecord,
    *,
    source_anchor: PointRecord,
    target_anchor: PointRecord,
) -> dict[str, float]:
    return {
        "x": (
            point["x"]
            + target_anchor["x"]
            - source_anchor["x"]
        ),
        "y": (
            point["y"]
            + target_anchor["y"]
            - source_anchor["y"]
        ),
    }


def weighted_point(
    points_and_weights: Sequence[
        tuple[PointRecord, float]
    ],
) -> dict[str, float]:
    total_weight = sum(
        weight
        for _, weight in points_and_weights
    )

    if total_weight <= 0.0:
        raise ValueError(
            "Point weights must sum to a positive value."
        )

    return {
        "x": sum(
            point["x"] * weight
            for point, weight in points_and_weights
        ) / total_weight,
        "y": sum(
            point["y"] * weight
            for point, weight in points_and_weights
        ) / total_weight,
    }


def _evaluate_smoothed_shaft_line(
    previous_frame: FrameRecord,
    current_frame: FrameRecord,
    next_frame: FrameRecord,
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[
    tuple[dict[str, Any], dict[str, Any]] | None,
    str,
]:
    if frame_width <= 0 or frame_height <= 0:
        return None, "invalid_frame_dimensions"

    if not all(
        frame.get("detected")
        for frame in (
            previous_frame,
            current_frame,
            next_frame,
        )
    ):
        return None, "missing_detection"

    previous_line = previous_frame.get("shaftLine")
    current_line = current_frame.get("shaftLine")
    next_line = next_frame.get("shaftLine")

    previous_anchor = previous_frame.get("handAnchor")
    current_anchor = current_frame.get("handAnchor")
    next_anchor = next_frame.get("handAnchor")

    if any(
        value is None
        for value in (
            previous_line,
            current_line,
            next_line,
            previous_anchor,
            current_anchor,
            next_anchor,
        )
    ):
        return None, "missing_geometry"

    previous_index = previous_frame.get("frameIndex")
    current_index = current_frame.get("frameIndex")
    next_index = next_frame.get("frameIndex")

    if not all(
        isinstance(value, int)
        for value in (
            previous_index,
            current_index,
            next_index,
        )
    ):
        return None, "invalid_frame_indices"

    assert isinstance(previous_index, int)
    assert isinstance(current_index, int)
    assert isinstance(next_index, int)

    previous_gap = current_index - previous_index
    next_gap = next_index - current_index

    if (
        previous_gap <= 0
        or next_gap <= 0
        or previous_gap > MAXIMUM_SMOOTHING_FRAME_GAP
        or next_gap > MAXIMUM_SMOOTHING_FRAME_GAP
    ):
        return None, "frame_gap_exceeds_threshold"

    previous_angle_change = (
        calculate_axial_angle_change(
            float(previous_line["angleDegrees"]),
            float(current_line["angleDegrees"]),
        )
    )

    next_angle_change = (
        calculate_axial_angle_change(
            float(current_line["angleDegrees"]),
            float(next_line["angleDegrees"]),
        )
    )

    if (
        previous_angle_change
        > MAXIMUM_SMOOTHING_NEIGHBOR_ANGLE_CHANGE_DEGREES
        or next_angle_change
        > MAXIMUM_SMOOTHING_NEIGHBOR_ANGLE_CHANGE_DEGREES
    ):
        return None, "neighbor_angle_change_exceeds_threshold"

    previous_grip, previous_distal = (
        get_grip_and_distal_endpoints(
            previous_line,
            previous_anchor,
        )
    )
    current_grip, current_distal = (
        get_grip_and_distal_endpoints(
            current_line,
            current_anchor,
        )
    )
    next_grip, next_distal = (
        get_grip_and_distal_endpoints(
            next_line,
            next_anchor,
        )
    )

    aligned_previous_grip = translate_point_to_anchor(
        previous_grip,
        source_anchor=previous_anchor,
        target_anchor=current_anchor,
    )
    aligned_previous_distal = translate_point_to_anchor(
        previous_distal,
        source_anchor=previous_anchor,
        target_anchor=current_anchor,
    )
    aligned_next_grip = translate_point_to_anchor(
        next_grip,
        source_anchor=next_anchor,
        target_anchor=current_anchor,
    )
    aligned_next_distal = translate_point_to_anchor(
        next_distal,
        source_anchor=next_anchor,
        target_anchor=current_anchor,
    )

    smoothed_grip = weighted_point(
        (
            (
                aligned_previous_grip,
                PREVIOUS_FRAME_WEIGHT,
            ),
            (
                current_grip,
                CURRENT_FRAME_WEIGHT,
            ),
            (
                aligned_next_grip,
                NEXT_FRAME_WEIGHT,
            ),
        )
    )

    smoothed_distal = weighted_point(
        (
            (
                aligned_previous_distal,
                PREVIOUS_FRAME_WEIGHT,
            ),
            (
                current_distal,
                CURRENT_FRAME_WEIGHT,
            ),
            (
                aligned_next_distal,
                NEXT_FRAME_WEIGHT,
            ),
        )
    )

    frame_diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    smoothed_length = calculate_line_length(
        smoothed_grip,
        smoothed_distal,
    )
    smoothed_length_ratio = (
        smoothed_length / frame_diagonal
    )

    if (
        smoothed_length_ratio
        < MINIMUM_SMOOTHED_LINE_LENGTH_RATIO
        or smoothed_length_ratio
        > MAXIMUM_SMOOTHED_LINE_LENGTH_RATIO
    ):
        return None, "smoothed_length_outside_range"

    raw_angle = float(
        current_line["angleDegrees"]
    )
    smoothed_angle = calculate_line_angle(
        smoothed_grip,
        smoothed_distal,
    )
    angle_adjustment = (
        calculate_axial_angle_change(
            raw_angle,
            smoothed_angle,
        )
    )

    if (
        angle_adjustment
        > MAXIMUM_SMOOTHING_ANGLE_ADJUSTMENT_DEGREES
    ):
        return (
            None,
            "angle_adjustment_exceeds_threshold",
        )

    smoothed_line = {
        "start": {
            "x": round(smoothed_grip["x"], 3),
            "y": round(smoothed_grip["y"], 3),
        },
        "end": {
            "x": round(smoothed_distal["x"], 3),
            "y": round(smoothed_distal["y"], 3),
        },
        "lengthPixels": round(
            smoothed_length,
            3,
        ),
        "angleDegrees": round(
            smoothed_angle,
            3,
        ),
    }

    smoothing_details = {
        "applied": True,
        "neighborFrameIndices": [
            previous_index,
            current_index,
            next_index,
        ],
        "rawAngleDegrees": round(
            raw_angle,
            3,
        ),
        "smoothedAngleDegrees": round(
            smoothed_angle,
            3,
        ),
        "angleAdjustmentDegrees": round(
            angle_adjustment,
            3,
        ),
        "previousAngleChangeDegrees": round(
            previous_angle_change,
            3,
        ),
        "nextAngleChangeDegrees": round(
            next_angle_change,
            3,
        ),
        "weights": {
            "previous": PREVIOUS_FRAME_WEIGHT,
            "current": CURRENT_FRAME_WEIGHT,
            "next": NEXT_FRAME_WEIGHT,
        },
    }

    return (
        (smoothed_line, smoothing_details),
        "applied",
    )


def build_smoothed_shaft_line(
    previous_frame: FrameRecord,
    current_frame: FrameRecord,
    next_frame: FrameRecord,
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    result, _ = _evaluate_smoothed_shaft_line(
        previous_frame,
        current_frame,
        next_frame,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    return result


def apply_club_trajectory_smoothing(
    frame_results: Sequence[FrameRecord],
    *,
    frame_width: int,
    frame_height: int,
) -> dict[str, int]:
    for frame_result in frame_results:
        frame_result["smoothedShaftLine"] = None
        frame_result["smoothingDetails"] = {
            "applied": False,
            "neighborFrameIndices": [],
            "reason": "not_eligible",
        }

    smoothed_count = 0

    for index in range(
        1,
        len(frame_results) - 1,
    ):
        result, reason = _evaluate_smoothed_shaft_line(
            frame_results[index - 1],
            frame_results[index],
            frame_results[index + 1],
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if result is None:
            frame_results[index][
                "smoothingDetails"
            ] = {
                "applied": False,
                "neighborFrameIndices": [],
                "reason": reason,
            }
            continue

        smoothed_line, smoothing_details = result

        frame_results[index][
            "smoothedShaftLine"
        ] = smoothed_line
        frame_results[index][
            "smoothingDetails"
        ] = smoothing_details

        smoothed_count += 1

    return {
        "smoothedFrames": smoothed_count,
        "rawDetectedFrames": sum(
            1
            for frame in frame_results
            if (
                frame.get("detected")
                and frame.get("shaftLine") is not None
            )
        ),
    }