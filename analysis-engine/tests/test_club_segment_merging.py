from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import patch

import numpy as np

from app.club_detector import (
    create_candidate_diagnostics,
    detect_shaft_candidates,
    merge_collinear_segments,
)


def create_test_search_region() -> dict[str, int]:
    return {
        "xMin": 0,
        "yMin": 0,
        "xMax": 1000,
        "yMax": 800,
        "width": 1000,
        "height": 800,
    }


class ClubSegmentMergingTests(
    unittest.TestCase
):
    def test_merges_nearby_collinear_segments(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [
                [
                    100,
                    100,
                    200,
                    100,
                ],
                [
                    210,
                    100,
                    300,
                    100,
                ],
            ],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            result,
            [
                [
                    100,
                    100,
                    300,
                    100,
                ]
            ],
        )

    def test_merges_segments_with_reversed_endpoint_order(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [
                [
                    200,
                    100,
                    100,
                    100,
                ],
                [
                    300,
                    100,
                    210,
                    100,
                ],
            ],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            len(result),
            1,
        )

        merged = result[0]

        self.assertEqual(
            {
                (merged[0], merged[1]),
                (merged[2], merged[3]),
            },
            {
                (100, 100),
                (300, 100),
            },
        )

    def test_does_not_merge_segments_with_large_angle_change(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [
                [
                    100,
                    100,
                    250,
                    100,
                ],
                [
                    255,
                    100,
                    255,
                    250,
                ],
            ],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_does_not_merge_parallel_segments_that_are_too_far_apart(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [
                [
                    100,
                    100,
                    250,
                    100,
                ],
                [
                    100,
                    160,
                    250,
                    160,
                ],
            ],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_does_not_merge_collinear_segments_with_excessive_gap(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [
                [
                    100,
                    100,
                    200,
                    100,
                ],
                [
                    400,
                    100,
                    500,
                    100,
                ],
            ],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_empty_segment_collection_returns_empty_result(
        self,
    ) -> None:
        result = merge_collinear_segments(
            [],
            frame_width=1000,
            frame_height=800,
        )

        self.assertEqual(
            result,
            [],
        )

    @patch(
        "app.club_detector.cv2.HoughLinesP"
    )
    def test_detector_records_raw_and_merged_line_counts(
        self,
        mock_hough_lines: Any,
    ) -> None:
        mock_hough_lines.return_value = np.array(
            [
                [
                    [
                        100,
                        100,
                        190,
                        100,
                    ]
                ],
                [
                    [
                        195,
                        100,
                        300,
                        100,
                    ]
                ],
            ],
            dtype=np.int32,
        )

        frame = np.zeros(
            (
                800,
                1000,
                3,
            ),
            dtype=np.uint8,
        )

        diagnostics = (
            create_candidate_diagnostics()
        )

        candidates = detect_shaft_candidates(
            frame,
            hand_anchor={
                "x": 100.0,
                "y": 100.0,
            },
            search_region=(
                create_test_search_region()
            ),
            diagnostics=diagnostics,
        )

        self.assertEqual(
            mock_hough_lines.call_count,
            1,
        )

        self.assertEqual(
            len(candidates),
            1,
        )

        self.assertEqual(
            diagnostics[
                "detectionPass"
            ],
            "rectangular_primary",
        )

        self.assertEqual(
            diagnostics[
                "rectangularPrimaryRawHoughLineCount"
            ],
            2,
        )

        self.assertEqual(
            diagnostics[
                "rectangularPrimaryMergedHoughLineCount"
            ],
            1,
        )

        self.assertEqual(
            diagnostics[
                "rawHoughLineCount"
            ],
            2,
        )

        self.assertEqual(
            diagnostics[
                "mergedHoughLineCount"
            ],
            1,
        )

        self.assertEqual(
            diagnostics[
                "segmentMergeCount"
            ],
            1,
        )

        self.assertEqual(
            diagnostics[
                "acceptedCandidateCount"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()