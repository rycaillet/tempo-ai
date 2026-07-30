from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np


TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.55
TEXT_THICKNESS = 1
LINE_THICKNESS = 4
ANCHOR_RADIUS = 7
SEARCH_REGION_THICKNESS = 2


def create_club_visualization_directory(
    refined_phases_path: Path,
) -> Path:
    file_name = refined_phases_path.name
    suffix = "-refined-phases.json"

    if file_name.endswith(suffix):
        stem = file_name[:-len(suffix)]
    else:
        stem = refined_phases_path.stem

    return (
        refined_phases_path.parent
        / f"{stem}-club-detection-frames"
    )


def sanitize_phase_name(
    phase_name: str,
) -> str:
    sanitized = re.sub(
        r"[^A-Za-z0-9_-]+",
        "-",
        phase_name.strip(),
    )

    sanitized = (
        sanitized
        .strip("-")
        .lower()
    )

    return sanitized or "unknown-phase"


def create_club_visualization_path(
    output_directory: Path,
    *,
    phase_name: str,
    frame_index: int,
) -> Path:
    safe_phase_name = sanitize_phase_name(
        phase_name
    )

    return output_directory / (
        f"{safe_phase_name}"
        f"-frame-{frame_index:06d}.jpg"
    )


def point_to_integer_tuple(
    point: Mapping[str, Any],
) -> tuple[int, int] | None:
    x = point.get("x")
    y = point.get("y")

    if not isinstance(x, (int, float)):
        return None

    if not isinstance(y, (int, float)):
        return None

    return (
        int(round(float(x))),
        int(round(float(y))),
    )


def get_search_region_corners(
    search_region: Mapping[str, Any],
) -> tuple[
    tuple[int, int],
    tuple[int, int],
] | None:
    x_min = search_region.get("xMin")
    y_min = search_region.get("yMin")
    x_max = search_region.get("xMax")
    y_max = search_region.get("yMax")

    values = (
        x_min,
        y_min,
        x_max,
        y_max,
    )

    if not all(
        isinstance(value, (int, float))
        for value in values
    ):
        return None

    return (
        (
            int(round(float(x_min))),
            int(round(float(y_min))),
        ),
        (
            int(round(float(x_max))),
            int(round(float(y_max))),
        ),
    )


def draw_text_line(
    image: np.ndarray,
    text: str,
    *,
    line_number: int,
) -> None:
    x = 16
    y = 28 + line_number * 24

    text_size, baseline = cv2.getTextSize(
        text,
        TEXT_FONT,
        TEXT_SCALE,
        TEXT_THICKNESS,
    )

    text_width, text_height = text_size

    cv2.rectangle(
        image,
        (
            x - 6,
            y - text_height - 6,
        ),
        (
            x + text_width + 6,
            y + baseline + 6,
        ),
        (0, 0, 0),
        thickness=-1,
    )

    cv2.putText(
        image,
        text,
        (x, y),
        TEXT_FONT,
        TEXT_SCALE,
        (255, 255, 255),
        TEXT_THICKNESS,
        cv2.LINE_AA,
    )


def get_diagnostic_count(
    diagnostics: Mapping[str, Any],
    key: str,
) -> int:
    value = diagnostics.get(key, 0)

    if isinstance(value, int):
        return value

    return 0


def get_diagnostic_float(
    diagnostics: Mapping[str, Any],
    key: str,
) -> float | None:
    value = diagnostics.get(key)

    if isinstance(value, (int, float)):
        return float(value)

    return None


def get_diagnostic_text(
    diagnostics: Mapping[str, Any],
    key: str,
    default: str,
) -> str:
    value = diagnostics.get(key)

    if isinstance(value, str):
        return value

    return default


