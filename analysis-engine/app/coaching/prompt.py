from __future__ import annotations

import json
from dataclasses import dataclass

from app.coaching.models import CoachContext


PROMPT_VERSION = "tempo-coach-v1"


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
        "The deterministic analysis engine is the source of truth. "
        "Use only the structured context supplied by the user message. "
        "Do not invent measurements, diagnoses, causes, swing faults, "
        "or recommendations that are not supported by that context.\n\n"
        "Requirements:\n"
        "1. Keep the coaching practical, supportive, and concise.\n"
        "2. Preserve the supplied primary coaching priority.\n"
        "3. Do not contradict scores, findings, recommendations, "
        "warnings, cautions, or limitations.\n"
        "4. Do not claim that pose landmarks directly measure forces, "
        "pressure, intent, pain, injury, or medical conditions.\n"
        "5. Treat the guidance as practice feedback rather than a "
        "replacement for an in-person golf professional.\n"
        "6. Return only one JSON object matching the required schema. "
        "Do not include Markdown or explanatory text outside JSON."
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
        "headline": "A concise coaching headline.",
        "overview": (
            "A short summary grounded only in the supplied analysis."
        ),
        "primaryFocus": (
            "A clear explanation of the highest-priority focus."
        ),
        "actionSteps": [
            "One to five practical steps grounded in supplied cues."
        ],
        "encouragement": (
            "A supportive closing grounded in measured strengths "
            "when available."
        ),
        "disclaimer": (
            "A concise video-analysis limitation or practice-guidance "
            "disclaimer."
        ),
        "warnings": [
            "Any relevant warning strings copied or derived from "
            "the supplied warnings and limitations."
        ],
        "sourceMetricKeys": [
            "Every context metricKey used to produce the response."
        ],
    }


def build_coaching_prompt(
    context: CoachContext,
) -> CoachingPrompt:
    """
    Build a versioned prompt from validated coaching context.

    Raw landmarks, frames, geometry, and low-level measurements cannot
    enter the prompt because CoachContext does not expose them.
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
            "Create a structured golf coaching response using only "
            "the supplied deterministic coaching context."
        ),
        "promptVersion": PROMPT_VERSION,
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