from __future__ import annotations

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)
from app.coaching.provider import (
    CoachingProvider,
    CoachingProviderError,
)


def append_unique(
    values: list[str],
    value: str,
) -> None:
    """
    Append a warning only when it is not already present.
    """

    if value not in values:
        values.append(value)


def build_unavailable_response(
    *,
    warnings: tuple[str, ...],
) -> CoachResponse:
    """
    Build a stable response when coaching cannot be generated.
    """

    return CoachResponse(
        status="not_available",
        headline=None,
        overview=None,
        primary_focus=None,
        action_steps=(),
        encouragement=None,
        disclaimer=None,
        warnings=warnings,
    )


def generate_coaching_response(
    *,
    context: CoachContext,
    provider: CoachingProvider,
) -> CoachResponse:
    """
    Generate coaching through a provider-independent service boundary.

    The service prevents providers from receiving unavailable context,
    converts provider failures into stable application responses, and
    validates the response contract before returning it.
    """

    warnings = list(context.warnings)

    if context.status != "ready":
        append_unique(
            warnings,
            "coach_context_not_ready",
        )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )

    if not context.priorities:
        append_unique(
            warnings,
            "coach_context_has_no_priorities",
        )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )

    try:
        response = provider.generate(context)
    except CoachingProviderError:
        append_unique(
            warnings,
            "coaching_provider_error",
        )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )
    except Exception:
        append_unique(
            warnings,
            "unexpected_coaching_provider_error",
        )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )

    if not isinstance(response, CoachResponse):
        append_unique(
            warnings,
            "invalid_coaching_provider_response",
        )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )

    if response.status != "ready":
        append_unique(
            warnings,
            "coaching_provider_response_not_ready",
        )

        for warning in response.warnings:
            append_unique(
                warnings,
                warning,
            )

        return build_unavailable_response(
            warnings=tuple(warnings),
        )

    for warning in response.warnings:
        append_unique(
            warnings,
            warning,
        )

    return CoachResponse(
        status=response.status,
        headline=response.headline,
        overview=response.overview,
        primary_focus=response.primary_focus,
        action_steps=response.action_steps,
        encouragement=response.encouragement,
        disclaimer=response.disclaimer,
        warnings=tuple(warnings),
    )