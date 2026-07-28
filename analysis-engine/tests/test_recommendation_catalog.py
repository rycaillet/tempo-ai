from __future__ import annotations

import unittest

from app.recommendations import (
    RECOMMENDATION_CATALOG,
    RecommendationTemplate,
    get_recommendation_template,
    validate_recommendation_catalog,
)


class RecommendationCatalogTests(unittest.TestCase):
    EXPECTED_METRIC_KEYS = {
        "tempo",
        "addressPosture",
        "impactPosition",
        "earlyExtension",
        "headStability",
        "weightShift",
        "rotation",
    }

    def test_catalog_contains_all_scored_metrics(self) -> None:
        self.assertEqual(
            set(RECOMMENDATION_CATALOG),
            self.EXPECTED_METRIC_KEYS,
        )

    def test_catalog_templates_match_their_keys(self) -> None:
        for metric_key, template in (
            RECOMMENDATION_CATALOG.items()
        ):
            self.assertIsInstance(
                template,
                RecommendationTemplate,
            )
            self.assertEqual(
                template.metric_key,
                metric_key,
            )

    def test_template_serializes_to_public_json_shape(self) -> None:
        template = RECOMMENDATION_CATALOG["rotation"]

        result = template.to_dict()

        self.assertEqual(
            tuple(result.keys()),
            (
                "metricKey",
                "title",
                "summary",
                "focus",
                "rationale",
                "practiceCues",
                "caution",
            ),
        )
        self.assertEqual(result["metricKey"], "rotation")
        self.assertIsInstance(result["practiceCues"], list)
        self.assertGreater(len(result["practiceCues"]), 0)

    def test_get_recommendation_template_returns_known_metric(
        self,
    ) -> None:
        template = get_recommendation_template("tempo")

        self.assertIsNotNone(template)
        self.assertEqual(template.metric_key, "tempo")

    def test_get_recommendation_template_returns_none_for_unknown_metric(
        self,
    ) -> None:
        template = get_recommendation_template(
            "unknownMetric"
        )

        self.assertIsNone(template)

    def test_validation_rejects_mismatched_metric_key(self) -> None:
        invalid_catalog = {
            "tempo": RecommendationTemplate(
                metric_key="rotation",
                title="Title",
                summary="Summary",
                focus="Focus",
                rationale="Rationale",
                practice_cues=("Practice cue",),
            ),
        }

        with self.assertRaisesRegex(
            ValueError,
            "does not match",
        ):
            validate_recommendation_catalog(
                invalid_catalog
            )

    def test_validation_rejects_empty_practice_cues(self) -> None:
        invalid_catalog = {
            "tempo": RecommendationTemplate(
                metric_key="tempo",
                title="Title",
                summary="Summary",
                focus="Focus",
                rationale="Rationale",
                practice_cues=(),
            ),
        }

        with self.assertRaisesRegex(
            ValueError,
            "at least one practice cue",
        ):
            validate_recommendation_catalog(
                invalid_catalog
            )


if __name__ == "__main__":
    unittest.main()