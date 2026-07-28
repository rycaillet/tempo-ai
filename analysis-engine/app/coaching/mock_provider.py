from __future__ import annotations

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)
from app.coaching.provider import (
    CoachingProviderError,
)


class MockCoachingProvider:
    """
    Deterministic coaching provider used for development and testing.

    It proves the provider architecture without requiring networking,
    API credentials, token usage, or nondeterministic LLM output.
    """

    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        if context.status != "ready":
            raise CoachingProviderError(
                "Coach context must be ready before generation."
            )

        if not context.priorities:
            raise CoachingProviderError(
                "Coach context does not contain a coaching priority."
            )

        primary_priority = context.priorities[0]

        headline = (
            f"Focus first on {primary_priority.display_name.lower()}"
        )

        overview = self.build_overview(context)

        primary_focus = (
            f"{primary_priority.summary} "
            f"The main goal is {primary_priority.focus.lower()}."
        )

        action_steps = self.build_action_steps(
            context=context,
        )

        encouragement = self.build_encouragement(
            context=context,
        )

        disclaimer = self.build_disclaimer(
            context=context,
        )

        return CoachResponse(
            status="ready",
            headline=headline,
            overview=overview,
            primary_focus=primary_focus,
            action_steps=action_steps,
            encouragement=encouragement,
            disclaimer=disclaimer,
            warnings=context.warnings,
        )

    @staticmethod
    def build_overview(
        context: CoachContext,
    ) -> str:
        if context.analysis_summary is not None:
            return context.analysis_summary

        if context.overall_finding is not None:
            return context.overall_finding

        if context.rating_label is not None:
            return (
                f"The measured swing received an overall "
                f"{context.rating_label.lower()} rating."
            )

        return (
            "The swing analysis produced measurable coaching "
            "opportunities."
        )

    @staticmethod
    def build_action_steps(
        *,
        context: CoachContext,
    ) -> tuple[str, ...]:
        primary_priority = context.priorities[0]

        action_steps = list(
            primary_priority.practice_cues
        )

        if not action_steps:
            action_steps.append(
                primary_priority.focus
            )

        return tuple(action_steps)

    @staticmethod
    def build_encouragement(
        *,
        context: CoachContext,
    ) -> str:
        if context.strengths:
            strongest_metric = context.strengths[0]

            return (
                f"Keep building on your "
                f"{strongest_metric.display_name.lower()} while "
                f"working on the primary focus."
            )

        return (
            "Work on the primary focus gradually and compare future "
            "swings for measurable progress."
        )

    @staticmethod
    def build_disclaimer(
        *,
        context: CoachContext,
    ) -> str:
        base_disclaimer = (
            "This coaching is generated from video-based pose "
            "analysis and should be treated as practice guidance, "
            "not a substitute for an in-person golf professional."
        )

        if not context.limitations:
            return base_disclaimer

        return (
            f"{base_disclaimer} "
            f"Analysis limitation: {context.limitations[0]}"
        )