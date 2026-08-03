from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ANALYSIS_ENGINE_NAME = "tempo-ai-analysis-engine"
ANALYSIS_ENGINE_VERSION = "1.0.0"


def build_analysis_version_manifest(
    *,
    contract_version: str,
    metric_versions: Mapping[str, str],
    coaching_prompt_version: str,
) -> dict[str, Any]:
    """
    Build static reproducibility metadata for one analysis report.

    Runtime-specific fields such as processing timestamp and duration
    are added later by the pipeline API-contract layer.
    """

    return {
        "name": ANALYSIS_ENGINE_NAME,
        "version": ANALYSIS_ENGINE_VERSION,
        "contractVersion": contract_version,
        "coachingPromptVersion": coaching_prompt_version,
        "metricVersions": dict(metric_versions),
    }


def build_execution_metadata(
    *,
    processed_at: str,
    duration_milliseconds: float,
) -> dict[str, Any]:
    """
    Build runtime metadata for one completed pipeline execution.
    """

    if not isinstance(processed_at, str) or not processed_at:
        raise ValueError(
            "Processed timestamp must be a nonempty string."
        )

    if (
        isinstance(duration_milliseconds, bool)
        or not isinstance(
            duration_milliseconds,
            (int, float),
        )
        or float(duration_milliseconds) < 0.0
    ):
        raise ValueError(
            "Execution duration must be a non-negative number."
        )

    return {
        "processedAt": processed_at,
        "durationMilliseconds": round(
            float(duration_milliseconds),
            3,
        ),
    }