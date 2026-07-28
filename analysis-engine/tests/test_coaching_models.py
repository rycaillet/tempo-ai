from __future__ import annotations

import unittest

from app.coaching.models import (
    CoachContext,
    CoachPriority,
    CoachResponse,
    CoachStrength,
)


class CoachingModelTests(unittest.TestCase):
    def test_coach_strength_serializes_public_shape(
        self,
    ) -> None:
        strength = CoachStrength(
            metric_key="headStability",
            display_name="Head stability",
            score=96.0,
            reason="Head stability was strongly measured.",
        )

        self.assertEqual(
            strength.to_dict(),
            {
                "metricKey": "headStability",
                "displayName": "Head stability",
                "score": 96.0,
                "reason": (
                    "Head stability was strongly measured."
                ),
            },
        )

    def test_coach_priority_serializes_public_shape(
        self,
    ) -> None:
        priority = CoachPriority(
            metric_key="weightShift",
            display_name="Weight shift",
            severity="high",
            priority=1,
            title="Improve pressure transfer",
            summary="Move pressure toward the lead side.",
            focus="Lower-body pressure transfer",
            rationale="Transfer supports sequencing.",
            practice_cues=(
                "Load without losing balance.",
                "Finish on the lead side.",
            ),
            caution=(
                "Pose landmarks do not directly measure "
                "pressure."
            ),
        )

        self.assertEqual(
            priority.to_dict(),
            {
                "metricKey": "weightShift",
                "displayName": "Weight shift",
                "severity": "high",
                "priority": 1,
                "title": "Improve pressure transfer",
                "summary": (
                    "Move pressure toward the lead side."
                ),
                "focus": "Lower-body pressure transfer",
                "rationale": "Transfer supports sequencing.",
                "practiceCues": [
                    "Load without losing balance.",
                    "Finish on the lead side.",
                ],
                "caution": (
                    "Pose landmarks do not directly measure "
                    "pressure."
                ),
            },
        )

    def test_coach_context_serializes_nested_models(
        self,
    ) -> None:
        context = CoachContext(
            status="ready",
            overall_score=85.0,
            score_confidence=100.0,
            score_coverage=85.0,
            rating="good",
            rating_label="Good",
            analysis_summary="Solid measured fundamentals.",
            overall_finding="Two areas need attention.",
            primary_focus_metric_key="weightShift",
            strengths=(
                CoachStrength(
                    metric_key="headStability",
                    display_name="Head stability",
                    score=100.0,
                    reason="Strong measured stability.",
                ),
            ),
            priorities=(
                CoachPriority(
                    metric_key="weightShift",
                    display_name="Weight shift",
                    severity="high",
                    priority=1,
                    title="Improve pressure transfer",
                    summary="Coordinate the lower body.",
                    focus="Pressure transfer",
                    rationale="Supports sequencing.",
                    practice_cues=(
                        "Finish on the lead side.",
                    ),
                    caution=None,
                ),
            ),
            warnings=(),
            limitations=(
                "One metric was unavailable.",
            ),
        )

        result = context.to_dict()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["overallScore"], 85.0)
        self.assertEqual(
            result["primaryFocusMetricKey"],
            "weightShift",
        )
        self.assertEqual(
            result["strengths"][0]["metricKey"],
            "headStability",
        )
        self.assertEqual(
            result["priorities"][0]["priority"],
            1,
        )
        self.assertEqual(
            result["limitations"],
            ["One metric was unavailable."],
        )

    def test_coach_response_serializes_public_shape(
        self,
    ) -> None:
        response = CoachResponse(
            status="ready",
            headline="Build a more balanced transfer",
            overview="Your swing has a solid foundation.",
            primary_focus="Improve pressure transfer.",
            action_steps=(
                "Practice slow rehearsals.",
                "Finish balanced.",
            ),
            encouragement="Keep building on your strengths.",
            disclaimer=(
                "This feedback is based on video analysis."
            ),
            warnings=(),
        )

        self.assertEqual(
            response.to_dict(),
            {
                "status": "ready",
                "headline": (
                    "Build a more balanced transfer"
                ),
                "overview": (
                    "Your swing has a solid foundation."
                ),
                "primaryFocus": (
                    "Improve pressure transfer."
                ),
                "actionSteps": [
                    "Practice slow rehearsals.",
                    "Finish balanced.",
                ],
                "encouragement": (
                    "Keep building on your strengths."
                ),
                "disclaimer": (
                    "This feedback is based on video "
                    "analysis."
                ),
                "warnings": [],
            },
        )


if __name__ == "__main__":
    unittest.main()