from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class RecommendationTemplate:
    """
    Curated coaching guidance associated with one scored golf metric.

    Templates describe the coaching direction for a metric without
    deciding whether that metric should be recommended for a particular
    swing. Priority selection belongs to the Recommendation Engine.
    """

    metric_key: str
    title: str
    summary: str
    focus: str
    rationale: str
    practice_cues: tuple[str, ...]
    caution: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "metricKey": self.metric_key,
            "title": self.title,
            "summary": self.summary,
            "focus": self.focus,
            "rationale": self.rationale,
            "practiceCues": list(self.practice_cues),
            "caution": self.caution,
        }


_RECOMMENDATION_CATALOG = {
    "tempo": RecommendationTemplate(
        metric_key="tempo",
        title="Build a repeatable swing rhythm",
        summary=(
            "Develop a more consistent relationship between backswing "
            "and downswing timing."
        ),
        focus="Swing rhythm and transition timing",
        rationale=(
            "A repeatable tempo can make the sequence of the swing "
            "easier to reproduce."
        ),
        practice_cues=(
            "Use the same smooth cadence on each practice swing.",
            "Avoid rushing the transition from backswing to downswing.",
            "Prioritize repeatable rhythm over maximum speed.",
        ),
        caution=(
            "Tempo targets are general references and should not force "
            "every golfer into an identical swing speed."
        ),
    ),
    "addressPosture": RecommendationTemplate(
        metric_key="addressPosture",
        title="Create a balanced address posture",
        summary=(
            "Establish a stable setup that supports balance and freedom "
            "of movement throughout the swing."
        ),
        focus="Balance, alignment, and setup posture",
        rationale=(
            "The address position influences how easily the body can "
            "rotate and maintain space during the swing."
        ),
        practice_cues=(
            "Begin from a balanced position over the middle of the feet.",
            "Create forward bend from the hips rather than the waist.",
            "Keep the setup athletic without adding unnecessary tension.",
        ),
        caution=(
            "Address posture varies with body proportions, mobility, "
            "club selection, and camera perspective."
        ),
    ),
    "impactPosition": RecommendationTemplate(
        metric_key="impactPosition",
        title="Improve impact alignment",
        summary=(
            "Organize the body more consistently as the club reaches "
            "the impact area."
        ),
        focus="Body alignment and stability through impact",
        rationale=(
            "A stable impact position can support more predictable "
            "contact and energy transfer."
        ),
        practice_cues=(
            "Maintain balance as the body moves through impact.",
            "Allow rotation to continue instead of stopping at the ball.",
            "Practice controlled swings before increasing speed.",
        ),
        caution=(
            "Two-dimensional pose analysis cannot directly measure "
            "clubface angle, club path, or exact ball contact."
        ),
    ),
    "earlyExtension": RecommendationTemplate(
        metric_key="earlyExtension",
        title="Maintain space through the downswing",
        summary=(
            "Preserve hip depth and posture as the body rotates toward "
            "impact."
        ),
        focus="Hip depth and lower-body movement",
        rationale=(
            "Maintaining space can help the arms and club move through "
            "the hitting area without unnecessary compensation."
        ),
        practice_cues=(
            "Feel the hips rotating rather than moving toward the ball.",
            "Maintain pressure through the feet during the downswing.",
            "Use slow rehearsals to preserve posture through impact.",
        ),
        caution=(
            "Apparent hip movement can be affected by camera placement, "
            "clothing, pose visibility, and individual mobility."
        ),
    ),
    "headStability": RecommendationTemplate(
        metric_key="headStability",
        title="Reduce unnecessary head movement",
        summary=(
            "Keep head movement controlled while allowing the body to "
            "rotate naturally."
        ),
        focus="Visual stability and centered movement",
        rationale=(
            "Controlled head movement can make posture and low-point "
            "control easier to repeat."
        ),
        practice_cues=(
            "Allow natural rotation without forcing the head to stay still.",
            "Avoid large lateral movement away from the starting position.",
            "Use balanced, controlled rehearsals before full-speed swings.",
        ),
        caution=(
            "The goal is controlled movement, not a completely fixed "
            "head throughout the swing."
        ),
    ),
    "weightShift": RecommendationTemplate(
        metric_key="weightShift",
        title="Improve pressure transfer",
        summary=(
            "Coordinate movement from the trail side toward the lead "
            "side during the swing."
        ),
        focus="Lower-body pressure transfer and balance",
        rationale=(
            "A coordinated transfer can support sequencing, rotation, "
            "and a balanced finish."
        ),
        practice_cues=(
            "Maintain balance while loading into the backswing.",
            "Begin moving pressure toward the lead side before impact.",
            "Finish with stable support on the lead side.",
        ),
        caution=(
            "Pose landmarks estimate body movement but do not directly "
            "measure pressure beneath the feet."
        ),
    ),
    "rotation": RecommendationTemplate(
        metric_key="rotation",
        title="Improve rotational sequencing",
        summary=(
            "Coordinate the shoulder and hip turn through the backswing "
            "and downswing."
        ),
        focus="Body turn and rotational sequence",
        rationale=(
            "Coordinated rotation can help produce speed while "
            "maintaining balance and posture."
        ),
        practice_cues=(
            "Create a comfortable shoulder turn without losing balance.",
            "Begin the downswing with coordinated lower-body movement.",
            "Continue rotating through impact toward a balanced finish.",
        ),
        caution=(
            "Current rotation measurements are two-dimensional "
            "image-plane estimates rather than true three-dimensional "
            "body rotation."
        ),
    ),
}


RECOMMENDATION_CATALOG: Mapping[
    str,
    RecommendationTemplate,
] = MappingProxyType(_RECOMMENDATION_CATALOG)


def get_recommendation_template(
    metric_key: str,
) -> RecommendationTemplate | None:
    """
    Return the curated template for a metric, when available.
    """

    return RECOMMENDATION_CATALOG.get(metric_key)


def validate_recommendation_catalog(
    catalog: Mapping[str, RecommendationTemplate],
) -> None:
    """
    Validate catalog integrity at application startup.
    """

    if not catalog:
        raise ValueError(
            "Recommendation catalog must contain at least one template."
        )

    for metric_key, template in catalog.items():
        if not isinstance(metric_key, str) or not metric_key:
            raise ValueError(
                "Recommendation catalog keys must be non-empty strings."
            )

        if not isinstance(template, RecommendationTemplate):
            raise TypeError(
                "Recommendation catalog values must be "
                "RecommendationTemplate instances."
            )

        if template.metric_key != metric_key:
            raise ValueError(
                "Recommendation template metric key does not match "
                f"catalog key: {metric_key}"
            )

        required_text_fields = {
            "title": template.title,
            "summary": template.summary,
            "focus": template.focus,
            "rationale": template.rationale,
        }

        for field_name, value in required_text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "Recommendation template field must be a non-empty "
                    f"string: {metric_key}.{field_name}"
                )

        if not template.practice_cues:
            raise ValueError(
                "Recommendation template must contain at least one "
                f"practice cue: {metric_key}"
            )

        if any(
            not isinstance(cue, str) or not cue.strip()
            for cue in template.practice_cues
        ):
            raise ValueError(
                "Recommendation practice cues must be non-empty strings: "
                f"{metric_key}"
            )

        if len(set(template.practice_cues)) != len(
            template.practice_cues
        ):
            raise ValueError(
                "Recommendation practice cues must be unique: "
                f"{metric_key}"
            )


validate_recommendation_catalog(RECOMMENDATION_CATALOG)