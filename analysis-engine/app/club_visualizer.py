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
CANDIDATE_LINE_THICKNESS = 2
CANDIDATE_LABEL_SCALE = 0.45
CANDIDATE_LABEL_THICKNESS = 1

PRESENTATION_LINE_THICKNESS = 6
PRESENTATION_ENDPOINT_RADIUS = 8
PRESENTATION_TEXT_SCALE = 0.62
PRESENTATION_TEXT_THICKNESS = 1


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


def create_club_presentation_directory(
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
        / f"{stem}-club-presentation-frames"
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


def create_club_presentation_path(
    output_directory: Path,
    *,
    phase_name: str,
    frame_index: int,
) -> Path:
    return create_club_visualization_path(
        output_directory,
        phase_name=phase_name,
        frame_index=frame_index,
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

    candidate_evaluation_count = len(
        get_candidate_evaluations(
            candidate_diagnostics
        )
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
        (
            f"candidate records {candidate_evaluation_count} | "
            "green selected | orange accepted | red rejected"
        ),
    ]


def get_candidate_evaluations(
    candidate_diagnostics: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    if candidate_diagnostics is None:
        return []

    value = candidate_diagnostics.get(
        "candidateEvaluations"
    )

    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, Mapping)
    ]


def draw_candidate_evaluations(
    image: np.ndarray,
    candidate_diagnostics: Mapping[str, Any] | None,
) -> None:
    """Draw every evaluated candidate without recomputing detector data."""

    for evaluation in get_candidate_evaluations(
        candidate_diagnostics
    ):
        line = evaluation.get("line")

        if not isinstance(line, Mapping):
            continue

        start_value = line.get("start")
        end_value = line.get("end")

        if not (
            isinstance(start_value, Mapping)
            and isinstance(end_value, Mapping)
        ):
            continue

        start_point = point_to_integer_tuple(
            start_value
        )
        end_point = point_to_integer_tuple(
            end_value
        )

        if (
            start_point is None
            or end_point is None
        ):
            continue

        selected = evaluation.get("selected") is True
        accepted = evaluation.get("accepted") is True

        if selected:
            line_color = (0, 255, 0)
            thickness = LINE_THICKNESS
        elif accepted:
            line_color = (0, 165, 255)
            thickness = CANDIDATE_LINE_THICKNESS
        else:
            line_color = (0, 0, 255)
            thickness = CANDIDATE_LINE_THICKNESS

        cv2.line(
            image,
            start_point,
            end_point,
            line_color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )

        index_value = evaluation.get("index")
        index_label = (
            str(index_value)
            if isinstance(index_value, int)
            else "?"
        )

        image_score = get_diagnostic_float(
            evaluation,
            "imageScore",
        )
        temporal_score = get_diagnostic_float(
            evaluation,
            "temporalScore",
        )

        score_value = (
            temporal_score
            if temporal_score is not None
            else image_score
        )

        score_label = (
            f" {score_value:.2f}"
            if score_value is not None
            else ""
        )

        label = f"C{index_label}{score_label}"
        midpoint = (
            int(round((start_point[0] + end_point[0]) / 2)),
            int(round((start_point[1] + end_point[1]) / 2)),
        )

        cv2.putText(
            image,
            label,
            midpoint,
            TEXT_FONT,
            CANDIDATE_LABEL_SCALE,
            line_color,
            CANDIDATE_LABEL_THICKNESS,
            cv2.LINE_AA,
        )


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

    candidate_evaluations = get_candidate_evaluations(
        candidate_diagnostics
    )

    draw_candidate_evaluations(
        annotated_frame,
        candidate_diagnostics,
    )

    if (
        shaft_line is not None
        and not candidate_evaluations
    ):
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



def draw_presentation_label(
    image: np.ndarray,
    text: str,
    *,
    origin: tuple[int, int],
) -> None:
    text_size, baseline = cv2.getTextSize(
        text,
        TEXT_FONT,
        PRESENTATION_TEXT_SCALE,
        PRESENTATION_TEXT_THICKNESS,
    )

    text_width, text_height = text_size
    x, y = origin

    cv2.rectangle(
        image,
        (
            x - 8,
            y - text_height - 8,
        ),
        (
            x + text_width + 8,
            y + baseline + 8,
        ),
        (16, 20, 24),
        thickness=-1,
    )

    cv2.putText(
        image,
        text,
        (x, y),
        TEXT_FONT,
        PRESENTATION_TEXT_SCALE,
        (255, 255, 255),
        PRESENTATION_TEXT_THICKNESS,
        cv2.LINE_AA,
    )


def order_shaft_endpoints(
    shaft_line: Mapping[str, Any],
    hand_anchor: Mapping[str, Any] | None,
) -> tuple[
    tuple[int, int],
    tuple[int, int],
] | None:
    start_value = shaft_line.get("start")
    end_value = shaft_line.get("end")

    if not (
        isinstance(start_value, Mapping)
        and isinstance(end_value, Mapping)
    ):
        return None

    start_point = point_to_integer_tuple(
        start_value
    )
    end_point = point_to_integer_tuple(
        end_value
    )

    if (
        start_point is None
        or end_point is None
    ):
        return None

    if hand_anchor is None:
        return start_point, end_point

    anchor_point = point_to_integer_tuple(
        hand_anchor
    )

    if anchor_point is None:
        return start_point, end_point

    start_distance = (
        (start_point[0] - anchor_point[0]) ** 2
        + (start_point[1] - anchor_point[1]) ** 2
    )
    end_distance = (
        (end_point[0] - anchor_point[0]) ** 2
        + (end_point[1] - anchor_point[1]) ** 2
    )

    if start_distance <= end_distance:
        return start_point, end_point

    return end_point, start_point


def draw_club_presentation_visualization(
    frame: np.ndarray,
    *,
    phase_name: str,
    frame_index: int,
    hand_anchor: Mapping[str, Any] | None,
    shaft_line: Mapping[str, Any],
    confidence: float,
    geometry_source: str,
    detection_source: str,
) -> np.ndarray:
    """
    Draw a clean customer-facing club visualization.

    Unlike the diagnostic visualization, this view includes only the
    selected shaft geometry, endpoint markers, and concise provenance.
    """

    if frame.size == 0:
        raise ValueError(
            "Cannot draw a presentation visualization "
            "on an empty frame."
        )

    endpoints = order_shaft_endpoints(
        shaft_line,
        hand_anchor,
    )

    if endpoints is None:
        raise ValueError(
            "Presentation shaft geometry is invalid."
        )

    grip_point, clubhead_point = endpoints
    annotated_frame = frame.copy()

    cv2.line(
        annotated_frame,
        grip_point,
        clubhead_point,
        (255, 218, 104),
        thickness=PRESENTATION_LINE_THICKNESS,
        lineType=cv2.LINE_AA,
    )

    cv2.circle(
        annotated_frame,
        grip_point,
        PRESENTATION_ENDPOINT_RADIUS,
        (99, 255, 156),
        thickness=-1,
        lineType=cv2.LINE_AA,
    )

    cv2.circle(
        annotated_frame,
        clubhead_point,
        PRESENTATION_ENDPOINT_RADIUS,
        (255, 255, 255),
        thickness=-1,
        lineType=cv2.LINE_AA,
    )

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