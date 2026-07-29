from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

from app.club_detector import (
    analyze_club_detection,
)
from app.geometry import (
    analyze_geometry,
    create_geometry_output_path,
    load_pose_timeline as load_geometry_pose_timeline,
    save_geometry_analysis,
)
from app.golf_metrics import analyze_golf_metrics
from app.golf_phase_refiner import (
    create_output_path as create_refined_phases_output_path,
    load_json,
    refine_golf_phases,
)
from app.phase_detector import (
    analyze_motion_signal,
    create_motion_output_path,
    load_pose_timeline as load_motion_pose_timeline,
    save_motion_analysis,
)
from app.pose_detector import analyze_video_pose


Handedness = Literal["right", "left"]


def write_json(
    output_path: Path,
    payload: dict[str, Any],
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


def run_analysis_pipeline(
    video_path: Path,
    *,
    handedness: Handedness = "right",
    report_output_path: Path | None = None,
) -> dict[str, Any]:
    resolved_video_path = (
        video_path
        .expanduser()
        .resolve()
    )

    if not resolved_video_path.is_file():
        raise FileNotFoundError(
            f"Video file not found: {resolved_video_path}"
        )

    pose_result = analyze_video_pose(
        resolved_video_path
    )

    pose_timeline_path = Path(
        pose_result["timelinePath"]
    ).resolve()

    (
        source_video,
        metadata,
        orientation,
        geometry_frames,
    ) = load_geometry_pose_timeline(
        pose_timeline_path
    )

    geometry_analysis = analyze_geometry(
        source_video=source_video,
        metadata=metadata,
        orientation=orientation,
        frames=geometry_frames,
    )

    geometry_analysis_path = (
        create_geometry_output_path(
            pose_timeline_path
        )
    )

    save_geometry_analysis(
        geometry_analysis_path,
        geometry_analysis,
    )

    (
        motion_frames,
        active_pose_window,
    ) = load_motion_pose_timeline(
        pose_timeline_path
    )

    motion_analysis = analyze_motion_signal(
        motion_frames,
        active_pose_window,
    )

    motion_analysis_path = (
        create_motion_output_path(
            pose_timeline_path
        )
    )

    save_motion_analysis(
        motion_analysis_path,
        motion_analysis,
    )

    pose_payload = load_json(
        pose_timeline_path
    )

    motion_payload = load_json(
        motion_analysis_path
    )

    refined_phases = refine_golf_phases(
        pose_payload,
        motion_payload,
    )

    refined_phases_path = (
        create_refined_phases_output_path(
            motion_analysis_path
        )
    )

    write_json(
        refined_phases_path,
        refined_phases,
    )

    club_detection_result = (
        analyze_club_detection(
            video_path=resolved_video_path,
            pose_timeline_path=(
                pose_timeline_path
            ),
            refined_phases_path=(
                refined_phases_path
            ),
        )
    )

    club_detection_path_value = (
        club_detection_result.get(
            "clubDetectionPath"
        )
    )

    if not isinstance(
        club_detection_path_value,
        str,
    ):
        raise RuntimeError(
            "Club detection did not return "
            "an artifact output path."
        )

    club_detection_path = Path(
        club_detection_path_value
    ).resolve()

    club_visualization_directory_value = (
        club_detection_result.get(
            "clubVisualizationDirectory"
        )
    )

    if not isinstance(
        club_visualization_directory_value,
        str,
    ):
        raise RuntimeError(
            "Club detection did not return "
            "a visualization directory."
        )

    club_visualization_directory = Path(
        club_visualization_directory_value
    ).resolve()

    club_detection_payload = (
        club_detection_result.get(
            "clubDetection"
        )
    )

    if not isinstance(
        club_detection_payload,
        dict,
    ):
        raise RuntimeError(
            "Club detection did not return "
            "a result payload."
        )

    metrics_result = analyze_golf_metrics(
        geometry_path=geometry_analysis_path,
        refined_phases_path=refined_phases_path,
        output_path=report_output_path,
        handedness=handedness,
    )

    golf_metrics_path_value = metrics_result.get(
        "golfMetricsPath"
    )

    if not isinstance(
        golf_metrics_path_value,
        str,
    ):
        raise RuntimeError(
            "Golf metrics analysis did not return "
            "a report output path."
        )

    golf_metrics_path = Path(
        golf_metrics_path_value
    ).resolve()

    final_report = load_json(
        golf_metrics_path
    )

    return {
        "success": True,
        "videoPath": str(
            resolved_video_path
        ),
        "handedness": handedness,
        "artifacts": {
            "poseTimelinePath": str(
                pose_timeline_path
            ),
            "motionAnalysisPath": str(
                motion_analysis_path
            ),
            "geometryAnalysisPath": str(
                geometry_analysis_path
            ),
            "refinedPhasesPath": str(
                refined_phases_path
            ),
            "clubDetectionPath": str(
                club_detection_path
            ),
            "clubVisualizationDirectory": str(
                club_visualization_directory
            ),
            "golfMetricsPath": str(
                golf_metrics_path
            ),
        },
        "stageSummaries": {
            "poseDetection": pose_result[
                "poseDetection"
            ],
            "activePoseWindow": pose_result[
                "activePoseWindow"
            ],
            "motion": motion_analysis[
                "summary"
            ],
            "geometry": geometry_analysis[
                "summary"
            ],
            "refinedPhases": refined_phases[
                "summary"
            ],
            "clubDetection": (
                club_detection_payload[
                    "summary"
                ]
            ),
        },
        "report": final_report,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete TempoAI golf swing "
            "analysis pipeline for one video."
        )
    )

    parser.add_argument(
        "video_path",
        type=Path,
        help="Path to the uploaded golf swing video.",
    )

    parser.add_argument(
        "--handedness",
        choices=("right", "left"),
        default="right",
        help=(
            "Golfer handedness used by metrics that "
            "distinguish the lead and trail sides. "
            "Defaults to right."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Optional final report path. By default, "
            "the golf metrics report is written beside "
            "the other generated analysis files."
        ),
    )

    return parser


def print_result(
    payload: dict[str, Any],
) -> None:
    print(
        json.dumps(
            payload,
            separators=(",", ":"),
        )
    )


def main() -> None:
    parser = build_parser()
    arguments = parser.parse_args()

    report_output_path = (
        arguments.output
        .expanduser()
        .resolve()
        if arguments.output is not None
        else None
    )

    try:
        result = run_analysis_pipeline(
            video_path=arguments.video_path,
            handedness=arguments.handedness,
            report_output_path=(
                report_output_path
            ),
        )
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        print_result(
            {
                "success": False,
                "error": str(error),
            }
        )

        raise SystemExit(1) from error

    print_result(result)


if __name__ == "__main__":
    main()