from __future__ import annotations

import unittest
from typing import Any

from app.metrics.registry import (
    MetricDefinition,
    MetricRegistration,
    SummaryField,
    build_registered_metric_summary,
    build_registered_metrics,
    get_enabled_metric_registrations,
    get_metric_versions,
    get_registered_metric_keys,
    get_score_enabled_metric_registrations,
    validate_metric_registry,
    validate_scoring_weights,
)


def build_test_metric(
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "classification": context.get(
            "classification",
            "good",
        ),
        "confidence": 0.9,
    }


def apply_test_feedback(
    metrics: dict[str, Any],
    feedback_eligibility: dict[str, Any],
    display_name: str,
) -> dict[str, Any]:
    return {
        **metrics,
        "feedback": {
            "status": (
                "available"
                if feedback_eligibility["eligible"]
                else "suppressed"
            ),
            "displayName": display_name,
        },
    }


class MetricRegistryTests(unittest.TestCase):
    @staticmethod
    def build_registration(
        *,
        key: str = "testMetric",
        summary_key: str = "testClassification",
        enabled: bool = True,
        version: str = "1.0.0",
        scoring_weight: float = 100.0,
    ) -> MetricRegistration:
        return MetricRegistration(
            definition=MetricDefinition(
                key=key,
                display_name="Test metric",
                builder=build_test_metric,
                summary_fields=(
                    SummaryField(
                        output_key=summary_key,
                        value_path=("classification",),
                    ),
                ),
            ),
            enabled=enabled,
            version=version,
            scoring_weight=scoring_weight,
        )

    def test_validate_metric_registry_accepts_valid_registration(
        self,
    ) -> None:
        registration = self.build_registration()

        validate_metric_registry((registration,))

    def test_validate_metric_registry_rejects_duplicate_metric_key(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                summary_key="firstSummary",
            ),
            self.build_registration(
                summary_key="secondSummary",
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "duplicate metric key",
        ):
            validate_metric_registry(registrations)

    def test_validate_metric_registry_rejects_duplicate_summary_key(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
            ),
            self.build_registration(
                key="secondMetric",
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "duplicate summary key",
        ):
            validate_metric_registry(registrations)

    def test_validate_metric_registry_rejects_invalid_enabled_state(
        self,
    ) -> None:
        registration = self.build_registration()

        invalid_registration = MetricRegistration(
            definition=registration.definition,
            enabled=1,  # type: ignore[arg-type]
            version=registration.version,
            scoring_weight=registration.scoring_weight,
        )

        with self.assertRaisesRegex(
            ValueError,
            "enabled state",
        ):
            validate_metric_registry(
                (invalid_registration,)
            )

    def test_validate_metric_registry_rejects_invalid_version(
        self,
    ) -> None:
        registration = self.build_registration(
            version="version-one",
        )

        with self.assertRaisesRegex(
            ValueError,
            "version",
        ):
            validate_metric_registry((registration,))

    def test_validate_metric_registry_accepts_two_part_version(
        self,
    ) -> None:
        registration = self.build_registration(
            version="1.0",
        )

        validate_metric_registry((registration,))

    def test_validate_metric_registry_rejects_negative_weight(
        self,
    ) -> None:
        registration = self.build_registration(
            scoring_weight=-1.0,
        )

        with self.assertRaisesRegex(
            ValueError,
            "scoring weight",
        ):
            validate_metric_registry((registration,))

    def test_validate_metric_registry_rejects_boolean_weight(
        self,
    ) -> None:
        registration = self.build_registration()

        invalid_registration = MetricRegistration(
            definition=registration.definition,
            enabled=registration.enabled,
            version=registration.version,
            scoring_weight=True,
        )

        with self.assertRaisesRegex(
            ValueError,
            "scoring weight",
        ):
            validate_metric_registry(
                (invalid_registration,)
            )

    def test_get_enabled_metric_registrations_excludes_disabled(
        self,
    ) -> None:
        enabled_registration = self.build_registration(
            key="enabledMetric",
            summary_key="enabledSummary",
            scoring_weight=60.0,
        )
        disabled_registration = self.build_registration(
            key="disabledMetric",
            summary_key="disabledSummary",
            enabled=False,
            scoring_weight=40.0,
        )

        result = get_enabled_metric_registrations(
            (
                enabled_registration,
                disabled_registration,
            )
        )

        self.assertEqual(
            result,
            (enabled_registration,),
        )

    def test_get_score_enabled_registrations_excludes_zero_weight(
        self,
    ) -> None:
        scored_registration = self.build_registration(
            key="scoredMetric",
            summary_key="scoredSummary",
            scoring_weight=100.0,
        )
        unscored_registration = self.build_registration(
            key="unscoredMetric",
            summary_key="unscoredSummary",
            scoring_weight=0.0,
        )

        result = get_score_enabled_metric_registrations(
            (
                scored_registration,
                unscored_registration,
            )
        )

        self.assertEqual(
            result,
            (scored_registration,),
        )

    def test_get_registered_metric_keys_returns_all_keys(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
                summary_key="firstSummary",
                scoring_weight=50.0,
            ),
            self.build_registration(
                key="secondMetric",
                summary_key="secondSummary",
                enabled=False,
                scoring_weight=50.0,
            ),
        )

        self.assertEqual(
            get_registered_metric_keys(registrations),
            (
                "firstMetric",
                "secondMetric",
            ),
        )

    def test_get_registered_metric_keys_can_return_enabled_only(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
                summary_key="firstSummary",
                scoring_weight=50.0,
            ),
            self.build_registration(
                key="secondMetric",
                summary_key="secondSummary",
                enabled=False,
                scoring_weight=50.0,
            ),
        )

        self.assertEqual(
            get_registered_metric_keys(
                registrations,
                enabled_only=True,
            ),
            ("firstMetric",),
        )

    def test_get_metric_versions_returns_enabled_versions(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
                summary_key="firstSummary",
                version="1.2.0",
                scoring_weight=50.0,
            ),
            self.build_registration(
                key="secondMetric",
                summary_key="secondSummary",
                enabled=False,
                version="2.0.0",
                scoring_weight=50.0,
            ),
        )

        self.assertEqual(
            get_metric_versions(registrations),
            {
                "firstMetric": "1.2.0",
            },
        )

        self.assertEqual(
            get_metric_versions(
                registrations,
                enabled_only=False,
            ),
            {
                "firstMetric": "1.2.0",
                "secondMetric": "2.0.0",
            },
        )

    def test_validate_scoring_weights_accepts_expected_total(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
                summary_key="firstSummary",
                scoring_weight=40.0,
            ),
            self.build_registration(
                key="secondMetric",
                summary_key="secondSummary",
                scoring_weight=60.0,
            ),
        )

        validate_scoring_weights(registrations)

    def test_validate_scoring_weights_rejects_wrong_total(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="firstMetric",
                summary_key="firstSummary",
                scoring_weight=40.0,
            ),
            self.build_registration(
                key="secondMetric",
                summary_key="secondSummary",
                scoring_weight=50.0,
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "must total 100",
        ):
            validate_scoring_weights(registrations)

    def test_validate_scoring_weights_ignores_disabled_metrics(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="enabledMetric",
                summary_key="enabledSummary",
                scoring_weight=100.0,
            ),
            self.build_registration(
                key="disabledMetric",
                summary_key="disabledSummary",
                enabled=False,
                scoring_weight=50.0,
            ),
        )

        validate_scoring_weights(registrations)

    def test_build_registered_metrics_skips_disabled_metrics(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="enabledMetric",
                summary_key="enabledSummary",
                scoring_weight=100.0,
            ),
            self.build_registration(
                key="disabledMetric",
                summary_key="disabledSummary",
                enabled=False,
                scoring_weight=0.0,
            ),
        )

        result = build_registered_metrics(
            registrations=registrations,
            context={
                "classification": "excellent",
            },
            feedback_eligibility={
                "eligible": True,
            },
            apply_feedback=apply_test_feedback,
        )

        self.assertEqual(
            tuple(result),
            ("enabledMetric",),
        )
        self.assertEqual(
            result["enabledMetric"]["classification"],
            "excellent",
        )
        self.assertEqual(
            result["enabledMetric"]["feedback"]["status"],
            "available",
        )

    def test_build_registered_summary_skips_disabled_metrics(
        self,
    ) -> None:
        registrations = (
            self.build_registration(
                key="enabledMetric",
                summary_key="enabledSummary",
                scoring_weight=100.0,
            ),
            self.build_registration(
                key="disabledMetric",
                summary_key="disabledSummary",
                enabled=False,
                scoring_weight=0.0,
            ),
        )

        summary = build_registered_metric_summary(
            registrations=registrations,
            metric_results={
                "enabledMetric": {
                    "classification": "good",
                },
            },
        )

        self.assertEqual(
            summary,
            {
                "enabledSummary": "good",
            },
        )


if __name__ == "__main__":
    unittest.main()