from __future__ import annotations

import unittest
from typing import Any

from app.club_trajectory_smoothing import (
    apply_club_trajectory_smoothing,
    build_smoothed_shaft_line,
)


def create_frame(
    *,
    frame_index: int,
    detected: bool = True,
    hand_x: float = 100.0,
    hand_y: float = 100.0,
    distal_x: float = 300.0,
    distal_y: float = 200.0,
    angle_degrees: float = 26.565,
) -> dict[str, Any]:
    shaft_line = (
        {
            "start": {
                "x": hand_x,
                "y": hand_y,
            },
            "end": {
                "x": distal_x,
                "y": distal_y,
            },
            "lengthPixels": (
                (
                    (distal_x - hand_x) ** 2
                    + (distal_y - hand_y) ** 2
                ) ** 0.5
            ),
            "angleDegrees": angle_degrees,
        }
        if detected
        else None
    )

    return {
        "frameIndex": frame_index,
        "detected": detected,
        "detectionSource": (
            "image" if detected else "unavailable"
        ),
        "handAnchor": {
            "x": hand_x,
            "y": hand_y,
        },
        "shaftLine": shaft_line,
    }


class ClubTrajectorySmoothingTests(
    unittest.TestCase
):
    def test_builds_weighted_smoothed_line(
        self,
    ) -> None:
        previous = create_frame(
            frame_index=10,
            distal_y=190.0,
            angle_degrees=24.228,
        )
        current = create_frame(
            frame_index=11,
            distal_y=220.0,
            angle_degrees=30.964,
        )
        next_frame = create_frame(
            frame_index=12,
            distal_y=200.0,
            angle_degrees=26.565,
        )

        result = build_smoothed_shaft_line(
            previous,
            current,
            next_frame,
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNotNone(result)

        assert result is not None

        line, details = result

        self.assertEqual(
            line["start"],
            {
                "x": 100.0,
                "y": 100.0,
            },
        )
        self.assertAlmostEqual(
            line["end"]["y"],
            207.5,
        )
        self.assertTrue(details["applied"])
        self.assertEqual(
            details["neighborFrameIndices"],
            [10, 11, 12],
        )

    def test_preserves_raw_shaft_line(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                distal_y=190.0,
                angle_degrees=24.228,
            ),
            create_frame(
                frame_index=11,
                distal_y=220.0,
                angle_degrees=30.964,
            ),
            create_frame(
                frame_index=12,
                distal_y=200.0,
                angle_degrees=26.565,
            ),
        ]

        raw_line = dict(frames[1]["shaftLine"])

        summary = apply_club_trajectory_smoothing(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary,
            {
                "smoothedFrames": 1,
                "rawDetectedFrames": 3,
            },
        )
        self.assertEqual(
            frames[1]["shaftLine"],
            raw_line,
        )
        self.assertIsNotNone(
            frames[1]["smoothedShaftLine"]
        )

    def test_does_not_fill_missing_frame(
        self,
    ) -> None:
        frames = [
            create_frame(frame_index=10),
            create_frame(
                frame_index=11,
                detected=False,
            ),
            create_frame(frame_index=12),
        ]

        summary = apply_club_trajectory_smoothing(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary["smoothedFrames"],
            0,
        )
        self.assertFalse(frames[1]["detected"])
        self.assertIsNone(
            frames[1]["smoothedShaftLine"]
        )

    def test_rejects_large_frame_gap(
        self,
    ) -> None:
        frames = [
            create_frame(frame_index=1),
            create_frame(frame_index=10),
            create_frame(frame_index=11),
        ]

        summary = apply_club_trajectory_smoothing(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary["smoothedFrames"],
            0,
        )

    def test_rejects_large_angle_disagreement(
        self,
    ) -> None:
        previous = create_frame(
            frame_index=10,
            distal_x=300.0,
            distal_y=100.0,
            angle_degrees=0.0,
        )
        current = create_frame(
            frame_index=11,
            distal_x=100.0,
            distal_y=300.0,
            angle_degrees=90.0,
        )
        next_frame = create_frame(
            frame_index=12,
            distal_x=300.0,
            distal_y=100.0,
            angle_degrees=0.0,
        )

        result = build_smoothed_shaft_line(
            previous,
            current,
            next_frame,
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(result)

    def test_aligns_neighbor_lines_to_current_anchor(
        self,
    ) -> None:
        previous = create_frame(
            frame_index=10,
            hand_x=90.0,
            distal_x=290.0,
        )
        current = create_frame(
            frame_index=11,
            hand_x=100.0,
            distal_x=300.0,
        )
        next_frame = create_frame(
            frame_index=12,
            hand_x=110.0,
            distal_x=310.0,
        )

        result = build_smoothed_shaft_line(
            previous,
            current,
            next_frame,
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNotNone(result)

        assert result is not None

        line, _ = result

        self.assertEqual(
            line["start"],
            {
                "x": 100.0,
                "y": 100.0,
            },
        )
        self.assertEqual(
            line["end"],
            {
                "x": 300.0,
                "y": 200.0,
            },
        )


    def test_rejects_excessive_angle_adjustment(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                distal_x=300.0,
                distal_y=100.0,
                angle_degrees=0.0,
            ),
            create_frame(
                frame_index=11,
                distal_x=300.0,
                distal_y=200.0,
                angle_degrees=26.565,
            ),
            create_frame(
                frame_index=12,
                distal_x=300.0,
                distal_y=100.0,
                angle_degrees=0.0,
            ),
        ]

        summary = apply_club_trajectory_smoothing(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary["smoothedFrames"],
            0,
        )
        self.assertIsNone(
            frames[1]["smoothedShaftLine"]
        )
        self.assertEqual(
            frames[1]["smoothingDetails"],
            {
                "applied": False,
                "neighborFrameIndices": [],
                "reason": (
                    "angle_adjustment_exceeds_threshold"
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()