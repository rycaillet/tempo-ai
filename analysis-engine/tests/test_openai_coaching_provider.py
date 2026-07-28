from __future__ import annotations

import json
import unittest
from typing import Any

from app.coaching import (
    CoachContext,
    CoachPriority,
    CoachStrength,
    CoachingProvider,
    CoachingProviderError,
    OpenAICoachingProvider,
    build_coaching_response_schema,
    PROMPT_VERSION,
)


class FakeResponse:
    def __init__(
        self,
        *,
        output_text: object,
    ) -> None:
        self.output_text = output_text


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
        output_text: object,
    ) -> tuple[
        OpenAICoachingProvider,
        FakeResponsesClient,
    ]:
        responses = FakeResponsesClient(
            response=FakeResponse(
                output_text=output_text,
            ),
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
            output_text=json.dumps(
                self.build_payload()
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
            output_text=json.dumps(
                self.build_payload()
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
            response.action_steps,
            (
                "Balance over the middle of the feet.",
            ),
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
            output_text=json.dumps(
                self.build_payload()
            ),
        )

        provider.generate(
            self.build_context()
        )

        self.assertEqual(len(responses.calls), 1)

        request = responses.calls[0]

        self.assertEqual(
            request["model"],
            "test-model",
        )
        self.assertIn(
            "TempoAI",
            request["instructions"],
        )
        self.assertIn(
            PROMPT_VERSION,
            request["input"],
        )

        text_config = request["text"]
        response_format = text_config["format"]

        self.assertEqual(
            response_format["type"],
            "json_schema",
        )
        self.assertTrue(
            response_format["strict"]
        )
        self.assertEqual(
            response_format["schema"],
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
        ):
            provider.generate(
                self.build_context()
            )

    def test_rejects_missing_output_text(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            output_text=None,
        )

        with self.assertRaises(
            CoachingProviderError
        ):
            provider.generate(
                self.build_context()
            )

    def test_rejects_invalid_json(
        self,
    ) -> None:
        provider, _ = self.build_provider(
            output_text="not-json",
        )

        with self.assertRaises(
            CoachingProviderError
        ):
            provider.generate(
                self.build_context()
            )

    def test_rejects_ungrounded_response(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["primaryMetricKey"] = "weightShift"

        provider, _ = self.build_provider(
            output_text=json.dumps(payload),
        )

        with self.assertRaises(
            CoachingProviderError
        ):
            provider.generate(
                self.build_context()
            )


if __name__ == "__main__":
    unittest.main()