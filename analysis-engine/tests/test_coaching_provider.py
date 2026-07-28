from __future__ import annotations

import unittest

from app.coaching import (
    CoachContext,
    CoachPriority,
    CoachStrength,
    CoachingProvider,
    CoachingProviderError,
    MockCoachingProvider,
)


class CoachingProviderTests(unittest.TestCase):
    @staticmethod
    def build_context(
        *,
        status: str = "ready",
        include_priorities: bool = True,
    ) -> CoachContext:
        priorities = (
            (
                CoachPriority(
                    metric_key="weightShift",
                    display_name="Weight shift",
                    severity="high",
                    priority=1,
                    title="Improve pressure transfer",
                    summary=(
                        "Coordinate movement toward the lead side."
                    ),
                    focus="Lower-body pressure transfer",
                    rationale=(
                        "Efficient transfer supports sequencing."
                    ),
                    practice_cues=(
                        "Finish balanced on the lead side.",
                        "Rehearse the transition slowly.",
                    ),
                    caution=(
                        "Pose landmarks do not directly measure "
                        "pressure."
                    ),
                ),
            )
            if include_priorities
            else ()
        )

        return CoachContext(
            status=status,
            overall_score=82.0,
            score_confidence=94.0,
            score_coverage=88.0,
            rating="good",
            rating_label="Good",
            analysis_summary=(
                "The swing demonstrates solid measured "
                "fundamentals."
            ),
            overall_finding=(
                "Weight shift is the primary improvement area."
            ),
            primary_focus_metric_key=(
                "weightShift"
                if include_priorities
                else None
            ),
            strengths=(
                CoachStrength(
                    metric_key="headStability",
                    display_name="Head stability",
                    score=96.0,
                    reason="Strong measured stability.",
                ),
            ),
            priorities=priorities,
            warnings=("limited_metric_coverage",),
            limitations=(
                "Pose landmarks do not directly measure pressure.",
            ),
        )

    def test_mock_provider_satisfies_provider_protocol(
        self,
    ) -> None:
        provider = MockCoachingProvider()

        self.assertIsInstance(
            provider,
            CoachingProvider,
        )

    def test_mock_provider_generates_ready_response(
        self,
    ) -> None:
        provider = MockCoachingProvider()

        response = provider.generate(
            self.build_context()
        )

        self.assertEqual(response.status, "ready")
        self.assertEqual(
            response.headline,
            "Focus first on weight shift",
        )
        self.assertIn(
            "Coordinate movement toward the lead side.",
            response.primary_focus or "",
        )
        self.assertEqual(
            response.action_steps,
            (
                "Finish balanced on the lead side.",
                "Rehearse the transition slowly.",
            ),
        )
        self.assertIn(
            "head stability",
            response.encouragement or "",
        )
        self.assertIn(
            "video-based pose analysis",
            response.disclaimer or "",
        )
        self.assertEqual(
            response.warnings,
            ("limited_metric_coverage",),
        )

    def test_mock_provider_rejects_unavailable_context(
        self,
    ) -> None:
        provider = MockCoachingProvider()

        with self.assertRaises(
            CoachingProviderError
        ):
            provider.generate(
                self.build_context(
                    status="not_available",
                )
            )

    def test_mock_provider_rejects_missing_priorities(
        self,
    ) -> None:
        provider = MockCoachingProvider()

        with self.assertRaises(
            CoachingProviderError
        ):
            provider.generate(
                self.build_context(
                    include_priorities=False,
                )
            )


if __name__ == "__main__":
    unittest.main()