def build_candidate_diagnostic_lines(
    candidate_diagnostics: Mapping[str, Any] | None,
) -> list[str]:
    if candidate_diagnostics is None:
        return []

    edge_pixels = get_diagnostic_count(
        candidate_diagnostics,
        "edgePixelCount",
    )

    primary_minimum = get_diagnostic_count(
        candidate_diagnostics,
        "primaryMinimumLineLengthPixels",
    )
    primary_raw = get_diagnostic_count(
        candidate_diagnostics,
        "primaryRawHoughLineCount",
    )

    fallback_minimum = get_diagnostic_count(
        candidate_diagnostics,
        "fallbackMinimumLineLengthPixels",
    )
    fallback_raw = get_diagnostic_count(
        candidate_diagnostics,
        "fallbackRawHoughLineCount",
    )

    accepted = get_diagnostic_count(
        candidate_diagnostics,
        "acceptedCandidateCount",
    )

    detection_pass_value = (
        candidate_diagnostics.get(
            "detectionPass",
            "none",
        )
    )

    detection_pass = (
        detection_pass_value
        if isinstance(
            detection_pass_value,
            str,
        )
        else "none"
    )

    fallback_attempted = (
        candidate_diagnostics.get(
            "fallbackAttempted",
            False,
        )
        is True
    )

    invalid = (
        get_diagnostic_count(
            candidate_diagnostics,
            "rejectedInvalidCoordinates",
        )
        + get_diagnostic_count(
            candidate_diagnostics,
            "rejectedInvalidFrameDimensions",
        )
    )

    too_short = get_diagnostic_count(
        candidate_diagnostics,
        "rejectedTooShort",
    )
    too_long = get_diagnostic_count(
        candidate_diagnostics,
        "rejectedTooLong",
    )
    too_far = get_diagnostic_count(
        candidate_diagnostics,
        "rejectedTooFarFromHands",
    )
    endpoint_far = get_diagnostic_count(
        candidate_diagnostics,
        "rejectedGripEndpointTooFar",
    )

    fallback_status = (
        "ran"
        if fallback_attempted
        else "skipped"
    )

    temporal_mode = get_diagnostic_text(
        candidate_diagnostics,
        "temporalSelectionMode",
        "not_attempted",
    )

    temporal_evaluated = get_diagnostic_count(
        candidate_diagnostics,
        "temporalCandidatesEvaluated",
    )

    temporal_rejected = get_diagnostic_count(
        candidate_diagnostics,
        "temporalCandidatesRejected",
    )

    selected_temporal_score = get_diagnostic_float(
        candidate_diagnostics,
        "selectedTemporalScore",
    )

    selected_angle_change = get_diagnostic_float(
        candidate_diagnostics,
        "selectedAngleChangeDegrees",
    )

    selected_distal_shift = get_diagnostic_float(
        candidate_diagnostics,
        "selectedDistalShiftRatio",
    )

    temporal_score_label = (
        f"{selected_temporal_score:.3f}"
        if selected_temporal_score is not None
        else "n/a"
    )

    angle_change_label = (
        f"{selected_angle_change:.1f}deg"
        if selected_angle_change is not None
        else "n/a"
    )

    distal_shift_label = (
        f"{selected_distal_shift:.3f}"
        if selected_distal_shift is not None
        else "n/a"
    )

    return [
        (
            f"edges {edge_pixels} | "
            f"pass {detection_pass} | "
            f"accepted {accepted}"
        ),
        (
            f"primary min {primary_minimum}px | "
            f"Hough {primary_raw}"
        ),
        (
            f"fallback {fallback_status} | "
            f"min {fallback_minimum}px | "
            f"Hough {fallback_raw}"
        ),
        (
            f"rejected invalid {invalid} | "
            f"short {too_short} | long {too_long} | "
            f"hands {too_far} | endpoint {endpoint_far}"
        ),
        (
            f"temporal {temporal_mode} | "
            f"evaluated {temporal_evaluated} | "
            f"rejected {temporal_rejected} | "
            f"score {temporal_score_label} | "
            f"angle {angle_change_label} | "
            f"distal {distal_shift_label}"
        ),
    ]


