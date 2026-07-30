from __future__ import annotations

import unittest
from typing import Any

from app.club_frame_window import (
    DEFAULT_WINDOW_RADIUS_FRAMES,
    build_dense_club_frame_requests,
    build_reference_phase_frames,
)


class ClubFrameWindowTests(
    unittest.TestCase
):
    def test_default_window_radius_is_two_frames(
        self,
    ) -> None:
        self.assertEqual(
            DEFAULT_WINDOW_RADIUS_FRAMES,
            2,
        )

    def test_builds_reference_phase_frame_model(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 20,
                    "timestampSeconds": 0.667,
                },
            ),
            (
                "takeaway",
                {
                    "frameIndex": 30,
                    "timestampSeconds": 1.0,
                },
            ),
        ]

        result = build_reference_phase_frames(
            reference_phases
        )

        self.assertEqual(
            result,
            [
                {
                    "phase": "address",
                    "frameIndex": 20,
                },
                {
                    "phase": "takeaway",
                    "frameIndex": 30,
                },
            ],
        )

    def test_builds_dense_window_around_reference_frame(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 20,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=100,
            window_radius_frames=2,
        )

        self.assertEqual(
            [
                request["frameIndex"]
                for request in result
            ],
            [
                18,
                19,
                20,
                21,
                22,
            ],
        )

        self.assertEqual(
            [
                request["phaseOffsetFrames"]
                for request in result
            ],
            [
                -2,
                -1,
                0,
                1,
                2,
            ],
        )

    def test_preserves_reference_frame_relationship(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "impactReference",
                {
                    "frameIndex": 50,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=100,
            window_radius_frames=1,
        )

        self.assertEqual(
            result,
            [
                {
                    "phase": "impactReference",
                    "referenceFrameIndex": 50,
                    "frameIndex": 49,
                    "phaseOffsetFrames": -1,
                    "isReferenceFrame": False,
                },
                {
                    "phase": "impactReference",
                    "referenceFrameIndex": 50,
                    "frameIndex": 50,
                    "phaseOffsetFrames": 0,
                    "isReferenceFrame": True,
                },
                {
                    "phase": "impactReference",
                    "referenceFrameIndex": 50,
                    "frameIndex": 51,
                    "phaseOffsetFrames": 1,
                    "isReferenceFrame": False,
                },
            ],
        )

    def test_clips_window_to_available_frame_range(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 1,
                },
            ),
            (
                "finishReference",
                {
                    "frameIndex": 9,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=10,
            window_radius_frames=3,
        )

        self.assertEqual(
            [
                request["frameIndex"]
                for request in result
            ],
            [
                0,
                1,
                2,
                3,
                4,
                6,
                7,
                8,
                9,
                10,
            ],
        )

    def test_overlapping_windows_process_each_frame_once(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 10,
                },
            ),
            (
                "takeaway",
                {
                    "frameIndex": 12,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=20,
            window_radius_frames=2,
        )

        frame_indices = [
            request["frameIndex"]
            for request in result
        ]

        self.assertEqual(
            frame_indices,
            [
                8,
                9,
                10,
                11,
                12,
                13,
                14,
            ],
        )

        self.assertEqual(
            len(frame_indices),
            len(set(frame_indices)),
        )

    def test_overlap_is_owned_by_nearest_reference_phase(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 10,
                },
            ),
            (
                "takeaway",
                {
                    "frameIndex": 13,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=20,
            window_radius_frames=3,
        )

        requests_by_frame = {
            request["frameIndex"]: request
            for request in result
        }

        self.assertEqual(
            requests_by_frame[11]["phase"],
            "address",
        )

        self.assertEqual(
            requests_by_frame[12]["phase"],
            "takeaway",
        )

        self.assertEqual(
            requests_by_frame[12][
                "referenceFrameIndex"
            ],
            13,
        )

    def test_equal_distance_overlap_uses_earlier_phase(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "topOfBackswing",
                {
                    "frameIndex": 20,
                },
            ),
            (
                "downswingStart",
                {
                    "frameIndex": 22,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=40,
            window_radius_frames=2,
        )

        requests_by_frame = {
            request["frameIndex"]: request
            for request in result
        }

        self.assertEqual(
            requests_by_frame[21]["phase"],
            "topOfBackswing",
        )

        self.assertEqual(
            requests_by_frame[21][
                "referenceFrameIndex"
            ],
            20,
        )

    def test_returns_frames_in_chronological_order(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "finishReference",
                {
                    "frameIndex": 40,
                },
            ),
            (
                "address",
                {
                    "frameIndex": 10,
                },
            ),
            (
                "impactReference",
                {
                    "frameIndex": 30,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=50,
            window_radius_frames=1,
        )

        frame_indices = [
            request["frameIndex"]
            for request in result
        ]

        self.assertEqual(
            frame_indices,
            sorted(frame_indices),
        )

    def test_zero_radius_preserves_sparse_reference_behavior(
        self,
    ) -> None:
        reference_phases: list[
            tuple[str, dict[str, Any]]
        ] = [
            (
                "address",
                {
                    "frameIndex": 10,
                },
            ),
            (
                "takeaway",
                {
                    "frameIndex": 20,
                },
            ),
        ]

        result = build_dense_club_frame_requests(
            reference_phases,
            minimum_frame_index=0,
            maximum_frame_index=30,
            window_radius_frames=0,
        )

        self.assertEqual(
            [
                request["frameIndex"]
                for request in result
            ],
            [
                10,
                20,
            ],
        )

        self.assertTrue(
            all(
                request["isReferenceFrame"]
                for request in result
            )
        )

    def test_rejects_negative_window_radius(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "cannot be negative",
        ):
            build_dense_club_frame_requests(
                [
                    (
                        "address",
                        {
                            "frameIndex": 10,
                        },
                    ),
                ],
                minimum_frame_index=0,
                maximum_frame_index=20,
                window_radius_frames=-1,
            )

    def test_rejects_invalid_frame_range(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "greater than or equal",
        ):
            build_dense_club_frame_requests(
                [
                    (
                        "address",
                        {
                            "frameIndex": 10,
                        },
                    ),
                ],
                minimum_frame_index=20,
                maximum_frame_index=10,
            )

    def test_rejects_empty_reference_phase_sequence(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "At least one reference phase",
        ):
            build_dense_club_frame_requests(
                [],
                minimum_frame_index=0,
                maximum_frame_index=20,
            )

    def test_rejects_reference_without_frame_index(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "valid frame index",
        ):
            build_dense_club_frame_requests(
                [
                    (
                        "address",
                        {},
                    ),
                ],
                minimum_frame_index=0,
                maximum_frame_index=20,
            )

    def test_rejects_window_entirely_outside_frame_range(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "did not contain any frames",
        ):
            build_dense_club_frame_requests(
                [
                    (
                        "address",
                        {
                            "frameIndex": 100,
                        },
                    ),
                ],
                minimum_frame_index=0,
                maximum_frame_index=20,
                window_radius_frames=2,
            )


if __name__ == "__main__":
    unittest.main()