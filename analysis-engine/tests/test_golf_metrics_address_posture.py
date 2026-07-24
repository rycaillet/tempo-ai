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
                "deltaYNormalized"
            ],
            -0.38,
        )
        self.assertEqual(
            measurements["shoulderToHipOffset"][
                "deltaYNormalized"
            ],
            -0.2,
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

    def test_neutral_address_posture_is_within_target(
        self,
    ) -> None:
        result = build_address_posture_metrics(
            references=self.build_references(),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(
            result["classification"],
            "neutral",
        )
        self.assertEqual(result["issueCount"], 0)
        self.assertIsNone(result["primaryIssue"])
        self.assertEqual(
            result["feedback"]["status"],
            "within_target",
        )

        for finding in result["findings"].values():
            self.assertIn(
                finding["status"],
                {
                    "within_target",
                    "centered",
                },
            )

    def test_upright_spine_is_identified(
        self,
    ) -> None:
        geometry = {
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
            "spineAngle": 25.0,
            "shoulderTilt": 5.0,
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
            result["classification"],
            "needs_attention",
        )
        self.assertEqual(result["issueCount"], 1)
        self.assertEqual(
            result["primaryIssue"],
            "spineAngle",
        )
        self.assertEqual(
            result["findings"]["spineAngle"]["status"],
            "too_upright",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "outside_target",
        )

    def test_excessive_tilts_are_identified(
        self,
    ) -> None:
        geometry = {
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
            "shoulderTilt": -22.0,
            "hipTilt": -14.0,
        }

        result = build_address_posture_metrics(
            references=self.build_references(
                geometry=geometry
            ),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(result["issueCount"], 2)
        self.assertEqual(
            result["findings"]["shoulderTilt"][
                "status"
            ],
            "excessive_tilt",
        )
        self.assertEqual(
            result["findings"]["hipTilt"]["status"],
            "excessive_tilt",
        )

    def test_horizontal_offsets_are_identified(
        self,
    ) -> None:
        geometry = {
            "headCenter": {
                "x": 0.70,
                "y": 0.20,
            },
            "shoulderCenter": {
                "x": 0.65,
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

        result = build_address_posture_metrics(
            references=self.build_references(
                geometry=geometry
            ),
            frame_width=1920,
            frame_height=1080,
        )

        self.assertEqual(result["issueCount"], 2)
        self.assertEqual(
            result["findings"]["headPosition"][
                "status"
            ],
            "excessive_horizontal_offset",
        )
        self.assertEqual(
            result["findings"]["shoulderPosition"][
                "status"
            ],
            "excessive_horizontal_offset",
        )

    def test_missing_measurements_produce_incomplete_result(
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
        self.assertEqual(
            result["classification"],
            "incomplete",
        )
        self.assertEqual(
            result["feedback"]["status"],
            "insufficient_data",
        )
        self.assertEqual(
            result["findings"]["shoulderTilt"][
                "status"
            ],
            "not_available",
        )
        self.assertEqual(
            result["findings"]["shoulderPosition"][
                "status"
            ],
            "not_available",
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