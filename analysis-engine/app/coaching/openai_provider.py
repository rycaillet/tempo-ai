from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol

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


class OpenAICoachingProvider:
    """
    OpenAI-backed implementation of the coaching provider contract.

    Prompt construction, API communication, JSON parsing, and semantic
    validation remain separate responsibilities even though they are
    coordinated by this adapter.
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
                "OpenAI coaching prompt could not be built."
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
            raise CoachingProviderError(
                "OpenAI coaching request failed."
            ) from error

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
                "OpenAI returned no coaching response text."
            )

        try:
            raw_payload = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise CoachingProviderError(
                "OpenAI returned invalid coaching JSON."
            ) from error

        if not isinstance(raw_payload, Mapping):
            raise CoachingProviderError(
                "OpenAI coaching payload must be a JSON object."
            )

        try:
            return validate_coaching_response_payload(
                payload=raw_payload,
                context=context,
            )
        except CoachingResponseValidationError as error:
            raise CoachingProviderError(
                "OpenAI returned an invalid or ungrounded "
                "coaching response."
            ) from error