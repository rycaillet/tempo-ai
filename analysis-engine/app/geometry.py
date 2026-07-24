from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import mean
from typing import Any, Mapping, Sequence, TypedDict


NOSE = 0
LEFT_EYE = 2
RIGHT_EYE = 5
LEFT_EAR = 7
RIGHT_EAR = 8

LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16

LEFT_HIP = 23
RIGHT_HIP = 24

MINIMUM_VISIBILITY = 0.35


class VideoMetadata(TypedDict):
    frameCount: int
    fps: float
    durationSeconds: float
    width: int
    height: int


class OrientationResult(TypedDict):
    selectedRotation: str
    candidates: list[dict[str, object]]


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


class GeometryPoint(TypedDict):
    x: float
    y: float
    z: float | None
    visibility: float | None


class FrameGeometry(TypedDict):
    headCenter: GeometryPoint | None
    shoulderCenter: GeometryPoint | None
    hipCenter: GeometryPoint | None
    leftWrist: GeometryPoint | None
    rightWrist: GeometryPoint | None
    shoulderWidth: float | None
    hipWidth: float | None
    torsoLength: float | None
    spineAngle: float | None
    shoulderTilt: float | None
    hipTilt: float | None
    leftElbowAngle: float | None
    rightElbowAngle: float | None


class GeometryFrame(TypedDict):
    frameIndex: int
    timestampMs: int
    timestampSeconds: float
    poseDetected: bool
    geometry: FrameGeometry


class GeometrySummary(TypedDict):
    processedFrames: int
    framesWithPose: int
    framesWithGeometry: int
    missingGeometryFrames: int
    minimumVisibility: float
    measurementCoordinateSpace: str
    angleUnits: str


class GeometryAnalysis(TypedDict):
    sourceVideo: str
    metadata: VideoMetadata
    orientation: OrientationResult
    summary: GeometrySummary
    frames: list[GeometryFrame]


def round_optional(
    value: float | None,
    decimal_places: int = 6,
) -> float | None:
    if value is None:
        return None

    return round(value, decimal_places)


def create_point(
    x: float,
    y: float,
    z: float | None,
    visibility: float | None,
) -> GeometryPoint:
    return {
        "x": round(x, 6),
        "y": round(y, 6),
        "z": round_optional(z),
        "visibility": round_optional(visibility),
    }


def get_landmark_map(
    frame: PoseFrame,
) -> dict[int, LandmarkData]:
    return {
        landmark["index"]: landmark
        for landmark in frame["landmarks"]
    }


def get_visible_landmark(
    landmarks: Mapping[int, LandmarkData],
    index: int,
    minimum_visibility: float,
) -> LandmarkData | None:
    landmark = landmarks.get(index)

    if landmark is None:
        return None

    if landmark["visibility"] < minimum_visibility:
        return None

    return landmark


def landmark_to_point(
    landmark: LandmarkData | None,
) -> GeometryPoint | None:
    if landmark is None:
        return None

    return create_point(
        x=landmark["x"],
        y=landmark["y"],
        z=landmark["z"],
        visibility=landmark["visibility"],
    )


def calculate_midpoint(
    first: LandmarkData | GeometryPoint | None,
    second: LandmarkData | GeometryPoint | None,
) -> GeometryPoint | None:
    if first is None or second is None:
        return None

    z_values = [
        float(value)
        for value in (
            first.get("z"),
            second.get("z"),
        )
        if value is not None
    ]

    visibility_values = [
        float(value)
        for value in (
            first.get("visibility"),
            second.get("visibility"),
        )
        if value is not None
    ]

    return create_point(
        x=(float(first["x"]) + float(second["x"])) / 2.0,
        y=(float(first["y"]) + float(second["y"])) / 2.0,
        z=mean(z_values) if z_values else None,
        visibility=(
            min(visibility_values)
            if visibility_values
            else None
        ),
    )


