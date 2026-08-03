from __future__ import annotations

import unittest

from app.club_detector import (
    build_candidate_evaluation_diagnostics,
    create_candidate_provenance,
    evaluate_shaft_candidate,
    group_collinear_segments,
)


class ClubCandidateProvenanceTests(unittest.TestCase):
    def test_standard_corridor_primary_receives_positive_adjustment(
        self,
    ) -> None:
        provenance = create_candidate_provenance(
            search_region="corridor",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=1,
        )

        self.assertEqual(
            provenance["searchRegion"],
            "corridor",
        )
        self.assertEqual(
            provenance["edgeSource"],
            "standard",
        )
        self.assertEqual(
            provenance["houghPass"],
            "primary",
        )
        self.assertEqual(
            provenance["segmentSource"],
            "single",
        )
        self.assertGreater(
            provenance["scoreAdjustment"],
            0.0,
        )

    def test_enhanced_fallback_receives_penalty(
        self,
    ) -> None:
        provenance = create_candidate_provenance(
            search_region="corridor",
            edge_source="enhanced",
            hough_pass="fallback",
            source_segment_count=1,
        )

        self.assertLess(
            provenance["scoreAdjustment"],
            0.0,
        )

    def test_rectangular_fallback_is_penalized_more_than_enhanced_fallback(
        self,
    ) -> None:
        enhanced = create_candidate_provenance(
            search_region="corridor",
            edge_source="enhanced",
            hough_pass="fallback",
            source_segment_count=1,
        )

        rectangular = create_candidate_provenance(
            search_region="rectangular",
            edge_source="standard",
            hough_pass="fallback",
            source_segment_count=1,
        )

        self.assertLess(
            rectangular["scoreAdjustment"],
            enhanced["scoreAdjustment"],
        )

    def test_merged_segment_records_source_count_and_bonus(
        self,
    ) -> None:
        single = create_candidate_provenance(
            search_region="corridor",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=1,
        )

        merged = create_candidate_provenance(
            search_region="corridor",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=3,
        )

        self.assertEqual(
            merged["segmentSource"],
            "merged",
        )
        self.assertEqual(
            merged["sourceSegmentCount"],
            3,
        )
        self.assertGreater(
            merged["scoreAdjustment"],
            single["scoreAdjustment"],
        )

    def test_candidate_preserves_base_and_adjusted_image_scores(
        self,
    ) -> None:
        provenance = create_candidate_provenance(
            search_region="corridor",
            edge_source="standard",
            hough_pass="primary",
            source_segment_count=2,
        )

        candidate, reason = evaluate_shaft_candidate(
            [100, 100, 500, 300],
            hand_anchor={
                "x": 105.0,
                "y": 105.0,
            },
            frame_width=1000,
            frame_height=800,
            provenance=provenance,
        )

        self.assertIsNone(reason)
        self.assertIsNotNone(candidate)

        assert candidate is not None

        self.assertEqual(
            candidate["provenance"],
            provenance,
        )
        self.assertGreater(
            candidate["score"],
            candidate["baseImageScore"],
        )

    def test_candidate_diagnostics_include_provenance_and_both_scores(
        self,
    ) -> None:
        provenance = create_candidate_provenance(
            search_region="rectangular",
            edge_source="standard",
            hough_pass="fallback",
            source_segment_count=1,
        )

        candidate, reason = evaluate_shaft_candidate(
            [100, 100, 500, 300],
            hand_anchor={
                "x": 105.0,
                "y": 105.0,
            },
            frame_width=1000,
            frame_height=800,
            provenance=provenance,
        )

        self.assertIsNone(reason)
        self.assertIsNotNone(candidate)

        assert candidate is not None

        record = build_candidate_evaluation_diagnostics(
            candidate,
            index=0,
            temporal_score=0.55,
            angle_change_degrees=10.0,
            distal_shift_ratio=0.05,
            accepted=True,
            selected=True,
        )

        self.assertEqual(
            record["imageScore"],
            candidate["baseImageScore"],
        )
        self.assertEqual(
            record["adjustedImageScore"],
            candidate["score"],
        )
        self.assertEqual(
            record["provenance"],
            provenance,
        )

    def test_grouping_retains_original_segment_membership(
        self,
    ) -> None:
        groups = group_collinear_segments(
            [
                [100, 100, 200, 100],
                [205, 101, 300, 101],
                [100, 300, 200, 400],
            ],
            frame_width=1000,
            frame_height=800,
        )

        group_sizes = sorted(
            len(group)
            for group in groups
        )

        self.assertEqual(
            group_sizes,
            [1, 2],
        )


if __name__ == "__main__":
    unittest.main()