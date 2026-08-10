from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.video_normalizer import (
    CANONICAL_LONG_EDGE_PIXELS,
    build_ffmpeg_command,
    build_scale_filter,
    normalize_video,
    normalized_analysis_video,
)


def test_build_scale_filter_uses_deterministic_dimensions():
    scale_filter = build_scale_filter()

    assert (
        str(CANONICAL_LONG_EDGE_PIXELS)
        in scale_filter
    )

    assert "if(gte(iw,ih)" in scale_filter
    assert "trunc(" in scale_filter

    assert (
        "force_original_aspect_ratio"
        not in scale_filter
    )

    assert (
        "force_divisible_by"
        not in scale_filter
    )

    assert "in_range=auto" in scale_filter
    assert "out_range=tv" in scale_filter
    assert "format=yuv420p" in scale_filter
    assert "setsar=1" in scale_filter


def test_build_ffmpeg_command_uses_canonical_video_format(
    tmp_path: Path,
):
    source_path = tmp_path / "input.mov"
    output_path = tmp_path / "output.mp4"

    command = build_ffmpeg_command(
        ffmpeg_path="/usr/bin/ffmpeg",
        source_path=source_path,
        output_path=output_path,
    )

    assert command[0] == "/usr/bin/ffmpeg"

    assert "-c:v" in command
    assert (
        command[
            command.index("-c:v") + 1
        ]
        == "libx264"
    )

    assert "-pix_fmt" in command
    assert (
        command[
            command.index("-pix_fmt") + 1
        ]
        == "yuv420p"
    )

    assert "-color_range" in command
    assert (
        command[
            command.index("-color_range") + 1
        ]
        == "tv"
    )

    assert "-fps_mode" in command
    assert (
        command[
            command.index("-fps_mode") + 1
        ]
        == "passthrough"
    )

    assert "-map_metadata" in command
    assert (
        command[
            command.index("-map_metadata") + 1
        ]
        == "-1"
    )

    assert "-threads" in command
    assert (
        command[
            command.index("-threads") + 1
        ]
        == "1"
    )

    assert command[-1] == str(output_path)


def test_normalize_video_rejects_missing_source(
    tmp_path: Path,
):
    source_path = tmp_path / "missing.mov"
    output_path = tmp_path / "output.mp4"

    with pytest.raises(
        FileNotFoundError,
        match="Video file not found",
    ):
        normalize_video(
            source_path=source_path,
            output_path=output_path,
        )


def test_normalize_video_does_not_overwrite_source(
    tmp_path: Path,
):
    source_path = tmp_path / "video.mp4"
    source_path.write_bytes(b"video")

    with pytest.raises(
        ValueError,
        match="must not overwrite",
    ):
        normalize_video(
            source_path=source_path,
            output_path=source_path,
        )


def test_normalize_video_reports_missing_ffmpeg(
    tmp_path: Path,
):
    source_path = tmp_path / "video.mov"
    source_path.write_bytes(b"video")

    output_path = tmp_path / "output.mp4"

    with patch(
        "app.video_normalizer.shutil.which",
        return_value=None,
    ):
        with pytest.raises(
            RuntimeError,
            match="FFmpeg is required",
        ):
            normalize_video(
                source_path=source_path,
                output_path=output_path,
            )


def test_normalize_video_reports_ffmpeg_failure(
    tmp_path: Path,
):
    source_path = tmp_path / "video.mov"
    source_path.write_bytes(b"video")

    output_path = tmp_path / "output.mp4"

    completed_process = (
        subprocess.CompletedProcess(
            args=["ffmpeg"],
            returncode=1,
            stdout="",
            stderr="decoder failed",
        )
    )

    with patch(
        "app.video_normalizer.shutil.which",
        return_value="/usr/bin/ffmpeg",
    ), patch(
        "app.video_normalizer.subprocess.run",
        return_value=completed_process,
    ):
        with pytest.raises(
            RuntimeError,
            match="decoder failed",
        ):
            normalize_video(
                source_path=source_path,
                output_path=output_path,
            )


def test_normalize_video_returns_created_output(
    tmp_path: Path,
):
    source_path = tmp_path / "video.mov"
    source_path.write_bytes(b"video")

    output_path = tmp_path / "output.mp4"

    def fake_run(
        command: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        Path(command[-1]).write_bytes(
            b"normalized-video"
        )

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        )

    with patch(
        "app.video_normalizer.shutil.which",
        return_value="/usr/bin/ffmpeg",
    ), patch(
        "app.video_normalizer.subprocess.run",
        side_effect=fake_run,
    ):
        result = normalize_video(
            source_path=source_path,
            output_path=output_path,
        )

    assert result == output_path.resolve()
    assert result.read_bytes() == (
        b"normalized-video"
    )


def test_normalized_analysis_video_cleans_up_workspace(
    tmp_path: Path,
):
    source_path = tmp_path / "video.mov"
    source_path.write_bytes(b"video")

    created_analysis_path: Path | None = None

    def fake_normalize_video(
        *,
        source_path: Path,
        output_path: Path,
    ) -> Path:
        assert source_path.is_file()

        output_path.write_bytes(
            b"normalized-video"
        )

        return output_path.resolve()

    with patch(
        "app.video_normalizer.normalize_video",
        side_effect=fake_normalize_video,
    ):
        with normalized_analysis_video(
            source_path
        ) as normalized:
            created_analysis_path = (
                normalized.analysis_path
            )

            assert (
                normalized.source_path
                == source_path.resolve()
            )

            assert (
                normalized.analysis_path
                .is_file()
            )

            assert (
                normalized.analysis_path.suffix
                == ".mp4"
            )

    assert created_analysis_path is not None
    assert not created_analysis_path.exists()
    assert (
        not created_analysis_path.parent.exists()
    )