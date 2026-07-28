from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from app.coaching.models import (
    CoachContext,
    CoachPriority,
    CoachResponse,
)


class CoachingResponseValidationError(ValueError):
    """
    Raised when an AI provider returns an invalid or ungrounded payload.
    """


PRIMARY_FOCUS_STOP_WORDS = {
    "about",
    "after",
    "again",
    "against",
    "also",
    "because",
    "before",
    "being",
    "build",
    "building",
    "create",
    "creating",
    "each",
    "establish",
    "focus",
    "improve",
    "improving",
    "into",
    "more",
    "only",
    "position",
    "primary",
    "should",
    "start",
    "swing",
    "that",
    "their",
    "then",
    "this",
    "through",
    "toward",
    "with",
    "your",
}


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


def normalize_comparison_text(
    value: str,
) -> str:
    """
    Normalize text for case-insensitive comparison.
    """

    return " ".join(value.casefold().split())


def extract_words(
    value: str,
) -> set[str]:
    """
    Return normalized words suitable for lightweight grounding checks.
    """

    expanded_value = re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        value,
    )

    return {
        word
        for word in re.findall(
            r"[a-z0-9]+",
            expanded_value.casefold(),
        )
        if len(word) >= 4
        and word not in PRIMARY_FOCUS_STOP_WORDS
    }


def normalize_action_steps(
    value: Any,
) -> tuple[str, ...]:
    """
    Validate action steps for substance and duplication.

    Action steps must provide enough detail to function as practical
    coaching instructions rather than generic encouragement.
    """

    if not isinstance(value, list):
        raise CoachingResponseValidationError(
            "Response field must be a list: actionSteps"
        )

    normalized_steps: list[str] = []
    comparison_values: set[str] = set()

    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CoachingResponseValidationError(
                "Response field contains an invalid item: "
                "actionSteps"
            )

        normalized_step = item.strip()
        comparison_value = normalize_comparison_text(
            normalized_step
        )

        if comparison_value in comparison_values:
            raise CoachingResponseValidationError(
                "Provider response contains duplicate action steps."
            )

        words = re.findall(
            r"[a-z0-9]+",
            normalized_step.casefold(),
        )

        if len(normalized_step) < 12 or len(words) < 3:
            raise CoachingResponseValidationError(
                "Provider response contains an action step "
                "that is too vague."
            )

        comparison_values.add(comparison_value)
        normalized_steps.append(normalized_step)

    if not normalized_steps:
        raise CoachingResponseValidationError(
            "Response field cannot be empty: actionSteps"
        )

    if len(normalized_steps) > 5:
        raise CoachingResponseValidationError(
            "Provider response contains more than five action steps."
        )

    return tuple(normalized_steps)


def validate_distinct_coaching_sections(
    *,
    headline: str,
    overview: str,
    primary_focus: str,
) -> None:
    """
    Ensure major coaching sections do not repeat identical language.
    """

    normalized_sections = (
        normalize_comparison_text(headline),
        normalize_comparison_text(overview),
        normalize_comparison_text(primary_focus),
    )

    if len(set(normalized_sections)) != len(
        normalized_sections
    ):
        raise CoachingResponseValidationError(
            "Provider response repeated the same coaching language "
            "across multiple sections."
        )


def get_primary_priority(
    context: CoachContext,
) -> CoachPriority:
    """
    Return the deterministic priority selected as the primary focus.
    """

    primary_metric_key = context.primary_focus_metric_key

    for priority in context.priorities:
        if priority.metric_key == primary_metric_key:
            return priority

    raise CoachingResponseValidationError(
        "Coaching context does not contain its primary priority."
    )


def validate_primary_focus_language(
    *,
    primary_focus: str,
    context: CoachContext,
) -> None:
    """
    Ensure the written primary focus remains connected to the
    deterministic primary priority.

    This is a lightweight language check rather than a semantic claim.
    At least one meaningful term from the deterministic recommendation
    must appear in the provider's primary-focus explanation.
    """

    primary_priority = get_primary_priority(context)

    grounding_text = " ".join(
        (
            primary_priority.metric_key,
            primary_priority.display_name,
            primary_priority.title,
            primary_priority.summary,
            primary_priority.focus,
            primary_priority.rationale,
            *primary_priority.practice_cues,
        )
    )

    grounding_words = extract_words(grounding_text)
    response_words = extract_words(primary_focus)

    if not grounding_words.intersection(response_words):
        raise CoachingResponseValidationError(
            "Provider response primary focus is not grounded in the "
            "deterministic primary priority."
        )


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
    primary focus, references only provider-safe metrics, and contains
    useful coaching language.
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

    headline = normalize_required_string(
        payload=payload,
        key="headline",
    )
    overview = normalize_required_string(
        payload=payload,
        key="overview",
    )
    primary_focus = normalize_required_string(
        payload=payload,
        key="primaryFocus",
    )

    validate_distinct_coaching_sections(
        headline=headline,
        overview=overview,
        primary_focus=primary_focus,
    )

    validate_primary_focus_language(
        primary_focus=primary_focus,
        context=context,
    )

    action_steps = normalize_action_steps(
        payload.get("actionSteps")
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
        headline=headline,
        overview=overview,
        primary_focus=primary_focus,
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