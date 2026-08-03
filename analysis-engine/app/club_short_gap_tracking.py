from __future__ import annotations

import math
from typing import Any, MutableMapping, Sequence


MAXIMUM_TRACKING_FRAME_SPAN = 4
MAXIMUM_TRACKING_SURROUNDING_ANGLE_CHANGE_DEGREES = 55.0
MAXIMUM_TRACKING_ANCHOR_RESIDUAL_RATIO = 0.04
TRACKING_CONFIDENCE_SCALE = 0.72
MAXIMUM_TRACKED_CONFIDENCE = 0.70
MINIMUM_TRACKED_LINE_LENGTH_RATIO = 0.04
MAXIMUM_TRACKED_LINE_LENGTH_RATIO = 0.55


FrameRecord = MutableMapping[str, Any]
PointRecord = MutableMapping[str, float]
LineRecord = MutableMapping[str, Any]


def clamp_confidence(value: float) -> float:
    return min(1.0, max(0.0, value))


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


def interpolate_value(
    first_value: float,
    second_value: float,
    ratio: float,
) -> float:
    return (
        first_value
        + (second_value - first_value) * ratio
    )


def interpolate_point(
    first_point: PointRecord,
    second_point: PointRecord,
    ratio: float,
) -> dict[str, float]:
    return {
        "x": interpolate_value(
            first_point["x"],
            second_point["x"],
            ratio,
        ),
        "y": interpolate_value(
            first_point["y"],
            second_point["y"],
            ratio,
        ),
    }


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


