from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict


DEFAULT_WINDOW_RADIUS_FRAMES = 2


class ReferencePhaseFrame(TypedDict):
    phase: str
    frameIndex: int


class ClubFrameRequest(TypedDict):
    phase: str
    referenceFrameIndex: int
    frameIndex: int
    phaseOffsetFrames: int
    isReferenceFrame: bool


def build_reference_phase_frames(
    reference_phases: Sequence[
        tuple[str, Mapping[str, object]]
    ],
) -> list[ReferencePhaseFrame]:
    """
    Convert refined phase mappings into a stable frame-only model.

    The input order is retained and acts as the deterministic
    phase-priority order when dense windows overlap at an equal
    distance from two reference frames.
    """

    phase_frames: list[ReferencePhaseFrame] = []

    for phase_name, phase in reference_phases:
        frame_index = phase.get("frameIndex")

        if not isinstance(frame_index, int):
            raise ValueError(
                f"Reference phase {phase_name!r} does not "
                "contain a valid frame index."
            )

        phase_frames.append(
            {
                "phase": phase_name,
                "frameIndex": frame_index,
            }
        )

    if not phase_frames:
        raise ValueError(
            "At least one reference phase is required "
            "to build dense club-detection windows."
        )

    return phase_frames


def build_dense_club_frame_requests(
    reference_phases: Sequence[
        tuple[str, Mapping[str, object]]
    ],
    *,
    minimum_frame_index: int,
    maximum_frame_index: int,
    window_radius_frames: int = (
        DEFAULT_WINDOW_RADIUS_FRAMES
    ),
) -> list[ClubFrameRequest]:
    """
    Build one chronological, duplicate-free dense frame sequence.

    Each frame is owned by the nearest reference phase. When a frame
    is equally distant from two reference phases, the phase appearing
    earlier in ``reference_phases`` owns it.

    Frame requests are clipped to the supplied inclusive video-frame
    bounds.
    """

    if minimum_frame_index < 0:
        raise ValueError(
            "Minimum frame index cannot be negative."
        )

    if maximum_frame_index < minimum_frame_index:
        raise ValueError(
            "Maximum frame index must be greater than "
            "or equal to the minimum frame index."
        )

    if window_radius_frames < 0:
        raise ValueError(
            "Club-detection window radius cannot be negative."
        )

    phase_frames = build_reference_phase_frames(
        reference_phases
    )

    ownership_candidates: dict[
        int,
        list[tuple[int, int, ReferencePhaseFrame]],
    ] = {}

    for phase_priority, phase_frame in enumerate(
        phase_frames
    ):
        reference_frame_index = phase_frame[
            "frameIndex"
        ]

        window_start = max(
            minimum_frame_index,
            reference_frame_index
            - window_radius_frames,
        )

        window_end = min(
            maximum_frame_index,
            reference_frame_index
            + window_radius_frames,
        )

        if window_start > window_end:
            continue

        for frame_index in range(
            window_start,
            window_end + 1,
        ):
            distance = abs(
                frame_index - reference_frame_index
            )

            ownership_candidates.setdefault(
                frame_index,
                [],
            ).append(
                (
                    distance,
                    phase_priority,
                    phase_frame,
                )
            )

    frame_requests: list[ClubFrameRequest] = []

    for frame_index in sorted(
        ownership_candidates
    ):
        _, _, owning_phase = min(
            ownership_candidates[frame_index],
            key=lambda candidate: (
                candidate[0],
                candidate[1],
            ),
        )

        reference_frame_index = owning_phase[
            "frameIndex"
        ]

        frame_requests.append(
            {
                "phase": owning_phase["phase"],
                "referenceFrameIndex": (
                    reference_frame_index
                ),
                "frameIndex": frame_index,
                "phaseOffsetFrames": (
                    frame_index
                    - reference_frame_index
                ),
                "isReferenceFrame": (
                    frame_index
                    == reference_frame_index
                ),
            }
        )

    if not frame_requests:
        raise ValueError(
            "Dense club-detection windows did not contain "
            "any frames inside the available frame range."
        )

    return frame_requests