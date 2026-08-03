from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol

import openai
from openai import OpenAI

from app.coaching.models import (
    CoachContext,
    CoachResponse,
)
from app.coaching.prompt import (
    CoachingPromptError,
    build_coaching_prompt,
)
from app.coaching.provider import (
    CoachingProviderError,
)
from app.coaching.response_validation import (
    CoachingResponseValidationError,
    validate_coaching_response_payload,
)


class ResponsesClient(Protocol):
    """
    Minimal Responses API contract required by OpenAI coaching.

    Keeping this protocol narrow allows the real SDK client to be
    replaced with deterministic fakes during unit tests.
    """

    def create(
        self,
        **kwargs: Any,
    ) -> Any:
        """
        Create one model response.
        """
        ...


class OpenAIClient(Protocol):
    """
    Minimal OpenAI client contract required by the provider.
    """

    responses: ResponsesClient


def build_coaching_response_schema() -> dict[str, object]:
    """
    Build the strict JSON schema requested from the OpenAI model.

    This schema guarantees structural correctness at the API boundary.
    Semantic grounding is still enforced separately by
    validate_coaching_response_payload().
    """

    return {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["ready"],
            },
            "primaryMetricKey": {
                "type": "string",
                "minLength": 1,
            },
            "headline": {
                "type": "string",
                "minLength": 1,
            },
            "overview": {
                "type": "string",
                "minLength": 1,
            },
            "primaryFocus": {
                "type": "string",
                "minLength": 1,
            },
            "actionSteps": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1,
                },
                "minItems": 1,
                "maxItems": 5,
            },
            "encouragement": {
                "type": "string",
                "minLength": 1,
            },
            "disclaimer": {
                "type": "string",
                "minLength": 1,
            },
            "warnings": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1,
                },
            },
            "sourceMetricKeys": {
                "type": "array",
                "items": {
                    "type": "string",
                    "minLength": 1,
                },
                "minItems": 1,
            },
        },
        "required": [
            "status",
            "primaryMetricKey",
            "headline",
            "overview",
            "primaryFocus",
            "actionSteps",
            "encouragement",
            "disclaimer",
            "warnings",
            "sourceMetricKeys",
        ],
        "additionalProperties": False,
    }


def get_request_id(
    value: Any,
) -> str | None:
    request_id = getattr(
        value,
        "request_id",
        None,
    )

    if not isinstance(request_id, str):
        request_id = getattr(
            value,
            "_request_id",
            None,
        )

    return (
        request_id
        if isinstance(request_id, str)
        and request_id
        else None
    )


def get_response_status(
    response: Any,
) -> str | None:
    status = getattr(response, "status", None)

    return status if isinstance(status, str) else None


def get_incomplete_reason(
    response: Any,
) -> str | None:
    details = getattr(
        response,
        "incomplete_details",
        None,
    )

    if isinstance(details, Mapping):
        reason = details.get("reason")
    else:
        reason = getattr(details, "reason", None)

    return reason if isinstance(reason, str) else None


def get_refusal_text(
    response: Any,
) -> str | None:
    output = getattr(response, "output", None)

    if not isinstance(output, list):
        return None

    for item in output:
        content = (
            item.get("content")
            if isinstance(item, Mapping)
            else getattr(item, "content", None)
        )

        if not isinstance(content, list):
            continue

        for content_item in content:
            if isinstance(content_item, Mapping):
                content_type = content_item.get("type")
                refusal = content_item.get("refusal")
            else:
                content_type = getattr(
                    content_item,
                    "type",
                    None,
                )
                refusal = getattr(
                    content_item,
                    "refusal",
                    None,
                )

            if (
                content_type == "refusal"
                and isinstance(refusal, str)
                and refusal
            ):
                return refusal

    return None