def calculate_head_center(
    landmarks: Mapping[int, LandmarkData],
    minimum_visibility: float,
) -> GeometryPoint | None:
    left_ear = get_visible_landmark(
        landmarks,
        LEFT_EAR,
        minimum_visibility,
    )
    right_ear = get_visible_landmark(
        landmarks,
        RIGHT_EAR,
        minimum_visibility,
    )

    ear_center = calculate_midpoint(
        left_ear,
        right_ear,
    )

    if ear_center is not None:
        return ear_center

    left_eye = get_visible_landmark(
        landmarks,
        LEFT_EYE,
        minimum_visibility,
    )
    right_eye = get_visible_landmark(
        landmarks,
        RIGHT_EYE,
        minimum_visibility,
    )

    eye_center = calculate_midpoint(
        left_eye,
        right_eye,
    )

    if eye_center is not None:
        return eye_center

    nose = get_visible_landmark(
        landmarks,
        NOSE,
        minimum_visibility,
    )

    return landmark_to_point(nose)


def resolve_analysis_dimensions(
    metadata: VideoMetadata,
    orientation: OrientationResult,
) -> tuple[float, float]:
    width = float(metadata["width"])
    height = float(metadata["height"])

    selected_rotation = orientation["selectedRotation"]

    if selected_rotation in {
        "clockwise90",
        "counterclockwise90",
    }:
        return height, width

    return width, height


def to_pixel_coordinates(
    point: LandmarkData | GeometryPoint,
    frame_width: float,
    frame_height: float,
) -> tuple[float, float]:
    return (
        float(point["x"]) * frame_width,
        float(point["y"]) * frame_height,
    )


def calculate_distance(
    first: LandmarkData | GeometryPoint | None,
    second: LandmarkData | GeometryPoint | None,
    frame_width: float,
    frame_height: float,
) -> float | None:
    if first is None or second is None:
        return None

    first_x, first_y = to_pixel_coordinates(
        first,
        frame_width,
        frame_height,
    )
    second_x, second_y = to_pixel_coordinates(
        second,
        frame_width,
        frame_height,
    )

    return math.hypot(
        second_x - first_x,
        second_y - first_y,
    )


def calculate_line_tilt(
    left_point: LandmarkData | GeometryPoint | None,
    right_point: LandmarkData | GeometryPoint | None,
    frame_width: float,
    frame_height: float,
) -> float | None:
    """
    Return the body's signed line tilt relative to image horizontal.

    The result is normalized to the range -90 to 90 degrees,
    making it independent of whether the anatomical left landmark
    appears on the left or right side of the image.

    Positive:
        The line rises from left to right in image space.

    Negative:
        The line falls from left to right in image space.

    Zero:
        The line is horizontal.
    """

    if left_point is None or right_point is None:
        return None

    left_x, left_y = to_pixel_coordinates(
        left_point,
        frame_width,
        frame_height,
    )
    right_x, right_y = to_pixel_coordinates(
        right_point,
        frame_width,
        frame_height,
    )

    delta_x = right_x - left_x
    delta_y_up = left_y - right_y

    if (
        math.isclose(delta_x, 0.0)
        and math.isclose(delta_y_up, 0.0)
    ):
        return None

    angle = math.degrees(
        math.atan2(
            delta_y_up,
            delta_x,
        )
    )

    if angle > 90.0:
        angle -= 180.0
    elif angle < -90.0:
        angle += 180.0

    return angle


