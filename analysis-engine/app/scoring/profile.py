from __future__ import annotations

import math

from app.scoring.types import ScoreProfile


DEFAULT_SCORING_PROFILE = ScoreProfile(
    name="default",
    version="1.0.0",
    classification_scores={
        "tempo": {
            "balanced": 100.0,
            "quick": 82.0,
            "deliberate": 82.0,
        },
        "addressPosture": {
            "neutral": 100.0,
            "needs_attention": 60.0,
            "incomplete": None,
        },
        "impactPosition": {
            "neutral": 100.0,
            "needs_attention": 55.0,
            "incomplete": None,
        },
        "earlyExtension": {
            "neutral": 100.0,
            "mild_early_extension": 80.0,
            "moderate_early_extension": 55.0,
            "severe_early_extension": 25.0,
            "needs_attention": 55.0,
            "incomplete": None,
        },
        "headStability": {
            "neutral": 100.0,
            "needs_attention": 60.0,
            "incomplete": None,
        },
        "weightShift": {
            "neutral": 100.0,
            "needs_attention": 60.0,
            "incomplete": None,
        },
        "rotation": {
            "neutral": 100.0,
            "needs_attention": 60.0,
            "incomplete": None,
        },
    },
)


def validate_score_profile(profile: ScoreProfile) -> None:
    if not profile.name.strip():
        raise ValueError("Scoring profile name cannot be empty.")

    if not profile.version.strip():
        raise ValueError("Scoring profile version cannot be empty.")

    if not profile.classification_scores:
        raise ValueError(
            "Scoring profile must contain at least one metric mapping."
        )

    for metric_key, classification_scores in (
        profile.classification_scores.items()
    ):
        if not metric_key.strip():
            raise ValueError(
                "Scoring profile metric keys cannot be empty."
            )

        if not classification_scores:
            raise ValueError(
                "Scoring profile metric mapping cannot be empty: "
                f"{metric_key}"
            )

        for classification, score in classification_scores.items():
            if not classification.strip():
                raise ValueError(
                    "Scoring profile classifications cannot be empty: "
                    f"{metric_key}"
                )

            if score is None:
                continue

            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(float(score))
                or float(score) < 0.0
                or float(score) > 100.0
            ):
                raise ValueError(
                    "Classification score must be None or a finite "
                    "number from 0 through 100: "
                    f"{metric_key}.{classification}"
                )


validate_score_profile(DEFAULT_SCORING_PROFILE)