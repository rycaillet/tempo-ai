import { useEffect } from "react";
import {
  CheckCircle2,
  Gauge,
  Info,
  Target,
  X,
} from "lucide-react";

import type {
  SwingFinding,
  SwingMetric,
} from "../../types/analysis";
import Badge from "../ui/Badge";

type MetricDetailDrawerProps = {
  metric: SwingMetric | null;
  finding: SwingFinding | null;
  onClose: () => void;
};

function formatMetricValue(
  value: string | null,
) {
  return value ?? "Unavailable";
}

function formatPercentage(
  value: number | null,
) {
  if (value === null) {
    return "Unavailable";
  }

  return `${Math.round(value * 100)}%`;
}

function formatWeight(
  value: number | null,
) {
  if (value === null) {
    return "Unavailable";
  }

  return `${value.toFixed(
    Number.isInteger(value) ? 0 : 1,
  )}%`;
}

function MetricDetailDrawer({
  metric,
  finding,
  onClose,
}: MetricDetailDrawerProps) {
  useEffect(() => {
    if (!metric) {
      return;
    }

    const previousOverflow =
      document.body.style.overflow;

    document.body.style.overflow =
      "hidden";

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown,
    );

    return () => {
      document.body.style.overflow =
        previousOverflow;

      window.removeEventListener(
        "keydown",
        handleKeyDown,
      );
    };
  }, [metric, onClose]);

  if (!metric) {
    return null;
  }

  const confidenceAvailable =
    metric.confidence !== null;

  const completenessAvailable =
    metric.measurementCompleteness !== null;

  return (
    <div
      aria-labelledby="metric-detail-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex justify-end"
      role="dialog"
    >
      <button
        aria-label="Close metric details"
        className="absolute inset-0 bg-black/40 transition-opacity duration-300"
        type="button"
        onClick={onClose}
      />

      <div className="relative z-10 flex h-full w-full max-w-2xl flex-col overflow-hidden border-l border-white/10 bg-canvas-deep shadow-2xl">
        <div className="flex items-start justify-between gap-5 border-b border-white/10 px-6 py-6 sm:px-8">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                Metric details
              </p>

              {metric.scoreStatus && (
                <Badge variant="success">
                  {formatMetricValue(
                    metric.scoreStatus,
                  )}
                </Badge>
              )}
            </div>

            <h2
              id="metric-detail-title"
              className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white"
            >
              {metric.label}
            </h2>

            <p className="mt-2 text-sm text-ice">
              {metric.phase} phase
            </p>
          </div>

          <button
            aria-label="Close metric details"
            className="flex size-11 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/5 text-copy-muted transition hover:bg-white/10 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-lime-soft/60"
            type="button"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-7 sm:px-8">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-lime-soft/15 bg-lime-soft/[0.05] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                Score
              </p>

              <p className="mt-3 font-display text-5xl font-semibold tracking-[-0.05em] text-white">
                {metric.score}
              </p>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-lime-soft"
                  style={{
                    width: `${metric.score}%`,
                  }}
                />
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                Classification
              </p>

              <p className="mt-3 font-display text-2xl font-semibold text-white">
                {formatMetricValue(
                  metric.classification,
                )}
              </p>

              <p className="mt-3 text-sm leading-6 text-copy-muted">
                The engine classification associated
                with this measured result.
              </p>
            </div>
          </div>

          <section className="mt-8">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-2xl bg-ice/10 text-ice">
                <Gauge size={19} />
              </div>

              <h3 className="font-display text-xl font-semibold text-white">
                Measurement quality
              </h3>
            </div>

            <dl className="mt-5 divide-y divide-white/10 rounded-3xl border border-white/10 bg-white/[0.025] px-5">
              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Confidence
                </dt>

                <dd className="text-sm font-semibold text-white">
                  {formatPercentage(
                    metric.confidence,
                  )}
                </dd>
              </div>

              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Measurement completeness
                </dt>

                <dd className="text-sm font-semibold text-white">
                  {formatPercentage(
                    metric.measurementCompleteness,
                  )}
                </dd>
              </div>

              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Scoring weight
                </dt>

                <dd className="text-sm font-semibold text-white">
                  {formatWeight(
                    metric.configuredWeight,
                  )}
                </dd>
              </div>

              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Weighted contribution
                </dt>

                <dd className="text-sm font-semibold text-white">
                  {metric.weightedContribution !==
                  null
                    ? metric.weightedContribution.toFixed(
                        1,
                      )
                    : "Unavailable"}
                </dd>
              </div>
            </dl>

            {(!confidenceAvailable ||
              !completenessAvailable) && (
              <p className="mt-3 text-xs leading-5 text-copy-subtle">
                Some quality fields were not available
                in this analysis version.
              </p>
            )}
          </section>

          <section className="mt-8">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                <Info size={19} />
              </div>

              <h3 className="font-display text-xl font-semibold text-white">
                What this measures
              </h3>
            </div>

            <p className="mt-4 leading-7 text-copy-muted">
              {metric.description}
            </p>

            <dl className="mt-5 divide-y divide-white/10 rounded-3xl border border-white/10 bg-white/[0.025] px-5">
              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Feedback status
                </dt>

                <dd className="text-right text-sm font-semibold text-white">
                  {formatMetricValue(
                    metric.feedbackStatus,
                  )}
                </dd>
              </div>

              <div className="flex items-center justify-between gap-5 py-4">
                <dt className="text-sm text-copy-muted">
                  Delivery status
                </dt>

                <dd className="text-right text-sm font-semibold text-white">
                  {formatMetricValue(
                    metric.deliveryStatus,
                  )}
                </dd>
              </div>
            </dl>
          </section>

          {finding && (
            <section className="mt-8">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-2xl bg-warning/10 text-warning">
                  <Target size={19} />
                </div>

                <div>
                  <h3 className="font-display text-xl font-semibold text-white">
                    Related coaching priority
                  </h3>

                  <p className="mt-1 text-sm text-copy-subtle">
                    Priority {finding.priority}
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-3xl border border-warning/15 bg-warning/[0.04] p-5">
                <div className="flex flex-wrap items-center gap-3">
                  <p className="font-display text-xl font-semibold text-white">
                    {finding.title}
                  </p>

                  <Badge variant="warning">
                    {finding.severity} priority
                  </Badge>
                </div>

                <p className="mt-4 leading-7 text-copy-muted">
                  {finding.explanation}
                </p>

                <div className="mt-5 border-t border-white/10 pt-5">
                  <p className="text-sm font-semibold text-white">
                    Supporting evidence
                  </p>

                  <p className="mt-2 text-sm leading-6 text-copy-muted">
                    {finding.evidence}
                  </p>
                </div>

                <div className="mt-5 border-t border-white/10 pt-5">
                  <div className="flex items-center gap-2">
                    <CheckCircle2
                      className="text-lime-soft"
                      size={17}
                    />

                    <p className="text-sm font-semibold text-white">
                      {finding.drill.name}
                    </p>
                  </div>

                  <p className="mt-2 text-sm leading-6 text-copy-muted">
                    {finding.drill.instructions}
                  </p>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

export default MetricDetailDrawer;