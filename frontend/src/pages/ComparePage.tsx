import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  CircleAlert,
  GitCompareArrows,
  LoaderCircle,
  Pause,
  Play,
  RotateCcw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import Section from "../components/ui/Section";
import {
  getAnalysis,
  getAnalysisRecords,
  type AnalysisRecord,
} from "../services/analysisService";
import type {
  SwingAnalysis,
  SwingMetric,
  SwingPhase,
} from "../types/analysis";

type ComparisonMetric = {
  id: string;
  label: string;
  baselineScore: number | null;
  comparisonScore: number | null;
  difference: number | null;
};

function formatAnalysisDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function createAnalysisLabel(record: AnalysisRecord) {
  const filename = record.originalFilename
    .replace(/\.[^/.]+$/, "")
    .replace(/[-_]+/g, " ")
    .trim();

  const title = filename
    ? filename.replace(
        /\b\w/g,
        (character) => character.toUpperCase(),
      )
    : "Swing Analysis";

  return `${title} · ${formatAnalysisDate(
    record.createdAt,
  )}`;
}

function getMetricMap(metrics: SwingMetric[]) {
  return new Map(
    metrics.map((metric) => [
      metric.id,
      metric,
    ]),
  );
}

function buildMetricComparisons(
  baseline: SwingAnalysis,
  comparison: SwingAnalysis,
): ComparisonMetric[] {
  const baselineMetrics = getMetricMap(
    baseline.metrics,
  );

  const comparisonMetrics = getMetricMap(
    comparison.metrics,
  );

  const metricIds = Array.from(
    new Set([
      ...baseline.metrics.map(
        (metric) => metric.id,
      ),
      ...comparison.metrics.map(
        (metric) => metric.id,
      ),
    ]),
  );

  return metricIds.map((metricId) => {
    const baselineMetric =
      baselineMetrics.get(metricId);

    const comparisonMetric =
      comparisonMetrics.get(metricId);

    const baselineScore =
      baselineMetric?.score ?? null;

    const comparisonScore =
      comparisonMetric?.score ?? null;

    return {
      id: metricId,
      label:
        comparisonMetric?.label ??
        baselineMetric?.label ??
        metricId,
      baselineScore,
      comparisonScore,
      difference:
        baselineScore !== null &&
        comparisonScore !== null
          ? comparisonScore - baselineScore
          : null,
    };
  });
}

function getPhaseTimeSeconds(
  phase: SwingPhase | undefined,
) {
  if (!phase) {
    return 0;
  }

  const parsedTime = Number.parseFloat(
    phase.timestamp.replace("s", ""),
  );

  if (
    !Number.isFinite(parsedTime) ||
    parsedTime < 0
  ) {
    return 0;
  }

  return parsedTime;
}

function findPhase(
  analysis: SwingAnalysis,
  phaseId: string,
) {
  return analysis.phases.find(
    (phase) => phase.id === phaseId,
  );
}

function seekVideoToPhase(
  video: HTMLVideoElement | null,
  analysis: SwingAnalysis,
  phaseId: string,
) {
  if (!video) {
    return;
  }

  const phaseTime = getPhaseTimeSeconds(
    findPhase(analysis, phaseId),
  );

  const maximumTime =
    Number.isFinite(video.duration) &&
    video.duration > 0
      ? video.duration
      : phaseTime;

  video.currentTime = Math.min(
    phaseTime,
    maximumTime,
  );
}

function ScoreDifference({
  difference,
}: {
  difference: number | null;
}) {
  if (difference === null) {
    return (
      <span className="text-sm font-semibold text-copy-subtle">
        Not comparable
      </span>
    );
  }

  if (difference === 0) {
    return (
      <span className="text-sm font-semibold text-copy-muted">
        No change
      </span>
    );
  }

  const improved = difference > 0;
  const Icon = improved
    ? TrendingUp
    : TrendingDown;

  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 text-sm font-semibold",
        improved
          ? "text-lime-soft"
          : "text-warning",
      ].join(" ")}
    >
      <Icon size={15} />

      {improved ? "+" : ""}
      {difference}
    </span>
  );
}