def calculate_spine_angle(
    shoulder_center: GeometryPoint | None,
    hip_center: GeometryPoint | None,
    frame_width: float,
    frame_height: float,
) -> float | None:
    """
    Return a signed angle relative to image vertical.

    Zero:
        Shoulder center is directly above hip center.

    Positive:
        Shoulder center is to the right of hip center.

    Negative:
        Shoulder center is to the left of hip center.
    """

    if shoulder_center is None or hip_center is None:
        return None

    shoulder_x, shoulder_y = to_pixel_coordinates(
        shoulder_center,
        frame_width,
        frame_height,
    )
    hip_x, hip_y = to_pixel_coordinates(
        hip_center,
        frame_width,
        frame_height,
    )

    delta_x = shoulder_x - hip_x
    delta_y_up = hip_y - shoulder_y

    if (
        math.isclose(delta_x, 0.0)
        and math.isclose(delta_y_up, 0.0)
    ):
        return None

    return math.degrees(
        math.atan2(
            delta_x,
            delta_y_up,
        )
    )


def calculate_joint_angle(
    first: LandmarkData | None,
    vertex: LandmarkData | None,
    third: LandmarkData | None,
    frame_width: float,
    frame_height: float,
) -> float | None:
    """
    Return the interior joint angle from 0 to 180 degrees.

    For an elbow:
        first = shoulder
        vertex = elbow
        third = wrist
    """

    if first is None or vertex is None or third is None:
        return None

    first_x, first_y = to_pixel_coordinates(
        first,
        frame_width,
        frame_height,
    )
    vertex_x, vertex_y = to_pixel_coordinates(
        vertex,
        frame_width,
        frame_height,
    )
    third_x, third_y = to_pixel_coordinates(
        third,
        frame_width,
        frame_height,
    )

    first_vector = (
        first_x - vertex_x,
        first_y - vertex_y,
    )
    third_vector = (
        third_x - vertex_x,
        third_y - vertex_y,
    )

    first_magnitude = math.hypot(
        first_vector[0],
        first_vector[1],
    )
    third_magnitude = math.hypot(
        third_vector[0],
        third_vector[1],
    )

    if (
        math.isclose(first_magnitude, 0.0)
        or math.isclose(third_magnitude, 0.0)
    ):
        return None

    dot_product = (
        first_vector[0] * third_vector[0]
        + first_vector[1] * third_vector[1]
    )

    cosine_angle = dot_product / (
        first_magnitude * third_magnitude
    )

    cosine_angle = max(
        -1.0,
        min(1.0, cosine_angle),
    )

    return math.degrees(
        math.acos(cosine_angle)
    )


def create_empty_geometry() -> FrameGeometry:
    return {
        "headCenter": None,
        "shoulderCenter": None,
        "hipCenter": None,
        "leftWrist": None,
        "rightWrist": None,
        "shoulderWidth": None,
        "hipWidth": None,
        "torsoLength": None,
        "spineAngle": None,
        "shoulderTilt": None,
        "hipTilt": None,
        "leftElbowAngle": None,
        "rightElbowAngle": None,
    }


