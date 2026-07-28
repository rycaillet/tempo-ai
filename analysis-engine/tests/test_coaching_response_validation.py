from __future__ import annotations

import unittest

from app.coaching import (
    CoachContext,
    CoachPriority,
    CoachStrength,
    CoachingResponseValidationError,
    validate_coaching_response_payload,
)


class CoachingResponseValidationTests(
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
                    summary="Establish a stable address position.",
                    focus="Balance and posture",
                    rationale=(
                        "Setup influences the motion that follows."
                    ),
                    practice_cues=(
                        "Balance over the middle of the feet.",
                    ),
                    caution=None,
                ),
                CoachPriority(
                    metric_key="weightShift",
                    display_name="Weight shift",
                    severity="medium",
                    priority=2,
                    title="Improve pressure transfer",
                    summary="Move efficiently toward the lead side.",
                    focus="Pressure transfer",
                    rationale="Transfer supports sequencing.",
                    practice_cues=(
                        "Finish balanced on the lead side.",
                    ),
                    caution=None,
                ),
            ),
            warnings=("existing_warning",),
            limitations=(),
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
                "Rehearse the setup before each swing.",
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

    def test_validates_ready_payload(
        self,
    ) -> None:
        response = validate_coaching_response_payload(
            payload=self.build_payload(),
            context=self.build_context(),
        )

        self.assertEqual(response.status, "ready")
        self.assertEqual(
            response.headline,
            "Build a more balanced setup",
        )
        self.assertEqual(
            len(response.action_steps),
            2,
        )
        self.assertEqual(
            response.warnings,
            (
                "existing_warning",
                "video_measurement_limitation",
            ),
        )

    def test_rejects_changed_primary_focus(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["primaryMetricKey"] = "weightShift"

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

    def test_rejects_unknown_source_metric(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["sourceMetricKeys"] = [
            "addressPosture",
            "clubPath",
        ]

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

    def test_requires_primary_metric_source(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["sourceMetricKeys"] = [
            "headStability",
        ]

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

    def test_rejects_invalid_action_steps(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["actionSteps"] = []

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

        payload["actionSteps"] = [
            "Step one",
            "Step two",
            "Step three",
            "Step four",
            "Step five",
            "Step six",
        ]

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

    def test_rejects_missing_required_text(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["headline"] = ""

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )

    def test_rejects_not_ready_payload(
        self,
    ) -> None:
        payload = self.build_payload()
        payload["status"] = "not_available"

        with self.assertRaises(
            CoachingResponseValidationError
        ):
            validate_coaching_response_payload(
                payload=payload,
                context=self.build_context(),
            )


if __name__ == "__main__":
    unittest.main()