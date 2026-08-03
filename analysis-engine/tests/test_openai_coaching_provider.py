from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from typing import Any

from app.coaching import (
    CoachContext,
    CoachPriority,
    CoachStrength,
    CoachingProvider,
    CoachingProviderError,
    OpenAICoachingProvider,
    PROMPT_VERSION,
    build_coaching_response_schema,
)


class FakeResponse:
    def __init__(
        self,
        *,
        output_text: object,
        status: str | None = "completed",
        request_id: str | None = "req_test",
        output: list[object] | None = None,
        incomplete_reason: str | None = None,
    ) -> None:
        self.output_text = output_text
        self.status = status
        self._request_id = request_id
        self.output = output or []
        self.incomplete_details = (
            SimpleNamespace(
                reason=incomplete_reason
            )
            if incomplete_reason is not None
            else None
        )


class FakeResponsesClient:
    def __init__(
        self,
        *,
        response: FakeResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(
        self,
        **kwargs: Any,
    ) -> FakeResponse:
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        if self.response is None:
            raise AssertionError(
                "Fake response was not configured."
            )

        return self.response


class FakeOpenAIClient:
    def __init__(
        self,
        responses: FakeResponsesClient,
    ) -> None:
        self.responses = responses


class OpenAICoachingProviderTests(
    unittest.TestCase
):
    @staticmethod
    def build_context() -> CoachContext:
        return CoachContext(
            status="ready",
            overall_score=84.0,
            score_confidence=93.0,
            score_coverage=89.0,
            rating="good",
            rating_label="Good",
            analysis_summary=(
                "The swing demonstrates solid fundamentals."
            ),
            overall_finding=(
                "Address posture is the primary opportunity."
            ),
            primary_focus_metric_key="addressPosture",
            strengths=(
                CoachStrength(
                    metric_key="headStability",
                    display_name="Head stability",
                    score=96.0,
                    reason="Strong measured stability.",
                ),
            ),
            priorities=(
                CoachPriority(
                    metric_key="addressPosture",
                    display_name="Address posture",
                    severity="high",
                    priority=1,
                    title="Create a balanced setup",
                    summary=(
                        "Establish a stable address position."
                    ),
                    focus="Balance and posture",
                    rationale=(
                        "Setup influences the motion that follows."
                    ),
                    practice_cues=(
                        "Balance over the middle of the feet.",
                    ),
                    caution=None,
                ),
            ),
            warnings=("existing_warning",),
            limitations=(
                "Video analysis cannot directly measure force.",
            ),
        )

    @staticmethod
    def build_payload() -> dict[str, object]:
        return {
            "status": "ready",
            "primaryMetricKey": "addressPosture",
            "headline": "Build a more balanced setup",
            "overview": (
                "Your measured swing has a solid foundation."
            ),
            "primaryFocus": (
                "Start by improving balance and posture "
                "at address."
            ),
            "actionSteps": [
                "Balance over the middle of the feet.",
            ],
            "encouragement": (
                "Keep building on your head stability."
            ),
            "disclaimer": (
                "This guidance is based on video pose analysis."
            ),
            "warnings": [
                "video_measurement_limitation",
            ],
            "sourceMetricKeys": [
                "addressPosture",
                "headStability",
            ],
        }

    def build_provider(
        self,
        *,
        response: FakeResponse,
    ) -> tuple[
        OpenAICoachingProvider,
        FakeResponsesClient,
    ]:
        responses = FakeResponsesClient(
            response=response,
        )

        provider = OpenAICoachingProvider(
            model="test-model",
            client=FakeOpenAIClient(responses),
        )

        return provider, responses

    def test_provider_satisfies_coaching_protocol(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=json.dumps(
                    self.build_payload()
                ),
            ),
        )

        self.assertIsInstance(
            provider,
            CoachingProvider,
        )

    def test_generates_validated_coaching_response(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=json.dumps(
                    self.build_payload()
                ),
            ),
        )

        response = provider.generate(
            self.build_context()
        )

        self.assertEqual(response.status, "ready")
        self.assertEqual(
            response.headline,
            "Build a more balanced setup",
        )
        self.assertEqual(
            response.warnings,
            (
                "existing_warning",
                "video_measurement_limitation",
            ),
        )

    def test_sends_versioned_prompt_and_strict_schema(
        self,
    ) -> None:
        provider, responses = self.build_provider(
            response=FakeResponse(
                output_text=json.dumps(
                    self.build_payload()
                ),
            ),
        )

        provider.generate(
            self.build_context()
        )

        request = responses.calls[0]

        self.assertEqual(
            request["model"],
            "test-model",
        )
        self.assertIn(
            PROMPT_VERSION,
            request["input"],
        )
        self.assertEqual(
            request["text"]["format"]["type"],
            "json_schema",
        )
        self.assertTrue(
            request["text"]["format"]["strict"]
        )
        self.assertEqual(
            request["text"]["format"]["schema"],
            build_coaching_response_schema(),
        )

    def test_rejects_empty_model_name(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            OpenAICoachingProvider(
                model="   ",
                client=FakeOpenAIClient(
                    FakeResponsesClient()
                ),
            )

    def test_handles_api_client_failure(
        self,
    ) -> None:
        responses = FakeResponsesClient(
            error=RuntimeError(
                "Network failure"
            ),
        )
        provider = OpenAICoachingProvider(
            model="test-model",
            client=FakeOpenAIClient(responses),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_unexpected_error",
        )

    def test_rejects_incomplete_response(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=None,
                status="incomplete",
                incomplete_reason=(
                    "max_output_tokens"
                ),
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            (
                "openai_incomplete_"
                "max_output_tokens"
            ),
        )
        self.assertTrue(
            raised.exception.retryable
        )
        self.assertEqual(
            raised.exception.request_id,
            "req_test",
        )

    def test_rejects_refusal(
        self,
    ) -> None:
        refusal = SimpleNamespace(
            type="refusal",
            refusal="Unable to comply.",
        )
        message = SimpleNamespace(
            content=[refusal],
        )

        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=None,
                output=[message],
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_refusal",
        )
        self.assertFalse(
            raised.exception.retryable
        )

    def test_rejects_failed_response(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=None,
                status="failed",
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_response_failed",
        )

    def test_rejects_missing_output_text(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=None,
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_missing_output_text",
        )
        self.assertEqual(
            raised.exception.request_id,
            "req_test",
        )

    def test_rejects_invalid_json(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text="not-json",
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_invalid_json",
        )

    def test_rejects_ungrounded_response(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["primaryMetricKey"] = "weightShift"

        provider, _ = self.build_provider(
            response=FakeResponse(
                output_text=json.dumps(payload),
            ),
        )

        with self.assertRaises(
            CoachingProviderError
        ) as raised:
            provider.generate(
                self.build_context()
            )

        self.assertEqual(
            raised.exception.code,
            "openai_validation_error",
        )


if __name__ == "__main__":
    unittest.main()