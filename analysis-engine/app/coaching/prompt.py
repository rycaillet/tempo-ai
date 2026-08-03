from __future__ import annotations

import json
from dataclasses import dataclass

from app.coaching.models import CoachContext


PROMPT_VERSION = "tempo-coach-v3"


class CoachingPromptError(ValueError):
    """
    Raised when a valid coaching prompt cannot be built.
    """


@dataclass(frozen=True)
class CoachingPrompt:
    """
    Provider-independent prompt package for AI coaching generation.

    Keeping the system message, user message, and version together
    allows prompts to be tested, audited, and upgraded independently
    from any specific AI provider.
    """

    version: str
    system_message: str
    user_message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "systemMessage": self.system_message,
            "userMessage": self.user_message,
        }


def build_system_message() -> str:
    """
    Build the stable system instructions for the coaching model.
    """

    return (
        "You are the coaching-language layer for TempoAI, a "
        "video-based golf swing analysis system.\n\n"

        "SOURCE OF TRUTH\n"
        "The deterministic analysis engine is the only source of "
        "truth. Use only the structured coaching context supplied in "
        "the user message. Do not invent measurements, observations, "
        "causes, diagnoses, swing faults, drills, or recommendations "
        "that are not supported by that context.\n\n"

        "COACHING APPROACH\n"
        "Write like a knowledgeable golf coach giving a golfer one "
        "clear practice direction after reviewing measured video "
        "analysis. The response should feel practical, specific, "
        "supportive, and easy to apply during a practice session.\n\n"

        "PRIORITIZATION\n"
        "1. Preserve the supplied primary coaching priority.\n"
        "2. Make the primary priority the clear center of the response.\n"
        "3. Do not replace it with a secondary priority.\n"
        "4. Mention secondary priorities only when they directly help "
        "clarify the primary focus.\n"
        "5. Do not overwhelm the golfer with unrelated changes.\n\n"

        "OBSERVATIONAL METRICS\n"
        "1. Observations are unscored, measurement-only context.\n"
        "2. Do not promote an observation into a coaching priority.\n"
        "3. Do not create a drill, fault diagnosis, or causal claim "
        "from an observation.\n"
        "4. Mention an observation only when it directly supports or "
        "clarifies the supplied primary priority.\n"
        "5. Preserve each observation's limitations and camera-relative "
        "language.\n\n"

        "GROUNDING\n"
        "1. Use only supplied findings, recommendations, practice "
        "cues, strengths, observations, cautions, warnings, and "
        "limitations.\n"
        "2. Do not claim to know why a measured result occurred unless "
        "the supplied context explicitly states the cause.\n"
        "3. Do not introduce a drill unless it is supported by a "
        "supplied recommendation or practice cue.\n"
        "4. Do not mention a metric unless its exact metricKey is "
        "included in sourceMetricKeys.\n"
        "5. Do not contradict any supplied score, finding, "
        "recommendation, observation, warning, caution, or "
        "limitation.\n\n"

        "LANGUAGE QUALITY\n"
        "1. Use direct, natural coaching language.\n"
        "2. Explain the primary focus in terms the golfer can "
        "understand and practice.\n"
        "3. Avoid generic phrases such as 'unlock your potential,' "
        "'take your game to the next level,' or 'practice makes "
        "perfect.'\n"
        "4. Avoid repeating the same idea across the headline, "
        "overview, primary focus, and action steps.\n"
        "5. Do not use technical terminology unless it appears in the "
        "supplied context or is necessary to explain the priority.\n"
        "6. Do not exaggerate the certainty or expected effect of a "
        "change.\n\n"

        "ACTION STEPS\n"
        "1. Provide one to five short, practical action steps.\n"
        "2. Base the steps on supplied practice cues and "
        "recommendations.\n"
        "3. Keep each step focused on something the golfer can rehearse, "
        "feel, check, or repeat.\n"
        "4. Do not promise that an action will fix another part of the "
        "swing unless the context supports that relationship.\n\n"

        "SAFETY AND LIMITATIONS\n"
        "1. Do not claim that pose landmarks directly measure force, "
        "pressure, balance, intent, pain, injury, or medical "
        "conditions.\n"
        "2. Treat the output as video-based practice guidance rather "
        "than a diagnosis or replacement for an in-person golf "
        "professional.\n"
        "3. Preserve relevant warnings, cautions, observation "
        "limitations, and analysis limitations.\n\n"

        "OUTPUT CONTRACT\n"
        "Return exactly one JSON object matching the required response "
        "schema. Do not include Markdown, code fences, commentary, or "
        "text outside the JSON object."
    )


