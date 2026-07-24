from __future__ import annotations

import json
import sys
from pathlib import Path

from app.pose_detector import analyze_video_pose


def print_result(payload: dict[str, object]) -> None:
    print(json.dumps(payload))


def main() -> None:
    if len(sys.argv) != 2:
        print_result(
            {
                "success": False,
                "error": "Usage: python -m app.main <video-path>",
            }
        )
        raise SystemExit(1)

    video_path = Path(sys.argv[1]).expanduser().resolve()

    if not video_path.is_file():
        print_result(
            {
                "success": False,
                "error": f"Video file not found: {video_path}",
            }
        )
        raise SystemExit(1)

    try:
        result = analyze_video_pose(video_path)
    except (ValueError, RuntimeError) as error:
        print_result(
            {
                "success": False,
                "error": str(error),
            }
        )
        raise SystemExit(1) from error

    print_result(
        {
            "success": True,
            "videoPath": str(video_path),
            **result,
        }
    )


if __name__ == "__main__":
    main()