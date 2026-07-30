from __future__ import annotations

import math
from typing import Any, Mapping, TypedDict

import numpy as np


LEFT_ELBOW_INDEX = 13
RIGHT_ELBOW_INDEX = 14
LEFT_WRIST_INDEX = 15
RIGHT_WRIST_INDEX = 16

MINIMUM_LANDMARK_VISIBILITY = 0.35

SEARCH_FORWARD_DIAGONAL_RATIO = 0.34
SEARCH_BACKWARD_DIAGONAL_RATIO = 0.05
SEARCH_HALF_WIDTH_DIAGONAL_RATIO = 0.11

MINIMUM_SEARCH_REGION_SIZE_PIXELS = 48


class PixelPoint(TypedDict):
    x: float
    y: float


class DirectionVector(TypedDict):
    x: float
    y: float


class SearchRegion(TypedDict):
    xMin: int
    yMin: int
    xMax: int
    yMax: int
    width: int
    height: int


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

    if (
        float(visibility)
        < MINIMUM_LANDMARK_VISIBILITY
    ):
        return None

    return {
        "x": float(x) * frame_width,
        "y": float(y) * frame_height,
    }


def normalize_direction(
    x: float,
    y: float,
) -> DirectionVector | None:
    magnitude = math.hypot(
        x,
        y,
    )

    if magnitude <= 0.0:
        return None

    return {
        "x": x / magnitude,
        "y": y / magnitude,
    }


def calculate_forearm_direction(
    elbow: PixelPoint,
    wrist: PixelPoint,
) -> DirectionVector | None:
    return normalize_direction(
        wrist["x"] - elbow["x"],
        wrist["y"] - elbow["y"],
    )


def estimate_club_extension_direction(
    pose_frame: Mapping[str, Any],
    *,
    frame_width: int,
    frame_height: int,
) -> DirectionVector | None:
    if frame_width <= 0 or frame_height <= 0:
        return None

    landmark_map = get_landmark_map(
        pose_frame
    )

    arm_indices = (
        (
            LEFT_ELBOW_INDEX,
            LEFT_WRIST_INDEX,
        ),
        (
            RIGHT_ELBOW_INDEX,
            RIGHT_WRIST_INDEX,
        ),
    )

    directions: list[
        DirectionVector
    ] = []

    for elbow_index, wrist_index in (
        arm_indices
    ):
        elbow_landmark = landmark_map.get(
            elbow_index
        )
        wrist_landmark = landmark_map.get(
            wrist_index
        )

        if (
            elbow_landmark is None
            or wrist_landmark is None
        ):
            continue

        elbow = landmark_to_pixel_point(
            elbow_landmark,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        wrist = landmark_to_pixel_point(
            wrist_landmark,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if elbow is None or wrist is None:
            continue

        direction = (
            calculate_forearm_direction(
                elbow,
                wrist,
            )
        )

        if direction is not None:
            directions.append(direction)

    if not directions:
        return None

    average_x = sum(
        direction["x"]
        for direction in directions
    ) / len(directions)

    average_y = sum(
        direction["y"]
        for direction in directions
    ) / len(directions)

    average_direction = normalize_direction(
        average_x,
        average_y,
    )

    if average_direction is not None:
        return average_direction

    return directions[0]


def clamp_integer(
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    return max(
        minimum,
        min(maximum, value),
    )


def create_search_region_from_direction(
    *,
    hand_anchor: PixelPoint,
    direction: DirectionVector,
    frame_width: int,
    frame_height: int,
) -> SearchRegion | None:
    if frame_width <= 0 or frame_height <= 0:
        return None

    normalized_direction = normalize_direction(
        direction["x"],
        direction["y"],
    )

    if normalized_direction is None:
        return None

    diagonal = math.hypot(
        frame_width,
        frame_height,
    )

    forward_distance = (
        diagonal
        * SEARCH_FORWARD_DIAGONAL_RATIO
    )

    backward_distance = (
        diagonal
        * SEARCH_BACKWARD_DIAGONAL_RATIO
    )

    half_width = (
        diagonal
        * SEARCH_HALF_WIDTH_DIAGONAL_RATIO
    )

    start_x = (
        hand_anchor["x"]
        - normalized_direction["x"]
        * backward_distance
    )

    start_y = (
        hand_anchor["y"]
        - normalized_direction["y"]
        * backward_distance
    )

    end_x = (
        hand_anchor["x"]
        + normalized_direction["x"]
        * forward_distance
    )

    end_y = (
        hand_anchor["y"]
        + normalized_direction["y"]
        * forward_distance
    )

    raw_x_min = math.floor(
        min(start_x, end_x)
        - half_width
    )

    raw_y_min = math.floor(
        min(start_y, end_y)
        - half_width
    )

    raw_x_max = math.ceil(
        max(start_x, end_x)
        + half_width
    )

    raw_y_max = math.ceil(
        max(start_y, end_y)
        + half_width
    )

    x_min = clamp_integer(
        raw_x_min,
        minimum=0,
        maximum=frame_width,
    )

    y_min = clamp_integer(
        raw_y_min,
        minimum=0,
        maximum=frame_height,
    )

    x_max = clamp_integer(
        raw_x_max,
        minimum=0,
        maximum=frame_width,
    )

    y_max = clamp_integer(
        raw_y_max,
        minimum=0,
        maximum=frame_height,
    )

    width = x_max - x_min
    height = y_max - y_min

    if (
        width
        < MINIMUM_SEARCH_REGION_SIZE_PIXELS
        or height
        < MINIMUM_SEARCH_REGION_SIZE_PIXELS
    ):
        return None

    return {
        "xMin": x_min,
        "yMin": y_min,
        "xMax": x_max,
        "yMax": y_max,
        "width": width,
        "height": height,
    }


def build_pose_guided_search_region(
    pose_frame: Mapping[str, Any],
    *,
    hand_anchor: PixelPoint,
    frame_width: int,
    frame_height: int,
) -> SearchRegion | None:
    direction = (
        estimate_club_extension_direction(
            pose_frame,
            frame_width=frame_width,
            frame_height=frame_height,
        )
    )

    if direction is None:
        return None

    return create_search_region_from_direction(
        hand_anchor=hand_anchor,
        direction=direction,
        frame_width=frame_width,
        frame_height=frame_height,
    )


def crop_frame_to_search_region(
    frame: np.ndarray,
    search_region: SearchRegion,
) -> np.ndarray:
    if frame.size == 0:
        raise ValueError(
            "Cannot crop an empty frame."
        )

    return frame[
        search_region["yMin"]:
        search_region["yMax"],
        search_region["xMin"]:
        search_region["xMax"],
    ]


def translate_coordinates_to_full_frame(
    coordinates: list[int],
    *,
    search_region: SearchRegion,
) -> list[int]:
    if len(coordinates) != 4:
        raise ValueError(
            "Line coordinates must contain "
            "exactly four values."
        )

    return [
        coordinates[0]
        + search_region["xMin"],
        coordinates[1]
        + search_region["yMin"],
        coordinates[2]
        + search_region["xMin"],
        coordinates[3]
        + search_region["yMin"],
    ]