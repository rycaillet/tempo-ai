from __future__ import annotations

from openai import OpenAI

from app.coaching.config import (
    CoachingConfigurationError,
    CoachingSettings,
)
from app.coaching.mock_provider import (
    MockCoachingProvider,
)
from app.coaching.openai_provider import (
    OpenAICoachingProvider,
)
from app.coaching.provider import CoachingProvider


def build_coaching_provider(
    settings: CoachingSettings,
) -> CoachingProvider:
    """
    Build the coaching provider selected by application settings.

    Provider construction is centralized here so callers do not need
    to know which concrete implementation is active.
    """

    if settings.provider_name == "mock":
        return MockCoachingProvider()

    if settings.provider_name == "openai":
        if settings.openai_api_key is None:
            raise CoachingConfigurationError(
                "An OpenAI API key is required to construct "
                "the OpenAI coaching provider."
            )

        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )

        return OpenAICoachingProvider(
            model=settings.openai_model,
            client=client,
        )

    raise CoachingConfigurationError(
        "Cannot construct unsupported coaching provider: "
        f"{settings.provider_name}"
    )


def build_configured_coaching_provider() -> CoachingProvider:
    """
    Build a provider directly from the process environment.
    """

    settings = CoachingSettings.from_environment()

    return build_coaching_provider(settings)