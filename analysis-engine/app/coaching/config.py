from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field


DEFAULT_COACHING_PROVIDER = "mock"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_OPENAI_MAX_RETRIES = 2

SUPPORTED_COACHING_PROVIDERS = frozenset(
    {
        "mock",
        "openai",
    }
)


class CoachingConfigurationError(ValueError):
    """
    Raised when coaching provider configuration is invalid.
    """


def parse_positive_float(
    *,
    raw_value: str | None,
    default: float,
    variable_name: str,
) -> float:
    if raw_value is None:
        return default

    try:
        value = float(raw_value.strip())
    except (AttributeError, ValueError) as error:
        raise CoachingConfigurationError(
            f"{variable_name} must be a positive number."
        ) from error

    if not math.isfinite(value) or value <= 0.0:
        raise CoachingConfigurationError(
            f"{variable_name} must be a positive number."
        )

    return value


def parse_nonnegative_integer(
    *,
    raw_value: str | None,
    default: int,
    variable_name: str,
) -> int:
    if raw_value is None:
        return default

    try:
        value = int(raw_value.strip())
    except (AttributeError, ValueError) as error:
        raise CoachingConfigurationError(
            f"{variable_name} must be a non-negative integer."
        ) from error

    if value < 0:
        raise CoachingConfigurationError(
            f"{variable_name} must be a non-negative integer."
        )

    return value


@dataclass(frozen=True)
class CoachingSettings:
    """
    Environment-derived settings for selecting a coaching provider.

    The API key is excluded from the dataclass representation so it
    cannot be exposed accidentally through logs or debugging output.
    """

    provider_name: str
    openai_model: str
    openai_api_key: str | None = field(
        default=None,
        repr=False,
    )
    openai_timeout_seconds: float = (
        DEFAULT_OPENAI_TIMEOUT_SECONDS
    )
    openai_max_retries: int = (
        DEFAULT_OPENAI_MAX_RETRIES
    )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> CoachingSettings:
        """
        Build validated coaching settings from environment variables.

        Supported variables:

        TEMPOAI_COACHING_PROVIDER
        TEMPOAI_OPENAI_MODEL
        TEMPOAI_OPENAI_TIMEOUT_SECONDS
        TEMPOAI_OPENAI_MAX_RETRIES
        OPENAI_API_KEY
        """

        source = (
            environment
            if environment is not None
            else os.environ
        )

        provider_name = source.get(
            "TEMPOAI_COACHING_PROVIDER",
            DEFAULT_COACHING_PROVIDER,
        ).strip().lower()

        if provider_name not in SUPPORTED_COACHING_PROVIDERS:
            supported_values = ", ".join(
                sorted(SUPPORTED_COACHING_PROVIDERS)
            )

            raise CoachingConfigurationError(
                "Unsupported coaching provider "
                f"'{provider_name}'. Supported providers: "
                f"{supported_values}."
            )

        openai_model = source.get(
            "TEMPOAI_OPENAI_MODEL",
            DEFAULT_OPENAI_MODEL,
        ).strip()

        if not openai_model:
            raise CoachingConfigurationError(
                "TEMPOAI_OPENAI_MODEL must be a nonempty string."
            )

        openai_timeout_seconds = parse_positive_float(
            raw_value=source.get(
                "TEMPOAI_OPENAI_TIMEOUT_SECONDS"
            ),
            default=DEFAULT_OPENAI_TIMEOUT_SECONDS,
            variable_name=(
                "TEMPOAI_OPENAI_TIMEOUT_SECONDS"
            ),
        )

        openai_max_retries = parse_nonnegative_integer(
            raw_value=source.get(
                "TEMPOAI_OPENAI_MAX_RETRIES"
            ),
            default=DEFAULT_OPENAI_MAX_RETRIES,
            variable_name=(
                "TEMPOAI_OPENAI_MAX_RETRIES"
            ),
        )

        raw_api_key = source.get("OPENAI_API_KEY")
        openai_api_key = (
            raw_api_key.strip()
            if isinstance(raw_api_key, str)
            and raw_api_key.strip()
            else None
        )

        if (
            provider_name == "openai"
            and openai_api_key is None
        ):
            raise CoachingConfigurationError(
                "OPENAI_API_KEY is required when the "
                "OpenAI coaching provider is selected."
            )

        return cls(
            provider_name=provider_name,
            openai_model=openai_model,
            openai_api_key=openai_api_key,
            openai_timeout_seconds=(
                openai_timeout_seconds
            ),
            openai_max_retries=openai_max_retries,
        )