from __future__ import annotations

import unittest
from typing import Any

import numpy as np

from app.club_search_region import (
    build_pose_guided_corridor_mask,
    build_pose_guided_search_region,
    calculate_forearm_direction,
    create_directional_corridor_mask,
    create_search_region_from_direction,
    crop_frame_to_search_region,
    estimate_club_extension_direction,
    normalize_direction,
    translate_coordinates_to_full_frame,
)


def create_test_pose_frame() -> dict[str, Any]:
    return {
        "landmarks": [
            {
                "index": 13,
                "x": 0.50,
                "y": 0.40,
                "visibility": 0.90,
            },
            {
                "index": 15,
                "x": 0.40,
                "y": 0.50,
                "visibility": 0.90,
            },
            {
                "index": 14,
                "x": 0.52,
                "y": 0.42,
                "visibility": 0.90,
            },
            {
                "index": 16,
                "x": 0.42,
                "y": 0.52,
                "visibility": 0.90,
            },
        ]
    }


class ClubSearchRegionTests(
    unittest.TestCase
):
    def test_normalize_direction_returns_unit_vector(
        self,
    ) -> None:
        result = normalize_direction(
            3.0,
            4.0,
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertAlmostEqual(
            result["x"],
            0.6,
        )

        self.assertAlmostEqual(
            result["y"],
            0.8,
        )

    def test_normalize_direction_rejects_zero_vector(
        self,
    ) -> None:
        self.assertIsNone(
            normalize_direction(
                0.0,
                0.0,
            )
        )

    def test_forearm_direction_extends_from_elbow_through_wrist(
        self,
    ) -> None:
        result = calculate_forearm_direction(
            {
                "x": 100.0,
                "y": 100.0,
            },
            {
                "x": 80.0,
                "y": 120.0,
            },
        )

        self.assertIsNotNone(result)

        assert result is not None

        self.assertLess(
            result["x"],
            0.0,
        )

        self.assertGreater(
            result["y"],
            0.0,
        )

    def test_estimates_average_forearm_direction(
        self,
    ) -> None:
        direction = (
            estimate_club_extension_direction(
                create_test_pose_frame(),
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(direction)

        assert direction is not None

        self.assertLess(
            direction["x"],
            0.0,
        )

        self.assertGreater(
            direction["y"],
            0.0,
        )

    def test_estimation_uses_one_reliable_arm(
        self,
    ) -> None:
        pose_frame: dict[str, Any] = {
            "landmarks": [
                {
                    "index": 13,
                    "x": 0.50,
                    "y": 0.40,
                    "visibility": 0.90,
                },
                {
                    "index": 15,
                    "x": 0.40,
                    "y": 0.50,
                    "visibility": 0.90,
                },
                {
                    "index": 14,
                    "x": 0.50,
                    "y": 0.40,
                    "visibility": 0.10,
                },
                {
                    "index": 16,
                    "x": 0.40,
                    "y": 0.50,
                    "visibility": 0.10,
                },
            ]
        }

        direction = (
            estimate_club_extension_direction(
                pose_frame,
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(direction)

    def test_estimation_returns_none_without_reliable_forearms(
        self,
    ) -> None:
        pose_frame: dict[str, Any] = {
            "landmarks": []
        }

        direction = (
            estimate_club_extension_direction(
                pose_frame,
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNone(direction)

    def test_search_region_extends_in_expected_direction(
        self,
    ) -> None:
        region = (
            create_search_region_from_direction(
                hand_anchor={
                    "x": 500.0,
                    "y": 250.0,
                },
                direction={
                    "x": -1.0,
                    "y": 0.0,
                },
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(region)

        assert region is not None

        left_distance = (
            500 - region["xMin"]
        )

        right_distance = (
            region["xMax"] - 500
        )

        self.assertGreater(
            left_distance,
            right_distance,
        )

    def test_search_region_clamps_to_frame_boundaries(
        self,
    ) -> None:
        region = (
            create_search_region_from_direction(
                hand_anchor={
                    "x": 20.0,
                    "y": 20.0,
                },
                direction={
                    "x": -1.0,
                    "y": -1.0,
                },
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(region)

        assert region is not None

        self.assertEqual(
            region["xMin"],
            0,
        )

        self.assertEqual(
            region["yMin"],
            0,
        )

        self.assertLessEqual(
            region["xMax"],
            1000,
        )

        self.assertLessEqual(
            region["yMax"],
            500,
        )

    def test_builds_region_from_pose_and_hand_anchor(
        self,
    ) -> None:
        region = (
            build_pose_guided_search_region(
                create_test_pose_frame(),
                hand_anchor={
                    "x": 410.0,
                    "y": 255.0,
                },
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(region)

    def test_directional_corridor_mask_matches_search_region_dimensions(
        self,
    ) -> None:
        search_region = {
            "xMin": 100,
            "yMin": 50,
            "xMax": 600,
            "yMax": 350,
            "width": 500,
            "height": 300,
        }

        mask = create_directional_corridor_mask(
            search_region=search_region,
            hand_anchor={
                "x": 300.0,
                "y": 200.0,
            },
            direction={
                "x": 1.0,
                "y": 0.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        self.assertEqual(
            mask.shape,
            (
                search_region["height"],
                search_region["width"],
            ),
        )

        self.assertEqual(
            mask.dtype,
            np.uint8,
        )

    def test_directional_corridor_mask_contains_hand_anchor(
        self,
    ) -> None:
        search_region = {
            "xMin": 100,
            "yMin": 50,
            "xMax": 700,
            "yMax": 450,
            "width": 600,
            "height": 400,
        }

        hand_anchor = {
            "x": 300.0,
            "y": 200.0,
        }

        mask = create_directional_corridor_mask(
            search_region=search_region,
            hand_anchor=hand_anchor,
            direction={
                "x": 1.0,
                "y": 0.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        local_x = int(
            round(
                hand_anchor["x"]
                - search_region["xMin"]
            )
        )

        local_y = int(
            round(
                hand_anchor["y"]
                - search_region["yMin"]
            )
        )

        self.assertEqual(
            mask[local_y, local_x],
            255,
        )

    def test_directional_corridor_extends_forward_from_hands(
        self,
    ) -> None:
        search_region = {
            "xMin": 0,
            "yMin": 0,
            "xMax": 1000,
            "yMax": 500,
            "width": 1000,
            "height": 500,
        }

        mask = create_directional_corridor_mask(
            search_region=search_region,
            hand_anchor={
                "x": 500.0,
                "y": 250.0,
            },
            direction={
                "x": -1.0,
                "y": 0.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        active_y, active_x = np.nonzero(mask)

        self.assertGreater(
            len(active_x),
            0,
        )

        left_extent = (
            500 - int(active_x.min())
        )

        right_extent = (
            int(active_x.max()) - 500
        )

        self.assertGreater(
            left_extent,
            right_extent,
        )

    def test_directional_corridor_suppresses_pixels_outside_corridor(
        self,
    ) -> None:
        search_region = {
            "xMin": 0,
            "yMin": 0,
            "xMax": 1000,
            "yMax": 500,
            "width": 1000,
            "height": 500,
        }

        mask = create_directional_corridor_mask(
            search_region=search_region,
            hand_anchor={
                "x": 500.0,
                "y": 250.0,
            },
            direction={
                "x": 1.0,
                "y": 0.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        self.assertEqual(
            mask[250, 600],
            255,
        )

        self.assertEqual(
            mask[20, 600],
            0,
        )

    def test_directional_corridor_supports_diagonal_direction(
        self,
    ) -> None:
        search_region = {
            "xMin": 0,
            "yMin": 0,
            "xMax": 1000,
            "yMax": 800,
            "width": 1000,
            "height": 800,
        }

        mask = create_directional_corridor_mask(
            search_region=search_region,
            hand_anchor={
                "x": 300.0,
                "y": 300.0,
            },
            direction={
                "x": 1.0,
                "y": 1.0,
            },
            frame_width=1000,
            frame_height=800,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        self.assertEqual(
            mask[400, 400],
            255,
        )

        self.assertEqual(
            mask[100, 700],
            0,
        )

    def test_directional_corridor_rejects_zero_direction(
        self,
    ) -> None:
        mask = create_directional_corridor_mask(
            search_region={
                "xMin": 0,
                "yMin": 0,
                "xMax": 500,
                "yMax": 300,
                "width": 500,
                "height": 300,
            },
            hand_anchor={
                "x": 250.0,
                "y": 150.0,
            },
            direction={
                "x": 0.0,
                "y": 0.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNone(mask)

    def test_directional_corridor_rejects_invalid_frame_dimensions(
        self,
    ) -> None:
        mask = create_directional_corridor_mask(
            search_region={
                "xMin": 0,
                "yMin": 0,
                "xMax": 500,
                "yMax": 300,
                "width": 500,
                "height": 300,
            },
            hand_anchor={
                "x": 250.0,
                "y": 150.0,
            },
            direction={
                "x": 1.0,
                "y": 0.0,
            },
            frame_width=0,
            frame_height=500,
        )

        self.assertIsNone(mask)

    def test_builds_pose_guided_corridor_mask(
        self,
    ) -> None:
        pose_frame = create_test_pose_frame()

        hand_anchor = {
            "x": 410.0,
            "y": 255.0,
        }

        search_region = (
            build_pose_guided_search_region(
                pose_frame,
                hand_anchor=hand_anchor,
                frame_width=1000,
                frame_height=500,
            )
        )

        self.assertIsNotNone(search_region)

        assert search_region is not None

        mask = build_pose_guided_corridor_mask(
            pose_frame,
            search_region=search_region,
            hand_anchor=hand_anchor,
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNotNone(mask)

        assert mask is not None

        self.assertEqual(
            mask.shape,
            (
                search_region["height"],
                search_region["width"],
            ),
        )

        self.assertGreater(
            int(np.count_nonzero(mask)),
            0,
        )

    def test_pose_guided_corridor_returns_none_without_forearms(
        self,
    ) -> None:
        mask = build_pose_guided_corridor_mask(
            {
                "landmarks": [],
            },
            search_region={
                "xMin": 0,
                "yMin": 0,
                "xMax": 500,
                "yMax": 300,
                "width": 500,
                "height": 300,
            },
            hand_anchor={
                "x": 250.0,
                "y": 150.0,
            },
            frame_width=1000,
            frame_height=500,
        )

        self.assertIsNone(mask)

    def test_crop_uses_search_region_bounds(
        self,
    ) -> None:
        frame = np.zeros(
            (300, 400, 3),
            dtype=np.uint8,
        )

        cropped = crop_frame_to_search_region(
            frame,
            {
                "xMin": 100,
                "yMin": 50,
                "xMax": 300,
                "yMax": 250,
                "width": 200,
                "height": 200,
            },
        )

        self.assertEqual(
            cropped.shape,
            (200, 200, 3),
        )

    def test_crop_rejects_empty_frame(
        self,
    ) -> None:
        frame = np.empty(
            (0, 0, 3),
            dtype=np.uint8,
        )

        with self.assertRaisesRegex(
            ValueError,
            "empty frame",
        ):
            crop_frame_to_search_region(
                frame,
                {
                    "xMin": 0,
                    "yMin": 0,
                    "xMax": 10,
                    "yMax": 10,
                    "width": 10,
                    "height": 10,
                },
            )

    def test_translates_local_coordinates_to_full_frame(
        self,
    ) -> None:
        result = (
            translate_coordinates_to_full_frame(
                [10, 20, 100, 120],
                search_region={
                    "xMin": 200,
                    "yMin": 50,
                    "xMax": 500,
                    "yMax": 300,
                    "width": 300,
                    "height": 250,
                },
            )
        )

        self.assertEqual(
            result,
            [
                210,
                70,
                300,
                170,
            ],
        )

    def test_translation_rejects_invalid_coordinate_count(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "four values",
        ):
            translate_coordinates_to_full_frame(
                [1, 2, 3],
                search_region={
                    "xMin": 0,
                    "yMin": 0,
                    "xMax": 100,
                    "yMax": 100,
                    "width": 100,
                    "height": 100,
                },
            )


if __name__ == "__main__":
    unittest.main()