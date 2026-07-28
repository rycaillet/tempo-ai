from __future__ import annotations

import unittest

from app.coaching import (
    DEFAULT_COACHING_PROVIDER,
    DEFAULT_OPENAI_MODEL,
    CoachingConfigurationError,
    CoachingSettings,
)


class CoachingSettingsTests(unittest.TestCase):
    def test_uses_safe_default_configuration(
        self,
    ) -> None:
        settings = CoachingSettings.from_environment({})

        self.assertEqual(
            settings.provider_name,
            DEFAULT_COACHING_PROVIDER,
        )
        self.assertEqual(
            settings.openai_model,
            DEFAULT_OPENAI_MODEL,
        )
        self.assertIsNone(settings.openai_api_key)

    def test_loads_mock_provider_configuration(
        self,
    ) -> None:
        settings = CoachingSettings.from_environment(
            {
                "TEMPOAI_COACHING_PROVIDER": "mock",
                "TEMPOAI_OPENAI_MODEL": "custom-model",
            }
        )

        self.assertEqual(
            settings.provider_name,
            "mock",
        )
        self.assertEqual(
            settings.openai_model,
            "custom-model",
        )

    def test_normalizes_provider_name(
        self,
    ) -> None:
        settings = CoachingSettings.from_environment(
            {
                "TEMPOAI_COACHING_PROVIDER": "  OPENAI  ",
                "OPENAI_API_KEY": "test-key",
            }
        )

        self.assertEqual(
            settings.provider_name,
            "openai",
        )

    def test_loads_openai_configuration(
        self,
    ) -> None:
        settings = CoachingSettings.from_environment(
            {
                "TEMPOAI_COACHING_PROVIDER": "openai",
                "TEMPOAI_OPENAI_MODEL": "test-model",
                "OPENAI_API_KEY": "test-key",
            }
        )

        self.assertEqual(
            settings.provider_name,
            "openai",
        )
        self.assertEqual(
            settings.openai_model,
            "test-model",
        )
        self.assertEqual(
            settings.openai_api_key,
            "test-key",
        )

    def test_rejects_unsupported_provider(
        self,
    ) -> None:
        with self.assertRaises(
            CoachingConfigurationError
        ):
            CoachingSettings.from_environment(
                {
                    "TEMPOAI_COACHING_PROVIDER": (
                        "unsupported"
                    ),
                }
            )

    def test_rejects_empty_model_name(
        self,
    ) -> None:
        with self.assertRaises(
            CoachingConfigurationError
        ):
            CoachingSettings.from_environment(
                {
                    "TEMPOAI_OPENAI_MODEL": "   ",
                }
            )

    def test_requires_key_for_openai_provider(
        self,
    ) -> None:
        with self.assertRaises(
            CoachingConfigurationError
        ):
            CoachingSettings.from_environment(
                {
                    "TEMPOAI_COACHING_PROVIDER": "openai",
                }
            )

    def test_does_not_expose_api_key_in_repr(
        self,
    ) -> None:
        settings = CoachingSettings.from_environment(
            {
                "TEMPOAI_COACHING_PROVIDER": "openai",
                "OPENAI_API_KEY": "secret-test-key",
            }
        )

        self.assertNotIn(
            "secret-test-key",
            repr(settings),
        )


if __name__ == "__main__":
    unittest.main()