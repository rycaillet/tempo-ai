from __future__ import annotations

import unittest
from typing import Any

from app.metrics.head_stability import (
    build_head_stability_metrics,
)


class HeadStabilityMetricsTests(unittest.TestCase):
    @staticmethod
    def build_reference(
        *,
        frame_index: int,
        timestamp_seconds: float,
        head_x: float | None,
        head_y: float | None,
        pose_detected: bool = True,
    ) -> dict[str, Any]:
        head_center = (
            {
                "x": head_x,
                "y": head_y,
            }
            if head_x is not None and head_y is not None
            else None
        )

        return {
            "frameIndex": frame_index,
            "timestampSeconds": timestamp_seconds,
            "poseDetected": pose_detected,
            "geometry": {
                "headCenter": head_center,
            },
        }

    def build_references(
        self,
    ) -> dict[str, dict[str, Any]]:
        return {
            "addressReference": self.build_reference(
                frame_index=10,
                timestamp_seconds=0.40,
                head_x=0.50,
                head_y=0.20,
            ),
            "topOfBackswing": self.build_reference(
                frame_index=30,
                timestamp_seconds=1.20,
                head_x=0.53,
                head_y=0.22,
            ),
            "impactReference": self.build_reference(
                frame_index=45,
                timestamp_seconds=1.80,
                head_x=0.55,
                head_y=0.23,
            ),
            "finishReference": self.build_reference(
                frame_index=60,
                timestamp_seconds=2.40,
                head_x=0.58,
                head_y=0.25,
            ),
        }

    @staticmethod
    def build_frames() -> list[dict[str, Any]]:
        return [
            {
                "frameIndex": 10,
                "timestampSeconds": 0.40,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.50,
                        "y": 0.20,
                    },
                },
            },
            {
                "frameIndex": 20,
                "timestampSeconds": 0.80,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.52,
                        "y": 0.21,
                    },
                },
            },
            {
                "frameIndex": 30,
                "timestampSeconds": 1.20,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.53,
                        "y": 0.22,
                    },
                },
            },
            {
                "frameIndex": 45,
                "timestampSeconds": 1.80,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.55,
                        "y": 0.23,
                    },
                },
            },
            {
                "frameIndex": 52,
                "timestampSeconds": 2.08,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.60,
                        "y": 0.27,
                    },
                },
            },
            {
                "frameIndex": 60,
                "timestampSeconds": 2.40,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.58,
                        "y": 0.25,
                    },
                },
            },
        ]

    def build_metrics(
        self,
        *,
        references: dict[str, dict[str, Any]] | None = None,
        frames: list[dict[str, Any]] | None = None,
        frame_width: float = 1920.0,
        frame_height: float = 1080.0,
    ) -> dict[str, Any]:
        return build_head_stability_metrics(
            references=(
                references
                if references is not None
                else self.build_references()
            ),
            frames=(
                frames
                if frames is not None
                else self.build_frames()
            ),
            frame_width=frame_width,
            frame_height=frame_height,
        )

    def test_extracts_complete_head_stability_measurements(
        self,
    ) -> None:
        metrics = self.build_metrics()

        self.assertEqual(
            metrics["measurementCompleteness"],
            {
                "available": 4,
                "total": 4,
                "ratio": 1.0,
            },
        )

        measurements = metrics["measurements"]

        self.assertAlmostEqual(
            measurements["addressToTop"][
                "deltaXNormalized"
            ],
            0.03,
        )
        self.assertAlmostEqual(
            measurements["addressToTop"][
                "deltaYNormalized"
            ],
            0.02,
        )
        self.assertAlmostEqual(
            measurements["addressToImpact"][
                "deltaXNormalized"
            ],
            0.05,
        )
        self.assertAlmostEqual(
            measurements["addressToImpact"][
                "deltaYNormalized"
            ],
            0.03,
        )
        self.assertAlmostEqual(
            measurements["addressToFinish"][
                "deltaXNormalized"
            ],
            0.08,
        )
        self.assertAlmostEqual(
            measurements["addressToFinish"][
                "deltaYNormalized"
            ],
            0.05,
        )

    def test_calculates_pixel_and_normalized_distances(
        self,
    ) -> None:
        metrics = self.build_metrics()
        impact_movement = metrics["measurements"][
            "addressToImpact"
        ]

        self.assertAlmostEqual(
            impact_movement["distanceNormalized"],
            0.05831,
            places=5,
        )
        self.assertAlmostEqual(
            impact_movement["deltaXPixels"],
            96.0,
        )
        self.assertAlmostEqual(
            impact_movement["deltaYPixels"],
            32.4,
        )
        self.assertAlmostEqual(
            impact_movement["distancePixels"],
            101.320087,
            places=6,
        )

    def test_records_maximum_movement_frame(
        self,
    ) -> None:
        metrics = self.build_metrics()
        maximum_movement = metrics["measurements"][
            "maximumMovement"
        ]

        self.assertEqual(
            maximum_movement["frameIndex"],
            52,
        )
        self.assertEqual(
            maximum_movement["timestampSeconds"],
            2.08,
        )
        self.assertAlmostEqual(
            maximum_movement["deltaXNormalized"],
            0.10,
        )
        self.assertAlmostEqual(
            maximum_movement["deltaYNormalized"],
            0.07,
        )
        self.assertAlmostEqual(
            maximum_movement["distanceNormalized"],
            0.122066,
            places=6,
        )

    def test_moderate_maximum_movement_needs_attention(
        self,
    ) -> None:
        metrics = self.build_metrics()

        self.assertEqual(
          metrics["classification"],
          "needs_attention",
        )
        self.assertEqual(metrics["issueCount"], 1)
        self.assertEqual(
          metrics["primaryIssue"],
          "maximumStability",
        )
        self.assertEqual(metrics["confidence"], 1.0)

        self.assertEqual(
          metrics["findings"]["impactStability"]["status"],
          "within_target",
        )
        self.assertEqual(
          metrics["findings"]["maximumStability"]["status"],
          "moderate_movement",
        )
        self.assertEqual(
          metrics["feedback"]["status"],
          "outside_target",
        )

    def test_moderate_impact_movement_needs_attention(
        self,
    ) -> None:
        references = self.build_references()
        references["impactReference"]["geometry"][
            "headCenter"
        ] = {
            "x": 0.61,
            "y": 0.25,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(metrics["issueCount"], 2)
        self.assertEqual(
            metrics["primaryIssue"],
            "impactStability",
        )
        self.assertEqual(
            metrics["findings"]["impactStability"][
                "status"
            ],
            "moderate_movement",
        )

    def test_excessive_impact_movement_is_identified(
        self,
    ) -> None:
        references = self.build_references()
        references["impactReference"]["geometry"][
            "headCenter"
        ] = {
            "x": 0.70,
            "y": 0.30,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["findings"]["impactStability"][
                "status"
            ],
            "excessive_movement",
        )

    def test_excessive_maximum_movement_is_identified(
        self,
    ) -> None:
        frames = self.build_frames()
        frames.append(
            {
                "frameIndex": 55,
                "timestampSeconds": 2.20,
                "poseDetected": True,
                "geometry": {
                    "headCenter": {
                        "x": 0.75,
                        "y": 0.35,
                    },
                },
            }
        )

        metrics = self.build_metrics(frames=frames)

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["findings"]["maximumStability"][
                "status"
            ],
            "excessive_movement",
        )

    def test_missing_measurements_produce_incomplete_result(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"]["geometry"][
            "headCenter"
        ] = None
        references["impactReference"]["geometry"][
            "headCenter"
        ] = None

        frames = [
            {
                "frameIndex": 10,
                "timestampSeconds": 0.40,
                "poseDetected": False,
                "geometry": {
                    "headCenter": None,
                },
            }
        ]

        metrics = self.build_metrics(
            references=references,
            frames=frames,
        )

        self.assertEqual(
            metrics["classification"],
            "incomplete",
        )
        self.assertEqual(
            metrics["feedback"]["status"],
            "insufficient_data",
        )
        self.assertEqual(
            metrics["measurementCompleteness"],
            {
                "available": 1,
                "total": 4,
                "ratio": 0.25,
            },
        )

    def test_missing_pose_reduces_confidence(
        self,
    ) -> None:
        references = self.build_references()
        references["impactReference"][
            "poseDetected"
        ] = False

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["measurementCompleteness"][
                "ratio"
            ],
            1.0,
        )
        self.assertEqual(metrics["confidence"], 0.75)

    def test_records_reference_metadata(
        self,
    ) -> None:
        metrics = self.build_metrics()
        reference_frames = metrics["referenceFrames"]

        self.assertEqual(
            reference_frames["addressReference"][
                "frameIndex"
            ],
            10,
        )
        self.assertEqual(
            reference_frames["topOfBackswing"][
                "frameIndex"
            ],
            30,
        )
        self.assertEqual(
            reference_frames["impactReference"][
                "frameIndex"
            ],
            45,
        )
        self.assertEqual(
            reference_frames["finishReference"][
                "frameIndex"
            ],
            60,
        )

    def test_missing_required_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["impactReference"]

        with self.assertRaisesRegex(
            ValueError,
            "impactReference is missing",
        ):
            self.build_metrics(references=references)

    def test_invalid_frame_width_raises_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Frame width must be greater than zero",
        ):
            self.build_metrics(frame_width=0.0)

    def test_invalid_frame_height_raises_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Frame height must be greater than zero",
        ):
            self.build_metrics(frame_height=-1.0)


if __name__ == "__main__":
    unittest.main()