def calculate_frame_geometry(
    frame: PoseFrame,
    frame_width: float,
    frame_height: float,
    minimum_visibility: float = MINIMUM_VISIBILITY,
) -> FrameGeometry:
    if not frame["poseDetected"] or not frame["landmarks"]:
        return create_empty_geometry()

    landmarks = get_landmark_map(frame)

    left_shoulder = get_visible_landmark(
        landmarks,
        LEFT_SHOULDER,
        minimum_visibility,
    )
    right_shoulder = get_visible_landmark(
        landmarks,
        RIGHT_SHOULDER,
        minimum_visibility,
    )
    left_elbow = get_visible_landmark(
        landmarks,
        LEFT_ELBOW,
        minimum_visibility,
    )
    right_elbow = get_visible_landmark(
        landmarks,
        RIGHT_ELBOW,
        minimum_visibility,
    )
    left_wrist = get_visible_landmark(
        landmarks,
        LEFT_WRIST,
        minimum_visibility,
    )
    right_wrist = get_visible_landmark(
        landmarks,
        RIGHT_WRIST,
        minimum_visibility,
    )
    left_hip = get_visible_landmark(
        landmarks,
        LEFT_HIP,
        minimum_visibility,
    )
    right_hip = get_visible_landmark(
        landmarks,
        RIGHT_HIP,
        minimum_visibility,
    )

    head_center = calculate_head_center(
        landmarks,
        minimum_visibility,
    )

    shoulder_center = calculate_midpoint(
        left_shoulder,
        right_shoulder,
    )
    hip_center = calculate_midpoint(
        left_hip,
        right_hip,
    )

    shoulder_width = calculate_distance(
        left_shoulder,
        right_shoulder,
        frame_width,
        frame_height,
    )
    hip_width = calculate_distance(
        left_hip,
        right_hip,
        frame_width,
        frame_height,
    )
    torso_length = calculate_distance(
        shoulder_center,
        hip_center,
        frame_width,
        frame_height,
    )

    spine_angle = calculate_spine_angle(
        shoulder_center,
        hip_center,
        frame_width,
        frame_height,
    )
    shoulder_tilt = calculate_line_tilt(
        left_shoulder,
        right_shoulder,
        frame_width,
        frame_height,
    )
    hip_tilt = calculate_line_tilt(
        left_hip,
        right_hip,
        frame_width,
        frame_height,
    )

    left_elbow_angle = calculate_joint_angle(
        left_shoulder,
        left_elbow,
        left_wrist,
        frame_width,
        frame_height,
    )
    right_elbow_angle = calculate_joint_angle(
        right_shoulder,
        right_elbow,
        right_wrist,
        frame_width,
        frame_height,
    )

    return {
        "headCenter": head_center,
        "shoulderCenter": shoulder_center,
        "hipCenter": hip_center,
        "leftWrist": landmark_to_point(left_wrist),
        "rightWrist": landmark_to_point(right_wrist),
        "shoulderWidth": round_optional(shoulder_width),
        "hipWidth": round_optional(hip_width),
        "torsoLength": round_optional(torso_length),
        "spineAngle": round_optional(spine_angle),
        "shoulderTilt": round_optional(shoulder_tilt),
        "hipTilt": round_optional(hip_tilt),
        "leftElbowAngle": round_optional(left_elbow_angle),
        "rightElbowAngle": round_optional(right_elbow_angle),
    }


def geometry_contains_measurements(
    geometry: FrameGeometry,
) -> bool:
    return any(
        value is not None
        for value in geometry.values()
    )


def analyze_geometry(
    source_video: str,
    metadata: VideoMetadata,
    orientation: OrientationResult,
    frames: list[PoseFrame],
    minimum_visibility: float = MINIMUM_VISIBILITY,
) -> GeometryAnalysis:
    frame_width, frame_height = (
        resolve_analysis_dimensions(
            metadata,
            orientation,
        )
    )

    geometry_frames: list[GeometryFrame] = []
    frames_with_pose = 0
    frames_with_geometry = 0

    for frame in frames:
        if frame["poseDetected"]:
            frames_with_pose += 1

        geometry = calculate_frame_geometry(
            frame=frame,
            frame_width=frame_width,
            frame_height=frame_height,
            minimum_visibility=minimum_visibility,
        )

        if geometry_contains_measurements(geometry):
            frames_with_geometry += 1

        geometry_frames.append(
            {
                "frameIndex": frame["frameIndex"],
                "timestampMs": frame["timestampMs"],
                "timestampSeconds": (
                    frame["timestampSeconds"]
                ),
                "poseDetected": frame["poseDetected"],
                "geometry": geometry,
            }
        )

    processed_frames = len(frames)

    summary: GeometrySummary = {
        "processedFrames": processed_frames,
        "framesWithPose": frames_with_pose,
        "framesWithGeometry": frames_with_geometry,
        "missingGeometryFrames": (
            processed_frames - frames_with_geometry
        ),
        "minimumVisibility": minimum_visibility,
        "measurementCoordinateSpace": "rotated-video-pixels",
        "angleUnits": "degrees",
    }

    return {
        "sourceVideo": source_video,
        "metadata": metadata,
        "orientation": orientation,
        "summary": summary,
        "frames": geometry_frames,
    }


