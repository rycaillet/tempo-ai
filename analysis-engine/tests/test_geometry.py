from __future__ import annotations

import unittest
from typing import Any

from app.geometry import (
    LEFT_HIP,
    LEFT_SHOULDER,
    RIGHT_HIP,
    RIGHT_SHOULDER,
    calculate_frame_geometry,
    create_empty_geometry,
)


class GeometryTests(unittest.TestCase):
    @staticmethod
    def build_landmark(
        *,
        index: int,
        x: float,
        y: float,
        z: float,
        visibility: float = 0.99,
        presence: float = 0.99,
    ) -> dict[str, int | float]:
        return {
            "index": index,
            "x": x,
            "y": y,
            "z": z,
            "visibility": visibility,
            "presence": presence,
        }

    def build_pose_frame(
        self,
        *,
        pose_detected: bool = True,
        landmarks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "frameIndex": 12,
            "timestampMs": 400,
            "timestampSeconds": 0.4,
            "poseDetected": pose_detected,
            "landmarks": landmarks or [],
        }

    def test_create_empty_geometry_contains_rotation_landmarks(
        self,
    ) -> None:
        geometry = create_empty_geometry()

        self.assertIn("leftShoulder", geometry)
        self.assertIn("rightShoulder", geometry)
        self.assertIn("leftHip", geometry)
        self.assertIn("rightHip", geometry)

        self.assertIsNone(geometry["leftShoulder"])
        self.assertIsNone(geometry["rightShoulder"])
        self.assertIsNone(geometry["leftHip"])
        self.assertIsNone(geometry["rightHip"])

    def test_calculate_frame_geometry_exposes_rotation_landmarks(
        self,
    ) -> None:
        landmarks = [
            self.build_landmark(
                index=LEFT_SHOULDER,
                x=0.40,
                y=0.30,
                z=-0.12,
            ),
            self.build_landmark(
                index=RIGHT_SHOULDER,
                x=0.60,
                y=0.32,
                z=0.08,
            ),
            self.build_landmark(
                index=LEFT_HIP,
                x=0.44,
                y=0.60,
                z=-0.05,
            ),
            self.build_landmark(
                index=RIGHT_HIP,
                x=0.56,
                y=0.61,
                z=0.04,
            ),
        ]

        frame = self.build_pose_frame(
            landmarks=landmarks,
        )

        geometry = calculate_frame_geometry(
            frame=frame,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertEqual(
            geometry["leftShoulder"],
            {
                "x": 0.4,
                "y": 0.3,
                "z": -0.12,
                "visibility": 0.99,
            },
        )
        self.assertEqual(
            geometry["rightShoulder"],
            {
                "x": 0.6,
                "y": 0.32,
                "z": 0.08,
                "visibility": 0.99,
            },
        )
        self.assertEqual(
            geometry["leftHip"],
            {
                "x": 0.44,
                "y": 0.6,
                "z": -0.05,
                "visibility": 0.99,
            },
        )
        self.assertEqual(
            geometry["rightHip"],
            {
                "x": 0.56,
                "y": 0.61,
                "z": 0.04,
                "visibility": 0.99,
            },
        )

    def test_calculate_frame_geometry_filters_low_visibility_points(
        self,
    ) -> None:
        landmarks = [
            self.build_landmark(
                index=LEFT_SHOULDER,
                x=0.40,
                y=0.30,
                z=-0.12,
                visibility=0.20,
            ),
            self.build_landmark(
                index=RIGHT_SHOULDER,
                x=0.60,
                y=0.32,
                z=0.08,
            ),
            self.build_landmark(
                index=LEFT_HIP,
                x=0.44,
                y=0.60,
                z=-0.05,
            ),
            self.build_landmark(
                index=RIGHT_HIP,
                x=0.56,
                y=0.61,
                z=0.04,
            ),
        ]

        frame = self.build_pose_frame(
            landmarks=landmarks,
        )

        geometry = calculate_frame_geometry(
            frame=frame,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertIsNone(geometry["leftShoulder"])
        self.assertIsNotNone(geometry["rightShoulder"])
        self.assertIsNotNone(geometry["leftHip"])
        self.assertIsNotNone(geometry["rightHip"])

    def test_calculate_frame_geometry_returns_empty_geometry_without_pose(
        self,
    ) -> None:
        frame = self.build_pose_frame(
            pose_detected=False,
        )

        geometry = calculate_frame_geometry(
            frame=frame,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertTrue(
            all(
                value is None
                for value in geometry.values()
            )
        )

    def test_calculate_frame_geometry_returns_empty_geometry_without_landmarks(
        self,
    ) -> None:
        frame = self.build_pose_frame(
            pose_detected=True,
            landmarks=[],
        )

        geometry = calculate_frame_geometry(
            frame=frame,
            frame_width=1920.0,
            frame_height=1080.0,
        )

        self.assertTrue(
            all(
                value is None
                for value in geometry.values()
            )
        )


if __name__ == "__main__":
    unittest.main()