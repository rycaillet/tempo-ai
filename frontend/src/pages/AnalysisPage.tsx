import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Dumbbell,
  Gauge,
  Play,
  RotateCcw,
  Sparkles,
  Target,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";
import { Link, useParams } from "react-router-dom";

import AnalysisSkeleton from "../components/analysis/AnalysisSkeleton";
import MetricDetailDrawer from "../components/analysis/MetricDetailDrawer";
import PhaseCoachPanel from "../components/analysis/PhaseCoachPanel";
import SwingTimeline from "../components/analysis/SwingTimeline";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/ui/Container";
import Panel from "../components/ui/Panel";
import ScoreRing from "../components/ui/ScoreRing";
import Section from "../components/ui/Section";
import { getAnalysis } from "../services/analysisService";
import type {
  SwingAnalysis,
  SwingMetric,
  SwingPhase,
} from "../types/analysis";

const severityVariant = {
  High: "warning",
  Medium: "info",
  Low: "neutral",
} as const;

const metricPhaseIds: Record<string, string> = {
  tempo: "top",
  addressPosture: "address",
  impactPosition: "impact",
  headStability: "address",
  weightShift: "downswing",
  earlyExtension: "impact",
  rotation: "top",
  consistency: "finish",
};

function getPhaseTime(
  phase: SwingPhase,
  duration: number,
) {
  const parsedTimestamp = Number.parseFloat(
    phase.timestamp.replace("s", ""),
  );

  if (
    Number.isFinite(parsedTimestamp) &&
    parsedTimestamp >= 0
  ) {
    if (duration > 0) {
      return Math.min(parsedTimestamp, duration);
    }

    return parsedTimestamp;
  }

  return 0;
}

function formatPlaybackTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0.0s";
  }

  return `${seconds.toFixed(1)}s`;
}

function formatPercentage(
  value: number | null,
) {
  if (value === null) {
    return "Unavailable";
  }

  return `${Math.round(value * 100)}%`;
}

function formatDegrees(
  value: number | null,
) {
  if (value === null) {
    return "Unavailable";
  }

  return `${value.toFixed(1)}°`;
}

function formatObservationLabel(
  value: string | null,
) {
  if (!value) {
    return "Unavailable";
  }

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}

function formatClubWarning(
  warning: string,
) {
  const warningLabels: Record<
    string,
    string
  > = {
    tracked_reference_geometry_used:
      "Tracked reference geometry was used.",
    low_reference_confidence:
      "At least one reference phase had limited confidence.",
  };

  return (
    warningLabels[warning] ??
    formatObservationLabel(warning)
  );
}

function findCurrentPhase(
  phases: SwingPhase[],
  currentTime: number,
  duration: number,
) {
  if (phases.length === 0) {
    return undefined;
  }

  return phases.reduce<SwingPhase>(
    (currentPhase, phase) => {
      const phaseTime = getPhaseTime(
        phase,
        duration,
      );

      if (phaseTime <= currentTime) {
        return phase;
      }

      return currentPhase;
    },
    phases[0],
  );
}

