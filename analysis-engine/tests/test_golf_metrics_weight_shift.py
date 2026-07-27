from __future__ import annotations

import unittest
from typing import Any

from app.metrics.weight_shift import (
    build_weight_shift_metrics,
)


class WeightShiftMetricsTests(unittest.TestCase):
    @staticmethod
    def build_reference(
        *,
        frame_index: int,
        timestamp_seconds: float,
        hip_x: float | None,
        hip_y: float | None = 0.60,
        pose_detected: bool = True,
    ) -> dict[str, Any]:
        hip_center = (
            {
                "x": hip_x,
                "y": hip_y,
            }
            if hip_x is not None and hip_y is not None
            else None
        )

        return {
            "frameIndex": frame_index,
            "timestampSeconds": timestamp_seconds,
            "poseDetected": pose_detected,
            "geometry": {
                "hipCenter": hip_center,
            },
        }

    def build_references(
        self,
    ) -> dict[str, dict[str, Any]]:
        return {
            "addressReference": self.build_reference(
                frame_index=10,
                timestamp_seconds=0.40,
                hip_x=0.50,
            ),
            "topOfBackswing": self.build_reference(
                frame_index=30,
                timestamp_seconds=1.20,
                hip_x=0.46,
            ),
            "downswingStart": self.build_reference(
                frame_index=36,
                timestamp_seconds=1.44,
                hip_x=0.48,
            ),
            "impactReference": self.build_reference(
                frame_index=45,
                timestamp_seconds=1.80,
                hip_x=0.54,
            ),
            "finishReference": self.build_reference(
                frame_index=60,
                timestamp_seconds=2.40,
                hip_x=0.58,
            ),
        }

    def build_metrics(
        self,
        *,
        references: dict[str, dict[str, Any]] | None = None,
        frame_width: float = 1920.0,
        frame_height: float = 1080.0,
    ) -> dict[str, Any]:
        return build_weight_shift_metrics(
            references=(
                references
                if references is not None
                else self.build_references()
            ),
            frame_width=frame_width,
            frame_height=frame_height,
        )

    def test_extracts_complete_weight_shift_measurements(
        self,
    ) -> None:
        metrics = self.build_metrics()

        self.assertEqual(
            metrics["measurementCompleteness"],
            {
                "available": 5,
                "total": 5,
                "ratio": 1.0,
            },
        )

        measurements = metrics["measurements"]

        self.assertAlmostEqual(
            measurements["addressToTop"][
                "deltaXNormalized"
            ],
            -0.04,
        )
        self.assertAlmostEqual(
            measurements["topToDownswingStart"][
                "deltaXNormalized"
            ],
            0.02,
        )
        self.assertAlmostEqual(
            measurements["topToImpact"][
                "deltaXNormalized"
            ],
            0.08,
        )
        self.assertAlmostEqual(
            measurements["addressToImpact"][
                "deltaXNormalized"
            ],
            0.04,
        )
        self.assertAlmostEqual(
            measurements["impactToFinish"][
                "deltaXNormalized"
            ],
            0.04,
        )

    def test_calculates_absolute_normalized_shift(
        self,
    ) -> None:
        metrics = self.build_metrics()
        measurements = metrics["measurements"]

        self.assertAlmostEqual(
            measurements["addressToTop"][
                "absoluteDeltaXNormalized"
            ],
            0.04,
        )
        self.assertAlmostEqual(
            measurements["topToDownswingStart"][
                "absoluteDeltaXNormalized"
            ],
            0.02,
        )
        self.assertAlmostEqual(
            measurements["topToImpact"][
                "absoluteDeltaXNormalized"
            ],
            0.08,
        )
        self.assertAlmostEqual(
            measurements["addressToImpact"][
                "absoluteDeltaXNormalized"
            ],
            0.04,
        )
        self.assertAlmostEqual(
            measurements["impactToFinish"][
                "absoluteDeltaXNormalized"
            ],
            0.04,
        )

    def test_calculates_pixel_shift(
        self,
    ) -> None:
        metrics = self.build_metrics()
        address_to_top = metrics["measurements"][
            "addressToTop"
        ]
        top_to_impact = metrics["measurements"][
            "topToImpact"
        ]

        self.assertAlmostEqual(
            address_to_top["deltaXPixels"],
            -76.8,
        )
        self.assertAlmostEqual(
            address_to_top["absoluteDeltaXPixels"],
            76.8,
        )
        self.assertAlmostEqual(
            top_to_impact["deltaXPixels"],
            153.6,
        )
        self.assertAlmostEqual(
            top_to_impact["absoluteDeltaXPixels"],
            153.6,
        )

    def test_records_lateral_movement_directions(
        self,
    ) -> None:
        metrics = self.build_metrics()
        measurements = metrics["measurements"]

        self.assertEqual(
            measurements["addressToTop"]["direction"],
            "left",
        )
        self.assertEqual(
            measurements["topToDownswingStart"][
                "direction"
            ],
            "right",
        )
        self.assertEqual(
            measurements["topToImpact"]["direction"],
            "right",
        )
        self.assertEqual(
            measurements["addressToImpact"][
                "direction"
            ],
            "right",
        )
        self.assertEqual(
            measurements["impactToFinish"][
                "direction"
            ],
            "right",
        )

    def test_complete_sequence_is_within_target(
        self,
    ) -> None:
        metrics = self.build_metrics()

        self.assertEqual(
            metrics["classification"],
            "neutral",
        )
        self.assertEqual(metrics["issueCount"], 0)
        self.assertIsNone(metrics["primaryIssue"])
        self.assertEqual(metrics["confidence"], 1.0)

        self.assertEqual(
            metrics["findings"]["backswingLoad"][
                "status"
            ],
            "within_target",
        )
        self.assertEqual(
            metrics["findings"]["transitionTransfer"][
                "status"
            ],
            "within_target",
        )
        self.assertEqual(
            metrics["findings"]["impactShift"][
                "status"
            ],
            "within_target",
        )
        self.assertEqual(
            metrics["findings"]["finishShift"][
                "status"
            ],
            "within_target",
        )
        self.assertEqual(
            metrics["feedback"]["status"],
            "within_target",
        )

    def test_transition_records_direction_reversal(
        self,
    ) -> None:
        metrics = self.build_metrics()
        transition_finding = metrics["findings"][
            "transitionTransfer"
        ]

        self.assertTrue(
            transition_finding["reversedDirection"]
        )
        self.assertEqual(
            transition_finding["direction"],
            "right",
        )
        self.assertAlmostEqual(
            transition_finding["value"],
            0.08,
        )

    def test_limited_backswing_load_needs_attention(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.495,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["primaryIssue"],
            "backswingLoad",
        )
        self.assertEqual(
            metrics["findings"]["backswingLoad"][
                "status"
            ],
            "limited_shift",
        )
        self.assertEqual(
            metrics["feedback"]["status"],
            "outside_target",
        )

    def test_excessive_backswing_load_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.35,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["primaryIssue"],
            "backswingLoad",
        )
        self.assertEqual(
            metrics["findings"]["backswingLoad"][
                "status"
            ],
            "excessive_shift",
        )

    def test_limited_transition_transfer_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["impactReference"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.47,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["primaryIssue"],
            "transitionTransfer",
        )
        self.assertEqual(
            metrics["findings"]["transitionTransfer"][
                "status"
            ],
            "limited_transfer",
        )

    def test_missing_direction_reversal_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.54,
            "y": 0.60,
        }
        references["downswingStart"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.57,
            "y": 0.60,
        }
        references["impactReference"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.60,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        transition_finding = metrics["findings"][
            "transitionTransfer"
        ]

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["primaryIssue"],
            "transitionTransfer",
        )
        self.assertEqual(
            transition_finding["status"],
            "no_direction_reversal",
        )
        self.assertFalse(
            transition_finding["reversedDirection"]
        )

    def test_excessive_transition_transfer_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["impactReference"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.65,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        transition_finding = metrics["findings"][
            "transitionTransfer"
        ]

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            transition_finding["status"],
            "excessive_shift",
        )
        self.assertTrue(
            transition_finding["reversedDirection"]
        )

    def test_excessive_address_to_impact_shift_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["impactReference"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.68,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["findings"]["impactShift"][
                "status"
            ],
            "excessive_shift",
        )

    def test_excessive_impact_to_finish_shift_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["finishReference"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.80,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["classification"],
            "needs_attention",
        )
        self.assertEqual(
            metrics["findings"]["finishShift"][
                "status"
            ],
            "excessive_shift",
        )

    def test_stationary_shift_direction_is_identified(
        self,
    ) -> None:
        references = self.build_references()

        references["topOfBackswing"]["geometry"][
            "hipCenter"
        ] = {
            "x": 0.505,
            "y": 0.60,
        }

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["measurements"]["addressToTop"][
                "direction"
            ],
            "stationary",
        )

    def test_missing_measurements_produce_incomplete_result(
        self,
    ) -> None:
        references = self.build_references()

        for reference_name in references:
            references[reference_name]["geometry"][
                "hipCenter"
            ] = None

        metrics = self.build_metrics(
            references=references
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
                "available": 0,
                "total": 5,
                "ratio": 0.0,
            },
        )
        self.assertEqual(metrics["issueCount"], 0)
        self.assertIsNone(metrics["primaryIssue"])

    def test_partial_measurements_reduce_completeness(
        self,
    ) -> None:
        references = self.build_references()

        references["downswingStart"]["geometry"][
            "hipCenter"
        ] = None

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["measurementCompleteness"],
            {
                "available": 4,
                "total": 5,
                "ratio": 0.8,
            },
        )
        self.assertEqual(metrics["confidence"], 0.8)

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

    def test_missing_pose_and_geometry_both_reduce_confidence(
        self,
    ) -> None:
        references = self.build_references()

        references["downswingStart"][
            "poseDetected"
        ] = False
        references["downswingStart"]["geometry"][
            "hipCenter"
        ] = None

        metrics = self.build_metrics(
            references=references
        )

        self.assertEqual(
            metrics["measurementCompleteness"][
                "ratio"
            ],
            0.8,
        )
        self.assertEqual(metrics["confidence"], 0.6)

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
            reference_frames["downswingStart"][
                "frameIndex"
            ],
            36,
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

        self.assertEqual(
            reference_frames["downswingStart"][
                "timestampSeconds"
            ],
            1.44,
        )
        self.assertTrue(
            reference_frames["impactReference"][
                "poseDetected"
            ]
        )

    def test_feedback_explains_proxy_limitations(
        self,
    ) -> None:
        metrics = self.build_metrics()
        basis = metrics["feedback"]["basis"]

        self.assertIn(
            "weight-shift proxy",
            basis,
        )
        self.assertIn(
            "does not measure pressure",
            basis,
        )
        self.assertIn(
            "video mirroring",
            basis,
        )

    def test_missing_address_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["addressReference"]

        with self.assertRaisesRegex(
            ValueError,
            "addressReference is missing",
        ):
            self.build_metrics(references=references)

    def test_missing_top_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["topOfBackswing"]

        with self.assertRaisesRegex(
            ValueError,
            "topOfBackswing is missing",
        ):
            self.build_metrics(references=references)

    def test_missing_downswing_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["downswingStart"]

        with self.assertRaisesRegex(
            ValueError,
            "downswingStart is missing",
        ):
            self.build_metrics(references=references)

    def test_missing_impact_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["impactReference"]

        with self.assertRaisesRegex(
            ValueError,
            "impactReference is missing",
        ):
            self.build_metrics(references=references)

    def test_missing_finish_reference_raises_error(
        self,
    ) -> None:
        references = self.build_references()
        del references["finishReference"]

        with self.assertRaisesRegex(
            ValueError,
            "finishReference is missing",
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