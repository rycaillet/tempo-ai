from __future__ import annotations

import math
from typing import Any


DEFAULT_DECIMAL_PLACES = 2


def round_score(
    value: float,
    decimal_places: int = DEFAULT_DECIMAL_PLACES,
) -> float:
    return round(float(value), decimal_places)


def normalize_confidence(value: Any) -> float | None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        return None

    return min(max(float(value), 0.0), 1.0)


def calculate_normalized_weight(
    configured_weight: float,
    available_weight: float,
) -> float:
    if available_weight <= 0.0:
        return 0.0

    return configured_weight / available_weight * 100.0


def calculate_weighted_contribution(
    raw_score: float,
    configured_weight: float,
    available_weight: float,
) -> float:
    if available_weight <= 0.0:
        return 0.0

    return raw_score * configured_weight / available_weight


def calculate_weighted_average(
    weighted_value_total: float,
    available_weight: float,
) -> float | None:
    if available_weight <= 0.0:
        return None

    return weighted_value_total / available_weight


def calculate_percentage(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0.0:
        return 0.0

    return numerator / denominator * 100.0