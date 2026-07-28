from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)


class CoachingResponseValidationError(ValueError):
    """
    Raised when an AI provider returns an invalid or ungrounded payload.
    """


def normalize_required_string(
    *,
    payload: Mapping[str, Any],
    key: str,
) -> str:
    """
    Read one required nonempty string from a provider payload.
    """

    value = payload.get(key)

    if not isinstance(value, str) or not value.strip():
        raise CoachingResponseValidationError(
            f"Invalid or missing response field: {key}"
        )

    return value.strip()


def normalize_string_list(
    *,
    value: Any,
    field_name: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    """
    Validate and normalize a list of nonempty strings.
    """

    if not isinstance(value, list):
        raise CoachingResponseValidationError(
            f"Response field must be a list: {field_name}"
        )

    normalized_values: list[str] = []

    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CoachingResponseValidationError(
                f"Response field contains an invalid item: "
                f"{field_name}"
            )

        normalized_item = item.strip()

        if normalized_item not in normalized_values:
            normalized_values.append(normalized_item)

    if not allow_empty and not normalized_values:
        raise CoachingResponseValidationError(
            f"Response field cannot be empty: {field_name}"
        )

    return tuple(normalized_values)


def append_unique(
    values: list[str],
    value: str,
) -> None:
    """
    Append one value only when it is not already present.
    """

    if value not in values:
        values.append(value)


def get_allowed_metric_keys(
    context: CoachContext,
) -> set[str]:
    """
    Return every metric key exposed to the coaching provider.
    """

    return {
        strength.metric_key
        for strength in context.strengths
    } | {
        priority.metric_key
        for priority in context.priorities
    }


def validate_coaching_response_payload(
    *,
    payload: Mapping[str, Any],
    context: CoachContext,
) -> CoachResponse:
    """
    Validate and normalize a structured provider response.

    The validator ensures the response preserves the deterministic
    primary focus and references only metrics that were present in the
    provider-safe CoachContext.
    """

    if context.status != "ready":
        raise CoachingResponseValidationError(
            "Cannot validate coaching against unavailable context."
        )

    if not context.priorities:
        raise CoachingResponseValidationError(
            "Cannot validate coaching without context priorities."
        )

    status = payload.get("status")

    if status != "ready":
        raise CoachingResponseValidationError(
            "Provider response status must be ready."
        )

    primary_metric_key = normalize_required_string(
        payload=payload,
        key="primaryMetricKey",
    )

    expected_primary_metric_key = (
        context.primary_focus_metric_key
    )

    if (
        expected_primary_metric_key is None
        or primary_metric_key
        != expected_primary_metric_key
    ):
        raise CoachingResponseValidationError(
            "Provider response changed the deterministic "
            "primary focus."
        )

    allowed_metric_keys = get_allowed_metric_keys(
        context
    )

    source_metric_keys = normalize_string_list(
        value=payload.get("sourceMetricKeys"),
        field_name="sourceMetricKeys",
        allow_empty=False,
    )

    unknown_metric_keys = [
        metric_key
        for metric_key in source_metric_keys
        if metric_key not in allowed_metric_keys
    ]

    if unknown_metric_keys:
        unknown_values = ", ".join(
            unknown_metric_keys
        )

        raise CoachingResponseValidationError(
            "Provider response referenced unknown metrics: "
            f"{unknown_values}"
        )

    if primary_metric_key not in source_metric_keys:
        raise CoachingResponseValidationError(
            "Provider response did not cite the primary metric."
        )

    action_steps = normalize_string_list(
        value=payload.get("actionSteps"),
        field_name="actionSteps",
        allow_empty=False,
    )

    if len(action_steps) > 5:
        raise CoachingResponseValidationError(
            "Provider response contains more than five action steps."
        )

    provider_warnings = normalize_string_list(
        value=payload.get("warnings"),
        field_name="warnings",
        allow_empty=True,
    )

    warnings = list(context.warnings)

    for warning in provider_warnings:
        append_unique(
            warnings,
            warning,
        )

    return CoachResponse(
        status="ready",
        headline=normalize_required_string(
            payload=payload,
            key="headline",
        ),
        overview=normalize_required_string(
            payload=payload,
            key="overview",
        ),
        primary_focus=normalize_required_string(
            payload=payload,
            key="primaryFocus",
        ),
        action_steps=action_steps,
        encouragement=normalize_required_string(
            payload=payload,
            key="encouragement",
        ),
        disclaimer=normalize_required_string(
            payload=payload,
            key="disclaimer",
        ),
        warnings=tuple(warnings),
    )