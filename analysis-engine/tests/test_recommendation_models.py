from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from app.recommendations import (
    PrimaryFocus,
    Recommendation,
    SwingRecommendations,
)


class RecommendationModelTests(unittest.TestCase):
    @staticmethod
    def build_recommendation() -> Recommendation:
        return Recommendation(
            metric_key="rotation",
            display_name="Rotation",
            severity="high",
            priority=1,
            title="Improve rotational sequencing",
            summary=(
                "Coordinate the shoulder and hip turn through the "
                "backswing and downswing."
            ),
            focus="Body turn and rotational sequence",
            rationale=(
                "Coordinated rotation can help produce speed while "
                "maintaining balance and posture."
            ),
            practice_cues=(
                "Create a comfortable shoulder turn without losing balance.",
                "Begin the downswing with coordinated lower-body movement.",
                (
                    "Continue rotating through impact toward a balanced "
                    "finish."
                ),
            ),
            caution=(
                "Current rotation measurements are two-dimensional "
                "image-plane estimates."
            ),
        )

    def test_primary_focus_serializes_to_public_json_shape(
        self,
    ) -> None:
        primary_focus = PrimaryFocus(
            metric_key="rotation",
            display_name="Rotation",
            severity="high",
        )

        result = primary_focus.to_dict()

        self.assertEqual(
            result,
            {
                "metricKey": "rotation",
                "displayName": "Rotation",
                "severity": "high",
            },
        )

    def test_recommendation_serializes_to_public_json_shape(
        self,
    ) -> None:
        recommendation = self.build_recommendation()

        result = recommendation.to_dict()

        self.assertEqual(
            tuple(result.keys()),
            (
                "metricKey",
                "displayName",
                "severity",
                "priority",
                "title",
                "summary",
                "focus",
                "rationale",
                "practiceCues",
                "caution",
            ),
        )
        self.assertEqual(result["metricKey"], "rotation")
        self.assertEqual(result["displayName"], "Rotation")
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["priority"], 1)
        self.assertIsInstance(result["practiceCues"], list)
        self.assertEqual(len(result["practiceCues"]), 3)

    def test_swing_recommendations_serializes_complete_output(
        self,
    ) -> None:
        recommendation = self.build_recommendation()
        primary_focus = PrimaryFocus(
            metric_key="rotation",
            display_name="Rotation",
            severity="high",
        )

        swing_recommendations = SwingRecommendations(
            status="ready",
            primary_focus=primary_focus,
            recommendations=(recommendation,),
            warnings=(),
        )

        result = swing_recommendations.to_dict()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(
            result["primaryFocus"],
            {
                "metricKey": "rotation",
                "displayName": "Rotation",
                "severity": "high",
            },
        )
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertEqual(
            result["recommendations"][0]["metricKey"],
            "rotation",
        )
        self.assertEqual(result["warnings"], [])

    def test_swing_recommendations_supports_no_primary_focus(
        self,
    ) -> None:
        swing_recommendations = SwingRecommendations(
            status="not_available",
            primary_focus=None,
            recommendations=(),
            warnings=("no_improvement_priorities",),
        )

        result = swing_recommendations.to_dict()

        self.assertEqual(result["status"], "not_available")
        self.assertIsNone(result["primaryFocus"])
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(
            result["warnings"],
            ["no_improvement_priorities"],
        )

    def test_serialization_returns_new_collection_objects(
        self,
    ) -> None:
        recommendation = self.build_recommendation()
        swing_recommendations = SwingRecommendations(
            status="ready",
            primary_focus=PrimaryFocus(
                metric_key="rotation",
                display_name="Rotation",
                severity="high",
            ),
            recommendations=(recommendation,),
            warnings=("example_warning",),
        )

        first_result = swing_recommendations.to_dict()
        second_result = swing_recommendations.to_dict()

        self.assertIsNot(
            first_result["recommendations"],
            second_result["recommendations"],
        )
        self.assertIsNot(
            first_result["warnings"],
            second_result["warnings"],
        )
        self.assertIsNot(
            first_result["recommendations"][0]["practiceCues"],
            second_result["recommendations"][0]["practiceCues"],
        )

    def test_models_are_immutable(self) -> None:
        primary_focus = PrimaryFocus(
            metric_key="rotation",
            display_name="Rotation",
            severity="high",
        )

        with self.assertRaises(FrozenInstanceError):
            primary_focus.severity = "medium"


if __name__ == "__main__":
    unittest.main()