from __future__ import annotations

import unittest
from typing import Any

from app.metrics.swing_plane import (
    build_phase_measurement,
    build_swing_plane_metrics,
    calculate_signed_axial_angle_change,
    select_reference_detection,
    select_shaft_geometry,
)


class SwingPlaneMetricTests(unittest.TestCase):
    @staticmethod
    def build_line(
        angle: float,
    ) -> dict[str, Any]:
        return {
            "start": {"x": 100.0, "y": 100.0},
            "end": {"x": 300.0, "y": 200.0},
            "lengthPixels": 223.607,
            "angleDegrees": angle,
        }

    def build_frame(
        self,
        *,
        phase: str,
        frame_index: int,
        angle: float | None,
        is_reference_frame: bool = True,
        smoothed_angle: float | None = None,
        detected: bool = True,
        detection_source: str = "image",
        confidence: float = 0.8,
        phase_offset_frames: int = 0,
        candidate_diagnostics: (
            dict[str, Any] | None
        ) = None,
    ) -> dict[str, Any]:
        return {
            "phase": phase,
            "referenceFrameIndex": frame_index,
            "frameIndex": frame_index,
            "phaseOffsetFrames": phase_offset_frames,
            "isReferenceFrame": is_reference_frame,
            "timestampSeconds": frame_index / 30.0,
            "detected": detected,
            "confidence": confidence,
            "shaftLine": (
                self.build_line(angle)
                if angle is not None
                else None
            ),
            "smoothedShaftLine": (
                self.build_line(smoothed_angle)
                if smoothed_angle is not None
                else None
            ),
            "detectionSource": detection_source,
            "candidateDiagnostics": (
                candidate_diagnostics
            ),
        }

    def build_club_detection(
        self,
    ) -> dict[str, Any]:
        phases = (
            ("address", 10, 135.0),
            ("takeaway", 20, 145.0),
            ("topOfBackswing", 30, 75.0),
            ("downswingStart", 40, 85.0),
            ("impactReference", 50, 120.0),
            ("finishReference", 60, 40.0),
        )

        return {
            "frames": [
                self.build_frame(
                    phase=phase,
                    frame_index=frame_index,
                    angle=angle,
                    smoothed_angle=(
                        angle + 1.0
                        if phase in {
                            "takeaway",
                            "downswingStart",
                        }
                        else None
                    ),
                )
                for phase, frame_index, angle
                in phases
            ]
        }

    def test_calculate_signed_axial_angle_change_wraps_direction(
        self,
    ) -> None:
        self.assertEqual(
            calculate_signed_axial_angle_change(
                175.0,
                5.0,
            ),
            10.0,
        )
        self.assertEqual(
            calculate_signed_axial_angle_change(
                5.0,
                175.0,
            ),
            -10.0,
        )

    def test_select_reference_detection_prefers_reference_frame(
        self,
    ) -> None:
        frames = [
            self.build_frame(
                phase="takeaway",
                frame_index=19,
                angle=140.0,
                is_reference_frame=False,
                phase_offset_frames=-1,
            ),
            self.build_frame(
                phase="takeaway",
                frame_index=20,
                angle=145.0,
                is_reference_frame=True,
            ),
        ]

        result = select_reference_detection(
            frames,
            "takeaway",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["frameIndex"], 20)

    def test_select_reference_detection_uses_nearest_detected_frame(
        self,
    ) -> None:
        frames = [
            self.build_frame(
                phase="impactReference",
                frame_index=49,
                angle=115.0,
                is_reference_frame=False,
                phase_offset_frames=-1,
            ),
            self.build_frame(
                phase="impactReference",
                frame_index=52,
                angle=125.0,
                is_reference_frame=False,
                phase_offset_frames=2,
            ),
        ]

        result = select_reference_detection(
            frames,
            "impactReference",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["frameIndex"], 49)

    def test_select_shaft_geometry_prefers_smoothed_line(
        self,
    ) -> None:
        frame = self.build_frame(
            phase="takeaway",
            frame_index=20,
            angle=145.0,
            smoothed_angle=146.0,
        )

        line, source = select_shaft_geometry(frame)

        self.assertIsNotNone(line)
        assert line is not None
        self.assertEqual(line["angleDegrees"], 146.0)
        self.assertEqual(source, "smoothed")

    def test_build_phase_measurement_falls_back_to_raw_line(
        self,
    ) -> None:
        frame = self.build_frame(
            phase="address",
            frame_index=10,
            angle=135.0,
        )

        result = build_phase_measurement(
            frame,
            phase_name="address",
        )

        self.assertTrue(result["available"])
        self.assertEqual(
            result["shaftAngleDegrees"],
            135.0,
        )
        self.assertEqual(
            result["geometrySource"],
            "raw",
        )

    def test_build_phase_measurement_rejects_short_single_fallback_fragment(
        self,
    ) -> None:
        frame = self.build_frame(
            phase="impactReference",
            frame_index=50,
            angle=120.0,
            candidate_diagnostics={
                "candidateEvaluations": [
                    {
                        "selected": True,
                        "lengthRatio": 0.05,
                        "provenance": {
                            "houghPass": "fallback",
                            "segmentSource": "single",
                        },
                    }
                ],
            },
        )

        result = build_phase_measurement(
            frame,
            phase_name="impactReference",
        )

        self.assertFalse(
            result["available"]
        )
        self.assertIsNone(
            result["shaftAngleDegrees"]
        )
        self.assertIsNone(
            result["geometrySource"]
        )

    def test_build_swing_plane_metrics_returns_observed_result(
        self,
    ) -> None:
        result = build_swing_plane_metrics(
            self.build_club_detection()
        )

        self.assertEqual(
            result["classification"],
            "observed",
        )
        self.assertEqual(result["issueCount"], 0)
        self.assertIsNone(result["primaryIssue"])

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 6,
                "total": 6,
                "ratio": 1.0,
            },
        )

        measurements = result["measurements"]

        self.assertEqual(
            measurements[
                "smoothedReferenceCount"
            ],
            2,
        )
        self.assertEqual(
            measurements[
                "trackedReferenceCount"
            ],
            0,
        )
        self.assertEqual(
            measurements[
                "phaseMeasurements"
            ]["takeaway"]["geometrySource"],
            "smoothed",
        )
        self.assertEqual(
            measurements[
                "phaseChangesDegrees"
            ]["topToImpactDegrees"],
            45.0,
        )
        self.assertEqual(
            result["feedback"]["status"],
            "measurement_only",
        )
        self.assertGreater(result["confidence"], 0.0)

    def test_build_swing_plane_metrics_handles_partial_trajectory(
        self,
    ) -> None:
        club_detection = self.build_club_detection()
        club_detection["frames"] = [
            frame
            for frame in club_detection["frames"]
            if frame["phase"] != "finishReference"
        ]

        result = build_swing_plane_metrics(
            club_detection
        )

        self.assertEqual(
            result["classification"],
            "observed",
        )
        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 5,
                "total": 6,
                "ratio": 0.833333,
            },
        )
        self.assertEqual(
            result["findings"][
                "cameraRelativeSwingPlane"
            ]["status"],
            "partial_trajectory",
        )

    def test_build_swing_plane_metrics_handles_missing_detection_input(
        self,
    ) -> None:
        result = build_swing_plane_metrics(
            {"frames": []}
        )

        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 0,
                "total": 6,
                "ratio": 0.0,
            },
        )
        self.assertEqual(
            result["feedback"]["status"],
            "insufficient_data",
        )


if __name__ == "__main__":
    unittest.main()