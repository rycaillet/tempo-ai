from __future__ import annotations

from app.pose_detector import (
    OrientationCandidate,
    select_orientation_candidate,
)


def build_candidate(
    *,
    rotation: str,
    score: float,
    frames_detected: int = 5,
) -> OrientationCandidate:
    return {
        "rotation": rotation,
        "framesTested": 5,
        "framesDetected": frames_detected,
        "averageVisibility": 0.85,
        "score": score,
    }


def test_preserves_unrotated_video_when_scores_are_nearly_tied():
    candidates = [
        build_candidate(
            rotation="none",
            score=0.9713,
        ),
        build_candidate(
            rotation="clockwise90",
            score=0.9734,
        ),
        build_candidate(
            rotation="counterclockwise90",
            score=0.9719,
        ),
        build_candidate(
            rotation="rotate180",
            score=0.9713,
        ),
    ]

    selected = select_orientation_candidate(
        candidates
    )

    assert selected["rotation"] == "none"


def test_uses_rotated_candidate_when_improvement_is_meaningful():
    candidates = [
        build_candidate(
            rotation="none",
            score=0.82,
        ),
        build_candidate(
            rotation="clockwise90",
            score=0.95,
        ),
        build_candidate(
            rotation="counterclockwise90",
            score=0.79,
        ),
        build_candidate(
            rotation="rotate180",
            score=0.81,
        ),
    ]

    selected = select_orientation_candidate(
        candidates
    )

    assert (
        selected["rotation"]
        == "clockwise90"
    )


def test_does_not_prefer_unrotated_candidate_without_pose_detection():
    candidates = [
        build_candidate(
            rotation="none",
            score=0.0,
            frames_detected=0,
        ),
        build_candidate(
            rotation="rotate180",
            score=0.92,
        ),
    ]

    selected = select_orientation_candidate(
        candidates
    )

    assert selected["rotation"] == "rotate180"