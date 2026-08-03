from __future__ import annotations

import unittest
from typing import Any

from app.club_detector import ClubFrameDetection
from app.club_short_gap_tracking import (
    apply_short_gap_tracking,
    build_short_gap_tracked_line,
)


def create_frame(
    *,
    frame_index: int,
    detected: bool,
    confidence: float = 0.8,
    hand_x: float = 100.0,
    hand_y: float = 100.0,
    distal_x: float = 300.0,
    distal_y: float = 200.0,
) -> ClubFrameDetection:
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
            "angleDegrees": 26.565,
        }
        if detected
        else None
    )

    return {
        "phase": "test",
        "referenceFrameIndex": frame_index,
        "frameIndex": frame_index,
        "phaseOffsetFrames": 0,
        "isReferenceFrame": False,
        "timestampSeconds": frame_index / 30.0,
        "detected": detected,
        "detectionSource": (
            "image" if detected else "unavailable"
        ),
        "confidence": confidence if detected else 0.0,
        "handAnchor": {
            "x": hand_x,
            "y": hand_y,
        },
        "shaftLine": shaft_line,
        "candidateCount": 1 if detected else 0,
        "candidateDiagnostics": None,
        "failureReason": (
            None if detected else "No image detection."
        ),
        "debugImagePath": None,
        "temporalStatus": "pending",
        "temporalComparison": None,
        "trackingDetails": None,
    }


class ClubShortGapTrackingTests(unittest.TestCase):
    def test_builds_midpoint_line_for_single_gap(
        self,
    ) -> None:
        previous = create_frame(
            frame_index=10,
            detected=True,
            hand_x=100.0,
            distal_x=300.0,
        )
        current = create_frame(
            frame_index=11,
            detected=False,
            hand_x=110.0,
        )
        next_frame = create_frame(
            frame_index=12,
            detected=True,
            hand_x=120.0,
            distal_x=320.0,
        )

        result = build_short_gap_tracked_line(
            previous,
            current,
            next_frame,
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNotNone(result)

        assert result is not None

        line, details = result

        self.assertEqual(line["start"]["x"], 110.0)
        self.assertEqual(line["end"]["x"], 310.0)
        self.assertEqual(
            details["interpolationRatio"],
            0.5,
        )

    def test_tracking_marks_recovered_frame(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                detected=True,
                confidence=0.8,
            ),
            create_frame(
                frame_index=11,
                detected=False,
                hand_x=110.0,
                distal_x=310.0,
            ),
            create_frame(
                frame_index=12,
                detected=True,
                confidence=0.6,
                hand_x=120.0,
                distal_x=320.0,
            ),
        ]

        summary = apply_short_gap_tracking(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary,
            {
                "trackedFrames": 1,
                "imageDetectedFrames": 2,
            },
        )
        self.assertTrue(frames[1]["detected"])
        self.assertEqual(
            frames[1]["detectionSource"],
            "tracked",
        )
        self.assertAlmostEqual(
            frames[1]["confidence"],
            0.504,
        )
        self.assertIsNotNone(
            frames[1]["trackingDetails"]
        )

    def test_tracking_does_not_fill_multi_frame_gap(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                detected=True,
            ),
            create_frame(
                frame_index=11,
                detected=False,
            ),
            create_frame(
                frame_index=12,
                detected=False,
            ),
            create_frame(
                frame_index=13,
                detected=True,
            ),
        ]

        summary = apply_short_gap_tracking(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary,
            {
                "trackedFrames": 0,
                "imageDetectedFrames": 2,
            },
        )
        self.assertFalse(frames[1]["detected"])
        self.assertFalse(frames[2]["detected"])

    def test_tracking_rejects_large_frame_span(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                detected=True,
            ),
            create_frame(
                frame_index=11,
                detected=False,
            ),
            create_frame(
                frame_index=20,
                detected=True,
            ),
        ]

        summary = apply_short_gap_tracking(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary,
            {
                "trackedFrames": 0,
                "imageDetectedFrames": 2,
            },
        )

    def test_tracking_rejects_large_anchor_residual(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                detected=True,
                hand_x=100.0,
            ),
            create_frame(
                frame_index=11,
                detected=False,
                hand_x=400.0,
            ),
            create_frame(
                frame_index=12,
                detected=True,
                hand_x=120.0,
            ),
        ]

        summary = apply_short_gap_tracking(
            frames,
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            summary,
            {
                "trackedFrames": 0,
                "imageDetectedFrames": 2,
            },
        )

    def test_tracking_requires_image_neighbors(
        self,
    ) -> None:
        frames = [
            create_frame(
                frame_index=10,
                detected=True,
            ),
            create_frame(
                frame_index=11,
                detected=False,
                hand_x=110.0,
            ),
            create_frame(
                frame_index=12,
                detected=True,
                hand_x=120.0,
            ),
        ]

        frames[0]["detectionSource"] = "tracked"

        result = build_short_gap_tracked_line(
            frames[0],
            frames[1],
            frames[2],
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()