def build_response_schema() -> dict[str, object]:
    """
    Describe the structured payload expected from an AI provider.

    The response validator enforces this contract after generation.
    """

    return {
        "status": "ready",
        "primaryMetricKey": (
            "The exact metricKey of the supplied primary focus."
        ),
        "headline": (
            "A concise coaching headline centered on the primary "
            "focus."
        ),
        "overview": (
            "A brief summary of the measured swing analysis and the "
            "main practice direction."
        ),
        "primaryFocus": (
            "A clear explanation of the primary priority, why it "
            "matters, and what the golfer should focus on. Use only "
            "relationships supported by the supplied context."
        ),
        "actionSteps": [
            "One to five short, practical steps based on supplied "
            "recommendations and practice cues."
        ],
        "encouragement": (
            "A specific supportive closing grounded in measured "
            "strengths when strengths are available. Otherwise, use "
            "a restrained practice-focused closing."
        ),
        "disclaimer": (
            "A concise statement describing the limitations of "
            "video-based analysis or the role of in-person coaching."
        ),
        "warnings": [
            "Relevant warning or limitation strings supported by the "
            "supplied coaching context."
        ],
        "sourceMetricKeys": [
            "Every exact context metricKey used to produce any part "
            "of the coaching response."
        ],
    }


def build_task_instructions() -> list[str]:
    """
    Build the ordered instructions for one coaching response.
    """

    return [
        (
            "Use the first coaching priority as the primary focus and "
            "preserve its exact metricKey."
        ),
        (
            "Create one clear coaching theme instead of giving equal "
            "attention to every available metric."
        ),
        (
            "Explain the primary focus using only the supplied finding, "
            "recommendation, rationale, cues, caution, and related "
            "context."
        ),
        (
            "Treat observations as measurement-only supporting context "
            "and never as new priorities, diagnoses, or drill sources."
        ),
        (
            "Convert supplied practice cues into short action steps "
            "without adding unsupported drills."
        ),
        (
            "Use measured strengths for encouragement when available, "
            "but do not let strengths distract from the primary focus."
        ),
        (
            "Include every metricKey used in sourceMetricKeys and do "
            "not include unused metric keys."
        ),
        (
            "Return only the required JSON object."
        ),
    ]


def build_coaching_prompt(
    context: CoachContext,
) -> CoachingPrompt:
    """
    Build a versioned prompt from validated coaching context.

    Raw landmarks, frames, geometry, and detector internals cannot enter
    the prompt because CoachContext does not expose them.
    """

    if context.status != "ready":
        raise CoachingPromptError(
            "Coach context must be ready before prompt construction."
        )

    if not context.priorities:
        raise CoachingPromptError(
            "Coach context must contain at least one priority."
        )

    if context.primary_focus_metric_key is None:
        raise CoachingPromptError(
            "Coach context must identify a primary focus."
        )

    first_priority = context.priorities[0]

    if (
        first_priority.metric_key
        != context.primary_focus_metric_key
    ):
        raise CoachingPromptError(
            "Primary focus does not match the first coaching priority."
        )

    context_payload = context.to_dict()
    response_schema = build_response_schema()

    user_payload = {
        "task": (
            "Create a grounded, structured golf coaching response from "
            "the supplied deterministic coaching context."
        ),
        "promptVersion": PROMPT_VERSION,
        "instructions": build_task_instructions(),
        "coachingContext": context_payload,
        "requiredResponseSchema": response_schema,
    }

    return CoachingPrompt(
        version=PROMPT_VERSION,
        system_message=build_system_message(),
        user_message=json.dumps(
            user_payload,
            indent=2,
            sort_keys=True,
        ),
    )