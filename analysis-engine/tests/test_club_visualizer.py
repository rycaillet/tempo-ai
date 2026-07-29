from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from app.club_visualizer import (
    create_club_visualization_directory,
    create_club_visualization_path,
    draw_club_detection_visualization,
    sanitize_phase_name,
    save_club_detection_visualization,
)


class ClubVisualizerTests(unittest.TestCase):
    def test_create_visualization_directory_from_refined_phases(
        self,
    ) -> None:
        refined_phases_path = Path(
            "/tmp/golf-swing-refined-phases.json"
        )

        result = create_club_visualization_directory(
            refined_phases_path
        )

        self.assertEqual(
            result,
            Path(
                "/tmp/"
                "golf-swing-club-detection-frames"
            ),
        )

    def test_create_visualization_directory_with_generic_name(
        self,
    ) -> None:
        refined_phases_path = Path(
            "/tmp/analysis.json"
        )

        result = create_club_visualization_directory(
            refined_phases_path
        )

        self.assertEqual(
            result,
            Path(
                "/tmp/"
                "analysis-club-detection-frames"
            ),
        )

    def test_sanitize_phase_name(
        self,
    ) -> None:
        self.assertEqual(
            sanitize_phase_name(
                "Top Of Backswing!"
            ),
            "top-of-backswing",
        )

    def test_sanitize_phase_name_handles_empty_value(
        self,
    ) -> None:
        self.assertEqual(
            sanitize_phase_name("!!!"),
            "unknown-phase",
        )

    def test_create_visualization_path(
        self,
    ) -> None:
        visualization_directory = Path(
            "/tmp/club-frames"
        )

        result = create_club_visualization_path(
            visualization_directory,
            phase_name="topOfBackswing",
            frame_index=93,
        )

        self.assertEqual(
            result,
            Path(
                "/tmp/club-frames/"
                "topofbackswing-frame-000093.jpg"
            ),
        )

    def test_draw_visualization_returns_modified_copy(
        self,
    ) -> None:
        frame = np.zeros(
            (300, 400, 3),
            dtype=np.uint8,
        )

        original_frame = frame.copy()

        visualization = (
            draw_club_detection_visualization(
                frame,
                phase_name="impactReference",
                frame_index=107,
                hand_anchor={
                    "x": 180.0,
                    "y": 150.0,
                },
                shaft_line={
                    "start": {
                        "x": 180.0,
                        "y": 150.0,
                    },
                    "end": {
                        "x": 300.0,
                        "y": 220.0,
                    },
                    "lengthPixels": 138.924,
                    "angleDegrees": 30.256,
                },
                confidence=0.82,
                candidate_count=4,
                detected=True,
                failure_reason=None,
            )
        )

        self.assertEqual(
            visualization.shape,
            frame.shape,
        )

        self.assertFalse(
            np.array_equal(
                visualization,
                original_frame,
            )
        )

        self.assertTrue(
            np.array_equal(
                frame,
                original_frame,
            )
        )

    def test_draw_failed_detection_visualization(
        self,
    ) -> None:
        frame = np.zeros(
            (300, 400, 3),
            dtype=np.uint8,
        )

        visualization = (
            draw_club_detection_visualization(
                frame,
                phase_name="address",
                frame_index=65,
                hand_anchor={
                    "x": 190.0,
                    "y": 160.0,
                },
                shaft_line=None,
                confidence=0.0,
                candidate_count=0,
                detected=False,
                failure_reason=(
                    "No reliable shaft-line "
                    "candidate was found."
                ),
            )
        )

        self.assertEqual(
            visualization.shape,
            frame.shape,
        )

        self.assertGreater(
            int(visualization.sum()),
            0,
        )

    def test_draw_visualization_rejects_empty_frame(
        self,
    ) -> None:
        empty_frame = np.empty(
            (0, 0, 3),
            dtype=np.uint8,
        )

        with self.assertRaises(ValueError):
            draw_club_detection_visualization(
                empty_frame,
                phase_name="address",
                frame_index=1,
                hand_anchor=None,
                shaft_line=None,
                confidence=0.0,
                candidate_count=0,
                detected=False,
                failure_reason="Frame unavailable.",
            )

    def test_save_visualization_writes_image(
        self,
    ) -> None:
        frame = np.zeros(
            (120, 160, 3),
            dtype=np.uint8,
        )

        cv2.line(
            frame,
            (20, 20),
            (140, 100),
            (255, 255, 255),
            3,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "nested"
                / "address-frame-000001.jpg"
            )

            save_club_detection_visualization(
                output_path,
                frame,
            )

            self.assertTrue(
                output_path.is_file()
            )

            saved_frame = cv2.imread(
                str(output_path)
            )

            self.assertIsNotNone(
                saved_frame
            )

            if saved_frame is None:
                self.fail(
                    "OpenCV could not read the "
                    "saved visualization."
                )

            self.assertEqual(
                saved_frame.shape,
                frame.shape,
            )

    def test_save_visualization_rejects_empty_frame(
        self,
    ) -> None:
        empty_frame = np.empty(
            (0, 0, 3),
            dtype=np.uint8,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_path = (
                Path(directory)
                / "empty.jpg"
            )

            with self.assertRaises(ValueError):
                save_club_detection_visualization(
                    output_path,
                    empty_frame,
                )


if __name__ == "__main__":
    unittest.main()