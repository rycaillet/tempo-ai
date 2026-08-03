from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import patch

import numpy as np

from app.club_detector import (
    build_enhanced_corridor_edges,
    calculate_adaptive_canny_thresholds,
    create_candidate_diagnostics,
    detect_shaft_candidates,
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


def create_full_corridor_mask() -> np.ndarray:
    return np.full(
        (800, 1000),
        255,
        dtype=np.uint8,
    )


class AdaptiveShaftEdgeEnhancementTests(
    unittest.TestCase
):
    def test_adaptive_thresholds_follow_local_median(
        self,
    ) -> None:
        grayscale = np.full(
            (20, 20),
            100,
            dtype=np.uint8,
        )

        low_threshold, high_threshold = (
            calculate_adaptive_canny_thresholds(
                grayscale
            )
        )

        self.assertEqual(
            low_threshold,
            67,
        )
        self.assertEqual(
            high_threshold,
            133,
        )

    def test_adaptive_thresholds_respect_minimums_for_dark_image(
        self,
    ) -> None:
        grayscale = np.zeros(
            (20, 20),
            dtype=np.uint8,
        )

        low_threshold, high_threshold = (
            calculate_adaptive_canny_thresholds(
                grayscale
            )
        )

        self.assertEqual(
            low_threshold,
            10,
        )
        self.assertEqual(
            high_threshold,
            30,
        )

    def test_adaptive_thresholds_use_only_masked_pixels(
        self,
    ) -> None:
        grayscale = np.full(
            (20, 20),
            200,
            dtype=np.uint8,
        )
        grayscale[:, :10] = 60

        mask = np.zeros(
            (20, 20),
            dtype=np.uint8,
        )
        mask[:, :10] = 255

        low_threshold, high_threshold = (
            calculate_adaptive_canny_thresholds(
                grayscale,
                mask=mask,
            )
        )

        self.assertEqual(
            low_threshold,
            40,
        )
        self.assertEqual(
            high_threshold,
            80,
        )

    def test_enhanced_edges_remain_inside_corridor_mask(
        self,
    ) -> None:
        grayscale = np.zeros(
            (100, 100),
            dtype=np.uint8,
        )
        grayscale[:, 50:] = 180

        mask = np.zeros(
            (100, 100),
            dtype=np.uint8,
        )
        mask[:, :60] = 255

        edges, low_threshold, high_threshold = (
            build_enhanced_corridor_edges(
                grayscale,
                corridor_mask=mask,
            )
        )

        self.assertEqual(
            edges.shape,
            grayscale.shape,
        )
        self.assertEqual(
            edges.dtype,
            np.uint8,
        )
        self.assertGreater(
            high_threshold,
            low_threshold,
        )
        self.assertEqual(
            int(np.count_nonzero(
                edges[mask == 0]
            )),
            0,
        )

    @patch(
        "app.club_detector.cv2.HoughLinesP"
    )
    def test_enhanced_primary_runs_after_standard_corridor_passes_fail(
        self,
        mock_hough_lines: Any,
    ) -> None:
        mock_hough_lines.side_effect = [
            None,
            None,
            np.array(
                [
                    [
                        [
                            100,
                            100,
                            500,
                            300,
                        ]
                    ]
                ],
                dtype=np.int32,
            ),
        ]

        frame = np.zeros(
            (800, 1000, 3),
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
            corridor_mask=(
                create_full_corridor_mask()
            ),
            diagnostics=diagnostics,
        )

        self.assertEqual(
            mock_hough_lines.call_count,
            3,
        )
        self.assertEqual(
            len(candidates),
            1,
        )
        self.assertTrue(
            diagnostics[
                "enhancedEdgeAttempted"
            ]
        )
        self.assertEqual(
            diagnostics["detectionPass"],
            "corridor_enhanced_primary",
        )
        self.assertIsNotNone(
            diagnostics[
                "adaptiveCannyLowThreshold"
            ]
        )
        self.assertIsNotNone(
            diagnostics[
                "adaptiveCannyHighThreshold"
            ]
        )
        self.assertEqual(
            diagnostics[
                "enhancedCorridorPrimaryRawHoughLineCount"
            ],
            1,
        )
        self.assertEqual(
            diagnostics[
                "acceptedCandidateCount"
            ],
            1,
        )

    @patch(
        "app.club_detector.cv2.HoughLinesP"
    )
    def test_standard_corridor_success_skips_enhanced_edges(
        self,
        mock_hough_lines: Any,
    ) -> None:
        mock_hough_lines.return_value = np.array(
            [
                [
                    [
                        100,
                        100,
                        500,
                        300,
                    ]
                ]
            ],
            dtype=np.int32,
        )

        frame = np.zeros(
            (800, 1000, 3),
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
            corridor_mask=(
                create_full_corridor_mask()
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
        self.assertFalse(
            diagnostics[
                "enhancedEdgeAttempted"
            ]
        )
        self.assertEqual(
            diagnostics["detectionPass"],
            "corridor_primary",
        )
        self.assertIsNone(
            diagnostics[
                "adaptiveCannyLowThreshold"
            ]
        )
        self.assertIsNone(
            diagnostics[
                "adaptiveCannyHighThreshold"
            ]
        )

    @patch(
        "app.club_detector.cv2.HoughLinesP"
    )
    def test_rectangular_fallback_runs_after_enhanced_passes_fail(
        self,
        mock_hough_lines: Any,
    ) -> None:
        mock_hough_lines.side_effect = [
            None,
            None,
            None,
            None,
            np.array(
                [
                    [
                        [
                            100,
                            100,
                            500,
                            300,
                        ]
                    ]
                ],
                dtype=np.int32,
            ),
        ]

        frame = np.zeros(
            (800, 1000, 3),
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
            corridor_mask=(
                create_full_corridor_mask()
            ),
            diagnostics=diagnostics,
        )

        self.assertEqual(
            mock_hough_lines.call_count,
            5,
        )
        self.assertEqual(
            len(candidates),
            1,
        )
        self.assertTrue(
            diagnostics[
                "enhancedEdgeAttempted"
            ]
        )
        self.assertEqual(
            diagnostics["detectionPass"],
            "rectangular_primary",
        )
        self.assertEqual(
            diagnostics[
                "enhancedCorridorPrimaryRawHoughLineCount"
            ],
            0,
        )
        self.assertEqual(
            diagnostics[
                "enhancedCorridorFallbackRawHoughLineCount"
            ],
            0,
        )
        self.assertEqual(
            diagnostics[
                "rectangularPrimaryRawHoughLineCount"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()