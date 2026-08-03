from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.analysis.api_contract import (
    ANALYSIS_API_VERSION,
)
from app.pipeline import run_analysis_pipeline


class PipelineApiContractTests(
    unittest.TestCase
):
    def test_pipeline_returns_versioned_analysis_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video_path = root / "swing.mp4"
            video_path.write_bytes(b"video")

            pose_path = root / "swing-pose.json"
            motion_path = root / "swing-motion.json"
            geometry_path = root / "swing-geometry.json"
            phases_path = root / "swing-phases.json"
            club_path = root / "swing-club.json"
            report_path = root / "swing-report.json"
            visualizations = root / "club-frames"
            visualizations.mkdir()

            pose_path.write_text(
                json.dumps({"frames": []}),
                encoding="utf-8",
            )
            motion_path.write_text(
                json.dumps({"summary": {}}),
                encoding="utf-8",
            )
            club_path.write_text(
                json.dumps({"summary": {}}),
                encoding="utf-8",
            )

            report_payload = {
                "sourceVideo": "swing.mp4",
                "metrics": {},
                "scoring": {
                    "interpretation": {
                        "status": "not_available",
                    },
                },
                "findings": {
                    "status": "not_available",
                    "strengths": [],
                    "improvementPriorities": [],
                    "warnings": [],
                },
                "recommendations": {
                    "status": "not_available",
                    "primaryFocus": None,
                    "recommendations": [],
                    "warnings": [],
                },
                "summary": {
                    "analysisEngine": {
                        "name": (
                            "tempo-ai-analysis-engine"
                        ),
                        "version": "1.0.0",
                        "contractVersion": "1.0.0",
                        "coachingPromptVersion": (
                            "tempo-coach-v3"
                        ),
                        "metricVersions": {},
                    },
                    "clubAnalysisQuality": {
                        "status": "not_available",
                    },
                },
                "coaching": {
                    "status": "not_available",
                    "headline": None,
                },
            }

            report_path.write_text(
                json.dumps(report_payload),
                encoding="utf-8",
            )

            with (
                patch(
                    "app.pipeline.analyze_video_pose",
                    return_value={
                        "timelinePath": str(pose_path),
                        "poseDetection": {},
                        "activePoseWindow": {},
                    },
                ),
                patch(
                    "app.pipeline.load_geometry_pose_timeline",
                    return_value=(
                        "swing.mp4",
                        {"width": 1920, "height": 1080},
                        {"selectedRotation": "none"},
                        [],
                    ),
                ),
                patch(
                    "app.pipeline.analyze_geometry",
                    return_value={
                        "summary": {},
                    },
                ),
                patch(
                    "app.pipeline.create_geometry_output_path",
                    return_value=geometry_path,
                ),
                patch(
                    "app.pipeline.save_geometry_analysis",
                ),
                patch(
                    "app.pipeline.load_motion_pose_timeline",
                    return_value=([], {}),
                ),
                patch(
                    "app.pipeline.analyze_motion_signal",
                    return_value={
                        "summary": {},
                    },
                ),
                patch(
                    "app.pipeline.create_motion_output_path",
                    return_value=motion_path,
                ),
                patch(
                    "app.pipeline.save_motion_analysis",
                ),
                patch(
                    "app.pipeline.load_json",
                    side_effect=lambda path: json.loads(
                        Path(path).read_text(
                            encoding="utf-8"
                        )
                    ),
                ),
                patch(
                    "app.pipeline.refine_golf_phases",
                    return_value={
                        "summary": {},
                    },
                ),
                patch(
                    "app.pipeline.create_refined_phases_output_path",
                    return_value=phases_path,
                ),
                patch(
                    "app.pipeline.analyze_club_detection",
                    return_value={
                        "clubDetectionPath": str(club_path),
                        "clubVisualizationDirectory": (
                            str(visualizations)
                        ),
                        "clubDetection": {
                            "summary": {},
                        },
                    },
                ),
                patch(
                    "app.pipeline.analyze_golf_metrics",
                    return_value={
                        "golfMetricsPath": str(report_path),
                    },
                ),
            ):
                result = run_analysis_pipeline(
                    video_path,
                    handedness="right",
                )

            self.assertTrue(result["success"])
            self.assertEqual(
                result["apiVersion"],
                ANALYSIS_API_VERSION,
            )
            self.assertIn(
                "analysis",
                result,
            )
            self.assertEqual(
                result["analysis"][
                    "contractVersion"
                ],
                ANALYSIS_API_VERSION,
            )
            self.assertEqual(
                result["analysis"]["status"],
                "partial",
            )
            self.assertEqual(
                result["analysis"]["engine"]["name"],
                "tempo-ai-analysis-engine",
            )
            self.assertIn(
                "processedAt",
                result["analysis"]["engine"],
            )
            self.assertGreaterEqual(
                result["analysis"]["engine"][
                    "durationMilliseconds"
                ],
                0.0,
            )
            self.assertEqual(
                result["analysis"]["source"][
                    "videoPath"
                ],
                str(video_path.resolve()),
            )
            self.assertEqual(
                result["analysis"]["artifacts"][
                    "golfMetricsPath"
                ],
                str(report_path.resolve()),
            )
            self.assertEqual(
                result["report"],
                report_payload,
            )


if __name__ == "__main__":
    unittest.main()