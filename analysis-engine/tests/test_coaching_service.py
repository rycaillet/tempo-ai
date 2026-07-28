from __future__ import annotations

import unittest

from app.coaching import (
    CoachContext,
    CoachPriority,
    CoachResponse,
    CoachingProviderError,
    MockCoachingProvider,
    generate_coaching_response,
)


class FailingProvider:
    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        raise CoachingProviderError(
            "Provider failure"
        )


class UnexpectedFailingProvider:
    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        raise RuntimeError(
            "Unexpected provider failure"
        )


class InvalidProvider:
    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        return "invalid"  # type: ignore[return-value]


class NotReadyProvider:
    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        return CoachResponse(
            status="not_available",
            headline=None,
            overview=None,
            primary_focus=None,
            action_steps=(),
            encouragement=None,
            disclaimer=None,
            warnings=("provider_not_ready",),
        )


class CoachingServiceTests(unittest.TestCase):
    @staticmethod
    def build_context(
        *,
        status: str = "ready",
        include_priorities: bool = True,
    ) -> CoachContext:
        priorities = (
            (
                CoachPriority(
                    metric_key="addressPosture",
                    display_name="Address posture",
                    severity="high",
                    priority=1,
                    title="Improve address posture",
                    summary="Create a more balanced setup.",
                    focus="Balanced setup posture",
                    rationale=(
                        "Setup influences the motion that follows."
                    ),
                    practice_cues=(
                        "Balance over the middle of the feet.",
                    ),
                    caution=None,
                ),
            )
            if include_priorities
            else ()
        )

        return CoachContext(
            status=status,
            overall_score=80.0,
            score_confidence=90.0,
            score_coverage=85.0,
            rating="good",
            rating_label="Good",
            analysis_summary="Solid measured fundamentals.",
            overall_finding=(
                "Address posture is the primary focus."
            ),
            primary_focus_metric_key=(
                "addressPosture"
                if include_priorities
                else None
            ),
            strengths=(),
            priorities=priorities,
            warnings=("existing_warning",),
            limitations=(),
        )

    def test_service_generates_response_with_mock_provider(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(),
            provider=MockCoachingProvider(),
        )

        self.assertEqual(response.status, "ready")
        self.assertIsNotNone(response.headline)
        self.assertIsNotNone(response.overview)
        self.assertEqual(
            response.warnings,
            ("existing_warning",),
        )

    def test_service_rejects_unavailable_context(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(
                status="not_available",
            ),
            provider=MockCoachingProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "coach_context_not_ready",
            response.warnings,
        )

    def test_service_rejects_context_without_priorities(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(
                include_priorities=False,
            ),
            provider=MockCoachingProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "coach_context_has_no_priorities",
            response.warnings,
        )

    def test_service_handles_provider_error(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(),
            provider=FailingProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "coaching_provider_error",
            response.warnings,
        )

    def test_service_handles_unexpected_provider_error(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(),
            provider=UnexpectedFailingProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "unexpected_coaching_provider_error",
            response.warnings,
        )

    def test_service_rejects_invalid_provider_response(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(),
            provider=InvalidProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "invalid_coaching_provider_response",
            response.warnings,
        )

    def test_service_handles_not_ready_provider_response(
        self,
    ) -> None:
        response = generate_coaching_response(
            context=self.build_context(),
            provider=NotReadyProvider(),
        )

        self.assertEqual(
            response.status,
            "not_available",
        )
        self.assertIn(
            "coaching_provider_response_not_ready",
            response.warnings,
        )
        self.assertIn(
            "provider_not_ready",
            response.warnings,
        )


if __name__ == "__main__":
    unittest.main()