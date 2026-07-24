from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Literal


Handedness = Literal["right", "left"]

REFERENCE_NAMES = (
    "addressReference",
    "topOfBackswing",
    "downswingStart",
    "impactReference",
    "finishReference",
)

CENTER_NAMES = (
    "headCenter",
    "shoulderCenter",
    "hipCenter",
)

ANGLE_NAMES = (
    "spineAngle",
    "shoulderTilt",
    "hipTilt",
    "leftElbowAngle",
    "rightElbowAngle",
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {path}: {error}") from error


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def round_value(
    value: float | None,
    digits: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, digits)


def get_rotated_dimensions(
    metadata: dict[str, Any],
    orientation: dict[str, Any],
) -> tuple[float, float]:
    width = float(metadata["width"])
    height = float(metadata["height"])

    selected_rotation = orientation.get(
        "selectedRotation",
        "none",
    )

    if selected_rotation in {
        "clockwise90",
        "counterclockwise90",
    }:
        return height, width

    return width, height


def create_frame_lookup(
    geometry_data: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    frames = geometry_data.get("frames")

    if not isinstance(frames, list):
        raise ValueError(
            "Geometry analysis must contain a frames array."
        )

    lookup: dict[int, dict[str, Any]] = {}

    for frame in frames:
        frame_index = frame.get("frameIndex")

        if isinstance(frame_index, int):
            lookup[frame_index] = frame

    return lookup


def get_reference_frame_indices(
    refined_phases_data: dict[str, Any],
) -> dict[str, int]:
    phases = refined_phases_data.get("phases")

    if not isinstance(phases, dict):
        raise ValueError(
            "Refined phase analysis is missing phases."
        )

    phase_mapping = {
        "addressReference": "address",
        "topOfBackswing": "topOfBackswing",
        "downswingStart": "downswingStart",
        "impactReference": "impactReference",
        "finishReference": "finishReference",
    }

    reference_indices: dict[str, int] = {}

    for reference_name, phase_name in phase_mapping.items():
        phase = phases.get(phase_name)

        if not isinstance(phase, dict):
            raise ValueError(
                "Refined phase analysis is missing "
                f"{phase_name}."
            )

        frame_index = phase.get("frameIndex")

        if not isinstance(frame_index, int):
            raise ValueError(
                f"Refined phase {phase_name} is missing "
                "a valid frameIndex."
            )

        reference_indices[reference_name] = frame_index

    frame_indices = list(reference_indices.values())

    if frame_indices != sorted(frame_indices):
        raise ValueError(
            "Refined golf phases are not chronological."
        )

    return reference_indices


def extract_reference_frames(
    reference_indices: dict[str, int],
    frame_lookup: dict[int, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    references: dict[str, dict[str, Any]] = {}

    for reference_name, frame_index in reference_indices.items():
        frame = frame_lookup.get(frame_index)

        if frame is None:
            raise ValueError(
                f"Geometry frame {frame_index} was not found "
                f"for {reference_name}."
            )

        geometry = frame.get("geometry")

        if not isinstance(geometry, dict):
            raise ValueError(
                f"Geometry is missing for frame {frame_index}."
            )

        references[reference_name] = {
            "frameIndex": frame_index,
            "timestampSeconds": frame.get(
                "timestampSeconds"
            ),
            "poseDetected": frame.get("poseDetected"),
            "geometry": geometry,
        }

    return references


def normalized_point_delta(
    start_point: dict[str, Any] | None,
    end_point: dict[str, Any] | None,
    frame_width: float,
    frame_height: float,
) -> dict[str, float | None]:
    if start_point is None or end_point is None:
        return {
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    start_x = start_point.get("x")
    start_y = start_point.get("y")
    end_x = end_point.get("x")
    end_y = end_point.get("y")

    values = (
        start_x,
        start_y,
        end_x,
        end_y,
    )

    if not all(
        isinstance(value, (int, float))
        for value in values
    ):
        return {
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    delta_x_normalized = float(end_x) - float(start_x)
    delta_y_normalized = float(end_y) - float(start_y)

    distance_normalized = math.hypot(
        delta_x_normalized,
        delta_y_normalized,
    )

    delta_x_pixels = delta_x_normalized * frame_width
    delta_y_pixels = delta_y_normalized * frame_height

    distance_pixels = math.hypot(
        delta_x_pixels,
        delta_y_pixels,
    )

    return {
        "deltaXNormalized": round_value(
            delta_x_normalized
        ),
        "deltaYNormalized": round_value(
            delta_y_normalized
        ),
        "distanceNormalized": round_value(
            distance_normalized
        ),
        "deltaXPixels": round_value(delta_x_pixels),
        "deltaYPixels": round_value(delta_y_pixels),
        "distancePixels": round_value(distance_pixels),
    }


def angle_delta(
    start_angle: Any,
    end_angle: Any,
) -> float | None:
    if not isinstance(start_angle, (int, float)):
        return None

    if not isinstance(end_angle, (int, float)):
        return None

    return round_value(
        float(end_angle) - float(start_angle)
    )

def axial_angle_delta(
    start_angle: Any,
    end_angle: Any,
) -> float | None:
    """
    Calculate the shortest signed change between two undirected
    line angles.

    Shoulder and hip tilt represent axes rather than directional
    vectors, so angles separated by 180 degrees describe the same
    physical line.

    The returned change is normalized to -90 through 90 degrees.
    """

    if not isinstance(start_angle, (int, float)):
        return None

    if not isinstance(end_angle, (int, float)):
        return None

    difference = float(end_angle) - float(start_angle)

    while difference > 90.0:
        difference -= 180.0

    while difference < -90.0:
        difference += 180.0

    return round_value(difference)

def build_transition_metrics(
    start_reference: dict[str, Any],
    end_reference: dict[str, Any],
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    start_geometry = start_reference["geometry"]
    end_geometry = end_reference["geometry"]

    center_movements: dict[str, Any] = {}

    for center_name in CENTER_NAMES:
        center_movements[center_name] = normalized_point_delta(
            start_geometry.get(center_name),
            end_geometry.get(center_name),
            frame_width,
            frame_height,
        )

    angle_changes: dict[str, float | None] = {}

    for angle_name in ANGLE_NAMES:
        start_angle = start_geometry.get(angle_name)
        end_angle = end_geometry.get(angle_name)

        if angle_name in {
            "shoulderTilt",
            "hipTilt",
        }:
            angle_changes[angle_name] = axial_angle_delta(
                start_angle,
                end_angle,
            )
        else:
            angle_changes[angle_name] = angle_delta(
                start_angle,
                end_angle,
            )

    return {
        "fromFrame": start_reference["frameIndex"],
        "toFrame": end_reference["frameIndex"],
        "durationSeconds": round_value(
            float(end_reference["timestampSeconds"])
            - float(start_reference["timestampSeconds"])
        ),
        "centerMovement": center_movements,
        "angleChangesDegrees": angle_changes,
    }


def get_arm_mapping(
    handedness: Handedness,
) -> dict[str, str]:
    if handedness == "right":
        return {
            "leadArm": "leftElbowAngle",
            "trailArm": "rightElbowAngle",
        }

    return {
        "leadArm": "rightElbowAngle",
        "trailArm": "leftElbowAngle",
    }


def build_arm_metrics(
    references: dict[str, dict[str, Any]],
    handedness: Handedness,
) -> dict[str, Any]:
    mapping = get_arm_mapping(handedness)

    arm_metrics: dict[str, Any] = {
        "handednessAssumption": handedness,
        "mapping": mapping,
    }

    for arm_name, geometry_key in mapping.items():
        values: dict[str, float | None] = {}

        for reference_name in REFERENCE_NAMES:
            geometry = references[reference_name]["geometry"]
            value = geometry.get(geometry_key)

            values[reference_name] = (
                round_value(float(value))
                if isinstance(value, (int, float))
                else None
            )

        arm_metrics[arm_name] = {
            "measurement": geometry_key,
            "anglesDegrees": values,
            "addressToTopChange": angle_delta(
                values["addressReference"],
                values["topOfBackswing"],
            ),
            "addressToImpactChange": angle_delta(
                values["addressReference"],
                values["impactReference"],
            ),
            "topToImpactChange": angle_delta(
                values["topOfBackswing"],
                values["impactReference"],
            ),
        }

    return arm_metrics


def calculate_maximum_center_movement(
    frames: list[dict[str, Any]],
    reference_geometry: dict[str, Any],
    center_name: str,
    frame_width: float,
    frame_height: float,
) -> dict[str, Any]:
    reference_point = reference_geometry.get(center_name)

    maximum_distance = -1.0
    maximum_result: dict[str, Any] | None = None

    for frame in frames:
        if not frame.get("poseDetected"):
            continue

        geometry = frame.get("geometry")

        if not isinstance(geometry, dict):
            continue

        current_point = geometry.get(center_name)

        movement = normalized_point_delta(
            reference_point,
            current_point,
            frame_width,
            frame_height,
        )

        distance_pixels = movement["distancePixels"]

        if not isinstance(distance_pixels, (int, float)):
            continue

        if distance_pixels > maximum_distance:
            maximum_distance = float(distance_pixels)

            maximum_result = {
                "frameIndex": frame.get("frameIndex"),
                "timestampSeconds": frame.get(
                    "timestampSeconds"
                ),
                **movement,
            }

    if maximum_result is None:
        return {
            "frameIndex": None,
            "timestampSeconds": None,
            "deltaXNormalized": None,
            "deltaYNormalized": None,
            "distanceNormalized": None,
            "deltaXPixels": None,
            "deltaYPixels": None,
            "distancePixels": None,
        }

    return maximum_result


def calculate_angle_ranges(
    frames: list[dict[str, Any]],
) -> dict[str, Any]:
    ranges: dict[str, Any] = {}

    for angle_name in ANGLE_NAMES:
        values: list[tuple[int, float, float | None]] = []

        for frame in frames:
            geometry = frame.get("geometry")

            if not isinstance(geometry, dict):
                continue

            value = geometry.get(angle_name)

            if not isinstance(value, (int, float)):
                continue

            values.append(
                (
                    int(frame["frameIndex"]),
                    float(value),
                    frame.get("timestampSeconds"),
                )
            )

        if not values:
            ranges[angle_name] = {
                "minimum": None,
                "minimumFrame": None,
                "maximum": None,
                "maximumFrame": None,
                "range": None,
            }
            continue

        minimum = min(values, key=lambda item: item[1])
        maximum = max(values, key=lambda item: item[1])

        ranges[angle_name] = {
            "minimum": round_value(minimum[1]),
            "minimumFrame": minimum[0],
            "minimumTimeSeconds": minimum[2],
            "maximum": round_value(maximum[1]),
            "maximumFrame": maximum[0],
            "maximumTimeSeconds": maximum[2],
            "range": round_value(
                maximum[1] - minimum[1]
            ),
        }

    return ranges


def count_available_reference_measurements(
    references: dict[str, dict[str, Any]],
) -> tuple[int, int]:
    available = 0
    total = 0

    for reference in references.values():
        geometry = reference["geometry"]

        for center_name in CENTER_NAMES:
            total += 1

            if geometry.get(center_name) is not None:
                available += 1

        for angle_name in ANGLE_NAMES:
            total += 1

            if geometry.get(angle_name) is not None:
                available += 1

    return available, total


def derive_output_path(
    geometry_path: Path,
) -> Path:
    filename = geometry_path.name

    suffix = "-geometry-analysis.json"

    if filename.endswith(suffix):
        prefix = filename[: -len(suffix)]
        output_name = f"{prefix}-golf-metrics.json"
    else:
        output_name = (
            f"{geometry_path.stem}-golf-metrics.json"
        )

    return geometry_path.with_name(output_name)


def analyze_golf_metrics(
    geometry_path: Path,
    refined_phases_path: Path,
    output_path: Path | None = None,
    handedness: Handedness = "right",
) -> dict[str, Any]:
    geometry_data = load_json(geometry_path)
    refined_phases_data = load_json(refined_phases_path)

    metadata = geometry_data.get("metadata")
    orientation = geometry_data.get("orientation")

    if not isinstance(metadata, dict):
        raise ValueError(
            "Geometry analysis is missing metadata."
        )

    if not isinstance(orientation, dict):
        raise ValueError(
            "Geometry analysis is missing orientation."
        )

    frame_width, frame_height = get_rotated_dimensions(
        metadata,
        orientation,
    )

    frame_lookup = create_frame_lookup(geometry_data)

    reference_indices = get_reference_frame_indices(
        refined_phases_data
    )

    references = extract_reference_frames(
        reference_indices,
        frame_lookup,
    )

    address_reference = references["addressReference"]

    transitions = {
        "addressToTop": build_transition_metrics(
            address_reference,
            references["topOfBackswing"],
            frame_width,
            frame_height,
        ),
        "addressToDownswingStart": (
            build_transition_metrics(
                address_reference,
                references["downswingStart"],
                frame_width,
                frame_height,
            )
        ),
        "addressToImpact": build_transition_metrics(
            address_reference,
            references["impactReference"],
            frame_width,
            frame_height,
        ),
        "addressToFinish": build_transition_metrics(
            address_reference,
            references["finishReference"],
            frame_width,
            frame_height,
        ),
        "topToImpact": build_transition_metrics(
            references["topOfBackswing"],
            references["impactReference"],
            frame_width,
            frame_height,
        ),
    }

    frames = geometry_data["frames"]

    maximum_center_movements = {
        center_name: calculate_maximum_center_movement(
            frames,
            address_reference["geometry"],
            center_name,
            frame_width,
            frame_height,
        )
        for center_name in CENTER_NAMES
    }

    available_measurements, total_measurements = (
        count_available_reference_measurements(
            references
        )
    )

    result = {
        "sourceVideo": geometry_data.get("sourceVideo"),
        "inputs": {
            "geometryAnalysisPath": str(
                geometry_path.resolve()
            ),
            "refinedPhasesPath": str(
                refined_phases_path.resolve()
            ),
        },
        "coordinateSystem": {
            "space": (
                "normalized-landmarks-and-rotated-video-pixels"
            ),
            "rotatedFrameWidth": frame_width,
            "rotatedFrameHeight": frame_height,
            "positiveXDirection": "image-right",
            "positiveYDirection": "image-down",
            "angleUnits": "degrees",
        },
        "assumptions": {
            "handedness": handedness,
            "phaseReferences": (
                "Reference frames come from the golf-specific "
                "refined phase analysis."
            ),
            "addressReference": (
                "Golf address frame selected from a sustained, "
                "plausible setup posture."
            ),
            "impactReference": (
                "Peak-motion impact reference from the refined "
                "golf phase analysis."
            ),
            "finishReference": (
                "Movement-end finish reference from the refined "
                "golf phase analysis. Finish posture validation "
                "is not yet implemented."
            ),
            "rotationMeasurements": (
                "Shoulder and hip tilt are 2D image-plane "
                "measurements, not true 3D body rotation."
            ),
        },
        "phaseFrames": {
            reference_name: {
                "frameIndex": reference["frameIndex"],
                "timestampSeconds": reference[
                    "timestampSeconds"
                ],
                "poseDetected": reference["poseDetected"],
            }
            for reference_name, reference in references.items()
        },
        "referenceGeometry": {
            reference_name: reference["geometry"]
            for reference_name, reference in references.items()
        },
        "metrics": {
            "transitions": transitions,
            "maximumMovementFromAddressReference": (
                maximum_center_movements
            ),
            "angleRanges": calculate_angle_ranges(frames),
            "armExtension": build_arm_metrics(
                references,
                handedness,
            ),
        },
        "summary": {
            "referenceFrameCount": len(references),
            "availableReferenceMeasurements": (
                available_measurements
            ),
            "totalReferenceMeasurements": (
                total_measurements
            ),
            "referenceMeasurementCompleteness": (
                round_value(
                    available_measurements
                    / total_measurements
                )
                if total_measurements > 0
                else None
            ),
            "allReferenceFramesHavePose": all(
                bool(reference["poseDetected"])
                for reference in references.values()
            ),
            "handednessAssumption": handedness,
        },
    }

    resolved_output_path = (
        output_path
        if output_path is not None
        else derive_output_path(geometry_path)
    )

    write_json(resolved_output_path, result)

    return {
        "success": True,
        "summary": result["summary"],
        "phaseFrames": result["phaseFrames"],
        "golfMetricsPath": str(
            resolved_output_path.resolve()
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate golf-specific metrics from geometry "
            "and refined golf phase analysis files."
        )
    )

    parser.add_argument(
        "geometry_path",
        type=Path,
        help="Path to the geometry-analysis JSON file.",
    )

    parser.add_argument(
        "refined_phases_path",
        type=Path,
        help="Path to the refined-phases JSON file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional output path. By default, the output "
            "is written beside the geometry-analysis file."
        ),
    )

    parser.add_argument(
        "--handedness",
        choices=("right", "left"),
        default="right",
        help=(
            "Golfer handedness used to identify lead and "
            "trail arms. Defaults to right."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        result = analyze_golf_metrics(
            geometry_path=args.geometry_path,
            refined_phases_path=args.refined_phases_path,
            output_path=args.output,
            handedness=args.handedness,
        )

        print(json.dumps(result))
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(error),
                }
            )
        )

        raise SystemExit(1) from error


if __name__ == "__main__":
    main()