def draw_club_detection_visualization(
    frame: np.ndarray,
    *,
    phase_name: str,
    frame_index: int,
    hand_anchor: Mapping[str, Any] | None,
    shaft_line: Mapping[str, Any] | None,
    confidence: float,
    candidate_count: int,
    detected: bool,
    failure_reason: str | None,
    search_region: Mapping[str, Any] | None = None,
    candidate_diagnostics: Mapping[str, Any] | None = None,
) -> np.ndarray:
    if frame.size == 0:
        raise ValueError(
            "Cannot draw a visualization on an "
            "empty frame."
        )

    annotated_frame = frame.copy()

    if search_region is not None:
        corners = get_search_region_corners(
            search_region
        )

        if corners is not None:
            top_left, bottom_right = corners

            cv2.rectangle(
                annotated_frame,
                top_left,
                bottom_right,
                (255, 255, 0),
                thickness=(
                    SEARCH_REGION_THICKNESS
                ),
                lineType=cv2.LINE_AA,
            )

    if hand_anchor is not None:
        anchor_point = point_to_integer_tuple(
            hand_anchor
        )

        if anchor_point is not None:
            cv2.circle(
                annotated_frame,
                anchor_point,
                ANCHOR_RADIUS,
                (0, 255, 255),
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

            cv2.circle(
                annotated_frame,
                anchor_point,
                ANCHOR_RADIUS + 3,
                (0, 0, 0),
                thickness=2,
                lineType=cv2.LINE_AA,
            )

    if shaft_line is not None:
        start_value = shaft_line.get("start")
        end_value = shaft_line.get("end")

        if (
            isinstance(start_value, Mapping)
            and isinstance(end_value, Mapping)
        ):
            start_point = (
                point_to_integer_tuple(
                    start_value
                )
            )

            end_point = (
                point_to_integer_tuple(
                    end_value
                )
            )

            if (
                start_point is not None
                and end_point is not None
            ):
                cv2.line(
                    annotated_frame,
                    start_point,
                    end_point,
                    (0, 255, 0),
                    thickness=LINE_THICKNESS,
                    lineType=cv2.LINE_AA,
                )

                cv2.circle(
                    annotated_frame,
                    start_point,
                    5,
                    (255, 0, 255),
                    thickness=-1,
                    lineType=cv2.LINE_AA,
                )

                cv2.circle(
                    annotated_frame,
                    end_point,
                    5,
                    (255, 0, 255),
                    thickness=-1,
                    lineType=cv2.LINE_AA,
                )

    status_label = (
        "DETECTED"
        if detected
        else "NOT DETECTED"
    )

    draw_text_line(
        annotated_frame,
        (
            f"{phase_name} | "
            f"frame {frame_index}"
        ),
        line_number=0,
    )

    draw_text_line(
        annotated_frame,
        (
            f"{status_label} | "
            f"confidence {confidence:.3f} | "
            f"candidates {candidate_count}"
        ),
        line_number=1,
    )

    next_line_number = 2

    if failure_reason:
        draw_text_line(
            annotated_frame,
            failure_reason,
            line_number=next_line_number,
        )
        next_line_number += 1

    for diagnostic_line in (
        build_candidate_diagnostic_lines(
            candidate_diagnostics
        )
    ):
        draw_text_line(
            annotated_frame,
            diagnostic_line,
            line_number=next_line_number,
        )
        next_line_number += 1

    return annotated_frame


def save_club_detection_visualization(
    output_path: Path,
    image: np.ndarray,
) -> None:
    if image.size == 0:
        raise ValueError(
            "Cannot save an empty club detection "
            "visualization."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    success = cv2.imwrite(
        str(output_path),
        image,
    )

    if not success:
        raise OSError(
            "OpenCV was unable to write the club "
            f"detection visualization: {output_path}"
        )