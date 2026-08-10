from __future__ import annotations

import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


CANONICAL_LONG_EDGE_PIXELS = 1280
CANONICAL_VIDEO_CODEC = "libx264"
CANONICAL_PIXEL_FORMAT = "yuv420p"
CANONICAL_CONTAINER_EXTENSION = ".mp4"
CANONICAL_CRF = 18
CANONICAL_PRESET = "medium"


@dataclass(frozen=True)
class NormalizedAnalysisVideo:
    """
    Canonical video representation used internally by TempoAI.

    The original uploaded video remains untouched. The normalized
    analysis video exists only for the lifetime of the normalization
    context and should be used by all computer-vision stages.
    """

    source_path: Path
    analysis_path: Path


def get_ffmpeg_executable() -> str:
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path is None:
        raise RuntimeError(
            "FFmpeg is required to normalize uploaded videos "
            "for analysis, but it could not be found."
        )

    return ffmpeg_path


def build_scale_filter() -> str:
    """
    Normalize the physically oriented video to a deterministic
    1280-pixel long edge while preserving aspect ratio.

    TempoAI explicitly calculates the short edge instead of relying
    on FFmpeg's force_original_aspect_ratio / force_divisible_by
    behavior. Different FFmpeg builds may otherwise round fractional
    dimensions differently.

    The calculated short edge is rounded to the nearest even pixel so
    the result remains compatible with H.264/yuv420p.

    FFmpeg performs display-matrix autorotation before filtering by
    default, so iw and ih describe the physically oriented frames.
    """

    long_edge = CANONICAL_LONG_EDGE_PIXELS

    portrait_width = (
        f"trunc(iw*{long_edge}/ih/2+0.5)*2"
    )
    landscape_height = (
        f"trunc(ih*{long_edge}/iw/2+0.5)*2"
    )

    return (
        "scale="
        f"w='if(gte(iw,ih),{long_edge},"
        f"{portrait_width})':"
        f"h='if(gte(iw,ih),"
        f"{landscape_height},{long_edge})':"
        "in_range=auto:"
        "out_range=tv:"
        "flags=lanczos,"
        "format=yuv420p,"
        "setsar=1"
    )


def build_ffmpeg_command(
    *,
    ffmpeg_path: str,
    source_path: Path,
    output_path: Path,
) -> list[str]:
    """
    Build the deterministic FFmpeg normalization command.

    The command intentionally does not specify an output frame rate.
    Source frame timing is preserved so phase detection continues to
    operate on the cadence supplied by the recording.
    """

    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_path),
        "-map",
        "0:v:0",
        "-an",
        "-vf",
        build_scale_filter(),
        "-c:v",
        CANONICAL_VIDEO_CODEC,
        "-preset",
        CANONICAL_PRESET,
        "-crf",
        str(CANONICAL_CRF),
        "-pix_fmt",
        CANONICAL_PIXEL_FORMAT,
        "-color_range",
        "tv",
        "-fps_mode",
        "passthrough",
        "-map_metadata",
        "-1",
        "-metadata:s:v:0",
        "rotate=0",
        "-movflags",
        "+faststart",
        "-threads",
        "1",
        str(output_path),
    ]


def normalize_video(
    *,
    source_path: Path,
    output_path: Path,
) -> Path:
    """
    Convert an uploaded video into TempoAI's canonical analysis
    representation.

    The original video is never modified.
    """

    resolved_source_path = (
        source_path.expanduser().resolve()
    )
    resolved_output_path = (
        output_path.expanduser().resolve()
    )

    if not resolved_source_path.is_file():
        raise FileNotFoundError(
            "Video file not found: "
            f"{resolved_source_path}"
        )

    if (
        resolved_source_path
        == resolved_output_path
    ):
        raise ValueError(
            "The normalized analysis video must not overwrite "
            "the original uploaded video."
        )

    resolved_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ffmpeg_path = get_ffmpeg_executable()

    command = build_ffmpeg_command(
        ffmpeg_path=ffmpeg_path,
        source_path=resolved_source_path,
        output_path=resolved_output_path,
    )

    try:
        completed_process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise RuntimeError(
            "Unable to start FFmpeg while normalizing "
            f"the uploaded video: {error}"
        ) from error

    if completed_process.returncode != 0:
        diagnostics = (
            completed_process.stderr.strip()
            or completed_process.stdout.strip()
            or "FFmpeg did not provide diagnostic output."
        )

        raise RuntimeError(
            "Unable to normalize the uploaded video. "
            f"FFmpeg reported: {diagnostics}"
        )

    if (
        not resolved_output_path.is_file()
        or resolved_output_path.stat().st_size <= 0
    ):
        raise RuntimeError(
            "FFmpeg completed without creating a valid "
            "normalized analysis video."
        )

    return resolved_output_path


@contextmanager
def normalized_analysis_video(
    source_path: Path,
) -> Iterator[NormalizedAnalysisVideo]:
    """
    Create a temporary canonical video for the analysis pipeline.

    The temporary directory and normalized video are removed
    automatically when processing finishes or raises an exception.
    """

    resolved_source_path = (
        source_path.expanduser().resolve()
    )

    if not resolved_source_path.is_file():
        raise FileNotFoundError(
            "Video file not found: "
            f"{resolved_source_path}"
        )

    with tempfile.TemporaryDirectory(
        prefix="tempo-ai-analysis-",
    ) as temporary_directory:
        temporary_path = Path(
            temporary_directory
        )

        normalized_path = (
            temporary_path
            / (
                f"{resolved_source_path.stem}"
                "-normalized"
                f"{CANONICAL_CONTAINER_EXTENSION}"
            )
        )

        analysis_path = normalize_video(
            source_path=resolved_source_path,
            output_path=normalized_path,
        )

        yield NormalizedAnalysisVideo(
            source_path=resolved_source_path,
            analysis_path=analysis_path,
        )