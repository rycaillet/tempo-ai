from __future__ import annotations

import json
import unittest

from app.coaching import (
    PROMPT_VERSION,
    CoachContext,
    CoachPriority,
    CoachStrength,
    CoachingPromptError,
    build_coaching_prompt,
)


class CoachingPromptTests(unittest.TestCase):
    @staticmethod
    def build_context(
        *,
        status: str = "ready",
        primary_focus_metric_key: str | None = (
            "addressPosture"
        ),
        include_priorities: bool = True,
    ) -> CoachContext:
        priorities = (
            (
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
                    caution=(
                        "Posture varies with body proportions."
                    ),
                ),
            )
            if include_priorities
            else ()
        )

        return CoachContext(
            status=status,
            overall_score=82.0,
            score_confidence=95.0,
            score_coverage=88.0,
            rating="good",
            rating_label="Good",
            analysis_summary=(
                "The swing demonstrates solid fundamentals."
            ),
            overall_finding=(
                "Address posture is the primary opportunity."
            ),
            primary_focus_metric_key=(
                primary_focus_metric_key
            ),
            strengths=(
                CoachStrength(
                    metric_key="headStability",
                    display_name="Head stability",
                    score=96.0,
                    reason="Strong measured stability.",
                ),
            ),
            priorities=priorities,
            warnings=("limited_metric_coverage",),
            limitations=(
                "Video analysis cannot directly measure force.",
            ),
        )

    def test_builds_versioned_prompt(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertEqual(
            prompt.version,
            PROMPT_VERSION,
        )
        self.assertEqual(
            prompt.to_dict()["version"],
            PROMPT_VERSION,
        )

    def test_prompt_contains_serialized_context(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        user_payload = json.loads(
            prompt.user_message
        )

        coaching_context = user_payload[
            "coachingContext"
        ]

        self.assertEqual(
            coaching_context["overallScore"],
            82.0,
        )
        self.assertEqual(
            coaching_context[
                "primaryFocusMetricKey"
            ],
            "addressPosture",
        )
        self.assertEqual(
            coaching_context["priorities"][0][
                "metricKey"
            ],
            "addressPosture",
        )

    def test_prompt_contains_required_response_schema(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        user_payload = json.loads(
            prompt.user_message
        )
        response_schema = user_payload[
            "requiredResponseSchema"
        ]

        self.assertIn(
            "primaryMetricKey",
            response_schema,
        )
        self.assertIn(
            "sourceMetricKeys",
            response_schema,
        )
        self.assertIn(
            "actionSteps",
            response_schema,
        )

    def test_prompt_excludes_raw_analysis_sections(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertNotIn(
            "referenceGeometry",
            prompt.user_message,
        )
        self.assertNotIn(
            "landmarks",
            prompt.user_message,
        )
        self.assertNotIn(
            "phaseFrames",
            prompt.user_message,
        )

    def test_prompt_includes_ordered_coaching_instructions(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        user_payload = json.loads(
            prompt.user_message
        )
        instructions = user_payload[
            "instructions"
        ]

        self.assertEqual(
            len(instructions),
            7,
        )
        self.assertIn(
            "first coaching priority",
            instructions[0],
        )
        self.assertIn(
            "one clear coaching theme",
            instructions[1],
        )
        self.assertIn(
            "practice cues",
            instructions[3],
        )
        self.assertIn(
            "sourceMetricKeys",
            instructions[5],
        )
        self.assertIn(
            "required JSON object",
            instructions[6],
        )

    def test_system_message_protects_primary_priority(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertIn(
            "Make the primary priority the clear center",
            prompt.system_message,
        )
        self.assertIn(
            "Do not replace it with a secondary priority",
            prompt.system_message,
        )
        self.assertIn(
            "Do not overwhelm the golfer with unrelated changes",
            prompt.system_message,
        )

    def test_system_message_blocks_unsupported_coaching(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertIn(
            "Do not claim to know why a measured result occurred",
            prompt.system_message,
        )
        self.assertIn(
            "Do not introduce a drill unless it is supported",
            prompt.system_message,
        )
        self.assertIn(
            "Do not invent measurements",
            prompt.system_message,
        )

    def test_system_message_requires_grounded_action_steps(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertIn(
            "Base the steps on supplied practice cues",
            prompt.system_message,
        )
        self.assertIn(
            "something the golfer can rehearse",
            prompt.system_message,
        )
        self.assertIn(
            "Do not promise that an action will fix",
            prompt.system_message,
        )

    def test_system_message_requires_json_only_output(
        self,
    ) -> None:
        prompt = build_coaching_prompt(
            self.build_context()
        )

        self.assertIn(
            "Return exactly one JSON object",
            prompt.system_message,
        )
        self.assertIn(
            "Do not include Markdown",
            prompt.system_message,
        )
        self.assertIn(
            "text outside the JSON object",
            prompt.system_message,
        )

    def test_rejects_invalid_context(
        self,
    ) -> None:
        with self.assertRaises(
            CoachingPromptError
        ):
            build_coaching_prompt(
                self.build_context(
                    status="not_available",
                )
            )

        with self.assertRaises(
            CoachingPromptError
        ):
            build_coaching_prompt(
                self.build_context(
                    include_priorities=False,
                    primary_focus_metric_key=None,
                )
            )

        with self.assertRaises(
            CoachingPromptError
        ):
            build_coaching_prompt(
                self.build_context(
                    primary_focus_metric_key=(
                        "weightShift"
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()