from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

MetricContext = Mapping[str, Any]
MetricResult = dict[str, Any]

MetricBuilder = Callable[[MetricContext], MetricResult]

FeedbackApplicator = Callable[
    [MetricResult, dict[str, Any], str],
    MetricResult,
]

VERSION_PATTERN = re.compile(
    r"^\d+\.\d+(?:\.\d+)?$"
)


@dataclass(frozen=True)
class SummaryField:
    output_key: str
    value_path: tuple[str, ...]


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    display_name: str
    builder: MetricBuilder
    summary_fields: tuple[SummaryField, ...] = ()


@dataclass(frozen=True)
class MetricRegistration:
    definition: MetricDefinition
    enabled: bool = True
    version: str = "1.0.0"
    scoring_weight: float = 0.0


def validate_metric_registry(
    registrations: Iterable[MetricRegistration],
) -> None:
    registration_list = tuple(registrations)

    metric_keys: set[str] = set()
    summary_keys: set[str] = set()

    for registration in registration_list:
        definition = registration.definition

        if not isinstance(registration.enabled, bool):
            raise ValueError(
                "Metric registration enabled state must be a boolean: "
                f"{definition.key}"
            )

        if (
            not isinstance(registration.version, str)
            or not VERSION_PATTERN.fullmatch(
                registration.version
            )
        ):
            raise ValueError(
                "Metric registration version must use numeric "
                "major.minor or major.minor.patch format: "
                f"{definition.key}"
            )

        scoring_weight = registration.scoring_weight

        if (
            isinstance(scoring_weight, bool)
            or not isinstance(scoring_weight, (int, float))
            or not math.isfinite(float(scoring_weight))
            or float(scoring_weight) < 0.0
        ):
            raise ValueError(
                "Metric registration scoring weight must be a "
                "finite non-negative number: "
                f"{definition.key}"
            )

        if definition.key in metric_keys:
            raise ValueError(
                "Metric registry contains duplicate metric key: "
                f"{definition.key}"
            )

        metric_keys.add(definition.key)

        for summary_field in definition.summary_fields:
            if summary_field.output_key in summary_keys:
                raise ValueError(
                    "Metric registry contains duplicate summary key: "
                    f"{summary_field.output_key}"
                )

            summary_keys.add(summary_field.output_key)


def get_enabled_metric_registrations(
    registrations: Iterable[MetricRegistration],
) -> tuple[MetricRegistration, ...]:
    registration_list = tuple(registrations)

    validate_metric_registry(registration_list)

    return tuple(
        registration
        for registration in registration_list
        if registration.enabled
    )


def get_score_enabled_metric_registrations(
    registrations: Iterable[MetricRegistration],
) -> tuple[MetricRegistration, ...]:
    return tuple(
        registration
        for registration in get_enabled_metric_registrations(
            registrations
        )
        if registration.scoring_weight > 0.0
    )


def validate_scoring_weights(
    registrations: Iterable[MetricRegistration],
    expected_total: float = 100.0,
    tolerance: float = 1e-6,
) -> None:
    if (
        isinstance(expected_total, bool)
        or not isinstance(expected_total, (int, float))
        or not math.isfinite(float(expected_total))
        or float(expected_total) <= 0.0
    ):
        raise ValueError(
            "Expected scoring weight total must be a finite "
            "positive number."
        )

    if (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or not math.isfinite(float(tolerance))
        or float(tolerance) < 0.0
    ):
        raise ValueError(
            "Scoring weight tolerance must be a finite "
            "non-negative number."
        )

    score_enabled_registrations = (
        get_score_enabled_metric_registrations(
            registrations
        )
    )

    if not score_enabled_registrations:
        raise ValueError(
            "Metric registry does not contain any enabled "
            "score-weighted metrics."
        )

    total_weight = sum(
        float(registration.scoring_weight)
        for registration in score_enabled_registrations
    )

    if not math.isclose(
        total_weight,
        float(expected_total),
        abs_tol=float(tolerance),
        rel_tol=0.0,
    ):
        raise ValueError(
            "Enabled metric scoring weights must total "
            f"{float(expected_total):g}; received "
            f"{total_weight:g}."
        )


def get_registered_metric_keys(
    registrations: Iterable[MetricRegistration],
    *,
    enabled_only: bool = False,
) -> tuple[str, ...]:
    registration_list = tuple(registrations)

    validate_metric_registry(registration_list)

    if enabled_only:
        registration_list = (
            get_enabled_metric_registrations(
                registration_list
            )
        )

    return tuple(
        registration.definition.key
        for registration in registration_list
    )


def build_registered_metrics(
    registrations: Iterable[MetricRegistration],
    context: MetricContext,
    feedback_eligibility: dict[str, Any],
    apply_feedback: FeedbackApplicator,
) -> dict[str, MetricResult]:
    enabled_registrations = (
        get_enabled_metric_registrations(
            registrations
        )
    )

    results: dict[str, MetricResult] = {}

    for registration in enabled_registrations:
        definition = registration.definition
        metrics = definition.builder(context)

        results[definition.key] = apply_feedback(
            metrics,
            feedback_eligibility,
            definition.display_name,
        )

    return results


def get_nested_value(
    data: Mapping[str, Any],
    path: tuple[str, ...],
) -> Any:
    current_value: Any = data

    for key in path:
        if not isinstance(current_value, Mapping):
            raise ValueError(
                "Cannot read registered summary path "
                f"{'.'.join(path)}."
            )

        if key not in current_value:
            raise ValueError(
                "Registered summary path is missing key "
                f"{key}: {'.'.join(path)}"
            )

        current_value = current_value[key]

    return current_value


def build_registered_metric_summary(
    registrations: Iterable[MetricRegistration],
    metric_results: Mapping[str, MetricResult],
) -> dict[str, Any]:
    enabled_registrations = (
        get_enabled_metric_registrations(
            registrations
        )
    )

    summary: dict[str, Any] = {}

    for registration in enabled_registrations:
        definition = registration.definition
        metrics = metric_results.get(definition.key)

        if not isinstance(metrics, Mapping):
            raise ValueError(
                "Registered metric result is missing or invalid: "
                f"{definition.key}"
            )

        for summary_field in definition.summary_fields:
            summary[summary_field.output_key] = (
                get_nested_value(
                    metrics,
                    summary_field.value_path,
                )
            )

    return summary