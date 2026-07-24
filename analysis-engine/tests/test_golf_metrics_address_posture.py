from __future__ import annotations

import unittest
from typing import Any

from app.golf_metrics import build_address_posture_metrics


class AddressPostureMetricsTests(unittest.TestCase):
    @staticmethod
    def build_references(
        *,
        pose_detected: bool = True,
        geometry: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        address_geometry = (
            geometry
            if geometry is not None
            else {
                "headCenter": {
                    "x": 0.50,
                    "y": 0.20,
                },
                "shoulderCenter": {
                    "x": 0.50,
                    "y": 0.38,
                },
                "hipCenter": {
                    "x": 0.50,
                    "y": 0.58,
                },
                "spineAngle": 42.0,
                "shoulderTilt": 5.0,
                "hipTilt": 2.0,
            }
        )

        return {
            "addressReference": {
                "frameIndex": 65,
                "timestampSeconds": 2.6,
                "poseDetected": pose_detected,
                "geometry": address_geometry,
            }
        }

    def test_extracts_complete_address_measurements(
        self,
    ) -> None:
        result = build_address_posture_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
        )

        measurements = result["measurements"]

        self.assertEqual(
            measurements["spineAngleDegrees"],
            42.0,
        )
        self.assertEqual(
            measurements["shoulderTiltDegrees"],
            5.0,
        )
        self.assertEqual(
            measurements["hipTiltDegrees"],
            2.0,
        )

        self.assertEqual(
            measurements["headToHipOffset"][
                "deltaXNormalized"
            ],
            0.0,
        )
        self.assertEqual(
            measurements["headToHipOffset"][
                "deltaYNormalized"
            ],
            -0.38,
        )
        self.assertEqual(
            measurements["headToHipOffset"][
                "deltaYPixels"
            ],
            -410.4,
        )

        self.assertEqual(
            measurements["shoulderToHipOffset"][
                "deltaYNormalized"
            ],
            -0.2,
        )
        self.assertEqual(
            measurements["shoulderToHipOffset"][
                "deltaYPixels"
            ],
            -216.0,
        )

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 5,
                "total": 5,
                "ratio": 1.0,
            },
        )
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(
            result["classification"],
            "unclassified",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "not_available",
        )

    def test_records_address_reference_metadata(
        self,
    ) -> None:
        result = build_address_posture_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(
            result["referenceFrame"],
            {
                "name": "addressReference",
                "frameIndex": 65,
                "timestampSeconds": 2.6,
                "poseDetected": True,
            },
        )

    def test_missing_measurements_reduce_completeness(
        self,
    ) -> None:
        geometry = {
            "headCenter": {
                "x": 0.50,
                "y": 0.20,
            },
            "shoulderCenter": None,
            "hipCenter": {
                "x": 0.50,
                "y": 0.58,
            },
            "spineAngle": 42.0,
            "shoulderTilt": None,
            "hipTilt": 2.0,
        }

        result = build_address_posture_metrics(
            references=self.build_references(
                geometry=geometry
            ),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(
            result["measurementCompleteness"],
            {
                "available": 3,
                "total": 5,
                "ratio": 0.6,
            },
        )
        self.assertEqual(result["confidence"], 0.6)

        self.assertIsNone(
            result["measurements"][
                "shoulderTiltDegrees"
            ]
        )
        self.assertIsNone(
            result["measurements"][
                "shoulderToHipOffset"
            ]["distanceNormalized"]
        )

    def test_missing_pose_reduces_confidence(
        self,
    ) -> None:
        result = build_address_posture_metrics(
            references=self.build_references(
                pose_detected=False
            ),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(
            result["measurementCompleteness"]["ratio"],
            1.0,
        )
        self.assertEqual(result["confidence"], 0.75)
        self.assertFalse(
            result["referenceFrame"]["poseDetected"]
        )

    def test_missing_address_reference_raises_error(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Address reference is missing",
        ):
            build_address_posture_metrics(
                references={},
                frame_width=1920,
                frame_height=1080,
            )

    def test_missing_address_geometry_raises_error(
        self,
    ) -> None:
        references = {
            "addressReference": {
                "frameIndex": 65,
                "timestampSeconds": 2.6,
                "poseDetected": True,
                "geometry": None,
            }
        }

        with self.assertRaisesRegex(
            ValueError,
            "Address reference geometry is missing",
        ):
            build_address_posture_metrics(
                references=references,
                frame_width=1920,
                frame_height=1080,
            )


if __name__ == "__main__":
    unittest.main()