def build_short_gap_tracked_line(
    previous_frame: FrameRecord,
    current_frame: FrameRecord,
    next_frame: FrameRecord,
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if frame_width <= 0 or frame_height <= 0:
        return None

    if (
        not previous_frame.get("detected")
        or not next_frame.get("detected")
        or previous_frame.get("detectionSource") != "image"
        or next_frame.get("detectionSource") != "image"
    ):
        return None

    previous_line = previous_frame.get("shaftLine")
    next_line = next_frame.get("shaftLine")

    previous_anchor = previous_frame.get("handAnchor")
    current_anchor = current_frame.get("handAnchor")
    next_anchor = next_frame.get("handAnchor")

    if (
        previous_line is None
        or next_line is None
        or previous_anchor is None
        or current_anchor is None
        or next_anchor is None
    ):
        return None

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
        return None

    assert isinstance(previous_index, int)
    assert isinstance(current_index, int)
    assert isinstance(next_index, int)

    frame_span = next_index - previous_index

    if (
        frame_span <= 0
        or frame_span > MAXIMUM_TRACKING_FRAME_SPAN
        or current_index <= previous_index
        or current_index >= next_index
    ):
        return None

    interpolation_ratio = (
        (current_index - previous_index)
        / frame_span
    )

    surrounding_angle_change = (
        calculate_axial_angle_change(
            float(previous_line["angleDegrees"]),
            float(next_line["angleDegrees"]),
        )
    )

    if (
        surrounding_angle_change
        > MAXIMUM_TRACKING_SURROUNDING_ANGLE_CHANGE_DEGREES
    ):
        return None

    frame_diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    predicted_anchor = interpolate_point(
        previous_anchor,
        next_anchor,
        interpolation_ratio,
    )

    anchor_residual_ratio = (
        calculate_line_length(
            predicted_anchor,
            current_anchor,
        )
        / frame_diagonal
    )

    if (
        anchor_residual_ratio
        > MAXIMUM_TRACKING_ANCHOR_RESIDUAL_RATIO
    ):
        return None

    previous_grip, previous_distal = (
        get_grip_and_distal_endpoints(
            previous_line,
            previous_anchor,
        )
    )

    next_grip, next_distal = (
        get_grip_and_distal_endpoints(
            next_line,
            next_anchor,
        )
    )

    interpolated_grip = interpolate_point(
        previous_grip,
        next_grip,
        interpolation_ratio,
    )

    interpolated_distal = interpolate_point(
        previous_distal,
        next_distal,
        interpolation_ratio,
    )

    anchor_shift_x = (
        current_anchor["x"]
        - predicted_anchor["x"]
    )

    anchor_shift_y = (
        current_anchor["y"]
        - predicted_anchor["y"]
    )

    tracked_grip = {
        "x": interpolated_grip["x"] + anchor_shift_x,
        "y": interpolated_grip["y"] + anchor_shift_y,
    }

    tracked_distal = {
        "x": interpolated_distal["x"] + anchor_shift_x,
        "y": interpolated_distal["y"] + anchor_shift_y,
    }

    tracked_length = calculate_line_length(
        tracked_grip,
        tracked_distal,
    )

    tracked_length_ratio = (
        tracked_length / frame_diagonal
    )

    if (
        tracked_length_ratio
        < MINIMUM_TRACKED_LINE_LENGTH_RATIO
        or tracked_length_ratio
        > MAXIMUM_TRACKED_LINE_LENGTH_RATIO
    ):
        return None

    tracked_line = {
        "start": {
            "x": round(tracked_grip["x"], 3),
            "y": round(tracked_grip["y"], 3),
        },
        "end": {
            "x": round(tracked_distal["x"], 3),
            "y": round(tracked_distal["y"], 3),
        },
        "lengthPixels": round(
            tracked_length,
            3,
        ),
        "angleDegrees": round(
            calculate_line_angle(
                tracked_grip,
                tracked_distal,
            ),
            3,
        ),
    }

    tracking_details = {
        "previousFrameIndex": previous_index,
        "nextFrameIndex": next_index,
        "interpolationRatio": round(
            interpolation_ratio,
            6,
        ),
        "surroundingAngleChangeDegrees": round(
            surrounding_angle_change,
            3,
        ),
        "anchorResidualRatio": round(
            anchor_residual_ratio,
            6,
        ),
        "confidenceScale": TRACKING_CONFIDENCE_SCALE,
    }

    return tracked_line, tracking_details


def apply_short_gap_tracking(
    frame_results: Sequence[FrameRecord],
    *,
    frame_width: int,
    frame_height: int,
) -> dict[str, int]:
    for frame_result in frame_results:
        frame_result["detectionSource"] = (
            "image"
            if frame_result.get("detected")
            else "unavailable"
        )
        frame_result["trackingDetails"] = None

    tracked_count = 0

    for index in range(
        1,
        len(frame_results) - 1,
    ):
        current_frame = frame_results[index]

        if current_frame.get("detected"):
            continue

        previous_frame = frame_results[index - 1]
        next_frame = frame_results[index + 1]

        tracked_result = build_short_gap_tracked_line(
            previous_frame,
            current_frame,
            next_frame,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if tracked_result is None:
            continue

        tracked_line, tracking_details = tracked_result

        interpolation_ratio = tracking_details[
            "interpolationRatio"
        ]

        neighbor_confidence = (
            float(previous_frame.get("confidence", 0.0))
            * (1.0 - interpolation_ratio)
            + float(next_frame.get("confidence", 0.0))
            * interpolation_ratio
        )

        tracked_confidence = min(
            MAXIMUM_TRACKED_CONFIDENCE,
            neighbor_confidence
            * TRACKING_CONFIDENCE_SCALE,
        )

        current_frame["detected"] = True
        current_frame["detectionSource"] = "tracked"
        current_frame["confidence"] = round(
            clamp_confidence(tracked_confidence),
            3,
        )
        current_frame["shaftLine"] = tracked_line
        current_frame["failureReason"] = None
        current_frame["trackingDetails"] = tracking_details
        current_frame["temporalStatus"] = "pending"
        current_frame["temporalComparison"] = None

        tracked_count += 1

    return {
        "trackedFrames": tracked_count,
        "imageDetectedFrames": sum(
            1
            for frame in frame_results
            if (
                frame.get("detected")
                and frame.get("detectionSource") == "image"
            )
        ),
    }