def build_api_error(
    error: Exception,
) -> CoachingProviderError:
    request_id = get_request_id(error)

    if isinstance(error, openai.APITimeoutError):
        return CoachingProviderError(
            "OpenAI coaching request timed out.",
            code="openai_timeout",
            request_id=request_id,
            retryable=True,
        )

    if isinstance(error, openai.RateLimitError):
        return CoachingProviderError(
            "OpenAI coaching request was rate limited.",
            code="openai_rate_limit",
            request_id=request_id,
            retryable=True,
        )

    if isinstance(error, openai.APIConnectionError):
        return CoachingProviderError(
            "OpenAI coaching service could not be reached.",
            code="openai_connection_error",
            request_id=request_id,
            retryable=True,
        )

    if isinstance(error, openai.APIStatusError):
        status_code = error.status_code
        retryable = (
            status_code in {408, 409, 429}
            or status_code >= 500
        )

        return CoachingProviderError(
            "OpenAI coaching request returned an API error.",
            code=f"openai_http_{status_code}",
            request_id=request_id,
            retryable=retryable,
        )

    return CoachingProviderError(
        "OpenAI coaching request failed.",
        code="openai_unexpected_error",
        request_id=request_id,
        retryable=False,
    )


class OpenAICoachingProvider:
    """
    OpenAI-backed implementation of the coaching provider contract.

    Prompt construction, API communication, response-state handling,
    JSON parsing, and semantic validation remain separate concerns.
    """

    def __init__(
        self,
        *,
        model: str,
        client: OpenAIClient | None = None,
    ) -> None:
        normalized_model = model.strip()

        if not normalized_model:
            raise ValueError(
                "OpenAI coaching model must be a nonempty string."
            )

        self._model = normalized_model
        self._client: OpenAIClient = (
            client
            if client is not None
            else OpenAI()
        )

    def generate(
        self,
        context: CoachContext,
    ) -> CoachResponse:
        """
        Generate and validate one structured coaching response.
        """

        try:
            prompt = build_coaching_prompt(context)
        except CoachingPromptError as error:
            raise CoachingProviderError(
                "OpenAI coaching prompt could not be built.",
                code="prompt_construction_error",
            ) from error

        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=prompt.system_message,
                input=prompt.user_message,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "tempo_ai_coaching_response",
                        "description": (
                            "A grounded TempoAI golf coaching response."
                        ),
                        "schema": build_coaching_response_schema(),
                        "strict": True,
                    },
                },
            )
        except Exception as error:
            raise build_api_error(error) from error

        request_id = get_request_id(response)
        response_status = get_response_status(response)

        if response_status in {
            "failed",
            "cancelled",
        }:
            raise CoachingProviderError(
                "OpenAI did not complete the coaching response.",
                code=f"openai_response_{response_status}",
                request_id=request_id,
                retryable=False,
            )

        if response_status == "incomplete":
            reason = (
                get_incomplete_reason(response)
                or "unknown"
            )

            raise CoachingProviderError(
                "OpenAI returned an incomplete coaching response.",
                code=f"openai_incomplete_{reason}",
                request_id=request_id,
                retryable=(
                    reason
                    in {
                        "max_output_tokens",
                        "max_tokens",
                    }
                ),
            )

        refusal = get_refusal_text(response)

        if refusal is not None:
            raise CoachingProviderError(
                "OpenAI refused the coaching request.",
                code="openai_refusal",
                request_id=request_id,
                retryable=False,
            )

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if (
            not isinstance(output_text, str)
            or not output_text.strip()
        ):
            raise CoachingProviderError(
                "OpenAI returned no coaching response text.",
                code="openai_missing_output_text",
                request_id=request_id,
            )

        try:
            raw_payload = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise CoachingProviderError(
                "OpenAI returned invalid coaching JSON.",
                code="openai_invalid_json",
                request_id=request_id,
            ) from error

        if not isinstance(raw_payload, Mapping):
            raise CoachingProviderError(
                "OpenAI coaching payload must be a JSON object.",
                code="openai_invalid_payload_type",
                request_id=request_id,
            )

        try:
            return validate_coaching_response_payload(
                payload=raw_payload,
                context=context,
            )
        except CoachingResponseValidationError as error:
            raise CoachingProviderError(
                "OpenAI returned an invalid or ungrounded "
                "coaching response.",
                code="openai_validation_error",
                request_id=request_id,
            ) from error