function ComparePage() {
  const [searchParams, setSearchParams] =
    useSearchParams();

  const requestedBaselineId =
    searchParams.get("baselineId");

  const requestedComparisonId =
    searchParams.get("comparisonId");

  const baselineVideoRef =
    useRef<HTMLVideoElement | null>(null);

  const comparisonVideoRef =
    useRef<HTMLVideoElement | null>(null);

  const [records, setRecords] = useState<
    AnalysisRecord[]
  >([]);

  const [baselineId, setBaselineId] =
    useState(requestedBaselineId ?? "");

  const [comparisonId, setComparisonId] =
    useState(requestedComparisonId ?? "");

  const [baseline, setBaseline] =
    useState<SwingAnalysis | null>(null);

  const [comparison, setComparison] =
    useState<SwingAnalysis | null>(null);

  const [isLoadingRecords, setIsLoadingRecords] =
    useState(true);

  const [
    isLoadingComparison,
    setIsLoadingComparison,
  ] = useState(false);

  const [
    selectedPhaseId,
    setSelectedPhaseId,
  ] = useState("address");

  const [
    isComparisonPlaying,
    setIsComparisonPlaying,
  ] = useState(false);

  const [error, setError] = useState("");

  const [playbackError, setPlaybackError] =
    useState("");

  useEffect(() => {
    let isCancelled = false;

    async function loadRecords() {
      try {
        setError("");
        setIsLoadingRecords(true);

        const analysisRecords =
          await getAnalysisRecords();

        if (isCancelled) {
          return;
        }

        const completedRecords =
          analysisRecords.filter(
            (record) =>
              record.status === "COMPLETED" &&
              record.analysisPayload !== null,
          );

        setRecords(completedRecords);

        const initialBaselineId =
          requestedBaselineId &&
          completedRecords.some(
            (record) =>
              record.id === requestedBaselineId,
          )
            ? requestedBaselineId
            : completedRecords[0]?.id ?? "";

        const initialComparisonId =
          requestedComparisonId &&
          completedRecords.some(
            (record) =>
              record.id === requestedComparisonId,
          )
            ? requestedComparisonId
            : completedRecords.find(
                (record) =>
                  record.id !== initialBaselineId,
              )?.id ?? "";

        setBaselineId(initialBaselineId);
        setComparisonId(initialComparisonId);
      } catch (caughtError) {
        if (isCancelled) {
          return;
        }

        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "TempoAI could not load your swing history.",
        );
      } finally {
        if (!isCancelled) {
          setIsLoadingRecords(false);
        }
      }
    }

    void loadRecords();

    return () => {
      isCancelled = true;
    };
  }, [
    requestedBaselineId,
    requestedComparisonId,
  ]);

  useEffect(() => {
    if (
      !baselineId ||
      !comparisonId ||
      baselineId === comparisonId
    ) {
      return;
    }

    let isCancelled = false;

    async function loadComparison() {
      try {
        setError("");
        setIsLoadingComparison(true);

        const [
          baselineAnalysis,
          comparisonAnalysis,
        ] = await Promise.all([
          getAnalysis(baselineId),
          getAnalysis(comparisonId),
        ]);

        if (isCancelled) {
          return;
        }

        setBaseline(baselineAnalysis);
        setComparison(comparisonAnalysis);

        setSearchParams(
          {
            baselineId,
            comparisonId,
          },
          {
            replace: true,
          },
        );
      } catch (caughtError) {
        if (isCancelled) {
          return;
        }

        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "TempoAI could not compare these swings.",
        );
      } finally {
        if (!isCancelled) {
          setIsLoadingComparison(false);
        }
      }
    }

    void loadComparison();

    return () => {
      isCancelled = true;
    };
  }, [
    baselineId,
    comparisonId,
    setSearchParams,
  ]);

  const metricComparisons = useMemo(
    () =>
      baseline && comparison
        ? buildMetricComparisons(
            baseline,
            comparison,
          )
        : [],
    [baseline, comparison],
  );

  const overallDifference =
    baseline && comparison
      ? comparison.summary.overallScore -
        baseline.summary.overallScore
      : null;

  const canCompare =
    baselineId.length > 0 &&
    comparisonId.length > 0 &&
    baselineId !== comparisonId;

  const comparisonPhases =
    baseline?.phases ?? comparison?.phases ?? [];

  const selectedBaselinePhase =
    baseline
      ? findPhase(baseline, selectedPhaseId)
      : undefined;

  const selectedComparisonPhase =
    comparison
      ? findPhase(comparison, selectedPhaseId)
      : undefined;

  const hasBothVideos = Boolean(
    baseline?.videoUrl &&
      comparison?.videoUrl,
  );

  function pauseComparisonVideos() {
    baselineVideoRef.current?.pause();
    comparisonVideoRef.current?.pause();
    setIsComparisonPlaying(false);
  }

  function handlePhaseSelect(
    phaseId: string,
  ) {
    if (!baseline || !comparison) {
      return;
    }

    pauseComparisonVideos();
    setPlaybackError("");
    setSelectedPhaseId(phaseId);

    seekVideoToPhase(
      baselineVideoRef.current,
      baseline,
      phaseId,
    );

    seekVideoToPhase(
      comparisonVideoRef.current,
      comparison,
      phaseId,
    );
  }

  async function handleSharedPlay() {
    const baselineVideo =
      baselineVideoRef.current;

    const comparisonVideo =
      comparisonVideoRef.current;

    if (
      !baselineVideo ||
      !comparisonVideo ||
      !hasBothVideos
    ) {
      setPlaybackError(
        "Both analyses need an available video for synchronized playback.",
      );

      return;
    }

    try {
      setPlaybackError("");

      await Promise.all([
        baselineVideo.play(),
        comparisonVideo.play(),
      ]);

      setIsComparisonPlaying(true);
    } catch {
      baselineVideo.pause();
      comparisonVideo.pause();
      setIsComparisonPlaying(false);

      setPlaybackError(
        "The browser could not begin synchronized playback.",
      );
    }
  }

  function handleRestart() {
    pauseComparisonVideos();
    setPlaybackError("");
    setSelectedPhaseId("address");

    if (baselineVideoRef.current) {
      baselineVideoRef.current.currentTime = 0;
    }

    if (comparisonVideoRef.current) {
      comparisonVideoRef.current.currentTime = 0;
    }
  }

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <Link
            className="inline-flex items-center gap-2 text-sm font-semibold text-copy-muted transition hover:text-white"
            to="/history"
          >
            <ArrowLeft size={17} />
            Return to history
          </Link>

          <div className="mt-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
                Measure your progress
              </p>

              <h1 className="mt-4 font-display text-5xl font-semibold tracking-[-0.05em] text-white">
                Compare swings
              </h1>

              <p className="mt-5 max-w-2xl text-lg leading-8 text-copy-muted">
                Select two completed analyses to compare
                scores, measured mechanics, and coaching
                priorities.
              </p>
            </div>

            <Button to="/analysis/new">
              Analyze new swing
              <ArrowRight size={17} />
            </Button>
          </div>

          <Panel
            className="mt-12"
            padding="lg"
            variant="raised"
          >
            <div className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                <GitCompareArrows size={21} />
              </div>

              <div>
                <h2 className="font-display text-2xl font-semibold text-white">
                  Select analyses
                </h2>

                <p className="mt-1 text-sm text-copy-muted">
                  The second swing is compared against
                  the baseline.
                </p>
              </div>
            </div>

            {isLoadingRecords ? (
              <div className="mt-8 flex items-center gap-3 text-copy-muted">
                <LoaderCircle
                  className="animate-spin"
                  size={19}
                />
                Loading swing history
              </div>
            ) : records.length < 2 ? (
              <div className="mt-8 rounded-2xl border border-warning/20 bg-warning/5 p-5">
                <div className="flex items-start gap-3">
                  <CircleAlert
                    className="mt-0.5 shrink-0 text-warning"
                    size={20}
                  />

                  <div>
                    <p className="font-semibold text-white">
                      Two completed analyses are required
                    </p>

                    <p className="mt-2 text-sm leading-6 text-copy-muted">
                      Upload and complete another swing
                      analysis before using comparison.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_auto_1fr] lg:items-end">
                <label>
                  <span className="text-sm font-semibold text-white">
                    Baseline swing
                  </span>

                  <select
                    className="mt-3 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                    value={baselineId}
                    onChange={(event) =>
                      setBaselineId(
                        event.target.value,
                      )
                    }
                  >
                    {records.map((record) => (
                      <option
                        key={record.id}
                        value={record.id}
                      >
                        {createAnalysisLabel(record)}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="hidden pb-3 text-copy-subtle lg:block">
                  <ArrowRight size={20} />
                </div>

                <label>
                  <span className="text-sm font-semibold text-white">
                    Comparison swing
                  </span>

                  <select
                    className="mt-3 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition focus:border-lime-soft/50 focus:ring-2 focus:ring-lime-soft/20"
                    value={comparisonId}
                    onChange={(event) =>
                      setComparisonId(
                        event.target.value,
                      )
                    }
                  >
                    {records.map((record) => (
                      <option
                        key={record.id}
                        value={record.id}
                      >
                        {createAnalysisLabel(record)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            )}

            {baselineId === comparisonId &&
              baselineId.length > 0 && (
                <p className="mt-5 text-sm font-medium text-warning">
                  Select two different analyses.
                </p>
              )}
          </Panel>

          {error && (
            <Panel
              className="mt-6 border-red-400/20 bg-red-400/5"
              variant="default"
            >
              <div className="flex items-start gap-3">
                <CircleAlert
                  className="mt-0.5 shrink-0 text-red-300"
                  size={20}
                />

                <p className="text-sm leading-6 text-red-200">
                  {error}
                </p>
              </div>
            </Panel>
          )}

          {isLoadingComparison && canCompare && (
            <div className="mt-10 flex items-center justify-center gap-3 py-14 text-copy-muted">
              <LoaderCircle
                className="animate-spin"
                size={22}
              />
              Building swing comparison
            </div>
          )}

          {!isLoadingComparison &&
            canCompare &&
            baseline &&
            comparison && (
              <>
                <div className="mt-10 grid gap-6 lg:grid-cols-2">
                  {[baseline, comparison].map(
                    (analysis, index) => (
                      <Panel
                        key={analysis.summary.id}
                        padding="lg"
                        variant="raised"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <Badge
                              variant={
                                index === 0
                                  ? "neutral"
                                  : "success"
                              }
                            >
                              {index === 0
                                ? "Baseline"
                                : "Comparison"}
                            </Badge>

                            <h2 className="mt-4 font-display text-2xl font-semibold text-white">
                              {analysis.summary.title}
                            </h2>

                            <p className="mt-2 inline-flex items-center gap-2 text-sm text-copy-muted">
                              <CalendarDays size={15} />
                              {analysis.summary.date}
                            </p>
                          </div>

                          <div className="text-right">
                            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-copy-subtle">
                              Swing score
                            </p>

                            <p className="mt-2 font-display text-5xl font-semibold text-white">
                              {
                                analysis.summary
                                  .overallScore
                              }
                            </p>
                          </div>
                        </div>

                        <p className="mt-6 border-t border-white/10 pt-6 text-sm leading-7 text-copy-muted">
                          {analysis.summary.summary}
                        </p>

                        <Link
                          className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-lime-soft transition hover:text-white"
                          to={`/analysis/${analysis.summary.id}`}
                        >
                          View full analysis
                          <ArrowRight size={15} />
                        </Link>
                      </Panel>
                    ),
                  )}
                </div>

                <Panel
                  className="mt-6"
                  padding="none"
                  variant="raised"
                >
                  <div className="flex flex-col gap-5 border-b border-white/10 px-6 py-6 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-ice">
                        Synchronized review
                      </p>

                      <h2 className="mt-3 font-display text-3xl font-semibold text-white">
                        Compare the same swing phase
                      </h2>

                      <p className="mt-2 max-w-2xl text-sm leading-6 text-copy-muted">
                        Select a phase to seek each video
                        to its independently detected
                        reference frame.
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      <Button
                        disabled={!hasBothVideos}
                        onClick={
                          isComparisonPlaying
                            ? pauseComparisonVideos
                            : () => {
                                void handleSharedPlay();
                              }
                        }
                        size="sm"
                      >
                        {isComparisonPlaying ? (
                          <>
                            <Pause size={16} />
                            Pause both
                          </>
                        ) : (
                          <>
                            <Play size={16} />
                            Play both
                          </>
                        )}
                      </Button>

                      <Button
                        onClick={handleRestart}
                        size="sm"
                        variant="secondary"
                      >
                        <RotateCcw size={16} />
                        Restart
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-px bg-white/10 lg:grid-cols-2">
                    <div className="bg-surface-raised">
                      <div className="flex items-center justify-between gap-4 px-5 py-4">
                        <Badge variant="neutral">
                          Baseline
                        </Badge>

                        <span className="text-xs font-semibold text-copy-subtle">
                          {selectedBaselinePhase?.label ??
                            "Phase unavailable"}
                          {" · "}
                          {selectedBaselinePhase?.timestamp ??
                            "—"}
                        </span>
                      </div>

                      <div className="relative aspect-video bg-black">
                        {baseline.videoUrl ? (
                          <video
                            ref={baselineVideoRef}
                            className="h-full w-full object-contain"
                            playsInline
                            preload="metadata"
                            src={baseline.videoUrl}
                            onEnded={() =>
                              setIsComparisonPlaying(false)
                            }
                          >
                            Your browser does not support
                            video playback.
                          </video>
                        ) : (
                          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-copy-muted">
                            Baseline video unavailable
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="bg-surface-raised">
                      <div className="flex items-center justify-between gap-4 px-5 py-4">
                        <Badge variant="success">
                          Comparison
                        </Badge>

                        <span className="text-xs font-semibold text-copy-subtle">
                          {selectedComparisonPhase?.label ??
                            "Phase unavailable"}
                          {" · "}
                          {selectedComparisonPhase?.timestamp ??
                            "—"}
                        </span>
                      </div>

                      <div className="relative aspect-video bg-black">
                        {comparison.videoUrl ? (
                          <video
                            ref={comparisonVideoRef}
                            className="h-full w-full object-contain"
                            playsInline
                            preload="metadata"
                            src={comparison.videoUrl}
                            onEnded={() =>
                              setIsComparisonPlaying(false)
                            }
                          >
                            Your browser does not support
                            video playback.
                          </video>
                        ) : (
                          <div className="flex h-full items-center justify-center px-6 text-center text-sm text-copy-muted">
                            Comparison video unavailable
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-white/10 px-5 py-5">
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6 lg:gap-3">
                      {comparisonPhases.map((phase) => {
                        const isSelected =
                          phase.id === selectedPhaseId;

                        return (
                          <button
                            key={phase.id}
                            aria-pressed={isSelected}
                            className={[
                              "min-h-14 w-full whitespace-normal rounded-xl border px-3 py-3 text-center text-[10px] font-semibold uppercase leading-tight tracking-[0.04em] transition",
                              isSelected
                                ? "border-lime-soft/40 bg-lime-soft/10 text-lime-soft"
                                : "border-white/10 bg-black/10 text-copy-subtle hover:border-white/20 hover:text-white",
                            ].join(" ")}
                            type="button"
                            onClick={() =>
                              handlePhaseSelect(
                                phase.id,
                              )
                            }
                          >
                            {phase.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {playbackError && (
                    <div className="border-t border-red-400/20 bg-red-400/5 px-6 py-4">
                      <p className="text-sm text-red-200">
                        {playbackError}
                      </p>
                    </div>
                  )}
                </Panel>

                <Panel
                  className="mt-6"
                  padding="lg"
                  variant="raised"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                        Overall change
                      </p>

                      <h2 className="mt-3 font-display text-3xl font-semibold text-white">
                        Swing score comparison
                      </h2>
                    </div>

                    <ScoreDifference
                      difference={overallDifference}
                    />
                  </div>

                  <div className="mt-8">
                    <div className="space-y-3 sm:hidden">
                      {metricComparisons.map(
                        (metric) => (
                          <div
                            key={metric.id}
                            className="rounded-2xl border border-white/10 bg-black/10 p-4"
                          >
                            <p className="font-semibold text-white">
                              {metric.label}
                            </p>

                            <div className="mt-4 grid grid-cols-3 gap-3">
                              <div>
                                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-copy-subtle">
                                  Before
                                </p>

                                <p className="mt-2 font-display text-2xl font-semibold text-copy-muted">
                                  {metric.baselineScore ??
                                    "—"}
                                </p>
                              </div>

                              <div>
                                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-copy-subtle">
                                  After
                                </p>

                                <p className="mt-2 font-display text-2xl font-semibold text-white">
                                  {metric.comparisonScore ??
                                    "—"}
                                </p>
                              </div>

                              <div className="text-right">
                                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-copy-subtle">
                                  Change
                                </p>

                                <div className="mt-3 flex justify-end">
                                  <ScoreDifference
                                    difference={
                                      metric.difference
                                    }
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        ),
                      )}
                    </div>

                    <div className="hidden overflow-hidden rounded-2xl border border-white/10 sm:block">
                      <div className="grid grid-cols-[minmax(0,1fr)_110px_110px_100px] gap-3 border-b border-white/10 bg-white/[0.03] px-5 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-copy-subtle">
                        <span>Metric</span>

                        <span className="text-center">
                          Before
                        </span>

                        <span className="text-center">
                          After
                        </span>

                        <span className="text-right">
                          Change
                        </span>
                      </div>

                      {metricComparisons.map(
                        (metric) => (
                          <div
                            key={metric.id}
                            className="grid grid-cols-[minmax(0,1fr)_110px_110px_100px] items-center gap-3 border-b border-white/8 px-5 py-4 last:border-b-0"
                          >
                            <span className="min-w-0 font-semibold text-white">
                              {metric.label}
                            </span>

                            <span className="text-center font-display text-xl font-semibold text-copy-muted">
                              {metric.baselineScore ??
                                "—"}
                            </span>

                            <span className="text-center font-display text-xl font-semibold text-white">
                              {metric.comparisonScore ??
                                "—"}
                            </span>

                            <span className="text-right">
                              <ScoreDifference
                                difference={
                                  metric.difference
                                }
                              />
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                </Panel>
              </>
            )}
        </Container>
      </Section>
    </main>
  );
}

export default ComparePage;