function AnalysisPage() {
  const { swingId } = useParams();

  const videoRef =
    useRef<HTMLVideoElement | null>(null);

  const [analysis, setAnalysis] =
    useState<SwingAnalysis | null>(null);

  const [selectedPhaseId, setSelectedPhaseId] =
    useState("address");

  const [isPlaying, setIsPlaying] =
    useState(false);

  const [currentTime, setCurrentTime] =
    useState(0);

  const [videoDuration, setVideoDuration] =
    useState(0);

  const [videoError, setVideoError] =
    useState<string | null>(null);

  const [
    selectedMetricId,
    setSelectedMetricId,
  ] = useState<string | null>(null);

  const [
    previewedMetricId,
    setPreviewedMetricId,
  ] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalysis() {
      const result = await getAnalysis(
        swingId ?? "demo-swing",
      );

      setAnalysis(result);
    }

    void loadAnalysis();
  }, [swingId]);

  if (!analysis) {
    return <AnalysisSkeleton />;
  }

  const {
    summary: analysisSummary,
    videoUrl,
    phases: swingPhases,
    metrics: swingMetrics,
    clubAnalysis,
    findings: swingFindings,
    practicePlan,
  } = analysis;

  const selectedPhase =
    swingPhases.find(
      (phase) => phase.id === selectedPhaseId,
    ) ?? swingPhases[0];

  const selectedFinding =
    selectedPhase?.coaching.findingId
      ? swingFindings.find(
          (finding) =>
            finding.id ===
            selectedPhase.coaching.findingId,
        )
      : undefined;

  const selectedMetric =
    swingMetrics.find(
      (metric) =>
        metric.id === selectedMetricId,
    ) ?? null;

  const selectedMetricFinding =
    selectedMetric
      ? swingFindings.find(
          (finding) =>
            finding.metricKey ===
            selectedMetric.id,
        ) ?? null
      : null;

  function getMetricPhase(
    metric: SwingMetric,
  ) {
    const phaseId =
      metricPhaseIds[metric.id];

    return (
      swingPhases.find(
        (phase) => phase.id === phaseId,
      ) ?? swingPhases[0]
    );
  }

  function previewMetricPhase(
    metric: SwingMetric,
  ) {
    const phase = getMetricPhase(metric);

    if (!phase) {
      return;
    }

    setPreviewedMetricId(metric.id);
    setSelectedPhaseId(phase.id);
  }

  function restorePlaybackPhase() {
    setPreviewedMetricId(null);

    const currentPhase = findCurrentPhase(
      swingPhases,
      currentTime,
      videoDuration,
    );

    if (currentPhase) {
      setSelectedPhaseId(currentPhase.id);
    }
  }

  function handleMetricSelect(
    metric: SwingMetric,
  ) {
    const phase = getMetricPhase(metric);

    setPreviewedMetricId(null);
    setSelectedMetricId(metric.id);

    if (phase) {
      handlePhaseSelect(phase);
    }
  }

  function handlePhaseSelect(
    phase: SwingPhase,
  ) {
    setSelectedPhaseId(phase.id);

    const video = videoRef.current;

    if (!video || videoDuration <= 0) {
      return;
    }

    const phaseTime = getPhaseTime(
      phase,
      videoDuration,
    );

    video.currentTime = phaseTime;
    setCurrentTime(phaseTime);
  }

  function handleTimelineSeek(
    timeSeconds: number,
  ) {
    const video = videoRef.current;

    if (
      !video ||
      !Number.isFinite(timeSeconds)
    ) {
      return;
    }

    const nextTime =
      videoDuration > 0
        ? Math.min(
            videoDuration,
            Math.max(0, timeSeconds),
          )
        : Math.max(0, timeSeconds);

    video.currentTime = nextTime;
    setCurrentTime(nextTime);

    const currentPhase = findCurrentPhase(
      swingPhases,
      nextTime,
      videoDuration,
    );

    if (currentPhase) {
      setSelectedPhaseId(currentPhase.id);
    }
  }

  async function handlePlay() {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    try {
      await video.play();
      setVideoError(null);
    } catch {
      setVideoError(
        "The video could not begin playback.",
      );
    }
  }

  function handleTimeUpdate() {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    const nextTime = video.currentTime;

    const currentPhase = findCurrentPhase(
      swingPhases,
      nextTime,
      video.duration,
    );

    setCurrentTime(nextTime);

    if (currentPhase) {
      setSelectedPhaseId(currentPhase.id);
    }
  }

  function handleLoadedMetadata() {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    setVideoDuration(video.duration);
    setCurrentTime(video.currentTime);
    setVideoError(null);
  }

  return (
    <main className="min-h-screen bg-canvas text-copy">
      <Section spacing="lg">
        <Container size="wide">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-sm font-semibold text-copy-muted transition hover:text-white"
          >
            <ArrowLeft size={17} />
            Return to dashboard
          </Link>

          <div className="mt-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-lime-soft">
                Swing analysis
              </p>

              <h1 className="mt-4 font-display text-5xl font-semibold tracking-[-0.05em] text-white">
                {analysisSummary.title}
              </h1>

              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3 text-sm text-copy-muted">
                {analysisSummary.club && (
                  <span>{analysisSummary.club}</span>
                )}

                {analysisSummary.cameraAngle && (
                  <span>
                    {analysisSummary.cameraAngle}
                  </span>
                )}

                <span className="inline-flex items-center gap-2">
                  <CalendarDays size={15} />
                  {analysisSummary.date}
                </span>

                <span className="text-copy-subtle">
                  Analysis ID:{" "}
                  {swingId ?? analysisSummary.id}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                to="/analysis/new"
                variant="secondary"
              >
                <RotateCcw size={17} />
                Analyze another
              </Button>

              <Button to="/compare">
                Compare swing
                <ChevronRight size={17} />
              </Button>
            </div>
          </div>

          <div className="mt-14 grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.65fr)]">
            <Panel
              padding="none"
              variant="raised"
            >
              <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-display text-xl font-semibold text-white">
                    Analyzed swing video
                  </p>

                  <p className="mt-1 text-sm text-copy-subtle">
                    {selectedPhase.label} selected
                    {" · "}
                    {formatPlaybackTime(currentTime)}
                  </p>
                </div>

                <Badge variant="success">
                  Analysis complete
                </Badge>
              </div>

              <div className="relative aspect-video overflow-hidden bg-black">
                {videoUrl ? (
                  <>
                    <video
                      ref={videoRef}
                      src={videoUrl}
                      className="h-full w-full object-contain"
                      controls
                      playsInline
                      preload="metadata"
                      onCanPlay={() =>
                        setVideoError(null)
                      }
                      onEnded={() =>
                        setIsPlaying(false)
                      }
                      onError={() =>
                        setVideoError(
                          "TempoAI could not load this swing video.",
                        )
                      }
                      onLoadedMetadata={
                        handleLoadedMetadata
                      }
                      onPause={() =>
                        setIsPlaying(false)
                      }
                      onPlay={() =>
                        setIsPlaying(true)
                      }
                      onTimeUpdate={
                        handleTimeUpdate
                      }
                    >
                      Your browser does not
                      support video playback.
                    </video>

                    {!isPlaying && (
                      <button
                        aria-label="Play analyzed swing"
                        className="absolute left-1/2 top-1/2 z-10 flex size-20 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-black/60 text-white backdrop-blur transition hover:scale-105 hover:bg-black/75"
                        type="button"
                        onClick={() =>
                          void handlePlay()
                        }
                      >
                        <Play
                          fill="currentColor"
                          size={28}
                        />
                      </button>
                    )}
                  </>
                ) : (
                  <div className="flex h-full items-center justify-center px-6 text-center">
                    <div>
                      <p className="font-display text-2xl font-semibold text-white">
                        Video unavailable
                      </p>

                      <p className="mt-3 text-sm leading-6 text-copy-muted">
                        This analysis does not
                        contain a stored video file.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {videoError && (
                <div className="border-t border-red-400/20 bg-red-400/5 px-6 py-4">
                  <p className="text-sm text-red-200">
                    {videoError}
                  </p>
                </div>
              )}

              <div className="border-t border-white/10 px-5 py-5">
                <SwingTimeline
                  phases={swingPhases}
                  currentTime={currentTime}
                  duration={videoDuration}
                  selectedPhaseId={selectedPhase.id}
                  onPhaseSelect={handlePhaseSelect}
                  onSeek={handleTimelineSeek}
                />
              </div>
            </Panel>

            <div className="grid gap-6">
              <Panel
                className="flex flex-col items-center justify-center"
                padding="lg"
                variant="raised"
              >
                <ScoreRing
                  label="Swing score"
                  score={analysisSummary.overallScore}
                  rating={analysisSummary.ratingLabel}
                  subtitle={
                    analysisSummary.change ??
                    "Production engine result"
                  }
                />
              </Panel>

              <PhaseCoachPanel
                phase={selectedPhase}
                finding={selectedFinding}
              />
            </div>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
            {swingMetrics.map((metric) => {
              const isMetricActive =
                previewedMetricId === metric.id ||
                selectedMetricId === metric.id;

              return (
                <button
                  key={metric.id}
                  aria-haspopup="dialog"
                  className="group h-full text-left focus:outline-none"
                  type="button"
                  onBlur={restorePlaybackPhase}
                  onClick={() =>
                    handleMetricSelect(metric)
                  }
                  onFocus={() =>
                    previewMetricPhase(metric)
                  }
                  onMouseEnter={() =>
                    previewMetricPhase(metric)
                  }
                  onMouseLeave={
                    restorePlaybackPhase
                  }
                >
                  <Panel
                    className={[
                      "h-full transition duration-200 group-hover:-translate-y-1 group-focus-visible:ring-2 group-focus-visible:ring-lime-soft/60",
                      isMetricActive
                        ? "border-lime-soft/40 shadow-lime ring-1 ring-lime-soft/30"
                        : "group-hover:border-lime-soft/25 group-hover:shadow-lime",
                    ].join(" ")}
                    padding="md"
                    variant="raised"
                  >
                    <div className="flex items-center justify-between">
                      <p
                        className={[
                          "text-sm font-semibold uppercase tracking-[0.18em] transition",
                          isMetricActive
                            ? "text-lime-soft"
                            : "text-copy-subtle",
                        ].join(" ")}
                      >
                        {metric.label}
                      </p>

                      <Gauge
                        className={[
                          "text-lime-soft transition",
                          isMetricActive
                            ? "scale-110"
                            : "group-hover:scale-110",
                        ].join(" ")}
                        size={18}
                      />
                    </div>

                    <p className="mt-5 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                      {metric.score}
                    </p>

                    <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/8">
                      <div
                        className="h-full rounded-full bg-lime-soft"
                        style={{
                          width: `${metric.score}%`,
                        }}
                      />
                    </div>

                    <p className="mt-4 text-sm leading-6 text-copy-muted">
                      {metric.description}
                    </p>

                    <p
                      className={[
                        "mt-5 text-xs font-semibold uppercase tracking-[0.16em] text-ice transition",
                        isMetricActive
                          ? "opacity-100"
                          : "opacity-70 group-hover:opacity-100",
                      ].join(" ")}
                    >
                      View details
                    </p>
                  </Panel>
                </button>
              );
            })}
          </div>

          {clubAnalysis && (
            <section className="mt-16">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-ice">
                    Club analysis
                  </p>

                  <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                    Camera-relative club observations
                  </h2>

                  <p className="mt-3 max-w-3xl leading-7 text-copy-muted">
                    These measurements describe the detected
                    shaft in the two-dimensional video frame.
                    They are shown separately from scored body
                    metrics and should not be interpreted as a
                    reconstructed three-dimensional club path.
                  </p>
                </div>

                <Badge variant="info">
                  Measurement only
                </Badge>
              </div>

              <div className="mt-8 grid gap-6 xl:grid-cols-3">
                <Panel
                  padding="lg"
                  variant="raised"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                        Shaft lean
                      </p>

                      <p className="mt-4 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                        {formatDegrees(
                          clubAnalysis.shaftLean
                            .angleDegrees,
                        )}
                      </p>

                      <p className="mt-2 text-sm text-ice">
                        From image vertical
                      </p>
                    </div>

                    <div className="flex size-11 items-center justify-center rounded-2xl bg-ice/10 text-ice">
                      <Gauge size={21} />
                    </div>
                  </div>

                  <dl className="mt-7 space-y-4 border-t border-white/10 pt-6">
                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Direction
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {formatObservationLabel(
                          clubAnalysis.shaftLean
                            .direction,
                        )}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Geometry
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {formatObservationLabel(
                          clubAnalysis.shaftLean
                            .geometrySource,
                        )}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Confidence
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {formatPercentage(
                          clubAnalysis.shaftLean
                            .confidence,
                        )}
                      </dd>
                    </div>
                  </dl>
                </Panel>

                <Panel
                  padding="lg"
                  variant="raised"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                        Swing plane
                      </p>

                      <p className="mt-4 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                        {formatDegrees(
                          clubAnalysis.swingPlane
                            .topToImpactDegrees,
                        )}
                      </p>

                      <p className="mt-2 text-sm text-ice">
                        Top-to-impact angle change
                      </p>
                    </div>

                    <div className="flex size-11 items-center justify-center rounded-2xl bg-ice/10 text-ice">
                      <Gauge size={21} />
                    </div>
                  </div>

                  <dl className="mt-7 space-y-4 border-t border-white/10 pt-6">
                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Confidence
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {formatPercentage(
                          clubAnalysis.swingPlane
                            .confidence,
                        )}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Smoothed phases
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {clubAnalysis.swingPlane
                          .smoothedReferenceCount ??
                          "Unavailable"}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Tracked phases
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {clubAnalysis.swingPlane
                          .trackedReferenceCount ??
                          "Unavailable"}
                      </dd>
                    </div>
                  </dl>
                </Panel>

                <Panel
                  padding="lg"
                  variant="raised"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                        Detection quality
                      </p>

                      <p className="mt-4 font-display text-4xl font-semibold tracking-[-0.05em] text-white">
                        {formatPercentage(
                          clubAnalysis.quality
                            .detectionRate,
                        )}
                      </p>

                      <p className="mt-2 text-sm text-ice">
                        Frames with club detection
                      </p>
                    </div>

                    <div className="flex size-11 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                      <CheckCircle2 size={21} />
                    </div>
                  </div>

                  <dl className="mt-7 space-y-4 border-t border-white/10 pt-6">
                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Detected frames
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {clubAnalysis.quality
                          .detectedFrames ??
                          "Unavailable"}
                        {clubAnalysis.quality
                          .requestedFrames !== null &&
                          ` of ${clubAnalysis.quality.requestedFrames}`}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Reference phases
                      </dt>

                      <dd className="text-sm font-semibold text-white">
                        {clubAnalysis.quality
                          .referencePhasesAvailable ??
                          "Unavailable"}
                        {clubAnalysis.quality
                          .referencePhasesTotal !== null &&
                          ` of ${clubAnalysis.quality.referencePhasesTotal}`}
                      </dd>
                    </div>

                    <div className="flex items-center justify-between gap-4">
                      <dt className="text-sm text-copy-subtle">
                        Geometry processing
                      </dt>

                      <dd className="text-right text-sm font-semibold text-white">
                        {[
                          clubAnalysis.quality
                            .usesSmoothedGeometry
                            ? "Smoothed"
                            : null,
                          clubAnalysis.quality
                            .usesTrackedGeometry
                            ? "Tracked"
                            : null,
                        ]
                          .filter(Boolean)
                          .join(" + ") ||
                          "Image detections"}
                      </dd>
                    </div>
                  </dl>
                </Panel>
              </div>

              {(clubAnalysis.quality.warnings.length >
                0 ||
                clubAnalysis.limitations.length >
                  0) && (
                <Panel
                  className="mt-6"
                  padding="lg"
                  variant="muted"
                >
                  <div className="grid gap-8 lg:grid-cols-2">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                        Quality notes
                      </p>

                      <div className="mt-4 space-y-3">
                        {clubAnalysis.quality.warnings
                          .map(formatClubWarning)
                          .map((warning) => (
                            <div
                              key={warning}
                              className="flex items-start gap-3"
                            >
                              <CheckCircle2
                                className="mt-0.5 shrink-0 text-ice"
                                size={17}
                              />

                              <p className="text-sm leading-6 text-copy-muted">
                                {warning}
                              </p>
                            </div>
                          ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                        Measurement limitations
                      </p>

                      <div className="mt-4 space-y-3">
                        {clubAnalysis.limitations.map(
                          (limitation) => (
                            <p
                              key={limitation}
                              className="text-sm leading-6 text-copy-muted"
                            >
                              {limitation}
                            </p>
                          ),
                        )}
                      </div>
                    </div>
                  </div>
                </Panel>
              )}
            </section>
          )}

          <div className="mt-16 grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
            <div className="space-y-6">
              <Panel
                padding="lg"
                variant="raised"
              >
                <div className="flex items-start gap-4">
                  <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-lime-soft/10 text-lime-soft">
                    <Sparkles size={23} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      AI coaching summary
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold tracking-[-0.04em] text-white">
                      Your swing analysis
                    </h2>

                    <p className="mt-5 leading-8 text-copy-muted">
                      {analysisSummary.summary}
                    </p>

                    <div className="mt-7 flex items-start gap-3 rounded-2xl border border-lime-soft/15 bg-lime-soft/[0.05] p-4">
                      <CheckCircle2
                        className="mt-0.5 shrink-0 text-lime-soft"
                        size={20}
                      />

                      <div>
                        <p className="font-semibold text-white">
                          Strongest measured area
                        </p>

                        <p className="mt-1 text-sm leading-6 text-copy-muted">
                          {analysisSummary.strength}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </Panel>

              <div>
                <div className="mb-6 flex items-end justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lime-soft">
                      Coaching priorities
                    </p>

                    <h2 className="mt-3 font-display text-3xl font-semibold text-white">
                      What to work on next
                    </h2>
                  </div>

                  <p className="hidden text-sm text-copy-subtle sm:block">
                    Prioritized by impact
                  </p>
                </div>

                <div className="space-y-4">
                  {swingFindings.map(
                    (finding) => {
                      const isSelectedFinding =
                        selectedFinding?.id ===
                        finding.id;

                      return (
                        <Panel
                          key={finding.id}
                          className={[
                            "transition",
                            isSelectedFinding
                              ? "ring-1 ring-lime-soft/50"
                              : "",
                          ].join(" ")}
                          padding="lg"
                          variant="raised"
                        >
                          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
                            <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-lime-soft/10 font-display text-lg font-semibold text-lime-soft">
                              {finding.priority}
                            </div>

                            <div className="flex-1">
                              <div className="flex flex-wrap items-center gap-3">
                                <h3 className="font-display text-2xl font-semibold text-white">
                                  {finding.title}
                                </h3>

                                <Badge
                                  variant={
                                    severityVariant[
                                      finding
                                        .severity
                                    ]
                                  }
                                >
                                  {
                                    finding.severity
                                  }{" "}
                                  priority
                                </Badge>

                                {isSelectedFinding && (
                                  <Badge variant="success">
                                    Selected phase
                                  </Badge>
                                )}
                              </div>

                              <p className="mt-2 text-sm font-medium text-ice">
                                {finding.phase}{" "}
                                phase
                              </p>

                              <p className="mt-5 leading-7 text-copy-muted">
                                {
                                  finding.explanation
                                }
                              </p>

                              <div className="mt-6 grid gap-5 border-t border-white/10 pt-6 md:grid-cols-2">
                                <div>
                                  <p className="text-sm font-semibold text-white">
                                    Supporting
                                    evidence
                                  </p>

                                  <p className="mt-2 text-sm leading-6 text-copy-muted">
                                    {
                                      finding.evidence
                                    }
                                  </p>
                                </div>

                                <div>
                                  <p className="text-sm font-semibold text-white">
                                    {
                                      finding.drill
                                        .name
                                    }
                                  </p>

                                  <p className="mt-2 text-sm leading-6 text-copy-muted">
                                    {
                                      finding.drill
                                        .instructions
                                    }
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        </Panel>
                      );
                    },
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <Panel
                padding="lg"
                variant="raised"
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-ice/10 text-ice">
                    <Dumbbell size={21} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                      Practice plan
                    </p>

                    <h2 className="mt-1 font-display text-2xl font-semibold text-white">
                      Your next 25 minutes
                    </h2>
                  </div>
                </div>

                <div className="mt-8 space-y-6">
                  {practicePlan.map(
                    (item, index) => (
                      <div
                        key={item.label}
                        className="grid grid-cols-[auto_1fr] gap-4"
                      >
                        <div className="flex size-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold text-white">
                          {index + 1}
                        </div>

                        <div>
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-semibold text-white">
                              {item.label}
                            </p>

                            <span className="inline-flex items-center gap-1.5 text-xs text-copy-subtle">
                              <Clock3
                                size={13}
                              />
                              {item.duration}
                            </span>
                          </div>

                          <p className="mt-2 text-sm leading-6 text-copy-muted">
                            {
                              item.instructions
                            }
                          </p>
                        </div>
                      </div>
                    ),
                  )}
                </div>

                <Button
                  className="mt-8 w-full"
                  to="/analysis/new"
                >
                  Record next swing
                  <Target size={17} />
                </Button>
              </Panel>

              <Panel
                padding="lg"
                variant="muted"
              >
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-copy-subtle">
                  Analysis limitations
                </p>

                <p className="mt-4 text-sm leading-7 text-copy-muted">
                  Results depend on camera
                  placement, lighting, video
                  quality, pose-detection
                  confidence, and the visibility
                  of your full body throughout the
                  recording.
                </p>
              </Panel>
            </div>
          </div>
        </Container>
      </Section>

      <MetricDetailDrawer
        metric={selectedMetric}
        finding={selectedMetricFinding}
        onClose={() =>
          setSelectedMetricId(null)
        }
      />
    </main>
  );
}

export default AnalysisPage;