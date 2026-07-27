from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


MetricContext = Mapping[str, Any]
MetricResult = dict[str, Any]

MetricBuilder = Callable[[MetricContext], MetricResult]

FeedbackApplicator = Callable[
    [MetricResult, dict[str, Any], str],
    MetricResult,
]


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


def validate_metric_registry(
    definitions: Iterable[MetricDefinition],
) -> None:
    metric_keys: set[str] = set()
    summary_keys: set[str] = set()

    for definition in definitions:
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


def get_registered_metric_keys(
    definitions: Iterable[MetricDefinition],
) -> tuple[str, ...]:
    return tuple(
        definition.key
        for definition in definitions
    )


def build_registered_metrics(
    definitions: Iterable[MetricDefinition],
    context: MetricContext,
    feedback_eligibility: dict[str, Any],
    apply_feedback: FeedbackApplicator,
) -> dict[str, MetricResult]:
    definition_list = tuple(definitions)

    validate_metric_registry(definition_list)

    results: dict[str, MetricResult] = {}

    for definition in definition_list:
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
    definitions: Iterable[MetricDefinition],
    metric_results: Mapping[str, MetricResult],
) -> dict[str, Any]:
    definition_list = tuple(definitions)

    validate_metric_registry(definition_list)

    summary: dict[str, Any] = {}

    for definition in definition_list:
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