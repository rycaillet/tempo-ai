from __future__ import annotations

import unittest
from unittest.mock import patch

from app.coaching import (
    CoachingConfigurationError,
    CoachingProvider,
    CoachingSettings,
    MockCoachingProvider,
    OpenAICoachingProvider,
    build_coaching_provider,
    build_configured_coaching_provider,
)


class FakeOpenAIClient:
    pass


class CoachingProviderFactoryTests(
    unittest.TestCase
):
    def test_builds_mock_provider(
        self,
    ) -> None:
        settings = CoachingSettings(
            provider_name="mock",
            openai_model="test-model",
        )

        provider = build_coaching_provider(settings)

        self.assertIsInstance(
            provider,
            MockCoachingProvider,
        )
        self.assertIsInstance(
            provider,
            CoachingProvider,
        )

    @patch("app.coaching.factory.OpenAI")
    def test_builds_openai_provider(
        self,
        openai_class: object,
    ) -> None:
        fake_client = FakeOpenAIClient()
        openai_class.return_value = fake_client

        settings = CoachingSettings(
            provider_name="openai",
            openai_model="test-model",
            openai_api_key="test-key",
            openai_timeout_seconds=45.0,
            openai_max_retries=3,
        )

        provider = build_coaching_provider(settings)

        self.assertIsInstance(
            provider,
            OpenAICoachingProvider,
        )
        self.assertIsInstance(
            provider,
            CoachingProvider,
        )
        openai_class.assert_called_once_with(
            api_key="test-key",
            timeout=45.0,
            max_retries=3,
        )

    def test_rejects_missing_openai_key(
        self,
    ) -> None:
        settings = CoachingSettings(
            provider_name="openai",
            openai_model="test-model",
            openai_api_key=None,
        )

        with self.assertRaises(
            CoachingConfigurationError
        ):
            build_coaching_provider(settings)

    def test_rejects_unknown_provider(
        self,
    ) -> None:
        settings = CoachingSettings(
            provider_name="unknown",
            openai_model="test-model",
        )

        with self.assertRaises(
            CoachingConfigurationError
        ):
            build_coaching_provider(settings)

    @patch(
        "app.coaching.factory."
        "CoachingSettings.from_environment"
    )
    @patch(
        "app.coaching.factory."
        "build_coaching_provider"
    )
    def test_builds_provider_from_environment(
        self,
        provider_builder: object,
        settings_builder: object,
    ) -> None:
        settings = CoachingSettings(
            provider_name="mock",
            openai_model="test-model",
        )
        expected_provider = MockCoachingProvider()

        settings_builder.return_value = settings
        provider_builder.return_value = expected_provider

        result = build_configured_coaching_provider()

        self.assertIs(
            result,
            expected_provider,
        )
        settings_builder.assert_called_once_with()
        provider_builder.assert_called_once_with(
            settings
        )


if __name__ == "__main__":
    unittest.main()