def load_pose_timeline(
    timeline_path: Path,
) -> tuple[
    str,
    VideoMetadata,
    OrientationResult,
    list[PoseFrame],
]:
    try:
        payload = json.loads(
            timeline_path.read_text(
                encoding="utf-8",
            )
        )
    except OSError as error:
        raise ValueError(
            f"Unable to read pose timeline: {error}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            "Pose timeline contains invalid JSON: "
            f"{error}"
        ) from error

    source_video = payload.get("sourceVideo")
    metadata = payload.get("metadata")
    orientation = payload.get("orientation")
    frames = payload.get("frames")

    if not isinstance(source_video, str):
        raise ValueError(
            "Pose timeline does not contain sourceVideo."
        )

    if not isinstance(metadata, dict):
        raise ValueError(
            "Pose timeline does not contain metadata."
        )

    if not isinstance(orientation, dict):
        raise ValueError(
            "Pose timeline does not contain orientation."
        )

    if not isinstance(frames, list):
        raise ValueError(
            "Pose timeline does not contain a frames list."
        )

    required_metadata_fields = {
        "frameCount",
        "fps",
        "durationSeconds",
        "width",
        "height",
    }

    if not required_metadata_fields.issubset(metadata):
        raise ValueError(
            "Pose timeline metadata is incomplete."
        )

    selected_rotation = orientation.get(
        "selectedRotation"
    )

    if selected_rotation not in {
        "none",
        "clockwise90",
        "counterclockwise90",
        "rotate180",
    }:
        raise ValueError(
            "Pose timeline contains an unsupported "
            "selectedRotation value."
        )

    return (
        source_video,
        metadata,
        orientation,
        frames,
    )


def create_geometry_output_path(
    timeline_path: Path,
) -> Path:
    filename = timeline_path.name

    if filename.endswith(
        "-pose-timeline.json"
    ):
        filename = filename.replace(
            "-pose-timeline.json",
            "-geometry-analysis.json",
        )
    else:
        filename = (
            f"{timeline_path.stem}"
            "-geometry-analysis.json"
        )

    return timeline_path.parent / filename


def save_geometry_analysis(
    output_path: Path,
    analysis: GeometryAnalysis,
) -> None:
    try:
        output_path.write_text(
            json.dumps(
                analysis,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError as error:
        raise RuntimeError(
            "Unable to save geometry analysis: "
            f"{error}"
        ) from error


def print_result(
    payload: dict[str, object],
) -> None:
    print(json.dumps(payload))


def main() -> None:
    if len(sys.argv) != 2:
        print_result(
            {
                "success": False,
                "error": (
                    "Usage: python -m app.geometry "
                    "<pose-timeline-path>"
                ),
            }
        )
        raise SystemExit(1)

    timeline_path = (
        Path(sys.argv[1])
        .expanduser()
        .resolve()
    )

    if not timeline_path.is_file():
        print_result(
            {
                "success": False,
                "error": (
                    "Pose timeline file not found: "
                    f"{timeline_path}"
                ),
            }
        )
        raise SystemExit(1)

    try:
        (
            source_video,
            metadata,
            orientation,
            frames,
        ) = load_pose_timeline(timeline_path)

        analysis = analyze_geometry(
            source_video=source_video,
            metadata=metadata,
            orientation=orientation,
            frames=frames,
        )

        output_path = create_geometry_output_path(
            timeline_path
        )

        save_geometry_analysis(
            output_path,
            analysis,
        )
    except (ValueError, RuntimeError) as error:
        print_result(
            {
                "success": False,
                "error": str(error),
            }
        )
        raise SystemExit(1) from error

    print_result(
        {
            "success": True,
            "geometrySummary": analysis["summary"],
            "geometryAnalysisPath": str(
                output_path
            ),
        }
    )


if __name__ == "__main__":
    main()