from __future__ import annotations

import unittest

from app.analysis.versioning import (
    ANALYSIS_ENGINE_NAME,
    ANALYSIS_ENGINE_VERSION,
    build_analysis_version_manifest,
    build_execution_metadata,
)


class AnalysisVersioningTests(unittest.TestCase):
    def test_builds_static_version_manifest(
        self,
    ) -> None:
        result = build_analysis_version_manifest(
            contract_version="1.0.0",
            metric_versions={
                "tempo": "1.0.0",
                "swingPlane": "1.0.0",
            },
            coaching_prompt_version=(
                "tempo-coach-v3"
            ),
        )

        self.assertEqual(
            result["name"],
            ANALYSIS_ENGINE_NAME,
        )
        self.assertEqual(
            result["version"],
            ANALYSIS_ENGINE_VERSION,
        )
        self.assertEqual(
            result["contractVersion"],
            "1.0.0",
        )
        self.assertEqual(
            result["metricVersions"],
            {
                "tempo": "1.0.0",
                "swingPlane": "1.0.0",
            },
        )

    def test_builds_execution_metadata(
        self,
    ) -> None:
        result = build_execution_metadata(
            processed_at=(
                "2026-08-03T18:00:00Z"
            ),
            duration_milliseconds=1234.56789,
        )

        self.assertEqual(
            result,
            {
                "processedAt": (
                    "2026-08-03T18:00:00Z"
                ),
                "durationMilliseconds": 1234.568,
            },
        )

    def test_rejects_invalid_execution_metadata(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "timestamp",
        ):
            build_execution_metadata(
                processed_at="",
                duration_milliseconds=1.0,
            )

        with self.assertRaisesRegex(
            ValueError,
            "duration",
        ):
            build_execution_metadata(
                processed_at=(
                    "2026-08-03T18:00:00Z"
                ),
                duration_milliseconds=-1.0,
            )


if __name__ == "__main__":
    unittest.main()